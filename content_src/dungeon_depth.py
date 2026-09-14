\
"""Task 21: reusable compact encounter wings attached to existing boss dungeons."""

PLANS = {
    'broken_mill': ('Millrace Foreworks', 'Gearhouse Gauntlet'),
    'silken_tollhouse': ('Webbed Toll Cells', 'Silkroot Gallery'),
    'sunken_foundry': ('Flooded Smelter', 'Kiln Access'),
    'glasswing_grotto': ('Shard Descent', 'Prismatic Gallery'),
}
ROOM_IDS = frozenset(name for dungeon in PLANS for name in (dungeon + '_threshold', dungeon + '_gauntlet'))


def point(x, y):
    return {'x': float(x), 'y': float(y)}


def room(ident, name, dungeon, seed, lore):
    return dict(
        id=ident, name=name, biome=dungeon['biome'], level=dungeon['level'], kind='dungeon', layer=dungeon['layer'],
        width=64, height=64, seed=seed, spawn=point(32.5, 32.5), worldX=dungeon['worldX'], worldY=dungeon['worldY'],
        lore=lore, exits=[], buildings=[], species=[], boss='', resources=[])


def exit_row(ident, target, position, arrival, kind='door', requirement=1):
    return dict(id=ident, target=target, position=position, arrival=arrival, kind=kind, requirement=requirement)


def build(data):
    zones = data['zones']
    by_id = {z['id']: z for z in zones}
    mobs = {m['id']: m for m in data['mobs']}
    if ROOM_IDS & set(by_id):
        raise ValueError('Task 21 compact dungeon rooms must be installed once.')

    for index, (dungeon_id, (threshold_name, gauntlet_name)) in enumerate(PLANS.items()):
        dungeon = by_id.get(dungeon_id)
        if dungeon is None or dungeon['kind'] != 'dungeon' or not dungeon['boss']:
            raise ValueError('Task 21 requires canonical boss dungeon ' + dungeon_id)
        incoming = [(z, e) for z in zones for e in z['exits'] if e['target'] == dungeon_id]
        if len(incoming) != 1:
            raise ValueError(f'Task 21 selected dungeon {dungeon_id} must have exactly one pre-existing entrance, found {len(incoming)}.')
        source, source_exit = incoming[0]
        reverse = [e for e in dungeon['exits'] if e['target'] == source['id']]
        if len(reverse) != 1:
            raise ValueError('Task 21 requires one reciprocal entrance for ' + dungeon_id)
        dungeon_exit = reverse[0]
        boss = mobs[dungeon['boss']]
        ordinary = [mobs[x] for x in dungeon['species'] if x in mobs and not mobs[x]['boss'] and not mobs[x]['elite']]
        if len(ordinary) < 2:
            raise ValueError('Task 21 dungeon lacks ordinary encounter templates: ' + dungeon_id)
        local_elites = [m for m in data['mobs'] if m.get('elite') and m['biome'] == dungeon['biome']]
        elite_pool = local_elites or [m for m in data['mobs'] if m.get('elite')]
        elite = min(elite_pool, key=lambda m: (abs(m['level'] - boss['level']), m['id']))

        threshold_id = dungeon_id + '_threshold'
        gauntlet_id = dungeon_id + '_gauntlet'
        threshold = room(
            threshold_id, threshold_name, dungeon, 8800 + index * 41,
            'A compact approach chamber reuses the existing entrance and establishes the dungeon threat before the deeper fight.')
        gauntlet = room(
            gauntlet_id, gauntlet_name, dungeon, 8900 + index * 41,
            'A short elite gauntlet concentrates traversal pressure immediately before the established boss chamber.')
        threshold['species'] = [ordinary[0]['id'], ordinary[1]['id']]
        gauntlet['species'] = [ordinary[-1]['id'], elite['id']]
        threshold['buildings'] = [dict(id=threshold_id + '_ward', name='Broken Threshold Ward', x=28, y=27, width=8, height=5, style='ruin', station='')]
        gauntlet['buildings'] = [dict(id=gauntlet_id + '_marker', name='Bossward Marker', x=28, y=27, width=8, height=5, style='shrine', station='')]

        original_dungeon_arrival = dict(source_exit['arrival'])
        original_requirement = max(1, source_exit['requirement'])
        source_exit['target'] = threshold_id
        source_exit['arrival'] = point(32.5, 62.5)
        dungeon_exit['target'] = gauntlet_id
        dungeon_exit['arrival'] = point(32.5, 2.5)
        threshold['exits'] = [
            exit_row(threshold_id + '_to_' + source['id'], source['id'], point(32.5, 62.5), dict(source_exit['position']), source_exit['kind'], 1),
            exit_row(threshold_id + '_to_' + gauntlet_id, gauntlet_id, point(32.5, 2.5), point(32.5, 62.5), 'door', 1),
        ]
        gauntlet['exits'] = [
            exit_row(gauntlet_id + '_to_' + threshold_id, threshold_id, point(32.5, 62.5), point(32.5, 2.5), 'door', 1),
            exit_row(gauntlet_id + '_to_' + dungeon_id, dungeon_id, point(32.5, 2.5), original_dungeon_arrival, 'door', original_requirement),
        ]
        zones.extend([threshold, gauntlet])
        by_id[threshold_id] = threshold
        by_id[gauntlet_id] = gauntlet
