# Asset build audit — 7 September 2026

## Verified scope

This audit records generated PNG/WAV files and structural validation.
It does not certify a complete game, visual quality, audio quality, or a Windows release.
The accepted MMORPG specification remains unchanged.

Tested source commit: `3d787bd8e41efb3d721e3b8ccf00f786243104b9`.
Branch: `team/release/playable-verification`.
Pull request: https://github.com/danial-maqbool/Kairnfall-RPG/pull/20
Workflow run: https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34113289960
Job: `101714270040`.

The inspected GitHub Actions log reports successful generation, validation, and both artifact uploads.
The job completed successfully. The final asset validator reports:

| Check | Actual result |
| --- | ---: |
| Generated PNG files | 1,523 |
| Animation sheets included in those PNG files | 562 |
| Generated WAV audio files | 22 |
| Required image references | 1,523 |
| Standalone actor frames checked for visibility | 35,136 |
| Technical assertions passed | 44,888 |
| Technical assertions failed | 0 |
| Exact duplicate normal-species animation silhouettes | 0 |
| Identical complete normal-species animation images | 0 |

These are file and frame checks, not 44,888 gameplay tests.
An animation sheet contains multiple frames. Do not count each sheet as a distinct creature or item.
Near-duplicate appearance, poor anatomy, animation quality, and gameplay readability still require visual review.

## Saved outputs

Audit artifact: `10015270226`, `generated-asset-validation`.
Size: 289,408 bytes.
SHA-256: `434e0ff6131f08b62eb0bcfb11ca30153f9e4ec9558e33e78fc88d594fd91f92`.
Download: https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34113289960/artifacts/10015270226

The audit artifact contains the JSON report, generation logs, image manifest, credits, and creature contact sheet.

Art/audio artifact: `10015271410`, `kairnfall-generated-art-and-audio`.
Size: 28,909,938 bytes.
SHA-256: `3470990339f3b406529224096b75e79cc80c587cdfe4c06787fa9c27dd7be8d7`.
Download: https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34113289960/artifacts/10015271410

The art/audio archive is not a playable game package. It contains no Windows game executable.
The workflow retains these artifacts for seven days. Versioned source can regenerate them.

## Defects found and repaired

The first asset build failed because Spell Wisp had no renderer.
A separate articulated ring renderer now handles that creature.
A preflight checks all 145 creature definitions in four directions before full generation.

The first complete asset audit found seven pairs of identical creature sheets and 22 groups of identical alpha silhouettes.
The refinement replaced shared geometry with species-specific structural features.
Examples include mouse proportions, tick leg placement, fish fins, turtle flippers, cuttlefish arms, fungal colonies, thorn cages, crab shells, bird anatomy, and different humanoid equipment.
The validator now fails on exact duplicate normal-species sheets and silhouettes.
The final inspected run passed those stricter checks without exceptions.

## Catalog used by this build

This build uses the `content_src` catalog: 8 classes, 60 skills, 530 item templates, 132 abilities, 463 recipes, 103 zones, 170 NPCs, and 166 quests.
Its 145 creature definitions comprise 100 normal species, 25 elite variants, and 20 bosses.
The catalog includes 5 major cities, 11 smaller settlements, 20 dungeons, and 20 biomes.
These are catalog records. Their existence does not prove balanced, complete, or visually approved gameplay.
Do not combine these counts with the different catalog on the older `persistent-client-build` branch.

## Client and launcher status

The existing client-source compilation workflow completed successfully for the same source commit:
https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34113293066

That workflow compiles C# source. It does not run the graphical game or export a Windows executable.
The local launcher and PostgreSQL Compose source are present, but the launcher requires packaged client and server executables.
No native Windows launcher test is established by this audit.
No production server was deployed.

## Unperformed acceptance checks

- No in-engine screenshot was inspected in this continuation.
- The creature contact sheet was generated but could not be opened for visual review in the local runtime.
- No audio listening review was performed.
- No complete graphical client playthrough was performed.
- No Windows executable was exported or installed by this continuation.
- No 100-client load result or final full-game acceptance was established.
- No independent Zeiko coding team executed this work.

The local container, Python, and user-visible Python runtime returned ClientError.
A proposed executable-packaging workflow write was rejected by the execution platform and was not installed.
No alternative credential or route was used to perform that blocked operation.
The allowed asset workflow only generates and validates image/audio files.
The shared personal token was not used. All repository writes used the existing authenticated connection.

## Release decision

Keep pull request 20 in draft. Do not describe the current output as the completed MMORPG.
The asset manifest retains `artistic_review: not_approved`.
The validator retains `visual_review: not_performed` and `audio_review: not_performed`.
Complete graphical and Windows execution, visual and audio inspection, gameplay coverage, progression balance, encounter review, load testing, and release acceptance before publishing a finished game.
