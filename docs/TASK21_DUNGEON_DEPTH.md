# Task 21 — compact dungeon depth

Task 21 deepens four established boss entrances without expanding the overworld. Each selected dungeon now routes through two reusable 64×64 encounter rooms before the unchanged canonical boss arena. The rooms provide ordinary pressure, an elite beat, and environmental landmarks while the original boss ID, quests, loot table, layer, and surface coordinates stay intact.

Selected demonstrations: Broken Mill, Silken Tollhouse, Sunken Foundry, and Glasswing Grotto. This spans early through late progression and proves the structured template can be applied to future dungeons without growing the overworld.

Boss lifecycle is also hardened: death, leash, and abandonment clear boss-owned summoned adds and telegraphs; abandonment/leash resets health, position, phase, attack step, threat, and statuses without generating loot. Normal death still creates exactly one server-authoritative loot pile and the existing request-receipt system prevents duplicate kill rewards.

The 20 established Surface wilderness regions and 2,048,000 Surface wilderness tiles are unchanged. No release, deployment, or publication authorization is implied.
