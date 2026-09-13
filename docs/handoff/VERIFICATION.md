# Verification record

Current consolidated status as of 2026-09-13.

Current implementation baseline: `83a99948c7e96ff1ed568b5090b3138294b8e713` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 15 is repository-side complete for release engineering and operational recovery. The permanent `src/release-operations.trigger` drives the Task 15 acceptance surface without publishing a release or tag. The accepted technical candidate is `83a99948c7e96ff1ed568b5090b3138294b8e713`. Task 16 was not started.

**NOT APPROVED — human acceptance remains.**

## Exact Task 15 technical evidence

All ten Task 15 technical workflows below succeeded against the same implementation baseline `83a99948c7e96ff1ed568b5090b3138294b8e713`:

- Build and verify — run `34772773706`.
- Task 13 adversarial acceptance — run `34772773717`.
- Load acceptance — run `34772773733`.
- Transaction security regression — run `34772773725`.
- Transaction integrity on Windows and Linux — run `34772773737`.
- Compile Windows client source — run `34772773709`.
- Live progression breadth — run `34772773727`.
- Graphical multiplayer acceptance — run `34772773744`.
- Windows package acceptance — run `34772773761`.
- Release operations acceptance — run `34772773748`.

Together these runs cover Linux and Windows core builds, malformed input, authoritative adversarial/transaction checks, PostgreSQL/network integration, save conflicts, concurrency, native Windows client compilation, progression, two-client graphical multiplayer, 2/10/25/50-client reference load, clean Windows packaging/start/restart/reconnect, and the Task 15 database recovery/fail-closed drill.

## Task 15 operational and package guarantees

`Release operations acceptance` proved, in disposable PostgreSQL 18 databases, that the reusable operations utility can create and verify a checksum-protected backup, restore only into a fresh target, recover the pre-backup realm state, exclude post-backup mutation, reject a second authoritative writer, reject an unsupported future schema history, reject a tampered backup, and reconnect to restored state. The retained CI artifact omits the raw database dump and the drill checks that its disposable database password does not leak into operational logs.

`Windows package acceptance` proved that the client, server, operations utility and reconnect probe can be published into checksum-manifested archives, combined into a structured release-candidate bundle, extracted from a clean path containing spaces, and exercised through packaged server startup, restart/reconnect persistence and exported-client launch. The structured candidate manifest remains `publicationReady: false`.

No release or tag was created by Task 15.

## Reconnect persistence regression found and fixed

The first Task 15 candidate (`2653b3bab4c2836f84cdc7584d2668a3f3f8089d`) exposed a real failure in `Live progression breadth` run `34771705676`: defensive skill XP could increase after the client considered disconnect complete because the server had not yet removed the character from the active realm.

Commit `83a99948c7e96ff1ed568b5090b3138294b8e713` fixes that persistence boundary with an authenticated graceful-disconnect handshake. A normal `GameConnection.DisconnectAsync()` now waits for authoritative server detach/persist completion before returning, while broken-network shutdown still falls back to the existing abort/detection path. The succeeding exact-head `Live progression breadth` run is `34772773727`; no assertion or threshold was weakened.

## Retained Task 14 evidence provenance

Task 14's complete release-candidate matrix remains historical evidence at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. In particular, the Windows display/input run `34769719092`, visual acceptance run `34769719027`, and audio acceptance run `34769719057` were not relabeled as Task 15 exact-SHA results. They remain valid retained evidence for the unchanged surfaces they exercised, with their original SHA preserved in `CURRENT_EVIDENCE.json`.

## Human acceptance still required before release approval

1. Owner Windows gameplay pass for visible XP/level pacing and reconnect/restart persistence.
2. Normal-play progression and class feel.
3. Independent human adversarial/gameplay acceptance if independent approval is required.
4. Independent artistic approval at native/in-engine scale.
5. Full ordinary-account world and quest walkthrough.
6. Sustained economy and balance feel.
7. Audio listening approval.
8. Production-scale load validation if a specific concurrent-player capacity will be advertised.
9. Physical Windows DPI and hardware-input inspection.
10. Owner-machine clean Windows package extraction and launch if required for release sign-off.

Automated structural, graphical, hosted, protocol, recovery and same-agent results must not be relabeled as those human approvals or as proof that a public production realm is deployed.
