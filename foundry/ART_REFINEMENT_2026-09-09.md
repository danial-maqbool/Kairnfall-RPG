# Final natural-ground refinement — 2026-09-09

This follow-up preserves the integrated cliff, panel and terrain repair. The
connected cliffs, nine-slice panels, catalogue-free partial builds and all original
art keys remain intact. The two source changes affect the natural-ground generator
and its seam regression. Regenerated PNGs, manifests, atlas pages and previews
are included in the same tested implementation commit.

## Visual decision

The first checker-free ground used eleven large colour deposits. The repeating
4x4 dither was gone, but the grass looked blotchy. The final revision uses 24
smaller deposits and lower-contrast shade and light blends. Grass blades remain
legible without bright isolated highlight pixels dominating the field. This
changes the pixels at their original resolution, not the preview's zoom.

Sand variants exposed a separate seam defect: ripple lines ended two pixels
higher on alternate tiles. Endpoints now agree at y=6, 16 and 26. Each variant
bends only the interior of each ripple. The exact horizontal and vertical seam
regression now covers all seven natural materials and all sixteen variant pairs.
The shared Piece.dither implementation is unchanged for structured materials.

## Review and limits

The final ground and scene sheets, connected cliff assemblies, populated panels,
and all seven mixed/single-variant terrain fields were opened and inspected.
Grass, moss and marsh no longer show the intrusive four-pixel woven pattern.
Cliff variants join through straight sections, outer corners, inner turns and
feet. Tooltip and inset borders and fills remain readable over the scene.
The panel contract remains 48x48 with 16px corners. The downloaded CI scene,
cliff and populated-panel renders were opened again before integration.

A finite tile library still repeats. Marsh puddles, dune/snow contours and the
unchanged water waves retain recognizable motifs. This does not claim infinite
terrain synthesis, a Godot gameplay review or whole-library artistic approval.

## Verification

Tested implementation: `8f12b78546c76d397b3e7170c1ea88c9972b936b`.
Its parent is main `464eac93575cbf51e6c3cdf3815217c4766ca6ce`.
GitHub Actions run `34350712362`, job `102463019071`, passed under
Python 3.12.14 and Pillow 12.0.0. This is the encoding used for committed PNGs.

- All 11 regression tests passed. The seam test was expanded, not relaxed.
- Both complete affected-group rebuilds passed, including Atelier terrain and
  manifest indexing, Foundry ground/UI, both atlas sets and six preview sheets.
- Repeat comparison covered 4,980 files and 4,921 PNGs. Only the built_seconds
  property in coverage.json was excluded; no PNG or manifest drift was permitted.
- Foundry did not write into Atelier. The four protected game directories stayed
  unchanged: client/Assets, tools/art, content_src and content.
- The downloaded 198-file update contains 2 Python sources, 194 PNGs and 2 JSON
  manifests. Every file matched its uploaded Git blob and report SHA-256.
- All 194 regenerated PNGs had identical decoded pixels to the reviewed local
  output. The local repeat run also passed under Python 3.13.5 / Pillow 12.3.0.
  Cross-version compressed PNG identity is not claimed.

Independent local atlas extraction checked 605 Foundry entries and 2,297 Atelier
entries. Every visible pixel and alpha byte matched its source. RGB under zero
alpha is normalized by compositing in 344 Foundry pixels; that is invisible and
not a lost-pixel defect. There were no oversized atlas entries.

The temporary refinement-publication workflow is removed after verification.
The existing read-only art-library workflow remains. It checks repeat builds
and parity with committed output and cannot change source or branches.

## Evidence and reproduction

Artifact `10103930397`: `art-refinement-464eac93575cbf51e6c3cdf3815217c4766ca6ce`.
Archive SHA-256: `60307d412d55cc4933f30bf06eeb10ec6890841ec915baf7e987abe9954ceef5`.
It contains source patch, generated updates, complete hash report, log and previews.

Run `python foundry/verify_repairs.py --report artifacts/art-repeat.json` to repeat
all checks without a game catalogue. Review foundry/preview/ground.png, scene.png,
cliffs.png, panels.png, terrain.png and ui.png. Before-state images remain in the
original main `cab2c1d7770e29628b5040b8d4b9d6ef3093445d`.
