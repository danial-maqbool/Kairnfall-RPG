Follow-up: [original presentation, route repair, updated tests and packaging evidence](NATIVE_CLASSIC_VISUAL_ROUTE_FOLLOWUP_2026_10_01.md). The counts and failures below remain this earlier checkpoint's history.

# Native classic controls and playable-loop checkpoint — October 1, 2026

This continues [the first October 1 checkpoint](NATIVE_CLASSIC_CHECKPOINT_2026_10_01.md).
The authoritative project remains `D:\1 - Personal\Docs\Danial\Masters\MS AI\3rd Sem\Side Projects\Kairnfall-RPG`:
Godot 4.7.2 .NET/C#, a .NET 10 authoritative server, and PostgreSQL 18.
The `MysteraLegacyLocal` browser project is historical. Its code, raw/reference corpus and saved games were not rewritten.
These are local, uncommitted changes on `main`, based on HEAD `192c8b50ce6ecac11e6327189af6208dd26c7944`.
Existing dirty changes were preserved. Historical CI and earlier artwork reviews are not approvals for this working tree.

## What to try

In the native client's Settings, select **Use classic local presentation**. It enables tile controls,
selected-target attacks, repeat gathering, the compact HUD and compact item panels together.
Individual settings and the full HUD/guides remain available. Existing saved positions and gameplay progress are retained.

- WASD/arrows: cardinal, server-owned tile steps. A tap completes its current tile; a held key continues.
- Click a living creature, then move into the existing weapon reach: attack that selected target automatically.
  Selection creates no chase path. Attack range, line of sight, cooldowns and rewards remain server-owned.
- Face or select an adjacent resource and hold Space through its first accepted gather. Releasing after acceptance
  keeps that resource armed through its real recovery time. Action again, movement, menus, chat, focus loss,
  food use, death or disconnect stops the intention. Releasing before acceptance cancels it.
- Shift: collect eligible loot on the current tile. Foreign reserved loot remains protected by the server.
- Bag: 15 slots per page, quantities at the lower left, selected-item inspector at the left,
  equipment/use/read actions, integer Drop amount and Drop all. Equipped and quest items cannot be dropped.
  Dropped possessions are reserved for their owner for 60 seconds, then public, and expire after 180 seconds.
- Crafting: 15 recipes per page, actual ingredient/skill/station requirements, Craft/Build, Info and the full guide.
  A build still requires the existing world-placement validation. Opening placement consumes no materials.
- The 2×2 quick-item controls use the actual native healing, mana, food and purge items and cooldowns.
  Native food restores stamina and grants regeneration; a Mystera hunger model has not been invented.

`Play-Classic-Native-Preview.cmd` in the MysteraLegacyLocal workspace launches a **separate retained offline
preview** using the already verified local PostgreSQL binary and native client. Create a preview account there;
personal accounts belong to the original realm. Its world persists across runs. This launcher starts no Docker
or Windows service, downloads nothing, and stops only the child game server/database it started. The startup
check uses the actual Main scene and separate `Kairnfall-Classic-Preview` preferences. Human preview play has
not been independently accepted.
Repeated startup passed with the same retained preview schema, including starting from a stopped private
database and shutting it down afterward. Final checks confirmed ports 5077, 5078 and 55433 were stopped;
all private realm data was retained.

The normal development launcher still needs its configured local PostgreSQL/Docker engine. That personal engine
was not started here because doing so could start unrelated services. The separate QA route described below
proves the local client/server loop without modifying or substituting the player's saved realm.

## Implementation and preservation

`move` keeps its existing behavior unless the optional classic intent is supplied. Legacy clients and continuous
controls remain valid. Grid intent is ephemeral: no save schema or item/character/template IDs changed.
Older valid positions align through actual movement, rather than being rounded during loading. Existing speed,
collision, stun/root, roads, travel, dash and respawn rules remain authoritative.

Repeat gathering requests the existing `gather` action, uses existing tools/skills/stamina, and respects node
recovery and the 1.8-second gather cooldown. Fishing still recovers in 12 seconds and copper in 20.5 seconds;
these are native catalog values, not claimed Mystera cadence. Nothing predicts or injects XP, materials or damage.

A live test found that the old server had no `drop` handler despite the proposed UI action. The new handler
uses the existing item-transfer and owned-loot model, atomic rejection rollback and action replay receipts.
Partial drops preserve the original stack ID and create one distinct split ID. Whole drops preserve item metadata.

Two input/UI faults found during verification were repaired: world targets are now populated from snapshots
and camera processing instead of only `_Draw`; gameplay Space reaches the world before a focused HUD button
can consume it. Modal/chat/focus guards remain. Compact inspectors keep amount editors and action buttons
stable across unrelated snapshots, updating when their actual item/action requirements change.

The compact HUD uses green health and narrow health/mana/stamina/character-XP/active-skill-XP overlays, with
Character/Bag/Menu, translucent chat and all ten ability slots reachable at 916×515. XP popups use actual
snapshot deltas. Existing original native artwork is retained; this is not an approved art replacement.
Native login accepts only loopback addresses. No production Mystera endpoint, account or game code is involved.

## Verification

Main changed-file groups (the working tree also contains the user's earlier changes):

- Native presentation/actions: `client/Scripts/GameRoot.Classic*.cs`, `ClassicItemSlot.cs`,
  `ClassicCraftRules.cs`, `ClassicInteractionRules.cs`, and integration in the existing GameRoot partials.
- Render-independent picking: `client/Scripts/WorldView.Interactions.cs` and additive changes in `WorldView.cs`.
- Authority/transport: `src/Kairnfall.Core/GridMovementRules.cs`, `RealmGridMovement.cs`, `RealmItemDrop.cs`,
  `GameConnection.cs`, and additive dispatch/tick changes in `RealmEngine.cs`/`RealmEconomy.cs`.
- Verification: `client/Tests/ClassicExperienceContract.cs/.tscn`, `ClassicLiveLoopContract.cs/.tscn`,
  `tests/Kairnfall.Tests/GridMovementCases.cs`, `ItemDropCases.cs`, and retained-fixture repairs.
- Native documentation: `README.md`, `HANDOFF.md` and the two dated October 1 reports.
- Workspace launch/evidence tools: `Play-Classic-Native-Preview.cmd` and the `tools/run_*native*.py` helpers.

Preservation evidence is deliberately separate: no personal native database was opened or rewritten, and no
personal SQL-realm reload is claimed. Historical browser save/backup sizes and timestamps remained unchanged.
The exact item/progress/timer/building comparisons above used only the newly generated isolated QA account.

Release solution build: zero warnings/errors. Native Debug client build: zero errors, one existing CS8793
warning in `PlayerExperienceContract.cs:76`. Builds used installed/cached dependencies.

| Check | Fresh result |
|---|---|
| Core gameplay, including seven new grid cases and five item-drop cases | 53 passed, 0 failed |
| Retained gameplay review | 34 passed, 0 failed |
| Retained transaction/security suite | 13 passed, 0 failed |
| Private PostgreSQL revision/concurrency review | 5 passed, 0 failed |
| New native classic fixture | 105 checks passed; clean engine-error scan |
| Retained control fixture | 1,184 checks passed; clean engine-error scan |
| Native input routing | Passed; clean engine-error scan |
| Retained player-experience fixture | 447 checks passed; clean engine-error scan |
| Windows layout/accessibility emulation | 1,639 checks passed; clean engine-error scan |
| XP HUD fixture | 9 checks passed; clean engine-error scan |
| Character presentation | 177 graphical checks passed; clean engine-error scan |
| Normal-account playthrough, native mouse/key input and real server actions | 79 checks passed, headless gameplay gate |
| Same QA realm after server restart | 14 checks passed, exact possession/progress/structure comparisons |
| Same retained QA save in the native Windows renderer | 15 checks passed, including a real restored-player/campfire frame |
| Separate retained preview Main-scene startup | Passed with clean engine-error scan; headless startup only |
| Offline draft Windows export | Blocked by three uncached .NET 10.0.11 runtime packs; no release produced |

The final Space change was followed by fresh classic, input and control reruns. The broader retained native
batch passed before that small input change; it is not described as an exact-head CI run. A subsequent test-only
correction uses actual direction-key taps before resource actions: a route may stop adjacent while facing
another object, and Space correctly uses the facing object. No production facing rule was weakened for the test.

Native graphical fixtures use a copied project named `Kairnfall-Classic-QA`, and assert their separate `user://`
directory. Actual PNGs at 916×515 and 1280×720 were inspected, including inventory and crafting panels.
An additional real-account graphical attempt produced movement/equipment/fishing/food/drop screenshots and
completed mining, then timed out on the path to the forge. Its full graphical gate failed and remains open;
the cause of that route timeout is not proven by that log. A separate graphical restart of the successful
headless realm passed all saved-state comparisons and rendered the owned campfire in Kingsmeadow.
The initial first-checkpoint original-project fixture may have exercised ordinary UI preferences; pre-test UI
preferences were not captured. Preservation claims apply to gameplay saves, not an invented UI-preference backup.

The real-account gate uses only a fresh QA schema and generated QA account. It performs ordinary merchant,
equipment, gather, consume, drop/loot, craft, selected combat, road and build actions through the actual local
client/server. It never injects player state or rewards. Its restart phase compares exact character identity,
valid position, every owned item and metadata, gold/equipment, skill/quest progress, cooldown/death timers,
owned structure identity/ownership/position/recovery time, and a non-rewinding realm clock.
Headless runs explicitly label themselves and skip screenshots; their success does not establish graphical or
human keyboard acceptance.

Docker remained stopped. To unblock database verification without touching other projects, a private game-only
PostgreSQL 18.6 cluster ran on `127.0.0.1:55433`, and only its QA game server used `127.0.0.1:5078`.
The embedded Windows package came from the Apache-licensed Zonky testing distribution on Maven Central:
`embedded-postgres-binaries-windows-amd64:18.6.0`, verified against published SHA-256
`b7ef2d03588e0439f0d0a2250f43905f7464f1e96ace47703ceaf79094198150` before extraction.
The regular personal database, containers, volumes and credentials were not opened or changed. No Windows
service was installed. The private test cluster and failed schemas are retained as QA data.

The draft export reused the existing official .NET 4.7.2 templates, verified against the pinned archive SHA-256
`92f8681e349ef1f90891b792da95e3b2b0bd1ed610b78018c58feb2d87e15a9d`, and checked the extracted Windows
template against that archive. A QA-only NuGet configuration cleared network sources; no templates were
installed and no packages downloaded. Publish failed with NU1100 for `Microsoft.NETCore.App.Runtime.win-x64`,
`Microsoft.WindowsDesktop.App.Runtime.win-x64` and `Microsoft.AspNetCore.App.Runtime.win-x64`, each at 10.0.11.
The partial executable/PCK are failed-export evidence, not usable deliverables or an approved release.
The copied QA project/export-preset source was restored after the attempt. Use the source-based preview launcher.

Failed attempts remain evidence, not passes: an initial fixture compile error was corrected; the old missing
drop handler was repaired; graphical runs cancelled gathering after external desktop focus loss; a restricted
Godot invocation hit log/certificate-store permissions and was rerun with appropriate scoped permissions;
one live fixture held a control across its rebuild; later mining diagnostics showed it facing a tree rather
than ore. Full uninterrupted graphical/human play remains a separate gate. Focus guards were not bypassed.

Evidence under `MysteraLegacyLocal`:

- `scratch/native_classic_results/native-results.json`, native fixture logs and `frames/`.
- `scratch/native_classic_results/frames/02-compact-916.png`, `04-inventory-916.png`, `05-crafting-916.png`.
- `scratch/native_classic_live/classic_*/live-results.json` and gameplay/server/reload logs.
- Final full-loop pass: `scratch/native_classic_live/classic_18b86bd8010d46e69c16017f815ee048/live-results.json`.
- Preview startup: `scratch/standalone-postgres/private-qa/native-preview/startup-results.json`.
- Graphical saved-state verification: `scratch/native_classic_playable/graphical-reload/results.json` and
  `frames/09-server-reload.png`.
- Real graphical play frames: `scratch/native_classic_live/classic_d2b5f10d91234bcb966b79b63c971825/frames/`;
  its `live-results.json` records the incomplete full gate as failed.
- Failed offline export: `scratch/native_packaging/draft_1dd54c2c8cc14a7c8f6480652e2d5fd3/export-results.json`
  and `missing-runtime-packs.txt`.
- `scratch/native_classic_playable/final-source-manifest.json` records the tested local source hashes.
- `scratch/native-classic-database-review.log` records the five private database checks.
- Prepared-file manifests and byte-exact pre-edit backups in the `scratch/native_*` staging folders.
- `tools/run_native_classic_checkpoint_qa.py`, `tools/run_isolated_native_live.py`, `tools/isolated_game_pg.py`,
  `tools/run_native_graphical_reload.py`, `tools/run_local_native_preview.py`, `tools/try_native_draft_export.py`,
  and `Play-Classic-Native-Preview.cmd`.

QA password/connection files and `private-qa-save.json` are local generated secrets, not deliverables to attach,
commit or publish. No personal save was reset, deleted or migrated. No unrelated service was restarted.
There was no commit, push, tag, release, publication or deployment.

## Remaining gaps

| Observed reference | Remaining difference |
|---|---|
| Dense stippled grass, layered crowns, small avatar, gray 3×3 spawn pad | Existing native art/village retained; close visual parity and prior failed art review remain open |
| Narrow Health/Food/Experience bars | Compact native bars added; hunger/food depletion semantics remain unverified |
| Circular action control and very sparse HUD | Native rectangular actions and ten ability slots retained; further layout/art review needed |
| White damage numbers/red hit pixels and exact target treatment | Existing native combat feedback retained, with green player/yellow target health; exact reference effects remain incomplete |
| Fifteen-slot inventory/crafting overlays | Implemented using native items/recipes; modal blocks world input for existing safety/keyboard contracts |
| Stone Pickaxe: 10 Stone + 5 Wood, Damage +4 | No native Stone Pickaxe template; native Copper Pickaxe uses copper bar/cured leather/oak plank at a workbench |
| Reference Fire: 3 Tinder + 1 Flint + 5 Wood | Native campfire recipe/placement retained; reference lifecycle/unlocks not fully observed |
| Hold/release harvesting and skill chance | Repeat intention implemented; exact reference release threshold/success chance is unknown |
| Tutorial sign/rats/quest XP and daily 20% bonus | Existing native first-hour quests retained; session-specific numbers were not adopted as canonical balance |
| Complete native offline release | Normal personal-realm startup, uninterrupted human/graphical full-loop acceptance, audio, sustained load, templates and Windows packaging remain open |

This is a bounded native implementation and verification checkpoint, not full MMO parity, an approved art set,
a packaged Windows release or a review of unavailable Mystera3/4 chat history.
