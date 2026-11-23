"""Whole games played on the official copies of the game files.

Found on 2026-11-22 while preparing the scorecard replay: local_game.py looks first in an older folder of game
files (reports/runs/phase4-v2-assets), and for 15 of the 25 games the copy there is not the file the ARC toolkit
downloads, though the version in its name is the same. Replayed on the official copies, the recorded actions of
the finished whole-game runs return every recorded board in all of those games but lf52, where the boards differ
from action 309 on. So only lf52 after action 308 was played on a different game. wa30 had just started on its
older copy and was stopped after 17 actions.

Here the official copies (.cache/local_games/environment_files, byte for byte the toolkit's) are looked in first.
Nothing else differs from whole_games.py, which is used unchanged, and local_game.py is not edited, so the plans
of the other sets still hold.

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
