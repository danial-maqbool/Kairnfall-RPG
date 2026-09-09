# Hunting and presentation integration — 2026-09-09

## Published source

The complete requested hunting/control/presentation implementation is integrated into `main` at:

```text
9d9b361fa49e5f85f802c494819227f1947b7f9c
```

The GitHub ref was read again after the non-forced update and matched this commit. Its first parent preserves the current main history. Its second parent retains the exact tested source:

```text
e5b0269048ef3ffd2fba6f511970e2f9d25dfeb2
```

A comparison between the tested source and integration commit contains only the two current `.ci` request files. No implementation file differs. No branch, pull request, tag, release, force-push or history rewrite was used. This does not claim that the user's Windows checkout has already pulled these commits.

Earlier successful integrations remain in the same history:

| Commit | Retained implementation |
| --- | --- |
| `def9bd4a9fccc4a6aab769ec0b01eae07a6eb935` | Q dash, target cycling, early progression and shared inventory groups |
| `f988317b68bfff981bb1d59ae564bd9d7fac7e78` | First dense hunting plan, hunting guide, patch motion and field domains |
| `9d9b361fa49e5f85f802c494819227f1947b7f9c` | Complete Atelier import, native pixels, beginner dungeons, migration corrections and native fixture repairs |

This record supersedes the pending-status interpretation of `JOURNEY_HUNTING_EXECUTION_CHECKPOINT.md`. Retain that older record as failure/recovery history. Do not restore its old candidate over current main.

## Implemented user requirements

Read [Hunting, movement and native-pixel presentation](../HUNTING_AND_JOURNEY.md) for player controls and implementation details.

| Area | Implemented behavior |
| --- | --- |
| Ordinary mob population | 30x for region levels 0-20; 20x for 21-40; 15x for 41-60; 10x for 61-80; 5x above 80 |
| Hunting layout | Several reachable species patches, at most five creatures per patch, separated spawn positions, protected service/entry areas |
| Map specialties | Biome descriptions, patch patterns, actual field-boss domains, public regional guide on H and guarded existing caches |
| Beginner underground routes | Wayfarer's Burrows and Silkroot Den; reciprocal transitions and a Silkroot-to-Dawnreach Deepway connection |
| Dungeon correction | Remove grossly over-level ordinary spawns; preserve captured animals and existing boss state |
| Target controls | Tab and Shift+Tab cycle eligible living creatures, including deliberately hunted neutral wildlife |
| Dash | Q requests at most 2.5 tiles; 4 mana; 0.65 seconds; authoritative collision, status, replay and resource checks |
| Inventory | Equipped, Ready to equip, Locked or unavailable, Tools and supplies; one shared 64-slot backpack |
| Early equipment | Grade 5/10/15 use gates become matching skill 3/6/10; requirements at 20+ and crafting grades remain unchanged |
| Early progression | Smooth overall-level bonus without rewriting raw skill XP, individual skill levels or old saved item IDs |
| Finer pixels | Default 1x world zoom, no full-canvas window stretch, native-size item icons, independent 1x/2x/3x preference |
| Atelier | 2,982 matching assets copied after integrity, dimensions and complete-rig validation; independent gear ladder excluded |

The census contains 4,682 initial creatures and 109 regions. These are spawn slots and seeded instances, not a guarantee that every creature is alive or visible simultaneously. Interiors and settlement service cores remain safe. Bosses and elites are not multiplied by the ordinary-species factor.

No new boss template or unique reward table is claimed. Field domains and the two added dungeons deliberately reuse compatible existing boss definitions, attack mechanics and authoritative loot. Existing hidden caches move to guarded sites; the implementation does not add a chest to every patch.

## Defects repaired during recovery

The previous candidate's backend/database tests passed, but its native input fixture failed after canvas stretching was disabled. The headless process did not automatically have a supported desktop-sized window. The first repair sets a physical window size before creating the real client scene and retains all world-click, HUD-consumption and keyboard assertions. It repeats them at 1280x720, 1920x1080 and 1280x720 again.

The next run passed that routing test and exposed the same unsupported-window setup in the independent player-experience fixture. Both player-experience and control fixtures now set and assert their physical window dimensions before placing controls. No critical action was hidden, no input assertion was removed and no requirement was weakened.

A separate review found that the early-access band could raise an original requirement of 2 to 3. The rule now takes the minimum of the original requirement and the accessible band. A new test covers every valid requirement from 1 through 100 for weapons, armor, tools and materials.

## Exact-source verification

[Full retained verification run 34298703468](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34298703468) passed for exact source `e5b0269048ef3ffd2fba6f511970e2f9d25dfeb2`.

Verify job: `102300861536`. Diagnostic job: `102302928619`.

[Graphical verification run 34298703451](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34298703451) passed for the same source. Render job: `102300813256`. Preview/diagnostic job: `102302206320`.

| Suite | Observed result |
| --- | --- |
| Solution and client compilation | Passed; client zero warnings/errors |
| Core tests | 33 passed |
| Gameplay-review tests | 34 passed |
| Transaction-security tests | 13 passed |
| Session/status security probes | 5 passed |
| Real HTTP/WebSocket/PostgreSQL integration | 18 passed |
| Database save-conflict tests | 5 passed |
| World, save-migration, furnishings, equipment and maintenance probe | Passed with no reported failures |
| Journey controls/progression | 7 groups passed |
| Hunting population/migration/motion | 7 groups passed; 109 regions counted |
| Python handoff and importer tests | 118 passed |
| Native signal lifetime and input routing | Passed |
| Native player-experience checks | 52 passed |
| Native control/layout checks | 1,002 passed |
| Live Godot/server/PostgreSQL checks | 85 passed |
| Authenticated graphical smoke | Passed |
| Native visual presentation | 197 checks passed |
| Asset structural validation | 54,999 checks passed; zero errors/warnings in that validator |

The live test used a normal account, generated native input, a real server and disposable PostgreSQL. It exercised movement, Q dash and mana, held Space, chat/menu suppression, equipment actions, native drag/drop, owned loot and reconnect persistence. This is stronger than a launch-only smoke test, but it is not human playtesting or Windows physical-input acceptance.

All retained tests remain in place. The graphics runner reported software-display V-Sync/cursor warnings. Those warnings were not converted into hardware graphics or audio approval.

## Measured density fixture

The exact-source fixture simulated 120 seconds with one active player and 21 nearby observed creatures in Thistle Woods. The realm contained 4,682 creatures.

| Measurement | Result |
| --- | ---: |
| Mean simulation tick | 0.2285968 ms |
| 95th-percentile simulation tick | 0.6215 ms |
| Maximum sampled tick | 1.4798 ms |
| Sample snapshot | 17,022 bytes |
| Mean observed travel | 58.4378 tiles |
| Moving observation samples | 5,165 of 25,200 |
| Cached-plan initialization | 8.285 ms |

These are bounded CI measurements, not a full server capacity result. They exclude sustained many-player action queues, disk/network latency and repeated transaction rollback-copy costs. They do not certify 20 Hz server operation under production load or 60 FPS on the user's RTX 4060.

## Evidence

Full test artifact: `player-experience-e5b0269048ef3ffd2fba6f511970e2f9d25dfeb2`, ID `10084341209`, run `34298703468`.

Graphical artifact: `visual-review-e5b0269048ef3ffd2fba6f511970e2f9d25dfeb2`, ID `10084257653`, run `34298703451`.

The full test artifact contains `hunting/census.json`, `hunting/performance.json`, exact-source logs and authenticated smoke screenshots. The graphical artifact contains actual client images under `engine/`, plus historical source-generator comparisons under `before/` and `after/`.

Representative native images include village views at 1280 and 1920, hunting maps, dungeon views, inventory, equipment, skills, abilities, crafting, map and equipment/creature action galleries. Source-generator comparison sheets are not substitutes for inspecting the imported Atelier art. Use the `engine/` images to review the actual runtime pack.

Sanitized preview objects are retained at commit `5d05a7975a1ca974c8a8278237a3848ac7d9e603`. It is an evidence object, not another branch or a source release. Never reset main to it.

## Source scope

The exact changed-file list is available in the [implementation comparison](https://github.com/danial-maqbool/Kairnfall-RPG/compare/4d8c8817d4bae66e359b2d9bc63d9ca8563016db...9d9b361fa49e5f85f802c494819227f1947b7f9c). Main areas are:

- `src/Kairnfall.Core/{DashRules,BeginnerProgression,HuntingGrounds,RealmHunting}.cs` and their existing realm/AI/progression hooks.
- Client control, experience, equipment-guide, inventory, hunting-guide and pixel-presentation scripts.
- `content_src/hunting_routes.py`, the world-generation hook, and `tools/integrate_atelier.py` in the existing asset build.
- Native journey/hunting/pixel/input/experience tests, the world-probe groups, and Python importer/route tests.

Original equipment definitions, crafting recipes, skill XP, session-expiry handling, trade fingerprints, item ownership and PostgreSQL isolation remain protected by retained checks. No credentials, local configuration, database backup or Docker volume was committed or deleted.

## Status and remaining gates

Implementation: INTEGRATED.
Retained automatic regression: PASSED at the exact source above.
Native graphical rendering: PASSED.
Independent visual inspection in this chat: NOT COMPLETED. Container/Python execution returned `ClientError`; the downloaded PNG archive could not be opened for inspection. Do not report generated images as visually approved.
Independent coding-agent team review: NOT EXECUTED. Tool discovery did not provide an installed coding/team runtime. The available Zeiko functions are customer-support actions and cannot perform this task. CI jobs are not independent coding agents.
Windows physical input and 125%/150% display scaling: NOT APPROVED by these Linux fixtures.
Human early-game balance, sustained multiplayer load, hardware frame rate, audio listening and extracted Windows package: STILL OPEN.
Whole-game release: NOT APPROVED.

The requested source features are no longer pending only in a candidate. The remaining review and hardware gates must not be marked closed without evidence. Rebuild current main locally, preserve saves and local tools, and inspect the native-pixel/Atelier result before approving visual quality.
