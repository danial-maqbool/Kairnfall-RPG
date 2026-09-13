# Verification record

Current consolidated status as of 2026-09-13.

Current implementation baseline: `3c4b6195e23f00fd34ae61e861dc7be2a2dadee3` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 12 adds synchronous modal cleanup and focus restoration, correct mouse/layer ordering, keyboard-following overflow for all existing pages, context-item cleanup, text/display setting resilience and current keybind discovery. See the [Task 12 engineering record](../UI_UX_ENGINEERING.md). Task 13 was not started. These are automated engineering results; subjective usability and physical monitor DPI remain human evaluation.

This file is the current repository-side evidence record. Dated handoff files remain historical evidence at their original revisions. Automated passes are not substitutes for human Windows play, artistic approval, listening approval, physical-monitor/DPI review, subjective balance approval, or production-capacity proof.

## Current repository-side status

The implemented Godot/.NET client, authoritative .NET server, PostgreSQL persistence, deterministic content/art pipeline, progression, world, economy, audio, multiplayer, load, Windows input/display, package, combat-readability, concurrency/persistence and release-boundary hardening remain integrated on `main`.

Earlier technical hardening protects unauthenticated `/play` admission at 120 attempts per minute per source while leaving established sessions under the existing per-peer command controls. A real PostgreSQL/network regression proves normal `/play` validation remains reachable and repeated unauthenticated admission reaches HTTP 429.

The retained reference-load gate now exercises 2, 10, 25 and 50 simultaneous clients, including reconnect behavior and server resource measurements. This is a CI reference target, not a production-capacity claim.

## Exact current-baseline workflow evidence

All of the following passed against `3c4b6195e23f00fd34ae61e861dc7be2a2dadee3`:

- Build and verify — run `34766126870`.
- Load acceptance — run `34766127780`.
- Transaction security regression — run `34766129605`.
- Transaction integrity on Windows and Linux — run `34766131696`.
- Compile Windows client source — run `34766126897`.
- Live progression breadth — run `34766126854`.
- Graphical multiplayer acceptance — run `34766126887`.
- Windows package acceptance — run `34766126879`.

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

## Additional Task 12 exact-baseline evidence

- Windows display and input acceptance — [run 34766126861](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34766126861), success at `3c4b6195e23f00fd34ae61e861dc7be2a2dadee3`.
- Visual acceptance matrix — [run 34766126888](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34766126888), success at `3c4b6195e23f00fd34ae61e861dc7be2a2dadee3`.
- Audio acceptance — [run 34766133964](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34766133964), success at `3c4b6195e23f00fd34ae61e861dc7be2a2dadee3`.

The ledger records implementation-baseline evidence. The documentation-only delivery commit is separately checked by fresh workflows at its own exact SHA; source-baseline runs are not claimed as delivery-head runs. Earlier failures and the retained reconnect-XP diagnostic are described in the Task 12 record.
