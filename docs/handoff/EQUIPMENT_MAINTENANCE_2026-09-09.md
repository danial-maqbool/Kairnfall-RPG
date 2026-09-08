# Equipment maintenance checkpoint — 2026-09-09

This source integration retains the completed 21-grade equipment expansion and the paged upgrade/crafting browsers. It adds tested tool maintenance and precise skill errors. It is not a release or whole-game acceptance record.

## Exact tested source

Baseline with integrated equipment and documentation: `13cea4201bbc181c2a93d8b7db2cab56f94bfa9e`.
Maintenance candidate: `f4ca6d09f5075651f8b555adc8adab50a16d54bd`.
Full verification run: `34273676276`, verify job `102221359177`, SUCCESS.
Diagnostics: job `102223422802`.
Separate graphical workflow: `34273676520`, render job `102221310055`, SUCCESS.

The integration copies the exact seven changed source/test/guide files from that candidate onto current main. This record is the only additional file. Main history and intervening request commits are retained. No branch, pull request, force push, save deletion, credential change or deployment is required.

## Repairs

- Damaged or broken backpack tools can use the existing blacksmith repair transaction.
- The server retains the existing repair price formula. Repair changes durability only; identity, rarity and bonuses remain intact.
- Replayed repair requests do not charge twice.
- The server rejects banked items, foreign items, undamaged items, consumables, insufficient gold, dead owners and remote blacksmith use without changing the transaction state.
- Inventory descriptions show tool durability. The repair button appears for damaged tools and remains disabled away from a blacksmith.
- Gathering and crafting failures name the exact required skill and level.
- Existing item definitions, recipes, tier requirements, tool benefits and combat balance do not change in this maintenance pass.

## Tests read from completed logs

| Suite | Result |
| --- | --- |
| Client build | PASS; zero warnings and errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session and status-security probes | 5 passed |
| Real-network/PostgreSQL integration | 18 passed |
| Save-conflict checks | 5 passed |
| Grade progression | 11 groups; 924 equip boundaries; 1,071 authoritative crafting paths; zero failures |
| Workstation access | 2 groups passed |
| Equipment maintenance | 5 groups; all 147 tier tools repaired and replay-checked; zero failures |
| Python handoff tests | 107 passed |
| Native signal lifetime and pointer/key routing | PASS |
| Native player-experience checks | 51 passed |
| Native control/layout checks | 881 passed, including 10 new inventory-maintenance checks |
| Live Godot/server/PostgreSQL checks | 83 passed |
| Authenticated graphical smoke | PASS |
| Separate graphical fixture workflow | PASS |

The maintenance checks run the actual RealmEngine repair/gather/craft transaction path with disposable state. The inventory checks instantiate native Godot controls at 1280x720 and 1920x1080. These are not physical Windows mouse/keyboard tests.

All retained test stages passed. No assertions were removed or reduced. The Linux virtual display emits its existing V-Sync/cursor diagnostics; a successful build does not mean the complete graphical log is warning-free.

## Evidence

The full workflow retained artifact `10075060001`, named `player-experience-f4ca6d09f5075651f8b555adc8adab50a16d54bd`. Its archive SHA-256 is `166d9fed9a90af7e66936475cbb500bde82dce8d08b2b22254e31619f19c155f`. This is a test-evidence archive, not an application package.

The graphical workflow stores source contact sheets and native engine captures in its `visual-review-f4ca6d09f5075651f8b555adc8adab50a16d54bd` artifact. The earlier grade handoff lists representative equipment-grade, upgrade-guide and crafting capture names.

## Remaining acceptance gates

Implemented: YES. Automatically tested: YES. Graphically rendered: YES.
Independent image inspection in this chat runtime: NOT COMPLETED. Attempts to retrieve a review PNG did not produce a readable local image.
Full manual Windows playthrough, 125%/150% DPI, audio listening, sustained multiplayer/load measurements, RTX 4060 frame-time measurement and extracted Windows-package tests: NOT APPROVED.
Visual acceptance: NOT PASSED. Whole-game acceptance: NOT PASSED.
No release package, tag, code-signing result or package checksum was produced.

## Next continuation

Fetch live main. Read `EQUIPMENT_PROGRESSION_2026-09-09.md` and this record. Do not restore an earlier equipment candidate over these integrated files. Prioritize independent in-engine inspection of the new grades and the normal-account acquisition/crafting/equip journey. Keep the published tool maintenance, workstation guards and existing security/persistence/input regressions.
