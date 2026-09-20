# Task 14 release-candidate acceptance

Status date: 2026-09-13  
Technical source baseline: `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`  
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`

**NOT APPROVED — human acceptance remains.**

## Purpose

Task 14 establishes a permanent repository-side release-candidate mechanism that can exercise the accepted automated matrix against one exact source revision. It does not replace owner gameplay, independent human review, artistic approval, listening approval, physical Windows hardware/DPI inspection, or deployment-specific production-capacity evidence.

The permanent sentinel is `src/release-candidate.trigger`. Existing accepted workflows already watched `src/**` except Windows display/input, visual acceptance and audio acceptance; those three workflows were extended only to watch the sentinel. Test commands, thresholds and production behavior were not weakened or changed.

## Exact Task 14 technical matrix

Every technical workflow below completed successfully at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`:

| Workflow | Run |
| --- | ---: |
| Build and verify | `34769719014` |
| Task 13 adversarial acceptance | `34769719025` |
| Load acceptance | `34769719010` |
| Transaction security regression | `34769719021` |
| Transaction integrity on Windows and Linux | `34769719029` |
| Compile Windows client source | `34769719013` |
| Live progression breadth | `34769719053` |
| Graphical multiplayer acceptance | `34769719082` |
| Windows package acceptance | `34769719040` |
| Windows display and input acceptance | `34769719092` |
| Visual acceptance matrix | `34769719027` |
| Audio acceptance | `34769719057` |

This matrix spans Linux/Windows core execution, malformed-input and adversarial authority checks, PostgreSQL/network and save-conflict behavior, transaction integrity, 2/10/25/50-client load/reconnect evidence, native Windows client/Godot contracts, live progression, two-client graphical multiplayer, clean Windows package export/restart/reconnect, Windows display/input contracts, structural/native visual acceptance and technical audio validation.

## Documentation guardrail result

The source-candidate push also ran Documentation evidence contract `34769719035`. It failed for the intended reason: the ledger still named Task 13 baseline `3dce816eade22c93a8dad65eee6964be3e12fd52` while the latest implementation was `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. No secondary documentation or runtime failure was present. This source-candidate failure is not accepted evidence; the synchronized delivery commit must pass the contract at its own exact head.

## Evidence boundaries

- Same-agent automation is not independent human approval.
- Structural/rendered art evidence is not artistic approval.
- Technical audio analysis is not listening approval.
- Hosted/emulated Windows checks are not physical-monitor or hardware-input approval.
- The 2/10/25/50-client gate is a reference CI target, not a public production-capacity claim.
- A repository release-candidate pass is not proof that a public persistent realm is deployed.

Task 14 is repository-side complete when the synchronized documentation delivery head is green and repository hygiene remains clean. Task 15 must not be started implicitly.
