# Measured smoothness, performance, camera and gameplay polish — Checkpoint 0 verification

Status date: **2026-09-20**
Repository: `danial-maqbool/Kairnfall-RPG`
Starting main: **`1a4704fee2194bf3b9c51eb28b6e7408a7c1e72e`**
Verified implementation SHA: **`7175292ed9521c718c99c9fbbccc80b54374d9af`**
Machine-readable truth: `docs/handoff/CURRENT_EVIDENCE.json`
Release status: **NOT APPROVED — human acceptance remains.**

## Scope and reconciliation

Checkpoint 0 changes delivery verification only. It preserves the inherited smoothness implementation at `1a4704fee2194bf3b9c51eb28b6e7408a7c1e72e` and does not change gameplay source, combat balance, movement speed, the 50 ms authoritative tick, progression, rewards, saves, publication, deployment, or production infrastructure.

The inherited smoothness delta from combat delivery `bc9561846cd480c1e899190cb9b6f2df75a30176` to `1a4704fee2194bf3b9c51eb28b6e7408a7c1e72e` is exactly:

- `client/Scripts/WorldView.CharacterMotion.cs`
- `client/Scripts/WorldView.cs`
- `client/Tests/CharacterPresentationContract.cs`

The previous active combat ledger was archived byte-for-byte as `docs/handoff/COMBAT_EVIDENCE_2026-09-18.json`; its git blob hash is `cf1a93b5cd2481dcc1de86ec10c72469d3828fc0`. Older character, onboarding, and task evidence files were not rewritten.

The prior smoothness head `1a4704f…` had 14 successful push workflows. Documentation run **35409060481** failed only with `Combat implementation evidence is stale.` The new evidence regression suite explicitly rejects stale SHAs, wrong repositories/branches, duplicated or missing runs, pending/failed runs, missing native platforms, and fabricated completion.

The implementation commit `7175292ed9521c718c99c9fbbccc80b54374d9af` changes only the archived ledger and evidence-validation tooling/tests. Its pre-sync documentation run **35469863304** passed **34/34** handoff evidence regression tests and then correctly rejected the still-active historical combat ledger. That pre-sync failure is not counted as acceptance; this document and `CURRENT_EVIDENCE.json` are the verified synchronization that resolves it.

## Exact implementation-SHA Actions

| Workflow | Run ID | Conclusion | Artifact ID(s) |
| --- | ---: | --- | --- |
| Transaction security regression | 35469863332 | success | — |
| Compile Windows client source | 35469876533 | success | 10592941561 |
| Live progression breadth | 35469878585 | success | 10592048370 |
| Windows package acceptance | 35469880577 | success | 10591943555 |
| Graphical multiplayer acceptance | 35469882629 | success | 10592527660 |
| Load acceptance | 35469863375 | success | 10591739405 |
| Build and verify | 35469863335 | success | 10592352440, 10592267720 |
| Task 13 adversarial acceptance | 35469863344 | success | 10592637242 |
| Release operations acceptance | 35469863431 | success | 10592961215 |
| Transaction integrity on Windows and Linux | 35469863325 | success | 10592961158, 10592167709 |
| New-player journey | 35469863323 | success | 10592348125 |
| Character sprite acceptance | 35469885192 | success | 10592038696, 10591993750 |
| Visual acceptance matrix | 35469887730 | success | 10592952154 |
| Windows display and input acceptance | 35469890700 | success | 10592173292 |
| Audio acceptance | 35469892924 | success | 10592462086 |

Character sprite acceptance run **35469885192** completed successfully on both required native jobs:

- `verify (ubuntu-latest, linux)` — success; artifact **10592038696**
- `verify (windows-latest, windows)` — success; artifact **10591993750**

All 15 rows above are tied to exact implementation SHA `7175292ed9521c718c99c9fbbccc80b54374d9af`. Cancelled, skipped, pending, old-head, pull-request-only, or duplicated runs are not accepted by the live evidence validator.

## Limits and next action

Checkpoint 0 establishes a truthful delivery baseline; it does **not** establish client FPS, frame-time percentiles, input latency, camera latency, or a 60 FPS achievement. The 16.7 ms target remains a target only. Linux CI/software rendering, screenshots, server-load data, and headless tests are not evidence of Windows GPU frame rate.

Next: **Checkpoint 1 — repeatable performance and motion measurements.** Add bounded opt-in client diagnostics and deterministic motion/render schedules, record cold/warm conditions and profiling overhead, and compare like-for-like runs before any performance percentage claim.
