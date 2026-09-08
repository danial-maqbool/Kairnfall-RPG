# Asset and dependency licensing record

The [September 8 repairs](handoff/LOCAL_VISUAL_REVIEW_2026-09-08.md) modify original
MIT-licensed source generators for fauna, floorboards, wand icons and held gear.
No external artwork/audio was introduced. The verified Godot 4.7.2 .NET editor
successfully imported and ran the project. No distribution/signing or matching
export-template acceptance is claimed. The following timeout is historical.

The 2026-09-07 acceptance repair added no external artwork or audio. Generated
creature art failed visual review and remains unapproved. The official Godot
4.7.2 .NET editor was checksum-verified and executed; matching-template download
timed out and no binaries were published. Package notice/signing review remains open.

## Current selected asset pipeline

The handoff generates artwork from checked-in `tools/art/` Python source.
It generates WAV audio in `tools/build_game_assets.py`.
It generates skill icons by selecting existing object/ability renderers through `tools/complete_skill_icons.py`.
This selected pipeline does not require externally downloaded game sprites or music.
Its generated CREDITS.txt describes the source and does not certify visual quality.

Original project source uses the repository MIT license.
Do not assume that every future external asset can inherit that license.
Do not copy game sprites, maps, audio, dialogue, or other protected content from the reference games.
Personal use does not remove the need to respect the asset's actual license, especially in a public repository.

## Tool dependencies are not game-art licenses

Godot, .NET, PostgreSQL, Python, Pillow, and Docker are development/runtime dependencies.
Preserve required distribution notices when preparing a binary package.
The source dependency manifests and their upstream licenses govern those components.
Review exact redistributed binaries and licenses during release preparation.

## Required record for each external asset added later

Record asset ID, local path, original title, author, exact source URL, license name/version,
license-text path, download/checksum where available, modifications, attribution wording,
and permission to redistribute in source and binary packages.
Do not commit font binaries from a hosted execution environment. Obtain fonts through a properly licensed source.

No external asset approval is implied by an inspection script or an unused source URL.
