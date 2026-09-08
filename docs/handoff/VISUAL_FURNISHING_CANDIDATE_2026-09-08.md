# Furnishing continuation checkpoint — 2026-09-08

Status: NOT ACCEPTED. The furnishing source described below is a candidate, not an integrated game update. Do not publish a release or replace main with this candidate without completing verification.

## Verified starting source

The continuation started from main at `1a257f8f53413b0989699e6341bf2f79455ba2ef`. Its latest local Windows review is recorded in `docs/handoff/LOCAL_VISUAL_REVIEW_2026-09-08.md`. Only main existed and no pull requests were open when inspected. These observations do not certify the current state of a developer's local checkout.

The baseline exact-source verification passed in Actions run `34248079653`. Baseline graphical fixture generation passed in run `34248079598`. The earlier core workflow failure on the starting source occurred during artifact finalization with HTTP 403, after its test commands passed. Do not classify that artifact failure as a gameplay regression.

## Retained implementation candidate

Candidate: `bc63891e0b707e75f6c61465e4b51839a6aba8d0`

Tree: `19d833b682693dea6aa49c86275f0defef66e7a1`

Preparation parent: `87c0f9e2b448198605938df0b01b818423aad163`

This candidate adds furnishing definitions, authored layout/art sources, asset-pipeline integration, world rendering integration, and collision/path checks. Inspect the complete candidate diff before retaining or changing these implementations. Do not assume that all proposed placements are correct.

The preparation job produced these integration files:

- `src/Kairnfall.Core/FurnishingDef.cs`
- `src/Kairnfall.Core/Models.cs`
- `src/Kairnfall.Core/WorldMap.cs`
- `src/Kairnfall.Core/Catalog.cs`
- `tools/world_probe/FurnishingChecks.cs`
- `tools/world_probe/Program.cs`
- `tools/build_content.py`
- `tools/build_game_assets.py`
- `tools/validate_game_assets.py`
- `client/Scripts/WorldView.cs`

Additional new source files are retained in the candidate's tree. Inspect that tree rather than reconstructing their contents from this list.

## Unresolved verification

Candidate verification run: `34250366361`

Failed verification job: `102142998143`

Diagnostics job: `102143306430`

Ancestry checks, content generation, and source compilation passed. The retained backend/security/world/database stage failed. Asset reconstruction, native contracts, and live graphical execution were skipped in that verification job. The diagnostics job and evidence upload completed.

The exact failing assertion has not been established in this continuation checkpoint. Later attempts to retrieve the diagnostic result did not provide readable output. Do not invent a cause, skip a check, or mark the candidate accepted.

The last confirmed test-request main revision before diagnostic retrieval failed was `a4723c4da242b7a5a65a799c71b7421a1077cc69`. It is a request revision, not evidence that the furnishing candidate was integrated. Fetch the live main ref before any subsequent edit.

## Next actions

1. Read the failed diagnostics and identify the exact assertion or exception.
2. Inspect the full furnishing candidate, including collision and saved-position recovery changes.
3. Repair the implementation without weakening retained security, migration, or world-path tests.
4. Run the complete exact-source verification and graphical fixture workflows.
5. Retrieve and inspect the rendered interiors, village, entrances, and service approaches.
6. Integrate only passing, reviewed source changes onto the then-current main. Preserve intervening changes. Use a normal fast-forward ref update; never force-push.
7. Continue bow handling, creature action quality, and populated HUD/interface work. Those requested areas are not complete in this checkpoint.

Preserve NPC identities, quest references, existing saved data, credentials, and Docker volumes. Any furnishing collision change needs explicit tests for valid old positions, narrowly scoped recovery, idempotency, and corrupt-position rejection.

## Acceptance boundaries

Furnishing implementation: candidate only.
Automatic candidate verification: FAILED.
Candidate graphical review: not established here.
Manual Windows playtest: NOT RUN in this continuation.
Windows 125% and 150% scaling: NOT RUN.
Two-client graphical acceptance, audio listening, sustained load, performance targets, and Windows packages: NOT ACCEPTED.
Full visual acceptance: NOT PASSED.
Whole-game acceptance: NOT PASSED.
