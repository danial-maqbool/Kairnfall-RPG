# Art-library repair review: 2026-09-09

## Scope

Repair the cliff joins, near-black nine-slice panels and repeating terrain
dither in Atelier and Foundry. No changes to `client/Assets/`, `tools/art/`,
`content_src/` or `content/`. Foundry reads Atelier but does not write to it.
The starting library source is from main `70f02581537ede1c749e3342907776c9455be673`.
That commit only added an offline source-export workflow over the prior main.

## Visual findings and revisions

Before repair, the top cliff stopped above the face, leaving a horizontal gap.
Corners were narrow disconnected strips. Different shape seeds changed the
heights of adjacent strata. The new shapes crop one common rock material, with
shared seam samples, a soil lip, an overhang shadow, side lighting, and a grounded
foot. Added feet and exported interior variants retain every old key and size.

The first joined version looked too much like regular masonry. It was revised
with broader fracture planes and varied internal strata, while keeping boundary
samples fixed. Both a straight ledge and a stepped wall now show connected rock
through convex and concave turns. The preview no longer places an isolated
corner beside an incomplete top/face pair.

The tooltip and inset fields were too dark. Their horizontal grain also stretched
into large bands. Brighter fields and frames alone were not sufficient: the
16x16 stretchable center is now kept quiet. Grain remains around the edges.
Populated panel previews show text at several panel sizes. All sources retain
the 48px size and 16px corners. Window/banner center banding is repaired too.

Terrain no longer calls ordered dither for grass, moss, marsh, dirt, sand, ash,
or snow. Low-contrast toroidal deposits form clusters instead. Vegetation variants
share their edge field, and grass blades no longer cross the seams. The grass
field selector in the preview is deterministic but no longer cycles variants in
a regular diagonal sequence. Single-variant fields remain in the review sheet so
larger repeated motifs cannot be hidden by the preview arrangement.

Two small source defects were fixed while testing: terrain-only builds and
manifest indexing unnecessarily demanded a game catalogue; and the unused
parchment color constant expanded to a malformed five-digit hex string. The
constant is now explicit `#c9b88a`. No external art or new dependency was added.

## Review evidence

The author inspected the before/after ground and scene sheets, both cliff
assemblies, populated tooltip/inset panels, and seven terrain fields. These are
library previews, not screenshots of a running Godot game.

- `preview/ground.png`: mixed ground transitions and a complete ledge.
- `preview/scene.png`: repaired panels over the same ground sample.
- `preview/cliffs.png`: individual shapes, mixed variants, concave turns and feet.
- `preview/panels.png`: populated 48/16 panels at several output sizes.
- `preview/terrain.png`: seven materials with mixed and repeated single variants.
- `preview/ui.png`: UI contact sheet.

Before-state images are recoverable from the starting commit. Local review
captures and test reports are also retained with the task delivery.

## Executable verification

`python -m unittest discover -s foundry/tests -v` contains 11 regression tests.
They cover all four cliff variants, horizontal and vertical sockets, concave
rock spans, complete cap faces, feet, vegetation seam compatibility, absence of
ordered terrain dither, four-pixel phase contrast, catalogue-free terrain plans,
nine-slice corner preservation, panel contrast, and repeat rendering.

`python foundry/verify_repairs.py` rebuilds affected groups twice. Both manifests,
both sets of atlas pages, and all six previews are included in the comparison.
Only the `built_seconds` property in either coverage report is excluded. The
script fails if Foundry writes to Atelier or a protected game directory changes.
CI records its Python/Pillow versions and exact hashes in the artifact report.
The script does not mark the entire libraries artistically approved.

The first local repeat check detected ongoing README edits between snapshots.
No asset mismatch occurred. The check was repeated after source and documentation
edits stopped; its report records the final result.

## Limits retained

The existing water wave pattern is still regular. Marsh puddles, sand ripples,
and single-variant fields still repeat at the tile scale. Removing the intrusive
four-pixel checker is not infinite terrain synthesis. Cliff variants are a
finite art set, not every possible height-map topology. Client integration,
walkability, combat, Godot rendering and whole-game acceptance are outside this
library-only repair. Existing full-library artistic-review flags remain pending.
