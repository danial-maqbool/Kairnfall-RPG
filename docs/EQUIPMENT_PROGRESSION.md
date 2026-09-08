# Equipment progression

## Level rule

Equipment tiers use the item's named skill, not overall player level. For example, a Bronze Arming Sword requires Swordsmanship 5. Crafting that sword requires its separate crafting skill and a usable forge. The existing skill cap remains 100.

Material grade does not replace rarity, affixes, durability, runes, or sockets. Compare the actual item statistics. An unusually strong lower-grade item can remain useful. Existing weapon ranges, base attack recovery, and two-handed compatibility rules remain unchanged.

## Complete grade table

Each row covers 51 equipment families. The additional level 1, 25, and 40 rows preserve the existing progression landmarks.

| Required skill level | Metal grade | Light-armor textile | Medium-armor material |
| --- | --- | --- | --- |
| 1 | Copper | Linen | Tanned Leather |
| 5 | Bronze | Hempweave | Waxhide |
| 10 | Iron | Wool | Boiled Leather |
| 15 | Tempered Iron | Ridgeweave | Hardened Hide |
| 20 | Blackiron | Duskcloth | Studded Leather |
| 25 | Steel | Silk | Reinforced Leather |
| 27 | Tempered Steel | Satinweave | Brigand Leather |
| 35 | Dawnsteel | Sunweave | Sunhide |
| 40 | Silver | Moonweave | Wyvern Hide |
| 45 | Moonsteel | Mistweave | Moonhide |
| 50 | Runesteel | Runeweave | Runebound Leather |
| 55 | Cobalt | Blueweave | Stormhide |
| 60 | Froststeel | Frostweave | Frosthide |
| 65 | Stormsteel | Stormweave | Tempest Hide |
| 70 | Mithril | Starweave | Moonbound Leather |
| 75 | Starforged Mithril | Astralweave | Starhide |
| 80 | Adamantite | Duskweave | Wyrmhide |
| 85 | Obsidian | Ashweave | Emberhide |
| 90 | Dragonsteel | Dragonweave | Drakeguard Leather |
| 95 | Celestium | Celestial Weave | Celestial Hide |
| 100 | Aetherium | Aetherweave | Starguard Leather |

The table describes the complete upgrade tracks. It does not rename existing saved equipment. Older alternative armor sets remain available at their original requirements and under their original IDs.

## Families in each grade

- Weapons: sword, greatsword, axe, greataxe, mace, greatmace, spear, halberd, dagger, bow, crossbow, staff, wand, tome, and knuckles.
- Armor: helmet, chest, gloves, legs, boots, belt, and cloak in light, medium, and heavy construction.
- Offhands: shield, spell focus, quiver, and orb. Accessories: ring, necklace, charm, and trinket.
- Working tools: pickaxe, woodcutting axe, fishing rod, harvest sickle, excavation shovel, skinning knife, and crafting hammer.

Light armor uses names such as Hood, Robe, Handwraps, and Mantle. Medium armor uses Coif, Jerkin, Bracers, and Travel Cloak. Heavy armor uses Plate Helm, Plate Cuirass, Gauntlets, Greaves, Sabatons, War Belt, and Chainmantle. Existing sets keep their original names.

The catalog has 1,071 entries across these tracks. The extension adds 824 templates, including materials, to the original 530. The resulting catalog contains 1,354 item templates and 1,286 recipes. These counts establish coverage, not visual or whole-game acceptance.

## Find and craft an upgrade

1. Open Inventory with I. Select **Upgrade guide**.
2. Select a category and family. Select a level to inspect its actual item.
3. Check the named skill requirement, statistics, recipe, owned ingredients, and merchant locations.
4. Select **Inspect crafting recipe**. The crafting window opens the selected recipe.
5. Obtain its ingredients. Approach the required workstation with a clear line of sight.
6. Select the batch count and select **Craft**. The server validates the request before consuming ingredients or producing an item.

The crafting browser displays at most 32 recipe buttons per page. Search also checks ingredient names and workstation names. Profession and learned-skill filters reduce the results. The ingredient inspector and Craft action remain separate from the scrolling recipe list. Selecting a recipe or receiving an inventory update does not destroy the pressed recipe button.

Equipped items do not count as consumable crafting ingredients. A missing skill, material, station, connection, or available crafting action produces a specific blocked state. A successful crafting request still depends on server checks, including ownership, inventory capacity, and action sequence.

## Material supply chains

Every tracked equipment item has a recipe. Supply-chain tests start from actual resource outputs, merchant stock, creature drops, and quest rewards. They then traverse the recipes. The new recipes have no circular dependency or ingredient whose requirement exceeds its recipe requirement.

Tin ore is sold by existing miners and blacksmiths. Three tin ore produce one tin ingot. Two copper ingots and one tin ingot produce three bronze ingots. The extension does not invent an unseeded tin mine.

Later alloys refine existing obtainable metals with coal and, at higher grades, rune dust and polished gems. New textiles use existing cloth, thread, and rune dust. Treated hides use cured leather, thread, and rune dust. Every added raw material has a real recipe use. These are fantasy material grades; their recipe names do not promise a new creature species or a dedicated resource zone.

Existing merchants receive bounded, role-specific additions. The upgrade guide lists merchants that actually stock the selected item. Where there is no retailer, it shows crafting and player trade. It does not advertise a guaranteed creature drop that does not exist.

## Working tools

Keep a tool in the backpack. Tools do not occupy an armor or weapon slot. The server chooses the highest-grade usable tool for the requested action. It excludes banked, broken, unlearned, and wrong-skill tools. Carrying multiple tools does not stack their benefits.

The inventory shows tool durability. A damaged or broken backpack tool can use the same blacksmith repair action as wearable equipment. Repair restores durability and retains the item's identity, rarity, and bonuses. The server checks ownership, distance, health and gold before charging. Banked tools must be withdrawn first. Undamaged tools and consumables cannot use repair.

Gathering tools add a chance of one extra item, up to 20% at skill tier 100. Their stamina-cost reduction reaches 15%, reducing the ordinary six-point cost to 5.1. The existing combined gathering-yield cap remains in force. Gathering cooldown and server action validation do not change.

Crafting hammers reduce smithing action recovery by up to 15%. They do not reduce the crafting skill requirement, remove ingredients, or accelerate unrelated professions. The original farming interaction still accepts the original herbalism sickle.

## Artwork and equipment presentation

The added icons retain 32 by 32 canvases. Equipped layers retain 64 by 64 frames, the shared body anchors, four directions, six action states, and eight frames per row. The source uses alloy highlights, textile folds, hide contours, stitching, blade details, and graded fittings. Nearest-neighbor scaling and the existing side-bow hand anchors remain in place.

Source review sheets cover every grade. Native Godot fixtures cover representative complete weapon and armor sets at levels 5, 27, 55, 75, and 100. Automated image construction and successful rendering do not constitute independent visual approval.

## Compatibility and verification

The extension preserves all original item definitions and recipes. It does not rename saved templates, reset characters, change the save schema, add classes, or alter world geometry. Existing progression, trade-consent, session-expiry, item-ownership, and save-migration checks remain in the test matrix.

The new tests exercise 924 equip boundaries, 1,071 authoritative crafting paths, supply-chain reachability, deterministic generation, tool eligibility, stat bounds, serialization, native guide input, and pinned crafting controls. Workstation tests reject both an NPC forge and an owned workbench behind solid furniture without consuming materials, sequence, or rewards.

See [the equipment checkpoint](handoff/EQUIPMENT_PROGRESSION_2026-09-09.md) for exact revisions and test evidence. Full manual playtesting, independent image review, Windows display scaling, sustained load, audio listening, performance targets, and package acceptance remain separate.
