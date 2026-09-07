# Combat verification guide

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
