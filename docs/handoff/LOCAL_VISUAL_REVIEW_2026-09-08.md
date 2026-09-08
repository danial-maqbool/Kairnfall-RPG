# Windows visual repair checkpoint — 2026-09-08

Status: **partial visual repair; full visual acceptance NOT PASSED**. This is not
a finished MMORPG, tested Windows distribution, or release approval.

Starting source: `4cb756448d59931aa4868b4496214f7a4874fbde` on `main`.
Tested implementation: `a66ae706e728b08cf06ba96443e5e2da44e0f25e` (the working tree tested before commit).
The subsequent report commit changes documentation only. Work stayed on main;
no branches, pull requests, history rewrites, or force pushes were used.
Unrelated local files were preserved and excluded from the commits.

## Implementation and review

| Area | Repair and evidence | Status |
| --- | --- | --- |
| Player | Existing articulated human rig, gear layers, and foot anchors retained. Native fixtures cover eight weapon families, four directions, six actions and frames 0/2/4/7. | Sampled graphical review; not full manual acceptance |
| Equipment | Held mace gains visible flanges; wand becomes a short tapered baton with small focus instead of the staff's large cage. Gloves added to equipment review fixtures. | Implemented and graphically checked |
| Common fauna | Dedicated black/polar bear construction with connected broad paws, jointed legs, distinct neck/head proportions and grounded collapse. Rat/hare/wolf/boar north/south deaths lower their torso/head and fold ears/tails. | Implemented; sampled native frames inspected |
| Item icons | Wand silhouette separated from staff; 19 representative item/chest icons captured through Godot. Existing sword, axe, bow, potion, ore, log, hide and rune images retained. | Sampled review; not approval of every item |
| NPC layout | Ten original Wayfarer's Rest service IDs retained, moved from a vertical queue to building forecourts; door thresholds and central lane kept clear. Corrected one intermediate water-adjacent smith position. | Implemented; native village images and path tests passed |
| HUD | Chat history panel reduced by 34 pixels; NPC names/roles enlarged with dark backing. Onboarding text follows innkeeper relocation and gives an interior exit hint. Exit labels raised above the player's head. | Implemented and sampled at 720p/1080p |
| Inventory | Normalize CRLF to LF, remove duplicate name/rarity and art-construction prose; quantity field visible at 720p. Opening actions for the already-selected item no longer rebuilds/disposes its slot. | Native regression and live server contract passed |
| Environment | Interior dirt routes render as timber without changing authoritative terrain/collision or saved positions. Long low-contrast floorboards replace brick-like blocks. | Improved floor appearance; rooms still fail furnishing quality |

Changed implementation/test sources:

- `client/Scripts/GameRoot.Experience.cs`
- `client/Scripts/GameRoot.Hud.cs`
- `client/Scripts/GameRoot.Inventory.cs`
- `client/Scripts/WorldView.cs`
- `client/Tests/LiveExperienceContract.cs`
- `client/Tests/VisualPresentationContract.cs`
- `content_src/items.py`
- `content_src/world.py`
- `tools/art/environment_pack.py`
- `tools/art/fauna.py`
- `tools/art/humanoid.py`
- `tools/art/items.py`
- `tests/handoff/test_building_interiors.py`
- `tests/handoff/test_visual_art.py`
- `tools/run_live_experience.py`

Original source generators remain canonical. No external art/audio was added;
these additions use the repository's MIT license. No generated count or image
uniqueness result is treated as artistic approval. An actual specialist agent
reviewed and edited fauna geometry; the integration owner ran native verification
and publishes the combined changes.

## Environment and data isolation

Windows; Intel Core i7-13620H, 15.7 GiB RAM, NVIDIA GeForce RTX 4060 Laptop GPU.
Godot used real NVIDIA OpenGL 3.3 Compatibility rendering, driver 595.71.

| Tool | Observed version |
| --- | --- |
| Git | 2.54.0.windows.1 |
| Python | 3.12.10 |
| Pillow | 12.0.0 |
| PowerShell | 7.6.5 |
| .NET SDK | 10.0.400 |
| Docker client/server | 29.6.1 |
| Docker Compose | v5.1.4 |
| Godot .NET | 4.7.2.stable.mono.official.ed1daf0bf |

The verified local .NET editor was selected with `GODOT_BIN`. Bootstrap and native
import used it; this does not establish export-template or extracted-package
acceptance. Docker Linux engine was operational. Development PostgreSQL remains
loopback port 55432. Database tests used the separate test user/database/volume
on 55433. The graphical live contract used loopback server port 5078 and a fresh
retained test schema on that test database. No development save, credential,
schema or Docker volume was deleted. Raw logs/captures remain ignored locally.
The live runner isolates database state, not Godot's user configuration: normal
startup loads and rewrites `user://settings.cfg`, retaining loaded preferences.
Custom bindings can affect the test. Run it serially with other database suites,
because its cleanup stops the shared test PostgreSQL container. Full client
configuration isolation remains a test-harness improvement.

## Commands and final bounded results

Run from the repository root with the verified Godot .NET editor selected.
All commands below completed with exit code 0 in this session:

| Command / suite | Result |
| --- | --- |
| `pwsh -NoProfile -File .\bootstrap.ps1` | PASS; source preparation, full asset pipeline, .NET build and editor import |
| `.\.venv\Scripts\python.exe tools/local_dev.py assets` | PASS; includes complete_skill_icons, all 60 icons, structural reference validation |
| `pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase` | PASS; core 33, gameplay review 34, transaction security 13, real network/PostgreSQL 18, save conflicts 5 |
| Security/world/migration probes in that launcher | PASS; security 5; 107 zones, 3,588 masonry tiles, 1,013 destinations, zero path failures; save migration 5 groups |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests/handoff -p "test_*.py" -v` | PASS; 74 tests |
| `.\.venv\Scripts\python.exe tools/local_dev.py signals` | PASS; captured/method/plain-object/async callbacks, GC, detachment, reattachment, reparenting, cleanup; native input routing |
| `dotnet build client/Kairnfall.Client.csproj -c Debug` | PASS; zero warnings and errors |
| Godot `res://Tests/PlayerExperienceContract.tscn` | PASS; 51 checks |
| Godot `res://Tests/ControlRulesContract.tscn` | PASS; 141 checks |
| Godot `res://Tests/VisualPresentationContract.tscn` | PASS; 102 checks and 68 fresh native fixture PNGs |
| `.\.venv\Scripts\python.exe tools/run_live_experience.py` | PASS; 83 checks with real Godot, server and isolated PostgreSQL |
| `pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke` | PASS; authenticated persistent world, inventory, skills, map; four new GPU-rendered images inspected |

The earlier `WorldView.Visible` compiler warning is absent; the existing
`IsWithinCameraBounds` repair was retained. Final native test logs were checked
for engine errors. Build/contract results are bounded evidence, not full-game
approval or hardware-keyboard approval.

The normal launcher was also run. Mouse account creation, character creation,
world entry, right-click movement and inventory opening were exercised in the
actual Windows game. The live contract separately tests native generated key and
pointer events, equipment/context-menu cycles, drag/drop, combat, owned loot,
chat input isolation, and reconnect/persisted state. Fixture equipment galleries
and in-memory visual scenes are explicitly fixtures, not normal progression.

## Retained failures and their disposition

- Repeated context-menu cycles reproduced `ObjectDisposedException` on an
  `EquipmentItemSlot`. Selection-stable menu opening now preserves that control;
  the strengthened regression checks identity across eight cancel cycles.
- A later live run against a reused test realm timed out collecting owned loot.
  Realm contamination was suspected, not conclusively established. The new
  runner creates a fresh retained schema; the unchanged pickup assertion passes
  there. Prior failed logs remain local. This does not certify every overlapping
  loot-target scenario.
- Intermediate bear clipping/floating paws and excessive floor grain contrast
  were found and repaired. Regression checks catch clipping, disconnected paws,
  and clipped floor colors; they do not certify anatomy by themselves.
- OS-driven password entry encountered a clipboard-open engine error during
  manual automation; retry succeeded. A synthesized inventory key did not open
  the panel in that manual session. Native generated key contracts pass, but
  actual hardware keyboard coverage remains unverified.
- Prior September 7 template-download timeout is historical. This session used
  the compatible local editor successfully; Windows export/package testing was
  not performed.

## Screenshot evidence and limits

Local evidence root: `artifacts/local/visual-review/20260908-194848/`.

- `before/`: 43 baseline native PNGs; `before/bear-repair/` retains 24 original
  common-creature frames captured before bear changes.
- `after/`: 68 final native PNGs, including village and Inventory/Character/Skills/
  Abilities/Map at 1280x720 and 1920x1080, four starter interiors, player movement/
  attack/cast, 24 equipment gallery frames, 24 creature gallery frames and icons.
- `after/contact-strips/`: contact strips assembled from those native captures.
- `logs/`: commands, successful results and failed intermediate attempts.
- `artifacts/local/live-experience/`: independently named retained test-schema
  runs with live contract logs and screenshots.
- `artifacts/local/smoke/`: timestamped real-server smoke screenshots and logs.

Final live evidence: `artifacts/local/live-experience/visual_b96685063a95483784b00e82d49a825c/`.
Final inspected smoke: `artifacts/local/smoke/1788882007320546200/`.
Final catalog file SHA-256:
`55f835bfb83884b3eccf5a6522e4eded9c74e85d1aab9115286106f4c2494884`.
This is a generated catalog checksum, not a Windows package checksum.

The disconnected banner in the visual contract images is expected for its
in-memory fixture; the separate smoke/live contract verifies authentication.
These are not twenty individually staged manual-play screenshots. Sampling four
frames does not approve every transition or every equipment combination.

## Remaining mandatory work

Full visual acceptance: **FAIL / incomplete**. Remaining defects include sparse,
oversized interiors without convincing furnishings or service workspaces;
overly broad/repetitive paved village areas; side-facing bow hand/string overlap;
and insufficient action distinction in several remaining creature poses. Bears
are improved but still stylized. Not every species, boss, material or animation
has been individually visually approved. HUD hierarchy still needs a longer
playtest with populated chat, combat and loot notifications.

Windows 125% scaling: **NOT RUN**. Windows 150% scaling: **NOT RUN**. Full hardware
keyboard/mouse acceptance, shop/dialogue/crafting manual coverage, all gear in
normal progression, two simultaneous graphical accounts, the complete 26-step
acceptance sequence, audio review, sustained 100-client load, frame-time/memory
targets, and extracted Windows client/server package tests remain unapproved.
No tag, signed binary, release package or public deployment was produced.

Launch the development game with:

```powershell
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1
```

Reproduce the isolated live regression after the normal build/test preparation:

```powershell
.\.venv\Scripts\python.exe tools/run_live_experience.py
```
