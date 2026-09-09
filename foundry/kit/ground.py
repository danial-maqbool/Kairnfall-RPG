"""Terrain transitions.

A field of 32px tiles laid edge to edge reads as a checkerboard, because every
boundary is a straight line on the grid. These are the pieces that hide the
grid: overlays that let one terrain spill over another with a ragged edge, the
inner corners that fill the gaps a four-bit mask leaves behind, shoreline foam,
cliff faces and a road set.

An overlay is drawn *on top of* whatever base tile is already there, so one set
per terrain covers every pairing instead of needing a tile per combination.

Mask bits say where the terrain continues:

    1 = north   2 = east   4 = south   8 = west

so mask 15 is solid ground and mask 0 is an isolated patch.
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from forge import lands, pigment
from forge.brush import Sketch, catmull
from forge.pigment import blend, keyed, ramp

TILE = 32
NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
SIDES = ((NORTH, 'north'), (EAST, 'east'), (SOUTH, 'south'), (WEST, 'west'))
CORNERS = ('ne', 'se', 'sw', 'nw')

# how far a terrain bites into its neighbour, and how ragged the bite is
BITE = {
    'grass': (6.0, 2.6), 'moss': (6.5, 2.8), 'marsh': (6.0, 2.4), 'dirt': (5.0, 2.2),
    'sand': (7.0, 3.0), 'snow': (6.5, 2.8), 'ash': (5.5, 2.6), 'stone': (3.5, 1.2),
    'wall': (2.5, 0.8), 'wood': (2.5, 0.8), 'water': (5.5, 2.2), 'lava': (5.0, 2.4),
    'crystal': (4.0, 1.8),
}


def _rng(*parts):
    return random.Random(keyed('|'.join(str(p) for p in parts)))


def _edge_points(side, depth, jitter, rng, steps=8):
    """A ragged line across one side of the tile, `depth` pixels in."""
    points = []
    for step in range(steps + 1):
        along = step / steps * TILE
        cut = depth + (rng.random() - 0.5) * jitter * 2
        cut = max(0.5, cut)
        if side == 'north':
            points.append((along, cut))
        elif side == 'south':
            points.append((along, TILE - cut))
        elif side == 'west':
            points.append((cut, along))
        else:
            points.append((TILE - cut, along))
    return points


def coverage(kind, mask, variant=0):
    """The alpha shape this terrain occupies for a given neighbour mask."""
    depth, jitter = BITE.get(kind, (5.0, 2.2))
    rng = _rng('coverage', kind, mask, variant)
    depth *= (0.72, 0.95, 1.18, 1.05)[variant % 4]
    jitter *= (1.25, 0.85, 1.1, 0.95)[variant % 4]
    shape = Image.new('L', (TILE, TILE), 0)
    draw = ImageDraw.Draw(shape)
    if mask == 15:
        draw.rectangle((0, 0, TILE - 1, TILE - 1), fill=255)
        return shape
    # start from the full tile and carve back the sides that have no neighbour
    draw.rectangle((0, 0, TILE - 1, TILE - 1), fill=255)
    for bit, side in SIDES:
        if mask & bit:
            continue
        line = _edge_points(side, depth, jitter, rng)
        if side == 'north':
            polygon = [(0, -1)] + line + [(TILE, -1)]
        elif side == 'south':
            polygon = [(0, TILE)] + line + [(TILE, TILE)]
        elif side == 'west':
            polygon = [(-1, 0)] + line + [(-1, TILE)]
        else:
            polygon = [(TILE, 0)] + line + [(TILE, TILE)]
        draw.polygon([(round(x), round(y)) for x, y in catmull(polygon, 3)], fill=0)
    if mask == 0:
        # an isolated patch is a blob, not a square with its corners shaved
        shape = Image.new('L', (TILE, TILE), 0)
        draw = ImageDraw.Draw(shape)
        blob = []
        for step in range(12):
            angle = step * math.tau / 12
            reach = (TILE / 2 - depth) * (0.85 + rng.random() * 0.3)
            blob.append((TILE / 2 + math.cos(angle) * reach,
                         TILE / 2 + math.sin(angle) * reach))
        draw.polygon([(round(x), round(y)) for x, y in catmull(blob, 4, closed=True)], fill=255)
    return shape


def inner_corner(kind, corner, variant=0):
    """The notch left where two sides meet but the diagonal does not."""
    depth, jitter = BITE.get(kind, (5.0, 2.2))
    rng = _rng('corner', kind, corner, variant)
    shape = Image.new('L', (TILE, TILE), 255)
    draw = ImageDraw.Draw(shape)
    reach = depth * 1.25
    origin = {'ne': (TILE, 0), 'se': (TILE, TILE), 'sw': (0, TILE), 'nw': (0, 0)}[corner]
    arc = []
    for step in range(7):
        angle = step / 6 * math.pi / 2
        dx = math.cos(angle) * reach * (0.85 + rng.random() * 0.3)
        dy = math.sin(angle) * reach * (0.85 + rng.random() * 0.3)
        arc.append((origin[0] + (-dx if origin[0] else dx),
                    origin[1] + (-dy if origin[1] else dy)))
    draw.polygon([(round(x), round(y)) for x, y in [origin] + arc], fill=0)
    return shape


def _lip(shape, tone, sketch):
    """A lighter rim just inside the exposed edge, so the overlap has a lip."""
    hard = shape.point(lambda v: 255 if v >= 128 else 0)
    inner = hard.filter(ImageFilter.MinFilter(3))
    band = ImageChops.subtract(hard, inner)
    lip = Sketch((TILE, TILE)).piece(tone)
    lip.image.paste(pigment.rgb(tone[5]), (0, 0), band)
    lip.image.putalpha(ImageChops.darker(lip.image.getchannel('A'),
                                         band.point(lambda v: round(v * 0.55))))
    sketch.overlay(lip)
    shade = Sketch((TILE, TILE)).piece(tone)
    outer = ImageChops.subtract(_grow(hard), hard)
    shade.image.paste(pigment.rgb(tone.line), (0, 0), outer)
    shade.image.putalpha(ImageChops.darker(shade.image.getchannel('A'),
                                           outer.point(lambda v: round(v * 0.42))))
    sketch.under(shade)


def _grow(mask):
    grown = mask
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        moved = Image.new('L', mask.size, 0)
        moved.paste(mask, (dx, dy))
        grown = ImageChops.lighter(grown, moved)
    return grown


def overlay(kind, mask, variant=0):
    """One terrain's material, cut to a neighbour mask, ready to lay on top."""
    base = lands.tile(kind, variant)
    shape = coverage(kind, mask, variant)
    sketch = Sketch((TILE, TILE))
    body = sketch.piece(ramp(lands.TERRAIN.get(kind, '#6a6a6a')))
    body.image.paste(base, (0, 0))
    body.image.putalpha(ImageChops.darker(body.image.getchannel('A'), shape))
    sketch.overlay(body)
    _lip(shape, ramp(lands.TERRAIN.get(kind, '#6a6a6a')), sketch)
    return sketch.result()


def corner_overlay(kind, corner, variant=0):
    base = lands.tile(kind, variant)
    shape = inner_corner(kind, corner, variant)
    sketch = Sketch((TILE, TILE))
    body = sketch.piece(ramp(lands.TERRAIN.get(kind, '#6a6a6a')))
    body.image.paste(base, (0, 0))
    body.image.putalpha(ImageChops.darker(body.image.getchannel('A'), shape))
    sketch.overlay(body)
    _lip(shape, ramp(lands.TERRAIN.get(kind, '#6a6a6a')), sketch)
    return sketch.result()


# ------------------------------------------------------------------ water --

def foam(mask, frame=0, variant=0):
    """Surf along a water tile's own ragged edge.

    Drawn from the same coverage shape as the water overlay and with the same
    seed, so the foam follows the shoreline exactly instead of ruling a straight
    white line across the tile.
    """
    sketch = Sketch((TILE, TILE))
    if mask == 15:
        return sketch.result()
    shape = coverage('water', mask, variant).point(lambda v: 255 if v >= 128 else 0)
    if shape.getbbox() is None:
        return sketch.result()
    rng = _rng('foam', mask, variant, frame)
    swell = 1 + frame % 3

    outer = ImageChops.subtract(_grow(shape), shape)
    for _ in range(swell - 1):
        outer = ImageChops.lighter(outer, ImageChops.subtract(_grow(_grow(shape)), _grow(shape)))
    crest = Sketch((TILE, TILE)).piece(ramp('#eaf2f6'))
    crest.image.paste(pigment.rgb('#eaf2f6'), (0, 0), outer)
    crest.image.putalpha(ImageChops.darker(crest.image.getchannel('A'),
                                           outer.point(lambda v: round(v * 0.62))))
    sketch.overlay(crest)

    inner = ImageChops.subtract(shape, shape.filter(ImageFilter.MinFilter(3)))
    wash = Sketch((TILE, TILE)).piece(ramp('#cfe4ee'))
    wash.image.paste(pigment.rgb('#cfe4ee'), (0, 0), inner)
    wash.image.putalpha(ImageChops.darker(wash.image.getchannel('A'),
                                          inner.point(lambda v: round(v * 0.45))))
    sketch.overlay(wash)

    bubbles = Sketch((TILE, TILE)).piece(ramp('#f2f8fa'))
    edge = outer.load()
    spots = [(x, y) for y in range(TILE) for x in range(TILE) if edge[x, y] > 0]
    rng.shuffle(spots)
    for x, y in spots[:4]:
        bubbles.dot(x, y, 5)
    sketch.overlay(bubbles)
    return sketch.result()


# ------------------------------------------------------------------ cliffs --

CLIFF_PIECES = ('face', 'top', 'left', 'right', 'corner_left', 'corner_right',
                'inner_left', 'inner_right')


def cliff(piece_name, variant=0):
    """A rock wall so height changes are not a flat colour step."""
    stone = ramp('#7a7770')
    sketch = Sketch((TILE, TILE))
    rng = _rng('cliff', piece_name, variant)
    body = sketch.piece(stone)
    if piece_name == 'top':
        body.rect((0, 0, TILE - 1, 11), 3)
        body.poly(catmull([(0, 11), (8, 13), (16, 10), (24, 13), (TILE, 11),
                           (TILE, 0), (0, 0)], 4, closed=True), 3)
    elif piece_name in ('left', 'right'):
        edge = 0 if piece_name == 'left' else TILE - 1
        inner = 9 if piece_name == 'left' else TILE - 10
        body.poly([(edge, 0), (inner, 0), (inner + (2 if piece_name == 'left' else -2), TILE),
                   (edge, TILE)], 3)
    elif piece_name.startswith('corner'):
        left = piece_name.endswith('left')
        body.rect((0, 0, TILE - 1, 11), 3)
        if left:
            body.poly([(0, 11), (10, 11), (12, TILE), (0, TILE)], 3)
        else:
            body.poly([(TILE, 11), (TILE - 10, 11), (TILE - 12, TILE), (TILE, TILE)], 3)
    elif piece_name.startswith('inner'):
        left = piece_name.endswith('left')
        if left:
            body.poly([(0, 0), (11, 0), (13, TILE), (0, TILE)], 3)
        else:
            body.poly([(TILE, 0), (TILE - 11, 0), (TILE - 13, TILE), (TILE, TILE)], 3)
    else:  # face
        body.rect((0, 0, TILE - 1, TILE - 1), 3)
    sketch.stamp(body, outline=False, rim=0, occlude=0)

    strata = sketch.piece(stone)
    for row in range(4):
        y = 3 + row * 8 + rng.randrange(-1, 2)
        strata.line(catmull([(0, y), (10, y + 1.6), (20, y - 1.2), (TILE, y + 0.8)], 4),
                    1 if row % 2 else 2, 1)
        strata.line(catmull([(0, y + 1), (10, y + 2.6), (20, y - 0.2), (TILE, y + 1.8)], 4), 4, 1)
    for _ in range(6):
        strata.dot(rng.randrange(1, TILE - 1), rng.randrange(1, TILE - 1), 1)
    strata.clip(body)
    sketch.overlay(strata)
    if piece_name in ('top', 'corner_left', 'corner_right'):
        cap = sketch.piece(ramp('#5f7a45'))
        cap.poly(catmull([(0, 0), (8, 2), (16, 0), (24, 3), (TILE, 1),
                          (TILE, 6), (0, 6)], 4, closed=True), 3)
        cap.clip(body)
        sketch.overlay(cap)
    return sketch.result()


# ------------------------------------------------------------------- roads --

def road(mask, variant=0):
    """A worn path overlay; the mask says which sides the road continues on."""
    sketch = Sketch((TILE, TILE))
    tone = ramp('#8a7a5e')
    rng = _rng('road', mask, variant)
    half = TILE / 2
    width = 11.0
    piece = sketch.piece(tone)
    if mask == 0:
        piece.ellipse((half - width * 0.7, half - width * 0.7,
                       half + width * 0.7, half + width * 0.7), 3)
    else:
        piece.ellipse((half - width * 0.62, half - width * 0.62,
                       half + width * 0.62, half + width * 0.62), 3)
        for bit, side in SIDES:
            if not mask & bit:
                continue
            wobble = (rng.random() - 0.5) * 2.0
            if side == 'north':
                piece.poly([(half - width / 2 + wobble, -1), (half + width / 2 + wobble, -1),
                            (half + width / 2, half), (half - width / 2, half)], 3)
            elif side == 'south':
                piece.poly([(half - width / 2 + wobble, TILE + 1), (half + width / 2 + wobble, TILE + 1),
                            (half + width / 2, half), (half - width / 2, half)], 3)
            elif side == 'west':
                piece.poly([(-1, half - width / 2 + wobble), (-1, half + width / 2 + wobble),
                            (half, half + width / 2), (half, half - width / 2)], 3)
            else:
                piece.poly([(TILE + 1, half - width / 2 + wobble), (TILE + 1, half + width / 2 + wobble),
                            (half, half + width / 2), (half, half - width / 2)], 3)
    sketch.stamp(piece, outline=False, rim=0, occlude=0)
    grit = sketch.piece(tone)
    for _ in range(16):
        grit.dot(rng.randrange(0, TILE), rng.randrange(0, TILE), 1 if rng.random() < 0.6 else 4)
    for _ in range(4):
        gx, gy = rng.randrange(2, TILE - 3), rng.randrange(2, TILE - 3)
        grit.ellipse((gx, gy, gx + 2, gy + 1), 2)
    grit.clip(piece)
    sketch.overlay(grit)
    _lip(piece.image.getchannel('A'), tone, sketch)
    return sketch.result()


def plan():
    """Every transition piece, as (key, maker) pairs."""
    out = []
    for kind in lands.TERRAIN:
        for mask in range(16):
            out.append(('ground/%s_edge_%02d' % (kind, mask),
                        lambda k=kind, m=mask: overlay(k, m)))
        for corner in CORNERS:
            out.append(('ground/%s_corner_%s' % (kind, corner),
                        lambda k=kind, c=corner: corner_overlay(k, c)))
    for mask in range(15):        # 15 is open water with no shore to break on
        for frame in range(3):
            out.append(('ground/foam_%02d_%d' % (mask, frame),
                        lambda m=mask, f=frame: foam(m, f)))
    for piece_name in CLIFF_PIECES:
        out.append(('ground/cliff_' + piece_name, lambda n=piece_name: cliff(n)))
    for mask in range(16):
        out.append(('ground/road_%02d' % mask, lambda m=mask: road(m)))
    return out
