# Equipment progression checkpoint — 2026-09-09

## Integrated source

Baseline: `645f81557aaf4787016c5807f3a25c06a380e671`.
Equipment/crafting integration: `b9dadef30bfd5747ff8a44c85c534bf22852dae7`.
Workstation-access integration: `4c560ccadf6a43ab4d0601844a8e200190795bd9`.

These commits contain actual implementation files. They preserve intervening main changes and the tested candidate histories. Ref updates used `force: false`. No branch, pull request, history rewrite, save reset, deployment, release or tag was created.

## Implemented

[Equipment progression](../EQUIPMENT_PROGRESSION.md) defines 21 named matching-skill tiers through level 100. All requested levels are included. Overall player level is not a second equipment gate.

Each grade contains 51 families: 15 weapons, 21 armor combinations, four offhands, four accessories and seven working tools. There are 1,071 tracked entries. The extension adds 824 item templates and 823 recipes. All original 530 templates and 463 recipes remain unchanged. Totals are 1,354 item templates and 1,286 recipes.

Every tracked item has a crafting route. Supply tests traverse actual resources, stock, drops, rewards and recipes. They reject cycles, inaccessible skill dependencies and unused new materials. Tin is sold by existing miners and blacksmiths. No new mine, creature, class, skill, quest or resource spawn is advertised.

Inventory opens the Upgrade guide. It shows all grades for a selected family, actual statistics, requirements, ingredients and vendors. The pinned action opens the selected recipe. Crafting shows at most 32 recipe rows per page. It includes search, profession filters, stable selection, owned ingredient counts, batch controls and a pinned action. The client requests actions; it never consumes ingredients or grants output.

The server selects eligible backpack tools. Broken, banked, locked and wrong-skill tools do not qualify. Bonuses do not stack. Maximum gathering stamina reduction is 15%; tool yield chance is capped at 20%. Smithing hammers affect smithing recovery only. The original farming/herbalism-sickle interaction remains valid.

The workstation repair requires clear approaches on client and server. NPC and owned stations behind walls or solid furniture cannot grant crafting access. Rejection preserves materials, sequence, cooldown and rewards. Another player's station remains unavailable.

Artwork retains 32-pixel icons, 64-pixel equipment frames and shared body anchors. Added original source provides alloy highlights, fabric folds, hide shapes, stitching and graded fittings. No external asset license was added.

## Exact verification

Equipment candidate `f73d9ec0c9a677d8440e08748f6cc7af59fe103f` passed [full run 34269781746](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34269781746) and [graphical run 34269781725](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34269781725).

Final workstation candidate `68956e42229c609e65071940a1b68f83dfb16a9c` includes that equipment source. It passed [full run 34270827868](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34270827868), verify job `102211736364`. Diagnostic job `102214258472` records the exact SHA. [Graphical run 34270827850](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34270827850) also passed.

| Suite | Result |
| --- | --- |
| Solution and client builds | Passed; client zero warnings/errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session/status security probes | 5 passed |
| Network/PostgreSQL / save conflicts | 18 / 5 passed |
| World paths | 107 zones, 1,013 destinations; zero failures |
| Save migration / furnishings | 5 / 7 groups passed |
| Equipment progression | 11 groups passed |
| Equip boundaries | 924 cases passed |
| Authoritative crafting paths | 1,071 passed |
| Workstation access | 2 groups passed |
| Python handoff | 107 tests passed |
| Native signals and input routing | Passed |
| Native player experience / control checks | 51 / 871 passed |
| Live Godot/server/PostgreSQL | 83 checks passed |
| Authenticated graphical smoke | Passed |

The equipment visual contract passed 179 native checks. Asset construction passed 54,997 assertions. These numbers do not grant independent visual approval.

Crafting paths use `RealmEngine.Execute` in isolated fixtures. They are not human playthroughs. The separate network suite exercises real HTTP/WebSocket and PostgreSQL behavior. Native input tests use generated Godot input, not a Windows physical keyboard. Existing thresholds and coverage were not reduced.

## Source and test files

```text
client/Scripts/CraftingGuidePanel.cs
client/Scripts/EquipmentGuidePanel.cs
client/Scripts/GameRoot.EquipmentGuide.cs
client/Scripts/GameRoot.Inventory.cs
client/Scripts/GameRoot.Panels.cs
client/Tests/ControlRulesContract.cs
client/Tests/CraftingGuideChecks.cs
client/Tests/EquipmentGuideChecks.cs
client/Tests/EquipmentTierGallery.cs
client/Tests/VisualPresentationContract.cs
content_src/gear_progression.py
src/Kairnfall.Core/Catalog.cs
src/Kairnfall.Core/EquipmentProgression.cs
src/Kairnfall.Core/Mechanics.cs
src/Kairnfall.Core/RealmEconomy.cs
src/Kairnfall.Core/RealmEngine.cs
tests/handoff/test_equipment_progression.py
tools/art/bow_pose.py
tools/art/gear_finish.py
tools/art/humanoid.py
tools/art/items.py
tools/build_content.py
tools/review_visual_art.py
tools/world_probe/CraftStationChecks.cs
tools/world_probe/GearProgressionChecks.cs
tools/world_probe/Program.cs
```

Documentation and `.ci` requests are additional. No local credentials, database files, editor cache or Docker state was committed.

## Evidence and remaining gates

Artifact `10073525152`, `visual-review-f73d9ec0c9a677d8440e08748f6cc7af59fe103f`, belongs to graphical run `34269781725`. It contains before/after source sheets and native captures. Paths include:

```text
after/equipment-tier-005.png
after/equipment-tier-027.png
after/equipment-tier-055.png
after/equipment-tier-100.png
after/equipment-grade-005.png
after/equipment-grade-075.png
engine/equipment-tier-5-1280-state-0.png
engine/equipment-tier-100-1920-state-2.png
engine/ui-equipment-guide-1280.png
engine/ui-equipment-guide-1920.png
engine/ui-crafting-1280.png
engine/ui-crafting-1920.png
```

Every grade has a source contact sheet. Native galleries render all 15 weapon families with complete armor at representative levels 5, 27, 55, 75 and 100, at 1280 by 720 and 1920 by 1080.

Implemented and automatically tested: equipment coverage, crafting authority, tools and native guide/crafting controls.
Graphically rendered: equipment and interface fixtures.
Independent PNG inspection in this chat: NOT COMPLETED. Container execution returned `ClientError`; binary fetch did not provide a usable image view.
All new gear artwork and equipped animations: NOT VISUALLY APPROVED.
Ordinary-account playtesting, Windows 125%/150% scaling and physical-keyboard review: NOT RUN for this extension.
Long-term economy pacing, full class balance, two simultaneous graphical clients, audio listening, sustained load, measured performance and extracted Windows packages: NOT ACCEPTED.
Whole-game acceptance: NOT PASSED. No release package or tag was produced.

## Safe continuation

Fetch current main before editing. Do not restore an older candidate or remove valid saves. Rebuild artwork and content, then restart client and server together with the same catalog. Preserve `.local`, `.tools`, `.venv`, credentials, verified partial downloads and Docker volumes.

Next inspect all new grade sheets and representative equipped animations. Complete an ordinary-account upgrade/crafting journey. Measure material acquisition time and review the first useful upgrade before changing economy balance. Preserve all security, native input and save regressions.
