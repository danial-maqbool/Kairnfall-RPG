# Item comparison and merchant selling

## Compact item cards

Item inspection, equipment hover cards and merchant item previews use one compact presentation. The logical card width is 328 pixels. Names, requirements, statistics and notices use centered text on both axes. Icons and headings remain centered. Long descriptions start collapsed in the full inspector. Hover cards show up to ten stat rows and direct the player to the full inspector for any remaining rows. General button tooltips also use a compact centered text layout.

The card shows the item's actual rarity, statistics, durability and rune information. These are not generic template-only comparisons. A locked item still shows its comparison. Banked items can be compared before withdrawal.

## Stat comparison

Each stat has its own row: Stat, Item and Change. The Change column compares the inspected item with the currently equipped item in the same slot.

| Result | Color | Difference |
| --- | --- | --- |
| Better | Green | Signed numeric difference |
| Worse | Red | Signed numeric difference |
| Equal | Normal text color | 0 |
| No applicable comparison | Normal text color | Dash |

For example, vitality 1 compared with vitality 6 shows a red -5. An unchanged luck bonus retains its normal color and shows 0. Power includes the item rarity multiplier. Affixes and inserted rune bonuses are included. A stat missing from the inspected item still shows the loss of that equipped bonus.

A lower attack interval is better. Its difference can therefore be negative and green. Other item bonuses use higher-is-better comparisons. The card labels attack interval in seconds and weapon range in tiles. These are item-level differences, not a promise that every change produces the same difference in final character damage. Character skills and combat formulas still apply.

A two-handed weapon comparison includes any incompatible offhand that the server would remove. The card names that offhand and includes its lost bonuses. This prevents a new weapon from hiding the loss of shield armor. Comparing an item never changes the real character or grants equipment.

## Equipment blockers

Unmet equipment requirements appear in red. The current rules include the named skill requirement, dead character state, broken gear, banked gear that must first enter the backpack, and incompatible offhand equipment. The card can display several blockers at once.

The current equipment rules do not impose a separate class or overall-player-level gate. The interface does not invent either restriction. Future additional server rules must also be represented by the inspection contract. Material grade, rarity and matching-skill requirements remain separate concepts.

## Sell items

1. Approach a merchant and open the shop.
2. Select **Sell from backpack**.
3. Select the item in the backpack list.
4. Enter a whole quantity, or use the minus and plus controls.
5. Check the displayed unit price and total gold.
6. Select **Sell quantity**, or select **Sell all** to sell the entire selected stack.

Sell all affects only the selected stack. It does not sell every item in the backpack or other stacks of the same template. Both buttons stay outside the scrolling item-details area. The page also shows current gold and the shared backpack slot count.

The client and server use the same sale-price rule: unit price is the greater of 1 and the integer part of 30% of the template value. Total gold is unit price multiplied by the accepted quantity. This retains the existing sale-price model. Purchase prices, which also consider bartering and reputation, are a separate rule.

Unsubmitted quantity text and its caret survive ordinary snapshots. When a stack becomes too small for the typed amount, the selected-quantity sale is disabled. The field does not silently clamp or reinterpret invalid text. Empty text, zero, negative values, fractions, expressions and excessive quantities cannot become a sale. Sell all remains independent of invalid partial-quantity text when the selected stack is otherwise sellable.

The server rejects equipped, banked, foreign, unavailable, quest and zero-value items as applicable. It also validates merchant type, distance, line of sight, character health, actual stack size and the gold limit. Non-provisioner merchants accept only types they stock. Red text explains why a sale is unavailable.

Epic-or-higher items and items containing runes require confirmation. A successful command receipt does not immediately re-enable selling against an old displayed inventory. Both sale actions wait for the corresponding authoritative snapshot. Replayed commands cannot grant duplicate gold. The client never removes items or awards gold itself.

## Verification limits

The integrated source passed full retained backend/database tests, native quantity and comparison tests, graphical fixtures at 1280 by 720 and 1920 by 1080, and real-connection partial/full-stack sales followed by reconnect. See [the exact-source record](handoff/ITEM_COMMERCE_VERIFIED_2026-09-09.md).

Rendered fixtures and generated native input do not establish independent visual approval or physical Windows input/DPI acceptance. The whole game remains a development build, not an accepted Windows release.
