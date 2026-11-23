"""Results of a whole-game test once every chain has finished, with a game that halted counted where it stands.

whole_games.py's own summary reads a game only when it ended (cap, win, or game over with no reset left). A game
can also halt: the model's reply to one turn takes longer than the harness waits, part after part (tr87 and bp35
on 2026-11-22). Such a game is counted here at the action it reached, which can only understate what the layers
do, and is marked "halted" with the reason. Nothing else differs from the summary.

    whole_results.py <out.json> <stamp>            the first eleven games (whole_games.py)
    whole_results.py <out.json> <stamp> rest       the second eleven (whole_games_rest.py)

Usage (project environment), from the repository root. No model call.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.level_brief_v1 import whole_games as W  # noqa: E402


def results(stamp):
    real = W.state_of
    last = {game: W.parts(game, stamp)[-1] for game in W.GAMES if W.parts(game, stamp)}
    states = {game: real(folder) for game, folder in last.items()}
    if 'running' in states.values():
        raise SystemExit('still playing: %s' % ', '.join(g for g, s in states.items() if s == 'running'))
    W.state_of = lambda folder: 'done' if real(folder) == 'stopped' else real(folder)
    try:
        value = W.summary(stamp)
    finally:
        W.state_of = real
    for row in value['runs']:
        game = next((g for g in last if g.startswith(row['game'])), None)
        if game is None:
            continue
        row['halted'] = states[game] == 'stopped'
        folders = W.parts(game, stamp)
        for part, folder in zip(row.get('parts', ()), folders):
            part['state'] = real(folder)
            part['seconds_a_call'] = next(e['config']['request_timeout_seconds'] for e in W.events_of(folder)
                                          if e['kind'] == 'configuration')
        if row['halted']:
            failed = [e for e in W.events_of(last[game]) if e['kind'] == 'game_failed']
            row['halted_because'] = failed[-1]['error'][:200] if failed else 'the part was cut off'
            row['state'] = 'halted'
    value['halted_games'] = [row['game'] for row in value['runs'] if row.get('halted')]
    return value


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] != 'rest'):
        raise SystemExit(__doc__)
    if len(sys.argv) == 4:
        from research.level_brief_v1 import whole_games_rest  # noqa: F401  (puts its games in the place of the first set's)
    value = results(sys.argv[2])
    Path(sys.argv[1]).write_text(json.dumps(value, indent=1) + '\n')
    for row in value['runs']:
        base = row.get('baseline') or {}
        print(json.dumps({k: row.get(k) for k in ('game', 'group', 'state', 'cap', 'actions', 'levels_completed', 'level_actions',
                                                   'score', 'model_replies')}
                         | {'baseline_levels': base.get('levels_completed'), 'baseline_actions': base.get('actions'),
                            'baseline_score': round(base['score'], 2) if base else None, 'parts': len(row.get('parts') or ())}))
    for name in ('all_eleven', 'never_used_in_design', 'used_in_design'):
        if name in value:
            print(name, json.dumps(value[name]))
    print('halted, counted where they stand:', ', '.join(value['halted_games']) or 'none')
