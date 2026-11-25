"""Reconstruct published arithmetic from archived data, without network/model calls.

Closing responses and per-level actions establish scores; this does not rerun
engines, inspect private inference logs, or measure unreported timeout usage.
"""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parent
PIN = '17d00cfdef7944dda9fd9388efa49fccce4877aa'      # evidence repository commit the paper cites
COUNTED_AT = '0628d3e5f3f0d03927b0b1107cb9d73ce49a7551'  # commit at which the game-over counts read their sources (unchanged since: hash check below)
RESULTS = '5284dc7f521ec14652d77adda4b70d9069587ef1'  # final-results commit; the result files are unchanged since

def load(name):
    return json.loads((ROOT / 'data' / name).read_text())

def close(a, b, tol=1e-7):
    assert math.isclose(a, b, rel_tol=0, abs_tol=tol), (a, b)

def score(actions, human, completed):
    weights = sum(range(1, len(human) + 1))
    completion = sum(range(1, completed + 1)) / weights
    efficiency = sum((i + 1) * min(1.15, (human[i] / actions[i]) ** 2)
                     for i in range(completed)) / weights
    return 100 * min(completion, efficiency)

def with_level_budget(games, times=5):
    """Card score and levels if a game ended once a level had used more than `times` its human count.
    A cut of the recorded trajectory: no new play."""
    total = levels = 0
    for game in games.values():
        run = game['runs'][0]
        actions, human, keep = run['level_actions'], run['level_baseline_actions'], run['levels_completed']
        for index, (used, count) in enumerate(zip(actions, human)):
            if used > times * count:
                keep = min(keep, index)
                break
        total += score(actions, human, keep)
        levels += keep
    return total / len(games), levels

def level_use(games):
    """Actions on levels left open, and actions/human for every completed level."""
    left_open, ratios = 0, []
    for game in games.values():
        run = game['runs'][0]
        done = run['levels_completed']
        left_open += sum(run['level_actions'][done:])
        ratios += [a / h for a, h in zip(run['level_actions'][:done], run['level_baseline_actions'][:done])]
    return left_open, ratios

def official(manifest, expected_score, levels, wins, actions):
    card = manifest['official_scorecard']
    assert card['competition_mode'] is True
    assert len(card['environments']) == card['total_environments'] == 25
    assert card['total_levels'] == 183
    games = {}
    for game in card['environments']:
        assert len(game['runs']) == 1
        run = game['runs'][0]
        value = score(run['level_actions'], run['level_baseline_actions'], run['levels_completed'])
        close(value, game['score'])
        close(value, run['score'])
        assert sum(run['level_actions']) == run['actions'] == game['actions']
        assert run['levels_completed'] == game['levels_completed']
        games[game['id'].split('-')[0]] = game
    close(sum(g['score'] for g in games.values()) / 25, expected_score)
    close(card['score'], expected_score)
    assert sum(g['levels_completed'] for g in games.values()) == card['total_levels_completed'] == levels
    assert sum(g['completed'] for g in games.values()) == card['total_environments_completed'] == wins
    assert sum(g['actions'] for g in games.values()) == card['total_actions'] == actions
    print('competition-mode manifest arithmetic:', round(expected_score, 8), levels, wins, actions)
    return games

def main():
    baseline = load('baseline_final_replay.json')
    layered = load('layered_final_replay.json')
    status = load('layered_revision_status.json')
    result = load('layered_final_result.json')
    bg = official(baseline, 46.19821646694091, 125, 7, 16560)
    lg = official(layered, 85.36898706491712, 166, 17, 10686)
    official(load('layered_confirmed_replay.json'), 82.56343286746824, 162, 15, 9348)
    full = sum(r['matched'] for r in layered['games'])
    final_only = sum(r['same_final_board_other_frames'] for r in layered['games'])
    assert full == 10661 and final_only == 25 and full + final_only == 10686
    assert sum(r['matched'] for r in baseline['games']) == 16560
    for row in layered['games']:
        assert row['stopped'] is None
        assert row['sent'] == row['recorded_actions'] == row['matched'] + row['same_final_board_other_frames']
        if row['same_final_board_other_frames']:
            assert row['game'].startswith('lf52-')
    assert not layered['games_still_playing_sent_up_to_their_last_action']
    print('replay acceptance: 10,661 full hashes + 25 lf52 final-state comparisons')

    rows = list(csv.DictReader((ROOT / 'data/layered_final_per_game.csv').open()))
    for row in rows:
        for key in ['baseline_actions', 'baseline_levels', 'levels', 'layer_actions', 'layer_levels', 'layer_cap']:
            row[key] = int(row[key])
        for key in ['baseline_score', 'layer_score']:
            row[key] = float(row[key])
        row['exposed'] = row['used_or_studied_in_development'] == 'True'
        b, l = bg[row['game']], lg[row['game']]
        assert row['game_id'] == b['id'] == l['id']
        assert row['baseline_actions'] == b['actions']
        assert row['baseline_levels'] == b['levels_completed']
        assert row['layer_actions'] == l['actions'] <= row['layer_cap']
        assert row['layer_levels'] == l['levels_completed']
        assert row['levels'] == l['level_count']
        close(row['baseline_score'], b['score'])
        close(row['layer_score'], l['score'])
    assert len(rows) == 25 and sum(r['layer_cap'] for r in rows) == 17500
    split = tuple(sum((r['layer_levels'] > r['baseline_levels']) if d == 1
                      else (r['layer_levels'] == r['baseline_levels']) if d == 0
                      else (r['layer_levels'] < r['baseline_levels']) for r in rows)
                  for d in [1, 0, -1])
    assert split == tuple(result['more_same_fewer_levels_vs_baseline']) == (15, 9, 1)
    assert Counter(r['layer_end_reason'] for r in rows) == {'win': 17, 'action_cap': 5, 'timeout_halt': 3}
    assert {r['game'] for r in rows if r['layer_end_reason'] == 'timeout_halt'} == {'bp35', 's5i5', 'tr87'}
    exposed = {r['game'] for r in rows if r['exposed']}
    assert exposed == set(status['development_exposure']['used_or_studied_in_development'])
    assert exposed == {'bp35', 'cd82', 'g50t', 'ls20', 'tr87', 's5i5', 'su15', 'vc33'}
    for flag, n, bl, ll, bs, ls, ba, la in [
        (False,17,89,113,52.06,87.22,12178,8048), (True,8,36,53,33.74,81.44,4382,2638)]:
        group = [r for r in rows if r['exposed'] == flag]
        assert len(group) == n
        assert sum(r['baseline_levels'] for r in group) == bl
        assert sum(r['layer_levels'] for r in group) == ll
        assert round(sum(r['baseline_score'] for r in group)/n, 2) == bs
        assert round(sum(r['layer_score'] for r in group)/n, 2) == ls
        assert sum(r['baseline_actions'] for r in group) == ba
        assert sum(r['layer_actions'] for r in group) == la
    common = [r for r in rows if r['layer_levels'] == r['baseline_levels'] == r['levels']]
    assert len(common) == 6
    assert sum(r['baseline_actions'] for r in common) == 1324
    assert sum(r['layer_actions'] for r in common) == 881
    assert round(100*(1-881/1324), 1) == 33.5
    wa = lg['wa30']['runs'][0]
    assert wa['actions'] == 1850 and wa['levels_completed'] == 7
    assert sum(wa['level_actions'][:7]) == 1560 and sum(wa['level_actions'][7:]) == 290
    close(lg['wa30']['score'], 52.678537475904804)
    print('25-game endpoints, 15/9/1 split, 17/8 exposure groups and common-win subset pass')

    higher = sum(r['layer_score'] > r['baseline_score'] + 1e-9 for r in rows)
    lower = [r['game'] for r in rows if r['layer_score'] < r['baseline_score'] - 1e-9]
    assert (higher, 25 - higher - len(lower), lower) == (20, 4, ['s5i5'])
    assert all(r['layer_score'] == 100 for r in rows if abs(r['layer_score'] - r['baseline_score']) <= 1e-9)
    assert (sum(r['layer_actions'] < r['baseline_actions'] for r in rows),
            sum(r['layer_actions'] == r['baseline_actions'] for r in rows)) == (19, 6)
    low = [r for r in rows if r['baseline_score'] < 40]
    assert len(low) == 11
    assert (sum(r['baseline_levels'] for r in low), sum(r['layer_levels'] for r in low)) == (34, 66)
    assert (round(sum(r['baseline_score'] for r in low) / 11, 2), round(sum(r['layer_score'] for r in low) / 11, 2)) == (14.69, 75.39)
    assert 166 - 125 == 41 and 66 - 34 == 32
    # the eight layered runs that did not win, and the action comparison without the three halted runs
    by = {r['game']: r for r in rows}
    assert {g: (r['layer_levels'], r['levels']) for g, r in by.items() if r['layer_end_reason'] == 'action_cap'} == {
        'wa30': (7, 9), 'ls20': (6, 7), 'tn36': (6, 7), 'lf52': (5, 10), 'sc25': (3, 6)}
    assert {g: (r['layer_levels'], r['levels']) for g, r in by.items() if r['layer_end_reason'] == 'timeout_halt'} == {
        'tr87': (4, 6), 'bp35': (8, 9), 's5i5': (6, 8)}
    assert [(by[g]['baseline_levels'], by[g]['layer_levels']) for g in ('lf52', 'sc25', 'wa30')] == [(4, 5), (3, 3), (7, 7)]
    assert [(by[g]['baseline_actions'], by[g]['layer_cap'], by[g]['baseline_levels'] < by[g]['levels'], by[g]['layer_actions'])
            for g in ('dc22', 're86')] == [(1250, 1250, True, 619), (1300, 1300, True, 655)]
    halted = [r for r in rows if r['layer_end_reason'] == 'timeout_halt']
    others = [r for r in rows if r['layer_end_reason'] != 'timeout_halt']
    unused = sum(r['layer_cap'] - r['layer_actions'] for r in halted)
    assert unused == 943 and len(others) == 22
    assert (sum(r['baseline_actions'] for r in others), sum(r['layer_actions'] for r in others)) == (14924, 9829)
    assert round(100 * (1 - 9829 / 14924), 1) == 34.1
    assert round(100 * (1 - (10686 + unused) / 16560), 1) == 29.8 and round(100 * (1 - 10686 / 16560), 1) == 35.5
    # game overs: the baseline's level resets (one after each game over, no run ended on one) and the layered
    # runs' own count, per game
    overs = load('game_over_counts.json')
    whole = {}
    for path in sorted((ROOT / 'data').glob('layered_whole_results_*.json')):
        for run in json.loads(path.read_text())['runs']:
            whole[str(run['game']).split('-')[0]] = (run['actions'], run['detail']['game_overs'])
    assert {g: (v['actions'], v['game_overs']) for g, v in overs['layered']['games'].items()} == whole
    assert {g: v['actions'] for g, v in overs['baseline']['games'].items()} == {g: r['baseline_actions'] for g, r in by.items()}
    assert {g: v['actions'] for g, v in overs['layered']['games'].items()} == {g: r['layer_actions'] for g, r in by.items()}
    base_overs = sum(v['level_resets'] for v in overs['baseline']['games'].values())
    layer_overs = sum(v['game_overs'] for v in overs['layered']['games'].values())
    assert (base_overs, layer_overs) == (127, 36) == (overs['baseline']['total_game_overs'], overs['layered']['total_game_overs'])
    assert (round(100 * base_overs / 16560, 2), round(100 * layer_overs / 10686, 2)) == (0.77, 0.34)
    assert layer_overs / 10686 < 0.5 * base_overs / 16560
    assert (overs['baseline']['games']['bp35'], overs['layered']['games']['bp35']['game_overs']) == ({'actions': 700, 'level_resets': 22}, 5)
    assert by['bp35']['layer_actions'] == 397 and overs['baseline']['source_commit'] == COUNTED_AT
    base_open, base_ratios = level_use(bg)
    layer_open, layer_ratios = level_use(lg)
    assert (base_open, 16560 - base_open, layer_open, 10686 - layer_open) == (7940, 8620, 2170, 8516)
    assert (base_open - layer_open, 16560 - 10686) == (5770, 5874)      # nearly all of the action reduction
    assert (round(100 * (1 - layer_open / base_open), 1), round(100 * (1 - 8516 / 8620), 1)) == (72.7, 1.2)
    assert (len(base_ratios), len(layer_ratios)) == (125, 166)
    assert (sum(r <= 1 for r in base_ratios), sum(r <= 1 for r in layer_ratios)) == (86, 151)
    assert (sum(r > 5 for r in base_ratios), sum(r > 5 for r in layer_ratios)) == (3, 1)
    wa7 = lg['wa30']['runs'][0]
    assert (wa7['level_actions'][6], wa7['level_baseline_actions'][6]) == (921, 79)
    base_cut, base_cut_levels = with_level_budget(bg)
    layer_cut, layer_cut_levels = with_level_budget(lg)
    assert (round(base_cut, 2), base_cut_levels, round(layer_cut, 2), layer_cut_levels) == (45.92, 121, 85.13, 165)
    assert round(layer_cut - base_cut, 2) == 39.20
    assert 0 < baseline['official_scorecard']['score'] - base_cut < 0.3      # "less than 0.3 points" each
    assert 0 < layered['official_scorecard']['score'] - layer_cut < 0.3
    budget = status['per_level_budget_sensitivity']
    close(budget['baseline_score'], base_cut, 1e-6)
    close(budget['layered_score'], layer_cut, 1e-6)
    print('per-game score and action comparisons, open-level actions, level ratios and the 5x per-level budget pass')

    usage = load('layered_token_usage.json')
    total = usage['totals']['finished games']
    assert len(total['games']) == 25 and set(total['games']) == set(lg)
    b, l = total['baseline'], total['layers']
    assert (b['in'], b['out'], b['actions'], b['replies']) == (219307219,37194101,16560,16433)
    assert (l['in'], l['out'], l['actions'], l['replies']) == (201029785,27316461,10686,11111)
    for side, key in [('baseline', 'base'), ('layers', 'mine')]:
        for field in ['in', 'out', 'think', 'actions', 'replies']:
            assert sum(g[key][field] for g in usage['games']) == total[side][field]
    for key, expected in [('in',8.3), ('out',26.6), ('actions',35.5), ('replies',32.4)]:
        assert round(100*(1-l[key]/b[key]), 1) == expected
    assert b['in'] + b['out'] == 256501320
    assert l['in'] + l['out'] == 228346246
    assert round(100*(1-(l['in']+l['out'])/(b['in']+b['out'])), 1) == 11.0
    assert round(100*((l['in']/l['actions'])/(b['in']/b['actions'])-1), 1) == 42.1
    old = load('layered_token_usage_24_game_snapshot.json')['totals']['finished games']
    assert len(old['games']) == 24 and 'wa30' not in old['games']
    assert round(100*(1-(old['layers']['in']+old['layers']['out'])/(old['baseline']['in']+old['baseline']['out'])),1) == 17.1
    print('all 25 reported token totals: 256,501,320 -> 228,346,246 (11.0% reduction)')

    for name, verdict, without, with_ in [('brief_first_set.json','no detectable difference',10,17), ('brief_second_set.json','helps',29,38)]:
        held = load(name)['held_out']
        assert held['verdict'] == verdict
        assert held['levels_completed'] == {'ledger': without, 'brief': with_}
    second = load('brief_second_set.json')['runs']
    for game in ['lp85', 'r11l', 'sb26']:
        runs = [r for r in second if r['game'] == game and r['state'] == 'clean']
        assert len(runs) == 4
        assert Counter(r['arm'] for r in runs) == {'ledger': 2, 'brief': 2}
        assert all(r['stop_reason'] == 'win' and r['new_actions'] < 100 for r in runs)
    tn36 = [r for r in second if r['game'] == 'tn36' and r['state'] == 'clean']
    assert len(tn36) == 4 and all(r['started_after_action'] == 0 for r in tn36)
    reset = status['reset_allowances']
    assert reset['baseline_initial_portions'] == 10
    assert reset['baseline_continuation'] == reset['layered_whole_game'] == 50
    assert reset['tu93_continued_after_stopping_at_10'] and not reset['shown_to_model']
    assert status['manual_interventions']['tr87_timeout_exception'] == {'actions':43,'seconds':400,'new_levels':0,'retries':1}
    assert status['manual_interventions']['wa30_connection_loss_stopped_first_segment_at_action'] == 1169
    assert status['earlier_log_verification_snapshot']['status'] == 'WITHDRAWN'
    counts = load('layered_final_log_counts.json')
    tally = counts['totals']
    assert counts['games'] == len(counts['per_game']) == 25
    for key, value in tally.items():
        assert sum(g[key] for g in counts['per_game']) == value, key
    by_game = {r['game']: r for r in rows}
    for g in counts['per_game']:
        assert (g['actions'], g['levels']) == (by_game[g['game']]['layer_actions'], by_game[g['game']]['layer_levels']), g['game']
        assert g['replies'] == g['replies_from_opus_5_5'] and g['audit'] == 'passes'
    assert tally['actions'] == 10686 and tally['replies'] == l['replies'] == 11111
    assert tally['replies_sent_back'] == 461 and round(100 * 461 / 11111, 1) == 4.1
    assert tally['replies_in_turns_cut_short'] == tally['replies_in_turns_cut_short_sent_back'] == 5
    assert (tally['calls_past_the_time_limit'], tally['calls_past_the_time_limit_that_ended_a_part']) == (97, 20)
    assert (tally['calls_at_a_usage_limit'], tally['calls_with_no_connection'], tally['other_failures']) == (8, 2, 0)
    final = status['final_log_counts']
    assert (final['replies'], final['replies_sent_back_for_full_12_rule_list'], final['calls_past_time_limit']) == (11111, 461, 97)
    assert (final['of_which_followed_by_a_retry'], final['of_which_ended_a_segment']) == (77, 20)
    assert not final['raw_logs_bundled']
    print('controlled tests, operational metadata and the archived final log counts pass; the counts themselves need the local logs')

    # the bp35 example of the Introduction: the baseline's notes about the fatal tiles, and the saved-position test
    trace = load('bp35_rule_trace.json')
    assert trace['level'] == 2 and trace['game_overs_at_actions'][:2] == [23, 48]
    assert trace['transitions_sent_with_a_request'] == 8
    gone = trace['first_request_without_the_fatal_action']
    assert gone['reply_choosing_action'] == 32 and 't23' not in gone['transitions_sent']
    assert 't23' in gone['sent_with_the_request_before']
    rule = {r['reply_choosing_action']: (r['notes_about_the_tiles'] or [None])[0] for r in trace['replies']}
    for action in range(25, 33):
        assert rule[action]['status'] == 'supported_locally', action
        assert rule[action]['statement'].startswith('The f objects with b0b at the bottom are hazards'), action
    for action in range(33, 36):
        assert rule[action]['status'] == 'tentative' and 'hazards' in rule[action]['statement'], action
    assert all(rule[action] is None for action in range(36, 42))
    for action in range(42, 49):
        assert rule[action]['status'] == 'tentative' and 'hazards or goals' in rule[action]['statement'], action
    assert rule[50]['status'] == 'supported_locally' and 'spikes' in rule[50]['statement']
    replay = load('bp35_saved_position_test.json')['by_request']
    assert (replay['turn47-none']['valid'], replay['turn47-none']['game_over']) == (8, 8)
    assert (replay['turn47-evidence']['valid'], replay['turn47-evidence']['game_over']) == (8, 4)
    print('bp35 example: rule supported at actions 25-32, tentative from 33, absent 36-41, game overs at 23 and 48; replay 8 of 8 and 4 of 8')

    assert result['status'] == 'CONFIRMED_COMPETITION_MODE_REPLAY'
    assert result['source_commit'] == status['source_commit'] == PIN
    assert result['result_files_commit'] == status['result_files_commit'] == RESULTS
    provenance = load('final_evidence_provenance.json')
    assert provenance['reviewed_commit'] == PIN
    assert provenance['files_changed_since_that_commit'] == ['reports/memory_fix_v1/README.md', 'research/level_brief_v1/whole_verify.py']
    listed = {f['path']: f['sha256'] for f in provenance['files']}
    assert hashlib.sha256((ROOT / 'data/layered_final_log_counts.json').read_bytes()).hexdigest() == \
        listed['reports/level_brief_v1/whole-log-counts.json']
    game_overs = load('game_over_counts.json')['baseline']
    assert game_overs['source_sha256'] == listed[game_overs['source']] and game_overs['source_commit'] == COUNTED_AT
    boards = load('figure_sources.json')['run_boards']
    assert boards['commit'] == PIN and len(boards['images']) == 11
    for image in boards['images']:
        assert hashlib.sha256((ROOT / image['local_path']).read_bytes()).hexdigest() == image['sha256'] == listed[image['source_path']]
    used = {name for names in boards['figures'].values() for name in names}
    assert used == {Path(image['local_path']).name for image in boards['images']}
    assert hashlib.sha256((ROOT / 'data/bp35_saved_position_test.json').read_bytes()).hexdigest() == \
        listed['reports/memory_fix_v1/death_test/scores.json']
    local = load('figure_sources.json')['baseline_boards']       # boards of the Introduction's example: local log only
    counters = load('figure_sources.json')['counter_boards']     # boards of the step-counter figure: local logs only
    assert (len(local['images']), len(counters['images'])) == (4, 6)
    for image in local['images'] + counters['images']:       # since commit 17d00cf these boards are in the repository too
        assert hashlib.sha256((ROOT / image['local_path']).read_bytes()).hexdigest() == image['sha256'] == listed[image['source_path']]
    assert hashlib.sha256((ROOT / local['note_trace']['local_path']).read_bytes()).hexdigest() == local['note_trace']['sha256'] \
        == listed[local['note_trace']['source_path']]
    counts_file = load('figure_sources.json')['game_over_counts']
    assert hashlib.sha256((ROOT / counts_file['local_path']).read_bytes()).hexdigest() == counts_file['sha256'] == listed[counts_file['source_path']]
    # the worked example of Section 3.3.1: what the figure quotes is word for word what the saved text holds
    sources = load('figure_sources.json')
    worked = load('worked_example_wa30.json')
    assert hashlib.sha256((ROOT / 'data/worked_example_wa30.json').read_bytes()).hexdigest() == sources['worked_example']['text_sha256'] \
        == listed[sources['worked_example']['source_path']]
    figure = (ROOT / sources['worked_example']['figure']).read_text()
    assert worked['lesson_written']['rule'] in figure and worked['lesson_written']['applies_when'] in figure
    assert worked['check_in_next_reply']['lesson_check'].split(' No-effect lesson')[0] in figure
    field = worked['next_request']['game_over_lessons_field']
    assert worked['lesson_written']['rule'] in field and worked['lesson_written']['applies_when'] in field
    assert '"after":"t357","level":5' in field
    assert (worked['game_over']['action'], worked['reset']['action'], worked['lesson_written']['in_reply_choosing_action'],
            worked['next_request']['for_action'], worked['check_in_next_reply']['in_reply_choosing_action']) == (357, 358, 359, 360, 360)
    assert worked['game_over']['state_after'] == 'GAME_OVER'
    assert (worked['game_over']['bottom_row_before'], worked['game_over']['bottom_row_after']) == ({'4': 63, '7': 1}, {'4': 64})
    assert set(sources['worked_example']['boards']) <= {Path(image['local_path']).name for image in boards['images']}
    charts = sources['result_charts']
    assert all((ROOT / name).exists() for name in charts if name.endswith('.pdf')) and 'figures/per_game_scores.pdf' in charts
    assert result['actions'] == 10686 and result['levels'] == 166 and result['games_won'] == 17
    assert result['reconstructed_from_archived_per_level_actions']
    close(result['unrounded_score'],layered['official_scorecard']['score'])
    close(result['score_gain_percentage_points'],layered['official_scorecard']['score']-baseline['official_scorecard']['score'])
    assert result['official_scorecard'] == layered['scorecard_url']
    assert not status['pending_updates']
    assert status['manuscript_authorship']['author_count'] == 1
    assert status['manuscript_authorship']['sole_author'] == 'Chongwei (Alan) Dai'
    manuscript = '\n'.join(p.read_text() for p in ROOT.rglob('*.tex'))
    for stale in ['10,396', '37.2\\%', 'author-reported final', 'replay remains pending', '8,675', 'at least 90',
                  '696 of', 'sc25_frames', 'ls20_frames', 'completion_comparison']:
        assert stale not in manuscript, stale
    assert manuscript.count('85.13') == 1       # once, as the per-level budget recalculation, never as a headline score
    # the corrected numbers are in the text, whatever the wording around them
    assert '461 of 11,111 replies (4.1\\%)' in manuscript and re.search(r'\b(?:Ninety-seven|97) calls', manuscript)
    assert re.search(r'45\.92\\% for the baseline and 85\.13\\% for the layered', manuscript)
    assert re.search(r'[Aa]t action 33\b.{0,80}?tentative', manuscript) and 'four of eight' in manuscript
    assert not re.search(r'\b(?:we|our)\b',manuscript,re.I)
    bib = (ROOT/'references.bib').read_text()
    keys = re.findall(r'@\w+\{([^,]+),',bib)
    assert len(keys) == len(set(keys)), 'Duplicate bibliography keys'
    cited = {k.strip() for c in re.findall(r'\\cite\w*\{([^}]+)\}',manuscript) for k in c.split(',')}
    assert cited <= set(keys), 'Missing references: ' + str(cited-set(keys))
    print('current score, sole-author voice, historical scope and bibliography guards pass')
    # the scope of the comparison (one run of each harness per game) is stated wherever the headline score is, in
    # the author's own wording
    scope = r'one (?:whole-game |recorded )?run (?:per condition|from each harness) per game|once (?:per|on each) game'
    for relative in ['main.tex', 'tables/main_results.tex', 'sections/01_introduction.tex', 'sections/05_results.tex',
                     'sections/06_discussion.tex']:
        assert re.search(scope, (ROOT/relative).read_text()), relative
    for url in [
        'https://arcprize.org/scorecards/0f882c2e-0451-41bd-86c5-211a54785c56',
        'https://arcprize.org/scorecards/96932ddf-ab6a-4354-94b2-9644447dae14',
        'https://github.com/dcw06/ARC-AGI-3-Opus-5.5-Harness/tree/'+PIN]:
        assert url in (ROOT/'main.tex').read_text(), url
    access = load('public_artifact_access.json')
    assert access['baseline']['http_status'] == access['layered']['http_status'] == access['pinned_code']['http_status'] == 200
    assert access['baseline']['watch_replay_links'] == access['layered']['watch_replay_links'] == 25
    assert access['pinned_code']['repository_visibility'] == 'public'
    links = access['link_check']                               # every cited or printed link, requested without signing in
    assert links['urls'] == links['http_status_200'] == len(links['results']) >= 30
    assert all(row['http_status'] == 200 for row in links['results'])
    linked = {url for url in re.findall(r'\\href\{([^}]*)\}', manuscript) if url.startswith('http')}
    assert linked <= {row['url'] for row in links['results']}, linked - {row['url'] for row in links['results']}
    assert status['submission_preparation']['fresh_interleaved_replication'] == 'recommended_future_work_not_conducted'
    assert re.search(r'confirmatory runs (?:have|had) not been conducted|(?:have|had) not conducted these confirmatory runs', manuscript)
    print('headline scope, direct artifact links, dated access record and proposed-only replication guards pass')

if __name__ == '__main__':
    main()
