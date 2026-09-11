# Living world and public-event ecosystem

Kairnfall's public events are server-authoritative regional incidents layered onto the existing connected world. They are not separate instances and they reuse ordinary combat, gathering, treasure, movement, skill progression, party presence, and save persistence.

## Event families

Eight deterministic event families rotate through eligible regions:

- **Starfall Harvest** — gather fallen star fragments, then defeat a Starborn champion.
- **Wayfarer Caravan** — stay near the caravan to escort it, survive route ambushes, then break the final attack.
- **Restless Graves** — clear a graveborn wave, then destroy the Grave Herald.
- **Arcane Rift** — actively stabilize the rift, then defeat the Rift Sentinel.
- **Settlement Under Siege** — repel attackers and then their commander.
- **Wild Migration** — drive back a dangerous migration and its apex beast.
- **Treasure Surge** — recover temporary regional caches before the surge collapses.
- **Regional Terror** — a focused public world-boss encounter in higher-level wilderness.

Up to three active events can coexist. Placement respects region type and progression: settlement sieges use real settlements, higher-risk rifts and world bosses use later wilderness, and starter Wayfarer's Rest is never selected for a siege.

## Scaling, contribution, and rewards

Stage-zero objectives scale upward when multiple active players arrive together, up to a bounded six-player contribution target. Combat damage, event kills, event gathering, cache recovery, rift stabilization, and caravan escort presence are tracked server-side. Rewards are granted once to meaningful contributors and scale by contribution tier rather than last-hit ownership.

Successful contributors receive gold, Exploration and Survival training, Wayfarers reputation, and an existing themed material or consumable where available. Public-event milestones are recorded at the first completion and at 10 and 25 completions. Event reward state is serialized with the realm so reconnects or saves cannot duplicate payouts.

## Success, failure, and regional aftermath

An event that completes all of its stages leaves a temporary positive regional consequence. An event that misses its deadline leaves **Regional Unrest**. These effects alter real server rules rather than only changing UI text:

- Starfall/Wild Bounty improves gathering yield.
- Safe Roads improves movement and stamina recovery.
- Hallowed Ground improves health recovery.
- Arcane Clarity improves mana recovery.
- Settlement/Heroic Morale improves recovery.
- Fortune increases chest gold.
- Regional Unrest slows movement slightly and increases hostile attack pressure.

Aftermath expires automatically and event-owned mobs, nodes, chests, and telegraphs are cleaned by exact event ownership.

## Player presentation

The combat HUD displays the current local event, stage, progress, remaining time, and personal contribution. Event markers appear directly in the world and on the minimap. The world atlas receives all current public-event summaries so distant events can be discovered without exposing private player information. The regional Hunting Guide prioritizes an active local event over ordinary hunting suggestions.

Only Arcane Rift and caravan support stages use the context interaction key. Combat, gathering, treasure, escort proximity, and other objectives continue through their normal gameplay inputs.

## Compatibility and validation

Historical `arcane_storm` events are upgraded to the staged `arcane_rift` family when a saved realm is loaded. All new event fields have safe defaults for older saves. `LivingWorldEventChecks` permanently covers the eight event families, stage chaining, timeouts, exact cleanup, contribution rewards, persistence, scaling, caravan escort behavior, gameplay aftermath hooks, legacy upgrades, global snapshots, and client visibility contracts.

Subjective event cadence, reward excitement, and large-group social feel still require human multiplayer playtesting; automated checks validate rules and integration rather than claiming those judgments.
