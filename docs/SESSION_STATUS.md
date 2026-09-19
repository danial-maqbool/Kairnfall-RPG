## Active workstream: Measured smoothness, performance, camera and gameplay polish

Status date: **2026-09-20**  
Repository: `danial-maqbool/Kairnfall-RPG`  
Persistent branch: **main only**  
Verified Checkpoint 1 implementation baseline: **`aa0df594bc8baa9405019b447c3226bc5904c012`**  
Evidence: `docs/handoff/CURRENT_EVIDENCE.json`  
Release status: **NOT APPROVED — human acceptance remains.**

Checkpoint 1 is complete repository-side. The permanent opt-in performance/motion diagnostics collect bounded in-memory samples and produce one completion report; they do not add per-frame console or file output. Ten native scenarios and 36 deterministic timing schedules cover cold/warm loads, dense actors, moving creatures, movement timing, combat, panels, interiors, 30/60/120/144 FPS schedules, regular/interstitial/irregular/duplicate/delayed/coalesced/stalled delivery and long-idle starts.

### Exact technical acceptance

All retained acceptance workflows plus the new `Client performance and motion diagnostics` workflow passed at exact SHA `aa0df594bc8baa9405019b447c3226bc5904c012`. The character run passed native Linux and Windows jobs; the diagnostics run passed native Linux and Windows jobs. Exact run/artifact IDs and reproduction commands are in `docs/handoff/PERFORMANCE_DIAGNOSTICS_VERIFICATION.md` and `docs/handoff/CURRENT_EVIDENCE.json`.

### Measured baseline

Owner Windows reference: Acer Nitro ANV15-51, i7-13620H, 16 GB RAM, RTX 4060 Laptop GPU, Godot 4.7.2 .NET/OpenGL compatibility, 1280×720 fixture. Three exact-head repetitions recorded warm-cache p95 10.00 / 13.33 / 11.64 ms with zero >33.3 ms frames; dense layered actors p95 11.11 / 13.22 / 9.52 ms; regular 10 Hz motion p95 position error 0.0153–0.0182 tile. Cold first-use p99 was 97–126 ms. Inventory stamp p95 was 8.39–12.29 ms. Skills first-use synchronously loaded 60 textures and produced 132–143 ms maximum frame intervals.

The ranked Checkpoint 2 targets are: first-use resource preparation; Inventory panel-specific change detection; warm managed-allocation/hot-path key/presentation caching; then later motion-timing correctness for interstitial unchanged samples. No percentage improvement is claimed before comparable after-runs exist.

### Scope and hygiene

- Checkpoint 1 gameplay-behavior changes: 0.
- Combat balance, movement speed, authoritative tick frequency, rewards and progression: unchanged.
- Historical Checkpoint 0 ledger remains archived byte-for-byte.
- Pre-existing untracked Godot `.uid` files were not staged.
- No release, publication, deployment, release tag, production-infrastructure change, history rewrite or save deletion occurred.

### Human-only gates still open

Owner Windows performance/smoothness acceptance, later camera/input-feel review, independent visual/readability review, audio listening, ordinary-account multiplayer/world walkthrough, physical Windows DPI/hardware input, owner-machine package launch where required, and production-scale validation remain human gates.

Next action: **Checkpoint 2 — Apply the smallest measured frame-time wins.**
