"""People: bodies, hair, worn equipment and named townsfolk.

Every layer in this module is built from shared shape helpers that read the rig,
so a breastplate drawn by `armour_frame` covers exactly the torso that
`body_frame` drew underneath it, in all four facings and all six states.
"""
from __future__ import annotations

import math

from . import gear, pigment, rig, smith
from .brush import Sketch, catmull, refine_sprite, taper_shape
from .pigment import blend, ramp

SIZE = 64
INK = (28, 24, 32, 255)

CLOTH_UNDER = '#7c6a58'
TRUNK = '#5d5347'


# ---------------------------------------------------------------- geometry --

def _axis(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length


def torso_shape(pose, expand=0.0, drop=0.0):
    """Outline of the trunk, built along the spine rather than along the screen.

    Reading the chest-to-pelvis axis is what lets one shape serve a standing
    figure, a kneeling one and a body lying on the ground.
    """
    build = pose.build
    chest, pelvis = pose.chest, pose.pelvis
    ux, uy = _axis(pelvis, chest)                       # points up the spine
    top = (chest[0] + ux * 4.6, chest[1] + uy * 4.6)
    bottom = (pelvis[0] - ux * (1.4 + drop), pelvis[1] - uy * (1.4 + drop))
    half_top = (build.chest_depth if pose.side else build.shoulder * 0.94) + expand
    half_waist = (build.chest_depth * 0.88 if pose.side else build.hip + 1.6) + expand
    px, py = -uy, ux                                    # across the body
    lean = pose.facing * 0.6 if pose.side else 0.0
    points = [
        (top[0] - px * half_top * 0.82 + px * lean, top[1] - py * half_top * 0.82 + py * lean),
        (top[0] + ux * 0.6, top[1] + uy * 0.6),
        (top[0] + px * half_top * 0.82 + px * lean, top[1] + py * half_top * 0.82 + py * lean),
        (chest[0] + px * half_top, chest[1] + py * half_top),
        (bottom[0] + px * half_waist, bottom[1] + py * half_waist),
        (bottom[0] - ux * 0.8, bottom[1] - uy * 0.8),
        (bottom[0] - px * half_waist, bottom[1] - py * half_waist),
        (chest[0] - px * half_top, chest[1] - py * half_top),
    ]
    return catmull(points, 5, closed=True)


def head_box(pose, expand=0.0):
    x, y = pose.head
    r = pose.head_r + expand
    return (x - r, y - r * 1.06, x + r, y + r * 1.02)


def arm_points(pose, key):
    return pose.shoulder[key], pose.elbow[key], pose.hand[key]


def leg_points(pose, key):
    return pose.hip[key], pose.knee[key], pose.foot[key]


def _limb(piece, a, b, w0, w1, colour):
    piece.poly(taper_shape(a, b, w0, w1), colour)


def foot_shape(pose, key, expand=0.0):
    """A foot sits across the shin, so the shoe follows the leg in every pose."""
    _, knee, foot = leg_points(pose, key)
    dx, dy = _axis(knee, foot)
    toe = pose.facing if pose.facing else (1 if key == 'near' else -1)
    px, py = dy * toe, -dx * toe
    ankle = (foot[0] - dx * (2.6 + expand), foot[1] - dy * (2.6 + expand))
    sole = (foot[0] + dx * (0.6 + expand * 0.4), foot[1] + dy * (0.6 + expand * 0.4))
    reach = 3.4 + expand
    heel = 2.2 + expand
    return catmull([
        (ankle[0] - px * (heel * 0.85), ankle[1] - py * (heel * 0.85)),
        (ankle[0] + px * 1.4, ankle[1] + py * 1.4),
        (sole[0] + px * reach, sole[1] + py * reach),
        (sole[0] + px * (reach * 0.7), sole[1] + py * (reach * 0.7)),
        (sole[0] - px * heel, sole[1] - py * heel),
    ], 4, closed=True)


def _rotate_about(points, centre, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    cx, cy = centre
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in points]


# ------------------------------------------------------------------- body ---

def _skin(index):
    return ramp(pigment.SKIN[max(0, min(5, index))])


def _draw_arm(sketch, pose, key, skin, cloth, sleeve=True):
    build = pose.build
    shoulder, elbow, hand = arm_points(pose, key)
    depth = 1.0 if key == 'near' else 0.88
    piece = sketch.piece(cloth if sleeve else skin)
    _limb(piece, shoulder, elbow, build.limb * 1.12 * depth, build.limb * 0.95 * depth, 3 if sleeve else 3)
    if sleeve:
        sketch.stamp(piece, rim=0.7, occlude=0.55)
        cuff = sketch.piece(cloth)
        dx, dy = _axis(shoulder, elbow); px, py = -dy, dx
        cuff.line([(elbow[0]-px*build.limb*0.46, elbow[1]-py*build.limb*0.46),
                   (elbow[0]+px*build.limb*0.46, elbow[1]+py*build.limb*0.46)], 4, 1)
        sketch.stamp(cuff, outline=False, rim=0, occlude=0)
        piece = sketch.piece(skin)
    _limb(piece, elbow, hand, build.limb * 0.92 * depth, build.limb * 0.74 * depth, 3)
    piece.disc(hand[0], hand[1], build.limb * 0.48 * depth + 0.4, 2 if key == 'far' else 3)
    sketch.stamp(piece, rim=0.75 if key == 'near' else 0.4, occlude=0.5)


def _draw_leg(sketch, pose, key, skin, cloth, shoe='#4a3a2e'):
    build = pose.build
    hip, knee, foot = leg_points(pose, key)
    depth = 1.0 if key == 'near' else 0.9
    piece = sketch.piece(cloth)
    _limb(piece, hip, knee, build.thigh * 1.05 * depth, build.thigh * 0.82 * depth, 3)
    sketch.stamp(piece, rim=0.65, occlude=0.55)
    seam = sketch.piece(cloth)
    seam.line([(hip[0]*0.55+knee[0]*0.45, hip[1]*0.55+knee[1]*0.45),
               (knee[0], knee[1]-0.4)], 4, 1)
    sketch.stamp(seam, outline=False, rim=0, occlude=0)
    piece = sketch.piece(skin)
    _limb(piece, knee, (foot[0], foot[1] - 1.6), build.thigh * 0.74 * depth, build.thigh * 0.56 * depth, 3)
    sketch.stamp(piece, rim=0.6, occlude=0.5)
    piece = sketch.piece(shoe)
    foot = foot_shape(pose, key, 0.0)
    piece.poly(foot, 3)
    sketch.stamp(piece, rim=0.7, occlude=0.6)
    sole = sketch.piece(shoe)
    ys = sorted(point[1] for point in foot)
    y = ys[-2] if len(ys)>1 else foot[-1][1]
    xs = [point[0] for point in foot]
    sole.line([(min(xs)+0.8, y), (max(xs)-0.8, y)], 1, 1)
    sketch.stamp(sole, outline=False, rim=0, occlude=0)


def head_basis(pose):
    """Local axes of the skull: down the jaw, and across the face."""
    tilt = -pose.head_tilt
    return (math.sin(-tilt), math.cos(-tilt)), (math.cos(-tilt), -math.sin(-tilt)), tilt


def _draw_head(sketch, pose, skin, face=True):
    piece = sketch.piece(skin)
    x, y = pose.head
    r = pose.head_r
    down, across, tilt = head_basis(pose)
    skull = [(x + math.cos(a * math.tau / 18) * r,
              y + math.sin(a * math.tau / 18) * r * 1.04) for a in range(18)]
    piece.poly(_rotate_about(skull, pose.head, tilt), 3)
    jaw = (x + down[0] * r * 0.66, y + down[1] * r * 0.66)
    piece.poly(_rotate_about([
        (jaw[0] - r * 0.66, jaw[1] - r * 0.34), (jaw[0] + r * 0.66, jaw[1] - r * 0.34),
        (jaw[0] + r * 0.46, jaw[1] + r * 0.40), (jaw[0] - r * 0.46, jaw[1] + r * 0.40),
    ], jaw, tilt), 2)
    if pose.side:
        nose = pose.facing
        tip = (x + across[0] * nose * (r + 1.4), y + across[1] * nose * (r + 1.4))
        base_a = (x + across[0] * nose * (r - 0.4) - down[0] * 1.3, y + across[1] * nose * (r - 0.4) - down[1] * 1.3)
        base_b = (x + across[0] * nose * (r - 0.5) + down[0] * 1.9, y + across[1] * nose * (r - 0.5) + down[1] * 1.9)
        piece.poly(catmull([base_a, tip, base_b], 3, closed=True), 3)
        ear = (x - across[0] * nose * r * 0.42, y - across[1] * nose * r * 0.42)
        piece.poly([(ear[0] - down[0] * 0.6, ear[1] - down[1] * 0.6),
                    (ear[0] + across[0] * nose * 0.9, ear[1] + across[1] * nose * 0.9),
                    (ear[0] + down[0] * 2.0, ear[1] + down[1] * 2.0)], 2)
    sketch.stamp(piece, rim=0.9, occlude=0.5)
    if not face or pose.back:
        return
    piece = sketch.piece(skin)
    eye = (36, 30, 40, 255)
    gleam = blend(eye, (255, 255, 255, 255), 0.34)

    def at(side_offset, down_offset):
        return (x + across[0] * side_offset + down[0] * down_offset,
                y + across[1] * side_offset + down[1] * down_offset)

    if pose.side:
        nose = pose.facing
        piece.dot(*at(nose * 2.2, -0.3), eye)
        piece.dot(*at(nose * 2.2, 0.5), gleam)
        piece.line([at(nose * 1.2, -1.7), at(nose * 3.1, -1.5)], 1)
        piece.dot(*at(nose * 3.0, 1.7), 2)
        piece.line([at(nose * 1.3, 3.0), at(nose * 2.8, 2.8)], 2, 1)
    else:
        for sign in (-1, 1):
            piece.dot(*at(sign * 2.1, -0.1), eye)
            piece.dot(*at(sign * 2.1, 0.7), gleam)
            piece.line([at(sign * 1.1, -1.6), at(sign * 3.0, -1.5)], 1)
            piece.dot(*at(sign * 3.0, 1.8), 4)
        piece.line([at(0.0, 0.8), at(0.0, 2.2)], 4, 1)
        piece.line([at(-1.4, 3.2), at(1.4, 3.2)], 1, 1)
    sketch.stamp(piece, outline=False, rim=0, occlude=0)


def _neck_span(pose, back=1.6, forward=1.8):
    """Neck axis runs from the chest toward the head, so it works when prone."""
    hx, hy = pose.head
    cx, cy = pose.chest
    dx, dy = hx - cx, hy - cy
    length = math.hypot(dx, dy) or 1.0
    dx, dy = dx / length, dy / length
    nx, ny = pose.neck
    return (nx - dx * back, ny - dy * back), (nx + dx * forward, ny + dy * forward)


def _draw_torso(sketch, pose, skin, cloth):
    piece = sketch.piece(cloth)
    piece.poly(torso_shape(pose), 3)
    collar_a, collar_b = _neck_span(pose, 2.4, 0.4)
    piece.poly(taper_shape(collar_a, collar_b, 6.0, 4.8), 2)
    sketch.stamp(piece, rim=0.8, occlude=0.6)
    # Two pose-locked construction lines add garment scale without noisy texture.
    ux, uy = _axis(pose.pelvis, pose.chest); px, py = -uy, ux
    detail = sketch.piece(cloth)
    collar = (pose.chest[0]+ux*1.9, pose.chest[1]+uy*1.9)
    waist = (pose.pelvis[0]+ux*1.1, pose.pelvis[1]+uy*1.1)
    detail.line([(collar[0]-px*3.0, collar[1]-py*3.0), (collar[0]+px*3.0, collar[1]+py*3.0)], 4, 1)
    detail.line([(waist[0]-px*(pose.build.hip+0.7), waist[1]-py*(pose.build.hip+0.7)),
                 (waist[0]+px*(pose.build.hip+0.7), waist[1]+py*(pose.build.hip+0.7))], 2, 1)
    detail.clip(piece); sketch.overlay(detail)
    neck_a, neck_b = _neck_span(pose, 1.4, 2.4)
    piece = sketch.piece(skin)
    piece.poly(taper_shape(neck_a, neck_b, 4.6, 4.2), 2)
    sketch.stamp(piece, outline=False, rim=0.5, occlude=0.4)


def body_layers(sketch, pose, skin_index, cloth=CLOTH_UNDER, trunk=TRUNK, shoe='#4a3a2e', face=True):
    """Depth sorted assembly. A raised arm is drawn after the head so it is not
    swallowed by it, which is what makes overhead swings and casts read."""
    skin = _skin(skin_index)
    raised = {key: pose.hand[key][1] < pose.shoulder[key][1] - 1.5 for key in ('far', 'near')}
    if not raised['far']:
        _draw_arm(sketch, pose, 'far', skin, cloth)
    _draw_leg(sketch, pose, 'far', skin, trunk, shoe)
    _draw_torso(sketch, pose, skin, cloth)
    _draw_leg(sketch, pose, 'near', skin, trunk, shoe)
    if not raised['near']:
        _draw_arm(sketch, pose, 'near', skin, cloth)
    _draw_head(sketch, pose, skin, face)
    for key in ('far', 'near'):
        if raised[key]:
            _draw_arm(sketch, pose, key, skin, cloth)


def finish(sketch, pose):
    sketch.image = refine_sprite(sketch.result(), 0.10)
    if pose.flash:
        sketch.tone((255, 236, 206, 255), 0.42 * pose.flash)
    if pose.fade < 1.0:
        sketch.fade(pose.fade)
    return sketch.result()


def body_frame(build, skin, state, frame, direction):
    pose = rig.pose(build, state, frame, direction)
    sketch = Sketch(SIZE)
    body_layers(sketch, pose, skin)
    return finish(sketch, pose)


# ------------------------------------------------------------------- hair ---

HAIR_STYLES = ('crop', 'long', 'tail', 'braids', 'curls', 'topknot')


def hair_frame(style, colour, state, frame, direction):
    pose = rig.pose(0, state, frame, direction)
    sketch = Sketch(SIZE)
    tone = ramp(pigment.HAIR[max(0, min(7, colour))])
    name = HAIR_STYLES[max(0, min(5, style))]
    x, y = pose.head
    r = pose.head_r
    back_side = -pose.facing if pose.facing else 0
    _, _, tilt = head_basis(pose)

    class Turned:
        """Draw hair in head-local space; the head tilt is applied on the way out."""

        def __init__(self, target):
            self.target = target

        def poly(self, points, colour):
            self.target.poly(_rotate_about(points, pose.head, tilt), colour)
            return self

        def line(self, points, colour, width=1):
            self.target.line(_rotate_about(points, pose.head, tilt), colour, width)
            return self

        def disc(self, cx, cy, radius, colour):
            px, py = _rotate_about([(cx, cy)], pose.head, tilt)[0]
            self.target.disc(px, py, radius, colour)
            return self

        def ellipse(self, box, colour):
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            px, py = _rotate_about([(cx, cy)], pose.head, tilt)[0]
            dx, dy = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
            self.target.ellipse((px - dx, py - dy, px + dx, py + dy), colour)
            return self

    flat = sketch.piece(tone)
    piece = Turned(flat)
    # skull cap common to every style
    # The hairline stops above the brow: a cap that reaches the eyes reads as a hood.
    piece.poly(catmull([
        (x - r - 0.2, y - r * 0.10), (x - r * 0.88, y - r * 0.92), (x, y - r * 1.24),
        (x + r * 0.88, y - r * 0.92), (x + r + 0.2, y - r * 0.10), (x + r * 0.62, y - r * 0.66),
        (x, y - r * 0.48), (x - r * 0.62, y - r * 0.66),
    ], 4, closed=True), 3)
    if pose.back:
        piece.ellipse((x - r - 0.2, y - r * 1.1, x + r + 0.2, y + r * 0.85), 3)
    if name == 'crop':
        piece.poly([(x - r - 0.6, y - 0.4), (x - r + 0.4, y + 2.2), (x - r - 0.9, y + 2.6)], 2)
        piece.poly([(x + r + 0.6, y - 0.4), (x + r - 0.4, y + 2.2), (x + r + 0.9, y + 2.6)], 2)
    elif name == 'long':
        for sign in ((-1, 1) if not pose.side else (back_side,)):
            piece.poly(catmull([
                (x + sign * (r - 0.4), y - 2.0), (x + sign * (r + 1.4), y + 3.0),
                (x + sign * (r + 1.0), y + 9.4), (x + sign * (r - 1.8), y + 9.6),
                (x + sign * (r - 2.2), y + 2.0),
            ], 5, closed=True), 3)
    elif name == 'tail':
        sign = back_side if pose.side else 1
        piece.poly(catmull([
            (x + sign * (r - 1.0), y - 1.6), (x + sign * (r + 2.6), y + 1.0),
            (x + sign * (r + 3.2), y + 6.6), (x + sign * (r + 0.8), y + 7.4),
            (x + sign * (r - 0.4), y + 2.4),
        ], 5, closed=True), 3)
        piece.line([(x + sign * (r - 0.6), y - 1.0), (x + sign * (r + 1.6), y + 0.4)], 1, 2)
    elif name == 'braids':
        for sign in ((-1, 1) if not pose.side else (back_side, back_side)):
            for step in range(3):
                piece.disc(x + sign * (r + 0.2), y + 2.0 + step * 2.4, 1.7 - step * 0.18, 3 if step % 2 == 0 else 2)
    elif name == 'curls':
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            if math.sin(rad) > 0.55:
                continue
            piece.disc(x + math.cos(rad) * (r + 0.4), y + math.sin(rad) * (r + 0.2) - 0.6, 2.3, 3)
        piece.disc(x, y - r * 0.9, 2.6, 4)
    else:  # topknot
        piece.disc(x + (back_side * 0.8 if pose.side else 0), y - r * 1.35, 2.5, 3)
        piece.line([(x - 1.6, y - r * 0.9), (x + 1.6, y - r * 0.9)], 2, 2)
    sketch.stamp(flat, rim=0.85, occlude=0.5)
    # a single strand of highlight keeps flat hair from reading as a helmet
    gloss_flat = sketch.piece(tone)
    Turned(gloss_flat).line(
        catmull([(x - r * 0.7, y - r * 0.5), (x - r * 0.1, y - r * 0.95), (x + r * 0.5, y - r * 0.6)], 4), 5, 1)
    gloss_flat.clip(flat)
    sketch.overlay(gloss_flat)
    return finish(sketch, pose)


# -------------------------------------------------------------- equipment ---

PLATE_SLOTS = {'helmet', 'chest', 'gloves', 'legs', 'boots'}


def _weight(item):
    tags = set(item.get('tags', ()))
    if 'heavy' in tags:
        return 'heavy'
    if 'medium' in tags:
        return 'medium'
    return 'light'


def _armour_ramp(item):
    return ramp(gear.body_colour(item))


def _trim_ramp(item):
    return ramp(gear.tier_of(item).trim)


def _gem_ramp(item):
    return ramp(gear.tier_of(item).gem)


def _worn_crest(sketch, pose, item, style):
    """Whatever this tier puts on top of a helm, drawn on the head."""
    kind = style['crest']
    if kind == 'none':
        return
    trim = _trim_ramp(item)
    x, y = pose.head
    r = pose.head_r
    top = y - r * 1.35
    plume = style['plume']
    piece = sketch.piece(trim)
    if kind == 'ridge':
        piece.poly(catmull([(x - r * 0.8, top + 1.6), (x, top - 1.4), (x + r * 0.8, top + 1.6),
                            (x, top + 0.6)], 4, closed=True), 3)
    elif kind == 'fin':
        piece.poly(catmull([(x - 1.4, top + 2.0), (x - 0.4, top - 3.0 - plume * 1.6),
                            (x + 2.4, top + 0.4), (x + 0.8, top + 1.8)], 4, closed=True), 3)
    elif kind == 'comb':
        piece.poly(catmull([(x - r * 0.9, top + 2.0), (x - 1.2, top - 3.4 - plume * 1.6),
                            (x + 1.2, top - 3.4 - plume * 1.6), (x + r * 0.9, top + 2.0),
                            (x, top + 0.8)], 5, closed=True), 3)
    elif kind == 'horns':
        for sign in (-1, 1):
            piece.poly(catmull([(x + sign * r * 0.7, top + 2.2), (x + sign * (r + 2.4), top - 0.6 - plume),
                                (x + sign * (r + 3.0), top + 2.6), (x + sign * r * 0.9, top + 2.8)],
                               4, closed=True), 3)
    elif kind == 'halo':
        piece.disc(x, top - 1.6 - plume, r * 0.95)
        piece.erase_ellipse((x - r * 0.62, top - 2.2 - plume - r * 0.62,
                             x + r * 0.62, top - 1.0 - plume + r * 0.62))
    elif kind == 'shards':
        for dx, height in ((-2.4, 2.4), (0.2, 4.2 + plume), (2.6, 2.8)):
            piece.poly([(x + dx - 1.1, top + 2.0), (x + dx, top - height), (x + dx + 1.1, top + 2.0)], 3)
    sketch.carve(piece, rim=0.9, occlude=0.6)
    if style['glow'] and kind in ('halo', 'shards'):
        sketch.glow(style['glow'], 2, 0.35)


def _helmet(sketch, pose, item):
    tone = _armour_ramp(item)
    trim = _trim_ramp(item)
    style = gear.style_of(item)
    weight = _weight(item)
    x, y = pose.head
    r = pose.head_r
    piece = sketch.piece(tone)
    if weight == 'heavy':
        piece.poly(catmull([
            (x - r - 1.2, y + 2.6), (x - r - 1.0, y - r * 0.6), (x, y - r * 1.5),
            (x + r + 1.0, y - r * 0.6), (x + r + 1.2, y + 2.6), (x + r * 0.5, y + 3.4),
            (x - r * 0.5, y + 3.4),
        ], 5, closed=True), 3)
        if not pose.back:
            slot = sketch.piece(tone)
            slot.rect((x - r * 0.75, y - 0.8, x + r * 0.75, y + 0.6), (22, 20, 26, 255))
            slot.clip(piece)
            sketch.carve(piece, rim=0.95, occlude=0.75)
            sketch.overlay(slot)
            ridge = sketch.piece(trim)
            ridge.line([(x, y - r * 1.45), (x, y + 3.0)], 4, 1)
            sketch.stamp(ridge, outline=False, rim=0, occlude=0)
            _worn_crest(sketch, pose, item, style)
            return
    elif weight == 'medium':
        piece.poly(catmull([
            (x - r - 0.9, y + 0.8), (x - r * 0.8, y - r * 1.0), (x, y - r * 1.42),
            (x + r * 0.8, y - r * 1.0), (x + r + 0.9, y + 0.8), (x + r * 0.4, y - 0.2),
            (x - r * 0.4, y - 0.2),
        ], 5, closed=True), 3)
        for sign in (-1, 1):
            piece.poly([(x + sign * (r + 0.4), y - 0.4), (x + sign * (r + 1.9), y + 2.4),
                        (x + sign * (r - 0.2), y + 2.8)], 2)
    else:
        piece.poly(catmull([
            (x - r - 0.7, y + 1.2), (x - r * 0.7, y - r * 1.05), (x, y - r * 1.3),
            (x + r * 0.7, y - r * 1.05), (x + r + 0.7, y + 1.2), (x, y - r * 0.2),
        ], 5, closed=True), 3)
    sketch.carve(piece, rim=0.95, occlude=0.75)
    band = sketch.piece(trim)
    if weight == 'light':
        band.line([(x - r * 0.9, y - r * 0.35), (x + r * 0.9, y - r * 0.35)], 4, 1)
    else:
        band.line([(x - r * 0.95, y - r * 0.15), (x + r * 0.95, y - r * 0.15)], 4, 1)
    sketch.stamp(band, outline=False, rim=0, occlude=0)
    _worn_crest(sketch, pose, item, style)


def _chest(sketch, pose, item):
    tone = _armour_ramp(item)
    trim = _trim_ramp(item)
    style = gear.style_of(item)
    weight = _weight(item)
    build = pose.build
    piece = sketch.piece(tone)
    # plate stands off the body, mail follows it, cloth drapes and flares
    bulk = {'heavy': 0.95, 'medium': 0.65}.get(weight, 0.35)
    piece.poly(torso_shape(pose, expand=bulk, drop=0.4), 3)
    if weight == 'light':
        hem = pose.pelvis[1] + 7.0
        flare = build.hip + 4.4
        piece.poly(catmull([
            (pose.pelvis[0] - build.hip - 1.4, pose.pelvis[1] - 1.0),
            (pose.pelvis[0] + build.hip + 1.4, pose.pelvis[1] - 1.0),
            (pose.pelvis[0] + flare, hem), (pose.pelvis[0], hem + 1.0),
            (pose.pelvis[0] - flare, hem),
        ], 5, closed=True), 3)
    sketch.carve(piece, rim=0.95, occlude=0.8, form=0.5)
    if weight == 'light':
        collar = sketch.piece(trim)
        neck = pose.neck
        collar.poly(catmull([(neck[0] - 4.6, neck[1] + 1.0), (neck[0], neck[1] + 6.4),
                             (neck[0] + 4.6, neck[1] + 1.0), (neck[0], neck[1] + 2.6)],
                            5, closed=True), 3)
        sketch.carve(collar, rim=0.9, occlude=0.6)
    detail = sketch.piece(tone)
    cx = pose.chest[0]
    top = pose.chest[1] - 4.4
    if weight == 'heavy':
        detail.line([(cx, top + 0.6), (cx, pose.pelvis[1] + 0.4)], 1, 1)
        detail.line([(cx - build.shoulder * 0.6, top + 3.2), (cx + build.shoulder * 0.6, top + 3.2)], 1, 1)
        detail.line([(cx - build.shoulder * 0.5, top + 6.0), (cx + build.shoulder * 0.5, top + 6.0)], 5, 1)
    elif weight == 'medium':
        for step in range(3):
            y = top + 1.6 + step * 2.8
            detail.line([(cx - build.shoulder * 0.72, y), (cx + build.shoulder * 0.72, y)], 1, 1)
            detail.line([(cx - build.shoulder * 0.5, y - 0.9), (cx + build.shoulder * 0.5, y - 0.9)], 5, 1)
    else:
        detail.line(catmull([(cx - 2.4, top + 1.0), (cx, top + 2.4), (cx + 2.4, top + 1.0)], 4), 1, 1)
        detail.line([(cx, top + 2.0), (cx, pose.pelvis[1] - 1.0)], 1, 1)
    detail.clip(piece)
    sketch.overlay(detail)
    if weight != 'light':
        kind = style['pauldron']
        plume = style['plume']
        for key in ('far', 'near'):
            shoulder = pose.shoulder[key]
            outward = 1 if shoulder[0] >= pose.chest[0] else -1
            pauldron = sketch.piece(tone if weight == 'medium' else trim)
            span = (3.4 if weight == 'medium' else 4.2) * (1.0 + plume * 0.12)
            if kind == 'winged':
                shape = [(shoulder[0] - span * 0.8, shoulder[1] - 1.0),
                         (shoulder[0], shoulder[1] - 2.6),
                         (shoulder[0] + outward * (span + 1.6 + plume * 1.6), shoulder[1] - 3.4 - plume),
                         (shoulder[0] + outward * span * 0.7, shoulder[1] + 2.0),
                         (shoulder[0] - span * 0.5, shoulder[1] + 2.4)]
            elif kind == 'spiked':
                shape = [(shoulder[0] - span * 0.8, shoulder[1] - 1.0),
                         (shoulder[0] - span * 0.2, shoulder[1] - 2.8),
                         (shoulder[0] + outward * (span + 2.2), shoulder[1] - 3.8 - plume),
                         (shoulder[0] + outward * span * 0.8, shoulder[1] + 1.4),
                         (shoulder[0] - span * 0.5, shoulder[1] + 2.4)]
            elif kind == 'crystal':
                shape = [(shoulder[0] - span * 0.7, shoulder[1] - 0.8),
                         (shoulder[0] - span * 0.1, shoulder[1] - 4.2 - plume),
                         (shoulder[0] + outward * span * 0.9, shoulder[1] - 1.4),
                         (shoulder[0] + outward * span * 0.7, shoulder[1] + 2.2),
                         (shoulder[0] - span * 0.5, shoulder[1] + 2.4)]
            else:
                shape = [(shoulder[0] - span * 0.8, shoulder[1] - 1.2),
                         (shoulder[0], shoulder[1] - 2.6),
                         (shoulder[0] + span * 0.8, shoulder[1] - 1.0),
                         (shoulder[0] + span * 0.6, shoulder[1] + 2.2),
                         (shoulder[0] - span * 0.6, shoulder[1] + 2.4)]
            pauldron.poly(catmull(shape, 5, closed=True), 3)
            sketch.carve(pauldron, rim=0.95, occlude=0.7)
            if kind == 'layered':
                lower = sketch.piece(trim)
                lower.poly(catmull([(shoulder[0] - span * 0.7, shoulder[1] + 1.6),
                                    (shoulder[0], shoulder[1] + 0.4),
                                    (shoulder[0] + span * 0.7, shoulder[1] + 1.6),
                                    (shoulder[0], shoulder[1] + 3.6)], 4, closed=True), 3)
                sketch.carve(lower, rim=0.9, occlude=0.7)
    if style['rune'] > 0.4:
        stone = sketch.piece(_gem_ramp(item))
        cx, cy = pose.chest
        stone.poly([(cx, cy - 2.6), (cx + 2.0, cy), (cx, cy + 2.6), (cx - 2.0, cy)], 3)
        sketch.carve(stone, rim=1.0, occlude=0.5)
        if style['glow']:
            sketch.glow(style['glow'], 2, 0.3)


def _legs(sketch, pose, item):
    tone = _armour_ramp(item)
    build = pose.build
    weight = _weight(item)
    for key in ('far', 'near'):
        hip, knee, _ = leg_points(pose, key)
        piece = sketch.piece(tone)
        wide = 1.18 if weight == 'heavy' else 1.06
        piece.poly(taper_shape(hip, (knee[0], knee[1] + 1.0), build.thigh * wide, build.thigh * 0.9), 3)
        if weight == 'heavy':
            piece.poly(taper_shape((knee[0], knee[1] - 1.0), (knee[0], knee[1] + 1.6), build.thigh * 0.95, build.thigh * 0.8), 4)
        sketch.carve(piece, rim=0.9, occlude=0.75, form=0.35)
    belt = sketch.piece(tone)
    belt.poly(taper_shape((pose.pelvis[0] - 0.4, pose.pelvis[1] - 0.6), (pose.pelvis[0] + 0.4, pose.pelvis[1] + 1.2),
                          (build.hip + 2.6) * 2, (build.hip + 2.2) * 2), 2)
    sketch.stamp(belt, rim=0.7, occlude=0.5)


def _boots(sketch, pose, item):
    tone = _armour_ramp(item)
    trim = _trim_ramp(item)
    build = pose.build
    for key in ('far', 'near'):
        _, knee, foot = leg_points(pose, key)
        piece = sketch.piece(tone)
        mid = ((knee[0] + foot[0]) / 2, (knee[1] + foot[1]) / 2 + 1.0)
        piece.poly(taper_shape(mid, (foot[0], foot[1] - 1.8), build.thigh * 0.86, build.thigh * 0.72), 3)
        toe = pose.facing if pose.facing else (1 if key == 'near' else -1)
        piece.poly(catmull([
            (foot[0] - 2.6, foot[1] - 3.0), (foot[0] + 2.2 + toe * 1.4, foot[1] - 2.8),
            (foot[0] + 2.8 + toe * 1.8, foot[1] - 0.3), (foot[0] - 2.8, foot[1] - 0.1),
        ], 4, closed=True), 3)
        sketch.stamp(piece, rim=0.8, occlude=0.6)
        cuff = sketch.piece(trim)
        cuff.poly(taper_shape((mid[0], mid[1] - 1.4), (mid[0], mid[1] + 0.6), build.thigh * 0.98, build.thigh * 0.9), 3)
        sketch.stamp(cuff, rim=0.6, occlude=0.4)


def _gloves(sketch, pose, item):
    tone = _armour_ramp(item)
    build = pose.build
    for key in ('far', 'near'):
        _, elbow, hand = arm_points(pose, key)
        piece = sketch.piece(tone)
        wrist = ((elbow[0] + hand[0]) / 2, (elbow[1] + hand[1]) / 2)
        piece.poly(taper_shape(wrist, hand, build.limb * 0.92, build.limb * 0.8), 3)
        piece.disc(hand[0], hand[1], build.limb * 0.55, 3)
        sketch.carve(piece, rim=0.9, occlude=0.7, form=0.3)


def _belt(sketch, pose, item):
    tone = _armour_ramp(item)
    trim = _trim_ramp(item)
    build = pose.build
    piece = sketch.piece(tone)
    width = (build.hip + 2.8) * 2 if not pose.side else (build.chest_depth + 1.6) * 2
    piece.poly(taper_shape((pose.pelvis[0], pose.pelvis[1] - 1.6), (pose.pelvis[0], pose.pelvis[1] + 0.4), width, width * 0.96), 3)
    sketch.stamp(piece, rim=0.8, occlude=0.55)
    buckle = sketch.piece(trim)
    buckle.rect((pose.pelvis[0] - 1.4, pose.pelvis[1] - 1.4, pose.pelvis[0] + 1.4, pose.pelvis[1] + 0.2), 4)
    sketch.stamp(buckle, rim=0.9, occlude=0.5)
    pouch = sketch.piece(tone)
    side = pose.facing if pose.facing else 1
    pouch.ellipse((pose.pelvis[0] + side * 3.0, pose.pelvis[1] + 0.2,
                   pose.pelvis[0] + side * 6.0, pose.pelvis[1] + 3.6), 2)
    sketch.stamp(pouch, rim=0.6, occlude=0.5)


def _cloak(sketch, pose, item):
    """A cape hangs behind the shoulders. Drawn as wide as the whole body it
    stops being a cloak and becomes a board with a head on top."""
    tone = _armour_ramp(item)
    style = gear.style_of(item)
    build = pose.build
    piece = sketch.piece(tone)
    sway = math.sin(pose.frame / rig.FRAMES * math.tau) * (1.6 if pose.state == 'walk' else 0.5)
    top = pose.shoulder['far'][1] - 1.0
    reach = {'long': 10.0, 'short': 7.5}.get(style['skirt'], 6.0)
    hem = pose.pelvis[1] + (reach if pose.prone < 0.3 else 3.0)
    if pose.side:
        back = -pose.facing
        piece.poly(catmull([
            (pose.chest[0] + back * 1.0, top - 1.0),
            (pose.chest[0] + back * (build.chest_depth + 1.2), top + 2.0),
            (pose.chest[0] + back * (build.chest_depth + 2.4 + abs(sway)), hem - 3.0),
            (pose.chest[0] + back * (build.chest_depth + 0.4) + sway, hem),
            (pose.chest[0] - back * 1.4, hem - 1.5),
            (pose.chest[0] - back * 2.0, top + 1.0),
        ], 5, closed=True), 3)
    else:
        collar = build.shoulder * 0.72
        flare = build.shoulder * 1.06 + style['plume'] * 0.8
        scallop = style['skirt'] == 'long'
        points = [
            (pose.chest[0] - collar, top + 0.6), (pose.chest[0], top - 1.2),
            (pose.chest[0] + collar, top + 0.6),
            (pose.chest[0] + flare + sway * 0.3, hem - 4.0),
            (pose.chest[0] + flare * 0.72 + sway, hem),
        ]
        if scallop:
            points.append((pose.chest[0] + flare * 0.30 + sway, hem - 2.6))
            points.append((pose.chest[0] + sway * 0.6, hem + 0.6))
            points.append((pose.chest[0] - flare * 0.30 + sway * 0.4, hem - 2.6))
        points += [
            (pose.chest[0] - flare * 0.72 + sway * 0.5, hem),
            (pose.chest[0] - flare + sway * 0.3, hem - 4.0),
        ]
        piece.poly(catmull(points, 6, closed=True), 3)
    sketch.carve(piece, rim=0.75, occlude=0.8, form=0.45)
    folds = sketch.piece(tone)
    for sign in (-1, 1):
        folds.line(catmull([(pose.chest[0] + sign * 2.6, top + 3.0),
                            (pose.chest[0] + sign * 3.4, (top + hem) / 2),
                            (pose.chest[0] + sign * 2.2 + sway * 0.5, hem - 1.5)], 5), 1, 1)
    folds.clip(piece)
    sketch.overlay(folds)
    clasp = sketch.piece(_trim_ramp(item))
    clasp.disc(pose.neck[0], pose.neck[1] + 2.0, 1.5, 4)
    sketch.carve(clasp, rim=0.9, occlude=0.5)


def _jewellery(sketch, pose, item, slot):
    """Worn trinkets are small, so the tier shows in the pendant's outline and
    in whether it glows, not in surface detail nobody can see at 64px."""
    tone = _trim_ramp(item)
    style = gear.style_of(item)
    gem = _gem_ramp(item)
    family = style['guard']
    piece = sketch.piece(tone)
    if slot == 'necklace':
        neck = pose.neck
        piece.line(catmull([(neck[0] - 3.2, neck[1] + 2.0), (neck[0], neck[1] + 4.6),
                            (neck[0] + 3.2, neck[1] + 2.0)], 4), 4,
                   2 if family in ('cross', 'shards') else 1)
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
        stone = sketch.piece(gem)
        cx, cy = neck[0], neck[1] + 5.0
        if family in ('shards', 'hooked'):
            stone.poly([(cx, cy - 2.2), (cx + 1.4, cy + 1.4), (cx - 1.4, cy + 1.4)], 3)
        elif family == 'cross':
            stone.poly([(cx - 0.9, cy - 2.2), (cx + 0.9, cy - 2.2), (cx + 0.9, cy - 0.6),
                        (cx + 2.4, cy - 0.6), (cx + 2.4, cy + 0.9), (cx + 0.9, cy + 0.9),
                        (cx + 0.9, cy + 2.6), (cx - 0.9, cy + 2.6), (cx - 0.9, cy + 0.9),
                        (cx - 2.4, cy + 0.9), (cx - 2.4, cy - 0.6), (cx - 0.9, cy - 0.6)], 3)
        elif family == 'wings':
            stone.poly([(cx, cy - 1.8), (cx + 2.8, cy), (cx, cy + 1.8), (cx - 2.8, cy)], 3)
        else:
            stone.disc(cx, cy, 1.6, 4)
        sketch.carve(stone, rim=1.0, occlude=0.5)
        if style['glow']:
            sketch.glow(style['glow'], 2, 0.30)
        return
    if slot == 'ring':
        hand = pose.hand['near']
        piece.dot(hand[0], hand[1], gem[4])
        piece.dot(hand[0] + 0.0, hand[1] - 1.0, tone[5])
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
        return
    anchor = pose.pelvis
    side = -(pose.facing or 1)
    if slot == 'charm':
        piece.line([(anchor[0] + side * 2.2, anchor[1] - 0.6), (anchor[0] + side * 3.0, anchor[1] + 2.6)], 2, 1)
        sketch.stamp(piece, outline=False, rim=0, occlude=0)
        stone = sketch.piece(gem)
        stone.poly([(anchor[0] + side * 3.0, anchor[1] + 2.4), (anchor[0] + side * 4.4, anchor[1] + 4.0),
                    (anchor[0] + side * 3.0, anchor[1] + 5.6), (anchor[0] + side * 1.6, anchor[1] + 4.0)], 4)
        sketch.stamp(stone, rim=0.9, occlude=0.5)
        return
    trinket = sketch.piece(gem)
    tx, ty = anchor[0] + side * 3.4, anchor[1] + 3.2
    if family in ('shards', 'crystal'):
        trinket.poly([(tx, ty - 2.6), (tx + 1.8, ty + 1.4), (tx - 1.8, ty + 1.4)], 3)
    elif family in ('cross', 'wings'):
        trinket.poly([(tx, ty - 2.2), (tx + 2.2, ty), (tx, ty + 2.2), (tx - 2.2, ty)], 3)
    else:
        trinket.disc(tx, ty, 1.9, 3)
    trinket.disc(tx - 0.4, ty - 0.6, 0.9, 5)
    sketch.carve(trinket, rim=0.95, occlude=0.55)
    if style['glow']:
        sketch.glow(style['glow'], 2, 0.28)


def _held(sketch, pose, item, main=True):
    """Weapons and off-hand gear, drawn from the same profiles as the icons."""
    hand = pose.hand['near' if main else 'far']
    angle = pose.grip_angle if main else pose.guard_angle
    smith.hold(sketch, item, hand, angle, pose)


ARMOUR_DRAW = {
    'helmet': _helmet, 'chest': _chest, 'legs': _legs, 'boots': _boots,
    'gloves': _gloves, 'belt': _belt, 'cloak': _cloak,
}


def armour_frame(item, state, frame, direction):
    slot = item.get('slot', '')
    pose = rig.pose(0, state, frame, direction)
    sketch = Sketch(SIZE)
    if slot in ARMOUR_DRAW:
        ARMOUR_DRAW[slot](sketch, pose, item)
    elif slot in ('ring', 'necklace', 'charm', 'trinket'):
        _jewellery(sketch, pose, item, slot)
    elif slot == 'weapon':
        _held(sketch, pose, item, main=True)
    elif slot == 'offhand':
        _held(sketch, pose, item, main=False)
    return finish(sketch, pose)


# -------------------------------------------------------------------- npcs --

# Draw order per facing, matching the client's SpritePoseRules.
LAYER_ORDER = (
    ('cloak', 'body', 'legs', 'boots', 'chest', 'belt', 'hair', 'helmet', 'necklace',
     'charm', 'trinket', 'offhand', 'weapon', 'gloves', 'ring'),
    ('cloak', 'weapon', 'body', 'legs', 'boots', 'chest', 'belt', 'hair', 'helmet',
     'necklace', 'charm', 'trinket', 'offhand', 'gloves', 'ring'),
    ('cloak', 'offhand', 'body', 'legs', 'boots', 'chest', 'belt', 'hair', 'helmet',
     'necklace', 'charm', 'trinket', 'weapon', 'gloves', 'ring'),
    ('weapon', 'offhand', 'body', 'legs', 'boots', 'chest', 'belt', 'cloak', 'hair',
     'helmet', 'necklace', 'charm', 'trinket', 'gloves', 'ring'),
)


def dress(equipment, state, frame, direction, build=0, skin=2, hair=2, hair_colour=1):
    """Compose a fully equipped character frame in the client's layer order.

    `equipment` maps slot name to an item record. Layer order matters: a cloak
    drawn on top of the body hides the body.
    """
    frame_image = Sketch(SIZE).result()
    for layer in LAYER_ORDER[max(0, min(3, direction))]:
        if layer == 'body':
            frame_image.alpha_composite(body_frame(build, skin, state, frame, direction))
        elif layer == 'hair':
            frame_image.alpha_composite(hair_frame(hair, hair_colour, state, frame, direction))
        else:
            item = equipment.get(layer)
            if item is not None:
                frame_image.alpha_composite(armour_frame(item, state, frame, direction))
    return frame_image


ROLE_LOOK = {
    'alchemist': ('#5d7a6e', '#c8b58a', 4, 5, 'flask'),
    'armorer': ('#6a6f78', '#8d5f3c', 0, 0, 'hammer'),
    'auctioneer': ('#7c5f8a', '#c9a86a', 1, 3, 'ledger'),
    'banker': ('#4f5a72', '#b9a05e', 0, 6, 'ledger'),
    'blacksmith': ('#6d5340', '#8a5f3c', 0, 0, 'hammer'),
    'carpenter': ('#8a6a49', '#9c7b3e', 1, 1, 'saw'),
    'enchanter': ('#6f5f96', '#a98fd0', 4, 5, 'staff'),
    'ferryman': ('#4a6b74', '#8a7550', 2, 6, 'pole'),
    'fisher': ('#4f7382', '#b9b1a0', 2, 1, 'rod'),
    'fletcher': ('#5f7350', '#8d6942', 1, 2, 'bow'),
    'guard': ('#5a6474', '#8a8f96', 0, 0, 'spear'),
    'guild_registrar': ('#6b6076', '#c8bda2', 3, 6, 'ledger'),
    'herbalist': ('#5d7a4e', '#a3946a', 4, 2, 'herb'),
    'innkeeper': ('#8a6a52', '#c69a5f', 3, 1, 'mug'),
    'jeweler': ('#7a6a8c', '#d0a63f', 5, 4, 'gem'),
    'miner': ('#6a5f52', '#7d858d', 0, 0, 'pick'),
    'provisioner': ('#7c6a4e', '#c08a52', 1, 2, 'crate'),
    'rune_merchant': ('#5f5a80', '#7b6f96', 3, 0, 'rune'),
    'scholar': ('#565f7c', '#c8bda2', 5, 6, 'book'),
    'scribe': ('#5f6684', '#d3c7a6', 3, 5, 'scroll'),
    'tailor': ('#7a5f74', '#c2b8d6', 1, 3, 'shears'),
    'tanner': ('#7a5a40', '#8a5f3c', 0, 1, 'knife'),
    'trainer': ('#6a5f4a', '#8a8f96', 0, 0, 'sword'),
    'traveler': ('#5f6b5a', '#8a7550', 2, 2, 'pack'),
    'weaponsmith': ('#6a6470', '#a9b6c0', 0, 0, 'sword'),
    'woodworker': ('#7a6647', '#8d6942', 1, 1, 'axe'),
}


def _npc_tool(sketch, pose, kind, accent):
    hand = pose.hand['near']
    tone = ramp(accent)
    wood = ramp('#8a6a49')
    piece = sketch.piece(tone)
    if kind in ('hammer', 'pick', 'axe'):
        head = (hand[0] + 1.0, hand[1] - 9.0)
        shaft = sketch.piece(wood)
        shaft.poly(taper_shape((hand[0] - 0.6, hand[1] + 3.0), head, 2.2, 1.9), 3)
        sketch.stamp(shaft, rim=0.7, occlude=0.5)
        if kind == 'hammer':
            piece.rect((head[0] - 3.2, head[1] - 2.2, head[0] + 3.2, head[1] + 1.8), 3)
            piece.rect((head[0] + 1.6, head[1] - 1.8, head[0] + 3.4, head[1] + 1.4), 4)
        elif kind == 'pick':
            piece.poly(catmull([(head[0] - 5.0, head[1] + 1.4), (head[0], head[1] - 2.0),
                                (head[0] + 5.0, head[1] + 1.4), (head[0], head[1] + 0.6)], 5, closed=True), 3)
        else:
            piece.poly(catmull([(head[0] - 0.4, head[1] - 2.4), (head[0] + 4.4, head[1] - 0.6),
                                (head[0] + 4.0, head[1] + 3.0), (head[0] - 0.4, head[1] + 3.4)], 5, closed=True), 3)
    elif kind in ('spear', 'pole', 'staff', 'rod'):
        top = (hand[0] + 0.4, hand[1] - 16.0)
        shaft = sketch.piece(wood)
        shaft.poly(taper_shape((hand[0] - 0.8, hand[1] + 6.0), top, 2.0, 1.7), 3)
        sketch.stamp(shaft, rim=0.7, occlude=0.5)
        if kind == 'spear':
            piece.poly([(top[0], top[1] - 4.6), (top[0] + 1.9, top[1] + 0.4), (top[0], top[1] + 2.2), (top[0] - 1.9, top[1] + 0.4)], 4)
        elif kind == 'staff':
            piece.disc(top[0], top[1] - 1.4, 2.4, 4)
        elif kind == 'rod':
            piece.line([(top[0], top[1]), (top[0] + 4.0, top[1] + 4.0)], 2, 1)
    elif kind == 'bow':
        piece.line(catmull([(hand[0] + 1.0, hand[1] - 9.0), (hand[0] + 4.2, hand[1] - 1.0), (hand[0] + 1.0, hand[1] + 7.0)], 6), 3, 2)
        piece.line([(hand[0] + 1.0, hand[1] - 9.0), (hand[0] + 1.0, hand[1] + 7.0)], 5, 1)
    elif kind in ('book', 'ledger', 'scroll'):
        piece.rect((hand[0] - 3.4, hand[1] - 3.2, hand[0] + 3.4, hand[1] + 1.6), 3)
        piece.rect((hand[0] - 2.6, hand[1] - 2.4, hand[0] + 3.0, hand[1] + 0.8), 5)
    elif kind in ('flask', 'mug'):
        piece.poly(catmull([(hand[0] - 2.0, hand[1] - 3.4), (hand[0] + 2.0, hand[1] - 3.4),
                            (hand[0] + 2.6, hand[1] + 1.6), (hand[0] - 2.6, hand[1] + 1.6)], 4, closed=True), 3)
        piece.rect((hand[0] - 1.0, hand[1] - 5.0, hand[0] + 1.0, hand[1] - 3.0), 2)
    elif kind in ('gem', 'rune'):
        piece.poly([(hand[0], hand[1] - 3.4), (hand[0] + 2.6, hand[1] - 0.4), (hand[0], hand[1] + 2.6), (hand[0] - 2.6, hand[1] - 0.4)], 3)
        piece.dot(hand[0] - 0.6, hand[1] - 1.2, 5)
    elif kind in ('shears', 'knife', 'saw', 'sword'):
        piece.poly(taper_shape((hand[0] - 0.6, hand[1] + 1.0), (hand[0] + 3.0, hand[1] - 9.0), 3.0, 1.4), 3)
        guard = sketch.piece(ramp('#6f6a62'))
        guard.line([(hand[0] - 2.4, hand[1] - 0.4), (hand[0] + 2.0, hand[1] - 1.4)], 3, 2)
        sketch.stamp(guard, rim=0.6, occlude=0.4)
    elif kind in ('crate', 'pack'):
        piece.rect((hand[0] - 3.4, hand[1] - 3.0, hand[0] + 3.4, hand[1] + 2.4), 3)
        piece.line([(hand[0] - 3.4, hand[1] - 0.4), (hand[0] + 3.4, hand[1] - 0.4)], 1, 1)
    else:
        piece.disc(hand[0], hand[1] - 1.0, 2.2, 3)
    sketch.stamp(piece, rim=0.85, occlude=0.55)


def npc_frame(role, state, frame, direction):
    look = ROLE_LOOK.get(role, ('#6a6a72', '#9a8f7a', 1, 1, 'pack'))
    coat, accent, hair_style, hair_colour, tool = look
    build = pigment.keyed(role, 2)
    skin = pigment.keyed(role + 'skin', 6)
    pose = rig.pose(build, state, frame, direction)
    sketch = Sketch(SIZE)
    body_layers(sketch, pose, skin, cloth=coat,
                trunk=blend(pigment.rgb(coat), (30, 26, 32, 255), 0.35), shoe='#4a3a2e')
    hair = hair_frame(hair_style, hair_colour, state, frame, direction)
    sketch.overlay(hair)
    apron = sketch.piece(ramp(accent))
    apron.poly(torso_shape(pose, expand=0.2, drop=1.6), 3)
    apron.erase_ellipse((pose.chest[0] - 9, pose.chest[1] - 12, pose.chest[0] + 9, pose.chest[1] - 2))
    sketch.stamp(apron, rim=0.6, occlude=0.5)
    if pose.prone < 0.3:
        _npc_tool(sketch, pose, tool, accent)
    return finish(sketch, pose)
