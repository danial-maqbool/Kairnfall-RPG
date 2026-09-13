# Kairnfall current source handoff

Current status as of 2026-09-13.

Use the live `main` branch as the only authoritative source line. Current implementation baseline: `b28429037bb9ed96d6ec727cb84345445fed177e`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Historical dated files under `docs/handoff/` preserve earlier failures and repair checkpoints at their original revisions; they are not the current implementation status.

**NOT APPROVED — human acceptance remains.**

## Current project state

The Godot/.NET client, authoritative .NET server, PostgreSQL persistence, deterministic content/art pipeline and retained gameplay/Windows acceptance infrastructure are integrated on `main`.

Current technical evidence includes:

- Linux and Windows core, gameplay/malformed-input, world/progression and PostgreSQL/network suites.
- Authoritative concurrency and save-conflict coverage.
- Adversarial transaction security plus Windows/Linux transaction-integrity runs.
- Native Windows client compilation/contracts.
- Graphical progression and two-independent-client shared-world acceptance.
- Clean Windows package export, extraction in a path with spaces, launch, restart/reconnect and SHA-256 manifests.
- Staged 2/10/25/50-client load/reconnect acceptance with resource measurements.
- Per-source unauthenticated `/play` admission bounded to 120/minute before handshake work, with real-network 429 regression coverage.

Exact successful run IDs for the current baseline are in `CURRENT_EVIDENCE.json` and `VERIFICATION.md`.

## One checkout

For a new checkout:

```powershell
git clone --branch main https://github.com/danial-maqbool/Kairnfall-RPG.git
cd Kairnfall-RPG
git status --short
git rev-parse HEAD
```

For an existing checkout, preserve unrelated local work and update `main` without force-resetting or deleting saves/settings. Do not recreate historical `team/*` branches unless the owner explicitly changes the single-main policy.

## Canonical source and asset flow

```text
content_src/* -> tools/build_content.py -> content/catalog.json
tools/art/* -> tools/build_game_assets.py -> client/Assets/*
atelier/Assets + tools/integrate_atelier.py -> checksum-verified humanoid/equipment/NPC cohort
tools/complete_skill_icons.py -> complete skill icon set
tools/validate_game_assets.py -> structural/checksum/reference/audio validation
tools/review_visual_art.py -> review evidence, never artistic approval
```

## Local development setup

Install the documented Git, Python, PowerShell, .NET and Docker prerequisites. The project uses Godot 4.7.2 .NET and matching export templates.

Typical Windows development flow:

```powershell
pwsh -NoProfile -File .\bootstrap.ps1
pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase
.\.venv\Scripts\python.exe tools/local_dev.py signals
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1
```

Development and destructive integration-test databases remain separate. Preserve `.local/database.json` with its matching local Docker volumes. Never point destructive tests at personal or production player data.

## Human acceptance still pending

1. Owner Windows XP/HUD gameplay and reconnect/restart persistence pass.
2. Normal-play progression and class feel.
3. Independent artistic approval of player/equipment/creature presentation.
4. Full ordinary-account world/quest/objective/resource/boss traversal.
5. Sustained economy/balance feel.
6. Audio listening approval.
7. Production-scale load validation if a specific concurrent-player capacity will be advertised.
8. Physical Windows DPI/hardware-input review.
9. Owner-machine clean package extraction/launch if required for release sign-off.

Do not convert these to passed solely because structural, graphical, emulated, protocol or CI checks are green.

## Evidence and documentation policy

`docs/handoff/VERIFICATION.md` is the narrative current evidence authority; `docs/handoff/CURRENT_EVIDENCE.json` is its machine-readable counterpart. `docs/QA_MATRIX.md` defines the automated/human gate split and `docs/FINAL_AUDIT.md` carries the release decision.

`tools/documentation_contract.py` compares the evidence baseline with the latest non-documentation implementation commit and checks all current-facing status files for synchronized date, baseline and release boundary. `.github/workflows/documentation-contract.yml` runs it on every push.

Future technical work must update the current evidence ledger when the implementation baseline changes. Keep credentials, tokens, private paths, private chat/account data and database contents out of committed evidence.
