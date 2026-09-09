"""Interface pieces.

The HUD is what a player looks at for the whole session, so it gets the same
treatment as the sprites: real bevels, one light direction, and a palette that
belongs with the rest of the pack — aged parchment and leather behind, worked
metal on the edges.

Panels are nine-slice sources: 48x48 with 16px corners, so a client can stretch
the middle. Bars, slots and icons are fixed size.
"""
from __future__ import annotations

import math

from forge import pigment
from forge.brush import Sketch, catmull, taper_shape
from forge.pigment import blend, ramp

SLICE = 48        # nine-slice source size
CORNER = 16       # slice inset
BAR_W, BAR_H = 128, 14
SLOT = 40
ICON = 16
CURSOR = 16

PARCHMENT = '#c9b territory'.replace(' territory', '8a')   # #c9b8a
LEATHER = '#6a4f38'
FRAME = '#8a7350'
IRON = '#8d949c'
DARK = '#2e2a30'


PANELS = {
    # name: (fill, frame, inset depth, whether the middle is sunken)
    'window': ('#4a4038', '#8a7350', 3, False),
    'tooltip': ('#3a3640', '#7a7286', 2, False),
    'inset': ('#332e2c', '#6a5c48', 2, True),
    'banner': ('#6a3f3a', '#c0a24a', 3, False),
}


def panel(name):
    """A nine-slice source: bevelled frame, textured field, corner studs."""
    fill, edge, depth, sunken = PANELS.get(name, PANELS['window'])
    sketch = Sketch((SLICE, SLICE))
    body = sketch.piece(ramp(fill))
    body.rect((0, 0, SLICE - 1, SLICE - 1), 3)
    sketch.stamp(body, outline=False, rim=0, occlude=0)

    grain = sketch.piece(ramp(fill))
    for y in range(2, SLICE - 2, 5):
        grain.line([(2, y), (SLICE - 3, y)], 2, 1)
    grain.dither((0, 0, SLICE - 1, SLICE - 1), 4, level=2)
    sketch.overlay(grain)

    frame = sketch.piece(ramp(edge))
    frame.rect((0, 0, SLICE - 1, SLICE - 1), 3)
    frame.erase((depth + 1, depth + 1, SLICE - depth - 2, SLICE - depth - 2))
    sketch.stamp(frame, outline=False, rim=0, occlude=0)

    light = sketch.piece(ramp(edge))
    outer = 5 if sunken else 4
    light.line([(0, 0), (SLICE - 1, 0)], outer, 1)
    light.line([(0, 0), (0, SLICE - 1)], outer, 1)
    light.line([(SLICE - 1, 1), (SLICE - 1, SLICE - 1)], 1, 1)
    light.line([(1, SLICE - 1), (SLICE - 1, SLICE - 1)], 1, 1)
    inner = depth
    light.line([(inner, SLICE - inner - 1), (SLICE - inner - 1, SLICE - inner - 1)],
               5 if sunken else 1, 1)
    light.line([(SLICE - inner - 1, inner), (SLICE - inner - 1, SLICE - inner - 1)],
               5 if sunken else 1, 1)
    light.line([(inner, inner), (SLICE - inner - 1, inner)], 1 if sunken else 5, 1)
    light.line([(inner, inner), (inner, SLICE - inner - 1)], 1 if sunken else 5, 1)
    sketch.overlay(light)

    studs = sketch.piece(ramp(edge))
    for sx, sy in ((5, 5), (SLICE - 6, 5), (5, SLICE - 6), (SLICE - 6, SLICE - 6)):
        studs.disc(sx, sy, 2.0, 4)
        studs.dot(sx - 1, sy - 1, 5)
    sketch.stamp(studs, outline=False, rim=0, occlude=0)
    outline = sketch.piece(ramp(DARK))
    outline.rect((0, 0, SLICE - 1, SLICE - 1), 0)
    outline.erase((1, 1, SLICE - 2, SLICE - 2))
    sketch.overlay(outline)
    return sketch.result()


# ---------------------------------------------------------------- buttons --

BUTTON_W, BUTTON_H = 48, 20
BUTTON_STYLES = {'plain': ('#5f5348', '#8a7350'), 'primary': ('#6a5230', '#c0a24a')}
BUTTON_STATES = ('normal', 'hover', 'pressed', 'disabled')


def button(style, state):
    fill, edge = BUTTON_STYLES.get(style, BUTTON_STYLES['plain'])
    if state == 'hover':
        fill = pigment.hexstr(blend(pigment.rgb(fill), (255, 240, 200, 255), 0.16))
    elif state == 'disabled':
        fill = pigment.hexstr(blend(pigment.rgb(fill), (110, 108, 112, 255), 0.55))
        edge = pigment.hexstr(blend(pigment.rgb(edge), (110, 108, 112, 255), 0.55))
    sketch = Sketch((BUTTON_W, BUTTON_H))
    drop = 1 if state == 'pressed' else 0
    body = sketch.piece(ramp(fill))
    body.poly(catmull([(2, 2 + drop), (BUTTON_W - 3, 2 + drop), (BUTTON_W - 2, 5 + drop),
                       (BUTTON_W - 2, BUTTON_H - 4), (BUTTON_W - 4, BUTTON_H - 2),
                       (3, BUTTON_H - 2), (1, BUTTON_H - 5), (1, 5 + drop)], 4, closed=True), 3)
    sketch.carve(body, rim=0.0 if state == 'pressed' else 0.95,
                 occlude=0.9 if state == 'pressed' else 0.7, form=0.5, gleam=0.0)
    edging = sketch.piece(ramp(edge))
    edging.line([(4, 2 + drop), (BUTTON_W - 5, 2 + drop)], 4 if state != 'pressed' else 1, 1)
    edging.line([(4, BUTTON_H - 2), (BUTTON_W - 5, BUTTON_H - 2)], 1, 1)
    sketch.overlay(edging)
    outline = sketch.piece(ramp(DARK))
    outline.poly(catmull([(2, 1 + drop), (BUTTON_W - 3, 1 + drop), (BUTTON_W - 1, 5 + drop),
                          (BUTTON_W - 1, BUTTON_H - 4), (BUTTON_W - 3, BUTTON_H - 1),
                          (2, BUTTON_H - 1), (0, BUTTON_H - 5), (0, 5 + drop)], 4, closed=True), 0)
    outline.erase(points=catmull([(3, 2 + drop), (BUTTON_W - 4, 2 + drop), (BUTTON_W - 2, 6 + drop),
                                  (BUTTON_W - 2, BUTTON_H - 5), (BUTTON_W - 4, BUTTON_H - 2),
                                  (3, BUTTON_H - 2), (1, BUTTON_H - 6), (1, 6 + drop)], 4, closed=True))
    sketch.overlay(outline)
    return sketch.result()


# ------------------------------------------------------------------- bars --

BARS = {
    'health': '#b2453c', 'mana': '#4a72c0', 'stamina': '#c0a24a',
    'experience': '#7fb04a', 'cast': '#a98fd0', 'enemy': '#8a4a4a',
}


def bar_frame():
    sketch = Sketch((BAR_W, BAR_H))
    body = sketch.piece(ramp('#2b2724'))
    body.poly(catmull([(2, 1), (BAR_W - 3, 1), (BAR_W - 1, BAR_H // 2),
                       (BAR_W - 3, BAR_H - 2), (2, BAR_H - 2), (0, BAR_H // 2)], 4, closed=True), 3)
    sketch.stamp(body, outline=False, rim=0, occlude=0)
    rim = sketch.piece(ramp(FRAME))
    rim.poly(catmull([(2, 0), (BAR_W - 3, 0), (BAR_W - 1, BAR_H // 2),
                      (BAR_W - 3, BAR_H - 1), (2, BAR_H - 1), (0, BAR_H // 2)], 4, closed=True), 3)
    rim.erase(points=catmull([(3, 2), (BAR_W - 4, 2), (BAR_W - 2, BAR_H // 2),
                              (BAR_W - 4, BAR_H - 3), (3, BAR_H - 3), (1, BAR_H // 2)], 4, closed=True))
    sketch.carve(rim, rim=0.95, occlude=0.8, form=0.0, gleam=0.0)
    for x in (BAR_W // 4, BAR_W // 2, BAR_W * 3 // 4):
        tick = sketch.piece(ramp(FRAME))
        tick.line([(x, 2), (x, BAR_H - 3)], 1, 1)
        sketch.overlay(tick)
    return sketch.result()


def bar_fill(kind):
    colour = BARS.get(kind, '#b2453c')
    width, height = BAR_W - 6, BAR_H - 6
    sketch = Sketch((width, height))
    body = sketch.piece(ramp(colour))
    body.rect((0, 0, width - 1, height - 1), 3)
    sketch.stamp(body, outline=False, rim=0, occlude=0)
    shine = sketch.piece(ramp(colour))
    shine.line([(0, 1), (width - 1, 1)], 5, 1)
    shine.line([(0, 2), (width - 1, 2)], 4, 1)
    shine.line([(0, height - 2), (width - 1, height - 2)], 1, 1)
    sketch.overlay(shine)
    gloss = sketch.piece(ramp(colour))
    for x in range(0, width, 8):
        gloss.poly([(x, 0), (x + 3, 0), (x - 1, height - 1), (x - 4, height - 1)], 4)
    gloss.image.putalpha(gloss.image.getchannel('A').point(lambda v: round(v * 0.30)))
    sketch.overlay(gloss)
    return sketch.result()


# ------------------------------------------------------------------ slots --

RARITY = (
    ('common', '#8a8578'), ('uncommon', '#6f9a5c'), ('fine', '#5f86b0'),
    ('rare', '#8a6ac0'), ('epic', '#c08a3c'), ('legendary', '#c85f45'),
    ('mythic', '#7fc4d8'), ('relic', '#e0c47a'),
)


def slot(kind='empty'):
    sketch = Sketch((SLOT, SLOT))
    well = sketch.piece(ramp('#332f2c'))
    well.rect((2, 2, SLOT - 3, SLOT - 3), 3)
    sketch.stamp(well, outline=False, rim=0, occlude=0)
    depth = sketch.piece(ramp('#332f2c'))
    depth.line([(3, 3), (SLOT - 4, 3)], 0, 1)
    depth.line([(3, 3), (3, SLOT - 4)], 0, 1)
    depth.line([(4, SLOT - 4), (SLOT - 4, SLOT - 4)], 4, 1)
    depth.line([(SLOT - 4, 4), (SLOT - 4, SLOT - 4)], 4, 1)
    sketch.overlay(depth)
    rim = sketch.piece(ramp(FRAME))
    rim.rect((0, 0, SLOT - 1, SLOT - 1), 3)
    rim.erase((3, 3, SLOT - 4, SLOT - 4))
    sketch.carve(rim, rim=0.95, occlude=0.8, form=0.0, gleam=0.0)
    if kind == 'hotbar':
        for cx, cy in ((2, 2), (SLOT - 3, 2), (2, SLOT - 3), (SLOT - 3, SLOT - 3)):
            stud = sketch.piece(ramp(IRON))
            stud.disc(cx, cy, 1.6, 4)
            sketch.stamp(stud, outline=False, rim=0, occlude=0)
    elif kind == 'equipment':
        mark = sketch.piece(ramp('#6a5c48'))
        mark.poly([(SLOT / 2, 9), (SLOT / 2 + 7, SLOT / 2), (SLOT / 2, SLOT - 9),
                   (SLOT / 2 - 7, SLOT / 2)], 2)
        mark.image.putalpha(mark.image.getchannel('A').point(lambda v: round(v * 0.5)))
        sketch.overlay(mark)
    outline = sketch.piece(ramp(DARK))
    outline.rect((0, 0, SLOT - 1, SLOT - 1), 0)
    outline.erase((1, 1, SLOT - 2, SLOT - 2))
    sketch.overlay(outline)
    return sketch.result()


def rarity_frame(name, colour):
    """A glowing border a client lays over a filled slot."""
    sketch = Sketch((SLOT, SLOT))
    rim = sketch.piece(ramp(colour))
    rim.rect((0, 0, SLOT - 1, SLOT - 1), 3)
    rim.erase((2, 2, SLOT - 3, SLOT - 3))
    sketch.carve(rim, rim=0.95, occlude=0.7, form=0.0, gleam=0.0)
    corners = sketch.piece(ramp(colour))
    for cx, cy, sx, sy in ((1, 1, 1, 1), (SLOT - 2, 1, -1, 1),
                           (1, SLOT - 2, 1, -1), (SLOT - 2, SLOT - 2, -1, -1)):
        corners.poly([(cx, cy), (cx + sx * 7, cy), (cx + sx * 7, cy + sy * 2),
                      (cx + sx * 2, cy + sy * 2), (cx + sx * 2, cy + sy * 7),
                      (cx, cy + sy * 7)], 5)
    sketch.stamp(corners, outline=False, rim=0, occlude=0)
    if name in ('legendary', 'mythic', 'relic', 'epic'):
        sketch.glow(colour, 3, 0.55)
    return sketch.result()


# ------------------------------------------------------------------ icons --

ICONS = ('close', 'settings', 'bag', 'map', 'quest', 'coin', 'lock', 'plus', 'minus',
         'arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'star', 'heart',
         'shield', 'sword', 'search', 'chat', 'trash', 'skull', 'clock')


def icon(name):
    sketch = Sketch((ICON, ICON))
    tone = ramp('#d8cfb8')
    piece = sketch.piece(tone)
    c = ICON / 2
    if name == 'close':
        piece.line([(4, 4), (ICON - 5, ICON - 5)], 3, 2)
        piece.line([(ICON - 5, 4), (4, ICON - 5)], 3, 2)
    elif name == 'settings':
        for index in range(8):
            angle = index * math.tau / 8
            piece.poly(taper_shape((c + math.cos(angle) * 3.4, c + math.sin(angle) * 3.4),
                                   (c + math.cos(angle) * 6.6, c + math.sin(angle) * 6.6),
                                   3.6, 2.4), 3)
        piece.disc(c, c, 4.6, 3)
        piece.erase_ellipse((c - 2.0, c - 2.0, c + 2.0, c + 2.0))
    elif name == 'bag':
        piece.poly(catmull([(3, 6), (ICON - 4, 6), (ICON - 3, ICON - 2), (2, ICON - 2)],
                           4, closed=True), 3)
        piece.arc((5, 1, ICON - 6, 9), 180, 360, 3, 2)
    elif name == 'map':
        piece.poly([(2, 3), (6, 2), (10, 4), (14, 2), (14, 13), (10, 15), (6, 13), (2, 14)], 3)
        piece.line([(6, 2), (6, 13)], 1, 1)
        piece.line([(10, 4), (10, 15)], 1, 1)
    elif name == 'quest':
        piece.poly([(4, 2), (12, 2), (12, 13), (8, 11), (4, 13)], 3)
        piece.line([(6, 5), (10, 5)], 1, 1)
        piece.line([(6, 8), (10, 8)], 1, 1)
    elif name == 'coin':
        piece = sketch.piece(ramp('#d0a63f'))
        piece.disc(c, c, 6.0, 3)
        piece.disc(c - 1, c - 1, 2.4, 5)
    elif name == 'lock':
        piece.arc((4, 2, 12, 10), 180, 360, 3, 2)
        piece.rect((3, 7, 13, 14), 3)
        piece.disc(c, 10.4, 1.4, 0)
    elif name in ('plus', 'minus'):
        piece.rect((3, 7, 13, 9), 3)
        if name == 'plus':
            piece.rect((7, 3, 9, 13), 3)
    elif name.startswith('arrow'):
        direction = name.split('_')[1]
        tips = {'up': [(c, 2), (13, 9), (10, 9), (10, 14), (6, 14), (6, 9), (3, 9)],
                'down': [(c, 14), (13, 7), (10, 7), (10, 2), (6, 2), (6, 7), (3, 7)],
                'left': [(2, c), (9, 3), (9, 6), (14, 6), (14, 10), (9, 10), (9, 13)],
                'right': [(14, c), (7, 3), (7, 6), (2, 6), (2, 10), (7, 10), (7, 13)]}
        piece.poly(tips[direction], 3)
    elif name == 'star':
        points = []
        for index in range(10):
            angle = index * math.pi / 5 - math.pi / 2
            reach = 6.6 if index % 2 == 0 else 2.8
            points.append((c + math.cos(angle) * reach, c + math.sin(angle) * reach))
        piece = sketch.piece(ramp('#e6c065'))
        piece.poly(points, 3)
    elif name == 'heart':
        piece = sketch.piece(ramp('#b2453c'))
        piece.poly(catmull([(c, 5), (11, 2), (14, 6), (c, 14), (2, 6), (5, 2)], 5, closed=True), 3)
    elif name == 'shield':
        piece.poly(catmull([(c, 1), (13, 4), (12, 10), (c, 15), (4, 10), (3, 4)], 5, closed=True), 3)
        piece.line([(c, 4), (c, 12)], 1, 1)
    elif name == 'sword':
        piece.poly(taper_shape((4, 12), (13, 3), 3.4, 1.4), 3)
        piece.line([(3, 10), (7, 14)], 3, 2)
        piece.disc(3.0, 13.0, 1.6, 3)
    elif name == 'search':
        piece.disc(6.6, 6.6, 5.0, 3)
        piece.erase_ellipse((3.6, 3.6, 9.6, 9.6))
        piece.line([(10, 10), (14, 14)], 3, 2)
    elif name == 'chat':
        piece.poly(catmull([(2, 3), (14, 3), (14, 10), (8, 10), (5, 14), (5, 10), (2, 10)],
                           4, closed=True), 3)
    elif name == 'trash':
        piece.rect((4, 5, 12, 14), 3)
        piece.rect((3, 3, 13, 5), 3)
        piece.rect((6, 1, 10, 3), 3)
        piece.line([(6, 7), (6, 12)], 1, 1)
        piece.line([(10, 7), (10, 12)], 1, 1)
    elif name == 'skull':
        piece.poly(catmull([(3, 7), (4, 3), (8, 1), (12, 3), (13, 7), (11, 10), (11, 14),
                            (5, 14), (5, 10)], 5, closed=True), 3)
        piece.ellipse((5, 5, 7.6, 8), 0)
        piece.ellipse((8.4, 5, 11, 8), 0)
    else:  # clock
        piece.disc(c, c, 6.4, 3)
        piece.disc(c, c, 4.8, 2)
        piece.line([(c, c), (c, 4.4)], 0, 1)
        piece.line([(c, c), (11.2, c)], 0, 1)
    sketch.carve(piece, rim=0.9, occlude=0.7, form=0.0, gleam=0.0)
    return sketch.result()


# ---------------------------------------------------------------- cursors --

CURSORS = ('pointer', 'hand', 'attack', 'gather', 'talk', 'deny')


def cursor(name):
    sketch = Sketch((CURSOR, CURSOR))
    tone = ramp('#e4dcc4')
    piece = sketch.piece(tone)
    if name == 'pointer':
        piece.poly([(1, 0), (1, 12), (4, 9), (6, 14), (8, 13), (6, 8), (10, 8)], 3)
    elif name == 'hand':
        piece.poly(catmull([(4, 14), (3, 8), (4, 6), (5, 8), (5, 3), (7, 3), (7, 7),
                            (8, 2), (10, 2), (10, 7), (11, 4), (13, 5), (12, 12), (9, 15)],
                           4, closed=True), 3)
    elif name == 'attack':
        piece = sketch.piece(ramp('#d8b25a'))
        for angle in (0.6, 2.2, 3.8, 5.4):
            piece.poly(taper_shape((8 + math.cos(angle) * 2.4, 8 + math.sin(angle) * 2.4),
                                   (8 + math.cos(angle) * 7.2, 8 + math.sin(angle) * 7.2),
                                   3.4, 1.0), 3)
    elif name == 'gather':
        piece.poly(taper_shape((3, 13), (11, 4), 3.0, 2.2), 3)
        piece.poly([(9, 2), (14, 5), (11, 8), (8, 5)], 3)
    elif name == 'talk':
        piece.poly(catmull([(1, 3), (14, 3), (14, 10), (7, 10), (4, 14), (4, 10), (1, 10)],
                           4, closed=True), 3)
        piece.dot(5, 6.5, 0)
        piece.dot(8, 6.5, 0)
        piece.dot(11, 6.5, 0)
    else:  # deny
        piece = sketch.piece(ramp('#b2453c'))
        piece.disc(8, 8, 6.8, 3)
        piece.erase_ellipse((3.2, 3.2, 12.8, 12.8))
        piece.poly(taper_shape((4, 12), (12, 4), 2.6, 2.6), 3)
    sketch.carve(piece, rim=0.9, occlude=0.75, form=0.0, gleam=0.0)
    return sketch.result()


# ------------------------------------------------------------------- misc --

def minimap_frame(size=96):
    sketch = Sketch((size, size))
    ring = sketch.piece(ramp(FRAME))
    ring.disc(size / 2, size / 2, size / 2 - 1, 3)
    ring.erase_ellipse((6, 6, size - 7, size - 7))
    sketch.carve(ring, rim=0.95, occlude=0.8, form=0.4, gleam=0.4)
    studs = sketch.piece(ramp(IRON))
    for index in range(8):
        angle = index * math.tau / 8
        studs.disc(size / 2 + math.cos(angle) * (size / 2 - 3.5),
                   size / 2 + math.sin(angle) * (size / 2 - 3.5), 2.2, 4)
    sketch.stamp(studs, outline=False, rim=0, occlude=0)
    marks = sketch.piece(ramp('#e4dcc4'))
    for label, angle in (('n', -math.pi / 2), ('e', 0.0), ('s', math.pi / 2), ('w', math.pi)):
        px = size / 2 + math.cos(angle) * (size / 2 - 9)
        py = size / 2 + math.sin(angle) * (size / 2 - 9)
        marks.poly([(px + math.cos(angle) * 3, py + math.sin(angle) * 3),
                    (px + math.cos(angle + 2.4) * 3, py + math.sin(angle + 2.4) * 3),
                    (px + math.cos(angle - 2.4) * 3, py + math.sin(angle - 2.4) * 3)], 4)
    sketch.stamp(marks, outline=False, rim=0, occlude=0)
    return sketch.result()


def compass(size=32):
    sketch = Sketch((size, size))
    disc = sketch.piece(ramp('#d8cfb2'))
    disc.disc(size / 2, size / 2, size / 2 - 2, 3)
    sketch.carve(disc, rim=0.95, occlude=0.8, form=0.5, gleam=0.5)
    needle = sketch.piece(ramp('#b2453c'))
    needle.poly([(size / 2, 4), (size / 2 + 4, size / 2), (size / 2, size - 4),
                 (size / 2 - 4, size / 2)], 3)
    needle.poly([(size / 2, 4), (size / 2 + 4, size / 2), (size / 2, size / 2)], 5)
    sketch.carve(needle, rim=0.9, occlude=0.6, form=0.0, gleam=0.0)
    return sketch.result()


def scroll_piece(name):
    if name == 'track':
        sketch = Sketch((12, 48))
        body = sketch.piece(ramp('#332f2c'))
        body.rect((3, 0, 8, 47), 3)
        sketch.stamp(body, outline=False, rim=0, occlude=0)
        rim = sketch.piece(ramp(FRAME))
        rim.line([(3, 0), (3, 47)], 1, 1)
        rim.line([(8, 0), (8, 47)], 4, 1)
        sketch.overlay(rim)
        return sketch.result()
    sketch = Sketch((12, 24))
    thumb = sketch.piece(ramp(FRAME))
    thumb.poly(catmull([(2, 2), (9, 2), (11, 6), (11, 18), (9, 22), (2, 22), (0, 18), (0, 6)],
                       4, closed=True), 3)
    sketch.carve(thumb, rim=0.95, occlude=0.8, form=0.5, gleam=0.3)
    grip = sketch.piece(ramp(FRAME))
    for y in (10, 12, 14):
        grip.line([(3, y), (8, y)], 1, 1)
    sketch.overlay(grip)
    return sketch.result()


def checkbox(checked):
    sketch = Sketch((ICON, ICON))
    box = sketch.piece(ramp('#332f2c'))
    box.rect((1, 1, ICON - 2, ICON - 2), 3)
    sketch.stamp(box, outline=False, rim=0, occlude=0)
    rim = sketch.piece(ramp(FRAME))
    rim.rect((0, 0, ICON - 1, ICON - 1), 3)
    rim.erase((2, 2, ICON - 3, ICON - 3))
    sketch.carve(rim, rim=0.95, occlude=0.8, form=0.0, gleam=0.0)
    if checked:
        tick = sketch.piece(ramp('#7fb04a'))
        tick.line([(4, 8), (7, 11), (12, 4)], 4, 2)
        sketch.stamp(tick, outline=False, rim=0, occlude=0)
    return sketch.result()


def divider(width=96):
    sketch = Sketch((width, 6))
    line = sketch.piece(ramp(FRAME))
    line.line([(6, 3), (width - 7, 3)], 3, 1)
    line.line([(6, 4), (width - 7, 4)], 5, 1)
    sketch.overlay(line)
    knot = sketch.piece(ramp(FRAME))
    knot.poly([(width / 2, 0), (width / 2 + 5, 3), (width / 2, 5), (width / 2 - 5, 3)], 3)
    sketch.carve(knot, rim=0.9, occlude=0.6, form=0.0, gleam=0.0)
    return sketch.result()


def plan():
    """Every interface piece, as (key, maker) pairs."""
    out = [('ui/panel_' + name, lambda n=name: panel(n)) for name in PANELS]
    for style in BUTTON_STYLES:
        for state in BUTTON_STATES:
            out.append(('ui/button_%s_%s' % (style, state),
                        lambda s=style, st=state: button(s, st)))
    out.append(('ui/bar_frame', bar_frame))
    out += [('ui/bar_' + kind, lambda k=kind: bar_fill(k)) for kind in BARS]
    out += [('ui/slot_' + kind, lambda k=kind: slot(k))
            for kind in ('empty', 'hotbar', 'equipment')]
    out += [('ui/rarity_' + name, lambda n=name, c=colour: rarity_frame(n, c))
            for name, colour in RARITY]
    out += [('ui/icon_' + name, lambda n=name: icon(n)) for name in ICONS]
    out += [('ui/cursor_' + name, lambda n=name: cursor(n)) for name in CURSORS]
    out.append(('ui/minimap_frame', minimap_frame))
    out.append(('ui/compass', compass))
    out.append(('ui/scroll_track', lambda: scroll_piece('track')))
    out.append(('ui/scroll_thumb', lambda: scroll_piece('thumb')))
    out.append(('ui/checkbox_on', lambda: checkbox(True)))
    out.append(('ui/checkbox_off', lambda: checkbox(False)))
    out.append(('ui/divider', divider))
    return out
