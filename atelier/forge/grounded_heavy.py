"""Grounded-2026 heavy-fauna rigs for bears and spiders.

These rigs construct fresh articulated frames in creature space. Bears use broad
plantigrade paws and continuous load-bearing legs; spiders use distinct rounded
wood-spider and angular quartz-spider body/joint construction. Completed frames
are never translated, rotated, stretched, or sampled from legacy art.
"""
from __future__ import annotations

import math
from PIL import Image

from . import pigment
from .grounded_beasts import Stage, _motion, _ramps


def _finish(stage: Stage, motion):
    if motion['flash']:
        overlay = Image.new('RGBA', stage.image.size, (255, 234, 210, 0))
        overlay.putalpha(stage.image.getchannel('A').point(lambda a: round(a * motion['flash'] * .45)))
        stage.image = Image.alpha_composite(stage.image, overlay)
    if motion['fade'] < 1:
        stage.image.putalpha(stage.image.getchannel('A').point(lambda a: round(a * motion['fade'])))
    return stage.image


def _bear_paw(stage: Stage, x: float, tone, pale, near: bool = True):
    """Broad plantigrade sole anchored to the common ground baseline."""
    fill = tone[3 if near else 2]
    stage.ellipse((x, .78), 4.15 if near else 3.75, 1.05, fill)
    claw = pale[1]
    for offset in (-2.2, 0, 2.2):
        stage.line([(x + offset - .55, .72), (x + offset + .55, .45)], claw, .65)


def _bear_front_back(stage: Stage, spec, motion, direction: int, polar: bool):
    coat, dark, pale = _ramps(spec)
    back = direction == 3
    body_y = (16.8 if polar else 16.2) + motion['bob'] - motion['crouch'] * .32
    left = -10.5 if polar else -12.5
    right = 10.5 if polar else 12.5

    for x in (left, right):
        stage.segment((x, body_y - .7), (x, 1.25), 6.4, 5.9, coat[2])
        _bear_paw(stage, x, coat, pale, False)
    stage.ellipse((0, body_y), 14.2 if polar else 14.6, 8.7, coat[3])
    stage.ellipse((0, body_y + 2.2), 12.2, 6.8, coat[4], None)
    for x in (left, right):
        stage.segment((x, body_y - .2), (x, 1.15), 6.6, 6.0, coat[3])
        _bear_paw(stage, x, coat, pale, True)

    if back:
        stage.disc((0, body_y + 5.0), 2.0, coat[2])
        stage.line([(-5.5, body_y + 6.0), (0, body_y + 7.1), (5.5, body_y + 6.0)], dark[3], 1.1)
        return

    lift = motion['charge'] * 1.2
    head = (0, body_y + 7.3 + lift)
    stage.ellipse(head, 5.6 if polar else 5.3, 4.9, coat[3])
    stage.disc((-3.7, head[1] + 3.4), 1.55, coat[3])
    stage.disc((3.7, head[1] + 3.4), 1.55, coat[3])
    stage.ellipse((0, head[1] - 1.55), 3.35, 2.05, pale[2])
    for s in (-1, 1):
        stage.disc((s * 2.0, head[1] + .55), .72, pigment.ramp(spec.eye)[4], None)
    stage.disc((0, head[1] - 1.3), .78, dark[1], None)


def _bear_side(stage: Stage, spec, motion, direction: int, polar: bool):
    coat, dark, pale = _ramps(spec)
    facing = 1 if direction == 2 else -1
    body_x = motion['lunge'] * facing * .32
    body_y = (16.4 if polar else 15.9) + motion['bob'] - motion['crouch'] * .34
    bases = (-11.5, -5.4, 5.4, 11.5)

    for index, base in enumerate(bases):
        gait = math.cos(motion['phase'] + (index % 2) * math.pi) * 2.0 * motion['stride']
        foot_x = base + gait
        hip_x = base * .70 + body_x
        near = index in (1, 2)
        tone = coat[3 if near else 2]
        stage.segment((hip_x, body_y - 1.3), ((hip_x + foot_x) * .5, 7.2), 5.7, 5.0, tone)
        stage.segment(((hip_x + foot_x) * .5, 7.2), (foot_x, 1.15), 5.0, 5.7, tone)
        _bear_paw(stage, foot_x, coat, pale, near)

    stage.ellipse((body_x, body_y), 14.8 if polar else 14.5, 8.4, coat[3])
    stage.ellipse((body_x - facing * 3.0, body_y + 2.5), 9.4, 6.7, coat[4], None)
    head_x = body_x + facing * (12.0 + motion['lunge'] * .42)
    head_y = body_y + 4.2 + motion['charge'] * 1.1
    stage.ellipse((head_x, head_y), 5.2, 4.55, coat[3])
    stage.disc((head_x - facing * 1.8, head_y + 3.4), 1.45, coat[3])
    muzzle_x = head_x + facing * 3.7
    stage.ellipse((muzzle_x, head_y - 1.0), 3.25, 2.0, pale[2])
    stage.disc((muzzle_x + facing * 1.7, head_y - .8), .74, dark[1], None)
    stage.disc((head_x + facing * 2.0, head_y + .55), .72, pigment.ramp(spec.eye)[4], None)


def _bear_death(stage: Stage, spec, motion, direction: int, polar: bool):
    coat, dark, pale = _ramps(spec)
    collapse = motion['collapse']
    facing = 1 if direction == 2 else -1 if direction == 1 else 0
    stage.ellipse((facing * collapse * 1.8, 5.2 - collapse * .8),
                  14.4 + collapse * 2.5, 4.9 - collapse * .55, coat[3])
    for index, x in enumerate((-11.5, -4.0, 4.0, 11.5)):
        _bear_paw(stage, x + facing * collapse * .9, coat, pale, index in (1, 2))
    head_x = facing * (9.6 - collapse * 2.6)
    head_y = 6.2 - collapse * 1.4
    stage.ellipse((head_x, head_y), 4.9, 3.8, coat[3])
    if direction != 3:
        stage.ellipse((head_x + facing * 2.4, head_y - 1.0), 2.7, 1.65, pale[2])
        if facing:
            stage.disc((head_x + facing * 2.0, head_y + .45), .65, dark[1], None)


def render_bear(definition, state, number, direction, spec):
    size = 128 if definition.get('boss') else 64
    stage = Stage(size)
    motion = _motion(state, number)
    polar = definition.get('family') == 'polar_bear'
    if state == 'death':
        _bear_death(stage, spec, motion, direction, polar)
    elif direction in (0, 3):
        _bear_front_back(stage, spec, motion, direction, polar)
    else:
        _bear_side(stage, spec, motion, direction, polar)
    return _finish(stage, motion)


def _wood_spider(stage: Stage, spec, motion, state: str, direction: int):
    coat, dark, pale = _ramps(spec)
    side = direction in (1, 2)
    facing = 1 if direction == 2 else -1 if direction == 1 else 0
    collapse = motion['collapse']
    y = max(3.3, 6.4 - collapse * 2.1 + motion['bob'] - motion['crouch'] * .2)
    drive = motion['lunge'] * (facing if side else .18)
    abdomen = (-facing * 2.8 + drive * .18, y + .35)
    head = (facing * 4.0 + drive * .46, y + (1.25 if direction == 0 else -.15))

    stage.ellipse(abdomen, 6.6, 4.8, coat[3])
    stage.ellipse((abdomen[0] - facing * 1.2, abdomen[1] + 1.1), 4.3, 2.7, coat[4], None)
    stage.ellipse(head, 4.0, 3.25, dark[3])
    spread = 11.2 - collapse * 4.2
    for index in range(8):
        side_sign = -1 if index < 4 else 1
        lane = index % 4
        phase = motion['phase'] + lane * .8 + (0 if side_sign < 0 else math.pi)
        walk = math.sin(phase) * 1.25 * motion['stride']
        root = (head[0] * .18 + side_sign * (2.0 + lane * .35), y + 1.4 - lane * .75)
        joint = (side_sign * (6.0 + lane * 1.2) + drive * .12,
                 y + 3.0 - lane * 1.25 + math.cos(phase) * .55)
        end = (side_sign * (spread + lane * 1.1) + walk + drive * .08,
               .55 + (lane % 2) * .22 + collapse * .8)
        if state == 'attack' and lane == 0:
            joint = (joint[0] + side_sign * 1.5, joint[1] + 3.4)
            end = (end[0] + facing * motion['lunge'] * .42, 3.2)
        stage.line([root, joint, end], dark[2], 1.55)
        stage.disc(joint, .72, coat[2], None)
    if direction != 3:
        for s in (-1, 1):
            stage.disc((head[0] + s * 1.25, head[1] + .7), .62, pigment.ramp(spec.eye)[4], None)
        stage.line([(head[0] - 1.3, head[1] - 2.1), (head[0] - .5, head[1] - 3.0)], pale[1], .9)
        stage.line([(head[0] + 1.3, head[1] - 2.1), (head[0] + .5, head[1] - 3.0)], pale[1], .9)


def _quartz_spider(stage: Stage, spec, motion, state: str, direction: int):
    coat, dark, pale = _ramps(spec)
    glow = pigment.ramp(spec.glow or '#8fb9c8')
    side = direction in (1, 2)
    facing = 1 if direction == 2 else -1 if direction == 1 else 0
    collapse = motion['collapse']
    y = max(3.8, 7.3 - collapse * 2.5 + motion['bob'] - motion['crouch'] * .18)
    drive = motion['lunge'] * (facing if side else .22)
    body_x = -facing * 1.8 + drive * .16
    head_x = facing * 5.0 + drive * .5

    stage.poly([(body_x - 6.8, y), (body_x - 3.2, y + 5.8),
                (body_x + 3.4, y + 5.0), (body_x + 7.0, y),
                (body_x + 2.8, y - 4.5), (body_x - 3.7, y - 4.2)], coat[3])
    stage.poly([(head_x - 4.2, y - .8), (head_x - 1.0, y + 3.9),
                (head_x + 3.8, y + 1.8), (head_x + 4.0, y - 2.5),
                (head_x, y - 3.7)], dark[3])
    for offset in (-3.8, 0, 3.8):
        stage.poly([(body_x + offset - .8, y + 4.0),
                    (body_x + offset, y + 7.0 + motion['charge'] * 1.7),
                    (body_x + offset + .9, y + 4.0)], pale[3])

    spread = 15.4 - collapse * 5.4
    for index in range(8):
        side_sign = -1 if index < 4 else 1
        lane = index % 4
        phase = motion['phase'] + lane * .72 + (0 if side_sign < 0 else math.pi)
        walk = math.sin(phase) * 1.45 * motion['stride']
        root = (body_x + side_sign * (2.5 + lane * .5), y + 2.4 - lane * 1.25)
        elbow = (side_sign * (8.0 + lane * 1.45) + drive * .14,
                 y + 5.5 - lane * .8 + math.cos(phase) * .7)
        ankle = (side_sign * (12.0 + lane * 1.1) + walk + drive * .1,
                 3.2 + (lane % 2) * 1.05 + collapse * .7)
        end = (side_sign * (spread + lane * .8) + walk + drive * .08,
               .6 + (lane % 2) * .18 + collapse * .7)
        if state == 'attack' and lane in (0, 1):
            elbow = (elbow[0] + side_sign * 2.2, elbow[1] + 3.2)
            ankle = (ankle[0] + facing * motion['lunge'] * .35, ankle[1] + 2.4)
        stage.line([root, elbow, ankle, end], dark[3], 1.7)
        stage.disc(elbow, .82, pale[2], None)
        stage.disc(ankle, .68, glow[4], None)
    stage.disc((body_x, y + .6), 1.25 + motion['charge'] * .55, glow[5], None)
    if direction != 3:
        for sx in (-1.4, 0, 1.4):
            stage.disc((head_x + sx, y + .4 + abs(sx) * .2), .62, glow[5], None)


def render_arachnid(definition, state, number, direction, spec):
    size = 128 if definition.get('boss') else 64
    stage = Stage(size)
    motion = _motion(state, number)
    if definition.get('family') == 'quartz_spider':
        _quartz_spider(stage, spec, motion, state, direction)
    else:
        _wood_spider(stage, spec, motion, state, direction)
    return _finish(stage, motion)
