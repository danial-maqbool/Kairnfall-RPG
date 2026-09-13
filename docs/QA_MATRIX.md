# QA acceptance matrix

Current consolidated status as of 2026-09-13.

Current implementation baseline: `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 14 is repository-side complete through a permanent exact-SHA release-candidate sentinel. It does not constitute human or independent approval. See `docs/qa/RELEASE_CANDIDATE_ACCEPTANCE.md`. Task 15 was not started.

| Area | Current status | Exact Task 14 evidence / remaining work |
| --- | --- | --- |
| Source / repository | **PASS** | Candidate baseline `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`; permanent sentinel and documentation drift contract retained. |
| Backend / malformed input | **PASS** | Build and verify `34769719014`. |
| Adversarial authority | **PASS AUTOMATED** | Task 13 adversarial acceptance `34769719025`; same-agent evidence, not independent approval. |
| Security / transactions | **PASS** | Transaction security `34769719021` and Windows/Linux integrity `34769719029`. |
| Progression / classes | **PASS AUTOMATED; HUMAN FEEL PENDING** | Live progression `34769719053`. |
| Native UI / Windows display | **PASS AUTOMATED; PHYSICAL REVIEW PENDING** | Client `34769719013` and display/input `34769719092`. |
| Art | **PASS STRUCTURAL/GRAPHICAL; HUMAN ART APPROVAL PENDING** | Visual matrix `34769719027`. |
| World / quests / economy | **PASS AUTOMATED; HUMAN WALKTHROUGH/BALANCE PENDING** | Build/adversarial world, persistence and database stages pass at the candidate SHA. |
| Audio | **PASS TECHNICAL; LISTENING PENDING** | Audio acceptance `34769719057`. |
| Multiplayer | **PASS** | Graphical multiplayer `34769719082`. |
| Load / performance | **PASS REFERENCE TARGET** | Load `34769719010` covers 2/10/25/50 clients; not a production-capacity claim. |
| Windows package | **PASS CI; OWNER-MACHINE CHECK OPTIONAL/PENDING** | Windows package `34769719040`. |
| Documentation | **PASS CONTRACT REQUIRED** | Synchronized delivery head must pass `tools/documentation_contract.py`. |
| Release | **NOT APPROVED** | Human acceptance gates remain. |

## Review rules

- A catalog record is not proof that a mechanic works.
- Same-agent adversarial testing is not independent approval.
- Structural/rendered checks are not artistic approval.
- Hosted/emulated DPI is not physical-monitor review.
- A fixed CI concurrency workload is not production-capacity proof.
- Technical audio analysis is not listening approval.
- A repository release-candidate pass is not proof of a public deployed realm.
- Do not delete failing tests, suppress errors, weaken validation or lower accepted scope to obtain green results.

## Release status

**NOT APPROVED — human acceptance remains.**
