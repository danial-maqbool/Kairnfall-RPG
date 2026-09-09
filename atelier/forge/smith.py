"""Items: icons, and the same objects placed in a character's hand.

A weapon is described once, in a local frame where the grip sits at the origin
and the business end points along +x. `icon` fits that description into a 32px
tile; `hold` rotates it onto the rig's grip angle. Because both read one
description, the sword on the hotbar is the sword in the hand.

Every blade carries an edge, a spine and a fuller; every haft carries a wrap and
a pommel or a butt cap. Nothing in this module is a rectangle standing in for a
weapon.
"""
from __future__ import annotations

import math

from PIL import Image

from . import gear, pigment
from .brush import Sketch, catmull, refine_sprite, taper_shape
from .pigment import blend, ramp

ICON = 32


# ------------------------------------------------------------- description --

def comp(role, shapes, details=()):
    return {'role': role, 'shapes': list(shapes), 'details': list(details)}


def poly(points):
    return ('poly', points)


def smooth(points, samples=5):
    return ('poly', catmull(points, samples, closed=True))


def line(points, width=1.0):
    return ('line', points, width)


def disc(centre, radius):
    return ('disc', centre, radius)


def limb(a, b, wa, wb):
    return ('poly', taper_shape(a, b, wa, wb))


# ------------------------------------------------------------------ hafts --

def _grip(length=7.0, thick=3.0, butt='pommel'):
    shapes = [limb((-length, 0), (0.6, 0), thick, thick * 1.05)]
    details = [line([(-length + 1, -0.8 + i * 1.6), (0.2, -0.8 + i * 1.6)], 1) for i in range(2)]
    wraps = [line([(-length + 1.2 + i * 1.8, -thick / 2), (-length + 0.6 + i * 1.8, thick / 2)], 1)
             for i in range(max(1, int(length / 1.8)))]
    return comp('grip', shapes, details + wraps), butt


def _pommel(x, radius=2.2):
    return comp('trim', [disc((x, 0), radius)], [disc((x - 0.6, -0.6), radius * 0.42)])


def _blade(length, half, edge_start=0.55, tip=2.0):
    """A double edged blade: spine, bevel and point."""
    body = poly([
        (1.0, -half), (length * edge_start, -half * 0.94), (length - tip, -half * 0.62),
        (length, 0.0), (length - tip, half * 0.62), (length * edge_start, half * 0.94), (1.0, half),
    ])
    fuller = line([(2.4, 0.0), (length - tip * 1.6, 0.0)], 1)
    bevel = line([(2.0, -half * 0.45), (length - tip * 1.4, -half * 0.2)], 1)
    return body, fuller, bevel


# --------------------------------------------------------------- profiles --
#
# Every profile takes a style dict from gear.style_of(). The style decides the
# guard family, the pommel, how the edge is cut, how the haft is dressed and how
# much ornament and glow the piece carries, so a tier change alters the actual
# silhouette rather than only the palette.

DEFAULT_STYLE = dict(guard='bar', pommel='round', edge='straight', haft='wrapped',
                     crest='none', pauldron='round', skirt='none', rune=0.0,
                     reach=1.0, breadth=1.0, guard_span=1.0, ornament=0, plume=0.0,
                     gem='#a8623c', glow='', tier=0, family='plain')


def resolve(style=None):
    merged = dict(DEFAULT_STYLE)
    if style:
        merged.update(style)
    return merged


def _rune_marks(shapes):
    return comp('rune', shapes, [])


def _pommel_parts(style, x):
    kind = style['pommel']
    if kind == 'disc':
        return [comp('trim', [disc((x, 0), 2.5)], [disc((x - 0.7, -0.7), 1.1)]),
                comp('metal', [limb((x + 1.6, 0), (x + 2.6, 0), 4.0, 3.4)])]
    if kind == 'faceted':
        return [comp('trim', [poly([(x, -2.8), (x + 2.4, 0), (x, 2.8), (x - 2.4, 0)])],
                     [poly([(x, -1.9), (x + 1.0, -0.3), (x - 0.9, -0.3)])]),
                comp('metal', [limb((x + 1.8, 0), (x + 2.8, 0), 4.2, 3.6)])]
    if kind == 'ring':
        return [comp('trim', [('ring', (x - 0.4, 0), 3.0, 1.3)]),
                comp('metal', [limb((x + 2.2, 0), (x + 3.2, 0), 4.0, 3.4)])]
    if kind == 'spike':
        return [comp('metal', [poly([(x - 4.2, 0), (x + 1.2, -2.4), (x + 1.2, 2.4)])]),
                comp('trim', [limb((x + 1.0, 0), (x + 2.4, 0), 4.6, 4.0)])]
    if kind == 'gem':
        parts = [comp('trim', [disc((x, 0), 2.9)]),
                 comp('gem', [poly([(x, -2.0), (x + 1.8, 0), (x, 2.0), (x - 1.8, 0)])],
                      [poly([(x, -1.3), (x + 0.8, -0.2), (x - 0.7, -0.2)])])]
        if style['glow']:
            parts.append(_rune_marks([disc((x, 0), 1.0)]))
        return parts
    return [comp('trim', [disc((x, 0), 2.2)], [disc((x - 0.6, -0.6), 0.9)])]


def _guard_parts(style, span):
    kind = style['guard']
    s = span * style['guard_span']
    out = []
    if kind == 'tipped':
        out.append(comp('metal', [smooth([(0.2, -s), (2.2, -s * 0.9), (2.6, 0), (2.2, s * 0.9),
                                          (0.2, s), (-1.0, s * 0.5), (-1.1, -s * 0.5)], 4)],
                        [line([(0.7, -s * 0.7), (0.7, s * 0.7)], 1)]))
        out.append(comp('trim', [disc((1.4, -s + 0.4), 1.6), disc((1.4, s - 0.4), 1.6)]))
    elif kind == 'wings':
        for sign in (-1, 1):
            out.append(comp('metal', [smooth([
                (0.0, sign * 1.8), (0.6, sign * s * 0.60), (4.0, sign * s * 1.05),
                (6.4, sign * s * 0.86), (3.2, sign * s * 0.40), (2.0, sign * 1.0)], 5)]))
        out.append(comp('trim', [limb((-0.8, 0), (2.4, 0), 4.8, 4.2)],
                        [line([(0.0, -1.4), (1.8, -1.4)], 1)]))
    elif kind == 'cross':
        out.append(comp('metal', [limb((1.2, -s * 1.12), (1.2, s * 1.12), 3.2, 3.2)],
                        [line([(1.2, -s), (1.2, s)], 1)]))
        out.append(comp('trim', [disc((1.2, 0), 2.6)], [disc((0.5, -0.7), 1.0)]))
        out.append(comp('trim', [limb((2.4, -1.5), (6.4, -1.5), 1.8, 1.2),
                                 limb((2.4, 1.5), (6.4, 1.5), 1.8, 1.2)]))
    elif kind == 'hooked':
        for sign in (-1, 1):
            out.append(comp('metal', [poly([(0.6, sign * 1.6), (1.4, sign * s * 0.85),
                                            (5.0, sign * s * 1.20), (3.4, sign * s * 0.52),
                                            (2.6, sign * 1.3)])]))
        out.append(comp('metal', [limb((-0.4, 0), (2.6, 0), 4.4, 3.8)]))
    elif kind == 'shards':
        for sign, reach in ((-1, 1.0), (1, 0.82), (-1, 0.58), (1, 0.42)):
            out.append(comp('gem', [poly([(0.8, sign * 1.2), (2.2 + reach * 2.2, sign * s * reach),
                                          (3.4, sign * 1.4)])]))
        out.append(comp('trim', [limb((-0.4, 0), (2.6, 0), 4.6, 4.0)]))
        if style['glow']:
            out.append(_rune_marks([disc((1.2, 0), 1.4)]))
    else:  # bar
        out.append(comp('metal', [smooth([(0.2, -s), (2.0, -s * 0.86), (2.4, 0), (2.0, s * 0.86),
                                          (0.2, s), (-0.9, s * 0.5), (-1.0, -s * 0.5)], 4)],
                        [line([(0.6, -s * 0.7), (0.6, s * 0.7)], 1)]))
    return out


def _blade(style, length, half, tip=2.0):
    """Blade outline plus its cut detail, sized by this tier's proportions."""
    kind = style['edge']
    reach = length * style['reach']
    thick = half * style['breadth']
    details = []
    if kind == 'toothed':
        points = [(1.0, -thick)]
        steps = 5
        for step in range(steps):
            run = 1.0 + (reach - tip - 1.0) * (step / steps)
            mid = 1.0 + (reach - tip - 1.0) * ((step + 0.55) / steps)
            points.append((run, -thick * 0.98))
            points.append((mid, -thick * 0.48))
        points += [(reach, 0.0), (reach - tip, thick * 0.62),
                   (reach * 0.55, thick * 0.96), (1.0, thick)]
        body = poly(points)
    elif kind in ('crystal', 'ethereal'):
        body = poly([(1.0, -thick), (reach * 0.42, -thick * 1.02), (reach * 0.74, -thick * 0.72),
                     (reach, 0.0), (reach * 0.74, thick * 0.72), (reach * 0.42, thick * 1.02),
                     (1.0, thick)])
    else:
        body = poly([(1.0, -thick), (reach * 0.55, -thick * 0.94), (reach - tip, -thick * 0.62),
                     (reach, 0.0), (reach - tip, thick * 0.62), (reach * 0.55, thick * 0.94),
                     (1.0, thick)])
    if kind in ('fullered', 'runed', 'doubled', 'crystal', 'ethereal'):
        details.append(line([(2.4, 0.0), (reach - tip * 1.8, 0.0)], 1))
    if kind in ('doubled', 'runed', 'crystal', 'ethereal'):
        details.append(line([(2.2, -thick * 0.48), (reach - tip * 1.5, -thick * 0.20)], 1))
        details.append(line([(2.2, thick * 0.48), (reach - tip * 1.5, thick * 0.20)], 1))
    else:
        details.append(line([(2.0, -thick * 0.45), (reach - tip * 1.4, -thick * 0.20)], 1))
    return body, details, reach, thick


def _edge_extras(style, reach, thick):
    """Runes, crystal growths and ethereal fragments riding on the blade."""
    kind = style['edge']
    out = []
    if kind == 'runed' and style['rune'] > 0:
        marks = []
        for step in range(2 + style['ornament'] // 2):
            x = reach * (0.28 + 0.15 * step)
            marks.append(('line', [(x, -thick * 0.34), (x, thick * 0.34)], 1.0))
            marks.append(('line', [(x - 1.1, 0.0), (x + 1.1, 0.0)], 1.0))
        out.append(_rune_marks(marks))
    elif kind == 'crystal':
        for step in range(2 + style['ornament'] // 3):
            x = reach * (0.30 + 0.18 * step)
            sign = 1 if step % 2 else -1
            out.append(comp('gem', [poly([(x - 1.6, sign * thick * 0.7), (x + 0.4, sign * (thick + 3.4)),
                                          (x + 2.2, sign * thick * 0.7)])]))
        if style['glow']:
            out.append(_rune_marks([('line', [(reach * 0.3, 0.0), (reach * 0.86, 0.0)], 1.0)]))
    elif kind == 'ethereal':
        for step in range(3):
            x = reach * (0.62 + 0.14 * step)
            out.append(comp('gem', [poly([(x, -thick * 0.5), (x + 2.4, 0.0), (x, thick * 0.5)])]))
        out.append(_rune_marks([('line', [(reach * 0.22, 0.0), (reach * 0.95, 0.0)], 1.0)]))
    return out


def _haft(style, back, front, thick, role='wood'):
    """The shaft plus whatever this tier wraps, bands or grows on it."""
    out = [comp(role, [limb((back, 0), (front, 0), thick, thick * 0.82)],
                [line([(back + 1.0, -thick * 0.26), (front - 1.5, -thick * 0.2)], 1)])]
    kind = style['haft']
    span = front - back
    if kind == 'banded':
        bands = [limb((back + span * (0.18 + 0.28 * step), 0),
                      (back + span * (0.24 + 0.28 * step), 0), thick * 1.25, thick * 1.25)
                 for step in range(3)]
        out.append(comp('trim', bands))
    elif kind == 'langets':
        out.append(comp('trim', [limb((front - span * 0.34, -thick * 0.42), (front - 1.0, -thick * 0.42), 1.5, 1.1),
                                 limb((front - span * 0.34, thick * 0.42), (front - 1.0, thick * 0.42), 1.5, 1.1)]))
        out.append(comp('trim', [limb((back + span * 0.20, 0), (back + span * 0.27, 0), thick * 1.3, thick * 1.3)]))
    elif kind == 'crystal':
        for step in range(2):
            x = back + span * (0.34 + 0.26 * step)
            sign = 1 if step % 2 else -1
            out.append(comp('gem', [poly([(x - 1.4, sign * thick * 0.4), (x + 0.6, sign * (thick + 2.6)),
                                          (x + 1.8, sign * thick * 0.4)])]))
    else:  # wrapped
        wraps = [line([(back + 1.4 + step * 2.0, -thick * 0.6), (back + 0.8 + step * 2.0, thick * 0.6)], 1)
                 for step in range(max(1, int(span * 0.28)))]
        out[0]['details'].extend(wraps)
    return out


def _studs(style, points, radius=1.0):
    if style['ornament'] <= 0:
        return []
    count = min(len(points), 2 + style['ornament'])
    return [comp('trim', [disc(point, radius) for point in points[:count]])]


def sword_parts(style=None, great=False):
    style = resolve(style)
    length = 30.0 if great else 21.0
    half = 3.0 if great else 2.6
    body, details, reach, thick = _blade(style, length, half)
    grip_len = (9.0 if great else 6.4) * (1.0 + style['plume'] * 0.06)
    grip, _ = _grip(grip_len, 2.8)
    parts = [grip]
    parts += _pommel_parts(style, -(grip_len + 0.8))
    parts += _guard_parts(style, 7.4 if great else 5.6)
    parts.append(comp('metal', [body], details))
    parts += _edge_extras(style, reach, thick)
    return parts


def axe_parts(style=None, great=False):
    style = resolve(style)
    reach = (26.0 if great else 20.0) * style['reach']
    parts = _haft(style, -9.0 * style['reach'], reach, 3.0)
    parts += _pommel_parts(style, -(9.6 * style['reach']))
    head_x = reach - (13.0 if great else 10.0)
    breadth = style['breadth'] * (1.18 if great else 1.42)
    kind = style['edge']
    # A single bit sitting to one side of the haft, with a curved cutting edge.
    # Bulk spread evenly around the haft reads as a maul, not an axe.
    if kind == 'toothed':
        face = poly([
            (head_x - 1.2, 1.2), (head_x - 2.2, -4.2 * breadth), (head_x - 1.0, -8.8 * breadth),
            (head_x + 3.6, -11.0 * breadth), (head_x + 6.6, -8.2 * breadth),
            (head_x + 8.0, -10.0 * breadth), (head_x + 10.2, -6.0 * breadth),
            (head_x + 8.0, -3.4 * breadth), (head_x + 9.0, -0.6 * breadth),
            (head_x + 3.2, 1.8),
        ])
    elif kind in ('crystal', 'ethereal'):
        face = poly([
            (head_x - 1.2, 1.2), (head_x - 2.4, -4.6 * breadth), (head_x - 0.8, -9.6 * breadth),
            (head_x + 4.6, -12.0 * breadth), (head_x + 12.4, -6.6 * breadth),
            (head_x + 9.0, -0.8 * breadth), (head_x + 3.2, 1.8),
        ])
    else:
        face = smooth([
            (head_x - 1.2, 1.2), (head_x - 2.2, -4.4 * breadth), (head_x - 1.0, -9.0 * breadth),
            (head_x + 4.0, -11.0 * breadth), (head_x + 9.8, -6.6 * breadth),
            (head_x + 8.6, -1.4 * breadth), (head_x + 3.2, 1.8),
        ], 4)
    parts.append(comp('trim', [limb((head_x - 1.6, 0), (head_x + 1.4, 0), 5.6, 5.0)]))
    parts.append(comp('metal', [face],
                      [line([(head_x + 7.4, -8.6 * breadth), (head_x + 8.6, -2.6 * breadth)], 1),
                       line([(head_x + 1.0, -7.4 * breadth), (head_x + 5.4, -8.4 * breadth)], 1),
                       line([(head_x + 0.6, -3.6 * breadth), (head_x + 5.0, -4.4 * breadth)], 1)]))
    if great:
        parts.append(comp('metal', [smooth([
            (head_x - 1.2, -1.2), (head_x - 2.2, 4.4 * breadth), (head_x - 1.0, 9.0 * breadth),
            (head_x + 4.0, 11.0 * breadth), (head_x + 9.8, 6.6 * breadth),
            (head_x + 8.6, 1.4 * breadth), (head_x + 3.2, -1.8),
        ], 4)], [line([(head_x + 7.4, 8.6 * breadth), (head_x + 8.6, 2.6 * breadth)], 1),
                 line([(head_x + 1.0, 7.4 * breadth), (head_x + 5.4, 8.4 * breadth)], 1)]))
    parts += _studs(style, [(-4.0, 0.0), (2.0, 0.0), (8.0, 0.0)], 1.1)
    if style['rune'] > 0.5:
        parts.append(_rune_marks([('line', [(head_x + 3.0, -5.0), (head_x + 7.4, -3.0)], 1.0)]))
    return parts


def mace_parts(style=None, great=False):
    style = resolve(style)
    reach = (22.0 if great else 17.0) * style['reach']
    parts = _haft(style, -8.0, reach - 4.0, 2.8)
    parts += _pommel_parts(style, -8.8)
    head = reach - 2.0
    breadth = style['breadth']
    flanges = []
    count = 4 if style['guard'] not in ('shards', 'hooked') else 6
    for step in range(count):
        angle = -1.25 + step * (2.5 / max(1, count - 1))
        tipx = head + math.cos(angle) * 5.8 * breadth + 1.0
        tipy = math.sin(angle) * 6.0 * breadth
        if style['edge'] in ('toothed', 'crystal', 'ethereal'):
            flanges.append(poly([(head - 2.0, math.sin(angle) * 2.2), (tipx + 1.6, tipy * 0.9),
                                 (head + 1.4, math.sin(angle) * 3.4)]))
        else:
            flanges.append(poly([(head - 2.0, math.sin(angle) * 2.2), (tipx, tipy * 0.72),
                                 (tipx + 0.6, tipy), (head + 1.4, math.sin(angle) * 3.4)]))
    core = comp('metal', [smooth([(head - 3.2, -3.8 * breadth), (head + 3.6, -3.0 * breadth),
                                  (head + 4.6, 0), (head + 3.6, 3.0 * breadth),
                                  (head - 3.2, 3.8 * breadth)], 5)] + flanges,
                [disc((head, -1.2), 1.3)])
    if great:
        core['shapes'].append(poly([(head + 4.4, -1.4), (head + 9.0, 0.0), (head + 4.4, 1.4)]))
    parts.append(comp('trim', [limb((head - 4.8, 0), (head - 3.0, 0), 4.6, 4.2)]))
    parts.append(core)
    if style['pommel'] == 'gem' or style['rune'] > 0.5:
        parts.append(comp('gem', [disc((head, 0), 2.0)]))
        if style['glow']:
            parts.append(_rune_marks([disc((head, 0), 1.1)]))
    return parts


def spear_parts(style=None, halberd=False):
    style = resolve(style)
    reach = 30.0 * style['reach']
    parts = _haft(style, -12.0, reach - 4.0, 2.6)
    parts += _pommel_parts(style, -12.8)
    tip = reach - 3.0
    breadth = style['breadth']
    kind = style['edge']
    if kind == 'toothed':
        head = smooth([(tip - 3.4, -1.5), (tip - 0.4, -3.0 * breadth), (tip + 2.6, -1.4),
                       (tip + 8.0, 0), (tip + 2.6, 1.4), (tip - 0.4, 3.0 * breadth),
                       (tip - 3.4, 1.5)], 4)
    elif kind in ('crystal', 'ethereal'):
        head = poly([(tip - 3.4, -1.4), (tip + 0.6, -3.4 * breadth), (tip + 8.6, 0),
                     (tip + 0.6, 3.4 * breadth), (tip - 3.4, 1.4)])
    else:
        head = smooth([(tip - 3.0, -1.4), (tip + 1.0, -2.8 * breadth), (tip + 7.8, 0),
                       (tip + 1.0, 2.8 * breadth), (tip - 3.0, 1.4)], 5)
    parts.append(comp('trim', [limb((tip - 4.4, 0), (tip - 2.4, 0), 4.2, 3.6)]))
    if halberd:
        parts.append(comp('metal', [smooth([(tip - 9.4, -1.6), (tip - 6.2, -8.2 * breadth),
                                            (tip - 0.6, -6.8 * breadth), (tip - 1.4, -1.6)], 5)],
                          [line([(tip - 6.6, -6.6), (tip - 1.8, -5.4)], 1)]))
        parts.append(comp('metal', [poly([(tip - 8.2, 1.4), (tip - 3.4, 4.4), (tip - 6.2, 5.6),
                                          (tip - 8.8, 2.6)])]))
    parts.append(comp('metal', [head], [line([(tip - 2.0, 0), (tip + 6.0, 0)], 1)]))
    parts += _edge_extras(style, tip + 8.0, 3.0)
    return parts


def dagger_parts(style=None):
    style = resolve(style)
    body, details, reach, thick = _blade(style, 12.0, 2.2, 1.6)
    grip, _ = _grip(4.6, 2.4)
    parts = [grip]
    parts += _pommel_parts(style, -5.4)
    parts += _guard_parts(style, 3.6)
    parts.append(comp('metal', [body], details))
    parts += _edge_extras(style, reach, thick)
    return parts


def bow_parts(style=None, cross=False):
    style = resolve(style)
    stretch = style['reach']
    if cross:
        stock = comp('wood', [poly([(-7.0, -1.6), (13.0, -2.4), (14.4, 0.4), (12.0, 2.6), (-6.0, 2.4)])],
                     [line([(-5.0, 0.4), (11.0, -0.2)], 1)])
        prod = comp('metal', [limb((8.0, -9.6 * stretch), (8.6, 9.6 * stretch), 2.2, 2.2)],
                    [line([(8.4, -8.0 * stretch), (8.4, 8.0 * stretch)], 1)])
        string = comp('string', [line([(8.2, -9.0 * stretch), (2.0, 0.0), (8.2, 9.0 * stretch)], 1)])
        lock = comp('trim', [poly([(1.0, -2.2), (4.4, -2.2), (4.4, 2.2), (1.0, 2.2)])])
        parts = [prod, string, stock, lock]
        parts += _studs(style, [(6.0, 0.0), (10.0, -0.6), (-3.0, 0.4)], 0.9)
        if style['rune'] > 0.5:
            parts.append(_rune_marks([('line', [(0.0, 0.0), (11.0, -0.4)], 1.0)]))
        return parts
    span = 15.0 * stretch
    if style['guard'] in ('wings', 'shards'):
        limbs = comp('wood', [smooth([
            (0.4, -span), (7.4, -span * 0.52), (9.6, 0.0), (7.4, span * 0.52), (0.4, span),
            (2.6, span * 0.94), (10.4, span * 0.50), (12.6, 0.0), (10.4, -span * 0.50), (2.6, -span * 0.94)], 7)],
            [line([(10.6, -span * 0.60), (11.4, 0.0), (10.6, span * 0.60)], 1)])
    else:
        limbs = comp('wood', [smooth([
            (0.4, -span), (6.4, -span * 0.55), (8.4, 0.0), (6.4, span * 0.55), (0.4, span),
            (2.4, span * 0.95), (9.2, span * 0.52), (11.2, 0.0), (9.2, -span * 0.52), (2.4, -span * 0.95)], 7)],
            [line([(9.4, -span * 0.62), (10.2, 0.0), (9.4, span * 0.62)], 1)])
    string = comp('string', [line([(1.0, -span), (0.2, 0.0), (1.0, span)], 1)])
    grip = comp('grip', [limb((9.4, -4.0), (9.4, 4.0), 5.0, 5.0)],
                [line([(7.6, -2.4), (11.2, -2.4)], 1), line([(7.6, 2.0), (11.2, 2.0)], 1)])
    parts = [string, limbs, grip]
    parts.append(comp('trim', [limb((2.4, -span * 0.94), (3.2, -span * 0.80), 4.0, 3.4),
                               limb((3.2, span * 0.80), (2.4, span * 0.94), 3.4, 4.0)]))
    if style['edge'] in ('crystal', 'ethereal'):
        for sign in (-1, 1):
            parts.append(comp('gem', [poly([(6.0, sign * span * 0.58), (11.6, sign * span * 0.70),
                                            (5.0, sign * span * 0.82)])]))
    if style['rune'] > 0.5:
        parts.append(_rune_marks([('line', [(4.8, -span * 0.7), (5.2, span * 0.7)], 1.0)]))
    return parts


def staff_parts(style=None, wand=False):
    style = resolve(style)
    stretch = style['reach']
    if wand:
        parts = _haft(style, -4.0, 11.0 * stretch, 2.6)
        parts += _pommel_parts(style, -4.8)
        cap = comp('trim', [limb((9.6 * stretch, 0), (12.0 * stretch, 0), 2.9, 2.3)])
        stone = comp('gem', [disc((14.0 * stretch, 0), 2.9)], [disc((13.0 * stretch, -0.9), 1.2)])
        parts += [cap, stone]
        if style['glow']:
            parts.append(_rune_marks([disc((14.0 * stretch, 0), 1.5)]))
        return parts
    parts = _haft(style, -13.0, 22.0 * stretch, 3.0)
    parts += _pommel_parts(style, -13.8)
    parts.append(comp('grip', [limb((-2.0, 0), (3.0, 0), 3.9, 3.7)],
                      [line([(-1.4, -1.9), (-2.0, 1.9)], 1), line([(1.4, -1.9), (0.8, 1.9)], 1)]))
    top = 21.0 * stretch
    crown_kind = style['crest']
    if crown_kind in ('shards', 'halo'):
        for sign, reach in ((-1, 1.0), (1, 0.86), (-1, 0.6)):
            parts.append(comp('gem', [poly([(top - 0.6, sign * 1.6), (top + 3.6, sign * 6.4 * reach),
                                            (top + 5.2, sign * 1.8)])]))
        parts.append(comp('trim', [limb((top - 1.6, 0), (top + 0.6, 0), 4.4, 4.0)]))
    elif crown_kind in ('fin', 'comb', 'horns'):
        parts.append(comp('metal', [smooth([(top, -2.0), (top + 2.6, -6.0), (top + 6.8, -2.6),
                                            (top + 7.2, 2.6), (top + 2.6, 6.0), (top, 2.0)], 5)]))
    else:
        parts.append(comp('metal', [('ring', (top + 3.4, 0), 5.2, 1.8)]))
    parts.append(comp('gem', [disc((top + 3.4, 0), 3.1)], [disc((top + 2.4, -1.0), 1.3)]))
    if style['glow']:
        parts.append(_rune_marks([disc((top + 3.4, 0), 1.7)]))
    return parts


def knuckle_parts(style=None):
    style = resolve(style)
    breadth = style['breadth']
    reach = 7.5 * breadth
    bar = comp('metal', [smooth([(-1.6, -reach), (4.2, -reach * 0.92), (5.6, 0),
                                 (4.2, reach * 0.92), (-1.6, reach), (-3.4, 0)], 5)],
               [line([(0.4, -reach * 0.6), (0.4, reach * 0.6)], 1)])
    holes = comp('grip', [disc((0.6, -reach * 0.52), 1.7), disc((0.6, -reach * 0.17), 1.7),
                          disc((0.6, reach * 0.17), 1.7), disc((0.6, reach * 0.52), 1.7)])
    knobs = []
    for offset in (-0.55, -0.18, 0.18, 0.55):
        y = reach * offset
        if style['edge'] in ('toothed', 'crystal', 'ethereal'):
            knobs.append(poly([(4.8, y - 1.5), (9.6, y), (4.8, y + 1.5)]))
        else:
            knobs.append(disc((5.4, y), 1.9))
    studs = comp('trim', knobs, [disc((5.0, -reach * 0.55), 0.6), disc((5.0, reach * 0.14), 0.6)])
    wrap = comp('grip', [limb((-3.6, -reach * 0.7), (-3.6, reach * 0.7), 3.8, 3.8)])
    parts = [wrap, bar, holes, studs]
    if style['rune'] > 0.5:
        parts.append(_rune_marks([('line', [(-1.0, -2.6), (3.4, -2.6)], 1.0),
                                  ('line', [(-1.0, 2.6), (3.4, 2.6)], 1.0)]))
    return parts


def shield_parts(item, style=None):
    """A boss, a rim and rivets. Broad cross bands read as a flag, not a shield."""
    style = resolve(style)
    tags = set(item.get('tags', ())) if isinstance(item, dict) else set()
    heavy = 'heavy' in tags or style['tier'] >= 4
    breadth = style['breadth']
    if style['guard'] in ('shards',):
        face = poly([(0.0, -10.0 * breadth), (7.6, -6.0), (8.8, 2.0), (0.0, 11.0 * breadth),
                     (-8.8, 2.0), (-7.6, -6.0)])
        rim = comp('trim', [poly([(0.0, -10.8 * breadth), (8.3, -6.2), (9.6, 2.2),
                                  (0.0, 11.9 * breadth), (-9.6, 2.2), (-8.3, -6.2)]),
                            ('poly', catmull([(0.0, -8.8 * breadth), (6.4, -5.4), (7.4, 1.8),
                                              (0.0, 9.4 * breadth), (-7.4, 1.8), (-6.4, -5.4)],
                                             5, closed=True))])
    elif heavy:
        face = smooth([(-1.0, -9.0 * breadth), (6.0, -8.2), (8.2, -2.0), (5.0, 8.0),
                       (-1.0, 10.6 * breadth), (-6.6, 8.0), (-8.6, -2.0), (-6.0, -8.2)], 6)
        rim = comp('trim', [smooth([(-1.0, -9.6 * breadth), (6.6, -8.8), (8.9, -2.0), (5.4, 8.6),
                                    (-1.0, 11.3 * breadth), (-7.2, 8.6), (-9.3, -2.0), (-6.6, -8.8)], 6),
                            ('poly', catmull([(-1.0, -8.0 * breadth), (5.2, -7.2), (7.2, -2.0),
                                              (4.4, 7.2), (-1.0, 9.4 * breadth), (-5.8, 7.2),
                                              (-7.6, -2.0), (-5.2, -7.2)], 6, closed=True))])
    else:
        face = ('disc', (0.0, 0.0), 8.4 * breadth)
        rim = comp('trim', [('ring', (0.0, 0.0), 9.2 * breadth, 1.6)])
    body = comp('metal', [face], [line([(-5.6, -3.6), (4.6, -4.2)], 1),
                                  line([(-4.4, 4.6), (4.0, 4.0)], 1)])
    boss_kind = style['pommel']
    if boss_kind in ('faceted', 'gem'):
        boss = comp('gem', [poly([(0.0, -3.4), (3.0, 0.0), (0.0, 3.4), (-3.0, 0.0)])],
                    [poly([(0.0, -2.2), (1.3, -0.3), (-1.2, -0.3)])])
    elif boss_kind == 'spike':
        boss = comp('trim', [poly([(0.0, -4.4), (2.6, 2.0), (-2.6, 2.0)])])
    else:
        boss = comp('trim', [disc((0.0, 0.0), 2.9)], [disc((-0.8, -0.9), 1.1)])
    rivets = comp('trim', [disc((-5.4, -5.0), 1.0), disc((5.4, -5.0), 1.0),
                           disc((-5.4, 5.0), 1.0), disc((5.4, 5.0), 1.0)])
    parts = [body, rim, boss, rivets]
    if style['plume'] > 0.4:
        for sign in (-1, 1):
            parts.append(comp('trim', [poly([(sign * 7.0, -6.0), (sign * (10.0 + style['plume'] * 3), -9.0),
                                             (sign * 8.4, -2.0)])]))
    if style['glow']:
        parts.append(_rune_marks([('ring', (0.0, 0.0), 6.2, 1.0)]))
    return parts


def focus_parts(kind, style=None):
    style = resolve(style)
    if kind == 'quiver':
        case = comp('grip', [smooth([(-3.4, -8.0), (3.4, -8.0), (2.8, 7.6), (-2.8, 7.6)], 5)],
                    [line([(-2.4, -4.0), (2.4, -4.0)], 1), line([(-2.4, 3.0), (2.4, 3.0)], 1)])
        shafts = comp('wood', [limb((-1.8, -8.0), (-1.8, -13.0), 1.4, 1.4),
                               limb((0.4, -8.0), (0.8, -13.6), 1.4, 1.4),
                               limb((2.4, -8.0), (3.2, -12.6), 1.4, 1.4)])
        fletch = comp('trim', [poly([(-2.6, -12.0), (-1.0, -13.4), (-1.0, -11.2)]),
                               poly([(0.0, -12.6), (1.6, -14.0), (1.6, -11.8)]),
                               poly([(2.2, -11.6), (3.8, -13.0), (3.8, -10.8)])])
        parts = [case, shafts, fletch]
        parts += _studs(style, [(-2.0, 0.0), (2.0, 0.4), (0.0, 5.6)], 0.9)
        return parts
    if kind == 'tome':
        cover = comp('book', [poly([(-6.4, -8.0), (6.4, -8.0), (6.4, 8.0), (-6.4, 8.0)])],
                     [line([(-4.4, -6.4), (-4.4, 6.4)], 1)])
        pages = comp('paper', [poly([(-4.0, -6.4), (5.6, -6.4), (5.6, 6.4), (-4.0, 6.4)])],
                     [line([(-2.4, -4.0), (4.0, -4.0)], 1), line([(-2.4, -1.0), (4.0, -1.0)], 1),
                      line([(-2.4, 2.0), (4.0, 2.0)], 1)])
        parts = [cover, pages, comp('trim', [disc((5.6, 0.0), 1.7)])]
        if style['pommel'] == 'gem':
            parts.append(comp('gem', [poly([(0.6, -2.4), (3.0, 0.0), (0.6, 2.4), (-1.8, 0.0)])]))
        if style['glow']:
            parts.append(_rune_marks([('line', [(-2.0, 5.2), (4.4, 5.2)], 1.0)]))
        return parts
    if kind == 'orb':
        parts = [comp('gem', [disc((0.0, 0.0), 7.0 * style['breadth'])],
                      [disc((-2.2, -2.6), 2.4), disc((2.4, 2.6), 1.2)]),
                 comp('trim', [limb((-5.4, 5.6), (5.4, 5.6), 2.6, 2.6)])]
        if style['crest'] in ('shards', 'halo'):
            for angle in (-2.4, -0.7, 0.9):
                parts.append(comp('trim', [poly([(math.cos(angle) * 6.0, math.sin(angle) * 6.0),
                                                 (math.cos(angle) * 10.4, math.sin(angle) * 10.4),
                                                 (math.cos(angle + 0.4) * 6.4, math.sin(angle + 0.4) * 6.4)])]))
        if style['glow']:
            parts.append(_rune_marks([disc((0.0, 0.0), 3.4)]))
        return parts
    # focus: a ring on a haft
    parts = [comp('wood', [limb((0.0, 7.0), (0.0, -2.0), 2.8, 2.2)]),
             comp('metal', [('ring', (0.0, -6.0), 5.4 * style['breadth'], 1.8)]),
             comp('gem', [disc((0.0, -6.0), 2.3)], [disc((-0.7, -6.9), 0.9)])]
    if style['crest'] in ('shards', 'halo', 'fin'):
        for sign in (-1, 1):
            parts.append(comp('trim', [poly([(sign * 4.6, -9.0), (sign * 8.0, -12.4), (sign * 6.4, -7.6)])]))
    if style['glow']:
        parts.append(_rune_marks([('ring', (0.0, -6.0), 3.4, 1.0)]))
    return parts

TOOL_PROFILES = {
    'pickaxe': lambda style=None: [comp('wood', [limb((-8.0, 0), (12.0, 0), 2.8, 2.4)]),
                        comp('metal', [smooth([(6.0, -7.4), (11.0, -1.6), (16.4, -6.6), (14.6, -8.6),
                                               (11.0, -4.0), (7.4, -8.6)], 5)]),
                        comp('trim', [limb((10.0, -2.0), (12.0, -2.0), 4.4, 4.0)])],
    'rod': lambda style=None: [comp('wood', [limb((-8.0, 0), (20.0, 0), 2.6, 1.4)]),
                    comp('trim', [disc((-8.6, 0), 1.8), disc((6.0, 0), 1.4)]),
                    comp('string', [line([(20.0, 0.4), (22.0, 7.0), (19.0, 12.0)], 1)])],
    'sickle': lambda style=None: [comp('grip', [limb((-6.0, 0), (1.0, 0), 3.0, 2.8)]),
                       comp('metal', [smooth([(1.0, -1.6), (8.0, -6.6), (14.0, -2.0), (12.0, 2.6),
                                              (8.0, -2.6), (2.0, 1.8)], 6)])],
    'shovel': lambda style=None: [comp('wood', [limb((-9.0, 0), (9.0, 0), 2.8, 2.4)]),
                       comp('metal', [smooth([(9.0, -4.4), (14.0, -4.0), (16.6, 0), (14.0, 4.0),
                                              (9.0, 4.4)], 5)], [line([(11.0, -2.4), (14.4, 0)], 1)]),
                       comp('trim', [disc((-9.6, 0), 2.0)])],
    'knife': dagger_parts,
    'hammer': lambda style=None: [comp('wood', [limb((-8.0, 0), (11.0, 0), 2.8, 2.4)]),
                       comp('metal', [poly([(8.0, -4.6), (16.0, -4.0), (16.0, 4.0), (8.0, 4.6)])],
                            [line([(14.0, -3.0), (14.0, 3.0)], 1)]),
                       comp('trim', [disc((-8.6, 0), 2.0)])],
}


WEAPON_PROFILES = {
    'sword': lambda style=None: sword_parts(style, False),
    'greatsword': lambda style=None: sword_parts(style, True),
    'axe': lambda style=None: axe_parts(style, False),
    'greataxe': lambda style=None: axe_parts(style, True),
    'mace': lambda style=None: mace_parts(style, False),
    'greatmace': lambda style=None: mace_parts(style, True),
    'spear': lambda style=None: spear_parts(style, False),
    'halberd': lambda style=None: spear_parts(style, True),
    'dagger': lambda style=None: dagger_parts(style),
    'bow': lambda style=None: bow_parts(style, False),
    'crossbow': lambda style=None: bow_parts(style, True),
    'staff': lambda style=None: staff_parts(style, False),
    'wand': lambda style=None: staff_parts(style, True),
    'knuckles': lambda style=None: knuckle_parts(style),
}
WEAPON_PROFILES.update(TOOL_PROFILES)

OFFHAND_PROFILES = ('shield', 'quiver', 'focus', 'orb', 'tome')


def profile_for(item):
    style = gear.style_of(item)
    tags = [t for t in item.get('tags', ()) if t in WEAPON_PROFILES]
    if tags:
        return WEAPON_PROFILES[tags[0]](style)
    for tag in item.get('tags', ()):
        if tag in OFFHAND_PROFILES:
            return shield_parts(item, style) if tag == 'shield' else focus_parts(tag, style)
    if item.get('slot') == 'offhand':
        return shield_parts(item, style)
    return sword_parts(style, False)


# ---------------------------------------------------------------- palette --

WOODS = ('oak', 'ash', 'yew', 'ironwood', 'blackwood', 'elderwood', 'emberwood', 'starwood')


def role_ramps(item):
    """Ramps per drawing role, taken from the item's own material where it has
    one and from its rung of the equipment ladder otherwise."""
    tier = gear.tier_of(item)
    material = item.get('material', 'iron')
    body = gear.body_colour(item)
    wood = pigment.MATERIALS.get(material) if material in WOODS else tier.wood
    element = item.get('element', 'Physical')
    gem = tier.gem if item.get('material') in gear.BY_KEY or element == 'Physical'         else pigment.ELEMENTS.get(element, tier.gem)
    return {
        'metal': ramp(body), 'wood': ramp(wood), 'grip': ramp(tier.leather),
        'trim': ramp(tier.trim), 'gem': ramp(gem), 'string': ramp('#cdc3a6'),
        'book': ramp(tier.leather), 'paper': ramp('#d3c7a6'), 'cloth': ramp(tier.cloth),
        'rune': ramp(tier.glow or gem),
    }


# -------------------------------------------------------------- rendering --

def _transform(points, origin, angle, scale, flip):
    ca, sa = math.cos(angle), math.sin(angle)
    out = []
    for x, y in points:
        y = y * flip
        out.append((origin[0] + (x * ca - y * sa) * scale, origin[1] + (x * sa + y * ca) * scale))
    return out


def _shape_points(shape):
    kind = shape[0]
    if kind == 'poly':
        return list(shape[1])
    if kind == 'line':
        return list(shape[1])
    if kind == 'disc':
        cx, cy = shape[1]
        r = shape[2]
        return [(cx - r, cy - r), (cx + r, cy + r)]
    if kind == 'ring':
        cx, cy = shape[1]
        r = shape[2]
        return [(cx - r, cy - r), (cx + r, cy + r)]
    return []


def _apply(piece, shape, origin, angle, scale, flip, colour):
    kind = shape[0]
    if kind == 'poly':
        piece.poly(_transform(shape[1], origin, angle, scale, flip), colour)
    elif kind == 'line':
        width = max(1, round(shape[2] * scale))
        piece.line(_transform(shape[1], origin, angle, scale, flip), colour, width)
    elif kind == 'disc':
        cx, cy = _transform([shape[1]], origin, angle, scale, flip)[0]
        piece.disc(cx, cy, max(0.7, shape[2] * scale), colour)
    elif kind == 'ring':
        cx, cy = _transform([shape[1]], origin, angle, scale, flip)[0]
        r = shape[2] * scale
        piece.disc(cx, cy, r, colour)
        piece.erase_ellipse((cx - r + shape[3] * scale, cy - r + shape[3] * scale,
                             cx + r - shape[3] * scale, cy + r - shape[3] * scale))


# How each material catches the light: polished metal takes a hard specular,
# leather and cloth take almost none, a cut gem takes the most of all.
SURFACE = {
    'metal': dict(gleam=0.60, form=0.46, rim=0.95, occlude=0.85),
    'trim': dict(gleam=0.55, form=0.44, rim=0.95, occlude=0.80),
    'gem': dict(gleam=0.80, form=0.55, rim=1.0, occlude=0.75),
    'wood': dict(gleam=0.20, form=0.40, rim=0.75, occlude=0.80),
    'grip': dict(gleam=0.12, form=0.34, rim=0.65, occlude=0.85),
    'cloth': dict(gleam=0.10, form=0.38, rim=0.70, occlude=0.80),
    'book': dict(gleam=0.22, form=0.40, rim=0.80, occlude=0.85),
    'paper': dict(gleam=0.10, form=0.32, rim=0.70, occlude=0.70),
    'string': dict(gleam=0.0, form=0.0, rim=0.7, occlude=0.5),
    'rune': dict(gleam=0.0, form=0.0, rim=0.0, occlude=0.0, outline=False),
}


def render_parts(sketch, parts, ramps, origin, angle=0.0, scale=1.0, flip=1, rim=None, occlude=None):
    for component in parts:
        role = component['role']
        tone = ramps.get(role, ramps['metal'])
        piece = sketch.piece(tone)
        for shape in component['shapes']:
            _apply(piece, shape, origin, angle, scale, flip, 3)
        if not component['shapes']:
            continue
        detail = sketch.piece(tone)
        for shape in component['details']:
            _apply(detail, shape, origin, angle, scale, flip, 5 if shape[0] != 'disc' else 5)
        detail.clip(piece)
        surface = dict(SURFACE.get(role, SURFACE['metal']))
        if role == 'rune':
            for shape in component['shapes']:
                _apply(piece, shape, origin, angle, scale, flip, 5)
        if rim is not None:
            surface['rim'] = rim
        if occlude is not None:
            surface['occlude'] = occlude
        sketch.carve(piece, **surface)
        sketch.overlay(detail)
    return sketch


def parts_bounds(parts):
    xs, ys = [], []
    for component in parts:
        for shape in component['shapes']:
            for x, y in _shape_points(shape):
                xs.append(x)
                ys.append(y)
    if not xs:
        return (0, 0, 1, 1)
    return min(xs), min(ys), max(xs), max(ys)


def hold(sketch, item, hand, angle, pose):
    """Place a weapon or off-hand item in the rig's hand."""
    parts = profile_for(item)
    ramps = role_ramps(item)
    tags = set(item.get('tags', ()))
    scale = 0.92
    if 'two_handed' in tags:
        # a great weapon is long, not wide; at full icon scale the head eats the figure
        scale = 0.82
        if pose.state in ('idle', 'walk', 'hit'):
            # carried on the shoulder at rest, not dragged head-down through the dirt
            hand = (hand[0] - pose.facing * 1.0, hand[1] - 7.5)
            angle = angle - 0.55 * (1 if pose.facing >= 0 else -1)
    if 'bow' in tags:
        angle = angle - math.pi / 2
    if item.get('slot') == 'offhand' and not tags & {'quiver', 'tome'}:
        # A shield rides on the forearm; at full icon scale it swallows the figure.
        angle = 0.0
        scale = 0.60 if 'shield' in tags or not tags & set(OFFHAND_PROFILES) else 0.70
    flip = -1 if pose.facing < 0 else 1
    scale = _fit_to_frame(parts, hand, angle, scale, flip, sketch.size)
    render_parts(sketch, parts, ramps, hand, angle, scale, flip)
    _aura(sketch, item, 0.8)
    return sketch


# ------------------------------------------------------------------ icons --

LONGEST = 46.0   # roughly a halberd; the yardstick for relative icon scale


def _fit(parts, target=27.0, centre=(16.0, 16.0), angle=-math.pi / 4, relative=True):
    """Fit into the tile, but keep weapons in proportion to each other.

    Fitting every weapon to the same box makes a dagger and a greatsword the
    same size on the hotbar, which is exactly the sameness that makes a set look
    lazy. Small arms keep some of that shrink so they stay readable.
    """
    x0, y0, x1, y1 = parts_bounds(parts)
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    rotated = _transform(corners, (0, 0), angle, 1.0, 1)
    rx0 = min(p[0] for p in rotated)
    rx1 = max(p[0] for p in rotated)
    ry0 = min(p[1] for p in rotated)
    ry1 = max(p[1] for p in rotated)
    span = max(rx1 - rx0, ry1 - ry0, 1.0)
    scale = min(1.35, target / span)
    if relative:
        scale *= 0.58 + 0.42 * min(1.0, span / LONGEST)
    origin = (centre[0] - (rx0 + rx1) / 2 * scale, centre[1] - (ry0 + ry1) / 2 * scale)
    return origin, scale


def weapon_icon(item):
    sketch = Sketch(ICON)
    parts = profile_for(item)
    ramps = role_ramps(item)
    tags = set(item.get('tags', ()))
    angle = -math.pi / 4
    relative = True
    if 'bow' in tags or 'crossbow' in tags or item.get('slot') == 'offhand' or tags & set(OFFHAND_PROFILES):
        angle = 0.0
        relative = 'bow' in tags or 'crossbow' in tags
    origin, scale = _fit(parts, 27.0, (16.0, 16.5), angle, relative)
    render_parts(sketch, parts, ramps, origin, angle, scale, 1)
    _aura(sketch, item)
    return sketch.result()


def _fit_to_frame(parts, origin, angle, scale, flip, size, margin=1.0):
    """Shrink a held weapon until it stops running past the sprite border.

    A greatsword swung forward at icon scale reaches outside a 64px frame and
    gets its point sliced off, which looks like a bug rather than a big sword.
    """
    x0, y0, x1, y1 = parts_bounds(parts)
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    width, height = size
    for _ in range(8):
        points = _transform(corners, origin, angle, scale, flip)
        if (min(p[0] for p in points) >= -margin
                and max(p[0] for p in points) <= width + margin
                and min(p[1] for p in points) >= -margin
                and max(p[1] for p in points) <= height + margin):
            break
        scale *= 0.90
    return scale


def _aura(sketch, item, strength=1.0):
    """Only enchanted rungs of the ladder glow; a copper sword is just metal."""
    tier = gear.tier_of(item)
    if tier.glow:
        sketch.glow(tier.glow, radius=3, strength=0.46 * strength)
        return
    element = item.get('element', 'Physical')
    if element not in ('Physical', '') and tier.index >= 5:
        sketch.glow(pigment.ELEMENTS.get(element, '#c6b9a4'), radius=2, strength=0.26 * strength)


# -- armour icons ----------------------------------------------------------

def _crest(sketch, tone, gemtone, style, x, top):
    """The thing on top of a helm. It is what tells two helms apart at a glance."""
    kind = style['crest']
    plume = style['plume']
    if kind == 'none':
        return
    piece = sketch.piece(tone)
    if kind == 'ridge':
        piece.poly([(x - 5, top + 2), (x, top - 3), (x + 5, top + 2), (x, top)], 4)
    elif kind == 'fin':
        piece.poly(catmull([(x - 4, top + 3), (x - 1, top - 6 - plume * 3),
                            (x + 5, top - 1), (x + 1, top + 2)], 4, closed=True), 4)
    elif kind == 'comb':
        piece.poly(catmull([(x - 6, top + 3), (x - 3, top - 5 - plume * 3), (x, top - 7 - plume * 3),
                            (x + 3, top - 5 - plume * 3), (x + 6, top + 3), (x, top + 1)],
                           5, closed=True), 4)
    elif kind == 'horns':
        for sign in (-1, 1):
            piece.poly(catmull([(x + sign * 4, top + 3), (x + sign * 10, top - 2 - plume * 2),
                                (x + sign * 12, top + 4), (x + sign * 7, top + 4)], 5, closed=True), 3)
    elif kind == 'halo':
        piece.disc(x, top - 4 - plume * 2, 8, 4)
        piece.erase_ellipse((x - 6, top - 10 - plume * 2, x + 6, top + 2 - plume * 2))
    elif kind == 'shards':
        for dx, height in ((-5, 5), (0, 9 + plume * 2), (5, 6)):
            piece.poly([(x + dx - 2, top + 3), (x + dx, top - height), (x + dx + 2, top + 3)], 4)
    sketch.carve(piece, rim=0.9, occlude=0.7)
    if kind in ('halo', 'shards') and style['glow']:
        spark = sketch.piece(gemtone)
        spark.disc(x, top - 3, 2.0, 5)
        sketch.stamp(spark, outline=False, rim=0, occlude=0)


def _pauldrons(sketch, tone, style, left, right, y):
    kind = style['pauldron']
    plume = style['plume']
    piece = sketch.piece(tone)
    for x, sign in ((left, -1), (right, 1)):
        if kind == 'winged':
            piece.poly(catmull([(x, y + 4), (x + sign * 2, y - 3),
                                (x + sign * (5 + plume * 3), y - 6 - plume * 2),
                                (x + sign * 4, y + 2), (x + sign * 2, y + 5)], 5, closed=True), 3)
        elif kind == 'spiked':
            piece.poly([(x - 3, y + 4), (x, y - 4), (x + sign * 7, y - 7), (x + sign * 4, y + 1),
                        (x + 3, y + 5)], 3)
        elif kind == 'layered':
            for step in range(2):
                piece.poly(catmull([(x - 4, y + 1 + step * 4), (x, y - 3 + step * 4),
                                    (x + 4, y + 1 + step * 4), (x, y + 3 + step * 4)],
                                   4, closed=True), 3)
        elif kind == 'crystal':
            piece.poly([(x - 4, y + 4), (x - 1, y - 7 - plume), (x + 3, y - 2), (x + 4, y + 4)], 3)
        elif kind == 'ridged':
            piece.poly(catmull([(x - 4, y + 4), (x, y - 4), (x + 4, y + 4), (x, y + 2)], 4, closed=True), 3)
        else:
            piece.ellipse((x - 4, y - 4, x + 4, y + 4), 3)
    sketch.carve(piece, rim=0.9, occlude=0.75)


def _armour_icon(item):
    slot = item.get('slot')
    style = gear.style_of(item)
    ramps = role_ramps(item)
    tone, trim, gemtone = ramps['metal'], ramps['trim'], ramps['gem']
    tags = item.get('tags', ())
    heavy = 'heavy' in tags
    medium = 'medium' in tags
    ornament = style['ornament']
    sketch = Sketch(ICON)

    if slot == 'helmet':
        piece = sketch.piece(tone)
        if heavy:
            piece.poly(catmull([(6, 24), (5, 13), (10, 4), (22, 4), (27, 13), (26, 24),
                                (21, 26), (16, 24), (11, 26)], 6, closed=True), 3)
        elif medium:
            piece.poly(catmull([(6, 23), (6, 12), (11, 5), (21, 5), (26, 12), (26, 23),
                                (20, 20), (16, 22), (12, 20)], 6, closed=True), 3)
        else:
            piece.poly(catmull([(7, 22), (6, 12), (11, 5), (21, 5), (26, 12), (25, 22),
                                (21, 14), (16, 12), (11, 14)], 6, closed=True), 3)
        sketch.carve(piece, rim=0.95, occlude=0.8, form=0.5)
        if heavy:
            slot_piece = sketch.piece(tone)
            slot_piece.rect((9, 13, 23, 16), (22, 19, 26, 255))
            slot_piece.rect((15, 16, 17, 22), (22, 19, 26, 255))
            slot_piece.clip(piece)
            sketch.overlay(slot_piece)
        elif medium:
            nasal = sketch.piece(trim)
            nasal.poly([(14, 10), (18, 10), (17, 22), (15, 22)], 3)
            sketch.carve(nasal, rim=0.85, occlude=0.6)
        else:
            band = sketch.piece(trim)
            band.poly([(6, 12), (26, 12), (26, 15), (6, 15)], 3)
            sketch.carve(band, rim=0.85, occlude=0.6)
        _crest(sketch, trim, gemtone, style, 16, 4)
        if ornament:
            rivets = sketch.piece(trim)
            for index in range(min(4, ornament)):
                rivets.disc(8 + index * 5, 21, 1.2, 4)
            rivets.clip(piece)
            sketch.overlay(rivets)

    elif slot == 'chest':
        piece = sketch.piece(tone)
        if heavy:
            piece.poly(catmull([(10, 6), (16, 4), (22, 6), (25, 12), (23, 17), (24, 26),
                                (16, 28), (8, 26), (9, 17), (7, 12)], 6, closed=True), 3)
        elif medium:
            piece.poly(catmull([(10, 6), (16, 5), (22, 6), (24, 12), (23, 26), (16, 28),
                                (9, 26), (8, 12)], 6, closed=True), 3)
        else:
            piece.poly(catmull([(11, 5), (16, 7), (21, 5), (25, 13), (26, 27), (16, 29),
                                (6, 27), (7, 13)], 6, closed=True), 3)
        sketch.carve(piece, rim=0.95, occlude=0.8, form=0.55)
        detail = sketch.piece(tone)
        if heavy:
            detail.line([(16, 8), (16, 26)], 1, 1)
            detail.line([(10, 15), (22, 15)], 1, 1)
            detail.line([(11, 13), (21, 13)], 5, 1)
        elif medium:
            for row in range(4):
                y = 10 + row * 4
                for column in range(4):
                    detail.disc(11 + column * 3.4 + (1.7 if row % 2 else 0), y, 1.6, 4)
                    detail.disc(11 + column * 3.4 + (1.7 if row % 2 else 0), y + 0.8, 1.2, 1)
        else:
            detail.line(catmull([(12, 7), (16, 12), (20, 7)], 4), 1, 1)
            detail.line([(16, 11), (16, 28)], 1, 1)
            detail.line([(9, 20), (23, 20)], 1, 1)
        detail.clip(piece)
        sketch.overlay(detail)
        if style['skirt'] != 'none':
            skirt = sketch.piece(trim)
            drop = 30 if style['skirt'] == 'long' else 28
            skirt.poly(catmull([(9, 24), (23, 24), (24, drop), (16, drop - 2), (8, drop)],
                               5, closed=True), 3)
            sketch.carve(skirt, rim=0.85, occlude=0.7)
        if heavy or medium:
            _pauldrons(sketch, trim, style, 8, 24, 10)
        if style['rune'] > 0.4 or style['pommel'] == 'gem':
            stone = sketch.piece(gemtone)
            stone.poly([(16, 12), (19, 16), (16, 20), (13, 16)], 3)
            stone.poly([(16, 14), (17.6, 16), (16, 18), (14.4, 16)], 5)
            sketch.carve(stone, rim=1.0, occlude=0.6)

    elif slot == 'gloves':
        piece = sketch.piece(tone)
        piece.poly(catmull([(9, 26), (8, 14), (12, 8), (16, 7), (21, 9), (23, 15),
                            (23, 26), (16, 28)], 6, closed=True), 3)
        sketch.carve(piece, rim=0.95, occlude=0.8, form=0.5)
        cuff = sketch.piece(trim)
        cuff.poly([(8, 22), (24, 22), (24, 27), (8, 27)], 3)
        sketch.carve(cuff, rim=0.9, occlude=0.7)
        knuckles = sketch.piece(trim)
        for index in range(3):
            x = 11 + index * 4.4
            if style['pauldron'] in ('spiked', 'crystal'):
                knuckles.poly([(x - 2, 14), (x, 8), (x + 2, 14)], 3)
            else:
                knuckles.disc(x, 12, 2.0, 3)
        sketch.carve(knuckles, rim=0.9, occlude=0.6)

    elif slot == 'legs':
        piece = sketch.piece(tone)
        piece.poly(catmull([(9, 4), (23, 4), (25, 11), (22, 28), (18, 28), (16, 16),
                            (14, 28), (10, 28), (7, 11)], 6, closed=True), 3)
        sketch.carve(piece, rim=0.95, occlude=0.8, form=0.5)
        belt = sketch.piece(trim)
        belt.poly([(8, 4), (24, 4), (24, 8), (8, 8)], 3)
        sketch.carve(belt, rim=0.9, occlude=0.7)
        knee = sketch.piece(trim)
        for x in (12, 20):
            if style['pauldron'] in ('spiked', 'crystal'):
                knee.poly([(x - 3, 20), (x, 13), (x + 3, 20)], 3)
            else:
                knee.ellipse((x - 3, 15, x + 3, 21), 3)
        sketch.carve(knee, rim=0.9, occlude=0.65)

    elif slot == 'boots':
        piece = sketch.piece(tone)
        piece.poly(catmull([(10, 5), (20, 5), (21, 17), (27, 21), (27, 27), (8, 27), (9, 17)],
                           6, closed=True), 3)
        sketch.carve(piece, rim=0.95, occlude=0.8, form=0.5)
        cuff = sketch.piece(trim)
        cuff.poly([(9, 5), (21, 5), (21, 10), (9, 10)], 3)
        sketch.carve(cuff, rim=0.9, occlude=0.7)
        if style['pauldron'] in ('winged', 'crystal'):
            wing = sketch.piece(trim)
            wing.poly([(9, 15), (2, 11), (4, 18)], 3)
            sketch.carve(wing, rim=0.9, occlude=0.6)

    elif slot == 'belt':
        strap = sketch.piece(tone)
        strap.poly([(3, 13), (29, 13), (29, 20), (3, 20)], 3)
        sketch.carve(strap, rim=0.9, occlude=0.8, form=0.4)
        studs = sketch.piece(trim)
        for index in range(2 + min(4, ornament)):
            studs.disc(5 + index * 4.2, 16.5, 1.2, 4)
        studs.clip(strap)
        sketch.overlay(studs)
        buckle = sketch.piece(trim)
        if style['pommel'] in ('faceted', 'gem'):
            buckle.poly([(16, 8), (23, 16.5), (16, 25), (9, 16.5)], 3)
            buckle.erase(points=[(16, 12), (20, 16.5), (16, 21), (12, 16.5)])
        else:
            buckle.rect((12, 10, 21, 23), 3)
            buckle.erase((15, 14, 18, 19))
        sketch.carve(buckle, rim=0.95, occlude=0.65)
        if style['rune'] > 0.4:
            stone = sketch.piece(gemtone)
            stone.disc(16.5, 16.5, 2.0, 4)
            sketch.carve(stone, rim=1.0, occlude=0.5)

    elif slot == 'cloak':
        piece = sketch.piece(tone)
        hem = style['skirt']
        if hem == 'long':
            shape = [(16, 4), (23, 8), (27, 20), (28, 29), (22, 25), (16, 29), (10, 25),
                     (4, 29), (5, 20), (9, 8)]
        elif hem == 'short':
            shape = [(16, 4), (22, 8), (26, 19), (26, 26), (16, 24), (6, 26), (6, 19), (10, 8)]
        else:
            shape = [(16, 4), (22, 7), (26, 18), (27, 27), (16, 24), (5, 27), (6, 18), (10, 7)]
        piece.poly(catmull(shape, 6, closed=True), 3)
        sketch.carve(piece, rim=0.9, occlude=0.8, form=0.5)
        folds = sketch.piece(tone)
        folds.line(catmull([(13, 9), (14, 18), (12, 26)], 5), 1, 1)
        folds.line(catmull([(19, 9), (18, 18), (20, 26)], 5), 1, 1)
        folds.clip(piece)
        sketch.overlay(folds)
        collar = sketch.piece(trim)
        collar.poly(catmull([(10, 7), (16, 3), (22, 7), (16, 10)], 5, closed=True), 3)
        sketch.carve(collar, rim=0.95, occlude=0.6)
        clasp = sketch.piece(gemtone)
        clasp.disc(16, 7, 2.2, 4)
        sketch.carve(clasp, rim=1.0, occlude=0.5)
    else:
        piece = sketch.piece(tone)
        piece.ellipse((7, 7, 25, 25), 3)
        sketch.carve(piece)
    _aura(sketch, item, 0.85)
    return sketch.result()


def _stone(sketch, tone, cx, cy, size, cut='faceted'):
    """A set stone. The cut is what separates a copper band from a star one."""
    piece = sketch.piece(tone)
    if cut == 'round':
        piece.disc(cx, cy, size, 3)
        piece.disc(cx - size * 0.32, cy - size * 0.34, size * 0.42, 5)
    elif cut == 'flat':
        # an emerald cut: clipped corners and a stepped table, not a plain box
        w, h = size * 0.86, size * 0.66
        chip = size * 0.30
        piece.poly([(cx - w + chip, cy - h), (cx + w - chip, cy - h), (cx + w, cy - h + chip),
                    (cx + w, cy + h - chip), (cx + w - chip, cy + h), (cx - w + chip, cy + h),
                    (cx - w, cy + h - chip), (cx - w, cy - h + chip)], 3)
        piece.poly([(cx - w * 0.52, cy - h * 0.46), (cx + w * 0.52, cy - h * 0.46),
                    (cx + w * 0.34, cy + h * 0.30), (cx - w * 0.34, cy + h * 0.30)], 5)
    elif cut == 'hollow':
        piece.disc(cx, cy, size, 3)
        piece.erase_ellipse((cx - size * 0.5, cy - size * 0.5, cx + size * 0.5, cy + size * 0.5))
    elif cut == 'point':
        piece.poly([(cx, cy - size * 1.5), (cx + size * 0.8, cy + size * 0.4),
                    (cx, cy + size * 1.1), (cx - size * 0.8, cy + size * 0.4)], 3)
        piece.poly([(cx, cy - size * 1.1), (cx + size * 0.4, cy), (cx - size * 0.4, cy)], 5)
    elif cut == 'cluster':
        for dx, dy, scale in ((-0.7, 0.4, 0.6), (0.0, -0.4, 1.0), (0.8, 0.5, 0.65)):
            piece.poly([(cx + dx * size, cy + dy * size - size * scale),
                        (cx + dx * size + size * 0.6 * scale, cy + dy * size),
                        (cx + dx * size, cy + dy * size + size * scale),
                        (cx + dx * size - size * 0.6 * scale, cy + dy * size)], 3)
    else:  # faceted
        piece.poly([(cx, cy - size * 1.2), (cx + size, cy), (cx, cy + size * 1.2), (cx - size, cy)], 3)
        piece.poly([(cx, cy - size * 0.75), (cx + size * 0.45, cy - size * 0.1),
                    (cx - size * 0.45, cy - size * 0.1)], 5)
    sketch.carve(piece, rim=1.0, occlude=0.6, gleam=0.9)
    return piece


STONE_CUT = {'round': 'round', 'disc': 'flat', 'faceted': 'faceted', 'ring': 'hollow',
             'spike': 'point', 'gem': 'cluster'}


def _accessory_icon(item):
    slot = item.get('slot')
    style = gear.style_of(item)
    ramps = role_ramps(item)
    metal, trim, gem = ramps['trim'], ramps['metal'], ramps['gem']
    cut = STONE_CUT.get(style['pommel'], 'faceted')
    family = style['guard']
    ornament = style['ornament']
    sketch = Sketch(ICON)

    if slot == 'ring':
        band = sketch.piece(metal)
        if family == 'shards':
            band.disc(16, 19, 8.6, 3)
            band.erase_ellipse((10.4, 13.4, 21.6, 24.6))
            for angle in (-2.5, -0.6, 0.9):
                band.poly([(16 + math.cos(angle) * 7, 19 + math.sin(angle) * 7),
                           (16 + math.cos(angle) * 12, 19 + math.sin(angle) * 12),
                           (16 + math.cos(angle + 0.5) * 7.4, 19 + math.sin(angle + 0.5) * 7.4)], 3)
        elif family == 'hooked':
            band.disc(16, 19, 8.4, 3)
            band.erase_ellipse((10.6, 13.6, 21.4, 24.4))
            for sign in (-1, 1):
                band.poly([(16 + sign * 4.4, 12.4), (16 + sign * 8.0, 6.0),
                           (16 + sign * 8.6, 11.4)], 3)
        elif family == 'wings':
            band.disc(16, 19, 8.4, 3)
            band.erase_ellipse((10.6, 13.6, 21.4, 24.4))
            for sign in (-1, 1):
                band.poly(catmull([(16 + sign * 5.0, 13.6), (16 + sign * 12.0, 9.0),
                                   (16 + sign * 10.0, 14.6), (16 + sign * 6.4, 16.4)],
                                  5, closed=True), 3)
        elif family == 'cross':
            band.disc(16, 19, 8.6, 3)
            band.erase_ellipse((10.8, 13.8, 21.2, 24.2))
            band.poly([(14.4, 4.0), (17.6, 4.0), (17.6, 14.0), (14.4, 14.0)], 3)
            band.poly([(10.0, 7.4), (22.0, 7.4), (22.0, 10.2), (10.0, 10.2)], 3)
        elif family == 'tipped':
            band.disc(16, 19, 8.6, 3)
            band.erase_ellipse((10.8, 13.8, 21.2, 24.2))
            for sign in (-1, 1):
                band.disc(16 + sign * 6.2, 13.0, 2.0, 3)
        else:
            band.disc(16, 19, 8.4, 3)
            band.erase_ellipse((11.0, 14.0, 21.0, 24.0))
        sketch.carve(band, rim=0.95, occlude=0.75, form=0.4)
        _stone(sketch, gem, 16, 9, 4.6, cut)
        if ornament >= 3:
            side = sketch.piece(gem)
            for sign in (-1, 1):
                side.disc(16 + sign * 6.4, 12.6, 1.5, 4)
            sketch.carve(side, rim=1.0, occlude=0.5)

    elif slot == 'necklace':
        chain = sketch.piece(metal)
        path = catmull([(5, 5), (8, 14), (16, 19), (24, 14), (27, 5)], 7)
        if family in ('cross', 'shards'):
            chain.line(path, 3, 3)
            chain.line(path, 5, 1)
        elif family in ('tipped', 'wings'):
            for index in range(0, len(path), 3):
                chain.disc(path[index][0], path[index][1], 1.7, 3)
        else:
            chain.line(path, 3, 2)
        sketch.carve(chain, rim=0.9, occlude=0.6)
        if family == 'hooked':
            fang = sketch.piece(trim)
            for sign in (-1, 1):
                fang.poly([(16 + sign * 5.4, 17.0), (16 + sign * 7.4, 25.0),
                           (16 + sign * 3.4, 19.0)], 3)
            sketch.carve(fang, rim=0.9, occlude=0.6)
        setting = sketch.piece(metal)
        if family == 'wings':
            for sign in (-1, 1):
                setting.poly(catmull([(16 + sign * 3.0, 19.0), (16 + sign * 11.0, 17.0),
                                      (16 + sign * 7.0, 23.0)], 5, closed=True), 3)
        elif family == 'cross':
            setting.poly([(14.2, 18.0), (17.8, 18.0), (17.8, 30.0), (14.2, 30.0)], 3)
            setting.poly([(9.6, 21.0), (22.4, 21.0), (22.4, 24.2), (9.6, 24.2)], 3)
        else:
            setting.disc(16, 22, 3.4, 3)
        sketch.carve(setting, rim=0.95, occlude=0.6)
        _stone(sketch, gem, 16, 23, 4.4 if family != 'cross' else 3.0, cut)

    elif slot == 'charm':
        cord = sketch.piece(ramps['grip'])
        cord.line(catmull([(8, 3), (16, 7), (24, 3)], 6), 3, 2)
        sketch.stamp(cord, rim=0.6, occlude=0.5)
        ring = sketch.piece(metal)
        ring.disc(16, 8, 2.6, 3)
        ring.erase_ellipse((14.6, 6.6, 17.4, 9.4))
        sketch.carve(ring, rim=0.95, occlude=0.6)
        body = sketch.piece(trim)
        if family == 'shards':
            for dx, height in ((-4.4, 8.0), (0.4, 12.0), (4.6, 9.0)):
                body.poly([(16 + dx - 2.2, 28.0), (16 + dx, 28.0 - height), (16 + dx + 2.2, 28.0)], 3)
        elif family == 'hooked':
            body.poly(catmull([(16, 11), (23, 17), (19, 29), (16, 24), (13, 29), (9, 17)],
                              6, closed=True), 3)
        elif family == 'cross':
            body.poly([(13.6, 11.0), (18.4, 11.0), (18.4, 18.0), (25.0, 18.0),
                       (25.0, 22.4), (18.4, 22.4), (18.4, 30.0), (13.6, 30.0),
                       (13.6, 22.4), (7.0, 22.4), (7.0, 18.0), (13.6, 18.0)], 3)
        elif family == 'wings':
            body.poly(catmull([(16, 11), (26, 15), (21, 21), (16, 30), (11, 21), (6, 15)],
                              6, closed=True), 3)
        elif family == 'tipped':
            body.poly(catmull([(16, 11), (24, 20), (16, 29), (8, 20)], 6, closed=True), 3)
        else:
            body.disc(16, 20, 8.4, 3)
        sketch.carve(body, rim=0.95, occlude=0.75, form=0.5)
        _stone(sketch, gem, 16, 20 if family != 'cross' else 20, 3.6, cut)
        if ornament >= 4:
            studs = sketch.piece(metal)
            for angle in (-2.2, -0.9, 0.4, 1.7):
                studs.disc(16 + math.cos(angle) * 6.2, 20 + math.sin(angle) * 6.2, 1.1, 4)
            studs.clip(body)
            sketch.overlay(studs)

    else:  # trinket
        if family == 'shards':
            base = sketch.piece(metal)
            base.poly([(9, 28), (23, 28), (21, 23), (11, 23)], 3)
            sketch.carve(base, rim=0.9, occlude=0.7)
            _stone(sketch, gem, 16, 15, 7.0, 'cluster')
        elif family == 'hooked':
            claw = sketch.piece(metal)
            for sign in (-1, 1):
                claw.poly(catmull([(16 + sign * 3.0, 26.0), (16 + sign * 10.0, 16.0),
                                   (16 + sign * 6.4, 8.0), (16 + sign * 7.6, 18.0)],
                                  5, closed=True), 3)
            claw.poly([(12, 24), (20, 24), (19, 29), (13, 29)], 3)
            sketch.carve(claw, rim=0.95, occlude=0.7)
            _stone(sketch, gem, 16, 17, 5.0, cut)
        elif family == 'cross':
            frame = sketch.piece(metal)
            frame.disc(16, 16, 10.0, 3)
            frame.erase_ellipse((7.0, 7.0, 25.0, 25.0))
            frame.poly([(14.6, 4.0), (17.4, 4.0), (17.4, 28.0), (14.6, 28.0)], 3)
            frame.poly([(4.0, 14.6), (28.0, 14.6), (28.0, 17.4), (4.0, 17.4)], 3)
            sketch.carve(frame, rim=0.95, occlude=0.7)
            _stone(sketch, gem, 16, 16, 4.0, cut)
        elif family == 'wings':
            wings = sketch.piece(metal)
            for sign in (-1, 1):
                wings.poly(catmull([(16 + sign * 3.4, 12.0), (16 + sign * 14.0, 9.0),
                                    (16 + sign * 11.0, 18.0), (16 + sign * 4.0, 19.0)],
                                   5, closed=True), 3)
            sketch.carve(wings, rim=0.95, occlude=0.65)
            hoop = sketch.piece(trim)
            hoop.disc(16, 16, 6.4, 3)
            hoop.erase_ellipse((11.4, 11.4, 20.6, 20.6))
            sketch.carve(hoop, rim=0.95, occlude=0.7)
            _stone(sketch, gem, 16, 16, 3.8, cut)
        elif family == 'tipped':
            glass = sketch.piece(metal)
            glass.poly([(9, 5), (23, 5), (17.6, 16), (23, 27), (9, 27), (14.4, 16)], 3)
            sketch.carve(glass, rim=0.9, occlude=0.7, form=0.5)
            sand = sketch.piece(gem)
            sand.poly([(11, 24), (21, 24), (17, 17), (15, 17)], 3)
            sand.clip(glass)
            sketch.overlay(sand)
            caps = sketch.piece(trim)
            caps.poly([(7, 3), (25, 3), (25, 6), (7, 6)], 3)
            caps.poly([(7, 26), (25, 26), (25, 29), (7, 29)], 3)
            sketch.carve(caps, rim=0.95, occlude=0.6)
        else:
            hoop = sketch.piece(metal)
            hoop.disc(16, 17, 9.4, 3)
            hoop.erase_ellipse((9.6, 10.6, 22.4, 23.4))
            hoop.poly([(14.6, 3.0), (17.4, 3.0), (17.4, 9.0), (14.6, 9.0)], 3)
            sketch.carve(hoop, rim=0.95, occlude=0.7)
            _stone(sketch, gem, 16, 17, 5.4, cut)
    _aura(sketch, item, 0.9)
    return sketch.result()


# -- goods icons -----------------------------------------------------------

def _ore_icon(item):
    tone = ramp(pigment.MATERIALS.get(item.get('material', 'stone'), '#8a8f96'))
    rock = ramp('#6f6f6c')
    sketch = Sketch(ICON)
    piece = sketch.piece(rock)
    piece.poly(catmull([(5, 22), (7, 13), (13, 8), (22, 9), (27, 16), (26, 24), (16, 27)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.85, occlude=0.65)
    vein = sketch.piece(tone)
    for points in ([(9, 20), (13, 16), (11, 12)], [(17, 24), (19, 18), (24, 15)], [(21, 22), (24, 21)]):
        vein.line(points, 3, 2)
    for x, y in ((12, 15), (19, 19), (23, 16)):
        vein.disc(x, y, 1.6, 4)
        vein.dot(x - 0.6, y - 0.8, 5)
    vein.clip(piece)
    sketch.overlay(vein)
    return sketch.result()


def _bar_icon(item):
    tone = ramp(pigment.MATERIALS.get(item.get('material', 'iron'), '#8a8f96'))
    sketch = Sketch(ICON)
    for index, (x, y) in enumerate(((6, 18), (13, 12))):
        piece = sketch.piece(tone)
        piece.poly([(x, y + 6), (x + 3, y), (x + 16, y), (x + 13, y + 6)], 3)
        piece.poly([(x, y + 6), (x + 13, y + 6), (x + 13, y + 10), (x, y + 10)], 2)
        detail = sketch.piece(tone)
        detail.line([(x + 4, y + 1.5), (x + 15, y + 1.5)], 5, 1)
        detail.line([(x + 1, y + 8), (x + 12, y + 8)], 1, 1)
        detail.clip(piece)
        sketch.stamp(piece, rim=0.9, occlude=0.6)
        sketch.overlay(detail)
    return sketch.result()


def _log_icon(item, plank=False):
    tone = ramp(pigment.MATERIALS.get(item.get('material', 'oak'), '#8a6a49'))
    sketch = Sketch(ICON)
    if plank:
        for index, y in enumerate((9, 16, 23)):
            piece = sketch.piece(tone)
            piece.poly([(4, y), (28, y - 1), (28, y + 5), (4, y + 6)], 3)
            detail = sketch.piece(tone)
            detail.line([(6, y + 1.6), (26, y + 0.8)], 4, 1)
            detail.line([(7, y + 4), (25, y + 3.4)], 1, 1)
            detail.clip(piece)
            sketch.stamp(piece, rim=0.85, occlude=0.6)
            sketch.overlay(detail)
        return sketch.result()
    for x, y, r in ((10, 20, 6.0), (20, 15, 6.4)):
        piece = sketch.piece(tone)
        piece.poly(taper_shape((x - 7, y + 2), (x + 8, y - 2), r * 2, r * 1.9), 3)
        sketch.stamp(piece, rim=0.85, occlude=0.6)
        end = sketch.piece(tone)
        end.disc(x + 7.4, y - 1.8, r * 0.92, 2)
        end.disc(x + 7.4, y - 1.8, r * 0.55, 1)
        end.disc(x + 7.4, y - 1.8, r * 0.22, 3)
        sketch.stamp(end, rim=0.6, occlude=0.4)
        bark = sketch.piece(tone)
        bark.line([(x - 5, y - 2), (x + 5, y - 4)], 1, 1)
        bark.line([(x - 4, y + 3), (x + 4, y + 1)], 1, 1)
        bark.clip(piece)
        sketch.overlay(bark)
    return sketch.result()


def _cloth_icon(item):
    tone = ramp(pigment.MATERIALS.get(item.get('material', 'cloth'), '#8d93a8'))
    sketch = Sketch(ICON)
    piece = sketch.piece(tone)
    piece.poly(catmull([(4, 12), (16, 7), (28, 12), (28, 20), (16, 25), (4, 20)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.85, occlude=0.6)
    fold = sketch.piece(tone)
    fold.line(catmull([(5, 15), (16, 11), (27, 15)], 6), 5, 1)
    fold.line(catmull([(5, 19), (16, 15), (27, 19)], 6), 1, 1)
    fold.line(catmull([(5, 22), (16, 19), (27, 22)], 6), 1, 1)
    fold.clip(piece)
    sketch.overlay(fold)
    band = sketch.piece(ramp('#a08351'))
    band.poly([(14, 8), (18, 9), (18, 24), (14, 23)], 3)
    sketch.stamp(band, rim=0.7, occlude=0.5)
    return sketch.result()


def _leather_icon(item):
    tone = ramp(pigment.MATERIALS.get(item.get('material', 'leather'), '#8a5f3c'))
    sketch = Sketch(ICON)
    piece = sketch.piece(tone)
    piece.poly(catmull([(7, 6), (13, 9), (20, 8), (26, 6), (27, 15), (23, 26),
                        (14, 27), (6, 21), (5, 12)], 7, closed=True), 3)
    sketch.stamp(piece, rim=0.85, occlude=0.6)
    detail = sketch.piece(tone)
    detail.line(catmull([(11, 12), (16, 16), (13, 22)], 5), 1, 1)
    detail.line(catmull([(20, 12), (22, 18)], 4), 1, 1)
    for x, y in ((9, 9), (24, 10), (10, 20), (22, 23)):
        detail.dot(x, y, 5)
    detail.clip(piece)
    sketch.overlay(detail)
    return sketch.result()


def _herb_icon(item):
    leaf = ramp(pigment.MATERIALS.get('leaf'))
    bloom = pigment.element_ramp(item.get('element', 'Nature'))
    ident = item.get('id', '')
    if 'ember' in ident:
        bloom = ramp('#d4703c')
    elif 'frost' in ident:
        bloom = ramp('#8fc9d8')
    elif 'moon' in ident or 'ghost' in ident:
        bloom = ramp('#cfd3ea')
    elif 'blood' in ident:
        bloom = ramp('#a8414a')
    sketch = Sketch(ICON)
    stem = sketch.piece(leaf)
    stem.line(catmull([(15, 28), (17, 20), (16, 12)], 6), 2, 2)
    for direction in (-1, 1):
        stem.poly(catmull([(16, 20), (16 + direction * 8, 15), (16 + direction * 9, 20),
                           (16 + direction * 3, 22)], 5, closed=True), 3)
    sketch.stamp(stem, rim=0.8, occlude=0.55)
    flower = sketch.piece(bloom)
    for angle in range(0, 360, 72):
        rad = math.radians(angle)
        flower.disc(16 + math.cos(rad) * 4.0, 10 + math.sin(rad) * 4.0, 2.6, 3)
    sketch.stamp(flower, rim=0.9, occlude=0.5)
    heart = sketch.piece(ramp('#e3c667'))
    heart.disc(16, 10, 2.0, 4)
    sketch.stamp(heart, rim=0.8, occlude=0.4)
    return sketch.result()


def _potion_icon(item):
    ident = item.get('id', '')
    liquid = ramp('#b8484c' if 'healing' in ident else '#4f7bc0' if 'mana' in ident else '#6faa5b')
    glass = ramp('#a9c6cf')
    sketch = Sketch(ICON)
    body = sketch.piece(glass)
    body.poly(catmull([(13, 8), (19, 8), (21, 14), (23, 21), (20, 27), (12, 27), (9, 21), (11, 14)], 6, closed=True), 3)
    sketch.stamp(body, rim=0.9, occlude=0.5)
    fluid = sketch.piece(liquid)
    fluid.poly(catmull([(11, 17), (21, 17), (22, 22), (19, 26), (13, 26), (10, 22)], 5, closed=True), 3)
    fluid.clip(body)
    sketch.overlay(fluid)
    shine = sketch.piece(glass)
    shine.line([(12.5, 14), (11.5, 22)], 5, 1)
    shine.clip(body)
    sketch.overlay(shine)
    neck = sketch.piece(glass)
    neck.rect((13, 5, 19, 9), 2)
    sketch.stamp(neck, rim=0.8, occlude=0.5)
    cork = sketch.piece(ramp('#b08a55'))
    cork.rect((13, 2, 19, 6), 3)
    sketch.stamp(cork, rim=0.85, occlude=0.5)
    return sketch.result()


def _food_icon(item):
    ident = item.get('id', '')
    sketch = Sketch(ICON)
    if 'bread' in ident:
        loaf = sketch.piece(ramp('#c69a5f'))
        loaf.poly(catmull([(5, 20), (8, 12), (16, 9), (25, 12), (27, 20), (16, 24)], 6, closed=True), 3)
        sketch.stamp(loaf, rim=0.9, occlude=0.6)
        cuts = sketch.piece(ramp('#c69a5f'))
        for x in (11, 16, 21):
            cuts.line([(x - 2, 13), (x + 1, 11)], 5, 1)
        cuts.clip(loaf)
        sketch.overlay(cuts)
        return sketch.result()
    fishy = any(word in ident for word in ('cod', 'pike', 'eel', 'snapper', 'trout', 'carp',
                                          'starfin', 'ray', 'fish'))
    if not fishy and ('cooked' in ident or 'meat' in ident):
        meat = sketch.piece(ramp('#a85a4e' if 'cooked' not in ident else '#8d5136'))
        meat.poly(catmull([(9, 10), (20, 8), (25, 14), (22, 22), (12, 23), (7, 17)], 6, closed=True), 3)
        sketch.stamp(meat, rim=0.9, occlude=0.6)
        bone = sketch.piece(ramp('#dcd3b8'))
        bone.line([(6, 22), (13, 18)], 3, 3)
        bone.disc(5.6, 22.6, 2.0, 4)
        sketch.stamp(bone, rim=0.8, occlude=0.5)
        return sketch.result()
    cooked = 'cooked' in ident
    scales = ('#8a6a4a' if cooked else
              '#6f95a8' if 'ice' in ident or 'abyssal' in ident else
              '#b06a5c' if 'snapper' in ident else
              '#9fb0bc' if 'carp' in ident or 'silver' in ident else '#9aa27f')
    fish = sketch.piece(ramp(scales))
    fish.poly(catmull([(6, 16), (13, 10), (22, 11), (26, 16), (22, 22), (13, 22)], 6, closed=True), 3)
    fish.poly([(6, 16), (2, 11), (2, 21)], 3)
    sketch.stamp(fish, rim=0.9, occlude=0.6)
    detail = sketch.piece(ramp('#c9d3cf'))
    detail.disc(22, 15, 1.4, 4)
    detail.dot(22, 15, (32, 28, 34, 255))
    detail.line(catmull([(12, 12), (16, 16), (12, 21)], 5), 3, 1)
    sketch.stamp(detail, outline=False, rim=0, occlude=0)
    return sketch.result()


GEMSTONES = ('#b6474b', '#4c72b6', '#4fa06a', '#b4577f', '#c9a13f', '#7fb8c8', '#8a6ac0', '#d8d2c0')


def _gem_icon(item):
    ident = item.get('id', '')
    tone = ramp('#b6474b' if 'red' in ident else '#4c72b6' if 'blue' in ident else
                '#4fa06a' if 'green' in ident else
                '#8fb9c8' if 'storm' in ident or 'crystal' in ident else
                GEMSTONES[pigment.keyed(ident, len(GEMSTONES))])
    sketch = Sketch(ICON)
    piece = sketch.piece(tone)
    piece.poly([(16, 4), (25, 13), (16, 28), (7, 13)], 3)
    sketch.stamp(piece, rim=0.95, occlude=0.6)
    facets = sketch.piece(tone)
    facets.poly([(16, 6), (22, 13), (16, 16), (10, 13)], 4)
    facets.poly([(16, 6), (19, 12), (16, 15), (13, 12)], 5)
    facets.line([(10, 14), (16, 26)], 1, 1)
    facets.line([(22, 14), (16, 26)], 1, 1)
    facets.clip(piece)
    sketch.overlay(facets)
    return sketch.result()


def _rune_icon(item):
    stone = ramp('#7b6f96')
    glyph = pigment.element_ramp(item.get('element', 'Arcane'))
    sketch = Sketch(ICON)
    piece = sketch.piece(stone)
    piece.poly(catmull([(9, 4), (23, 5), (25, 15), (23, 27), (16, 29), (9, 27), (7, 15)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.65)
    grain = sketch.piece(stone)
    grain.line([(11, 9), (21, 8)], 4, 1)
    grain.line([(10, 24), (22, 23)], 1, 1)
    grain.clip(piece)
    sketch.overlay(grain)
    mark = sketch.piece(glyph)
    seed = pigment.keyed(item.get('id', 'rune'))
    strokes = [
        [(13, 10), (19, 10)], [(16, 9), (16, 23)], [(12, 15), (20, 13)],
        [(13, 22), (19, 19)], [(12, 12), (19, 21)], [(20, 12), (13, 20)],
        [(13, 12), (13, 21)], [(19, 11), (19, 22)],
    ]
    for index, stroke in enumerate(strokes):
        if (seed >> index) & 1:
            mark.line(stroke, 4, 1)
    mark.line([(16, 9), (16, 23)], 4, 1)
    sketch.stamp(mark, outline=False, rim=0, occlude=0)
    sketch.glow(pigment.ELEMENTS.get(item.get('element', 'Arcane'), '#a98fd0'), 2, 0.4)
    return sketch.result()


def _book_icon(item, scroll=False):
    sketch = Sketch(ICON)
    if scroll:
        paper = sketch.piece(ramp('#d8cca8'))
        paper.poly([(6, 7), (26, 6), (26, 26), (6, 25)], 3)
        sketch.stamp(paper, rim=0.9, occlude=0.6)
        text = sketch.piece(ramp('#7a6a52'))
        for y in range(10, 24, 3):
            text.line([(9, y), (23 if y % 6 else 19, y)], 3, 1)
        text.clip(paper)
        sketch.overlay(text)
        for x in (5, 27):
            rod = sketch.piece(ramp('#8a6a49'))
            rod.poly(taper_shape((x, 4), (x, 28), 4.0, 4.0), 3)
            sketch.stamp(rod, rim=0.85, occlude=0.55)
        return sketch.result()
    cover = sketch.piece(ramp(pigment.MATERIALS.get(item.get('material', 'book'), '#7a5240')))
    cover.poly([(6, 5), (25, 7), (25, 27), (6, 25)], 3)
    sketch.stamp(cover, rim=0.9, occlude=0.65)
    pages = sketch.piece(ramp('#ddd2b4'))
    pages.poly([(10, 8), (26, 9), (26, 25), (10, 24)], 3)
    sketch.stamp(pages, rim=0.8, occlude=0.5)
    text = sketch.piece(ramp('#8b7f66'))
    for y in range(12, 23, 3):
        text.line([(13, y), (24, y + 0.4)], 3, 1)
    text.clip(pages)
    sketch.overlay(text)
    band = sketch.piece(ramp('#c0a24a'))
    band.poly([(6, 5), (9, 5.4), (9, 25.4), (6, 25)], 3)
    band.disc(16, 16, 2.4, 3)
    sketch.stamp(band, rim=0.85, occlude=0.5)
    return sketch.result()


def _map_icon(item):
    sketch = Sketch(ICON)
    paper = sketch.piece(ramp('#d7c8a1'))
    paper.poly(catmull([(4, 8), (11, 5), (21, 8), (28, 5), (28, 24), (21, 27), (11, 24), (4, 27)], 7, closed=True), 3)
    sketch.stamp(paper, rim=0.9, occlude=0.6)
    ink = sketch.piece(ramp('#7d6b4e'))
    ink.line(catmull([(8, 20), (13, 15), (18, 18), (24, 12)], 6), 2, 1)
    ink.line([(11, 5), (11, 24)], 1, 1)
    ink.line([(21, 8), (21, 27)], 1, 1)
    ink.clip(paper)
    sketch.overlay(ink)
    mark = sketch.piece(ramp('#a8413c'))
    mark.line([(20, 18), (26, 24)], 3, 2)
    mark.line([(26, 18), (20, 24)], 3, 2)
    sketch.stamp(mark, outline=False, rim=0, occlude=0)
    return sketch.result()


def _material_icon(item):
    ident = item.get('id', '')
    material = item.get('material', 'stone')
    sketch = Sketch(ICON)
    if 'feather' in ident:
        piece = sketch.piece(ramp('#c9c2b4'))
        piece.poly(catmull([(9, 27), (12, 16), (18, 6), (23, 10), (21, 21), (13, 27)], 6, closed=True), 3)
        sketch.stamp(piece, rim=0.9, occlude=0.55)
        quill = sketch.piece(ramp('#8f7f66'))
        quill.line(catmull([(10, 27), (16, 16), (20, 8)], 6), 3, 1)
        for step in range(5):
            quill.line([(13 + step * 1.6, 24 - step * 3.2), (17 + step * 1.2, 21 - step * 3.0)], 1, 1)
        quill.clip(piece)
        sketch.overlay(quill)
        return sketch.result()
    if 'bone' in ident or 'fang' in ident:
        piece = sketch.piece(ramp('#d6cdb2'))
        if 'fang' in ident:
            piece.poly(catmull([(12, 4), (20, 6), (19, 16), (16, 28), (13, 16)], 6, closed=True), 3)
        else:
            piece.poly(taper_shape((8, 24), (24, 8), 5.0, 5.0), 3)
            piece.disc(8, 24, 3.6, 3)
            piece.disc(11, 26, 3.0, 3)
            piece.disc(24, 8, 3.6, 3)
            piece.disc(21, 6, 3.0, 3)
        sketch.stamp(piece, rim=0.9, occlude=0.6)
        return sketch.result()
    if 'scale' in ident or 'pelt' in ident or 'hide' in ident or 'fur' in ident:
        return _leather_icon(item)
    if 'thread' in ident or 'fiber' in ident or 'silk' in ident:
        piece = sketch.piece(ramp(pigment.MATERIALS.get(material, '#b7a887')))
        piece.disc(16, 17, 8.5, 3)
        sketch.stamp(piece, rim=0.9, occlude=0.6)
        wind = sketch.piece(ramp(pigment.MATERIALS.get(material, '#b7a887')))
        for offset in (-4, 0, 4):
            wind.line(catmull([(9, 15 + offset * 0.4), (16, 12 + offset), (23, 15 + offset * 0.4)], 6), 5, 1)
        wind.clip(piece)
        sketch.overlay(wind)
        spool = sketch.piece(ramp('#8a6a49'))
        spool.line([(16, 6), (16, 28)], 3, 3)
        sketch.stamp(spool, rim=0.7, occlude=0.5)
        return sketch.result()
    if 'vial' in ident or 'glass' in ident:
        piece = sketch.piece(ramp('#a9c6cf'))
        piece.poly(catmull([(12, 9), (20, 9), (22, 18), (19, 26), (13, 26), (10, 18)], 6, closed=True), 3)
        piece.rect((13, 4, 19, 10), 2)
        sketch.stamp(piece, rim=0.95, occlude=0.45)
        shine = sketch.piece(ramp('#a9c6cf'))
        shine.line([(13.5, 13), (12.5, 22)], 5, 1)
        shine.clip(piece)
        sketch.overlay(shine)
        return sketch.result()
    if 'coal' in ident or 'ember' in ident or 'core' in ident or 'mote' in ident:
        tone = ramp('#3f3f45' if 'coal' in ident else pigment.ELEMENTS.get(item.get('element', 'Fire'), '#c96b3c'))
        piece = sketch.piece(tone)
        piece.poly(catmull([(8, 20), (10, 12), (17, 8), (25, 13), (24, 22), (16, 26)], 6, closed=True), 3)
        sketch.stamp(piece, rim=0.9, occlude=0.6)
        if 'coal' not in ident:
            sketch.glow(pigment.ELEMENTS.get(item.get('element', 'Fire'), '#c96b3c'), 3, 0.55)
        return sketch.result()
    if 'ectoplasm' in ident:
        piece = sketch.piece(ramp('#9fd4c8'))
        piece.poly(catmull([(9, 22), (10, 12), (16, 7), (23, 12), (23, 22), (19, 26), (16, 22), (13, 26)], 7, closed=True), 3)
        sketch.stamp(piece, rim=0.9, occlude=0.4)
        sketch.glow('#9fd4c8', 3, 0.5)
        return sketch.result()
    if 'seed' in ident:
        piece = sketch.piece(ramp('#b9a05e'))
        for x, y in ((12, 20), (19, 17), (15, 12)):
            piece.ellipse((x - 3.4, y - 2.4, x + 3.4, y + 2.4), 3)
        sketch.stamp(piece, rim=0.85, occlude=0.55)
        return sketch.result()
    if 'salt' in ident:
        piece = sketch.piece(ramp('#dfe2e4'))
        for x, y, r in ((12, 21, 4.0), (19, 19, 3.4), (16, 14, 3.0)):
            piece.poly([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], 3)
        sketch.stamp(piece, rim=0.9, occlude=0.5)
        return sketch.result()
    if 'ink' in ident:
        pot = sketch.piece(ramp('#4a4f6d'))
        pot.poly(catmull([(9, 14), (23, 14), (24, 24), (16, 27), (8, 24)], 6, closed=True), 3)
        pot.rect((13, 9, 19, 15), 2)
        sketch.stamp(pot, rim=0.9, occlude=0.6)
        quill = sketch.piece(ramp('#d3c7a6'))
        quill.poly(taper_shape((14, 13), (24, 4), 3.4, 1.2), 3)
        sketch.stamp(quill, rim=0.85, occlude=0.5)
        return sketch.result()
    if 'compass' in ident or 'lockpick' in ident or 'charter' in ident or 'manifest' in ident or 'fragment' in ident:
        if 'compass' in ident:
            case = sketch.piece(ramp('#c0a24a'))
            case.disc(16, 16, 10, 3)
            sketch.stamp(case, rim=0.9, occlude=0.6)
            face = sketch.piece(ramp('#e2d8bc'))
            face.disc(16, 16, 7, 3)
            sketch.stamp(face, rim=0.7, occlude=0.4)
            needle = sketch.piece(ramp('#a8413c'))
            needle.poly([(16, 9), (18, 16), (16, 23), (14, 16)], 3)
            needle.poly([(16, 9), (18, 16), (16, 16)], 5)
            sketch.stamp(needle, outline=False, rim=0, occlude=0)
            return sketch.result()
        if 'lockpick' in ident:
            piece = sketch.piece(ramp('#a9b6c0'))
            piece.line(catmull([(6, 25), (16, 18), (24, 8)], 6), 3, 2)
            piece.poly([(23, 6), (27, 8), (24, 12)], 3)
            piece.disc(6, 25, 2.6, 2)
            sketch.stamp(piece, rim=0.9, occlude=0.5)
            return sketch.result()
        return _book_icon(item, scroll=True)
    if 'arrow' in ident:
        sketch = Sketch(ICON)
        for index, x in enumerate((10, 16, 22)):
            shaft = sketch.piece(ramp('#a98a5d'))
            shaft.poly(taper_shape((x - 1, 27), (x + 1, 6), 2.4, 2.0), 3)
            sketch.stamp(shaft, rim=0.8, occlude=0.5)
            head = sketch.piece(ramp('#a9b6c0'))
            head.poly([(x + 1, 2.5), (x + 3.4, 8), (x - 1.4, 8)], 3)
            sketch.stamp(head, rim=0.9, occlude=0.5)
            fletch = sketch.piece(ramp('#8e9c74' if index % 2 == 0 else '#a2634c'))
            fletch.poly([(x - 1.4, 20), (x - 4.4, 24), (x - 1.0, 25)], 3)
            sketch.stamp(fletch, rim=0.8, occlude=0.5)
        return sketch.result()
    if 'mushroom' in ident:
        stalk = sketch.piece(ramp('#d9cdb0'))
        stalk.poly(catmull([(13, 27), (14, 17), (18, 17), (19, 27)], 5, closed=True), 3)
        sketch.stamp(stalk, rim=0.8, occlude=0.55)
        cap = sketch.piece(ramp('#a8524a'))
        cap.poly(catmull([(6, 18), (9, 9), (16, 6), (23, 9), (26, 18), (16, 20)], 6, closed=True), 3)
        sketch.stamp(cap, rim=0.9, occlude=0.6)
        spots = sketch.piece(ramp('#e6dcc2'))
        for x, y, r in ((11, 13, 1.8), (17, 10, 1.5), (21, 14, 1.6)):
            spots.disc(x, y, r, 4)
        spots.clip(cap)
        sketch.overlay(spots)
        return sketch.result()
    # generic worked good: a wrapped bundle
    piece = sketch.piece(ramp(pigment.MATERIALS.get(material, '#9a8f7a')))
    piece.poly(catmull([(7, 21), (8, 12), (16, 7), (25, 12), (25, 21), (16, 26)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    tie = sketch.piece(ramp('#8a6a49'))
    tie.line([(7, 16), (25, 16)], 3, 2)
    tie.line([(16, 8), (16, 25)], 3, 1)
    sketch.stamp(tie, outline=False, rim=0, occlude=0)
    return sketch.result()


def _structure_icon(item):
    tone = ramp('#8a6a49')
    sketch = Sketch(ICON)
    ident = item.get('id', '')
    piece = sketch.piece(tone)
    piece.poly([(4, 14), (28, 14), (28, 18), (4, 18)], 3)
    piece.poly([(6, 18), (10, 18), (10, 27), (6, 27)], 2)
    piece.poly([(22, 18), (26, 18), (26, 27), (22, 27)], 2)
    sketch.stamp(piece, rim=0.85, occlude=0.6)
    top = sketch.piece(ramp('#a9b6c0' if 'forge' in ident or 'rune' in ident else '#9c8158'))
    if 'campfire' in ident:
        top = sketch.piece(ramp('#d4703c'))
        top.poly(catmull([(11, 14), (16, 4), (21, 14), (16, 17)], 6, closed=True), 3)
    elif 'rune' in ident:
        top.poly([(10, 6), (22, 6), (22, 13), (10, 13)], 3)
        top.line([(16, 7), (16, 12)], 5, 1)
    elif 'kitchen' in ident:
        top.disc(16, 9, 6, 3)
        top.rect((10, 9, 22, 13), 3)
    else:
        top.poly([(8, 8), (24, 8), (24, 13), (8, 13)], 3)
        top.line([(10, 10), (22, 10)], 5, 1)
    sketch.stamp(top, rim=0.9, occlude=0.6)
    return sketch.result()


def _quest_icon(item):
    sketch = Sketch(ICON)
    ident = item.get('id', '')
    if 'charter' in ident or 'manifest' in ident or 'writ' in ident or 'letter' in ident:
        return _book_icon(item, scroll=True)
    piece = sketch.piece(ramp('#a08a5e'))
    piece.poly(catmull([(8, 22), (7, 12), (16, 6), (25, 12), (24, 22), (16, 27)], 6, closed=True), 3)
    sketch.stamp(piece, rim=0.9, occlude=0.6)
    seal = sketch.piece(ramp('#a8413c'))
    seal.disc(16, 16, 4.0, 3)
    seal.disc(14.8, 14.6, 1.6, 5)
    sketch.stamp(seal, rim=0.85, occlude=0.5)
    return sketch.result()


def _polish_icon(image, item):
    """Add sparse material cues without changing the icon silhouette or size."""
    image = refine_sprite(image, 0.12)
    if image.mode != 'RGBA':
        return image
    out = image.copy(); pixels = image.load(); target = out.load()
    ident = str(item.get('id', '')); kind = item.get('type', 'material')
    seed = pigment.keyed(ident + '|detail', 2**16)
    width, height = image.size
    candidates = []
    for y in range(2, height - 2):
        for x in range(2, width - 2):
            r,g,b,a = pixels[x,y]
            if a < 220: continue
            nearby = [pixels[x-1,y], pixels[x+1,y], pixels[x,y-1], pixels[x,y+1]]
            if any(p[3] < 220 for p in nearby): continue
            if max(abs(r-p[0])+abs(g-p[1])+abs(b-p[2]) for p in nearby) > 75: continue
            h = ((x+11)*73856093 ^ (y+17)*19349663 ^ seed*83492791) & 0xffffffff
            if h % 37 == 0: candidates.append((h,x,y))
    candidates.sort()
    limit = 6 if kind in ('weapon','armor','tool','offhand','accessory') else 4
    for index,(_,x,y) in enumerate(candidates[:limit]):
        r,g,b,a = pixels[x,y]
        light = index % 2 == 0
        tone = (255,239,211,255) if light else (39,31,42,255)
        amount = 0.16 if light else 0.12
        nr,ng,nb,_ = blend((r,g,b,a), tone, amount)
        target[x,y] = (nr,ng,nb,a)
        # Metal gets a crisp paired glint; organic materials get a one-pixel grain stroke.
        nx = x + (1 if (seed + index) % 2 else -1)
        if 0 <= nx < width and pixels[nx,y][3] >= 220:
            pr,pg,pb,pa = pixels[nx,y]
            amt = 0.10 if kind in ('weapon','armor','tool','offhand','accessory') else 0.07
            tr,tg,tb,_ = blend((pr,pg,pb,pa), tone, amt)
            target[nx,y] = (tr,tg,tb,pa)
    out.putalpha(image.getchannel('A'))
    return out


TYPE_ICONS = {
    'weapon': weapon_icon,
    'offhand': weapon_icon,
    'armor': _armour_icon,
    'accessory': _accessory_icon,
    'ore': _ore_icon,
    'gem': _gem_icon,
    'rune': _rune_icon,
    'book': _book_icon,
    'treasure_map': _map_icon,
    'potion': _potion_icon,
    'food': _food_icon,
    'herb': _herb_icon,
    'structure': _structure_icon,
    'quest': _quest_icon,
    'tool': weapon_icon,
    'ammo': _material_icon,
    'seed': _material_icon,
    'animal_material': _material_icon,
}


def icon(item):
    """32x32 inventory icon with the second-stage material refinement pass."""
    kind = item.get('type', 'material')
    ident = item.get('id', '')
    if kind == 'wood':
        image = _log_icon(item, plank='plank' in ident)
    elif kind == 'material':
        if ident.endswith('_bar'):
            image = _bar_icon(item)
        elif 'cloth' in ident or 'weave' in ident or 'linen' in ident or 'wool' in ident:
            image = _cloth_icon(item)
        elif 'leather' in ident:
            image = _leather_icon(item)
        else:
            image = _material_icon(item)
    elif kind == 'ore' and ident.endswith('_bar'):
        image = _bar_icon(item)
    else:
        handler = TYPE_ICONS.get(kind)
        image = _material_icon(item) if handler is None else handler(item)
    return _polish_icon(image, item)
