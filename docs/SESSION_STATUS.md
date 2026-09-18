## Active workstream: Combat feel and encounter presentation

Status date: **2026-09-18**. Verified implementation baseline: **`06776f6b0de7dbe02cab30a9e236e730c377de2e`**. Evidence: `docs/handoff/CURRENT_EVIDENCE.json`. Release status: **NOT APPROVED — human acceptance remains.**

Repository-side combat feel/readability work is complete on `main`. The client now has a 0.25-second authoritative basic-attack buffer, a 0.35-second ability buffer that preserves the original target/aim, explicit-target retention, threat-aware automatic target priority, bounded short approach, authoritative target/range/pressure feedback, urgent telegraph presentation, and corrected hit-feedback attribution. Damage, cooldown resolution, encounter balance, authored content, saves, and server combat handlers are unchanged.

All required exact-head workflows passed at `06776f6b0de7dbe02cab30a9e236e730c377de2e`. See `docs/COMBAT_FEEL.md` and `docs/handoff/COMBAT_FEEL_VERIFICATION.md`. Human owner play remains required for subjective responsiveness, combat weight, balance feel, visual quality, audio mix, and physical hardware behavior.

The Wayfarer character replacement and first-hour sections below are retained as historical verified context.

---

## Active workstream: Wayfarer character replacement

Status date: **2026-09-18**. Verified implementation baseline: **`16f2798edc6b90791548b5bf551eab6433ac9277`**. Evidence: `docs/handoff/CURRENT_EVIDENCE.json`. Release status: **NOT APPROVED — human acceptance remains.**

Repository-side character replacement is complete on `main`. Wayfarer is the active actor source; the committed pack covers 1,245 base sheets, 5,500 additional motion sheets, 6,745 actor sheets and 415,040 frame cells with zero historical actor fallbacks. Linux and Windows native character acceptance both pass at the exact implementation baseline. See `docs/CHARACTER_REBUILD.md` and `docs/handoff/CHARACTER_VERIFICATION.md`.

---

# Kairnfall RPG — session status

Status date: **2026-09-16**  
Workstream: **New-player experience / first-hour retention, Grounded actor migration, and UI cohesion**  
Verified implementation baseline: **`7b11027ba913781443871ece56c8ab13008408d5`**  
Evidence: `docs/handoff/CURRENT_EVIDENCE.json`  
Release status: **NOT APPROVED — human acceptance remains.**

## Repository-side implementation status

The authorized first-hour pass is implemented on `main`. The fresh-player opening is a coherent authoritative sequence: Bren Gale → two Field Rats → exactly-once class-compatible Rare Roadwarden weapon and potion ingredients → player-controlled Inventory equip → ordinary Healing Potion craft → return to Bren and handoff into the existing persistent world. All eight classes have distinct compatible reward identities. Full-inventory rollback, replay protection, pending mandatory reward protection/recovery, reconnect/restart, death/respawn, out-of-order milestone retention and established-character exclusion are permanent regressions.

Grounded-2026 is the sole active actor runtime source for player bodies/hair, equipment overlays, NPC roles and mobs. Permanent acceptance verifies 1,245 actor sheets, 239,040 frame cells, 5,322 motion checks, 1,237 replaced historical actor hashes and zero actor fallbacks. Historical Atelier integration remains available only for compatible non-actor assets. Human artistic approval is not implied.

The UI pass preserves Task #12 modal/focus/input/accessibility protections and uses `PageLayoutProfiles` for real content-specific modal geometry and purpose summaries. Permanent Windows coverage includes 1024×720, 1280×720, 1920×1080 and 2560×1440 plus supported text/content scaling, keyboard/mouse focus paths, overflow, settings/error/stale-state behavior and modal blocking.

## Exact technical acceptance

All 14 workflows required by the current evidence guard succeeded at `7b11027ba913781443871ece56c8ab13008408d5`: Build and verify, Task 13 adversarial acceptance, Load acceptance, Transaction security regression, Transaction integrity on Windows and Linux, Compile Windows client source, Live progression breadth, Graphical multiplayer acceptance, Windows package acceptance, Windows display and input acceptance, Visual acceptance matrix, Grounded actor acceptance, Release operations acceptance, and New-player journey. Exact run IDs are recorded in `docs/handoff/NEW_PLAYER_VERIFICATION.md` and `CURRENT_EVIDENCE.json`.

Key exact-head measurements:

- New-player: 12/12 retained journey groups; 5/5 opening groups; 8/8 classes; 442 native player-experience checks; 1,169 native control/layout checks; 125 real-server/PostgreSQL live checks.
- Windows package artifact `10450049656`: 56,319,111-byte CI archive; clean export/launch/restart/reconnect smoke passed.
- Load reference: 2/10/25/50 real clients × 20 seconds; snapshot p95 204.8 ms; final rolling tick p95 42.8 ms; max sampled RSS 647,120 KiB; 10 reconnects in the 50-client stage.
- Grounded exact-head artifact `10450285632`: 24,799,957-byte evidence archive; zero actor fallbacks.

The pre-synchronization Documentation evidence contract failed as designed because the checked-in evidence still named the previous implementation. Documentation is now synchronized without changing the verified implementation baseline; the final documentation-only head must pass a fresh live evidence contract.

## Scope and hygiene

- Persistent branches: `main` only.
- New overworld regions: 0.
- Authored `content_src` footprint from starting main: only `content_src/opening_journey.py`.
- Tutorial reward identities added: 8 class-specific opening weapons; reward authority remains server-side.
- Old saves remain compatible; historical characters are not reset or silently enrolled.
- Temporary candidate/repair/diagnostic workflows and request files are removed.
- No release, publication, deployment, release tag or production-infrastructure change was authorized by this workstream.

## Human-only gates still open

Repository automation does not replace an owner Windows gameplay pass, uncoached first-hour timing/retention measurement, normal-play class/economy feel, independent artistic review, audio listening approval, a full ordinary-account world/quest walkthrough, physical Windows DPI/hardware-input inspection, owner-machine package extraction/launch where required, or production-scale validation before any capacity claim.

Do not start another development task implicitly. This status records the completed repository-side work and its remaining human acceptance boundary.
