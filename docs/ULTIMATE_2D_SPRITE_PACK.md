# Ultimate 2D Sprite Pack

Kairnfall's preferred full-game art source is `atelier/UltimateAssets`, generated deterministically by
`tools/art/generate_kairnfall_ultimate_pack_runner.py`. The entry point contains the exact deterministic 2D generator sources in compressed form to keep the repository source compact.
No third-party sprite artwork is required.

The pack includes humanoid bodies, hair, armour, weapons, complete archetypes, NPCs, normal creatures,
bosses, terrain, props, resources, buildings, structures, chests, item icons, ability icons, skill icons,
VFX, projectiles and status icons.

Actor sheets keep the client contract: 64x64 frames, eight columns, 24 rows, six states in
`idle, walk, attack, cast, hit, death` order, four facings in `south, west, east, north` order, and foot
contact at y=55. Bosses use 128x128 frames with the same layout.

`tools/integrate_ultimate_pack.py` adapts the catalog-agnostic source masters to the exact generated
client keys after the regular Atelier integrity cohort is installed. It does not rename content IDs or
change collision/gameplay records. Equipment masters are split into the existing chest/legs/boots/gloves/
belt layers, while specialized slots that do not have an equivalent Ultimate master retain their existing
compatible artwork. Creature replacements never reuse an identical normal-species sheet, preserving the
existing duplicate-silhouette validation rule.

`tools/complete_skill_icons.py` prefers Ultimate icons for all catalog skills, using semantic aliases for
skills beyond the 24 direct source icons.

The GitHub workflow `.github/workflows/ultimate-2d-sprite-pack.yml` regenerates the checked-in source pack,
builds the actual client assets, runs structural validation, and only publishes the pack if the game
integration succeeds.
