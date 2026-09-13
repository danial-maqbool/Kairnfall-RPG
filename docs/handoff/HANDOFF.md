# Kairnfall current source handoff

Current status as of 2026-09-13.

Use live `main` as the authoritative source line. Current Task 16 implementation/candidate baseline: `2365a0df98beca178e22c099f0f31cd5adf65e6e`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.
Owner acceptance procedure: `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

**NOT APPROVED — human acceptance remains.**

## Current technical state

Task 16 repository-side preparation is complete. Ten technical workflows pass at the exact candidate SHA: Build `34775900161`, Load `34775900163`, Transaction security `34775900154`, Windows/Linux transaction integrity `34775900126`, Windows client compile `34775900236`, Live progression `34775900143`, Graphical multiplayer `34775900159`, Windows package `34775900170`, Task 13 adversarial `34775900129`, and Release operations `34775900148`.

The deterministic owner package is `Kairnfall-Release-Candidate-2365a0df98be.zip`, Actions artifact `10324090750`, SHA-256 `45e00144c910c0b79daa327c30086bb604896a8a425b9391e57a9340ab61b54e`. Post-CI verification confirmed the outer checksum, package/document manifest, exact Actions provenance, bundled owner-runbook hash, and all three inner package hashes.

Task 16 fixes concrete release-preparation defects without redesigning working gameplay: manifest document filenames now match the outer bundle; candidate provenance includes Actions run/artifact identity; the live reconnect evidence correctly rejects acknowledged XP loss without falsely requiring XP to remain frozen while an already in-flight hostile action completes; and the owner runbook is bundled and hashed with the candidate.

Historical Task 15 recovery/release evidence remains at `83a99948c7e96ff1ed568b5090b3138294b8e713`. Historical Task 14 display/input, visual and technical-audio evidence remains at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a` with original run IDs preserved in `CURRENT_EVIDENCE.json`.

## Manual phase

The owner should now perform `docs/qa/TASK16_OWNER_ACCEPTANCE.md` against the exact candidate. Do not substitute another build. Record objective defects separately from subjective feedback and include exact reproduction/evidence. Human results are added only after the owner reports them.

If a later fix changes the executable/package, produce a new exact candidate and repeat only the manual checks plausibly affected by that change plus required exact-head CI.

No GitHub release, tag or public deployment is authorized. Do not start Task 17 without explicit owner authorization.
