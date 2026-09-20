# Hunting and controls continuation — pending verification

This record does not approve gameplay changes or claim a successful source integration.

## Request

Increase ordinary hunting populations relative to the existing one-creature-per-species baseline: 30x for region levels 0–20, 20x for 21–40, 15x for 41–60, then decreasing high-level multipliers. Use multiple reachable patches rather than one overlapping pile. Keep village service cores and interiors safe. Add deliberate target cycling, a short mana-consuming dash, easier early equipment use and overall progression, grouped inventory views with one shared capacity, finer rendering, map specialties, and validated Atelier art integration. Keep only main and preserve all saves, source history and authority checks.

## Retained work

The earlier recovered local source was copied from the verified source-review artifact for `63e6c112fb128b943fe6e2fead93c6b3ff81859b`. Its pre-change solution build and 33/34/13 backend test suites passed. A later local client build containing dash/control, early-progression and inventory-grouping changes passed with zero warnings/errors. That compilation was not a native-input, network, artwork or final gameplay acceptance result.

A candidate-preparation request was attempted against `4d8c8817d4bae66e359b2d9bc63d9ca8563016db`, preserving the newer Atelier source. Inspect live `.ci/client-edit-request.json` and its actual preparation logs before using it. The proposed additions include `DashRules.cs`, `BeginnerProgression.cs`, `GameRoot.MobControls.cs`, `InventorySections.cs`, and new core/native/live regressions. Preparation and final integration were not verified in this interrupted execution.

The local implementation workspace was `/mnt/data/Kairnfall-RPG`, not the user's Windows checkout. Do not assume its uncommitted files were copied to Windows. The runtime later stopped returning usable execution results. A partial `HuntingGrounds.cs` write may exist there; do not integrate a truncated file.

## Intended controls and compatibility

- Q: server-validated 2.5-tile dash, 4 mana, 0.65-second cooldown, no invulnerability. Reject death, root, stun, silence, insufficient mana, invalid direction and blocked travel. Test replay and collision.
- Tab / Shift+Tab: forward/backward selection of nearby living creatures, including deliberately targeted neutral wildlife. Exclude pets, corpses and blocked line of sight.
- Grade 5/10/15 equipment use gates: matching skill 3/6/10. Preserve the original grade, item IDs, crafting requirements and raw saved skill XP. Keep grade 20 and higher unchanged.
- Inventory views: equipped, ready to equip, locked/unavailable, tools/supplies. All remain the same 64-slot backpack. Filtering must never add capacity or transfer ownership.

These are intended and partially compiled changes, not all closed acceptance gates. Validate the actual source and tests before publication.

## Next safe operations

1. Fetch current main. Preserve any intervening Atelier or other source changes.
2. Recover the current preparation result and fix exact replacement or compiler errors. Do not weaken tests.
3. Run core, security, migration, PostgreSQL, native input, inventory, dash, target and live-client checks before integrating the control/progression changes.
4. Finish deterministic hunting plans. Verify exact ordinary populations, unique stable IDs, safe cores, reachable spawn positions, separated members, bounded packs and save-load idempotency. Do not multiply bosses by the ordinary mob factor.
5. Profile the denser realm, including tick time, snapshot size and sequenced-action rollback copies. Do not claim 20 Hz without measurement.
6. Integrate Atelier assets by exact matching catalog IDs and verified frame sizes. Do not replace live gameplay records with the alternative Atelier gear ladder. Body and worn-equipment layers must use one coherent rig.
7. Render at native/finer pixel scale without shrinking the authoritative world or collision geometry. Preserve readable GUI text. Inspect real output at 1280x720 and 1920x1080.
8. Publish only passing, reviewed source onto current main with a non-forced update. Fetch the resulting ref again and record the actual tested SHA.

No independent coding-agent outputs were produced. The discovered Zeiko actions are customer-support tools, not game-development agents. Do not report simulated roles as independently executed agents.

Visual acceptance, the requested hunting-density extension, full-game acceptance, Windows DPI, measured performance and release acceptance remain open. This handoff must not be used as a completion certificate.
