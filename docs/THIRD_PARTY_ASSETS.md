# Asset and dependency licensing record

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
