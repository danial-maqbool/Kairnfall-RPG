# Combat feel and encounter presentation verification

Status date: **2026-09-18**  
Verified implementation baseline: **`06776f6b0de7dbe02cab30a9e236e730c377de2e`**  
Evidence ledger: `docs/handoff/CURRENT_EVIDENCE.json`  
Release status: **NOT APPROVED — human acceptance remains.**

This document records repository-side technical acceptance for **Combat feel and encounter presentation**. It does not grant subjective combat-feel, balance, artistic, audio, publication, deployment, or release approval.

## Exact-head required workflows

All 15 required workflows below completed successfully on exact `main` SHA `06776f6b0de7dbe02cab30a9e236e730c377de2e`:

| Workflow | Run ID |
| --- | ---: |
| Transaction security regression | 35336451370 |
| Compile Windows client source | 35336451361 |
| Live progression breadth | 35336451398 |
| Windows package acceptance | 35336451385 |
| Graphical multiplayer acceptance | 35336451404 |
| Load acceptance | 35336451444 |
| Build and verify | 35336451316 |
| Task 13 adversarial acceptance | 35336451396 |
| Release operations acceptance | 35336451412 |
| Transaction integrity on Windows and Linux | 35336451378 |
| New-player journey | 35336451358 |
| Character sprite acceptance | 35336451435 |
| Visual acceptance matrix | 35336451418 |
| Windows display and input acceptance | 35336451388 |
| Audio acceptance | 35336451291 |

Supplemental exact-head verification also passed: **Review exact visual candidate** run `35336451382` and **Art library source and visual verification** run `35336451415`.

The pre-synchronization **Documentation evidence contract** run `35336451417` failed as designed because `CURRENT_EVIDENCE.json` still described the preceding character-rebuild baseline. The documentation-only synchronization after `06776f6b0de7dbe02cab30a9e236e730c377de2e` does not change the verified implementation.

## Objective combat coverage

The retained native and integration suites exercise:

- a 0.25-second basic-attack queue that waits for authoritative cooldown readiness;
- held attack with no target without empty-target requests;
- release, menu, focus-loss, death/disconnect, and hard-stop queue cancellation;
- bounded short attack approach and no infinite replanning;
- 0.35-second ability buffering with original target/aim preservation;
- explicit-target retention and fail-closed missing/out-of-range/blocked target behavior;
- threat-aware automatic target priority;
- authoritative target health/range/pressure text and non-color-only reticle state;
- urgent telegraph presentation derived from server resolve time;
- native combat HUD cooldown and QUEUED feedback;
- accurate feedback attribution when a snapshot does not identify the damage source;
- server-authoritative combat, replay/security, persistence, multiplayer, reconnect and package regressions.

## Scope boundary

Relative to starting main `7658fdf0d505d886bc0058565eea5c7e9f907dc0`, the pass changed no `content_src` files and no `src/Kairnfall.Server` files. The sole `src/Kairnfall.Core` change is `CombatReadability.cs`, which derives presentation text/state from authoritative snapshots. No damage, cooldown, resource-cost, XP, loot, enemy-stat, or encounter-balance values were changed.

The previous verified character ledger is archived verbatim at `docs/handoff/CHARACTER_EVIDENCE_2026-09-18.json`.

Human-only acceptance remains for owner Windows combat feel, normal-play class/encounter balance, independent visual review, audio listening quality, physical hardware/DPI input behavior, full ordinary-account multiplayer/world play, and production-scale validation.
