"""Bust portraits.

A 64px world sprite has an eleven pixel head, which is not enough face for a
dialogue box or a character sheet. These are drawn at portrait scale instead —
the same person, but with a head worth looking at.

Player portraits are layered exactly like the world sprites: a base per build
and skin tone, a hair overlay per style and colour. Townsfolk and bosses are
composed pieces, since they never need to be recombined.
"""
from __future__ import annotations

import math

from forge import beasts, folk, pigment
from forge.brush import Sketch, catmull, taper_shape
from forge.pigment import blend, keyed, ramp

SIZE = 64
CENTRE = SIZE / 2
HEAD_Y = 27.0
HEAD_R = 15.0
SHOULDER_Y = 55.0

BUILDS = 2
SKINS = 6
HAIR_STYLES = 6
HAIR_COLOURS = 8


def _frame(sketch, tone='#3a3630'):
    """A vignette so a portrait reads as a portrait and not a floating head."""
    back = Sketch((SIZE, SIZE)).piece(ramp(tone))
    back.disc(CENTRE, CENTRE + 2, SIZE * 0.52, 2)
    back.image.putalpha(back.image.getchannel('A').point(lambda v: round(v * 0.72)))
    sketch.under(back)
    return sketch


def _shoulders(sketch, cloth, build):
    width = 25.0 + build * -2.0
    piece = sketch.piece(ramp(cloth))
    piece.poly(catmull([
        (CENTRE - width, SIZE + 4), (CENTRE - width * 0.86, SHOULDER_Y - 2),
        (CENTRE - width * 0.34, SHOULDER_Y - 8), (CENTRE, SHOULDER_Y - 9),
        (CENTRE + width * 0.34, SHOULDER_Y - 8), (CENTRE + width * 0.86, SHOULDER_Y - 2),
        (CENTRE + width, SIZE + 4),
    ], 6, closed=True), 3)
    sketch.carve(piece, rim=0.9, occlude=0.8, form=0.5, gleam=0.15)
    collar = sketch.piece(ramp(blend(pigment.rgb(cloth), (30, 26, 32, 255), 0.35)))
    collar.poly(catmull([(CENTRE - 9, SHOULDER_Y - 7), (CENTRE, SHOULDER_Y + 1),
                         (CENTRE + 9, SHOULDER_Y - 7), (CENTRE, SHOULDER_Y - 4)],
                        5, closed=True), 3)
    sketch.carve(collar, rim=0.85, occlude=0.7, form=0.0, gleam=0.0)


def _head(sketch, skin_hex, build, face=True):
    skin = ramp(skin_hex)
    radius = HEAD_R - build * 0.8
    neck = sketch.piece(skin)
    neck.poly(taper_shape((CENTRE, HEAD_Y + radius * 0.5), (CENTRE, SHOULDER_Y - 2),
                          radius * 0.72, radius * 0.86), 2)
    sketch.carve(neck, rim=0.5, occlude=0.85, form=0.3, gleam=0.0)

    piece = sketch.piece(skin)
    skull = [(CENTRE + math.cos(a * math.tau / 24) * radius * (1.0 - 0.05 * math.sin(a * 0.7)),
              HEAD_Y + math.sin(a * math.tau / 24) * radius * 1.06) for a in range(24)]
    piece.poly(skull, 3)
    jaw = (CENTRE, HEAD_Y + radius * 0.60)
    piece.poly(catmull([(jaw[0] - radius * 0.72, jaw[1] - radius * 0.30),
                        (jaw[0] + radius * 0.72, jaw[1] - radius * 0.30),
                        (jaw[0] + radius * 0.46, jaw[1] + radius * 0.52),
                        (jaw[0], jaw[1] + radius * 0.66),
                        (jaw[0] - radius * 0.46, jaw[1] + radius * 0.52)], 5, closed=True), 3)
    for sign in (-1, 1):
        piece.ellipse((CENTRE + sign * radius * 0.92 - 2.2, HEAD_Y - 1.0,
                       CENTRE + sign * radius * 0.92 + 2.2, HEAD_Y + 4.4), 2)
    sketch.carve(piece, rim=0.95, occlude=0.7, form=0.55, gleam=0.18)
    if not face:
        return radius

    detail = sketch.piece(skin)
    eye_y = HEAD_Y + 0.5
    for sign in (-1, 1):
        ex = CENTRE + sign * radius * 0.38
        detail.ellipse((ex - 3.2, eye_y - 2.0, ex + 3.2, eye_y + 2.0), (240, 236, 224, 255))
        detail.disc(ex + sign * 0.3, eye_y + 0.2, 2.0, (86, 72, 58, 255))
        detail.disc(ex + sign * 0.3, eye_y + 0.2, 1.0, (34, 28, 34, 255))
        detail.dot(ex + sign * 0.3 - 0.8, eye_y - 0.8, (250, 248, 240, 255))
        detail.line([(ex - 3.6, eye_y - 4.2), (ex + 3.4, eye_y - 4.6)], 1, 1)
    detail.poly([(CENTRE - 1.6, eye_y + 4.6), (CENTRE + 1.8, eye_y + 4.6),
                 (CENTRE + 0.6, eye_y + 1.0)], 2)
    detail.line([(CENTRE - 2.6, eye_y + 7.6), (CENTRE + 2.6, eye_y + 7.6)], 1, 1)
    detail.line([(CENTRE - 1.6, eye_y + 8.4), (CENTRE + 1.6, eye_y + 8.4)], 2, 1)
    sketch.overlay(detail)
    return radius


def base(build, skin):
    """Player portrait base: shoulders, neck, head, face. Hair goes on top."""
    sketch = Sketch((SIZE, SIZE))
    _shoulders(sketch, folk.CLOTH_UNDER, build)
    _head(sketch, pigment.SKIN[max(0, min(SKINS - 1, skin))], build)
    _frame(sketch)
    return sketch.result()


def hair(style, colour):
    """Portrait hair as its own layer, matching the world sprite's styles."""
    tone = ramp(pigment.HAIR[max(0, min(HAIR_COLOURS - 1, colour))])
    name = folk.HAIR_STYLES[max(0, min(HAIR_STYLES - 1, style))]
    sketch = Sketch((SIZE, SIZE))
    radius = HEAD_R
    x, y = CENTRE, HEAD_Y
    piece = sketch.piece(tone)
    piece.poly(catmull([
        (x - radius - 0.6, y - radius * 0.10), (x - radius * 0.88, y - radius * 0.94),
        (x, y - radius * 1.22), (x + radius * 0.88, y - radius * 0.94),
        (x + radius + 0.6, y - radius * 0.10), (x + radius * 0.60, y - radius * 0.62),
        (x, y - radius * 0.46), (x - radius * 0.60, y - radius * 0.62),
    ], 5, closed=True), 3)
    if name == 'long':
        for sign in (-1, 1):
            piece.poly(catmull([
                (x + sign * (radius - 1.0), y - radius * 0.5),
                (x + sign * (radius + 3.4), y + radius * 0.6),
                (x + sign * (radius + 2.4), SHOULDER_Y + 2),
                (x + sign * (radius - 3.0), SHOULDER_Y),
                (x + sign * (radius - 4.0), y + radius * 0.2),
            ], 5, closed=True), 3)
    elif name == 'tail':
        piece.poly(catmull([(x + radius - 2.0, y - radius * 0.4),
                            (x + radius + 6.0, y + radius * 0.2),
                            (x + radius + 7.0, y + radius * 1.6),
                            (x + radius + 1.0, y + radius * 1.2)], 5, closed=True), 3)
    elif name == 'braids':
        for sign in (-1, 1):
            for step in range(3):
                piece.disc(x + sign * (radius + 0.4), y + radius * 0.3 + step * 5.0,
                           3.4 - step * 0.4, 3 if step % 2 == 0 else 2)
    elif name == 'curls':
        for angle in range(0, 360, 40):
            rad = math.radians(angle)
            if math.sin(rad) > 0.5:
                continue
            piece.disc(x + math.cos(rad) * (radius + 1.0),
                       y + math.sin(rad) * (radius + 0.4) - 1.4, 4.6, 3)
        piece.disc(x, y - radius * 0.95, 5.2, 4)
    elif name == 'topknot':
        piece.disc(x, y - radius * 1.34, 5.0, 3)
        piece.line([(x - 3.4, y - radius * 0.9), (x + 3.4, y - radius * 0.9)], 2, 2)
    else:  # crop
        for sign in (-1, 1):
            piece.poly([(x + sign * (radius + 0.8), y - radius * 0.2),
                        (x + sign * (radius - 0.6), y + radius * 0.34),
                        (x + sign * (radius + 1.4), y + radius * 0.40)], 2)
    sketch.carve(piece, rim=0.9, occlude=0.7, form=0.5, gleam=0.12)
    gloss = sketch.piece(tone)
    gloss.line(catmull([(x - radius * 0.7, y - radius * 0.55), (x - radius * 0.1, y - radius * 1.0),
                        (x + radius * 0.5, y - radius * 0.66)], 5), 5, 2)
    gloss.clip(piece)
    sketch.overlay(gloss)
    return sketch.result()


def townsfolk(role):
    """A composed portrait for one NPC role, using their world colours."""
    look = folk.ROLE_LOOK.get(role, ('#6a6a72', '#9a8f7a', 1, 1, 'pack'))
    coat, accent, hair_style, hair_colour, _tool = look
    build = pigment.keyed(role, 2)
    skin = pigment.keyed(role + 'skin', SKINS)
    sketch = Sketch((SIZE, SIZE))
    _shoulders(sketch, coat, build)
    _head(sketch, pigment.SKIN[skin], build)
    sketch.overlay(hair(hair_style, hair_colour))
    trim = sketch.piece(ramp(accent))
    trim.poly([(CENTRE - 22, SIZE - 6), (CENTRE + 22, SIZE - 6),
               (CENTRE + 22, SIZE - 2), (CENTRE - 22, SIZE - 2)], 3)
    sketch.carve(trim, rim=0.85, occlude=0.7, form=0.0, gleam=0.0)
    _frame(sketch)
    return sketch.result()


def _humanoid_bust(spec):
    """A goblin or a knight gets a face, not a muzzle with pointed ears."""
    cloth = spec.accent or '#5f5346'
    build = 0 if spec.height >= 16 else 1
    sketch = Sketch((SIZE, SIZE))
    _shoulders(sketch, cloth, build)
    _head(sketch, pigment.hexstr(spec.coat), build)
    weapon, headgear = beasts.HUMANOID_KIT.get(spec.family_key, ('', ''))
    radius = HEAD_R - build * 0.8
    if headgear in ('hood', 'bandana', 'hat'):
        cowl = sketch.piece(ramp(blend(pigment.rgb(cloth), (28, 24, 30, 255), 0.22)))
        if headgear == 'bandana':
            cowl.poly([(CENTRE - radius - 1, HEAD_Y - radius * 0.16),
                       (CENTRE + radius + 1, HEAD_Y - radius * 0.16),
                       (CENTRE + radius * 0.9, HEAD_Y - radius * 0.86),
                       (CENTRE - radius * 0.9, HEAD_Y - radius * 0.86)], 3)
        elif headgear == 'hat':
            cowl.poly([(CENTRE - radius - 7, HEAD_Y - radius * 0.30),
                       (CENTRE + radius + 7, HEAD_Y - radius * 0.30),
                       (CENTRE + radius + 3, HEAD_Y - radius * 0.02),
                       (CENTRE - radius - 3, HEAD_Y - radius * 0.02)], 3)
            cowl.poly(catmull([(CENTRE - radius * 0.8, HEAD_Y - radius * 0.36),
                               (CENTRE - radius * 0.3, HEAD_Y - radius * 1.7),
                               (CENTRE + radius * 0.7, HEAD_Y - radius * 1.5),
                               (CENTRE + radius * 0.8, HEAD_Y - radius * 0.36)], 5, closed=True), 3)
        else:
            cowl.poly(catmull([(CENTRE - radius - 3, HEAD_Y + radius * 0.7),
                               (CENTRE - radius - 1, HEAD_Y - radius * 1.05),
                               (CENTRE, HEAD_Y - radius * 1.4),
                               (CENTRE + radius + 1, HEAD_Y - radius * 1.05),
                               (CENTRE + radius + 3, HEAD_Y + radius * 0.7),
                               (CENTRE + radius * 0.5, HEAD_Y + radius * 0.05),
                               (CENTRE, HEAD_Y - radius * 0.35),
                               (CENTRE - radius * 0.5, HEAD_Y + radius * 0.05)], 5, closed=True), 3)
        sketch.carve(cowl, rim=0.9, occlude=0.75, form=0.5, gleam=0.1)
    elif headgear in ('helm', 'horns'):
        tone = ramp(spec.accent or '#8a939c')
        gear = sketch.piece(tone)
        if headgear == 'helm':
            gear.poly(catmull([(CENTRE - radius - 2, HEAD_Y + radius * 0.4),
                               (CENTRE - radius * 0.85, HEAD_Y - radius * 1.0),
                               (CENTRE, HEAD_Y - radius * 1.32),
                               (CENTRE + radius * 0.85, HEAD_Y - radius * 1.0),
                               (CENTRE + radius + 2, HEAD_Y + radius * 0.4),
                               (CENTRE, HEAD_Y - radius * 0.12)], 5, closed=True), 3)
        else:
            for sign in (-1, 1):
                gear.poly(catmull([(CENTRE + sign * radius * 0.66, HEAD_Y - radius * 0.52),
                                   (CENTRE + sign * radius * 1.5, HEAD_Y - radius * 1.5),
                                   (CENTRE + sign * radius * 1.02, HEAD_Y - radius * 0.34)],
                                  4, closed=True), 3)
        sketch.carve(gear, rim=0.95, occlude=0.75, form=0.5, gleam=0.35)
    if spec.glow:
        sketch.glow(spec.glow, 3, 0.35)
    _frame(sketch, '#2c2830')
    return sketch.result()


BEAST_SKULLS = {
    'quadruped': 'muzzle', 'drake': 'muzzle', 'serpent': 'muzzle', 'worm': 'maw',
    'bird': 'beak', 'insect': 'mandible', 'arachnid': 'mandible', 'crustacean': 'mandible',
    'aquatic': 'muzzle', 'humanoid': 'face', 'spirit': 'hollow', 'construct': 'plate',
    'elemental': 'hollow', 'mineral': 'plate', 'plant': 'cap', 'mimic': 'maw',
    'amphibian': 'muzzle', 'primate': 'face',
}


def creature(mob):
    """A boss portrait: the head only, at a size where its anatomy is legible."""
    spec = beasts.describe(mob)
    if spec.archetype == 'humanoid':
        return _humanoid_bust(spec)
    tones = spec.ramps()
    kind = BEAST_SKULLS.get(spec.archetype, 'muzzle')
    sketch = Sketch((SIZE, SIZE))
    radius = 17.0
    x, y = CENTRE, HEAD_Y + 2

    if spec.mane:
        mane = sketch.piece(tones['accent'])
        mane.disc(x, y + 2, radius * 1.34, 3)
        sketch.carve(mane, rim=0.7, occlude=0.75, form=0.4, gleam=0.0)

    skull = sketch.piece(tones['coat'])
    if kind == 'beak':
        skull.disc(x, y, radius * 0.86, 3)
    elif kind == 'mandible':
        skull.poly(catmull([(x - radius, y - radius * 0.5), (x, y - radius),
                            (x + radius, y - radius * 0.5), (x + radius * 0.7, y + radius * 0.8),
                            (x, y + radius), (x - radius * 0.7, y + radius * 0.8)],
                           6, closed=True), 3)
    elif kind == 'plate':
        skull.poly([(x - radius * 0.9, y - radius), (x + radius * 0.9, y - radius),
                    (x + radius, y + radius * 0.4), (x, y + radius),
                    (x - radius, y + radius * 0.4)], 3)
    elif kind == 'hollow':
        skull.poly(catmull([(x - radius * 0.9, y + radius * 0.6), (x - radius * 0.7, y - radius * 0.7),
                            (x, y - radius * 1.1), (x + radius * 0.7, y - radius * 0.7),
                            (x + radius * 0.9, y + radius * 0.6), (x, y + radius * 1.1)],
                           6, closed=True), 3)
    elif kind == 'cap':
        skull.poly(catmull([(x - radius * 1.1, y + radius * 0.4), (x - radius * 0.7, y - radius * 0.8),
                            (x, y - radius * 1.15), (x + radius * 0.7, y - radius * 0.8),
                            (x + radius * 1.1, y + radius * 0.4), (x, y + radius * 0.7)],
                           6, closed=True), 3)
    else:
        skull.disc(x, y, radius, 3)
    sketch.carve(skull, rim=0.95, occlude=0.75, form=0.55, gleam=0.2)

    if kind == 'muzzle':
        snout = sketch.piece(tones['coat'])
        snout.poly(catmull([(x - radius * 0.52, y + radius * 0.24),
                            (x + radius * 0.52, y + radius * 0.24),
                            (x + radius * 0.40, y + radius * 1.05),
                            (x - radius * 0.40, y + radius * 1.05)], 5, closed=True), 3)
        sketch.carve(snout, rim=0.9, occlude=0.7, form=0.4, gleam=0.1)
        nose = sketch.piece(tones['claw'])
        nose.ellipse((x - 3.4, y + radius * 0.78, x + 3.4, y + radius * 1.02), 3)
        sketch.carve(nose, rim=0.8, occlude=0.5, form=0.0, gleam=0.3)
    elif kind == 'beak':
        beak = sketch.piece(tones['horn'])
        beak.poly(catmull([(x - radius * 0.42, y + radius * 0.1),
                           (x + radius * 0.42, y + radius * 0.1),
                           (x, y + radius * 1.25)], 5, closed=True), 3)
        sketch.carve(beak, rim=0.95, occlude=0.7, form=0.4, gleam=0.35)
    elif kind in ('maw', 'mandible'):
        maw = sketch.piece(ramp('#5c2a30'))
        maw.ellipse((x - radius * 0.62, y + radius * 0.2, x + radius * 0.62, y + radius * 0.95), 3)
        sketch.carve(maw, rim=0.3, occlude=0.4, form=0.0, gleam=0.0)
        teeth = sketch.piece(tones['horn'])
        for index in range(5):
            tx = x - radius * 0.5 + index * radius * 0.25
            teeth.poly([(tx, y + radius * 0.24), (tx + radius * 0.13, y + radius * 0.24),
                        (tx + radius * 0.06, y + radius * 0.58)], 3)
        sketch.stamp(teeth, rim=0.6, occlude=0.4)

    if spec.horn:
        horns = sketch.piece(tones['horn'])
        for sign in (-1, 1):
            horns.poly(catmull([(x + sign * radius * 0.62, y - radius * 0.64),
                                (x + sign * radius * 1.24, y - radius * 1.34),
                                (x + sign * radius * 1.02, y - radius * 0.46)], 4, closed=True), 3)
        sketch.carve(horns, rim=0.95, occlude=0.7, form=0.4, gleam=0.3)
    if spec.ear not in ('', 'none') and kind in ('muzzle', 'face'):
        ears = sketch.piece(tones['coat'])
        for sign in (-1, 1):
            ears.poly(catmull([(x + sign * radius * 0.62, y - radius * 0.52),
                               (x + sign * radius * 1.02, y - radius * 1.22),
                               (x + sign * radius * 1.06, y - radius * 0.36)], 4, closed=True), 3)
        sketch.carve(ears, rim=0.85, occlude=0.7, form=0.3, gleam=0.0)

    eyes = sketch.piece(ramp(spec.eye))
    for sign in (-1, 1):
        ex = x + sign * radius * 0.42
        ey = y - radius * 0.16
        eyes.ellipse((ex - 3.6, ey - 2.4, ex + 3.6, ey + 2.4), 4)
        eyes.disc(ex, ey, 1.7, (28, 22, 28, 255))
        eyes.dot(ex - 0.9, ey - 0.9, (250, 248, 240, 255))
    sketch.stamp(eyes, rim=0.8, occlude=0.4)
    if spec.glow:
        sketch.glow(spec.glow, 3, 0.42)
    _frame(sketch, '#2c2830')
    return sketch.result()


def plan(catalogue=None):
    """Every portrait, as (key, maker) pairs."""
    out = []
    for build in range(BUILDS):
        for skin in range(SKINS):
            out.append(('portraits/base_%d_%d' % (build, skin),
                        lambda b=build, s=skin: base(b, s)))
    for style in range(HAIR_STYLES):
        for colour in range(HAIR_COLOURS):
            out.append(('portraits/hair_%d_%d' % (style, colour),
                        lambda s=style, c=colour: hair(s, c)))
    for role in sorted(folk.ROLE_LOOK):
        out.append(('portraits/npc_' + role, lambda r=role: townsfolk(r)))
    if catalogue:
        for mob in catalogue['mobs']:
            if mob.get('boss') or mob.get('elite'):
                out.append(('portraits/mob_' + mob['id'], lambda m=mob: creature(m)))
    return out
