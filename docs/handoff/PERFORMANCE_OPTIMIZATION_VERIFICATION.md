# Measured smoothness, performance, camera and gameplay polish — Checkpoint 2 verification

Status date: **2026-09-20**
Repository: danial-maqbool/Kairnfall-RPG
Checkpoint start: **efd418c4233802e91f5e0dd861b73119addb850d**
Verified implementation SHA: **4e81db842bb09c00b4565e4d2daedd45d254943a**
Machine-readable truth: docs/handoff/CURRENT_EVIDENCE.json
Release status: **NOT APPROVED — human acceptance remains.**

## What changed

Checkpoint 2 applies three measured presentation-only optimizations: Inventory/Bank refresh detection compares only page dependencies; PixelAssets.Texture skips repeated identifier validation only for already-validated cached/known-missing keys; and the local visible-equipment presentation map is updated on accepted snapshots instead of every draw. First-time asset keys are still validated, and the native fixture rejects ../outside.

No renderer rewrite, prediction, server rule, movement speed, tick frequency, combat balance, reward, save, progression, publication or deployment change is included.

## Direct targeted result

The exact Windows CI diagnostic artifact at run **35478205011** performs 5,000 legacy and candidate Inventory-stamp iterations in the same process:

| Metric | Legacy | Candidate |
| --- | ---: | ---: |
| Time per call | 10.1389 µs | 5.91132 µs |
| Allocated bytes per call | 7,712 B | 192 B |

Three exact-head owner Windows repetitions independently measured **7.975 / 10.362 / 9.104 µs** legacy versus **3.460 / 4.260 / 3.650 µs** candidate, and **7744 / 7736 / 7712 B** versus **248 / 248 / 192 B** allocated per call. This is a like-for-like targeted result, not a whole-client FPS percentage claim.

Inventory PanelStamp p95 moved from **8.393 / 12.178 / 12.289 ms** at Checkpoint 1 to **0.76 / 0.76 / 0.92 ms** at Checkpoint 2.

## Representative Windows after-runs

Owner reference: Acer Nitro ANV15-51, i7-13620H, 16 GB RAM, RTX 4060 Laptop GPU, Godot 4.7.2 .NET/OpenGL compatibility, 1280×720. Three exact-head runs were recorded.

| Scenario | p50 ms | p95 ms | p99 ms | max ms |
| --- | --- | --- | --- | --- |
| Warm cache | 12.96 / 14.29 / 9.50 | 20.42 / 16.67 / 13.03 | 24.82 / 27.96 / 14.58 | 24.82 / 27.96 / 15.34 |
| Dense layered actors | 10.00 / 12.17 / 9.09 | 12.99 / 15.28 / 12.15 | 21.75 / 22.80 / 16.67 | 46.77 / 22.80 / 29.93 |
| Motion start/stop/reversal | 10.42 / 8.33 / 8.69 | 14.71 / 11.11 / 12.12 | 16.67 / 12.76 / 13.64 | 21.42 / 15.51 / 14.39 |
| Combat telegraphs/labels | 8.71 / 8.78 / 9.09 | 11.63 / 11.67 / 13.99 | 17.16 / 14.48 / 16.67 | 45.93 / 15.50 / 36.66 |
| Inventory open | 11.16 / 9.52 / 9.09 | 16.67 / 16.67 / 15.32 | 22.67 / 29.83 / 27.60 | 131.55 / 86.21 / 93.89 |
| Crafting open | 13.64 / 12.53 / 12.12 | 18.19 / 18.06 / 16.67 | 130.40 / 90.47 / 143.29 | 130.40 / 90.47 / 143.29 |
| Skills open | 10.61 / 13.89 / 9.72 | 15.04 / 18.88 / 12.50 | 17.17 / 136.93 / 16.67 | 136.80 / 136.93 / 138.62 |
| Interior round-trip | 8.99 / 8.41 / 6.94 | 9.46 / 10.00 / 9.09 | 16.67 / 12.44 / 10.00 | 28.00 / 21.91 / 13.89 |

Whole-frame results vary across repetitions: some scenarios improve and some are slower, so no broad frame-time percentage is claimed. Non-Inventory PanelStamp phase timing changed scope in Checkpoint 2 to include equality comparison and is not directly comparable to Checkpoint 1.

Motion position-error p95 was **0.01 / 0.02 / 0.01 tiles**, versus **0.0153 / 0.0157 / 0.0182** before. No gameplay state is derived from rendered positions.

Cold first-use loading is deliberately deferred; this checkpoint did not preload the world or move Godot scene mutation to worker threads.

## Exact implementation-SHA Actions

| Workflow | Run ID | Conclusion | Artifact ID(s) |
| --- | ---: | --- | --- |
| Transaction security regression | 35478204961 | success | — |
| Compile Windows client source | 35478204976 | success | 10594289104 |
| Live progression breadth | 35478204963 | success | 10594908609 |
| Windows package acceptance | 35478204942 | success | 10595306561 |
| Graphical multiplayer acceptance | 35478204947 | success | 10595331401 |
| Load acceptance | 35478204977 | success | 10594343985 |
| Build and verify | 35478204941 | success | 10595156515, 10594638479 |
| Task 13 adversarial acceptance | 35478204982 | success | 10594918131 |
| Release operations acceptance | 35478204943 | success | 10594678387 |
| Transaction integrity on Windows and Linux | 35478204971 | success | 10595121371, 10594956717 |
| New-player journey | 35478205019 | success | 10595466349 |
| Character sprite acceptance | 35478204983 | success | 10595201974, 10594903634 |
| Visual acceptance matrix | 35478205052 | success | 10595211751 |
| Windows display and input acceptance | 35478204946 | success | 10595490107 |
| Audio acceptance | 35478220518 | success | 10595351041 |
| Client performance and motion diagnostics | 35478205011 | success | 10594659039, 10594464364 |

Character sprite acceptance run **35478204983** passed Linux and Windows native jobs. Performance diagnostics run **35478205011** passed Linux and Windows jobs. The pre-sync Documentation evidence contract run **35478204988** is expected failed evidence: all **42** evidence regressions passed first, then the stale Checkpoint 1 ledger was rejected.

## Reproduction

Owner Windows exact-head diagnostic:

    py -3.12 tools\get_godot.py --os windows
    dotnet build client\Kairnfall.Client.csproj -c Debug
    $m = Get-Content .tools\godot.json -Raw | ConvertFrom-Json
    $env:KAIRNFALL_PERF_DIAGNOSTICS = '1'
    $env:KAIRNFALL_PERF_OUTPUT = (Resolve-Path artifacts\performance-cp2).Path + '\windows-reference.json'
    $env:GITHUB_SHA = '4e81db842bb09c00b4565e4d2daedd45d254943a'
    & $m.binary --path client --rendering-method gl_compatibility --audio-driver Dummy res://Tests/PerformanceMotionDiagnosticsContract.tscn

Linux software/Xvfb results are regression evidence and are not used as Windows GPU performance claims.

## Boundary and next action

Checkpoint 2 demonstrates a targeted Inventory refresh win and preserves correctness across retained visual, input, progression, multiplayer, package, transaction, load and audio checks. The accepted 60 FPS target remains a target, not a claim. Cold-load preparation remains open.

Next action: **Checkpoint 3 — align authoritative and rendered actor positions, attached labels/picking, sample clocks and telegraph presentation timing without client-owned prediction.**
