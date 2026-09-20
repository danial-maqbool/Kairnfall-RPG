# Player-experience checkpoint — 2026-09-08

## Scope

This checkpoint integrates source candidate `51a48ce5316c85c380bd67c4053215916744e967`.
It is a tested development update. It is not a completed MMORPG or a Windows release.

The candidate passed workflow https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34188954274 .
The verify job was `101942900694`; bounded diagnostic output is in job `101944073207`.
No branch was created. Integration preserves the current main CI files and source-overlay tooling.

## Implemented and exercised

- Contextual Space tap/hold combat, target validity, line of sight, bounded approach, cooldown cadence, and stop conditions.
- Separate interaction/system feedback. Twenty invalid E presses produce no accepted action or chat messages.
- Equipment button, double-click, right-click action panel, matching paper-doll drop, and reconnect state.
- Compact HUD, contextual target frame, resource/cooldown-aware hotbar, collapsible chat, and icon/name pickup feedback.
- Six-category Skills browser, native search, actual catalog unlocks, and stable navigation during XP refresh.
- Four reciprocal starter interiors and indoor staff for existing capital service buildings.
- Deterministic idle wandering and finite wounded-animal retreat. Creature movement does not overshoot a nearby goal.
- Audio lifecycle and native scene teardown repairs. Smoke captures use rendered-frame synchronization.

The previous native encounter failed because a nearly defeated field rat continued fleeing outside melee reach.
The repair limits each low-level retreat to 1.25 tiles followed by a pause. The original 15-second live encounter assertion remains.

## Recorded evidence

| Check | Result |
| --- | --- |
| Client compilation | 0 warnings, 0 errors |
| Core, including four new creature-motion cases | 33 passed |
| Gameplay-review regressions | 34 passed |
| Transaction security | 13 passed |
| Real network/PostgreSQL | 18 passed |
| Save conflicts | 5 passed |
| Session/status security probes | 5 passed |
| World probe | 107 zones; 3,588 masonry tiles; 1,013 destinations; 0 failures |
| Save-migration groups | 5 passed |
| Python handoff and interior tests | 42 passed |
| Native signal and input contracts | Passed |
| Native player-experience contract | 51 checks passed |
| Native control, layout, skill-browser contract | 135 checks passed |
| Real-server native-input contract | 75 checks passed |
| Graphical smoke | Passed on Linux Xvfb/OpenGL |

The live test uses generated native input, real client code, a real authoritative server, and PostgreSQL.
It does not represent human playtesting or Windows hardware input.
Linux Xvfb reported unsupported V-Sync and cursor-theme warnings. It reported no remaining audio-resource leak in these tests.
Raw captures and logs are in the `player-experience-51a48ce5316c85c380bd67c4053215916744e967` workflow artifact.

## Open gates

Full sprite anatomy and animation review, new-player enjoyment, Windows scaling and physical input, sustained multiplayer capacity, complete tutorial playthrough, world balance, audio listening, all skill/ability effects, and Windows packaging remain open.
The player-experience gate is NOT passed. Structural assets and native assertions do not approve art.

The beginner tutorial and population/chest work are separate pending candidates. Do not describe their CI request files as integrated gameplay.

## Local preservation

Do not overwrite `.local`, `.tools`, `.venv`, credentials, or Docker volumes.
The user has local uncommitted source repairs. Back up those source files and review their diffs before updating main.
Use a source overlay only after comparing its base hashes with local files. Do not create another nested checkout.
