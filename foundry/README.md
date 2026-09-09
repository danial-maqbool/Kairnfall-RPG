# Foundry — effects, ground transitions, interface, portraits and atlases

Supplementary to the [Atelier](../atelier/README.md) sprite library. Atelier
draws the world's things; Foundry draws what happens to them, what joins them
up, what frames them on screen, and how it all gets loaded.

It uses Atelier's drawing engine (`atelier/forge`) as a read-only library and
writes only inside `foundry/`. It modifies nothing under `atelier/`, `client/`
or `content/`.

## Build

```bash
python foundry/build.py                    # everything, then pack atlases
python foundry/build.py --list             # counts per group
python foundry/build.py --only ui vfx      # rebuild part of it
python foundry/build.py --atlas            # repack what is already on disk
python foundry/build.py --pack-atelier     # also atlas the Atelier icon set
```

Output goes to `foundry/Assets/`, with `manifest.json` (every key, size, frame
count and SHA-256), `CREDITS.txt`, and `foundry/coverage.json` for the last run.

## What it contains

| Group | Count | Size | Notes |
| --- | --- | --- | --- |
| vfx | 44 | 8-frame strips | impacts, slashes, bolts, cast circles, auras, flourishes |
| ground | 329 | 32×32 | terrain transition overlays, corners, foam, cliffs, roads |
| ui | 65 | various | panels, buttons, bars, slots, rarity frames, icons, cursors |
| portraits | 131 | 64×64 | player layers, 26 townsfolk, boss busts |

569 images, packed onto **1 atlas page** at 51% occupancy.

### Effects

Nine elements × impact bursts, projectiles and cast circles; three slash arcs;
eight status auras (burning, frozen, poisoned, shocked, blessed, cursed,
shielded, hastened); and six flourishes (level up, heal, death poof, gather,
block, crit). Strips run left to right, eight frames, one row — one-shots end on
an empty frame, auras and projectiles loop seamlessly. Projectiles point along
+x so a client can rotate them to the travel angle.

### Ground transitions

The problem these solve: a field of 32px tiles laid edge to edge reads as a
checkerboard, because every boundary is a straight line on the grid.

An overlay is drawn **on top of** whatever base tile is already there, so one set
per terrain covers every pairing rather than needing a tile per combination.
Overlays are keyed by a four-bit mask of which orthogonal neighbours share the
terrain:

```
1 = north   2 = east   4 = south   8 = west
```

so `grass_edge_15` is solid ground and `grass_edge_00` is an isolated patch.
Four inner-corner pieces per terrain fill the notches a four-bit mask leaves
behind. Shoreline foam is generated from the *same coverage shape and seed* as
the water overlay, so it follows the ragged shoreline exactly instead of ruling
a white line across the tile. Cliffs give height changes a rock face, and a
16-mask road set lays paths.

### Interface

Panels are nine-slice sources — 48×48 with 16px corners, so a client stretches
the middle. Buttons come in two styles × four states. Bars have a frame and six
fills. Slots come in three kinds with eight rarity frames over them, the top four
of which glow. Twenty-two icons, six cursors, a minimap frame, compass,
scrollbar, checkboxes and a divider.

### Portraits

A 64px world sprite has an eleven-pixel head, which is not enough face for a
dialogue box. Portraits are drawn at portrait scale instead: a proper skull, eyes
with iris and highlight, a brow and a jaw. Player portraits layer the same way
the world sprites do — a base per build and skin tone, a hair overlay per style
and colour — so the character creator can mix them freely. Townsfolk and bosses
are composed pieces. Humanoid bosses get a face and their headgear, not a muzzle.

### Atlases

Shelf packing, stable across rebuilds so the map does not churn. `--pack-atelier`
also packs Atelier's icons and tiles: **2,297 loose files onto a single 2048px
page** at 62% occupancy, with `atelier.json` mapping every key to its rectangle.

Godot writes its own `.import` files the first time it sees a texture, so this
does not fake them. It emits `godot_importer_defaults.cfg` instead — the settings
that actually need saying, since without them pixel art is filtered into mush.

## Reviewing it

```bash
python foundry/preview.py scene      # the HUD over a world built from the set
python foundry/preview.py ground     # patches, shoreline, road and cliff
python foundry/preview.py vfx        # every effect, frame by frame
python foundry/preview.py ui
python foundry/preview.py portraits
```

Sheets land in `foundry/preview/`.

The build's checks are structural: files exist, are RGBA, are not blank, and
strips divide evenly into frames. That is not artistic approval — the preview
sheets are for that.

## Layout

```
kit/vfx.py         impacts, slashes, bolts, cast circles, auras, flourishes
kit/ground.py      transition overlays, corners, foam, cliffs, roads
kit/face.py        panels, buttons, bars, slots, icons, cursors
kit/portraits.py   player, townsfolk and creature busts
kit/atlas.py       shelf packer and Godot importer notes
build.py           the pipeline;  preview.py   contact sheets
```

Generated art is committed here, as it is in `atelier/`. Everything under
`foundry/Assets` is reproducible with `python foundry/build.py`.
