# Asset pipeline and release boundaries

## Scope

This pipeline generates PNG sprite sheets, item icons, environment art, and WAV audio for the existing Godot client.
It does not export a Windows executable or certify the complete MMORPG.
The accepted game specification and real-object pixel-art requirement remain unchanged.

## Reproduce the asset build

Use Python 3.12 and Pillow 12.0.0, matching the inspected asset job.
Run these commands from the repository root:

```text
python -m pip install Pillow==12.0.0
python tools/build_content.py
python tools/build_game_assets.py
python tools/validate_game_assets.py
```

The compiler writes the catalog to `content/catalog.json`.
The asset generator writes the client copy to `client/Assets/catalog.json`.
The validator requires both copies to match exactly.
Generated assets and local credentials are excluded from Git. The generator source is versioned.

## Output contract

The client loads assets below `client/Assets`.

| Directory | Content |
| --- | --- |
| `terrain` | Four variants for each terrain type |
| `props` | Trees, vegetation, rocks, landmarks, travel objects, and loot |
| `buildings` | Zone-specific buildings with tile-aligned dimensions |
| `resources` | Gathering nodes and planted wheat |
| `structures` | Crafting stations and campfires |
| `chests` | Open and closed chest states |
| `items` | One icon per item template |
| `abilities` | One icon per ability definition |
| `people` | Body and hair layers |
| `equipment` | Animated equipment layers |
| `npcs` | Animated NPC role sheets |
| `mobs` | Animated creature sheets |
| `audio` | Music, ambient audio, and action effects |

Animation sheets contain eight columns and 24 rows.
Rows are grouped by state: idle, walk, attack, cast, hit, death.
Each state contains south, west, east, and north directions, matching the client renderer.
Normal actor frames use 64 pixels per side. Current boss frames use 128 pixels per side.
Frame size alone does not establish sufficient boss detail or unique boss design.

`manifest.json` records each PNG path, dimensions, checksum, and animation status.
`CREDITS.txt` identifies this generated pack as original procedural artwork and synthesized audio.
The repository MIT license covers the original source. This pack imports no third-party artwork.

## Validation

The preflight draws all creature definitions before the full build.
Unknown renderer families fail immediately.
The final validator checks the expected client image keys, matching catalogs, image checksums, dimensions, RGBA format, actor-frame visibility, and audio file formats.
It rejects identical full animation images and exact duplicate alpha silhouettes among normal species.
It does not hide those failures by counting palette changes as new anatomy.

The first complete pack exposed duplicate species sheets.
The following refinement adds actual structural differences, including mouse proportions, tick leg placement, fish fins, turtle flippers, cephalopod arms, fungal colonies, thorn cages, crab shells, bird anatomy, and different humanoid equipment.
No random identification pixels are used to make duplicate sprites appear unique to the test.

Reports are saved in `artifacts/test-results/asset-structure.json`.
The contact sheet is saved in `artifacts/screenshots/creature-contact-sheet.png`.
The workflow retains the generated PNG/WAV pack separately from the report.
Neither artifact is a playable game archive.

## Required visual review

A successful structural check is not visual acceptance.
The manifest deliberately retains `artistic_review: not_approved`.
Review native-resolution frames and actual client screenshots before approving the art.
Check silhouette readability, anatomical accuracy, material shading, layer alignment, directional views, clipping, weapon grip, attack timing, and boss identity.
Near-duplicate art can still pass an exact-hash test. That requires visual review.
Audio format validation does not establish sound quality or correct mixing.

## Local launcher source

`Run-Kairnfall.ps1` and `docker-compose.yml` are source additions for a future Windows package.
The launcher expects `server/Kairnfall.Server.exe` and `client/Kairnfall.exe`.
Those executables are not produced by the asset workflow and are not present merely because this script exists.
Do not advertise the launcher as ready to play until a complete package is tested.

The launcher creates a private local database password, limits access to its file, binds PostgreSQL and the game server to loopback, and retains the database volume.
Its stop operation verifies the recorded executable and process start time before stopping a process.
The launcher still requires execution tests on Windows.

## Current execution boundaries

The platform rejected a proposed packaging-workflow write in this continuation.
That workflow was not installed. No alternative credential or execution route was used to perform that blocked operation.
The permitted asset workflow performs image and audio generation only.
The local execution environment returned ClientError, so no local image inspection or graphical game test was verified.
No independent coding-agent team executed this work.

Open release requirements include graphical client validation, visual and audio review, complete gameplay acceptance, unique boss encounters, progression balance, multi-client and load tests, launcher tests, Windows export, and release packaging.
Keep the work in draft until its relevant gates pass. Do not describe this document or the generated asset counts as completion of the game.
