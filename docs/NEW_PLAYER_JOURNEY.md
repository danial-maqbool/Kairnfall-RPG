# New-player experience — journey and early retention

## Scope and audited starting state

This pass joins guidance, real progression feedback and optional public activity in the existing persistent world. It adds no region, tutorial instance, quest reward, currency source, character-level modifier, faction skip or production infrastructure. Existing Task 20 event rules, Task 21 dungeon/boss behavior and Task 22 endgame prerequisites remain authoritative. The first-15-minute and first-hour windows below describe intended play, not measured human completion times or retention results.

A new character starts at Wayfarer's Rest with the class weapon and armor equipped, usable backpack tools, potions, a starter rune and one weapon socket. A Place by the Fire is the existing innkeeper quest: gather three oak logs, craft a wooden handle through the oak-plank intermediate recipe, and speak to the blacksmith. A Spark in the Stone already teaches the rune upgrade. The sealed letter leads through Kingsmeadow to the Dawnreach traveler. The prior checklist exposed gathering/crafting before combat, repeated for established characters, mixed stale keyboard instructions with current bindings and lacked a single actionable route. Public-event text competed with the location heading and notifications were not adequately restricted to nearby appropriate activity.

The audit included the starting spawn, nearby NPCs and weak field rat, quest prerequisites/rewards, existing starter loadout and inventory, sawbench recipes/materials, exit routes and map, death recovery, XP indicators, social/nameplate information and normal public-event scheduling. The repair reuses those systems instead of creating disconnected tutorial content.

## Designer-facing opening sequence

1. **Arrival:** enter the shared settlement. The expanded objective names the actual innkeeper and provides the quest context, reward preview and walkable route. A short movement/interaction hint resolves the player's current bindings.
2. **First purpose and combat:** accept the workshop errand. A nearby authored starter rat or other suitable weak foe offers optional practice. Targeting and held basic attack are explained in context. When no suitable foe exists, the quest stays actionable rather than waiting for a respawn or another player.
3. **Loot and gear:** a real kill and owned loot lead to backpack discovery. Normal combat XP and drops are unchanged. A usable, non-regressive upgrade is flagged only when real item and derived-stat comparisons agree. The player chooses Equip; receiving an item never auto-equips it.
4. **First dependable power improvement:** use the existing starter rune and trainer quest. Feedback describes actual changed equipment stats, not an invented power score. Continue the active workshop objective through oak logs, oak planks and the wooden handle, with the required intermediate recipe made explicit.
5. **Quest payoff:** speak to the blacksmith and claim the quest normally. The feedback queue identifies actual rewards and earned skill/character changes. Character-level feedback states the new level and real maximum-health gain; ability notices use actual requirements.
6. **Next destination:** follow the sealed letter through the legitimate exit graph toward Dawnreach. The action marks the next local waypoint and uses ordinary walking. It neither teleports nor bypasses entry requirements. The map and journal remain available.
7. **Shared world:** an eligible Kingsmeadow newcomer may encounter the scheduler's existing treasure-surge event in one normal event slot. It uses shared contribution, scaling, reward ledger and aftermath rules. Grouping and another human player are not required. Not now returns to the quest route without granting credit or rewards.
8. **Reason to continue:** reach Dawnreach and continue The Letter on the Road. Nearby-player awareness opens existing social tools and accurately reflects a populated or empty area. The existing rare hunt and deeper systems retain their true level/quest gates.

For the intended first 15 minutes, emphasize arrival, a clear errand, a safe combat opportunity, loot, the rune/equipment explanation and a visible reward or skill/level gain. During the remainder of the intended first hour, emphasize completing the small crafting chain, claiming the quest, reaching the next settlement and discovering optional shared activity. The order adapts to legitimate character state, nearby targets and player choices; it is not a timed script.

## Progression audit and feedback

The existing progression curve is preserved. Skill level 2 requires 90 skill XP. Character XP is the actual sum of awarded skill XP; level 2 requires 100 total XP and level 3 requires 220. Training across different skills can therefore advance character level independently of any one skill milestone. The existing early character-level cost is `100 + 20 * (current level - 1)` below level 20. Class affinity, challenge adjustment and fractional award carry remain unchanged.

The real derived maximum-health formula includes `3 * character level`, so an otherwise unchanged character gains three maximum health on a level-up. Feedback compares real before/after character state and shows that gain rather than implying every stat increased. Equipment comparisons account for actual power, armor, rarity, durability, runes/affixes, usability and resulting derived-stat differences. Non-equipment items and misleading or regressive swaps are not called upgrades.

Several existing reward moments become legible: normal combat/loot, skill growth, character growth, the starter rune, gathering/crafting success, the introductory quest payout and the next settlement/activity. No global XP, damage, time-to-kill, item-quality or gold rebalance is made. The probe confirms these rewards can be reached using real gameplay commands; it does not measure unassisted human time-to-kill or prove economy/retention feel.

A bounded six-second progression queue avoids modal interruptions and immediate overwriting of skill, level, equipment and reward notices. The first snapshot after login/reconnect establishes a baseline and never fabricates a level-up. Equipment remains a deliberate player action through the existing inventory UI.

## Guidance, fallback and gradual system exposure

`NewPlayerJourney.Recommend` reads authoritative owned-character snapshots, zone/level, accepted and completed quests, prerequisites, cooldowns, visible targets/resources/chests and owned claimable loot. It prioritizes one meaningful goal. Dynamic faction contracts resolve through the same endgame resolver as gameplay. Missing or stale optional targets fall back to accepted quests or legitimate available leads. Crafting recommendations resolve intermediate recipes and missing gatherable materials. Death exposes recovery rather than making the journey disappear.

Hints are contextual and bounded. Got it acknowledges an explanation; successful real movement or interactions can also retire it. Input labels resolve current bindings. Important objective details answer what to do, where to go, why it matters and what the authored reward will be. The route is recalculated when clicked to avoid acting on stale targets. No recommendation accepts, unlocks, completes or rewards content by itself.

Movement, interaction, quests and a weak-foe combat opportunity come first. Backpack, gear, the rune, leveling and navigation follow when relevant. Gathering/crafting are introduced for the real errand; shared activity and social tools stay optional. Deeper faction optimization, dungeon loops and endgame contracts are not added to the beginner hint queue. Their existing panels and legitimate access remain available through Menu. Beginner hints end naturally after main_03, level 20 or acknowledged dismissal, while useful recommendations remain independent of tutorial eligibility.

## Multiplayer introduction

Existing nameplates already show public character identity and level. The nearby-traveler control adds visible social access using only snapshot-visible character names, level, class and party status; no private account/contact data is added. A truthful zero count explains that the journey works solo. Existing chat, parties, friends and LFG remain optional and discoverable.

Activity awareness filters by geography, active state and appropriate participation context. The newcomer scheduler preference uses server-owned creation, quest, zone, level, combat and public-event state, not hint acknowledgements. It replaces one normal scheduled event rather than adding a parallel event timer, reward pool or requestable spawn API. Reachable placements outside nearby hostile aggro are preferred; an unsafe placement waits rather than forcing a dangerous encounter. Contributions and all rewards still belong to the existing public-event authority and ledger.

## Windows UI and accessibility

The existing HUD, fonts, input map and scaling framework are extended, not replaced. The objective card contains one activity, progress/action, approximate map direction/distance and reward context; its hover details preserve full destination, reason and reward text. At short logical viewports the same card moves below the minimap. Compact layouts retain a full map button and a Menu entry for every previous navigation destination instead of a colliding multi-button grid. Text and action labels supplement color.

Native tests cover 1024x720 at native content scale, and 1280x720/1920x1080 at 100%, 125% and 150% content scale, each with 100% and 125% text scale: fourteen combinations. Wrapped hints reserve actual scaled-font glyph height. Welcome/reward notices reserve two rows above the resource meter in both desktop and compact layouts. Tests check readable lines, containment and separation from chat, minimap, target frame, hotbar, navigation and combat controls. Frames are also inspected because metadata-only assertions previously missed an invisible hint.

## Persistence and server authority

No save-schema migration or progression reset is needed. Creation alone adds `onboarding:v1:eligible` to `Character.Discoveries`. Historical saves lack that key and intentionally stay outside beginner hints, including low-level old characters. Missing discovery fields use the model's safe empty default. Existing `first_hour` markers remain readable and are not reset.

Presentation acknowledgements use `onboarding:v1:hint:<allowlisted-id>`. Successful real actions may record `onboarding:v1:milestone:loot` or equipment. The server alone records `onboarding:v1:public_scheduled` for the normal eligible event slot. A client cannot acknowledge its way into creation eligibility, server milestones, event contribution, XP, gold, items, reputation, quest completion or unlocks.

The `guide_ack` command accepts only a known hint ID, rejects unrelated gameplay payload fields and passes through the ordinary validated, sequenced, receipted realm transaction and persistence rules. Repeated flags are HashSet-idempotent; replayed requests use existing receipts. **No tutorial milestone pays any reward.** Existing quest/public-event rewards remain exactly-once where required and are tested for replay/restart behavior through normal command APIs.

## Diagnostics and automated coverage

The recommendation model exposes stage, target, destination and action. Trusted save inspection can inspect bounded hint and milestone keys. Native controls expose `journey_stage`, `journey_target`, `guidance_id`, `nearby_count` and `progression_kind` for automated checks, without security-sensitive account information or client reward authority.

Run the dedicated probe after content generation:

```sh
python tools/build_content.py
dotnet run --project tools/new_player_probe -c Release -- content/catalog.json
```

The same runner is compiled into the retained world probe. Its twelve groups cover fresh legitimate recommendations, nonempty normal progression, real movement/combat/loot/socket/gather/craft/quest/transition APIs, real equipment improvement and level feedback, old/missing-save defaults, hint persistence, adversarial acknowledgements, reward neutrality, receipt replay/restart, optional-target/death fallback, solo public discovery/contribution/reward, noncontributor rejection and unchanged world footprint. Controlled clocks and reachable proximity fixtures keep it bounded without pretending to be an unassisted human playthrough.

`NewPlayerJourneyUiChecks` extends native `PlayerExperienceContract`; `LiveExperienceContract` covers generated native input against a real disposable server and PostgreSQL, including guidance persistence and reconnect. The permanent `New-player journey` workflow checks exact main source and retains logs/screenshots. Existing Windows, core/world/security/adversarial, graphical progression/multiplayer, transaction, public-event, dungeon and endgame suites remain required.

Verified implementation and exact run evidence are in `docs/handoff/CURRENT_EVIDENCE.json` and `docs/handoff/NEW_PLAYER_VERIFICATION.md`. Current evidence is promoted only after implementation-head functional success; documentation delivery receives its own checks. Human first-hour pacing, uncoached usability and retention improvement remain unmeasured, and release approval is separate.
