# Combat feel and encounter presentation

Status date: **2026-09-18**  
Verified implementation baseline: **`06776f6b0de7dbe02cab30a9e236e730c377de2e`**  
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`  
Release status: **NOT APPROVED — human acceptance remains.**

This pass improves combat responsiveness and readability without changing authoritative damage, cooldown resolution, rewards, encounter balance, saves, or server gameplay handlers.

## Responsiveness

- Basic attacks have a **0.25 second** input buffer. A tap just before the authoritative cooldown clears can queue one attack; the client still waits for the snapshot to show the cooldown ready before sending the request.
- Holding basic attack with no valid target remains armed without sending empty-target combat requests, so a newly valid nearby target can be engaged naturally. Releasing the key cancels automatic approach but preserves only the bounded tap queue; menus, focus loss, death, disconnect, and explicit combat cancellation clear queued intent.
- Basic-attack approach remains short and bounded. If no short route exists, pursuit stops with a clear message instead of replanning indefinitely.
- Ability buffering remains **0.35 seconds**, but now preserves the target kind, target ID, and cursor aim from the original key press. A queued cast therefore cannot drift to a different target or later mouse position.

## Targeting

- Explicit targets are sticky: a selected creature within the short **1.75 tile** approach grace is retained rather than silently replaced by a nearer creature.
- Explicit offensive abilities fail closed if the selected target disappears, is blocked, or is out of ability range. They no longer silently retarget another enemy.
- Automatic targeting prefers an eligible enemy that is already attacking the player before ordinary distance/facing tie-breaks.
- The selected-target overlay reports authoritative health percentage, distance/range state, crowd control, elite/boss identity, and whether the creature is attacking the player.
- The target reticle reflects in-range, short-gap, or out-of-range state; matching text remains present so the information is not color-only.

## Encounter readability and feedback

- Authoritative enemy telegraphs pulse more strongly as their server resolve time approaches, and the final 0.35 seconds show an explicit **NOW** cue.
- Confirmed health changes still create impact rings, floating damage/healing numbers, hit/death animation, and creature reaction audio.
- Snapshot health deltas do not identify a trustworthy damage source, so generic selected-target damage no longer plays the local player's weapon-impact identity. This avoids falsely attributing another player's hit to the local character.

## Authority and scope

The client sends intentions only. It does not predict damage, cooldown completion, crowd control, target health, hit success, or telegraph resolution. No `content_src` files, `src/Kairnfall.Server` files, damage formulas, resource costs, enemy stats, loot rules, XP rules, or authoritative combat handlers were changed. The only shared-core change is read-only presentation logic in `src/Kairnfall.Core/CombatReadability.cs`.

All 15 permanent required workflows succeeded on exact implementation SHA `06776f6b0de7dbe02cab30a9e236e730c377de2e`. See `docs/handoff/COMBAT_FEEL_VERIFICATION.md` for the run IDs and scope boundaries.

Repository automation does not establish subjective combat feel, balance quality, artistic quality, audio-mix quality, physical-device input quality, release readiness, or production capacity. Those remain human-only gates.
