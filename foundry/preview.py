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


def nine_slice(image, width, height, corner=face.CORNER):
    """Preview the actual 48/16 source contract without scaling corner pixels."""
    if min(width, height) < corner * 2:
        raise ValueError('A panel must fit both fixed corners.')
    source_x = (0, corner, image.width - corner, image.width)
    source_y = (0, corner, image.height - corner, image.height)
    target_x = (0, corner, width - corner, width)
    target_y = (0, corner, height - corner, height)
    out = Image.new('RGBA', (width, height))
    for row in range(3):
        for column in range(3):
            w = target_x[column + 1] - target_x[column]
            h = target_y[row + 1] - target_y[row]
            if not w or not h:
                continue
            piece = image.crop((source_x[column], source_y[row],
                                source_x[column + 1], source_y[row + 1]))
            out.alpha_composite(piece.resize((w, h), Image.Resampling.NEAREST),
                                (target_x[column], target_y[row]))
    return out


def sheet_panels(_):
    """Populated panels at native scene scale and different nine-slice sizes."""
    view = Image.new('RGBA', (700, 330), BACK)
    draw = ImageDraw.Draw(view)
    draw.text((12, 8), '48x48 sources / 16px fixed corners / no magnified center grain', fill=LABEL)
    for row, name in enumerate(('tooltip', 'inset')):
        y = 38 + row * 140
        source = face.panel(name)
        view.alpha_composite(source, (12, y + 25))
        draw.text((12, y + 80), name, fill=LABEL)
        x = 90
        for w, h in ((132, 96), (202, 104), (248, 112)):
            view.alpha_composite(nine_slice(source, w, h), (x, y))
            draw.text((x + 15, y + 15), 'IRON SWORD', fill='#eee5d4')
            draw.text((x + 15, y + 37), 'Power 12   +3', fill='#c8dca2')
            draw.text((x + 15, y + 57), 'Weight 4', fill='#eee5d4')
            draw.text((x + 15, y + 75), 'Common weapon', fill='#ded4c5')
            x += w + 8
    return view.resize((1400, 660), Image.Resampling.NEAREST)


def sheet_terrain(_):
    """Mixed variants and repeated single variants, so repeat artifacts stay visible."""
    from forge import lands
    kinds = ('grass', 'moss', 'marsh', 'dirt', 'sand', 'ash', 'snow')
    view = Image.new('RGBA', (7 * 164, 366), BACK)
    draw = ImageDraw.Draw(view)
    for column, kind in enumerate(kinds):
        x = column * 164 + 2
        draw.text((x, 8), kind + ' / mixed', fill=LABEL)
        for row in range(4):
            for tile_x in range(5):
                variant = ground.pigment.keyed('field:%d:%d' % (tile_x, row)) % 4
                view.alpha_composite(lands.tile(kind, variant), (x + tile_x * 32, 28 + row * 32))
        draw.text((x, 176), 'repeat variant 0', fill=LABEL)
        for row in range(4):
            for tile_x in range(5):
                view.alpha_composite(lands.tile(kind, 0), (x + tile_x * 32, 196 + row * 32))
    return view.resize((view.width * 2, view.height * 2), Image.Resampling.NEAREST)


CLIFF_LAYOUTS = {
    'ledge': (
        ('corner_left', 'top', 'top', 'top', 'top', 'top', 'corner_right'),
        ('left', 'face', 'face', 'face', 'face', 'face', 'right'),
        ('foot_left', 'foot', 'foot', 'foot', 'foot', 'foot', 'foot_right'),
    ),
    'step': (
        (None, None, 'corner_left', 'top', 'corner_right', None, None),
        (None, None, 'left', 'face', 'right', None, None),
        ('corner_left', 'top', 'inner_right', 'face', 'inner_left', 'top', 'corner_right'),
        ('left', 'face', 'face', 'face', 'face', 'face', 'right'),
        ('foot_left', 'foot', 'foot', 'foot', 'foot', 'foot', 'foot_right'),
    ),
}


def paste_cliff_layout(view, layout, tx=0, ty=0, variant=0):
    for y, row in enumerate(layout):
        for x, name in enumerate(row):
            if name:
                view.alpha_composite(ground.cliff(name, (variant + x) % 4),
                                     ((tx + x) * 32, (ty + y) * 32))


def sheet_cliffs(_):
    """All sockets, then mixed-variant joins with convex and concave turns."""
    from forge import lands
    sheet = Image.new('RGBA', (1024, 766), BACK)
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 10), 'CLIFF SOCKETS / 32px tiles at 2x / shared strata across variants', fill=LABEL)
    for i, name in enumerate(ground.CLIFF_PIECES):
        x, y = 16 + i % 6 * 166, 32 + i // 6 * 92
        image = lands.tile('grass', 0); image.alpha_composite(ground.cliff(name))
        sheet.alpha_composite(image.resize((64, 64), Image.Resampling.NEAREST), (x, y))
        draw.text((x, y + 67), name, fill=LABEL)
    for i, (name, layout) in enumerate(CLIFF_LAYOUTS.items()):
        w, h = len(layout[0]) + 2, len(layout) + 2
        view = Image.new('RGBA', (w * 32, h * 32))
        for y in range(h):
            for x in range(w):
                view.alpha_composite(lands.tile('grass', ground.pigment.keyed('cliff-field:%d:%d' % (x,y)) % 4), (x*32,y*32))
        paste_cliff_layout(view, layout, 1, 1)
        x, y = 16 + i * 496, 270
        draw.text((x, y - 18), name + ' / mixed variants / NO GRID GAPS', fill=LABEL)
        sheet.alpha_composite(view.resize((w*48,h*48), Image.Resampling.NEAREST), (x,y))
    draw.text((16, 690), 'Assembly: corner/top/corner -> left/face/right -> foot_left/foot/foot_right', fill=LABEL)
    draw.text((16, 710), 'Inner turns connect the side of a raised section to the lower top edge.', fill=LABEL)
    draw.text((16, 730), 'Preview only: these pieces define artwork, not collision or elevation rules.', fill=LABEL)
    return sheet


def sheet_ground(_):
    """A worked map: patches, shoreline, road and cliff, all using the set."""
    from forge import lands
    width, height = 22, 15
    view = Image.new('RGBA', (width * 32, height * 32), (0, 0, 0, 255))
    for ty in range(height):
        for tx in range(width):
            view.alpha_composite(lands.tile('grass', ground.pigment.keyed('field:%d:%d' % (tx, ty)) % 4), (tx * 32, ty * 32))

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
    paste_cliff_layout(view, CLIFF_LAYOUTS['ledge'], 13, 11)
    return view.resize((view.width * 2, view.height * 2), Image.Resampling.NEAREST)


def sheet_scene(_):
    """The HUD over a scene: bars, slots, a portrait and a minimap."""
    base = sheet_ground(None).resize((704, 480), Image.Resampling.NEAREST)
    view = Image.new('RGBA', (704, 480), (0, 0, 0, 255))
    view.alpha_composite(base)

    def nine(panel_image, x, y, w, h):
        view.alpha_composite(nine_slice(panel_image, w, h), (x, y))

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
          'portraits': sheet_portraits, 'scene': sheet_scene, 'cliffs': sheet_cliffs,
          'panels': sheet_panels, 'terrain': sheet_terrain}


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
