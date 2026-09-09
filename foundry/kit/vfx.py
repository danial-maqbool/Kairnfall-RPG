"""Combat effects.

The art pack has an icon for every ability but nothing that happens on screen
when one is used. These are the moving parts: the burst where a hit lands, the
arc a blade cuts, the bolt in flight, the circle under a caster's feet, and the
aura that says a target is burning or frozen.

Every effect is a horizontal strip of frames — eight for a one-shot, eight for a
loop — so a client can play one by advancing a column, exactly like the actor
sheets. One-shots end on empty; loops are seamless.
"""
from __future__ import annotations

import math
import random

from forge import pigment
from forge.brush import Sketch, catmull, taper_shape
from forge.pigment import blend, keyed, ramp

FRAMES = 8
BURST = 64
BOLT = 32
AURA = 64

ELEMENTS = ('Physical', 'Fire', 'Frost', 'Lightning', 'Nature', 'Poison', 'Arcane',
            'Radiant', 'Shadow')


def _tone(element):
    return ramp(pigment.ELEMENTS.get(element, '#c6b9a4'))


def _rng(*parts):
    return random.Random(keyed('|'.join(str(p) for p in parts)))


def strip(draw_frame, size=BURST, frames=FRAMES):
    """One effect as a horizontal strip."""
    from PIL import Image
    sheet = Image.new('RGBA', (size * frames, size), (0, 0, 0, 0))
    for index in range(frames):
        image = draw_frame(index)
        if image.size != (size, size):
            raise ValueError('effect frame is %s, expected %d' % (image.size, size))
        sheet.alpha_composite(image, (index * size, 0))
    return sheet


# ------------------------------------------------------------------ bursts --

def impact(element, frame, size=BURST):
    """The flash where a blow or a spell lands: core, ring, shards, smoke."""
    tone = _tone(element)
    sketch = Sketch(size)
    centre = size / 2
    t = frame / (FRAMES - 1)
    if t > 0.98:
        return sketch.result()
    fade = max(0.0, 1.0 - t)
    rng = _rng('impact', element)

    ring = sketch.piece(tone)
    radius = 4 + t * (size * 0.42)
    thickness = max(1.0, 5.0 * (1 - t))
    ring.disc(centre, centre, radius, 4)
    ring.erase_ellipse((centre - radius + thickness, centre - radius + thickness,
                        centre + radius - thickness, centre + radius - thickness))
    sketch.stamp(ring, outline=False, rim=0, occlude=0)

    shards = sketch.piece(tone)
    count = 7 if element != 'Physical' else 5
    for index in range(count):
        angle = index * math.tau / count + rng.random() * 0.4
        inner = radius * 0.55
        outer = radius * (1.05 + rng.random() * 0.35)
        spread = 0.11 * (1 - t * 0.6)
        shards.poly([
            (centre + math.cos(angle) * outer, centre + math.sin(angle) * outer),
            (centre + math.cos(angle + spread) * inner, centre + math.sin(angle + spread) * inner),
            (centre + math.cos(angle - spread) * inner, centre + math.sin(angle - spread) * inner),
        ], 5 if t < 0.5 else 3)
    sketch.stamp(shards, outline=False, rim=0, occlude=0)

    if t < 0.55:
        core = sketch.piece(tone)
        core.disc(centre, centre, (size * 0.20) * (1 - t / 0.55), 5)
        sketch.stamp(core, outline=False, rim=0, occlude=0)
    sketch.fade(fade ** 0.6)
    sketch.glow(pigment.ELEMENTS.get(element, '#c6b9a4'), 3, 0.55 * fade)
    return sketch.result()


def slash(kind, frame, size=BURST):
    """A blade's arc. Reads as a cut because it thins toward both ends."""
    sketch = Sketch(size)
    t = frame / (FRAMES - 1)
    if t > 0.92:
        return sketch.result()
    tone = ramp('#f0ead6')
    centre = size / 2
    sweeps = {'light': (1, 0.62, 2.6), 'heavy': (1, 0.80, 4.4), 'cross': (2, 0.72, 3.4)}
    count, reach, width = sweeps.get(kind, sweeps['light'])
    for blade in range(count):
        # the arc travels around the target and narrows behind the edge, so the
        # eye reads a cut being made rather than a ring being inflated
        lead = -2.3 + t * 3.1 + blade * math.pi * 0.62
        piece = sketch.piece(tone)
        radius = size * reach * 0.5
        width = width * (1.25 - t * 0.7)
        points = []
        span = 1.75 - t * 1.05
        steps = 10
        for step in range(steps + 1):
            angle = lead - span + span * 2 * step / steps
            thickness = math.sin(step / steps * math.pi) ** 0.6
            points.append((centre + math.cos(angle) * (radius + thickness * width),
                           centre + math.sin(angle) * (radius + thickness * width)))
        for step in range(steps, -1, -1):
            angle = lead - span + span * 2 * step / steps
            thickness = math.sin(step / steps * math.pi) ** 0.6
            points.append((centre + math.cos(angle) * (radius - thickness * width),
                           centre + math.sin(angle) * (radius - thickness * width)))
        piece.poly(points, 4 if blade == 0 else 3)
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
    sketch.fade(max(0.0, 1.0 - t) ** 0.5)
    sketch.glow('#ffffff', 2, 0.30)
    return sketch.result()


# -------------------------------------------------------------- projectiles --

def bolt(element, frame, size=BOLT):
    """A projectile in flight, pointing along +x, looping over its frames."""
    tone = _tone(element)
    sketch = Sketch(size)
    cy = size / 2
    phase = frame / FRAMES * math.tau
    head = size * 0.70
    wobble = math.sin(phase) * 1.1

    trail = sketch.piece(tone)
    trail.poly(catmull([
        (head - 2, cy + wobble * 0.3), (head * 0.55, cy - 3.0 + wobble),
        (2.0, cy + wobble * 0.6), (head * 0.55, cy + 3.0 + wobble),
    ], 6, closed=True), 2)
    trail.image.putalpha(trail.image.getchannel('A').point(lambda v: round(v * 0.55)))
    sketch.overlay(trail)

    core = sketch.piece(tone)
    if element == 'Physical':
        core.poly(taper_shape((head - 13, cy + wobble * 0.4), (head, cy), 3.0, 1.4), 3)
        core.poly([(head + 4, cy), (head - 3, cy - 2.6), (head - 3, cy + 2.6)], 4)
        fletch = sketch.piece(ramp('#9aa27f'))
        fletch.poly([(head - 13, cy - 1.0), (head - 17, cy - 3.6), (head - 12, cy + 0.6)], 3)
        fletch.poly([(head - 13, cy + 1.0), (head - 17, cy + 3.6), (head - 12, cy - 0.6)], 3)
        sketch.stamp(fletch, rim=0.7, occlude=0.5)
    elif element == 'Lightning':
        core.poly([(head + 3, cy - 1), (head - 6, cy - 5 + wobble), (head - 4, cy - 1),
                   (head - 11, cy + 5 + wobble), (head - 6, cy + 1), (head - 1, cy + 1)], 4)
    elif element == 'Frost':
        for angle in range(0, 360, 60):
            rad = math.radians(angle + frame * 12)
            core.poly(taper_shape((head - 5, cy), (head - 5 + math.cos(rad) * 6,
                                                   cy + math.sin(rad) * 6), 3.0, 0.8), 4)
    else:
        core.disc(head - 5, cy + wobble * 0.3, 5.0 + math.sin(phase) * 0.6, 3)
        core.disc(head - 6, cy - 1 + wobble * 0.3, 2.4, 5)
    sketch.stamp(core, outline=element == 'Physical', rim=0.8, occlude=0.4)
    sketch.glow(pigment.ELEMENTS.get(element, '#c6b9a4'), 2, 0.5)
    return sketch.result()


# ------------------------------------------------------------- cast circles --

def cast_circle(element, frame, size=BURST):
    """A rune circle on the ground under a caster: rises, turns, sinks."""
    tone = _tone(element)
    sketch = Sketch(size)
    centre = size / 2
    ground = size * 0.72
    t = frame / (FRAMES - 1)
    swell = math.sin(min(1.0, t * 1.15) * math.pi) ** 0.55
    if swell <= 0.02:
        return sketch.result()
    radius = size * 0.40 * (0.5 + swell * 0.5)
    squash = 0.42

    ring = sketch.piece(tone)
    ring.ellipse((centre - radius, ground - radius * squash,
                  centre + radius, ground + radius * squash), 4)
    ring.erase_ellipse((centre - radius + 2, ground - radius * squash + 1.4,
                        centre + radius - 2, ground + radius * squash - 1.4))
    inner = radius * 0.62
    ring.ellipse((centre - inner, ground - inner * squash,
                  centre + inner, ground + inner * squash), 3)
    ring.erase_ellipse((centre - inner + 1.4, ground - inner * squash + 1.0,
                        centre + inner - 1.4, ground + inner * squash - 1.0))
    sketch.stamp(ring, outline=False, rim=0, occlude=0)

    glyphs = sketch.piece(tone)
    turn = frame * 0.22
    for index in range(6):
        angle = turn + index * math.tau / 6
        gx = centre + math.cos(angle) * radius * 0.81
        gy = ground + math.sin(angle) * radius * squash * 0.81
        glyphs.poly([(gx, gy - 2.2), (gx + 1.6, gy), (gx, gy + 2.2), (gx - 1.6, gy)], 5)
    sketch.stamp(glyphs, outline=False, rim=0, occlude=0)

    motes = sketch.piece(tone)
    for index in range(5):
        angle = -turn * 1.3 + index * math.tau / 5
        lift = (index / 5.0 + t) % 1.0
        mx = centre + math.cos(angle) * radius * 0.7
        my = ground + math.sin(angle) * radius * squash * 0.7 - lift * size * 0.35
        motes.disc(mx, my, max(0.8, 1.8 * (1 - lift)), 5)
    sketch.stamp(motes, outline=False, rim=0, occlude=0)
    sketch.fade(min(1.0, swell * 1.4))
    sketch.glow(pigment.ELEMENTS.get(element, '#c6b9a4'), 3, 0.5 * swell)
    return sketch.result()


# ------------------------------------------------------------------- auras --

AURAS = {
    'burning': ('Fire', 'flame'), 'frozen': ('Frost', 'crystal'), 'poisoned': ('Poison', 'bubble'),
    'shocked': ('Lightning', 'spark'), 'blessed': ('Radiant', 'halo'), 'cursed': ('Shadow', 'wisp'),
    'shielded': ('Arcane', 'shell'), 'hastened': ('Nature', 'streak'),
}


def aura(name, frame, size=AURA):
    """A looping status overlay drawn on top of whatever is afflicted."""
    element, motif = AURAS.get(name, ('Arcane', 'wisp'))
    tone = _tone(element)
    sketch = Sketch(size)
    centre = size / 2
    phase = frame / FRAMES * math.tau
    rng = _rng('aura', name)

    piece = sketch.piece(tone)
    if motif == 'flame':
        for index in range(5):
            offset = index / 5.0
            rise = ((offset + frame / FRAMES) % 1.0)
            fx = centre + math.sin((offset + rise) * math.tau) * size * 0.20
            fy = size * 0.86 - rise * size * 0.62
            scale = (1.0 - rise) * 3.4 + 0.8
            piece.poly(catmull([(fx - scale, fy + scale), (fx - scale * 0.6, fy - scale * 0.4),
                                (fx, fy - scale * 2.0), (fx + scale * 0.7, fy - scale * 0.3),
                                (fx + scale, fy + scale)], 5, closed=True), 4)
    elif motif == 'crystal':
        for index in range(6):
            angle = index * math.tau / 6 + phase * 0.15
            cx = centre + math.cos(angle) * size * 0.28
            cy = centre + math.sin(angle) * size * 0.24
            grow = 2.2 + math.sin(phase + index) * 0.8
            piece.poly([(cx, cy - grow * 1.7), (cx + grow, cy), (cx, cy + grow * 1.7),
                        (cx - grow, cy)], 4)
    elif motif == 'bubble':
        for index in range(6):
            offset = (index / 6.0 + frame / FRAMES) % 1.0
            bx = centre + math.cos(index * 2.3) * size * 0.24
            by = size * 0.82 - offset * size * 0.56
            piece.disc(bx, by, max(0.9, 2.6 * (1 - offset * 0.6)), 4)
    elif motif == 'spark':
        for index in range(4):
            angle = phase * 1.6 + index * math.tau / 4
            sx = centre + math.cos(angle) * size * 0.30
            sy = centre + math.sin(angle) * size * 0.26
            piece.poly([(sx, sy - 4), (sx + 1.6, sy - 0.6), (sx + 0.6, sy - 0.6),
                        (sx + 2.2, sy + 4), (sx - 1.4, sy + 0.4), (sx - 0.2, sy + 0.4)], 5)
    elif motif == 'halo':
        radius = size * 0.26 + math.sin(phase) * 1.2
        piece.ellipse((centre - radius, size * 0.20 - radius * 0.32,
                       centre + radius, size * 0.20 + radius * 0.32), 5)
        piece.erase_ellipse((centre - radius + 2.0, size * 0.20 - radius * 0.32 + 1.4,
                             centre + radius - 2.0, size * 0.20 + radius * 0.32 - 1.4))
        for index in range(5):
            angle = -phase + index * math.tau / 5
            piece.disc(centre + math.cos(angle) * size * 0.22,
                       size * 0.34 + math.sin(angle) * size * 0.06, 1.3, 5)
    elif motif == 'shell':
        # a ward that breathes and turns, not a decal
        radius = size * 0.32 + math.sin(phase) * 2.2
        piece.ellipse((centre - radius * 0.86, centre - radius,
                       centre + radius * 0.86, centre + radius), 4)
        piece.erase_ellipse((centre - radius * 0.86 + 2, centre - radius + 2,
                             centre + radius * 0.86 - 2, centre + radius - 2))
        for index in range(8):
            angle = phase * 0.9 + index * math.tau / 8
            plate = 5 if (index + frame) % 2 == 0 else 3
            piece.poly([(centre + math.cos(angle) * radius * 0.80,
                         centre + math.sin(angle) * radius * 0.92),
                        (centre + math.cos(angle + 0.30) * radius * 0.90,
                         centre + math.sin(angle + 0.30) * radius * 1.02),
                        (centre + math.cos(angle - 0.30) * radius * 0.90,
                         centre + math.sin(angle - 0.30) * radius * 1.02)], plate)
    else:  # wisp and streak
        for index in range(5):
            offset = (index / 5.0 + frame / FRAMES) % 1.0
            angle = index * 1.9 + phase * 0.4
            wx = centre + math.cos(angle) * size * (0.16 + offset * 0.18)
            wy = centre + math.sin(angle) * size * 0.20 - (offset - 0.5) * size * 0.30
            if motif == 'streak':
                piece.poly(taper_shape((wx - 4, wy), (wx + 4, wy - 1), 2.6, 0.8), 4)
            else:
                piece.disc(wx, wy, max(0.9, 2.4 * (1 - abs(offset - 0.5) * 1.4)), 4)
    piece.image.putalpha(piece.image.getchannel('A').point(lambda v: round(v * 0.85)))
    sketch.overlay(piece)
    sketch.glow(pigment.ELEMENTS.get(element, '#c6b9a4'), 3, 0.5)
    return sketch.result()


# ---------------------------------------------------------------- one-offs --

def flourish(name, frame, size=BURST):
    """Short one-shots that are not tied to an element."""
    sketch = Sketch(size)
    t = frame / (FRAMES - 1)
    centre = size / 2
    rng = _rng('flourish', name)
    if name == 'level_up':
        if t > 0.95:
            return sketch.result()
        tone = ramp('#f0dc9e')
        piece = sketch.piece(tone)
        for index in range(8):
            angle = index * math.tau / 8 - math.pi / 2
            reach = size * 0.12 + t * size * 0.36
            piece.poly(taper_shape((centre, size * 0.86 - t * size * 0.3),
                                   (centre + math.cos(angle) * reach,
                                    size * 0.86 - t * size * 0.3 + math.sin(angle) * reach * 0.7),
                                   4.0, 1.0), 4)
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
        ring = sketch.piece(tone)
        radius = 6 + t * size * 0.42
        ring.ellipse((centre - radius, size * 0.80 - radius * 0.3,
                      centre + radius, size * 0.80 + radius * 0.3), 5)
        ring.erase_ellipse((centre - radius + 2.4, size * 0.80 - radius * 0.3 + 1.6,
                            centre + radius - 2.4, size * 0.80 + radius * 0.3 - 1.6))
        sketch.stamp(ring, outline=False, rim=0, occlude=0)
        sketch.fade((1 - t) ** 0.5)
        sketch.glow('#ffe9a8', 4, 0.6)
    elif name == 'heal':
        if t > 0.95:
            return sketch.result()
        tone = ramp('#8fd6a0')
        piece = sketch.piece(tone)
        for index in range(5):
            offset = (index / 5.0 + t) % 1.0
            mx = centre + math.sin(index * 2.1 + offset * 3.0) * size * 0.20
            my = size * 0.82 - offset * size * 0.66
            grow = max(1.6, 4.4 * (1 - offset * 0.7))
            piece.poly([(mx - grow * 0.42, my - grow), (mx + grow * 0.42, my - grow),
                        (mx + grow * 0.42, my - grow * 0.42), (mx + grow, my - grow * 0.42),
                        (mx + grow, my + grow * 0.42), (mx + grow * 0.42, my + grow * 0.42),
                        (mx + grow * 0.42, my + grow), (mx - grow * 0.42, my + grow),
                        (mx - grow * 0.42, my + grow * 0.42), (mx - grow, my + grow * 0.42),
                        (mx - grow, my - grow * 0.42), (mx - grow * 0.42, my - grow * 0.42)], 4)
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
        sketch.fade((1 - t * 0.7) ** 0.6)
        sketch.glow('#9fe0b0', 3, 0.5)
    elif name == 'death_poof':
        if t > 0.95:
            return sketch.result()
        tone = ramp('#8a8496')
        piece = sketch.piece(tone)
        for index in range(7):
            angle = index * math.tau / 7 + rng.random()
            reach = t * size * 0.32
            px = centre + math.cos(angle) * reach
            py = size * 0.70 + math.sin(angle) * reach * 0.6 - t * size * 0.12
            piece.disc(px, py, max(1.0, 6.0 * (1 - t) * (0.6 + rng.random() * 0.6)), 3)
        piece.image.putalpha(piece.image.getchannel('A').point(lambda v: round(v * 0.75)))
        sketch.overlay(piece)
        sketch.fade((1 - t) ** 0.7)
    elif name == 'gather':
        if t > 0.95:
            return sketch.result()
        tone = ramp('#c9b98a')
        piece = sketch.piece(tone)
        for index in range(6):
            angle = index * math.tau / 6 + rng.random() * 0.5
            reach = t * size * 0.26
            piece.disc(centre + math.cos(angle) * reach,
                       size * 0.74 + math.sin(angle) * reach * 0.5 - t * size * 0.16,
                       max(0.9, 3.4 * (1 - t)), 3)
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
        sketch.fade((1 - t) ** 0.6)
    elif name == 'block':
        if t > 0.85:
            return sketch.result()
        tone = ramp('#cfe0ea')
        piece = sketch.piece(tone)
        radius = size * 0.30 * (1 + t * 0.5)
        piece.ellipse((centre - radius * 0.8, centre - radius, centre + radius * 0.8, centre + radius), 5)
        piece.erase_ellipse((centre - radius * 0.8 + 3, centre - radius + 3,
                             centre + radius * 0.8 - 3, centre + radius - 3))
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
        sketch.fade((1 - t / 0.85) ** 0.5)
        sketch.glow('#dff0ff', 3, 0.5)
    else:  # crit
        if t > 0.9:
            return sketch.result()
        tone = ramp('#f0c060')
        piece = sketch.piece(tone)
        points = []
        radius = size * 0.16 + t * size * 0.22
        for index in range(10):
            angle = index * math.pi / 5 - math.pi / 2
            reach = radius if index % 2 == 0 else radius * 0.42
            points.append((centre + math.cos(angle) * reach, centre + math.sin(angle) * reach))
        piece.poly(points, 4)
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
        sketch.fade((1 - t) ** 0.5)
        sketch.glow('#ffd070', 3, 0.6)
    return sketch.result()


FLOURISHES = ('level_up', 'heal', 'death_poof', 'gather', 'block', 'crit')
SLASHES = ('light', 'heavy', 'cross')


def plan():
    """Every effect this module owns, as (key, size, maker) tuples."""
    out = []
    for element in ELEMENTS:
        out.append(('vfx/impact_' + element.lower(), BURST,
                    lambda f, e=element: impact(e, f)))
        out.append(('vfx/bolt_' + element.lower(), BOLT,
                    lambda f, e=element: bolt(e, f, BOLT)))
        out.append(('vfx/cast_' + element.lower(), BURST,
                    lambda f, e=element: cast_circle(e, f)))
    for kind in SLASHES:
        out.append(('vfx/slash_' + kind, BURST, lambda f, k=kind: slash(k, f)))
    for name in AURAS:
        out.append(('vfx/aura_' + name, AURA, lambda f, n=name: aura(n, f)))
    for name in FLOURISHES:
        out.append(('vfx/' + name, BURST, lambda f, n=name: flourish(n, f)))
    return out
