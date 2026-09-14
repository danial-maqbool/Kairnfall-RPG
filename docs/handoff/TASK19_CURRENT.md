# Task 19 current state

Current status as of 2026-09-14.

Task 19 implementation baseline: `dbec66155142caa96dd6612eea97a164a050bcd7` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

**NOT APPROVED — human acceptance remains.**

Repository-side Task 19 is complete. The implementation adds four sparse profession chains to existing regions only: Heartwood in The Old Boughs, Ghost Reed in Mosswater Basin, Moonfin in The Gull Isles, and Frostsilver in Glassmere. Rare-node recovery remains within the authored 6–10 minute window. Each chain has a gather resource, processed component, and regional specialty tool with bounded utility; finalization restores its exact authored inputs and value sink after global gear normalization.

The same baseline includes checked-in Atelier source coverage for all 12 new profession item identities and fixes Dialogue “Track objectives” so native input opens `Quests` while retaining the selected quest. Exact integrated verification run `34844649467` passed against `dbec66155142caa96dd6612eea97a164a050bcd7` and produced immutable artifact `10347388189` (`sha256:6ec245e07c024b330ce01d98937b7219d463e7cc6a5e94f30e8e7de2a2b7d172`).

Historical Task 18 evidence remains in `docs/handoff/TASK18_EVIDENCE.json` plus the Task 18 current/verification documents. Task 20 has not been started and requires explicit approval.
