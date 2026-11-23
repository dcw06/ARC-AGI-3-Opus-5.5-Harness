"""One official ARC scorecard for the whole-game runs with every layer, made by replaying their recorded actions.

The whole-game runs (whole_games.py, whole_games_rest.py, whole_games_last.py) were played on local copies of
the games, so no scorecard exists for them. This sends every recorded action of all 25 games to the ARC service
in one competition-mode scorecard, with no model call. It is the baseline's replay
(research/baseline_continue_v1/replay_scorecard.py) pointed at these runs: the same sender, the same check after
every action (the observation the service returns must hash to the recorded one; at the first difference that
game stops), the same scoring rule for the expected score.

A game's actions come from the last part of its run, which holds the whole game. A game that halted because a
reply kept running past the time limit is sent up to the action it reached.

One difference from the baseline's sender. There a game stops at the first returned observation whose hash differs
from the recorded one. lf52 has an animated action on level 6 (21 frames) whose in-between frames come out
differently from one process to the next, while the board it ends on is the same: replayed locally, 25 of the 1,350
recorded lf52 actions return another hash, each with an equal last frame, state and level count, and every other
action returns the recorded hash. So here an observation whose hash differs is accepted when its last frame, its
state and its level count equal the recorded ones; the game stops only when one of those differs. Such actions
are counted apart.

    replay_scorecard.py expect       offline: the score the service should give
    replay_scorecard.py dry          offline: the same replay against local game copies
    replay_scorecard.py inventory    read-only call: does the service still offer the recorded game versions?
    replay_scorecard.py send --confirm-online-arc     the live replay; needs all 25 games, none still playing

  --available   (expect, dry) use the games that have finished and leave out the rest, to try the tool early
  --current     (expect, dry, send) a scorecard of the state right now: a game that is still playing is sent up to
                the last action it has finished. Asked for by the user on 2026-11-22, before the last three games
                (dc22, re86, wa30) had ended; the scorecard gets a tag saying so

Usage (project environment), from the repository root.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.baseline_continue_v1 import replay_scorecard as B  # noqa: E402
from research.level_brief_v1 import whole_games as W  # noqa: E402

# the sets of games; a later stamp wins (wa30 was started again under its own, after 17 actions under the third)
STAMPS = ('20261121T235533Z', '20261122T071626Z', '20261122T172802Z', '20261122T173235Z')
TAGS = ['claude-arc-v1', 'hypotheses', 'competition', 'replay-of-recorded-actions', 'level-brief-v1-all-layers']
RUNS = ROOT / '.cache/claude_arc_runs'
REPORT = ROOT / 'reports/level_brief_v1'


def board_hash(frame):
    return hashlib.sha256(np.ascontiguousarray(frame, dtype=np.uint8).tobytes()).hexdigest()


def replay(adapter, plan, log, pace):
    """The baseline's sender (B.replay) with one change: an observation whose hash differs from the recorded one is
    accepted when its last frame, state and level count are the recorded ones. One scorecard, opened and closed
    here. Returns (card id, what the service returned at close, per-game results)."""
    from agent.action import ActionDecision
    results, card, closed = [], None, None
    inventory = adapter.list_game_ids()
    absent = [g for g in plan if g not in inventory]
    if absent:
        raise SystemExit('these game versions are not offered by the service, nothing was sent: ' + ', '.join(absent))
    card = adapter.open_scorecard(tags=TAGS)
    log({'event': 'scorecard_opened', 'card_id': card})
    print('scorecard opened:', card, flush=True)
    try:
        for game, saved in plan.items():
            row = {'game': game, 'recorded_actions': len(saved['steps']), 'sent': 0, 'matched': 0,
                   'same_final_board_other_frames': 0, 'stopped': None}
            results.append(row)
            client = None
            began = time.monotonic()
            try:
                client = adapter.bootstrap(game)
                if client.observation.canonical_hash != saved['first']:
                    row['stopped'] = 'the first board differs from the recorded one'
                    continue
                for index, step in enumerate(saved['steps']):
                    tick = time.monotonic()
                    decision = ActionDecision(step['action']['action_id'], dict(step['action']['action_data']),
                                              source='recorded_replay')
                    after = adapter.dispatch(client, decision)
                    row['sent'] += 1
                    if after.canonical_hash == step['after']:
                        row['matched'] += 1
                    elif (board_hash(after.frames[-1]) == step['last_frame'] and after.state.name == step['state']
                          and after.levels_completed == step['levels']):
                        row['same_final_board_other_frames'] += 1
                    else:
                        row['stopped'] = 'the board differs from the recorded one at action %d' % (index + 1)
                        break
                    wait = pace - (time.monotonic() - tick)
                    if wait > 0:
                        time.sleep(wait)
            except KeyboardInterrupt:
                row['stopped'] = 'interrupted'
                raise
            except Exception as exc:
                row['stopped'] = '%s: %s' % (type(exc).__name__, str(exc)[:200])
            finally:
                if client is not None:
                    adapter.finalize_client(client)
                row['seconds'] = round(time.monotonic() - began, 1)
                log({'event': 'game', **row})
                print('  %-14s sent %4d of %4d, matched %4d%s, %s' % (
                    game, row['sent'], row['recorded_actions'], row['matched'],
                    ' and %d with the same final board' % row['same_final_board_other_frames']
                    if row['same_final_board_other_frames'] else '', row['stopped'] or 'complete'), flush=True)
    finally:
        try:
            closed = adapter.close_scorecard()
            log({'event': 'scorecard_closed', 'result': closed})
        except Exception as exc:
            log({'event': 'scorecard_close_failed', 'error': '%s: %s' % (type(exc).__name__, str(exc)[:200])})
    return card, closed, results


def last_part(game):
    """(folder of the last part of the game's run, its state), or (None, 'not started')."""
    for stamp in reversed(STAMPS):
        parts = W.parts(game, stamp)
        if parts:
            return parts[-1], W.state_of(parts[-1])
    return None, 'not started'


def recorded(available=False, current=False):
    """{game id: {'source', 'state', 'first', 'steps': [...]}} in the 6 November order, as the baseline's replay
    reads it. Without `available`, every game must have finished; with `current`, a game still playing is taken
    up to the last action its log holds in full."""
    out, open_games = {}, []
    for game in B.saved_summary()['selected_games']:
        folder, state = last_part(game)
        if state not in ('done', 'stopped') and not (current and state == 'running'):
            open_games.append('%s (%s)' % (game.split('-')[0], state))
            continue
        first, steps = None, []
        with (folder / 'events.jsonl').open(encoding='utf-8') as handle:
            for line in handle:
                if not line.endswith('\n'):
                    break
                if '"kind":"initial_observation"' in line:
                    first = json.loads(line)['observation']['observation_sha256']
                elif '"kind":"transition"' in line:
                    event = json.loads(line)
                    steps.append({'action': event['action'], 'after': event['after']['observation_sha256'],
                                  'before_levels': event['before']['levels_completed'],
                                  'levels': event['after']['levels_completed'], 'state': event['after']['state'],
                                  'last_frame': board_hash(event['after']['frames'][-1])})
        out[game] = {'source': str(folder.relative_to(ROOT)),
                     'state': {'done': 'ended', 'stopped': 'halted', 'running': 'still playing'}[state],
                     'first': first, 'steps': steps}
    if open_games and not available:
        raise SystemExit('not finished: %s. Wait for them, or pass --available to try the tool on the rest.'
                         % ', '.join(open_games))
    if open_games:
        print('left out, not finished:', ', '.join(open_games))
    return out


if __name__ == '__main__':
    os.chdir(ROOT)
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    available, current = '--available' in sys.argv, '--current' in sys.argv
    if command == 'expect':
        plan = recorded(available, current)
        card, rows = B.expect(plan)
        for row in rows:
            print('  %-14s actions %4d  resets %2d  levels %d of %d  expected score %6.2f  %s' % (
                row['game'], row['actions'], row['resets'], row['levels_completed'], row['levels'], row['score'],
                '' if plan[row['game']]['state'] == 'ended' else '(%s)' % plan[row['game']]['state']))
        print('games %d | actions %d | levels %d of %d | expected card score %.4f' % (
            len(rows), sum(r['actions'] for r in rows), sum(r['levels_completed'] for r in rows),
            sum(r['levels'] for r in rows), card))
    elif command == 'inventory':
        offered = B.live_adapter().list_game_ids()
        wanted = B.saved_summary()['selected_games']
        absent = [g for g in wanted if g not in offered]
        print('service offers %d games | all 25 recorded versions offered: %s%s' % (
            len(offered), not absent, ' | absent: ' + ', '.join(absent) if absent else ''))
        sys.exit(0 if not absent else 1)
    elif command in ('dry', 'send'):
        if command == 'send' and (available or '--confirm-online-arc' not in sys.argv):
            raise SystemExit('the live replay sends all 25 games to the ARC service: pass --confirm-online-arc, '
                             'without --available')
        plan = recorded(available, current)
        playing = sorted(g.split('-')[0] for g, saved in plan.items() if saved['state'] == 'still playing')
        if playing:                 # a snapshot says so in its tags, and which games were not finished
            TAGS = TAGS + ['snapshot-still-playing-' + '-'.join(playing)]
        if command == 'send' and len(plan) != 25:
            raise SystemExit('the scorecard needs all 25 games; %d have finished' % len(plan))
        expected_card, rows = B.expect(plan)
        folder = RUNS / ('layers-replay-%s-%s' % (command, time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())))
        folder.mkdir(parents=True)
        stream = (folder / 'replay.jsonl').open('w', encoding='utf-8')

        def log(value):
            stream.write(json.dumps(value) + '\n')
            stream.flush()
        if command == 'dry':
            from research.baseline_continue_v1.local_games import LocalGames
            adapter, pace = LocalGames(list(plan)), 0
        else:
            adapter, pace = B.live_adapter(), B.MIN_SECONDS_PER_ACTION
        card, closed, results = replay(adapter, plan, log, pace)
        complete = all(r['stopped'] is None and r['matched'] + r['same_final_board_other_frames'] == r['recorded_actions']
                       for r in results)
        manifest = {'command': command, 'card_id': card,
                    'scorecard_url': 'https://arcprize.org/scorecards/' + card if command == 'send' else None,
                    'every_action_matched': complete, 'expected_card_score': expected_card,
                    'official_scorecard': closed, 'games': results, 'expected': rows, 'tags': TAGS,
                    'halted_games_sent_up_to_their_last_action': sorted(g for g, s in plan.items() if s['state'] == 'halted'),
                    'games_still_playing_sent_up_to_their_last_action': sorted(g for g, s in plan.items() if s['state'] == 'still playing')}
        (folder / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
        stream.close()
        print('every recorded action matched:', complete, '| actions sent', sum(r['sent'] for r in results),
              '| of them accepted on the final board only', sum(r['same_final_board_other_frames'] for r in results),
              '| expected card score %.4f' % expected_card)
        if command == 'send':
            (REPORT / 'data').mkdir(exist_ok=True)
            name = 'scorecard_replay_manifest%s.json' % ('_snapshot_' + folder.name.split('-')[-1] if playing else '')
            (REPORT / 'data' / name).write_text(json.dumps(manifest, indent=1) + '\n')
            print('scorecard:', manifest['scorecard_url'])
            if isinstance(closed, dict) and 'score' in closed:
                print('official score at close: %.4f | levels %s of %s | actions %s' % (
                    closed['score'], closed.get('total_levels_completed'), closed.get('total_levels'), closed.get('total_actions')))
        print('saved:', folder.relative_to(ROOT))
        sys.exit(0 if complete else 1)
    else:
        raise SystemExit(__doc__)
