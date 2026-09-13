# Implementation status

Current status as of 2026-09-13.

Current implementation baseline: `83a99948c7e96ff1ed568b5090b3138294b8e713` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 15 is repository-side complete. It adds fail-closed database schema-history compatibility, a reusable PostgreSQL backup/verify/restore utility, a disposable operational recovery gate, a Windows operations archive, checksum/provenance manifests, and release-candidate setup/limitations/audit material. The Task 15 candidate remains explicitly non-published. Task 16 was not started.

## Current exact technical evidence

All ten Task 15 technical workflows are successful at `83a99948c7e96ff1ed568b5090b3138294b8e713`: Build and verify, Task 13 adversarial acceptance, load, both transaction gates, Windows client compilation, live progression, graphical multiplayer, Windows package, and release operations. Exact run IDs are recorded in `docs/handoff/CURRENT_EVIDENCE.json` and `docs/handoff/VERIFICATION.md`.

The release-operations gate proves backup checksum verification, restore into a fresh database, rollback-to-backup state, duplicate-writer rejection, unsupported-future-schema rejection, backup tamper rejection and reconnect after restore in disposable PostgreSQL 18. The Windows package gate proves the client/server/operations archives, checksums, structured candidate manifest, clean extraction, packaged restart/reconnect and exported-client launch. The manifest remains `publicationReady: false`.

The first Task 15 candidate exposed a real disconnect/persistence race in live progression. `83a99948c7e96ff1ed568b5090b3138294b8e713` fixes the normal disconnect boundary so client completion waits for authoritative detach/persist; live progression run `34772773727` then passed without weakening the assertion.

Task 14 display/input, visual and audio automation remains historical evidence at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a` and is intentionally not presented as Task 15 exact-SHA evidence.

The reference load gate remains 2, 10, 25 and 50 simultaneous clients with reconnect/resource evidence. It is not a production-capacity claim.

## Remaining release blockers

The remaining blockers are human or owner-environment decisions: owner Windows gameplay/persistence, normal-play feel, independent human review where required, artistic approval, ordinary-account world traversal, economy/balance feel, audio listening, physical Windows DPI/input, owner package launch where required, and any separately advertised production-scale load target.

## Documentation authority

1. `docs/handoff/CURRENT_EVIDENCE.json` — machine-readable current and historical workflow provenance.
2. `docs/handoff/VERIFICATION.md` — narrative Task 15 exact-run evidence and regression record.
3. `docs/release/CANDIDATE_AUDIT.md` — Task 15 release-engineering/recovery candidate audit.
4. `docs/release/WINDOWS_SETUP.md` and `docs/release/KNOWN_LIMITATIONS.md` — candidate operation/setup boundaries.
5. `docs/qa/RELEASE_CANDIDATE_ACCEPTANCE.md` — historical Task 14 exact-candidate mechanism.
6. `docs/qa/INDEPENDENT_FINDINGS.md` — Task 13 adversarial findings/retests.
7. `docs/QA_MATRIX.md` — automated/human gate split.
8. `docs/FINAL_AUDIT.md` — release decision boundary.

**NOT APPROVED — human acceptance remains.**

No release or tag was created by Task 15. Do not claim a public persistent production realm is deployed unless one is actually running and verified.
