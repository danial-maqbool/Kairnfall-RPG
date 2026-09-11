# Mid/late-game content

Status: implemented as Area 7 mid/late-game content work.

This pass extends existing world systems rather than adding a separate endgame mode.

- All 20 authored dungeons now have a daily guild expedition. Each contract requires entering the real dungeon and defeating its authored boss.
- Bosses at level 50 and above add a relic-shard field objective, so veteran expeditions feed the existing crafting/material economy instead of becoming pure boss-reset loops.
- Expedition offers have authoritative character-level gates at five levels below the boss and story prerequisites. The server enforces both; the client shows the required character level before acceptance.
- The six optional dungeons omitted by the 25-quest main chain now have one-time guild circuits: two Deepways sites and four Umbral sites. This gives every dungeon a narrative objective before it becomes repeatable work.
- Regional survey and field-report quests now unlock at the same five-level frontier band as their wilderness region, reducing high-level quest clutter and making progression bands easier to read.
- Journey/Hunt guidance can surface repeatable work again after its daily cooldown once one-time local work is exhausted.

`MidLateGameContentChecks` verifies complete dungeon coverage, veteran objective composition, optional-dungeon narrative coverage, regional level bands, authoritative level/story/cooldown enforcement, exact repeatable rewards, and post-story repeatable guidance.

Repository automation establishes content wiring and gate correctness. Long-session variety, reward satisfaction, and perceived repetition remain hands-on playtest judgments.
