"""Results of a whole-game test once every chain has finished, with a game that halted counted where it stands.

whole_games.py's own summary reads a game only when it ended (cap, win, or game over with no reset left). A game
can also halt: the model's reply to one turn takes longer than the harness waits, part after part (tr87 and bp35
on 2026-11-22). Such a game is counted here at the action it reached, which can only understate what the layers
do, and is marked "halted" with the reason. Nothing else differs from the summary.

    whole_results.py <out.json> <stamp>            the first eleven games (whole_games.py)
    whole_results.py <out.json> <stamp> rest       the second eleven (whole_games_rest.py)
    whole_results.py <out.json> <stamp> last       dc22 and re86 (whole_games_last.py; wa30 was started again
                                                   under its own stamp and is left out here)
    whole_results.py <out.json> <stamp> official   wa30 (whole_games_official.py)

Usage (project environment), from the repository root. No model call.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.level_brief_v1 import whole_games as W  # noqa: E402


def compare(group):
    """whole_games.py's comparison of a group of games with the baseline, for a group of any size."""
    if not group:
        return None
    mine, theirs = sum(r['levels_completed'] for r in group), sum(r['baseline']['levels_completed'] for r in group)
    my_score = sum(r['score'] for r in group) / len(group)
    their_score = sum(r['baseline']['score'] for r in group) / len(group)
    word = 'better' if mine > theirs and my_score > their_score else 'worse' if mine < theirs and my_score < their_score else 'mixed'
    return {'games': len(group), 'levels_completed': {'layers': mine, 'baseline': theirs},
            'mean_game_score': {'layers': round(my_score, 2), 'baseline': round(their_score, 2)}, 'reading': word,
            'actions': {'layers': sum(r['actions'] for r in group), 'baseline': sum(r['baseline']['actions'] for r in group)}}


def results(stamp, small=False):
    """small: a set too small for whole_games.py's own overall comparison, which divides by the size of the
    'used in design' group (none of the last three games is in it). The comparison is then made here."""
    real = W.state_of
    last = {game: W.parts(game, stamp)[-1] for game in W.GAMES if W.parts(game, stamp)}
    states = {game: real(folder) for game, folder in last.items()}
    if 'running' in states.values():
        raise SystemExit('still playing: %s' % ', '.join(g for g, s in states.items() if s == 'running'))
    W.state_of = lambda folder: 'done' if real(folder) == 'stopped' else real(folder)
    groups = W.GROUPS
    if small:       # a game that never started keeps whole_games.py from making its own overall comparison
        W.GROUPS = {**groups, 'none': ('none-none',)}
    try:
        value = W.summary(stamp)
    finally:
        W.state_of, W.GROUPS = real, groups
    if small:
        value['runs'] = [row for row in value['runs'] if row['group'] != 'none']
        value['games_not_ended'] = [row['game'] for row in value['runs'] if row['state'] != 'done']
        if not value['games_not_ended']:
            value['all_games_of_this_set'] = compare(value['runs'])
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
    if len(sys.argv) not in (3, 4) or (len(sys.argv) == 4 and sys.argv[3] not in ('rest', 'last', 'official')):
        raise SystemExit(__doc__)
    which = sys.argv[3] if len(sys.argv) == 4 else 'first'
    if which == 'rest':
        from research.level_brief_v1 import whole_games_rest  # noqa: F401  (puts its games in the place of the first set's)
    elif which == 'last':
        from research.level_brief_v1 import whole_games_last  # noqa: F401
        W.GROUPS = {'one': W.GROUPS['one']}          # wa30's counted run is under the stamp of whole_games_official.py
        W.GAMES = {game: W.GAMES[game] for game in W.GROUPS['one']}
    elif which == 'official':
        from research.level_brief_v1 import whole_games_official  # noqa: F401
    value = results(sys.argv[2], small=which in ('last', 'official'))
    Path(sys.argv[1]).write_text(json.dumps(value, indent=1) + '\n')
    for row in value['runs']:
        base = row.get('baseline') or {}
        print(json.dumps({k: row.get(k) for k in ('game', 'group', 'state', 'cap', 'actions', 'levels_completed', 'level_actions',
                                                   'score', 'model_replies')}
                         | {'baseline_levels': base.get('levels_completed'), 'baseline_actions': base.get('actions'),
                            'baseline_score': round(base['score'], 2) if base else None, 'parts': len(row.get('parts') or ())}))
    for name in ('all_eleven', 'never_used_in_design', 'used_in_design', 'all_games_of_this_set'):
        if name in value:
            print(name, json.dumps(value[name]))
    print('halted, counted where they stand:', ', '.join(value['halted_games']) or 'none')
