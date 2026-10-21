## October 1 verified portable offline folder

[Latest portable checkpoint](docs/NATIVE_CLASSIC_PORTABLE_CHECKPOINT_2026_10_01.md): client/server/native launcher/PostgreSQL are bundled without saved data or secrets. Run `deliverables/Kairnfall-Offline-Windows-2026-10-01/Play-Kairnfall.cmd` in MysteraLegacyLocal; no Python/installed .NET/editor/Docker/dev checkout is needed at runtime. A clean relocated C: copy passed cold startup, 101 headless account checks, 14 exact restart checks, 15 graphical saved reload and 15 more after saved-folder relocation. All owned endpoints stopped. Human full graphical/input/art/audio/load and measured reference fidelity remain open; [concrete gaps](docs/NATIVE_REFERENCE_FIDELITY_GAPS_2026_10_01.md) distinguish missing mechanics from subjective taste. Local/uncommitted only; no public release.

## October 1 verified local Windows client checkpoint

[Latest local Windows checkpoint](docs/NATIVE_CLASSIC_WINDOWS_CHECKPOINT_2026_10_01.md): approved runtime packs verified; standard self-contained client export, native main startup/normal close and 134 packaged graphical checks passed. Packaged normal-account headless gameplay/restart passed 100/14, with 15 real graphical saved-realm checks. Compact progression feedback now leaves the avatar clear. Use `Play-Classic-Windows-Package.cmd` in MysteraLegacyLocal for the retained separate offline preview realm. Full uninterrupted graphical/human play, original art, audio/load and portable server packaging remain open. Source, IDs, protocol and personal saves are preserved; this is local, uncommitted work and no public release is approved.

## October 1 native visual/routing follow-up

[Latest local follow-up](docs/NATIVE_CLASSIC_VISUAL_ROUTE_FOLLOWUP_2026_10_01.md): graphical route overshoot repaired with authoritative single steps; optional original dense grass, layered oak crowns, spiral Action Circle and clearer combat feedback. Core 54, review 34, security 13; native classic 113, controls 1184, layout 1639 and input passed. Updated real-account headless play passed 100, exact restart 14, graphical saved-realm restart 15. Full uninterrupted graphical play remains open due retained interruption/failure evidence. Framework-dependent publishing passed, but draft startup failed 0xC0000005; no package/release is approved. Use the source preview; exact required NuGet packages/87.58 MB are documented for a future authorized export attempt. Existing source, IDs, protocol and personal saves are preserved.

## October 1 local classic controls and playable-loop checkpoint

[Current local implementation and verification](docs/NATIVE_CLASSIC_PLAYABLE_CHECKPOINT_2026_10_01.md) supersedes the bounded [first checkpoint](docs/NATIVE_CLASSIC_CHECKPOINT_2026_10_01.md). Optional authoritative tile movement, selected adjacent attacks, hold/release gathering, compact 15-slot inventory/crafting, quick consumables, item drops, Shift pickup and input/refresh repairs are implemented. Core 53, review 34, security 13 and private PostgreSQL review 5 passed. Real native/local-server account play passed 79 checks, then server restart passed 14 exact possession/progress/building checks. Native fixture/graphical evidence is separate from human approval.

Native architecture, prior dirty changes, IDs, protocol compatibility and personal saves are preserved. The private game-only QA database ran without Docker or unrelated service changes. Native visual parity, uninterrupted human/graphical full-loop play, audio/load and packaging remain open. This is an uncommitted local checkpoint, not a release or exact-head CI approval. Read the dated report and source hashes before continuing; do not treat older evidence as new-tree approval.


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
