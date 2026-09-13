# QA acceptance matrix

Current consolidated status as of 2026-09-13.

Current Task 16 implementation/candidate baseline: `2365a0df98beca178e22c099f0f31cd5adf65e6e`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.
Owner-machine procedure: `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

**NOT APPROVED — human acceptance remains.**

| Area | Current status | Exact evidence / remaining work |
| --- | --- | --- |
| Source / repository | **PASS AUTOMATED** | Exact candidate `2365a0df98beca178e22c099f0f31cd5adf65e6e`; Task 16 freeze sentinel and drift contract retained. |
| Backend / malformed input | **PASS** | Build and verify `34775900161`. |
| Adversarial authority | **PASS AUTOMATED** | Task 13 adversarial `34775900129`; same-agent automation, not human approval. |
| Security / transactions | **PASS** | Transaction security `34775900154`; Windows/Linux integrity `34775900126`. |
| Database schema / recovery | **PASS DISPOSABLE OPERATIONS DRILL** | Release operations `34775900148`. |
| Progression / classes | **PASS AUTOMATED; HUMAN FEEL PENDING** | Live progression `34775900143`; owner first-hour/class feel remains. |
| Native Windows client | **PASS AUTOMATED** | Compile/layout `34775900236`. |
| Windows display / input | **RETAINED TECHNICAL EVIDENCE; PHYSICAL REVIEW PENDING** | Historical Task 14 `34769719092` at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. |
| Art | **RETAINED TECHNICAL EVIDENCE; HUMAN ART REVIEW PENDING** | Historical visual `34769719027` at the Task 14 SHA. |
| World / quests / resources / bosses | **PASS AUTOMATED; HUMAN WALKTHROUGH PENDING** | Core/adversarial/world/database stages pass; owner ordinary-account walkthrough remains. |
| Economy | **PASS AUTOMATED; HUMAN BALANCE PENDING** | Transaction and adversarial correctness gates pass; sustained subjective economic feel remains. |
| Audio | **RETAINED TECHNICAL EVIDENCE; LISTENING PENDING** | Historical audio `34769719057` at the Task 14 SHA. |
| Multiplayer / social | **PASS AUTOMATED; OWNER USABILITY PENDING** | Graphical multiplayer `34775900159`; owner two-client social checks remain where practical. |
| Load / performance | **PASS REFERENCE TARGET** | Load `34775900163` covers 2/10/25/50 clients; not a production-capacity claim. |
| Windows package | **PASS CI; OWNER MACHINE PENDING; PUBLICATION DISABLED** | Windows package `34775900170`; candidate ZIP SHA-256 `45e00144c910c0b79daa327c30086bb604896a8a425b9391e57a9340ab61b54e`. |
| UI/UX / accessibility | **AUTOMATED STRUCTURAL COVERAGE; HUMAN INSPECTION PENDING** | Existing native/graphical automation retained; actual owner navigation/readability inspection remains. |
| Documentation | **PASS CONTRACT REQUIRED ON SYNCHRONIZED HEAD** | `tools/documentation_contract.py` validates exact Task 16 evidence and historical provenance. |
| Release | **NOT APPROVED** | `publicationReady: false`; no public release/tag/deployment authorized. |

## Review rules

- A catalog record is not proof that a mechanic works.
- Same-agent adversarial testing is not independent approval.
- Structural/rendered checks are not artistic approval.
- Hosted/emulated DPI is not physical-monitor review.
- A fixed CI workload is not production-capacity proof.
- Technical audio analysis is not listening approval.
- A disposable backup/restore drill is not production disaster-recovery deployment.
- A CI candidate artifact is not a public release.
- Do not delete failing tests, suppress errors, weaken validation or fabricate human results to obtain approval.
