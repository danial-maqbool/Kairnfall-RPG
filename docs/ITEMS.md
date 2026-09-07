# Item and rune audit contract

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
