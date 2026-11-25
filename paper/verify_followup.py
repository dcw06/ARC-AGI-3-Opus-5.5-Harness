"""Offline checks for the November 9 follow-up. No model or network calls."""
import json, math
from pathlib import Path
P=Path(__file__).resolve().parent/'data'/'tycho'
def get(n): return json.loads((P/(n+'.json')).read_text())
def close(a,b): assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8),(a,b)
def score(acts,base,n):
 q=[min(1.15,(b/a)**2) if i<n else 0 for i,(a,b) in enumerate(zip(acts,base))]
 w=len(base)*(len(base)+1)/2
 return 100*min(sum(range(1,n+1))/w,sum((i+1)*v for i,v in enumerate(q))/w)
def cost(u):return (4*u['tokens_in']+.2*u['cache_read']+5*u['cache_write']+20*u['tokens_out'])/1e6
def env(manifest,game):return next(g for g in manifest['scorecard']['environments'] if g['id'].startswith(game))
r=get('results');m=get('matched_replay_manifest');f=get('final_replay_manifest');c=get('cap100_replay_manifest')
assert m['closed'] and f['closed'] and c['closed']
assert m['failed'] is None and f['failed'] is None and c['failed'] is None
for game,arms in r['games'].items():
 for arm,v in arms.items():
  close(score(v['level_actions'],v['level_baseline_actions'],v['levels_completed']),v['score'])
  assert sum(v['level_actions'])==v['actions']==100
  if arm=='tycho':
   e=env(m,game); run=e['runs'][0]
   assert e['levels_completed']==v['levels_completed'] and e['resets']==v['resets']
   assert run['level_actions']==v['level_actions'];close(run['score'],v['score'])
   assert round(cost(v['usage']),2)==v['inference_cost_usd_list_price']
   assert sum(v['llm_calls_by_type'].values())==({'lf52':128,'bp35':156}[game])
for name,manifest in [('cap100',c),('cap115',f)]:
 v=r['bp35_continuation'][name];b=r['games']['bp35']['baseline']['level_baseline_actions']
 close(score(v['level_actions'],b,v['levels_completed']),v['score'])
 assert sum(v['level_actions'])==v['total_actions']
 e=env(manifest,'bp35');s=e['runs'][0]
 assert s['level_actions']==v['level_actions'] and s['actions']==v['total_actions']
 close(s['score'],v['score']);assert e['resets']==v['resets']
 close(round(cost(v['cumulative_usage']),2),v['cumulative_cost_usd_list_price'])
matched=next(g for g in get('matched_trace')['games'] if g['short_id']=='bp35')
final=get('final_trace')['games'][0]
assert final['actions'][:100]==matched['actions']
assert len(final['actions'])==474
assert sum(a['action']=='RESET' for a in final['actions'])==6
assert final['actions'][-1]['expected_levels_completed']==9
assert final['actions'][-1]['expected_state'].endswith('WIN')
# Both cap changes retain identical executable source fingerprints and config,
# apart from the budget field named in the archived override.
prev=get('run_spec')
for name in ['cap100','cap115']:
 nxt=get(name+'_run_spec');ov=get(name+'_override')
 assert prev['policy']['sources_sha256']==nxt['policy']['sources_sha256']
 assert ov['source_run_spec_fingerprint']==prev['fingerprint']
 assert ov['new_fingerprint']==nxt['fingerprint']
 diffs=[]
 for section,cfg in prev['policy']['config'].items():
  for k,v in cfg.items():
   nv=nxt['policy']['config'][section][k]
   if v!=nv:diffs.append([section,k,v,nv])
 assert diffs==ov['allowed_budget_diffs'],diffs
 prev=nxt
# The reference actions are external context, not matched trials.
astra=[x for x in get('astra_reference') if x[0]=='bp35' and x[1]=='adapter']
assert len(astra)==6 and min(x[7] for x in astra)==430 and max(x[7] for x in astra)==516
high=next(x for x in astra if x[2]=='high');assert sum(high[10])==high[7]==488
print('PASS: four matched scores, two continuation scores, replay totals, costs, 100-action prefix, six resets, budget-only config changes, and external reference counts.')
print('Matched Tycho costs:',{g:round(cost(v['tycho']['usage']),6) for g,v in r['games'].items()})
print('Final cumulative cost:',cost(r['bp35_continuation']['cap115']['cumulative_usage']))
