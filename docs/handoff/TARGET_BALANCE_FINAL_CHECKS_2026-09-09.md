# Targeting and balance: final integrated checks — 2026-09-09

This record supplements [the implementation handoff](TARGET_BALANCE_VERIFIED_2026-09-09.md). It does not grant visual, hardware, balance-playtest or release approval.

## Final tested implementation

Gameplay integration: `8e02613101194894186abc4a936dd99852ec7c30`.
Tested integration plus handoff: `658c16147661505d92b4c9c5ae77c9853ce5e069`.
Final request commit: `426366665ea8ccb27065a730d8b14aec947fdcdc`.

The final full workflow [34308543359](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34308543359) passed. Verify job `102330232751` completed every required stage. Diagnostic job `102332416720` identifies the tested revision as `658c16147661505d92b4c9c5ae77c9853ce5e069` and records these results:

| Test | Result |
| --- | --- |
| Client compilation | Zero warnings and errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session/status security probes | 5 passed |
| Real-network/PostgreSQL / save conflicts | 18 / 5 passed |
| Retained world, migration, furnishing, gear, maintenance and hunting stage | Passed |
| Challenge progression and combat curves | 9 groups; 50 exported scenarios |
| Actual-encounter support XP | 4 groups passed |
| Python handoff/importer tests | 118 passed |
| Native signal lifetime and input routing | Passed |
| Native player experience / control-layout checks | 52 / 1,040 passed |
| Live Godot/server/PostgreSQL | 101 checks passed |
| Authenticated graphical smoke | Passed |

Final graphical run [34308543364](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34308543364) passed rendering and evidence upload. Linux and Windows core jobs also passed in [34308543375](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34308543375).

Full evidence artifact: `10087767845`, `player-experience-658c16147661505d92b4c9c5ae77c9853ce5e069`.
Graphical artifact: `10087650360`, `visual-review-658c16147661505d92b4c9c5ae77c9853ce5e069`.

These are test-evidence archives, not Windows application packages. Native generated input is not human playtesting or a physical Windows keyboard test.

## Concurrent source preservation

Main advanced to `77c934a884a79d837154eea89fac7526258ac7a4` during final verification. That separate commit adds the supplementary `foundry/` library. It is a descendant of the final request commit.

The complete nonrecursive root trees were compared. Every existing root entry has the same object ID; only `foundry/` is new. In particular, `client`, `src`, `content_src`, `tools`, `tests`, `atelier`, `.github` and `.ci` are unchanged. The tested gameplay source therefore remains intact. This record preserves that addition instead of resetting main.

The Foundry library was not integrated into the running client or independently accepted by this task. Do not describe it as a new runtime graphics update based only on its presence in Git.

## Remaining known warning and acceptance limits

The final smoke log repeats the caught `Connection cleanup: ObjectDisposedException` at `GameRoot.Lifetime.cs:32`. Tests and process exit succeeded, but the cleanup defect is not repaired. Do not suppress it to obtain a clean log.

Independent image inspection and a coding-agent team did not run successfully in this environment. Windows physical input and DPI, human progression/class balance, audio listening, sustained multiplayer/load, measured hardware performance and extracted Windows packages remain open.

The requested targeting, denser distribution, nonlinear future XP, combat mastery, support-reward safeguards and adaptive HUD source is pushed and automatically verified. Whole-game and release acceptance remain unapproved. Existing earned levels and saved data are retained.
