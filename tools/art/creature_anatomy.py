"""Retained catalogue species proportions and coloration; contains no image renderer."""
import math, random
from dataclasses import dataclass, replace
from atelier.forge import pigment
from atelier.forge.pigment import blend

@dataclass
class Beast:
    archetype: str = 'quadruped'
    length: float = 20.0        # nose to tail base, creature units
    height: float = 13.0        # shoulder height
    girth: float = 6.0          # body half depth
    leg: float = 11.0           # ground to shoulder
    leg_width: float = 2.6
    neck: float = 5.0
    neck_width: float = 4.0
    head: float = 4.6           # skull radius
    muzzle: float = 4.0
    muzzle_drop: float = 0.6
    jaw: float = 2.0
    ear: str = 'pointed'
    ear_size: float = 2.6
    tail: str = 'brush'
    tail_length: float = 9.0
    horn: str = ''
    back: str = ''              # 'hump', 'ridge', 'shell', 'plates', 'spikes'
    coat: str = '#8a7a63'
    belly: str = ''
    accent: str = ''
    eye: str = '#e6d089'
    legs: int = 4
    wings: str = ''
    digit: str = 'paw'
    mane: float = 0.0
    plates: float = 0.0
    glow: str = ''
    spots: str = ''
    shell: float = 0.0
    segments: int = 0
    scale: float = 1.0
    # per-creature variation, filled in by describe()
    pattern: str = ''
    pattern_colour: str = ''
    family_key: str = ''
    seed: int = 0
    scarred: float = 0.0
    crown: str = ''

    def ramps(self):
        coat = ramp(self.coat)
        return {
            'coat': coat,
            # limbs on the far side of the body are the coat in shadow, never a
            # different colour, or an elemental accent turns a horse's legs purple
            'far': ramp(blend(pigment.rgb(self.coat), (38, 34, 44, 255), 0.30)),
            'belly': ramp(self.belly) if self.belly else ramp(blend(pigment.rgb(self.coat), (238, 228, 205, 255), 0.34)),
            'accent': ramp(self.accent) if self.accent else ramp(blend(pigment.rgb(self.coat), (34, 28, 36, 255), 0.42)),
            'horn': ramp('#cfc4a4'),
            'claw': ramp('#3c3540'),
        }

Q = 'quadruped'

FAMILIES = {
    # canines and felines
    'wolf': Beast(length=23, height=14, leg=12, muzzle=5.2, ear='pointed', tail='brush', coat='#79736e', mane=1.2),
    'hound': Beast(length=21, height=12.5, leg=11, muzzle=5.0, ear='drop', tail='whip', coat='#8a6a4c'),
    'jackal': Beast(length=20, height=12, leg=11.5, muzzle=5.4, ear='tall', tail='brush', coat='#a08154'),
    'fox': Beast(length=19, height=11, leg=9.5, muzzle=4.8, ear='tall', tail='brush', tail_length=11, coat='#b96a35', belly='#e0d6c4'),
    'arctic_fox': Beast(length=18, height=10.5, leg=9, muzzle=4.4, ear='tall', tail='brush', tail_length=11, coat='#dce2e6', belly='#f2f4f4'),
    'leopard': Beast(length=24, height=13, leg=12, muzzle=4.2, ear='round', tail='whip', tail_length=13, coat='#c69a52', spots='#4a3a2a'),
    'weasel': Beast(length=17, height=7.5, leg=5.6, muzzle=3.6, ear='round', tail='whip', coat='#a2764a', belly='#e2d5b8'),
    'wolverine': Beast(length=19, height=10, girth=6.6, leg=8.5, muzzle=4.2, ear='round', tail='brush', tail_length=7, coat='#5f4a3c', accent='#c8b58a'),
    # bears and heavy beasts
    'bear': Beast(length=21.5, height=16.5, girth=8.4, leg=12, leg_width=3.6, muzzle=4.4, ear='round', tail='stub', coat='#6f4f36', back='hump'),
    'polar_bear': Beast(length=22.5, height=17, girth=8.6, leg=12.5, leg_width=3.8, muzzle=4.8, ear='round', tail='stub', coat='#e2e6e6', back='hump'),
    'owlbear': Beast(length=22, height=16.5, girth=8.4, leg=12, leg_width=3.6, muzzle=3.0, ear='tuft', tail='stub', coat='#7a6247', accent='#c4b48c', back='hump', horn='beak'),
    'badger': Beast(length=18, height=9, girth=6.4, leg=6.4, muzzle=3.8, ear='round', tail='stub', coat='#5c564f', accent='#e0dbcd'),
    'armadillo': Beast(length=17, height=8.5, girth=6.0, leg=5.6, muzzle=4.2, ear='round', tail='whip', coat='#9c8a6c', back='shell', shell=1.0),
    # hoofed
    'deer': Beast(length=21, height=16, girth=5.4, leg=15, leg_width=2.0, neck=7.0, muzzle=4.4, ear='tall', tail='stub', coat='#a4784c', belly='#e2d2b4', horn='antler', digit='hoof'),
    'stag': Beast(length=24, height=18, girth=6.0, leg=16.5, leg_width=2.2, neck=8.0, muzzle=4.6, ear='tall', tail='stub', coat='#8a6238', horn='antler', digit='hoof'),
    'goat': Beast(length=18, height=13, girth=5.2, leg=11.5, leg_width=2.0, neck=5.0, muzzle=4.0, ear='drop', tail='stub', coat='#b8ab92', horn='curl', digit='hoof'),
    'ibex': Beast(length=20, height=14.5, girth=5.8, leg=12.5, leg_width=2.2, neck=5.6, muzzle=4.2, ear='drop', tail='stub', coat='#9c8a6a', horn='ridge_horn', digit='hoof'),
    'horse': Beast(length=27, height=19, girth=6.8, leg=17, leg_width=2.6, neck=8.6, muzzle=6.0, ear='tall', tail='tassel', tail_length=12, coat='#7d5a3c', mane=1.4, digit='hoof'),
    'ox': Beast(length=23, height=17.5, girth=8.8, leg=13.5, leg_width=3.4, neck=5.4, muzzle=5.4, ear='drop', tail='tassel', coat='#6b5a4a', horn='bull', digit='hoof', back='hump'),
    'boar': Beast(length=21, height=12.5, girth=7.6, leg=9.5, leg_width=2.8, neck=3.4, muzzle=5.6, ear='pointed', tail='curl', coat='#5f5147', horn='tusk', digit='hoof', back='ridge', mane=1.0),
    # small mammals
    'rat': Beast(length=14, height=6.5, girth=4.0, leg=4.4, leg_width=1.8, neck=2.0, head=3.6, muzzle=3.6, ear='round', ear_size=2.8, tail='rope', tail_length=11, coat='#7d6d5c', belly='#c9b89c'),
    'mouse': Beast(length=11, height=5.2, girth=3.2, leg=3.4, leg_width=1.5, neck=1.6, head=3.0, muzzle=2.8, ear='round', ear_size=2.9, tail='rope', tail_length=9, coat='#8d8177', belly='#d8cdba'),
    'hare': Beast(length=15, height=8.5, girth=4.4, leg=6.5, leg_width=1.8, neck=2.2, head=3.4, muzzle=2.8, ear='rabbit', ear_size=5.4, tail='puff', tail_length=3, coat='#a8977c', belly='#e2dac6'),
    'monkey': Beast(archetype='primate', length=14, height=13, girth=4.4, leg=7.0, head=3.8, muzzle=2.6, ear='round', tail='rope', tail_length=14, coat='#7a5c40', accent='#d9bb92'),
    # reptiles and amphibians
    'lizard': Beast(length=18, height=6.0, girth=4.2, leg=4.2, leg_width=1.8, neck=2.4, head=3.4, muzzle=4.0, ear='none', tail='taper', tail_length=13, coat='#6f8f52', back='ridge'),
    'salamander': Beast(length=19, height=6.2, girth=4.6, leg=4.4, leg_width=2.0, neck=2.4, head=3.6, muzzle=4.2, ear='none', tail='taper', tail_length=13, coat='#b0503a', accent='#e8b452', back='ridge', glow='#e07a44'),
    'crocodile': Beast(length=27, height=6.6, girth=5.8, leg=4.6, leg_width=2.4, neck=2.0, head=3.6, muzzle=8.4, jaw=2.8, ear='none', tail='taper', tail_length=16, coat='#5f6b48', back='plates'),
    'tortoise': Beast(length=17, height=9.0, girth=7.6, leg=4.4, leg_width=2.6, neck=4.0, head=3.2, muzzle=3.0, ear='none', tail='stub', coat='#7b6a4c', back='shell', shell=1.4),
    'turtle': Beast(length=17, height=8.4, girth=7.4, leg=4.0, leg_width=2.6, neck=4.2, head=3.2, muzzle=3.0, ear='none', tail='stub', coat='#5c7a68', back='shell', shell=1.4),
    'toad': Beast(archetype='amphibian', length=14, height=8, girth=6.2, leg=5.0, head=4.2, muzzle=3.4, coat='#7c8a4e', belly='#cdc79a'),
    'frog': Beast(archetype='amphibian', length=12, height=7, girth=5.4, leg=4.6, head=3.8, muzzle=3.0, coat='#5f9a56', belly='#d4d79a'),
    'mudskipper': Beast(archetype='amphibian', length=13, height=5.5, girth=4.6, leg=3.6, head=3.6, muzzle=3.4, coat='#7d7350', belly='#c4bb92'),
    # serpents and worms
    'serpent': Beast(archetype='serpent', length=30, height=12, girth=3.4, head=3.8, muzzle=3.4, coat='#4f7a52', accent='#c9b96a'),
    'viper': Beast(archetype='serpent', length=26, height=10, girth=3.0, head=3.6, muzzle=3.0, coat='#7a6a3c', accent='#3f3a30'),
    'wyrm': Beast(archetype='serpent', length=34, height=15, girth=4.6, head=5.0, muzzle=4.6, coat='#6a5a80', accent='#c8b0e0', horn='crest', glow='#a98fd0'),
    'worm': Beast(archetype='worm', length=22, height=9, girth=3.8, head=3.4, coat='#a87f74', segments=7),
    'grave_worm': Beast(archetype='worm', length=26, height=11, girth=4.4, head=4.0, coat='#8c7f6e', accent='#5c5346', segments=8),
    'leech': Beast(archetype='worm', length=18, height=7, girth=3.4, head=3.0, coat='#6f4a4e', segments=6),
    'centipede': Beast(archetype='worm', length=26, height=6, girth=3.0, head=3.2, coat='#8a5a3c', segments=9, legs=14),
    'snail': Beast(archetype='worm', length=16, height=9, girth=3.6, head=3.0, coat='#a89478', back='shell', shell=1.6, segments=4),
    # birds
    'crow': Beast(archetype='bird', length=13, height=12, girth=4.4, leg=5.0, head=3.2, muzzle=3.4, tail='fan', coat='#37343e', accent='#5d5a68', eye='#d8c470'),
    'gull': Beast(archetype='bird', length=14, height=12.5, girth=4.6, leg=5.4, head=3.2, muzzle=3.6, tail='fan', coat='#dfe2e4', accent='#8a97a2'),
    'vulture': Beast(archetype='bird', length=16, height=14, girth=5.4, leg=6.0, head=3.0, muzzle=3.8, tail='fan', coat='#4a423c', accent='#c3b499', mane=1.2),
    'heron': Beast(archetype='bird', length=15, height=18, girth=4.0, leg=11.0, neck=8.0, head=2.8, muzzle=6.0, tail='fan', coat='#9fb0b6', accent='#4e5a62'),
    'owl': Beast(archetype='bird', length=13, height=12, girth=5.2, leg=4.4, head=4.0, muzzle=2.2, tail='fan', ear='tuft', coat='#8a7a5e', accent='#d8cbaa', eye='#e8b64a'),
    'harpy': Beast(archetype='bird', length=15, height=16, girth=5.0, leg=7.0, head=3.6, muzzle=2.6, tail='fan', coat='#7c5f6a', accent='#c9a86a', wings='feather', mane=1.0),
    'griffon': Beast(length=24, height=16, girth=7.0, leg=12, muzzle=3.0, ear='tuft', tail='tassel', coat='#b09258', accent='#8a7048', horn='beak', wings='feather', mane=1.3),
    # winged reptiles
    'drake': Beast(archetype='drake', length=26, height=15, girth=7.0, leg=11, muzzle=6.0, coat='#6b7a4e', accent='#c9b06a', horn='crest', wings='membrane', back='ridge'),
    'wyvern': Beast(archetype='drake', length=28, height=16, girth=6.6, leg=12, muzzle=6.4, coat='#5a6a80', accent='#c0cbe0', horn='crest', wings='membrane', back='ridge'),
    'bat': Beast(archetype='drake', length=12, height=8, girth=3.6, leg=4.0, muzzle=2.4, head=3.2, coat='#5a4a52', accent='#8a7a80', ear='tall', wings='membrane'),
    'moth': Beast(archetype='insect', length=12, height=9, girth=4.0, leg=4.0, head=3.0, coat='#a99a7c', accent='#d8cdb2', wings='moth', legs=6),
    'spore_moth': Beast(archetype='insect', length=13, height=9.5, girth=4.2, leg=4.2, head=3.0, coat='#8a9a6c', accent='#c8d8a4', wings='moth', legs=6, glow='#9fc258'),
    'wasp': Beast(archetype='insect', length=14, height=8, girth=3.6, leg=4.0, head=3.0, coat='#c8a63c', accent='#3a3430', wings='clear', legs=6, segments=3),
    # bugs
    'beetle': Beast(archetype='insect', length=14, height=7, girth=5.0, leg=3.6, head=3.0, coat='#4a5a45', accent='#7f9a6a', legs=6, back='shell', shell=1.0),
    'fire_beetle': Beast(archetype='insect', length=14, height=7, girth=5.0, leg=3.6, head=3.0, coat='#8a3f2c', accent='#e0a24a', legs=6, back='shell', shell=1.0, glow='#e07a44'),
    'crystal_beetle': Beast(archetype='insect', length=15, height=7.5, girth=5.2, leg=3.8, head=3.0, coat='#6f8aa8', accent='#c6e0ea', legs=6, back='shell', shell=1.0, glow='#7fc4d8'),
    'scarab': Beast(archetype='insect', length=13, height=6.5, girth=4.8, leg=3.4, head=2.8, coat='#4f5a6a', accent='#a8b46a', legs=6, back='shell', shell=1.0),
    'mantis': Beast(archetype='insect', length=16, height=13, girth=3.6, leg=6.0, head=3.2, coat='#7fa055', accent='#c4d68e', legs=6),
    'tick': Beast(archetype='arachnid', length=11, height=6, girth=5.0, leg=4.0, head=2.4, coat='#6a5040', legs=8),
    'spider': Beast(archetype='arachnid', length=13, height=8, girth=5.4, leg=7.0, head=3.0, coat='#3f3a44', accent='#8a5f6a', legs=8, eye='#d8615a'),
    'quartz_spider': Beast(archetype='arachnid', length=14, height=8.5, girth=5.6, leg=7.4, head=3.2, coat='#8a94ac', accent='#d4e0ea', legs=8, glow='#8fb9c8'),
    # crustaceans
    'crab': Beast(archetype='crustacean', length=15, height=7, girth=6.0, leg=4.4, head=2.6, coat='#b0553c', accent='#e0b48a', legs=8),
    'sand_crab': Beast(archetype='crustacean', length=15, height=7, girth=6.0, leg=4.4, head=2.6, coat='#c4a878', accent='#e6d6b0', legs=8),
    'hermit_crab': Beast(archetype='crustacean', length=15, height=8, girth=6.2, leg=4.2, head=2.6, coat='#a06a4a', accent='#d6bb92', legs=8, back='shell', shell=1.5),
    'hermit': Beast(archetype='crustacean', length=15, height=8, girth=6.2, leg=4.2, head=2.6, coat='#8a6a52', accent='#c9b48c', legs=8, back='shell', shell=1.5),
    'scorpion': Beast(archetype='crustacean', length=18, height=7, girth=5.0, leg=4.6, head=2.8, coat='#8a6a3c', accent='#c4a469', legs=8, tail='sting', tail_length=12),
    # water
    'manta': Beast(archetype='aquatic', length=20, height=9, girth=8.0, head=3.0, coat='#4a6a80', accent='#c0d0da', tail='whip', tail_length=12),
    'cuttle': Beast(archetype='aquatic', length=16, height=11, girth=5.0, head=4.4, coat='#8a5f7a', accent='#d8b6c8', tail='tentacle', legs=6),
    'skimmer': Beast(archetype='aquatic', length=15, height=8, girth=4.4, head=3.4, coat='#6f8f9a', accent='#cfe0e4', tail='fan'),
    'coral': Beast(archetype='plant', length=14, height=14, girth=5.0, coat='#c06a72', accent='#e0a8a4'),
    # plants and fungus
    'fungus': Beast(archetype='plant', length=13, height=13, girth=5.4, coat='#a8926c', accent='#c46a52'),
    'myconid': Beast(archetype='plant', length=14, height=17, girth=5.0, coat='#9a8a68', accent='#8a5a6a', glow='#9fc258'),
    'tree': Beast(archetype='plant', length=18, height=24, girth=6.4, coat='#6f5a42', accent='#5f7a44'),
    'scarecrow': Beast(archetype='humanoid', height=17, coat='#8a7346', accent='#6a5540'),
    # humanoids
    'goblin': Beast(archetype='humanoid', height=13, coat='#6f8a52', accent='#8a6a3c'),
    'kobold': Beast(archetype='humanoid', height=12.5, coat='#9a6a44', accent='#5f4a52'),
    'bandit': Beast(archetype='humanoid', height=16, coat='#6a5a4a', accent='#8a3f3c'),
    'pirate': Beast(archetype='humanoid', height=16, coat='#4f5a6a', accent='#a8613c'),
    'knight': Beast(archetype='humanoid', height=17, coat='#8a939c', accent='#5f6a80'),
    'ogre': Beast(archetype='humanoid', height=21, coat='#8a7a5c', accent='#6a4a3c'),
    'skeleton': Beast(archetype='humanoid', height=16, coat='#d8d0b4', accent='#6a6250'),
    'ghoul': Beast(archetype='humanoid', height=15.5, coat='#8a9a86', accent='#5a4a4e'),
    'revenant': Beast(archetype='humanoid', height=16.5, coat='#7a7a8c', accent='#4f4a5e', glow='#8a78aa'),
    # spirits
    'wisp': Beast(archetype='spirit', height=13, girth=4.4, coat='#a8c6d8', glow='#7fc4d8'),
    'spell_wisp': Beast(archetype='spirit', height=13, girth=4.4, coat='#b6a8d8', glow='#a98fd0'),
    'sprite': Beast(archetype='spirit', height=12, girth=3.8, coat='#c0d8a8', glow='#9fc258'),
    'phantom': Beast(archetype='spirit', height=17, girth=5.4, coat='#9aa4bc', glow='#8a9ad0'),
    'wraith': Beast(archetype='spirit', height=18, girth=5.6, coat='#6a6280', glow='#7a6b9e'),
    'djinn': Beast(archetype='spirit', height=19, girth=6.0, coat='#c08a5c', glow='#e0a24a'),
    'horror': Beast(archetype='spirit', height=18, girth=7.0, coat='#4f4459', glow='#6a4a7a'),
    # constructs and minerals
    'golem': Beast(archetype='construct', height=20, girth=8.0, coat='#7f8079', accent='#5f6a5c'),
    'construct': Beast(archetype='construct', height=18, girth=7.0, coat='#8a8272', accent='#a89a6a'),
    'automaton': Beast(archetype='construct', height=17, girth=6.2, coat='#8a949c', accent='#c0a24a', glow='#e8cf5e'),
    'sentinel': Beast(archetype='construct', height=19, girth=6.6, coat='#7a8494', accent='#c9b06a'),
    'guardian': Beast(archetype='construct', height=20, girth=7.4, coat='#8a8a7c', accent='#c4b06a', glow='#f0dc9e'),
    'gargoyle': Beast(archetype='construct', height=17, girth=6.4, coat='#6f6f72', accent='#55555c', wings='membrane'),
    'elemental': Beast(archetype='elemental', height=17, girth=6.4, coat='#c07a4c', glow='#e07a44'),
    'geode': Beast(archetype='mineral', height=13, girth=7.0, coat='#7a7a8c', accent='#a8c0d8', glow='#8fb9c8'),
    'prism': Beast(archetype='mineral', height=15, girth=6.0, coat='#9ab4c8', accent='#d8e6ee', glow='#7fc4d8'),
    'mimic': Beast(archetype='mimic', height=12, girth=7.6, coat='#8a6a44', accent='#c0a24a'),
}

BIOME_TINT = {
    'tundra': ('#dfe8ea', 0.26), 'glacier': ('#d4e4ec', 0.30), 'volcanic': ('#c4653c', 0.22),
    'badlands': ('#c09a68', 0.18), 'swamp': ('#6f7a4c', 0.20), 'wetlands': ('#6f8a6a', 0.16),
    'crystal': ('#a8c8dc', 0.22), 'fungal': ('#9a7f9c', 0.20), 'ruins': ('#8a8478', 0.16),
    'arcane_anomaly': ('#a98fd0', 0.24), 'coast': ('#9ab4bc', 0.14), 'archipelago': ('#a4bcb8', 0.14),
    'wasteland': ('#8a7f6a', 0.18), 'ancient_forest': ('#5f7a4a', 0.14), 'pine_forest': ('#5f7458', 0.12),
}

PATTERNS = {
    'quadruped': ('', '', 'spots', 'stripes', 'patches', 'dapple', 'saddle', 'countershade'),
    'drake': ('', 'bands', 'patches', 'dapple', 'countershade'),
    'bird': ('', '', 'speckle', 'bands', 'patches'),
    'insect': ('', 'bands', 'spots'),
    'arachnid': ('', 'spots', 'bands'),
    'serpent': ('bands', 'bands', 'spots', 'patches'),
    'worm': ('bands', 'bands', ''),
    'crustacean': ('', 'spots', 'patches'),
    'aquatic': ('', 'bands', 'spots', 'countershade'),
    'amphibian': ('', 'spots', 'patches'),
    'primate': ('', 'patches', 'countershade'),
    'plant': ('', 'patches', 'speckle'),
    'mineral': ('', 'bands'),
    'construct': ('', 'bands', 'patches'),
}

EYE_COLOURS = ('#e6d089', '#d8a24a', '#c8e07a', '#8fd8e0', '#e08a6a', '#c0b0e8', '#e4e0c8')

def _vary(spec, mob):
    """Give one creature its own build inside its family's body plan."""
    seed = pigment.keyed(mob.get('id', 'mob'))
    spec.seed = seed
    rng = random.Random(seed)
    archetype = spec.archetype

    choices = PATTERNS.get(archetype, ('',))
    spec.pattern = choices[seed % len(choices)]
    if spec.spots:                       # families that always carry markings
        spec.pattern = 'spots'
        spec.pattern_colour = spec.spots
    if spec.pattern and not spec.pattern_colour:
        toward = (238, 232, 214, 255) if (seed >> 3) & 1 else (34, 30, 40, 255)
        weight = 0.34 if toward[0] > 128 else 0.40
        spec.pattern_colour = pigment.hexstr(blend(pigment.rgb(spec.coat), toward, weight))

    # hide colour drifts a little between individuals
    spec.coat = pigment.hexstr(blend(pigment.rgb(spec.coat),
                                     (rng.randrange(90, 210), rng.randrange(90, 200),
                                      rng.randrange(80, 190), 255),
                                     0.06 + rng.random() * 0.07))
    spec.eye = EYE_COLOURS[(seed >> 5) % len(EYE_COLOURS)]

    # proportions: same species, different animal
    spec.length *= 0.93 + rng.random() * 0.14
    spec.height *= 0.94 + rng.random() * 0.13
    spec.girth *= 0.92 + rng.random() * 0.17
    spec.leg *= 0.93 + rng.random() * 0.15
    spec.head *= 0.94 + rng.random() * 0.12
    spec.muzzle *= 0.88 + rng.random() * 0.24
    spec.ear_size *= 0.85 + rng.random() * 0.32
    spec.tail_length *= 0.84 + rng.random() * 0.34
    if spec.mane:
        spec.mane *= 0.7 + rng.random() * 0.7
    elif archetype == 'quadruped' and (seed >> 7) % 5 == 0:
        spec.mane = 0.8 + rng.random() * 0.5

    if not spec.horn and archetype in ('quadruped', 'drake') and (seed >> 9) % 6 == 0:
        spec.horn = ('curl', 'ridge_horn', 'tusk', 'crest')[(seed >> 11) % 4]
    if not spec.back and archetype in ('quadruped', 'drake') and (seed >> 13) % 7 == 0:
        spec.back = 'ridge'
    return spec

def describe(mob):
    """Anatomy for one catalogue creature."""
    spec = FAMILIES.get(mob.get('family', ''))
    if spec is None:
        raise ValueError("Unmapped creature family: " + str(mob.get("family", "")))
    spec = replace(spec)
    spec.family_key = mob.get('family', '')
    tint = BIOME_TINT.get(mob.get('biome', ''))
    if tint and not mob.get('boss'):
        spec.coat = pigment.hexstr(blend(pigment.rgb(spec.coat), tint[0], tint[1]))
    _vary(spec, mob)
    if not mob.get('boss'):
        spec.horn = FAMILIES[mob['family']].horn
    element = mob.get('element', 'Physical')
    if element not in ('Physical', ''):
        spec.glow = spec.glow or pigment.ELEMENTS.get(element)
        # Only bodies that are made of their element take its colour; a lightning
        # horse keeps a horse's hide and gets the glow instead.
        if not spec.accent and spec.archetype in ('spirit', 'elemental', 'mineral', 'construct'):
            spec.accent = pigment.ELEMENTS.get(element)
    if mob.get('elite') or mob.get('boss'):
        # veterans carry the marks of it: heavier plating, scars, harder eyes
        spec.plates = 1.0
        spec.scarred = 1.0
        spec.back = spec.back or 'spikes'
        spec.eye = '#f0c060'
    if mob.get('boss'):
        spec.crown = 'horns'
        spec.horn = spec.horn or 'crest'
        spec.mane = max(spec.mane, 1.2)
    grow = 1.0 + min(0.22, max(0, mob.get('level', 1) - 1) * 0.004)
    spec.length *= grow
    spec.height *= grow
    spec.leg *= grow
    return spec
