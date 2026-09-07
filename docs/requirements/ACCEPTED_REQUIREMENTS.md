# Accepted Kairnfall requirements

## Source and interpretation

This document records the game requirements from the user's accepted master specification and later instructions.
It is a requirements baseline, not an implementation report. It does not reduce the target to a prototype.
The later real-object pixel-art instruction strengthens the visual requirement.
The latest instruction requests a source checkout, requirements, and a local-agent handoff for testing and repair.
It does not establish that the game or its artwork is already complete.

Use `docs/handoff/VERIFICATION.md` for observed evidence. Mark a requirement verified only after its actual acceptance check.
Examples below remain design references. A substitute must provide an equivalent mechanic, not remove the requirement.

## R01. Project and authority

- Game: Kairnfall. Repository: `danial-maqbool/Kairnfall-RPG`.
- Platform: Windows x64. Persistent online 2D top-down MMORPG.
- Client: Godot 4.7.2 .NET with C#. Server: authoritative .NET 10. Database: PostgreSQL.
- Medieval high fantasy with original identities, lore, maps, and artwork.
- Mystera Legacy and Mirage Realms are system/design references. Do not copy their protected code, maps, sprites, names, audio, or dialogue.
- MIT for original project source. External assets require permission for their actual redistribution and retain their licenses.
- The user authorizes branches, commits, pushes, PRs, tested merges, Actions, LFS where appropriate, dependency installation, and routine engineering decisions.
- Use existing authenticated connections. Never ask for credentials in chat or use a token exposed in the conversation.
- Do not change billing, deploy publicly, remove safeguards, or destroy unrelated files or saves under this authority.
- Do not force-push `main`. Preserve work from other contributors. Do not merge failing changes merely to remove open PRs.

## R02. Development teams and evidence

Workstreams: orchestration/integration; server/networking; client; world; classes/combat/skills;
items/crafting/economy; creatures/AI/bosses; NPCs/quests/lore; pixel art/animation/VFX;
UI; audio; test automation; adversarial review; visual review; performance/release.

Use actual specialist workers if a supported runtime is available. Assign file ownership and integration tests.
Limit concurrency to the host's resources. Work in waves when necessary. A named branch is not an independent agent.
A single agent can perform sequential reviews, but must not label them independent reviews.
Only the integration owner can accept the combined result after all completion gates pass.
Push cohesive changes throughout implementation. Record commands, exit codes, commit IDs, and evidence.
Keep failed, blocked, and unrun checks visible. Documentation and catalog counts do not replace implementation.

## R03. Account and character flow

Title -> connection -> registration/login -> character selection -> character creation -> world entry.
Provide validated names, body choice, skin tones, hair styles/colors, class selection, and an animated appearance preview.
Persist characters. Handle authentication failure, expired sessions, disconnect, reconnect, and server-version mismatch without corrupting state.
Use secure password hashing. Never store plaintext account passwords.

## R04. Classes

| Class | Role and identity |
| --- | --- |
| Vanguard | Defensive melee; sword, shield, heavy armor, block and guard. |
| Berserker | Aggressive melee; two-handed axes/maces, rage, bleeding, risk/reward. |
| Ranger | Physical ranged; bows/crossbows, traps, mobility, tracking. |
| Rogue | Fast melee; daggers, critical strikes, poison, evasion, stealth. |
| Arcanist | Elemental caster; staves/wands, Arcane, Fire, Frost, Lightning. |
| Warden | Nature hybrid; roots, companions/summons, animal affinity, healing. |
| Templar | Melee support; Radiant, Restoration, maces, shields, auras. |
| Spellblade | Melee/magic hybrid; swords, magic enhancement, teleport strikes, elements. |

Each class needs a stat profile, meaningful passive, signature abilities, class quests, equipment affinity,
visual identity, and progression rewards. Other skills remain trainable. Class identity must not become a blanket skill lock.

## R05. All 60 independent skills

| Category | Skills |
| --- | --- |
| Weapons (11) | Swordsmanship; Axe Mastery; Mace Mastery; Spear Mastery; Dagger Mastery; Archery; Crossbow Mastery; Staff Mastery; Wand Mastery; Shield Mastery; Unarmed Combat. |
| Magic (11) | Pyromancy; Cryomancy; Stormcalling; Geomancy; Nature Magic; Shadow Magic; Radiance; Arcane Magic; Restoration; Summoning; Runecasting. |
| Survival (10) | Light Armor; Medium Armor; Heavy Armor; Evasion; Endurance; Meditation; Hunting; Slayer; Survival; Exploration. |
| Gathering (10) | Mining; Woodcutting; Fishing; Farming; Foraging; Herbalism; Skinning; Excavation; Prospecting; Treasure Hunting. |
| Crafting (13) | Smithing; Woodworking; Fletching; Tailoring; Leatherworking; Cooking; Alchemy; Enchanting; Runecrafting; Jewelcrafting; Carpentry; Scribing; Tinkering. |
| Utility (5) | Lockpicking; Bartering; Cartography; Animal Handling; Construction. |

Each skill requires server-owned XP, levels, a curve, accessible training actions, meaningful effects,
unlock thresholds, visible feedback, a description, an icon, and persistence.
A skill record or a button that awards arbitrary XP is insufficient.

Overall player level derives from accumulated skill XP, not a separate combat-only progression bar.
Targets are approximately skill levels 1-100 and overall levels 1-200. Simulate early, middle, and late progression.
Test both specialists and generalists. Gatherers, crafters, explorers, and combat users must all progress.
Prevent repeatable trivial actions or failure cases from producing disproportionate XP.

## R06. Attributes, combat, and abilities

Attributes: Strength, Dexterity, Intellect, Vitality, Spirit, Resolve, Luck.
Derived values include health, mana, stamina, physical/spell power, armor, block, accuracy, evasion,
critical chance/damage, attack/cast/movement speed, regeneration, threat, healing, item/gold find, and cooldown reduction.
Use justified caps or diminishing returns. Explain displayed formulas and validate their effects.

Combat is real time. Provide melee/ranged attacks, projectiles, targeted spells, cones, lines, ground areas,
healing, buffs/debuffs, absorption, block/dodge, critical hits, armor/resistance, threat/aggro, cooldowns,
resource costs, crowd control, interrupt, appropriate knockback, damage-over-time, and healing-over-time.
Telegraph dangerous attacks clearly. Boss difficulty cannot consist only of more health.

Provide at least 120 meaningful player abilities. Each class needs offensive, defensive, utility, mobility,
signature, and ultimate abilities. Add weapon, magic, rune, item, and quest unlocks.
Mechanically identical attacks with changed percentages do not satisfy the diversity requirement.

## R07. Elements and statuses

Elements: Physical, Fire, Frost, Lightning, Nature, Poison, Arcane, Radiant, Shadow.
Give items and creatures appropriate bonuses, resistances, weaknesses, and rare justified immunities.
Statuses include Burn, Chill/Freeze buildup, Shock, Entangle, poison stacks, Arcane Vulnerability,
Blind/Purge, and Curse. Implement readable interactions, durations, stacking, immunity, and cleansing rules.
Test elemental outcomes in combat, not only enum or data coverage.

## R08. Items, equipment, and rarity

Weapons: one-/two-handed swords, axes/great axes, maces/great maces, spears, halberds, daggers,
bows, crossbows, staves, wands, tomes, fist weapons.
Offhands: shields, tomes, focuses, orbs, quivers.
Armor: helmet, chest, gloves, legs, boots, belt, cloak.
Accessories: rings, necklaces, charms, trinkets.
Tools: pickaxe, woodcutting axe, fishing rod, sickle, shovel, skinning knife, hammer.
Also provide food, potions, scrolls, runes, gems, ores, wood, herbs, animal materials,
crafting components, quest items, keys, treasure maps, and collectibles.

At least 450 authored item templates, including 100 weapons and 100 armor pieces.
Procedural affixes add combinations, not replacement template-count claims.
Use unique item-instance IDs, stack limits, ownership, equipment constraints, durability, and repair.
Equipment must visibly change the character through aligned modular sprite layers.

Rarities: Common, Uncommon, Rare, Epic, Legendary, Mythic, Relic.
Show rarity text and a shape/border/icon cue, not only color.
Rarity affects plausible stat ranges, affixes, sockets, special-effect chance, and value.
Item level, roll quality, and build suitability must still matter.
Use coherent prefixes/suffixes and item-specific affix families, not every stat on every item.
Include attribute, offense, defense, resources, regeneration, elemental, skill, gathering,
craft quality, item-find, and gold-find modifiers where mechanically supported.

## R09. Runes

Runes are collectible item instances, not only visual effects or labels.
Categories: Power, Protection, Elemental, Utility, Skill, Trigger, Rare Signature.
Tiers I-V. Equipment supports 0-4 sockets according to its type, rarity, and crafting result.
Provide stats, elemental effects/resistance, conditional triggers, skill changes, and bounded proc behavior.
Examples: Embers, Winter, Bulwark, Precision, Leeching, Echoes, Prospector, Wanderer.
Test acquisition, insertion, removal, ownership, stack rules, caps, costs, and active gameplay effects.
An item name promising a proc must not silently provide only an unrelated flat stat.

## R10. World geography

At least five major cities, ten smaller settlements, fifteen biomes, twenty major dungeons,
plus caves, mines, ruins, interiors, and secrets. Outdoor scale must exceed an equivalent 1,200 x 1,200 tiles.
Use region/chunk streaming, not one giant loaded scene. Large empty repeated fields are not sufficient.
Maintain a machine-readable topology and test routes, collision, transitions, and service accessibility.

| City | Location and required identity |
| --- | --- |
| Dawnreach | Plains starting capital; stone walls, markets, guilds, cathedral, training grounds, story/services. |
| Emberhold | Mountain/volcanic forge city; mining, smithing, gems, heavy gear, lower mine access. |
| Thornhollow | Ancient forest; living trees, timber bridges, nature shrines, wood/herbs/alchemy/companions. |
| Frostgate | Tundra/glacier fortress; northern clans, high-level hunting, rare ore, frost magic. |
| Gloamport | Coastal marsh harbor; ships, fog, markets, smuggling, fishing, trade, treasure, shadow quests. |

Every city needs a distinct layout, architecture, palette, named NPC population, shops, bank, inn,
crafting, quests, secrets, travel links, nearby dungeon, surrounding region, and appropriate music/ambience.

Biome coverage: plains, farmland, forest, ancient forest, pine forest, highlands, mountains,
volcanic land, tundra, glacier, wetlands, swamp, coast, archipelago, badlands, cursed wasteland,
crystal caverns, fungal underground, ancient ruins, arcane anomaly zones.
Each differs in terrain, plants, creatures, resources, light, ambience, and applicable weather.

## R11. Layers, connectivity, and start

Layers: Surface; Deepways with mines/caves/sewers/buried roads; Umbral Depths with late-game
ancient regions; Aether Rift with rare portal regions and end-game encounters/resources.
Use physical stairs, cave mouths, shafts, lifts, wells, portals, ruins, or hidden passages.
Do not replace connected travel with unrelated menu maps.

Verify routes between every major city, accessible spawn positions, reciprocal exits where intended,
connected dungeon floors, usable shortcuts, and clear destinations. Document intentional one-way links.
Graph connectivity alone is insufficient when tile collision blocks the actual route.

All new players start at Wayfarer's Rest, west of Dawnreach.
Teach movement, interaction, combat, loot, inventory, equipment, skill XP, gathering, crafting,
shops, maps, quests, death, and respawn through playable tasks rather than one text wall.
The route to Dawnreach must require normal exploration.

## R12. NPCs, narrative, quests, and reputation

At least 150 named NPCs. Provide merchants by trade, smiths/armorers/fletchers, bankers/auction brokers,
innkeepers, trainers, class representatives, guards, farmers, miners, fishers, scholars, priests,
ferrymen, stablemasters, travelers, caravans, storytellers, and criminal contacts as appropriate.
Important NPCs need a name, role, home region, dialogue, purpose, and practical schedules.

At least 25 main-story stages, 100 side quests, and 30 repeatable/dynamic quests.
Provide prerequisites, objectives, branching where useful, dialogue triggers, rewards, and persistence.
Vary kill, gather, craft, escort, exploration, puzzle, boss, delivery, and secret objectives.
Prevent impossible prerequisites, missing quest items, repeated rewards, and unrecoverable quest states.

Use city factions plus Wayfarers Guild, Arcane Collegium, and Shadow Covenant or equivalents.
Reputation must affect actual prices, quests, equipment, access, dialogue, or cosmetics.
Support lore books, journals, signs, rumors, discoveries, and environmental stories.

## R13. Gathering and cross-profession crafting

Provide distinct ore seams, timber species, waters/fish, crops/seeds/growth, wild materials,
medicinal herbs, skins/hides, excavation sites, gemstone prospecting, and treasure clues.
Nodes need visible forms, tools/level requirements, resource tables, respawn, and server-awarded XP.
Farming must include placement, growth, ownership rules, harvest, and persistence.

Recipes need stations, skill/ingredient requirements, quantities, suitable timing, XP,
quality, affix/socket chances, and rare outcomes. Validate all input/output references.
Professions must interact: ore -> metal; wood -> handles; hides -> grips; gems -> settings;
runes -> effects; final crafting -> useful equipped item.
Construction and Carpentry must produce usable, owned world structures with safe placement/removal.
Prevent negative counts, free output, item loss, infinite-profit conversion, and duplicate completion.

## R14. Economy and services

Merchants: buy/sell quantities, stock/restock, category and regional differences, reputation/Bartering,
clear prices, expensive-purchase confirmation, and equipment comparison.
Banks: persistent stacks and unique items, deposit/withdraw quantity, search, sorting, categories, deposit-all.
Auction house: listing, filters, quantity, price, fees, expiry, atomic purchase, seller proceeds, and offline handling.
Trade: invite, private offer preview, two-stage readiness/confirmation. Any offer-content change cancels prior consent.
Use atomic server transactions. Test races, replay, disconnect, capacity, invalid quantities, and insufficient funds.
Provide coherent gold sources/sinks and balance reports rather than unchecked catalog values.

## R15. Creatures, AI, and bosses

At least 100 distinct normal species, 25 rare/elite variants, and 20 named bosses.
Every normal species needs recognizable anatomy and its own gameplay identity.
Palette swaps, relabeled records, and exact duplicate artwork do not count as distinct species.
Each record needs level/region, stats, resistance/weakness, AI, attacks, animations, drops, XP, and respawn.

AI archetypes: passive, territorial, aggressive, pack hunter, ranged kiter, ambusher,
guard, patroller, caster, healer, summoner, berserker, fleeing creature, boss controller.
Use suitable navigation, spacing, ranges, cooldowns, leashes, and ally awareness.

Each boss requires an authored form, arena/context, multiple attacks, telegraphs,
phase logic where appropriate, special drops, lore, and discovery/achievement hooks.
Several bosses must use positioning, additional enemies, interrupts, or environmental mechanics.
Test boss death, reward, reset, leash, disconnect, and server-restart behavior.

## R16. Loot, secrets, and world events

Server decides loot: gold, equipment, materials, food, potions, runes, components, keys, maps, collectibles, cosmetics.
Use weighted tables, ownership rules, expiry, and clear rarity feedback.
Chests: Weathered, Locked, Ancient, Runic, Royal, Cursed, Mimic.
Mix fixed secrets with randomized finds in passages, ruins, puzzles, treasure maps, events, and wilderness.
Do not reveal every secret on the default map.

Provide optional discoveries such as breakable walls, hidden switches, suspicious floors, shrines,
buried treasure, wandering merchants, ghosts, weather creatures, lunar events, meteors,
secret bosses, mimic chests, portals, forgotten journals, cursed wells, riddles, bridges, and ambushes.

Dynamic events can include raids, caravan attacks, meteors, undead outbreaks, migrations,
arcane storms, pirate landings, frozen rifts, and world bosses.
Each event needs server state, start/resolve/expire conditions, cleanup, reward rules, and restart safety.

## R17. Social, death, and travel

Parties: invite/accept/leave/kick, leader, members, valid shared objectives, nearby XP, loot rules, party chat.
Guilds: creation/name, invites, roles/permissions, member list, persistent membership/message, guild chat.
Chat: local, global, party, guild, whisper, system; timestamps, names, channels, spam limits, ignore/mute.
Prevent private message or trade-data disclosure to outsiders.

Death: animation, safe respawn, balanced repair/durability or equivalent cost, death log, suitable recovery.
Do not arbitrarily destroy rare items by default.
Map/minimap: discovered regions, player/party, cities, known travel points, appropriate quest markers, optional custom markers.
Fast travel uses discovered ferries, carriages, waystones, or justified portals. Preserve meaningful early exploration.

## R18. Time, weather, immersion

Dawn/day/dusk/night. Biome-appropriate rain, fog, snow, storms, ash, and clear periods.
Time/weather must affect some spawning, fishing, gathering, or rare events without making combat unreadable.
Regions need paths, resource logic, encounters, historical/NPC context, variation, secrets, and landmarks.
Examples: towers, bridges, graves, shrines, waterfalls, farms, watch posts, statues, mines,
shipwrecks, battlefields, camps, caves, unusual trees, monoliths.
Measure density and travel experience. Do not pad world size with empty repeated tiles.

## R19. Detailed real-object pixel art

Native terrain tiles: 32 x 32 pixels. Player frames approximately 48-64 pixels.
Ordinary/large creatures approximately 64-96 pixels. Bosses may use 96-192 pixels with a consistent anchor.
The current pipeline uses 64-pixel actors and 128-pixel bosses, eight columns and 24 rows per sheet.
States: idle, walk, attack, cast, hit, death. Directions: south, west, east, north.
Use at least four genuine directions; add eight only when the quality and workload permit it.

Animals need recognizable anatomy: correct limb count, joints, feet, tails, ears, muzzles, fins,
wing membranes or feathers, shells, and species-appropriate proportions.
Humanoids need separate head/torso/arms/legs, readable clothing, equipment, highlights, and shadows.
Weapons need identifiable working heads/blades, guards, grips, fittings, and attachment points.
Buildings/chests need structural boards/stonework, roof planes, joinery, hinges, lids, locks, and consistent perspective.
Metal, wood, stone, skin, fur, cloth, leather, bone, and magical materials require distinct pixel clusters.

Create an art bible, proportions, palette, light direction, reference sheets, and frame/anchor rules.
Use original artwork or licensed reusable artwork with attribution. Inspect actual native frames and gameplay captures.
Reject monochrome blobs, generic circles/rectangles, silhouette-only figures, random noise, debug icons,
palette-only species, clipped bodies, jumping frames, muddy materials, and poor equipment alignment.
A one-pixel difference or distinct hash is not evidence of a meaningful silhouette difference.
Record review evidence separately from automated asset checks.

## R20. UI and controls

Finish HUD health/mana/stamina, target, hotbar, statuses, XP feedback, minimap, and chat.
Windows: Inventory, Equipment, Character, Skills, Classes, Abilities, Quest Log, World Map,
Bestiary, Achievements, Crafting, Bank, Auction House, Shop, Party, Guild, Trade, Settings.
Provide drag/drop, item comparison/tooltips, stack splitting, sorting/search, hotkeys, and useful notifications.
Style the UI. Default unstyled editor-like controls do not satisfy visual acceptance.
Test 1280x720, 1920x1080, larger displays, resizing, scaling, focus, text entry, and input rebinding.

Defaults: WASD/arrow movement, mouse target/interact/context, 1-0 hotbar, Tab target cycle,
I inventory, C character, K skills, J quests, M map, Enter chat, Esc menu.
Additional bindings must be documented and consistent. Text entry must not move or attack the character.

## R21. Audio

Provide menu, city, wilderness, dungeon, and boss music plus environmental ambience,
weapons/spells/creatures, footsteps, gathering, water/fire/wind, and UI feedback.
Use original or correctly licensed audio. Record sources, authors, licenses, and modifications.
Test audible playback, volume controls, clipping, loop boundaries, region changes, and repeated effects.
A valid WAV file is not an audio quality review.

## R22. Authority, persistence, and security

The client sends intentions only. Server validates position, speed, range, cooldown,
resources, inventory ownership/counts, prices, crafting, loot, runes, XP, quests, and trade state.
Use versioned messages, IDs, bounded serialization, rate limits, expiry, reconnect, validation, and clear errors.
Persist accounts, characters, appearance, position, inventory, bank, equipment, gold, skills,
quests, reputation, achievements, guilds, known travel points, and discovery.
Use unique item IDs and transactions for purchases, trades, banking, auction buys, crafting, loot, and rewards.

Adversarial tests must cover forged movement/damage/loot, malformed/null/oversized messages,
negative/overflow counts, unknown IDs, replay, duplicate rewards, transaction races, speed/teleport abuse,
logout/reconnect/session expiry, database conflicts, death/disconnect abuse, stale consent, and crashes.
Keep credentials, backups, private chats, tokens, local state, and build caches out of Git and public artifacts.

## R23. Performance and balance

Target at least 20 Hz authoritative simulation and 60 FPS client rendering on reported Windows hardware.
Use spatial indexing, visibility/interest management, streaming/culling, atlases, pooling where useful,
efficient navigation, and safe database batching. Measure before claiming performance.

Run real protocol bots for login, movement, combat, loot, zones, shops, crafting, trade, reconnect.
Target 100 simultaneous clients if hardware permits. Record actual sustained count and resource use.
Do not claim 100-player capacity from three connected test clients or in-memory calls.
Simulate time-to-kill, XP/hour, class damage/survival/healing, progression, gold sources/sinks,
crafting profit, shop prices, rare drops, and boss rewards. Fix dominant exploits.

## R24. Local delivery and completion

A fresh clone must include requirements, dependency setup, generated-content sources,
server/client launch commands, tests, and an explicit handoff.
Required entry points: bootstrap.ps1, Run-Kairnfall-Dev.ps1, Run-Kairnfall-Server.ps1, Run-Kairnfall-Client.ps1.
Do not depend on a chat attachment or expiring CI artifact to reconstruct necessary assets.
Use data-driven validated catalogs. Reject invalid IDs, missing references/icons, inaccessible unlocks,
recipe cycles, incomplete quests, and unsupported advertised effects.

Maintain ARCHITECTURE, WORLD_BIBLE, COMBAT, SKILLS, ITEMS, ECONOMY, NETWORKING,
ART_DIRECTION, CONTENT_MATRIX, QA_MATRIX, THIRD_PARTY_ASSETS, and FINAL_AUDIT documentation.
README needs accurate setup, controls, layout, status, licensing, and real screenshots when available.
Do not use concept art as a gameplay screenshot.

### Clean-database acceptance sequence

1. Create an account.
2. Create a character.
3. Spawn at Wayfarer's Rest.
4. Complete playable tutorial activities.
5. Train multiple different skills.
6. Equip an item and see its appearance.
7. Gather wood.
8. Mine ore.
9. Craft a useful item.
10. Fight a creature.
11. Receive and collect drops.
12. Acquire a rune through gameplay.
13. Insert the rune and verify its effect.
14. Travel normally to Dawnreach.
15. Buy and sell through a merchant.
16. Deposit and withdraw through a bank.
17. List and purchase through the auction house with another account.
18. Complete quests without developer reward injection.
19. Travel between connected regions and all five cities.
20. Enter and exit underground layers.
21. Defeat a boss using its actual encounter mechanics.
22. Create/join a party.
23. Complete a two-player trade.
24. Disconnect safely.
25. Reconnect with the same character.
26. Restart the server and verify persisted state, ownership, and quantities.

### Final acceptance gates

All required systems, content, geography, classes/skills, combat, equipment, elements/runes,
gathering/crafting, services/economy, quests, loot/bosses/secrets, UI, and social features must work.
Sprites must pass visual review. Audio must pass listening review. No core placeholder may remain.
Multiplayer, persistence, adversarial tests, balance, and performance must have recorded evidence.
Build a Windows client and server package. Test the extracted package from a clean directory.
Verify required DLLs/PCK/resources, paths with spaces, prerequisites, launchers, save/restart, and exit behavior.
Only then create a release/tag with packages, SHA-256 checksums, setup guide, screenshots, audit, and known limitations.
A source build, task document, generated catalog, asset file count, or smoke test alone is not full-game completion.
If an actual tool or runtime blocks a check, state the blocker and preserve the checkpoint. Do not fabricate completion.
