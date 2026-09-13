# Task 16 evidence

Current status as of 2026-09-13.

Task 16 implementation/candidate baseline: `2365a0df98beca178e22c099f0f31cd5adf65e6e`.
Machine-readable authority: `docs/handoff/CURRENT_EVIDENCE.json`.
Owner procedure: `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

**NOT APPROVED — human acceptance remains.**

## Automated exact-SHA evidence

The following workflows all concluded successfully at `2365a0df98beca178e22c099f0f31cd5adf65e6e`:

| Workflow | Run |
| --- | ---: |
| Build and verify | `34775900161` |
| Load acceptance | `34775900163` |
| Transaction security regression | `34775900154` |
| Transaction integrity on Windows and Linux | `34775900126` |
| Compile Windows client source | `34775900236` |
| Live progression breadth | `34775900143` |
| Graphical multiplayer acceptance | `34775900159` |
| Windows package acceptance | `34775900170` |
| Task 13 adversarial acceptance | `34775900129` |
| Release operations acceptance | `34775900148` |

Windows owner candidate: `Kairnfall-Release-Candidate-2365a0df98be.zip`; Actions artifact `10324090750`; SHA-256 `45e00144c910c0b79daa327c30086bb604896a8a425b9391e57a9340ab61b54e`.

The retained artifact was inspected after CI. Its outer checksum matches `RELEASE-CANDIDATE.sha256`; its manifest records Task 16, exact source SHA and workflow/artifact provenance; `OWNER_ACCEPTANCE.md` is present and its hash matches the manifest; and client/server/operations archive hashes match `SHA256SUMS.txt` and the manifest.

## Owner/manual acceptance still pending

No owner-machine or subjective result is marked passed. Pending areas include clean Windows package use, account/character/reconnect/restart behavior, representative durable-state persistence, first-hour normal-play progression, all class/combat feel, world/quest/resource/boss traversal, economy, social/multiplayer usability, UI/UX/accessibility, physical DPI/input, artistic review and actual audio listening.

Automated hosted DPI/visual/audio evidence does not substitute for those observations.

## Human results received

None.

## Historical evidence retained

Task 15 release/recovery evidence remains at `83a99948c7e96ff1ed568b5090b3138294b8e713`. Task 14 display/input, visual and technical-audio evidence remains at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`, including runs `34769719092`, `34769719027` and `34769719057`. These are historical provenance, not Task 16 exact-SHA claims.

## Release status

`publicationReady: false`.

No GitHub release, tag, public realm, production credentials/infrastructure, DNS/certificate, or advertised capacity is authorized by Task 16 repository-side completion. Human results are added only after the owner explicitly reports them.
