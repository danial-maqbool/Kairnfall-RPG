# Build-Defining Loot, Crafting, and Progression

Task #4 extends Kairnfall's existing equipment progression rather than replacing it. The ordinary rarity, affix, rune, maintenance, commerce, bank, auction, trading, boss-drop, and deterministic asset systems remain the foundation.

## Boss signatures

The existing forty class milestone boss uniques now have authored signature engines. Their ordinary skill requirements still determine whether an item can be equipped, so an off-class player is never prohibited from using one. The matching class gains an additional effect while its Task #1 class resource is at its native READY threshold:

- Vanguard: Resolve-driven bastion defenses.
- Berserker: Fury-driven pressure and finishing damage.
- Ranger: Focus-driven attack tempo and elite/boss quarry pressure.
- Rogue: Momentum-driven speed plus poisoned-target burst.
- Arcanist: Resonance-driven spell and cooldown pressure.
- Warden: Bond-driven healing and spell pressure.
- Templar: Conviction-driven Radiant pressure and armor.
- Spellblade: Spellweave strengthens the opposite school and rewards alternation.

These loot effects do not consume class resources. Native class techniques remain the only automatic class-resource spenders, preserving the server-authoritative class combat contract.

Every boss signature keeps its existing deterministic item ID, icon path, level band, and boss drop assignment. The item card identifies the exact authored boss source for target farming.

## Conditional affixes

Rare-or-better ordinary equipment can roll one additional authored conditional affix. The effect pool is intentionally small and bounded instead of proc-heavy:

- Execution: extra damage below 25% target health.
- Resonant: power and cooldown recovery while the character's class resource is READY.
- Holdfast: armor and pressure while a usable shield is equipped.
- Attuned: bonus damage matching the item's non-Physical element.
- Aegiswoven: healing/protection-oriented bonuses.

These effects are represented as normal persisted affixes, participate in trade-consent fingerprints through the complete serialized item instance, survive bank/auction/save roundtrips, and are excluded from the numeric-stat comparison table so effect IDs are never rendered as fake numbers.

## Optional micro-sets

Three existing progression pieces at each selected mastery band form optional three-piece sets. No new item template or icon is created.

- Roadwarden (level-25 progression band): heavy chest, shield, charm. Two pieces improve block; three add armor and physical pressure.
- Stormrunner (level-55 progression band): medium boots, quiver, ring. Two improve attack speed; three add critical pressure while the class resource is READY.
- Starweaver (level-70 progression band): light gloves, focus, necklace. Two improve cooldown recovery; three add spell power while the class resource is READY.

Bonuses are computed from currently equipped, non-broken pieces. Removing a piece immediately deactivates the corresponding threshold.

## Offhand identity

Progression offhands now have stable family behavior in addition to their existing stats and compatibility rules:

- Shields are the bastion/pressure-absorption choice.
- Foci emphasize spell power and cooldown recovery.
- Quivers emphasize bow/crossbow attack tempo and critical pressure.
- Orbs emphasize mana reserve and sustained spell pressure.

Existing two-handed and quiver compatibility rules are unchanged.

## Skill-changing runes

Existing rune templates are upgraded without adding templates or art:

- Embers converts offensive abilities to Fire.
- Storm converts offensive abilities to Lightning.
- Echoes improves bounded ability recovery.
- Bulwark retains its block identity and advertises that build role.

When multiple element-conversion runes are equipped, the server selects exactly one transform: highest rune tier, then stable rune ID. Class-resource generation/spending still receives the authored ability family and therefore cannot be redirected into another class engine by a rune.

## Crafted specialization

Equipment recipes expose a Standard finish and mastery-gated targeted finishes. The crafting skill requirement is deliberately higher than the base recipe requirement. Available choices are:

- Execution finish.
- Holdfast finish.
- Class-engine READY finish.
- A fixed Fire, Frost, Lightning, Poison, Nature, Arcane, Radiant, or Shadow attunement at the highest specialization gate.

The specialization is persisted as an authored item affix (and, for elemental choices, the item's existing element field). The normal rarity roll still occurs, so specialization chooses build direction rather than guaranteeing maximal quality.

## Controlled reforging

At an enchanter or rune table, an unequipped item can reforge one non-specialization affix at a time. Every other affix remains locked. The operation consumes both gold and Rune Dust, preserves affix count, cannot reroll a crafted specialization, and inherits request-receipt replay protection. Reforging therefore cannot duplicate resources or increase merchant quality by adding affix slots.

Existing reclaim remains deliberately lossy: one item is destroyed and less than half of its recipe input value can be recovered. Socketed runes must still be extracted first, while boss signatures and exploration keepsakes remain excluded.

## Presentation and target farming

Full and compact item cards surface signature effects, conditional affixes, crafted specialization, socketed rune transforms, active set counts, and boss source hints. Existing rarity name colors remain intact and signature/set metadata is explicitly labeled. No generic replacement art is introduced.

## Determinism and regression coverage

`BuildDefiningLootChecks` is a permanent world-probe suite. It covers authored effect breadth, boss-source resolution, deterministic unique/set behavior, class-resource isolation, off-class legality, set activation/deactivation, bounded rune transforms, crafting skill gates, reforge/reclaim value safety, save/load, bank/auction/transfer serialization, merchant pricing, client effect presentation, deterministic icon paths, and offhand compatibility.

The content pass runs after equipment progression and asserts that every pre-existing item retains exactly the same icon path. Task #4 adds no item templates, so the deterministic Atelier/client asset path set is unchanged.
