## Active workstream: Measured smoothness, performance, camera and gameplay polish

Status date: **2026-09-20**
Repository: danial-maqbool/Kairnfall-RPG
Persistent branch: **main only**
Verified Checkpoint 2 implementation baseline: **4e81db842bb09c00b4565e4d2daedd45d254943a**
Evidence: docs/handoff/CURRENT_EVIDENCE.json
Release status: **NOT APPROVED — human acceptance remains.**

Checkpoint 2 is complete repository-side. Targeted changes reduce measured Inventory refresh overhead without changing gameplay rules: page-specific structural change detection, cached-key texture validation bypass, and accepted-snapshot visible-equipment caching.

### Measured result

Exact Windows CI same-process Inventory-stamp benchmark, 5,000 iterations: **10.1389 → 5.91132 µs/call** and **7,712 → 192 allocated bytes/call**. Owner RTX 4060 exact-head repetitions measured legacy **7.975 / 10.362 / 9.104 µs** versus candidate **3.460 / 4.260 / 3.650 µs**. Inventory PanelStamp p95 moved from **8.393 / 12.178 / 12.289 ms** before to **0.76 / 0.76 / 0.92 ms** after.

Whole-frame p50/p95/p99/max results remain in docs/handoff/PERFORMANCE_OPTIMIZATION_VERIFICATION.md. They show run-to-run variance, including slower warm/Crafting/Skills repetitions, so no broad frame-time percentage is claimed. Non-Inventory PanelStamp measurement scope changed to include equality comparison and is not directly comparable with Checkpoint 1.

Cold first-use loading remains deferred. The 60 FPS Windows target remains a target, not an achievement claim.

### Acceptance and hygiene

All 15 retained acceptance workflows plus the Linux/Windows performance diagnostics matrix passed on exact implementation SHA 4e81db842bb09c00b4565e4d2daedd45d254943a. Local build and all **42** evidence regression tests also pass. The pre-sync documentation failure is expected stale-ledger behavior and must be replaced by a green delivery-head contract after this synchronization.

- Gameplay-behavior changes: 0.
- Combat balance, movement speed, tick frequency, rewards and progression: unchanged.
- Historical Checkpoint 1 ledger remains byte-for-byte archived.
- Pre-existing untracked Godot .uid files remain unstaged.
- No release, publication, deployment, tag, history rewrite or save deletion occurred.

Next action: **Checkpoint 3 — Make motion, labels, picking, and clocks consistent.**
