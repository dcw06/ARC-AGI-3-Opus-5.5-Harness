"""What the baseline wrote about the fatal tiles of bp35 level 2, reply by reply, in the saved run of 6 November.

The run lost on level 2 at actions 23, 48 and 78, each time when its piece rose to a purple tile with a
yellow-white-yellow underside (colours f and b0b in the text board). This prints, for every reply from the first
game over to just after the second, the notes that mention those tiles, with their status, and shows when the
fatal action left the transitions the model is sent. It reads the saved log only: no model call, no game.

    rule_trace.py <out.json>

Usage (project environment), from the repository root. Needs the local run log.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAVED = ROOT / '.cache/claude_arc_runs/opus55-competition-20261106T054112Z/events.jsonl'
CONFIG = ROOT / 'config/claude_arc_v1.opus55_competition.json'
GAME = 'bp35-0a0ad940'
ABOUT = r'b0b|hazard|spike'                      # a note is about the tiles if its statement matches this


def trace():
    steps, notes, shown, at = [], {}, {}, None
    for line in SAVED.open():
        if '"game_id":"%s"' % GAME not in line:
            continue
        if '"kind":"transition"' in line:
            steps.append(json.loads(line))
        elif '"kind":"model_entered"' in line:
            event = json.loads(line)
            at = event['action_index'] + 1          # the action this reply chooses, counted from 1
            body = json.loads(event['request']['messages'][1]['content'])
            shown[at] = [entry['transition_id'] for entry in body['evidence']['history']]
        elif '"kind":"model_returned"' in line:
            notes[at] = json.loads(json.loads(line)['content']).get('hypotheses') or []
    overs = [n + 1 for n, step in enumerate(steps) if step['after']['state'] == 'GAME_OVER']
    first, second = overs[0], overs[1]
    limit = json.loads(CONFIG.read_text())['history_limit']
    rows = []
    for action in range(first, second + 3):
        if action not in notes:                     # the level reset after a game over is the controller's action
            continue
        about = [{'id': h['id'], 'status': h['status'], 'statement': h['statement'], 'evidence_ids': h.get('evidence_ids', [])}
                 for h in notes[action] if re.search(ABOUT, h['statement'])]
        rows.append({'reply_choosing_action': action, 'notes_in_reply': len(notes[action]), 'notes_about_the_tiles': about})
    gone = next(a for a in sorted(shown) if a > first and 't%d' % first not in shown[a])
    return {
        'what': 'The notes of the baseline (no layers) about the fatal tiles of bp35 level 2, from the saved run of '
                '6 November 2026, which is the first 100 actions of the baseline trajectory.',
        'made_by': 'research/memory_fix_v1/rule_trace.py', 'game': GAME,
        'level': steps[first - 1]['before']['levels_completed'] + 1,
        'game_overs_at_actions': overs,
        'fatal_actions': {str(a): steps[a - 1]['action'] for a in (first, second)},
        'transitions_sent_with_a_request': limit,
        'first_request_without_the_fatal_action': {'reply_choosing_action': gone, 'transitions_sent': shown[gone],
                                                   'sent_with_the_request_before': shown[gone - 1]},
        'a_note_is_about_the_tiles_if_it_matches': ABOUT,
        'replies': rows}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    value = trace()
    Path(sys.argv[1]).write_text(json.dumps(value, indent=1) + '\n')
    for row in value['replies']:
        first = row['notes_about_the_tiles'][:1]
        print(row['reply_choosing_action'], '|', ' '.join('%s: %s' % (h['status'], h['statement'][:90]) for h in first) or 'no note about the tiles')
    print('game overs at', value['game_overs_at_actions'], '| fatal action gone from the request choosing action',
          value['first_request_without_the_fatal_action']['reply_choosing_action'])
