"""Ability and skill icons.

An ability icon is built from two readable parts: the element says what the
magic is made of, the kind says what it does to the target. A frost cone and a
frost shield share a palette but never share a silhouette. A deterministic
accent drawn from the ability id keeps same element, same kind pairs apart.
"""
from __future__ import annotations

import math

from . import pigment, smith
from .brush import Sketch, catmull, taper_shape
from .pigment import blend, keyed, ramp

ICON = 32
C = 16.0


# ------------------------------------------------------------- elements ----

def _flame(sketch, tone, cx=16, cy=17, size=1.0):
    piece = sketch.piece(tone)
    piece.poly(catmull([
        (cx - 8 * size, cy + 8 * size), (cx - 9 * size, cy - 1 * size), (cx - 4 * size, cy - 7 * size),
        (cx - 2 * size, cy - 2 * size), (cx + 1 * size, cy - 12 * size), (cx + 6 * size, cy - 3 * size),
        (cx + 9 * size, cy + 3 * size), (cx + 5 * size, cy + 10 * size), (cx - 3 * size, cy + 10 * size),
    ], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.45)
    core = sketch.piece(tone)
    core.poly(catmull([
        (cx - 3 * size, cy + 7 * size), (cx - 4 * size, cy), (cx - 1 * size, cy - 6 * size),
        (cx + 1 * size, cy - 1 * size), (cx + 4 * size, cy + 2 * size), (cx + 2 * size, cy + 8 * size),
    ], 5, closed=True), 5)
    core.clip(piece)
    sketch.overlay(core)
    return piece


def _shard(sketch, tone, cx=16, cy=16, size=1.0):
    piece = sketch.piece(tone)
    for angle, length in ((-90, 12), (-20, 9), (60, 10), (150, 8), (210, 9)):
        rad = math.radians(angle)
        tip = (cx + math.cos(rad) * length * size, cy + math.sin(rad) * length * size)
        piece.poly(taper_shape((cx, cy), tip, 6.0 * size, 1.4 * size), 3)
    sketch.stamp(piece, rim=0.95, occlude=0.5)
    face = sketch.piece(tone)
    for angle, length in ((-90, 12), (60, 10), (210, 9)):
        rad = math.radians(angle)
        face.poly(taper_shape((cx, cy), (cx + math.cos(rad) * length * size * 0.8,
                                         cy + math.sin(rad) * length * size * 0.8), 2.4 * size, 0.9 * size), 5)
    face.clip(piece)
    sketch.overlay(face)
    return piece


def _bolt(sketch, tone, cx=16, cy=16, size=1.0):
    piece = sketch.piece(tone)
    piece.poly([(cx + 3 * size, cy - 13 * size), (cx - 7 * size, cy + 1 * size),
                (cx - 1 * size, cy + 1 * size), (cx - 4 * size, cy + 13 * size),
                (cx + 8 * size, cy - 3 * size), (cx + 2 * size, cy - 3 * size)], 3)
    sketch.stamp(piece, rim=0.95, occlude=0.4)
    hot = sketch.piece(tone)
    hot.poly([(cx + 2 * size, cy - 10 * size), (cx - 4 * size, cy - 0.5 * size),
              (cx - 0.5 * size, cy - 0.5 * size), (cx + 1 * size, cy - 4 * size)], 5)
    hot.clip(piece)
    sketch.overlay(hot)
    return piece


def _leaf(sketch, tone, cx=16, cy=16, size=1.0, poison=False):
    piece = sketch.piece(tone)
    for angle in (-120, -20, 100):
        rad = math.radians(angle)
        tip = (cx + math.cos(rad) * 12 * size, cy + math.sin(rad) * 12 * size)
        mid = (cx + math.cos(rad) * 6 * size, cy + math.sin(rad) * 6 * size)
        wide = (mid[0] - math.sin(rad) * 5 * size, mid[1] + math.cos(rad) * 5 * size)
        other = (mid[0] + math.sin(rad) * 5 * size, mid[1] - math.cos(rad) * 5 * size)
        piece.poly(catmull([(cx, cy), wide, tip, other], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.55)
    veins = sketch.piece(tone)
    for angle in (-120, -20, 100):
        rad = math.radians(angle)
        veins.line([(cx, cy), (cx + math.cos(rad) * 11 * size, cy + math.sin(rad) * 11 * size)], 5, 1)
    veins.clip(piece)
    sketch.overlay(veins)
    if poison:
        drop = sketch.piece(ramp('#7f9a3c'))
        drop.poly(catmull([(cx + 6, cy + 6), (cx + 9, cy + 10), (cx + 6, cy + 13), (cx + 3, cy + 10)], 5, closed=True), 3)
        sketch.stamp(drop, rim=0.9, occlude=0.4)
    return piece


def _star(sketch, tone, cx=16, cy=16, size=1.0, points=4):
    piece = sketch.piece(tone)
    shape = []
    for index in range(points * 2):
        angle = index * math.pi / points - math.pi / 2
        radius = (13 if index % 2 == 0 else 4.5) * size
        shape.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    piece.poly(shape, 3)
    sketch.stamp(piece, rim=0.95, occlude=0.45)
    inner = sketch.piece(tone)
    inner.disc(cx, cy, 4.0 * size, 5)
    inner.clip(piece)
    sketch.overlay(inner)
    return piece


def _sun(sketch, tone, cx=16, cy=16, size=1.0):
    piece = sketch.piece(tone)
    for index in range(8):
        angle = index * math.tau / 8
        piece.poly(taper_shape((cx + math.cos(angle) * 5 * size, cy + math.sin(angle) * 5 * size),
                               (cx + math.cos(angle) * 14 * size, cy + math.sin(angle) * 14 * size),
                               4.4 * size, 1.2 * size), 3)
    piece.disc(cx, cy, 7 * size, 3)
    sketch.stamp(piece, rim=0.95, occlude=0.4)
    core = sketch.piece(tone)
    core.disc(cx, cy, 4.6 * size, 5)
    core.clip(piece)
    sketch.overlay(core)
    return piece


def _shadow(sketch, tone, cx=16, cy=16, size=1.0):
    piece = sketch.piece(tone)
    piece.poly(catmull([
        (cx - 10 * size, cy + 4 * size), (cx - 8 * size, cy - 6 * size), (cx, cy - 12 * size),
        (cx + 8 * size, cy - 6 * size), (cx + 10 * size, cy + 4 * size), (cx + 5 * size, cy + 11 * size),
        (cx, cy + 6 * size), (cx - 5 * size, cy + 11 * size),
    ], 6, closed=True), 2)
    sketch.stamp(piece, rim=0.7, occlude=0.4)
    eyes = sketch.piece(ramp('#e6dcc2'))
    for sign in (-1, 1):
        eyes.disc(cx + sign * 3.4 * size, cy - 3 * size, 1.5 * size, 5)
    sketch.stamp(eyes, outline=False, rim=0, occlude=0)
    return piece


def _stone(sketch, tone, cx=16, cy=17, size=1.0):
    piece = sketch.piece(tone)
    piece.poly(catmull([(cx - 11 * size, cy + 8 * size), (cx - 10 * size, cy - 2 * size),
                        (cx - 3 * size, cy - 10 * size), (cx + 7 * size, cy - 7 * size),
                        (cx + 11 * size, cy + 3 * size), (cx + 5 * size, cy + 9 * size)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.65)
    facet = sketch.piece(tone)
    facet.line([(cx - 6 * size, cy + 5 * size), (cx - 2 * size, cy - 5 * size)], 1, 1)
    facet.line([(cx - 2 * size, cy - 5 * size), (cx + 8 * size, cy - 1 * size)], 5, 1)
    facet.clip(piece)
    sketch.overlay(facet)
    return piece


def _fist(sketch, tone, cx=16, cy=16, size=1.0):
    piece = sketch.piece(tone)
    piece.poly(catmull([(cx - 9 * size, cy + 5 * size), (cx - 9 * size, cy - 5 * size),
                        (cx - 1 * size, cy - 9 * size), (cx + 8 * size, cy - 5 * size),
                        (cx + 9 * size, cy + 4 * size), (cx + 2 * size, cy + 9 * size),
                        (cx - 5 * size, cy + 9 * size)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    knuckles = sketch.piece(tone)
    for index in range(3):
        knuckles.disc(cx - 5 * size + index * 5 * size, cy - 4 * size, 2.0 * size, 4)
    knuckles.clip(piece)
    sketch.overlay(knuckles)
    return piece


ELEMENT_MOTIF = {
    'Fire': lambda s, t, x, y, k: _flame(s, t, x, y + 1, k),
    'Frost': lambda s, t, x, y, k: _shard(s, t, x, y, k),
    'Lightning': lambda s, t, x, y, k: _bolt(s, t, x, y, k),
    'Nature': lambda s, t, x, y, k: _leaf(s, t, x, y, k),
    'Poison': lambda s, t, x, y, k: _leaf(s, t, x, y, k, poison=True),
    'Arcane': lambda s, t, x, y, k: _star(s, t, x, y, k, points=4),
    'Radiant': lambda s, t, x, y, k: _sun(s, t, x, y, k),
    'Shadow': lambda s, t, x, y, k: _shadow(s, t, x, y, k),
    'Physical': lambda s, t, x, y, k: _fist(s, t, x, y, k),
}

# Kinds that draw a badge in the lower left; the element motif steps aside for them.
BADGE_KINDS = {'area', 'field', 'cone', 'line', 'projectile', 'dot', 'drain', 'summon',
               'stealth', 'buff', 'heal', 'purge', 'taunt', 'dash', 'charge',
               'strike', 'execute', 'interrupt'}


# ----------------------------------------------------------------- kinds ---

def _weapon_mark(sketch, tone, kind):
    """Physical kinds get a real weapon shape rather than a generic slash."""
    tags = {'strike': 'sword', 'execute': 'greatsword', 'charge': 'spear', 'taunt': 'mace',
            'interrupt': 'mace', 'dash': 'dagger', 'drain': 'dagger'}.get(kind, 'sword')
    item = {'id': 'ability_' + kind, 'type': 'weapon', 'slot': 'weapon', 'tags': [tags],
            'material': 'steel', 'element': 'Physical', 'tier': 4}
    parts = smith.profile_for(item)
    ramps = smith.role_ramps(item)
    ramps['metal'] = tone
    origin, scale = smith._fit(parts, 26.0, (16.0, 16.5), -math.pi / 4)
    smith.render_parts(sketch, parts, ramps, origin, -math.pi / 4, scale, 1)


def _overlay(sketch, tone, kind, accent):
    """The kind badge. Drawn large in the lower left with its own contour so it
    survives against a busy element motif."""
    piece = sketch.piece(tone)
    outline = True
    if kind == 'area':
        piece.arc((0, 19, 21, 31), 0, 360, 5, 2)
        piece.arc((5, 22, 16, 29), 0, 360, 4, 1)
        outline = False
    elif kind == 'field':
        piece.arc((0, 20, 22, 31), 0, 360, 5, 2)
        for x in (3, 8, 14, 19):
            piece.line([(x, 30 - abs(x - 11) * 0.4), (x, 19 - abs(x - 11) * 0.3)], 5, 1)
        outline = False
    elif kind == 'cone':
        piece.poly([(1, 31), (7, 17), (20, 25)], 4)
        piece.poly([(2, 30), (7, 21), (15, 25)], 5)
    elif kind in ('line', 'projectile'):
        piece.poly(taper_shape((1, 31), (17, 15), 5.4, 1.4), 4)
        piece.poly([(19, 13), (13, 15), (16, 20)], 5)
    elif kind == 'dot':
        for index, (x, y, r) in enumerate(((4, 28, 3.0), (10, 25, 2.4), (15, 21, 1.8))):
            piece.disc(x, y, r, 4 if index % 2 == 0 else 5)
    elif kind == 'drain':
        piece.line(catmull([(2, 31), (9, 25), (7, 18), (15, 13)], 6), 4, 2)
        piece.poly([(17, 11), (19, 17), (12, 16)], 5)
        outline = False
    elif kind == 'summon':
        piece.arc((0, 21, 22, 31), 0, 360, 5, 2)
        piece.poly([(11, 18), (15, 24), (11, 30), (7, 24)], 4)
        outline = False
    elif kind == 'stealth':
        for y in (14, 20, 26):
            piece.poly(taper_shape((0, y), (8, y - 2), 2.6, 1.2), 5)
        outline = False
    elif kind == 'buff':
        piece.poly([(8, 14), (15, 23), (11, 23), (11, 31), (5, 31), (5, 23), (1, 23)], 4)
    elif kind == 'heal':
        piece.poly([(5, 16), (11, 16), (11, 22), (17, 22), (17, 28), (11, 28), (11, 31),
                    (5, 31), (5, 28), (-1, 28), (-1, 22), (5, 22)], 4)
    elif kind == 'purge':
        piece.arc((1, 18, 17, 31), 0, 360, 5, 2)
        piece.line([(4, 21), (14, 29)], 4, 2)
        outline = False
    elif kind == 'taunt':
        piece.arc((2, 16, 18, 32), 240, 120, 5, 2)
        piece.arc((5, 20, 15, 30), 240, 120, 4, 1)
        outline = False
    elif kind in ('dash', 'charge'):
        for y in (18, 23, 28):
            piece.poly(taper_shape((0, y), (10, y - 1), 3.0, 1.2), 4)
        outline = False
    elif kind == 'strike':
        piece.poly(taper_shape((1, 30), (16, 15), 5.0, 1.6), 4)
        piece.poly(taper_shape((3, 31), (13, 21), 2.0, 1.0), 5)
        outline = False
    elif kind == 'execute':
        piece.poly(taper_shape((10, 14), (5, 31), 5.6, 1.4), 4)
        piece.poly([(12, 12), (3, 15), (8, 19)], 5)
        outline = False
    elif kind == 'interrupt':
        piece.poly(taper_shape((1, 22), (17, 26), 4.0, 4.0), 4)
        piece.erase(points=[(7, 18), (11, 18), (9, 31), (5, 31)])
        piece.poly([(2, 14), (7, 20), (1, 20)], 5)
        outline = False
    else:
        return
    sketch.stamp(piece, outline=outline, rim=0.8 if outline else 0, occlude=0.4 if outline else 0)


def _arrow(sketch, tone, cx=16, cy=16):
    piece = sketch.piece(tone)
    piece.poly(taper_shape((cx - 11, cy + 11), (cx + 8, cy - 8), 4.2, 3.0), 3)
    piece.poly([(cx + 12, cy - 12), (cx + 3, cy - 9), (cx + 9, cy - 3)], 3)
    piece.poly([(cx - 12, cy + 12), (cx - 4, cy + 6), (cx - 6, cy + 4)], 3)
    piece.poly([(cx - 10, cy + 10), (cx - 3, cy + 9), (cx - 9, cy + 3)], 2)
    sketch.stamp(piece, rim=0.9, occlude=0.55)
    return piece


def _crater(sketch, tone, cx=16, cy=18):
    piece = sketch.piece(tone)
    piece.poly(catmull([(cx - 13, cy + 4), (cx - 8, cy - 4), (cx, cy - 7), (cx + 8, cy - 4),
                        (cx + 13, cy + 4), (cx + 6, cy + 9), (cx - 6, cy + 9)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    cracks = sketch.piece(tone)
    for angle in (200, 250, 300, 340):
        rad = math.radians(angle)
        cracks.line([(cx, cy), (cx + math.cos(rad) * 12, cy + math.sin(rad) * 9)], 1, 1)
    cracks.clip(piece)
    sketch.overlay(cracks)
    shards = sketch.piece(tone)
    for dx, dy in ((-10, -9), (2, -12), (11, -8)):
        shards.poly([(cx + dx, cy + dy), (cx + dx + 4, cy + dy + 3), (cx + dx + 1, cy + dy + 5)], 4)
    sketch.stamp(shards, rim=0.9, occlude=0.5)
    return piece


def _claw(sketch, tone, cx=16, cy=16):
    piece = sketch.piece(tone)
    for offset in (-6, 0, 6):
        piece.poly(taper_shape((cx + offset - 6, cy - 11), (cx + offset + 3, cy + 12), 4.6, 1.2), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.5)
    return piece


def _banner(sketch, tone, cx=16, cy=16):
    pole = sketch.piece(ramp('#8a6a45'))
    pole.poly(taper_shape((cx - 7, cy + 14), (cx - 7, cy - 13), 3.0, 2.4), 3)
    sketch.stamp(pole, rim=0.8, occlude=0.5)
    piece = sketch.piece(tone)
    piece.poly([(cx - 6, cy - 12), (cx + 12, cy - 9), (cx + 12, cy + 3), (cx - 6, cy + 6)], 3)
    sketch.stamp(piece, rim=0.9, occlude=0.55)
    mark = sketch.piece(tone)
    mark.poly([(cx + 3, cy - 7), (cx + 7, cy - 3), (cx + 3, cy + 1), (cx - 1, cy - 3)], 5)
    mark.clip(piece)
    sketch.overlay(mark)
    return piece


def _guard_plate(sketch, tone, heavy=False):
    piece = sketch.piece(tone)
    piece.poly(catmull([(4, 6), (16, 2), (28, 6), (27, 17), (21, 26), (16, 30),
                        (10, 25), (5, 17)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.95, occlude=0.6)
    face = sketch.piece(tone)
    face.poly(catmull([(8, 9), (16, 6), (24, 9), (22, 17), (16, 24), (11, 18)], 6, closed=True), 4)
    face.clip(piece)
    sketch.overlay(face)
    boss = sketch.piece(tone)
    if heavy:
        boss.poly([(16, 8), (20, 15), (16, 23), (12, 15)], 2)
    else:
        boss.line([(16, 7), (16, 24)], 2, 1)
        boss.line([(8, 13), (24, 13)], 2, 1)
    boss.clip(piece)
    sketch.overlay(boss)
    return piece


def _runes(sketch, tone, ident):
    """Deterministic accent so two frost cones are still distinguishable."""
    seed = keyed(ident)
    piece = sketch.piece(tone)
    spots = [(4, 5), (28, 5), (4, 27), (28, 27), (16, 2), (2, 16), (30, 16)]
    drawn = 0
    for index, (x, y) in enumerate(spots):
        if (seed >> index) & 1 and drawn < 3:
            drawn += 1
            style = (seed >> (index + 8)) & 3
            if style == 0:
                piece.disc(x, y, 1.5, 5)
            elif style == 1:
                piece.poly([(x, y - 2), (x + 2, y), (x, y + 2), (x - 2, y)], 5)
            elif style == 2:
                piece.line([(x - 2, y - 2), (x + 2, y + 2)], 5, 1)
                piece.line([(x + 2, y - 2), (x - 2, y + 2)], 5, 1)
            else:
                piece.line([(x, y - 2), (x, y + 2)], 5, 1)
                piece.line([(x - 2, y), (x + 2, y)], 5, 1)
    sketch.stamp(piece, outline=False, rim=0, occlude=0)


# Physical magic has no element to show, so the picture has to carry the verb:
# a swing, a shot, an impact, a wound, a rally.
PHYSICAL_MOTIF = {
    'strike': lambda s, t: _weapon_mark(s, t, 'strike'),
    'execute': lambda s, t: _weapon_mark(s, t, 'execute'),
    'charge': lambda s, t: _weapon_mark(s, t, 'charge'),
    'interrupt': lambda s, t: _weapon_mark(s, t, 'interrupt'),
    'taunt': lambda s, t: _weapon_mark(s, t, 'taunt'),
    'drain': lambda s, t: _weapon_mark(s, t, 'drain'),
    'dash': lambda s, t: _weapon_mark(s, t, 'dash'),
    'projectile': lambda s, t: _arrow(s, t),
    'line': lambda s, t: _arrow(s, t),
    'cone': lambda s, t: _arrow(s, t),
    'area': lambda s, t: _crater(s, t),
    'field': lambda s, t: _crater(s, t),
    'dot': lambda s, t: _claw(s, t),
    'buff': lambda s, t: _banner(s, t),
    'summon': lambda s, t: _banner(s, t),
}


def ability_icon(ability):
    element = ability.get('element', 'Physical')
    kind = ability.get('kind', 'strike')
    tone = pigment.element_ramp(element)
    sketch = Sketch(ICON)
    if kind in ('shield', 'guard'):
        _guard_plate(sketch, tone, heavy=element in ('Physical', 'Radiant'))
    elif element == 'Physical' and kind in PHYSICAL_MOTIF:
        PHYSICAL_MOTIF[kind](sketch, tone)
    elif kind == 'heal':
        piece = sketch.piece(tone)
        piece.poly([(12, 3), (20, 3), (20, 12), (29, 12), (29, 20), (20, 20), (20, 29),
                    (12, 29), (12, 20), (3, 20), (3, 12), (12, 12)], 3)
        sketch.stamp(piece, rim=0.95, occlude=0.5)
        inner = sketch.piece(tone)
        inner.poly([(14, 6), (18, 6), (18, 14), (26, 14), (26, 18), (18, 18), (18, 26),
                    (14, 26), (14, 18), (6, 18), (6, 14), (14, 14)], 5)
        inner.clip(piece)
        sketch.overlay(inner)
    elif kind == 'stealth':
        piece = sketch.piece(tone)
        piece.poly(catmull([(16, 4), (24, 9), (26, 20), (16, 29), (6, 20), (8, 9)], 6, closed=True), 2)
        sketch.stamp(piece, rim=0.6, occlude=0.4)
        eyes = sketch.piece(ramp('#e6dcc2'))
        for sign in (-1, 1):
            eyes.disc(16 + sign * 4, 15, 1.6, 5)
        sketch.stamp(eyes, outline=False, rim=0, occlude=0)
    else:
        badge = kind in BADGE_KINDS
        motif = ELEMENT_MOTIF.get(element, ELEMENT_MOTIF['Physical'])
        motif(sketch, tone, 18.0 if badge else 16.0, 14.0 if badge else 16.0, 0.84 if badge else 1.0)
    _overlay(sketch, tone, kind, element)
    _runes(sketch, tone, ability.get('id', 'ability'))
    if element not in ('Physical',):
        sketch.glow(pigment.ELEMENTS.get(element, '#c6b9a4'), 2, 0.40)
    return sketch.result()


# ---------------------------------------------------------------- skills ---

def _tool_icon(tag, material='steel', tier=4, element='Physical'):
    item = {'id': 'skill_' + tag, 'type': 'weapon', 'slot': 'weapon', 'tags': [tag],
            'material': material, 'element': element, 'tier': tier}
    return smith.weapon_icon(item)


def _plate(sketch, tone, weight):
    piece = sketch.piece(tone)
    piece.poly(catmull([(9, 5), (16, 3), (23, 5), (26, 11), (24, 16), (25, 26),
                        (16, 29), (7, 26), (8, 16), (6, 11)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    detail = sketch.piece(tone)
    if weight == 'heavy':
        detail.line([(16, 7), (16, 27)], 1, 1)
        detail.line([(10, 15), (22, 15)], 1, 1)
        detail.line([(11, 13), (21, 13)], 5, 1)
    elif weight == 'medium':
        for y in (11, 16, 21):
            detail.line([(10, y), (22, y)], 1, 1)
            detail.line([(11, y - 1), (21, y - 1)], 5, 1)
    else:
        detail.line(catmull([(12, 6), (16, 11), (20, 6)], 4), 1, 1)
        detail.line([(16, 10), (16, 27)], 1, 1)
    detail.clip(piece)
    sketch.overlay(detail)
    return sketch.result()


def _simple(draw):
    sketch = Sketch(ICON)
    draw(sketch)
    return sketch.result()


def _pot(sketch, body='#5f6166', fill='#b8814a'):
    pot = sketch.piece(ramp(body))
    pot.poly(catmull([(6, 12), (26, 12), (24, 25), (16, 29), (8, 25)], 6, closed=True), 3)
    pot.arc((3, 8, 12, 20), 100, 260, 3, 1)
    pot.arc((20, 8, 29, 20), 280, 80, 3, 1)
    sketch.stamp(pot, rim=0.9, occlude=0.65)
    soup = sketch.piece(ramp(fill))
    soup.ellipse((8, 10, 24, 16), 3)
    sketch.stamp(soup, rim=0.8, occlude=0.4)
    steam = sketch.piece(ramp('#cfd6d8'))
    for dx in (-5, 0, 5):
        steam.line(catmull([(16 + dx, 9), (18 + dx, 5), (15 + dx, 2)], 5), 4, 1)
    sketch.stamp(steam, outline=False, rim=0, occlude=0)


def _gear(sketch, colour='#8d959c'):
    tone = ramp(colour)
    piece = sketch.piece(tone)
    for index in range(8):
        angle = index * math.tau / 8
        piece.poly(taper_shape((16 + math.cos(angle) * 7, 16 + math.sin(angle) * 7),
                               (16 + math.cos(angle) * 13, 16 + math.sin(angle) * 13), 7.0, 5.0), 3)
    piece.disc(16, 16, 10, 3)
    piece.erase_ellipse((12, 12, 20, 20))
    sketch.stamp(piece, rim=0.9, occlude=0.6)


def _coin_stack(sketch, colour='#d0a63f'):
    tone = ramp(colour)
    for index, (x, y) in enumerate(((11, 25), (11, 21), (11, 17))):
        piece = sketch.piece(tone)
        piece.ellipse((x - 8, y - 4, x + 8, y + 4), 3)
        sketch.stamp(piece, rim=0.9, occlude=0.5)
    coin = sketch.piece(tone)
    coin.disc(23, 13, 7, 3)
    coin.disc(21.4, 11.4, 2.6, 5)
    sketch.stamp(coin, rim=0.95, occlude=0.5)


def _paw(sketch, colour='#8a6a4c'):
    tone = ramp(colour)
    piece = sketch.piece(tone)
    piece.ellipse((9, 15, 23, 27), 3)
    for x, y, r in ((8, 11, 3.0), (14, 8, 3.2), (21, 9, 3.0), (26, 14, 2.8)):
        piece.disc(x, y, r, 3)
    sketch.stamp(piece, rim=0.9, occlude=0.55)


def _skull(sketch, colour='#d6cdb2'):
    tone = ramp(colour)
    piece = sketch.piece(tone)
    piece.poly(catmull([(7, 16), (8, 8), (16, 4), (24, 8), (25, 16), (21, 21),
                        (21, 26), (11, 26), (11, 21)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    holes = sketch.piece(ramp('#3a3440'))
    holes.ellipse((10, 12, 15, 18), 3)
    holes.ellipse((17, 12, 22, 18), 3)
    holes.poly([(16, 19), (18, 22), (14, 22)], 3)
    sketch.stamp(holes, outline=False, rim=0, occlude=0)
    teeth = sketch.piece(tone)
    for x in (12, 15, 18):
        teeth.line([(x, 23), (x, 26)], 1, 1)
    teeth.clip(piece)
    sketch.overlay(teeth)


def _needle(sketch):
    tone = ramp('#c0c8ce')
    piece = sketch.piece(tone)
    piece.poly(taper_shape((6, 27), (25, 6), 3.2, 1.2), 3)
    piece.disc(7, 26, 2.6, 3)
    piece.erase_ellipse((5.6, 24.6, 8.4, 27.4))
    sketch.stamp(piece, rim=0.9, occlude=0.5)
    thread = sketch.piece(ramp('#b0567a'))
    thread.line(catmull([(7, 26), (2, 22), (7, 17), (3, 12)], 6), 3, 2)
    sketch.stamp(thread, outline=False, rim=0, occlude=0)


def _quill(sketch):
    tone = ramp('#e0d8c0')
    piece = sketch.piece(tone)
    piece.poly(catmull([(6, 28), (11, 17), (20, 6), (25, 10), (18, 21), (10, 28)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.5)
    spine = sketch.piece(ramp('#8f7f66'))
    spine.line(catmull([(7, 28), (14, 18), (23, 8)], 6), 3, 1)
    sketch.stamp(spine, outline=False, rim=0, occlude=0)
    ink = sketch.piece(ramp('#3a3f5c'))
    ink.poly(catmull([(3, 26), (7, 24), (8, 29), (4, 30)], 4, closed=True), 3)
    sketch.stamp(ink, rim=0.8, occlude=0.4)


def _lock(sketch):
    tone = ramp('#a09a8a')
    piece = sketch.piece(tone)
    piece.arc((9, 5, 23, 20), 180, 360, 3, 3)
    piece.rect((7, 15, 25, 28), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    hole = sketch.piece(ramp('#3a3440'))
    hole.disc(16, 20, 2.2, 3)
    hole.poly([(15, 20), (17, 20), (16.5, 25), (15.5, 25)], 3)
    sketch.stamp(hole, outline=False, rim=0, occlude=0)
    pick = sketch.piece(ramp('#c0c8ce'))
    pick.line([(22, 27), (30, 19)], 3, 2)
    pick.poly([(29, 17), (31, 21), (27, 21)], 3)
    sketch.stamp(pick, rim=0.9, occlude=0.4)


def _anvil(sketch):
    tone = ramp('#7d858d')
    piece = sketch.piece(tone)
    piece.poly([(4, 14), (24, 14), (28, 17), (20, 18), (19, 22), (24, 26), (24, 29),
                (8, 29), (8, 26), (13, 22), (12, 18), (4, 17)], 3)
    sketch.stamp(piece, rim=0.9, occlude=0.65)
    hammer = sketch.piece(ramp('#8a6a45'))
    hammer.poly(taper_shape((6, 12), (22, 4), 3.4, 3.0), 3)
    sketch.stamp(hammer, rim=0.8, occlude=0.5)
    head = sketch.piece(ramp('#a9b6c0'))
    head.poly([(19, 1), (28, 4), (25, 10), (17, 7)], 3)
    sketch.stamp(head, rim=0.9, occlude=0.5)


def _map_icon(sketch):
    paper = sketch.piece(ramp('#d7c8a1'))
    paper.poly(catmull([(4, 8), (11, 5), (21, 8), (28, 5), (28, 24), (21, 27), (11, 24), (4, 27)], 7, closed=True), 3)
    sketch.stamp(paper, rim=0.9, occlude=0.6)
    ink = sketch.piece(ramp('#7d6b4e'))
    ink.line(catmull([(8, 20), (13, 15), (18, 18), (24, 12)], 6), 2, 1)
    ink.line([(11, 5), (11, 24)], 1, 1)
    ink.line([(21, 8), (21, 27)], 1, 1)
    ink.clip(paper)
    sketch.overlay(ink)


def _compass(sketch):
    case = sketch.piece(ramp('#c0a24a'))
    case.disc(16, 16, 12, 3)
    sketch.stamp(case, rim=0.9, occlude=0.6)
    face = sketch.piece(ramp('#e2d8bc'))
    face.disc(16, 16, 9, 3)
    sketch.stamp(face, rim=0.7, occlude=0.4)
    needle = sketch.piece(ramp('#a8413c'))
    needle.poly([(16, 7), (19, 16), (16, 25), (13, 16)], 3)
    needle.poly([(16, 7), (19, 16), (16, 16)], 5)
    sketch.stamp(needle, outline=False, rim=0, occlude=0)


def _wheat(sketch):
    tone = ramp('#c8a44a')
    piece = sketch.piece(tone)
    for dx in (-6, 0, 6):
        piece.line(catmull([(16 + dx, 30), (16 + dx * 0.6, 20), (16 + dx * 0.4, 8)], 6), 3, 1)
        for step in range(4):
            y = 10 + step * 4
            x = 16 + dx * (0.4 + step * 0.05)
            piece.poly(catmull([(x, y + 3), (x - 3, y), (x, y - 3)], 4, closed=True), 3)
            piece.poly(catmull([(x, y + 3), (x + 3, y), (x, y - 3)], 4, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.5)


def _basket(sketch):
    tone = ramp('#a8895a')
    piece = sketch.piece(tone)
    piece.poly(catmull([(5, 14), (27, 14), (24, 28), (8, 28)], 5, closed=True), 3)
    piece.arc((7, 4, 25, 22), 190, 350, 3, 2)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    weave = sketch.piece(tone)
    for y in (18, 22, 26):
        weave.line([(6, y), (26, y)], 1, 1)
    for x in (11, 16, 21):
        weave.line([(x, 15), (x, 28)], 1, 1)
    weave.clip(piece)
    sketch.overlay(weave)
    fruit = sketch.piece(ramp('#a8434a'))
    for x, y in ((11, 13), (16, 11), (21, 13)):
        fruit.disc(x, y, 3.0, 3)
    sketch.stamp(fruit, rim=0.9, occlude=0.5)


def _eye(sketch, colour='#8fb9c8'):
    tone = ramp(colour)
    piece = sketch.piece(tone)
    piece.poly(catmull([(2, 16), (10, 8), (22, 8), (30, 16), (22, 24), (10, 24)], 7, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.5)
    iris = sketch.piece(ramp('#3f4a6a'))
    iris.disc(16, 16, 5.0, 3)
    iris.disc(16, 16, 2.2, 0)
    iris.disc(14.4, 14.4, 1.4, 5)
    sketch.stamp(iris, rim=0.6, occlude=0.3)


def _hide(sketch):
    tone = ramp('#8a5f3c')
    piece = sketch.piece(tone)
    piece.poly(catmull([(7, 6), (13, 9), (20, 8), (26, 6), (27, 16), (23, 27),
                        (14, 28), (6, 22), (5, 12)], 7, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    knife = sketch.piece(ramp('#c0c8ce'))
    knife.poly(taper_shape((6, 27), (22, 10), 4.0, 1.4), 3)
    sketch.stamp(knife, rim=0.9, occlude=0.5)


def _flask(sketch, colour='#6faa5b'):
    glass = ramp('#a9c6cf')
    body = sketch.piece(glass)
    body.poly(catmull([(13, 5), (19, 5), (21, 13), (25, 22), (21, 28), (11, 28), (7, 22), (11, 13)], 6, closed=True), 3)
    sketch.stamp(body, rim=0.9, occlude=0.5)
    fluid = sketch.piece(ramp(colour))
    fluid.poly(catmull([(9, 19), (23, 19), (24, 23), (20, 27), (12, 27), (8, 23)], 5, closed=True), 3)
    fluid.clip(body)
    sketch.overlay(fluid)
    cork = sketch.piece(ramp('#b08a55'))
    cork.rect((12, 1, 20, 6), 3)
    sketch.stamp(cork, rim=0.9, occlude=0.5)
    sketch.glow(colour, 2, 0.3)


def _rune_tablet(sketch, colour='#a98fd0'):
    stone = sketch.piece(ramp('#7b6f96'))
    stone.poly(catmull([(9, 4), (23, 5), (25, 15), (23, 27), (16, 29), (9, 27), (7, 15)], 6, closed=True), 3)
    sketch.stamp(stone, rim=0.9, occlude=0.65)
    glyph = sketch.piece(ramp(colour))
    glyph.line([(16, 8), (16, 24)], 4, 1)
    glyph.line([(11, 12), (21, 10)], 4, 1)
    glyph.line([(11, 20), (21, 18)], 4, 1)
    sketch.stamp(glyph, outline=False, rim=0, occlude=0)
    sketch.glow(colour, 2, 0.42)


def _boot(sketch):
    tone = ramp('#7a5236')
    piece = sketch.piece(tone)
    piece.poly(catmull([(10, 4), (19, 4), (20, 17), (27, 22), (27, 27), (9, 27), (9, 17)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    speed = sketch.piece(ramp('#cfd6d8'))
    for y in (10, 15, 20):
        speed.line([(1, y), (7, y)], 4, 1)
    sketch.stamp(speed, outline=False, rim=0, occlude=0)


def _heart(sketch, colour='#b0574c'):
    tone = ramp(colour)
    piece = sketch.piece(tone)
    piece.poly(catmull([(16, 10), (22, 5), (28, 10), (26, 18), (16, 28), (6, 18), (4, 10), (10, 5)],
                       7, closed=True), 3)
    sketch.stamp(piece, rim=0.95, occlude=0.55)
    shine = sketch.piece(tone)
    shine.disc(11, 12, 2.6, 5)
    shine.clip(piece)
    sketch.overlay(shine)


def _antler(sketch):
    tone = ramp('#cfc4a4')
    piece = sketch.piece(tone)
    for sign in (-1, 1):
        piece.line(catmull([(16, 29), (16 + sign * 3, 20), (16 + sign * 7, 8)], 6), 3, 2)
        piece.line([(16 + sign * 4, 17), (16 + sign * 11, 13)], 3, 1)
        piece.line([(16 + sign * 6, 12), (16 + sign * 13, 7)], 3, 1)
    sketch.stamp(piece, rim=0.9, occlude=0.5)


def _campfire(sketch):
    logs = sketch.piece(ramp('#7a5a3c'))
    logs.poly(taper_shape((6, 24), (26, 28), 5.0, 4.0), 3)
    logs.poly(taper_shape((26, 24), (6, 28), 5.0, 4.0), 2)
    sketch.stamp(logs, rim=0.8, occlude=0.6)
    _flame(sketch, ramp('#d4703c'), 16, 15, 0.85)
    sketch.glow('#e8894a', 3, 0.5)


def _saw(sketch):
    tone = ramp('#b6bec6')
    piece = sketch.piece(tone)
    piece.poly([(4, 8), (26, 14), (24, 20), (3, 14)], 3)
    for index in range(7):
        x = 5 + index * 3
        piece.poly([(x, 14 + index * 0.3), (x + 3, 15 + index * 0.3), (x + 1, 19 + index * 0.3)], 3)
    sketch.stamp(piece, rim=0.9, occlude=0.55)
    grip = sketch.piece(ramp('#8a6a45'))
    grip.poly(catmull([(24, 10), (30, 12), (30, 22), (24, 22)], 5, closed=True), 3)
    sketch.stamp(grip, rim=0.85, occlude=0.5)


def _ring_gem(sketch):
    tone = ramp('#d0a63f')
    piece = sketch.piece(tone)
    piece.disc(16, 20, 9, 3)
    piece.erase_ellipse((11, 15, 21, 25))
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    gem = sketch.piece(ramp('#7fb8c8'))
    gem.poly([(16, 2), (22, 9), (16, 16), (10, 9)], 3)
    gem.poly([(16, 4), (19, 9), (16, 12), (13, 9)], 5)
    sketch.stamp(gem, rim=0.95, occlude=0.5)
    sketch.glow('#7fb8c8', 2, 0.3)


def _house_frame(sketch):
    tone = ramp('#8a6a45')
    piece = sketch.piece(tone)
    piece.poly(taper_shape((5, 28), (5, 12), 4.0, 4.0), 3)
    piece.poly(taper_shape((27, 28), (27, 12), 4.0, 4.0), 3)
    piece.poly(taper_shape((3, 13), (16, 4), 4.0, 4.0), 3)
    piece.poly(taper_shape((29, 13), (16, 4), 4.0, 4.0), 3)
    piece.poly(taper_shape((5, 20), (27, 20), 3.4, 3.4), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)


SKILL_ICONS = {
    'swordsmanship': lambda: _tool_icon('sword'),
    'axe_mastery': lambda: _tool_icon('axe'),
    'mace_mastery': lambda: _tool_icon('mace'),
    'spear_mastery': lambda: _tool_icon('spear'),
    'dagger_mastery': lambda: _tool_icon('dagger'),
    'archery': lambda: _tool_icon('bow', 'yew'),
    'crossbow_mastery': lambda: _tool_icon('crossbow', 'oak'),
    'staff_mastery': lambda: _tool_icon('staff', 'elderwood', element='Arcane'),
    'wand_mastery': lambda: _tool_icon('wand', 'starwood', element='Arcane'),
    'shield_mastery': lambda: _simple(lambda s: _guard_plate(s, ramp('#a9b6c0'), True)),
    'unarmed_combat': lambda: _simple(lambda s: _fist(s, ramp('#c28656'))),
    'pyromancy': lambda: _simple(lambda s: (_flame(s, ramp('#e07a44')), s.glow('#e07a44', 3, 0.5))),
    'cryomancy': lambda: _simple(lambda s: (_shard(s, ramp('#7fc4d8')), s.glow('#7fc4d8', 3, 0.45))),
    'stormcalling': lambda: _simple(lambda s: (_bolt(s, ramp('#e8cf5e')), s.glow('#e8cf5e', 3, 0.5))),
    'geomancy': lambda: _simple(lambda s: _stone(s, ramp('#8a8b86'))),
    'nature_magic': lambda: _simple(lambda s: _leaf(s, ramp('#77a95c'))),
    'shadow_magic': lambda: _simple(lambda s: (_shadow(s, ramp('#7a6b9e')), s.glow('#7a6b9e', 3, 0.4))),
    'radiance': lambda: _simple(lambda s: (_sun(s, ramp('#f0dc9e')), s.glow('#f0dc9e', 3, 0.5))),
    'arcane_magic': lambda: _simple(lambda s: (_star(s, ramp('#a98fd0'), points=5), s.glow('#a98fd0', 3, 0.45))),
    'restoration': lambda: _simple(lambda s: _heart(s, '#c07a6a')),
    'summoning': lambda: _simple(lambda s: _eye(s, '#9fd4c8')),
    'runecasting': lambda: _simple(_rune_tablet),
    'light_armor': lambda: _simple(lambda s: _plate(s, ramp('#a8895a'), 'light')),
    'medium_armor': lambda: _simple(lambda s: _plate(s, ramp('#8a7a62'), 'medium')),
    'heavy_armor': lambda: _simple(lambda s: _plate(s, ramp('#a9b6c0'), 'heavy')),
    'evasion': lambda: _simple(_boot),
    'endurance': lambda: _simple(lambda s: _heart(s, '#b0574c')),
    'meditation': lambda: _simple(lambda s: _eye(s, '#b6a8d8')),
    'hunting': lambda: _simple(_antler),
    'slayer': lambda: _simple(_skull),
    'survival': lambda: _simple(_campfire),
    'exploration': lambda: _simple(_compass),
    'mining': lambda: _tool_icon('pickaxe', 'iron'),
    'woodcutting': lambda: _tool_icon('axe', 'bronze'),
    'fishing': lambda: _tool_icon('rod', 'oak'),
    'farming': lambda: _simple(_wheat),
    'foraging': lambda: _simple(_basket),
    'herbalism': lambda: smith._herb_icon({'id': 'herb', 'element': 'Nature'}),
    'skinning': lambda: _simple(_hide),
    'excavation': lambda: _tool_icon('shovel', 'iron'),
    'prospecting': lambda: smith._ore_icon({'id': 'gold_ore', 'material': 'gold'}),
    'treasure_hunting': lambda: _simple(_map_icon),
    'smithing': lambda: _simple(_anvil),
    'woodworking': lambda: _simple(_saw),
    'fletching': lambda: smith._material_icon({'id': 'arrow_bundle', 'material': 'wood'}),
    'tailoring': lambda: _simple(_needle),
    'leatherworking': lambda: _simple(_hide),
    'cooking': lambda: _simple(_pot),
    'alchemy': lambda: _simple(lambda s: _flask(s, '#6faa5b')),
    'enchanting': lambda: _simple(lambda s: _rune_tablet(s, '#7fc4d8')),
    'runecrafting': lambda: _simple(lambda s: _rune_tablet(s, '#e8cf5e')),
    'jewelcrafting': lambda: _simple(_ring_gem),
    'carpentry': lambda: _simple(_house_frame),
    'scribing': lambda: _simple(_quill),
    'tinkering': lambda: _simple(_gear),
    'lockpicking': lambda: _simple(_lock),
    'bartering': lambda: _simple(_coin_stack),
    'cartography': lambda: _simple(_map_icon),
    'animal_handling': lambda: _simple(_paw),
    'construction': lambda: _simple(_house_frame),
}


def skill_icon(skill_id):
    maker = SKILL_ICONS.get(skill_id)
    if maker is None:
        return _simple(_gear)
    return maker()
