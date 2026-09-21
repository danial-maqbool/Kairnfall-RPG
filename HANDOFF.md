## Active workstream: Measured smoothness, performance, camera and gameplay polish

Status date: **2026-09-21**. Verified Checkpoint 3 implementation: **5dc4d4209361279d534c02529d167f1de4ab2e54**. Machine-readable truth: docs/handoff/CURRENT_EVIDENCE.json. Release status: **NOT APPROVED — human acceptance remains.**

The focused movement-stutter + ranged caster-basic-attack task is repository-side complete. The movement repair preserves bounded authoritative presentation velocity across short unchanged/interstitial snapshots while local movement intent remains active, handles reversals responsively, and clears visual lead immediately on real local stop. No client-owned authoritative position was introduced.

Measured same-process interstitial false-stop frames fell from **1 / 0 / 1 / 0** to **0 / 0 / 0 / 0** at 30/60/120/144 FPS. At 144 FPS the candidate records p95 rendered-authoritative error **0.168924 tile**, max error **0.220624 tile**, max forward lead **0.194442 tile**, and final error **0**. Windows native CI also recorded zero false-stop frames. This is a movement-continuity result, not a broad FPS claim.

The repository's actual caster/healer classes are **Arcanist** and **Templar**. Their ordinary Spacebar basic attack now uses a server-authoritative **6.0-tile** class profile and targeted projectile delivery; Arcanist presents Arcane and Templar Radiant. Client targeting/HUD/auto-approach use that same range. Melee classes remain melee. Basic damage, stamina, cooldown, movement speed, tick frequency, progression and rewards are unchanged.

All 15 retained functional acceptance workflows plus **Client performance and motion diagnostics** passed at exact implementation SHA **5dc4d4209361279d534c02529d167f1de4ab2e54**. Exact run IDs, native job/artifact IDs, measurements, and the expected pre-sync documentation rejection are in docs/handoff/MOVEMENT_RANGED_BASIC_VERIFICATION.md and docs/handoff/CURRENT_EVIDENCE.json.

The temporary exact-head acceptance dispatcher was removed at **19a582a1bf3d7f4ffb7b4874c8ddcaf7e6dff781**. Checkpoint 2 evidence is archived byte-for-byte at docs/handoff/SMOOTHNESS_CHECKPOINT2_EVIDENCE_2026-09-20.json.

## Remaining human gate

No post-change owner-machine run is claimed after the user requested that Desktop Commander not be used. Owner live traversal and Arcanist/Templar attack-feel/visual-timing checks remain useful acceptance gates; repository-side implementation and automated acceptance are complete.

Keep **main** as the only persistent branch. Do not release, deploy, tag, rewrite history, delete saves, or alter production infrastructure. No such action was authorized or performed.
