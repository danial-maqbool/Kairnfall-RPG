# Task 19 — Gathering, Crafting, and Profession Depth

Task 19 increases profession reasons to revisit existing geography without adding overworld regions or enlarging any zone.

Four scarce regional resources are attached to existing surface regions: Ancient Heartwood in The Old Boughs, Ghost Reed in Mosswater Basin, Moonfin in The Gull Isles, and Frostsilver in Glassmere. Each source uses the established deterministic resource-node seeder, creating three shared nodes in one region, with controlled 6–10 minute recovery windows.

Each material has a gather → process → specialty-tool loop. Processing uses existing crafting professions and stations, while the finished tools improve gathering efficiency/yield within the existing `ToolRules` caps. Tool selection now chooses the strongest usable utility rather than assuming requirement alone equals quality, allowing a regional specialty to matter until later masterwork tools overtake it.

Recipe progression remains server-authoritative through the existing skill, material, station, cooldown, sequence, and request-receipt gates. No client-only recipe authority or second unlock counter is introduced. The existing searchable crafting journal automatically exposes the new routes, their ingredients, profession requirements, stations, and regional-source descriptions.

Economy safeguards are unchanged: commands are receipt-idempotent, failed operations roll back authoritative state, ingredient quantities are checked before consumption, outputs are bounded, and the new processing/tool recipes do not create base item value. Rare-node recovery state persists through realm restart.

Automated coverage verifies unchanged world footprint, sparse deterministic node seeding, gather/recovery/restart behavior, shared-node contention, exact recipe consumption/output, replay safety, failure rollback, bounded tool utility, later-tier replacement, and generated catalog counts.
