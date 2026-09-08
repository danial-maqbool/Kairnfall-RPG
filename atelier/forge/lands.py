"""The world: ground tiles, scenery, gathering nodes, chests, crafting stations
and buildings.

Ground tiles are authored to wrap at 32px so a field of grass has no seams.
Everything that stands on the ground is drawn with its feet at the bottom of its
own sprite, matching how the client anchors props.
"""
from __future__ import annotations

import math
import random

from . import pigment
from .brush import Sketch, catmull, taper_shape
from .pigment import blend, keyed, ramp

TILE = 32

TERRAIN = {
    'grass': '#5f7a45', 'dirt': '#7d6448', 'stone': '#787b76', 'sand': '#c0a97e',
    'snow': '#c7d2d6', 'water': '#3c6580', 'lava': '#b4552f', 'wall': '#5f6166',
    'wood': '#8a6a45', 'moss': '#4f6844', 'crystal': '#6d7396', 'marsh': '#5c6a52',
    'ash': '#6b6866',
}

PROPS = ['oak', 'ancient_oak', 'pine', 'snow_pine', 'willow', 'palm', 'dead_tree', 'bush',
         'flowers', 'rock', 'snow_rock', 'basalt', 'grass_tuft', 'reeds', 'mushrooms',
         'cactus', 'crystal', 'signpost', 'waystone', 'stairs', 'stump', 'loot', 'shadow']

TREES = {'oak', 'ancient_oak', 'pine', 'snow_pine', 'willow', 'palm', 'dead_tree'}

CHESTS = ['weathered', 'locked', 'ancient', 'runic', 'royal', 'cursed', 'mimic']

STATIONS = ['structure_campfire', 'structure_workbench', 'structure_sawbench',
            'structure_kitchen', 'structure_rune_table']


def _rng(*parts):
    return random.Random(keyed('|'.join(str(p) for p in parts)))


# ------------------------------------------------------------------ tiles --

def tile(kind, variant=0):
    """A 32px ground tile. Detail is kept off the seams so fields do not grid."""
    base = TERRAIN.get(kind, '#6a6a6a')
    tone = ramp(base)
    sketch = Sketch((TILE, TILE))
    ground = sketch.piece(tone)
    ground.rect((0, 0, TILE - 1, TILE - 1), 3)
    r = _rng(kind, variant)

    if kind in ('grass', 'moss', 'marsh'):
        ground.dither((0, 0, TILE - 1, TILE - 1), 2, level=4, phase=variant)
        ground.dither((0, 0, TILE - 1, TILE - 1), 4, level=2, phase=variant + 2)
    elif kind in ('dirt', 'sand', 'ash'):
        ground.dither((0, 0, TILE - 1, TILE - 1), 2, level=3, phase=variant)
        ground.dither((0, 0, TILE - 1, TILE - 1), 4, level=2, phase=variant + 1)
    elif kind == 'snow':
        ground.dither((0, 0, TILE - 1, TILE - 1), 5, level=3, phase=variant)
        ground.dither((0, 0, TILE - 1, TILE - 1), 2, level=1, phase=variant + 2)
    sketch.stamp(ground, outline=False, rim=0, occlude=0)
    detail = sketch.piece(tone)

    if kind in ('grass', 'moss'):
        for _ in range(9 if kind == 'grass' else 6):
            x, y = r.randrange(2, TILE - 2), r.randrange(3, TILE - 2)
            lean = r.choice((-1, 0, 1))
            detail.line([(x, y), (x + lean, y - 3)], 4, 1)
            detail.line([(x + 2, y), (x + 2 + lean, y - 2)], 1, 1)
        for _ in range(3):
            x, y = r.randrange(1, TILE - 3), r.randrange(1, TILE - 3)
            detail.dot(x, y, 5)
    elif kind == 'dirt':
        for _ in range(7):
            x, y = r.randrange(2, TILE - 3), r.randrange(2, TILE - 3)
            detail.dot(x, y, 1)
            detail.dot(x + 1, y, 4)
        for _ in range(3):
            x, y = r.randrange(3, TILE - 5), r.randrange(3, TILE - 5)
            detail.ellipse((x, y, x + 2, y + 1), 5)
    elif kind == 'stone':
        seam = 16 if variant % 2 == 0 else 12
        detail.line([(0, seam), (TILE - 1, seam)], 1, 1)
        detail.line([(0, seam + 1), (TILE - 1, seam + 1)], 4, 1)
        for x in (0, 16):
            offset = 0 if variant % 2 == 0 else 8
            detail.line([((x + offset) % TILE, 0), ((x + offset) % TILE, seam)], 1, 1)
            detail.line([((x + offset + 8) % TILE, seam + 1), ((x + offset + 8) % TILE, TILE - 1)], 1, 1)
        for _ in range(5):
            detail.dot(r.randrange(1, TILE - 1), r.randrange(1, TILE - 1), 2)
    elif kind == 'wall':
        for row in range(4):
            y = row * 8
            detail.line([(0, y), (TILE - 1, y)], 0, 1)
            shift = 0 if row % 2 == 0 else 8
            for column in range(2):
                x = (column * 16 + shift) % TILE
                detail.line([(x, y + 1), (x, y + 7)], 0, 1)
            detail.line([(0, y + 1), (TILE - 1, y + 1)], 4, 1)
    elif kind == 'sand':
        for index in range(3):
            y = 6 + index * 11 + (variant % 2) * 2
            detail.line(catmull([(0, y), (10, y - 2), (20, y + 2), (TILE - 1, y)], 6), 4, 1)
            detail.line(catmull([(0, y + 1), (10, y - 1), (20, y + 3), (TILE - 1, y + 1)], 6), 3, 1)
    elif kind == 'snow':
        for _ in range(6):
            x, y = r.randrange(2, TILE - 2), r.randrange(2, TILE - 2)
            detail.dot(x, y, 5)
            detail.dot(x + 1, y + 1, 2)
        detail.line(catmull([(0, 22), (12, 20), (24, 24), (TILE - 1, 22)], 6), 2, 1)
    elif kind == 'water':
        for index in range(4):
            y = 3 + index * 8 + (variant % 4)
            detail.line(catmull([(0, y), (8, y - 2), (16, y), (24, y + 2), (TILE - 1, y)], 6), 4, 1)
            detail.line(catmull([(0, y + 3), (8, y + 1), (16, y + 3), (24, y + 5), (TILE - 1, y + 3)], 6), 1, 1)
        for _ in range(3):
            x, y = r.randrange(2, TILE - 4), r.randrange(2, TILE - 4)
            detail.line([(x, y), (x + 2, y)], 5, 1)
    elif kind == 'lava':
        crust = sketch.piece(ramp('#3f3230'))
        crust.rect((0, 0, TILE - 1, TILE - 1), 3)
        crust.dither((0, 0, TILE - 1, TILE - 1), 1, level=3, phase=variant)
        crust.dither((0, 0, TILE - 1, TILE - 1), 4, level=2, phase=variant + 2)
        sketch.stamp(crust, outline=False, rim=0, occlude=0)
        veins = sketch.piece(tone)
        for index in range(3):
            y = 5 + index * 10 + (variant % 3)
            veins.line(catmull([(0, y), (9, y + 4), (18, y - 3), (TILE - 1, y + 2)], 7), 4, 2)
            veins.line(catmull([(0, y), (9, y + 4), (18, y - 3), (TILE - 1, y + 2)], 7), 5, 1)
        sketch.stamp(veins, outline=False, rim=0, occlude=0)
        sketch.glow('#e8894a', 2, 0.34)
        return sketch.result()
    elif kind == 'wood':
        for row in range(4):
            y = row * 8
            plank = sketch.piece(ramp(blend(pigment.rgb(base), (40, 30, 26, 255), 0.12 * ((row + variant) % 3))))
            plank.rect((0, y, TILE - 1, y + 7), 3)
            plank.line([(1, y + 1), (TILE - 2, y + 1)], 4, 1)
            plank.line([(1, y + 6), (TILE - 2, y + 6)], 1, 1)
            for _ in range(2):
                gx = r.randrange(2, TILE - 4)
                plank.line([(gx, y + 3), (gx + 5, y + 4)], 2, 1)
            sketch.stamp(plank, outline=False, rim=0, occlude=0)
        nails = sketch.piece(tone)
        for row in range(4):
            nails.dot(3, row * 8 + 3, 5)
            nails.dot(TILE - 4, row * 8 + 4, 1)
        sketch.stamp(nails, outline=False, rim=0, occlude=0)
        return sketch.result()
    elif kind == 'crystal':
        for _ in range(5):
            x, y = r.randrange(4, TILE - 5), r.randrange(4, TILE - 5)
            size = r.randrange(2, 5)
            detail.poly([(x, y - size), (x + size, y), (x, y + size), (x - size, y)], 4)
            detail.poly([(x, y - size), (x + size * 0.5, y), (x, y)], 5)
        sketch.stamp(detail, outline=False, rim=0, occlude=0)
        sketch.glow('#8fb9c8', 2, 0.22)
        return sketch.result()
    elif kind == 'marsh':
        for _ in range(3):
            x, y = r.randrange(3, TILE - 9), r.randrange(3, TILE - 7)
            detail.ellipse((x, y, x + 7, y + 4), 1)
            detail.line([(x + 1, y + 1), (x + 5, y + 1)], 2, 1)
        for _ in range(5):
            x, y = r.randrange(2, TILE - 2), r.randrange(4, TILE - 2)
            detail.line([(x, y), (x, y - 3)], 4, 1)
    elif kind == 'ash':
        for _ in range(6):
            x, y = r.randrange(2, TILE - 3), r.randrange(2, TILE - 3)
            detail.dot(x, y, 1)
        for _ in range(2):
            x, y = r.randrange(3, TILE - 4), r.randrange(3, TILE - 4)
            detail.dot(x, y, (196, 96, 52, 255))
    sketch.stamp(detail, outline=False, rim=0, occlude=0)
    return sketch.result()


# ------------------------------------------------------------------ props --

def _trunk(sketch, x, foot, height, width, tone, lean=0.0):
    piece = sketch.piece(tone)
    piece.poly(catmull([
        (x - width, foot), (x - width * 0.42 + lean * 0.4, foot - height * 0.55),
        (x - width * 0.30 + lean, foot - height),
        (x + width * 0.30 + lean, foot - height),
        (x + width * 0.44 + lean * 0.4, foot - height * 0.55), (x + width, foot),
    ], 6, closed=True), 3)
    # buttress roots
    piece.poly(catmull([(x - width * 1.7, foot), (x - width * 0.6, foot - height * 0.16),
                        (x - width * 0.2, foot)], 4, closed=True), 2)
    piece.poly(catmull([(x + width * 1.7, foot), (x + width * 0.6, foot - height * 0.16),
                        (x + width * 0.2, foot)], 4, closed=True), 2)
    sketch.stamp(piece, rim=0.85, occlude=0.65)
    bark = sketch.piece(tone)
    for step in range(3):
        bark.line(catmull([(x - width * 0.3 + step * width * 0.3, foot - height * 0.12),
                           (x - width * 0.2 + step * width * 0.3 + lean * 0.4, foot - height * 0.6),
                           (x - width * 0.1 + step * width * 0.3 + lean, foot - height * 0.95)], 6),
                  1 if step % 2 else 4, 1)
    bark.clip(piece)
    sketch.overlay(bark)
    return piece


def _canopy(sketch, x, y, rx, ry, tone, lobes=5, seed_text='canopy'):
    piece = sketch.piece(tone)
    r = _rng(seed_text)
    points = []
    for index in range(lobes * 2):
        angle = index * math.pi / lobes
        radius = 1.0 if index % 2 == 0 else 0.78
        radius *= 0.92 + r.random() * 0.18
        points.append((x + math.cos(angle - math.pi / 2) * rx * radius,
                       y + math.sin(angle - math.pi / 2) * ry * radius))
    piece.poly(catmull(points, 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.7)
    light = sketch.piece(tone)
    for index in range(lobes):
        angle = index * math.tau / lobes - 1.2
        lx = x + math.cos(angle) * rx * 0.52
        ly = y + math.sin(angle) * ry * 0.52
        light.disc(lx, ly, min(rx, ry) * 0.30, 4)
    light.clip(piece)
    sketch.overlay(light)
    speckle = sketch.piece(tone)
    for _ in range(16):
        sx = x + (r.random() - 0.5) * rx * 1.6
        sy = y + (r.random() - 0.5) * ry * 1.6
        speckle.dot(sx, sy, 5 if r.random() > 0.4 else 1)
    speckle.clip(piece)
    sketch.overlay(speckle)
    return piece


def tree(kind):
    size = (112, 144) if kind == 'ancient_oak' else (80, 112)
    sketch = Sketch(size)
    w, h = size
    x = w / 2
    foot = h - 4
    wood = {'willow': '#7a6a4e', 'dead_tree': '#6b5b4c', 'palm': '#8a6f4a',
            'snow_pine': '#5f5344', 'pine': '#6a563e'}.get(kind, '#7a5a3c')
    leaf = {'pine': '#3f5f42', 'snow_pine': '#48685a', 'willow': '#79924e',
            'palm': '#5f8a4a', 'ancient_oak': '#4a6b3c'}.get(kind, '#557a42')
    tone = ramp(wood)
    if kind == 'dead_tree':
        _trunk(sketch, x, foot, h * 0.72, w * 0.085, tone)
        branch = sketch.piece(tone)
        for sign, height, reach in ((-1, 0.52, 0.30), (1, 0.62, 0.34), (-1, 0.74, 0.22), (1, 0.80, 0.18)):
            start = (x + sign * w * 0.02, foot - h * height)
            end = (x + sign * w * reach, foot - h * (height + 0.16))
            branch.poly(taper_shape(start, end, 4.0, 1.6), 3)
            branch.poly(taper_shape(end, (end[0] + sign * w * 0.08, end[1] - h * 0.08), 1.8, 1.0), 3)
        sketch.stamp(branch, rim=0.8, occlude=0.6)
        return sketch.result()
    if kind == 'palm':
        trunk = sketch.piece(tone)
        trunk.poly(taper_shape((x - w * 0.03, foot), (x + w * 0.10, foot - h * 0.66), w * 0.13, w * 0.08), 3)
        sketch.stamp(trunk, rim=0.85, occlude=0.6)
        rings = sketch.piece(tone)
        for step in range(6):
            t = step / 5.0
            rings.line([(x - w * 0.03 + t * w * 0.13 - 4, foot - h * 0.66 * t),
                        (x - w * 0.03 + t * w * 0.13 + 4, foot - h * 0.66 * t - 1)], 1, 1)
        rings.clip(trunk)
        sketch.overlay(rings)
        crown = sketch.piece(ramp(leaf))
        top = (x + w * 0.10, foot - h * 0.68)
        for index in range(7):
            angle = -math.pi + index * math.pi / 6
            tip = (top[0] + math.cos(angle) * w * 0.36, top[1] + math.sin(angle) * h * 0.20)
            mid = ((top[0] + tip[0]) / 2, (top[1] + tip[1]) / 2 - h * 0.05)
            crown.poly(catmull([top, (mid[0], mid[1] - 4), tip, (mid[0], mid[1] + 4)], 6, closed=True), 3)
        sketch.stamp(crown, rim=0.9, occlude=0.6)
        nuts = sketch.piece(ramp('#7a5a3c'))
        for dx in (-3, 2, 5):
            nuts.disc(top[0] + dx, top[1] + 4, 2.4, 3)
        sketch.stamp(nuts, rim=0.8, occlude=0.5)
        return sketch.result()
    if kind in ('pine', 'snow_pine'):
        _trunk(sketch, x, foot, h * 0.34, w * 0.065, tone)
        needles = ramp(leaf)
        layers = 5
        for index in range(layers):
            t = index / (layers - 1)
            y = foot - h * (0.28 + t * 0.60)
            spread = w * (0.40 - t * 0.24)
            piece = sketch.piece(needles)
            piece.poly(catmull([
                (x - spread, y), (x - spread * 0.5, y - h * 0.05), (x, y - h * 0.14),
                (x + spread * 0.5, y - h * 0.05), (x + spread, y),
                (x + spread * 0.4, y + h * 0.02), (x - spread * 0.4, y + h * 0.02),
            ], 5, closed=True), 3)
            sketch.stamp(piece, rim=0.85, occlude=0.6)
            if kind == 'snow_pine':
                snow = sketch.piece(ramp('#dae4e8'))
                snow.poly(catmull([
                    (x - spread * 0.92, y - 1), (x, y - h * 0.12), (x + spread * 0.92, y - 1),
                    (x + spread * 0.5, y - h * 0.045), (x - spread * 0.5, y - h * 0.045)], 5, closed=True), 3)
                snow.clip(piece)
                sketch.overlay(snow)
        return sketch.result()
    if kind == 'willow':
        _trunk(sketch, x, foot, h * 0.44, w * 0.10, tone)
        _canopy(sketch, x, foot - h * 0.60, w * 0.40, h * 0.20, ramp(leaf), 6, 'willow')
        drape = sketch.piece(ramp(leaf))
        for index in range(9):
            sx = x - w * 0.36 + index * w * 0.09
            drape.line(catmull([(sx, foot - h * 0.60), (sx + 2, foot - h * 0.42),
                                (sx - 1, foot - h * 0.26)], 6), 2, 2)
        sketch.stamp(drape, rim=0.6, occlude=0.4)
        return sketch.result()
    # broadleaf
    scale = 1.0 if kind != 'ancient_oak' else 1.12
    _trunk(sketch, x, foot, h * 0.46, w * 0.10 * scale, tone, lean=-2 if kind == 'ancient_oak' else 0)
    limbs = sketch.piece(tone)
    for sign, height in ((-1, 0.40), (1, 0.44)):
        limbs.poly(taper_shape((x, foot - h * height), (x + sign * w * 0.22, foot - h * (height + 0.16)), 5.0, 2.4), 3)
    sketch.stamp(limbs, rim=0.8, occlude=0.6)
    _canopy(sketch, x, foot - h * 0.66, w * 0.42 * scale, h * 0.26 * scale, ramp(leaf),
            6 if kind == 'ancient_oak' else 5, kind)
    return sketch.result()


def prop(name):
    if name == 'shadow':
        sketch = Sketch((32, 12))
        piece = sketch.piece(ramp('#1d2426'))
        piece.ellipse((1, 1, 30, 10), (20, 26, 30, 90))
        sketch.overlay(piece)
        return sketch.result()
    if name in TREES:
        return tree(name)
    size = (48, 64)
    sketch = Sketch(size)
    w, h = size
    x, foot = w / 2, h - 5
    r = _rng('prop', name)
    if name in ('rock', 'snow_rock', 'basalt'):
        base = {'snow_rock': '#9aa8ad', 'basalt': '#4f4a52'}.get(name, '#7c7a74')
        tone = ramp(base)
        piece = sketch.piece(tone)
        if name == 'basalt':
            piece.poly([(x - 11, foot), (x - 9, foot - 26), (x - 2, foot - 32),
                        (x + 4, foot - 24), (x + 3, foot), ], 3)
            piece.poly([(x + 3, foot), (x + 5, foot - 18), (x + 12, foot - 14), (x + 13, foot)], 2)
        else:
            piece.poly(catmull([(x - 14, foot), (x - 12, foot - 12), (x - 5, foot - 19),
                                (x + 6, foot - 17), (x + 14, foot - 8), (x + 13, foot)], 6, closed=True), 3)
            piece.poly(catmull([(x - 4, foot), (x + 2, foot - 9), (x + 11, foot - 6), (x + 12, foot)], 5, closed=True), 2)
        sketch.stamp(piece, rim=0.9, occlude=0.7)
        facets = sketch.piece(tone)
        facets.line([(x - 9, foot - 10), (x - 3, foot - 16)], 1, 1)
        facets.line([(x + 1, foot - 14), (x + 8, foot - 9)], 4, 1)
        facets.clip(piece)
        sketch.overlay(facets)
        if name == 'snow_rock':
            snow = sketch.piece(ramp('#e0e8ea'))
            snow.poly(catmull([(x - 12, foot - 10), (x - 4, foot - 19), (x + 7, foot - 16),
                               (x + 13, foot - 7), (x + 4, foot - 12), (x - 5, foot - 13)], 6, closed=True), 3)
            snow.clip(piece)
            sketch.overlay(snow)
        return sketch.result()
    if name == 'bush':
        tone = ramp('#4f6f3f')
        piece = _canopy(sketch, x, foot - 12, 15, 11, tone, 5, 'bush')
        stems = sketch.piece(ramp('#6a5238'))
        stems.line([(x, foot), (x, foot - 8)], 3, 2)
        sketch.stamp(stems, rim=0.6, occlude=0.5)
        berries = sketch.piece(ramp('#a8434a'))
        for _ in range(4):
            berries.disc(x + r.randrange(-10, 10), foot - 8 - r.randrange(0, 12), 1.8, 3)
        sketch.stamp(berries, rim=0.8, occlude=0.4)
        return sketch.result()
    if name == 'flowers':
        stems = sketch.piece(ramp('#5f7a44'))
        heads = []
        for index in range(5):
            sx = x - 12 + index * 6 + r.randrange(-1, 2)
            top = foot - 10 - r.randrange(0, 9)
            stems.line(catmull([(sx, foot), (sx + 1, (foot + top) / 2), (sx, top)], 5), 3, 1)
            stems.poly(catmull([(sx, (foot + top) / 2), (sx - 4, (foot + top) / 2 - 3),
                                (sx - 1, (foot + top) / 2 - 4)], 4, closed=True), 2)
            heads.append((sx, top))
        sketch.stamp(stems, rim=0.7, occlude=0.5)
        for index, (sx, top) in enumerate(heads):
            bloom = sketch.piece(ramp(('#c86a7a', '#d8bf5a', '#8a7ac0', '#d88a4a', '#cfd2d8')[index % 5]))
            for angle in range(0, 360, 72):
                rad = math.radians(angle)
                bloom.disc(sx + math.cos(rad) * 2.2, top + math.sin(rad) * 2.2, 1.7, 3)
            bloom.disc(sx, top, 1.4, 5)
            sketch.stamp(bloom, rim=0.8, occlude=0.4)
        return sketch.result()
    if name == 'grass_tuft':
        piece = sketch.piece(ramp('#63804a'))
        for index in range(9):
            sx = x - 12 + index * 3
            lean = r.randrange(-4, 5)
            piece.line(catmull([(sx, foot), (sx + lean * 0.4, foot - 7), (sx + lean, foot - 13)], 5), 3, 1)
        sketch.stamp(piece, rim=0.7, occlude=0.5)
        tips = sketch.piece(ramp('#8aa35c'))
        for index in range(4):
            sx = x - 8 + index * 5
            tips.line([(sx, foot - 8), (sx + r.randrange(-3, 4), foot - 15)], 4, 1)
        sketch.stamp(tips, outline=False, rim=0, occlude=0)
        return sketch.result()
    if name == 'reeds':
        piece = sketch.piece(ramp('#6f8a4c'))
        heads = []
        for index in range(6):
            sx = x - 11 + index * 4.4
            top = foot - 22 - r.randrange(0, 8)
            piece.line(catmull([(sx, foot), (sx + r.randrange(-2, 3), (foot + top) / 2), (sx, top)], 6), 3, 1)
            heads.append((sx, top))
        sketch.stamp(piece, rim=0.7, occlude=0.5)
        cattail = sketch.piece(ramp('#7a5a3c'))
        for sx, top in heads[:3]:
            cattail.poly(catmull([(sx - 2, top + 6), (sx - 2, top), (sx + 2, top), (sx + 2, top + 6)], 4, closed=True), 3)
        sketch.stamp(cattail, rim=0.8, occlude=0.5)
        return sketch.result()
    if name == 'mushrooms':
        for index, (dx, size) in enumerate(((-8, 1.0), (3, 1.3), (10, 0.75))):
            stalk = sketch.piece(ramp('#d9cdb0'))
            stalk.poly(catmull([(x + dx - 2.6 * size, foot), (x + dx - 1.8 * size, foot - 9 * size),
                                (x + dx + 1.8 * size, foot - 9 * size), (x + dx + 2.6 * size, foot)],
                               4, closed=True), 3)
            sketch.stamp(stalk, rim=0.8, occlude=0.55)
            cap = sketch.piece(ramp(('#a8524a', '#8a6ab0', '#c08a4a')[index % 3]))
            cap.poly(catmull([(x + dx - 8 * size, foot - 8 * size), (x + dx - 5 * size, foot - 15 * size),
                              (x + dx, foot - 17 * size), (x + dx + 5 * size, foot - 15 * size),
                              (x + dx + 8 * size, foot - 8 * size), (x + dx, foot - 6 * size)], 6, closed=True), 3)
            sketch.stamp(cap, rim=0.9, occlude=0.6)
            spots = sketch.piece(ramp('#e6dcc2'))
            for sx, sy in ((-4, -11), (1, -13), (4, -10)):
                spots.disc(x + dx + sx * size, foot + sy * size, 1.5 * size, 4)
            spots.clip(cap)
            sketch.overlay(spots)
        return sketch.result()
    if name == 'cactus':
        tone = ramp('#5f8a58')
        piece = sketch.piece(tone)
        piece.poly(catmull([(x - 6, foot), (x - 6, foot - 30), (x, foot - 35), (x + 6, foot - 30),
                            (x + 6, foot)], 5, closed=True), 3)
        piece.poly(catmull([(x - 6, foot - 20), (x - 13, foot - 22), (x - 14, foot - 30),
                            (x - 10, foot - 30), (x - 10, foot - 25), (x - 6, foot - 24)], 5, closed=True), 3)
        piece.poly(catmull([(x + 6, foot - 14), (x + 12, foot - 16), (x + 13, foot - 24),
                            (x + 9, foot - 24), (x + 9, foot - 19), (x + 6, foot - 18)], 5, closed=True), 3)
        sketch.stamp(piece, rim=0.9, occlude=0.6)
        ribs = sketch.piece(tone)
        for dx in (-3, 0, 3):
            ribs.line([(x + dx, foot - 4), (x + dx, foot - 30)], 1 if dx else 4, 1)
        ribs.clip(piece)
        sketch.overlay(ribs)
        spines = sketch.piece(ramp('#e0dcc0'))
        for step in range(7):
            y = foot - 6 - step * 4
            spines.line([(x - 7, y), (x - 9, y - 1)], 4, 1)
            spines.line([(x + 7, y), (x + 9, y - 1)], 4, 1)
        sketch.stamp(spines, outline=False, rim=0, occlude=0)
        return sketch.result()
    if name == 'crystal':
        return crystal_cluster(sketch, x, foot, '#8fb9c8')
    if name == 'signpost':
        post = sketch.piece(ramp('#8a6a45'))
        post.poly(taper_shape((x, foot), (x, foot - 34), 6.0, 5.0), 3)
        sketch.stamp(post, rim=0.85, occlude=0.6)
        board = sketch.piece(ramp('#a07f4e'))
        board.poly([(x - 16, foot - 32), (x + 12, foot - 33), (x + 16, foot - 27),
                    (x + 12, foot - 21), (x - 16, foot - 22)], 3)
        sketch.stamp(board, rim=0.9, occlude=0.6)
        text = sketch.piece(ramp('#5f4a33'))
        for index in range(3):
            text.line([(x - 12, foot - 30 + index * 3), (x + 6 - index * 3, foot - 30 + index * 3)], 3, 1)
        text.clip(board)
        sketch.overlay(text)
        return sketch.result()
    if name == 'waystone':
        tone = ramp('#7d8088')
        piece = sketch.piece(tone)
        piece.poly(catmull([(x - 10, foot), (x - 8, foot - 26), (x - 3, foot - 34),
                            (x + 5, foot - 32), (x + 9, foot - 20), (x + 10, foot)], 6, closed=True), 3)
        sketch.stamp(piece, rim=0.9, occlude=0.7)
        glyph = sketch.piece(ramp('#8fb9c8'))
        glyph.line([(x - 1, foot - 28), (x - 1, foot - 10)], 4, 1)
        glyph.line([(x - 5, foot - 24), (x + 4, foot - 21)], 4, 1)
        glyph.line([(x - 5, foot - 15), (x + 4, foot - 18)], 4, 1)
        sketch.stamp(glyph, outline=False, rim=0, occlude=0)
        sketch.glow('#8fb9c8', 2, 0.34)
        return sketch.result()
    if name == 'stairs':
        tone = ramp('#84837c')
        for index in range(4):
            step = sketch.piece(tone)
            y = foot - index * 6
            inset = index * 3
            step.poly([(x - 16 + inset, y - 6), (x + 16 - inset, y - 6),
                       (x + 14 - inset, y), (x - 14 + inset, y)], 3)
            step.line([(x - 15 + inset, y - 5), (x + 15 - inset, y - 5)], 5, 1)
            sketch.stamp(step, rim=0.8, occlude=0.6)
        return sketch.result()
    if name == 'stump':
        tone = ramp('#7a5a3c')
        piece = sketch.piece(tone)
        piece.poly(catmull([(x - 11, foot), (x - 10, foot - 12), (x + 10, foot - 13),
                            (x + 11, foot)], 5, closed=True), 3)
        sketch.stamp(piece, rim=0.85, occlude=0.65)
        top = sketch.piece(tone)
        top.ellipse((x - 10, foot - 17, x + 10, foot - 9), 2)
        top.ellipse((x - 7, foot - 16, x + 7, foot - 11), 3)
        top.ellipse((x - 4, foot - 15, x + 4, foot - 12), 1)
        sketch.stamp(top, rim=0.7, occlude=0.4)
        moss = sketch.piece(ramp('#5f7a44'))
        moss.poly(catmull([(x - 11, foot - 4), (x - 6, foot - 8), (x - 1, foot - 5),
                           (x - 3, foot - 1)], 5, closed=True), 3)
        moss.clip(piece)
        sketch.overlay(moss)
        return sketch.result()
    if name == 'loot':
        bag = sketch.piece(ramp('#8a6a45'))
        bag.poly(catmull([(x - 11, foot), (x - 12, foot - 11), (x - 5, foot - 17),
                          (x + 6, foot - 16), (x + 12, foot - 9), (x + 11, foot)], 6, closed=True), 3)
        sketch.stamp(bag, rim=0.9, occlude=0.65)
        tie = sketch.piece(ramp('#5f4a33'))
        tie.line([(x - 8, foot - 13), (x + 9, foot - 12)], 3, 2)
        sketch.stamp(tie, outline=False, rim=0, occlude=0)
        coins = sketch.piece(ramp('#d0a63f'))
        for dx, dy in ((-4, -19), (1, -21), (5, -18)):
            coins.disc(x + dx, foot + dy, 2.4, 3)
            coins.dot(x + dx - 1, foot + dy - 1, 5)
        sketch.stamp(coins, rim=0.9, occlude=0.5)
        sketch.glow('#e8cf5e', 2, 0.4)
        return sketch.result()
    # fallback marker so nothing is ever an empty tile
    piece = sketch.piece(ramp('#8a8272'))
    piece.poly(catmull([(x - 9, foot), (x - 7, foot - 14), (x + 7, foot - 15), (x + 9, foot)], 5, closed=True), 3)
    sketch.stamp(piece, rim=0.85, occlude=0.6)
    return sketch.result()


def crystal_cluster(sketch, x, foot, colour):
    tone = ramp(colour)
    for dx, height, width in ((-8, 18, 5), (0, 30, 6), (7, 22, 5), (12, 12, 4)):
        piece = sketch.piece(tone)
        piece.poly([(x + dx - width, foot), (x + dx - width * 0.7, foot - height * 0.72),
                    (x + dx, foot - height), (x + dx + width * 0.7, foot - height * 0.66),
                    (x + dx + width, foot)], 3)
        piece.poly([(x + dx - width * 0.35, foot - 1), (x + dx - width * 0.2, foot - height * 0.66),
                    (x + dx, foot - height), (x + dx + width * 0.1, foot - height * 0.6),
                    (x + dx + width * 0.15, foot - 1)], 5)
        sketch.stamp(piece, rim=0.95, occlude=0.6)
    sketch.glow(colour, 3, 0.45)
    return sketch.result()


# ----------------------------------------------------------------- chests --

CHEST_LOOK = {
    'weathered': ('#8a6a45', '#7d7b72', 0), 'locked': ('#9a7346', '#b0a06a', 1),
    'ancient': ('#7f7460', '#a89a6a', 2), 'runic': ('#6a5f86', '#a98fd0', 3),
    'royal': ('#a0824c', '#d0a63f', 4), 'cursed': ('#5f5468', '#7a6b9e', 5),
    'mimic': ('#8a6a45', '#c0a24a', 0),
}


def chest(kind, opened=False):
    wood, metal, flavour = CHEST_LOOK.get(kind, ('#8a6a45', '#a6a29a', 0))
    sketch = Sketch((48, 48))
    x, foot = 24, 43
    body = sketch.piece(ramp(wood))
    body.poly([(x - 15, foot - 16), (x + 15, foot - 16), (x + 15, foot), (x - 15, foot)], 3)
    sketch.stamp(body, rim=0.85, occlude=0.7)
    planks = sketch.piece(ramp(wood))
    for dx in (-8, 0, 8):
        planks.line([(x + dx, foot - 15), (x + dx, foot - 1)], 1, 1)
        planks.line([(x + dx + 1, foot - 15), (x + dx + 1, foot - 1)], 4, 1)
    planks.clip(body)
    sketch.overlay(planks)
    lid_y = foot - 16
    lift = 9 if opened else 0
    lid = sketch.piece(ramp(wood))
    if opened:
        lid.poly([(x - 15, lid_y - lift), (x + 15, lid_y - lift - 3),
                  (x + 15, lid_y - lift - 10), (x - 15, lid_y - lift - 7)], 3)
    else:
        lid.poly(catmull([(x - 15, lid_y), (x - 13, lid_y - 8), (x, lid_y - 10),
                          (x + 13, lid_y - 8), (x + 15, lid_y)], 5, closed=True), 3)
    sketch.stamp(lid, rim=0.9, occlude=0.6)
    bands = sketch.piece(ramp(metal))
    for dx in (-11, 11):
        bands.rect((x + dx - 2, lid_y - (10 + lift if not opened else lift + 9), x + dx + 2, foot - 1), 3)
    bands.rect((x - 15, lid_y - 1, x + 15, lid_y + 2), 3)
    sketch.stamp(bands, rim=0.85, occlude=0.55)
    lock = sketch.piece(ramp(metal))
    lock.rect((x - 4, lid_y + 1, x + 4, lid_y + 8), 3)
    lock.disc(x, lid_y + 4, 1.6, 0)
    sketch.stamp(lock, rim=0.9, occlude=0.5)
    if kind == 'mimic':
        teeth = sketch.piece(ramp('#e4dcc2'))
        for index in range(6):
            tx = x - 13 + index * 5
            teeth.poly([(tx, lid_y + 1), (tx + 4, lid_y + 1), (tx + 2, lid_y + 5)], 3)
        sketch.stamp(teeth, rim=0.6, occlude=0.4)
        eyes = sketch.piece(ramp('#d8a24a'))
        for dx in (-7, 7):
            eyes.disc(x + dx, lid_y - 5, 2.0, 4)
            eyes.dot(x + dx, lid_y - 5, (28, 24, 30, 255))
        sketch.stamp(eyes, rim=0.8, occlude=0.4)
    if opened:
        glow = sketch.piece(ramp('#e8cf5e'))
        glow.poly([(x - 12, lid_y + 1), (x + 12, lid_y + 1), (x + 10, lid_y - 4), (x - 10, lid_y - 4)], 4)
        sketch.stamp(glow, outline=False, rim=0, occlude=0)
        sketch.glow('#e8cf5e', 3, 0.45)
    if kind in ('runic', 'cursed'):
        sketch.glow('#a98fd0' if kind == 'runic' else '#7a6b9e', 3, 0.4)
    return sketch.result()


# -------------------------------------------------------------- resources --

ORE_COLOURS = {
    'copper': '#b06a3c', 'iron': '#8d959c', 'steel': '#a9b6c0', 'silver': '#cfd8dd',
    'cobalt': '#5d84ad', 'mithril': '#8fc4bd', 'obsidian': '#5b5468', 'aetherium': '#a8b8e2',
    'gold': '#d0a63f', 'coal': '#3f3f45', 'crystal': '#8fb9c8', 'salt': '#dfe2e4',
}


def resource(definition):
    ident = definition.get('id', '')
    skill = definition.get('skill', '')
    if skill == 'woodcutting':
        for name in ('pine', 'snow_pine', 'willow', 'palm'):
            if name.split('_')[-1] in ident:
                return tree(name)
        if 'frost' in ident or 'ice' in ident:
            return tree('snow_pine')
        if 'ancient' in ident:
            return tree('ancient_oak')
        if 'dead' in ident or 'black' in ident:
            return tree('dead_tree')
        return tree('oak')
    if skill == 'fishing':
        sketch = Sketch((48, 48))
        water = sketch.piece(ramp('#3c6580'))
        water.ellipse((3, 12, 44, 42), 3)
        sketch.stamp(water, rim=0.5, occlude=0.5)
        ripples = sketch.piece(ramp('#3c6580'))
        for index, (cx, cy, rx) in enumerate(((16, 24, 8), (30, 20, 6), (26, 34, 7))):
            ripples.arc((cx - rx, cy - rx * 0.5, cx + rx, cy + rx * 0.5), 20, 320, 5, 1)
            ripples.arc((cx - rx * 0.6, cy - rx * 0.3, cx + rx * 0.6, cy + rx * 0.3), 30, 300, 4, 1)
        ripples.clip(water)
        sketch.overlay(ripples)
        fish = sketch.piece(ramp('#9aa27f'))
        fish.poly(catmull([(18, 30), (24, 27), (30, 30), (24, 33)], 5, closed=True), 3)
        fish.poly([(18, 30), (14, 27), (14, 33)], 3)
        sketch.stamp(fish, rim=0.8, occlude=0.5)
        return sketch.result()
    if skill in ('mining', 'prospecting', 'excavation'):
        sketch = Sketch((48, 64))
        x, foot = 24, 59
        rock = ramp('#77756f' if skill != 'excavation' else '#7d6448')
        piece = sketch.piece(rock)
        piece.poly(catmull([(x - 16, foot), (x - 14, foot - 16), (x - 6, foot - 26),
                            (x + 7, foot - 24), (x + 15, foot - 12), (x + 16, foot)], 7, closed=True), 3)
        sketch.stamp(piece, rim=0.9, occlude=0.7)
        facet = sketch.piece(rock)
        facet.line([(x - 10, foot - 14), (x - 2, foot - 22)], 1, 1)
        facet.line([(x + 2, foot - 20), (x + 11, foot - 12)], 4, 1)
        facet.clip(piece)
        sketch.overlay(facet)
        metal = next((c for key, c in ORE_COLOURS.items() if key in ident), '#b8ab77')
        vein = sketch.piece(ramp(metal))
        for cx, cy, size in ((-8, -8, 2.6), (-1, -15, 3.0), (6, -9, 2.4), (9, -17, 2.0)):
            vein.poly([(x + cx, foot + cy - size), (x + cx + size, foot + cy),
                       (x + cx, foot + cy + size), (x + cx - size, foot + cy)], 3)
            vein.dot(x + cx - 0.6, foot + cy - 0.8, 5)
        vein.clip(piece)
        sketch.overlay(vein)
        if 'crystal' in ident or 'aetherium' in ident:
            sketch.glow(metal, 2, 0.35)
        return sketch.result()
    if skill == 'skinning' or 'carcass' in ident:
        sketch = Sketch((48, 64))
        x, foot = 24, 59
        hide = sketch.piece(ramp('#8a6a4c'))
        hide.poly(catmull([(x - 16, foot), (x - 14, foot - 9), (x - 4, foot - 13),
                           (x + 10, foot - 11), (x + 16, foot - 3), (x + 8, foot)], 6, closed=True), 3)
        sketch.stamp(hide, rim=0.85, occlude=0.65)
        legs = sketch.piece(ramp('#7a5c42'))
        for dx in (-9, -2, 6):
            legs.poly(taper_shape((x + dx, foot - 11), (x + dx + 3, foot - 19), 3.2, 2.2), 3)
        sketch.stamp(legs, rim=0.7, occlude=0.5)
        head = sketch.piece(ramp('#8a6a4c'))
        head.disc(x + 17, foot - 6, 4.6, 3)
        sketch.stamp(head, rim=0.8, occlude=0.5)
        return sketch.result()
    if skill == 'farming':
        sketch = Sketch((48, 64))
        x, foot = 24, 59
        soil = sketch.piece(ramp('#6f5842'))
        soil.ellipse((x - 16, foot - 6, x + 16, foot + 2), 2)
        sketch.stamp(soil, rim=0.5, occlude=0.5)
        stalks = sketch.piece(ramp('#b39a54'))
        heads = []
        for index in range(5):
            sx = x - 12 + index * 6
            top = foot - 26 - (index % 2) * 4
            stalks.line(catmull([(sx, foot - 2), (sx + 1, (foot + top) / 2), (sx, top)], 5), 3, 1)
            heads.append((sx, top))
        sketch.stamp(stalks, rim=0.7, occlude=0.5)
        grain = sketch.piece(ramp('#d8be6a'))
        for sx, top in heads:
            grain.poly(catmull([(sx - 3, top + 8), (sx - 3, top + 1), (sx, top - 2),
                                (sx + 3, top + 1), (sx + 3, top + 8)], 5, closed=True), 3)
        sketch.stamp(grain, rim=0.9, occlude=0.5)
        return sketch.result()
    # herbalism and foraging
    sketch = Sketch((48, 64))
    x, foot = 24, 59
    if 'mushroom' in ident or 'fungus' in ident or 'spore' in ident:
        return prop('mushrooms')
    if 'berry' in ident:
        return prop('bush')
    leafy = sketch.piece(ramp('#5f7a44'))
    for index in range(4):
        angle = -2.5 + index * 0.7
        tip = (x + math.cos(angle) * 15, foot - 8 + math.sin(angle) * 14)
        leafy.poly(catmull([(x, foot - 4), (tip[0] - 3, tip[1] + 3), tip, (tip[0] + 2, tip[1] + 5)],
                           6, closed=True), 3)
    leafy.line([(x, foot), (x, foot - 12)], 2, 2)
    sketch.stamp(leafy, rim=0.85, occlude=0.6)
    colour = ('#d8a24a' if 'ember' in ident else '#8fc9d8' if 'frost' in ident else
              '#cfd3ea' if 'moon' in ident or 'ghost' in ident else
              '#a8414a' if 'blood' in ident else '#c8a8d0')
    bloom = sketch.piece(ramp(colour))
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        bloom.disc(x + math.cos(rad) * 5, foot - 22 + math.sin(rad) * 5, 3.0, 3)
    bloom.disc(x, foot - 22, 2.6, 5)
    sketch.stamp(bloom, rim=0.9, occlude=0.5)
    if 'ghost' in ident or 'moon' in ident or 'ember' in ident:
        sketch.glow(colour, 2, 0.35)
    return sketch.result()


# ------------------------------------------------------------- structures --

def structure(ident):
    sketch = Sketch((64, 72))
    x, foot = 32, 68
    if 'campfire' in ident:
        stones = sketch.piece(ramp('#7c7a74'))
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            stones.ellipse((x + math.cos(rad) * 16 - 5, foot - 6 + math.sin(rad) * 6 - 3,
                            x + math.cos(rad) * 16 + 5, foot - 6 + math.sin(rad) * 6 + 3), 3)
        sketch.stamp(stones, rim=0.85, occlude=0.6)
        logs = sketch.piece(ramp('#7a5a3c'))
        logs.poly(taper_shape((x - 11, foot - 8), (x + 10, foot - 14), 5.0, 4.0), 3)
        logs.poly(taper_shape((x + 11, foot - 8), (x - 10, foot - 14), 5.0, 4.0), 2)
        sketch.stamp(logs, rim=0.8, occlude=0.6)
        fire = sketch.piece(ramp('#d4703c'))
        fire.poly(catmull([(x - 9, foot - 12), (x - 5, foot - 24), (x - 1, foot - 18),
                           (x + 3, foot - 32), (x + 8, foot - 20), (x + 9, foot - 12)], 6, closed=True), 3)
        sketch.stamp(fire, rim=0.9, occlude=0.4)
        core = sketch.piece(ramp('#f0d27a'))
        core.poly(catmull([(x - 4, foot - 12), (x - 1, foot - 21), (x + 3, foot - 15),
                           (x + 5, foot - 24), (x + 6, foot - 12)], 5, closed=True), 4)
        sketch.stamp(core, outline=False, rim=0, occlude=0)
        sketch.glow('#e8894a', 4, 0.55)
        return sketch.result()
    if 'rune' in ident:
        table = sketch.piece(ramp('#6a5f86'))
        table.poly([(x - 22, foot - 22), (x + 22, foot - 22), (x + 20, foot - 15), (x - 20, foot - 15)], 3)
        for dx in (-16, 14):
            table.poly([(x + dx, foot - 15), (x + dx + 5, foot - 15), (x + dx + 4, foot), (x + dx + 1, foot)], 2)
        sketch.stamp(table, rim=0.85, occlude=0.65)
        stone = sketch.piece(ramp('#a98fd0'))
        stone.poly([(x - 6, foot - 24), (x + 6, foot - 24), (x + 5, foot - 34), (x - 5, foot - 34)], 3)
        stone.line([(x, foot - 32), (x, foot - 26)], 5, 1)
        stone.line([(x - 3, foot - 30), (x + 3, foot - 29)], 5, 1)
        sketch.stamp(stone, rim=0.9, occlude=0.5)
        sketch.glow('#a98fd0', 3, 0.5)
        return sketch.result()
    if 'kitchen' in ident:
        hearth = sketch.piece(ramp('#7c7a74'))
        hearth.poly([(x - 20, foot), (x - 20, foot - 22), (x + 20, foot - 22), (x + 20, foot)], 3)
        hearth.erase((x - 11, foot - 16, x + 11, foot))
        sketch.stamp(hearth, rim=0.85, occlude=0.7)
        fire = sketch.piece(ramp('#d4703c'))
        fire.poly(catmull([(x - 8, foot - 1), (x - 4, foot - 10), (x, foot - 5),
                           (x + 4, foot - 13), (x + 8, foot - 1)], 5, closed=True), 3)
        sketch.stamp(fire, outline=False, rim=0, occlude=0)
        pot = sketch.piece(ramp('#5f6166'))
        pot.poly(catmull([(x - 9, foot - 22), (x + 9, foot - 22), (x + 7, foot - 32),
                          (x - 7, foot - 32)], 5, closed=True), 3)
        pot.arc((x - 8, foot - 38, x + 8, foot - 28), 190, 350, 4, 1)
        sketch.stamp(pot, rim=0.9, occlude=0.6)
        sketch.glow('#e8894a', 3, 0.35)
        return sketch.result()
    if 'saw' in ident:
        bench = sketch.piece(ramp('#8a6a45'))
        bench.poly([(x - 22, foot - 24), (x + 22, foot - 24), (x + 22, foot - 18), (x - 22, foot - 18)], 3)
        for dx in (-18, 13):
            bench.poly([(x + dx, foot - 18), (x + dx + 5, foot - 18), (x + dx + 4, foot), (x + dx + 1, foot)], 2)
        sketch.stamp(bench, rim=0.85, occlude=0.65)
        log = sketch.piece(ramp('#7a5a3c'))
        log.poly(taper_shape((x - 16, foot - 29), (x + 12, foot - 29), 10.0, 10.0), 3)
        log.disc(x + 12, foot - 29, 5.0, 2)
        sketch.stamp(log, rim=0.8, occlude=0.6)
        blade = sketch.piece(ramp('#a9b6c0'))
        blade.poly([(x - 4, foot - 42), (x + 2, foot - 42), (x + 2, foot - 26), (x - 4, foot - 26)], 3)
        for index in range(5):
            blade.poly([(x + 2, foot - 40 + index * 3), (x + 6, foot - 39 + index * 3), (x + 2, foot - 37 + index * 3)], 3)
        sketch.stamp(blade, rim=0.9, occlude=0.5)
        return sketch.result()
    # workbench and anything else
    bench = sketch.piece(ramp('#8a6a45'))
    bench.poly([(x - 22, foot - 24), (x + 22, foot - 24), (x + 22, foot - 17), (x - 22, foot - 17)], 3)
    for dx in (-19, 14):
        bench.poly([(x + dx, foot - 17), (x + dx + 5, foot - 17), (x + dx + 4, foot), (x + dx + 1, foot)], 2)
    sketch.stamp(bench, rim=0.85, occlude=0.65)
    grain = sketch.piece(ramp('#8a6a45'))
    grain.line([(x - 20, foot - 22), (x + 20, foot - 22)], 5, 1)
    grain.line([(x - 20, foot - 19), (x + 20, foot - 19)], 1, 1)
    grain.clip(bench)
    sketch.overlay(grain)
    vice = sketch.piece(ramp('#7d858d'))
    vice.rect((x + 12, foot - 30, x + 20, foot - 24), 3)
    sketch.stamp(vice, rim=0.85, occlude=0.5)
    tools = sketch.piece(ramp('#8d959c'))
    tools.poly(taper_shape((x - 14, foot - 26), (x - 4, foot - 34), 4.0, 3.0), 3)
    tools.rect((x - 7, foot - 38, x - 1, foot - 32), 3)
    sketch.stamp(tools, rim=0.9, occlude=0.5)
    return sketch.result()


# -------------------------------------------------------------- buildings --

STYLE_LOOK = {
    'cottage': dict(wall='#b9a684', roof='#8a5a45', trim='#7a5a3c', roof_kind='shingle'),
    'timber': dict(wall='#c3b291', roof='#6f5340', trim='#5f4632', roof_kind='shingle'),
    'limestone': dict(wall='#cbc3ab', roof='#7f8a8e', trim='#9a917c', roof_kind='tile'),
    'forge': dict(wall='#8f8b83', roof='#5f5a56', trim='#6a5f52', roof_kind='tile'),
    'northern': dict(wall='#8a7c63', roof='#5f6f4c', trim='#4f4436', roof_kind='turf'),
    'harbor': dict(wall='#9aa5a8', roof='#4f6a76', trim='#6a5f52', roof_kind='shingle'),
    'shrine': dict(wall='#c6c0ae', roof='#7a6a8c', trim='#a89a6a', roof_kind='peak'),
    'camp': dict(wall='#a08a64', roof='#7a6a4c', trim='#5f4a33', roof_kind='tent'),
    'ruin': dict(wall='#8e8a7e', roof='#6a6459', trim='#6f6a5f', roof_kind='none'),
}


def building(zone, definition):
    width = int(definition.get('width', 5)) * TILE
    height = (int(definition.get('height', 4)) + 2) * TILE
    style = definition.get('style', 'cottage')
    look = STYLE_LOOK.get(style, STYLE_LOOK['cottage'])
    r = _rng(zone.get('id', 'zone'), definition.get('id', 'building'))
    sketch = Sketch((width, height))
    wall_tone = ramp(look['wall'])
    roof_tone = ramp(look['roof'])
    trim_tone = ramp(look['trim'])
    base = height - 4
    roof_base = min(height * 0.46, 2.05 * TILE)
    wall_top = roof_base - 4

    if style == 'camp':
        return _camp(sketch, width, height, look, r)
    if style == 'ruin':
        return _ruin(sketch, width, height, look, r)
    if style == 'shrine':
        return _shrine(sketch, width, height, look, r)

    ground = sketch.piece(trim_tone)
    ground.ellipse((2, base - 6, width - 3, base + 4), 1)
    sketch.stamp(ground, outline=False, rim=0, occlude=0)

    walls = sketch.piece(wall_tone)
    walls.poly([(6, wall_top), (width - 7, wall_top), (width - 7, base), (6, base)], 3)
    sketch.stamp(walls, rim=0.9, occlude=0.7)
    texture = sketch.piece(wall_tone)
    if style in ('limestone', 'forge', 'harbor'):
        for row in range(int((base - wall_top) // 12) + 1):
            y = wall_top + 6 + row * 12
            texture.line([(7, y), (width - 8, y)], 1, 1)
            shift = 0 if row % 2 == 0 else 14
            for column in range(int(width // 28) + 1):
                bx = 8 + shift + column * 28
                if bx < width - 8:
                    texture.line([(bx, y), (bx, min(base - 1, y + 12))], 1, 1)
    else:
        for column in range(int(width // 34) + 1):
            bx = 12 + column * 34
            if bx < width - 12:
                texture.line([(bx, wall_top + 3), (bx, base - 2)], 1, 2)
        texture.line([(8, wall_top + (base - wall_top) * 0.45), (width - 9, wall_top + (base - wall_top) * 0.45)], 1, 2)
        for column in range(int(width // 34) + 1):
            bx = 12 + column * 34
            if bx + 34 < width - 12:
                texture.line([(bx, base - 2), (bx + 34, wall_top + (base - wall_top) * 0.45)], 1, 1)
    texture.clip(walls)
    sketch.overlay(texture)

    # door
    door_w = 26
    door_h = min(46, (base - wall_top) * 0.72)
    dx = width / 2
    frame = sketch.piece(trim_tone)
    frame.poly([(dx - door_w / 2 - 3, base), (dx - door_w / 2 - 3, base - door_h - 4),
                (dx + door_w / 2 + 3, base - door_h - 4), (dx + door_w / 2 + 3, base)], 3)
    sketch.stamp(frame, rim=0.8, occlude=0.6)
    door = sketch.piece(ramp('#6a4a30'))
    door.poly([(dx - door_w / 2, base), (dx - door_w / 2, base - door_h),
               (dx + door_w / 2, base - door_h), (dx + door_w / 2, base)], 3)
    door.line([(dx - door_w / 2 + 2, base - door_h + 3), (dx + door_w / 2 - 2, base - door_h + 3)], 1, 1)
    for plank in range(3):
        px = dx - door_w / 2 + 6 + plank * 7
        door.line([(px, base - door_h + 2), (px, base - 2)], 1, 1)
    sketch.stamp(door, rim=0.7, occlude=0.6)
    knob = sketch.piece(ramp('#c0a24a'))
    knob.disc(dx + door_w / 2 - 5, base - door_h * 0.5, 2.0, 4)
    sketch.stamp(knob, rim=0.9, occlude=0.4)

    # windows
    slots = max(1, int((width - 60) // 44))
    for index in range(slots):
        wx = 22 + index * ((width - 44) / max(1, slots)) + 10
        if abs(wx - dx) < door_w:
            continue
        wy = wall_top + (base - wall_top) * 0.34
        shutter = sketch.piece(trim_tone)
        shutter.rect((wx - 13, wy - 12, wx + 13, wy + 12), 3)
        sketch.stamp(shutter, rim=0.8, occlude=0.6)
        glass = sketch.piece(ramp('#e0c58a' if style != 'harbor' else '#9ec0c6'))
        glass.rect((wx - 10, wy - 9, wx + 10, wy + 9), 3)
        glass.line([(wx, wy - 9), (wx, wy + 9)], 1, 1)
        glass.line([(wx - 10, wy), (wx + 10, wy)], 1, 1)
        glass.poly([(wx - 9, wy + 8), (wx - 1, wy - 8), (wx + 2, wy - 8), (wx - 6, wy + 8)], 5)
        sketch.stamp(glass, rim=0.9, occlude=0.4)

    # roof
    overhang = 8
    roof = sketch.piece(roof_tone)
    ridge = 6
    roof.poly([(1, roof_base), (width - 2, roof_base),
               (width - 2 - overhang, ridge), (1 + overhang, ridge)], 3)
    sketch.stamp(roof, rim=0.9, occlude=0.65)
    shingles = sketch.piece(roof_tone)
    rows = int((roof_base - ridge) // 9) + 1
    for row in range(rows):
        y = ridge + 4 + row * 9
        inset = overhang * (1 - (y - ridge) / max(1, roof_base - ridge))
        shingles.line([(2 + inset, y), (width - 3 - inset, y)], 1, 1)
        if look['roof_kind'] == 'shingle':
            step = 14
            offset = 0 if row % 2 == 0 else 7
            for column in range(int(width // step) + 1):
                sx = 2 + inset + offset + column * step
                if sx < width - 3 - inset:
                    shingles.line([(sx, y), (sx, min(roof_base, y + 9))], 1, 1)
        elif look['roof_kind'] == 'tile':
            shingles.line([(2 + inset, y + 1), (width - 3 - inset, y + 1)], 4, 1)
    if look['roof_kind'] == 'turf':
        turf = sketch.piece(ramp('#5f7a45'))
        turf.poly([(1, roof_base), (width - 2, roof_base), (width - 2 - overhang, ridge),
                   (1 + overhang, ridge)], 3)
        turf.dither((0, ridge, width, int(roof_base)), 1, level=6)
        turf.clip(roof)
        sketch.overlay(turf)
    shingles.clip(roof)
    sketch.overlay(shingles)
    ridge_beam = sketch.piece(trim_tone)
    ridge_beam.poly([(overhang, ridge - 3), (width - overhang, ridge - 3),
                     (width - overhang, ridge + 2), (overhang, ridge + 2)], 3)
    sketch.stamp(ridge_beam, rim=0.9, occlude=0.5)
    eave = sketch.piece(trim_tone)
    eave.poly([(0, roof_base - 3), (width - 1, roof_base - 3), (width - 1, roof_base + 3), (0, roof_base + 3)], 3)
    sketch.stamp(eave, rim=0.8, occlude=0.6)

    if style == 'forge' or definition.get('station') == 'forge':
        chimney = sketch.piece(ramp('#6f6a62'))
        chimney.poly([(width * 0.74, ridge + 2), (width * 0.74 + 18, ridge + 2),
                      (width * 0.74 + 18, ridge - 22), (width * 0.74, ridge - 22)], 3)
        chimney.poly([(width * 0.74 - 3, ridge - 22), (width * 0.74 + 21, ridge - 22),
                      (width * 0.74 + 21, ridge - 27), (width * 0.74 - 3, ridge - 27)], 4)
        sketch.stamp(chimney, rim=0.9, occlude=0.6)
        smoke = sketch.piece(ramp('#a8a49c'))
        for index in range(3):
            smoke.disc(width * 0.74 + 9 + index * 3, ridge - 32 - index * 7, 4.0 + index, 2)
        smoke.image.putalpha(smoke.image.getchannel('A').point(lambda v: round(v * 0.55)))
        sketch.overlay(smoke)
    elif style in ('cottage', 'timber', 'northern'):
        chimney = sketch.piece(trim_tone)
        chimney.poly([(width * 0.20, ridge + 4), (width * 0.20 + 14, ridge + 4),
                      (width * 0.20 + 14, ridge - 14), (width * 0.20, ridge - 14)], 3)
        sketch.stamp(chimney, rim=0.85, occlude=0.6)

    sign = sketch.piece(trim_tone)
    sign.poly([(dx - 20, base - door_h - 12), (dx + 20, base - door_h - 12),
               (dx + 20, base - door_h - 6), (dx - 20, base - door_h - 6)], 3)
    sketch.stamp(sign, rim=0.9, occlude=0.5)
    return sketch.result()


def _camp(sketch, width, height, look, r):
    base = height - 4
    canvas_tone = ramp(look['wall'])
    pole_tone = ramp(look['trim'])
    ground = sketch.piece(pole_tone)
    ground.ellipse((6, base - 8, width - 7, base + 4), 1)
    sketch.stamp(ground, outline=False, rim=0, occlude=0)
    count = max(2, width // 90)
    for index in range(count):
        cx = (index + 0.5) * width / count
        peak = base - min(height * 0.62, 92)
        tent = sketch.piece(canvas_tone)
        span = min(48, width / count * 0.46)
        tent.poly([(cx - span, base), (cx, peak), (cx + span, base)], 3)
        sketch.stamp(tent, rim=0.9, occlude=0.65)
        seam = sketch.piece(canvas_tone)
        seam.line([(cx, peak + 2), (cx, base - 1)], 1, 1)
        seam.line([(cx - span * 0.5, base), (cx - span * 0.05, peak + 6)], 1, 1)
        seam.clip(tent)
        sketch.overlay(seam)
        flap = sketch.piece(ramp('#6a5238'))
        flap.poly([(cx - 9, base), (cx, base - 26), (cx + 9, base)], 3)
        sketch.stamp(flap, rim=0.7, occlude=0.6)
        pole = sketch.piece(pole_tone)
        pole.poly(taper_shape((cx, peak + 2), (cx, peak - 12), 3.0, 2.2), 3)
        sketch.stamp(pole, rim=0.8, occlude=0.5)
        flag = sketch.piece(ramp('#a8613c'))
        flag.poly([(cx + 1, peak - 12), (cx + 14, peak - 8), (cx + 1, peak - 4)], 3)
        sketch.stamp(flag, rim=0.85, occlude=0.5)
    fire = sketch.piece(ramp('#7c7a74'))
    fx = width / 2
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        fire.ellipse((fx + math.cos(rad) * 14 - 4, base - 4 + math.sin(rad) * 5 - 2,
                      fx + math.cos(rad) * 14 + 4, base - 4 + math.sin(rad) * 5 + 2), 3)
    sketch.stamp(fire, rim=0.8, occlude=0.6)
    flame = sketch.piece(ramp('#d4703c'))
    flame.poly(catmull([(fx - 7, base - 6), (fx - 3, base - 18), (fx + 1, base - 12),
                        (fx + 5, base - 22), (fx + 8, base - 6)], 5, closed=True), 3)
    sketch.stamp(flame, rim=0.9, occlude=0.4)
    sketch.glow('#e8894a', 4, 0.42)
    return sketch.result()


def _ruin(sketch, width, height, look, r):
    base = height - 4
    stone = ramp(look['wall'])
    ground = sketch.piece(ramp(look['trim']))
    ground.ellipse((4, base - 8, width - 5, base + 4), 1)
    sketch.stamp(ground, outline=False, rim=0, occlude=0)
    top = base - min(height * 0.5, 78)
    walls = sketch.piece(stone)
    profile = [(8, base)]
    steps = max(4, width // 40)
    for index in range(steps + 1):
        px = 8 + index * (width - 16) / steps
        broken = top + r.randrange(0, 34) + (18 if index % 2 else 0)
        profile.append((px, broken))
    profile.append((width - 8, base))
    walls.poly([(round(px), round(py)) for px, py in profile], 3)
    sketch.stamp(walls, rim=0.9, occlude=0.7)
    blocks = sketch.piece(stone)
    for row in range(int((base - top) // 13) + 1):
        y = top + 8 + row * 13
        blocks.line([(9, y), (width - 10, y)], 1, 1)
        shift = 0 if row % 2 == 0 else 16
        for column in range(int(width // 32) + 1):
            bx = 10 + shift + column * 32
            if bx < width - 10:
                blocks.line([(bx, y), (bx, y + 13)], 1, 1)
    blocks.clip(walls)
    sketch.overlay(blocks)
    arch = sketch.piece(ramp('#3a3630'))
    ax = width / 2
    arch.poly([(ax - 16, base), (ax - 16, base - 34), (ax + 16, base - 34), (ax + 16, base)], 3)
    arch.ellipse((ax - 16, base - 50, ax + 16, base - 18), 3)
    sketch.stamp(arch, rim=0.3, occlude=0.4)
    moss = sketch.piece(ramp('#5f7a45'))
    for _ in range(7):
        mx = r.randrange(12, max(13, width - 12))
        my = r.randrange(int(top) + 10, int(base))
        moss.ellipse((mx - 6, my - 3, mx + 6, my + 4), 3)
    moss.clip(walls)
    sketch.overlay(moss)
    rubble = sketch.piece(stone)
    for _ in range(6):
        rx = r.randrange(6, max(7, width - 6))
        rubble.poly(catmull([(rx - 7, base + 2), (rx - 4, base - 6), (rx + 5, base - 5),
                             (rx + 7, base + 2)], 4, closed=True), 2)
    sketch.stamp(rubble, rim=0.8, occlude=0.6)
    return sketch.result()


def _shrine(sketch, width, height, look, r):
    base = height - 4
    stone = ramp(look['wall'])
    trim = ramp(look['trim'])
    platform = sketch.piece(stone)
    for step in range(3):
        inset = step * 8
        platform.poly([(6 + inset, base - step * 7), (width - 7 - inset, base - step * 7),
                       (width - 7 - inset, base - step * 7 - 7), (6 + inset, base - step * 7 - 7)], 3)
    sketch.stamp(platform, rim=0.85, occlude=0.7)
    deck = base - 22
    columns = max(2, width // 60)
    for index in range(columns + 1):
        cx = 24 + index * (width - 48) / columns
        column = sketch.piece(stone)
        column.poly(taper_shape((cx, deck), (cx, deck - min(72, height * 0.42)), 15.0, 13.0), 3)
        sketch.stamp(column, rim=0.9, occlude=0.6)
        flute = sketch.piece(stone)
        flute.line([(cx - 3, deck - 4), (cx - 3, deck - min(70, height * 0.4))], 1, 1)
        flute.line([(cx + 3, deck - 4), (cx + 3, deck - min(70, height * 0.4))], 5, 1)
        flute.clip(column)
        sketch.overlay(flute)
        cap = sketch.piece(trim)
        cap.poly([(cx - 11, deck - min(72, height * 0.42)), (cx + 11, deck - min(72, height * 0.42)),
                  (cx + 11, deck - min(72, height * 0.42) - 6), (cx - 11, deck - min(72, height * 0.42) - 6)], 3)
        sketch.stamp(cap, rim=0.9, occlude=0.5)
    lintel_y = deck - min(72, height * 0.42) - 8
    lintel = sketch.piece(stone)
    lintel.poly([(10, lintel_y), (width - 11, lintel_y), (width - 11, lintel_y - 10), (10, lintel_y - 10)], 3)
    sketch.stamp(lintel, rim=0.9, occlude=0.6)
    roof = sketch.piece(ramp(look['roof']))
    roof.poly([(4, lintel_y - 10), (width - 5, lintel_y - 10), (width / 2, max(4, lintel_y - 44))], 3)
    sketch.stamp(roof, rim=0.9, occlude=0.6)
    emblem = sketch.piece(trim)
    ex, ey = width / 2, lintel_y - 24
    emblem.poly([(ex, ey - 9), (ex + 7, ey), (ex, ey + 9), (ex - 7, ey)], 3)
    emblem.disc(ex, ey, 3.2, 5)
    sketch.stamp(emblem, rim=0.9, occlude=0.5)
    altar = sketch.piece(trim)
    altar.poly([(width / 2 - 16, base - 24), (width / 2 + 16, base - 24),
                (width / 2 + 13, base - 40), (width / 2 - 13, base - 40)], 3)
    sketch.stamp(altar, rim=0.9, occlude=0.6)
    flame = sketch.piece(ramp('#e8cf5e'))
    flame.poly(catmull([(width / 2 - 5, base - 40), (width / 2 - 1, base - 52),
                        (width / 2 + 3, base - 46), (width / 2 + 5, base - 40)], 5, closed=True), 4)
    sketch.stamp(flame, outline=False, rim=0, occlude=0)
    sketch.glow('#f0dc9e', 4, 0.45)
    return sketch.result()
