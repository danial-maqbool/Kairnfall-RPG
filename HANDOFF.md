## Active workstream: Measured smoothness, performance, camera and gameplay polish

Status date: **2026-09-20**. Verified Checkpoint 1 implementation baseline: **`aa0df594bc8baa9405019b447c3226bc5904c012`**. Machine-readable truth: `docs/handoff/CURRENT_EVIDENCE.json`. Release status: **NOT APPROVED — human acceptance remains.**

Checkpoint 1 is complete repository-side. Opt-in bounded client diagnostics and a deterministic/native timing matrix now distinguish frame pacing, snapshot timing, motion error, world drawing, HUD work, panel stamp/refresh cost, managed allocation/GC scope, resource misses/loading, visible actors, draw submissions and memory indicators. The permanent Linux/Windows workflow is `Client performance and motion diagnostics`.

All 15 retained acceptance workflows plus the new diagnostic workflow passed at exact implementation SHA `aa0df594bc8baa9405019b447c3226bc5904c012`. Character acceptance passed Linux and Windows native jobs; the performance workflow also passed Linux and Windows jobs. Exact run and artifact IDs are in `docs/handoff/PERFORMANCE_DIAGNOSTICS_VERIFICATION.md`.

Three graphical Windows reference runs on the owner Acer Nitro ANV15-51 / RTX 4060 Laptop GPU at 1280×720 separated cold and warm behavior. Warm-cache frame p95 was 10.00 / 13.33 / 11.64 ms with no >33.3 ms frames. Cold first-use p99 was 126.40 / 97.45 / 100.00 ms. Inventory `PageStamp` p95 was 8.393 / 12.178 / 12.289 ms, and Skills first-use requested 60 uncached textures. These measurements rank the next optimization targets; they do not establish a universal 60 FPS guarantee.

Checkpoint 1 changes no gameplay behavior, movement speed, tick cadence, combat balance, rewards, saves, publication, deployment or production infrastructure. The next authorized action is **Checkpoint 2 — Apply the smallest measured frame-time wins**, beginning with panel-specific change detection and targeted hot-path presentation/resource caching.

---

## Historical workstream: Smoothness evidence reconciliation — Checkpoint 0

Checkpoint 0 implementation: `7175292ed9521c718c99c9fbbccc80b54374d9af`; delivery: `6e76af928af21c8ed7e1d14fd9fe59093174d228`. Historical machine-readable ledger: `docs/handoff/SMOOTHNESS_CHECKPOINT0_EVIDENCE_2026-09-20.json`. It remains byte-for-byte archived under blob `79779ce75560c5dd98132827181e8f56f35e1f70`.

## Historical workstream: Combat feel and encounter presentation

Implementation `06776f6b0de7dbe02cab30a9e236e730c377de2e`; delivery `bc9561846cd480c1e899190cb9b6f2df75a30176`. Historical evidence remains at `docs/handoff/COMBAT_EVIDENCE_2026-09-18.json`, `docs/COMBAT_FEEL.md`, and `docs/handoff/COMBAT_FEEL_VERIFICATION.md`.

## Historical workstream: Wayfarer character replacement

Verified implementation `16f2798edc6b90791548b5bf551eab6433ac9277`; evidence remains in `docs/handoff/CHARACTER_EVIDENCE_2026-09-18.json` and `docs/handoff/CHARACTER_VERIFICATION.md`. Wayfarer remains the active actor pipeline with zero historical actor fallback requirement.

## Historical workstream: New-player experience

Verified implementation `7b11027ba913781443871ece56c8ab13008408d5`; evidence remains in `docs/handoff/NEW_PLAYER_VERIFICATION.md`. The first-hour progression, all eight classes, authoritative persistence/replay protection, UI/focus/input safeguards and DPI support remain preserved.

## Continuation boundary

Continue with Checkpoint 2 only. Preserve server authority, snapshot coalescing, durable acknowledgements, saves, first-hour progression, Wayfarer assets, combat buffering/target retention, keyboard rebinding, modal blocking, chat typing/focus restoration and DPI support. Keep `main` as the only persistent branch. Do not release, deploy, tag, rewrite history or delete saves.

No release, publication, deployment, release tag or production-infrastructure change has been authorized or performed. CI packages remain test artifacts.
