# Task 2 progression audit — 2026-09-11

## Scope

This record covers the automated authoritative portion of acceptance Task 2. It does not claim a human normal-play session.

The permanent `tools/world_probe/RealActivityProgressionChecks.cs` audit boundary-seeds only prerequisite state and a one-XP skill-level boundary, then requires XP to come from the same `RealmEngine` activity handlers used by gameplay. It writes `artifacts/logs/task2-progression-audit.json` in CI.

## Skill coverage

All 60 accepted skills are exercised through an authoritative activity rather than through a direct `Progression.Train` call. Coverage includes:

- weapon attacks, including unarmed combat;
- hostile block, evasion and matching armor damage resolution;
- class ability casts for magic training;
- meditation, hostile kills, camp rest and sector exploration;
- every gathering family, prospecting and treasure/locked chests;
- every crafting family through a real recipe/station handler;
- merchant bartering, regional charting, animal taming and construction.

For every skill the audit requires the real activity to increase skill XP, cross a prepared visible skill-level boundary, increase accumulated Character XP, advance Character Level value, respect each declared milestone threshold, and survive a full serialized realm restart roundtrip. The report also records concrete equipment, recipe, ability and resource unlock sources for each skill.

## Class coverage

All eight accepted classes are checked for their authored role/passive metadata, three affinity skills, starter weapon and chest identity, restart persistence, and the class-affinity training multiplier. Every one of the 15 authored abilities per class is executed through the real cast handler, for 120 class abilities total, with an observable effect required for its behavior family (damage, heal, shield, buff, stealth, purge, summon, taunt, dash, interrupt or area/line/cone/field/projectile behavior).

The first CI execution exposed a fixture error in the three self-centered taunt abilities: the audit supplied a hostile target position to zero-range taunts. The permanent fixture now keeps both the target identifier and cast location on the caster while retaining a nearby hostile to prove the taunt/guard effect. This corrects the test harness and does not change gameplay rules or lower an acceptance threshold.

## Verified automated result

Build and verify run `34549335990` passed on source `3ecae2846d1d531b1720e2b91eb305169c9557c3`. The authoritative activity audit recorded all 60 skills and all eight classes with 68 groups passed and zero failures. The same run also passed core regressions, gameplay/malformed-input regressions, world/save checks, PostgreSQL real-network integration (18/18), save-conflict checks (5/5), and the Windows core job. The later `47fd5cd5b23fce0bfdef5365d9704da978e4948c` cleanup changes only three nullability annotations in this audit fixture and removes its one-shot cleanup workflow; no runtime behavior or acceptance threshold changes.

## Evidence boundary

This automated audit is deliberately stronger than catalog counting, but it is not the human normal-play acceptance requested by the QA matrix. Human review is still required for class feel/identity in sustained play, pacing, subjective usefulness, and physical Windows input. Those claims must not be inferred from this record.

Task 1's hands-on Windows XP/HUD playthrough also remains reserved for final user testing and is not closed by this Task 2 record.
