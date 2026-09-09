"""Drawing engine for the Atelier sprite library.

The unit of work is a Piece: one transparent layer that is drawn flat and then
baked. Baking adds a contour, an inner rim light on the upper left edge and an
occlusion band on the lower right edge, so every limb, plank and blade in the
library is lit from the same direction and separates cleanly from its
neighbours. Sprites are assembled by stamping pieces in depth order.
"""
from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from . import pigment
from .pigment import blend, rgb

BAYER = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def canvas(size, color=(0, 0, 0, 0)):
    return Image.new('RGBA', size, color)


def _shift(mask, dx, dy):
    out = Image.new('L', mask.size, 0)
    out.paste(mask, (dx, dy))
    return out


def _hard(mask, cut=110):
    return mask.point(lambda v: 255 if v >= cut else 0)


def _fade(mask, amount):
    if amount >= 1.0:
        return mask
    return mask.point(lambda v, a=amount: round(v * a))


def _shells(mask, dx, dy, depth):
    """Successive one pixel bands walking in from the (-dx,-dy) facing edge."""
    bands = []
    current = mask
    for step in range(max(1, depth)):
        nxt = _shift(mask, dx * (step + 1), dy * (step + 1))
        band = ImageChops.darker(ImageChops.subtract(current, nxt), mask)
        bands.append(band)
        current = nxt
    return bands


def _grow(mask, diagonal=False):
    grown = mask
    steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diagonal:
        steps += [(1, 1), (-1, -1), (1, -1), (-1, 1)]
    for dx, dy in steps:
        grown = ImageChops.lighter(grown, _shift(mask, dx, dy))
    return grown


def refine_sprite(image, strength=0.11):
    """Second-pass pixel modelling for actor and icon composites.

    Piece.bake lights each component before assembly. Once layers overlap, some
    final silhouettes become visually flat again. This pass adds a restrained
    one-pixel inner highlight on exposed upper/left edges and a cool inner
    shadow on lower/right edges. It preserves the exact canvas, alpha mask and
    anchor, so higher detail never becomes animation jitter or collision drift.
    """
    if strength <= 0 or image.mode != 'RGBA':
        return image
    source = image.copy()
    alpha = source.getchannel('A')
    solid = _hard(alpha, 160)
    # Boundary pixels that remain inside the final silhouette.
    upper = ImageChops.subtract(solid, ImageChops.darker(_shift(solid, 0, 1), _shift(solid, 1, 0)))
    lower = ImageChops.subtract(solid, ImageChops.darker(_shift(solid, 0, -1), _shift(solid, -1, 0)))
    # Keep the accents one pixel in from the external contour.
    interior = solid.filter(ImageFilter.MinFilter(3))
    upper = ImageChops.darker(_shift(upper, 1, 1), interior)
    lower = ImageChops.darker(_shift(lower, -1, -1), interior)
    out = source.copy()
    warm = canvas(source.size, (255, 236, 205, 255))
    cool = canvas(source.size, (33, 29, 43, 255))
    out = Image.composite(Image.blend(out, warm, strength), out, _fade(upper, 0.82))
    out = Image.composite(Image.blend(out, cool, strength * 0.86), out, _fade(lower, 0.78))
    out.putalpha(alpha)
    return out


def catmull(points, samples=6, closed=False):
    """Smooth a control polyline; keeps organic shapes off the 45 degree grid."""
    pts = [tuple(p) for p in points]
    if len(pts) < 3:
        return pts
    ring = pts + [pts[0]] if closed else pts
    guide = [ring[0]] + ring + [ring[-1]]
    out = []
    for i in range(len(guide) - 3):
        p0, p1, p2, p3 = guide[i:i + 4]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
            ))
    out.append(ring[-1])
    return out


def taper_shape(a, b, width_a, width_b, cap=True):
    """Polygon for a limb or blade that changes thickness along its length."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    ra, rb = width_a / 2.0, width_b / 2.0
    points = [
        (ax + nx * ra, ay + ny * ra), (bx + nx * rb, by + ny * rb),
        (bx - nx * rb, by - ny * rb), (ax - nx * ra, ay - ny * ra),
    ]
    if cap:
        ex, ey = dx / length, dy / length
        points.insert(2, (bx + ex * rb * 0.8, by + ey * rb * 0.8))
        points.append((ax - ex * ra * 0.8, ay - ey * ra * 0.8))
    return points


def arc_points(cx, cy, rx, ry, start, end, steps=14):
    return [(cx + math.cos(start + (end - start) * i / steps) * rx,
             cy + math.sin(start + (end - start) * i / steps) * ry) for i in range(steps + 1)]


class Piece:
    """One flat layer that will be contoured and lit when it is stamped."""

    def __init__(self, size, ramp=None):
        self.image = canvas(size)
        self.draw = ImageDraw.Draw(self.image)
        self.ramp = pigment.ramp(ramp) if ramp is not None else None

    # -- colour resolution -------------------------------------------------
    def _color(self, value):
        if value is None and self.ramp is not None:
            return self.ramp.base
        if isinstance(value, int):
            return self.ramp[value] if self.ramp else (255, 255, 255, 255)
        return rgb(value)

    # -- primitives --------------------------------------------------------
    @staticmethod
    def _round(points):
        return [(round(x), round(y)) for x, y in points]

    @staticmethod
    def _box(box):
        x0, y0, x1, y1 = (round(v) for v in box)
        return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)

    def poly(self, points, color=None):
        pts = self._round(points)
        if len(pts) >= 2:
            self.draw.polygon(pts, fill=self._color(color))
        return self

    def smooth_poly(self, points, color=None, samples=6):
        return self.poly(catmull(points, samples, closed=True), color)

    def rect(self, box, color=None):
        self.draw.rectangle(self._box(box), fill=self._color(color))
        return self

    def ellipse(self, box, color=None):
        self.draw.ellipse(self._box(box), fill=self._color(color))
        return self

    def disc(self, cx, cy, radius, color=None):
        return self.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), color)

    def line(self, points, color=None, width=1):
        pts = self._round(points)
        if len(pts) >= 2:
            self.draw.line(pts, fill=self._color(color), width=max(1, round(width)), joint='curve')
        elif pts:
            self.draw.point(pts[0], fill=self._color(color))
        return self

    def curve(self, points, color=None, width=1, samples=6):
        return self.line(catmull(points, samples), color, width)

    def taper(self, a, b, width_a, width_b, color=None, cap=True):
        return self.poly(taper_shape(a, b, width_a, width_b, cap), color)

    def dot(self, x, y, color=None):
        self.draw.point((round(x), round(y)), fill=self._color(color))
        return self

    def pixels(self, points, color=None):
        fill = self._color(color)
        for x, y in points:
            self.draw.point((round(x), round(y)), fill=fill)
        return self

    def arc(self, box, start, end, color=None, width=1):
        self.draw.arc(self._box(box), start, end, fill=self._color(color), width=max(1, round(width)))
        return self

    # -- surface treatment -------------------------------------------------
    def dither(self, box, color, level=8, phase=0, inside=True):
        """Ordered 4x4 dither; level 0 paints nothing, 16 paints everything."""
        x0, y0, x1, y1 = self._box(box)
        fill = self._color(color)
        alpha = self.image.getchannel('A').load()
        target = self.draw
        for y in range(y0, y1 + 1):
            if y < 0 or y >= self.image.height:
                continue
            for x in range(x0, x1 + 1):
                if x < 0 or x >= self.image.width:
                    continue
                if inside and alpha[x, y] < 110:
                    continue
                if BAYER[(y + phase) % 4][(x + phase) % 4] < level:
                    target.point((x, y), fill=fill)
        return self

    def speckle(self, points, color, jitter=None):
        fill = self._color(color)
        alpha = self.image.getchannel('A').load()
        for x, y in points:
            x, y = round(x), round(y)
            if 0 <= x < self.image.width and 0 <= y < self.image.height and alpha[x, y] >= 110:
                self.draw.point((x, y), fill=fill)
        return self

    def erase(self, box=None, points=None):
        if box is not None:
            self.draw.rectangle(self._box(box), fill=(0, 0, 0, 0))
        if points:
            self.draw.polygon(self._round(points), fill=(0, 0, 0, 0))
        return self

    def erase_ellipse(self, box):
        self.draw.ellipse(self._box(box), fill=(0, 0, 0, 0))
        return self

    def clip(self, mask):
        """Keep only the area covered by another piece or mask image."""
        source = mask.image.getchannel('A') if isinstance(mask, Piece) else mask
        self.image.putalpha(ImageChops.darker(self.image.getchannel('A'), source))
        return self

    def paste(self, image, xy=(0, 0)):
        self.image.alpha_composite(image, (round(xy[0]), round(xy[1])))
        return self

    # -- baking ------------------------------------------------------------
    def form(self, strength=1.0, axis=None):
        """Dithered tonal gradient across the piece, so broad surfaces turn.

        The gradient runs across the short dimension, never along the long one:
        a blade should get lighter across its bevel, not brighter toward the
        point. Slivers are left alone, because the edge bands already shade them.
        """
        if self.ramp is None or strength <= 0:
            return self
        box = self.image.getbbox()
        if box is None:
            return self
        x0, y0, x1, y1 = box
        if min(x1 - x0, y1 - y0) < 8:
            return self
        if axis is None:
            axis = (1, 0) if (y1 - y0) > (x1 - x0) else (0, 1)
        span = max(1.0, (x1 - x0) * abs(axis[0]) + (y1 - y0) * abs(axis[1]))
        alpha = self.image.getchannel('A').load()
        draw = self.draw
        light = rgb(self.ramp[4])
        dark = rgb(self.ramp[2])
        for y in range(y0, y1):
            for x in range(x0, x1):
                if alpha[x, y] < 110:
                    continue
                t = ((x - x0) * axis[0] + (y - y0) * axis[1]) / span
                level = (0.5 - t) * 2.0 * strength          # +1 fully lit, -1 fully shaded
                threshold = BAYER[y % 4][x % 4] / 16.0
                if level > 0 and level > threshold:
                    draw.point((x, y), fill=light)
                elif level < 0 and -level > threshold:
                    draw.point((x, y), fill=dark)
        return self

    def gleam(self, strength=1.0):
        """A specular hit in the upper left of the mass; sells polished metal."""
        if self.ramp is None or strength <= 0:
            return self
        box = self.image.getbbox()
        if box is None:
            return self
        x0, y0, x1, y1 = box
        width, height = x1 - x0, y1 - y0
        if width < 3 or height < 3:
            return self
        if min(width, height) < 6:
            return self
        cx = x0 + width * 0.32
        cy = y0 + height * 0.28
        radius = max(0.8, min(width, height) * 0.15 * strength)
        spot = Piece(self.image.size, self.ramp)
        spot.disc(cx, cy, radius, 5)
        if min(width, height) > 12:
            spot.disc(cx + width * 0.20, cy + height * 0.18, radius * 0.45, 5)
        spot.clip(_hard(self.image.getchannel('A')).filter(ImageFilter.MinFilter(3)))
        self.image.alpha_composite(spot.image)
        return self

    def bake(self, outline=True, rim=0.0, occlude=0.0, contour=None, light=None, dark=None,
             depth=2, bounce=True, gleam=0.0, form=0.0, axis=None):
        """Turn a flat fill into a lit solid.

        Walking inward from each edge gives a band per step, so the piece reads
        highlight, light, body, core shadow, then a cooler bounce along the very
        bottom edge. That last band is what makes the shape look round instead
        of merely outlined.
        """
        image = self.image
        solid = _hard(image.getchannel('A'))
        if solid.getbbox() is None:
            return image
        ramp = self.ramp
        if ramp is not None and (rim or occlude):
            if form:
                self.form(form, axis)
            lit = _shells(solid, 1, 1, depth)
            shade = _shells(solid, -1, -1, depth)
            # A sliver only one or two pixels across belongs to neither side.
            overlap = ImageChops.darker(lit[0], shade[0])
            lit[0] = ImageChops.subtract(lit[0], overlap)
            shade[0] = ImageChops.subtract(shade[0], overlap)
            if occlude:
                core = ramp[1] if dark is None else dark
                edge = shade[1] if len(shade) > 1 else shade[0]
                image.paste(rgb(core), (0, 0), _fade(edge, occlude))
                if bounce and len(shade) > 1:
                    # reflected light: the ground and sky throw a little back
                    image.paste(rgb(blend(ramp[2], (110, 126, 168, 255), 0.30)),
                                (0, 0), _fade(shade[0], occlude * 0.9))
                elif len(shade) == 1:
                    image.paste(rgb(ramp[2]), (0, 0), _fade(shade[0], occlude * 0.7))
            if rim:
                if len(lit) > 1:
                    image.paste(rgb(ramp[4]), (0, 0), _fade(lit[1], rim * 0.55))
                image.paste(rgb(light if light is not None else ramp.rim), (0, 0), _fade(lit[0], rim))
            if gleam:
                self.gleam(gleam)
        if outline:
            colour = contour if contour is not None else (ramp.line if ramp else (26, 22, 30, 255))
            ring = ImageChops.subtract(_grow(solid), solid)
            image.paste(rgb(colour), (0, 0), ring)
        return image


class Sketch:
    """A sprite under construction."""

    def __init__(self, size, ramp=None):
        self.size = (size, size) if isinstance(size, int) else tuple(size)
        self.image = canvas(self.size)
        self.default_ramp = ramp

    def piece(self, ramp=None):
        return Piece(self.size, ramp if ramp is not None else self.default_ramp)

    def stamp(self, piece, outline=True, rim=0.85, occlude=0.55, contour=None, light=None,
              dark=None, offset=(0, 0), depth=2, gleam=0.0, form=0.0, axis=None, bounce=True):
        baked = piece.bake(outline=outline, rim=rim, occlude=occlude, contour=contour, light=light,
                           dark=dark, depth=depth, gleam=gleam, form=form, axis=axis, bounce=bounce)
        self.image.alpha_composite(baked, (round(offset[0]), round(offset[1])))
        return self

    def carve(self, piece, **kwargs):
        """Stamp with the full volume treatment: gradient, bands, bounce, gleam."""
        kwargs.setdefault('rim', 0.95)
        kwargs.setdefault('occlude', 0.8)
        kwargs.setdefault('form', 0.55)
        kwargs.setdefault('gleam', 0.7)
        kwargs.setdefault('depth', 2)
        return self.stamp(piece, **kwargs)

    def overlay(self, piece_or_image, offset=(0, 0)):
        image = piece_or_image.image if isinstance(piece_or_image, Piece) else piece_or_image
        self.image.alpha_composite(image, (round(offset[0]), round(offset[1])))
        return self

    def under(self, piece_or_image, offset=(0, 0)):
        """Place art behind everything drawn so far."""
        image = piece_or_image.image if isinstance(piece_or_image, Piece) else piece_or_image
        base = canvas(self.size)
        base.alpha_composite(image, (round(offset[0]), round(offset[1])))
        base.alpha_composite(self.image)
        self.image = base
        return self

    def glow(self, color, radius=2, strength=0.5):
        """Soft light bloom around the current silhouette, drawn behind it."""
        mask = self.image.getchannel('A').filter(ImageFilter.GaussianBlur(radius))
        mask = mask.point(lambda v, s=strength: round(min(255, v * s)))
        halo = canvas(self.size)
        halo.paste(rgb(color), (0, 0), mask)
        halo.alpha_composite(self.image)
        self.image = halo
        return self

    def shift(self, dx, dy):
        moved = canvas(self.size)
        moved.paste(self.image, (round(dx), round(dy)))
        self.image = moved
        return self

    def tone(self, color, strength):
        """Blend a flat colour into every opaque pixel; used for hit flashes."""
        layer = canvas(self.size)
        layer.paste(rgb(color), (0, 0), self.image.getchannel('A').point(lambda v, s=strength: round(v * s)))
        self.image.alpha_composite(layer)
        return self

    def fade(self, amount):
        self.image.putalpha(self.image.getchannel('A').point(lambda v, a=amount: round(v * a)))
        return self

    def outline_all(self, color, diagonal=False):
        solid = _hard(self.image.getchannel('A'))
        ring = ImageChops.subtract(_grow(solid, diagonal), solid)
        self.image.paste(rgb(color), (0, 0), ring)
        return self

    def quantise(self):
        """Snap partial alpha to on or off so nothing renders as mush."""
        self.image.putalpha(_hard(self.image.getchannel('A'), 96))
        return self

    def result(self):
        return self.image
