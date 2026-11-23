"""Whole games played on the official copies of the game files.

Why this file exists. On 2026-11-22, while the scorecard replay was being prepared, a local replay of lf52 did not
return the recorded observation at action 309, and local_game.py turned out to look first in an older folder of
game files (reports/runs/phase4-v2-assets) whose copies of 15 games are not byte for byte the files the ARC toolkit
downloads. wa30 had just started on its older copy, so it was stopped after 17 actions and started again here, on
the toolkit's copy.

The older copies were then checked and are NOT a different game. They differ from the toolkit's only by a licence
comment at the top of the official file and one or two helper functions (_get_hidden_state, _get_valid_actions) in
the older one, which the engine never calls; every recorded action of every finished run returns the recorded
board on the toolkit's copies. The lf52 difference has another cause: one animated action on its level 6 gives
different in-between frames from one process to the next, while the board it ends on is the same (25 of its 1,350
actions; see replay_scorecard.py). So the restart of wa30 was a precaution that turned out not to be needed, and
its discarded first 17 actions are reported as such.

Here the toolkit's copies (.cache/local_games/environment_files) are looked in first. Nothing else differs from
whole_games.py, which is used unchanged, and local_game.py is not edited, so the plans of the other sets still
hold. (This note was corrected after wa30 had ended; while it played, the file was pinned by its plan.)

    official    wa30    the signed-in account, from the first action

    whole_games_official.py check                       no model call
    whole_games_official.py plan <stamp>                writes the plan; to be run before the first call
    whole_games_official.py game <game id> <stamp> --send

Usage (project environment), from the repository root.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.action_waste_v1 import local_game  # noqa: E402

OFFICIAL = ROOT / '.cache/local_games/environment_files'
TOOLKIT = Path.home() / '.cache/arc-skill/arcade/environment_files'       # what the ARC toolkit downloaded; read only
local_game.FILES = (OFFICIAL,) + tuple(folder for folder in local_game.FILES if folder != OFFICIAL)

from research.level_brief_v1 import whole_games_last as X  # noqa: E402  (the rule of the last three games)
from research.level_brief_v1 import whole_games as W  # noqa: E402

GROUPS = {'official': ('wa30-ee6fef47',)}
ACCOUNTS = {'official': 'the signed-in account'}
W.GROUPS, W.ACCOUNTS = GROUPS, ACCOUNTS
W.GAMES = {game: W.CAPS[game.split('-')[0]] for games in GROUPS.values() for game in games}
_hashes_before = W.code_hashes


def game_file_hashes():
    return {'game file ' + game: hashlib.sha256(local_game.game_file(game).read_bytes()).hexdigest() for game in W.GAMES}


W.code_hashes = lambda: {**_hashes_before(), 'research/level_brief_v1/whole_games_official.py':
                         hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), **game_file_hashes()}


def check():
    for game, cap in W.GAMES.items():
        prefix, version = game.split('-')
        used, toolkit = local_game.game_file(game), TOOLKIT / prefix / version / (prefix + '.py')
        differs, total = local_game.check_against_saved_run(game)
        print('%s | file %s | equal to the toolkit\'s copy: %s | against the saved run: %d actions, observations that '
              'differ: %s | cap %d' % (game, used.relative_to(ROOT), used.read_bytes() == toolkit.read_bytes(), total,
                                       differs or 'none', cap))
        assert used.is_relative_to(OFFICIAL) and used.read_bytes() == toolkit.read_bytes() and not differs


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'check' and len(sys.argv) == 2:
        check()
    elif command == 'plan' and len(sys.argv) == 3:
        check()
        W.plan(sys.argv[2])
    elif command == 'game' and len(sys.argv) == 5 and sys.argv[4] == '--send':
        if sys.argv[2] not in W.GAMES:
            raise SystemExit('%s is not a game of this set' % sys.argv[2])
        W.planned(sys.argv[3])
        W.next_part(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
