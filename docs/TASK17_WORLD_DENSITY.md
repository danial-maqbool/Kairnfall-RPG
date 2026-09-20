# Task 17 — Quest and World-Content Density

Task 17 enriches the established Kairnfall geography without increasing the overworld footprint.

## Scope

The implementation keeps the same 20 authored surface wilderness regions and the same 2,048,000 surface-wilderness tiles. No new continent, surface region, or replacement overworld is introduced.

The ten established minor settlements now receive a deliberately denser local layer:

- three additional purposeful residents per settlement: a guard, a scribe, and a locally appropriate specialist;
- one authored three-stage regional story chain per settlement;
- explicit reuse of nearby waymarks, resources, ordinary threats, services, and existing dungeon entrances;
- settlement resolutions that return to local people instead of ending at the encounter site.

This adds 30 residents and 30 non-repeatable quests while reusing existing geography.

## Chain shape

Each settlement chain uses its own story but follows a broad progression:

1. **Discovery / investigation.** The local traveler sends the player into the settlement's existing parent region to inspect two authored waymarks and consult a specialist.
2. **Escalation / practical work.** The specialist asks for a region-appropriate mixture of gathering, crafting, local threat removal, and watch coordination.
3. **Resolution.** Where an existing dungeon belongs to the region, the local story gives that dungeon and boss an additional settlement-facing purpose. Brambleford, which has no authored dungeon in Thistle Woods, resolves through a sustained road-clearing and waymark task instead of inventing a new zone.

The chains are deliberately non-repeatable so their rewards cannot become a new daily currency faucet. Existing repeatable field reports and guild expeditions remain the repeat-visit layer.

## Hidden exploration

The implementation extends the purpose of the existing regional exploration system instead of creating a second secret-state mechanism.

Every discovery stage asks the player to inspect two real regional waymarks. The existing authoritative exploration rules reveal a hidden-cache clue after two waymarks. Opening that cache is **not** a quest objective, so optional exploration never blocks critical local progression.

The existing hidden-cache, charting, regional mastery, achievement, and discovery persistence rules remain authoritative.

## Rewards and economy

Rewards use existing progression items and modest gold values scaled to the established region or encounter level.

The new content does not add a new currency, bypass crafting requirements, duplicate loot tables, or create a new item source outside the normal authoritative quest-claim path. Quest claims continue to use request receipts, action sequencing, transactional rollback, completed-quest state, and persistent character storage.

## Server authority and persistence

Task 17 does not introduce a client-owned quest system. New definitions flow through the existing `QuestDef` catalog and the existing `RealmEngine` commands:

- `accept_quest`;
- normal authoritative world actions such as transition, inspect, gather, craft, kill, boss, and talk;
- `claim_quest`.

The server remains responsible for objective progress, prerequisite gates, rewards, reputation, completed state, cooldowns, command replay handling, and persistence.

## Validation and regression coverage

`content_src/world_density.py` validates every new giver, reward, prerequisite, and objective target while generating the catalog.

`tests/handoff/test_task17_content.py` rebuilds the complete authored catalog twice and checks deterministic equality, exact surface footprint, settlement density, and chain structure.

`tools/world_probe/Task17WorldDensityChecks.cs` runs as part of the existing world-probe test executable and verifies:

- unchanged overworld footprint;
- all ten minor settlements have the expected resident roles;
- all ten three-stage chains are present and ordered;
- objective variety and navigation guidance;
- existing-dungeon reuse;
- optional hidden-cache clue integration;
- authoritative quest acceptance/progression;
- quest-progress survival across a realm-state restart;
- exactly-once reward delivery under command replay;
- rejection of a fresh duplicate claim;
- completed-state and reward persistence after restart.

No public release, tag, deployment, production realm, DNS, or production credential is created by Task 17.
