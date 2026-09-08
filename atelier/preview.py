#!/usr/bin/env python3
"""Contact sheets for reviewing Atelier art by eye.

Usage: python atelier/preview.py <sheet> [--scale N] [--out PATH]

Sheets: body, walk, states, hair, gear, weapons, items, npcs, beasts, world.
Nothing here writes into the shipped asset folders; output lands in
atelier/preview/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from forge import folk, pigment, rig, smith  # noqa: E402

OUT = Path(__file__).resolve().parent / 'preview'
BACK = (38, 40, 46, 255)
LABEL = (206, 200, 182, 255)


def catalog():
    return json.loads((ROOT / 'content' / 'catalog.json').read_text(encoding='utf-8'))


def grid(cells, columns, scale=3, pad=6, label_height=10):
    """cells: list of (image, caption)."""
    if not cells:
        raise SystemExit('nothing to draw')
    width = max(c[0].width for c in cells)
    height = max(c[0].height for c in cells)
    rows = (len(cells) + columns - 1) // columns
    tile_w = width * scale + pad
    tile_h = height * scale + pad + label_height
    sheet = Image.new('RGBA', (columns * tile_w + pad, rows * tile_h + pad), BACK)
    draw = ImageDraw.Draw(sheet)
    for index, (image, caption) in enumerate(cells):
        x = pad + (index % columns) * tile_w
        y = pad + (index // columns) * tile_h
        big = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        draw.rectangle((x - 1, y - 1, x + big.width, y + big.height), outline=(58, 60, 68, 255))
        sheet.alpha_composite(big, (x, y))
        if caption:
            draw.text((x, y + big.height + 1), caption[:26], fill=LABEL)
    return sheet


def sheet_body(_):
    cells = []
    for direction, name in enumerate(rig.DIRECTIONS):
        for build in range(2):
            for skin in (0, 2, 4):
                cells.append((folk.body_frame(build, skin, 'idle', 0, direction), f'{name} b{build} s{skin}'))
    return grid(cells, 6, 4)


def sheet_walk(_):
    cells = []
    for direction, name in enumerate(rig.DIRECTIONS):
        for frame in range(8):
            cells.append((folk.body_frame(0, 2, 'walk', frame, direction), f'{name} {frame}'))
    return grid(cells, 8, 4)


def sheet_states(_):
    cells = []
    for state in rig.STATES:
        for frame in range(8):
            cells.append((folk.body_frame(0, 2, state, frame, 2), f'{state} {frame}'))
    return grid(cells, 8, 4)


def sheet_hair(_):
    cells = []
    for style in range(6):
        for colour in range(8):
            image = folk.body_frame(0, 2, 'idle', 0, 0)
            image.alpha_composite(folk.hair_frame(style, colour, 'idle', 0, 0))
            cells.append((image, f'{folk.HAIR_STYLES[style]} {colour}'))
    return grid(cells, 8, 3)


def _dressed(items, state='idle', frame=0, direction=0):
    image = folk.body_frame(0, 2, state, frame, direction)
    image.alpha_composite(folk.hair_frame(1, 1, state, frame, direction))
    for item in items:
        image.alpha_composite(folk.armour_frame(item, state, frame, direction))
    return image


def sheet_gear(_):
    data = catalog()
    by_slot = {}
    for item in data['items']:
        slot = item.get('slot')
        if slot:
            by_slot.setdefault(slot, []).append(item)
    cells = []
    for slot, items in sorted(by_slot.items()):
        for item in items[:3]:
            cells.append((_dressed([item]), f'{slot}:{item["id"][:16]}'))
    kit = [next(i for i in data['items'] if i['id'] == key) for key in
           ('steel_helmet', 'steel_chestplate', 'steel_greaves', 'steel_boots', 'steel_gauntlets')
           if any(x['id'] == key for x in data['items'])]
    if kit:
        for direction in range(4):
            cells.append((_dressed(kit, 'idle', 0, direction), 'kit ' + rig.DIRECTIONS[direction]))
    return grid(cells, 6, 4)


def sheet_weapons(_):
    data = catalog()
    seen = {}
    for item in data['items']:
        for tag in item.get('tags', ()):
            if tag in smith.WEAPON_PROFILES or tag in smith.OFFHAND_PROFILES:
                seen.setdefault(tag, item)
    cells = []
    for tag, item in sorted(seen.items()):
        cells.append((smith.icon(item), tag))
        for direction in (0, 2):
            cells.append((_dressed([item], 'attack', 4, direction), f'{tag} {direction}'))
    return grid(cells, 6, 4)


def sheet_items(_):
    data = catalog()
    picked = {}
    for item in data['items']:
        key = item['type'] + ':' + (item.get('slot') or '')
        picked.setdefault(key, []).append(item)
    cells = []
    for key, items in sorted(picked.items()):
        for item in items[:4]:
            cells.append((smith.icon(item), item['id'][:20]))
    return grid(cells, 10, 4)


def sheet_npcs(_):
    cells = []
    for role in sorted(folk.ROLE_LOOK):
        for direction in (0, 2):
            cells.append((folk.npc_frame(role, 'idle', 0, direction), role[:16]))
    return grid(cells, 8, 3)


def sheet_beasts(args):
    from forge import beasts
    data = catalog()
    families = {}
    for mob in data['mobs']:
        families.setdefault(mob['family'], mob)
    cells = []
    for family, mob in sorted(families.items()):
        image = beasts.frame(mob, 'idle', 0, 0)
        cells.append((image, family[:18]))
    return grid(cells, 10, 3)


def sheet_world(args):
    from forge import lands
    data = catalog()
    cells = []
    for kind in lands.TERRAIN:
        cells.append((lands.tile(kind, 0), kind))
    for name in lands.PROPS:
        cells.append((lands.prop(name), name))
    for definition in data['resources'][:12]:
        cells.append((lands.resource(definition), definition['id'][:16]))
    for kind in lands.CHESTS:
        cells.append((lands.chest(kind, False), kind))
    return grid(cells, 10, 3)


def sheet_scene(args):
    """A village corner at 1:1, then scaled up. This is the honest test: the art
    has to hold together as a scene, not just as rows of separate sprites."""
    from forge import beasts, lands
    data = catalog()
    tiles_x, tiles_y = 21, 13
    view = Image.new('RGBA', (tiles_x * 32, tiles_y * 32), (0, 0, 0, 255))
    path_rows = {7, 8}
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            kind = 'dirt' if ty in path_rows else ('grass' if (tx + ty) % 17 else 'moss')
            view.alpha_composite(lands.tile(kind, (tx * 3 + ty) % 4), (tx * 32, ty * 32))

    def place(image, tile_x, tile_y, anchor='feet'):
        px = round(tile_x * 32 + 16 - image.width / 2)
        py = round(tile_y * 32 + 32 - image.height + 5) if anchor == 'feet' else round(tile_y * 32)
        view.alpha_composite(image, (px, py))

    zone = next(z for z in data['zones'] if z['buildings'])
    building = zone['buildings'][0]
    house = lands.building({'id': zone['id'], 'biome': zone.get('biome', '')}, dict(building, width=6, height=4))
    view.alpha_composite(house, (2 * 32, 0))
    place(lands.prop('oak'), 16, 3)
    place(lands.prop('pine'), 19, 6)
    place(lands.prop('bush'), 15, 6)
    place(lands.prop('rock'), 1, 10)
    place(lands.prop('flowers'), 6, 10)
    place(lands.prop('grass_tuft'), 12, 11)
    place(lands.structure('structure_campfire'), 9, 10)
    place(lands.chest('royal', False), 13, 9)
    node = next((r for r in data['resources'] if r['skill'] == 'mining'), data['resources'][0])
    place(lands.resource(node), 3, 11)

    shadow = lands.prop('shadow')

    def actor(image, tile_x, tile_y):
        px = round(tile_x * 32 + 16)
        py = round(tile_y * 32 + 27)
        view.alpha_composite(shadow, (px - 16, py - 6))
        view.alpha_composite(image, (px - 32, py - 55))

    items = {i['id']: i for i in data['items']}

    def gear(*ids):
        return [items[i] for i in ids if i in items]

    def dressed(build, skin, hair_style, hair_colour, kit, state, frame, direction):
        image = folk.body_frame(build, skin, state, frame, direction)
        image.alpha_composite(folk.hair_frame(hair_style, hair_colour, state, frame, direction))
        for item in kit:
            image.alpha_composite(folk.armour_frame(item, state, frame, direction))
        return image

    knight = gear('steel_cloak', 'steel_chest', 'steel_legs', 'steel_boots', 'steel_belt',
                  'steel_gloves', 'steel_helmet', 'steel_sword', 'steel_shield')
    if not knight:
        knight = [i for i in data['items'] if i.get('slot')][:8]
    actor(dressed(0, 2, 2, 1, knight, 'walk', 3, 2), 8, 8)
    ranger = gear('linen_medium_chest', 'linen_medium_legs', 'linen_medium_boots',
                  'linen_medium_cloak', 'yew_bow')
    actor(dressed(1, 4, 1, 4, ranger, 'idle', 2, 0), 11, 8)
    actor(folk.npc_frame('blacksmith', 'idle', 1, 0), 5, 7)
    actor(folk.npc_frame('herbalist', 'idle', 4, 2), 6, 11)
    mobs = {m['family']: m for m in data['mobs']}
    if 'wolf' in mobs:
        actor(beasts.frame(mobs['wolf'], 'walk', 5, 1), 16, 9)
    if 'crow' in mobs:
        actor(beasts.frame(mobs['crow'], 'idle', 2, 2), 18, 3)
    if 'rat' in mobs:
        actor(beasts.frame(mobs['rat'], 'walk', 1, 2), 13, 11)
    scale = 3
    return view.resize((view.width * scale, view.height * scale), Image.Resampling.NEAREST)


def sheet_ladder(args):
    """Every weapon and off-hand across every tier: the variety check."""
    from forge import gear
    items = {item['id']: item for item in gear.catalogue()}
    rows = list(gear.WEAPONS) + list(gear.OFFHANDS)
    cells = []
    for kind in rows:
        for tier in gear.TIERS:
            cells.append((smith.icon(items['%s_%s' % (tier.key, kind)]),
                          '%s %d' % (tier.metal_name[:6], tier.level)))
    return grid(cells, len(gear.TIERS), 4)


def sheet_armour(args):
    from forge import gear
    items = {item['id']: item for item in gear.catalogue()}
    cells = []
    for weight in gear.WEIGHTS:
        for slot in gear.ARMOUR_SLOTS:
            for tier in gear.TIERS:
                cells.append((smith.icon(items['%s_%s_%s' % (tier.key, weight, slot)]),
                              '%s %s' % (tier.metal_name[:6], slot[:5])))
    return grid(cells, len(gear.TIERS), 4)


def sheet_sets(args):
    """A full set from every tier, worn, in the client's own layer order."""
    from forge import gear
    items = {item['id']: item for item in gear.catalogue()}

    def kit(tier, weight, weapon, offhand):
        equipment = {slot: items['%s_%s_%s' % (tier.key, weight, slot)]
                     for slot in gear.ARMOUR_SLOTS}
        equipment['weapon'] = items['%s_%s' % (tier.key, weapon)]
        equipment['offhand'] = items['%s_%s' % (tier.key, offhand)]
        equipment['necklace'] = items['%s_necklace' % tier.key]
        return equipment

    cells = []
    for weight, weapon, offhand, state, frame, direction in (
            ('heavy', 'sword', 'shield', 'idle', 0, 0),
            ('heavy', 'greataxe', 'shield', 'walk', 3, 2),
            ('medium', 'bow', 'quiver', 'idle', 0, 0),
            ('light', 'staff', 'orb', 'cast', 4, 0)):
        for tier in gear.TIERS:
            cells.append((folk.dress(kit(tier, weight, weapon, offhand), state, frame, direction),
                          '%s %d' % (tier.metal_name[:7], tier.level)))
    return grid(cells, len(gear.TIERS), 3)


def sheet_accessories(args):
    """Rings, amulets, charms and relics across the whole ladder."""
    from forge import gear
    items = {item['id']: item for item in gear.catalogue()}
    cells = []
    for kind in gear.ACCESSORIES:
        for tier in gear.TIERS:
            cells.append((smith.icon(items['%s_%s' % (tier.key, kind)]),
                          '%s %s' % (tier.metal_name[:6], kind[:4])))
    return grid(cells, len(gear.TIERS), 5)


def sheet_kin(args):
    """Every creature in the catalogue, to check they read as individuals."""
    from forge import beasts
    data = catalog()
    cells = []
    for mob in data['mobs']:
        image = beasts.frame(mob, 'idle', 0, 2)
        if image.width > 64:
            image = image.resize((64, 64), Image.Resampling.NEAREST)
        cells.append((image, mob['id'][:17]))
    return grid(cells, 12, 2)


SHEETS = {
    'accessories': sheet_accessories, 'kin': sheet_kin,
    'ladder': sheet_ladder, 'armour': sheet_armour, 'sets': sheet_sets,
    'body': sheet_body, 'walk': sheet_walk, 'states': sheet_states, 'hair': sheet_hair,
    'gear': sheet_gear, 'weapons': sheet_weapons, 'items': sheet_items, 'npcs': sheet_npcs,
    'beasts': sheet_beasts, 'world': sheet_world, 'scene': sheet_scene,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('sheet', choices=sorted(SHEETS))
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    image = SHEETS[args.sheet](args)
    OUT.mkdir(parents=True, exist_ok=True)
    path = Path(args.out) if args.out else OUT / (args.sheet + '.png')
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    print('wrote', path, image.size)


if __name__ == '__main__':
    main()
