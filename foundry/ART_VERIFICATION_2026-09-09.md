# Three art-library repairs: verified integration

Date: 2026-09-09.

## Exact source and output

The implementation and generated assets are retained together in commit `45a9c830bc2e81b653601902e045d2ad880c2d28`, based on main `1e48c197d959530a2b9bad6c3d72b695b66e026b`. It contains 314 changed library files: 7 Python files, 3 Markdown files, 299 PNGs and 5 JSON indexes/reports. It preserves the earlier main history and all unrelated source. The final integration adds this receipt and replaces temporary candidate upload workflows/requests with one read-only verifier. No branch or pull request was created.

## Observed checks

GitHub Actions run `34348773031`, job `102456612171`, passed the full art-library check and Git-object upload. The runner used Python 3.12.14 and Pillow 12.0.0.

- 11 regression tests passed, including all four cliff variants, exact compatible edge pairs, concave joins, complete cap faces, feet, vegetation edges, removal of ordered terrain dither and nine-slice corner/contrast checks.
- `python atelier/build.py --only terrain --jobs 2` and `python atelier/build.py --manifest` passed. Atelier retains 4,274 source PNGs and 22 audio files.
- `python foundry/build.py --only ground ui --jobs 2` and `python foundry/build.py --atlas` passed. Foundry now has 605 source PNGs, including 44 cliff tiles; 36 cliff images were added while preserving old keys. Its atlas has one page with no oversized assets.
- `python foundry/build.py --pack-atelier --atlas` passed and updated the read-only packed Atelier pages.
- Two complete affected-group rebuilds reproduced 4,981 library files, including 4,921 PNGs. Only coverage.json built_seconds was excluded from comparison.
- Foundry did not write into Atelier. The four protected game directories did not change: client/Assets, tools/art, content_src and content.
- The downloaded 314-file archive was checked against every Git blob hash and the verification report's SHA-256 values. All Python and Markdown contents matched the locally reviewed patch. Every rebuilt PNG had the same decoded pixels as the locally reviewed output.

## Visual review

The author opened and reviewed regenerated ground, scene, cliffs, populated panels and terrain preview sheets. The pinned CI scene, cliffs, panels and terrain outputs were opened again after download. The continuous ledge and stepped wall include mixed cliff variants, both convex corners, both concave turns and ground-contact feet. The grass field no longer has the four-pixel woven checker. Tooltip and inset fields, frames and bevels remain visible at scene scale. The stretchable panel center no longer expands grain into thick bars. Sources retain the 48x48 / 16px-corner contract.

The first joined cliff attempt still looked like regular masonry and was revised with broader fracture planes and variable internal strata. Global Piece.dither was deliberately left unchanged; only ground generation stopped using it. Single-variant terrain repeats remain visible in the review sheet so the demonstration does not hide finite tile repetition.

These observations approve the three requested library-preview repairs. They do not approve the complete art libraries or claim a Godot playthrough. See ART_REPAIR_2026-09-09.md for the implementation details and remaining limits.

## Evidence

Artifact: `10103182350`, `art-library-final-1e48c197d959530a2b9bad6c3d72b695b66e026b`.
Archive SHA-256: `dfecdf8d73b363f8d7d06413e94d08fa4e288eb95e0ce127c42ef92613a317af`.
The archive contains the verification log, complete hash report, source patch, candidate metadata and generated updates.zip. Committed preview images are under foundry/preview: ground.png, scene.png, cliffs.png, panels.png, terrain.png and ui.png.

The earlier run `34348058364` passed every art test but failed at the subsequent concurrent Git-object upload with HTTP 403. It is not counted as a successful overall run. Serial uploads with bounded, server-directed rate-limit backoff then passed. No test or checksum was weakened.

The new read-only workflow verifies both repeat-build determinism and equality with committed output on subsequent art changes. It accepts no drift except built_seconds and cannot modify GitHub source.

## Unchanged limits

Water waves remain regular. Marsh puddles, sand ripples and repeated single-variant fields still have tile-scale motifs. This is not infinite terrain synthesis or every possible cliff topology. No game integration, collision, performance, combat, saved state or Windows package change is included. The malformed unused parchment color and unnecessary catalogue access in partial terrain/manifest builds were also repaired. No third-party art was added.
