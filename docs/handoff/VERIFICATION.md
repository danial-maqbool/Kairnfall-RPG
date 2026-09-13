# Verification record

Current consolidated status as of 2026-09-13.

Current implementation baseline: `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a` on `main`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 14 adds a permanent release-candidate sentinel that forces the accepted automated matrix onto one exact source revision. Detailed scope and evidence are in `docs/qa/RELEASE_CANDIDATE_ACCEPTANCE.md`. Task 15 was not started.

**NOT APPROVED — human acceptance remains.**

## Exact Task 14 release-candidate evidence

All twelve technical workflows below succeeded against the same source baseline `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`:

- Build and verify — run `34769719014`.
- Task 13 adversarial acceptance — run `34769719025`.
- Load acceptance — run `34769719010`.
- Transaction security regression — run `34769719021`.
- Transaction integrity on Windows and Linux — run `34769719029`.
- Compile Windows client source — run `34769719013`.
- Live progression breadth — run `34769719053`.
- Graphical multiplayer acceptance — run `34769719082`.
- Windows package acceptance — run `34769719040`.
- Windows display and input acceptance — run `34769719092`.
- Visual acceptance matrix — run `34769719027`.
- Audio acceptance — run `34769719057`.

Together these runs cover Linux and Windows core builds, malformed input, authoritative adversarial/transaction checks, PostgreSQL/network integration, save conflicts, world/persistence/social behavior, concurrency, native Windows client and Godot contracts, progression, two-client graphical multiplayer, package export/restart/reconnect, 2/10/25/50-client reference load, Windows display/input, structural/native visual evidence and technical audio validation.

## Task 14 mechanism

`src/release-candidate.trigger` is a permanent schema-1 sentinel. Existing accepted workflows already watched `src/**` except Windows display/input, visual acceptance and audio acceptance; those three workflows now explicitly watch the sentinel. The Task 14 implementation changed acceptance triggering only. It did not weaken tests, change accepted thresholds, or alter gameplay/content/art behavior.

The source-candidate documentation run `34769719035` failed closed because `CURRENT_EVIDENCE.json` still named the Task 13 baseline. Its log reports only that baseline mismatch. This is expected evidence sequencing, not a technical candidate failure. The synchronized documentation delivery commit is separately required to pass the contract at its exact head.

## Human acceptance still required before release approval

1. Owner Windows gameplay pass for visible XP/level pacing and reconnect/restart persistence.
2. Normal-play progression and class feel.
3. Independent human adversarial/gameplay acceptance if independent approval is required.
4. Independent artistic approval at native/in-engine scale.
5. Full ordinary-account world and quest walkthrough.
6. Sustained economy and balance feel.
7. Audio listening approval.
8. Production-scale load validation if a specific concurrent-player capacity will be advertised.
9. Physical Windows DPI and hardware-input inspection.
10. Owner-machine clean Windows package extraction and launch if required for release sign-off.

Automated structural, graphical, emulated, protocol and same-agent results must not be relabeled as those human approvals.
