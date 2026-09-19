## Active workstream: Measured smoothness, performance, camera and gameplay polish

Status date: **2026-09-20**. Verified Checkpoint 0 implementation baseline: **`7175292ed9521c718c99c9fbbccc80b54374d9af`**. Machine-readable truth: `docs/handoff/CURRENT_EVIDENCE.json`. Release status: **NOT APPROVED — human acceptance remains.**

Checkpoint 0 is complete repository-side. It reconciles the inherited smoothness work with exact-head delivery evidence, archives the previous combat ledger byte-for-byte, and adds a smoothness-specific evidence validator plus adversarial regressions. The inherited motion changes at `1a4704fee2194bf3b9c51eb28b6e7408a7c1e72e` remain intact; Checkpoint 0 changes no gameplay source, movement speed, combat balance, tick frequency, rewards, saves, publication, deployment, or production infrastructure.

All 15 required workflows passed at exact implementation SHA `7175292ed9521c718c99c9fbbccc80b54374d9af`, including the Linux/Windows character-native matrix. Exact run and artifact IDs are in `docs/handoff/SMOOTHNESS_VERIFICATION.md`. The pre-sync documentation run failed only because `CURRENT_EVIDENCE.json` still named the historical combat implementation; the synchronized evidence now describes this workstream and retains exact-SHA/live-run/platform/source-footprint/release-boundary checks.

Checkpoint 0 makes no FPS or performance-improvement claim. The accepted 60 FPS goal corresponds to a 16.7 ms frame budget but has not yet been measured on owner Windows GPU hardware. The next authorized action is Checkpoint 1: bounded, opt-in frame-pacing and motion diagnostics with comparable cold/warm fixture baselines.

---

## Historical workstream: Combat feel and encounter presentation

Status date: **2026-09-18**. Verified implementation baseline: **`06776f6b0de7dbe02cab30a9e236e730c377de2e`**. Historical delivery SHA: **`bc9561846cd480c1e899190cb9b6f2df75a30176`**. Historical ledger: `docs/handoff/COMBAT_EVIDENCE_2026-09-18.json`.

Repository-side combat responsiveness/readability work remains preserved: bounded basic-attack buffering, queued-ability target/aim locking, sticky explicit targets, threat-aware automatic targeting, authoritative target/range feedback, urgent telegraph presentation, bounded approach behavior, and corrected damage-feedback attribution. Implementation details remain in `docs/COMBAT_FEEL.md` and historical verification remains in `docs/handoff/COMBAT_FEEL_VERIFICATION.md`.

---

## Historical workstream: Wayfarer character replacement

Status date: **2026-09-18**. Verified implementation baseline: **`16f2798edc6b90791548b5bf551eab6433ac9277`**. Historical evidence remains in `docs/handoff/CHARACTER_EVIDENCE_2026-09-18.json` and `docs/handoff/CHARACTER_VERIFICATION.md`.

Wayfarer remains the active actor source with the previously accepted 6,745 committed actor sheets, 415,040 validated frame cells, zero historical actor fallbacks, and permanent Linux/Windows character acceptance. Checkpoint 0 did not rebuild or replace the character pack.

---

# Kairnfall RPG — current handoff

## Historical workstream: New-player experience

Status date: **2026-09-16**. Verified implementation baseline: **`7b11027ba913781443871ece56c8ab13008408d5`**. Historical verification remains in `docs/handoff/NEW_PLAYER_VERIFICATION.md`.

The first-hour pass remains implemented and preserved: Bren Gale → two Field Rats → exactly-once class-compatible Rare Roadwarden weapon plus potion ingredients → player-controlled Inventory equip → ordinary Healing Potion craft → return to Bren and handoff into the persistent world. All eight classes retain distinct compatible reward identities, persisted authoritative progress, rollback/replay protection, mandatory reward recovery, reconnect/restart handling, and established-character exclusion.

The retained UI and first-hour regressions still cover the prior modal/focus/input/accessibility protections, supported Windows layouts/scales, keyboard and mouse paths, focus restoration, overflow, settings persistence, stale-state cleanup, and non-color-only error treatment.

## Verification

Checkpoint 0 exact run IDs, artifact identifiers, historical-integrity checks, native platform coverage, and limitations are recorded in `docs/handoff/SMOOTHNESS_VERIFICATION.md` and `docs/handoff/CURRENT_EVIDENCE.json`.

The current verification policy intentionally distinguishes:
- implementation SHA `7175292ed9521c718c99c9fbbccc80b54374d9af`, which contains the evidence validator/tests/archive;
- the later documentation-only synchronization SHA, which must leave that implementation baseline unchanged; and
- owner-hardware/subjective gates, which repository automation cannot certify.

## Continuation boundary

Continue with **Checkpoint 1 — Establish repeatable performance and motion measurements**. Do not skip directly to caching, camera easing, gameplay feel tuning, or world polish without measured evidence. Preserve server authority, snapshot coalescing, durable acknowledgement, saves, first-hour progression, Wayfarer assets, combat buffering, target retention, input rebinding/modal behavior, chat typing/focus restoration, and DPI support.

Keep `main` as the only persistent branch. Do not create PRs/issues, release, deploy, tag, alter production infrastructure, reset history, delete saves, or treat CI software rendering as Windows GPU performance.

## Release boundary

No release, publication, deployment, release tag or production-infrastructure change was authorized or performed. CI packages are test artifacts.

Human acceptance remains open for owner Windows performance/smoothness, camera/input feel after those checkpoints, independent visual review, audio listening, ordinary-account multiplayer/world walkthrough, physical Windows DPI/hardware input, owner-machine package launch where required, and production-scale validation before any capacity claim.
