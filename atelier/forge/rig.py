"""Humanoid skeleton for the Atelier library.

One rig drives the body, the hair, every armour layer, the held weapon and the
named townsfolk. Because all of those layers read the same joint table, a helmet
sits on the head and a sword stays in the hand in all six states, all eight
frames and all four facings.

Frame space is 64x64 with the ground contact at y=55 and the centre line at
x=31.5, matching the anchor the client uses when it draws a sprite at a
character's feet.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

CENTRE = 31.5
GROUND = 55.0
STATES = ('idle', 'walk', 'attack', 'cast', 'hit', 'death')
DIRECTIONS = ('south', 'west', 'east', 'north')
FRAMES = 8


@dataclass
class Build:
    """Body proportions. Kept small so silhouettes stay readable at 64px."""

    shoulder: float = 7.6      # half width across the shoulders
    hip: float = 4.6           # half width across the pelvis
    head: float = 5.4          # head radius
    chest_depth: float = 5.1   # half width seen from the side
    limb: float = 4.0          # arm thickness
    thigh: float = 5.0
    reach: float = 8.0         # upper arm length
    forearm: float = 7.4
    femur: float = 8.6
    shin: float = 9.4
    neck_y: float = 22.6
    shoulder_y: float = 24.4
    chest_y: float = 29.0
    pelvis_y: float = 36.6
    head_y: float = 16.4


BROAD = Build()
SLIGHT = Build(shoulder=6.6, hip=4.2, head=5.2, chest_depth=3.8, limb=3.4, thigh=4.4,
               reach=7.8, forearm=7.2, femur=8.4, shin=9.6, chest_y=29.2, pelvis_y=36.4)
BUILDS = (BROAD, SLIGHT)


@dataclass
class Pose:
    build: Build
    direction: int
    frame: int
    state: str
    facing: int                     # -1 west, 0 front or back, +1 east
    back: bool
    side: bool
    head: tuple = (CENTRE, 16.4)
    head_r: float = 5.4
    head_tilt: float = 0.0
    neck: tuple = (CENTRE, 22.6)
    chest: tuple = (CENTRE, 29.0)
    pelvis: tuple = (CENTRE, 36.6)
    shoulder: dict = field(default_factory=dict)
    elbow: dict = field(default_factory=dict)
    hand: dict = field(default_factory=dict)
    hip: dict = field(default_factory=dict)
    knee: dict = field(default_factory=dict)
    foot: dict = field(default_factory=dict)
    lean: float = 0.0
    prone: float = 0.0
    flash: float = 0.0
    fade: float = 1.0
    grip_angle: float = 0.0         # main hand weapon angle, radians, 0 = right
    guard_angle: float = 0.0        # off hand angle
    energy: float = 0.0             # 0..1 spell charge at the hands
    squash: float = 1.0

    @property
    def torso_top(self):
        return self.chest[1] - 5.0

    def mirrored(self):
        """Mirror every joint about the centre line for the west facing."""
        def flip(point):
            return (2 * CENTRE - point[0], point[1])

        def flip_map(values):
            return {key: flip(value) for key, value in values.items()}

        return replace(
            self, facing=-self.facing, head=flip(self.head), neck=flip(self.neck),
            chest=flip(self.chest), pelvis=flip(self.pelvis), head_tilt=-self.head_tilt,
            shoulder=flip_map(self.shoulder), elbow=flip_map(self.elbow), hand=flip_map(self.hand),
            hip=flip_map(self.hip), knee=flip_map(self.knee), foot=flip_map(self.foot),
            lean=-self.lean, grip_angle=math.pi - self.grip_angle, guard_angle=math.pi - self.guard_angle,
        )


def _lerp(a, b, t):
    return a + (b - a) * t


def _point(a, b, t):
    return (_lerp(a[0], b[0], t), _lerp(a[1], b[1], t))


def _arm(shoulder, angle, bend, build, length=1.0):
    """Place an elbow and hand from a shoulder angle and an elbow bend."""
    ex = shoulder[0] + math.cos(angle) * build.reach * length
    ey = shoulder[1] + math.sin(angle) * build.reach * length
    ax = angle + bend
    return (ex, ey), (ex + math.cos(ax) * build.forearm * length, ey + math.sin(ax) * build.forearm * length)


def _leg(hip, angle, bend, build):
    kx = hip[0] + math.cos(angle) * build.femur
    ky = hip[1] + math.sin(angle) * build.femur
    ax = angle + bend
    return (kx, ky), (kx + math.cos(ax) * build.shin, ky + math.sin(ax) * build.shin)


def _base(build, direction, drop=0.0):
    """Neutral standing skeleton for one facing."""
    side = direction in (1, 2)
    back = direction == 3
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    cx = CENTRE
    pose = Pose(build=build, direction=direction, frame=0, state='idle', facing=facing, back=back, side=side)
    pose.head_r = build.head
    pose.head = (cx, build.head_y + drop)
    pose.neck = (cx, build.neck_y + drop)
    pose.chest = (cx, build.chest_y + drop)
    pose.pelvis = (cx, build.pelvis_y + drop)
    if side:
        near_x, far_x = cx + 2.6, cx - 2.8
        pose.shoulder = {'far': (far_x, build.shoulder_y + drop + 0.4), 'near': (near_x, build.shoulder_y + drop)}
        pose.hip = {'far': (cx - 2.2, build.pelvis_y + drop + 0.6), 'near': (cx + 1.8, build.pelvis_y + drop)}
    else:
        pose.shoulder = {'far': (cx - build.shoulder, build.shoulder_y + drop),
                         'near': (cx + build.shoulder, build.shoulder_y + drop)}
        pose.hip = {'far': (cx - build.hip, build.pelvis_y + drop),
                    'near': (cx + build.hip, build.pelvis_y + drop)}
    for key in ('far', 'near'):
        shoulder = pose.shoulder[key]
        lean_out = 0.20 if key == 'near' else -0.20
        if side:
            lean_out = 0.10 if key == 'near' else -0.06
        elbow, hand = _arm(shoulder, math.pi / 2 + lean_out * 0.5, lean_out * 0.7, build, 0.94)
        pose.elbow[key] = elbow
        pose.hand[key] = hand
        hip = pose.hip[key]
        knee, foot = _leg(hip, math.pi / 2 + (0.06 if key == 'near' else -0.06), -0.04, build)
        pose.knee[key] = knee
        pose.foot[key] = (foot[0], GROUND + drop * 0.0)
    return pose


def _breathe(pose, phase):
    lift = math.sin(phase) * 0.5
    pose.chest = (pose.chest[0], pose.chest[1] - lift * 0.6)
    pose.neck = (pose.neck[0], pose.neck[1] - lift)
    pose.head = (pose.head[0], pose.head[1] - lift)
    for key in ('far', 'near'):
        shoulder = pose.shoulder[key]
        pose.shoulder[key] = (shoulder[0], shoulder[1] - lift * 0.8)
        elbow = pose.elbow[key]
        pose.elbow[key] = (elbow[0], elbow[1] - lift * 0.4)
        hand = pose.hand[key]
        pose.hand[key] = (hand[0], hand[1] - lift * 0.15)
    return pose


def _walk(pose, build, frame, side, back):
    phase = frame / FRAMES * math.tau
    swing = math.cos(phase)
    bob = -(1.0 - abs(math.cos(phase))) * 1.6
    lift_near = max(0.0, -math.sin(phase)) * 2.4
    lift_far = max(0.0, math.sin(phase)) * 2.4
    for name, value in (('chest', pose.chest), ('neck', pose.neck), ('head', pose.head), ('pelvis', pose.pelvis)):
        setattr(pose, name, (value[0], value[1] + bob))
    pose.head = (pose.head[0] + (swing * 0.3 if side else 0.0), pose.head[1])
    for key, sign in (('near', 1.0), ('far', -1.0)):
        shoulder = pose.shoulder[key]
        pose.shoulder[key] = (shoulder[0] + (swing * sign * 0.5 if side else swing * sign * 0.35), shoulder[1] + bob)
        hip = pose.hip[key]
        pose.hip[key] = (hip[0], hip[1] + bob)
        # arms swing against the legs
        arm_angle = math.pi / 2 - swing * sign * (0.62 if side else 0.30)
        bend = 0.34 * (1 if side else 0.5) + (0.12 if key == 'near' else 0.06)
        elbow, hand = _arm(pose.shoulder[key], arm_angle, bend * (1 if side else 0.8), build, 0.92)
        pose.elbow[key] = elbow
        pose.hand[key] = hand
        lift = lift_near if key == 'near' else lift_far
        leg_angle = math.pi / 2 + swing * sign * (0.46 if side else 0.16)
        knee_bend = 0.10 + lift * 0.16
        knee, foot = _leg(pose.hip[key], leg_angle, -knee_bend, build)
        pose.knee[key] = knee
        pose.foot[key] = (foot[0], min(GROUND, foot[1]) - lift)
    return pose


_ATTACK_KEYS = ((0.0, -0.55), (0.28, -1.35), (0.52, 0.45), (0.72, 0.95), (1.0, 0.10))


def _attack_curve(t):
    for i in range(len(_ATTACK_KEYS) - 1):
        t0, v0 = _ATTACK_KEYS[i]
        t1, v1 = _ATTACK_KEYS[i + 1]
        if t <= t1:
            local = (t - t0) / (t1 - t0)
            local = local * local * (3 - 2 * local)
            return _lerp(v0, v1, local)
    return _ATTACK_KEYS[-1][1]


def _attack(pose, build, frame, side, back):
    t = frame / (FRAMES - 1)
    swing = _attack_curve(t)
    push = math.sin(min(1.0, max(0.0, (t - 0.2) / 0.5)) * math.pi) * (2.6 if side else 1.4)
    drop = math.sin(t * math.pi) * 1.1
    lean = swing * (1.5 if side else 0.9)
    for name in ('chest', 'neck', 'head', 'pelvis'):
        x, y = getattr(pose, name)
        weight = {'pelvis': 0.35, 'chest': 0.85, 'neck': 1.0, 'head': 1.15}[name]
        setattr(pose, name, (x + lean * weight, y + drop * weight * 0.5))
    pose.lean = lean
    pose.head_tilt = swing * 0.25
    # front foot steps into the blow
    near_foot = pose.foot['near']
    pose.foot['near'] = (near_foot[0] + push * 0.8, near_foot[1])
    knee, _ = _leg(pose.hip['near'], math.pi / 2 + (push * 0.05), -0.16, build)
    pose.knee['near'] = knee
    far_foot = pose.foot['far']
    pose.foot['far'] = (far_foot[0] - push * 0.35, far_foot[1])
    for key in ('far', 'near'):
        shoulder = pose.shoulder[key]
        pose.shoulder[key] = (shoulder[0] + lean * 0.9, shoulder[1] + drop * 0.4)
    if side:
        weapon_angle = _lerp(-2.35, 0.62, (swing + 1.35) / 2.3)
        elbow, hand = _arm(pose.shoulder['near'], weapon_angle * 0.72 - 0.25, 0.42, build, 1.02)
        pose.elbow['near'], pose.hand['near'] = elbow, hand
        elbow, hand = _arm(pose.shoulder['far'], math.pi / 2 - swing * 0.45, 0.55, build, 0.86)
        pose.elbow['far'], pose.hand['far'] = elbow, hand
        pose.grip_angle = weapon_angle
    else:
        base_angle = -0.95 if not back else -2.2
        weapon_angle = base_angle + swing * 1.35
        elbow, hand = _arm(pose.shoulder['near'], weapon_angle, 0.5, build, 1.0)
        pose.elbow['near'], pose.hand['near'] = elbow, hand
        elbow, hand = _arm(pose.shoulder['far'], math.pi / 2 + 0.35 - swing * 0.25, 0.4, build, 0.88)
        pose.elbow['far'], pose.hand['far'] = elbow, hand
        pose.grip_angle = weapon_angle + (0.4 if not back else -0.4)
    pose.guard_angle = pose.grip_angle + math.pi * 0.6
    return pose


def _cast(pose, build, frame, side, back):
    t = frame / (FRAMES - 1)
    charge = math.sin(t * math.pi) ** 0.7
    rise = -charge * 2.0
    for name in ('chest', 'neck', 'head'):
        x, y = getattr(pose, name)
        setattr(pose, name, (x - charge * 0.6, y + rise * (1.0 if name != 'chest' else 0.6)))
    pose.head_tilt = -charge * 0.2
    pose.energy = charge
    for key, sign in (('near', 1.0), ('far', -1.0)):
        shoulder = pose.shoulder[key]
        pose.shoulder[key] = (shoulder[0], shoulder[1] + rise * 0.5)
        if side:
            angle = _lerp(math.pi / 2 + 0.16, -1.02 + sign * 0.14, charge)
            elbow, hand = _arm(pose.shoulder[key], angle, _lerp(0.30, 0.72, charge), build, 0.94)
        else:
            angle = _lerp(math.pi / 2 + sign * 0.30, -1.10 + sign * 0.34, charge)
            elbow, hand = _arm(pose.shoulder[key], angle, sign * _lerp(0.24, 0.62, charge), build, 0.95)
        pose.elbow[key], pose.hand[key] = elbow, hand
    knee, foot = _leg(pose.hip['far'], math.pi / 2 - 0.12, -0.10, build)
    pose.knee['far'] = knee
    pose.foot['far'] = (foot[0], GROUND)
    pose.grip_angle = -1.25 if not side else -1.05
    pose.guard_angle = -1.9
    return pose


def _hit(pose, build, frame, side, back):
    t = frame / (FRAMES - 1)
    shock = math.sin(min(1.0, t * 1.9) * math.pi) ** 0.6
    back_step = shock * (2.6 if side else 1.6)
    for name in ('chest', 'neck', 'head', 'pelvis'):
        x, y = getattr(pose, name)
        weight = {'pelvis': 0.4, 'chest': 0.9, 'neck': 1.1, 'head': 1.35}[name]
        setattr(pose, name, (x - back_step * weight, y + shock * 0.9 * weight * 0.5))
    pose.head_tilt = -shock * 0.4
    pose.flash = 0.62 if frame == 0 else (0.44 if frame == 1 else (0.20 if frame == 2 else 0.0))
    for key, sign in (('near', 1.0), ('far', -1.0)):
        shoulder = pose.shoulder[key]
        pose.shoulder[key] = (shoulder[0] - back_step * 0.9, shoulder[1] + shock * 0.4)
        angle = math.pi / 2 + sign * (0.5 + shock * 0.75)
        elbow, hand = _arm(pose.shoulder[key], angle - shock * 0.55, sign * 0.5, build, 0.9)
        pose.elbow[key], pose.hand[key] = elbow, hand
        knee, foot = _leg(pose.hip[key], math.pi / 2 + sign * 0.12 - shock * 0.1, -0.12 - shock * 0.12, build)
        pose.knee[key] = knee
        pose.foot[key] = (foot[0] - back_step * (0.5 if key == 'far' else 0.15), GROUND)
    return pose


def _kneel_pose(build, direction):
    """Authored mid-collapse key: weight on one knee, torso pitched forward."""
    pose = _base(build, direction)
    cx = CENTRE
    pose.head = (cx + 3.4, 30.0)
    pose.neck = (cx + 2.4, 34.4)
    pose.chest = (cx + 1.4, 38.6)
    pose.pelvis = (cx - 2.0, 45.4)
    pose.head_tilt = 0.55
    pose.shoulder = {'far': (cx + 0.2, 36.4), 'near': (cx + 2.6, 37.4)}
    pose.hip = {'far': (cx - 3.2, 45.6), 'near': (cx - 1.0, 46.0)}
    pose.elbow = {'far': (cx + 3.6, 43.0), 'near': (cx + 6.0, 43.6)}
    pose.hand = {'far': (cx + 5.4, 50.0), 'near': (cx + 8.4, 50.6)}
    pose.knee = {'far': (cx + 1.6, 52.0), 'near': (cx + 3.4, 52.6)}
    pose.foot = {'far': (cx - 7.0, 53.4), 'near': (cx - 5.0, 54.2)}
    return pose


def _prone_pose(build, direction):
    """Authored final key: the body lies along the ground, not stood on its side."""
    pose = _base(build, direction)
    cx = CENTRE
    pose.head = (cx + 9.6, 50.0)
    pose.head_r = build.head * 0.94
    pose.head_tilt = -1.30
    pose.neck = (cx + 5.4, 50.8)
    pose.chest = (cx + 2.0, 51.2)
    pose.pelvis = (cx - 4.6, 52.2)
    pose.shoulder = {'far': (cx + 2.8, 49.6), 'near': (cx + 2.0, 52.8)}
    pose.hip = {'far': (cx - 4.2, 50.8), 'near': (cx - 4.8, 53.4)}
    pose.elbow = {'far': (cx + 6.8, 47.6), 'near': (cx + 6.0, 54.8)}
    pose.hand = {'far': (cx + 11.2, 47.0), 'near': (cx + 10.4, 55.6)}
    pose.knee = {'far': (cx - 11.0, 50.4), 'near': (cx - 11.6, 53.8)}
    pose.foot = {'far': (cx - 17.0, 51.4), 'near': (cx - 17.4, 54.6)}
    pose.squash = 0.86
    return pose


def _blend(a, b, t):
    out = replace(a)
    out.head = _point(a.head, b.head, t)
    out.head_r = _lerp(a.head_r, b.head_r, t)
    out.head_tilt = _lerp(a.head_tilt, b.head_tilt, t)
    out.neck = _point(a.neck, b.neck, t)
    out.chest = _point(a.chest, b.chest, t)
    out.pelvis = _point(a.pelvis, b.pelvis, t)
    out.squash = _lerp(a.squash, b.squash, t)
    for name in ('shoulder', 'elbow', 'hand', 'hip', 'knee', 'foot'):
        first, second = getattr(a, name), getattr(b, name)
        setattr(out, name, {key: _point(first[key], second[key], t) for key in first})
    return out


def _death(build, direction, frame):
    stand = _base(build, direction)
    stand.head_tilt = -0.18
    stand.hand['far'] = (stand.hand['far'][0] - 1.6, stand.hand['far'][1] - 2.2)
    stand.hand['near'] = (stand.hand['near'][0] + 1.4, stand.hand['near'][1] - 2.6)
    kneel = _kneel_pose(build, direction)
    prone = _prone_pose(build, direction)
    t = frame / (FRAMES - 1)
    if t <= 0.42:
        local = t / 0.42
        pose = _blend(stand, kneel, local * local)
    else:
        local = (t - 0.42) / 0.58
        local = min(1.0, local)
        pose = _blend(kneel, prone, local ** 0.72)
    pose.prone = min(1.0, max(0.0, (t - 0.30) / 0.55))
    pose.fade = 1.0 if frame < 6 else (0.86 if frame == 6 else 0.7)
    pose.state = 'death'
    pose.frame = frame
    pose.grip_angle = _lerp(0.6, 1.5, t)
    pose.guard_angle = _lerp(1.9, 2.4, t)
    return pose


def pose(build, state, frame, direction):
    """Joint table for one sprite frame."""
    build = BUILDS[build] if isinstance(build, int) else build
    frame = max(0, min(FRAMES - 1, frame))
    source = 2 if direction == 1 else direction     # west is authored as east, then mirrored
    side = source in (1, 2)
    back = source == 3
    if state == 'death':
        result = _death(build, source, frame)
    else:
        result = _base(build, source)
        result.state = state
        result.frame = frame
        phase = frame / FRAMES * math.tau
        if state == 'idle':
            _breathe(result, phase)
            result.grip_angle = 1.15 if not side else 1.35
            result.guard_angle = 1.9
        elif state == 'walk':
            _walk(result, build, frame, side, back)
            result.grip_angle = 1.2
            result.guard_angle = 1.95
        elif state == 'attack':
            _attack(result, build, frame, side, back)
        elif state == 'cast':
            _cast(result, build, frame, side, back)
        elif state == 'hit':
            _hit(result, build, frame, side, back)
    result.state = state
    result.frame = frame
    result.direction = direction
    if direction == 1:
        result = result.mirrored()
        result.direction = 1
    return result


def draw_order(pose):
    """Limb keys from far to near, so the torso always separates them."""
    return ('far', 'near')


def sheet(draw_frame, size=64):
    """Compose one animation sheet: 8 frames across, state-major x direction down."""
    from PIL import Image
    result = Image.new('RGBA', (size * FRAMES, size * len(STATES) * len(DIRECTIONS)), (0, 0, 0, 0))
    for state_index, state in enumerate(STATES):
        for direction in range(len(DIRECTIONS)):
            for frame in range(FRAMES):
                image = draw_frame(state, frame, direction)
                if image.size != (size, size):
                    raise ValueError('Frame is %s, expected %s for %s' % (image.size, size, state))
                result.alpha_composite(image, (frame * size, (state_index * 4 + direction) * size))
    return result
