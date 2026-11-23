"""The whole-game test (whole_games.py) on the last three games, asked for by the user on 2026-11-22 ("run the
remaining games under two batches"): dc22, re86 and wa30, the three largest, which the first two sets left out.
With them all 25 games have been played once from the first action with every layer.

    one    dc22, re86    the second subscription
    two    wa30          the signed-in account

As whole_games_rest.py, this file holds only the games, the accounts and the rule, puts them in the place of
whole_games.py's own and uses whole_games.py unchanged.

    whole_games_last.py check                       no model call
    whole_games_last.py rehearse <game id>          no model call
    whole_games_last.py plan <stamp>                writes the plan; to be run before the first call
    whole_games_last.py game <game id> <stamp> --send
    whole_games_last.py summary <out.json> <stamp>

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

GROUPS = {'one': ('dc22-fdcac232', 're86-8af5384d'), 'two': ('wa30-ee6fef47',)}
ACCOUNTS = {'one': 'the second subscription', 'two': 'the signed-in account'}
USED_IN_DESIGN = ()          # no layer was designed on any of the three
RULE = ('The last three games, one run each with the layers on, beside the baseline run of the same game at the same '
        'cap. Per game: levels completed, and the game score by the scorecard rule (replay_scorecard.game_score with '
        'the human counts of the official scorecard). Overall "better": more levels completed in total and a higher '
        'mean game score than the baseline. "worse": fewer levels in total and a lower mean game score. Anything '
        'else: "mixed". One run a game on each side, played on different days: a difference in a single game may be '
        'chance. No game is played again because of its result. A game that stops early is continued from its own '
        'saved replies; one that halts because a reply keeps running past the time limit is counted where it stands.')

# whole_games.py reads these names when it plans, plays and summarises: here they stand for this set of games
W.GROUPS, W.ACCOUNTS, W.USED_IN_DESIGN, W.RULE = GROUPS, ACCOUNTS, USED_IN_DESIGN, RULE
W.GAMES = {game: W.CAPS[game.split('-')[0]] for games in GROUPS.values() for game in games}
_hashes_of_the_runner = W.code_hashes
W.code_hashes = lambda: {**_hashes_of_the_runner(), 'research/level_brief_v1/whole_games_last.py':
                         hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def check():
    reference = W.baseline()
    for group, games in GROUPS.items():
        total = sum(W.GAMES[game] for game in games)
        assert total <= W.GROUP_BUDGET, (group, total)
        print('%s (%s): %s | %d actions at most, limit %d' % (group, ACCOUNTS[group],
              ', '.join('%s %d' % (game.split('-')[0], W.GAMES[game]) for game in games), total, W.GROUP_BUDGET))
    assert len(W.GAMES) == 3 and set(W.GAMES) == set(reference), sorted(W.GAMES)
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
            raise SystemExit('%s is not one of the three games of this set' % sys.argv[2])
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
