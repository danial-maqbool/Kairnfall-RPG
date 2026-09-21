# Measured smoothness, performance, camera and gameplay polish — Checkpoint 3 verification

Status date: **2026-09-21**
Repository: danial-maqbool/Kairnfall-RPG
Checkpoint start: **192c8b50ce6ecac11e6327189af6208dd26c7944**
Verified implementation SHA: **5dc4d4209361279d534c02529d167f1de4ab2e54**
Machine-readable truth: docs/handoff/CURRENT_EVIDENCE.json
Release status: **NOT APPROVED — human acceptance remains.**

## Scope and root cause

Checkpoint 3 addresses the two requested player-visible defects: local walk → brief stick/freeze → walk presentation, and melee-only Spacebar basics for the caster/healer archetypes.

The movement defect was in presentation continuity, not authoritative movement speed. The server remains at its existing 50 ms simulation step and 100 ms snapshot cadence. The old client lead/freshness window was short enough that rendered motion could converge to an unchanged/interstitial authoritative sample and briefly lose visible velocity even while movement intent continued. Position error alone hid this symptom. The repair measures authoritative sample time, preserves bounded velocity through short unchanged samples while local movement intent remains active, handles reversals without slow blended turn-through, extends the bounded presentation lead/freshness window, and explicitly clears local visual velocity when movement intent stops.

No authoritative position is predicted or committed client-side. Local intent is only a presentation-continuity hint.

## Movement measurements

The exact Windows CI artifact from **Client performance and motion diagnostics** run **35532183875** compares retained legacy and candidate rules in the same process over 48 deterministic schedules.

| Interstitial metric | Legacy 30/60/120/144 FPS | Candidate 30/60/120/144 FPS |
| --- | --- | --- |
| False-stop frames | 1 / 0 / 1 / 0 | 0 / 0 / 0 / 0 |
| Longest false stop (ms) | 33.33 / 0 / 8.33 / 0 | 0 / 0 / 0 / 0 |

At 144 FPS, candidate p95 rendered-authoritative error is **0.168924 tile**, max error **0.220624 tile**, max forward lead **0.194442 tile**, and final error **0**. The retained legacy comparison at 144 FPS measured p95 error **0.141268 tile**, max error **0.220624 tile**, and max lead **0.075975 tile**. The candidate intentionally trades some bounded visual lead for continuity; no broad FPS improvement is claimed.

The Windows native interstitial scenario recorded **0 false-stop frames**, **0 ms longest false stop**, p95 position error **0.003777 tile**, and max position error **0.234101 tile**.

## Ranged Spacebar basic attacks

Repository class taxonomy identifies **Arcanist** (`arcanist`) as the elemental caster and **Templar** (`templar`) as healing/support. Both now use an explicit server-owned basic-attack profile with a **6.0-tile** maximum basic range. Six tiles lies inside the authored 5–8 tile caster/support spell band and below Arcanist's dedicated 8-tile projectile abilities.

The server still validates living hostile target, zone, line of sight, range, stamina, stun state, weapon durability, cooldown, damage, training and death. Damage/cooldown formulas were not changed. Ranged basics create a targeted authoritative projectile telegraph; Arcanist uses Arcane presentation and Templar uses Radiant presentation. The projectile carries authoritative origin/start/target data, travels visually from attacker to target, and resolves damage once on the server. Nearby creatures are not splash-hit. Melee classes keep their existing melee basic profile.

Client target selection, HUD range feedback and bounded auto-approach now use the same class-aware basic range, so Arcanist/Templar stop approaching once within six tiles instead of walking to weapon-melee range.

## Exact implementation-SHA acceptance

| Workflow | Run ID | Result |
| --- | ---: | --- |
| Transaction security regression | 35532173984 | success |
| Compile Windows client source | 35532180225 | success |
| Live progression breadth | 35532182689 | success |
| Windows package acceptance | 35532188643 | success |
| Graphical multiplayer acceptance | 35532187324 | success |
| Load acceptance | 35532173881 | success |
| Build and verify | 35532173930 | success |
| Task 13 adversarial acceptance | 35532173909 | success |
| Release operations acceptance | 35532173951 | success |
| Transaction integrity on Windows and Linux | 35532173826 | success |
| New-player journey | 35532189759 | success |
| Character sprite acceptance | 35532185003 | success |
| Visual acceptance matrix | 35532181390 | success |
| Windows display and input acceptance | 35532186278 | success |
| Audio acceptance | 35532178994 | success |
| Client performance and motion diagnostics | 35532183875 | success |

Performance diagnostics ran native Linux job **106134664520** and Windows job **106134664572**. Artifact IDs are **10612340756** (Linux) and **10612400699** (Windows). The temporary exact-head dispatcher succeeded at run **35532173828** and was removed at **19a582a1bf3d7f4ffb7b4874c8ddcaf7e6dff781**.

The pre-sync Documentation evidence contract run **35532173844** failed only after its evidence regression suite passed; it correctly rejected the still-Checkpoint-2 CURRENT_EVIDENCE.json as stale.

## Validation boundary

The accepted implementation changes no server tick frequency, movement speed, basic damage formula, attack cooldown formula, progression rewards or save schema. Server authority is preserved. No release, publication, deployment, tag, force push, history rewrite or save deletion is part of this checkpoint.

No post-change owner-machine run is claimed after the user requested that Desktop Commander not be used. Exact Windows GitHub Actions native coverage is retained as automated evidence; owner live movement/combat feel remains a human gate.
