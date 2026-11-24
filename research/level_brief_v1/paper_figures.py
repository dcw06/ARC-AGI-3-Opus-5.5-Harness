"""Figures for the paper: one real moment from the whole-game runs for each layer, drawn from the run logs.

Each figure shows boards exactly as the game returned them (64 by 64 cells, ARC's 16 colours), with the action
marked. What the model wrote at that moment is not drawn into the image; it is in figures/README.md, word for
word, with the game, the action number and the log it comes from, so that it can be quoted in a caption.

    lessons-game-over    wa30, level 5: the action that used up the level's action budget, and the board after it
    lessons-no-effect    ka59, level 1: a click that changed nothing
    frames-between       dc22, level 5: a click after which the board changes and changes back, so that the final
                         board is the one before it
    object-ledger        wa30, first turn of level 5: the things the harness listed, outlined and named
    level-brief          wa30, level 5 to level 6: the board shown as completion feedback, and the new level

    paper_figures.py            writes reports/level_brief_v1/figures/*.png, panels/*.png and README.md

Each board of a figure is also written alone, with no title, as figures/panels/<figure>-<a, b, ...>.png, so that
a paper can set the boards and their titles itself.

Usage (project environment), from the repository root. Needs the local run logs. No model call.
"""
import json
import sys
from pathlib import Path

import numpy as np
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research'))
from research.level_brief_v1 import whole_verify as V  # noqa: E402

OUT = ROOT / 'reports/level_brief_v1/figures'
PALETTE = ['#FFFFFF', '#CCCCCC', '#999999', '#666666', '#333333', '#000000', '#E53AA3', '#FF7BCC', '#F93C31', '#1E93FF',
           '#88D8F1', '#FFDC00', '#FF851B', '#921231', '#4FCC30', '#A356D6']        # as the replay pages draw them
RGB = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in PALETTE], dtype=np.uint8)
CELL, GAP, PAD, TITLE = 12, 36, 24, 44          # pixels: one cell, between boards, around the figure, title band
INK, PAPER, MARK = (24, 34, 43), (255, 255, 255), (255, 255, 255)
FONT = font_manager.findfont('DejaVu Sans')
BOLD = font_manager.findfont(font_manager.FontProperties(family='DejaVu Sans', weight='bold'))


def load(game):
    """(run folder, transitions, {action index: reply}, {action index: request body}) of the game's counted run."""
    _, parts = V.counted(game)
    transitions, replies, bodies, at = [], {}, {}, None
    with (parts[-1] / 'events.jsonl').open() as handle:
        for line in handle:
            if '"kind":"transition"' in line:
                transitions.append(json.loads(line))
            elif '"kind":"model_entered"' in line:
                event = json.loads(line)
                at = event['action_index']
                bodies[at] = json.loads(event['request']['messages'][1]['content'])
            elif '"kind":"model_returned"' in line:
                replies[at] = json.loads(json.loads(line)['content'])
    return parts[-1], transitions, replies, bodies


def board(frame):
    """A 64 by 64 frame of colour numbers as an image, CELL pixels a cell."""
    cells = np.asarray(frame, dtype=np.uint8)
    return Image.fromarray(np.kron(RGB[cells], np.ones((CELL, CELL, 1), dtype=np.uint8)))


def from_hex(rows):
    """The harness's text board ("yy|" then hexadecimal cells in groups of 8) back to colour numbers."""
    return np.array([[int(c, 16) for c in row.split('|', 1)[1].replace(' ', '')] for row in rows], dtype=np.uint8)


def ring(image, x, y):
    """Mark a clicked cell: a white ring with a dark edge, readable on any colour."""
    draw = ImageDraw.Draw(image)
    cx, cy, r = x * CELL + CELL // 2, y * CELL + CELL // 2, int(CELL * 2.2)
    draw.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], outline=INK, width=8)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=MARK, width=4)


def outline(image, box, name):
    """Outline one listed thing (x first, y first, x last, y last) and write the ledger's name for its look."""
    draw = ImageDraw.Draw(image)
    x0, y0, x1, y1 = box[0] * CELL, box[1] * CELL, (box[2] + 1) * CELL - 1, (box[3] + 1) * CELL - 1
    draw.rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], outline=INK, width=5)
    draw.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], outline=MARK, width=2)
    font = ImageFont.truetype(BOLD, 20)
    width = draw.textlength(name, font=font)
    tx = min(max(x0 - 2, 2), image.width - width - 10)
    ty = y0 - 30 if y0 >= 34 else y1 + 6
    draw.rectangle([tx, ty, tx + width + 8, ty + 25], fill=INK)
    draw.text((tx + 4, ty + 1), name, font=font, fill=MARK)


def figure(name, panels):
    """panels: [(title, board image)] side by side on white, each with its title above and a thin frame."""
    size = 64 * CELL
    width = 2 * PAD + len(panels) * size + (len(panels) - 1) * GAP
    sheet = Image.new('RGB', (width, 2 * PAD + TITLE + size), PAPER)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT, 24)
    for n, (title, image) in enumerate(panels):
        left = PAD + n * (size + GAP)
        draw.text((left, PAD), title, font=font, fill=INK)
        sheet.paste(image, (left, PAD + TITLE))
        draw.rectangle([left - 1, PAD + TITLE - 1, left + size, PAD + TITLE + size], outline=(125, 136, 145), width=1)
    (OUT / 'panels').mkdir(parents=True, exist_ok=True)
    sheet.save(OUT / (name + '.png'), optimize=True)
    for n, (_, image) in enumerate(panels):
        image.save(OUT / 'panels' / ('%s-%s.png' % (name, 'abcdef'[n])), optimize=True)
    return sheet.size


def source(folder):
    return '\n\nSource log: `%s` (local; not in the repository).' % folder.name


def build():
    notes = []
    # wa30: object ledger at the first turn of level 5, the budget game over on that level, the brief for level 6
    folder, steps, replies, bodies = load('wa30-ee6fef47')
    start = next(i for i, t in enumerate(steps) if t['before']['levels_completed'] == 4)
    body, reply = bodies[start], replies[start]
    image = board(steps[start]['before']['frames'][-1])
    listed = []
    for look in body['evidence']['things']['looks']:
        for instance in look['instances']:
            outline(image, instance['at'], look['look'])
        listed.append('- **%s** (%d place%s)%s' % (look['look'], len(look['instances']), '' if len(look['instances']) == 1 else 's',
                                                  ': "%s"' % look['does'] if look.get('does') else ': no note yet'))
    size = figure('object-ledger', [('wa30, level 5, first turn: the things the harness listed', image)])
    notes.append(('object-ledger.png', 'Object ledger', size,
                  'wa30, the board before action %d (the first turn of level 5). The outlines are the places the harness '
                  'listed, each with the name the ledger gives its look. The model\'s own notes on what a look does, '
                  'carried over from earlier levels:' % (start + 1) + '\n\n' + '\n'.join(listed)
                  + '\n\nWhat the model wrote about its target on this turn: "%s"' % reply['thing_check'] + source(folder)))

    over = next(i for i in range(start, len(steps)) if steps[i]['after']['state'] == 'GAME_OVER')
    lesson_at = next(i for i in range(over, len(steps)) if replies.get(i, {}).get('game_over_lesson')
                     and 'game_over_lesson' in bodies[i]['output_contract'])
    lesson = replies[lesson_at]['game_over_lesson']
    size = figure('lessons-game-over', [
        ('wa30, level 5, before action %d' % (over + 1), board(steps[over]['before']['frames'][-1])),
        ('after it: game over, the bottom bar is used up', board(steps[over]['after']['frames'][-1]))])
    notes.append(('lessons-game-over.png', 'Lesson after a game over', size,
                  'wa30, level 5. Action %d (ACTION%d) used the last cell of the bar along the bottom row and the game '
                  'ended; the controller then reset the level. On its next turn (action %d) the model wrote this '
                  'lesson, which stayed in every later request:' % (over + 1, steps[over]['action']['action_id'], lesson_at + 1)
                  + '\n\n> Rule: %s\n>\n> Applies when: %s' % (lesson['rule'], lesson['applies_when']) + source(folder)))

    done = next(i for i, t in enumerate(steps) if t['after']['levels_completed'] == 5)
    body, reply = bodies[done + 1], replies[done + 1]
    shown, brief = body['evidence']['completed_level'], reply['level_brief']
    rules = [note['rule'] for note in reply.get('rule_notes') or ()]
    size = figure('level-brief', [
        ('wa30: the board that completed level 5', board(from_hex(shown['board']))),
        ('first board of level 6', board(steps[done + 1]['before']['frames'][-1]))])
    notes.append(('level-brief.png', 'Kept rules and the level brief', size,
                  'wa30. Action %d completed level 5. Left: the frame the harness kept as completion feedback (the last '
                  'frame the game returned before it showed the next level; %d frames came back for that action). Right: '
                  'the first board of level 6. On that turn (action %d) the model wrote this brief:'
                  % (done + 1, shown['frames_returned'], done + 2)
                  + '\n\n> Won by: %s\n>\n> Different: %s\n>\n> Why: %s\n>\n> First: %s' % (
                      brief['won_by'], brief['different'], brief['why'], brief['first'])
                  + ''.join('\n\nRule recorded on the same turn: "%s"' % rule for rule in rules) + source(folder)))

    # ka59: a click that changed nothing, and the lesson written two actions later
    folder, steps, replies, bodies = load('ka59-38d34dbb')
    lesson_at = next(i for i in sorted(replies) if replies[i].get('no_effect_lesson') and 'no_effect_lesson' in bodies[i]['output_contract'])
    case = bodies[lesson_at]['evidence']['no_effect_case']
    at = int(case['transition_id'][1:]) - 1
    click, lesson = steps[at]['action']['action_data'], replies[lesson_at]['no_effect_lesson']
    before = board(steps[at]['before']['frames'][-1])
    ring(before, click['x'], click['y'])
    size = figure('lessons-no-effect', [
        ('ka59, level 1, action %d: a click at (%d, %d)' % (at + 1, click['x'], click['y']), before),
        ('after it: nothing changed but the step counter', board(steps[at]['after']['frames'][-1]))])
    differing = int((np.asarray(steps[at]['before']['frames'][-1]) != np.asarray(steps[at]['after']['frames'][-1])).sum())
    notes.append(('lessons-no-effect.png', 'Lesson after an action that changed nothing', size,
                  'ka59, level 1. Action %d clicked the ringed cell and the board came back the same apart from the step '
                  'counter along the bottom row (%d cell%s), which the harness sets aside. The harness opened a case, and '
                  'after %d further action%s of its own the model explained it (action %d):' % (
                      at + 1, differing, ' differs' if differing == 1 else 's differ', len(case['actions_since']),
                      '' if len(case['actions_since']) == 1 else 's', lesson_at + 1)
                  + '\n\n> Rule: %s\n>\n> Applies when: %s' % (lesson['rule'], lesson['applies_when']) + source(folder)))

    # dc22: a click after which the board changes and changes back. The first action for which the harness opened
    # a no-effect case although more than 1,000 cells differ from the board before in some frame in between.
    folder, steps, replies, bodies = load('dc22-fdcac232')
    opened = sorted({int(body['evidence']['no_effect_case']['transition_id'][1:]) - 1 for body in bodies.values()
                     if body['evidence'].get('no_effect_case')})

    def differing(frame, start):
        return int((np.asarray(frame) != np.asarray(start)).sum())

    at = next(i for i in opened if max((differing(f, steps[i]['before']['frames'][-1])
                                        for f in steps[i]['after']['frames'][:-1]), default=0) > 1000)
    start, frames, click = steps[at]['before']['frames'][-1], steps[at]['after']['frames'], steps[at]['action']['action_data']
    counts = [differing(f, start) for f in frames]
    early, late = 4, 9                          # the 5th frame (the change has played) and the 10th (the board is going dark)
    lesson_at = next(i for i in sorted(replies) if i > at and replies[i].get('no_effect_lesson')
                     and bodies[i]['evidence'].get('no_effect_case', {}).get('transition_id') == 't%d' % (at + 1))
    lesson = replies[lesson_at]['no_effect_lesson']
    shown = bodies[lesson_at]['evidence']['no_effect_case']['in_between']['t%d' % (at + 1)]
    before = board(start)
    ring(before, click['x'], click['y'])
    size = figure('frames-between', [
        ('dc22, level %d, action %d: a click at (%d, %d)' % (steps[at]['before']['levels_completed'] + 1, at + 1, click['x'], click['y']), before),
        ('frame %d of %d: the change plays' % (early + 1, len(frames)), board(frames[early])),
        ('frame %d of %d: the board goes dark' % (late + 1, len(frames)), board(frames[late])),
        ('last frame: the board as it was', board(frames[-1]))])
    notes.append(('frames-between.png', 'A board that ends as it began, with changes in between', size,
                  'dc22, level %d. Action %d clicked the ringed cell. The game returned %d frames for it. Counted against '
                  'the board before the action, they differ in %s cells, in order. The change the click starts is in '
                  'place by frame %d (%d cells), the board then goes dark from the top left (%d cells in frame %d, at '
                  'most %d), and the last frame is the board before the action except for %d cell%s of the step counter '
                  'on the bottom row, which the harness sets aside. So the harness counted the action as one that '
                  'changed nothing and opened a case, and after %d further action%s of its own the model explained it '
                  '(action %d):' % (
                      steps[at]['before']['levels_completed'] + 1, at + 1, len(frames), ', '.join(str(c) for c in counts),
                      early + 1, counts[early], counts[late], late + 1, max(counts), counts[-1],
                      '' if counts[-1] == 1 else 's',
                      len(bodies[lesson_at]['evidence']['no_effect_case']['actions_since']),
                      '' if len(bodies[lesson_at]['evidence']['no_effect_case']['actions_since']) == 1 else 's', lesson_at + 1)
                  + '\n\n> Rule: %s\n>\n> Applies when: %s' % (lesson['rule'], lesson['applies_when'])
                  + '\n\nThe model is sent only the last frame of an action. A no-effect case adds a summary of '
                    'the one frame in between that differed most from the board before: here frame %d, the dark '
                    'board, reported as %d frames returned and %s cells differing (step counter aside)%s. What the '
                    'model wrote about the frames in between is its reading of that summary.' % (
                        counts.index(max(counts)) + 1, shown['frames_returned'], format(shown['cells_that_differed'], ','),
                        '' if shown['changes_in_that_frame'].get('listed', True) else ', too many to list one by one')
                  + source(folder)))

    order = ('lessons-game-over.png', 'lessons-no-effect.png', 'frames-between.png', 'object-ledger.png', 'level-brief.png')
    text = ['# Figures: moments from the runs, one or two per layer', '',
            'Boards are drawn exactly as the game returned them: 64 by 64 cells in ARC\'s 16 colours, %d pixels a cell. '
            'All five moments are from the whole-game runs with every layer on, the runs behind the final scorecard '
            '(https://arcprize.org/scorecards/96932ddf-ab6a-4354-94b2-9644447dae14). The text quoted below is what '
            'the model wrote, word for word; none of it is drawn into the images, so it can go in a caption.' % CELL, '',
            'Each board is also saved alone, with no title, in `panels/` (`<figure>-a.png`, `<figure>-b.png`, ...), '
            'left to right.', '',
            'Made by `research/level_brief_v1/paper_figures.py` from the run logs.', '']
    for name in order:
        _, title, size, note = next(n for n in notes if n[0] == name)
        text += ['## %s' % title, '', '![%s](%s)' % (title, name), '', '`%s`, %d by %d pixels.' % (name, size[0], size[1]), '', note, '']
    (OUT / 'README.md').write_text('\n'.join(text))
    for name, title, size, _ in notes:
        print(name, size, title)


if __name__ == '__main__':
    build()
