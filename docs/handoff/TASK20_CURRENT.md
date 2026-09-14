# Task 20 current

Current status as of 2026-09-14.

Task 20 implementation baseline: `5167d6323ac4264250fc4b64072450c0f6d69ead` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

**NOT APPROVED — human acceptance remains.**

Task 20 hardens the existing dynamic-world-event system without increasing overworld footprint. Eight event families remain in place. The server-authoritative director prevents overlapping active/aftermath events, prefers eligible regions with active living players, enforces a meaningful absolute reward-contribution floor of 4, preserves late-arrival participation, persists/restarts active event state safely, prevents duplicate rewards across disconnect/reconnect, and returns regions to reusable state after aftermath cleanup.

Detached candidate `abc141dcaf82420c8289ebd47f8a7942aec6ee04` passed exact verifier run `34860458864`. Implementation head `5167d6323ac4264250fc4b64072450c0f6d69ead` passed all ten functional workflows. Historical Task 19 evidence is preserved in `docs/handoff/TASK19_EVIDENCE.json`.
