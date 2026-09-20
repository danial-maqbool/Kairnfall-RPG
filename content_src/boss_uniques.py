"""Boss-only signature relics: five milestone weapons for each playable class."""
from copy import deepcopy

MILESTONES = [
    (25, 'steel', 'kilnheart'),
    (45, 'silver', 'glasswing'),
    (65, 'cobalt', 'cinder_marshal'),
    (85, 'obsidian', 'the_unwritten'),
    (100, 'aetherium', 'aether_heart'),
]

SIGNATURES = {
    'vanguard': ('sword', 'Radiant', ['Oathsteel','Gatewarden','Bastion Edge','Crownward','Last Citadel'], {'vitality':2,'resolve':2}),
    'berserker': ('greataxe', 'Fire', ['Red Wake','Skullstorm','Ashhowl','Ruin Feast','Worldsplitter'], {'strength':3,'crit':1}),
    'ranger': ('bow', 'Lightning', ['Gale Thorn','Skytrace','Tempest String','Starhunter','Horizon Piercer'], {'dexterity':3,'accuracy':2}),
    'rogue': ('dagger', 'Poison', ['Whisperfang','Nightglass','Venom Psalm','Eclipse Needle','Kingless Mercy'], {'dexterity':3,'crit':2}),
    'arcanist': ('staff', 'Arcane', ['Prism Reed','Astral Measure','Null Canticle','Eventide Spire','Aether Equation'], {'intellect':3,'spell':3}),
    'warden': ('staff', 'Nature', ['Rootsong','Hartwood','Briar Covenant','Verdant Moon','First Grove'], {'spirit':3,'healing':3}),
    'templar': ('mace', 'Radiant', ['Dawn Bell','Mercy Weight','Sunward Vow','Saintfire','Last Benediction'], {'spirit':3,'armor':3}),
    'spellblade': ('sword', 'Shadow', ['Riftbrand','Hexsteel','Mirror Edge','Void Accord','Kairnfall Edge'], {'intellect':2,'spell':3}),
}


def _slug(text):
    return ''.join(c.lower() if c.isalnum() else '_' for c in text).strip('_').replace('__','_')


def build(data):
    items = {item['id']: item for item in data['items']}
    bosses = {mob['id']: mob for mob in data['mobs'] if mob.get('boss')}
    classes = {entry['id'] for entry in data['classes']}
    if classes != set(SIGNATURES):
        raise ValueError('Boss unique signatures must cover every playable class exactly once.')
    for class_id, (family, element, names, bonus_stats) in SIGNATURES.items():
        if len(names) != len(MILESTONES):
            raise ValueError(class_id + ': expected one unique name per milestone')
        for index, ((level, material, boss_id), name) in enumerate(zip(MILESTONES, names)):
            base_id = material + '_' + family
            base = deepcopy(items[base_id])
            ident = 'boss_' + class_id + '_' + str(level) + '_' + _slug(name)
            base['id'] = ident
            base['name'] = name
            base['requirement'] = level
            base['icon'] = 'items/' + ident + '.png'
            base['element'] = element
            base['power'] = round(base.get('power', 0) * 1.22 + level * 0.04, 1)
            base['value'] = int(base.get('value', 1) * 3 + level * 12)
            stats = dict(base.get('stats', {}))
            scale = 1 + index // 2
            for key, value in bonus_stats.items():
                stats[key] = round(stats.get(key, 0) + value * scale, 1)
            base['stats'] = stats
            tags = list(dict.fromkeys(list(base.get('tags', [])) + [
                'boss_unique', 'class:' + class_id, 'unique_level:' + str(level), 'base:' + base_id]))
            base['tags'] = tags
            base['description'] = (name + ' is a boss-forged signature relic. It is stronger than ordinary ' +
                                   family.replace('_',' ') + ' equipment near skill level ' + str(level) +
                                   ' and can enter the world only through its assigned boss loot table.')
            data['items'].append(base)
            items[ident] = base
            bosses[boss_id]['drops'].append(ident)
