"""Authored room furnishings and service yards.

Dimensions are authoritative floor footprints in tiles. Rise is the number of
pixels above that footprint. The art builder uses the same definitions. Rugs
and paving are ground layers; furniture has real server-side collision.
"""
from __future__ import annotations

# width, floor depth, vertical rise, solid, ground layer
FURNITURE = {
    'hearth': (3, 2, 56, True, False),
    'dining_table': (3, 2, 18, True, False),
    'bench': (3, 1, 10, True, False),
    'chair': (1, 1, 22, True, False),
    'bar_counter': (4, 1, 28, True, False),
    'shop_counter': (4, 1, 28, True, False),
    'shelf_food': (3, 1, 64, True, False),
    'shelf_potions': (3, 1, 64, True, False),
    'shelf_goods': (3, 1, 52, True, False),
    'bed': (2, 3, 16, True, False),
    'barrel': (1, 1, 28, True, False),
    'woodpile': (2, 1, 18, True, False),
    'forge': (3, 2, 64, True, False),
    'anvil': (2, 1, 20, True, False),
    'weapon_rack': (3, 1, 56, True, False),
    'armor_stand': (1, 1, 64, True, False),
    'workbench': (3, 1, 24, True, False),
    'quench': (1, 1, 24, True, False),
    'ore_sacks': (2, 1, 20, True, False),
    'crate_stack': (2, 1, 40, True, False),
    'bookcase': (3, 1, 64, True, False),
    'lectern': (1, 1, 40, True, False),
    'practice_dummy': (1, 1, 56, True, False),
    'target_board': (2, 1, 56, True, False),
    'map_board': (3, 1, 52, True, False),
    'rug_warm': (6, 5, 0, False, True),
    'rug_work': (6, 5, 0, False, True),
    'practice_ring': (6, 5, 0, False, True),
    'runner': (2, 8, 0, False, True),
    'paving_mosaic': (5, 5, 0, False, True),
    'flower_bed': (2, 1, 0, False, True),
    'well': (2, 2, 48, True, False),
    'cart': (3, 2, 30, True, False),
    'fence': (3, 1, 24, True, False),
}

ROOMS = {
    'inn': [
        ('bed',5,5), ('bed',10,5), ('woodpile',22,9), ('hearth',24,7),
        ('shelf_food',21,5), ('bar_counter',19,19), ('barrel',24,19),
        ('rug_warm',13,20), ('runner',15,20),
        ('dining_table',6,21), ('bench',6,24), ('chair',5,22), ('chair',10,22),
        ('dining_table',23,22), ('bench',23,25), ('chair',22,23), ('chair',27,23),
        ('bookcase',6,10),
    ],
    'forge': [
        ('forge',23,5), ('woodpile',23,8), ('ore_sacks',25,10),
        ('weapon_rack',6,5), ('armor_stand',10,6), ('armor_stand',12,6),
        ('workbench',5,10), ('crate_stack',9,10),
        ('rug_work',13,20), ('anvil',19,21), ('quench',22,21),
        ('workbench',6,22), ('ore_sacks',10,23), ('weapon_rack',24,24),
        ('barrel',25,20), ('woodpile',6,25),
    ],
    'shop': [
        ('shelf_food',5,5), ('shelf_goods',10,5), ('shelf_potions',20,5),
        ('shelf_goods',25,5), ('crate_stack',6,10), ('barrel',10,11),
        ('shop_counter',19,19), ('rug_warm',13,20), ('runner',15,20),
        ('shelf_goods',5,22), ('shelf_food',10,22),
        ('crate_stack',24,23), ('barrel',27,23), ('ore_sacks',24,26),
    ],
    'workshop': [
        ('map_board',5,5), ('bookcase',10,5), ('weapon_rack',22,5),
        ('target_board',24,10), ('workbench',5,10),
        ('practice_ring',20,20), ('practice_dummy',21,21), ('practice_dummy',25,21),
        ('rug_work',13,20), ('lectern',19,19), ('workbench',6,22),
        ('bench',6,24), ('weapon_rack',10,26), ('crate_stack',25,25),
    ],
    'hall': [
        ('bookcase',5,5), ('bookcase',10,5), ('map_board',23,5),
        ('shop_counter',19,19), ('lectern',23,19),
        ('rug_warm',13,20), ('runner',15,20),
        ('dining_table',6,21), ('bench',6,24), ('chair',10,22),
        ('crate_stack',24,24), ('bookcase',5,10), ('bookcase',24,10),
    ],
}


def theme(zone: dict, staff: list[dict]) -> str:
    role_set = {npc['role'] for npc in staff}
    name = zone['name'].casefold()
    if 'innkeeper' in role_set or 'inn' in name or 'lantern hearth' in name:
        return 'inn'
    if role_set & {'blacksmith','armorer','weaponsmith'} or 'forge' in name or 'smith' in name:
        return 'forge'
    if role_set & {'trainer','enchanter','alchemist','carpenter','woodworker'} or 'workshop' in name:
        return 'workshop'
    if role_set & {'provisioner','fletcher','tailor','tanner','jeweler','rune_merchant'} or 'market' in name or 'store' in name:
        return 'shop'
    return 'hall'


def place(zone: dict, entries: list[tuple]) -> None:
    result = []
    for index, (kind,x,y) in enumerate(entries):
        width,height,rise,solid,ground = FURNITURE[kind]
        if x < 3 or y < 3 or x+width > zone['width']-3 or y+height > zone['height']-3:
            raise ValueError(f'Furnishing is outside its room: {zone["id"]}/{kind}')
        result.append(dict(id=f'{zone["id"]}/furnishing/{index}',kind=kind,x=x,y=y,
                           width=width,height=height,rise=rise,solid=solid,ground=ground))
    occupied = set()
    for item in result:
        if not item['solid']: continue
        for y in range(item['y'],item['y']+item['height']):
            for x in range(item['x'],item['x']+item['width']):
                if (x,y) in occupied:
                    raise ValueError(f'Overlapping furniture in {zone["id"]} at {x},{y}')
                occupied.add((x,y))
    zone['furnishings'] = result


def build(data: dict) -> None:
    """Keep all service IDs, zone IDs and exits. Change only furniture and staff staging."""
    for zone in data['zones']:
        if zone['kind'] != 'interior': continue
        if zone['width'] != 32 or zone['height'] != 32:
            # Never project the 32-tile plan into an unreviewed smaller room.
            raise ValueError(f'An authored furnishing plan is required for {zone["id"]}')
        staff = [npc for npc in data['npcs'] if npc['zone']==zone['id']]
        room_theme = theme(zone,staff)
        place(zone,ROOMS[room_theme])
        # The original threshold and the central travel cross remain free.
        service_points = [(17.5,20.5),(13.5,20.5),(17.5,23.5),(13.5,23.5)]
        if len(staff)>len(service_points):
            raise ValueError(f'Explicit staff staging is required for {zone["id"]}')
        for npc,(x,y) in zip(staff,service_points): npc['position'] = dict(x=x,y=y)
    starter = next(zone for zone in data['zones'] if zone['id']=='wayfarers_rest')
    place(starter,[
        ('bench',25,35), ('barrel',31,36), ('flower_bed',33,35),
        ('anvil',44,36), ('woodpile',44,35),
        ('crate_stack',25,56), ('barrel',28,57), ('flower_bed',33,56),
        ('workbench',49,57), ('practice_ring',44,58),
        ('well',35,44), ('paving_mosaic',36,43), ('fence',23,36),
    ])
    # Service-specific construction is art metadata, not a new building or service.
    for building,style in zip(starter['buildings'],('inn','forge','shop','workshop')):
        building['style']=style
