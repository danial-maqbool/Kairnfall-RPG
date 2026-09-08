# Atelier — an independent art library for Kairnfall

A second, complete art pack: every sprite, tile, icon and sound the game
catalogue asks for, drawn by its own generators with its own palette system and
its own animation rig.

This directory is self-contained. It reads `content/catalog.json` and writes
only inside `atelier/`. It does not import, modify, extend or replace anything
under `client/Assets`, `tools/art` or `content_src`; both packs can sit in the
repository at the same time without touching each other.

## Build

```bash
python atelier/build.py                      # everything, ~4 min on 12 workers
python atelier/build.py --list               # counts per group
python atelier/build.py --only items mobs    # rebuild part of the library
python atelier/build.py --jobs 1             # single process
python atelier/build.py --manifest           # reindex what is on disk
```

Output lands in `atelier/Assets/`, alongside `manifest.json` (every key with its
size, animation flag and SHA-256) and `CREDITS.txt`. `atelier/coverage.json`
records what the last build produced.

## What it contains

| Group | Count | Size | Notes |
| --- | --- | --- | --- |
| terrain | 52 | 32×32 | 13 ground types, 4 seamless variants each |
| props | 23 | 48×64 – 112×144 | trees, rocks, flora, signage, loot, shadow |
| buildings | 164 | width×(height+2) tiles | 9 styles, one sprite per zone building |
| resources | 41 | 48×48 – 112×144 | gathering nodes by skill and material |
| chests | 14 | 48×48 | 7 kinds, closed and open |
| items | 1354 | 32×32 | every catalogue item |
| structures | 5 | 64×72 | placed crafting stations |
| abilities | 132 | 32×32 | element motif + kind badge |
| skills | 60 | 32×32 | one bespoke icon per skill |
| people | 60 | 512×1536 | 2 builds × 6 skin tones, 6 hair styles × 8 colours |
| equipment | 966 | 512×1536 | every equippable item as a worn layer |
| npcs | 26 | 512×1536 | one per townsfolk role, with their tool |
| mobs | 145 | 512×1536 / 1024×3072 | bosses are double size |
| gear | 616 | 32×32 | the tiered equipment ladder, as icons |
| gear_worn | 616 | 512×1536 | the same gear, worn, as animation sheets |
| audio | 22 | mono 22 050 Hz | 10 music beds, 4 ambiences, 8 effects |

4274 images and 22 sounds. The first thirteen groups are driven by
`content/catalog.json` and match it key-for-key, so those counts move when the
game's content does — rerun the build after a content change. `gear` and
`gear_worn` are this library's own equipment ladder, with records written to
`atelier/gear.json` in the catalogue's own format.

## The equipment ladder

Fourteen level bands, each with its own metal, cloth and leather, and its own
silhouette family. 44 pieces per tier — 14 weapons, 5 off-hands, 7 armour slots
in three weights, and 4 accessories — for 616 items.

| Tier | Level | Plate | Mail / leather | Cloth | Silhouette |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | Copper | Hide | Homespun | plain |
| 2 | 5 | Bronze | Boiled Leather | Linen | plain |
| 3 | 10 | Iron | Studded Leather | Wool | fluted |
| 4 | 15 | Steel | Scalemail | Silk | fluted |
| 5 | 20 | Silver | Chainmail | Brocade | winged |
| 6 | 27 | Cobalt | Wyrmhide | Moonweave | winged |
| 7 | 35 | Mithril | Mithril Weave | Mistweave | cruciform |
| 8 | 45 | Adamantine | Adamant Scale | Runeweave | cruciform |
| 9 | 50 | Obsidian | Shadowhide | Shadowsilk | serrated |
| 10 | 55 | Aetherium | Aetherscale | Aetherweave | runed |
| 11 | 60 | Drakeforged | Drakescale | Drakeweave | runed |
| 12 | 70 | Umbral | Umbral Hide | Umbraweave | crystalline |
| 13 | 80 | Dawnforged | Dawnscale | Dawnweave | crystalline |
| 14 | 90 | Starforged | Starhide | Starweave | ethereal |

A tier is not a recolour. The silhouette family switches the cross guard, the
pommel, how the edge is cut, how the haft is dressed, the shoulder plate and the
helm crest; on top of that each rung moves blade length, blade width, guard span,
ornament count and crest height, and the last six rungs carry a gem and a glow.
So a Cobalt longsword has swept wings on the guard and a faceted pommel where the
Iron one has a plain tipped bar and a disc, and they are different lengths.

Names come from the same table: `Copper Shortsword`, `Steel Greatsword`,
`Mithril Hornbow`, `Obsidian Grave Aegis`, `Umbral Nightfang`, `Starbreaker`.
Materials and piece names are joined without stuttering, so it is `Drakescale
Boots`, never `Drakescale Drake Boots`.

## Sheet layout

Animation sheets are 8 frames across. The 6 states run down the sheet, each
taking 4 rows, one per facing:

```
row = state_index * 4 + direction        state: idle walk attack cast hit death
col = frame                              direction: south west east north
```

Actor frames are 64×64 with the ground contact at y=55 and the centre line at
x=31.5; boss frames are 128×128 with the same proportions. That is the same
convention the client already uses, so these sheets are drop-in compatible.

## How it is put together

```
forge/pigment.py   colour: hue-rotating ramps, materials, elements
forge/brush.py     drawing: pieces, contours, rim light, occlusion, dither
forge/rig.py       humanoid skeleton: joints per state, frame and facing
forge/folk.py      bodies, hair, worn armour, weapons in hand, townsfolk
forge/smith.py     item construction, shared by icons and held sprites
forge/beasts.py    creature anatomy by family and archetype
forge/lands.py     tiles, scenery, gathering nodes, chests, stations, buildings
forge/gear.py      the tier ladder: materials, names, silhouette families
forge/sigils.py    ability and skill icons
forge/score.py     synthesised music, ambience and effects
build.py           the pipeline; preview.py   contact sheets for review
```

Four ideas do most of the work:

**Ramps rotate hue, not just brightness.** Shadows drift toward violet and
highlights toward warm gold, so materials read as lit rather than tinted.

**Every part is a lit solid, not a flat fill with an outline.** A piece is drawn
flat, then baked: the renderer walks inward one pixel at a time from each edge
and lays down bands — highlight, light, body, core shadow, and a cooler bounce
along the very bottom edge where the ground throws light back up. Broad surfaces
also get a dithered gradient across their short axis, and metal takes a specular
hit. That bounce band is what makes a shield read as a dome rather than a disc;
slivers one or two pixels across are detected and left mid-tone so they do not
turn into pure highlight.

**One rig drives every humanoid layer.** Bodies, hair, each armour slot, the
weapon in hand and the named townsfolk all read the same joint table, so a
helmet sits on the head and a sword stays in the grip in all 192 frames of a
sheet. Humanoid monsters reuse it too, at their own scale and hide colour.

**Anatomy is per family, not per palette.** Creatures are mapped to body plans —
quadruped, bird, insect, arachnid, serpent, worm, crustacean, aquatic, drake,
spirit, construct, elemental, mineral, plant, humanoid, mimic — and then to
proportions: muzzle length, ear shape, tail type, horns, leg count and stance. A
wolf is a long low quadruped with a deep chest and a brush tail; a heron is a
two-legged bird on stilts. Head-on views are drawn as head-on views, not as a
standing figure.

Death is a scripted collapse — stagger, buckle, fall, settle — interpolated
between authored keys, not a standing frame rotated onto its side.

**Every creature is an individual.** On top of its family's body plan, each mob
draws its own build from its id: coat markings suited to the body plan (spots,
stripes, bands, patches, dapple, a dark saddle, countershading), a colour drift,
and jitter on length, height, girth, leg, head, muzzle, ear and tail — plus a
chance of horns, a mane or a back ridge. Elites gain plating, scars and harder
eyes; bosses gain a crest and a mane. Humanoid monsters are told apart by what
they carry and wear, not by hue: goblins get hoods and daggers, kobolds horns
and spears, ogres a maul, revenants a helm and a greatsword, scarecrows a hat
and a sickle.

## Reviewing it

```bash
python atelier/preview.py ladder    # every weapon across every tier
python atelier/preview.py accessories  # rings, amulets, charms, relics by tier
python atelier/preview.py kin       # all 145 creatures, one grid
python atelier/preview.py armour    # every armour slot across every tier
python atelier/preview.py sets      # full sets, worn, one per tier
python atelier/preview.py body      # builds and facings
python atelier/preview.py states    # all six states, eight frames
python atelier/preview.py hair
python atelier/preview.py gear      # equipment on a dressed figure
python atelier/preview.py weapons
python atelier/preview.py items
python atelier/preview.py npcs
python atelier/preview.py beasts    # one per creature family
python atelier/preview.py world     # tiles, props, nodes, chests
```

Sheets are written to `atelier/preview/`.

The build's checks are structural: files exist, are RGBA, are not blank, and
animation grids are the right shape. That is not artistic approval — the art
still has to be looked at, which is what the preview sheets are for.

## Licence and provenance

Everything here is generated by the code in `forge/`. No third-party artwork or
audio is included, and no pixels are copied from the existing pack — the two
libraries share zero identical files. It inherits the repository's licence.
