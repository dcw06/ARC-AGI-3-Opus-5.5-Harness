"""Test the level brief. Local game files, no ARC service, no scorecard.

Each run first repeats the saved 6 November actions up to the start of the level that run stopped on (no
model call; every observation must hash to the saved one), then plays 100 new actions with its own choices.

    ledger   every memory layer plus the object ledger: the best set-up so far
    brief    the same, plus level_brief

Two groups of games, kept apart:

    designed on   ls20, tr87, cd82. The layer was thought out on these three levels. One brief run each, only
                  to see whether the layer does what it was designed for. These runs decide nothing.
    held out      ar25, ka59, lf52, sc25, sk48, sp80, wa30: every game with a local game file that no layer
                  was built on and whose replays were never studied. All seven, none picked. Both arms, two
                  runs each. The rule below is applied to these only.

A second batch, planned after the first was finished and read, to see whether its result holds up:

    second set    cn04, dc22, lp85, m0r0, r11l, re86, sb26, tn36, tu93: the nine games left that no layer was
                  built on and that no test of a layer has played, with copies of the official game files. All
                  nine, none picked. Both arms, two runs each, the layer's code unchanged. The same rule, applied
                  to these nine on their own. tn36 starts at the first action, because the saved run completed no
                  level of it: the brief has nothing to say there until a level is completed.

    runs.py check [first|second]               no model call
    runs.py rehearse <game id> <arm>           no model call: a whole run with a stand-in for the model, then the
                                               audit and the summary of it
    runs.py plan <stamp> [first|second]        writes the plan and the rule; to be run before the first call
    runs.py game <game id> <stamp> --send      the runs of one game, one after another. Run again after a stop:
                                               finished runs are skipped, a run that ended with a problem is
                                               repeated once under the same name with "-again" added
    runs.py summary <out.json> <stamp>         the rule is applied only when every run has ended without a problem

Usage (project environment), from the repository root. Set ARC_CLAUDE_TOKEN_FILE to put the runs on the
second subscription.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from agent.e1_policy import CompletionResult  # noqa: E402
from research.claude_arc_v1 import audit, config as C, policy  # noqa: E402
from research.claude_arc_v1.backends import Budget  # noqa: E402
from research.action_waste_v1 import level_runs as L  # noqa: E402
from research.action_waste_v1.local_game import check_against_saved_run, saved_run  # noqa: E402

# game -> saved actions repeated before play: the action at which the last level the saved run completed ended
DESIGNED_ON = {'ls20-9607627b': 60, 'tr87-cd924810': 61, 'cd82-fb555c5d': 35}
HELD_OUT = {'ar25-0c556536': 72, 'ka59-38d34dbb': 30, 'lf52-271a04aa': 8, 'sc25-635fd71a': 64,
            'sk48-d8078629': 65, 'sp80-589a99af': 69, 'wa30-ee6fef47': 95}
# tn36: the saved run completed no level, so play starts at the first action
SECOND = {'cn04-2fe56bfb': 52, 'dc22-fdcac232': 32, 'lp85-305b61c3': 100, 'm0r0-492f87ba': 71, 'r11l-495a7899': 77,
          're86-8af5384d': 56, 'sb26-7fbdac44': 91, 'tn36-ef4dde99': 0, 'tu93-0768757b': 98}
BATCHES = {'first': (DESIGNED_ON, HELD_OUT), 'second': ({}, SECOND)}      # batch -> (designed on, held out)
GAMES = {**DESIGNED_ON, **HELD_OUT, **SECOND}
ARMS = {'ledger': L.ARMS['ledger'], 'brief': {**L.ARMS['ledger'], 'level_brief': True}}
# which arm goes first alternates between the held-out games, so neither arm always runs earlier
ORDER = {game: ('ledger', 'brief') if n % 2 == 0 else ('brief', 'ledger')
         for held in (HELD_OUT, SECOND) for n, game in enumerate(held)}
NEW_ACTIONS, REPEATS = 100, 2
SET_UP = {'ledger': 'memory layers and object ledger', 'brief': 'memory layers, object ledger and level brief'}
REPORT = ROOT / 'reports/level_brief_v1'
RULE = ('Decided on %s. Measure: levels completed in the 100 new actions, summed over the '
        'two runs of an arm. "helps": the brief arm completes more levels in total than the ledger arm, is ahead in '
        'at least two games and behind in none. "hurts": it completes fewer in total. Anything else: "no detectable '
        'difference". %sNo run is repeated because of its '
        'result; a run that ends with a problem (backend error, failed audit) is reported and repeated once, before '
        'its result is looked at. Reported beside the verdict, not part of it: actions on the first level completed, '
        'game overs, actions that changed nothing, replies sent back, output tokens, and every brief and rule written.')
RULES = {'first': RULE % ('the seven held-out games only', 'The runs on the three designed-on games decide nothing. '),
         'second': RULE % ('the nine games of the second set only, on their own and not pooled with the first seven', '')}


def settings(game, arm):
    start = GAMES[game]
    resume = {'resume_events': L.SAVED, 'resume_actions': start} if start else {}     # nothing to repeat from 0
    return C.Config(**{**json.loads(L.CONTROL.read_text()), 'mode': 'online', 'games': [game.split('-')[0]], **resume,
                       'max_actions_per_game': start + NEW_ACTIONS, 'max_model_calls': NEW_ACTIONS + 80, **ARMS[arm]})


def name_of(game, arm, n, stamp, again=False):
    return 'brief-%s-%s-%d-%s%s' % (game.split('-')[0], arm, n, stamp, '-again' if again else '')


def state_of(folder):
    """'absent', 'running' (no end yet, written to within the last ten minutes), 'clean' or 'problem'."""
    path = Path(folder) / 'events.jsonl'
    if not path.exists():
        return 'absent'
    final = None
    with path.open() as handle:
        for line in handle:
            if '"kind":"summary"' in line:
                final = json.loads(line)['summary']
    if final is None:
        return 'running' if time.time() - path.stat().st_mtime < 600 else 'problem'
    return 'problem' if final['problems'] else 'clean'


def counted(game, arm, n, stamp):
    """The folder whose result counts for one planned run: the first attempt, or its one repeat if the first
    ended with a problem and the repeat was played."""
    first, again = L.RUNS / name_of(game, arm, n, stamp), L.RUNS / name_of(game, arm, n, stamp, again=True)
    return again if state_of(first) == 'problem' and state_of(again) != 'absent' else first


def runs_of(game):
    """(arm, run number) in the order they are played."""
    if game in DESIGNED_ON:
        return [('brief', 1)]
    return [(arm, n) for n in range(1, REPEATS + 1) for arm in ORDER[game]]


def check(batch='first'):
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    for game, start in {**BATCHES[batch][0], **BATCHES[batch][1]}.items():
        prefix = game.split('-')[0]
        _, steps = saved_run(game)
        done = [i + 1 for i, (_, after) in enumerate(steps)
                if after['levels_completed'] > (steps[i - 1][1]['levels_completed'] if i else 0)]
        differs, total = check_against_saved_run(game)
        print(game, '| local game against the saved run: %d actions, observations that differ: %s | play starts after '
              'action %d, the end of the last level the saved run completed: %s'
              % (total, differs or 'none', start, (done[-1] if done else 0) == start))
        requests = {}
        for arm in ARMS:
            first = L.SavedReplies(settings(game, arm), game, start, stop_after=0)
            L.play(game, arm, 'brief-check-%s-%s-%s' % (prefix, arm, stamp), first, settings(game, arm))
            requests[arm] = first.requests[0]
        mine, theirs = (json.loads(requests[arm]['messages'][1]['content']) for arm in ('brief', 'ledger'))
        looks = (mine['evidence'].get('things') or {}).get('looks', [])
        same_system = requests['brief']['messages'][0]['content'] == requests['ledger']['messages'][0]['content']
        for look in looks:
            look.pop('new', None)
        (mine['evidence'].get('things') or {}).pop('new_looks_not_listed', None)
        rules = mine['evidence'].pop('rules', None)         # the brief arm's own list, empty before the first reply
        won = mine['evidence'].pop('completed_level', {})   # and the last board of the level completed before
        print('   first request of the brief arm: system prompt equal to the ledger arm %s | evidence otherwise equal %s | '
              'rules list present and empty %s | completed board shown %s (level %s, %s frames returned) | brief asked for %s | '
              'rule notes offered %s | level %d'
              % (same_system, mine['evidence'] == theirs['evidence'], rules == [], bool(won.get('board')), won.get('level'),
                 won.get('frames_returned'), 'level_brief' in mine['output_contract'],
                 'rule_notes' in mine['output_contract'], mine['evidence']['current']['levels_completed'] + 1))


def code_hashes():
    files = ('research/claude_arc_v1/policy.py', 'research/claude_arc_v1/things.py', 'research/claude_arc_v1/config.py',
             'research/claude_arc_v1/run.py', 'research/level_brief_v1/runs.py', 'research/action_waste_v1/level_runs.py')
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}


def plan(stamp, batch='first'):
    designed, held = BATCHES[batch]
    value = {'written': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'stamp': stamp, 'batch': batch,
             'rule': RULES[batch], 'arms': ARMS, 'new_actions': NEW_ACTIONS,
             'designed_on': {game: {'starts_after_action': start, 'runs': runs_of(game)} for game, start in designed.items()},
             'held_out': {game: {'starts_after_action': start, 'runs': runs_of(game)} for game, start in held.items()},
             'wording': {'RULES_NOTE': policy.RULES_NOTE, 'brief_ask_with_the_completed_board': policy.brief_ask(2, True),
                         'brief_ask_without_it': policy.brief_ask(2, False), 'BRIEF_NOTE': policy.BRIEF_NOTE,
                         'NEW_NOTE': policy.NEW_NOTE},
             'rule_limit': policy.RULE_LIMIT, 'code_sha256': code_hashes()}
    REPORT.mkdir(parents=True, exist_ok=True)
    path = REPORT / ('plan-%s.json' % stamp)
    if path.exists():
        raise SystemExit('%s exists: a plan is written once, before the first call' % path)
    path.write_text(json.dumps(value, indent=1) + '\n')
    print('written', path)


def planned(stamp):
    """Refuse to send anything unless the plan was written for this stamp and for the code as it is now."""
    path = REPORT / ('plan-%s.json' % stamp)
    if not path.exists():
        raise SystemExit('write the plan first: runs.py plan %s' % stamp)
    value = json.loads(path.read_text())
    changed = sorted(name for name, digest in code_hashes().items() if value['code_sha256'].get(name) != digest)
    if changed:
        raise SystemExit('the code changed after the plan was written: %s' % ', '.join(changed))


def batch_of(stamp):
    """Which batch a stamp's plan was written for (plans older than the second set are the first)."""
    return json.loads((REPORT / ('plan-%s.json' % stamp)).read_text()).get('batch', 'first')


def game_batch(game, stamp):
    planned(stamp)
    if game not in {**BATCHES[batch_of(stamp)][0], **BATCHES[batch_of(stamp)][1]}:
        raise SystemExit('%s is not a game of the plan written for %s' % (game, stamp))
    for arm, n in runs_of(game):
        first, again = name_of(game, arm, n, stamp), name_of(game, arm, n, stamp, again=True)
        states = state_of(L.RUNS / first), state_of(L.RUNS / again)
        if 'running' in states:
            raise SystemExit('%s was written to in the last ten minutes and has not ended: it may still be playing. '
                             'Nothing was started.' % (first if states[0] == 'running' else again))
        if states[0] == 'clean' or states[1] != 'absent':
            continue                                  # finished, or already repeated once
        name = first if states[0] == 'absent' else again
        out = L.play(game, arm, name, config=settings(game, arm))
        if out['problems']:
            print('stopped: %s ended with a problem. Running this command again %s.'
                  % (name, 'goes on with the next run (a run is repeated only once)' if name == again
                     else 'repeats it once and goes on'), flush=True)
            return


class StandIn:
    """In place of the model, for rehearsals: fills every field the request asks for and cycles through the
    legal actions. Nothing it writes means anything."""

    def __init__(self, config):
        self.config, self.budget, self.last_record, self.requests, self.turn = config, Budget(config), None, [], 0

    def complete(self, request):
        reserved = self.budget.reserve()
        body = json.loads(request['messages'][1]['content'])
        self.requests.append(body)
        self.turn += 'previous_reply_rejected' not in body
        contract, legal = body['output_contract'], body['evidence']['current']['available_actions']
        action = legal[self.turn % len(legal)]
        reply = {'action': {'action_id': action, 'action_data': {'x': 30, 'y': 20 + self.turn % 20} if action == 6 else {}},
                 'hypotheses': []}
        text = 'stand-in text'
        for name in ('thing_check', 'lesson_check'):
            if name in contract:
                reply[name] = text
        if 'game_over_lesson' in contract:
            reply['game_over_lesson'] = {'rule': text, 'applies_when': text}
        if 'no_effect_lesson' in contract:
            reply['no_effect_lesson'] = {'rule': text, 'applies_when': text, 'replaces': 0}
        have = len(body['evidence'].get('rules') or [])
        if 'level_brief' in contract:
            reply['level_brief'] = {name: text for name in policy.BRIEF_LIMITS}
            reply['rule_notes'] = [{'rule': 'written on the first turn of a level', 'replaces': have if have >= policy.RULE_LIMIT else 0}]
        elif 'rule_notes' in contract and self.turn % 7 == 0:
            reply['rule_notes'] = [{'rule': 'rule from turn %d' % self.turn, 'replaces': have if have >= policy.RULE_LIMIT else 0}]
        if 'level_brief' in body['evidence'] and self.turn % 23 == 0:
            reply['level_brief'] = {**{name: text for name in policy.BRIEF_LIMITS}, 'why': 'replaced at turn %d' % self.turn}
        self.budget.settle(reserved, 10, 10)
        self.last_record = {'outcome': 'stand_in', 'usage': {'input_tokens': 10, 'output_tokens': 10}}
        return CompletionResult(json.dumps(reply), 10, 10, 0)


def rehearse(game, arm):
    """A whole run without the model. Fails loudly if the audit, the summary or the brief bookkeeping is off."""
    config, stamp = settings(game, arm), time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    backend, name = StandIn(config), 'brief-rehearsal-%s-%s-%s' % (game.split('-')[0], arm, stamp)
    out = L.play(game, arm, name, backend, config)
    audit.audit(L.RUNS / name)
    row = summary(L.RUNS / name)
    asked = [b['evidence']['current']['levels_completed'] + 1 for b in backend.requests if 'level_brief' in b['output_contract']]
    levels = sorted({b['evidence']['current']['levels_completed'] + 1 for b in backend.requests})
    assert not out['problems'] and state_of(L.RUNS / name) == 'clean', out
    assert row['new_actions'] == NEW_ACTIONS and row['set_up'] == SET_UP[arm], row
    # once on every level it had a turn on, except the game's first level, which has no brief
    assert asked == ([level for level in levels if level > 1] if arm == 'brief' else []), (asked, levels)
    assert len(row['briefs']) >= len(asked) and all(b['level'] in levels for b in row['briefs'])
    print('rehearsal of %s, %s arm: 100 actions, audit passes, summary reads, brief asked on levels %s, %d rule notes'
          % (game, arm, asked, len(row['rule_notes'])))


def summary(folder):
    folder = Path(folder)
    row = L.summary(folder)
    events = [json.loads(line) for line in (folder / 'events.jsonl').read_text().splitlines()]
    config = next(e['config'] for e in events if e['kind'] == 'configuration')
    asked, accepted, body, index = {}, {}, None, None
    for event in events:
        if event['kind'] == 'model_entered':
            body, index = json.loads(event['request']['messages'][1]['content']), event['action_index']
        elif event['kind'] == 'model_returned':
            try:        # the last reply to a turn is the one that was accepted: earlier ones were sent back
                asked[index], accepted[index] = body, json.loads(event['content'])
            except ValueError:
                continue
    briefs, rules = [], []
    for index in sorted(accepted):
        body, reply, at = asked[index], accepted[index], index + 1 - row['started_after_action']
        due = 'level_brief' in body['output_contract']
        if reply.get('level_brief') and (due or 'level_brief' in body['evidence']):
            briefs.append({'at_action': at, 'level': body['evidence']['current']['levels_completed'] + 1,
                           'asked_for': due, **reply['level_brief']})
        if 'rule_notes' in body['output_contract']:
            rules.extend({'at_action': at, **note} for note in reply.get('rule_notes') or ())
    row.update({'arm': 'brief' if config.get('level_brief') else 'ledger',
                'set_up': SET_UP['brief' if config.get('level_brief') else 'ledger'],
                'state': state_of(folder), 'briefs': briefs, 'rule_notes': rules})
    return row


def verdict(rows, held=HELD_OUT):
    """The rule, applied to the held-out games of one batch."""
    levels = {}
    for row in rows:
        game = next(g for g in GAMES if g.startswith(str(row['game']).split('-')[0]))
        if game in held:
            levels.setdefault(game, {'ledger': 0, 'brief': 0})[row['arm']] += row['levels_completed_in_new_actions']
    total = {arm: sum(v[arm] for v in levels.values()) for arm in ('ledger', 'brief')}
    ahead = sum(v['brief'] > v['ledger'] for v in levels.values())
    behind = sum(v['brief'] < v['ledger'] for v in levels.values())
    if total['brief'] > total['ledger'] and ahead >= 2 and not behind:
        word = 'helps'
    elif total['brief'] < total['ledger']:
        word = 'hurts'
    else:
        word = 'no detectable difference'
    return {'verdict': word, 'levels_completed': total, 'games_ahead': ahead, 'games_behind': behind, 'by_game': levels}


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'check' and len(sys.argv) in (2, 3):
        check(*sys.argv[2:])
    elif command == 'plan' and len(sys.argv) in (3, 4):
        plan(*sys.argv[2:])
    elif command == 'game' and len(sys.argv) == 5 and sys.argv[4] == '--send':
        game_batch(sys.argv[2], sys.argv[3])
    elif command == 'rehearse' and len(sys.argv) == 4:
        rehearse(sys.argv[2], sys.argv[3])
    elif command == 'summary' and len(sys.argv) == 4:
        stamp, rows, not_counted, designed_open, problem_runs = sys.argv[3], [], [], [], []
        designed, held = BATCHES[batch_of(stamp)]
        for game in {**designed, **held}:
            for arm, n in sorted(runs_of(game)):
                first, folder = L.RUNS / name_of(game, arm, n, stamp), counted(game, arm, n, stamp)
                if folder != first:
                    problem_runs.append(first.name)                  # the attempt that was repeated: reported, not counted
                state = state_of(folder)
                if state in ('clean', 'problem'):
                    rows.append(summary(folder))
                reason = state if state != 'clean' else None if rows[-1]['audit'] == 'passes' else rows[-1]['audit']
                if reason:
                    (not_counted if game in held else designed_open).append('%s: %s' % (folder.name, reason))
        result = {'batch': batch_of(stamp), 'runs': rows, 'runs_repeated_after_a_problem': problem_runs,
                  'held_out_runs_that_cannot_be_counted': not_counted, 'designed_on_runs_not_finished': designed_open,
                  'rule': RULES[batch_of(stamp)], 'held_out': verdict(rows, held) if not not_counted else
                  'not applied: every held-out run must have ended without a problem and pass the audit'}
        Path(sys.argv[2]).write_text(json.dumps(result, indent=1) + '\n')
        for row in rows:
            print(json.dumps({k: v for k, v in row.items() if k not in (
                'lessons', 'game_over_lessons', 'thing_notes', 'things_by_level', 'briefs', 'rule_notes')}))
        print('repeated after a problem:', problem_runs or 'none', '| designed-on runs not finished:', designed_open or 'none',
              '| held-out runs that cannot be counted:', len(not_counted), not_counted[:3])
        print(json.dumps(result['held_out']))
    else:
        raise SystemExit(__doc__)
