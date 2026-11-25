"""Draw the result figures from the paper's own data files. No new evaluation, no network.

    per_game_scores.pdf       game score in each game, both harnesses (the score panel alone, for the Introduction)
    per_game_outcomes.pdf     levels completed, game score and actions used in each game, both the baseline and layered harnesses
    level_action_ratio.pdf    actions on each completed level against the human count, both the baseline and layered harnesses
    brief_tests.pdf           the two controlled tests of the level-brief package, game by game

    python3 figures/make_result_figures.py             writes the four PDF files beside this script
    python3 figures/make_result_figures.py <folder>    also writes PNG previews into <folder>

Needs Matplotlib. Every number drawn is checked against the totals the paper reports before it is drawn.
"""
from pathlib import Path
import csv
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures'
PREVIEW = Path(sys.argv[1]) if len(sys.argv) == 2 else None
plt.rcParams.update({'font.family': 'cmr10', 'mathtext.fontset': 'cm', 'axes.formatter.use_mathtext': True,
                     'font.size': 9, 'pdf.fonttype': 42, 'ps.fonttype': 42, 'axes.unicode_minus': False})
BASE = dict(marker='o', facecolor='white', edgecolor='black', linewidth=.8, s=34, zorder=2)      # open circle
LAYER = dict(marker='s', facecolor='black', edgecolor='black', linewidth=.5, s=11, zorder=3)     # filled square
LEGEND = [Line2D([], [], marker='o', markerfacecolor='white', markeredgecolor='black', linestyle='none',
                 markersize=5.8, label='Baseline'),
          Line2D([], [], marker='s', color='black', linestyle='none', markersize=3.4, label='Layered')]


def save(fig, name):
    fig.savefig(OUT / (name + '.pdf'))
    if PREVIEW:
        fig.savefig(PREVIEW / (name + '.png'), dpi=200)
    plt.close(fig)


def rows_of(axis, count, used=None):
    """Rows of a dot plot: light bands on every other row in use, no frame but the bottom line."""
    for i in range(0, count if used is None else used, 2):
        axis.axhspan(i - .5, i + .5, facecolor='.955', edgecolor='none', zorder=0)
    axis.set_ylim(count - .4, -.6)
    axis.tick_params(axis='y', length=0, pad=6)
    axis.tick_params(axis='x', length=3)
    for side in ('top', 'right', 'left'):
        axis.spines[side].set_visible(False)
    axis.spines['bottom'].set_color('.4')


def pair(axis, row, before, after):
    axis.plot([before, after], [row, row], color='.55', lw=1.1, zorder=1)
    axis.scatter([before], [row], **BASE)
    axis.scatter([after], [row], **LAYER)


def games_by_baseline_score():
    """The 25 per-game rows, checked against the paper's totals, lowest baseline score first."""
    games = list(csv.DictReader((ROOT / 'data/layered_final_per_game.csv').open()))
    for g in games:
        for key in ('baseline_actions', 'baseline_levels', 'levels', 'layer_actions', 'layer_levels', 'layer_cap'):
            g[key] = int(g[key])
        for key in ('baseline_score', 'layer_score'):
            g[key] = float(g[key])
    assert len(games) == 25 and sum(g['layer_cap'] for g in games) == 17500
    assert (sum(g['baseline_levels'] for g in games), sum(g['layer_levels'] for g in games)) == (125, 166)
    assert (sum(g['baseline_actions'] for g in games), sum(g['layer_actions'] for g in games)) == (16560, 10686)
    assert round(sum(g['baseline_score'] for g in games) / 25, 2) == 46.20
    assert round(sum(g['layer_score'] for g in games) / 25, 2) == 85.37
    games.sort(key=lambda g: (g['baseline_score'], g['game']))          # lowest baseline score at the top
    return games


def names_of(games):
    """Row labels: a dagger for a game used or studied in development, an asterisk for a halted layered run."""
    names = []
    for g in games:
        name = g['game']
        if g['used_or_studied_in_development'] == 'True':
            name += r'$^{\dagger}$'
        if g['halted'] == 'True':
            name += r'$^{*}$'
        names.append(name)
    return names


def per_game_scores():
    """The score panel alone: one row a game, the baseline run and the layered run, and the two means."""
    games = games_by_baseline_score()
    higher = sum(g['layer_score'] > g['baseline_score'] + 1e-9 for g in games)
    lower = sum(g['layer_score'] < g['baseline_score'] - 1e-9 for g in games)
    assert (higher, 25 - higher - lower, lower) == (20, 4, 1)
    fig, axis = plt.subplots(figsize=(4.7, 3.95))
    fig.subplots_adjust(left=.125, right=.975, bottom=.115, top=.94)
    rows_of(axis, len(games))
    for x in (0, 25, 50, 75, 100):
        axis.axvline(x, color='.88', lw=.5, zorder=0.5)
    for row, g in enumerate(games):
        pair(axis, row, g['baseline_score'], g['layer_score'])
    # the two means, drawn below the last row so that they cross no marker
    base_mean = sum(g['baseline_score'] for g in games) / 25
    layer_mean = sum(g['layer_score'] for g in games) / 25
    axis.set_ylim(len(games) + 1.75, -.6)
    for mean, text, row in ((base_mean, 'Baseline mean 46.20%', len(games) + .1),
                            (layer_mean, 'Layered mean 85.37%', len(games) + 1.0)):
        axis.plot([mean, mean], [-.5, row + .35], color='.3', lw=.7, linestyle=(0, (1, 2)), zorder=1)
        axis.text(mean - 1.5, row, text, ha='right', va='center', fontsize=8, color='.15')
    axis.set_xlim(-5, 105)
    axis.set_xticks([0, 25, 50, 75, 100])
    axis.set_xlabel('Game score (%)', labelpad=5)
    axis.set_yticks(range(len(games)), names_of(games))
    fig.legend(handles=LEGEND, loc='upper left', bbox_to_anchor=(.11, 1.005), ncol=2, frameon=False,
               handletextpad=.3, columnspacing=1.6)
    save(fig, 'per_game_scores')


def per_game():
    games = games_by_baseline_score()
    fig, axes = plt.subplots(1, 3, figsize=(6.9, 5.0), sharey=True)
    fig.subplots_adjust(left=.085, right=.985, bottom=.115, top=.935, wspace=.09)
    panels = (
        ('(a) Levels completed (%)',
         lambda g: (100 * g['baseline_levels'] / g['levels'], 100 * g['layer_levels'] / g['levels'])),
        ('(b) Game score (%)', lambda g: (g['baseline_score'], g['layer_score'])),
        ('(c) Actions used (% of cap)',
         lambda g: (100 * g['baseline_actions'] / g['layer_cap'], 100 * g['layer_actions'] / g['layer_cap'])))
    for axis, (label, values) in zip(axes, panels):
        rows_of(axis, len(games))
        for x in (0, 25, 50, 75, 100):
            axis.axvline(x, color='.88', lw=.5, zorder=0.5)
        for row, g in enumerate(games):
            pair(axis, row, *values(g))
        axis.set_xlim(-5, 105)
        axis.set_xticks([0, 25, 50, 75, 100])
        axis.set_xlabel(label, labelpad=5)
    axes[0].set_yticks(range(len(games)), names_of(games))
    fig.legend(handles=LEGEND, loc='upper left', bbox_to_anchor=(.075, 1.0), ncol=2, frameon=False,
               handletextpad=.3, columnspacing=1.6)
    save(fig, 'per_game_outcomes')


def level_ratios(name):
    """(actions on the level / human count) of every completed level in a closing replay record."""
    card = json.loads((ROOT / 'data' / name).read_text())['official_scorecard']
    ratios, open_actions = [], 0
    for game in card['environments']:
        run = game['runs'][0]
        done = run['levels_completed']
        ratios += [a / h for a, h in zip(run['level_actions'][:done], run['level_baseline_actions'][:done])]
        open_actions += sum(run['level_actions'][done:])
    return sorted(ratios), open_actions, card['total_actions']


def action_ratio():
    base, base_open, base_all = level_ratios('baseline_final_replay.json')
    layer, layer_open, layer_all = level_ratios('layered_final_replay.json')
    assert (len(base), len(layer)) == (125, 166)
    assert (sum(r <= 1 for r in base), sum(r <= 1 for r in layer)) == (86, 151)
    assert (sum(r > 5 for r in base), sum(r > 5 for r in layer)) == (3, 1)
    assert (base_open, base_all, layer_open, layer_all) == (7940, 16560, 2170, 10686)
    fig, axis = plt.subplots(figsize=(5.0, 3.05))
    fig.subplots_adjust(left=.115, right=.80, bottom=.155, top=.93)
    low, high = .08, 14
    for ratios, style, width in ((base, (0, (4, 2)), 1.2), (layer, 'solid', 1.6)):
        xs = [low] + ratios + [high]
        ys = [0] + list(range(1, len(ratios) + 1)) + [len(ratios)]
        axis.step(xs, ys, where='post', color='black', linestyle=style, lw=width, zorder=3)
    axis.text(high * 1.06, len(layer), 'Layered\n166 levels', va='center', ha='left', linespacing=1.15)
    axis.text(high * 1.06, len(base), 'Baseline\n125 levels', va='center', ha='left', linespacing=1.15)
    for x, text in ((1, 'human count'), (5, r'5$\times$')):
        axis.axvline(x, color='.45', lw=.7, linestyle=(0, (1, 2)), zorder=1)
        axis.text(x * 1.07, 6, text, va='bottom', ha='left', fontsize=8, color='.25')
    axis.axhline(183, color='.45', lw=.7, linestyle=(0, (1, 2)), zorder=1)
    axis.text(low * 1.12, 183 - 4, 'all 183 levels', va='top', ha='left', fontsize=8, color='.25')
    axis.set_xscale('log')
    axis.set_xlim(low, high)
    axis.set_ylim(0, 192)
    ticks = [.1, .25, .5, 1, 2, 5, 10]
    axis.set_xticks(ticks, ['0.1', '0.25', '0.5', '1', '2', '5', '10'])
    axis.minorticks_off()
    axis.set_yticks([0, 50, 100, 150])
    axis.set_xlabel('Actions used on a completed level, divided by its human count', labelpad=5)
    axis.set_ylabel('Completed levels at or below this ratio', labelpad=5)
    for side in ('top', 'right'):
        axis.spines[side].set_visible(False)
    axis.tick_params(length=3)
    save(fig, 'level_action_ratio')


def brief_tests():
    sets = []
    for name, verdict, total in (('brief_first_set.json', 'no detectable difference', (10, 17)),
                                 ('brief_second_set.json', 'helps', (29, 38))):
        held = json.loads((ROOT / 'data' / name).read_text())['held_out']
        assert held['verdict'] == verdict and held['levels_completed'] == {'ledger': total[0], 'brief': total[1]}
        games = [(key.split('-')[0], value['ledger'], value['brief']) for key, value in sorted(held['by_game'].items())]
        assert (sum(g[1] for g in games), sum(g[2] for g in games)) == total
        sets.append(games)
    assert (len(sets[0]), len(sets[1])) == (7, 9)
    every_run_won = {'lp85', 'r11l', 'sb26'}
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.55), sharex=True)
    fig.subplots_adjust(left=.075, right=.985, bottom=.185, top=.88, wspace=.2)
    labels = ('(a) First set: levels completed in two runs', '(b) Second set: levels completed in two runs')
    for axis, games, label in zip(axes, sets, labels):
        rows_of(axis, 9, len(games))             # nine rows in both panels, so that the rows line up
        for x in range(0, 10):
            axis.axvline(x, color='.9', lw=.5, zorder=0.5)
        for row, (game, without, with_) in enumerate(games):
            pair(axis, row, without, with_)
        axis.set_yticks(range(len(games)), [g[0] + (r'$^{\ddagger}$' if g[0] in every_run_won else '') for g in games])
        axis.set_xlim(-.5, 9.5)
        axis.set_xticks(range(0, 10))
        axis.set_xlabel(label, labelpad=5)
    legend = [Line2D([], [], marker='o', markerfacecolor='white', markeredgecolor='black', linestyle='none',
                     markersize=5.8, label='Without the level-brief package'),
              Line2D([], [], marker='s', color='black', linestyle='none', markersize=3.4,
                     label='With the level-brief package')]
    fig.legend(handles=legend, loc='upper left', bbox_to_anchor=(.065, 1.01), ncol=2, frameon=False,
               handletextpad=.3, columnspacing=1.6)
    save(fig, 'brief_tests')


if __name__ == '__main__':
    per_game_scores()
    per_game()
    action_ratio()
    brief_tests()
