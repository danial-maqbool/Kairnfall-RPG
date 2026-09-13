# Task 15 release engineering candidate audit

Status date: 2026-09-13.

Current implementation baseline: `83a99948c7e96ff1ed568b5090b3138294b8e713` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 15 prepares release engineering and operational recovery without publishing a release. The permanent sentinel is `src/release-operations.trigger`.

**NOT APPROVED — human acceptance remains.**

## Exact technical candidate

All ten Task 15 technical workflows succeeded at `83a99948c7e96ff1ed568b5090b3138294b8e713`:

- Build and verify — `34772773706`.
- Task 13 adversarial acceptance — `34772773717`.
- Load acceptance — `34772773733`.
- Transaction security regression — `34772773725`.
- Transaction integrity on Windows and Linux — `34772773737`.
- Compile Windows client source — `34772773709`.
- Live progression breadth — `34772773727`.
- Graphical multiplayer acceptance — `34772773744`.
- Windows package acceptance — `34772773761`.
- Release operations acceptance — `34772773748`.

The candidate adds fail-closed database schema-history validation, a reusable PostgreSQL backup/verify/restore utility, a disposable recovery drill, an operations Windows archive, a structured release-candidate manifest, and setup/limitations documentation. The recovery design restores into a fresh database rather than overwriting an active realm.

The recovery drill verifies checksum-protected backup creation, restore of the pre-backup realm, exclusion of post-backup mutation, duplicate-writer rejection, future-schema rejection, tamper rejection, and reconnect after restore. Its retained artifact excludes the raw dump.

The Windows package gate builds checksum-manifested client/server/operations archives plus a combined candidate bundle, extracts it cleanly, runs the packaged server through restart/reconnect persistence, and launches the exported client. The generated manifest remains `publicationReady: false`.

The first candidate at `2653b3bab4c2836f84cdc7584d2668a3f3f8089d` exposed a genuine disconnect/persistence race in live progression run `34771705676`. The final Task 15 implementation baseline `83a99948c7e96ff1ed568b5090b3138294b8e713` adds server-acknowledged graceful disconnect; live progression then succeeded at run `34772773727` without weakening the assertion.

Task 14 display/input, visual and technical-audio evidence remains historical at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a` and is not relabeled as Task 15 exact-SHA proof.

No test threshold, gameplay rule, security control, or human gate is weakened by this work. No release or tag is created by Task 15.
