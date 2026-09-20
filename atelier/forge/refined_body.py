"""Refined 64 px humanoid base-body renderer.

This renderer keeps the shared Atelier humanoid rig. It changes only the base
body drawing. Hair, armour, held equipment, collision, animation order, and the
64 px foot anchor remain unchanged.

Version 2 pushes the base toward grounded fantasy pixel art: more anatomical
limbs, clearer joints, shaped boots and hands, a constructed tunic, and small
state-aware facial expressions. All marks are drawn as hard-edged pixel
clusters from the existing rig joints; completed sprites are never resampled.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

from . import pigment, rig

SIZE = 64
INK = (28, 24, 32, 255)
DEEP_INK = (21, 19, 25, 255)
EYE = (34, 29, 31, 255)
EYE_LIGHT = (224, 210, 181, 255)
CLOTH = '#79634e'
TROUSER = '#544c43'
SHOE = '#433429'
BELT = '#513a28'
STITCH = (185, 151, 101, 255)


def _pt(point):
    return int(round(point[0])), int(round(point[1]))


def _points(values):
    return [_pt(value) for value in values]


def _axis(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length


def _point(a, b, amount):
    return a[0] + (b[0] - a[0]) * amount, a[1] + (b[1] - a[1]) * amount


def _normal(a, b):
    ux, uy = _axis(a, b)
    return -uy, ux


def _tapered(a, b, width_a, width_b):
    px, py = _normal(a, b)
    return [
        (a[0] + px * width_a / 2, a[1] + py * width_a / 2),
        (b[0] + px * width_b / 2, b[1] + py * width_b / 2),
        (b[0] - px * width_b / 2, b[1] - py * width_b / 2),
        (a[0] - px * width_a / 2, a[1] - py * width_a / 2),
    ]


def _poly(draw, values, fill, outline=INK):
    points = _points(values)
    draw.polygon(points, fill=fill)
    if outline:
        draw.line(points + [points[0]], fill=outline, width=1)


def _line(draw, values, fill, width=1):
    draw.line(_points(values), fill=fill, width=width)


def _ellipse(draw, box, fill, outline=INK):
    box = tuple(int(round(value)) for value in box)
    draw.ellipse(box, fill=fill, outline=outline, width=1)


def _pixel(draw, point, fill):
    draw.point(_pt(point), fill=fill)


def _segment(draw, a, b, width_a, width_b, colours, depth=1.0, joint=False):
    """Draw one faceted limb segment with one lit and one shaded edge."""
    width_a *= depth
    width_b *= depth
    _poly(draw, _tapered(a, b, width_a, width_b), colours[2])
    ux, uy = _axis(a, b)
    px, py = -uy, ux
    inset = 0.22
    _line(draw, [
        (a[0] + px * width_a * inset - 0.5, a[1] + py * width_a * inset - 0.5),
        (b[0] + px * width_b * inset - 0.5, b[1] + py * width_b * inset - 0.5),
    ], colours[4])
    _line(draw, [
        (a[0] - px * width_a * 0.27 + 0.5, a[1] - py * width_a * 0.27 + 0.5),
        (b[0] - px * width_b * 0.27 + 0.5, b[1] - py * width_b * 0.27 + 0.5),
    ], colours[1])
    if joint:
        _ellipse(draw, (b[0] - width_b * 0.34, b[1] - width_b * 0.30,
                        b[0] + width_b * 0.34, b[1] + width_b * 0.30), colours[3], None)
        _pixel(draw, (b[0] - 1, b[1] - 1), colours[5])


def _hand(draw, hand, forearm, colours, near):
    """Compact mitten silhouette with thumb, knuckle light, and finger split."""
    ux, uy = _axis(forearm, hand)
    px, py = -uy, ux
    length = 3.15 if near else 2.8
    width = 2.7 if near else 2.35
    wrist = (hand[0] - ux * 1.15, hand[1] - uy * 1.15)
    tip = (hand[0] + ux * length, hand[1] + uy * length)
    shape = [
        (wrist[0] + px * width * 0.50, wrist[1] + py * width * 0.50),
        (tip[0] + px * width * 0.28, tip[1] + py * width * 0.28),
        (tip[0] + ux * 0.55, tip[1] + uy * 0.55),
        (tip[0] - px * width * 0.34, tip[1] - py * width * 0.34),
        (wrist[0] - px * width * 0.48, wrist[1] - py * width * 0.48),
    ]
    _poly(draw, shape, colours[3])
    thumb = (hand[0] + px * (1.25 if near else 1.05), hand[1] + py * (1.25 if near else 1.05))
    _ellipse(draw, (thumb[0] - 1, thumb[1] - 1, thumb[0] + 1, thumb[1] + 1), colours[2], None)
    knuckle = (hand[0] + ux * 0.5 - 1, hand[1] + uy * 0.5 - 1)
    _pixel(draw, knuckle, colours[5])
    split_a = _point(hand, tip, 0.62)
    split_b = (split_a[0] - px * 0.7, split_a[1] - py * 0.7)
    _line(draw, [split_a, split_b], colours[1])


def _foot_shape(pose, key):
    knee, foot = pose.knee[key], pose.foot[key]
    ux, uy = _axis(knee, foot)
    if pose.side:
        toe_sign = pose.facing or 1
    elif pose.back:
        toe_sign = -1 if key == 'far' else 1
    else:
        toe_sign = -1 if key == 'far' else 1
    px, py = uy * toe_sign, -ux * toe_sign
    ankle = (foot[0] - ux * 3.0, foot[1] - uy * 3.0)
    sole = (foot[0] + ux * 0.25, foot[1] + uy * 0.25)
    return [
        (ankle[0] - px * 1.65, ankle[1] - py * 1.65),
        (ankle[0] + px * 1.45, ankle[1] + py * 1.45),
        (sole[0] + px * 4.0, sole[1] + py * 4.0),
        (sole[0] + px * 3.3, sole[1] + py * 3.3),
        (sole[0] + px * 1.0, sole[1] + py * 1.0),
        (sole[0] - px * 2.1, sole[1] - py * 2.1),
    ]


def _draw_boot(draw, pose, key, colours, near):
    shape = _foot_shape(pose, key)
    _poly(draw, shape, colours[2])
    xs = [point[0] for point in shape]
    ys = [point[1] for point in shape]
    sole_y = max(ys) - 1
    _line(draw, [(min(xs) + 1, sole_y), (max(xs) - 1, sole_y)], colours[0])
    top = min(shape, key=lambda value: value[1])
    _line(draw, [(top[0] - 1.4, top[1] + 1), (top[0] + 1.4, top[1] + 1)], colours[4])
    if near:
        heel = min(shape, key=lambda value: value[0] if pose.facing >= 0 else -value[0])
        _pixel(draw, (heel[0], heel[1] - 1), colours[1])


def _draw_leg(draw, pose, key, trouser, boot, near):
    """Shape the thigh, knee and calf separately instead of one tube."""
    build = pose.build
    depth = 1.0 if near else 0.89
    hip, knee = pose.hip[key], pose.knee[key]
    foot = pose.foot[key][0], pose.foot[key][1] - 1.7
    thigh_end = _point(hip, knee, 0.84)
    calf_start = _point(knee, foot, 0.10)
    boot_top = _point(knee, foot, 0.62)
    _segment(draw, hip, thigh_end, build.thigh * 1.08, build.thigh * 0.78, trouser, depth)
    _segment(draw, thigh_end, knee, build.thigh * 0.80, build.thigh * 0.67, trouser, depth, joint=True)
    _segment(draw, calf_start, boot_top, build.thigh * 0.69, build.thigh * 0.54, trouser, depth)
    _segment(draw, boot_top, foot, build.thigh * 0.61, build.thigh * 0.49, boot, depth)
    px, py = _normal(hip, knee)
    crease = (
        (knee[0] - px * build.thigh * 0.28, knee[1] - py * build.thigh * 0.28),
        (knee[0] + px * build.thigh * 0.20, knee[1] + py * build.thigh * 0.20),
    )
    _line(draw, crease, trouser[0])
    _draw_boot(draw, pose, key, boot, near)


def _draw_arm(draw, pose, key, skin, cloth, near):
    """Use a shoulder cap, sleeve, elbow and narrower forearm for anatomy."""
    build = pose.build
    depth = 1.0 if near else 0.87
    shoulder, elbow, hand = pose.shoulder[key], pose.elbow[key], pose.hand[key]
    sleeve_end = _point(shoulder, elbow, 0.58)
    _ellipse(draw, (shoulder[0] - build.limb * 0.65 * depth,
                    shoulder[1] - build.limb * 0.55 * depth,
                    shoulder[0] + build.limb * 0.65 * depth,
                    shoulder[1] + build.limb * 0.55 * depth), cloth[3], INK)
    _segment(draw, shoulder, sleeve_end, build.limb * 1.20, build.limb * 1.04, cloth, depth)
    _line(draw, [(sleeve_end[0] - 1.5, sleeve_end[1]), (sleeve_end[0] + 1.5, sleeve_end[1])], cloth[0])
    _segment(draw, sleeve_end, elbow, build.limb * 0.88, build.limb * 0.74, skin, depth, joint=True)
    _segment(draw, elbow, hand, build.limb * 0.72, build.limb * 0.56, skin, depth)
    _hand(draw, hand, elbow, skin, near)


def _torso_polygon(pose):
    build = pose.build
    chest, pelvis = pose.chest, pose.pelvis
    ux, uy = _axis(pelvis, chest)
    px, py = -uy, ux
    broad = build.shoulder >= 7.0
    half_top = build.chest_depth if pose.side else build.shoulder * (0.93 if broad else 0.91)
    half_rib = build.chest_depth * 0.96 if pose.side else build.shoulder * (0.79 if broad else 0.76)
    half_waist = build.chest_depth * 0.76 if pose.side else build.hip * (0.96 if broad else 0.90)
    half_hip = build.chest_depth * 0.83 if pose.side else build.hip + (0.9 if broad else 1.05)
    neck = (pose.neck[0] + ux * 0.65, pose.neck[1] + uy * 0.65)
    ribs = _point(chest, pelvis, 0.42)
    waist = _point(chest, pelvis, 0.72)
    bottom = (pelvis[0] - ux * 1.0, pelvis[1] - uy * 1.0)
    return [
        (neck[0] - px * half_top * 0.61, neck[1] - py * half_top * 0.61),
        (chest[0] - px * half_top, chest[1] - py * half_top),
        (ribs[0] - px * half_rib, ribs[1] - py * half_rib),
        (waist[0] - px * half_waist, waist[1] - py * half_waist),
        (bottom[0] - px * half_hip, bottom[1] - py * half_hip),
        (bottom[0] + px * half_hip, bottom[1] + py * half_hip),
        (waist[0] + px * half_waist, waist[1] + py * half_waist),
        (ribs[0] + px * half_rib, ribs[1] + py * half_rib),
        (chest[0] + px * half_top, chest[1] + py * half_top),
        (neck[0] + px * half_top * 0.61, neck[1] + py * half_top * 0.61),
    ]


def _draw_torso(draw, pose, skin, cloth, belt):
    """Draw a belted short tunic with readable seams, folds, and hem."""
    _poly(draw, _torso_polygon(pose), cloth[2])
    build = pose.build
    chest, pelvis = pose.chest, pose.pelvis
    ux, uy = _axis(pelvis, chest)
    px, py = -uy, ux
    light_width = build.chest_depth * 0.50 if pose.side else build.shoulder * 0.68
    shade_width = build.chest_depth * 0.54 if pose.side else build.shoulder * 0.58
    _line(draw, [
        (chest[0] - px * light_width - 1, chest[1] - py * light_width - 1),
        (_point(chest, pelvis, 0.46)[0] - 1, _point(chest, pelvis, 0.46)[1] - 1),
    ], cloth[4])
    _line(draw, [
        (pelvis[0] + px * (build.hip + 0.2) + 1, pelvis[1] + py * (build.hip + 0.2) + 1),
        (chest[0] + px * shade_width + 1, chest[1] + py * shade_width + 1),
    ], cloth[1])

    collar = (pose.neck[0] - ux * 1.0, pose.neck[1] - uy * 1.0)
    collar_width = 2.2 if pose.side else 3.0
    _line(draw, [
        (collar[0] - px * collar_width, collar[1] - py * collar_width),
        (collar[0], collar[1] + uy * 2.0),
        (collar[0] + px * collar_width, collar[1] + py * collar_width),
    ], cloth[0])
    neck_a = _point(pose.chest, pose.neck, 0.80)
    neck_b = _point(pose.neck, pose.head, 0.28)
    _segment(draw, neck_a, neck_b, 4.0, 3.6, skin)

    if not pose.back:
        centre_a = _point(chest, pelvis, 0.18)
        centre_b = _point(chest, pelvis, 0.55)
        _line(draw, [centre_a, centre_b], cloth[1])
        if not pose.side:
            for amount in (0.27, 0.39, 0.51):
                stitch = _point(chest, pelvis, amount)
                _line(draw, [(stitch[0] - 1, stitch[1]), (stitch[0] + 1, stitch[1])], STITCH)
    else:
        seam_a = _point(chest, pelvis, 0.34)
        seam_b = _point(chest, pelvis, 0.70)
        _line(draw, [(seam_a[0] + px * 2.0, seam_a[1] + py * 2.0),
                     (seam_b[0] + px * 1.8, seam_b[1] + py * 1.8)], cloth[0])

    waist = _point(chest, pelvis, 0.81)
    belt_width = build.chest_depth * 0.84 if pose.side else build.hip + 1.1
    _line(draw, [
        (waist[0] - px * belt_width, waist[1] - py * belt_width),
        (waist[0] + px * belt_width, waist[1] + py * belt_width),
    ], belt[1], 2)
    if not pose.side:
        _ellipse(draw, (waist[0] - 1.5, waist[1] - 1.3, waist[0] + 1.5, waist[1] + 1.3), belt[4], belt[0])
        _pixel(draw, (waist[0], waist[1]), belt[1])

    hem = _point(chest, pelvis, 0.96)
    hem_width = build.chest_depth * 0.74 if pose.side else build.hip * 0.92
    _line(draw, [(hem[0] - px * hem_width, hem[1] - py * hem_width),
                 (hem[0] + px * hem_width, hem[1] + py * hem_width)], cloth[0])
    if not pose.side:
        _line(draw, [(hem[0] - 1, hem[1]), (hem[0], hem[1] + 1), (hem[0] + 1, hem[1])], cloth[1])


def _rotate(point, centre, angle):
    cosine, sine = math.cos(angle), math.sin(angle)
    x, y = point
    cx, cy = centre
    return cx + (x - cx) * cosine - (y - cy) * sine, cy + (x - cx) * sine + (y - cy) * cosine


def _face_basis(pose):
    down = math.sin(pose.head_tilt), math.cos(pose.head_tilt)
    across = math.cos(pose.head_tilt), -math.sin(pose.head_tilt)
    x, y = pose.head

    def at(side, lower):
        return x + across[0] * side + down[0] * lower, y + across[1] * side + down[1] * lower

    return at


def _draw_expression(draw, pose, skin):
    """Small readable expression changes without changing head geometry."""
    at = _face_basis(pose)
    state = pose.state
    if pose.side:
        facing = pose.facing or 1
        eye = at(facing * 2.1, -0.6)
        _pixel(draw, eye, EYE)
        if state not in ('hit', 'death'):
            _pixel(draw, (eye[0] - facing * 0.2, eye[1] - 1), EYE_LIGHT)
        brow_drop = 0.7 if state in ('attack', 'hit') else 0.0
        _line(draw, [at(facing * 0.8, -2.0 + brow_drop), at(facing * 2.8, -1.8 + brow_drop)], skin[0])
        mouth_y = 3.0
        if state == 'attack':
            _line(draw, [at(facing * 1.0, mouth_y), at(facing * 2.8, mouth_y - 0.5)], DEEP_INK)
        elif state == 'hit':
            _line(draw, [at(facing * 1.1, mouth_y - 0.2), at(facing * 2.4, mouth_y + 0.7)], DEEP_INK)
        elif state == 'death':
            _line(draw, [at(facing * 1.3, -0.5), at(facing * 2.7, -0.1)], DEEP_INK)
        else:
            _line(draw, [at(facing * 1.2, mouth_y), at(facing * 2.6, mouth_y)], skin[0])
        return

    for facing in (-1, 1):
        eye = at(facing * 1.9, -0.55)
        if state == 'death':
            _line(draw, [at(facing * 1.2, -0.5), at(facing * 2.7, -0.1)], DEEP_INK)
        elif state == 'hit':
            _line(draw, [at(facing * 1.2, -0.3), at(facing * 2.6, 0.2)], EYE)
        else:
            _pixel(draw, eye, EYE)
            _pixel(draw, at(facing * 1.8, -1.2), EYE_LIGHT)
        brow_inner = -1.45 + (0.55 if state in ('attack', 'hit') else 0.0)
        brow_outer = -1.8 + (0.25 if state == 'cast' else 0.0)
        _line(draw, [at(facing * 0.9, brow_inner), at(facing * 2.8, brow_outer)], skin[0])

    _line(draw, [at(-0.15, 0.1), at(0.25, 1.9)], skin[1])
    _pixel(draw, at(0.75, 2.0), skin[0])
    if state == 'attack':
        _line(draw, [at(-1.6, 3.25), at(0.0, 3.7), at(1.8, 3.1)], DEEP_INK)
    elif state == 'hit':
        _line(draw, [at(-1.5, 3.6), at(0.0, 3.0), at(1.6, 3.7)], DEEP_INK)
    elif state == 'death':
        _line(draw, [at(-1.4, 3.55), at(1.4, 3.55)], skin[0])
    else:
        _line(draw, [at(-1.4, 3.45), at(1.4, 3.45)], skin[0])
        if state == 'idle' and pose.frame in (2, 3):
            _pixel(draw, at(0.0, 4.35), skin[1])


def _draw_head(draw, pose, skin):
    """More human head: flatter cranium, temples, jaw corners, and chin."""
    x, y = pose.head
    radius = pose.head_r
    angle = -pose.head_tilt
    side = pose.side
    if side:
        facing = pose.facing or 1
        shape = [
            (x - facing * radius * 0.78, y - radius * 0.91),
            (x + facing * radius * 0.38, y - radius * 1.00),
            (x + facing * radius * 0.82, y - radius * 0.64),
            (x + facing * radius * 0.98, y - radius * 0.12),
            (x + facing * radius * 0.86, y + radius * 0.46),
            (x + facing * radius * 0.52, y + radius * 0.88),
            (x + facing * radius * 0.12, y + radius * 1.05),
            (x - facing * radius * 0.43, y + radius * 0.76),
            (x - facing * radius * 0.72, y + radius * 0.20),
            (x - facing * radius * 0.80, y - radius * 0.42),
        ]
    else:
        shape = [
            (x - radius * 0.66, y - radius * 0.97),
            (x + radius * 0.66, y - radius * 0.97),
            (x + radius * 0.90, y - radius * 0.60),
            (x + radius * 0.94, y + radius * 0.16),
            (x + radius * 0.68, y + radius * 0.66),
            (x + radius * 0.38, y + radius * 0.90),
            (x + radius * 0.18, y + radius * 1.04),
            (x - radius * 0.18, y + radius * 1.04),
            (x - radius * 0.38, y + radius * 0.90),
            (x - radius * 0.68, y + radius * 0.66),
            (x - radius * 0.94, y + radius * 0.16),
            (x - radius * 0.90, y - radius * 0.60),
        ]
    rotated = [_rotate(value, pose.head, angle) for value in shape]
    _poly(draw, rotated, skin[3])

    light = [
        (x - radius * 0.58, y - radius * 0.72),
        (x - radius * 0.18, y - radius * 0.88),
        (x + radius * 0.18, y - radius * 0.78),
        (x - radius * 0.30, y - radius * 0.30),
    ]
    _poly(draw, [_rotate(value, pose.head, angle) for value in light], skin[5], None)
    shadow = [
        (x + radius * 0.42, y + radius * 0.10),
        (x + radius * 0.68, y + radius * 0.40),
        (x + radius * 0.30, y + radius * 0.82),
        (x - radius * 0.04, y + radius * 0.92),
    ]
    _poly(draw, [_rotate(value, pose.head, angle) for value in shadow], skin[2], None)

    if pose.back:
        ear_y = y + 0.4
        _ellipse(draw, (x - radius - 1, ear_y - 1, x - radius + 1, ear_y + 2), skin[2])
        _ellipse(draw, (x + radius - 1, ear_y - 1, x + radius + 1, ear_y + 2), skin[2])
        _line(draw, [(x - 2, y + radius * 0.7), (x + 2, y + radius * 0.7)], skin[1])
        return

    at = _face_basis(pose)
    if pose.side:
        facing = pose.facing or 1
        ear = at(-facing * radius * 0.58, 0.35)
        _ellipse(draw, (ear[0] - 1, ear[1] - 1, ear[0] + 1, ear[1] + 2), skin[2])
        _poly(draw, [at(facing * (radius - 0.65), -0.25),
                     at(facing * (radius + 1.35), 0.95),
                     at(facing * (radius - 0.35), 1.55)], skin[3])
    else:
        for facing in (-1, 1):
            ear = at(facing * radius * 0.91, 0.55)
            _ellipse(draw, (ear[0] - 1, ear[1] - 1, ear[0] + 1, ear[1] + 2), skin[2])
    _draw_expression(draw, pose, skin)


def body_frame(build, skin_index, state, frame, direction):
    """Draw one refined body frame on the existing shared rig."""
    pose = rig.pose(build, state, frame, direction)
    image = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    skin = pigment.ramp(pigment.SKIN[max(0, min(5, skin_index))])
    cloth = pigment.ramp(CLOTH)
    trouser = pigment.ramp(TROUSER)
    boot = pigment.ramp(SHOE)
    belt = pigment.ramp(BELT)

    raised = {key: pose.hand[key][1] < pose.shoulder[key][1] - 1.5 for key in ('far', 'near')}
    if not raised['far']:
        _draw_arm(draw, pose, 'far', skin, cloth, False)
    _draw_leg(draw, pose, 'far', trouser, boot, False)
    _draw_torso(draw, pose, skin, cloth, belt)
    _draw_leg(draw, pose, 'near', trouser, boot, True)
    if not raised['near']:
        _draw_arm(draw, pose, 'near', skin, cloth, True)
    _draw_head(draw, pose, skin)
    for key in ('far', 'near'):
        if raised[key]:
            _draw_arm(draw, pose, key, skin, cloth, key == 'near')

    if pose.flash:
        pixels = image.load()
        weight = 0.25 * pose.flash
        for y in range(SIZE):
            for x in range(SIZE):
                red, green, blue, alpha = pixels[x, y]
                if alpha:
                    pixels[x, y] = (
                        round(red * (1 - weight) + 255 * weight),
                        round(green * (1 - weight) + 236 * weight),
                        round(blue * (1 - weight) + 206 * weight),
                        alpha,
                    )
    if pose.fade < 1.0:
        image.putalpha(image.getchannel('A').point(lambda alpha: round(alpha * pose.fade)))
    return image
