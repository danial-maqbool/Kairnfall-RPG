#!/usr/bin/env python3
"""Contact sheets for reviewing the Foundry pack by eye.

Usage: python foundry/preview.py <sheet>

Sheets: vfx, ground, ui, portraits, scene.
Output lands in foundry/preview/.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'atelier'))

from kit import face, ground, portraits, vfx  # noqa: E402

OUT = HERE / 'preview'
BACK = (26, 28, 34, 255)
LABEL = (206, 200, 182, 255)


def catalogue():
    path = ROOT / 'content' / 'catalog.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else None


def grid(cells, columns, scale=3, pad=6, label=12):
    width = max(c[0].width for c in cells)
    height = max(c[0].height for c in cells)
    rows = (len(cells) + columns - 1) // columns
    tile_w, tile_h = width * scale + pad, height * scale + pad + label
    sheet = Image.new('RGBA', (columns * tile_w + pad, rows * tile_h + pad), BACK)
    draw = ImageDraw.Draw(sheet)
    for index, (image, caption) in enumerate(cells):
        x = pad + (index % columns) * tile_w
        y = pad + (index // columns) * tile_h
        big = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        sheet.alpha_composite(big, (x + (width * scale - big.width) // 2, y))
        if caption:
            draw.text((x, y + height * scale + 1), caption[:24], fill=LABEL)
    return sheet


def sheet_vfx(_):
    """Every effect, one row per effect, frames left to right."""
    plan = vfx.plan()
    scale, cell = 2, 64 * 2
    sheet = Image.new('RGBA', (vfx.FRAMES * (cell + 4) + 160, len(plan) * (cell + 12) + 6), BACK)
    draw = ImageDraw.Draw(sheet)
    for row, (key, size, maker) in enumerate(plan):
        y = 6 + row * (cell + 12)
        draw.text((4, y + cell // 2), key.split('/')[1][:20], fill=LABEL)
        for frame in range(vfx.FRAMES):
            image = maker(frame)
            big = image.resize((size * scale, size * scale), Image.Resampling.NEAREST)
            sheet.alpha_composite(big, (160 + frame * (cell + 4) + (cell - big.width) // 2,
                                        y + (cell - big.height) // 2))
    return sheet


def sheet_ui(_):
    return grid([(maker(), key.split('/')[1]) for key, maker in face.plan()], 11, 3)


def sheet_portraits(_):
    cells = []
    for build in range(portraits.BUILDS):
        for skin in range(portraits.SKINS):
            image = portraits.base(build, skin)
            image.alpha_composite(portraits.hair((build * 3 + skin) % 6, (skin + build) % 8))
            cells.append((image, 'player %d/%d' % (build, skin)))
    from forge import folk
    for role in sorted(folk.ROLE_LOOK):
        cells.append((portraits.townsfolk(role), role))
    data = catalogue()
    if data:
        for mob in data['mobs']:
            if mob.get('boss'):
                cells.append((portraits.creature(mob), mob['id'][:16]))
    return grid(cells, 10, 3)


def sheet_ground(_):
    """A worked map: patches, shoreline, road and cliff, all using the set."""
    from forge import lands
    width, height = 22, 15
    view = Image.new('RGBA', (width * 32, height * 32), (0, 0, 0, 255))
    for ty in range(height):
        for tx in range(width):
            view.alpha_composite(lands.tile('grass', (tx * 3 + ty) % 4), (tx * 32, ty * 32))

    def mask_of(cells, tx, ty):
        mask = 0
        if (tx, ty - 1) in cells:
            mask |= ground.NORTH
        if (tx + 1, ty) in cells:
            mask |= ground.EAST
        if (tx, ty + 1) in cells:
            mask |= ground.SOUTH
        if (tx - 1, ty) in cells:
            mask |= ground.WEST
        return mask

    def patch(cells, kind, foam=False):
        found = set(cells)
        for tx, ty in cells:
            mask = mask_of(found, tx, ty)
            variant = (tx * 5 + ty * 3) % 4
            view.alpha_composite(ground.overlay(kind, mask, variant), (tx * 32, ty * 32))
            for corner, (dx, dy, first, second) in {
                    'ne': (1, -1, ground.NORTH, ground.EAST),
                    'se': (1, 1, ground.SOUTH, ground.EAST),
                    'sw': (-1, 1, ground.SOUTH, ground.WEST),
                    'nw': (-1, -1, ground.NORTH, ground.WEST)}.items():
                if mask & first and mask & second and (tx + dx, ty + dy) not in found:
                    view.alpha_composite(ground.corner_overlay(kind, corner, variant),
                                         (tx * 32, ty * 32))
        if foam:
            for tx, ty in cells:
                view.alpha_composite(ground.foam(mask_of(found, tx, ty), 0,
                                                 (tx * 5 + ty * 3) % 4), (tx * 32, ty * 32))

    patch([(x, y) for x in range(2, 9) for y in range(1, 7)
           if (x - 5) ** 2 / 9 + (y - 4) ** 2 / 5 < 2.2], 'sand')
    patch([(x, y) for x in range(12, 20) for y in range(1, 8)
           if (x - 15) ** 2 / 9 + (y - 4) ** 2 / 6 < 2.0], 'water', foam=True)
    patch([(x, y) for x in range(3, 8) for y in range(10, 13)], 'stone')
    road = [(x, 8) for x in range(0, width)] + [(10, y) for y in range(8, 15)]
    found = set(road)
    for tx, ty in road:
        view.alpha_composite(ground.road(mask_of(found, tx, ty), (tx + ty) % 4), (tx * 32, ty * 32))
    for x in range(14, 20):
        view.alpha_composite(ground.cliff('top'), (x * 32, 12 * 32))
        view.alpha_composite(ground.cliff('face'), (x * 32, 13 * 32))
    view.alpha_composite(ground.cliff('corner_left'), (13 * 32, 12 * 32))
    return view.resize((view.width * 2, view.height * 2), Image.Resampling.NEAREST)


def sheet_scene(_):
    """The HUD over a scene: bars, slots, a portrait and a minimap."""
    base = sheet_ground(None).resize((704, 480), Image.Resampling.NEAREST)
    view = Image.new('RGBA', (704, 480), (0, 0, 0, 255))
    view.alpha_composite(base)

    def nine(panel_image, x, y, w, h, corner=face.CORNER):
        """Stretch a nine-slice source to fill a rectangle."""
        size = panel_image.width
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        parts = [(0, 0, corner, corner), (corner, 0, size - corner, corner),
                 (size - corner, 0, size, corner), (0, corner, corner, size - corner),
                 (corner, corner, size - corner, size - corner),
                 (size - corner, corner, size, size - corner),
                 (0, size - corner, corner, size), (corner, size - corner, size - corner, size),
                 (size - corner, size - corner, size, size)]
        targets = [(0, 0, corner, corner), (corner, 0, w - corner, corner),
                   (w - corner, 0, w, corner), (0, corner, corner, h - corner),
                   (corner, corner, w - corner, h - corner),
                   (w - corner, corner, w, h - corner),
                   (0, h - corner, corner, h), (corner, h - corner, w - corner, h),
                   (w - corner, h - corner, w, h)]
        for source, target in zip(parts, targets):
            tile = panel_image.crop(source)
            tw, th = max(1, target[2] - target[0]), max(1, target[3] - target[1])
            out.alpha_composite(tile.resize((tw, th), Image.Resampling.NEAREST),
                                (target[0], target[1]))
        view.alpha_composite(out, (x, y))

    window = face.panel('window')
    nine(window, 8, 8, 190, 60)
    view.alpha_composite(portraits.townsfolk('blacksmith').resize((48, 48), Image.Resampling.NEAREST),
                         (14, 14))
    frame = face.bar_frame()
    for index, kind in enumerate(('health', 'mana', 'stamina')):
        view.alpha_composite(frame, (68, 14 + index * 16))
        fill = face.bar_fill(kind)
        keep = int(fill.width * (0.82 - index * 0.22))
        view.alpha_composite(fill.crop((0, 0, keep, fill.height)), (71, 17 + index * 16))

    minimap = face.minimap_frame()
    view.alpha_composite(minimap, (704 - 104, 8))
    view.alpha_composite(face.compass(), (704 - 40, 104))

    slots = face.slot('hotbar')
    rarities = [name for name, _ in face.RARITY]
    for index in range(8):
        x = 704 // 2 - (8 * 42) // 2 + index * 42
        view.alpha_composite(slots, (x, 480 - 50))
        if index < len(rarities):
            view.alpha_composite(face.rarity_frame(rarities[index],
                                                   dict(face.RARITY)[rarities[index]]),
                                 (x, 480 - 50))
    nine(face.panel('tooltip'), 704 - 190, 480 - 150, 180, 90)
    for index, name in enumerate(('bag', 'map', 'quest', 'settings')):
        view.alpha_composite(face.icon(name), (12 + index * 22, 76))
    view.alpha_composite(face.cursor('pointer'), (330, 220))
    return view.resize((view.width * 2, view.height * 2), Image.Resampling.NEAREST)


SHEETS = {'vfx': sheet_vfx, 'ground': sheet_ground, 'ui': sheet_ui,
          'portraits': sheet_portraits, 'scene': sheet_scene}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sheet', choices=sorted(SHEETS))
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    image = SHEETS[args.sheet](args)
    OUT.mkdir(parents=True, exist_ok=True)
    path = Path(args.out) if args.out else OUT / (args.sheet + '.png')
    image.save(path)
    print('wrote', path, image.size)


if __name__ == '__main__':
    main()
