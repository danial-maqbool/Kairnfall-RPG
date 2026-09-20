# Task 16 owner-acceptance candidate audit

Task 16 prepares one deterministic Windows owner-test candidate and the final human acceptance procedure without publishing a release.

Machine-readable candidate/evidence authority: `docs/handoff/CURRENT_EVIDENCE.json`.
Owner acceptance procedure: `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

**NOT APPROVED — human acceptance remains.**

## Candidate identity

The exact Task 16 implementation SHA, exact workflow run IDs, Actions artifact ID/name, candidate ZIP filename, and outer SHA-256 are recorded after CI completes in `CURRENT_EVIDENCE.json`. The Windows package manifest additionally records its source SHA and GitHub Actions producer/run/artifact provenance.

Do not infer candidate identity from a branch name or an old artifact. Do not substitute a locally rebuilt ZIP for the recorded owner-test artifact.

## Automated scope

The final Task 16 technical matrix reruns the established build, adversarial authority, load, transaction, Windows client compilation, live progression, graphical multiplayer, Windows packaging, and release-operations gates against the exact Task 16 implementation revision.

The Windows package gate produces checksum-manifested client/server/operations archives plus a combined candidate bundle, extracts runtime archives into a clean path containing spaces, runs the packaged server through restart/reconnect persistence, and launches the exported client outside the source tree. `release-candidate.json` remains `publicationReady: false`.

Task 16 also fixes candidate-document provenance so manifest document filenames correspond to the files actually present in the outer bundle, and records Actions producer/run/artifact identity in the generated manifest. The machine-readable current evidence must retain a non-empty `humanOnlyGates` list; candidate assembly fails closed if those explicit human release gates are missing.

## Historical evidence boundary

Task 14 display/input, visual and technical-audio runs remain historical evidence at their original SHA unless those surfaces are changed and genuinely rerun. Task 15 release/recovery evidence likewise remains retained historical provenance after the Task 16 exact candidate supersedes it.

No historical run may be relabeled as exact-SHA Task 16 proof.

## Human boundary

The owner must perform the applicable checks in `docs/qa/TASK16_OWNER_ACCEPTANCE.md`. Repository automation cannot approve subjective pacing/combat feel, artistic quality, audio listening, or physical Windows DPI/input behavior.

Human results are recorded only after they are explicitly supplied by the owner. A technically green candidate does not authorize release/tag creation or deployment.
