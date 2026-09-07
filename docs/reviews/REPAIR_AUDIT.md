# Gameplay repair audit

## Scope and evidence

This audit covers backend repairs, not completed MMORPG acceptance.
No independent AI worker or visual reviewer executed this batch.
The author inspected the code and GitHub Actions executed the tests.

Base: `5ea0ff9753e3aeabfad4610b25c839d38d49c0df`.
Tested source repair commit: `fdfe81a16390c3d7cc3bcfe6495b3fc044a70916`.
Workflow run: https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34106654485
Job: `101693115055`.
Evidence artifact: `10012698380`, `review-repair-evidence-34106654485`.
Artifact SHA256: `3982daeee4fad845cf22f402a63cd0dcfa8773ff49165229f33eff3067b84bae`.

The inspected log reports a successful server build with zero compiler warnings and zero compiler errors.
It reports these completed suites on Ubuntu:

| Suite | Passed | Failed |
|---|---:|---:|
| Existing core regressions | 29 | 0 |
| New gameplay and malformed-input regressions | 34 | 0 |
| Real-network and PostgreSQL integration | 18 | 0 |
| New PostgreSQL save-conflict regressions | 5 | 0 |
| Total | 86 | 0 |

The network test connects three clients. It is not a 100-player load test.
The JSON reports and logs contain the individual outcomes.
Catalog counts remain unchanged and do not certify content quality.

## Repairs

Shield block now requires an equipped usable shield with a valid hand pairing.
Quivers work with bows and crossbows without allowing shields beside two-handed weapons.
Weapon changes detach incompatible offhands without deleting those items.
Removing a bow also detaches its dependent quiver.
Loaded invalid hand combinations fail validation.
Spears and halberds now use melee reach rather than projectile behavior.

Delayed player attacks preserve their originating skill through weapon changes and serialization.
Projectile, area, cone, line, and field hits carry that skill explicitly.
Old player telegraphs without valid skill metadata expire without inventing a skill award.
Creature telegraphs do not require a player skill.
Selected creatures in another region cannot receive offensive projectile commands.

Null command fields return a rule failure without changing state.
Character name validation applies to the trimmed name.
Expired event cleanup removes associated objects and attacks by exact ID boundaries.
Restoring a realm does not regenerate an already processed event cycle.
Event creature selection now respects regional level bounds.

A save with a nonzero revision cannot recreate a deleted database snapshot row.
Stale writes and fresh-state overwrites fail without advancing the in-memory revision.
The database regression suite creates and removes only its own random test schema.

## Permanent verification

The follow-up CI configuration builds all existing solution projects and requires all four suites.
A Windows job runs the two core suites through `Test-Kairnfall.ps1`.
The Windows job must produce its own successful run before Windows behavior is claimed.
This document's confirmed 86-check result is the Ubuntu repair run above.

The temporary patch script and its branch-writing workflow are removed after successful application.
The provenance manifest remains under `docs/reviews/repair-source-manifest.json`.
Normal verification jobs retain read-only repository permissions.

The solution no longer references a nonexistent Godot client project.
This corrects the build configuration. It does not implement the missing client.

## Open release gates

No playable Windows client, approved sprite set, final world presentation, audio package, or release is delivered by this batch.
Full gameplay coverage, content uniqueness, high-level skill progression, boss encounter implementation, balance, load testing, and final adversarial/visual acceptance remain open.
The original specification and detailed real-object pixel-art requirement remain unchanged.
