# Economy test plan

## Equipment supply verification — 2026-09-09

[Equipment progression](EQUIPMENT_PROGRESSION.md) adds reachable alloys, textiles, hides and gear recipes. Tin ore is sold by existing miners and blacksmiths. New materials have actual recipe uses; tests reject circular dependencies and forward skill gates. Added output sell values remain below the minimum tested NPC purchase cost of their ingredients. This is not a full gold-per-hour or player-market balance approval. Workstation line of sight and ownership are enforced on the server. See the [checkpoint](handoff/EQUIPMENT_PROGRESSION_2026-09-09.md).

Accepted requirements R13-R14 define gathering, professions, shops, banks, auctions, and atomic trades.
Inspect `RealmEconomy.cs`, `RealmSocial.cs`, the transaction repair source, and authored recipes/prices/drop tables.

Verify buy/sell quantity, stock/restock, different merchant categories/regions, reputation,
Bartering, inventory capacity, equipped-item restrictions, bank transfer, listing/expiry,
seller proceeds, fees, private trade previews, and two-stage confirmation.

Reproduce stale consent through rune, durability, affix, ownership, quantity, and equipment changes.
Test replay, parallel purchase, disconnect, full inventory, negative/overflow values, and insufficient funds.
Assert total quantities and gold before/after each atomic operation, including failure.

Simulate gold/hour, expected drops, profession costs, repair/travel fees, and sale values.
Find crafting or vendor cycles with positive unbounded return. Check leveling efficiency and rare-reward frequency.
Use separate disposable accounts and databases. Never run these scenarios against personal saves.
A pass of transaction safety tests is not evidence of balanced prices or enjoyable progression.
