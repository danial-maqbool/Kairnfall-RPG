# Pixel-art direction and review contract

## Native pixels and Atelier integration — 2026-09-09

Current main integrates 2,982 matching Atelier assets after hash, path, dimensions, animation-order and complete-rig checks. Body, hair, worn gear and NPC sheets switch as one coherent cohort. The independent Atelier gear ladder never replaces gameplay records. Default world zoom is 1x, full-canvas window stretching is disabled, and inventory icons do not enlarge their source pixels. World collision and tile coordinates remain unchanged. The actual pack renders in Godot at 1280x720 and 1920x1080. Use native `engine/` captures for Atelier review; historical `before/after` generator sheets do not prove approval of the imported pack. Independent image inspection remains uncompleted. [Rules and asset counts](HUNTING_AND_JOURNEY.md), [evidence and limits](handoff/HUNTING_AND_PRESENTATION_2026-09-09.md).

## Equipment materials — 2026-09-09

The [gear extension](EQUIPMENT_PROGRESSION.md) retains 32 by 32 icons and 64 by 64 equipment frames. Original source adds material highlights, cloth folds, hide contours, stitching and fittings. Equipped layers retain shared body anchors, four directions, six states and nearest-neighbor presentation. Grade metadata does not rewrite old saved templates. Every grade has a contact sheet; representative full sets render in Godot at two resolutions. File construction checks and rendered frames are not independent visual approval. See the [review evidence and limits](handoff/EQUIPMENT_PROGRESSION_2026-09-09.md).

## Current action presentation

See [the action checkpoint](handoff/ACTION_PRESENTATION_2026-09-08.md). The player and gear
retain their shared 64-pixel canvas and integer foot anchor. WorldView now plays all eight
action frames across the actual action duration. Corpses complete a 0.65-second collapse
and hold the final pose separately from corpse retention. Spider and turtle actions use
authored joint/neck offsets, not bitmap rotation or meaningless per-frame pixel changes.
Review galleries now sample frames 0, 1, 2, 3, 4, and 7 in every state and direction.
The tests and native renderer passed. Independent PNG inspection and final visual approval
were not completed in the chat runtime; the evidence locations are in the checkpoint.

## Required visual standard

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
