# ARC-AGI-3 Opus 5.5 Harness

A harness that plays the 25 public [ARC-AGI-3](https://arcprize.org) games with Claude Opus 5.5. The model is
asked once per action, has no tools, and gets no hints about any game. On top of a plain baseline the harness adds
four layers of memory and evidence that the model builds for itself while it plays.

With the layers on, the official scorecard score goes from **46.20** to **85.37**, under the same action cap
per game.

## Results

| | Baseline | With the layers |
|---|---|---|
| Official score | 46.20 | 85.37 |
| Levels completed | 125 of 183 | 166 of 183 |
| Games won | 7 of 25 | 17 of 25 |
| Actions used | 16,560 | 10,686 |
| Tokens, input and output | 256.5M | 228.3M |

- Baseline scorecard: https://arcprize.org/scorecards/0f882c2e-0451-41bd-86c5-211a54785c56
- Layered scorecard: https://arcprize.org/scorecards/96932ddf-ab6a-4354-94b2-9644447dae14

The layered runs used 35.5% fewer actions and 11.0% fewer tokens in total. Each action costs more with the layers
(about 42% more input), but far fewer actions are needed. Token counts leave out calls that were cut off at the
time limit, which report no usage.

Scores are ARC's own (competition mode). The games were played on local copies of the public game files, and each
scorecard was then made by sending the recorded actions to the ARC service, with no model call; the service has to
return the recorded board after every action.

### Per game

| Game | Baseline: levels | Baseline: actions | Baseline: score | Layers: levels | Layers: actions | Layers: score | How the layered run ended |
|---|---|---|---|---|---|---|---|
| ar25 | 8 of 8 | 393 | 100.0 | 8 of 8 | 263 | 100.0 | won |
| bp35 | 4 of 9 | 700 | 3.6 | 8 of 9 | 397 | 80.0 | halted on slow model calls |
| cd82 | 2 of 6 | 200 | 14.3 | 6 of 6 | 112 | 100.0 | won |
| cn04 | 4 of 6 | 800 | 47.6 | 6 of 6 | 303 | 100.0 | won |
| dc22 | 4 of 6 | 1,250 | 40.3 | 6 of 6 | 619 | 100.0 | won |
| ft09 | 6 of 6 | 75 | 100.0 | 6 of 6 | 75 | 100.0 | won |
| g50t | 2 of 7 | 900 | 10.7 | 7 of 7 | 359 | 100.0 | won |
| ka59 | 3 of 7 | 750 | 10.2 | 7 of 7 | 508 | 100.0 | won |
| lf52 | 4 of 10 | 1,350 | 8.5 | 5 of 10 | 1,350 | 27.3 | action cap |
| lp85 | 8 of 8 | 124 | 100.0 | 8 of 8 | 107 | 100.0 | won |
| ls20 | 2 of 7 | 800 | 10.7 | 6 of 7 | 800 | 70.9 | action cap |
| m0r0 | 2 of 6 | 1,150 | 14.3 | 6 of 6 | 260 | 100.0 | won |
| r11l | 6 of 6 | 159 | 92.3 | 6 of 6 | 92 | 100.0 | won |
| re86 | 6 of 8 | 1,300 | 58.3 | 8 of 8 | 655 | 100.0 | won |
| s5i5 | 8 of 8 | 486 | 85.3 | 6 of 8 | 201 | 58.3 | halted on slow model calls |
| sb26 | 8 of 8 | 127 | 100.0 | 8 of 8 | 125 | 100.0 | won |
| sc25 | 3 of 6 | 350 | 27.1 | 3 of 6 | 350 | 28.6 | action cap |
| sk48 | 4 of 8 | 1,100 | 15.9 | 8 of 8 | 494 | 100.0 | won |
| sp80 | 4 of 6 | 550 | 47.6 | 6 of 6 | 447 | 99.2 | won |
| su15 | 7 of 9 | 400 | 45.9 | 9 of 9 | 291 | 94.7 | won |
| tn36 | 4 of 7 | 350 | 19.1 | 6 of 7 | 350 | 75.0 | action cap |
| tr87 | 4 of 6 | 450 | 27.1 | 4 of 6 | 259 | 47.6 | halted on slow model calls |
| tu93 | 8 of 9 | 500 | 62.2 | 9 of 9 | 200 | 100.0 | won |
| vc33 | 7 of 7 | 446 | 72.3 | 7 of 7 | 219 | 100.0 | won |
| wa30 | 7 of 9 | 1,850 | 41.4 | 7 of 9 | 1,850 | 52.7 | action cap |

Every game score in this table equals the one on the official scorecard. Two earlier scorecards were taken on 22 November 2026 while games were still playing (82.56 and 84.14); their records are in `reports/level_brief_v1/data/`.

Three games halted before their cap because the model's reply to one turn kept running past the harness's
240-second limit (tr87, bp35, s5i5). They are counted where they stopped. s5i5 is the one game that did worse than
the baseline, which had won it.

## How it works

**Baseline.** Every turn the model receives the board as text, the last eight transitions, and up to eight
hypotheses it wrote itself. It returns one action and its updated hypotheses as JSON. The harness checks that the
action is legal and sends it. Nothing is kept between games.

**The four layers.** Each is a switch in the configuration and all are off in the baseline.

| Layer | Switch | What it adds |
|---|---|---|
| Lessons after a game over | `game_over_lessons` | After a game over the model writes a general lesson. It stays in every later request. |
| Lessons after an action that changed nothing | `no_effect_lessons`, `lesson_check` | When an action leaves the board as it was, the model explains why within a few turns, keeps the lesson, and checks each later action against its lessons. |
| Object ledger | `object_ledger` | The harness lists the things on the board, grouped by look, with what has happened at each. The model notes what a look does and says which thing it is going for. |
| Kept rules and a level brief | `level_brief` | Up to 12 rules the model records as confirmed are kept for the whole game. On the first turn of each new level it is shown the board that completed the level before and writes a short brief: what completed it, what is different now, why, and what to try first. |

Everything in these layers is written by the model from its own play, or derived by the harness from the boards.
None of it is checked against the game's real rules.

## How the comparison was made

- All 25 public games, the same action cap per game on both sides (the human action count for the game), the same
  model and harness code, one run per game.
- The baseline is the harness with every layer off. The layered runs start each game from its first action.
- A game that was interrupted (usage limit, slow calls, lost connection) continues from its own saved replies:
  each rebuilt request must equal the saved one before the model is asked again. No game was played again because
  of its result.

Limits to keep in mind:

- These are the public games, and there is no hidden test set. Eight games were used to design or tune layers, or
  had their replays studied (bp35, cd82, g50t, ls20, tr87, s5i5, su15, vc33); the other 17 were not.
- One run per game on each side, on different days, so a difference in a single game may be chance.
- The comparison is all four layers together against none. It does not show what each layer contributes. The level
  brief alone was tested separately on 16 games, from mid-game, with mixed results
  (`reports/level_brief_v1/results-*.json`).
- About 4% of replies (461 of 11,111) were sent back and asked again because the 12-rule list was full, and slow
  replies halted three games. Both are costs of the layers. An earlier version of this page said about 6%: that
  count took a reply once for every part of an interrupted game that repeated it
  (`reports/level_brief_v1/whole-log-counts.json` has the corrected counts and how they are made).

## What is in this repository

```
research/claude_arc_v1/         the harness: prompt and layers (policy.py, things.py), controller (run.py),
                                Claude Code backend (backends.py), configuration, audit
research/level_brief_v1/        whole-game runner, checks, results and scorecard replay for the layered runs
research/baseline_continue_v1/  the baseline's runner and its scorecard replay
research/action_waste_v1/       no-effect lessons study, local game adapter, replay page builder
research/memory_fix_v1/         game-over lessons study
research/object_ledger_v1/      object ledger study
research/recovery_v1/           recovery study (stopped; negative result)
reports/                        plans written before each test, results, scorecard records, replay pages
config/                         the configuration every run used
tests/                          the harness tests
agent/                          the small interface the harness imports: actions, observations, ARC adapter
```

The replay pages under `reports/` are single HTML files. Download one and open it in a browser to step through a
game action by action, with what the model wrote on each turn.

Useful starting points:

- `reports/level_brief_v1/figures/`: moments from the runs for each layer, with what the model wrote at that
  moment; `panels/` holds each board as an image of its own.
- `reports/level_brief_v1/whole-results-*.json`: results of the whole-game runs.
- `reports/level_brief_v1/whole-plan-*.json`: what was fixed before each set of runs, with code hashes.
- `reports/level_brief_v1/data/`: what the ARC service returned for each scorecard.
- `reports/level_brief_v1/token_usage.json`: token use beside the baseline.
- `reports/level_brief_v1/whole-log-counts.json`: replies, replies sent back and failed calls, counted from the
  run logs.
- `reports/baseline_continue_v1/README.md`: how the baseline was run.

## Running it

Requirements: Python 3.12, the packages in `requirements.txt`, and the Claude Code CLI signed in to a Claude
subscription (every model call counts against that plan's usage limits). Sending a scorecard also needs an ARC API
key in `.env` as `ARC_API_KEY=...`.

```
python -m unittest tests.test_claude_arc_v1 tests.test_claude_arc_v1_claude_code \
    tests.test_claude_arc_v1_cli_evidence tests.test_claude_arc_v1_recovery tests.test_claude_arc_v1_report_r2
```

The tests make no model call. Two of them are skipped without the original 6 November run log, which is not in the
repository.

To play whole games locally, put the public game files under `environment_files/<game>/<version>/<game>.py` (the
layout the ARC toolkit downloads them in), then:

```
python research/level_brief_v1/whole_games.py plan <stamp>
python research/level_brief_v1/whole_games.py game <game id> <stamp> --send
python research/level_brief_v1/whole_results.py <out.json> <stamp>
```

`whole_games.py check` and `rehearse` make no model call, but compare against the 6 November run log and so need
that log. `scripts/run_claude_arc_opus55.sh` runs the baseline against the live ARC service.

## What is not here

- The raw run logs (every request and reply). They are large and stay local; the results, plans, scorecard records
  and replay pages are here.
- The parent project's own agent. `agent/` holds only the interface types the harness imports.

## License

Apache License 2.0. The ARC-AGI-3 games belong to the ARC Prize Foundation and are not included.
