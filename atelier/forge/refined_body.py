"""Refined 64 px humanoid base-body renderer.

This renderer keeps the shared Atelier humanoid rig. It changes only the base
body drawing. Hair, armour, held equipment, collision, animation order, and the
64 px foot anchor remain unchanged.

The renderer uses deliberate hard-edged pixel clusters. It does not rotate or
resample completed sprites. Each frame is drawn from the current rig joints.
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

from . import pigment, rig

SIZE = 64
INK = (28, 24, 32, 255)
CLOTH = '#7c6a58'
TROUSER = '#5d5347'
SHOE = '#4a3a2e'
BELT = '#4d3b2d'


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


def _tapered(a, b, width_a, width_b):
    ux, uy = _axis(a, b)
    px, py = -uy, ux
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
        draw.line(points + [points[0]], fill=outline, width=1, joint='curve')


def _line(draw, values, fill, width=1):
    draw.line(_points(values), fill=fill, width=width)


def _ellipse(draw, box, fill, outline=INK):
    box = tuple(int(round(value)) for value in box)
    draw.ellipse(box, fill=fill, outline=outline, width=1)


def _segment(draw, a, b, width_a, width_b, colours, depth=1.0):
    width_a *= depth
    width_b *= depth
    _poly(draw, _tapered(a, b, width_a, width_b), colours[2])
    ux, uy = _axis(a, b)
    px, py = -uy, ux
    _line(draw, [
        (a[0] + px * width_a * 0.22 + 1, a[1] + py * width_a * 0.22 + 1),
        (b[0] + px * width_b * 0.22 + 1, b[1] + py * width_b * 0.22 + 1),
    ], colours[1])
    _line(draw, [
        (a[0] - px * width_a * 0.25 - 1, a[1] - py * width_a * 0.25 - 1),
        (b[0] - px * width_b * 0.25 - 1, b[1] - py * width_b * 0.25 - 1),
    ], colours[4])


def _hand(draw, hand, forearm, colours, near):
    ux, uy = _axis(forearm, hand)
    px, py = -uy, ux
    length = 3.0 if near else 2.6
    width = 2.5 if near else 2.2
    shape = [
        (hand[0] - ux * 1.2 + px * width / 2, hand[1] - uy * 1.2 + py * width / 2),
        (hand[0] + ux * length + px * 0.8, hand[1] + uy * length + py * 0.8),
        (hand[0] + ux * (length + 0.8), hand[1] + uy * (length + 0.8)),
        (hand[0] + ux * length - px * 0.8, hand[1] + uy * length - py * 0.8),
        (hand[0] - ux * 1.2 - px * width / 2, hand[1] - uy * 1.2 - py * width / 2),
    ]
    _poly(draw, shape, colours[3])
    _line(draw, [(hand[0] - 1, hand[1] - 1), (hand[0] + 1, hand[1] - 1)], colours[5])
    thumb = hand[0] + px, hand[1] + py
    _ellipse(draw, (thumb[0] - 1, thumb[1] - 1, thumb[0] + 1, thumb[1] + 1), colours[2], None)


def _foot_shape(pose, key):
    knee, foot = pose.knee[key], pose.foot[key]
    ux, uy = _axis(knee, foot)
    if pose.side:
        toe = pose.facing or 1
    elif pose.back:
        toe = -1 if key == 'far' else 1
    else:
        toe = -1 if key == 'far' else 1
    px, py = uy * toe, -ux * toe
    ankle = foot[0] - ux * 2.5, foot[1] - uy * 2.5
    sole = foot[0] + ux * 0.2, foot[1] + uy * 0.2
    return [
        (ankle[0] - px * 1.8, ankle[1] - py * 1.8),
        (ankle[0] + px * 1.5, ankle[1] + py * 1.5),
        (sole[0] + px * 3.7, sole[1] + py * 3.7),
        (sole[0] + px * 2.6, sole[1] + py * 2.6),
        (sole[0] - px * 2.2, sole[1] - py * 2.2),
    ]


def _draw_boot(draw, pose, key, colours):
    shape = _foot_shape(pose, key)
    _poly(draw, shape, colours[2])
    xs = [point[0] for point in shape]
    ys = [point[1] for point in shape]
    y = max(ys) - 1
    _line(draw, [(min(xs) + 1, y), (max(xs) - 1, y)], colours[0])
    top = min(shape, key=lambda value: value[1])
    _line(draw, [(top[0] - 1, top[1]), (top[0] + 1, top[1])], colours[4])


def _draw_leg(draw, pose, key, trouser, boot, near):
    build = pose.build
    depth = 1.0 if near else 0.90
    hip, knee = pose.hip[key], pose.knee[key]
    foot = pose.foot[key][0], pose.foot[key][1] - 1.7
    _segment(draw, hip, knee, build.thigh * 1.04, build.thigh * 0.82, trouser, depth)
    _segment(draw, knee, foot, build.thigh * 0.80, build.thigh * 0.56, trouser, depth)
    ux, uy = _axis(hip, knee)
    px, py = -uy, ux
    _line(draw, [
        (knee[0] - px * build.thigh * 0.32, knee[1] - py * build.thigh * 0.32),
        (knee[0] + px * build.thigh * 0.32, knee[1] + py * build.thigh * 0.32),
    ], trouser[0])
    _draw_boot(draw, pose, key, boot)


def _draw_arm(draw, pose, key, skin, cloth, near):
    build = pose.build
    depth = 1.0 if near else 0.88
    shoulder, elbow, hand = pose.shoulder[key], pose.elbow[key], pose.hand[key]
    sleeve_end = _point(shoulder, elbow, 0.72)
    _segment(draw, shoulder, sleeve_end, build.limb * 1.18, build.limb * 0.98, cloth, depth)
    _line(draw, [(sleeve_end[0] - 1, sleeve_end[1]), (sleeve_end[0] + 1, sleeve_end[1])], cloth[0])
    _segment(draw, sleeve_end, elbow, build.limb * 0.90, build.limb * 0.76, skin, depth)
    _segment(draw, elbow, hand, build.limb * 0.78, build.limb * 0.62, skin, depth)
    _hand(draw, hand, elbow, skin, near)


def _torso_polygon(pose):
    build = pose.build
    chest, pelvis = pose.chest, pose.pelvis
    ux, uy = _axis(pelvis, chest)
    px, py = -uy, ux
    half_top = build.chest_depth if pose.side else build.shoulder * 0.91
    half_mid = build.chest_depth * 0.96 if pose.side else build.shoulder * 0.77
    half_hip = build.chest_depth * 0.82 if pose.side else build.hip + 1.0
    neck = pose.neck[0] + ux * 0.7, pose.neck[1] + uy * 0.7
    middle = _point(chest, pelvis, 0.52)
    bottom = pelvis[0] - ux * 1.2, pelvis[1] - uy * 1.2
    return [
        (neck[0] - px * half_top * 0.65, neck[1] - py * half_top * 0.65),
        (chest[0] - px * half_top, chest[1] - py * half_top),
        (middle[0] - px * half_mid, middle[1] - py * half_mid),
        (bottom[0] - px * half_hip, bottom[1] - py * half_hip),
        (bottom[0] + px * half_hip, bottom[1] + py * half_hip),
        (middle[0] + px * half_mid, middle[1] + py * half_mid),
        (chest[0] + px * half_top, chest[1] + py * half_top),
        (neck[0] + px * half_top * 0.65, neck[1] + py * half_top * 0.65),
    ]


def _draw_torso(draw, pose, skin, cloth, belt):
    _poly(draw, _torso_polygon(pose), cloth[2])
    build = pose.build
    chest, pelvis = pose.chest, pose.pelvis
    ux, uy = _axis(pelvis, chest)
    px, py = -uy, ux
    light_width = build.chest_depth * 0.60 if pose.side else build.shoulder * 0.75
    shade_width = build.chest_depth * 0.55 if pose.side else build.shoulder * 0.62
    _line(draw, [
        (chest[0] - px * light_width - 1, chest[1] - py * light_width - 1),
        (chest[0] + ux * 2 - 1, chest[1] + uy * 2 - 1),
    ], cloth[4])
    _line(draw, [
        (pelvis[0] + px * (build.hip + 0.4) + 1, pelvis[1] + py * (build.hip + 0.4) + 1),
        (chest[0] + px * shade_width + 1, chest[1] + py * shade_width + 1),
    ], cloth[1])
    collar = pose.neck[0] - ux * 1.1, pose.neck[1] - uy * 1.1
    collar_width = 2.4 if pose.side else 3.0
    _line(draw, [
        (collar[0] - px * collar_width, collar[1] - py * collar_width),
        (collar[0], collar[1] + uy * 1.8),
        (collar[0] + px * collar_width, collar[1] + py * collar_width),
    ], cloth[0])
    neck_a = _point(pose.chest, pose.neck, 0.80)
    neck_b = _point(pose.neck, pose.head, 0.28)
    _segment(draw, neck_a, neck_b, 4.3, 3.8, skin)
    if not pose.back:
        _line(draw, [_point(chest, pelvis, 0.18), _point(chest, pelvis, 0.62)], cloth[3])
    waist = _point(chest, pelvis, 0.82)
    belt_width = build.chest_depth * 0.82 if pose.side else build.hip + 1.1
    _line(draw, [
        (waist[0] - px * belt_width, waist[1] - py * belt_width),
        (waist[0] + px * belt_width, waist[1] + py * belt_width),
    ], belt[2], 2)
    if not pose.side:
        _ellipse(draw, (waist[0] - 1, waist[1] - 1, waist[0] + 1, waist[1] + 1), belt[4], belt[0])


def _rotate(point, centre, angle):
    cosine, sine = math.cos(angle), math.sin(angle)
    x, y = point
    cx, cy = centre
    return cx + (x - cx) * cosine - (y - cy) * sine, cy + (x - cx) * sine + (y - cy) * cosine


def _draw_head(draw, pose, skin):
    x, y = pose.head
    radius = pose.head_r
    angle = -pose.head_tilt
    shape = [
        (x - radius * 0.72, y - radius * 0.98),
        (x + radius * 0.62, y - radius * 0.98),
        (x + radius * 0.94, y - radius * 0.55),
        (x + radius, y + radius * 0.22),
        (x + radius * 0.58, y + radius * 0.83),
        (x + radius * 0.26, y + radius * 1.07),
        (x - radius * 0.30, y + radius * 1.07),
        (x - radius * 0.69, y + radius * 0.78),
        (x - radius, y + radius * 0.18),
        (x - radius * 0.92, y - radius * 0.52),
    ]
    _poly(draw, [_rotate(value, pose.head, angle) for value in shape], skin[3])
    light = [
        (x - radius * 0.64, y - radius * 0.72),
        (x - radius * 0.18, y - radius * 0.90),
        (x + radius * 0.18, y - radius * 0.78),
        (x - radius * 0.34, y - radius * 0.48),
    ]
    _poly(draw, [_rotate(value, pose.head, angle) for value in light], skin[4], None)
    shadow = [
        (x + radius * 0.35, y + radius * 0.18),
        (x + radius * 0.67, y + radius * 0.36),
        (x + radius * 0.26, y + radius * 0.89),
        (x - 0.1, y + radius * 0.94),
    ]
    _poly(draw, [_rotate(value, pose.head, angle) for value in shadow], skin[2], None)
    if pose.back:
        _ellipse(draw, (x - radius - 1, y - 1, x - radius + 1, y + 2), skin[2])
        _ellipse(draw, (x + radius - 1, y - 1, x + radius + 1, y + 2), skin[2])
        return

    down = math.sin(pose.head_tilt), math.cos(pose.head_tilt)
    across = math.cos(pose.head_tilt), -math.sin(pose.head_tilt)

    def at(side, lower):
        return x + across[0] * side + down[0] * lower, y + across[1] * side + down[1] * lower

    eye = (38, 30, 34, 255)
    eye_light = (226, 207, 170, 255)
    if pose.side:
        facing = pose.facing or 1
        ear = at(-facing * radius * 0.56, 0.2)
        _ellipse(draw, (ear[0] - 1, ear[1] - 1, ear[0] + 1, ear[1] + 2), skin[2])
        _poly(draw, [
            at(facing * (radius - 0.5), -0.3),
            at(facing * (radius + 1.9), 0.7),
            at(facing * (radius - 0.35), 1.7),
        ], skin[3])
        eye_at = at(facing * 2.2, -0.5)
        _ellipse(draw, (eye_at[0] - 1, eye_at[1] - 1, eye_at[0] + 1, eye_at[1] + 1), eye, None)
        _line(draw, [at(facing * 0.9, -1.8), at(facing * 3.0, -1.7)], skin[0])
        _line(draw, [at(facing * 1.2, 3.0), at(facing * 2.8, 2.8)], skin[1])
    else:
        for facing in (-1, 1):
            ear = at(facing * radius * 0.93, 0.6)
            _ellipse(draw, (ear[0] - 1, ear[1] - 1, ear[0] + 1, ear[1] + 2), skin[2])
            _line(draw, [at(facing * 1.0, -1.8), at(facing * 3.0, -1.7)], skin[0])
            eye_at = at(facing * 2.0, -0.45)
            _ellipse(draw, (eye_at[0] - 1, eye_at[1] - 1, eye_at[0] + 1, eye_at[1] + 1), eye, None)
            draw.point(_pt(at(facing * 2.0, -0.8)), fill=eye_light)
        _line(draw, [at(0.0, 0.2), at(0.35, 2.2)], skin[1])
        _line(draw, [at(-1.4, 3.4), at(1.4, 3.4)], skin[0])
        _line(draw, [at(-2.4, 4.6), at(0.0, 5.1), at(2.4, 4.6)], skin[1])


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
