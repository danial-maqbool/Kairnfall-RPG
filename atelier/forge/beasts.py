"""Creatures.

Each catalogue family is mapped to an anatomy archetype and a small set of
proportions: how long the body is, how tall it stands, how long the muzzle is,
what the ears and tail do. A wolf is a long low quadruped with a deep chest and
a brush tail; a heron is a two legged bird on stilts. Nothing shares one generic
blob shape, because a silhouette that could be any animal is not a sprite for a
particular animal.

Drawing happens in creature space: the origin sits on the ground between the
feet, x runs right and y runs up. `Stage` maps that onto the sprite frame, so
the same code serves 64px creatures and 128px bosses.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from PIL import Image

from . import folk, pigment, rig
from .brush import Sketch, catmull, taper_shape
from .pigment import blend, ramp

FRAMES = 8
STATES = rig.STATES


class Stage:
    """Creature space to frame space."""

    def __init__(self, size, scale=1.0):
        self.size = size
        self.sketch = Sketch(size)
        self.cx = size / 2 - 0.5
        self.ground = size * 0.86
        self.scale = scale

    def at(self, x, y):
        return (self.cx + x * self.scale, self.ground - y * self.scale)

    def path(self, points):
        return [self.at(x, y) for x, y in points]

    def piece(self, tone):
        return self.sketch.piece(tone)

    def stamp(self, piece, **kwargs):
        self.sketch.stamp(piece, **kwargs)
        return self

    def blob(self, tone, points, samples=6, rim=0.85, occlude=0.6):
        piece = self.piece(tone)
        piece.poly(catmull(self.path(points), samples, closed=True), 3)
        self.stamp(piece, rim=rim, occlude=occlude)
        return piece

    def limb(self, tone, a, b, wa, wb, shade=3, rim=0.7, occlude=0.5):
        piece = self.piece(tone)
        piece.poly(taper_shape(self.at(*a), self.at(*b), wa * self.scale, wb * self.scale), shade)
        self.stamp(piece, rim=rim, occlude=occlude)
        return piece

    def ball(self, tone, centre, radius, shade=3, rim=0.9, occlude=0.55):
        piece = self.piece(tone)
        x, y = self.at(*centre)
        piece.disc(x, y, radius * self.scale, shade)
        self.stamp(piece, rim=rim, occlude=occlude)
        return piece


# ------------------------------------------------------------------ motion --

@dataclass
class Motion:
    bob: float = 0.0
    lunge: float = 0.0
    crouch: float = 0.0
    phase: float = 0.0
    stride: float = 0.0
    mouth: float = 0.0
    rear: float = 0.0
    flash: float = 0.0
    fade: float = 1.0
    collapse: float = 0.0
    charge: float = 0.0
    pitch: float = 0.0


def motion(state, frame):
    t = frame / (FRAMES - 1)
    phase = frame / FRAMES * math.tau
    m = Motion(phase=phase)
    if state == 'idle':
        m.bob = math.sin(phase) * 0.5
        m.mouth = 0.1
    elif state == 'walk':
        m.stride = 1.0
        m.bob = abs(math.cos(phase)) * 0.7 - 0.35
    elif state == 'attack':
        drive = math.sin(min(1.0, t * 1.35) * math.pi)
        m.lunge = drive * 5.0
        m.crouch = drive * 1.6
        m.mouth = min(1.0, drive * 1.6)
        m.pitch = -drive * 0.16
    elif state == 'cast':
        m.charge = math.sin(t * math.pi) ** 0.7
        m.rear = m.charge * 0.7
        m.mouth = m.charge
        m.bob = -m.charge * 1.4
    elif state == 'hit':
        shock = math.sin(min(1.0, t * 1.9) * math.pi) ** 0.6
        m.lunge = -shock * 3.0
        m.crouch = shock * 1.2
        m.flash = 0.6 if frame == 0 else (0.42 if frame == 1 else (0.2 if frame == 2 else 0.0))
        m.mouth = shock * 0.7
    elif state == 'death':
        m.collapse = min(1.0, (t * 1.25) ** 0.85)
        m.fade = 1.0 if frame < 6 else (0.86 if frame == 6 else 0.7)
        m.mouth = 0.4 * (1 - m.collapse)
    return m


# --------------------------------------------------------------- anatomy ----

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


def describe(mob):
    """Anatomy for one catalogue creature."""
    spec = FAMILIES.get(mob.get('family', ''))
    if spec is None:
        spec = Beast()
    spec = replace(spec)
    tint = BIOME_TINT.get(mob.get('biome', ''))
    if tint and not mob.get('boss'):
        spec.coat = pigment.hexstr(blend(pigment.rgb(spec.coat), tint[0], tint[1]))
    element = mob.get('element', 'Physical')
    if element not in ('Physical', ''):
        spec.glow = spec.glow or pigment.ELEMENTS.get(element)
        # Only bodies that are made of their element take its colour; a lightning
        # horse keeps a horse's hide and gets the glow instead.
        if not spec.accent and spec.archetype in ('spirit', 'elemental', 'mineral', 'construct'):
            spec.accent = pigment.ELEMENTS.get(element)
    if mob.get('elite') or mob.get('boss'):
        spec.plates = 1.0
    grow = 1.0 + min(0.22, max(0, mob.get('level', 1) - 1) * 0.004)
    spec.length *= grow
    spec.height *= grow
    spec.leg *= grow
    return spec


# --------------------------------------------------------------- drawing ----

def _gait(m, offset, reach=4.2, lift=2.4):
    """Foot displacement for one leg: forward or back, and lifted while swinging."""
    if m.stride <= 0:
        return 0.0, 0.0
    angle = m.phase + offset * math.tau
    return math.cos(angle) * reach, max(0.0, -math.sin(angle)) * lift


def _leg_pair(stage, spec, tones, hip, offsets, m, back=False, depth=1.0, spread=None):
    """Two legs at one girdle, near leg drawn brighter than the far leg.

    `spread` places the pair across the body for head-on views; without it the
    pair is staggered in depth for the side view.
    """
    out = []
    for index, offset in enumerate(offsets):
        near = index == 1
        dx, lift = _gait(m, offset)
        collapse = m.collapse
        if spread is None:
            base_x = hip[0] + (1.4 if near else -1.0) * (0.6 if not back else -0.6)
            knee_out = 0.8 if near else -0.6
        else:
            base_x = hip[0] + spread * (1 if near else -1)
            knee_out = spread * 0.12 * (1 if near else -1)
        foot_x = base_x + dx
        foot_y = lift
        knee_x = base_x + dx * 0.45 + knee_out
        knee_y = hip[1] * 0.5 + 0.6
        if collapse > 0.05:
            splay = collapse * (5.0 if back else 4.0)
            foot_x = base_x + (splay if back else -splay) * (1 if near else 0.7)
            foot_y = collapse * 0.6
            knee_x = base_x + (splay * 0.5 if back else -splay * 0.5)
            knee_y = hip[1] * (1 - collapse * 0.7) * 0.5
        tone = tones['coat'] if near else tones['far']
        width = spec.leg_width * (1.0 if near else 0.86) * depth
        stage.limb(tone, (hip[0], hip[1]), (knee_x, knee_y), width * 1.15, width * 0.9,
                   rim=0.75 if near else 0.4)
        stage.limb(tone, (knee_x, knee_y), (foot_x, foot_y), width * 0.9, width * 0.72,
                   rim=0.7 if near else 0.35)
        piece = stage.piece(tones['claw'] if spec.digit != 'hoof' else tones['horn'])
        x, y = stage.at(foot_x, foot_y)
        if spec.digit == 'hoof':
            piece.poly([(x - 1.6 * stage.scale, y - 1.6 * stage.scale), (x + 1.8 * stage.scale, y - 1.6 * stage.scale),
                        (x + 1.6 * stage.scale, y), (x - 1.6 * stage.scale, y)], 3)
        else:
            piece.poly(catmull([(x - 2.0 * stage.scale, y - 1.8 * stage.scale),
                                (x + 2.6 * stage.scale, y - 1.6 * stage.scale),
                                (x + 2.8 * stage.scale, y), (x - 2.2 * stage.scale, y)], 4, closed=True), 3)
        stage.stamp(piece, rim=0.6, occlude=0.5)
        out.append((foot_x, foot_y))
    return out


def _tail(stage, spec, tones, root, m, facing):
    kind = spec.tail
    if kind in ('', 'none'):
        return
    sway = math.sin(m.phase) * 1.4 + m.lunge * -0.2
    length = spec.tail_length * (1 - m.collapse * 0.2)
    tip = (root[0] - length * facing, root[1] + (2.6 if kind in ('brush', 'whip', 'taper') else 1.0)
           - m.collapse * root[1] * 0.8 + sway * 0.4)
    mid = ((root[0] + tip[0]) / 2 - facing * 0.6, (root[1] + tip[1]) / 2 + 2.2 - m.collapse * 2.0 + sway * 0.6)
    if kind == 'stub':
        stage.ball(tones['coat'], (root[0] - 1.6 * facing, root[1] + 1.0), 2.0)
        return
    if kind == 'puff':
        stage.ball(tones['belly'], (root[0] - 2.4 * facing, root[1] + 0.6), 2.6)
        return
    if kind == 'sting':
        curve = [root, (root[0] - length * 0.4 * facing, root[1] + length * 0.5),
                 (root[0] - length * 0.2 * facing, root[1] + length * 0.95),
                 (root[0] + length * 0.35 * facing, root[1] + length * 0.75)]
        piece = stage.piece(tones['coat'])
        piece.line(catmull(stage.path(curve), 6), 3, max(1, round(2.6 * stage.scale)))
        stage.stamp(piece, rim=0.7, occlude=0.5)
        barb = stage.piece(tones['claw'])
        x, y = stage.at(curve[-1][0] + facing * 1.2, curve[-1][1] - 1.0)
        barb.poly([(x, y - 3 * stage.scale), (x + 2.2 * stage.scale, y + 1.6 * stage.scale),
                   (x - 2.2 * stage.scale, y + 1.6 * stage.scale)], 3)
        stage.stamp(barb, rim=0.8, occlude=0.5)
        return
    piece = stage.piece(tones['coat'])
    path = catmull(stage.path([root, mid, tip]), 8)
    width = {'brush': 4.6, 'whip': 2.4, 'rope': 1.8, 'taper': 4.0, 'tassel': 2.2, 'curl': 2.4}.get(kind, 3.0)
    piece.line(path, 3, max(1, round(width * stage.scale * 0.62)))
    if kind == 'brush':
        piece.poly(catmull(stage.path([
            (mid[0], mid[1] + 2.0), (tip[0] - 1.2 * facing, tip[1] + 1.6),
            (tip[0] - 1.6 * facing, tip[1] - 1.8), (mid[0], mid[1] - 2.0)]), 5, closed=True), 3)
    elif kind == 'tassel':
        x, y = stage.at(*tip)
        piece.poly(catmull([(x - 2 * stage.scale, y - 2 * stage.scale), (x + 2 * stage.scale, y - 1 * stage.scale),
                            (x, y + 4 * stage.scale)], 4, closed=True), 2)
    elif kind == 'rope':
        pass
    stage.stamp(piece, rim=0.6, occlude=0.5)


def _ears(stage, spec, tones, head, m, facing, side):
    kind = spec.ear
    if kind in ('', 'none'):
        return
    size = spec.ear_size
    piece = stage.piece(tones['coat'])
    inner = stage.piece(tones['belly'])
    positions = [(head[0] - 1.0 * facing, head[1] + spec.head * 0.7)] if side else [
        (head[0] - spec.head * 0.72, head[1] + spec.head * 0.62),
        (head[0] + spec.head * 0.72, head[1] + spec.head * 0.62)]
    for bx, by in positions:
        if kind == 'rabbit':
            pts = [(bx - 1.1, by), (bx - 0.2, by + size), (bx + 1.1, by + size * 0.86), (bx + 1.0, by)]
            inner_pts = [(bx - 0.4, by + 0.6), (bx + 0.1, by + size * 0.78), (bx + 0.6, by + 0.6)]
        elif kind == 'tall':
            pts = [(bx - 1.6, by), (bx - 0.2, by + size * 1.25), (bx + 1.6, by)]
            inner_pts = [(bx - 0.7, by + 0.4), (bx - 0.1, by + size * 0.9), (bx + 0.7, by + 0.4)]
        elif kind == 'drop':
            pts = [(bx - 1.4, by), (bx + 1.6, by + 0.4), (bx + 2.4, by - size * 0.9), (bx - 0.2, by - size * 0.6)]
            inner_pts = [(bx + 0.2, by - 0.4), (bx + 1.4, by - size * 0.7), (bx + 0.2, by - size * 0.4)]
        elif kind == 'tuft':
            pts = [(bx - 1.2, by), (bx - 0.4, by + size * 1.1), (bx + 1.4, by + size * 0.2), (bx + 0.6, by - 0.4)]
            inner_pts = []
        else:  # round
            pts = [(bx - 1.8, by - 0.4), (bx - 1.4, by + size * 0.85), (bx + 1.4, by + size * 0.85), (bx + 1.8, by - 0.4)]
            inner_pts = [(bx - 0.9, by + 0.2), (bx, by + size * 0.6), (bx + 0.9, by + 0.2)]
        piece.poly(catmull(stage.path(pts), 4, closed=True), 3)
        if inner_pts:
            inner.poly(catmull(stage.path(inner_pts), 4, closed=True), 3)
    stage.stamp(piece, rim=0.8, occlude=0.5)
    inner.clip(piece)
    stage.sketch.overlay(inner)


def _horns(stage, spec, tones, head, m, facing, side):
    kind = spec.horn
    if not kind:
        return
    piece = stage.piece(tones['horn'])
    hx, hy = head
    r = spec.head
    if kind == 'antler':
        for sign in ((facing,) if side else (-1, 1)):
            base = (hx + sign * r * 0.4, hy + r * 0.7)
            main = [(base[0], base[1]), (base[0] + sign * 1.6, base[1] + 4.0), (base[0] + sign * 3.4, base[1] + 7.4)]
            piece.line(catmull(stage.path(main), 5), 3, max(1, round(1.8 * stage.scale)))
            for branch, height in ((2.0, 3.0), (3.0, 5.4)):
                a = (base[0] + sign * branch * 0.55, base[1] + height)
                b = (base[0] + sign * (branch + 2.6), base[1] + height + 2.2)
                piece.line(stage.path([a, b]), 3, max(1, round(1.5 * stage.scale)))
    elif kind == 'curl':
        for sign in ((facing,) if side else (-1, 1)):
            arc = [(hx + sign * r * 0.5, hy + r * 0.6), (hx + sign * (r + 2.4), hy + r * 0.2),
                   (hx + sign * (r + 2.0), hy - r * 0.9), (hx + sign * (r * 0.6), hy - r * 0.8)]
            piece.line(catmull(stage.path(arc), 6), 3, max(1, round(2.0 * stage.scale)))
    elif kind == 'bull':
        for sign in ((facing, -facing) if side else (-1, 1)):
            arc = [(hx + sign * r * 0.5, hy + r * 0.5), (hx + sign * (r + 2.8), hy + r * 0.9),
                   (hx + sign * (r + 3.6), hy + r * 0.1)]
            piece.line(catmull(stage.path(arc), 5), 3, max(1, round(2.2 * stage.scale)))
    elif kind == 'ridge_horn':
        for sign in ((facing,) if side else (-1, 1)):
            arc = [(hx + sign * r * 0.4, hy + r * 0.7), (hx + sign * (r * 0.2), hy + r * 2.6),
                   (hx - sign * (r * 0.9), hy + r * 3.4)]
            piece.line(catmull(stage.path(arc), 5), 3, max(1, round(2.0 * stage.scale)))
    elif kind == 'tusk':
        for sign in ((1,) if side else (-1, 1)):
            base = (hx + facing * r * 0.8 * (1 if side else sign), hy - r * 0.5)
            piece.line(catmull(stage.path([base, (base[0] + facing * 1.4, base[1] + 1.4),
                                           (base[0] + facing * 0.6, base[1] + 3.0)]), 4), 3,
                       max(1, round(1.6 * stage.scale)))
    elif kind == 'crest':
        pts = [(hx - r * 0.8, hy + r * 0.6), (hx - r * 0.2, hy + r * 2.2), (hx + r * 0.8, hy + r * 1.0),
               (hx + r * 1.2, hy + r * 2.0), (hx + r * 1.4, hy + r * 0.2)]
        piece.poly(catmull(stage.path(pts), 4, closed=True), 3)
    elif kind == 'beak':
        beak = [(hx + facing * (r * 0.4), hy + 0.8), (hx + facing * (r + spec.muzzle), hy - 0.4),
                (hx + facing * (r * 0.4), hy - 2.0)]
        piece.poly(catmull(stage.path(beak), 4, closed=True), 3)
    stage.stamp(piece, rim=0.9, occlude=0.5)


def _eye(stage, spec, tones, head, facing, side, m):
    piece = stage.piece(ramp(spec.eye))
    r = spec.head
    spots = [(head[0] + facing * r * 0.42, head[1] + r * 0.18)] if side else [
        (head[0] - r * 0.42, head[1] + r * 0.2), (head[0] + r * 0.42, head[1] + r * 0.2)]
    for ex, ey in spots:
        x, y = stage.at(ex, ey)
        piece.disc(x, y, max(0.9, 1.3 * stage.scale), 4)
        piece.dot(x, y, (30, 26, 32, 255))
    stage.stamp(piece, outline=False, rim=0, occlude=0)


def _muzzle(stage, spec, tones, head, facing, side, m):
    r = spec.head
    length = spec.muzzle
    if length <= 0.4:
        return
    piece = stage.piece(tones['coat'])
    if side:
        tip = (head[0] + facing * (r * 0.5 + length), head[1] - spec.muzzle_drop)
        pts = [(head[0], head[1] + r * 0.35), (tip[0], tip[1] + 1.5), (tip[0] + facing * 0.4, tip[1] - 1.2),
               (head[0], head[1] - r * 0.62)]
    else:
        tip = (head[0], head[1] - r * 0.5 - spec.muzzle_drop)
        pts = [(head[0] - r * 0.5, head[1]), (head[0] + r * 0.5, head[1]),
               (tip[0] + r * 0.34, tip[1] - length * 0.42), (tip[0] - r * 0.34, tip[1] - length * 0.42)]
    piece.poly(catmull(stage.path(pts), 5, closed=True), 3)
    stage.stamp(piece, rim=0.8, occlude=0.55)
    nose = stage.piece(tones['claw'])
    if side:
        x, y = stage.at(head[0] + facing * (r * 0.5 + length * 0.92), head[1] - spec.muzzle_drop + 0.4)
    else:
        x, y = stage.at(head[0], head[1] - r * 0.5 - spec.muzzle_drop - length * 0.3)
    nose.disc(x, y, max(0.9, 1.2 * stage.scale), 3)
    stage.stamp(nose, outline=False, rim=0, occlude=0)
    if m.mouth > 0.15 and side:
        jaw = stage.piece(ramp('#5c3038'))
        a = stage.at(head[0] + facing * r * 0.3, head[1] - r * 0.45)
        b = stage.at(head[0] + facing * (r * 0.5 + length * 0.9), head[1] - spec.muzzle_drop - 0.6 - m.mouth * 2.2)
        jaw.poly([a, b, (b[0], b[1] + 3 * stage.scale * m.mouth), (a[0], a[1] + 1.6 * stage.scale)], 3)
        stage.stamp(jaw, rim=0.3, occlude=0.3)
        fang = stage.piece(tones['horn'])
        fang.poly([(b[0] - 2 * stage.scale, b[1] + 0.6 * stage.scale), (b[0], b[1] + 3.2 * stage.scale),
                   (b[0] - 3.4 * stage.scale, b[1] + 1.0 * stage.scale)], 4)
        stage.stamp(fang, outline=False, rim=0, occlude=0)


def _back(stage, spec, tones, front, rear, top, m):
    kind = spec.back
    if not kind:
        return
    if kind == 'shell':
        piece = stage.piece(tones['accent'])
        cx = (front[0] + rear[0]) / 2
        half = abs(front[0] - rear[0]) / 2 + 1.4
        piece.poly(catmull(stage.path([
            (cx - half, top - spec.girth * 0.7), (cx - half * 0.7, top + spec.girth * 0.9 * spec.shell),
            (cx, top + spec.girth * 1.15 * spec.shell), (cx + half * 0.7, top + spec.girth * 0.9 * spec.shell),
            (cx + half, top - spec.girth * 0.7)]), 6, closed=True), 3)
        stage.stamp(piece, rim=0.9, occlude=0.65)
        marks = stage.piece(tones['coat'])
        for step in (-0.5, 0.0, 0.5):
            marks.line(catmull(stage.path([
                (cx + half * step, top - spec.girth * 0.5),
                (cx + half * step * 1.15, top + spec.girth * 0.95 * spec.shell)]), 4), 1, 1)
        marks.clip(piece)
        stage.sketch.overlay(marks)
        return
    piece = stage.piece(tones['accent'])
    steps = 5 if kind == 'ridge' else 4
    for index in range(steps):
        t = index / (steps - 1)
        x = front[0] + (rear[0] - front[0]) * t
        y = top + spec.girth * 0.55
        height = (2.4 if kind == 'ridge' else 3.2) * (1.0 - abs(t - 0.4))
        if kind == 'plates':
            piece.poly(catmull(stage.path([(x - 2.2, y - 0.6), (x, y + height * 0.8), (x + 2.2, y - 0.6)]), 4, closed=True), 3)
        elif kind == 'hump':
            continue
        else:
            piece.poly(stage.path([(x - 1.6, y - 0.4), (x, y + height), (x + 1.6, y - 0.4)]), 3)
    if kind != 'hump':
        stage.stamp(piece, rim=0.85, occlude=0.5)


def quadruped(spec, m, direction, stage):
    """Dog, cat, bear, deer, boar, lizard: one body plan with real proportions."""
    if direction in (0, 3):
        return _quadruped_face(spec, m, direction, stage)
    return _quadruped_side(spec, m, direction, stage)


def _quadruped_face(spec, m, direction, stage):
    """Head on. A four legged animal seen from the front is a chest with a head
    over it and a foreshortened back behind, never a figure standing upright."""
    tones = spec.ramps()
    back_view = direction == 3
    collapse = m.collapse
    girth = spec.girth
    body_y = spec.height * (1 - collapse * 0.72) - m.crouch * 0.5 + m.bob
    lunge = m.lunge * 0.3

    # far girdle: the hind legs stand wider and read dimmer
    _leg_pair(stage, spec, tones, (0.0, body_y - girth * 0.10), (0.5, 0.0), m,
              back=True, depth=0.82, spread=girth * 0.92)
    rump = stage.piece(tones['accent'])
    rx, ry = stage.at(0.0, body_y + girth * 0.80)
    rump.ellipse((rx - girth * 0.86 * stage.scale, ry - girth * 0.60 * stage.scale,
                  rx + girth * 0.86 * stage.scale, ry + girth * 0.72 * stage.scale), 3)
    stage.stamp(rump, rim=0.6, occlude=0.5)
    # Seen head on the tail is behind the animal; walking away it hangs over the
    # rump. Either way it never sticks out sideways like a plank.
    if back_view and spec.tail not in ('', 'none'):
        tail = stage.piece(tones['coat'])
        sway = math.sin(m.phase) * 1.2
        drop = spec.tail_length * (0.34 if spec.tail in ('rope', 'whip', 'taper', 'tassel') else 0.24)
        width = {'brush': 4.0, 'taper': 3.4, 'whip': 2.0, 'rope': 1.6}.get(spec.tail, 2.6)
        tail.poly(taper_shape(stage.at(0.4, body_y + girth * 1.10),
                              stage.at(sway, body_y + girth * 1.10 + drop),
                              width * stage.scale, width * 0.6 * stage.scale), 3)
        stage.stamp(tail, rim=0.7, occlude=0.5)

    _leg_pair(stage, spec, tones, (lunge, body_y - girth * 0.05), (0.0, 0.5), m,
              depth=1.0, spread=girth * 0.56)

    chest = stage.piece(tones['coat'])
    top = body_y + girth * (1.05 if spec.back == 'hump' else 0.92)
    chest.poly(catmull(stage.path([
        (-girth * 0.98 + lunge, body_y - girth * 0.55),
        (-girth * 0.88 + lunge, top - girth * 0.2),
        (0.0 + lunge, top),
        (girth * 0.88 + lunge, top - girth * 0.2),
        (girth * 0.98 + lunge, body_y - girth * 0.55),
        (girth * 0.62 + lunge, body_y - girth * 1.10),
        (0.0 + lunge, body_y - girth * 1.22),
        (-girth * 0.62 + lunge, body_y - girth * 1.10),
    ]), 6, closed=True), 3)
    stage.stamp(chest, rim=0.9, occlude=0.65)
    belly = stage.piece(tones['belly'])
    belly.poly(catmull(stage.path([
        (-girth * 0.44 + lunge, body_y + girth * 0.35), (girth * 0.44 + lunge, body_y + girth * 0.35),
        (girth * 0.40 + lunge, body_y - girth * 1.10), (-girth * 0.40 + lunge, body_y - girth * 1.10)]),
        5, closed=True), 3)
    belly.clip(chest)
    stage.sketch.overlay(belly)
    if spec.spots:
        marks = stage.piece(ramp(spec.spots))
        for index in range(5):
            x, y = stage.at(math.sin(index * 2.1) * girth * 0.55 + lunge, body_y - girth * 0.4 + index * girth * 0.32)
            marks.disc(x, y, max(0.9, 1.1 * stage.scale), 2)
        marks.clip(chest)
        stage.sketch.overlay(marks)
    if spec.mane > 0:
        mane = stage.piece(tones['accent'])
        mane.poly(catmull(stage.path([
            (-girth * 1.05 + lunge, body_y + girth * 0.25), (0.0 + lunge, top + girth * 0.25),
            (girth * 1.05 + lunge, body_y + girth * 0.25), (girth * 0.5 + lunge, body_y - girth * 0.1),
            (-girth * 0.5 + lunge, body_y - girth * 0.1)]), 5, closed=True), 3)
        stage.stamp(mane, rim=0.7, occlude=0.5)

    # Low slung animals carry the head near the shoulder, not above it.
    carriage = min(1.0, spec.height / max(1.0, spec.girth * 2.2))
    head_pos = (lunge, top + (spec.head * 0.32 + spec.neck * 0.42 * (1 - collapse)) * carriage + m.rear * 2.0)
    stage.limb(tones['coat'], (lunge, top - girth * 0.2), head_pos,
               spec.neck_width * 1.25, spec.neck_width * 0.95, rim=0.8)
    head_piece = stage.piece(tones['coat'])
    hx, hy = stage.at(*head_pos)
    head_piece.ellipse((hx - spec.head * 1.02 * stage.scale, hy - spec.head * 0.96 * stage.scale,
                        hx + spec.head * 1.02 * stage.scale, hy + spec.head * 1.04 * stage.scale), 3)
    stage.stamp(head_piece, rim=0.9, occlude=0.55)
    _ears(stage, spec, tones, head_pos, m, 0, False)
    if back_view:
        return
    _muzzle(stage, spec, tones, head_pos, 1, False, m)
    _horns(stage, spec, tones, head_pos, m, 1, False)
    _eye(stage, spec, tones, head_pos, 1, False, m)


def _quadruped_side(spec, m, direction, stage):
    tones = spec.ramps()
    side = direction in (1, 2)
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    back_view = direction == 3
    collapse = m.collapse
    height = spec.height * (1 - collapse * 0.72) - m.crouch * 0.5 + m.bob
    body_y = height
    half = spec.length / 2 if side else spec.girth * 0.92
    lunge = m.lunge * (1 if side else 0.4)
    front = (half * 0.82 * (facing or 1) + lunge, body_y + m.rear * 3.0)
    rear = (-half * 0.86 * (facing or 1) + lunge * 0.3, body_y - m.rear * 1.4)
    if not side:
        front = (0.0, body_y)
        rear = (0.0, body_y - 1.2)

    hip_front = (front[0] - 1.0 * (facing or 1), front[1] - spec.girth * 0.34)
    hip_rear = (rear[0] + 0.6 * (facing or 1), rear[1] - spec.girth * 0.34)
    if side:
        _leg_pair(stage, spec, tones, hip_rear, (0.5, 0.0), m, back=True, depth=0.94)
        _leg_pair(stage, spec, tones, hip_front, (0.0, 0.5), m, depth=0.94)
    else:
        _leg_pair(stage, spec, tones, (rear[0], rear[1] - spec.girth * 0.3), (0.5, 0.0), m, back=True, depth=0.8)

    # trunk
    piece = stage.piece(tones['coat'])
    if side:
        top = body_y + spec.girth * (1.25 if spec.back == 'hump' else 1.0)
        belly = body_y - spec.girth * 0.85
        pts = [
            (rear[0] - half * 0.34, rear[1] + spec.girth * 0.75),
            (rear[0] + half * 0.2 * (facing or 1), top - (1.6 if spec.back == 'hump' else 0.4)),
            (front[0] - half * 0.15 * (facing or 1), top),
            (front[0] + half * 0.30 * (facing or 1), front[1] + spec.girth * 0.62),
            (front[0] + half * 0.34 * (facing or 1), belly + spec.girth * 0.3),
            (front[0] - half * 0.1 * (facing or 1), belly),
            (rear[0] + half * 0.1 * (facing or 1), belly + spec.girth * 0.18),
            (rear[0] - half * 0.30, rear[1] - spec.girth * 0.55),
        ]
    else:
        top = body_y + spec.girth * 0.95
        pts = [
            (-spec.girth * 0.95, body_y - spec.girth * 0.7),
            (-spec.girth * 0.86, top),
            (0.0, top + spec.girth * 0.22),
            (spec.girth * 0.86, top),
            (spec.girth * 0.95, body_y - spec.girth * 0.7),
            (spec.girth * 0.55, body_y - spec.girth * 1.15),
            (-spec.girth * 0.55, body_y - spec.girth * 1.15),
        ]
    piece.poly(catmull(stage.path(pts), 6, closed=True), 3)
    stage.stamp(piece, rim=0.9, occlude=0.65)
    belly_piece = stage.piece(tones['belly'])
    if side:
        belly_piece.poly(catmull(stage.path([
            (rear[0] - half * 0.2, body_y - spec.girth * 0.5),
            (front[0] + half * 0.2 * (facing or 1), body_y - spec.girth * 0.45),
            (front[0], body_y - spec.girth * 1.0),
            (rear[0], body_y - spec.girth * 0.95)]), 5, closed=True), 3)
    else:
        belly_piece.poly(catmull(stage.path([
            (-spec.girth * 0.5, body_y + spec.girth * 0.5), (spec.girth * 0.5, body_y + spec.girth * 0.5),
            (spec.girth * 0.42, body_y - spec.girth * 1.05), (-spec.girth * 0.42, body_y - spec.girth * 1.05)]),
            5, closed=True), 3)
    belly_piece.clip(piece)
    stage.sketch.overlay(belly_piece)
    if spec.spots:
        marks = stage.piece(ramp(spec.spots))
        for index in range(7):
            angle = index * 2.4
            mx = rear[0] + (front[0] - rear[0]) * (index / 6.0)
            my = body_y + math.sin(angle) * spec.girth * 0.45
            x, y = stage.at(mx, my)
            marks.disc(x, y, max(0.9, 1.2 * stage.scale), 2)
        marks.clip(piece)
        stage.sketch.overlay(marks)
    _back(stage, spec, tones, front, rear, body_y, m)
    if spec.mane > 0:
        mane = stage.piece(tones['accent'])
        mx = front[0] - 0.5 * (facing or 1)
        mane.poly(catmull(stage.path([
            (mx - 2.4, body_y + spec.girth * 0.4), (mx, body_y + spec.girth * (1.2 + 0.3 * spec.mane)),
            (mx + 2.6 * (facing or 1), body_y + spec.girth * 0.8), (mx + 1.6 * (facing or 1), body_y - spec.girth * 0.2)]),
            5, closed=True), 3)
        stage.stamp(mane, rim=0.7, occlude=0.5)

    if side:
        _leg_pair(stage, spec, tones, hip_rear, (0.0, 0.5), m, back=True)
        _leg_pair(stage, spec, tones, hip_front, (0.5, 0.0), m)
    else:
        _leg_pair(stage, spec, tones, (front[0], front[1] - spec.girth * 0.34), (0.0, 0.5), m)
    _tail(stage, spec, tones, (rear[0] - half * 0.28 * (facing or 1), body_y + spec.girth * 0.5), m, facing or 1)

    # neck and head
    neck_base = (front[0] + half * 0.14 * (facing or 1), body_y + spec.girth * 0.55)
    reach = spec.neck * (1 - collapse * 0.85) + m.rear * 2.0
    head_pos = (neck_base[0] + (facing or 0) * reach * 0.72 + (0 if side else 0),
                neck_base[1] + reach * (0.72 if side else 0.9) - m.crouch * 0.8)
    if collapse > 0.4:
        head_pos = (neck_base[0] + (facing or 1) * (reach * 0.5 + 3.0), spec.head * 0.9)
    stage.limb(tones['coat'], neck_base, head_pos, spec.neck_width * 1.1, spec.neck_width * 0.86, rim=0.8)
    if back_view:
        stage.ball(tones['coat'], head_pos, spec.head)
        _ears(stage, spec, tones, head_pos, m, 0, False)
        return
    head_piece = stage.piece(tones['coat'])
    hx, hy = stage.at(*head_pos)
    head_piece.disc(hx, hy, spec.head * stage.scale, 3)
    stage.stamp(head_piece, rim=0.9, occlude=0.55)
    _ears(stage, spec, tones, head_pos, m, facing or 1, side)
    _muzzle(stage, spec, tones, head_pos, facing or 1, side, m)
    _horns(stage, spec, tones, head_pos, m, facing or 1, side)
    _eye(stage, spec, tones, head_pos, facing or 1, side, m)


def bird(spec, m, direction, stage):
    tones = spec.ramps()
    side = direction in (1, 2)
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    collapse = m.collapse
    body_y = spec.leg * (1 - collapse * 0.85) + m.bob - m.crouch * 0.4
    for index, offset in enumerate((0.0, 0.5)):
        dx, lift = _gait(m, offset, 2.6, 1.8)
        near = index == 1
        foot = (dx + (0.8 if near else -0.8) + collapse * (5 if near else 3), lift)
        knee = (dx * 0.4 + (0.6 if near else -0.6), body_y * 0.45)
        stage.limb(tones['accent'], (0.0, body_y - spec.girth * 0.4), knee, 2.2, 1.8, rim=0.6)
        stage.limb(tones['accent'], knee, foot, 1.8, 1.5, rim=0.6)
        claw = stage.piece(tones['claw'])
        x, y = stage.at(*foot)
        claw.line([(x - 2.4 * stage.scale, y), (x + 2.8 * stage.scale, y)], 3, max(1, round(stage.scale)))
        claw.line([(x, y - 1.6 * stage.scale), (x + 2.0 * stage.scale, y)], 3, max(1, round(stage.scale)))
        stage.stamp(claw, outline=False, rim=0, occlude=0)
    tilt = 0.0 if not collapse else collapse * 3.0
    body = stage.piece(tones['coat'])
    length = spec.length * 0.5
    body.poly(catmull(stage.path([
        (-length * 0.9 * (facing or 1), body_y + spec.girth * 0.2 - tilt),
        (-length * 0.2 * (facing or 1), body_y + spec.girth * 1.0 - tilt),
        (length * 0.7 * (facing or 1), body_y + spec.girth * 0.7 - tilt),
        (length * 0.85 * (facing or 1), body_y - spec.girth * 0.4 - tilt),
        (0.0, body_y - spec.girth * 1.05 - tilt),
        (-length * 0.8 * (facing or 1), body_y - spec.girth * 0.5 - tilt),
    ]), 6, closed=True), 3)
    stage.stamp(body, rim=0.9, occlude=0.6)
    wing = stage.piece(tones['accent'])
    flap = math.sin(m.phase) * 1.2 * (1 if m.stride else 0.3) + m.charge * 3.0
    for sign in ((1,) if side else (-1, 1)):
        base = (sign * (length * 0.1 if not side else 0.1) * (facing or 1), body_y + spec.girth * 0.5 - tilt)
        wing.poly(catmull(stage.path([
            (base[0] - length * 0.5 * (facing or 1) * (1 if side else sign),
             base[1] + 0.4 + flap * 0.4),
            (base[0] + length * 0.35 * (facing or 1) * (1 if side else sign), base[1] + 1.4 + flap),
            (base[0] + length * 0.15 * (facing or 1) * (1 if side else sign), base[1] - spec.girth * 1.2),
            (base[0] - length * 0.62 * (facing or 1) * (1 if side else sign), base[1] - spec.girth * 0.7),
        ]), 5, closed=True), 3)
    stage.stamp(wing, rim=0.8, occlude=0.55)
    tail = stage.piece(tones['accent'])
    tail.poly(catmull(stage.path([
        (-length * 0.85 * (facing or 1), body_y + spec.girth * 0.3 - tilt),
        (-length * 1.7 * (facing or 1), body_y + spec.girth * 0.8 - tilt),
        (-length * 1.8 * (facing or 1), body_y - spec.girth * 0.5 - tilt),
        (-length * 0.8 * (facing or 1), body_y - spec.girth * 0.4 - tilt),
    ]), 5, closed=True), 3)
    stage.stamp(tail, rim=0.7, occlude=0.5)
    neck_top = body_y + spec.girth * 1.0 + spec.neck * (1 - collapse) - tilt
    head_pos = (length * 0.5 * (facing or 1) + (0 if not collapse else facing * 4), neck_top)
    stage.limb(tones['coat'], (length * 0.35 * (facing or 1), body_y + spec.girth * 0.6 - tilt), head_pos,
               spec.girth * 0.62, spec.girth * 0.46, rim=0.8)
    head = stage.piece(tones['coat'])
    hx, hy = stage.at(*head_pos)
    head.disc(hx, hy, spec.head * stage.scale, 3)
    stage.stamp(head, rim=0.9, occlude=0.5)
    if spec.ear == 'tuft':
        _ears(stage, spec, tones, head_pos, m, facing or 1, side)
    beak = stage.piece(tones['horn'])
    if side or facing:
        tip = (head_pos[0] + (facing or 1) * (spec.head + spec.muzzle), head_pos[1] - 0.4 - m.mouth * 1.2)
        beak.poly(catmull(stage.path([
            (head_pos[0] + (facing or 1) * spec.head * 0.4, head_pos[1] + spec.head * 0.42),
            tip, (head_pos[0] + (facing or 1) * spec.head * 0.4, head_pos[1] - spec.head * 0.5)]), 4, closed=True), 3)
    else:
        beak.poly(stage.path([
            (head_pos[0] - spec.head * 0.42, head_pos[1] - spec.head * 0.2),
            (head_pos[0] + spec.head * 0.42, head_pos[1] - spec.head * 0.2),
            (head_pos[0], head_pos[1] - spec.head - spec.muzzle * 0.6)]), 3)
    stage.stamp(beak, rim=0.9, occlude=0.5)
    _eye(stage, spec, tones, head_pos, facing or 1, side or bool(facing), m)


def insect(spec, m, direction, stage, arachnid=False):
    tones = spec.ramps()
    side = direction in (1, 2)
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    collapse = m.collapse
    # A spider carries its body between arched legs; sitting it on the ground
    # hides the legs and turns the sprite into a lump.
    body_y = spec.leg * (0.86 if arachnid else 0.62) * (1 - collapse * 0.8) + m.bob * 0.5
    count = max(3, spec.legs // 2)
    span = spec.length * 0.5
    for index in range(count):
        t = index / max(1, count - 1)
        anchor = (span * (0.6 - t * 1.2) * (facing or 1), body_y)
        for near in (False, True):
            dx, lift = _gait(m, (index * 0.33 + (0.5 if near else 0.0)) % 1.0, 2.2, 1.4)
            reach = spec.leg * (1.15 if near else 0.95) * (1.25 if arachnid else 1.0)
            out = (1 if near else -1)
            knee = (anchor[0] + dx * 0.5 + out * reach * 0.34,
                    body_y + reach * (0.52 if arachnid else 0.36) - collapse * body_y * 0.5)
            foot = (anchor[0] + dx + out * reach * 0.92 + collapse * out * 3.0, lift)
            tone = tones['coat'] if near else tones['far']
            stage.limb(tone, anchor, knee, 1.9, 1.5, rim=0.6 if near else 0.3)
            stage.limb(tone, knee, foot, 1.5, 1.1, rim=0.6 if near else 0.3)
    body = stage.piece(tones['coat'])
    segments = max(2, spec.segments or (2 if arachnid else 3))
    for index in range(segments):
        t = index / max(1, segments - 1)
        cx = span * (0.65 - t * 1.35) * (facing or 1)
        radius = spec.girth * (0.72 + 0.35 * math.sin(t * math.pi))
        x, y = stage.at(cx, body_y + spec.girth * 0.25)
        body.disc(x, y, radius * stage.scale, 3)
    stage.stamp(body, rim=0.9, occlude=0.65)
    if spec.back == 'shell':
        shell = stage.piece(tones['accent'])
        shell.poly(catmull(stage.path([
            (span * 0.5 * (facing or 1), body_y + spec.girth * 0.5),
            (0.0, body_y + spec.girth * 1.35),
            (-span * 0.85 * (facing or 1), body_y + spec.girth * 0.4),
            (-span * 0.5 * (facing or 1), body_y - spec.girth * 0.2),
            (span * 0.4 * (facing or 1), body_y - spec.girth * 0.1),
        ]), 6, closed=True), 3)
        stage.stamp(shell, rim=0.9, occlude=0.6)
        split = stage.piece(tones['coat'])
        split.line(stage.path([(span * 0.45 * (facing or 1), body_y + spec.girth * 0.6),
                               (-span * 0.7 * (facing or 1), body_y + spec.girth * 0.5)]), 1, 1)
        split.clip(shell)
        stage.sketch.overlay(split)
    if spec.wings:
        wing = stage.piece(tones['accent'])
        flap = math.sin(m.phase * 2) * 1.6 + m.charge * 2.0
        for sign in ((1,) if side else (-1, 1)):
            wing.poly(catmull(stage.path([
                (span * 0.2 * (facing or 1), body_y + spec.girth * 0.9),
                (span * 0.5 * sign * (facing or 1), body_y + spec.girth * 2.2 + flap),
                (-span * 0.5 * sign * (facing or 1), body_y + spec.girth * 1.9 + flap * 0.6),
                (-span * 0.3 * (facing or 1), body_y + spec.girth * 0.7),
            ]), 6, closed=True), 3)
        wing.image.putalpha(wing.image.getchannel('A').point(lambda v: round(v * 0.78)))
        stage.stamp(wing, rim=0.6, occlude=0.3)
    head_pos = (span * 0.86 * (facing or 1), body_y + spec.girth * 0.45)
    head = stage.piece(tones['coat'])
    hx, hy = stage.at(*head_pos)
    head.disc(hx, hy, spec.head * stage.scale, 3)
    stage.stamp(head, rim=0.9, occlude=0.5)
    feelers = stage.piece(tones['accent'])
    for sign in (-1, 1):
        feelers.line(catmull(stage.path([
            head_pos,
            (head_pos[0] + (facing or 1) * 2.2, head_pos[1] + spec.head * 1.1 + sign * 0.6),
            (head_pos[0] + (facing or 1) * 5.4, head_pos[1] + spec.head * 1.6 + sign * 2.0)]), 5), 3,
            max(1, round(stage.scale)))
    if arachnid:
        for sign in (-1, 1):
            feelers.poly(stage.path([
                (head_pos[0] + (facing or 1) * spec.head * 0.5, head_pos[1] + sign * 0.6),
                (head_pos[0] + (facing or 1) * (spec.head + 2.6), head_pos[1] + sign * 1.6 - 1.0),
                (head_pos[0] + (facing or 1) * (spec.head + 0.6), head_pos[1] + sign * 0.4 - 1.4)]), 3)
    stage.stamp(feelers, rim=0.6, occlude=0.4)
    _eye(stage, spec, tones, head_pos, facing or 1, side, m)


def serpent(spec, m, direction, stage):
    tones = spec.ramps()
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    facing = facing or 1
    collapse = m.collapse
    coil = spec.length
    rise = spec.height * (1 - collapse * 0.9) + m.rear * 2.5 + m.bob
    sway = math.sin(m.phase) * 1.6
    path = [
        (-coil * 0.34 * facing, 1.2),
        (-coil * 0.10 * facing, 2.6 + sway * 0.3),
        (coil * 0.12 * facing, 1.6),
        (coil * 0.02 * facing + sway, rise * 0.45),
        (-coil * 0.06 * facing + sway * 0.6, rise * 0.78),
        (coil * 0.10 * facing + sway * 0.4, rise),
    ]
    piece = stage.piece(tones['coat'])
    points = catmull(stage.path(path), 8)
    piece.line(points, 3, max(2, round(spec.girth * 1.5 * stage.scale)))
    coil_base = stage.piece(tones['coat'])
    x, y = stage.at(-coil * 0.1 * facing, 1.8)
    coil_base.ellipse((x - coil * 0.42 * stage.scale, y - 2.6 * stage.scale,
                       x + coil * 0.42 * stage.scale, y + 2.4 * stage.scale), 3)
    stage.stamp(coil_base, rim=0.8, occlude=0.6)
    stage.stamp(piece, rim=0.85, occlude=0.55)
    bands = stage.piece(tones['accent'])
    for index in range(6):
        t = 0.12 + index * 0.14
        px = int(t * (len(points) - 1))
        bands.disc(points[px][0], points[px][1], max(1.0, 1.6 * stage.scale), 3)
    bands.clip(piece)
    stage.sketch.overlay(bands)
    head_pos = (path[-1][0] + facing * 1.6, path[-1][1] + 0.6)
    head = stage.piece(tones['coat'])
    hx, hy = stage.at(*head_pos)
    head.ellipse((hx - spec.head * 1.25 * stage.scale, hy - spec.head * 0.85 * stage.scale,
                  hx + spec.head * 1.25 * stage.scale, hy + spec.head * 0.85 * stage.scale), 3)
    stage.stamp(head, rim=0.9, occlude=0.5)
    if spec.horn:
        _horns(stage, spec, tones, head_pos, m, facing, True)
    jaw = stage.piece(ramp('#5c3038'))
    if m.mouth > 0.2:
        a = stage.at(head_pos[0] + facing * spec.head * 0.2, head_pos[1] - 0.4)
        b = stage.at(head_pos[0] + facing * (spec.head * 1.3 + 1.4), head_pos[1] - 1.4 - m.mouth * 2.0)
        jaw.poly([a, b, (b[0], b[1] + 3.0 * stage.scale), (a[0], a[1] + 1.4 * stage.scale)], 3)
        stage.stamp(jaw, rim=0.3, occlude=0.3)
        fang = stage.piece(tones['horn'])
        fang.poly([(b[0] - 1.4 * stage.scale, b[1] + 0.6 * stage.scale), (b[0] + 0.6 * stage.scale, b[1] + 3.0 * stage.scale),
                   (b[0] - 2.6 * stage.scale, b[1] + 1.0 * stage.scale)], 4)
        stage.stamp(fang, outline=False, rim=0, occlude=0)
    tongue = stage.piece(ramp('#b8515e'))
    tongue.line(stage.path([(head_pos[0] + facing * spec.head * 1.2, head_pos[1] - 0.8),
                            (head_pos[0] + facing * (spec.head * 1.2 + 3.4), head_pos[1] - 1.6)]), 3,
                max(1, round(stage.scale)))
    stage.stamp(tongue, outline=False, rim=0, occlude=0)
    _eye(stage, spec, tones, head_pos, facing, True, m)


def worm(spec, m, direction, stage):
    tones = spec.ramps()
    facing = (1 if direction == 2 else (-1 if direction == 1 else 1))
    collapse = m.collapse
    rise = spec.height * (1 - collapse * 0.85) + m.rear * 2.0
    segments = max(4, spec.segments)
    piece = stage.piece(tones['coat'])
    centres = []
    for index in range(segments):
        t = index / (segments - 1)
        wave = math.sin(m.phase + t * 3.2) * (1.2 if m.stride else 0.5)
        cx = (-spec.length * 0.5 + spec.length * t) * facing
        cy = 1.6 + wave + rise * (t ** 2.2)
        radius = spec.girth * (1.05 - 0.42 * t)
        centres.append((cx, cy, radius))
        x, y = stage.at(cx, cy)
        piece.disc(x, y, radius * stage.scale, 3)
    stage.stamp(piece, rim=0.85, occlude=0.6)
    rings = stage.piece(tones['accent'])
    for cx, cy, radius in centres[1:-1]:
        x, y = stage.at(cx, cy)
        rings.line([(x - radius * stage.scale, y - radius * 0.5 * stage.scale),
                    (x - radius * stage.scale, y + radius * 0.6 * stage.scale)], 1, 1)
    rings.clip(piece)
    stage.sketch.overlay(rings)
    if spec.legs > 4:
        legs = stage.piece(tones['accent'])
        for index, (cx, cy, radius) in enumerate(centres):
            dx, lift = _gait(m, (index * 0.3) % 1.0, 1.6, 1.0)
            for sign in (-1, 1):
                legs.line(stage.path([(cx, cy - radius * 0.4),
                                      (cx + dx + sign * radius * 1.5, max(0.4, cy - radius * 1.7 + lift))]), 3,
                          max(1, round(stage.scale)))
        stage.stamp(legs, rim=0.5, occlude=0.4)
    if spec.back == 'shell':
        shell = stage.piece(tones['accent'])
        x, y = stage.at(-spec.length * 0.1 * facing, rise * 0.4 + spec.girth * 1.4)
        radius = spec.girth * 2.0 * stage.scale
        shell.disc(x, y, radius, 3)
        stage.stamp(shell, rim=0.9, occlude=0.6)
        swirl = stage.piece(tones['coat'])
        for step in range(3):
            r = radius * (0.72 - step * 0.22)
            swirl.arc((x - r, y - r, x + r, y + r), 20 + step * 90, 300 + step * 90, 1, 1)
        swirl.clip(shell)
        stage.sketch.overlay(swirl)
    head_pos = (centres[-1][0] + facing * spec.girth * 0.6, centres[-1][1] + 0.6)
    head = stage.piece(tones['coat'])
    hx, hy = stage.at(*head_pos)
    head.disc(hx, hy, spec.head * stage.scale, 3)
    stage.stamp(head, rim=0.9, occlude=0.5)
    maw = stage.piece(ramp('#6a3038'))
    mx, my = stage.at(head_pos[0] + facing * spec.head * 0.5, head_pos[1])
    maw.disc(mx, my, spec.head * (0.36 + m.mouth * 0.30) * stage.scale, 3)
    stage.stamp(maw, rim=0.2, occlude=0.3)
    _eye(stage, spec, tones, head_pos, facing, True, m)


def crustacean(spec, m, direction, stage):
    """Crabs and scorpions read the same from every angle: a low wide carapace,
    splayed walking legs, claws held forward and eyes up on stalks."""
    tones = spec.ramps()
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    collapse = m.collapse
    girth = spec.girth
    body_y = spec.leg * 0.62 * (1 - collapse * 0.7) + m.bob * 0.4
    scuttle = math.sin(m.phase) * (1.4 if m.stride else 0.3)

    for pair in range(3):
        reach = girth * (1.25 + pair * 0.30)
        for sign in (-1, 1):
            dx, lift = _gait(m, (pair * 0.28 + (0.5 if sign > 0 else 0.0)) % 1.0, 1.6, 1.1)
            anchor = (sign * girth * 0.55, body_y - girth * 0.15)
            knee = (sign * (reach * 0.72) + dx * 0.4, body_y + girth * 0.30)
            foot = (sign * (reach + collapse * 2.4) + dx, lift)
            tone = tones['coat'] if sign > 0 else tones['far']
            stage.limb(tone, anchor, knee, 1.9, 1.5, rim=0.6 if sign > 0 else 0.3)
            stage.limb(tone, knee, foot, 1.5, 1.1, rim=0.6 if sign > 0 else 0.3)

    if spec.tail == 'sting':
        segments = []
        for step in range(5):
            t = step / 4.0
            segments.append((-girth * (0.6 + t * 0.5) + scuttle * 0.4,
                             body_y + girth * (0.6 + t * 1.5) - t * t * girth * 0.5))
        stinger = stage.piece(tones['coat'])
        for index, (sx, sy) in enumerate(segments):
            x, y = stage.at(sx, sy)
            stinger.disc(x, y, (girth * 0.34 - index * 0.16) * stage.scale + 0.8, 3)
        stage.stamp(stinger, rim=0.8, occlude=0.5)
        barb = stage.piece(tones['claw'])
        bx, by = stage.at(segments[-1][0] - 1.2, segments[-1][1] - 1.4)
        barb.poly([(bx - 1.8 * stage.scale, by - 1.8 * stage.scale), (bx + 1.4 * stage.scale, by - 2.2 * stage.scale),
                   (bx - 0.4 * stage.scale, by + 2.6 * stage.scale)], 3)
        stage.stamp(barb, rim=0.9, occlude=0.5)

    body = stage.piece(tones['coat'])
    if spec.back == 'shell':
        sx, sy = stage.at(0.0, body_y + girth * 0.55)
        body.disc(sx, sy, girth * 1.35 * stage.scale, 3)
    else:
        body.poly(catmull(stage.path([
            (-girth * 1.45, body_y + girth * 0.10),
            (-girth * 0.95, body_y + girth * 0.85),
            (0.0, body_y + girth * 1.00),
            (girth * 0.95, body_y + girth * 0.85),
            (girth * 1.45, body_y + girth * 0.10),
            (girth * 0.85, body_y - girth * 0.55),
            (-girth * 0.85, body_y - girth * 0.55),
        ]), 6, closed=True), 3)
    stage.stamp(body, rim=0.9, occlude=0.65)
    shellwork = stage.piece(tones['accent'])
    if spec.back == 'shell':
        sx, sy = stage.at(0.0, body_y + girth * 0.55)
        for step in range(3):
            r = girth * (1.05 - step * 0.30) * stage.scale
            shellwork.arc((sx - r, sy - r, sx + r, sy + r), 25 + step * 80, 300 + step * 80, 3, 1)
    else:
        shellwork.line(catmull(stage.path([(-girth * 1.1, body_y + girth * 0.42),
                                           (0.0, body_y + girth * 0.66),
                                           (girth * 1.1, body_y + girth * 0.42)]), 5), 5, 1)
        for sign in (-1, 1):
            shellwork.line(stage.path([(sign * girth * 0.45, body_y + girth * 0.55),
                                       (sign * girth * 0.60, body_y - girth * 0.30)]), 1, 1)
    shellwork.clip(body)
    stage.sketch.overlay(shellwork)

    open_amount = 0.35 + m.mouth * 0.9
    for sign in (-1, 1):
        lead = 1.0 if sign * (facing or 1) > 0 else 0.82
        shoulder = (sign * girth * 0.85, body_y + girth * 0.25)
        elbow = (sign * (girth * 1.55) * lead + m.lunge * 0.3, body_y + girth * 0.55)
        tone = tones['coat'] if sign > 0 else tones['far']
        stage.limb(tone, shoulder, elbow, 2.8, 2.4, rim=0.7 if sign > 0 else 0.4)
        claw = stage.piece(tone)
        cx, cy = stage.at(sign * (girth * 2.15) * lead + m.lunge * 0.4, body_y + girth * 0.72)
        size = girth * 0.85 * stage.scale
        claw.poly(catmull([(cx - size * sign * 0.7, cy + size * 0.5), (cx - size * sign * 0.2, cy - size * 0.85),
                           (cx + size * sign * 0.9, cy - size * (0.30 + open_amount * 0.45)),
                           (cx + size * sign * 0.5, cy + size * 0.12)], 5, closed=True), 3)
        claw.poly(catmull([(cx - size * sign * 0.55, cy + size * 0.55), (cx + size * sign * 0.85, cy + size * (0.45 + open_amount * 0.5)),
                           (cx + size * sign * 0.15, cy + size * 0.95)], 4, closed=True), 2)
        stage.stamp(claw, rim=0.9, occlude=0.55)

    stalks = stage.piece(tones['coat'])
    for sign in (-1, 1):
        stalks.line(stage.path([(sign * girth * 0.38, body_y + girth * 0.80),
                                (sign * girth * 0.45, body_y + girth * 1.45)]), 3,
                    max(1, round(1.4 * stage.scale)))
    stage.stamp(stalks, rim=0.6, occlude=0.4)
    eyes = stage.piece(ramp(spec.eye))
    for sign in (-1, 1):
        ex, ey = stage.at(sign * girth * 0.45, body_y + girth * 1.55)
        eyes.disc(ex, ey, max(1.0, 1.4 * stage.scale), 4)
        eyes.dot(ex, ey, (28, 24, 30, 255))
    stage.stamp(eyes, rim=0.8, occlude=0.4)



def spirit(spec, m, direction, stage):
    tones = spec.ramps()
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    drift = math.sin(m.phase) * 1.2
    lift = spec.height * 0.42 + drift + m.bob - m.collapse * spec.height * 0.5
    body = stage.piece(tones['coat'])
    tail_wave = math.sin(m.phase + 1.2) * 2.0
    body.poly(catmull(stage.path([
        (-spec.girth, lift), (-spec.girth * 0.7, lift + spec.height * 0.55),
        (0.0, lift + spec.height * 0.72), (spec.girth * 0.7, lift + spec.height * 0.55),
        (spec.girth, lift), (spec.girth * 0.6 + tail_wave * 0.3, lift - spec.height * 0.42),
        (tail_wave, lift - spec.height * 0.62), (-spec.girth * 0.6 + tail_wave * 0.4, lift - spec.height * 0.38),
    ]), 7, closed=True), 3)
    body.image.putalpha(body.image.getchannel('A').point(lambda v: round(v * 0.86)))
    stage.stamp(body, rim=0.7, occlude=0.4)
    hood = stage.piece(tones['accent'])
    hood.poly(catmull(stage.path([
        (-spec.girth * 0.86, lift + spec.height * 0.30), (0.0, lift + spec.height * 0.80),
        (spec.girth * 0.86, lift + spec.height * 0.30), (spec.girth * 0.5, lift + spec.height * 0.36),
        (0.0, lift + spec.height * 0.55), (-spec.girth * 0.5, lift + spec.height * 0.36),
    ]), 6, closed=True), 3)
    stage.stamp(hood, rim=0.7, occlude=0.4)
    for sign in ((facing or 1,) if facing else (-1, 1)):
        arm = stage.piece(tones['coat'])
        reach = 1.0 + m.charge * 2.2 + m.mouth
        arm.line(catmull(stage.path([
            (sign * spec.girth * 0.5, lift + spec.height * 0.34),
            (sign * (spec.girth * 0.9 + reach), lift + spec.height * 0.1),
            (sign * (spec.girth * 1.1 + reach * 1.6), lift + spec.height * 0.28 + m.charge * 2.0)]), 5), 3,
            max(1, round(2.2 * stage.scale)))
        arm.image.putalpha(arm.image.getchannel('A').point(lambda v: round(v * 0.9)))
        stage.stamp(arm, rim=0.6, occlude=0.3)
    eyes = stage.piece(ramp(spec.glow or spec.eye))
    for sign in ((-1, 1) if not facing else (facing * 0.4, facing * 1.0)):
        x, y = stage.at(sign * spec.girth * 0.42, lift + spec.height * 0.52)
        eyes.disc(x, y, max(1.0, 1.5 * stage.scale), 5)
    stage.stamp(eyes, outline=False, rim=0, occlude=0)
    stage.sketch.glow(spec.glow or spec.coat, 3, 0.5)


def construct(spec, m, direction, stage):
    tones = spec.ramps()
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    collapse = m.collapse
    stand = spec.height * (1 - collapse * 0.62) + m.bob * 0.4 - m.crouch
    girth = spec.girth
    for index, sign in enumerate((-1, 1)):
        dx, lift = _gait(m, index * 0.5, 3.0, 1.6)
        hip = (sign * girth * 0.5, stand * 0.44)
        foot = (sign * girth * 0.62 + dx + collapse * sign * 4.0, lift)
        stage.limb(tones['coat'] if sign > 0 else tones['far'], hip, foot, girth * 0.55, girth * 0.44,
                   rim=0.7 if sign > 0 else 0.35)
        block = stage.piece(tones['accent'])
        x, y = stage.at(*foot)
        block.poly([(x - girth * 0.45 * stage.scale, y - girth * 0.34 * stage.scale),
                    (x + girth * 0.5 * stage.scale, y - girth * 0.34 * stage.scale),
                    (x + girth * 0.45 * stage.scale, y), (x - girth * 0.42 * stage.scale, y)], 3)
        stage.stamp(block, rim=0.7, occlude=0.5)
    torso = stage.piece(tones['coat'])
    top = stand + girth * 0.5
    torso.poly(catmull(stage.path([
        (-girth * 0.92, stand * 0.42), (-girth * 1.05, top), (0.0, top + girth * 0.22),
        (girth * 1.05, top), (girth * 0.92, stand * 0.42), (0.0, stand * 0.30),
    ]), 5, closed=True), 3)
    stage.stamp(torso, rim=0.9, occlude=0.7)
    seam = stage.piece(tones['accent'])
    seam.line(stage.path([(0.0, stand * 0.36), (0.0, top)]), 1, 1)
    seam.line(stage.path([(-girth * 0.8, stand * 0.78), (girth * 0.8, stand * 0.78)]), 1, 1)
    seam.clip(torso)
    stage.sketch.overlay(seam)
    core = stage.piece(ramp(spec.glow or spec.accent or '#c9b06a'))
    x, y = stage.at(0.0, stand * 0.82)
    core.poly([(x, y - 3.0 * stage.scale), (x + 2.4 * stage.scale, y), (x, y + 3.0 * stage.scale),
               (x - 2.4 * stage.scale, y)], 4)
    stage.stamp(core, rim=0.9, occlude=0.4)
    for sign in (-1, 1):
        swing = math.sin(m.phase + (0 if sign > 0 else math.pi)) * (1.6 if m.stride else 0.4)
        shoulder = (sign * girth * 1.0, top - girth * 0.2)
        hand = (sign * (girth * 1.25) + swing + m.lunge * (0.6 if sign * (facing or 1) > 0 else 0),
                stand * 0.30 + m.charge * girth * 1.6)
        stage.limb(tones['coat'] if sign > 0 else tones['far'], shoulder, hand, girth * 0.5, girth * 0.42,
                   rim=0.7 if sign > 0 else 0.35)
        fist = stage.piece(tones['coat'] if sign > 0 else tones['far'])
        fx, fy = stage.at(*hand)
        fist.disc(fx, fy, girth * 0.34 * stage.scale, 3)
        stage.stamp(fist, rim=0.8, occlude=0.5)
    head_pos = (0.0, top + girth * 0.85 - collapse * girth)
    head = stage.piece(tones['coat'])
    hx, hy = stage.at(*head_pos)
    size = girth * 0.62 * stage.scale
    head.poly(catmull([(hx - size, hy - size * 0.8), (hx, hy - size * 1.15), (hx + size, hy - size * 0.8),
                       (hx + size * 0.8, hy + size * 0.9), (hx - size * 0.8, hy + size * 0.9)], 5, closed=True), 3)
    stage.stamp(head, rim=0.9, occlude=0.6)
    if spec.wings:
        wing = stage.piece(tones['accent'])
        for sign in (-1, 1):
            wing.poly(catmull(stage.path([
                (sign * girth * 0.7, top), (sign * girth * 2.3, top + girth * 1.3),
                (sign * girth * 2.6, top - girth * 0.7), (sign * girth * 1.1, stand * 0.5)]), 5, closed=True), 3)
        stage.sketch.under(wing.bake(outline=True, rim=0.6, occlude=0.5))
    glow = ramp(spec.glow or '#e8cf5e')
    eyes = stage.piece(glow)
    for sign in ((-1, 1) if not facing else (facing * 0.3, facing * 0.9)):
        ex, ey = stage.at(head_pos[0] + sign * girth * 0.3, head_pos[1] + girth * 0.1)
        eyes.disc(ex, ey, max(0.9, 1.2 * stage.scale), 5)
    stage.stamp(eyes, outline=False, rim=0, occlude=0)
    if spec.glow:
        stage.sketch.glow(spec.glow, 2, 0.32)


def elemental(spec, m, direction, stage):
    tones = spec.ramps()
    glow = ramp(spec.glow or spec.coat)
    lift = spec.height * 0.3 + math.sin(m.phase) * 1.0 + m.bob - m.collapse * spec.height * 0.55
    core = stage.piece(glow)
    height = spec.height * (1 - m.collapse * 0.5)
    swirl = math.sin(m.phase * 1.5)
    core.poly(catmull(stage.path([
        (-spec.girth, lift), (-spec.girth * 0.6 + swirl, lift + height * 0.5),
        (-spec.girth * 0.2, lift + height * 0.95), (spec.girth * 0.45 + swirl * 0.6, lift + height * 0.7),
        (spec.girth * 0.9, lift + height * 0.3), (spec.girth * 0.55, lift - height * 0.1),
        (0.0, lift - height * 0.18),
    ]), 7, closed=True), 3)
    stage.stamp(core, rim=0.8, occlude=0.4)
    inner = stage.piece(glow)
    inner.poly(catmull(stage.path([
        (-spec.girth * 0.45, lift + height * 0.15), (0.0, lift + height * 0.72),
        (spec.girth * 0.45, lift + height * 0.2), (0.0, lift)]), 5, closed=True), 5)
    inner.clip(core)
    stage.sketch.overlay(inner)
    for index in range(3):
        mote = stage.piece(glow)
        angle = m.phase + index * 2.1
        x, y = stage.at(math.cos(angle) * spec.girth * 1.5, lift + height * 0.5 + math.sin(angle) * height * 0.35)
        mote.disc(x, y, max(0.9, (1.4 - index * 0.25) * stage.scale), 5)
        stage.stamp(mote, outline=False, rim=0, occlude=0)
    eyes = stage.piece(ramp('#fdf3d6'))
    for sign in (-1, 1):
        ex, ey = stage.at(sign * spec.girth * 0.35, lift + height * 0.62)
        eyes.disc(ex, ey, max(0.9, 1.2 * stage.scale), 5)
    stage.stamp(eyes, outline=False, rim=0, occlude=0)
    stage.sketch.glow(spec.glow or spec.coat, 3, 0.6)


def mineral(spec, m, direction, stage):
    tones = spec.ramps()
    glow = ramp(spec.glow or spec.accent or spec.coat)
    lift = 0.4 + m.bob * 0.5 - m.collapse * 1.6
    height = spec.height * (1 - m.collapse * 0.45)
    base = stage.piece(tones['coat'])
    base.poly(catmull(stage.path([
        (-spec.girth, lift), (-spec.girth * 0.7, lift + height * 0.45),
        (0.0, lift + height * 0.62), (spec.girth * 0.75, lift + height * 0.42),
        (spec.girth, lift)]), 5, closed=True), 3)
    stage.stamp(base, rim=0.9, occlude=0.7)
    for index, (dx, scale_) in enumerate(((-0.55, 0.7), (0.05, 1.0), (0.6, 0.62))):
        shard = stage.piece(glow)
        top = lift + height * (0.55 + 0.55 * scale_) + math.sin(m.phase + index) * 0.6 + m.charge * 2.0
        x0, y0 = stage.at(dx * spec.girth - 2.0 * scale_, lift + height * 0.3)
        x1, y1 = stage.at(dx * spec.girth + 2.2 * scale_, lift + height * 0.34)
        tx, ty = stage.at(dx * spec.girth + 0.4, top)
        shard.poly([(x0, y0), (tx, ty), (x1, y1)], 3)
        shard.poly([(x0 + (tx - x0) * 0.4, y0), (tx, ty), (tx, y0)], 5)
        stage.stamp(shard, rim=0.9, occlude=0.5)
    eyes = stage.piece(ramp('#fdf3d6'))
    for sign in (-1, 1):
        ex, ey = stage.at(sign * spec.girth * 0.32, lift + height * 0.34)
        eyes.disc(ex, ey, max(0.9, 1.1 * stage.scale), 5)
    stage.stamp(eyes, outline=False, rim=0, occlude=0)
    if spec.glow:
        stage.sketch.glow(spec.glow, 3, 0.45)


def plant(spec, m, direction, stage):
    tones = spec.ramps()
    sway = math.sin(m.phase) * 1.2 + m.lunge * 0.3
    collapse = m.collapse
    height = spec.height * (1 - collapse * 0.55)
    trunk = stage.piece(tones['coat'])
    trunk.poly(catmull(stage.path([
        (-spec.girth * 0.85, 0.4), (-spec.girth * 0.32, height * 0.55),
        (-spec.girth * 0.22 + sway, height), (spec.girth * 0.28 + sway, height),
        (spec.girth * 0.38, height * 0.5), (spec.girth * 0.9, 0.4),
    ]), 6, closed=True), 3)
    stage.stamp(trunk, rim=0.85, occlude=0.65)
    grain = stage.piece(tones['coat'])
    for sign in (-1, 1):
        grain.line(catmull(stage.path([(sign * spec.girth * 0.4, 1.6), (sign * spec.girth * 0.2, height * 0.6)]), 4), 1, 1)
    grain.clip(trunk)
    stage.sketch.overlay(grain)
    for sign in (-1, 1):
        stage.limb(tones['coat'], (sign * spec.girth * 0.4, height * 0.62),
                   (sign * (spec.girth * 1.5) + sway, height * 0.5 + m.mouth * 2.0), 2.4, 1.8, rim=0.7)
    crown = stage.piece(tones['accent'])
    if spec.archetype == 'plant' and spec.accent and 'fung' not in spec.coat:
        pass
    crown.poly(catmull(stage.path([
        (-spec.girth * 1.5 + sway, height * 0.86), (-spec.girth * 0.9 + sway, height * 1.5),
        (0.0 + sway, height * 1.72), (spec.girth * 0.95 + sway, height * 1.48),
        (spec.girth * 1.55 + sway, height * 0.86), (spec.girth * 0.7 + sway, height * 0.68),
        (-spec.girth * 0.7 + sway, height * 0.7),
    ]), 7, closed=True), 3)
    stage.stamp(crown, rim=0.9, occlude=0.6)
    eyes = stage.piece(ramp(spec.glow or '#e6d089'))
    for sign in (-1, 1):
        ex, ey = stage.at(sign * spec.girth * 0.3, height * 0.55)
        eyes.disc(ex, ey, max(0.9, 1.2 * stage.scale), 5)
    stage.stamp(eyes, outline=False, rim=0, occlude=0)
    if spec.glow:
        stage.sketch.glow(spec.glow, 2, 0.32)


def aquatic(spec, m, direction, stage):
    tones = spec.ramps()
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    swim = math.sin(m.phase) * 1.6
    lift = spec.height * 0.5 + swim * 0.5 + m.bob - m.collapse * spec.height * 0.42
    body = stage.piece(tones['coat'])
    length = spec.length * 0.5
    body.poly(catmull(stage.path([
        (-length * (facing or 1), lift + swim * 0.4),
        (-length * 0.3 * (facing or 1), lift + spec.girth * 0.95),
        (length * 0.75 * (facing or 1), lift + spec.girth * 0.4),
        (length * (facing or 1), lift - spec.girth * 0.1),
        (length * 0.6 * (facing or 1), lift - spec.girth * 0.85),
        (-length * 0.4 * (facing or 1), lift - spec.girth * 0.7),
    ]), 7, closed=True), 3)
    stage.stamp(body, rim=0.9, occlude=0.55)
    fin = stage.piece(tones['accent'])
    fin.poly(catmull(stage.path([
        (-length * 0.9 * (facing or 1), lift + spec.girth * 0.2),
        (-length * 1.8 * (facing or 1), lift + spec.girth * 1.1 + swim),
        (-length * 1.7 * (facing or 1), lift - spec.girth * 1.0 + swim),
    ]), 5, closed=True), 3)
    fin.poly(catmull(stage.path([
        (-length * 0.1 * (facing or 1), lift + spec.girth * 0.85),
        (length * 0.2 * (facing or 1), lift + spec.girth * 1.9),
        (length * 0.55 * (facing or 1), lift + spec.girth * 0.6),
    ]), 4, closed=True), 3)
    stage.stamp(fin, rim=0.8, occlude=0.5)
    if spec.tail == 'tentacle':
        arms = stage.piece(tones['coat'])
        for index in range(spec.legs or 6):
            offset = (index - 2.5) * 1.5
            arms.line(catmull(stage.path([
                (length * 0.6 * (facing or 1), lift - spec.girth * 0.5),
                (length * 0.9 * (facing or 1) + offset * 0.4, lift - spec.girth * 1.6 + math.sin(m.phase + index) * 1.2),
                (length * 1.0 * (facing or 1) + offset, max(0.4, lift - spec.girth * 2.8))]), 5), 3,
                max(1, round(1.6 * stage.scale)))
        stage.stamp(arms, rim=0.6, occlude=0.4)
    head_pos = (length * 0.72 * (facing or 1), lift + spec.girth * 0.15)
    _eye(stage, spec, tones, head_pos, facing or 1, True, m)
    if m.mouth > 0.2:
        mouth = stage.piece(ramp('#5c3038'))
        mx, my = stage.at(length * 0.95 * (facing or 1), lift - spec.girth * 0.15)
        mouth.disc(mx, my, (1.4 + m.mouth * 1.6) * stage.scale, 3)
        stage.stamp(mouth, rim=0.2, occlude=0.3)


def drake(spec, m, direction, stage):
    """Winged quadruped: the body plan is a quadruped plus membrane wings."""
    tones = spec.ramps()
    facing = 1 if direction == 2 else (-1 if direction == 1 else 0)
    wing = stage.piece(tones['accent'])
    flap = math.sin(m.phase) * 2.2 + m.charge * 3.0 + (1.4 if m.stride else 0)
    body_y = spec.height * (1 - m.collapse * 0.7) + m.bob
    span = spec.length * 0.5
    for sign in ((1,) if direction in (1, 2) else (-1, 1)):
        root = (-span * 0.1 * (facing or 1), body_y + spec.girth * 0.8)
        tip = (root[0] - span * 0.9 * (facing or 1) * (1 if direction in (1, 2) else sign),
               root[1] + spec.girth * 1.6 + flap)
        wing.poly(catmull(stage.path([
            root, (root[0] + span * 0.15 * (facing or 1), root[1] + spec.girth * 1.4 + flap * 0.8),
            tip, (tip[0] + span * 0.25 * (facing or 1), tip[1] - spec.girth * 1.5),
            (root[0] + span * 0.2 * (facing or 1), root[1] - spec.girth * 0.4),
        ]), 6, closed=True), 3)
        for rib in (0.3, 0.6):
            wing.line(stage.path([root, ((root[0] + (tip[0] - root[0]) * (0.6 + rib * 0.5)),
                                         root[1] + (tip[1] - root[1]) * (0.5 + rib * 0.4))]), 1, 1)
    stage.sketch.under(wing.bake(outline=True, rim=0.7, occlude=0.5))
    quadruped(spec, m, direction, stage)
    if spec.glow:
        stage.sketch.glow(spec.glow, 2, 0.3)


def mimic(spec, m, direction, stage):
    tones = spec.ramps()
    open_amount = 0.25 + m.mouth * 0.75
    height = spec.height * (1 - m.collapse * 0.5)
    girth = spec.girth
    base = stage.piece(tones['coat'])
    base.poly(stage.path([(-girth, 0.6), (girth, 0.6), (girth * 0.95, height * 0.62), (-girth * 0.95, height * 0.62)]), 3)
    stage.stamp(base, rim=0.85, occlude=0.7)
    bands = stage.piece(tones['accent'])
    for x in (-girth * 0.5, girth * 0.5):
        bands.line(stage.path([(x, 0.8), (x, height * 0.6)]), 3, max(1, round(1.6 * stage.scale)))
    bands.line(stage.path([(-girth, height * 0.30), (girth, height * 0.30)]), 3, max(1, round(1.6 * stage.scale)))
    stage.stamp(bands, rim=0.7, occlude=0.5)
    maw = stage.piece(ramp('#5c2a30'))
    maw.poly(stage.path([(-girth * 0.9, height * 0.6), (girth * 0.9, height * 0.6),
                         (girth * 0.8, height * (0.6 + open_amount * 0.5)),
                         (-girth * 0.8, height * (0.6 + open_amount * 0.5))]), 3)
    stage.stamp(maw, rim=0.3, occlude=0.4)
    teeth = stage.piece(ramp('#e4dcc2'))
    for index in range(5):
        x = -girth * 0.7 + index * girth * 0.35
        teeth.poly(stage.path([(x, height * 0.62), (x + girth * 0.15, height * 0.62),
                               (x + girth * 0.07, height * (0.62 + open_amount * 0.28))]), 3)
        teeth.poly(stage.path([(x, height * (0.6 + open_amount * 0.5)), (x + girth * 0.15, height * (0.6 + open_amount * 0.5)),
                               (x + girth * 0.07, height * (0.6 + open_amount * 0.24))]), 3)
    stage.stamp(teeth, outline=False, rim=0.5, occlude=0.3)
    lid = stage.piece(tones['coat'])
    top = height * (0.62 + open_amount * 0.55)
    lid.poly(stage.path([(-girth, top), (girth, top), (girth * 0.9, top + height * 0.32),
                         (-girth * 0.9, top + height * 0.32)]), 3)
    stage.stamp(lid, rim=0.85, occlude=0.6)
    lock = stage.piece(tones['accent'])
    lx, ly = stage.at(0.0, height * 0.5)
    lock.poly([(lx - 2.2 * stage.scale, ly - 2.6 * stage.scale), (lx + 2.2 * stage.scale, ly - 2.6 * stage.scale),
               (lx + 2.2 * stage.scale, ly + 1.4 * stage.scale), (lx - 2.2 * stage.scale, ly + 1.4 * stage.scale)], 3)
    stage.stamp(lock, rim=0.9, occlude=0.5)
    eyes = stage.piece(ramp(spec.eye))
    for sign in (-1, 1):
        ex, ey = stage.at(sign * girth * 0.45, top + height * 0.16)
        eyes.disc(ex, ey, max(0.9, 1.3 * stage.scale), 4)
        eyes.dot(ex, ey, (28, 24, 30, 255))
    stage.stamp(eyes, outline=False, rim=0, occlude=0)


def humanoid(spec, m, direction, stage, state, index):
    """Goblins, bandits and skeletons reuse the person rig at creature scale.

    The rig gives them a real gait and a real collapse; the hide colour and the
    build come from the creature, so a goblin is not a recoloured villager.
    """
    build = 0 if spec.height >= 16 else 1
    pose = rig.pose(build, state, index, direction)
    sketch = Sketch(64)
    hide = pigment.hexstr(spec.coat)
    cloth = spec.accent or '#5f5346'
    trunk = pigment.hexstr(blend(pigment.rgb(cloth), (30, 26, 32, 255), 0.35))
    folk.body_layers(sketch, pose, 2, cloth=cloth, trunk=trunk, shoe='#43382e', face=True)
    frame_image = _reskin(sketch.result(), hide)
    grow = spec.height / 16.0
    if grow < 0.95 or grow > 1.05 or stage.size != 64:
        target = max(16, min(stage.size, round(64 * grow * stage.scale)))
        frame_image = frame_image.resize((target, target), Image.Resampling.NEAREST)
    x = round(stage.cx - frame_image.width / 2 + 0.5)
    y = round(stage.ground - frame_image.height * 0.86)
    stage.sketch.overlay(frame_image, (x, y))
    if m.flash == 0 and spec.glow:
        stage.sketch.glow(spec.glow, 2, 0.3)


_SKIN_KEYS = None


def _reskin(image, hide):
    """Repaint the person's skin ramp with the creature's hide, leaving cloth alone."""
    global _SKIN_KEYS
    if _SKIN_KEYS is None:
        _SKIN_KEYS = {}
        for tone in pigment.SKIN:
            source = ramp(tone)
            for index, stop in enumerate(source.stops):
                _SKIN_KEYS[stop[:3]] = index
            _SKIN_KEYS[source.line[:3]] = -1
    target = ramp(hide)
    lookup = {}
    for key, index in _SKIN_KEYS.items():
        lookup[key] = target.line[:3] if index < 0 else target[index][:3]
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            swap = lookup.get((r, g, b))
            if swap is not None:
                pixels[x, y] = (swap[0], swap[1], swap[2], a)
    return image


ARCHETYPES = {
    'quadruped': quadruped, 'bird': bird, 'insect': insect, 'serpent': serpent, 'worm': worm,
    'crustacean': crustacean, 'spirit': spirit, 'construct': construct, 'elemental': elemental,
    'mineral': mineral, 'plant': plant, 'aquatic': aquatic, 'drake': drake, 'mimic': mimic,
}


def frame(mob, state, index, direction):
    """One creature frame, sized 64 for regular mobs and 128 for bosses."""
    spec = describe(mob)
    size = 128 if mob.get('boss') else 64
    stage = Stage(size, 2.0 if size == 128 else 1.0)
    m = motion(state, index)
    kind = spec.archetype
    if kind == 'humanoid':
        humanoid(spec, m, direction, stage, state, index)
    elif kind in ('arachnid',):
        insect(spec, m, direction, stage, arachnid=True)
    elif kind in ('amphibian', 'primate'):
        quadruped(spec, m, direction, stage)
    else:
        ARCHETYPES.get(kind, quadruped)(spec, m, direction, stage)
    if m.flash:
        stage.sketch.tone((255, 236, 206, 255), 0.4 * m.flash)
    if m.fade < 1.0:
        stage.sketch.fade(m.fade)
    return stage.sketch.result()
