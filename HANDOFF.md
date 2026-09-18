## Active workstream: Combat feel and encounter presentation

Status date: **2026-09-18**. Verified implementation baseline: **`06776f6b0de7dbe02cab30a9e236e730c377de2e`**. Machine-readable truth: `docs/handoff/CURRENT_EVIDENCE.json`. Release status: **NOT APPROVED — human acceptance remains.**

Repository-side combat responsiveness/readability work is complete: bounded basic-attack buffering, queued-ability target/aim locking, sticky explicit targets, threat-aware automatic targeting, authoritative target/range feedback, urgent telegraph presentation, bounded approach behavior, and corrected damage-feedback attribution. No combat balance, authored content, save, server-handler, publication, deployment, or production-infrastructure changes were made. Exact run evidence is in `docs/handoff/COMBAT_FEEL_VERIFICATION.md`; implementation details are in `docs/COMBAT_FEEL.md`.

The Wayfarer character replacement section below remains a completed historical workstream and its ledger is archived verbatim at `docs/handoff/CHARACTER_EVIDENCE_2026-09-18.json`.

---

## Active workstream: Wayfarer character replacement

Status date: **2026-09-18**. Verified implementation baseline: **`16f2798edc6b90791548b5bf551eab6433ac9277`**. Machine-readable truth: `docs/handoff/CURRENT_EVIDENCE.json`. Release status: **NOT APPROVED — human acceptance remains.**

Repository-side character replacement is complete. Wayfarer is the active actor source with 6,745 committed actor sheets, 415,040 validated frame cells, zero historical actor fallbacks, and permanent Linux/Windows character acceptance. The exact successful workflow set is recorded in `docs/handoff/CHARACTER_VERIFICATION.md`. The previous first-hour material below remains historical context and continues to be covered by the retained new-player regressions.

---

# Kairnfall RPG — current handoff

## New-player experience

Status date: **2026-09-16**.  
Repository: `danial-maqbool/Kairnfall-RPG`. Persistent branch: **main only**.  
Verified implementation baseline: **`7b11027ba913781443871ece56c8ab13008408d5`**.  
Machine-readable truth: `docs/handoff/CURRENT_EVIDENCE.json`.  
Release status: **NOT APPROVED — human acceptance remains.**

The repository-side first-hour pass is implemented. A fresh eligible character now follows one coherent opening in the existing shared world: meet Bren Gale, kill two Field Rats using server-owned combat credit, receive exactly one class-compatible Rare Roadwarden weapon plus potion ingredients, manually equip the weapon through Inventory, brew Healing Potion recovery consumables through ordinary Crafting, return to Bren, then continue into the normal world journey. All eight classes have distinct compatible reward identities.

Opening progress is persistent and authoritative. Full inventory rolls the reward grant back atomically; replay cannot duplicate it; the pending mandatory reward is protected/recoverable until equipped; reconnect/restart, death/respawn and valid out-of-order milestones retain progress. Established characters are not reset or silently enrolled, and historical `first_hour` state remains compatible.

Grounded-2026 is the sole active actor runtime source for player bodies/hair, equipment overlays, NPC roles and mobs. The permanent contract verifies 1,245 active sheets, 239,040 frame cells, 5,322 meaningful motion checks, 1,237 replaced historical hashes and zero actor fallbacks. Historical Atelier actor bytes are inactive; compatible non-actor integration remains. This is technical migration evidence, not artistic approval.

The UI pass keeps Task #12 protections and wires content-specific `PageLayoutProfiles` into actual modal geometry/purpose summaries. Windows native coverage spans 1024×720, 1280×720, 1920×1080 and 2560×1440 plus supported text/content scales, keyboard and mouse input, modal blocking, focus restoration, overflow, settings persistence, stale-state cleanup and non-color-only errors.

## Verification

All **14** required technical workflows succeeded at exact implementation SHA `7b11027ba913781443871ece56c8ab13008408d5`. Exact run IDs and measurements are in `docs/handoff/NEW_PLAYER_VERIFICATION.md` and `CURRENT_EVIDENCE.json`.

Key evidence includes 12/12 retained new-player groups, 5/5 opening groups across 8/8 classes, 442 native player-experience checks, 1,169 native control/layout checks and 125 real-server/PostgreSQL live checks. The Windows package CI artifact is `10450049656` (56,319,111-byte archive; clean export/launch/restart/reconnect acceptance passed). Load acceptance exercised 2/10/25/50 real clients for 20 seconds per stage with aggregate snapshot p95 204.8 ms, final rolling tick p95 42.8 ms and maximum sampled RSS 647,120 KiB. These are bounded CI results, not a production-capacity claim.

The pre-sync Documentation evidence contract failed only because the ledger still named the previous implementation; documentation is now synchronized in docs-only commits, which do not alter the verified implementation baseline. The final delivery head must pass the live documentation-evidence contract against the exact run IDs above.

## Continuation boundary

Read `AGENTS.md`, `docs/NEW_PLAYER_JOURNEY.md`, `docs/ART_DIRECTION.md`, `docs/ASSET_MIGRATION_FIRST_HOUR_UI.md`, `docs/handoff/NEW_PLAYER_CURRENT.md`, `docs/handoff/NEW_PLAYER_VERIFICATION.md`, and `docs/handoff/CURRENT_EVIDENCE.json` before continuing. Do not restart this completed pass or begin another development task without explicit authorization.

The repository adds zero overworld regions. Relative to starting main `dff9f170f25f44c8ae024e8d94133f72d63f6446`, the only authored `content_src` delta is `content_src/opening_journey.py`. Temporary candidate/repair/diagnostic workflows and request files are removed. Keep only `main`; do not create branches, pull requests or issues. The prior Task 22 evidence remains archived verbatim in `docs/handoff/TASK22_EVIDENCE.json`.

## Release boundary

No release, publication, deployment, release tag or production-infrastructure change was authorized or performed. CI packages are test artifacts.

Human acceptance remains open for owner Windows gameplay, uncoached first-hour timing/retention, normal-play balance/class feel, independent artistic review, audio listening, full ordinary-account world/quest walkthrough, physical Windows DPI/hardware input, owner-machine package launch where required, and production-scale validation before any capacity claim.
