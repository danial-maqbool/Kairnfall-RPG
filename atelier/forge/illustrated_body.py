"""Pure 2D illustrated humanoid renderer for Kairnfall.

This renderer intentionally stays in screen space. It uses the shared 64 px
humanoid rig, the refined pixel body as its silhouette foundation, and then adds
hand-authored 2D pixel clusters for facial structure, joints, garment
construction and material separation. No mesh, camera, lighting engine or 3D
projection is involved.
"""
from __future__ import annotations

import math

from PIL import ImageDraw

from . import pigment, refined_body, rig
from .pigment import blend, ramp

SIZE = 64
INK = (24, 22, 27, 255)
DEEP = (18, 17, 21, 255)
EYE_WHITE = (224, 216, 200, 255)
IRIS = (49, 55, 50, 255)
LIP = (103, 57, 53, 255)
CLOTH = '#79634e'
LEATHER = '#5f432d'
METAL = '#8e8b80'


def _pt(point):
    return int(round(point[0])), int(round(point[1]))


def _axis(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length


def _mix_effect(colour, pose):
    red, green, blue, alpha = colour
    if pose.flash:
        amount = 0.25 * pose.flash
        red = round(red * (1 - amount) + 255 * amount)
        green = round(green * (1 - amount) + 236 * amount)
        blue = round(blue * (1 - amount) + 206 * amount)
    alpha = round(alpha * pose.fade)
    return red, green, blue, alpha


def _line(draw, values, fill, width=1):
    draw.line([_pt(value) for value in values], fill=fill, width=width)


def _poly(draw, values, fill):
    draw.polygon([_pt(value) for value in values], fill=fill)


def _pixel(draw, point, fill):
    draw.point(_pt(point), fill=fill)


def _ellipse(draw, box, fill, outline=None):
    draw.ellipse(tuple(int(round(v)) for v in box), fill=fill, outline=outline, width=1)


def _face_basis(pose):
    down = math.sin(pose.head_tilt), math.cos(pose.head_tilt)
    across = math.cos(pose.head_tilt), -math.sin(pose.head_tilt)
    x, y = pose.head

    def at(side, lower):
        return x + across[0] * side + down[0] * lower, y + across[1] * side + down[1] * lower

    return at


def _face_details(draw, pose, skin):
    if pose.back:
        return
    at = _face_basis(pose)
    shade = _mix_effect(skin[1], pose)
    mid = _mix_effect(skin[2], pose)
    light = _mix_effect(skin[5], pose)
    ink = _mix_effect(INK, pose)
    deep = _mix_effect(DEEP, pose)
    white = _mix_effect(EYE_WHITE, pose)
    iris = _mix_effect(IRIS, pose)
    lip = _mix_effect(LIP, pose)
    state = pose.state

    if pose.side:
        facing = pose.facing or 1
        eye = at(facing * 2.05, -0.45)
        if state == 'death':
            _line(draw, [at(facing * 1.25, -0.45), at(facing * 2.75, -0.05)], deep)
        elif state == 'hit':
            _line(draw, [at(facing * 1.20, -0.20), at(facing * 2.55, 0.25)], ink)
        else:
            _pixel(draw, eye, white)
            _pixel(draw, at(facing * 2.35, -0.38), iris)
            _pixel(draw, at(facing * 2.48, -0.62), light)
        brow_y = -1.75 + (0.45 if state in ('attack', 'hit') else 0.0)
        _line(draw, [at(facing * 0.95, brow_y), at(facing * 2.8, brow_y - 0.25)], ink)
        # Nose bridge, tip and nostril. These are separate clusters so the
        # profile reads as a face rather than one flat skin block.
        _line(draw, [at(facing * 1.20, 0.55), at(facing * 2.75, 1.25)], shade)
        _pixel(draw, at(facing * 3.05, 1.55), mid)
        _pixel(draw, at(facing * 2.75, 1.85), deep)
        # Ear bowl and inner cartilage sit behind the eye in profile.
        ear = at(-facing * 2.75, 0.75)
        _ellipse(draw, (ear[0] - 1, ear[1] - 1, ear[0] + 1, ear[1] + 2), mid, shade)
        _pixel(draw, (ear[0], ear[1] + 0.5), shade)
        if state == 'attack':
            _line(draw, [at(facing * 1.20, 3.05), at(facing * 2.65, 2.70)], deep)
        elif state == 'hit':
            _line(draw, [at(facing * 1.15, 2.95), at(facing * 2.55, 3.45)], deep)
        else:
            _line(draw, [at(facing * 1.10, 3.05), at(facing * 2.55, 3.00)], lip)
        _pixel(draw, at(facing * 1.65, 3.75), shade)
        return

    for sign in (-1, 1):
        eye = at(sign * 1.85, -0.40)
        if state == 'death':
            _line(draw, [at(sign * 1.10, -0.42), at(sign * 2.65, -0.02)], deep)
        elif state == 'hit':
            _line(draw, [at(sign * 1.05, -0.18), at(sign * 2.55, 0.30)], ink)
        else:
            _pixel(draw, at(sign * 1.72, -0.34), white)
            _pixel(draw, eye, iris)
            _pixel(draw, at(sign * 1.78, -0.70), light)
        brow_inner = -1.62 + (0.42 if state in ('attack', 'hit') else 0.0)
        brow_outer = -1.86 + (0.20 if state == 'cast' else 0.0)
        _line(draw, [at(sign * 0.85, brow_inner), at(sign * 2.80, brow_outer)], ink)

    # Nose plane: bridge, tip and nostrils.
    _line(draw, [at(-0.20, 0.20), at(0.15, 1.95)], shade)
    _line(draw, [at(-0.75, 2.05), at(0.0, 2.35), at(0.75, 2.05)], mid)
    _pixel(draw, at(-0.55, 2.28), deep)
    _pixel(draw, at(0.55, 2.28), deep)

    # Ear rims and inner folds stay visible at native 1x.
    for sign in (-1, 1):
        ear = at(sign * pose.head_r * 0.92, 0.72)
        _ellipse(draw, (ear[0] - 1, ear[1] - 1, ear[0] + 1, ear[1] + 2), mid, shade)
        _pixel(draw, (ear[0] - sign * 0.25, ear[1] + 0.55), shade)

    if state == 'attack':
        _line(draw, [at(-1.55, 3.30), at(0.0, 3.68), at(1.55, 3.22)], deep)
    elif state == 'hit':
        _line(draw, [at(-1.45, 3.62), at(0.0, 3.12), at(1.45, 3.68)], deep)
    else:
        _line(draw, [at(-1.45, 3.38), at(1.45, 3.38)], lip)
        _line(draw, [at(-0.85, 3.86), at(0.85, 3.86)], shade)

    # Cheek and chin pixels add healthy facial volume without smoothing.
    _pixel(draw, at(-2.85, 2.20), light)
    _pixel(draw, at(2.85, 2.20), mid)
    _line(draw, [at(-1.15, 4.45), at(0.0, 4.82), at(1.15, 4.45)], shade)


def _garment_details(draw, pose, skin, cloth, leather, metal):
    chest, pelvis = pose.chest, pose.pelvis
    ux, uy = _axis(pelvis, chest)
    px, py = -uy, ux
    build = pose.build
    cloth_dark = _mix_effect(cloth[1], pose)
    cloth_light = _mix_effect(cloth[4], pose)
    leather_dark = _mix_effect(leather[1], pose)
    leather_mid = _mix_effect(leather[3], pose)
    metal_light = _mix_effect(metal[5], pose)
    skin_shade = _mix_effect(skin[1], pose)

    shoulder_span = build.chest_depth * 0.85 if pose.side else build.shoulder * 0.74
    collar = (pose.neck[0] - ux * 0.55, pose.neck[1] - uy * 0.55)
    _line(draw, [
        (collar[0] - px * shoulder_span * 0.40, collar[1] - py * shoulder_span * 0.40),
        (collar[0], collar[1] + uy * 1.55),
        (collar[0] + px * shoulder_span * 0.40, collar[1] + py * shoulder_span * 0.40),
    ], leather_dark)

    # A short leather jerkin panel gives the base body constructed clothing.
    upper = (chest[0] + ux * 0.7, chest[1] + uy * 0.7)
    lower = (chest[0] - ux * 4.9, chest[1] - uy * 4.9)
    panel = build.chest_depth * 0.56 if pose.side else build.shoulder * 0.49
    _line(draw, [(upper[0] - px * panel, upper[1] - py * panel),
                 (lower[0] - px * panel * 0.78, lower[1] - py * panel * 0.78)], leather_mid)
    _line(draw, [(upper[0] + px * panel, upper[1] + py * panel),
                 (lower[0] + px * panel * 0.78, lower[1] + py * panel * 0.78)], leather_dark)

    # Centre fastening and rivets. Back views get a centre seam instead.
    if pose.back:
        _line(draw, [chest, pelvis], cloth_dark)
    elif not pose.side:
        centre_a = (chest[0] - ux * 0.4, chest[1] - uy * 0.4)
        centre_b = (pelvis[0] + ux * 1.8, pelvis[1] + uy * 1.8)
        _line(draw, [centre_a, centre_b], leather_dark)
        for amount in (0.25, 0.45, 0.65):
            point = (centre_a[0] + (centre_b[0] - centre_a[0]) * amount,
                     centre_a[1] + (centre_b[1] - centre_a[1]) * amount)
            _pixel(draw, point, metal_light)

    # Shoulder seam / clavicle line reinforces upper-body anatomy.
    if not pose.back:
        clavicle = (pose.neck[0] + ux * 1.45, pose.neck[1] + uy * 1.45)
        span = build.chest_depth * 0.65 if pose.side else build.shoulder * 0.58
        _line(draw, [(clavicle[0] - px * span, clavicle[1] - py * span),
                     (clavicle[0] + px * span, clavicle[1] + py * span)], cloth_light)

    # Explicit elbow, wrist, knee and ankle clusters make limb lengths readable.
    for key in ('far', 'near'):
        elbow = pose.elbow[key]
        hand = pose.hand[key]
        knee = pose.knee[key]
        foot = pose.foot[key]
        _pixel(draw, elbow, skin_shade)
        _line(draw, [(hand[0] - 1, hand[1]), (hand[0] + 1, hand[1])], skin_shade)
        _line(draw, [(knee[0] - 1.2, knee[1]), (knee[0] + 1.2, knee[1])], cloth_dark)
        _line(draw, [(foot[0] - 1.5, foot[1] - 1.2), (foot[0] + 1.5, foot[1] - 1.2)], leather_dark)

    # Belt and buckle give the torso a clear waist and prevent a tube silhouette.
    waist = (chest[0] + (pelvis[0] - chest[0]) * 0.78,
             chest[1] + (pelvis[1] - chest[1]) * 0.78)
    belt_half = build.chest_depth * 0.80 if pose.side else build.hip + 0.8
    _line(draw, [(waist[0] - px * belt_half, waist[1] - py * belt_half),
                 (waist[0] + px * belt_half, waist[1] + py * belt_half)], leather_dark, 2)
    if not pose.side:
        _pixel(draw, waist, metal_light)


def body_frame(build, skin_index, state, frame, direction):
    """Render one purely 2D humanoid frame."""
    image = refined_body.body_frame(build, skin_index, state, frame, direction)
    pose = rig.pose(build, state, frame, direction)
    draw = ImageDraw.Draw(image)
    skin = ramp(pigment.SKIN[max(0, min(5, int(skin_index)))])
    cloth = ramp(CLOTH)
    leather = ramp(LEATHER)
    metal = ramp(METAL)
    _garment_details(draw, pose, skin, cloth, leather, metal)
    _face_details(draw, pose, skin)
    return image
