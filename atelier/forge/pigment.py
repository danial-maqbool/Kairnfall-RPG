"""Colour system for the Atelier sprite library.

Every material resolves to a six stop ramp built by rotating hue as value moves:
shadows drift toward violet, highlights drift toward warm gold. Flat value
scaling makes pixel art look plastic, so each step here carries a hue and a
saturation change as well as a brightness change.
"""
from __future__ import annotations

import colorsys
import hashlib
from dataclasses import dataclass

SHADOW_HUE = 0.70   # violet-blue
LIGHT_HUE = 0.115   # warm gold

# dv, ds, hue pull toward shadow, hue pull toward light
CURVE = (
    (-0.56, 0.14, 0.26, 0.00),
    (-0.36, 0.09, 0.17, 0.00),
    (-0.17, 0.04, 0.08, 0.00),
    (0.00, 0.00, 0.00, 0.00),
    (0.15, -0.07, 0.00, 0.13),
    (0.29, -0.15, 0.00, 0.24),
)


def rgb(value):
    """Accept '#rrggbb', 'rrggbb', (r,g,b) or (r,g,b,a) and return rgba."""
    if isinstance(value, str):
        text = value.lstrip('#')
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    value = tuple(value)
    return value if len(value) == 4 else value + (255,)


def hexstr(color):
    r, g, b = rgb(color)[:3]
    return '#%02x%02x%02x' % (r, g, b)


def _rotate(hue, target, amount):
    if amount <= 0:
        return hue
    delta = ((target - hue + 0.5) % 1.0) - 0.5
    return (hue + delta * amount) % 1.0


def _step(base, dv, ds, to_shadow, to_light):
    r, g, b, a = rgb(base)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = _rotate(h, SHADOW_HUE, to_shadow)
    h = _rotate(h, LIGHT_HUE, to_light)
    s = min(1.0, max(0.0, s + ds))
    v = min(1.0, max(0.02, v + dv * (0.55 + 0.45 * v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return round(r * 255), round(g * 255), round(b * 255), a


@dataclass(frozen=True)
class Ramp:
    """Six ordered stops plus the derived contour colour."""

    stops: tuple
    line: tuple

    def __getitem__(self, index):
        return self.stops[max(0, min(5, index))]

    @property
    def deep(self):
        return self.stops[0]

    @property
    def shade(self):
        return self.stops[1]

    @property
    def base(self):
        return self.stops[3]

    @property
    def light(self):
        return self.stops[4]

    @property
    def rim(self):
        return self.stops[5]

    def lift(self, amount=0.10):
        return Ramp(tuple(_step(s, amount, -0.02, 0, 0.05) for s in self.stops), self.line)

    def toward(self, other, weight):
        return build(blend(self.base, other, weight))


def build(base):
    stops = tuple(_step(base, *values) for values in CURVE)
    r, g, b, a = rgb(base)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = _rotate(h, SHADOW_HUE, 0.34)
    s = min(1.0, s * 1.15 + 0.14)
    v = max(0.055, v * 0.27)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return Ramp(stops, (round(r * 255), round(g * 255), round(b * 255), a))


_CACHE: dict = {}


def ramp(base):
    """Cached ramp lookup; accepts a material name, a colour or a Ramp."""
    if isinstance(base, Ramp):
        return base
    key = base if isinstance(base, str) else tuple(base)
    found = _CACHE.get(key)
    if found is None:
        found = build(MATERIALS.get(base, base) if isinstance(base, str) else base)
        _CACHE[key] = found
    return found


def blend(a, b, weight):
    a, b = rgb(a), rgb(b)
    return tuple(round(a[i] * (1 - weight) + b[i] * weight) for i in range(4))


def tint(color, amount, target=(255, 244, 214, 255)):
    return blend(color, target, amount)


def alpha(color, value):
    r, g, b = rgb(color)[:3]
    return (r, g, b, max(0, min(255, round(value))))


def keyed(text, span=None):
    """Stable integer derived from a string; this library never uses clock time."""
    number = int.from_bytes(hashlib.blake2b(text.encode('utf-8'), digest_size=6).digest(), 'little')
    return number if span is None else number % span


MATERIALS = {
    # worked metal
    'copper': '#b06a3c', 'bronze': '#9c7b3e', 'iron': '#7d858d', 'steel': '#a9b6c0',
    'silver': '#cfd8dd', 'cobalt': '#5d84ad', 'mithril': '#8fc4bd', 'obsidian': '#5b5468',
    'aetherium': '#a8b8e2', 'gold': '#d0a63f', 'metal': '#9aa5ae', 'wood_metal': '#8f9aa0',
    'tin': '#b5b9bc', 'brass': '#bb9445',
    # timber
    'oak': '#8d6942', 'ash': '#a98a5d', 'yew': '#87604a', 'ironwood': '#5f5b4e',
    'blackwood': '#463f48', 'elderwood': '#a3946a', 'emberwood': '#8e5340',
    'starwood': '#9aa0bb', 'wood': '#8a6a49', 'wood_stone': '#8b8478',
    # soft goods
    'cloth': '#6d7a92', 'leather': '#8a5f3c', 'silk': '#c2b8d6', 'linen': '#c8bda2',
    'wool': '#b9b1a0', 'fiber': '#a89a76', 'fur': '#8a6b4e', 'feather': '#c9c2b4',
    'hide': '#9a7550', 'rope': '#b19a6c',
    # earth and stone
    'stone': '#7f8079', 'granite': '#8a8b86', 'slate': '#606773', 'marble': '#ccc9bd',
    'sand': '#c3ac82', 'soil': '#6f5842', 'coal': '#3f3f45', 'salt': '#dfe2e4',
    # organic
    'bone': '#d6cdb2', 'organic': '#87a05e', 'leaf': '#6d8f4c', 'seed': '#b9a05e',
    'meat': '#a85a4e', 'bread': '#c69a5f', 'food': '#c08a52', 'scale': '#6f9a72',
    'ectoplasm': '#9fd4c8', 'blood': '#8c3a33', 'chitin': '#6b5a4a',
    # arcane and glass
    'crystal': '#8fb9c8', 'glass': '#a9c6cf', 'red_glass': '#b6474b', 'blue_glass': '#4c72b6',
    'green_glass': '#4fa06a', 'runestone': '#7b6f96', 'paper': '#d3c7a6', 'book': '#7a5240',
    'ink': '#3a3f5c', 'ember': '#c96b3c', 'gem': '#b4577f',
}

ELEMENTS = {
    'Physical': '#c6b9a4', 'Fire': '#e07a44', 'Frost': '#7fc4d8', 'Lightning': '#e8cf5e',
    'Nature': '#77a95c', 'Poison': '#9fc258', 'Arcane': '#a98fd0', 'Radiant': '#f0dc9e',
    'Shadow': '#7a6b9e',
}

SKIN = ('#f1cba4', '#e0ab7c', '#c28656', '#98643c', '#70472c', '#4c3122')
HAIR = ('#2b2430', '#4d3324', '#70492c', '#8b442a', '#c9a05a', '#ded1b0', '#9a9691', '#a8492f')


def element_ramp(name):
    return ramp(ELEMENTS.get(name, '#c6b9a4'))


def material_ramp(name, fallback='#9aa5ae'):
    return ramp(MATERIALS.get(name, fallback))
