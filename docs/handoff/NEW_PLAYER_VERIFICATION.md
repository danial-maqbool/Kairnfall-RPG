# New-player experience — verification evidence

Status date: **2026-09-15**.
Repository: `danial-maqbool/Kairnfall-RPG`; persistent branch: **main only**.
Implementation baseline: **4214c57692bd70196f4c50db0a95ca6f2a510f31**.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.
Release status: **NOT APPROVED — human acceptance remains.**

## Exact implementation-head workflows

Every run below completed successfully at the implementation SHA above before current-evidence synchronization. Run identifiers refer to this repository's GitHub Actions; no candidate-only or earlier-head success substitutes for these runs.

| Workflow | Run ID | Conclusion |
| --- | ---: | --- |
| Transaction security regression | 34916653785 | success |
| Compile Windows client source | 34916653731 | success |
| Live progression breadth | 34916653737 | success |
| Windows package acceptance | 34916653734 | success |
| Graphical multiplayer acceptance | 34916653638 | success |
| Load acceptance | 34916653673 | success |
| Build and verify | 34916653837 | success |
| Task 13 adversarial acceptance | 34916653645 | success |
| Release operations acceptance | 34916653651 | success |
| Transaction integrity on Windows and Linux | 34916653845 | success |
| New-player journey | 34916653660 | success |
| Windows native input and display | 34916653650 | success |
| Visual acceptance | 34916653656 | success |

The first eleven are required by the live documentation-evidence guard; the two supplemental native/visual workflows also passed. Visual acceptance is automated structure/presentation verification, not independent artistic approval. Release-operations acceptance is a disposable database backup/restore/fail-closed drill, not a deployment. Windows package output is a non-publishable CI artifact, not a release.

## Dedicated artifact and measured checks

Journey run `34916653660` produced artifact `10377072147`, named `new-player-journey-4214c57692bd70196f4c50db0a95ca6f2a510f31`.
Artifact digest: `sha256:fbe0f9534937eabd46ec9b323919f6fd3654ac923ad4709943a4e3b60e52053b`.
Its `revision.txt` equals the implementation baseline. The logs and fresh-spawn/combat frames were retrieved through the connected GitHub integration and inspected.

| Check | Verified result |
| --- | --- |
| Standalone new-player journey | 12/12 groups |
| Native player experience, including onboarding | 328 checks |
| Native control rules | 1,165 checks |
| Native XP HUD | 9 checks |
| Native signal and input routing | passed |
| Real-server/PostgreSQL native experience | 125 checks |
| Core regression | 38 passed, zero failed |
| Gameplay/malformed-input review | 34 passed, zero failed |
| Transaction security | 13 passed, zero failed |
| Isolated security probe | 5 passed, zero failed |
| Real-network integration | 20 passed, zero failed |
| Isolated database review | 5 passed, zero failed |
| Python handoff/guard regression | 139 tests passed, including 10 new evidence-guard tests |
| Full retained world probe | passed, including living public events, persistence, social, crafting and progression checks |
| Retained Task 21 dungeon depth | 3 passed, zero failed |
| Retained Task 22 endgame loops | 5 passed, zero failed |

The standalone journey log records ordinary quest acceptance, combat, owned loot, rune insertion, plank/handle crafting, quest claim and arrival at Dawnreach, reaching character level 3 through existing awards. Replay of the same quest receipt immediately and after state reload does not duplicate rewards. Fresh duplicate claims are rejected. The clock and reachable interaction proximity are controlled fixtures; this does not measure human time-to-kill or an unassisted session duration.

The native onboarding matrix covers fourteen combinations: 1024x720 at native content scale, plus 1280x720 and 1920x1080 at 100%, 125% and 150% content scale, each with 100% and 125% text scale. Assertions require actual visible line/glyph height, not just nonempty text or a metadata marker. They check containment and separation from chat, minimap, target frame, hotbar, navigation, attack/interact/target/dash buttons and the class-resource meter. Current-head frames show a readable starter movement tip, real objective/reward, non-overlapping welcome notice and an actual level-up maximum-health delta.

## Acceptance coverage

| Requested behavior | Automated evidence |
| --- | --- |
| Fresh valid objective; uninterrupted normal early sequence | Dedicated fresh fixture and `Next()` validation after real movement, talk, combat, loot, crafting, quest and transition APIs |
| Hint persistence, old saves and established-character eligibility | Serialized reload, missing-discovery defaults, old-character exclusion and real-server reconnect checks |
| Real level-up and real usable equipment upgrades | Authoritative before/after progression, socket/equip commands, non-regressive stat comparison, no fake login banner |
| Guidance cannot award XP/items/gold/reputation or skip quests | Allowlist and payload rejection, unchanged economy snapshots, rejected-command rollback, creation-only eligibility |
| Exactly-once reward and reconnect/replay protection | Existing quest/event receipts, saved claim state and noncontributor rejection; no new tutorial reward exists |
| Low-population multiplayer path | Solo public-event scheduling/participation/reward fixture and truthful zero-nearby-player native UI |
| Existing Task 20/21/22 systems | Full world probe, public-event contribution regression, dungeon/boss cleanup/exactly-once checks and faction/endgame contract/reputation tests |
| No overworld expansion | No authored `content_src` changes from starting main; serialized zone-footprint assertion; no new region or instance |
| Windows and existing suites | Exact-head Windows compile/native/package plus full core/world/security/adversarial/database/network workflows |

## Failure history retained

Candidate `0d04aca0ff18694311e0aeae64f14f95e8a67f68` passed candidate run `34912895819` and was integrated in `d5ac8c64b5822987f8ec0e34d5b165adf526ad2d`. Native-frame inspection exposed zero-height wrapped tips and welcome notices behind combat controls that marker-only checks had missed. Commit `bf7f79e5136006592e0038b04b9633a19fbf0725` reserved real scaled-font hint height, adjusted compact geometry and added stronger native assertions.

Those assertions correctly failed journey run `34915571582` at `3fdca6068b2e2688b9815ffd88541da34876b994`: the 1920x1080 desktop notification at 125% text scale extended into the class-resource HUD. Commit `4214c57692bd70196f4c50db0a95ca6f2a510f31` reserves two notification rows in both compact and desktop layouts. The same assertions passed in `34916653660`; none were removed or weakened.

Documentation run `34916653612` at the implementation baseline failed because current evidence still named Task 22. Its ten guard regressions passed. This was not treated as successful: evidence promotion was intentionally withheld until all functional workflows passed. The documentation-only delivery commit resolves the stale current-workstream record, preserves the previous Task 22 JSON blob verbatim and must pass a fresh documentation run at its own head.

## Delivery-head contract and limits

A handoff commit contains only `docs/**` and root `HANDOFF.md`, so it cannot change the verified gameplay, tests or workflows. The evidence guard independently verifies each required recorded run through the read-only Actions API, its exact implementation SHA/branch/repository/identity and completed-success status. Workflow, tooling, test or source edits invalidate the baseline. The guard also checks the seven temporary files are absent and archived Task 22 evidence has the original Git blob SHA `f6623a46db658f3f8c9ef3656a74722583380233`.

Fresh delivery-head Actions, including documentation, build, adversarial, journey and other triggered gates, are required in addition to this baseline evidence. Their status is attached to the exact main commit in Actions, avoiding an impossible self-referential documentation SHA. Before final delivery, confirm that comparison against the implementation is documentation-only and the remote branch list still contains only `main`.

No release, publication, deployment, release tag, production infrastructure change, permanent branch, pull request or issue was created for this work. Temporary candidate/edit/overlay request files and workflows are removed; the retained journey workflow is permanent regression coverage. Human first-hour timing, retention, subjective balance, artistic/audio approval and physical Windows hardware acceptance remain unmeasured or unapproved; they are not inferred from compilation, automated fixtures or generated asset counts.
