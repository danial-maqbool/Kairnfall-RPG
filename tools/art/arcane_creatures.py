"""Render ring-based arcane creatures separately from anatomical creatures."""
from __future__ import annotations
import math
from PIL import Image
from .common import Pixel, canvas, palette, animation_pose, finish_frame, INK
from .creature_pack import frame as anatomical_frame


def frame(definition, state, number, direction):
    if definition['family'] != 'spell_wisp':
        return anatomical_frame(definition, state, number, direction)
    image = canvas()
    p = Pixel(image)
    pose = animation_pose(state, number, direction)
    phase = number * math.tau / 8
    x, y = 32, 32 + pose['bob']
    metal = palette('a995c4')
    core = palette('c2d9cf')
    rings = []
    for radius, tilt, offset in [(23, .38, 0), (18, .65, math.pi / 3), (12, .8, -math.pi / 3)]:
        angle = phase * .35 + offset + direction * math.pi / 2
        points = []
        for n in range(41):
            a = n * math.tau / 40
            xx, yy = math.cos(a) * radius, math.sin(a) * radius * tilt
            points.append((x + xx * math.cos(angle) - yy * math.sin(angle),
                           y + xx * math.sin(angle) + yy * math.cos(angle)))
        rings.append(points)
        p.line(points, INK, 5)
        p.line(points, metal[2], 3)
        p.line(points[:21], metal[4], 1)
    p.poly([(x-6,y),(x-3,y-8),(x+3,y-7),(x+7,y),(x+3,y+8),(x-4,y+7)],core[2])
    p.poly([(x-2,y-6),(x+2,y-5),(x+4,y),(x+1,y+5),(x-3,y+2)],core[4],None)
    p.line([(x,y-4),(x-1,y),(x+2,y+2)],core[5],2)
    for points in rings:
        for index in (5, 18, 31):
            xx, yy = points[index]
            p.poly([(xx-2,yy),(xx,yy-3),(xx+2,yy),(xx,yy+3)],metal[3])
            p.dot(xx,yy,core[5])
    if state in {'attack','cast'}:
        for i in range(4):
            a = phase + i * math.pi / 2
            xx, yy = x + math.cos(a)*27, y + math.sin(a)*27
            p.line([(xx-2,yy),(xx+2,yy)],core[4])
            p.line([(xx,yy-2),(xx,yy+2)],core[5])
    image = finish_frame(image, state, number, direction)
    if definition.get('boss'):
        image = image.resize((128,128),Image.Resampling.NEAREST)
    return image
