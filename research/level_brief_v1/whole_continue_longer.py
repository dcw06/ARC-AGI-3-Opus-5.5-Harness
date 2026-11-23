"""Continue one game of a whole-game test (whole_games.py) with a longer time limit for each model call.

For a game that halted because the model's reply to one turn takes longer than the harness waits (240 seconds):
tr87 on 2026-11-22, at its 217th action, where 8 of 9 calls ran past the limit. The user chose to continue it
("You can continue tr87", 2026-11-22). Nothing the model is sent changes: the part repeats the stopped part from
its saved replies, every rebuilt request must equal the saved one, and the model is asked again from the action
that was not finished. Only two settings differ from the plan, and neither is shown to the model:

    request_timeout_seconds    240 -> the number given (400)
    model_retries_per_action   2 -> 1     (the harness requires the longest wait for one action, retries
                                          included, to stay under 14 minutes)

So this game has more time to think on each action than the baseline run had. Whoever reads its result should
know that; whole_games.py's summary reads the last part of the game as usual.

    whole_continue_longer.py <game id> <stamp> <seconds> --send
        the next part of the game. Prints a line starting "done:", "stopped:" (run again) or "halted:" (two parts
        in a row under the longer limit added no action, or the part before could not be repeated)

Usage (project environment), from the repository root. Set ARC_CLAUDE_TOKEN_FILE to use the second subscription.
"""
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.claude_arc_v1.backends import Budget, ClaudeCodeBackend  # noqa: E402
from research.action_waste_v1 import level_runs as L  # noqa: E402
from research.level_brief_v1 import whole_games as W  # noqa: E402

RETRIES = 1


def limit_of(folder):
    return next(e['config']['request_timeout_seconds'] for e in W.events_of(folder) if e['kind'] == 'configuration')


def next_part(game, stamp, seconds, real=None):
    folders = W.parts(game, stamp)
    states = [W.state_of(folder) for folder in folders]
    if not folders:
        raise SystemExit('%s has no part yet: start it with whole_games.py' % game)
    if 'running' in states:
        raise SystemExit('%s was written to in the last ten minutes and has not ended: it may still be playing. '
                         'Nothing was started.' % folders[states.index('running')].name)
    if states[-1] == 'done':
        print('done: %s has ended (%s)' % (game, folders[-1].name), flush=True)
        return 'done'
    if len(folders) >= W.MOST_PARTS + 10:
        print('halted: %s has %d parts and has not ended' % (game, len(folders)), flush=True)
        return 'halted'
    counts = [W.actions_in(folder) for folder in folders]
    stuck = [folder for folder, count in zip(folders, counts) if count == counts[-1]]    # parts that ended where the last did
    if sum(limit_of(folder) == seconds for folder in stuck) >= 2:
        print('halted: two parts of %s with %d seconds a call added no action' % (game, seconds), flush=True)
        return 'halted'
    if any(e['kind'] == 'game_failed' and e['error_type'] == 'NotTheSameRequest' for e in W.events_of(folders[-1])):
        print('halted: %s could not repeat the part before it' % folders[-1].name, flush=True)
        return 'halted'
    saved, before = W.replies_of(folders[-1]), W.actions_in(folders[-1])
    config = replace(W.settings(game), request_timeout_seconds=seconds, model_retries_per_action=RETRIES)
    backend = W.Continued(config, saved, real or ClaudeCodeBackend(config, Budget(config)))
    name = W.name_of(game, stamp, len(folders))
    L.play(game, 'brief', name, backend, config)
    if backend.given == len(saved) and not W.same_actions(folders[-1], L.RUNS / name, before):
        print('halted: %s repeated the part before it with different actions' % name, flush=True)
        return 'halted'
    state = W.state_of(L.RUNS / name)
    print('%s: %s, %d actions, %d saved replies given back, %d seconds a call' % (
        state, name, W.actions_in(L.RUNS / name), backend.given, seconds), flush=True)
    return state


if __name__ == '__main__':
    if len(sys.argv) != 5 or sys.argv[4] != '--send' or sys.argv[1] not in W.GAMES:
        raise SystemExit(__doc__)
    W.planned(sys.argv[2])          # the layers and the runner are still the ones the plan pins
    next_part(sys.argv[1], sys.argv[2], int(sys.argv[3]))
