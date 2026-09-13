# Implementation status

Current status as of 2026-09-13.

Current implementation baseline: `3c4b6195e23f00fd34ae61e861dc7be2a2dadee3` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 12 adds synchronous modal cleanup and focus restoration, correct mouse/layer ordering, keyboard-following overflow for all existing pages, context-item cleanup, text/display setting resilience and current keybind discovery. See the [Task 12 engineering record](UI_UX_ENGINEERING.md). Task 13 was not started. These are automated engineering results; subjective usability and physical monitor DPI remain human evaluation.

## Current state

The repository contains the implemented Godot client, authoritative .NET server, PostgreSQL persistence, deterministic content/art pipeline and retained automated progression, world, economy, audio, multiplayer, combat-readability, concurrency/load, Windows and package gates.

The current technical baseline also includes the bounded unauthenticated `/play` admission path: 120 admissions per minute per source before handshake work, with a permanent real-network regression proving normal validation remains reachable and repeated unauthenticated pressure reaches HTTP 429.

The reference load gate is 2, 10, 25 and 50 simultaneous clients with reconnect behavior and server resource measurements. It is reference CI evidence, not a public production-capacity claim.

## Current exact-baseline evidence

All eight current-baseline workflows are successful and recorded in `docs/handoff/CURRENT_EVIDENCE.json`:

- Build and verify.
- Load acceptance.
- Transaction security regression.
- Transaction integrity on Windows and Linux.
- Compile Windows client source.
- Live progression breadth.
- Graphical multiplayer acceptance.
- Windows package acceptance.

`docs/handoff/VERIFICATION.md` records the exact run IDs and scope of those passes.

## Current release blockers

The remaining blockers are human or owner-environment acceptance decisions:

1. Owner Windows XP/HUD gameplay and reconnect/restart persistence pass.
2. Normal-play progression/class feel.
3. Independent artwork approval.
4. Full ordinary-account world/quest traversal.
5. Sustained economy/balance feel.
6. Audio listening approval.
7. Production-scale load validation if a specific capacity will be advertised.
8. Physical Windows DPI/hardware-input review.
9. Owner-machine clean package extraction/launch if required for release sign-off.

## Documentation authority

For current status use, in order:

1. `docs/handoff/CURRENT_EVIDENCE.json` for machine-readable baseline/workflow evidence.
2. `docs/handoff/VERIFICATION.md` for the narrative evidence record.
3. `docs/QA_MATRIX.md` for acceptance-gate definitions.
4. `docs/FINAL_AUDIT.md` for the release decision.
5. this file for continuation context.

Dated handoff/review files remain historical evidence and must not override the current status above. `tools/documentation_contract.py` enforces that the machine ledger matches the latest non-documentation implementation commit and that the current-facing status files stay synchronized.

## Release status

**NOT APPROVED — human acceptance remains.**

Do not claim a public persistent production realm is deployed unless one is actually running and verified.
