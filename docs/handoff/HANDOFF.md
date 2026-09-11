# Kairnfall current source handoff

Current status as of 2026-09-11.

Use the live `main` branch as the only authoritative source line. Historical dated handoff files under this directory preserve earlier failures and repair checkpoints, but they are not the current implementation status.

Implementation baseline audited before the documentation-only Task 11 consolidation: `defec56aadf5bc01289b4c7ec8c0e422b918624f`.

## Current project state

Repository-side implementation and automated acceptance are complete for Tasks 2–10. Task 11 is the documentation consolidation. Task 1 is implemented and its final hands-on Windows XP/HUD gameplay verification is intentionally deferred to the owner.

`docs/handoff/VERIFICATION.md` is the current evidence record.
`docs/QA_MATRIX.md` defines the current automated/human gate split.
`docs/FINAL_AUDIT.md` contains the release decision.
`docs/requirements/ACCEPTED_REQUIREMENTS.md` remains the accepted product scope.

**Release status remains NOT APPROVED because human acceptance gates remain.**

## One checkout

For a new checkout:

```powershell
git clone --branch main https://github.com/danial-maqbool/Kairnfall-RPG.git
cd Kairnfall-RPG
git status --short
git rev-parse HEAD
```

For an existing checkout, preserve unrelated local work and then update `main` without force-resetting or deleting saves/settings.

Do not recreate historical `team/*` branches. New work should remain on the single intended `main` line unless the owner explicitly changes that policy.

## Canonical source and asset flow

```text
content_src/* -> tools/build_content.py -> content/catalog.json
tools/art/* -> tools/build_game_assets.py -> client/Assets/*
atelier/Assets + tools/integrate_atelier.py -> checksum-verified humanoid/equipment/NPC cohort in client/Assets
tools/complete_skill_icons.py -> complete skill icon set
tools/validate_game_assets.py -> structural/checksum/reference/audio validation
tools/review_visual_art.py -> review evidence, never artistic approval
```

The refined Atelier player renderer is checked in under `atelier/forge/refined_body.py`. Permanent visual verification regenerates the 12 player body sheets and requires source/output parity. The temporary workflow that wrote generated body assets back to `main` has been removed.

## Current verified automated coverage

### Progression and classes

- 60/60 skills are exercised through real authoritative activity routes.
- Skill XP, level transitions, Character XP contribution, unlock thresholds and persistence are checked.
- 8/8 class kits and 120 class abilities are exercised through real effect handlers.
- Task 2 final CI: run `34550409865` on `d2eb494ff9f3dacc4e3e7fecab811ab7883ddc7a`.

### Character and creature visuals

- 12 shipped base player variants.
- 13 visible equipment slots with isolated review sheets.
- 100 normal creatures, 25 elites and 20 bosses.
- Idle/walk/attack/cast/hit/death coverage in four directions.
- Boss review cells preserve 128×128 poses without clipping.
- Refined player source/asset parity is enforced.
- Final Task 3 baseline `defec56aadf5bc01289b4c7ec8c0e422b918624f` passed build run `34555269188`, visual matrix `34555269207`, and exact visual review `34555269185`.

### World and quests

- Automated world audit covers 109 zone-anchor checks.
- Automated quest audit covers 166 quest-anchor checks.
- Dynamic resources such as skinned carcasses are classified separately from static seeded nodes.

### Economy and audio

- Economy audit checks authored price spreads, crafting value relationships, tier progression, rarity distribution, gold sinks and boss-drop design.
- All 22 runtime WAV files pass technical format/duration/peak/RMS/DC/clipping/loop-boundary analysis.

### Multiplayer

- Two separate graphical Godot clients authenticate, enter the shared world, exchange local chat, move using keyboard input and observe peer movement.
- Retained protocol suites cover party, trade, loot ownership, reconnect and server restart.
- Graphical multiplayer acceptance run `34534712045` passed.

### Load and Windows

- Reference load gate exercises 4, 8 and 16 active clients in staged windows and records tick/snapshot latency, DB commits, RSS and CPU.
- Native Windows display/input automation covers keyboard/mouse plus 125%/150% scale emulation at 1280×720 and 1920×1080 for HUD, XP bars, inventory/equipment, crafting, minimap and map.
- Windows package CI exports with the pinned Godot .NET toolchain/templates, copies client/server to a clean path containing spaces, launches outside the source tree, restarts/reconnects and creates SHA-256 manifests.

## Local development setup

Install the repository's documented Git, Python, PowerShell, .NET and Docker prerequisites. The project bootstrap uses the verified Godot 4.7.2 .NET toolchain and matching export templates.

Typical Windows development flow:

```powershell
pwsh -NoProfile -File .\bootstrap.ps1
pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase
.\.venv\Scripts\python.exe tools/local_dev.py signals
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1
```

Development database and integration-test database remain separate. Preserve `.local/database.json` with its corresponding local Docker volumes. Never run destructive test commands against personal or production player data.

## Human acceptance still pending

The following remain human/owner acceptance rather than missing repository implementation:

1. Task 1 final Windows XP/HUD gameplay pass, including visible progression pacing and reconnect/restart persistence.
2. Normal-play feel across skills/classes.
3. Independent artistic approval of player/equipment/creature presentation.
4. Full ordinary-account world/quest/objective/resource/boss traversal.
5. Sustained economy/balance feel.
6. Audio listening approval.
7. Production-scale load target if a specific concurrent-player capacity will be advertised.
8. Physical Windows monitor DPI/input review.
9. Owner-machine clean package extraction/launch if required by the release process.

Do not convert these to passed solely because their corresponding structural, graphical, emulated, protocol or CI checks are green.

## Evidence policy

Record exact commit SHA, relevant workflow/run IDs, OS/tool versions, failures, fixes and artifact locations. Keep sensitive credentials, account data, private Windows paths and database contents out of committed evidence.

Historical September 7–9 handoff documents remain available for provenance. They include statements that were true at their own revisions—such as missing client work, untested DPI/load/package gates, or failed setup downloads—but those statements are superseded for current status by `VERIFICATION.md`, `QA_MATRIX.md`, and `FINAL_AUDIT.md`.

When future acceptance changes, update those three current-status files together.
