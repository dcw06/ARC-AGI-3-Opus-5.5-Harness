"""Reproduce the paper's score, action-budget and exposure analyses offline."""
from collections import defaultdict
import csv
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
levels=list(csv.DictReader((ROOT/'data/level_results.csv').open()))
games=list(csv.DictReader((ROOT/'data/per_game_results.csv').open()))
ledger=json.loads((ROOT/'data/holdout_ledger.yaml').read_text())  # JSON-compatible YAML
by_game=defaultdict(list)
for row in levels:
    by_game[row['game_id']+'-'+row['game_version']].append(row)

results=[]
for full, rows in sorted(by_game.items()):
    rows.sort(key=lambda r:int(r['level_index']))
    L=len(rows); W=L*(L+1)/2
    completed_weight=0; efficiency_weight=0; capped=0; human_total=0; human_weight=0
    for row in rows:
        ell=int(row['level_index'])
        done=row['completed']=='true'
        a=int(row['scorer_counted_actions'])
        b=int(row['official_human_baseline_actions'])
        q=min(1.15,(b/a)**2) if done else 0.0
        shown=float(row['official_level_efficiency_fraction'])
        # Displayed level efficiency uses four fractional decimal places.
        if abs(q-shown)>0.00005000001:
            raise ValueError(f'Level score differs from displayed precision: {full} level {ell}')
        completed_weight+=ell*done; efficiency_weight+=ell*q
        capped+=int(done and q==1.15)
        human_total+=b
        if human_total<=100:human_weight+=ell
    score=100*min(completed_weight/W,efficiency_weight/W)
    game=next(r for r in games if r['game_id']+'-'+r['game_version']==full)
    if abs(score-float(game['displayed_rhae_pct']))>0.005000001:
        raise ValueError(f'Game score differs from display: {full}')
    results.append(dict(game=full,score=score,weighted_completion=100*completed_weight/W,
        human_total=human_total,human_100_score=100*human_weight/W,levels=L,
        done=sum(r['completed']=='true' for r in rows),cap_levels=capped))

mean=lambda field, rows=results:sum(r[field] for r in rows)/len(rows)
out=dict(games=results,rhae=mean('score'),weighted_completion=mean('weighted_completion'),
  efficiency_penalty=mean('weighted_completion')-mean('score'),human_100_rhae=mean('human_100_score'),
  min_human_total=min(r['human_total'] for r in results),max_human_total=max(r['human_total'] for r in results),
  capped_solved=sum(r['cap_levels'] for r in results),mean_per_game_completion=sum(100*r['done']/r['levels'] for r in results)/len(results),
  without_ft09=mean('score',[r for r in results if not r['game'].startswith('ft09-')]),
  without_ft09_ls20=mean('score',[r for r in results if not r['game'].startswith(('ft09-','ls20-'))]))
out['development_mean']=mean('score',[r for r in results if r['game'] in ledger['development']])
out['reduced_exposure_mean']=mean('score',[r for r in results if r['game'] in ledger['h1']+ledger['h2']])
out['pooled_completion_pct']=100*sum(r['done'] for r in results)/len(levels)
out['model_action_selection_calls']=sum(int(r['model_action_selection_calls']) for r in games)
out['environment_actions']=sum(int(r['environment_actions']) for r in games)
out['controller_resets']=sum(int(r['controller_resets']) for r in games)
assert len(results)==25 and len(levels)==183
assert out['model_action_selection_calls']+out['controller_resets']==out['environment_actions']==2475
assert math.isclose(out['rhae'],23.164340099991225,abs_tol=1e-10)
print(json.dumps(out,indent=2))
