# Verification record

Current consolidated status as of 2026-09-13.

Current implementation baseline: `b28429037bb9ed96d6ec727cb84345445fed177e` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

This file is the current repository-side evidence record. Dated handoff files remain historical evidence at their original revisions. Automated passes are not substitutes for human Windows play, artistic approval, listening approval, physical-monitor/DPI review, subjective balance approval, or production-capacity proof.

## Current repository-side status

The implemented Godot/.NET client, authoritative .NET server, PostgreSQL persistence, deterministic content/art pipeline, progression, world, economy, audio, multiplayer, load, Windows input/display, package, combat-readability, concurrency/persistence and release-boundary hardening remain integrated on `main`.

The most recent technical hardening protects unauthenticated `/play` admission at 120 attempts per minute per source while leaving established sessions under the existing per-peer command controls. A real PostgreSQL/network regression proves normal `/play` validation remains reachable and repeated unauthenticated admission reaches HTTP 429.

The retained reference-load gate now exercises 2, 10, 25 and 50 simultaneous clients, including reconnect behavior and server resource measurements. This is a CI reference target, not a production-capacity claim.

## Exact current-baseline workflow evidence

All of the following passed against `b28429037bb9ed96d6ec727cb84345445fed177e`:

- Build and verify — run `34727191151`.
- Load acceptance — run `34727191167`.
- Transaction security regression — run `34727191125`.
- Transaction integrity on Windows and Linux — run `34727191198`.
- Compile Windows client source — run `34727191182`.
- Live progression breadth — run `34727191137`.
- Graphical multiplayer acceptance — run `34727191138`.
- Windows package acceptance — run `34727191153`.

Together these exact-baseline runs cover Linux/Windows core builds, malformed/gameplay regressions, world/progression audits, authoritative concurrency, PostgreSQL/network integration, save-conflict handling, adversarial transaction checks, native client compilation/contracts, graphical progression, two-client shared-world behavior, clean Windows export/restart/reconnect, and the 2/10/25/50-client load stages.

## Historical task-specific evidence

Earlier task-specific commits and run IDs remain recorded in dated files under `docs/handoff/`. They are still useful for provenance, but the exact current-baseline matrix above is the authority for whether the integrated repository remained green after later hardening.

## Human acceptance still required before release approval

The following remain intentionally human or owner-environment gates:

1. Owner Windows gameplay pass for visible XP/level pacing and reconnect/restart persistence.
2. Normal-play progression and class feel.
3. Independent artistic approval at native/in-engine scale.
4. Full ordinary-account world and quest walkthrough.
5. Sustained economy and balance feel.
6. Audio listening approval.
7. Production-scale load validation if a specific concurrent-player capacity will be advertised.
8. Physical Windows DPI and hardware-input inspection.
9. Owner-machine clean Windows package extraction and launch if required for release sign-off.

## Documentation drift contract

`tools/documentation_contract.py` validates `docs/handoff/CURRENT_EVIDENCE.json` against the latest non-documentation implementation commit and checks the current-facing status files for a synchronized evidence date, baseline, workflow ledger and release boundary. `.github/workflows/documentation-contract.yml` runs that contract on every push with full Git history.

Future implementation work must update the current evidence ledger before the documentation contract can pass. Historical dated handoffs are excluded from that rule so their revision-specific statements remain intact.

## Release status

**NOT APPROVED — human acceptance remains.**

This is an acceptance decision, not a claim that the repository-side systems above are unimplemented. Do not claim a public production realm is running when only development/CI realms have been verified.
