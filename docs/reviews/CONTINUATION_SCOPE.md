# Continuation scope

## Team connection

The user connected Zeiko and identified a team named Kairnfall-RPG.
The connected agent catalog returned zero agents in this session.
The exposed Zeiko actions support customer-support agent operations.
They do not expose coding-team lookup, task dispatch, repository workspaces, or worker execution.
This does not establish that the user's team is absent from the Zeiko website.
No independent coding agents were started through this connection.
GitHub Actions runs below are automated tests, not independent AI reviewers.

## Reviewed repairs

Source base: `5ea0ff9753e3aeabfad4610b25c839d38d49c0df`.
Branch: `team/qa/combat-equipment-repair`.

The isolated workflow verifies source preimages, applies a bounded patch, runs the existing core and network tests, runs new regressions, and commits only if those checks pass.
The local execution environment returned errors. The workflow supplies the execution environment for this batch.
The source manifest records original and resulting Git blob hashes. It is not a test report.

The batch covers:

- Shield block requires an equipped, usable, compatible shield.
- Bows and crossbows accept quivers. Other two-handed combinations remain restricted.
- Weapon changes and weapon removal detach incompatible offhands without deleting items.
- Polearms use melee reach rather than the projectile path.
- Every delayed player hit retains its originating skill through serialization and weapon changes.
- Skill-less legacy player telegraphs expire without inventing a skill award. Creature telegraphs remain unaffected.
- Offensive projectile selection rejects creatures in another region.
- Null command fields return a rule failure without changing realm state.
- Character name validation checks the trimmed name.
- Expired world events remove their objects and pending attacks with exact ID boundaries.
- A restored realm does not regenerate its current event cycle.
- A later save cannot silently recreate a deleted snapshot row.

## Unchanged acceptance requirements

The accepted Windows MMORPG specification remains the target. This batch does not reduce its content, gameplay, multiplayer, sprite, or release requirements.
Real-object pixel art remains mandatory. Readable anatomy, construction, materials, native-resolution detail, and aligned animation frames require image inspection in the game.
No sprite or Windows release acceptance is claimed by this repair batch.
The incomplete client, art, audio, balance, full-world presentation, load testing, and final release gates remain open.
