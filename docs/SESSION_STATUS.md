## Active workstream: Measured smoothness, performance, camera and gameplay polish

Focused checkpoint: **Movement continuity + ranged caster basic attacks**

Status date: **2026-09-21**
Repository: danial-maqbool/Kairnfall-RPG
Persistent branch: **main only**
Verified Checkpoint 3 implementation: **5dc4d4209361279d534c02529d167f1de4ab2e54**
Evidence: docs/handoff/CURRENT_EVIDENCE.json
Release status: **NOT APPROVED — human acceptance remains.**

Checkpoint 3 is repository-side complete. It fixes the measured false-stop presentation defect during continuous local movement and gives the real caster/healer archetypes, Arcanist and Templar, a server-authoritative 6.0-tile ranged Spacebar basic attack with class-specific projectile presentation.

### Movement result

Same-process deterministic interstitial schedules reduced false-stop frames from **1 / 0 / 1 / 0** to **0 / 0 / 0 / 0** at 30/60/120/144 FPS; longest false-stop duration fell from **33.33 ms** to **0 ms**. At 144 FPS the candidate remains bounded at p95 error **0.168924 tile**, max error **0.220624 tile**, max lead **0.194442 tile**, final error **0**. The Windows native interstitial scenario also recorded zero false-stop frames. This is a continuity result, not an FPS claim.

### Combat result

Arcanist and Templar basic attacks use a **6.0-tile** server range and targeted authoritative projectile delivery. Arcanist uses Arcane visual language; Templar uses Radiant. Melee classes remain melee. Basic damage, stamina and cooldown formulas are unchanged. Client auto-approach/HUD use the same server profile range.

### Acceptance and hygiene

All 15 retained functional acceptance workflows plus **Client performance and motion diagnostics** passed on exact implementation SHA **5dc4d4209361279d534c02529d167f1de4ab2e54**. The temporary dispatcher was removed at **19a582a1bf3d7f4ffb7b4874c8ddcaf7e6dff781**. The prior Checkpoint 2 ledger is archived byte-for-byte at docs/handoff/SMOOTHNESS_CHECKPOINT2_EVIDENCE_2026-09-20.json.

No post-change owner-machine run is claimed after Desktop Commander was disallowed. Owner live traversal and Arcanist/Templar attack-feel checks remain useful human gates.

No release, publication, deployment, tag, force push, history rewrite or save deletion occurred. Server authority, movement speed, tick frequency, progression and rewards remain unchanged.
