"""The whole-game test (whole_games.py) on eleven more games: the same layers, the same rules of play, the same way
of continuing a stopped game. Asked for by the user on 2026-11-21, to start when the first eleven games have ended.

Two batches, each played once from the first action with every memory layer, the object ledger and the level
brief, up to the cap the baseline had, beside the baseline run of the same game:

    won        ar25, ft09, lp85, r11l, s5i5, sb26, vc33    the seven games the baseline won. The layers cannot add
                                                           a level here; they can lose one, or use fewer actions
    not-won    cn04, sp80, tu93, su15                      four of the seven the baseline did not win and scored
                                                           40 or more on (the user left out dc22, re86 and wa30)

This file holds only what differs from whole_games.py: the games, the accounts and the rule. It puts them in the
place of whole_games.py's own, which is then used unchanged, so whole_games.py stays as the plan of the first
eleven games pins it.

    whole_games_rest.py check                       no model call
    whole_games_rest.py rehearse <game id>          no model call
    whole_games_rest.py plan <stamp>                writes the plan; to be run before the first call
    whole_games_rest.py game <game id> <stamp> --send
    whole_games_rest.py summary <out.json> <stamp>

Usage (project environment), from the repository root.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.action_waste_v1 import level_runs as L  # noqa: E402
from research.action_waste_v1.local_game import check_against_saved_run  # noqa: E402
from research.level_brief_v1 import whole_games as W  # noqa: E402

GROUPS = {'won': ('ar25-0c556536', 's5i5-18d95033', 'vc33-5430563c', 'lp85-305b61c3', 'r11l-495a7899',
                  'sb26-7fbdac44', 'ft09-0d8bbf25'),
          'not-won': ('cn04-2fe56bfb', 'sp80-589a99af', 'tu93-0768757b', 'su15-1944f8ab')}
ACCOUNTS = {'won': 'the second subscription', 'not-won': 'the signed-in account'}
# the no-effect lessons were designed on these three; no layer was designed on the other eight
USED_IN_DESIGN = ('s5i5', 'su15', 'vc33')
RULE = ('Eleven more games, one run each with the layers on, beside the baseline run of the same game at the same cap. '
        'Per game: levels completed, and the game score by the scorecard rule (replay_scorecard.game_score with the '
        'human counts of the official scorecard). Read apart for the two batches. The seven games the baseline won: '
        'the layers cannot complete more levels, so the question is whether they lose any ("worse": fewer levels in '
        'total) and whether the mean game score is higher or lower. The four it did not win: "better" if more levels '
        'in total and a higher mean game score than the baseline, "worse" if fewer levels and a lower mean score, '
        'anything else "mixed". The three games a layer was designed on (s5i5, su15, vc33) are named in the results. '
        'One run a game on each side, played on different days: a difference in a single game may be chance. No game '
        'is played again because of its result. A game that stops early is continued from its own saved replies.')

# whole_games.py reads these names when it plans, plays and summarises: here they stand for this set of games
W.GROUPS, W.ACCOUNTS, W.USED_IN_DESIGN, W.RULE = GROUPS, ACCOUNTS, USED_IN_DESIGN, RULE
W.GAMES = {game: W.CAPS[game.split('-')[0]] for games in GROUPS.values() for game in games}
_hashes_of_the_runner = W.code_hashes
W.code_hashes = lambda: {**_hashes_of_the_runner(), 'research/level_brief_v1/whole_games_rest.py':
                         hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def check():
    reference = W.baseline()
    for group, games in GROUPS.items():
        total = sum(W.GAMES[game] for game in games)
        assert total <= W.GROUP_BUDGET, (group, total)
        print('%s (%s): %s | %d actions at most, limit %d' % (group, ACCOUNTS[group],
              ', '.join('%s %d' % (game.split('-')[0], W.GAMES[game]) for game in games), total, W.GROUP_BUDGET))
    assert len(W.GAMES) == 11 and set(W.GAMES) == set(reference), sorted(W.GAMES)
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    for game, cap in W.GAMES.items():
        differs, total = check_against_saved_run(game)
        name = 'whole-check-%s-%s' % (game.split('-')[0], stamp)
        L.play(game, 'brief', name, W.Continued(W.settings(game), [], None), W.settings(game))
        events = W.events_of(L.RUNS / name)
        body = json.loads(next(e for e in events if e['kind'] == 'model_entered')['request']['messages'][1]['content'])
        config = next(e for e in events if e['kind'] == 'configuration')['config']
        print('%s | local game against the saved run: %d actions, observations that differ: %s | cap %d, the baseline '
              'played %d and completed %d of %d levels | first request: level %d, rules list present and empty %s, '
              'things listed %s | layers on: %s | resets allowed %d'
              % (game, total, differs or 'none', cap, reference[game]['actions'], reference[game]['levels_completed'],
                 reference[game]['levels'], body['evidence']['current']['levels_completed'] + 1,
                 body['evidence'].get('rules') == [], 'things' in body['evidence'],
                 all(config[name] for name in ('level_brief', 'object_ledger', 'no_effect_lessons', 'game_over_lessons',
                                               'lesson_check')), config['resets_per_game']))


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'check' and len(sys.argv) == 2:
        check()
    elif command == 'rehearse' and len(sys.argv) == 3:
        W.rehearse(sys.argv[2])
    elif command == 'plan' and len(sys.argv) == 3:
        W.plan(sys.argv[2])
    elif command == 'game' and len(sys.argv) == 5 and sys.argv[4] == '--send':
        if sys.argv[2] not in W.GAMES:
            raise SystemExit('%s is not one of the eleven games of this set' % sys.argv[2])
        W.planned(sys.argv[3])
        W.next_part(sys.argv[2], sys.argv[3])
    elif command == 'summary' and len(sys.argv) == 4:
        value = W.summary(sys.argv[3])
        done = [row for row in value['runs'] if row['state'] == 'done']
        for group in GROUPS:
            rows = [row for row in done if row['group'] == group]
            if rows and len(rows) == len(GROUPS[group]):
                value[group] = {
                    'games': len(rows),
                    'levels_completed': {'layers': sum(r['levels_completed'] for r in rows),
                                         'baseline': sum(r['baseline']['levels_completed'] for r in rows)},
                    'mean_game_score': {'layers': round(sum(r['score'] for r in rows) / len(rows), 2),
                                        'baseline': round(sum(r['baseline']['score'] for r in rows) / len(rows), 2)},
                    'actions': {'layers': sum(r['actions'] for r in rows), 'baseline': sum(r['baseline']['actions'] for r in rows)}}
        Path(sys.argv[2]).write_text(json.dumps(value, indent=1) + '\n')
        for row in value['runs']:
            base = row.get('baseline') or {}
            print(json.dumps({k: row.get(k) for k in ('game', 'group', 'state', 'cap', 'actions', 'levels_completed',
                                                       'level_actions', 'score', 'model_replies')}
                             | {'baseline_levels': base.get('levels_completed'), 'baseline_score': base.get('score'),
                                'parts': len(row.get('parts') or ())}))
        for name in GROUPS:
            if name in value:
                print(name, json.dumps(value[name]))
        if value['games_not_ended']:
            print('not ended yet:', ', '.join(value['games_not_ended']))
    else:
        raise SystemExit(__doc__)
