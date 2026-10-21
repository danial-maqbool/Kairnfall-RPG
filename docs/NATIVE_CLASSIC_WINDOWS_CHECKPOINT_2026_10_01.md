# Native classic Windows checkpoint - October 1, 2026

This continues the [native visual/routing follow-up](NATIVE_CLASSIC_VISUAL_ROUTE_FOLLOWUP_2026_10_01.md).
The current Godot 4.7.2 .NET client, .NET 10 authoritative server and PostgreSQL stack remain intact.
Native main HEAD remains `192c8b50ce6ecac11e6327189af6208dd26c7944`; changes are local and uncommitted.
Existing edits, IDs, protocol compatibility and personal saved realms were preserved. No push or deployment occurred.

## What changed

The optional classic mode already includes authoritative cardinal tile movement and camera-following world
presentation, facing interactions/Space and a spiral Action circle, selected-target attacks within native
weapon reach, hold/release gathering on the accepted resource, 15-slot inventory/crafting pages, quick
consumables, exact partial item drops and Shift pickup. The prior route overshoot repair waits for each
server-owned tile step before consuming the next point. Original generated dense grass and layered round
oak crowns, yellow target feedback and authoritative XP/damage feedback are retained.

This continuation moves progression rewards from the large central banner to a small translucent feed
beside the world in classic mode. The title has an explicitly reserved text row, with its full detail
retained; the centered avatar and world targeting stay clear. Expanded layout can still be restored.
Recipe IDs, costs, hunger semantics, XP, skill requirements, resource recovery and rewards remain native.
No unverified Mystera balance or proprietary code/assets were added.

## Windows package

The exact three approved Microsoft 10.0.11 runtime packs downloaded successfully: **91,827,616 bytes**.
Their hashes, package identity/version, ZIP integrity and NuGet author/repository signatures were verified.
The task-local export feed also uses cached Godot 4.7.2 packages. No further export-time downloads,
runtime/SDK installation, system service, certificate change or security bypass was performed.

The standard Godot self-contained Windows export passed. The **client** contains its .NET runtime and
does not need the editor to launch. Its 196 client/runtime files total **238,293,029 bytes**,
with hashes in `scratch/native_packaging/verified-current-package.json`.
The complete local game still uses this checkout's prebuilt native server, the already-installed .NET 10
for that server, cached task PostgreSQL and Python launcher. This is a usable local test checkpoint,
not an installer, a fully portable server bundle or an approved public release.

The exported main screen initializes and closes through ordinary Windows WM_CLOSE sent only to its owned
window, with clean engine-error scans. No focus forcing was used. The release template disables arbitrary
command-line scene paths; a small QA-only entrypoint selects a fixed fixture whitelist and otherwise opens
the normal native Main scene. It adds no production gameplay mechanism. Its first screenshot observer
forced exit too early and reported resources in use; that retained failed QA shutdown is not a game-startup
failure. Verification now uses the existing normal close path. Earlier access-violation framework drafts
and the first timed-out export remain historical failed attempts, not launch deliverables.

## Launch locally

From MysteraLegacyLocal, run **`Play-Classic-Windows-Package.cmd`**. It validates all 196 package hashes,
starts only the game-specific private PostgreSQL/server if needed, then opens the verified client.
Create/sign into a **preview account**, then use **Settings > Use classic local presentation**.
This retains the existing separate preview schema and progress; it never opens the personal SQL realm.
Closing the game stops its owned server and stops the QA database only if the launcher started it.
Source preview remains available through `Play-Classic-Native-Preview.cmd`.

The local endpoint is `http://127.0.0.1:5077`; nonloopback login addresses are refused. QA account tests
use `127.0.0.1:5078` and the retained game-only PostgreSQL cluster uses `127.0.0.1:55433`.
No production server/WebSocket is needed. Existing database-wide single-server ownership is preserved,
so preview and QA servers cannot run concurrently against their shared private database.

## Verified evidence

| Gate | Actual result |
|---|---|
| Release solution | Zero warnings/errors |
| Native Debug client | Zero errors; pre-existing CS8793 warning at PlayerExperienceContract.cs:76 |
| Retained core / review / security | 54 / 34 / 13 passed |
| Current native and packaged graphical classic fixture | 134 checks each, clean engine-error scans |
| Packaged native Main | Initialized, actual main-screen PNG inspected, normal window-close exit 0 |
| Packaged normal-account complete gameplay | 100 passed; explicitly headless |
| Same packaged QA realm after server restart | 14 exact saved-state checks passed |
| Same packaged QA save in Windows renderer | 15 passed; restored avatar and owned campfire frame inspected |
| Packaged local-preview cold startup/shutdown | Passed, same retained preview realm |

The complete account gate uses real local-server actions and native input handlers: movement/collision-valid
routes, equipment, normally purchased food, fishing with accepted hold/release repeat and native recovery,
food benefit, drop-one/Shift-pickup conservation, copper gathering/smelting and skill XP, normally acquired
timber/ore, exact selected rat combat without a selection chase, loot, wilderness road travel, real compact
UI campfire placement and construction XP. No money, rewards or character state are injected.

Restart comparisons cover exact character identity/region/valid position, item IDs/metadata/quantities,
gold/equipment, skills/quests, cooldown/death timers, owned structure identity/owner/position/recovery time,
non-rewinding clock and absence of stale action intentions. This applies to a newly generated QA account;
personal SQL saves were not opened or migrated, and no personal reload is claimed.

Uninterrupted graphical full-loop acceptance remains **open**. The packaged graphical attempt passed
repeat fishing, food, inventory/equipment, drop/pickup, smelting and timber gathering, then explicitly
logged `ROUTE_CANCEL application focus lost` while walking. Cancellation was correctly retained; no focus
safeguard was bypassed. The prior focused graphical fishing diagnosis passed 25 checks, and this new
graphical run passed repeat fishing again. The earlier unclassified fishing timeout has not reproduced;
its original log still does not prove its cause. A complete headless gate and short real graphical
save-reload gate are separate evidence, not a claim of an uninterrupted human playthrough.

Physical keyboard/mouse feel, actual monitor DPI, audio quality, load/stress and human art approval remain
open. Current native tiles, village/spawn footprint, humanoid/equipment art, catalog/classes, recipes,
survival semantics and progression still differ from the observed Mystera tutorial. Full MMO parity,
unobserved mechanics and exact canonical balance have not been implemented or claimed.

## Evidence paths (relative to MysteraLegacyLocal)

- `scratch/native_packaging/approved-runtime-packs/verification.json`: exact official downloads/signatures.
- `scratch/native_packaging/approved_e55cc231f7b44c3399b0c8bc844b0e7c/export-results.json`, `source-checksums.json`,
  `package-runtime-results.json`, logs and frames: current self-contained client export/runtime/134.
- `scratch/native_packaging/verified-current-package.json`: pin and every client/runtime checksum.
- `scratch/native_classic_live/classic_c2661f68f80b4fb5b2abac7b727987bc/live-results.json` and normal/reload logs: 100/14.
- `scratch/native_classic_playable/graphical-reload-classic_c2661f68f80b4fb5b2abac7b727987bc/results.json` and
  `frames/09-server-reload.png`: current packaged rendered save gate, 15.
- `scratch/native_classic_live/classic_2ba7a904a6324a1083f7261e59c4c27f/live-results.json` and log: preserved graphical interruption.
- `scratch/native_classic_playable/final-source-manifest.json`, `verification.json`: current source/evidence index.
- `scratch/standalone-postgres/private-qa/native-preview/package-startup-results.json`: retained preview check.

The private QA save record contains a generated test password. Do not publish or attach it or the
task database credentials. QA data and previous failed evidence remain intact for later investigation.
The working tree and all personal saves remain preserved; all game-specific test processes are stopped
after this checkpoint. No unrelated service was restarted.
