# Pixel-art direction and review contract

The user requires pixel art based on the construction of real objects and recognizable anatomy.
This is a visual acceptance contract. Generated files have not received final visual approval.

Use 32-pixel terrain tiles, 64-pixel actor frames, and 128-pixel boss frames in the current pipeline.
A sheet has eight columns and 24 rows: idle, walk, attack, cast, hit, death; four rows per state.
Directions are south, west, east, north. The client anchors feet at half the frame width and 0.86 of its height.
All equipment and body layers must use the same pose and anchor. Test movement as well as still frames.

Use deliberate pixel clusters, controlled material ramps, and consistent upper-left light.
Do not add random noise or smoothing to simulate detail. Preserve nearest-neighbor rendering.
An animal must remain identifiable with its name hidden. A weapon must show its working shape and construction.

Review rats and mice for muzzle/tail proportions; rabbits for long ears and folded hind legs;
birds for beaks, wing feathers, and feet; bats for finger-supported membranes;
insects for six legs and body segments; spiders for eight legs; snakes for coherent coils;
snails for a shell and muscular foot; fish for fins; turtles for flippers versus tortoise feet.
Fantasy creatures must retain coherent anatomy. An owlbear is not a ghost or a recolored bear blob.

Show metal blade edges, guards, tang/grip fittings, wood grain, cloth seams/folds,
leather straps, stone facets, bone joints, and chest hinges/locks where visible at native scale.
Buildings require roof planes, joinery, entrances, foundation, and usable perspective.
Create different silhouettes and construction for each city, creature species, and boss.

The current generator and duplicate checks are development tools. Different hashes do not prove different anatomy.
Do not repair a duplicate warning by adding a meaningless pixel or invisible mark.
Keep elite recolors separate from the normal-species count.

Inspect contact sheets for every normal species and boss. Review every state/direction on problematic assets.
Inspect equipped character animation for all weapon families and representative armor weights.
Check clipping, flipped light direction, occluded hands, floating weapons, sprite jumps, and foot sliding.
Inspect cities, interiors, underground areas, combat telegraphs, and interface screens in the real game.

Save reviewed screenshots or recordings and an asset-by-asset decision log under ignored `artifacts/visual/`.
Commit a sanitized review summary with exact source revision and remaining defects.
Do not label a contact sheet a gameplay screenshot. Do not label art approved before inspecting it.
