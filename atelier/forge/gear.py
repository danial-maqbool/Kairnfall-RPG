"""The equipment ladder: fourteen tiers of weapons, armour and trinkets.

Each tier is a level band with its own metal, its own cloth and leather, and —
the part that matters — its own *shape*. A Cobalt longsword is not a recoloured
iron one: the guard sweeps, the pommel is faceted, the blade is longer and the
fuller is cut differently. Every second tier changes the silhouette family
outright, and within a family the proportions, ornament count and glow keep
moving, so no two rungs of the ladder read the same.

`catalogue()` returns item records in the same shape the game catalogue uses, so
the pack can be consumed by the client as-is.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import pigment


@dataclass(frozen=True)
class Tier:
    index: int
    level: int
    key: str
    metal_name: str
    metal: str
    trim: str
    cloth_name: str
    cloth: str
    leather_name: str
    leather: str
    wood: str
    gem: str
    style: str
    glow: str = ''
    epithet: str = ''
    # shape modifiers, applied on top of the style family
    reach: float = 1.0        # blade / haft length
    breadth: float = 1.0      # blade width, plate thickness
    guard: float = 1.0        # cross guard span
    ornament: int = 0         # extra studs, rivets, gems, spikes
    plume: float = 0.0        # crest and pauldron flourish

    @property
    def band(self):
        return '%d' % self.level


TIERS = (
    Tier(0, 1, 'copper', 'Copper', '#b06a3c', '#8a6a45', 'Homespun', '#9a8f78',
         'Hide', '#8a6a4c', '#8d6942', '#a8623c', 'plain',
         reach=0.92, breadth=0.94, guard=0.90, ornament=0),
    Tier(1, 5, 'bronze', 'Bronze', '#a8853c', '#7d6a4a', 'Linen', '#c0b394',
         'Boiled Leather', '#7d5638', '#a98a5d', '#c08a3c', 'plain',
         reach=0.97, breadth=0.98, guard=0.96, ornament=1),
    Tier(2, 10, 'iron', 'Iron', '#7d858d', '#5f6166', 'Wool', '#a8a294',
         'Studded Leather', '#6a4c36', '#8d6942', '#8a939c', 'fluted',
         reach=1.0, breadth=1.04, guard=1.02, ornament=1),
    Tier(3, 15, 'steel', 'Steel', '#aab6c0', '#6f7a84', 'Silk', '#c2b8d6',
         'Scalemail', '#7a7f86', '#87604a', '#b6c2cc', 'fluted',
         reach=1.04, breadth=1.06, guard=1.08, ornament=2),
    Tier(4, 20, 'silver', 'Silver', '#cfd8dd', '#9aa2b0', 'Brocade', '#c8a86a',
         'Chainmail', '#9aa2ac', '#a3946a', '#d8dce4', 'winged',
         reach=1.06, breadth=1.02, guard=1.14, ornament=2, plume=0.5),
    Tier(5, 27, 'cobalt', 'Cobalt', '#5d84ad', '#42607f', 'Moonweave', '#8fa8cc',
         'Wyrmhide', '#4f6a7a', '#5f5b4e', '#7fb8d8', 'winged',
         reach=1.08, breadth=1.06, guard=1.18, ornament=3, plume=0.7),
    Tier(6, 35, 'mithril', 'Mithril', '#8fc4bd', '#5f948c', 'Mistweave', '#b8d8d2',
         'Mithril Weave', '#7faea6', '#a4a7bb', '#a8e0d4', 'cruciform',
         reach=1.10, breadth=1.02, guard=1.20, ornament=3, plume=0.6),
    Tier(7, 45, 'adamant', 'Adamantine', '#5f7a62', '#3f5445', 'Runeweave', '#8aa88c',
         'Adamant Scale', '#4f6a52', '#635d50', '#8ad4a0', 'cruciform',
         reach=1.12, breadth=1.10, guard=1.22, ornament=4, plume=0.8),
    Tier(8, 50, 'obsidian', 'Obsidian', '#5b5468', '#3a3644', 'Shadowsilk', '#6a6280',
         'Shadowhide', '#4a4452', '#504b55', '#a06ad0', 'serrated', glow='#8a6ad0',
         reach=1.14, breadth=1.12, guard=1.16, ornament=4, plume=0.9),
    Tier(9, 55, 'aetherium', 'Aetherium', '#a8b8e2', '#7a86b4', 'Aetherweave', '#b6c0e8',
         'Aetherscale', '#8a94c4', '#9aa0bb', '#c0c8ff', 'runed', glow='#9fb0ff',
         reach=1.15, breadth=1.06, guard=1.20, ornament=5, plume=1.0),
    Tier(10, 60, 'drakeforged', 'Drakeforged', '#b0703c', '#6f4a30', 'Drakeweave', '#c89a5c',
         'Drakescale', '#8a5230', '#8e5340', '#e08a3c', 'runed', glow='#e08a44',
         reach=1.17, breadth=1.14, guard=1.18, ornament=5, plume=1.1),
    Tier(11, 70, 'umbral', 'Umbral', '#4a4258', '#2e2a3a', 'Umbraweave', '#5f5670',
         'Umbral Hide', '#403a4c', '#463f48', '#7a52c0', 'crystalline', glow='#7a52c0',
         reach=1.19, breadth=1.10, guard=1.22, ornament=6, plume=1.2),
    Tier(12, 80, 'dawnforged', 'Dawnforged', '#e0c47a', '#b08a3c', 'Dawnweave', '#f0dca8',
         'Dawnscale', '#c8a45c', '#c9b98a', '#fff0b0', 'crystalline', glow='#ffd98a',
         reach=1.21, breadth=1.12, guard=1.26, ornament=6, plume=1.3),
    Tier(13, 90, 'starforged', 'Starforged', '#8fa0d8', '#4f5a90', 'Starweave', '#c0c8f0',
         'Starhide', '#6a74a8', '#9aa0bb', '#d8e0ff', 'ethereal', glow='#a8b8ff',
         reach=1.24, breadth=1.08, guard=1.28, ornament=7, plume=1.5),
)

BY_KEY = {tier.key: tier for tier in TIERS}
BY_LEVEL = {tier.level: tier for tier in TIERS}


# ------------------------------------------------------------------ names --

WEAPON_NAMES = {
    'sword': ('Shortsword', 'Falchion', 'Arming Sword', 'Longsword', 'Sabre', 'Estoc',
              'Rapier', 'Broadsword', 'Backsword', 'Bastard Sword', 'Warblade',
              'Kriegsmesser', 'Sunblade', 'Eclipse Blade'),
    'greatsword': ('Cleaver', 'Warsword', 'Claymore', 'Greatsword', 'Zweihander', 'Flamberge',
                   'Highblade', 'Executioner', 'Doomblade', 'Rune Greatsword', 'Drake Cleaver',
                   'Nightfall Edge', 'Dawnsplitter', 'Starrender'),
    'axe': ('Hatchet', 'Hand Axe', 'Battle Axe', 'War Axe', 'Bearded Axe', 'Crescent Axe',
            'Reaver', 'Sunder Axe', 'Ruin Axe', 'Rune Axe', 'Drake Axe', 'Nightreaver',
            'Dawnbreaker', 'Starfall Axe'),
    'greataxe': ('Splitter', 'Woodsman Maul', 'Great Axe', 'Broadaxe', 'Twinbite', 'Crescent Maul',
                 'Skullcleaver', 'Ruinbringer', 'Deathbite', 'Rune Broadaxe', 'Drake Maul',
                 'Nightsunder', 'Dawnhewer', 'Starcleaver'),
    'mace': ('Club', 'Cudgel', 'Mace', 'Flanged Mace', 'Morningstar', 'War Mace',
             'Skullbreaker', 'Crusher', 'Grave Mace', 'Rune Mace', 'Drake Mace',
             'Nightfall Star', 'Dawnhammer', 'Starcrusher'),
    'greatmace': ('Log Maul', 'Heavy Club', 'War Maul', 'Great Maul', 'Siege Hammer', 'Warhammer',
                  'Earthbreaker', 'Ruin Maul', 'Grave Maul', 'Rune Maul', 'Drake Warhammer',
                  'Nightbreaker', 'Dawnfall Maul', 'Starbreaker'),
    'spear': ('Pike Staff', 'Boar Spear', 'Spear', 'Warspear', 'Lance', 'Winged Spear',
              'Impaler', 'Skewer', 'Grave Lance', 'Rune Lance', 'Drake Spear',
              'Nightpiercer', 'Dawnlance', 'Starpiercer'),
    'halberd': ('Bill Hook', 'Guisarme', 'Halberd', 'Poleaxe', 'Glaive', 'Bardiche',
                'Voulge', 'Reaper Glaive', 'Grave Glaive', 'Rune Halberd', 'Drake Glaive',
                'Nightreaper', 'Dawnglaive', 'Starreaper'),
    'dagger': ('Shiv', 'Knife', 'Dirk', 'Dagger', 'Stiletto', 'Main Gauche',
               'Kris', 'Fang', 'Grave Fang', 'Rune Dagger', 'Drake Fang',
               'Nightfang', 'Dawnfang', 'Starfang'),
    'bow': ('Shortbow', 'Hunting Bow', 'Recurve Bow', 'Longbow', 'War Bow', 'Composite Bow',
            'Hornbow', 'Siege Bow', 'Grave Bow', 'Rune Longbow', 'Drakehorn Bow',
            'Nightsong Bow', 'Dawnstring', 'Starsinger'),
    'crossbow': ('Hand Crossbow', 'Light Crossbow', 'Crossbow', 'Heavy Crossbow', 'Arbalest',
                 'Repeater', 'Siege Arbalest', 'Ballista Arm', 'Grave Arbalest', 'Rune Arbalest',
                 'Drake Repeater', 'Nightbolt', 'Dawnbolt', 'Starbolt'),
    'staff': ('Walking Staff', 'Apprentice Staff', 'Oak Staff', 'Runed Staff', 'Adept Staff',
              'Conduit Staff', 'Archon Staff', 'Sage Staff', 'Grave Staff', 'Rune Sceptre',
              'Drakebone Staff', 'Nightspire', 'Dawnspire', 'Starspire'),
    'wand': ('Twig Wand', 'Apprentice Wand', 'Oak Wand', 'Runed Wand', 'Adept Wand',
             'Conduit Wand', 'Archon Wand', 'Sage Wand', 'Grave Wand', 'Rune Wand',
             'Drakebone Wand', 'Nightwand', 'Dawnwand', 'Starwand'),
    'knuckles': ('Wrapped Fists', 'Knuckles', 'Iron Knuckles', 'Battle Claws', 'Talons',
                 'War Claws', 'Ripper Claws', 'Render Claws', 'Grave Claws', 'Rune Claws',
                 'Drake Talons', 'Nightclaws', 'Dawnfists', 'Starclaws'),
}

OFFHAND_NAMES = {
    'shield': ('Buckler', 'Round Shield', 'Kite Shield', 'Heater Shield', 'Tower Shield',
               'Warshield', 'Aegis', 'Bulwark', 'Grave Aegis', 'Rune Aegis', 'Drake Bulwark',
               'Nightward', 'Dawnward', 'Starward'),
    'tome': ('Notebook', 'Primer', 'Codex', 'Grimoire', 'Tome of Insight', 'Arcane Codex',
             'Archon Grimoire', 'Sage Tome', 'Grave Codex', 'Rune Grimoire', 'Drake Codex',
             'Nightbook', 'Dawn Codex', 'Star Codex'),
    'focus': ('Charm Loop', 'Focus Ring', 'Channel Ring', 'Runed Focus', 'Adept Focus',
              'Conduit Ring', 'Archon Focus', 'Sage Focus', 'Grave Focus', 'Rune Focus',
              'Drake Focus', 'Night Focus', 'Dawn Focus', 'Star Focus'),
    'orb': ('Glass Orb', 'Clay Orb', 'Polished Orb', 'Runed Orb', 'Adept Orb', 'Conduit Orb',
            'Archon Orb', 'Sage Orb', 'Grave Orb', 'Rune Orb', 'Drake Orb',
            'Nightsphere', 'Dawnsphere', 'Starsphere'),
    'quiver': ('Bark Quiver', 'Hide Quiver', 'Hunting Quiver', 'War Quiver', 'Ranger Quiver',
               'Skirmisher Quiver', 'Marksman Quiver', 'Sharpshot Quiver', 'Grave Quiver',
               'Rune Quiver', 'Drake Quiver', 'Night Quiver', 'Dawn Quiver', 'Star Quiver'),
}

ARMOUR_NAMES = {
    'heavy': {
        'helmet': ('Cap', 'Kettle Helm', 'Helm', 'Barbute', 'Great Helm', 'Visored Helm',
                   'Winged Helm', 'Crowned Helm', 'Grave Helm', 'Rune Helm', 'Drake Helm',
                   'Nighthelm', 'Dawnhelm', 'Starhelm'),
        'chest': ('Chest Plate', 'Cuirass', 'Breastplate', 'Plate Cuirass', 'Field Plate',
                  'War Plate', 'Winged Cuirass', 'Crowned Plate', 'Grave Plate', 'Rune Plate',
                  'Drake Plate', 'Night Plate', 'Dawn Plate', 'Star Plate'),
        'gloves': ('Plated Mitts', 'Gauntlets', 'War Gauntlets', 'Battle Gauntlets', 'Field Gauntlets',
                   'Vambraces', 'Winged Gauntlets', 'Crowned Gauntlets', 'Grave Gauntlets',
                   'Rune Gauntlets', 'Drake Gauntlets', 'Night Gauntlets', 'Dawn Gauntlets',
                   'Star Gauntlets'),
        'legs': ('Plated Legs', 'Cuisses', 'Greaves', 'Plate Greaves', 'Field Greaves',
                 'War Greaves', 'Winged Greaves', 'Crowned Greaves', 'Grave Greaves',
                 'Rune Greaves', 'Drake Greaves', 'Night Greaves', 'Dawn Greaves', 'Star Greaves'),
        'boots': ('Plated Boots', 'Sabatons', 'War Sabatons', 'Battle Sabatons', 'Field Sabatons',
                  'Warshod Sabatons', 'Winged Sabatons', 'Crowned Sabatons', 'Grave Sabatons',
                  'Rune Sabatons', 'Drake Sabatons', 'Night Sabatons', 'Dawn Sabatons',
                  'Star Sabatons'),
        'belt': ('Plated Belt', 'War Belt', 'Battle Girdle', 'Plate Girdle', 'Field Girdle',
                 'Warlord Belt', 'Winged Girdle', 'Crowned Girdle', 'Grave Girdle', 'Rune Girdle',
                 'Drake Girdle', 'Night Girdle', 'Dawn Girdle', 'Star Girdle'),
        'cloak': ('Heavy Mantle', 'War Mantle', 'Battle Mantle', 'Plated Mantle', 'Field Mantle',
                  'Warlord Mantle', 'Winged Mantle', 'Crowned Mantle', 'Grave Mantle',
                  'Rune Mantle', 'Drake Mantle', 'Night Mantle', 'Dawn Mantle', 'Star Mantle'),
    },
    'medium': {
        'helmet': ('Hood', 'Coif', 'Scaled Coif', 'Hunter Helm', 'Ranger Helm', 'Skirmish Helm',
                   'Stalker Helm', 'Warden Helm', 'Grave Coif', 'Rune Coif', 'Drake Coif',
                   'Night Coif', 'Dawn Coif', 'Star Coif'),
        'chest': ('Jerkin', 'Brigandine', 'Hauberk', 'Scaled Hauberk', 'Ranger Hauberk',
                  'Skirmish Hauberk', 'Stalker Hauberk', 'Warden Hauberk', 'Grave Hauberk',
                  'Rune Hauberk', 'Drake Hauberk', 'Night Hauberk', 'Dawn Hauberk',
                  'Star Hauberk'),
        'gloves': ('Wraps', 'Bracers', 'Scaled Bracers', 'Hunter Bracers', 'Ranger Bracers',
                   'Skirmish Bracers', 'Stalker Bracers', 'Warden Bracers', 'Grave Bracers',
                   'Rune Bracers', 'Drake Bracers', 'Night Bracers', 'Dawn Bracers',
                   'Star Bracers'),
        'legs': ('Leggings', 'Chausses', 'Scaled Chausses', 'Hunter Chausses', 'Ranger Chausses',
                 'Skirmish Chausses', 'Stalker Chausses', 'Warden Chausses', 'Grave Chausses',
                 'Rune Chausses', 'Drake Chausses', 'Night Chausses', 'Dawn Chausses',
                 'Star Chausses'),
        'boots': ('Shoes', 'Travel Boots', 'Scaled Boots', 'Hunter Boots', 'Ranger Boots',
                  'Skirmish Boots', 'Stalker Boots', 'Warden Boots', 'Grave Boots', 'Rune Boots',
                  'Drake Boots', 'Night Boots', 'Dawn Boots', 'Star Boots'),
        'belt': ('Cord Belt', 'Buckled Belt', 'Scaled Belt', 'Hunter Belt', 'Ranger Belt',
                 'Skirmish Belt', 'Stalker Belt', 'Warden Belt', 'Grave Belt', 'Rune Belt',
                 'Drake Belt', 'Night Belt', 'Dawn Belt', 'Star Belt'),
        'cloak': ('Travel Cape', 'Rider Cape', 'Scaled Cape', 'Hunter Cape', 'Ranger Cape',
                  'Skirmish Cape', 'Stalker Cape', 'Warden Cape', 'Grave Cape', 'Rune Cape',
                  'Drake Cape', 'Night Cape', 'Dawn Cape', 'Star Cape'),
    },
    'light': {
        'helmet': ('Cowl', 'Hood', 'Circlet', 'Woven Hood', 'Adept Hood', 'Conduit Circlet',
                   'Archon Circlet', 'Sage Circlet', 'Grave Cowl', 'Rune Circlet', 'Drake Cowl',
                   'Night Circlet', 'Dawn Circlet', 'Star Circlet'),
        'chest': ('Shirt', 'Tunic', 'Robe', 'Woven Robe', 'Adept Robe', 'Conduit Robe',
                  'Archon Robe', 'Sage Robe', 'Grave Robe', 'Rune Robe', 'Drake Robe',
                  'Night Robe', 'Dawn Robe', 'Star Robe'),
        'gloves': ('Mitts', 'Gloves', 'Woven Gloves', 'Adept Gloves', 'Conduit Gloves',
                   'Archon Gloves', 'Sage Gloves', 'Seer Gloves', 'Grave Gloves', 'Rune Gloves',
                   'Drake Gloves', 'Night Gloves', 'Dawn Gloves', 'Star Gloves'),
        'legs': ('Trousers', 'Leggings', 'Woven Leggings', 'Adept Leggings', 'Conduit Leggings',
                 'Archon Leggings', 'Sage Leggings', 'Seer Leggings', 'Grave Leggings',
                 'Rune Leggings', 'Drake Leggings', 'Night Leggings', 'Dawn Leggings',
                 'Star Leggings'),
        'boots': ('Sandals', 'Slippers', 'Woven Slippers', 'Adept Slippers', 'Conduit Slippers',
                  'Archon Slippers', 'Sage Slippers', 'Seer Slippers', 'Grave Slippers',
                  'Rune Slippers', 'Drake Slippers', 'Night Slippers', 'Dawn Slippers',
                  'Star Slippers'),
        'belt': ('Rope Sash', 'Sash', 'Woven Sash', 'Adept Sash', 'Conduit Sash', 'Archon Sash',
                 'Sage Sash', 'Seer Sash', 'Grave Sash', 'Rune Sash', 'Drake Sash',
                 'Night Sash', 'Dawn Sash', 'Star Sash'),
        'cloak': ('Wrap', 'Cloak', 'Woven Cloak', 'Adept Cloak', 'Conduit Cloak', 'Archon Cloak',
                  'Sage Cloak', 'Seer Cloak', 'Grave Cloak', 'Rune Cloak', 'Drake Cloak',
                  'Night Cloak', 'Dawn Cloak', 'Star Cloak'),
    },
}

ACCESSORY_NAMES = {
    'ring': ('Band', 'Ring', 'Signet', 'Seal Ring', 'Ward Ring', 'Sigil Ring', 'Archon Ring',
             'Sage Ring', 'Grave Ring', 'Rune Ring', 'Drake Ring', 'Night Ring', 'Dawn Ring',
             'Star Ring'),
    'necklace': ('Cord', 'Pendant', 'Amulet', 'Torc', 'Ward Amulet', 'Sigil Amulet',
                 'Archon Amulet', 'Sage Amulet', 'Grave Amulet', 'Rune Amulet', 'Drake Amulet',
                 'Night Amulet', 'Dawn Amulet', 'Star Amulet'),
    'charm': ('Token', 'Charm', 'Talisman', 'Ward Charm', 'Sigil Charm', 'Archon Charm',
              'Sage Charm', 'Seer Charm', 'Grave Charm', 'Rune Charm', 'Drake Charm',
              'Night Charm', 'Dawn Charm', 'Star Charm'),
    'trinket': ('Trinket', 'Keepsake', 'Relic', 'Ward Relic', 'Sigil Relic', 'Archon Relic',
                'Sage Relic', 'Seer Relic', 'Grave Relic', 'Rune Relic', 'Drake Relic',
                'Night Relic', 'Dawn Relic', 'Star Relic'),
}

WEAPONS = tuple(WEAPON_NAMES)
OFFHANDS = tuple(OFFHAND_NAMES)
ARMOUR_SLOTS = ('helmet', 'chest', 'gloves', 'legs', 'boots', 'belt', 'cloak')
WEIGHTS = ('light', 'medium', 'heavy')
ACCESSORIES = tuple(ACCESSORY_NAMES)

TWO_HANDED = {'greatsword', 'greataxe', 'greatmace', 'spear', 'halberd', 'bow', 'crossbow', 'staff'}
WEAPON_SKILL = {
    'sword': 'swordsmanship', 'greatsword': 'swordsmanship', 'axe': 'axe_mastery',
    'greataxe': 'axe_mastery', 'mace': 'mace_mastery', 'greatmace': 'mace_mastery',
    'spear': 'spear_mastery', 'halberd': 'spear_mastery', 'dagger': 'dagger_mastery',
    'bow': 'archery', 'crossbow': 'crossbow_mastery', 'staff': 'staff_mastery',
    'wand': 'wand_mastery', 'knuckles': 'unarmed_combat',
}
WEAPON_ELEMENT = {
    'staff': 'Arcane', 'wand': 'Arcane', 'dagger': 'Shadow', 'bow': 'Nature',
}
ARMOUR_SKILL = {'light': 'light_armor', 'medium': 'medium_armor', 'heavy': 'heavy_armor'}


# ----------------------------------------------------------------- styles --

# Silhouette families. Each switches real geometry, not just colour.
STYLE_FAMILIES = {
    'plain':       dict(guard='bar', pommel='round', edge='straight', haft='wrapped',
                        crest='none', pauldron='round', skirt='none', rune=0.0),
    'fluted':      dict(guard='tipped', pommel='disc', edge='fullered', haft='banded',
                        crest='ridge', pauldron='ridged', skirt='short', rune=0.0),
    'winged':      dict(guard='wings', pommel='faceted', edge='fullered', haft='banded',
                        crest='fin', pauldron='winged', skirt='short', rune=0.0),
    'cruciform':   dict(guard='cross', pommel='ring', edge='doubled', haft='langets',
                        crest='comb', pauldron='layered', skirt='long', rune=0.15),
    'serrated':    dict(guard='hooked', pommel='spike', edge='toothed', haft='langets',
                        crest='horns', pauldron='spiked', skirt='long', rune=0.25),
    'runed':       dict(guard='cross', pommel='gem', edge='runed', haft='banded',
                        crest='halo', pauldron='layered', skirt='long', rune=1.0),
    'crystalline': dict(guard='shards', pommel='gem', edge='crystal', haft='crystal',
                        crest='shards', pauldron='crystal', skirt='long', rune=0.8),
    'ethereal':    dict(guard='shards', pommel='gem', edge='ethereal', haft='crystal',
                        crest='halo', pauldron='crystal', skirt='long', rune=1.0),
}


def tier_of(item):
    """The ladder rung for an item, whether it came from this pack or the game."""
    key = item.get('material', '')
    tier = BY_KEY.get(key)
    if tier is not None:
        return tier
    index = int(item.get('tier', 1)) - 1
    return TIERS[max(0, min(len(TIERS) - 1, index))]


def style_of(item):
    """Shape switches for one item: family traits plus this tier's proportions."""
    tier = tier_of(item)
    style = dict(STYLE_FAMILIES[tier.style])
    style.update(reach=tier.reach, breadth=tier.breadth, guard_span=tier.guard,
                 ornament=tier.ornament, plume=tier.plume, gem=tier.gem,
                 glow=tier.glow, tier=tier.index, family=tier.style)
    return style


# ------------------------------------------------------------- catalogue ---

MATERIAL_STEMS = ('forged', 'weave', 'scale', 'hide', 'silk', 'mail', 'steel')


def compose(material, type_name):
    """Join a material to a piece name without stuttering.

    'Drakescale' + 'Drake Boots' is 'Drakescale Boots'; 'Starforged' +
    'Starbreaker' is just 'Starbreaker'.
    """
    stem = material.lower()
    for suffix in MATERIAL_STEMS:
        if stem.endswith(suffix) and len(stem) > len(suffix) + 2:
            stem = stem[:-len(suffix)]
            break
    if stem and stem in type_name.lower():
        kept = [word for word in type_name.split() if stem not in word.lower()]
        return '%s %s' % (material, ' '.join(kept)) if kept else type_name
    return '%s %s' % (material, type_name)


def _stat(base, tier, growth=1.34):
    return round(base * (growth ** tier.index), 1)


def _describe(name, tier, kind):
    if kind == 'weapon':
        return '%s forged at the %s standard. Rated for level %d.' % (name, tier.metal_name, tier.level)
    if kind == 'armour':
        return '%s made to the %s pattern. Rated for level %d.' % (name, tier.metal_name, tier.level)
    return '%s set with %s stone. Rated for level %d.' % (name, tier.metal_name, tier.level)


def _record(ident, name, kind, slot, tags, material, tier, element='Physical', **extra):
    record = {
        'id': ident, 'name': name, 'type': kind, 'slot': slot, 'tags': list(tags),
        'material': material, 'tier': tier.index + 1, 'level': tier.level,
        'requirement': tier.level, 'element': element,
        'icon': 'gear/' + ident + '.png', 'stackMax': 1, 'stats': {},
        'effect': '', 'skill': '', 'power': 0, 'armor': 0, 'range': 1.5, 'speed': 1.0,
        'value': int(12 * (1.55 ** tier.index)), 'description': '',
    }
    record.update(extra)
    return record


def catalogue():
    """Every piece of gear in the ladder, as catalogue style records."""
    items = []
    for tier in TIERS:
        index = tier.index
        for weapon in WEAPONS:
            name = compose(tier.metal_name, WEAPON_NAMES[weapon][index])
            ident = '%s_%s' % (tier.key, weapon)
            two = weapon in TWO_HANDED
            tags = [weapon, 'two_handed' if two else 'one_handed']
            tags.append('heavy' if weapon in ('greatsword', 'greataxe', 'greatmace', 'halberd')
                        else 'light' if weapon in ('dagger', 'wand', 'knuckles') else 'medium')
            speed = {'dagger': 1.55, 'knuckles': 1.45, 'sword': 1.15, 'axe': 1.05, 'mace': 1.0,
                     'wand': 1.2, 'bow': 1.1, 'crossbow': 0.85, 'spear': 1.0, 'staff': 0.95,
                     'greatsword': 0.75, 'greataxe': 0.7, 'greatmace': 0.65, 'halberd': 0.8}[weapon]
            reach = {'spear': 2.8, 'halberd': 2.9, 'bow': 8.0, 'crossbow': 7.5, 'staff': 4.5,
                     'wand': 5.0, 'dagger': 1.4, 'knuckles': 1.3}.get(weapon, 1.9)
            items.append(_record(
                ident, name, 'weapon', 'weapon', tags, tier.key, tier,
                WEAPON_ELEMENT.get(weapon, 'Physical'),
                power=_stat(9.0 * (1.7 if two else 1.0), tier), speed=speed, range=reach,
                skill=WEAPON_SKILL[weapon],
                description=_describe(name, tier, 'weapon')))
        for offhand in OFFHANDS:
            name = compose(tier.metal_name, OFFHAND_NAMES[offhand][index])
            ident = '%s_%s' % (tier.key, offhand)
            weight = 'heavy' if offhand == 'shield' else 'light'
            items.append(_record(
                ident, name, 'offhand', 'offhand', [offhand, weight], tier.key, tier,
                'Arcane' if offhand in ('tome', 'focus', 'orb') else 'Physical',
                armor=_stat(4.0 if offhand == 'shield' else 1.0, tier),
                power=_stat(2.0, tier), skill='shield_mastery' if offhand == 'shield' else '',
                description=_describe(name, tier, 'armour')))
        for weight in WEIGHTS:
            material = {'light': tier.cloth_name, 'medium': tier.leather_name,
                        'heavy': tier.metal_name}[weight]
            material_key = {'light': tier.key + '_cloth', 'medium': tier.key + '_leather',
                            'heavy': tier.key}[weight]
            for slot in ARMOUR_SLOTS:
                name = compose(material, ARMOUR_NAMES[weight][slot][index])
                ident = '%s_%s_%s' % (tier.key, weight, slot)
                bulk = {'helmet': 0.9, 'chest': 1.6, 'gloves': 0.7, 'legs': 1.3,
                        'boots': 0.8, 'belt': 0.6, 'cloak': 0.6}[slot]
                weight_scale = {'light': 0.65, 'medium': 1.0, 'heavy': 1.45}[weight]
                items.append(_record(
                    ident, name, 'armor', slot, [slot, weight], material_key, tier,
                    armor=_stat(3.4 * bulk * weight_scale, tier),
                    skill=ARMOUR_SKILL[weight],
                    description=_describe(name, tier, 'armour')))
        for accessory in ACCESSORIES:
            name = compose(tier.metal_name, ACCESSORY_NAMES[accessory][index])
            ident = '%s_%s' % (tier.key, accessory)
            items.append(_record(
                ident, name, 'accessory', accessory, [accessory], tier.key, tier,
                'Arcane' if accessory in ('charm', 'trinket') else 'Radiant',
                power=_stat(2.4, tier), armor=_stat(1.1, tier),
                description=_describe(name, tier, 'accessory')))
    return items


def body_colour(item):
    """The colour of an item's own material, whichever ladder it sits on."""
    tier = tier_of(item)
    material = item.get('material', tier.key)
    known = pigment.MATERIALS.get(material)
    if known is not None:
        return known
    if material.endswith('_cloth'):
        return tier.cloth
    if material.endswith('_leather'):
        return tier.leather
    if material in BY_KEY:
        return BY_KEY[material].metal
    weight = 'heavy'
    tags = item.get('tags', ())
    if 'light' in tags:
        weight = 'light'
    elif 'medium' in tags:
        weight = 'medium'
    return {'light': tier.cloth, 'medium': tier.leather, 'heavy': tier.metal}[weight]


def palette(item):
    """Ramps for one gear item, honouring the cloth and leather ladders."""
    tier = tier_of(item)
    body = body_colour(item)
    return {
        'metal': pigment.ramp(body), 'trim': pigment.ramp(tier.trim),
        'wood': pigment.ramp(tier.wood), 'grip': pigment.ramp(tier.leather),
        'gem': pigment.ramp(tier.gem), 'string': pigment.ramp('#cdc3a6'),
        'cloth': pigment.ramp(tier.cloth), 'leather': pigment.ramp(tier.leather),
        'book': pigment.ramp(tier.leather), 'paper': pigment.ramp('#e0d6b4'),
    }


def summary():
    lines = []
    for tier in TIERS:
        lines.append('%2d  lvl %-3d %-12s %-12s %-16s %s'
                     % (tier.index + 1, tier.level, tier.metal_name, tier.cloth_name,
                        tier.leather_name, tier.style))
    return '\n'.join(lines)
