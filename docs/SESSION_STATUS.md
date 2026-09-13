# Implementation status

Current status as of 2026-09-13.

Current implementation baseline: `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 14 is repository-side complete: a permanent release-candidate sentinel now drives the accepted automation matrix against one exact source revision. All twelve technical workflows passed at the candidate SHA. See `docs/qa/RELEASE_CANDIDATE_ACCEPTANCE.md`. Task 15 was not started.

## Current exact technical evidence

The exact candidate is `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. Successful Task 14 runs cover Build/verify, Task 13 adversarial testing, load, transaction security/integrity, Windows client, progression, graphical multiplayer, Windows package, Windows display/input, visual acceptance and audio acceptance. Exact run IDs are recorded in `docs/handoff/CURRENT_EVIDENCE.json` and `docs/handoff/VERIFICATION.md`.

The reference load gate remains 2, 10, 25 and 50 simultaneous clients with reconnect/resource evidence. It is not a production-capacity claim.

## Remaining release blockers

The remaining blockers are human or owner-environment decisions: owner Windows gameplay/persistence, normal-play feel, independent human review where required, artistic approval, ordinary-account world traversal, economy/balance feel, audio listening, physical Windows DPI/input, owner package launch where required, and any separately advertised production-scale load target.

## Documentation authority

1. `docs/handoff/CURRENT_EVIDENCE.json` — machine-readable baseline/workflow evidence.
2. `docs/handoff/VERIFICATION.md` — narrative Task 14 exact-run evidence.
3. `docs/qa/RELEASE_CANDIDATE_ACCEPTANCE.md` — Task 14 mechanism, matrix and evidence boundaries.
4. `docs/qa/INDEPENDENT_FINDINGS.md` — Task 13 adversarial findings/retests.
5. `docs/QA_MATRIX.md` — automated/human gate split.
6. `docs/FINAL_AUDIT.md` — release decision.

**NOT APPROVED — human acceptance remains.**

Do not claim a public persistent production realm is deployed unless one is actually running and verified.
