# Hunting, movement and native-pixel presentation

## Controls

| Input | Action |
| --- | --- |
| WASD or arrow keys | Walk |
| Q | Dash in the movement direction, or in the facing direction when stationary |
| Tab | Select the next eligible nearby creature |
| Shift+Tab | Select the previous eligible nearby creature |
| Space | Basic attack; hold to repeat at the allowed cadence |
| H | Open the regional Hunting guide |
| I | Open the shared backpack |
| Mouse wheel | Change world zoom between 1x, 2x and 3x |

The Settings page supports key reassignment. Typing, menus, focus loss, death and a disconnected session suppress gameplay input. Target cycling does not attack by itself. It includes deliberately hunted neutral wildlife, but excludes dead creatures, companions, other regions and blocked lines of sight.

Dash travels at most 2.5 tiles. Each accepted dash costs 4 mana and has a 0.65-second cooldown. Repeated use can exhaust mana despite ordinary regeneration. The server validates direction, collision, status effects, available mana and action sequence. Root, stun and silence prevent dashing. A fully blocked dash does not consume mana. Dash does not grant invulnerability. Replaying an acknowledged request does not repeat movement or charge mana twice.

## Actual hunting populations

The multiplier applies to each ordinary species' original one-creature spawn baseline. These are authoritative spawn slots, not decorative copies or enlarged minimap dots.

| Suggested region level | Ordinary spawn multiplier |
| --- | ---: |
| 0-20 | 30x |
| 21-40 | 20x |
| 41-60 | 15x |
| 61-80 | 10x |
| 81 and above | 5x |

A region with five ordinary species at level 10 has 150 ordinary slots. Bosses and elites use separate single slots. Killing or taming creatures can reduce the living population until a slot becomes available again.

The layout separates each species into several patches of up to five creatures. Every initial position is reachable from the regional arrival point and is separated from other initial positions. Narrow underground areas may use closer patch centers, but they retain the same actor separation and reachability checks. The builder fails rather than silently dropping requested population when it cannot place a valid slot.

Interiors remain safe. Village and city service cores, NPC work positions, doors and arrival points remain protected. Previously empty settlements gain suitable wildlife outside their protected core. The system does not fill inns or shops with hostile packs.

The generated world currently contains 109 regions and 4,682 initial creatures, including separate boss and elite instances. This is a seeded-world census, not a promise that every creature remains visible or alive simultaneously.

## Hunting patches and specialties

The Hunting guide displays terrain, patch locations, regional exits and actual boss locations. Select a site to read its species, level, movement pattern, possible loot and direction from the player. The guide does not expose undiscovered hidden caches, private loot or other players.

Biome specialties include meadow herds, field-pest colonies, woodland dens, web ambush sites, ridge patrols, shore groups, ice predators, fungal colonies and rift sentries. A creature's existing AI determines whether its patch uses grazing, pack, patrol, ambush, colony or territorial behavior.

Patrol creatures follow bounded routes with pauses. Grazing and wandering creatures retain individual decision timing. Pack assistance stays within its hunting patch rather than pulling all matching creatures across the region. Local separation and collision checks reduce stacking. Remote motion still uses the existing client interpolation.

Ordinary hunting slots wait while a living player is within seven tiles of the home position. Field bosses use a twelve-tile exclusion. A clear slot can respawn after its authoritative timer expires. This prevents a fresh creature from appearing directly under a camping player.

## Boss domains, dungeons and underground routes

Wilderness regions have a reachable field-boss domain away from the arrival point. The planner selects an appropriate existing boss definition by biome and level. It does not multiply boss populations by the ordinary mob multiplier or invent a new boss reward table.

Two additional connected beginner routes use existing creature, boss and reward systems:

| Dungeon | Suggested region level | Entry | Layer | Boss |
| --- | ---: | --- | --- | --- |
| Wayfarer's Burrows | 5 | Stairs outside the village service core | Deepways | Millbreaker |
| Silkroot Den | 15 | Stairs in Thistle Woods | Umbral Depths | Mother of Silk |

Silkroot Den also connects to the Dawnreach Deepway. Every new transition has a reciprocal exit. Travel remains server-validated. Existing capital interiors, dungeon bosses and the four world layers remain intact.

Ordinary dungeon rosters exclude creatures more than eight levels above the region's suggested level. This removes cases such as a level-65 guardian in a beginner cellar. The migration retires obsolete wild spawn slots but preserves captured animals, boss state and player saves.

Special loot sites reuse existing guarded hidden caches. No extra chest is added for every hunting patch. The ordinary loot-ownership window, reward validation and chest cooldown remain unchanged. Potential drops shown in the guide are not guaranteed drops.

## Easier early equipment and overall progression

Material grade, crafting level, equipment use level and overall player level remain separate concepts.

| Original equipment grade | Matching skill needed to use it |
| --- | ---: |
| 1 | 1 |
| 5 | 3 |
| 10 | 6 |
| 15 | 10 |
| 20 and above | Original requirement |

The rule also handles intermediate requirements. It never raises an item's original requirement. It does not lower a raw material's requirement or rewrite an item's grade, recipe, saved identifier or instance statistics.

Overall progression uses a smooth early-growth bonus. For nonnegative total earned skill XP `x`, the equivalent value used for overall level is:

```text
x + 50*x / (1 + x/250000)
```

The extra slope decreases as earned XP increases. Raw saved skill XP and individual skill levels do not change. Existing characters do not lose an overall level. An automated boundary test verifies that 10,000 total earned skill XP reaches at least overall level 20. This is not a measured human completion time or a full class-balance approval.

## One backpack, separate views

Inventory groups items into Equipped, Ready to equip, Locked or unavailable, and Tools and supplies. The Ready group uses the same current requirements and compatibility rules as the equipment inspector.

All groups use the same backpack and its existing 64-slot capacity. Filtering does not create extra bags, move items, alter ownership or add capacity. Tools remain backpack tools rather than equipment-slot items. Bank storage remains a separate existing system.

## Finer presentation and Atelier integration

The default world view uses 1x native pixels. The previous 2x default enlarged each source pixel. Players can select 1x, 2x or 3x in Settings or with the mouse wheel. The new preference uses `display/native_world_zoom`; the historical zoom preference is retained rather than deleted.

The window no longer stretches the complete 1280-by-720 canvas when resized. At 1x, one 32-pixel world tile remains 32 physical viewport pixels. This changes the view, not tile coordinates, collision geometry, attack range or server movement. Interface text keeps its own readable font sizes. Inventory icons retain their native aspect ratio and do not magnify source pixels inside their slots.

The asset builder reads the original `atelier/Assets` library and integrates 2,982 matching assets: 1,354 item icons, 966 equipped layers, 60 body/hair sheets, 26 NPC sheets, 145 creature sheets, 132 ability icons, 164 buildings, 52 terrain tiles, 41 resources, 23 props, 14 chests and five structures. Fifteen incompatible or missing non-rig matches retain the existing generated fallback art.

The importer checks SHA-256 hashes, safe paths, RGBA data, nonempty frames, exact dimensions, animation order and the shared foot anchor. Body, hair, equipment and NPC layers switch as one complete rig cohort. A corrupt or incomplete cohort stops the build before replacement. The independent Atelier `gear` and `gear_worn` ladder does not replace the game catalog or saved equipment IDs.

The derived pack contains `atelier-integration.json` and Atelier credits. Integrity checks do not establish visual approval. Native Godot screenshots show the actual imported runtime art. Older `before` and `after` source-generator sheets remain historical comparisons and must not be presented as proof that the imported Atelier pack was visually approved.

## Updating an existing checkout

Stop the local client and server before rebuilding. Pull current `main` with a normal fast-forward update. Preserve local changes, credentials, `.local`, `.tools`, `.venv`, verified partial downloads and Docker volumes.

Run the existing bootstrap to rebuild content and derived art. Start the client and server from the same checkout. The automatic hunting migration preserves valid saved characters, captured creatures, killed-creature timers and item identities. Do not delete the database to enable the new population.

## Acceptance boundary

Read the latest dated hunting checkpoint in `docs/handoff` for exact source revisions, workflow results and remaining gates. Compilation, asset hashes, seed counts and automated input are not human visual approval. Windows display scaling, physical input, sustained multiplayer load, audio listening and release-package tests require separate evidence.
