# Kairnfall

Persistent 2D top-down medieval fantasy RPG for Windows. The client uses Godot C#.
The authoritative .NET server stores accounts and world state in PostgreSQL.

**Status: source handoff for local testing. This is not a completed game release.**

The [September 8 visual repair checkpoint](docs/handoff/LOCAL_VISUAL_REVIEW_2026-09-08.md)
records current main's bear/weapon presentation, village placement, inventory and
HUD repairs. Local bootstrap, isolated database suites, native Godot contracts
and inspected graphical smoke passed. Full visual acceptance remains incomplete;
interiors, bow alignment, manual/DPI coverage and release gates remain open.

Historical September 7 Windows repairs and bounded test results are recorded in
[the acceptance checkpoint](docs/handoff/LOCAL_ACCEPTANCE_2026-09-07.md).
Security, collision, native mouse input, and 720p HUD/map issues were repaired.
Reviewed follow-ups preserve legacy saved positions and securely resume interrupted
official toolchain downloads without bypassing checksum verification.
That run's bootstrap timed out downloading matching templates. September 8 source
preparation succeeded with the verified local editor; full gameplay, audio,
performance, export-template and package acceptance remain open.
Catalog counts, compilation, and generated-image validation do not establish complete gameplay or approved artwork.

## Start here

Use `main` for the integrated source handoff and reviewed local repairs. It retains
the transaction repairs, source asset generators, and native button callback repair.
Do not assemble a checkout by merging every old workstream branch.

```powershell
git clone --branch main https://github.com/danial-maqbool/Kairnfall-RPG.git
cd Kairnfall-RPG
pwsh -NoProfile -File .\bootstrap.ps1
pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1
```

Install the prerequisites in [LOCAL_REQUIREMENTS](docs/LOCAL_REQUIREMENTS.md) before bootstrap.
Open Docker Desktop with Linux containers before a database or gameplay command.
Bootstrap creates a local Python environment, generates content and art, builds source, and imports the pinned Godot project.
It does not deploy an Internet server or publish a release.

For the testing agent, read [the handoff](docs/handoff/HANDOFF.md), then execute
[the local agent prompt](docs/handoff/LOCAL_AGENT_PROMPT.md).
The [accepted requirements](docs/requirements/ACCEPTED_REQUIREMENTS.md) remain the completion target.

## Local commands

| Command | Purpose |
| --- | --- |
| `bootstrap.ps1` | Prepare source dependencies, generated assets, .NET builds, and Godot imports. |
| `Test-Kairnfall-Local.ps1` | Run core, gameplay-review, and transaction security suites. |
| `Test-Kairnfall-Local.ps1 -WithDatabase` | Also run network and persistence tests in the isolated test database. |
| `Run-Kairnfall-Dev.ps1` | Start the local realm, then the client. Stop that child server when the client exits. |
| `Run-Kairnfall-Dev.ps1 -Smoke` | Require the live-client smoke run and its four screenshot files. |
| `Run-Kairnfall-Server.ps1` | Keep a local source server running until Ctrl+C. |
| `Run-Kairnfall-Client.ps1` | Open another client against the local realm. |
| `Stop-Kairnfall-Database.ps1` | Stop this checkout's database containers without removing volumes. |
| `Kairnfall.cmd` | Start the development game after bootstrap. |

The login server address is `http://127.0.0.1:5077`. Create a new local test account in the game.
This is a private development realm, not a publicly hosted MMORPG.

## Controls

WASD or arrow keys move. E interacts. Tab cycles targets. Keys 1-0 use the hotbar.
I opens inventory. C opens the character window. K opens skills. J opens quests.
M opens the map. B opens abilities. F opens crafting. P opens social controls.
Enter opens chat. Esc closes a window or opens the menu. Inspect rebinding behavior during local QA.

## Source layout

- `client/`: Godot project, main scene, interface, rendering, and native signal tests.
- `src/Kairnfall.Core/`: authoritative gameplay, state models, and shared protocol.
- `src/Kairnfall.Server/`: HTTP/WebSocket endpoints, account handling, and PostgreSQL storage.
- `content_src/`: authored catalog inputs. `content/catalog.json` is generated.
- `tools/art/`: original artwork source. `client/Assets/` is generated.
- `tools/local_dev.py`: source setup, local process lifecycle, and isolated test commands.
- `tests/`: executable backend regression suites and handoff contract tests.
- `docs/`: requirements, verification boundaries, local handoff, and historical reviews.

## Asset generation

Run `.\.venv\Scripts\python.exe tools/local_dev.py assets` after editing asset or catalog source.
This runs content compilation, the base art/audio generator, skill-icon completion, and strict reference validation.
No expiring Actions artifact is needed to reconstruct the pack. Generated PNG/WAV files are not a playable release.

Artwork must show recognizable anatomy, material shading, and real object construction.
Palette counts and different file hashes do not prove that sprites meet this requirement.
See [ART_DIRECTION](docs/ART_DIRECTION.md) and the local visual acceptance checklist.

## Data and secrets

Keep `.local/`, `.venv/`, `.tools/`, database volumes, private logs, and account data out of Git.
The launchers generate random local database passwords. Do not share `.local/database.json`.
Development data and destructive integration-test data use separate containers, databases, and volumes.
Never point test suites at a production or personal-save database.
The local guide explains shutdown, credential recovery, and port-conflict handling.

## Evidence and release policy

See [VERIFICATION](docs/handoff/VERIFICATION.md) for observed results and unrun checks.
Do not call this project complete until the full gameplay, multiplayer, artwork, performance,
and Windows-package gates pass. A release must include a commit, logs, checksums, and actual startup evidence.

Original project source uses [MIT](LICENSE). External assets retain their own licenses.
See [THIRD_PARTY_ASSETS](docs/THIRD_PARTY_ASSETS.md).
