# Kairnfall local source handoff

## Final merchant boundaries — 2026-09-09

Start with [the verified merchant boundary checkpoint](MERCHANT_BOUNDARIES_2026-09-09.md). Integration `51b575323969da9c9b0fab5f3c23a7a5f0c4147e` installs exact passing source `b941ac221e3084772330b98d5b0cbc7e6302669c`. It retains compact comparisons and adds visible large totals, current equipped-stat comparisons, explicit reselection and a narrow cancelled-socket shutdown fix. Full run `34322836260` and graphical run `34322836227` passed. Keep only main and preserve all newer source, local settings and saves. Do not restore a previous candidate or claim manual Windows acceptance.

## Latest item and merchant integration — 2026-09-09

Read [Item commerce verified integration](ITEM_COMMERCE_VERIFIED_2026-09-09.md). Source `dbd31fc4b0391045754966eb30c73fb1e4404f71` contains the passing compact-card and merchant-sale candidate. It retains earlier targeting, challenge XP, hunting, Foundry and Atelier work. Both native sale buttons were exercised over the real connection and their exact gold and quantities survived reconnect. Keep only main and preserve all saves. Windows, independent visual and full-game release gates remain separate.

## Targeting and difficulty continuation — 2026-09-09

Task 1 is integrated at `1628b73770393980bb2d1e8017345f2f830786d7`. It repairs Tab being consumed by GUI focus traversal. The subsequent density, progression, pursuit and HUD source is described in [Challenge balance](../CHALLENGE_BALANCE.md) and [the player guide](../HUNTING_AND_JOURNEY.md). Consult the latest dated session checkpoint for exact source and final verification status. Preserve historical failed attempts rather than interpreting a prepared candidate as an accepted integration. Keep only main, preserve saves, and do not promise a completed game from passing native fixtures.

## Current hunting and presentation integration — 2026-09-09

Read [HUNTING_AND_PRESENTATION_2026-09-09](HUNTING_AND_PRESENTATION_2026-09-09.md) first. Actual source is integrated at `9d9b361fa49e5f85f802c494819227f1947b7f9c`, not only stored in a candidate. The complete retained suite and graphical workflow passed for exact source `e5b0269048ef3ffd2fba6f511970e2f9d25dfeb2`. This includes dense hunting, beginner dungeons, Atelier import, native pixels, Q dash, target cycling, early progression and shared inventory views. The pending execution checkpoint is historical. Keep only main and preserve all intervening source, saves, credentials and local tools. Independent visual and hardware/release gates remain open.

## Latest equipment integration — 2026-09-09

Start from live main and read [Equipment progression checkpoint](EQUIPMENT_PROGRESSION_2026-09-09.md). Actual source is integrated in `b9dadef30bfd5747ff8a44c85c534bf22852dae7` and `4c560ccadf6a43ab4d0601844a8e200190795bd9`. The latest work adds all named gear tiers, real recipes, a native Upgrade guide, bounded crafting controls and clear workstation access. Rebuild client and server catalogs together. Preserve saves, credentials and prior repairs. Whole-game and Windows package acceptance remain incomplete.

## Latest integrated presentation checkpoint

Continue from live main, not an older candidate. Read [ACTION_PRESENTATION_2026-09-08](ACTION_PRESENTATION_2026-09-08.md).
Implementation `4d840b5f802fcf79f0e048ba2223ccf6fbecdcae` retains the furnished rooms and bow/browser
repairs and adds tested creature action playback, ability-panel lifecycle and HUD corrections.
The checkpoint records 94 Python tests, 601 native control checks, 83 live server checks,
and 126 graphical fixture checks. Native rendering passed; independent image inspection
was blocked by the chat runtime. Full visual and whole-game acceptance are not granted.
Preserve saved data and keep only main. Do not reset to an evidence or preparation commit.

## Previous local Windows status

Continue only on `main`; do not create branches or pull requests. The
[September 8 visual checkpoint](LOCAL_VISUAL_REVIEW_2026-09-08.md) supersedes older
workflow/setup status below. Source preparation, native tests and graphical
smoke now pass locally, with tested visual/UI repairs. The game and its visual
acceptance remain incomplete. Preserve all saves and unrelated local files.

### Historical September 7 checkpoint

Local continuation produced repair source `90143dff664ffd5811316cc924fc8983066e3648`
on `team/local/acceptance-repair`. Read
[the Windows acceptance record](LOCAL_ACCEPTANCE_2026-09-07.md) before continuing.
It records repaired session/status security, world collision, native pointer input,
and HUD/map layout, with passing bounded tests. A reviewed follow-up preserves
legacy saved positions and adds secure download resume. Full bootstrap timed out downloading
templates; art failed review, and full gameplay/release gates remain open.

This is a consolidated source checkpoint for local testing, repair, refinement, and release preparation.
It is not a completed MMORPG. Do not assume that only testing remains.
Missing or incomplete gameplay must be implemented during the local continuation.

The requested game scope is in `docs/requirements/ACCEPTED_REQUIREMENTS.md`.
The exact continuation prompt is in `docs/handoff/LOCAL_AGENT_PROMPT.md`.
Machine prerequisites and commands are in `docs/LOCAL_REQUIREMENTS.md`.
Recorded checks and their limits are in `docs/handoff/VERIFICATION.md`.

## One checkout

```powershell
git clone --branch main https://github.com/danial-maqbool/Kairnfall-RPG.git
cd Kairnfall-RPG
git status --short
git rev-parse HEAD
```

For an existing clone, preserve local changes before switching branches.
Fetch `origin` and select the integrated `main` source only when switching can preserve
that work. Do not reset, clean, overwrite, or auto-stash unrelated work.
Work directly on `main` for local repairs. Do not recreate historical team branches. Record the source revision in the local audit and use tested, non-forced fast-forward updates.

This branch starts from main commit `c5d80d60f5803958da0a76a61f9aae436f49c310`.
It retains PR #21's actual transaction and stack-splitting fixes.
It adds the canonical generated-art source from PR #20, not that branch's older server.
It selects the four native button/signal-test files from the native-client workstream.
It adds new source setup, database isolation, skill-icon coverage, and handoff tests.
See `SOURCE_PROVENANCE.json` for exact source revisions.

Do not merge all old branches. There are competing asset builders and old server copies.
Some old PRs contain only task documents. A merged task document is not a finished feature.
Read a PR's diff, base, tests, and scope before using it. Preserve IDs, current security fixes, and stable protocol contracts.

## Reconstruct from source

No chat attachment or expiring CI artifact is required.
The canonical sequence is:

```text
content_src/* -> tools/build_content.py -> content/catalog.json
tools/art/* -> tools/build_game_assets.py -> client/Assets/*
tools/complete_skill_icons.py -> all client skill icons + updated manifest
tools/validate_game_assets.py -> reference/frame/checksum/audio-format report
```

Run this sequence through `tools/local_dev.py assets`. Do not omit the skill-icon stage.
Generated assets are reproducible from checked-in source, but their visual quality is not accepted by generation alone.
Historical manifests with 1,523 PNG files did not include this handoff's additional 60 skill icons.
Use the new audit output instead of repeating historical counts.

## Local setup and first checks

Install Git, Python 3.12.x, PowerShell 7.4+, a stable .NET 10 SDK, and Docker Desktop with Linux containers.
Bootstrap prepares the pinned Pillow dependency and verified Godot 4.7.2 .NET toolchain.
It will fail rather than silently install a different engine or skip a checksum check.

```powershell
pwsh -NoProfile -File .\bootstrap.ps1
pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase
.\.venv\Scripts\python.exe tools/local_dev.py signals
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1
```

Inspect real screenshots and interact with the real client. A headless startup or a zero exit code is not sufficient.
The smoke run must create four fresh PNG files. It does not test all gameplay or prove visual quality.
For two clients, run the standalone server script and open the client script twice with separate accounts.
The local address is `http://127.0.0.1:5077`. No public realm is configured.

## Local data safety

The development database uses port 55432. Integration tests use a separate test database on port 55433.
Their named Docker volumes are separate. The project name depends on the checkout path.
The launcher creates random passwords in `.local/database.json`. This private file is ignored by Git.
Treat that file and the volumes as a pair. Keep the workspace private on Windows.
Do not publish resolved Compose configuration, environment dumps, account tables, or database backups.

`Test-Kairnfall-Local.ps1 -WithDatabase` opts into tests and does not use `KAIRNFALL_DB` from the caller.
Lower-level direct test commands require deliberate test configuration. Never use a personal or production database.

The combined development command owns its server child and stops it after the client exits.
Use Ctrl+C for a standalone server. Stop database containers with `Stop-Kairnfall-Database.ps1`.
No command removes volumes. Do not use volume deletion or source-reset commands as general repair steps.

## Known acceptance gaps at this handoff

1. Full graphical gameplay has not passed acceptance on this consolidated checkout.
2. A historical native-client branch passed its signal contract but failed its live-client job. Read `VERIFICATION.md`.
3. The complete sprite set has not passed actual native-scale and in-engine visual review.
4. File uniqueness does not prove species-specific anatomy. The local agent must inspect and repair inappropriate shapes and animations.
5. Equipment alignment, directional layering, attack/cast poses, UI focus, resizing, and all interaction paths require local testing.
6. The 60 skill records need action/effect/unlock evidence. Catalog descriptions are not implementation proof.
7. Complete world reachability, service paths, all quests, boss encounters, secrets, and progression remain acceptance work.
8. Economy simulations, audio listening review, sustained multiplayer/load tests, and a clean extracted Windows package remain unverified.
9. No public persistent production server is deployed. The development realm is local only.
10. No independent multi-agent review is claimed for the handoff authoring session.

The local agent is authorized to fix defects and implement missing requirements, not only produce a list of problems.
Do not remove features, lower content requirements, or weaken tests to mark completion.

## First repair priorities

- Confirm the source and generated catalogs agree. Make all setup and test commands pass.
- Confirm native button callbacks, asynchronous UI actions, and repeated page recreation.
- Diagnose the first real-client failure from logs. Do not suppress engine errors.
- Complete the clean-account gameplay sequence without cheats or direct reward injection.
- Verify two-client ownership, trading, banking, auctions, party/guild/chat, and restart persistence.
- Inspect every normal species and boss. Inspect representative complete animation cycles in all directions.
- Audit each skill and each advertised rune/ability effect against a real server execution path.
- Check region graph plus walkable tile paths to every required exit, NPC, service, and objective.
- Run balance, security, crash/recovery, and performance tests.
- Build and test Windows packages locally only after the preceding gates pass.

## Evidence to retain

Keep raw logs, captures, test databases, and diagnostic output in ignored `artifacts/` or private storage.
Commit sanitized summaries and reproduction tests. Record commit SHA, OS, tool versions, hardware,
commands, exit codes, timestamps, test counts, failures, and screenshot/recording paths.
Do not publish personal Windows paths, credentials, session tokens, or account data.

Update `docs/handoff/VERIFICATION.md`, `docs/QA_MATRIX.md`, `docs/CONTENT_MATRIX.md`,
and `docs/FINAL_AUDIT.md`. Use separate statuses for implementation, automated tests,
visual review, audio review, gameplay review, load capacity, and package acceptance.

When complete, provide a tested Windows client/server package, launch instructions, real gameplay images,
checksums, a release/tag, and an audit that matches the tested revision.
Until then, call the result a development checkpoint and state the exact remaining blockers.
