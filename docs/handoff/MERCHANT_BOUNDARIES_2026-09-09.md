# Compact item panels and protected merchant sales — 2026-09-09

## Published source

Implementation integration: `51b575323969da9c9b0fab5f3c23a7a5f0c4147e`.
Tested source: `b941ac221e3084772330b98d5b0cbc7e6302669c`.
Integration parent on main: `86ec7f509f9c9e640360263dac2b9b349ad5d2bb`.

The integration contains the actual source. Its only differences from the tested candidate are the two retained `.ci` request files. The candidate is also a parent of the integration. The ref update used `force: false`. No new branch, pull request, history rewrite, save reset or release was created. Earlier Foundry, Atelier, equipment, targeting, hunting, XP and security work is retained.

The base item-card and sale implementation was already integrated before this continuation. See [its original verification](ITEM_COMMERCE_VERIFIED_2026-09-09.md). This checkpoint completes the retained merchant-boundary and shutdown repairs instead of restarting that work.

## User-facing changes

The shared item card is 328 logical pixels wide. It centers labels horizontally and vertically. Icons and headings are centered. Long descriptions start collapsed. Hover cards show ten stat rows and link the remaining information to full inspection. The full inspector retains all applicable stat rows.

Each row independently compares the inspected item with equipped gear. Better values are green, worse values red, and equal values retain normal text. Numeric differences include their sign. A lower attack interval is an improvement and can be negative and green. Affixes, runes, lost bonuses and incompatible offhand removal contribute to the comparison. Locked items still show their stat differences.

Actual equipment blockers appear in red, including matching-skill requirements, death, broken gear, backpack ownership and offhand compatibility. The game has no separate class or overall-level equipment restriction to invent in the UI. Several existing blockers can appear together. Inspection never changes the authoritative character.

Merchant selling is reached through Shop > Sell from backpack. It has a persistent whole-number quantity field, explicit minus/plus controls, an exact total, and separate Sell quantity and Sell all buttons. Each pinned button now has its own centered row. Even large gold totals remain fully visible at the tested resolutions. Sell all acts on the selected stack only.

After a complete stack sale, the next item is not automatically armed under the same button. The player must select another item. Delayed snapshots cannot enable a second sale against old displayed quantities. Invalid text and the caret survive updates; the panel rejects an excessive amount rather than silently reducing it. Valuable items retain confirmation.

Equipped-item affixes, runes and durability can change without an ID change. The merchant comparison now refreshes for those changes while preserving the pending quantity and caret.

The real sale/reconnect test exposed a cancelled socket receive disposal race. The connection now accepts OperationCanceledException or ObjectDisposedException as shutdown only when that receiver's cancellation token is already cancelled. Active-session and protocol failures retain their error paths. Three additional real reconnect cycles test saved sale state.

## Final passing candidate workflows

- [Full verification 34322836260](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34322836260): passed. Verify job `102373218360`; diagnostic job `102376646574` identifies exact source `b941ac221e3084772330b98d5b0cbc7e6302669c`.
- [Graphical verification 34322836227](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34322836227): passed. Render job `102373177015`; preview diagnostics `102375314499`.

| Suite | Verified result |
| --- | --- |
| Client Debug build | Zero warnings and errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session and pending-status security | 5 passed |
| Real-network/PostgreSQL / save conflicts | 18 / 5 passed |
| Item commerce, including shutdown filter | 7 groups passed |
| Python handoff tests | 118 passed |
| Native signals and pointer/key routing | Passed |
| Native player-experience checks | 52 passed |
| Native control and layout checks | 1,140 passed |
| Live Godot/server/PostgreSQL checks | 116 passed |
| Native graphical presentation checks | 305 passed |
| Authenticated graphical smoke | Passed |

The complete retained workflow also runs the existing migration, world, equipment, crafting, maintenance, density and challenge checks. No assertion or timeout was reduced. Bulk and high-price cases use copied catalogs; they do not change production prices, stack capacity or the shared backpack limit.

Live coverage uses a normal account, ordinary server-validated movement to a village merchant, the real shop button, native quantity typing, both actual sale buttons and production GameConnection transactions. It verifies exact removed quantities and gold after reconnect. Three further reconnect cycles retain sale gold, equipment and earned XP. These are generated native inputs, not a human Windows playthrough.

## Files completed in this continuation

```text
client/Scripts/MerchantSellPanel.cs
client/Tests/ControlRulesContract.cs
client/Tests/ItemCommerceUiChecks.cs
client/Tests/LiveExperienceContract.cs
client/Tests/MerchantBoundaryUiChecks.cs
src/Kairnfall.Core/GameConnection.cs
tools/world_probe/ItemCommerceChecks.cs
```

The existing CompactItemCard, EquipmentComparison, MerchantSales and their inventory/shop integrations remain intact. Documentation and request metadata are additional to the seven implementation/test paths above.

## Evidence

Full-test artifact: `10092942130`, `player-experience-b941ac221e3084772330b98d5b0cbc7e6302669c`.
SHA-256: `e2d2b9e0d8b84d65402fdebd2fee66a5fd802b8e51af8e6b083a0102dcd19caf`.

Graphical artifact: `10092787696`, `visual-review-b941ac221e3084772330b98d5b0cbc7e6302669c`.
SHA-256: `8318cd931b013a62f4efc5c1985ce3c9b1fa9cdddc327b7634e4c50ee2473551`.

Representative fixture filenames include `item-compare-1280.png`, `item-compare-1920.png`, `merchant-sell-1280.png`, `merchant-sell-1920.png`, `merchant-large-totals-1280.png`, `merchant-large-totals-1920.png`, `merchant-fresh-comparison-1280.png` and `merchant-fresh-comparison-1920.png`. Live captures include `13-merchant-live.png` and `14-merchant-after-sale.png`. The archives retain logs alongside rendered evidence. They are not release packages.

## Retained failures and limits

Earlier native typing exposed SpinBox coercion; the integrated merchant uses an explicit integer LineEdit. The first large-total fixture set Text programmatically, which did not emit its native change event; the fixture now types through real input while retaining all expected values. Candidate `633b1f23673126c5c4ffad956704808ba2f2b9f7` exposed the socket shutdown race in full run `34318019455`. The subsequent full run `34319374625` timed out twice before producing control output. These attempts are not marked passed. The retained diagnostics flush native stages to an ignored local log, without changing assertions or time limits. Final run `34322836260` completed every stage.

The requested source changes are implemented, automatically tested, graphically rendered and integrated. Independent image inspection in this chat could not be completed: container and Python calls returned transport timeouts. Physical Windows keyboard/mouse, 125%/150% scaling, human visual approval and whole-game release acceptance remain separate. Existing virtual-display V-Sync/cursor and dependency deprecation warnings remain in logs; the zero-warning statement applies to compilation only.

## Safe local continuation

Close the client and local server, fetch current main without resetting local files, run bootstrap, and restart both from the same catalog. Preserve credentials, `.local`, `.tools` and Docker volumes. Use Inventory to inspect comparisons. Approach a merchant and select Sell from backpack to use the new sale controls. Do not restore an old unintegrated candidate over this checkpoint.
