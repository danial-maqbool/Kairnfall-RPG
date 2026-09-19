# Measured smoothness, performance, camera and gameplay polish — Checkpoint 1 verification

Status date: **2026-09-20**  
Repository: `danial-maqbool/Kairnfall-RPG`  
Checkpoint start: **`6e76af928af21c8ed7e1d14fd9fe59093174d228`**  
Verified implementation SHA: **`aa0df594bc8baa9405019b447c3226bc5904c012`**  
Machine-readable truth: `docs/handoff/CURRENT_EVIDENCE.json`  
Release status: **NOT APPROVED — human acceptance remains.**

## What Checkpoint 1 measures

The diagnostics are opt-in (`KAIRNFALL_PERF_DIAGNOSTICS=1`), hold fixed-size in-memory histories of 4,096 samples, emit no per-frame console output, and perform no per-frame file writes. The native fixture writes one JSON report at completion. It measures frame interval p50/p95/p99/max, >33.3 ms and >50 ms frames, snapshot acceptance, motion advance, world draw, HUD, panel stamp/refresh, managed allocation/GC scope, texture misses/synchronous loads, snapshot arrival/authoritative spacing/age, rendered-authoritative position error, actor/draw counts, and memory indicators.

The permanent fixture covers 10 native scenarios: cold first-use, warmed cache, dense layered actors, stationary player with moving creatures, start/stop/reversal movement, combat telegraphs/labels, Inventory, Crafting, Skills, and interior round-trip. The deterministic motion matrix covers 36 cases: nine timing/motion patterns at 30/60/120/144 FPS, including continuous straight/diagonal motion, first movement after long idle, regular 10 Hz samples, unchanged interstitial samples, irregular spacing, duplicates, delayed/coalesced delivery, and a short stall.

## Windows graphical reference

Three exact-head runs used an Acer Nitro ANV15-51, Intel i7-13620H (10C/16T), 16 GB RAM, NVIDIA RTX 4060 Laptop GPU, NVIDIA OpenGL 595.71, Godot 4.7.2 .NET, `gl_compatibility`, and a 1280×720 fixture window. The desktop was 1920×1080. These are owner-machine reference measurements, not a universal performance guarantee.

| Scenario | samples/run | p50 ms | p95 ms | p99 ms | max ms | >33.3 ms | >50 ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Cold first-use | 86 / 82 / 82 | 10.00 / 10.61 / 9.72 | 17.85 / 16.38 / 16.67 | 126.40 / 97.45 / 100.00 | 126.40 / 97.45 / 100.00 | 2 / 2 / 2 | 2 / 1 / 2 |
| Warm cache | 112 / 90 / 109 | 9.09 / 11.67 / 9.09 | 10.00 / 13.33 / 11.64 | 10.00 / 20.04 / 13.31 | 10.00 / 20.04 / 15.30 | 0 / 0 / 0 | 0 / 0 / 0 |
| Dense layered actors | 117 / 98 / 122 | — | 11.11 / 13.22 / 9.52 | 12.17 / 15.42 / 10.79 | 17.02 / 15.42 / 12.88 | 0 / 0 / 0 | 0 / 0 / 0 |
| Stationary + moving creatures | 166 / 149 / 162 | — | 9.52 / 11.11 / 10.00 | 10.12 / 11.11 / 10.42 | 10.32 / 11.11 / 15.36 | 0 / 0 / 0 | 0 / 0 / 0 |
| Start/stop/reversal | 313 / 287 / 331 | — | 11.11 / 13.89 / 10.09 | 12.50 / 15.48 / 10.68 | 21.98 / 16.26 / 14.06 | 0 / 0 / 0 | 0 / 0 / 0 |
| Combat telegraphs/labels | — | — | 21.48 / 16.82 / 20.98 | 31.38 / 28.72 / 27.08 | 31.38 / 28.72 / 27.08 | 0 / 0 / 0 | 0 / 0 / 0 |
| Inventory open | — | — | 12.11 / 16.67 / 15.55 | 33.33 / 129.67 / 46.12 | 129.61 / 129.67 / 142.19 | 2 / 2 / 2 | 1 / 2 / 1 |
| Crafting open | — | — | 13.89 / 12.34 / 16.67 | — | 132.17 / 113.53 / 96.06 | — | 1 / 1 / 1 |
| Skills open | — | — | 10.15 / 11.31 / 13.89 | — | 142.17 / 143.30 / 131.93 | — | 1 / 1 / 1 |
| Interior round-trip | — | — | 12.50 / 10.42 / 10.55 | — | 27.82 / 33.62 / 15.75 | — | 0 / 0 / 0 |

Cold and warm data are intentionally separate. Warm world draw p95 was 2.459 / 3.468 / 2.701 ms; motion-advance p95 was 0.008 / 0.009 / 0.009 ms. Dense actors showed 49 visible actors p95 and about 2,160 instrumented texture/sprite submissions. Warm managed allocation p95 was 320.4 / 328.3 / 316.2 KiB per frame. The motion scenario managed heap p95 was 39.30 / 39.16 / 38.42 MiB with 8 / 7 / 9 Gen0 collections and no Gen1/Gen2 collections.

Regular 10 Hz motion produced snapshot-arrival p50 98.92–99.90 ms and p95 105.12–106.92 ms; authoritative spacing was exactly 100 ms p50/p95 in the fixture. Snapshot age p50 was 54.01–55.01 ms and p95 98.48–100.00 ms. No duplicate or reversed authoritative samples occurred in those native runs. Rendered-authoritative position-error p95 was 0.0153–0.0182 tile. The deterministic worst case was unchanged interstitial samples at 144 FPS: 0.2394-tile p95 error, 0.4525-tile max error, 0.1187-tile max forward lead, and zero final error after reconvergence.

First-use resource loading is a measured spike source: cold first-use loaded 7 textures synchronously; Inventory first-use loaded 13, Crafting 30, and Skills 60. Inventory `PageStamp` p95 was 8.393 / 12.178 / 12.289 ms and Inventory refresh p95 was 6.940 / 9.920 / 8.828 ms. Collector overhead probes added about 102.5–118.5 ns per synthetic instrumentation iteration.

## Ranked bottlenecks for Checkpoint 2

1. First-use synchronous resource loading / panel asset preparation: cold p99 97–126 ms; Skills first-use max 132–143 ms with 60 texture misses.
2. Inventory’s broad JSON `PageStamp`: p95 8.39–12.29 ms, followed by 6.94–9.92 ms refresh work.
3. Warm managed allocation remains roughly 316–328 KiB/frame p95 while the world submits about two thousand instrumented texture/sprite draws; targeted hot-path key/presentation caching is justified before any renderer rewrite.
4. Interstitial unchanged samples are the largest synthetic motion-error case; this is a timing-correctness target for the later presentation checkpoint, not a reason to increase visual lead.

## Exact implementation-SHA Actions

| Workflow | Run ID | Conclusion | Artifact ID(s) |
| --- | ---: | --- | --- |
| Transaction security regression | 35474314497 | success | — |
| Compile Windows client source | 35474961984 | success | 10593682942 |
| Live progression breadth | 35474963688 | success | 10593333535 |
| Windows package acceptance | 35474965196 | success | 10593073936 |
| Graphical multiplayer acceptance | 35474966697 | success | 10593974360 |
| Load acceptance | 35474314495 | success | 10593878311 |
| Build and verify | 35474314498 | success | 10594093169, 10593741968 |
| Task 13 adversarial acceptance | 35474314527 | success | 10594113141 |
| Release operations acceptance | 35474314492 | success | 10594157658 |
| Transaction integrity on Windows and Linux | 35474314489 | success | 10593933038, 10593462241 |
| New-player journey | 35474314501 | success | 10593754295 |
| Character sprite acceptance | 35474968567 | success | 10594485203, 10593648382 |
| Visual acceptance matrix | 35474970237 | success | 10593789837 |
| Windows display and input acceptance | 35474971869 | success | 10594167757 |
| Audio acceptance | 35474973486 | success | 10593263054 |
| Client performance and motion diagnostics | 35474314509 | success | 10594148339, 10594008225 |

Character sprite acceptance run **35474968567** passed both `verify (ubuntu-latest, linux)` and `verify (windows-latest, windows)`. Performance diagnostics run **35474314509** passed both `diagnostics (ubuntu-latest, linux)` and `diagnostics (windows-latest, windows)`.

The first diagnostic workflow attempt at `1ae26e8e…` is rejected evidence: its fixture passed 47 checks but the workflow correctly failed because generated skill icons were absent from that workflow’s asset preparation. The repair at `aa0df594…` added `tools/complete_skill_icons.py`; it did not suppress missing-art errors.

## Reproduction

On the owner Windows checkout, using the pinned toolchain:

    py -3.12 tools\get_godot.py --os windows
    dotnet build client\Kairnfall.Client.csproj -c Debug
    $m = Get-Content .tools\godot.json -Raw | ConvertFrom-Json
    $env:KAIRNFALL_PERF_DIAGNOSTICS = '1'
    $env:KAIRNFALL_PERF_OUTPUT = (Resolve-Path artifacts\performance-diagnostics).Path + '\windows-reference.json'
    $env:GITHUB_SHA = 'aa0df594bc8baa9405019b447c3226bc5904c012'
    & $m.binary --path client --rendering-method gl_compatibility --audio-driver Dummy res://Tests/PerformanceMotionDiagnosticsContract.tscn

CI reproduction is the permanent `Client performance and motion diagnostics` workflow. Linux uses Xvfb/software rendering and must not be compared directly to the owner Windows GPU results. The Windows CI job is headless and is regression evidence, not owner-GPU FPS evidence.

## Boundary

Checkpoint 1 changes diagnostics/tests/workflow instrumentation only. No movement speed, tick frequency, combat balance, rewards, saves, authoritative rules, publication, deployment, or production infrastructure changed. The accepted 60 FPS target remains a target, not a claim. Next action: **Checkpoint 2 — smallest measured frame-time wins.**
