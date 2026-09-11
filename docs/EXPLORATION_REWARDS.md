# World exploration rewards

Status: implemented as Area 5 exploration-reward work.

The 20 surface wilderness regions now share one coherent exploration loop rather than isolated discovery counters:

1. **Survey waymarks.** First-time landmark surveys grant Exploration XP and surface the region's authored lore.
2. **Earn a cache clue.** Surveying two of the region's four waymarks grants a permanent clue and Treasure Hunting XP. The clue never reveals an exact atlas coordinate; it only lets the hidden cache appear in-world when the player searches within 12 tiles.
3. **Find and open the hidden cache.** Every surface wilderness region already had one hidden cache. Its first opening now records a permanent regional objective and grants an additional Treasure Hunting bonus.
4. **Chart real terrain.** Regional charts now require four actual 16x16 map sectors; landmark metadata can no longer satisfy the chart requirement by itself.
5. **Claim regional mastery.** Surveying all four waymarks, opening the hidden cache, and charting the region grants a one-time regional keepsake, bonus gold, Exploration XP and Treasure Hunting XP. Five, ten and twenty mastered regions award Pathfinder, Trailblazer and Worldwalker achievements.

There are 20 deterministic `exploration_unique` keepsakes, one per surface wilderness region. They are trophy/treasure items rather than combat gear, so exploration rewards do not create mandatory power creep. If the backpack is full, the keepsake goes to the bank; if both are full, mastery remains claimable by inspecting a waymark after freeing a slot.

The Hunt guide and Atlas show exploration progress, clue state and the named mastery prize without exposing hidden-cache coordinates. Server-side discovery, cache visibility, first-open bonuses, chart validation and one-time reward issuance are covered by `ExplorationRewardChecks` in the normal world-probe suite.
