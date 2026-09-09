# Item comparison and merchant sales: verified integration — 2026-09-09

## Current integration

Main at session start: `5c3e3e074fc79683ebe5de873548ff413de58675`. Only the main branch was returned by the live branch listing.

Tested candidate: `2559da7e9e22823c49e8a71de87c76f72cffaab7`.
Actual source integration: `dbd31fc4b0391045754966eb30c73fb1e4404f71`.

The source integration is a fast-forward ref update with the existing main as its first parent and the tested candidate as an additional parent. It creates no branch or pull request and rewrites no history. The difference from the tested candidate contains only the retained `.ci` request files and `docs/handoff/TARGET_BALANCE_FINAL_CHECKS_2026-09-09.md`. All runtime source is identical. Foundry and Atelier remain present. No save, credential, editor cache, database or Docker volume was modified.

The earlier Tab, expanded hunting distribution, nonlinear progression, support XP, combat mastery and HUD repairs were already integrated before this item task. See [the prior final record](TARGET_BALANCE_FINAL_CHECKS_2026-09-09.md). Do not treat the older interrupted chat summaries as the current Git state.

## Changes

[Player instructions](../ITEM_COMPARISON_AND_SELLING.md) cover compact centered item cards, independently colored signed stat differences, actual red equipment blockers, and the dedicated merchant selling page. Quantity entry now uses a LineEdit with explicit minus/plus controls. Both sale buttons show exact gold. Server authority, pricing, replay protection and one shared backpack capacity remain intact.

The source also prevents another sale between command confirmation and the corresponding inventory snapshot. Offline native fixtures deliberately delay that snapshot. Live tests walk an ordinary account to a village merchant, use the real shop button, type a quantity and invoke both sale buttons through the production GameConnection. Exact items and gold survive reconnect.

## Final exact-source evidence

Full verification: [run 34313980306](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34313980306), verify job `102346246852`, diagnostics `102348256911`. The revision file records candidate `2559da7e9e22823c49e8a71de87c76f72cffaab7`. Every required stage passed.

Graphical verification: [run 34313980303](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34313980303), renderer `102346214145`, previews `102347653099`. Rendering and evidence upload passed.

| Suite | Result |
| --- | --- |
| Client Debug build | Zero warnings and errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session and status security probes | 5 passed |
| Network/PostgreSQL / save conflicts | 18 / 5 passed |
| Retained world, migration, furnishing, equipment, maintenance, hunting and challenge suites | Passed |
| Actual-encounter support XP | 4 groups passed |
| Item comparison and commerce | 6 groups passed |
| Python handoff/importer tests | 118 passed |
| Native signal lifetime and input routing | Passed |
| Native player experience | 52 checks passed |
| Native control/layout contract | 1,102 checks passed |
| Live Godot/server/PostgreSQL contract | 110 checks passed |
| Authenticated graphical smoke | Passed |
| Native visual presentation | 263 checks passed |
| Art-focused Python tests | 24 passed |
| Asset construction assertions | 54,999 passed; not visual approval |

The real-network suite is distinct from isolated RealmEngine transaction fixtures. The large-stack fixture uses a copied catalog with a 999-cap copper ore to exercise 150-item transactions. Production item stack limits are unchanged. Native UI input is generated through Godot, not a physical Windows keyboard or human playthrough.

## Retained failure history

Run `34311441450` passed backend tests but failed the new native assertion that an unsubmitted quantity survives a snapshot. The original SpinBox updated its text from committed values.

Run `34313085984` still failed the native typing assertion after the first bounds-preservation repair. The final source replaced merchant SpinBox expression behavior with explicit integer text entry. The quantity, signed-comparison, total-gold, ownership, replay and layout assertions were retained. New tests cover a smaller stack limit, focus loss, plus/minus controls and delayed snapshots. Test-created tooltip node trees are explicitly freed; leak diagnostics were not suppressed.

## Evidence files

Full artifact: `10089610859`, `player-experience-2559da7e9e22823c49e8a71de87c76f72cffaab7`.
Graphical artifact: `10089539410`, `visual-review-2559da7e9e22823c49e8a71de87c76f72cffaab7`.

Relevant paths inside the graphical artifact:

```text
engine/item-compare-1280.png
engine/item-compare-1920.png
engine/merchant-sell-1280.png
engine/merchant-sell-1920.png
engine/ui-inventory-1280.png
engine/ui-inventory-1920.png
```

Relevant full-workflow paths:

```text
revision.txt
logs/control-rules.log
logs/live-experience.log
screenshots/13-merchant-live.png
screenshots/14-merchant-after-sale.png
```

The sanitized preview object is `2bb5ef9853a0a23e90a8511866eaef36d6523016`. It is review evidence, not a runtime branch. Do not merge its root tree into main.

## Source and test files

```text
client/Scripts/ActionButton.cs
client/Scripts/CompactItemCard.cs
client/Scripts/EquipmentItemSlot.cs
client/Scripts/GameRoot.Inventory.cs
client/Scripts/GameRoot.ItemPresentation.cs
client/Scripts/GameRoot.Panels.cs
client/Scripts/MerchantSellPanel.cs
client/Tests/ControlRulesContract.cs
client/Tests/ItemCommerceUiChecks.cs
client/Tests/LiveExperienceContract.cs
client/Tests/LiveMerchantChecks.cs
client/Tests/VisualPresentationContract.cs
src/Kairnfall.Core/EquipmentComparison.cs
src/Kairnfall.Core/MerchantSales.cs
src/Kairnfall.Core/RealmEconomy.cs
tools/world_probe/ItemCommerceChecks.cs
tools/world_probe/Program.cs
```

## Acceptance states

Requested item/merchant functionality: implemented and automatically tested.
Native interaction and live authoritative sale/reconnect: tested.
Supported-resolution screenshots: rendered and native layout assertions passed.
Independent image inspection in this continuation: not completed. Local container and Python execution timed out; the public image fetch returned no image.
Independent coding-agent review: not run. The available Zeiko actions support customer-support agents, not coding-team execution. CI jobs are not counted as independent agents.
Physical Windows input, 125%/150% DPI, human usability and balance playtests, audio listening, sustained multiplayer load, measured hardware performance and extracted Windows packages: remain open.
Whole-game release acceptance: not passed. No release or tag was created.

Fetch live main before further work. Preserve saved state and use the same updated catalog in the client and server. The next local review should inspect the compact cards and sell a normal stack through each visible sale action.
