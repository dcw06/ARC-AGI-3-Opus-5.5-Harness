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
  - how often a call ran past its time limit, hit a usage limit, or had its reply sent back

and once: the harness files are the ones every plan pinned, and unchanged in git since the last commit.

    whole_verify.py            prints one line a game and a list of everything that is not as planned

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
    deadline = usage_limit = sent_back = other = 0
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
    for folder in parts:                        # failed calls are counted over all parts: a later part leaves them out
        for e in W.events_of(folder):
            if e['kind'] in ('model_failed_retrying', 'game_failed'):
                text = e.get('error') or ''
                if 'exceeded its deadline' in text:
                    deadline += 1
                elif 'limit' in text and 'resets' in text:
                    usage_limit += 1
                elif e['kind'] == 'model_failed_retrying' and e['error_type'] != 'TransportFailure':
                    sent_back += 1
                elif e['error_type'] not in ('KeyboardInterrupt',):
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
           'calls_past_the_time_limit': deadline, 'calls_at_a_usage_limit': usage_limit, 'replies_sent_back': sent_back,
           'other_failures': other}
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
    print('games %d | replies %d, from %s alone %d | calls past the time limit %d | at a usage limit %d | replies sent back %d'
          % (len(done), sum(r['replies'] for r in done), MODEL, sum(r['replies_from_opus_5_5'] for r in done),
             sum(r['calls_past_the_time_limit'] for r in done), sum(r['calls_at_a_usage_limit'] for r in done),
             sum(r['replies_sent_back'] for r in done)))
    print('not as planned (%d):' % len(everything))
    for note in everything:
        print('  -', note)
