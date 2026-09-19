## Active workstream: Measured smoothness, performance, camera and gameplay polish

Status date: **2026-09-20**
Repository: `danial-maqbool/Kairnfall-RPG`
Persistent branch: **main only**
Verified Checkpoint 0 implementation baseline: **`7175292ed9521c718c99c9fbbccc80b54374d9af`**
Evidence: `docs/handoff/CURRENT_EVIDENCE.json`
Release status: **NOT APPROVED — human acceptance remains.**

Checkpoint 0 is complete repository-side. The inherited smoothness head `1a4704fee2194bf3b9c51eb28b6e7408a7c1e72e` is preserved, the historical combat ledger is archived byte-for-byte at `docs/handoff/COMBAT_EVIDENCE_2026-09-18.json`, and the active evidence contract now targets the smoothness/performance workstream. The implementation revision changes evidence tooling/tests/archive only; gameplay source, combat balance, movement speed, authoritative tick frequency, progression, rewards, saves, deployment, and production infrastructure are unchanged.

All 15 required exact-head workflows passed at `7175292ed9521c718c99c9fbbccc80b54374d9af`. Character sprite acceptance passed both `verify (ubuntu-latest, linux)` and `verify (windows-latest, windows)`. See `docs/handoff/SMOOTHNESS_VERIFICATION.md` for exact run and artifact IDs.

No client FPS result is claimed yet. The 60 FPS requirement implies a 16.7 ms target frame budget, but Checkpoint 0 does not measure Windows GPU rendering. Checkpoint 1 is next: bounded opt-in diagnostics, deterministic frame/network schedules, comparable cold/warm baselines, and a ranked bottleneck list before optimization.

---

## Historical workstream: Combat feel and encounter presentation

Status date: **2026-09-18**. Verified implementation baseline: **`06776f6b0de7dbe02cab30a9e236e730c377de2e`**. Historical delivery SHA: **`bc9561846cd480c1e899190cb9b6f2df75a30176`**. Evidence is retained at `docs/handoff/COMBAT_EVIDENCE_2026-09-18.json`, `docs/COMBAT_FEEL.md`, and `docs/handoff/COMBAT_FEEL_VERIFICATION.md`.

The completed combat pass remains preserved: 0.25-second basic-attack buffering, queued ability intent retention, explicit-target retention, authoritative targeting/range rules, bounded approach, urgent telegraph/readability presentation, and corrected feedback attribution. Damage authority, cooldown resolution, encounter balance, saves, and server combat ownership remain unchanged.

---

## Historical workstream: Wayfarer character replacement

Status date: **2026-09-18**. Verified implementation baseline: **`16f2798edc6b90791548b5bf551eab6433ac9277`**. Historical evidence remains in `docs/handoff/CHARACTER_EVIDENCE_2026-09-18.json` and `docs/handoff/CHARACTER_VERIFICATION.md`.

Wayfarer remains the active actor source with the previously accepted actor-sheet/frame-cell coverage and zero historical actor fallback requirement. Permanent Linux/Windows character-native acceptance remains in place.

---

# Kairnfall RPG — session status

## Historical workstream: New-player experience and UI cohesion

Status date: **2026-09-16**. Verified implementation baseline: **`7b11027ba913781443871ece56c8ab13008408d5`**. Historical evidence remains in `docs/handoff/NEW_PLAYER_VERIFICATION.md`.

The first-hour sequence, eight class paths, persisted authoritative progress, exactly-once reward behavior, reconnect/restart safeguards, UI layout profiles, modal/focus protections, settings/input coverage, and Grounded/Wayfarer actor migration protections remain preserved. Checkpoint 0 did not restart or change this work.

## Exact technical acceptance

For current Checkpoint 0, the required implementation-SHA set is:
Build and verify; Task 13 adversarial acceptance; Load acceptance; Transaction security regression; Transaction integrity on Windows and Linux; Compile Windows client source; Live progression breadth; Graphical multiplayer acceptance; Windows package acceptance; Windows display and input acceptance; Visual acceptance matrix; Character sprite acceptance; Release operations acceptance; New-player journey; and Audio acceptance.

All passed at exact SHA `7175292ed9521c718c99c9fbbccc80b54374d9af`. The active validator also requires unique run IDs, correct repository/branch/event/head identity, completed-success status, both character native platforms, historical evidence integrity, the allowed source footprint, retained human gates, and release boundaries.

## Scope and hygiene

- Persistent branches: `main` only.
- Checkpoint 0 gameplay-source changes: 0.
- Historical combat evidence archive blob: `cf1a93b5cd2481dcc1de86ec10c72469d3828fc0`.
- Inherited smoothness client delta remains the three previously landed files only.
- No release, publication, deployment, release tag, production-infrastructure change, history rewrite, or save deletion was authorized or performed.
- Pre-existing untracked Godot `.uid` files in the owner checkout were preserved and not staged.

## Human-only gates still open

Repository automation does not replace owner Windows GPU frame-time measurement and subjective smoothness, later camera/input-feel review, independent visual review, audio listening, a full ordinary-account multiplayer/world walkthrough, physical Windows DPI/hardware-input inspection, owner-machine package launch where required, or production-scale validation before any capacity claim.

Next action: **Checkpoint 1 — Establish repeatable performance and motion measurements.**
