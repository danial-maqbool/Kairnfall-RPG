# Kairnfall pixel-art direction

The accepted 3,291-line game specification remains the project requirement.
This document adds the user's real-object art requirement. It does not reduce scope.

## Construction

Draw recognizable objects at native pixel resolution. A sword needs a blade edge,
central plane, guard, wrapped grip, and pommel. An axe needs a shaped metal head,
eye, wooden shaft, cutting edge, and attachment detail. A chest needs separate
boards, joints, hinges, lid thickness, metal straps, and a lock. A building needs
walls, roof planes, roof texture, structural supports, doors, windows, and a base.

Use anatomical references for animals. Wolves need a muzzle, ears, shoulder mass,
articulated legs, paws, and a tail. Birds need a beak, wing structure, and feet.
Fantasy creatures must retain understandable anatomy or material construction.

## Scale and rendering

Use 32-pixel terrain tiles and 64-pixel character frames. Use a consistent overhead
three-quarter view. Anchor actors at their feet. Render pixel textures with nearest
sampling and integer scaling. Do not add smooth gradients or blurred outlines.
Use an upper-left light source. Show form with deliberate pixel clusters, highlights,
midtones, reflected light, and contact shadows. Texture must describe material.

Metal uses narrow bright highlights and dark planes. Wood uses grain and end rings.
Leather uses seams and straps. Cloth uses folds and hems. Stone uses facets and
joints. Skin uses a limited tonal ramp. Glass needs a rim, highlight, and contents.
Do not add random noise to increase the apparent colour count.

## Animation and equipment

Use four directions. Keep feet and equipment anchors consistent across frames.
Implement idle, movement, attack, cast, hit, and death for the player. Show equipped
weapons, shields, helmets, armor, boots, and cloaks as aligned sprite layers.
Large monsters and bosses may use larger frames. Recolours are variants, not species.

## Review gate

Inspect contact sheets at 1x and 4x. Inspect the same assets in the running client.
Check object identity, material separation, anatomy, animation alignment, collision
alignment, contrast, and combat readability. Record each reviewed sheet and scene.
A numeric palette test is not a visual approval. Generated assets remain unapproved
until inspection. Reject flat blobs, letter icons, geometric actor placeholders,
broken anatomy, unreadable weapons, and generic copies used to meet content counts.

## Reference and licensing

Use real objects and anatomy as structural references. Do not reproduce proprietary
game artwork. Record the source, author, license, and changes for external assets.
The MIT source-code license does not replace third-party asset licenses.
