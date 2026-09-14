# Task 20 verification

Current status as of 2026-09-14.

Task 20 implementation baseline: `5167d6323ac4264250fc4b64072450c0f6d69ead`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

**NOT APPROVED — human acceptance remains.**

Detached exact candidate `abc141dcaf82420c8289ebd47f8a7942aec6ee04` passed `Verify exact player-experience candidate` run `34860458864`. Artifact `10356070613` (`player-experience-abc141dcaf82420c8289ebd47f8a7942aec6ee04`) has digest `sha256:8e185ca82e9a264bc38001c001224015a489893fdbf63865ece5e99046f56a5c`.

Implementation-head functional workflows at `5167d6323ac4264250fc4b64072450c0f6d69ead`:
- Build and verify — `34862412834` — success.
- Load acceptance — `34862412704` — success.
- Transaction security regression — `34862413032` — success.
- Transaction integrity on Windows and Linux — `34862412868` — success.
- Compile Windows client source — `34862412724` — success.
- Task 13 adversarial acceptance — `34862412800` — success.
- Live progression breadth — `34862412792` — success.
- Windows package acceptance — `34862412854` — success.
- Graphical multiplayer acceptance — `34862412720` — success.
- Release operations acceptance — `34862412821` — success.

Pre-synchronization Documentation evidence contract run `34862412700` failed only because `CURRENT_EVIDENCE.json` still named Task 19 baseline `dbec66155142caa96dd6612eea97a164a050bcd7`. That failure is preserved rather than relabeled.

Task 20 maintains 20 surface wilderness regions / 2,048,000 surface wilderness tiles, adds zero overworld regions, retains eight event families, keeps the global active-event cap at 3, and uses reward contribution floor 4. Historical Task 19 evidence is preserved in `TASK19_EVIDENCE.json`.
