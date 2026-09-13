# Verification record

Current consolidated status as of 2026-09-14.

Current Task 16 implementation/candidate baseline: `2365a0df98beca178e22c099f0f31cd5adf65e6e` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.
Owner-machine procedure: `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

Task 16 repository-side work is closed. On 2026-09-14 the owner accepted the Task 16 repository changes and requested closure of remaining repository-side work. No itemized owner-machine/manual observations were supplied, so no physical, artistic, listening, pacing, usability, or other human-only check is recorded as passed.

**NOT APPROVED — human acceptance remains.**

## Exact Task 16 automated evidence

All ten required technical workflows succeeded against `2365a0df98beca178e22c099f0f31cd5adf65e6e`:

- Build and verify — run `34775900161` — success.
- Load acceptance — run `34775900163` — success.
- Transaction security regression — run `34775900154` — success.
- Transaction integrity on Windows and Linux — run `34775900126` — success.
- Compile Windows client source — run `34775900236` — success.
- Live progression breadth — run `34775900143` — success.
- Graphical multiplayer acceptance — run `34775900159` — success.
- Windows package acceptance — run `34775900170` — success.
- Task 13 adversarial acceptance — run `34775900129` — success.
- Release operations acceptance — run `34775900148` — success.

The 2/10/25/50-client workload remains reference acceptance evidence, not a public capacity claim. Recovery checks use disposable PostgreSQL environments and are not a production deployment claim.

## Deterministic Windows owner candidate

Windows package run `34775900170` retained Actions artifact `10324090750`, named `windows-package-2365a0df98beca178e22c099f0f31cd5adf65e6e`.

Candidate: `Kairnfall-Release-Candidate-2365a0df98be.zip`  
SHA-256: `45e00144c910c0b79daa327c30086bb604896a8a425b9391e57a9340ab61b54e`

Post-CI inspection verified the outer checksum, exact source/run/artifact provenance, bundled owner runbook hash, and all inner archive checksums. The candidate remains non-public and `publicationReady: false`.

## Objective Task 16 defects closed

1. Manifest document filenames were corrected to match actual outer-bundle names and exact Actions provenance was added.
2. The superseded candidate `441f394a32cc131a7490505312f21ddbf6c898d9` failed live progression run `34775147970` because the reconnect regression incorrectly required skill XP to remain exactly frozen while a legitimate in-flight authoritative defensive award could complete. The final regression rejects acknowledged XP loss while allowing legitimate increases; final run `34775900143` passes.
3. The permanent owner runbook is included and hashed in the final candidate.

No failing production behavior was hidden, no accepted threshold was reduced, and no manual result was fabricated.

## Owner decision received

Owner decision date: 2026-09-14.  
Decision: repository changes accepted; remaining repository-side Task 16 work closed.  
Manual checklist observations supplied: none.  
Full release acceptance complete: no.  
Publication authorized: no.  
Task 17 authorized: no.

This owner decision is recorded as approval of the repository changes only. It is not evidence that the owner executed the physical Windows DPI/input review, actual audio listening, artistic review, normal-play pacing/combat/economy checks, or the other manual checklist items.

## Historical evidence boundary

Task 15 implementation/recovery evidence remains historical at `83a99948c7e96ff1ed568b5090b3138294b8e713` with its original run IDs preserved in `CURRENT_EVIDENCE.json`.

Task 14 display/input, visual and technical-audio evidence remains historical at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`, including Windows display/input `34769719092`, visual acceptance `34769719027`, and audio acceptance `34769719057`.

No GitHub release, release tag, public realm, production credential, DNS/certificate, infrastructure provisioning, or player-capacity advertisement is authorized by this closure.
