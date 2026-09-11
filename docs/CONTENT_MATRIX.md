# Content acceptance matrix

Current consolidated status as of 2026-09-11.

This file tracks content breadth separately from human quality approval. Counts and automated paths establish coverage; they do not by themselves establish artistic quality, subjective balance, or a complete human playthrough.

## Current verified content coverage

| Content | Accepted target | Current repository evidence | Human acceptance remainder |
| --- | ---: | --- | --- |
| Classes | 8 | 8/8 class kits are audited; all 120 class abilities execute through real effect handlers. | Subjective class identity/feel. |
| Trainable skills | 60 | 60/60 skills execute through real authoritative activity routes with XP, level transition, Character XP contribution, unlock and persistence checks. | Normal-play pacing/feel. |
| Player abilities | 120 | All 120 class abilities are exercised by the Task 2 authoritative audit. | Human combat feel/readability. |
| Item templates | >=450 | Current equipment expansion retains 1,354 item templates and 1,286 recipes from the integrated gear progression. | Economy/art usefulness through normal play. |
| Equipment tracks | 100+ weapons / 100+ armor | 21 skill tiers, 51 families and 1,071 tracked equipment entries remain integrated; 13 visible equipment slots have isolated action/direction review evidence. | Independent visual approval and sustained balance feel. |
| Normal species | 100 | 100/100 normal creatures have action/direction structural and rendered review coverage. | Independent anatomy/art approval. |
| Elites | 25 | 25/25 elites have action/direction structural and rendered review coverage. | Independent encounter/art approval. |
| Bosses | 20 | 20/20 bosses have full action/direction review coverage with 128×128 boss-safe evidence. | Human encounter/art approval. |
| World regions / zone anchors | 109 audited | 109 zone-anchor checks pass, including authored connectivity and service/objective destinations used by the world audit. | Full ordinary-account traversal. |
| Quests / objective anchors | 166 audited | 166 quest-anchor checks pass. | Full objective/resource/boss-arena walkthrough and narrative-quality review. |
| Map layers | 4 required | The authored world graph retains Surface, Deepways, Umbral Depths and Aether Rift connections in automated route coverage. | Human traversal of every required layer/link. |
| Runtime audio | 22 WAV assets | All 22 pass technical format/duration/peak/RMS/DC/clipping/loop-boundary analysis. | Listening approval. |
| Player base variants | 12 shipped | Refined Atelier source regenerates the 12 checked-in base-body sheets exactly; all variants/actions are included in visual review evidence. | Independent artistic approval. |

## Progression and class evidence

Task 2 final authoritative audit verifies all 60 skills through real server activity routes and all eight class kits / 120 abilities through real effect handlers. Final Task 2 CI run `34550409865` passed on `d2eb494ff9f3dacc4e3e7fecab811ab7883ddc7a`.

Catalog descriptions are not used as proof of implementation.

## Character and creature evidence

Task 3 final baseline `defec56aadf5bc01289b4c7ec8c0e422b918624f` passed:

- Build and verify run `34555269188`.
- Visual acceptance matrix run `34555269207`.
- Exact visual review run `34555269185`.

The final visual evidence covers idle/walk/attack/cast/hit/death in all four directions, readable per-creature sheets, isolated per-equipment-slot sheets, all 12 shipped player base variants, and native Godot presentation captures.

Automated rendering does not grant independent artwork approval.

## World and quest evidence

The automated audit covers 109 zone anchors and 166 quest anchors. It distinguishes dynamically created resources (for example skinning/carcass state) from static seeded resource nodes rather than failing valid dynamic gameplay.

This closes the repository-side route/reference audit. The full ordinary-account world and quest walkthrough remains a human acceptance gate.

## Equipment and economy evidence

The complete equipment progression remains integrated: 21 skill tiers, 51 families and 1,071 tracked entries, with 1,354 item templates and 1,286 recipes from the current equipment expansion. Authoritative equip/craft behavior, workstation boundaries and the economy correctness audit are automated.

Sustained economic pacing remains human balance work.

## Acceptance interpretation

The following historical statements are no longer current: that the complete creature roster lacks automated review, that 60 skills lack authoritative action evidence, that resource/quest/boss routes have no coverage, or that Windows/package/load/multiplayer infrastructure is absent. Those statements remain only in dated historical checkpoints at their original revisions.

Current human-only content acceptance still includes:

- full normal-play progression/class feel;
- independent character/equipment/creature artwork approval;
- full world/quest/resource/boss traversal;
- sustained economy/balance feel;
- audio listening review.

Use `handoff/VERIFICATION.md` and `QA_MATRIX.md` for the current gate status. Do not declare a public release from counts alone.
