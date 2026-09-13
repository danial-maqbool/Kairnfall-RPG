# QA acceptance matrix

Current consolidated status as of 2026-09-13.

Current implementation baseline: `b28429037bb9ed96d6ec727cb84345445fed177e`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

This matrix separates repository automation from human-only acceptance. Consult `handoff/VERIFICATION.md` for the current evidence record and `FINAL_AUDIT.md` for the release decision.

| Area | Required check | Current status | Evidence / remaining work |
| --- | --- | --- | --- |
| Source / repository | Single authoritative mainline and reproducible source/assets. | **PASS** | `main` baseline is `b28429037bb9ed96d6ec727cb84345445fed177e`; current evidence is machine-checked for drift. |
| Backend | Core, gameplay, malformed-input, PostgreSQL/network and save-conflict suites. | **PASS** | Exact-baseline Build and verify is green. |
| Security / transactions | Session, ownership, transaction, replay and persistence-integrity checks. | **PASS** | Transaction security plus Windows/Linux transaction-integrity workflows are green. |
| Network admission | Bound unauthenticated WebSocket admission without limiting established sessions. | **PASS** | `/play` accepts at most 120 admissions/minute/source; real-network regression verifies normal validation then HTTP 429 under pressure. |
| XP / HUD | Character/skill XP presentation and real activity progression. | **IMPLEMENTED / HUMAN CHECK PENDING** | Live progression automation is green; owner Windows pacing/visibility pass remains human. |
| Progression / classes | Authoritative skill/class/ability routes and persistence. | **PASS** | Retained progression breadth and core audits remain green. |
| Native UI | Client compilation, lifecycle, signals and native contracts. | **PASS** | Exact-baseline Windows client source/native contract workflow is green. |
| Character / creature art | Required actor/equipment presentation coverage. | **PASS STRUCTURAL/GRAPHICAL; HUMAN ART APPROVAL PENDING** | Retained deterministic/native graphical checks remain green; independent artistic approval remains human. |
| World / quests | Authored topology/objective/reference checks. | **PASS AUTOMATED; HUMAN WALKTHROUGH PENDING** | Retained world/quest audits remain green; full ordinary-account traversal remains human. |
| Economy | Transaction correctness and authored balance sanity. | **PASS AUTOMATED; HUMAN BALANCE PENDING** | Retained economy/security checks pass; sustained pacing remains subjective. |
| Audio | Runtime format/quality checks. | **PASS TECHNICAL; LISTENING PENDING** | Technical audio audit remains retained; listening approval remains human. |
| Combat presentation | Targeting, telegraphs, control/readability and progression interactions. | **PASS AUTOMATED; SUBJECTIVE FEEL PENDING** | Native/graphical progression and retained combat-readability checks are green. |
| Multiplayer | Shared state, chat, movement, protocol, reconnect/restart. | **PASS** | Exact-baseline graphical multiplayer workflow is green. |
| Load / performance | Staged concurrency and resource measurements. | **PASS REFERENCE TARGET** | Exact-baseline 2/10/25/50-client load/reconnect gate passes; not a production-capacity claim. |
| Windows display/input | Native keyboard/mouse and supported scale/resolution coverage. | **PASS AUTOMATED; PHYSICAL REVIEW PENDING** | Retained Windows/native checks are green; physical hardware review remains human. |
| Windows package | Export, clean-path launch, restart/reconnect, checksums. | **PASS CI; OWNER-MACHINE CHECK OPTIONAL/PENDING** | Exact-baseline Windows package acceptance is green. |
| Documentation | Current evidence files match the latest non-documentation implementation commit. | **PASS CONTRACT REQUIRED** | `tools/documentation_contract.py` and `CURRENT_EVIDENCE.json` enforce synchronized baseline/evidence on every push. |
| Release | Applicable automated and human gates accepted against an exact package/revision. | **NOT APPROVED** | Human acceptance gates remain. |

## Exact current-baseline workflow matrix

The eight successful run IDs are recorded in `docs/handoff/CURRENT_EVIDENCE.json` and reproduced in `handoff/VERIFICATION.md`. The current load stages are 2, 10, 25 and 50 clients.

## Human acceptance still required

- Owner Windows XP/HUD gameplay and reconnect/restart persistence pass.
- Normal-play progression/class feel.
- Independent artistic approval at native/in-engine scale.
- Full ordinary-account world/quest walkthrough.
- Sustained economy/balance feel.
- Audio listening approval.
- Production-scale load/hardware target if a specific capacity will be advertised.
- Physical Windows DPI/hardware-input review.
- Owner-machine clean package extraction/launch if required for release sign-off.

## Review rules

- A catalog record is not proof that a mechanic works.
- Structural/rendered checks are not artistic approval.
- Emulated DPI is not physical-monitor review.
- A fixed CI concurrency workload is not production-capacity proof.
- Technical WAV analysis is not listening approval.
- Do not delete failing tests, suppress engine errors, weaken production validation or lower accepted scope to obtain green results.

## Release status

**NOT APPROVED — human acceptance remains.**
