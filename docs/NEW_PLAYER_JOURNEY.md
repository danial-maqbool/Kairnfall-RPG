# New-player journey and early retention

## Scope and audit

This pass joins guidance, real progression feedback and optional public activity in the existing persistent world. It adds no region, tutorial instance, quest reward, currency source, character-level modifier, faction skip or production infrastructure. Existing Task 20 event rules, Task 21 dungeon/boss rules and Task 22 endgame prerequisites remain authoritative. The targeted 15-minute and first-hour sequence below is design intent, not measured human completion time or retention evidence.

A new character starts at Wayfarer's Rest with the class weapon and armor equipped, usable backpack tools, potions, a starter rune and one weapon socket. A Place by the Fire is the introductory innkeeper quest: gather three oak logs, craft a wooden handle through the oak-plank intermediate recipe, and speak to the blacksmith. A Spark in the Stone already teaches the rune upgrade. The sealed letter leads through Kingsmeadow to the Dawnreach traveler. The previous checklist exposed gathering/crafting before combat, repeated for established characters, mixed stale keyboard instructions with current input bindings and had no single actionable route. Public-event text competed with the location heading and event notices were not filtered to nearby appropriate activity.

## Designer-facing opening sequence

1. Spawn in the shared settlement. The expanded objective names the real innkeeper, explains the reward and offers a walkable route. A brief hint shows current movement and interaction bindings.
2. Accept the existing workshop errand. When an authored starter rat or another suitable weak foe is visible, guidance offers one optional practice fight. Target selection and held basic attack are explained near the foe. If no suitable foe is available, the actual quest remains actionable.
3. A real kill and owned loot lead to backpack discovery. Normal combat XP and dropped rewards are unchanged. A usable, non-regressive equipment upgrade is flagged only when actual item and derived-stat comparisons agree. Receiving an item never equips it automatically.
4. Use the starter rune through the existing trainer quest. The feedback queue shows actual equipment-stat changes, not a cosmetic power score. Gathering and crafting then follow the real oak-log -> oak-plank -> wooden-handle dependency chain.
5. Claim the introductory quest normally. The reward card identifies the authored reward. Earned skill and character levels produce separate, non-modal cards; character-level feedback includes real maximum-health change, and ability notices use actual skill and cross-class requirements.
6. Follow the level-eligible exit graph toward Dawnreach with the sealed letter. The route button marks the next local waypoint and uses ordinary movement. The map, journal, and all existing service panels remain available.
7. On the Kingsmeadow road, an eligible newcomer may receive the scheduler's existing treasure-surge event in one normal event slot. It is a shared public event with normal contribution thresholds, scaling, reward ledger, and aftermath. It requires neither a party nor another human player. Not now returns to the quest route without rewards or credit.
8. Reach the first meaningful settlement and continue The Letter on the Road. Social discovery stays optional; the nearby-player control reflects real snapshot-visible travelers, including a truthful zero-population state. The existing rare hunt remains gated by its real level and quest prerequisites.

## First hour and system exposure

Movement, interaction, quests and a safe combat opportunity come first. Loot, backpack, equipment comparison, the rune, level feedback and navigation are introduced when relevant. Gathering and the small crafting dependency are shown for the active errand, followed by shared activity and optional social tools. Deeper faction optimization, dungeon loops and endgame contracts are not added to the beginner hint queue. Their existing panels, rules and access remain intact. The journey ends naturally after main_03, level 20, or an acknowledged dismissal; recommended objectives remain available independently of beginner eligibility.

No global XP, damage, time-to-kill, item-quality or gold rebalance is made. The opening keeps the existing skill-training curve, quick early character levels, normal combat/drop rewards, rune improvement, crafting skill gains and quest payouts. The improvement is sequencing and legibility rather than reward inflation. Human first-hour pacing and subjective feel remain separate live checks.

## Guidance and recommendation rules

NewPlayerJourney.Recommend reads the authoritative owned-character snapshot, current zone and level, accepted/completed quests, prerequisites, cooldowns, visible foes/resources/chests, and claimable loot. It prioritizes one meaningful goal. Dynamic faction contracts resolve through the same EndgameLoops resolver as gameplay. Missing or stale optional targets fall back to real accepted quests or legitimate available leads. Navigation uses the actual exit graph and entry requirements; it does not teleport, unlock, accept or complete content. Crafting recommendations resolve intermediate recipes and missing gatherable materials. Death exposes recovery rather than hiding the journey.

Hints are contextual, bounded and acknowledged with Got it; successful real interactions also retire relevant explanations. Hint text resolves current keyboard bindings. Public activity is optional and geographically limited; inappropriate boss events are not advertised to fresh players. Existing nameplates already show character identity and level; the nearby-player control adds discoverable social access using only public snapshot information.

The HUD retains its existing scaling and layout framework. The compact objective includes activity, progress/action, approximate map direction/distance and reward; its detail tooltip preserves the full destination, reason and reward wording. Route and contextual actions use existing panels and command methods. A bounded progression queue avoids modal interruptions and prevents competing level/skill/reward notices from immediately overwriting one another. The first snapshot after login/reconnect establishes a baseline, never a fabricated level-up.

## Persistence and authority

No save-schema migration or progression reset is needed. Creation alone adds onboarding:v1:eligible to Character.Discoveries. Historical saves lack that key and deliberately remain outside the beginner hint sequence, including low-level existing characters. Missing discovery fields retain the model's safe empty default. Existing first_hour markers remain readable and are not reset.

Presentation keys use onboarding:v1:hint:<allowlisted-id>. Successful real interactions may record onboarding:v1:milestone:loot or equipment. The server alone records onboarding:v1:public_scheduled when it substitutes the normal eligible event slot. Client acknowledgement cannot create eligibility, a server milestone, contribution, XP, gold, reputation, items, quest completion or event rewards.

The guide_ack command accepts only a known hint ID and rejects extraneous gameplay parameters. It uses the ordinary validated, sequenced, receipted realm transaction and persistent character state. Repeated acknowledgements are HashSet-idempotent; replayed requests use existing receipts. No tutorial milestone pays any reward. Existing quest and public-event rewards are tested for replay/restart behavior through real command APIs. Public-event scheduling is bounded by the existing cadence and capacity; it waits for a reachable anchor outside nearby hostile aggro rather than forcing a dangerous tutorial encounter.

## Diagnostics and automated checks

The recommendation model exposes stage, target, destination and action; hint keys and milestones are visible in trusted save inspection. Native controls retain journey_stage, journey_target, guidance_id, nearby_count and progression_kind metadata for tests. No security-sensitive account fields or reward decisions are exposed by these presentation markers.

Run the dedicated probe after content generation:

```sh
python tools/build_content.py
dotnet run --project tools/new_player_probe -c Release -- content/catalog.json
```

The same runner is compiled into the existing world_probe and runs as a module-initializer check, keeping every retained world CI gate responsible for onboarding behavior. It exercises fresh recommendations, normal movement/combat/loot/socket/gather/craft/quest/transition commands, real equipment improvements, progression differences, missing/old-save compatibility, hint acknowledgements, adversarial payloads, receipt replay, restart, empty-server public discovery, normal public contribution rewards and noncontributor rejection. Controlled proximity and event-calendar fixtures bound test time; they do not claim an unassisted human playthrough. No tutorial reward exists to duplicate.

NewPlayerJourneyUiChecks extends the existing Godot PlayerExperienceContract at 1280x720 and 1920x1080, checking meaningful objective/hint markers, actual binding resolution, social discovery with zero nearby players, HUD placement, optional-event exit, old-character behavior and a progression-driven non-modal level card. Existing Windows compilation, native/UI acceptance, core/world/security/adversarial, live progression, transaction, public-event, dungeon and endgame gates remain required. Current evidence and handoff are updated only after exact implementation-head verification; this document alone is not a green-CI claim.
