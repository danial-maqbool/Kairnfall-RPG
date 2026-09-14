"""Task 18: regional rare/champion identities layered onto existing elite templates."""

CHAMPIONS = {
    'rare_pine_wolf': ('Champion Duskfang', 'root', 'A scarred pack-leader that binds prey against the old forest boundary stones.'),
    'rare_kobold_slinger': ('Champion Cragshot', 'charge', 'A ridge captain who alternates sling pressure with sudden downhill charges.'),
    'rare_fire_beetle': ('Champion Cinderback', 'field', 'A furnace-scarred beetle that turns familiar ash paths into lingering fire zones.'),
    'rare_ice_elemental': ('Champion Pale Bell', 'ring', 'A glacier sentinel whose tolling shock ring punishes players who stack too tightly.'),
    'rare_gilded_scarab': ('Champion Gilded Warden', 'summon', 'A tomb sentinel that calls lesser ruin-dwellers when its burial road is challenged.'),
    'rare_arcane_sentinel': ('Champion Riftwarden', 'interruptible', 'A rift sentinel whose dangerous focused cast rewards timely interrupts.'),
}


def build(data):
    elites = [mob for mob in data['mobs'] if mob.get('elite')]
    if len(elites) != 25:
        raise ValueError(f'Task 18 expects the existing 25 elite templates, found {len(elites)}.')
    lookup = {mob['id']: mob for mob in elites}
    missing = sorted(set(CHAMPIONS) - set(lookup))
    if missing:
        raise ValueError('Task 18 champion templates are missing: ' + ', '.join(missing))

    for ident, (name, signature, identity) in CHAMPIONS.items():
        mob = lookup[ident]
        mob['name'] = name
        mob['health'] = round(mob['health'] * 1.35, 1)
        mob['power'] = round(mob['power'] * 1.12, 1)
        mob['gold'] = max(mob['gold'] + 6, round(mob['gold'] * 1.35))
        mob['xp'] = max(mob['xp'] + 20, round(mob['xp'] * 1.35))
        attacks = list(mob['attacks'])
        if signature not in attacks:
            attacks.append(signature)
        mob['attacks'] = attacks
        mob['anatomy'] += '; champion trophies and a landmark-readable silhouette distinguish this regional mini-boss'
        mob['lore'] = identity + ' It remains an optional regional challenge rather than required story progression.'

    signatures = {row[1] for row in CHAMPIONS.values()}
    known = {'strike','lunge','slam','brace','frenzy','ambush','projectile','circle','charge','cone','stomp','line','ring','interruptible','poison_field','summon','root','field','tempest'}
    if not signatures <= known:
        raise ValueError('Task 18 champion signature attack is not supported by the authoritative combat engine.')
    if len({lookup[ident]['biome'] for ident in CHAMPIONS}) != len(CHAMPIONS):
        raise ValueError('Task 18 champions must represent distinct regional biomes.')
