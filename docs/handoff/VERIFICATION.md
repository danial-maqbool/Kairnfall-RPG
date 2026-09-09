# Verification record

## Final item and merchant boundaries — 2026-09-09

Exact source `b941ac221e3084772330b98d5b0cbc7e6302669c` passed full run `34322836260` and graphical run `34322836227`. Integration `51b575323969da9c9b0fab5f3c23a7a5f0c4147e` differs only in retained request metadata. Results include 7 item-commerce groups, 118 Python tests, 52 native player checks, 1,140 native control/layout checks, 116 live client/server checks and 305 native presentation checks. Reconnect tests preserve exact sale gold, removed quantities, equipment and XP. Earlier failed and timed-out attempts remain documented. [Evidence, files and acceptance limits](MERCHANT_BOUNDARIES_2026-09-09.md).

## Item comparison and selling — 2026-09-09

Actual source integration `dbd31fc4b0391045754966eb30c73fb1e4404f71` matches tested candidate `2559da7e9e22823c49e8a71de87c76f72cffaab7` except for retained documentation and request metadata. Full run `34313980306` and graphical run `34313980303` passed. Counts: 6 commerce groups, 118 Python tests, 52 native player checks, 1,102 native control checks, 110 live client/server checks and 263 native presentation checks. Existing backend, database, security, migration, hunting and challenge tests remain in the passing matrix. [Exact evidence and limits](ITEM_COMMERCE_VERIFIED_2026-09-09.md).

## Hunting, controls and Atelier — 2026-09-09

Exact source `e5b0269048ef3ffd2fba6f511970e2f9d25dfeb2` passed full run `34298703468` and graphical run `34298703451`. Integration `9d9b361fa49e5f85f802c494819227f1947b7f9c` differs only in current test-request metadata. Results: 33 core, 34 gameplay review, 13 transaction security, 5 security probes, 18 real-network/PostgreSQL, 5 save-conflict, 7 journey groups, 7 hunting groups, 118 Python tests, 52 native player checks, 1,002 native control checks, 85 live client/server checks and 197 native visual checks passed. Signals, pointer routing, migration, equipment, maintenance and authenticated smoke remained in the passing matrix. Windows core also passed on the actual integration in run `34299503013`. Windows graphical/DPI acceptance is not implied. See [the full checkpoint](HUNTING_AND_PRESENTATION_2026-09-09.md) for artifacts, retained failures and measurement limits.

## Equipment verification — 2026-09-09

The [equipment checkpoint](EQUIPMENT_PROGRESSION_2026-09-09.md) records exact source `68956e42229c609e65071940a1b68f83dfb16a9c`, full passing run `34270827868`, and graphical run `34270827850`. Retained suites passed with 11 gear groups, 924 equip boundaries, 1,071 authoritative crafting paths, two workstation-access groups, 107 Python tests, 871 native control checks and 83 live-client checks. These results do not constitute independent image inspection, human playtesting, Windows DPI review, measured performance or a release package.

## Integrated action presentation checkpoint, 2026-09-08

Read [ACTION_PRESENTATION_2026-09-08](ACTION_PRESENTATION_2026-09-08.md) for exact source blobs,
coverage, artifact identifiers, and limits. The implementation integrated in `4d840b5f802fcf79f0e048ba2223ccf6fbecdcae`
was tested as `dd3900bd1dcdb3baa3a7860bcdd7a306e47fa159`. Full verification run `34258153781`
and graphical fixture run `34258153880` passed. Backend/database counts remain 33/34/13/18/5;
security probes 5, migration groups 5, furnishing checks 7, Python tests 94, native player 51,
native controls 601, live client/server 83, and graphical fixture checks 126 passed.
Signals, input cleanup, and 45,610 asset structural assertions also passed.
The graphical contract produced 92 PNG fixtures. The integration owner read the logs but could
not independently open those images in this chat runtime. These are Linux/native automated
results, not human gameplay, Windows DPI, audio listening, or package acceptance.
The local Windows result below describes an earlier source revision.

## Local Windows visual repair checkpoint, 2026-09-08

Read [the current detailed record](LOCAL_VISUAL_REVIEW_2026-09-08.md) for the exact
tested source, commands, hardware, preserved failures and screenshot locations.
Bootstrap passed using the verified Godot .NET editor. Backend/database suites
passed 33/34/13/18/5 checks, plus security/world/migration probes; Python 74,
native presentation 102 and isolated live experience 83 checks passed. Fresh
GPU-rendered smoke images were inspected. Visual acceptance remains incomplete;
Windows DPI, full manual play, audio, load and package gates are not approved.
The following September 7 records are historical, not the current setup status.

## Local Windows repair checkpoint, 2026-09-07

Source `90143dff664ffd5811316cc924fc8983066e3648`: 99 backend/database checks,
five security probes, five save-migration groups, 103-zone world-path checks,
35 Python tests, and both native
Godot contracts passed. Client build: zero warnings/errors. Four new real OpenGL
screenshots were inspected, and mouse account/character creation, reconnect,
right-click walking, and map scrolling were exercised. These are bounded checks.
The later migration repairs old saved road positions without changing progress;
the downloader now securely resumes interrupted official archives. An isolated
diagnostic identified mismatched physical keycodes from OS automation, leaving
actual hardware keyboard acceptance unverified.

Full bootstrap failed at the 1,200-second matching-template download timeout.
Art review failed; keyboard acceptance, full gameplay, audio, load, and packages
remain incomplete. See [the local acceptance record](LOCAL_ACCEPTANCE_2026-09-07.md)
for commands, exact evidence, retained failures, hardware, fixes, and remaining gates.
Historical results below retain their original revision boundaries. The CS0108
warning described below was repaired in this local checkpoint.

## Delivery status

The consolidated source handoff is prepared for local testing and repair.
Full-game acceptance: NOT ESTABLISHED.
Windows graphical/package acceptance: NOT ESTABLISHED.
Sprite and audio quality acceptance: NOT APPROVED.
The source handoff must not be described as a completed MMORPG or a tested Windows release.

GitHub repository operations and GitHub Actions worked in the authoring session.
Local container/Python execution returned ClientError. The fresh results below come from GitHub Actions.
No pasted personal credential was used. No independent Zeiko coding-team execution is claimed.

## Exact tested revisions

Handoff source head: `100cebec719abaa68c1c7d9cb1457986b373ba57`.
PR #26 base at testing: `b005bba7837a2c9ba4acaf33d158c237a7d0873e`.
Tested PR merge tree: `80693e4b85fe49311de55ac81a4c81590647c643`.
Date of observed results: 2026-09-07.
Later documentation-only commits record these results; they do not imply that later gameplay changes were tested.
Use `git rev-parse HEAD` to record the actual local checkout before continuing.

## Fresh handoff results

All six pull-request workflows for the source head above completed successfully.

| Workflow | Run ID | Observed result |
| --- | --- | --- |
| Local source setup execution | 34118906621 | Passed on Windows and Ubuntu. Actual bootstrap and local test commands executed. |
| Local source handoff checks | 34118906616 | Passed contract checks on Windows/Ubuntu, PowerShell parsing, and complete asset references. |
| Build and verify | 34118906617 | Passed existing backend, gameplay-review, network/PostgreSQL, and save-conflict jobs. |
| Compile Windows client source | 34118906683 | C# client compilation passed. This workflow name does not imply graphical Windows execution. |
| Transaction security regression | 34118906686 | Passed. |
| Transaction integrity on Windows and Linux | 34118906643 | Passed on both platforms. |

### Source preparation and native backend tests

Run 34118906621 executed `bootstrap.ps1 -SkipGodot` on both operating systems.
This created the Python environment, installed the pinned Pillow dependency, rebuilt all assets,
validated references, restored dependencies, and compiled the server/test solution and Godot C# client.
**The SkipGodot option deliberately omitted the editor download, Godot import, and graphical runtime.**
Those steps are still required locally. Do not describe this run as a complete fresh-machine graphical setup test.

Windows job 101732124538 also executed `Test-Kairnfall-Local.ps1` successfully.
Its PostgreSQL integration step was skipped by design because this workflow runs that step on Linux.
This is not evidence of Docker Desktop or graphical gameplay acceptance on Windows.

Ubuntu job 101732124836 executed the new `tools/local_dev.py test --with-database` command.
It created the isolated PostgreSQL test volume, verified password authentication with SELECT 1,
ran the actual suites below, and stopped the test container without removing its volume.
The development database was not selected for these tests.

| Backend suite in the isolated Ubuntu run | Passed | Failed |
| --- | ---: | ---: |
| Core | 29 | 0 |
| Gameplay and input review | 34 | 0 |
| Transaction security | 13 | 0 |
| Real-network/PostgreSQL integration | 18 | 0 |
| Save conflicts | 5 | 0 |
| Total | 99 | 0 |

The integration suite used three real protocol clients. It verified registration, character ownership,
private chat, trade consent, rune insertion, gathering, crafting, travel, bank/auction operations,
realm-writer exclusion, logout, and acknowledged state after a hard server restart.
Three clients do not establish 100-player capacity or a complete MMORPG playthrough.

Observed Ubuntu environment: Ubuntu 24.04.4, Python 3.12.14, .NET SDK 10.0.400,
Docker Compose 2.38.2, and the PostgreSQL 18 Alpine image resolved by the runner.
The database image uses a major-version tag, not an immutable pinned digest.

### Local handoff contracts

Run 34118906616 passed the handoff test suite on Windows and Ubuntu.
The current file defines 16 test methods. They cover all 60 skill-icon sources,
unknown-reference rejection, credential creation/preservation, separate database environments,
secret redaction, native exit-code failure, ignored private files, Compose isolation,
explicit database-test opt-in, retained server/native UI repairs, asset-build ordering,
and required handoff documentation links.

These tests mock some host operations. Their pass is not proof of a complete Windows host lifecycle.
The real Linux database execution above provides additional integration evidence.
PowerShell AST parsing passed for all root launcher scripts on both runners.

The initial Windows contract test failed because text-mode stdin inserted carriage returns into Git paths.
The repair uses binary NUL-delimited `git check-ignore -z --stdin` input/output.
The safety assertion was retained. The corrected test passed on both platforms.

### Generated asset checks

The canonical build includes `tools/complete_skill_icons.py` after the base generator.
The complete pack passes `tools/validate_game_assets.py` with:

| Asset measure | Observed result |
| --- | ---: |
| Structural assertions | 45,248 passed; 0 failed |
| Required image references | 1,583 |
| Generated PNG files | 1,583 |
| Animation sheets included in PNG files | 562 |
| Actor frames checked for visible pixels | 35,136 |
| Required skill icons | 60 |
| Required WAV files | 22 |
| Missing required references | 0 |
| Exact duplicate normal-species image sheets | 0 |
| Exact duplicate normal-species alpha sheets | 0 |

The audit explicitly reports visual_review=not_performed, visual_acceptance=not_approved,
audio_review=not_performed, and gameplay_acceptance=not_tested_by_this_tool.
Different hashes or alpha sheets do not prove anatomically distinct, high-quality artwork.
The local agent must inspect the native frames and actual game presentation.

The current generated catalog SHA-256 is:
`0e93a9c9bedf32b83d0ee05c60efbe8f021a916330f7035b0386f168245bc06d`.
Catalog totals are records, not accepted gameplay content. Recompute them after content changes.

## Remaining compiler warning

The Ubuntu source setup built the backend solution with zero warnings and zero errors.
The Godot C# client compiled with zero errors and one warning:

`CS0108: WorldView.Visible(Point, double) hides inherited member CanvasItem.Visible`.

Inspect `client/Scripts/WorldView.cs` and rename the visibility helper and its call sites
when completing the local refinement pass. Do not suppress the warning without understanding it.
No claim of a warning-free client build is made here.

## Fresh run links

- https://github.com/danial-maqbool/Kairnfall-RPG/pull/26
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34118906621
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34118906616
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34118906617
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34118906683
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34118906686
- https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34118906643

## Historical evidence, not current graphical acceptance

| Revision or check | Observed evidence | Limit |
| --- | --- | --- |
| Main c5d80d60f5803958da0a76a61f9aae436f49c310 | PR #21 merged actual trade-consent and stack-splitting repair plus 13 security tests. | This handoff preserves and reruns those tests. |
| Asset source 3d787bd8e41efb3d721e3b8ccf00f786243104b9 | Run 34113289960 passed 44,888 structural assertions for 1,523 PNG files. | The old expected-reference set omitted the 60 skill icons now added. |
| Native client f326b9aa87e1f1f5ee143d03d4756813e0165b0c | Run 34116169448 passed the native Godot button signal contract. Runs 34116169286 and 34116169509 passed compilation/backend checks. | The native test must run again on the consolidated local checkout. |
| Same historical native client | Run 34116169395 failed at the real client/import step; its Windows-package job was skipped. | Diagnose locally. No later full graphical pass is established by this handoff. |

## Required local acceptance work

- Run full bootstrap with the verified Godot editor and matching templates. Import and launch the real project.
- Test local Windows process lifecycle, Docker Desktop, occupied ports, shutdown, and credential recovery.
- Rerun native signal tests and create fresh non-headless smoke screenshots.
- Inspect the screenshots and complete the full clean-account 26-step gameplay sequence.
- Test all skill effects/unlocks, class identity, item/rune/ability effects, quests, bosses, services, and map routes.
- Implement missing requirements and repair gameplay defects; do not assume only testing remains.
- Complete actual sprite/UI/environment visual reviews and audio listening reviews.
- Complete two-client graphical play, sustained load tests, balance simulations, and performance measurements.
- Test crash/restart recovery and an extracted Windows client/server package in a clean directory.
- Publish a finished release only after the accepted full-game gates pass at the reported revision.
