# Journey update: final inventory verification — 2026-09-09

## Scope and source

This record accompanies the integration of exact source `f2ef5643d9e4860adaa8769155b86b90af1b622e` onto main. That source contains the complete hunting, dash, target, early progression, shared inventory, Atelier and native-pixel implementation from `9d9b361fa49e5f85f802c494819227f1947b7f9c`, plus the inventory refresh repair described below.

The integration preserves the documentation published at `0e644eba3a786e1b953ac77800a52abcce91393f`. A comparison to the tested source must show documentation and current `.ci` metadata only. Do not replace newer main source with an old candidate. Ref updates remain non-forced and only main is used.

Read [the player guide](../HUNTING_AND_JOURNEY.md) and [the hunting implementation checkpoint](HUNTING_AND_PRESENTATION_2026-09-09.md) for population multipliers, controls, dungeon connections, asset import safeguards and the original integration evidence. This record supplements those scoped results; it does not invalidate their historical measurements.

## Inventory repair

Ordinary item selection and authoritative snapshots now retain the native inventory slot controls. This preserves keyboard focus and the control identity used by double-click and drag detection. New snapshot data updates the existing slot's quantity, durability, tooltip, selected state and equipped state.

The inventory rebuilds its slot groups only when membership, order, template, bag, grouping or filter results change. Equipping an item still moves it to the Equipped group. Removing an item removes its obsolete control. Closing the inventory releases the retained controls. All groups retain the same 64-slot backpack and unchanged server-side ownership rules.

Changed implementation and regression files:

```text
client/Scripts/GameRoot.Inventory.cs
client/Tests/InventoryRefreshChecks.cs
client/Tests/ControlRulesContract.cs
```

The new regression uses actual native mouse input at 1280x720 and 1920x1080. It checks selection, focus, repeated snapshots, current quantities/durability, group changes, removals, filtering, shared capacity and scene cleanup.

## Final exact-source tests

[Full retained workflow 34300236694](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34300236694) passed for `f2ef5643d9e4860adaa8769155b86b90af1b622e`. Verify job: `102305444678`. Diagnostic job: `102307464022`.

[Graphical workflow 34300236691](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34300236691) passed for the same source. Render job: `102305400607`.

| Suite | Result |
| --- | --- |
| Solution and client build | Passed; client zero warnings/errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session and status-damage security probes | 5 passed |
| Real-network/PostgreSQL / save conflicts | 18 / 5 passed |
| Retained world, save migration, furnishings, equipment and maintenance | Passed |
| Journey controls and progression | 7 groups passed |
| Hunting population, migration and motion | 7 groups passed; 109 regions |
| Python handoff, importer and route tests | 118 passed |
| Native signal lifetime and pointer/keyboard routing | Passed |
| Native player-experience checks | 52 passed |
| Native controls and layout | 1,028 passed |
| Live Godot/server/PostgreSQL checks | 85 passed |
| Authenticated graphical smoke | Passed |
| Separate graphical rendering workflow | Passed |

The live suite exercises Q dash, mana and cooldowns, held Space, chat/menu suppression, equipment buttons, double-click, context menus, drag-and-drop, owned loot and reconnect persistence. The native fixture generates input; it is not a human or Windows hardware-input test.

The unchanged server source also passed Linux and Windows core jobs on the earlier actual hunting integration in [run 34299503013](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34299503013). That is a Windows backend result, not a Windows graphical or DPI approval.

## Density measurement and evidence

The final source census contains 4,682 initial creatures in 109 regions. The 120-second single-player fixture observed 21 nearby creatures. Mean tick was 0.2290911 ms, 95th percentile 0.6112 ms and maximum sampled tick 9.5267 ms. Its sample snapshot was 17,022 bytes. Cached-plan initialization was 8.0032 ms; this is not a cold-start measurement.

These bounded measurements do not include sustained many-player action queues, transaction-copy costs or hardware client frame rate. They do not certify production 20 Hz or RTX 4060 60 FPS.

Full test artifact: `player-experience-f2ef5643d9e4860adaa8769155b86b90af1b622e`, ID `10084880668`, attached to run `34300236694`. It includes exact-source logs, hunting census/performance and authenticated screenshots. The graphical workflow retains the actual runtime captures separately.

## Acceptance boundary

Requested source functionality: integrated with retained automatic tests passing.
Native graphical generation: passed.
Independent inspection of new PNGs: not completed. The container/Python runtime returned execution failures and then transport timeouts; successful generation is not visual approval.
Independent coding-agent team: not executed. No installed coding-team runtime was available. Customer-support agents and CI jobs must not be represented as coding agents.
Windows physical input and 125%/150% DPI, human progression/balance, audio listening, sustained multiplayer, measured hardware performance and extracted Windows package tests remain open.

No release, tag, package approval or whole-game completion is asserted. Preserve saves, local credentials, tool downloads and Docker volumes. Rebuild client and server from the same current main catalog before the next local test.
