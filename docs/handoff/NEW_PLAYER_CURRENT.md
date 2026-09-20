# New-player experience — current implementation

Status date: **2026-09-16**.  
Verified implementation source: **`7b11027ba913781443871ece56c8ab13008408d5`** on `main`.  
Evidence authority: `docs/handoff/CURRENT_EVIDENCE.json`.  
Release status: **NOT APPROVED — human acceptance remains.**

## Player-facing opening

A newly created eligible character begins a bounded opening in the existing shared world. Bren Gale gives the first purpose, two Field Rats establish authoritative combat completion, and the server grants one deterministic class-compatible Rare Roadwarden weapon plus the ingredients for the craft lesson. The player equips the weapon through the normal Inventory action, brews Healing Potion recovery consumables through ordinary Crafting, returns to Bren, and is handed into Kairnfall's normal quest/travel/social world.

The eight class reward identities are distinct and skill-compatible: Vanguard Longsword, Berserker Greataxe, Ranger Recurve, Rogue Dirk, Arcanist Focus Staff, Warden Thornstaff, Templar Flanged Mace, and Spellblade Arming Sword. The reward is never auto-equipped. Full inventory is an atomic recoverable failure; replay cannot duplicate the grant; and the mandatory reward remains protected/recoverable until the equip milestone is established.

Death/respawn, reconnect, realm restart and valid out-of-order actions retain server-owned milestones. Established characters are not reset or silently re-enrolled, and historical `first_hour` markers remain compatible. The opening is an intended early-session route, not a measured twenty-minute human benchmark.

Kairnfall's multiplayer nature is visible through the existing Nearby Travelers/social/chat/party/group-finding surfaces and normal shared activity. Empty nearby population is represented truthfully; no fake player or tutorial-only multiplayer system is introduced.

## Art and UI state

Grounded-2026 is the sole active actor runtime source for player bodies/hair, equipment overlays, NPC roles and mobs. The permanent migration contract verifies 1,245 active actor sheets, 239,040 frame cells, 1,237 replaced historical actor hashes, anatomy-appropriate motion and zero actor fallbacks. Historical Atelier use is restricted to compatible non-actor groups. See `docs/ASSET_MIGRATION_FIRST_HOUR_UI.md` and `docs/ART_DIRECTION.md`.

The existing Task #12 modal/focus/input architecture remains intact. `PageLayoutProfiles` drives real page geometry and purpose summaries. Native Windows acceptance exercises 1024×720, 1280×720, 1920×1080 and 2560×1440, supported text scales, keyboard/mouse navigation, modal blocking/focus restoration, overflow, stale-state dismissal, settings persistence and non-color-only error feedback.

## Source map

| Responsibility | Active source |
| --- | --- |
| Opening authority, eligibility, milestones and reward mapping | `src/Kairnfall.Core/OpeningJourney.cs` |
| Authored opening content and eight reward identities | `content_src/opening_journey.py` |
| Existing broader recommendation/handoff journey | `src/Kairnfall.Core/NewPlayerJourney.cs` |
| Opening dialogue/objective/UI integration | `client/Scripts/GameRoot.Opening.cs`, `GameRoot.Panels.cs`, `GameRoot.NewPlayer.cs` |
| Page geometry/accessibility/modal protections | `client/Scripts/PageLayoutProfiles.cs`, `GameRoot.UiUx.cs` |
| Active actor construction | `atelier/forge/grounded_*.py`, `tools/art/people.py`, `tools/art/fauna.py` |
| Opening authority/progression probes | `tools/world_probe/OpeningJourneyChecks.cs`, `tools/new_player_probe/NewPlayerJourneyProbe.cs` |
| Native journey/layout/live-server contracts | `client/Tests/*Contract.cs`, `client/Tests/NewPlayerJourneyUiChecks.cs` |
| Permanent exact-head CI | `.github/workflows/new-player-journey.yml`, `.github/workflows/grounded-actor-acceptance.yml` and retained acceptance workflows |
| Anti-stale evidence guard | `tools/documentation_contract.py`, `tests/handoff/test_onboarding_evidence.py` |

## Verified repository-side state

All **14** evidence-required technical workflows completed successfully at exact implementation SHA `7b11027ba913781443871ece56c8ab13008408d5`. The permanent New-player journey run passed 12/12 retained journey groups, 5/5 opening groups across 8/8 classes, 442 native player-experience checks, 1,169 native control/layout checks and 125 real-server/PostgreSQL live checks. Grounded actor, Visual matrix, Windows package/display/input, graphical multiplayer, load, progression, security, adversarial, transaction and release-operations acceptance also passed at that same SHA. Exact run IDs are recorded in `NEW_PLAYER_VERIFICATION.md` and `CURRENT_EVIDENCE.json`.

The implementation adds zero overworld regions and no deployment or production-infrastructure change. The only authored `content_src` delta from starting main `dff9f170f25f44c8ae024e8d94133f72d63f6446` is `content_src/opening_journey.py`. Temporary candidate/repair/diagnostic workflows are removed; `main` remains the only persistent branch.

Human first-hour timing/retention, subjective usability and balance, independent artistic approval, audio listening approval, physical Windows DPI/hardware input and production-capacity claims remain outside automated acceptance and are still required where applicable.
