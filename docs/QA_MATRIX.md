# QA acceptance matrix

Current consolidated status as of 2026-09-13.

Current implementation baseline: `3dce816eade22c93a8dad65eee6964be3e12fd52`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 13 is repository-side complete through a permanent same-agent adversarial gate; it does not constitute independent human approval. Findings and retests are in `docs/qa/INDEPENDENT_FINDINGS.md`. Task 14 was not started.

| Area | Current status | Evidence / remaining work |
| --- | --- | --- |
| Source / repository | **PASS** | `main` implementation baseline is `3dce816eade22c93a8dad65eee6964be3e12fd52`; documentation drift is checked permanently. |
| Backend / malformed input | **PASS** | Build and verify `34768386855` is green on Linux and Windows. |
| Task 13 adversarial authority | **PASS AUTOMATED** | Run `34768390034` passes all new scenarios and retained security/world/concurrency/database reruns. This is same-agent evidence, not independent approval. |
| Security / transactions | **PASS** | Forged ownership, invalid quantities, replay, trade privacy/consent and persistence-integrity coverage pass. |
| Progression / classes | **PASS AUTOMATED; HUMAN FEEL PENDING** | Retained live progression run `34766721059` is green. |
| Native UI / Windows display | **PASS AUTOMATED; PHYSICAL REVIEW PENDING** | Retained client `34766713586` and display/input `34766727800` are green at unchanged product baseline `d4d1b4e`. |
| Art | **PASS STRUCTURAL/GRAPHICAL; HUMAN ART APPROVAL PENDING** | Visual matrix `34766729859` is green; its artifact does not claim artistic approval. |
| World / quests / economy | **PASS AUTOMATED; HUMAN WALKTHROUGH/BALANCE PENDING** | Task 13 world/security reruns and retained product gates are green. |
| Audio | **PASS TECHNICAL; LISTENING PENDING** | Retained audio run `34766731782` is green. |
| Multiplayer | **PASS** | Retained graphical multiplayer run `34766723424` is green. |
| Load / performance | **PASS REFERENCE TARGET** | Retained load run `34766715225` covers 2/10/25/50 clients; not a production-capacity claim. |
| Windows package | **PASS CI; OWNER-MACHINE CHECK OPTIONAL/PENDING** | Retained package run `34766725549` is green. |
| Documentation | **PASS CONTRACT REQUIRED** | `tools/documentation_contract.py` must pass at delivery head. |
| Release | **NOT APPROVED** | Human acceptance gates remain. |

## Review rules

- A catalog record is not proof that a mechanic works.
- Same-agent adversarial testing is not independent approval.
- Structural/rendered checks are not artistic approval.
- Emulated DPI is not physical-monitor review.
- A fixed CI concurrency workload is not production-capacity proof.
- Technical audio analysis is not listening approval.
- Do not delete failing tests, suppress errors, weaken validation or lower accepted scope to obtain green results.

## Release status

**NOT APPROVED — human acceptance remains.**
