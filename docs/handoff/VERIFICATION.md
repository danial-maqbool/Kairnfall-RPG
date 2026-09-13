# Verification record

Current consolidated status as of 2026-09-13.

Current Task 16 implementation/candidate baseline: `2365a0df98beca178e22c099f0f31cd5adf65e6e` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.
Owner-machine procedure: `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

Task 16 repository-side preparation is complete at the exact implementation candidate above. Publication and release approval remain blocked until the owner reports the applicable human acceptance results.

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

The 2/10/25/50-client workload remains a reference acceptance target, not a public capacity claim. Recovery checks use disposable PostgreSQL environments and are not a production deployment claim.

## Deterministic Windows owner-test candidate

Windows package run `34775900170` retained Actions artifact `10324090750`, named `windows-package-2365a0df98beca178e22c099f0f31cd5adf65e6e`. Its exact source SHA is the Task 16 baseline.

Owner candidate: `Kairnfall-Release-Candidate-2365a0df98be.zip`  
SHA-256: `45e00144c910c0b79daa327c30086bb604896a8a425b9391e57a9340ab61b54e`

Independent post-CI inspection verified that `RELEASE-CANDIDATE.sha256` matches the candidate ZIP; the bundle contains client/server/operations archives, `SHA256SUMS.txt`, `release-candidate.json`, setup/limitations/audit material and `OWNER_ACCEPTANCE.md`; the manifest records Task 16, exact source SHA, workflow run `34775900170`, exact artifact name, and `publicationReady: false`; the bundled owner-runbook hash matches the manifest; and all three inner archive hashes match both `SHA256SUMS.txt` and the manifest.

Inner archive SHA-256 values:

- client: `d1a1ac7447a20baad4e9a2077b082aaf0696272c5cf46846f2ae38924f02d72b`
- server: `e9dde64dd18cb0de02ea57f6263730ece971f6cb58b11d8bdce9604377bada49`
- operations: `16e115b3fbc3076b830f89d0e568af0c55c47052784c57489c5bdbc32a85488f`

The Actions artifact is retained until `2026-09-27T18:57:35Z` according to GitHub metadata. It is a release candidate, not a public release.

## Objective Task 16 defects found and closed

1. Candidate manifest document names disagreed with the files actually renamed into the outer ZIP (`WINDOWS_SETUP.md`/`CANDIDATE_AUDIT.md` versus `SETUP.md`/`AUDIT.md`). The manifest now records actual bundle names and GitHub Actions producer/run/artifact provenance.
2. The first Task 16 candidate `441f394a32cc131a7490505312f21ddbf6c898d9` failed `Live progression breadth` run `34775147970`. The exact failure showed `heavy_armor` and `endurance` XP increasing after the checkpoint. Root cause was a test assertion requiring exact skill-XP equality even though already in-flight authoritative hostile attacks can award defensive XP before graceful disconnect acknowledgement. The regression now requires every acknowledged per-skill checkpoint and total XP to be retained or exceeded; exact merchant/equipment persistence assertions remain. Final live progression run `34775900143` passes.
3. The initial Task 16 outer candidate did not carry the permanent owner runbook. The final bundle includes `OWNER_ACCEPTANCE.md` and hashes it in `release-candidate.json`.

No failing production behavior was hidden, no accepted threshold was reduced, and no manual result was fabricated.

## Historical evidence boundary

Task 15 implementation/recovery evidence remains historical at `83a99948c7e96ff1ed568b5090b3138294b8e713` with its original ten workflow run IDs preserved in `CURRENT_EVIDENCE.json`.

Task 14 display/input, visual and technical-audio evidence remains historical at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`, including Windows display/input `34769719092`, visual acceptance `34769719027`, and audio acceptance `34769719057`. Task 16 did not change product UI/display/rendering/art/audio/input behavior, so those runs are retained honestly rather than relabeled as Task 16 exact-SHA proof.

## Human acceptance still required

The owner must execute `docs/qa/TASK16_OWNER_ACCEPTANCE.md` against the exact recorded candidate and report observed results. Physical Windows DPI/input, real listening, artistic judgement, normal-play pacing/combat/economy feel, and other subjective/owner-machine observations remain unpassed until reported by the owner.

No GitHub release, release tag, public realm, production credential, DNS/certificate, infrastructure provisioning, or player-capacity advertisement is authorized by repository-side completion.
