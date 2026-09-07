# Verification record

## Handoff status

This file separates historical evidence from results on the consolidated `handoff/local-qa` branch.
Full-game acceptance: not established.
Windows graphical/package acceptance: not established.
Sprite and audio quality acceptance: not approved.
Local host execution in the authoring session: blocked by repeated container/Python ClientError.
GitHub repository operations work. No pasted personal credential was used.

Fresh handoff checks are defined in `.github/workflows/local-handoff.yml`.
Record their run IDs, tested commits, counts, and outcomes below after they finish.
Do not infer a pass from a workflow being created or submitted.

## Historical evidence, not a pass for this checkout

| Revision or check | Observed evidence | Limit |
| --- | --- | --- |
| Main `c5d80d60f5803958da0a76a61f9aae436f49c310` | PR #21 merged actual trade-consent and stack-splitting repair plus 13 security tests. | Main did not contain the complete selected asset pipeline or local source setup. |
| Asset source `3d787bd8e41efb3d721e3b8ccf00f786243104b9` | Run 34113289960 passed 44,888 structural assertions; 1,523 PNG files, 562 animation sheets, 22 WAV files. | These were not gameplay tests. This handoff adds 60 skill icons that the old expected-reference set omitted. |
| Native client `f326b9aa87e1f1f5ee143d03d4756813e0165b0c` | Run 34116169448 passed the native Godot button signal contract. Runs 34116169286 and 34116169509 passed compilation/backend checks. | Not full graphical gameplay or Windows packaging. |
| Same native client | Run 34116169395 failed. Job 101723466042 passed assets and compilation, then failed the real client/import step. Windows-package job was skipped. | Diagnose and repair in the local runtime. Do not convert this failure to a pass through documentation. |

Run links:
- https://github.com/danial-maqbool/Kairnfall-RPG/pull/21
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34113289960
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34116169448
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34116169395

## Fresh handoff results

Pending execution/result review at initial document creation. Replace this section with exact results.
Record each tested code revision. Documentation-only follow-up commits do not retroactively test code.
Do not combine repeated platform runs into a misleading count of unique gameplay tests.

## Required local evidence

- Fresh clone, dependencies, source build, content regeneration, full asset references.
- Database isolation and authenticated connection; no development data modified by tests.
- Existing core, gameplay, security, network/PostgreSQL, and save-conflict suites.
- Native signal contract and real graphical smoke captures.
- Full clean-account acceptance sequence and two-client playthrough.
- Skill effects/unlocks, class identity, item/rune effects, quests, encounters, map tile reachability.
- Actual visual and audio reviews, not only image/audio file checks.
- Sustained load/performance results with hardware and duration.
- Crash/restart recovery and clean-directory Windows package execution.
