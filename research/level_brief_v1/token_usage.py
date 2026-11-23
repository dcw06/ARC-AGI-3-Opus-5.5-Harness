"""Token usage of the baseline's whole games and of the whole games with every layer. No model call.

For each of the 25 games: the model replies, the input tokens (cache reads and writes included), the output
tokens and the thinking tokens among them, as the Claude Code CLI reported them for each reply.

  - with the layers: the last part of the game's run, which holds every reply up to its last finished action
  - the baseline: the replies in the last log of the game, plus, for the actions that log repeated, the replies
    in the log it continued from

A call that ran past its time limit reports no usage and is not counted, on either side.

    token_usage.py        prints one line a game and the totals; writes reports/level_brief_v1/token_usage.json

Usage (project environment), from the repository root.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.level_brief_v1 import whole_games as W, whole_verify as V

def usage_of(path, game, upto_actions=None):
    """Sums over the model replies of one game in one log; upto_actions: only replies for the first so many actions."""
    out = {'replies': 0, 'in': 0, 'out': 0, 'think': 0, 'cost': 0.0, 'actions': 0}
    with open(path) as handle:
        for line in handle:
            if '"kind":"transition"' in line:
                if json.loads(line).get('game_id') == game:
                    out['actions'] += 1
            elif '"kind":"model_returned"' in line:
                e = json.loads(line)
                if e.get('game_id') != game:
                    continue
                if upto_actions is not None and out['actions'] >= upto_actions:
                    continue
                u = (e.get('metadata') or {}).get('usage') or {}
                out['replies'] += 1
                out['in'] += sum(int(u.get(k) or 0) for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
                out['out'] += int(u.get('output_tokens') or 0)
                out['think'] += int((u.get('output_tokens_details') or {}).get('thinking_tokens') or 0)
                out['cost'] += float((e.get('metadata') or {}).get('notional_cost_usd') or 0)
    return out

def add(a, b):
    return {k: a[k] + b[k] for k in a}

def baseline(game, source):
    """The baseline's whole game: the last log's own replies plus, for the actions it repeated, the replies in the log it continued from."""
    path = ROOT / source / 'events.jsonl'
    config = None
    with path.open() as handle:
        for line in handle:
            if '"kind":"configuration"' in line:
                config = json.loads(line)['config']; break
    mine = usage_of(path, game)
    resumed = config.get('resume_actions') or 0
    total, chain = dict(mine), [source.split('/')[-1]]
    if resumed and len((config.get('games') or [])) == 1:
        earlier = usage_of(ROOT / config['resume_events'], game, upto_actions=resumed)
        total = add(mine, {**earlier, 'actions': 0})
        chain.append(str(config['resume_events']).split('/')[-1] + ' (first %d actions, %d replies)' % (resumed, earlier['replies']))
    return total, chain

card = json.load(open(ROOT / 'reports/baseline_continue_v1/data/scorecard_replay_manifest_3.json'))
rows = []
for b in sorted(card['expected'], key=lambda r: r['game']):
    game = b['game']
    base, chain = baseline(game, b['source'])
    stamp, parts = V.counted(game)
    state = W.state_of(parts[-1])
    mine = usage_of(parts[-1] / 'events.jsonl', game)
    rows.append({'game': game.split('-')[0], 'state': state, 'base': base, 'mine': mine, 'base_actions': b['actions'], 'chain': chain})
    print(game.split('-')[0], state, '| baseline: actions %d, replies %d, in %.2fM, out %.2fM (thinking %.0f%%), $%.0f | layers: actions %d, replies %d, in %.2fM, out %.2fM (thinking %.0f%%), $%.0f | %s'
          % (b['actions'], base['replies'], base['in'] / 1e6, base['out'] / 1e6, 100 * base['think'] / max(1, base['out']), base['cost'],
             mine['actions'], mine['replies'], mine['in'] / 1e6, mine['out'] / 1e6, 100 * mine['think'] / max(1, mine['out']), mine['cost'], ' + '.join(chain)[:150]))
totals = {}
for label, rs in (('finished games', [r for r in rows if r['state'] != 'running']), ('still playing, so far', [r for r in rows if r['state'] == 'running'])):
    if not rs:
        continue
    B = {k: sum(r['base'][k] for r in rs) for k in ('replies', 'in', 'out', 'think', 'cost')}; M = {k: sum(r['mine'][k] for r in rs) for k in ('replies', 'in', 'out', 'think', 'cost', 'actions')}
    ba = sum(r['base_actions'] for r in rs)
    print('%s (%d): baseline actions %d, replies %d, in %.1fM, out %.1fM, thinking %.1fM, notional $%.0f | layers actions %d, replies %d, in %.1fM, out %.1fM, thinking %.1fM, notional $%.0f'
          % (label, len(rs), ba, B['replies'], B['in'] / 1e6, B['out'] / 1e6, B['think'] / 1e6, B['cost'], M['actions'], M['replies'], M['in'] / 1e6, M['out'] / 1e6, M['think'] / 1e6, M['cost']))
    print('   per action: baseline in %.0f out %.0f | layers in %.0f out %.0f' % (B['in'] / ba, B['out'] / ba, M['in'] / M['actions'], M['out'] / M['actions']))
    print('   per reply:  baseline in %.0f out %.0f | layers in %.0f out %.0f' % (B['in'] / B['replies'], B['out'] / B['replies'], M['in'] / M['replies'], M['out'] / M['replies']))
    totals[label] = {'games': [r['game'] for r in rs], 'baseline': {**B, 'actions': ba}, 'layers': M,
                     'fewer_tokens_with_the_layers_percent': {
                         'input': round(100 * (1 - M['in'] / B['in']), 1), 'output': round(100 * (1 - M['out'] / B['out']), 1),
                         'input_and_output': round(100 * (1 - (M['in'] + M['out']) / (B['in'] + B['out'])), 1)}}
(ROOT / 'reports/level_brief_v1/token_usage.json').write_text(json.dumps({'games': rows, 'totals': totals}, indent=1) + '\n')
