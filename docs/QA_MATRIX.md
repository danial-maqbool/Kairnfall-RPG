# QA acceptance matrix

Current consolidated status as of 2026-09-13.

Current implementation baseline: `83a99948c7e96ff1ed568b5090b3138294b8e713`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 15 is repository-side complete for release engineering and operational recovery. The accepted Task 15 technical matrix contains ten exact-SHA workflows at `83a99948c7e96ff1ed568b5090b3138294b8e713`. Historical Task 14 display/visual/audio evidence remains pinned to `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a` instead of being relabeled. Task 16 was not started.

| Area | Current status | Exact evidence / remaining work |
| --- | --- | --- |
| Source / repository | **PASS** | Task 15 baseline `83a99948c7e96ff1ed568b5090b3138294b8e713`; permanent Task 15 sentinel and documentation drift contract retained. |
| Backend / malformed input | **PASS** | Build and verify `34772773706`. |
| Adversarial authority | **PASS AUTOMATED** | Task 13 adversarial acceptance `34772773717`; same-agent evidence, not independent approval. |
| Security / transactions | **PASS** | Transaction security `34772773725` and Windows/Linux integrity `34772773737`. |
| Database schema / recovery | **PASS DISPOSABLE OPERATIONS DRILL** | Release operations `34772773748`: schema fail-closed, backup checksum, fresh restore, rollback boundary, duplicate-writer rejection, future-schema rejection, tamper rejection and reconnect recovery. |
| Progression / classes | **PASS AUTOMATED; HUMAN FEEL PENDING** | Live progression `34772773727`; includes the fixed graceful-disconnect persistence boundary. |
| Native Windows client | **PASS AUTOMATED** | Client compilation `34772773709`. |
| Windows display / input | **RETAINED AUTOMATED EVIDENCE; PHYSICAL REVIEW PENDING** | Historical Task 14 run `34769719092` at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`; not relabeled as Task 15 exact-SHA evidence. |
| Art | **RETAINED STRUCTURAL/GRAPHICAL EVIDENCE; HUMAN ART APPROVAL PENDING** | Historical Task 14 visual run `34769719027` at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. |
| World / quests / economy | **PASS AUTOMATED; HUMAN WALKTHROUGH/BALANCE PENDING** | Build/adversarial world, persistence and database stages pass at the Task 15 baseline. |
| Audio | **RETAINED TECHNICAL EVIDENCE; LISTENING PENDING** | Historical Task 14 audio run `34769719057` at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. |
| Multiplayer | **PASS** | Graphical multiplayer `34772773744`. |
| Load / performance | **PASS REFERENCE TARGET** | Load `34772773733` covers 2/10/25/50 clients; not a production-capacity claim. |
| Windows package | **PASS CI; PUBLICATION DISABLED** | Windows package `34772773761`; operations archive/checksums/candidate manifest/clean extraction/restart/reconnect/exported-client launch; `publicationReady: false`. |
| Documentation | **PASS CONTRACT REQUIRED** | Synchronized delivery head must pass `tools/documentation_contract.py`. |
| Release | **NOT APPROVED** | No release/tag created; human acceptance gates remain. |

## Review rules

- A catalog record is not proof that a mechanic works.
- Same-agent adversarial testing is not independent approval.
- Structural/rendered checks are not artistic approval.
- Hosted/emulated DPI is not physical-monitor review.
- A fixed CI concurrency workload is not production-capacity proof.
- Technical audio analysis is not listening approval.
- A disposable backup/restore drill is not proof of a production disaster-recovery service.
- A repository release-candidate pass is not proof of a public deployed realm.
- Do not delete failing tests, suppress errors, weaken validation or lower accepted scope to obtain green results.

## Release status

**NOT APPROVED — human acceptance remains.**
