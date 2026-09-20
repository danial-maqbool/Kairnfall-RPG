## Active workstream: Measured smoothness, performance, camera and gameplay polish

Status date: **2026-09-20**. Verified Checkpoint 2 implementation baseline: **4e81db842bb09c00b4565e4d2daedd45d254943a**. Machine-readable truth: docs/handoff/CURRENT_EVIDENCE.json. Release status: **NOT APPROVED — human acceptance remains.**

Checkpoint 2 is complete repository-side. It narrows Inventory/Bank refresh detection to actual page dependencies, bypasses repeated texture-key validation only for already-validated cache entries, and updates the local visible-equipment presentation map on accepted snapshots instead of every draw. No gameplay behavior changed.

Exact Windows CI same-process benchmark: Inventory stamp **10.1389 → 5.91132 µs/call** and **7,712 → 192 allocated bytes/call** over 5,000 iterations. Three owner Windows exact-head repetitions measured legacy **7.975 / 10.362 / 9.104 µs** versus candidate **3.460 / 4.260 / 3.650 µs**. Whole-frame results remain noisy and are not converted into a broad percentage claim. Cold first-use loading remains deferred.

All 15 retained acceptance workflows plus Client performance and motion diagnostics passed at exact implementation SHA 4e81db842bb09c00b4565e4d2daedd45d254943a. Exact run/artifact IDs and before/after measurements are in docs/handoff/PERFORMANCE_OPTIMIZATION_VERIFICATION.md.

Checkpoint 2 changes no movement speed, authoritative tick cadence, combat balance, rewards, saves, progression, publication, deployment or production infrastructure. The next authorized action is **Checkpoint 3 — Make motion, labels, picking, and clocks consistent**.

---

## Historical workstream: Performance/motion diagnostics — Checkpoint 1

Implementation aa0df594bc8baa9405019b447c3226bc5904c012; delivery efd418c4233802e91f5e0dd861b73119addb850d. Historical ledger: docs/handoff/SMOOTHNESS_CHECKPOINT1_EVIDENCE_2026-09-20.json.

## Historical workstream: Smoothness evidence reconciliation — Checkpoint 0

Implementation 7175292ed9521c718c99c9fbbccc80b54374d9af; delivery 6e76af928af21c8ed7e1d14fd9fe59093174d228. Historical ledger: docs/handoff/SMOOTHNESS_CHECKPOINT0_EVIDENCE_2026-09-20.json.

## Historical workstream: Combat feel and encounter presentation

Implementation 06776f6b0de7dbe02cab30a9e236e730c377de2e; delivery bc9561846cd480c1e899190cb9b6f2df75a30176. Historical evidence remains in docs/handoff/COMBAT_EVIDENCE_2026-09-18.json, docs/COMBAT_FEEL.md, and docs/handoff/COMBAT_FEEL_VERIFICATION.md.

## Continuation boundary

Continue with Checkpoint 3 only. Preserve server authority, snapshot coalescing, durable acknowledgements, saves, first-hour progression, Wayfarer assets, combat buffering/target retention, keyboard rebinding, modal blocking, chat typing/focus restoration and DPI support. Keep main as the only persistent branch. Do not release, deploy, tag, rewrite history or delete saves.

No release, publication, deployment, release tag or production-infrastructure change has been authorized or performed. CI packages remain test artifacts.
