"""Check every whole-game run with the layers: the model, the harness, the settings, the continuity of the parts,
the audit and the caps. No model call, no ARC call.

For each of the 25 games (the run that counts is the one the scorecard replay takes), over every part of it:

  - the settings: Opus 5.5, effort high, adaptive thinking, the Claude Code backend, every layer on, 50 level
    resets, the game's cap, and every other setting equal to the control configuration. The time limit is 240 s
    and 2 retries; anything else is listed (tr87's last parts, by the user's choice)
  - every reply: answered by claude-opus-5-5 and no other model, through the same CLI version
  - which account answered
  - a later part repeats the part before it action for action and board for board
  - the last part passes the harness's audit (a part that ended on a failed call is checked up to that call)
  - actions within the cap, level resets within the allowance
  - how often a call ran past its time limit, hit a usage limit or had no connection, and how many replies
    were sent back

and once: the harness files are the ones every plan pinned, and unchanged in git since the last commit.

How the failed calls are counted. A call that fails with no reply (time limit, usage limit, no connection) is
logged only in the part where it happened, so these are counted over all parts of a game. A reply that was sent
back is a reply the model did return: a later part gives it back from the saved replies and logs it again, so
these are counted in the last part only, which holds the whole game. One kind of reply is in no later part: a
reply returned in a turn that the end of a part cut short (the turn starts again in the next part). Those are
counted apart, as replies in turns cut short. (Until 2026-11-23 this script counted replies sent back over all
parts, once per part that repeated them, which gave too many: 605 of 8,675 at the time, and 696 of 11,111 for
the finished runs. The right count for the finished runs is 461 of 11,111, and 5 more in turns cut short.)

    whole_verify.py            prints one line a game and a list of everything that is not as planned
    whole_verify.py <out.json> also writes the counts, per game and in total

Usage (project environment), from the repository root.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.claude_arc_v1 import audit  # noqa: E402
from research.action_waste_v1 import level_runs as L  # noqa: E402
from research.level_brief_v1 import runs as R, whole_games as W  # noqa: E402

# stamp -> its games; the last stamp that has a game is the run that counts (wa30 was restarted under its own)
STAMPS = ('20261121T235533Z', '20261122T071626Z', '20261122T172802Z', '20261122T173235Z')
HARNESS = ('research/claude_arc_v1/policy.py', 'research/claude_arc_v1/things.py', 'research/claude_arc_v1/config.py',
           'research/claude_arc_v1/run.py', 'research/level_brief_v1/runs.py', 'research/level_brief_v1/whole_games.py',
           'research/action_waste_v1/level_runs.py', 'research/action_waste_v1/local_game.py')
MODEL, CLI = 'claude-opus-5-5', '2.1.318'


def counted(game):
    for stamp in reversed(STAMPS):
        parts = W.parts(game, stamp)
        if parts:
            return stamp, parts
    return None, []


def check_game(game, cap, control):
    stamp, parts = counted(game)
    notes = []
    if not parts:
        return {'game': game, 'state': 'not started'}, ['%s: not started' % game]
    wanted = {**control, 'mode': 'online', 'games': [game.split('-')[0]], 'max_actions_per_game': cap,
              'resets_per_game': W.RESETS, 'max_model_calls': cap + cap // 4 + 40, **R.ARMS['brief']}
    replies = models = 0
    accounts, limits, previous, row = {}, {}, None, None
    deadline = deadline_ended = usage_limit = connection = other = 0
    for folder in parts:
        events = W.events_of(folder)
        config = next(e['config'] for e in events if e['kind'] == 'configuration')
        differ = {k: (config.get(k), v) for k, v in wanted.items() if config.get(k) != v
                  and k not in ('request_timeout_seconds', 'model_retries_per_action')}
        if differ:
            notes.append('%s: settings not as planned: %s' % (folder.name, differ))
        limit = (config['request_timeout_seconds'], config['model_retries_per_action'])
        limits[limit] = limits.get(limit, 0) + 1
        steps = [(e['action'], e['after']['observation_sha256']) for e in events if e['kind'] == 'transition']
        if previous is not None and steps[:len(previous)] != previous[:len(steps)] and steps[:len(previous)] != previous:
            notes.append('%s: does not repeat the part before it' % folder.name)
        previous = steps
    events = W.events_of(parts[-1])            # the last part holds the whole game
    for e in events:
        if e['kind'] == 'model_returned':
            replies += 1
            record = e['metadata']
            used = set(record.get('model_usage') or {})
            models += record.get('model') == MODEL and used == {MODEL}
            if record.get('cli_version') != CLI:
                notes.append('%s: a reply came through CLI %s' % (game, record.get('cli_version')))
            name = record.get('subscription_token_file') or 'signed-in'
            accounts[name] = accounts.get(name, 0) + 1
    def returned_then_refused(e):               # the model answered and the harness sent the reply back
        return (e['kind'] in ('model_failed_retrying', 'game_failed')
                and e['error_type'] not in ('TransportFailure', 'KeyboardInterrupt'))

    sent_back = sum(1 for e in events if returned_then_refused(e))     # last part only: see the note at the top
    cut_short = cut_short_sent_back = 0
    for folder in parts:
        earlier = W.events_of(folder)
        if folder != parts[-1]:                 # replies of the turn the part ended in: the next part starts it again
            done = max((n for n, e in enumerate(earlier) if e['kind'] == 'transition'), default=-1)
            cut_short += sum(1 for e in earlier[done + 1:] if e['kind'] == 'model_returned')
            cut_short_sent_back += sum(1 for e in earlier[done + 1:] if returned_then_refused(e))
        for e in earlier:                       # calls with no reply: logged only in the part where they happened
            if e['kind'] not in ('model_failed_retrying', 'game_failed'):
                continue
            text = e.get('error') or ''
            if e['error_type'] == 'TransportFailure' and 'exceeded its deadline' in text:
                deadline += 1
                deadline_ended += e['kind'] == 'game_failed'
            elif e['error_type'] == 'TransportFailure' and 'limit' in text and 'resets' in text:
                usage_limit += 1
            elif e['error_type'] == 'TransportFailure' and "Can't reach" in text:
                connection += 1
                notes.append('%s: no connection' % folder.name)
            elif e['kind'] == 'game_failed' and returned_then_refused(e):
                notes.append('%s: the part ended on a reply sent back: %s' % (folder.name, text[:70]))
            elif e['error_type'] == 'TransportFailure':
                other += 1
                notes.append('%s: %s %s' % (folder.name, e['error_type'], text[:90]))
    if models != replies:
        notes.append('%s: %d of %d replies are not from %s alone' % (game, replies - models, replies, MODEL))
    state = W.state_of(parts[-1])
    actions = len(previous)
    resets = sum(1 for action, _ in previous if action['action_id'] == 0)
    levels = max([e['after']['levels_completed'] for e in events if e['kind'] == 'transition'] or [0])
    if actions > cap or resets > W.RESETS:
        notes.append('%s: %d actions (cap %d), %d resets' % (game, actions, cap, resets))
    audited = 'not ended'
    if state != 'running':
        try:
            audit.audit(parts[-1])
            audited = 'passes'
        except Exception as exc:
            audited = 'fails: %s' % str(exc)[:120]
            if state == 'done':
                notes.append('%s: audit %s' % (game, audited))
    if len(limits) > 1 or next(iter(limits)) != (control['request_timeout_seconds'], control['model_retries_per_action']):
        notes.append('%s: parts played with other time limits (seconds, retries -> parts): %s' % (game, limits))
    row = {'game': game.split('-')[0], 'stamp': stamp, 'state': {'done': 'ended', 'stopped': 'halted'}.get(state, state),
           'parts': len(parts), 'actions': actions, 'cap': cap, 'levels': levels, 'resets': resets, 'replies': replies,
           'replies_from_opus_5_5': models, 'accounts': accounts, 'audit': audited,
           'replies_sent_back': sent_back, 'replies_in_turns_cut_short': cut_short,
           'replies_in_turns_cut_short_sent_back': cut_short_sent_back, 'calls_past_the_time_limit': deadline,
           'calls_past_the_time_limit_that_ended_a_part': deadline_ended, 'calls_at_a_usage_limit': usage_limit,
           'calls_with_no_connection': connection, 'other_failures': other}
    return row, notes


def harness_notes():
    notes, seen = [], {}
    for stamp in STAMPS:
        plan = json.loads((W.REPORT / ('whole-plan-%s.json' % stamp)).read_text())
        for name in HARNESS:
            seen.setdefault(name, set()).add(plan['code_sha256'][name])
    for name in HARNESS:
        now = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if seen[name] != {now}:
            notes.append('harness file %s: the plans pin %d different versions, or not the file as it is now' % (name, len(seen[name])))
    changed = subprocess.run(['git', 'status', '--short', 'research/claude_arc_v1', 'agent', 'config'], cwd=ROOT,
                             capture_output=True, text=True).stdout.strip()
    if changed:
        notes.append('changed since the last commit: ' + changed.replace('\n', '; '))
    return notes


if __name__ == '__main__':
    control = json.loads(L.CONTROL.read_text())
    caps = W.CAPS
    games = json.loads((ROOT / '.cache/claude_arc_runs/opus55-competition-20261106T054112Z/summary.json').read_text())['selected_games']
    everything, rows = harness_notes(), []
    print('harness files as every plan pins them and unchanged in git: %s' % (not everything))
    for game in sorted(games):
        row, notes = check_game(game, caps[game.split('-')[0]], control)
        rows.append(row)
        everything += notes
        print(json.dumps(row))
    done = [r for r in rows if r.get('replies') is not None]
    total = {key: sum(r[key] for r in done) for key in (
        'actions', 'replies', 'replies_from_opus_5_5', 'replies_sent_back', 'replies_in_turns_cut_short',
        'replies_in_turns_cut_short_sent_back', 'calls_past_the_time_limit',
        'calls_past_the_time_limit_that_ended_a_part', 'calls_at_a_usage_limit', 'calls_with_no_connection',
        'other_failures')}
    print('games %d | replies %d, from %s alone %d | replies sent back %d (and %d of %d in turns cut short) '
          '| calls past the time limit %d (%d ended a part) | at a usage limit %d | no connection %d'
          % (len(done), total['replies'], MODEL, total['replies_from_opus_5_5'], total['replies_sent_back'],
             total['replies_in_turns_cut_short_sent_back'], total['replies_in_turns_cut_short'],
             total['calls_past_the_time_limit'], total['calls_past_the_time_limit_that_ended_a_part'],
             total['calls_at_a_usage_limit'], total['calls_with_no_connection']))
    print('not as planned (%d):' % len(everything))
    for note in everything:
        print('  -', note)
    if len(sys.argv) == 2:
        for row in rows:                        # which account answered, without the place its token is kept
            row['accounts'] = {('signed-in account' if name == 'signed-in' else 'second account'): count
                               for name, count in (row.get('accounts') or {}).items()}
        Path(sys.argv[1]).write_text(json.dumps({
            'what': 'Counts from the local run logs of the 25 whole-game runs with every layer on, the runs behind '
                    'the final scorecard. The logs are not in the repository.',
            'made_by': 'research/level_brief_v1/whole_verify.py',
            'how_counted': {
                'replies': 'replies the model returned, in the last part of each game (it holds the whole game)',
                'replies_sent_back': 'returned replies the harness refused and asked again; every one was refused '
                                     'because the list of 12 rules was full; counted in the last part only, because '
                                     'a later part repeats the saved replies and logs them again',
                'replies_in_turns_cut_short': 'replies returned in a turn that the end of a part cut short; the '
                                              'next part starts that turn again and does not repeat them, so they '
                                              'are outside the count of replies and outside the token totals',
                'calls_past_the_time_limit': 'calls cut off at the time limit with no reply and no usage; counted '
                                             'over all parts, since a later part does not repeat them',
                'calls_at_a_usage_limit': 'calls refused by the subscription\'s usage limit; counted over all parts',
                'calls_with_no_connection': 'calls that could not reach the service; counted over all parts'},
            'correction': 'Earlier counts of replies sent back (605 of 8,675 while three games were still playing; '
                          '696 of 11,111 for the finished runs) were made over all parts and counted a reply once '
                          'for every part that repeated it. They are withdrawn.',
            'games': len(done), 'totals': total,
            'share_of_replies_sent_back': round(total['replies_sent_back'] / total['replies'], 4),
            'per_game': rows, 'not_as_planned': everything}, indent=1) + '\n')
        print('written', sys.argv[1])
