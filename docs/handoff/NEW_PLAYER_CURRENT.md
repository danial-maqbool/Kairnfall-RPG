# New-player experience — current implementation

Status: **2026-09-15**.
Verified source: **4214c57692bd70196f4c50db0a95ca6f2a510f31** on `main`.
Evidence authority: `docs/handoff/CURRENT_EVIDENCE.json`.
Release status: **NOT APPROVED — human acceptance remains.**

## Player-facing sequence

A fresh character enters the real Wayfarer's Rest settlement with the existing starter equipment. The objective card names the innkeeper, shows the actual quest/reward and supplies a normal walkable route. Movement and interaction hints use current bindings. Once the introductory quest is accepted, a suitable starter foe may introduce targeting and held basic attack; the quest remains available when no foe is present.

Owned loot leads to the backpack. Actual usable upgrades are identified by item and derived-stat comparisons; the player chooses whether to equip. The existing rune and trainer quest provide a deterministic equipment improvement. The workshop errand explains its necessary oak-log to oak-plank to wooden-handle dependency before the blacksmith conversation and ordinary quest claim. Real skill/character changes produce a short non-modal feedback queue. The sealed letter and legitimate exit graph direct the character through Kingsmeadow toward Dawnreach and the next quest.

An eligible Kingsmeadow newcomer may encounter the existing treasure-surge activity in one normal public-event slot. The event remains shared and uses normal contribution, scaling, reward and aftermath rules. It is optional and solo-functional. The nearby-traveler control opens existing social tools, names only public snapshot information, and truthfully displays zero when no other players are nearby.

## Source map

| Responsibility | Existing or extended source |
| --- | --- |
| Recommended objective, eligibility, hints, legitimate navigation | `src/Kairnfall.Core/NewPlayerJourney.cs` |
| Actual stat differences and usable upgrade comparison | `src/Kairnfall.Core/ProgressionFeedback.cs` |
| Reward-neutral acknowledgement and existing-event scheduling preference | `src/Kairnfall.Core/RealmOnboarding.cs`, `RealmEngine.cs`, `RealmEvents.cs` |
| Objective card, optional social access, level/gear feedback, adaptive placement | `client/Scripts/GameRoot.NewPlayer.cs` and existing HUD/panel partials |
| Real gameplay-API journey and adversarial state checks | `tools/new_player_probe/NewPlayerJourneyProbe.cs` |
| Native readable-hint and collision matrix | `client/Tests/NewPlayerJourneyUiChecks.cs`, called by `PlayerExperienceContract` |
| Native real-server acknowledgement/reconnect checks | `client/Tests/LiveExperienceContract.cs` |
| Exact-head permanent CI | `.github/workflows/new-player-journey.yml` |
| Verified evidence and anti-staleness guard | `tools/documentation_contract.py`, `tests/handoff/test_onboarding_evidence.py` |

## Persistence and safety

Creation-only `onboarding:v1:eligible` opts in new characters. Missing eligibility deliberately excludes old characters, even at low levels. Existing `Character.Discoveries` storage provides safe empty defaults and persists allowlisted hint acknowledgements and server-observed milestones without resetting old `first_hour` progress.

`guide_ack` is a presentation command, not a reward or event-credit command. It rejects gameplay payload fields and uses ordinary sequenced, receipted character transactions. Repeated acknowledgement is idempotent. Neither a hint nor its acknowledgement can change XP, levels, inventory, gold, reputation, quest completion or event contribution. No tutorial reward was added. Existing quest claims and event rewards are covered by replay/restart and noncontributor tests.

## Verified completion and remaining boundaries

The 13 functional workflows at the stated implementation baseline passed, including the permanent journey runner, Windows compilation, native layout/input, clean package/reconnect, full retained world checks and Task 20/21/22 regressions. `NEW_PLAYER_VERIFICATION.md` records exact runs and repaired failures. Handoff synchronization follows, rather than precedes, this verification; documentation delivery is checked at its own exact main head.

No authored `content_src` file changed relative to starting main `dff9f170f25f44c8ae024e8d94133f72d63f6446`. There are zero new overworld regions, no economy rebalance and no production changes. Temporary candidate/edit/overlay workflows and request files are removed. The previous Task 22 current-evidence document is preserved byte-for-byte as `TASK22_EVIDENCE.json`, with older history unchanged.

Do not start another task automatically. Manual/live acceptance remains after repository work; automated reachable-proximity fixtures and native tests are not human timing, retention, physical hardware or artistic approval.
