# Item and rune audit contract

## Named equipment progression — 2026-09-09

See [Equipment progression](EQUIPMENT_PROGRESSION.md) for 21 matching-skill tiers and all 51 families. The extension in `content_src/gear_progression.py` preserves the original 530 item definitions and 463 recipes. It adds obtainable supplies, exact equip requirements, working tools and a native Upgrade guide. Material grade remains separate from rarity, sockets and runes. [Verification](handoff/EQUIPMENT_PROGRESSION_2026-09-09.md) does not close the broader rune or artwork audit below.

Read accepted requirements R08-R09. Item definitions are authored in `content_src/items.py`.
The server source owns item instances, quantities, equipment rules, transactions, and stat application.
Generated catalog entries and art files are necessary but do not establish useful gameplay.

Verify each item family, equipment slot, stack limit, affix family, rarity, material,
level/skill requirement, durability, price, recipe, drop source, icon, and equipment overlay.
Test all seven rarity tiers with text/non-color cues and meaningful roll ranges.

For rune tiers I-V, verify acquisition, socket capacity, insertion/removal cost, stat/proc effect,
element behavior, stacking caps, ownership, saving, and trade-consent invalidation.
A description that promises a repeated cast, chill buildup, or conditional proc must have that actual effect.
Document and repair mismatches rather than relabeling them as tested.

The inherited PR #21 server code protects trade consent against offered-item changes and supports stack splitting.
Re-run security tests and graphical inventory/trade flows on the consolidated checkout.
Never patch item quantities directly to make a gameplay acceptance step appear successful.
