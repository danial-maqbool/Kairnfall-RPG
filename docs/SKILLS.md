# Skill audit contract

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
