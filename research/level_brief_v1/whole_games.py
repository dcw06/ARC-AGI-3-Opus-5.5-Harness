"""Whole games with the layers on, from the first action, beside the finished baseline. Local game files, no ARC
service, no scorecard.

The eleven games on which the baseline (the unchanged harness, round 2, reports/baseline_continue_v1) scored
under 40. Each is played once from its first action with every memory layer, the object ledger and the level
brief, up to the cap the baseline had: the human count for the whole game, rounded up to 50. A cap counts
every action, level resets included, and 50 level resets are allowed, as in the baseline's round 2.

Three groups, by the account that pays for them and the budget the user set on 2026-11-21 (6,000 actions on the
signed-in account in two batches of 3,000, and 3,000 on the second account):

    second     lf52, m0r0, tr87                  the second subscription (ARC_CLAUDE_TOKEN_FILE set)
    first-1    sk48, ka59, sc25, tn36            the signed-in account, first batch
    first-2    g50t, ls20, bp35, cd82            the signed-in account, second batch, after the first has ended

The six games no layer was designed on (ka59, lf52, m0r0, sc25, sk48, tn36) are all in the groups that start
first, so what the layers do in general is known first.

A game that stops before its cap (usage limit, calls over their deadline, the machine going down) is not played
again from the start. Its next part repeats the stopped part with no model call: the model's saved replies are
given back one by one, and each request the harness builds must equal the request that was saved, so the
agent's notes, lessons, rules and briefs are rebuilt exactly. The model is asked again only from the action the
stopped part did not finish. Each part has its own folder; the last part holds the whole game.

    whole_games.py check                      no model call: the game files, the caps, the first request
    whole_games.py replay <run folder>        no model call: repeats a finished run from its saved replies and
                                              compares every request and every action with it
    whole_games.py rehearse <game id>         no model call: a short game with a stand-in for the model, stopped
                                              on purpose and continued in two more parts
    whole_games.py plan <stamp>               writes the plan; to be run before the first call
    whole_games.py game <game id> <stamp> --send
                                              the next part of one game. Prints a line starting "done:" when the
                                              game has ended, "stopped:" when the part ended early and the command
                                              can be run again, "halted:" when it must be looked at first
    whole_games.py summary <out.json> <stamp>

Usage (project environment), from the repository root.
"""
import hashlib
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from agent.e1_policy import CompletionResult  # noqa: E402
from research.claude_arc_v1 import audit, config as C, policy  # noqa: E402
from research.claude_arc_v1.backends import Budget, ClaudeCodeBackend  # noqa: E402
from research.action_waste_v1 import level_runs as L  # noqa: E402
from research.action_waste_v1.local_game import check_against_saved_run  # noqa: E402
from research.level_brief_v1 import runs as R  # noqa: E402

GROUPS = {'second': ('lf52-271a04aa', 'm0r0-492f87ba', 'tr87-cd924810'),
          'first-1': ('sk48-d8078629', 'ka59-38d34dbb', 'sc25-635fd71a', 'tn36-ef4dde99'),
          'first-2': ('g50t-5849a774', 'ls20-9607627b', 'bp35-0a0ad940', 'cd82-fb555c5d')}
ACCOUNTS = {'second': 'the second subscription', 'first-1': 'the signed-in account', 'first-2': 'the signed-in account'}
GROUP_BUDGET = 3000                 # most actions a group may play
CAPS_FILE = ROOT / 'reports/baseline_continue_v1/action_caps_human.json'
BASELINE = ROOT / 'reports/baseline_continue_v1/data/scorecard_replay_manifest_3.json'
CAPS = {row['game']: row['action_cap'] for row in json.loads(CAPS_FILE.read_text())['games']}
GAMES = {game: CAPS[game.split('-')[0]] for games in GROUPS.values() for game in games}
RESETS = 50                         # the baseline's round 2 allowance; it is not shown to the model
# layers were designed on these, or their replays were studied while designing; the other six were never used
USED_IN_DESIGN = ('bp35', 'cd82', 'g50t', 'ls20', 'tr87')
ENDED = ('action_cap', 'win', 'game_over')
MOST_PARTS = 15
REPORT = ROOT / 'reports/level_brief_v1'
RULE = ('Eleven games, one run each with the layers on, beside the baseline run of the same game at the same cap. '
        'Per game: levels completed, and the game score by the scorecard rule (replay_scorecard.game_score with the '
        'human counts of the official scorecard). Overall "better": more levels completed in total and a higher mean '
        'game score than the baseline. "worse": fewer levels in total and a lower mean game score. Anything else: '
        '"mixed". The same three numbers are given apart for the six games no layer was designed on and whose '
        'replays were not studied (ka59, lf52, m0r0, sc25, sk48, tn36) and for the five that were (bp35, cd82, g50t, '
        'ls20, tr87); what the layers do in general is read from the six. One run a game on each side, played on '
        'different days: a difference in a single game may be chance. No game is played again because of its '
        'result. A game that stops early is continued from its own saved replies, not restarted.')


def settings(game, cap=None):
    cap = GAMES[game] if cap is None else cap
    return C.Config(**{**json.loads(L.CONTROL.read_text()), 'mode': 'online', 'games': [game.split('-')[0]],
                       'max_actions_per_game': cap, 'resets_per_game': RESETS,
                       # one call per action, with room for replies the controller sends back
                       'max_model_calls': cap + cap // 4 + 40, **R.ARMS['brief']})


def name_of(game, stamp, part):
    return 'whole-%s-%s%s' % (game.split('-')[0], stamp, '-c%d' % part if part else '')


def parts(game, stamp):
    """The folders of one game's parts, in the order they were played."""
    found = []
    while (L.RUNS / name_of(game, stamp, len(found)) / 'events.jsonl').exists():
        found.append(L.RUNS / name_of(game, stamp, len(found)))
    return found


def events_of(folder):
    return [json.loads(line) for line in (Path(folder) / 'events.jsonl').read_text().splitlines()]


def state_of(folder):
    """'running' (no end yet, written to within the last ten minutes), 'done' (the game ended: cap, win, or game
    over with no reset left) or 'stopped' (ended early or was killed)."""
    path = Path(folder) / 'events.jsonl'
    final = None
    with path.open() as handle:
        for line in handle:
            if '"kind":"summary"' in line:
                final = json.loads(line)['summary']
    if final is None:
        return 'running' if time.time() - path.stat().st_mtime < 600 else 'stopped'
    rows = final['games']
    return 'done' if not final['problems'] and rows and rows[0]['stop_reason'] in ENDED else 'stopped'


def actions_in(folder):
    count = 0
    with (Path(folder) / 'events.jsonl').open() as handle:
        for line in handle:
            count += '"kind":"transition"' in line
    return count


def replies_of(folder):
    """(request, reply, backend record, seconds) for every reply of a part up to its last finished action, in
    order. Replies sent back by the controller are among them: given back again, they are sent back again."""
    found, request, last = [], None, 0
    for event in events_of(folder):
        if event['kind'] == 'model_entered':
            request = event['request']
        elif event['kind'] == 'model_returned':
            found.append((request, event['content'], event['metadata'], event.get('elapsed_seconds')))
        elif event['kind'] == 'transition':
            last = len(found)
    return found[:last]


class NotTheSameRequest(PermissionError):
    """The harness built a request that differs from the saved one: the stopped part cannot be continued as it
    is. A PermissionError, so that the controller does not ask again."""


class Continued:
    """In place of the model while the saved replies of the stopped part last, then the model itself."""

    def __init__(self, config, saved, real):
        self.config, self.saved, self.real, self.given, self.record = config, list(saved), real, 0, None
        self.budget = real.budget if real is not None else Budget(config)

    @property
    def last_record(self):
        return self.real.last_record if self.record is None and self.real is not None else self.record

    def complete(self, request):
        if not self.saved:
            if self.real is None:
                raise KeyboardInterrupt()          # a check without the model ends where the saved replies end
            self.record = None
            return self.real.complete(request)
        want, content, record, seconds = self.saved[0]
        if json.dumps(request, sort_keys=True) != json.dumps(want, sort_keys=True):
            raise NotTheSameRequest('request %d differs from the saved one' % (self.given + 1))
        reserved = self.budget.reserve()
        self.budget.settle(reserved, 0, 0)
        self.saved.pop(0)
        self.given += 1
        self.record = record
        return CompletionResult(content, 0, 0, seconds or 0)


def same_actions(first, second, count):
    """Whether two parts agree on their first `count` actions and on the boards those led to."""
    def steps(folder):
        return [(e['action'], e['after']['observation_sha256']) for e in events_of(folder) if e['kind'] == 'transition']
    one, two = steps(first)[:count], steps(second)[:count]
    return len(one) == len(two) == count and one == two


def next_part(game, stamp, real=None, config=None, send=True):
    """Play the next part of one game. Returns 'done', 'stopped' or 'halted' and says why."""
    folders = parts(game, stamp)
    states = [state_of(folder) for folder in folders]
    if 'running' in states:
        raise SystemExit('%s was written to in the last ten minutes and has not ended: it may still be playing. '
                         'Nothing was started.' % folders[states.index('running')].name)
    if states and states[-1] == 'done':
        print('done: %s has ended (%s)' % (game, folders[-1].name), flush=True)
        return 'done'
    if len(folders) >= MOST_PARTS:
        print('halted: %s has %d parts and has not ended' % (game, len(folders)), flush=True)
        return 'halted'
    if len(folders) >= 3 and actions_in(folders[-1]) == actions_in(folders[-2]) == actions_in(folders[-3]):
        print('halted: the last two parts of %s added no action' % game, flush=True)
        return 'halted'
    if folders and any(e['kind'] == 'game_failed' and e['error_type'] == 'NotTheSameRequest' for e in events_of(folders[-1])):
        print('halted: %s could not repeat the part before it' % folders[-1].name, flush=True)
        return 'halted'
    saved = replies_of(folders[-1]) if folders else []
    before = actions_in(folders[-1]) if folders else 0
    config = config or settings(game)
    if real is None and send:
        real = ClaudeCodeBackend(config, Budget(config))
    name = name_of(game, stamp, len(folders))
    backend = Continued(config, saved, real)
    L.play(game, 'brief', name, backend, config)
    if folders and backend.given == len(saved) and not same_actions(folders[-1], L.RUNS / name, before):
        print('halted: %s repeated the part before it with different actions' % name, flush=True)
        return 'halted'
    state = state_of(L.RUNS / name)
    print('%s: %s, %d actions, %d saved replies given back' % (state, name, actions_in(L.RUNS / name), backend.given),
          flush=True)
    return state


def code_hashes():
    files = ('research/claude_arc_v1/policy.py', 'research/claude_arc_v1/things.py', 'research/claude_arc_v1/config.py',
             'research/claude_arc_v1/run.py', 'research/level_brief_v1/runs.py', 'research/level_brief_v1/whole_games.py',
             'research/action_waste_v1/level_runs.py', 'research/action_waste_v1/local_game.py')
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}


def baseline():
    """{game: the baseline's actions, levels, per-level actions, score and the human count per level}."""
    value = json.loads(BASELINE.read_text())
    human = {env['id']: env['runs'][0]['level_baseline_actions'] for env in value['official_scorecard']['environments']}
    return {row['game']: {'actions': row['actions'], 'levels_completed': row['levels_completed'], 'levels': row['levels'],
                          'level_actions': row['level_actions'], 'score': row['score'], 'human_level_actions': human[row['game']]}
            for row in value['expected'] if row['game'] in GAMES}


def plan(stamp):
    value = {'written': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'stamp': stamp, 'rule': RULE,
             'set_up': R.ARMS['brief'], 'level_resets_allowed': RESETS,
             'groups': {group: {'account': ACCOUNTS[group], 'most_actions': GROUP_BUDGET,
                                'games': {game: GAMES[game] for game in games},
                                'cap_total': sum(GAMES[game] for game in games)} for group, games in GROUPS.items()},
             'used_in_design': list(USED_IN_DESIGN), 'baseline': baseline(),
             'wording': {'RULES_NOTE': policy.RULES_NOTE, 'brief_ask_with_the_completed_board': policy.brief_ask(2, True),
                         'brief_ask_without_it': policy.brief_ask(2, False), 'BRIEF_NOTE': policy.BRIEF_NOTE,
                         'NEW_NOTE': policy.NEW_NOTE},
             'rule_limit': policy.RULE_LIMIT, 'code_sha256': code_hashes()}
    path = REPORT / ('whole-plan-%s.json' % stamp)
    if path.exists():
        raise SystemExit('%s exists: a plan is written once, before the first call' % path)
    path.write_text(json.dumps(value, indent=1) + '\n')
    print('written', path)


def planned(stamp):
    path = REPORT / ('whole-plan-%s.json' % stamp)
    if not path.exists():
        raise SystemExit('write the plan first: whole_games.py plan %s' % stamp)
    changed = sorted(name for name, digest in code_hashes().items()
                     if json.loads(path.read_text())['code_sha256'].get(name) != digest)
    if changed:
        raise SystemExit('the code changed after the plan was written: %s' % ', '.join(changed))


def check():
    for group, games in GROUPS.items():
        total = sum(GAMES[game] for game in games)
        assert total <= GROUP_BUDGET, (group, total)
        print('%s (%s): %s | %d actions at most, limit %d' % (group, ACCOUNTS[group],
              ', '.join('%s %d' % (game.split('-')[0], GAMES[game]) for game in games), total, GROUP_BUDGET))
    assert len(GAMES) == 11 and sum(GAMES.values()) == 8100, sum(GAMES.values())
    reference = baseline()
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    for game, cap in GAMES.items():
        differs, total = check_against_saved_run(game)
        first = Continued(settings(game), [], None)
        try:
            L.play(game, 'brief', 'whole-check-%s-%s' % (game.split('-')[0], stamp), first, settings(game))
        except KeyboardInterrupt:
            pass
        events = events_of(L.RUNS / ('whole-check-%s-%s' % (game.split('-')[0], stamp)))
        body = json.loads(next(e for e in events if e['kind'] == 'model_entered')['request']['messages'][1]['content'])
        config = next(e for e in events if e['kind'] == 'configuration')['config']
        print('%s | local game against the saved run: %d actions, observations that differ: %s | cap %d, the baseline '
              'played %d | first request: level %d, rules list present and empty %s, brief asked for %s, rule notes '
              'offered %s, things listed %s | resets allowed %d, saved actions repeated %s'
              % (game, total, differs or 'none', cap, reference[game]['actions'],
                 body['evidence']['current']['levels_completed'] + 1, body['evidence'].get('rules') == [],
                 'level_brief' in body['output_contract'], 'rule_notes' in body['output_contract'],
                 'things' in body['evidence'], config['resets_per_game'], config.get('resume_actions')))


def replay(folder):
    """Repeat a finished run from its own saved replies, with no model call, in a new folder; every request must
    equal the saved one and every action and board must be the same."""
    folder = Path(folder)
    events = events_of(folder)
    config = C.Config(**next(e['config'] for e in events if e['kind'] == 'configuration'))
    game = next(e['game_id'] for e in events if e['kind'] == 'initial_observation')
    saved = replies_of(folder)
    backend = Continued(config, saved, None)
    name = 'whole-replay-%s-%s' % (folder.name, time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
    try:
        L.play(game, 'brief', name, backend, config)
    except KeyboardInterrupt:
        pass
    count = actions_in(folder)
    print('%s: %d saved replies, %d given back with an equal request | %d actions, the same actions and boards: %s'
          % (folder.name, len(saved), backend.given, count, same_actions(folder, L.RUNS / name, count)))
    assert backend.given == len(saved) and same_actions(folder, L.RUNS / name, count)


class Failing:
    """A stand-in for the model that stops answering after some calls, as an account at its usage limit does."""

    def __init__(self, inner, calls):
        self.inner, self.left, self.budget = inner, calls, inner.budget

    @property
    def last_record(self):
        return self.inner.last_record

    def complete(self, request):
        if self.left <= 0:
            from research.claude_arc_v1.transport import TransportFailure
            raise TransportFailure('rehearsal: no answer')
        self.left -= 1
        return self.inner.complete(request)


def rehearse(game):
    """A 60-action game with a stand-in for the model: stopped after 25 calls, continued and stopped after 20
    more, continued to the end. The audit and the summary must read the last part as one whole game."""
    stamp, cap = 'rehearsal' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()), 60
    config = replace(settings(game, cap), model_retry_backoff_seconds=0)       # no waiting between the failed calls
    states = [next_part(game, stamp, Failing(R.StandIn(config), 25), config),
              next_part(game, stamp, Failing(R.StandIn(config), 20), config),
              next_part(game, stamp, R.StandIn(config), config)]
    folders = parts(game, stamp)
    counts = [actions_in(folder) for folder in folders]
    audit.audit(folders[-1])
    row = R.summary(folders[-1])
    assert states == ['stopped', 'stopped', 'done'] and counts[0] < counts[1] < counts[2] == cap, (states, counts)
    assert row['new_actions'] == cap and row['state'] == 'clean' and next_part(game, stamp, None, config, send=False) == 'done'
    print('rehearsal of %s: parts ended %s after %s actions; the last part passes the audit and reads as one game of '
          '%d actions, %d levels' % (game, states, counts, row['new_actions'], row['levels_completed_in_new_actions']))


def summary(stamp):
    from research.baseline_continue_v1.replay_scorecard import game_score
    reference, rows = baseline(), []
    for group, games in GROUPS.items():
        for game in games:
            folders = parts(game, stamp)
            if not folders:
                rows.append({'game': game.split('-')[0], 'group': group, 'state': 'not started'})
                continue
            state, base, cap = state_of(folders[-1]), reference[game], GAMES[game]
            row = {'game': game.split('-')[0], 'group': group, 'account': ACCOUNTS[group], 'state': state, 'cap': cap,
                   'parts': [{'run': folder.name, 'actions': actions_in(folder), 'state': state_of(folder)} for folder in folders],
                   'used_in_design': game.split('-')[0] in USED_IN_DESIGN,
                   'baseline': {k: base[k] for k in ('actions', 'levels_completed', 'level_actions', 'score')},
                   'levels_in_the_game': base['levels']}
            if state == 'done':
                detail = R.summary(folders[-1])
                used = detail['actions_per_completed_level'] + [detail['actions_on_the_open_level']]
                used += [0] * (base['levels'] - len(used))
                score, _ = game_score(used[:base['levels']], base['human_level_actions'], detail['levels_completed_in_new_actions'])
                real = sum(e['kind'] == 'model_returned' and e['metadata'].get('outcome') == 'response_received'
                           for e in events_of(folders[-1]))
                row.update({'actions': detail['new_actions'], 'levels_completed': detail['levels_completed_in_new_actions'],
                            'level_actions': used[:base['levels']], 'score': score, 'model_replies': real, 'detail': detail})
            rows.append(row)
    done = [row for row in rows if row['state'] == 'done']
    out = {'stamp': stamp, 'rule': RULE, 'runs': rows, 'games_not_ended': [row['game'] for row in rows if row['state'] != 'done']}

    def compare(group):
        mine, theirs = sum(r['levels_completed'] for r in group), sum(r['baseline']['levels_completed'] for r in group)
        my_score = sum(r['score'] for r in group) / len(group)
        their_score = sum(r['baseline']['score'] for r in group) / len(group)
        word = ('better' if mine > theirs and my_score > their_score
                else 'worse' if mine < theirs and my_score < their_score else 'mixed')
        return {'games': len(group), 'levels_completed': {'layers': mine, 'baseline': theirs},
                'mean_game_score': {'layers': round(my_score, 2), 'baseline': round(their_score, 2)}, 'reading': word,
                'actions': {'layers': sum(r['actions'] for r in group), 'baseline': sum(r['baseline']['actions'] for r in group)}}
    if len(done) == len(rows):
        out['all_eleven'] = compare(done)
        out['never_used_in_design'] = compare([r for r in done if not r['used_in_design']])
        out['used_in_design'] = compare([r for r in done if r['used_in_design']])
    return out


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'check' and len(sys.argv) == 2:
        check()
    elif command == 'replay' and len(sys.argv) == 3:
        replay(sys.argv[2])
    elif command == 'rehearse' and len(sys.argv) == 3:
        rehearse(sys.argv[2])
    elif command == 'plan' and len(sys.argv) == 3:
        plan(sys.argv[2])
    elif command == 'game' and len(sys.argv) == 5 and sys.argv[4] == '--send':
        if sys.argv[2] not in GAMES:
            raise SystemExit('%s is not one of the eleven games' % sys.argv[2])
        planned(sys.argv[3])
        next_part(sys.argv[2], sys.argv[3])
    elif command == 'summary' and len(sys.argv) == 4:
        value = summary(sys.argv[3])
        Path(sys.argv[2]).write_text(json.dumps(value, indent=1) + '\n')
        for row in value['runs']:
            base = row.get('baseline') or {}
            print(json.dumps({k: row.get(k) for k in ('game', 'group', 'state', 'cap', 'actions', 'levels_completed',
                                                       'level_actions', 'score', 'model_replies')}
                             | {'baseline_levels': base.get('levels_completed'), 'baseline_score': base.get('score'),
                                'parts': len(row.get('parts') or ())}))
        for name in ('all_eleven', 'never_used_in_design', 'used_in_design'):
            if name in value:
                print(name, json.dumps(value[name]))
        if value['games_not_ended']:
            print('not ended, so no overall reading yet:', ', '.join(value['games_not_ended']))
    else:
        raise SystemExit(__doc__)
