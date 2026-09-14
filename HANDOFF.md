# Kairnfall handoff

Current status as of 2026-09-14. Current Task 20 implementation baseline: `5167d6323ac4264250fc4b64072450c0f6d69ead` on the single authoritative `main` branch. Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

**NOT APPROVED — human acceptance remains.**

Start with `docs/handoff/TASK20_CURRENT.md`, `docs/handoff/TASK20_VERIFICATION.md`, and `docs/SESSION_STATUS.md`.

Task 20 repository implementation is complete. The existing eight dynamic-event families now use a hardened authoritative director with overlap/aftermath exclusion, active-player region preference, absolute contribution eligibility with a floor of 4, late-arrival fairness, restart and reconnect-safe rewards, and clean aftermath reset. The overworld footprint is unchanged. Detached candidate `abc141dcaf82420c8289ebd47f8a7942aec6ee04` passed exact verifier run `34860458864`; all ten functional workflows at implementation head `5167d6323ac4264250fc4b64072450c0f6d69ead` also passed.

Historical Task 19 evidence is preserved in `docs/handoff/TASK19_EVIDENCE.json` and the existing Task 19 handoff documents. Publication and deployment remain unauthorized. Task 21 may begin only from the verified Task 20 delivery head.
