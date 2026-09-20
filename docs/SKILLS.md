# Skill audit contract

## Early access and overall growth

Equipment grades 5, 10 and 15 now require matching skill levels 3, 6 and 10 to use. Grade 20 and higher keep their original use requirements. Intermediate early requirements never increase. Crafting grades and raw-material requirements do not change. A smooth bonus accelerates early overall progression without rewriting saved skill XP or individual skill levels. Existing overall levels do not decrease. [The journey guide](HUNTING_AND_JOURNEY.md) gives the exact formula and distinguishes measured boundary tests from unmeasured human progression time.

## Equipment requirements — 2026-09-09

[Named equipment tiers](EQUIPMENT_PROGRESSION.md) use the item's matching skill. They do not require the same overall player level. Equipment and crafting skills are separate requirements. The skill cap remains 100. The Upgrade guide displays the exact skill, the requirement and the player's current skill level. Server-boundary and crafting tests cover every tracked gear item; this does not approve the pacing or benefits of every other skill.

All 60 named skills are listed in accepted requirements R05 and defined in `content_src/skills.py`.
Use its action and benefit fields as claims to verify, not proof that the action/effect exists.
The handoff completes all catalog skill-icon references through `tools/complete_skill_icons.py`.

Create one audit row per skill: source ID, training input, valid action, XP award, duplicate/failure behavior,
level curve, unlock, real gameplay benefit, UI feedback, overall-level contribution, and restart persistence.
Test from the player's accessible interface, not only by directly assigning XP in a fixture.
Use fixture seeding for isolated tests only and label it separately from normal progression.

Overall player level must derive from individual skill progress. Verify gathering/crafting/exploration as well as combat.
Simulate specialists and generalists across early, middle, and late levels.
Check requirements for every tool, recipe, equipment item, class ability, and training action.
Repair inaccessible progress and meaningless skill counters without removing the skill from the accepted set.
