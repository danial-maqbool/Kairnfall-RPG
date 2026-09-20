# Combat verification guide

## Current target and dash controls

Tab and Shift+Tab cycle eligible living nearby creatures. Deliberate targeting includes neutral wildlife, not companions or corpses. Q requests a collision-checked dash of at most 2.5 tiles, costing 4 mana with a 0.65-second cooldown. Root, stun and silence block it. Dash adds no invulnerability. The server owns direction validation, mana, cooldown and replay behavior. Chat/menu focus suppresses gameplay input. Existing mouse targeting and held-Space attack remain available. [Hunting and journey rules](HUNTING_AND_JOURNEY.md) and [exact verification](handoff/HUNTING_AND_PRESENTATION_2026-09-09.md) describe the integrated source.

Local repair `7f284b3` retains already-applied poison/burn/bleed damage while a
character is disconnected. Offline healing/training remain paused; lethal damage
cannot be undone by a later regeneration status in the same tick. Focused probes
pass. This does not resolve every combat-logout or boss-reset acceptance case.

Read accepted requirements R04-R09 and R15. Inspect `RealmCombat.cs`, `Mechanics.cs`,
`HandEquipment.cs`, item definitions, ability definitions, and their actual dispatch paths.
These files exist in the handoff; that does not prove every advertised effect works.

For all eight classes, verify basic damage, resource costs, targeting, cooldown, range,
armor/resistance, threat, block/evasion, critical effects, buffs/debuffs, interrupt, death, and respawn.
Test melee reach separately from projectiles. Verify shields and hand-equipment combinations.
Use server measurements for delayed hits. Switching equipment must not change the skill credit of an attack already launched.

For every ability, record its activation condition, server handler, visible effect, cost,
unlock, invalid-target behavior, cooldown, and persistence implications.
Compare description with runtime outcome. Similar names or data rows are not mechanically distinct abilities.
Test boss phases, telegraphs, adds, leashes, interrupted casts, resets, loot, and disconnect behavior.

Record time-to-kill, survival, healing throughput, and class/element comparisons under fixed inputs.
Choose balance changes from recorded results. Do not report measured performance from formula inspection alone.
