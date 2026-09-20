# Task 22 — factions, reputation, and repeatable endgame loops

Task 22 enriches the existing Kairnfall world rather than expanding its footprint. The five authored city factions—Crown, Forge Clans, Circle, Wardens, and League—now expose deterministic veteran contract boards through their existing guild registrars.

## Daily rotation

Each faction offers three contracts per realm day. Across the rotation the board covers six existing gameplay systems: elite hunts, gathering supply musters, crafting orders, dungeon expeditions, boss writs, and public-event response. Targets are selected deterministically from existing creatures, resources, recipes, dungeons, bosses, events, cities, and wilderness regions. No new overworld region, dungeon footprint, or arbitrary faction is introduced.

Contract identifiers contain the rotation day and canonical target. The server regenerates and validates the expected contract before accepting it, so a client cannot forge targets or rewards. Accepted contracts use the existing persisted quest-progress dictionary; completed contract identifiers use the existing persisted completed-quest set. This keeps old saves compatible while making acceptance, progress, claims, restart recovery, and duplicate prevention server-authoritative.

## Reputation and rewards

Faction contracts grant 18–30 reputation depending on loop type, plus level-scaled gold. Reputation remains capped at 1000 and continues to feed the existing merchant pricing system. Canonical city factions now have persisted rank milestones at 250 Trusted, 500 Honored, 750 Revered, and 1000 Exalted reputation. Each milestone records an achievement and grants its gold bonus exactly once; the achievement is the idempotency key, so later reputation changes cannot duplicate the reward.

Normal authored quests and public events still use the same reputation store. Task 22 routes reputation changes through the shared helper so caps remain consistent; Wayfarer event reputation remains supported without inventing a new city board.

## Authority and anti-duplication

Faction contracts can only be accepted and claimed near the matching existing guild registrar and after the server verifies the character-level gate. Claims are atomic under `RealmEngine.Execute`: gold, reputation, rank milestones, completed state, and active-contract removal roll back together on any rule failure. Existing request receipts make network retries idempotent, while the completed contract identifier prevents a second fresh claim for the same daily contract.

Accepted progress survives realm-state roundtrips. A contract accepted before a daily rotation can still be resolved and completed afterward because its identifier contains the original deterministic rotation day and target.

## Player presentation

Guild registrar dialogue now shows the current faction board, objectives, level gate, gold, and reputation reward. Active veteran contracts appear in the normal quest tracker and can be claimed or abandoned there. The Achievements/Factions page now shows reputation rank, next threshold, and active/claimed rotation status for all five canonical boards.

## Automated coverage

`tools/world_probe/Task22EndgameChecks.cs` verifies:

- the unchanged 20-region / 2,048,000-tile Surface wilderness footprint;
- all five boards are anchored to existing faction guild registrars;
- six-day rotation covers elite, gather, craft, dungeon, boss, and event loops;
- generated contract IDs resolve deterministically;
- shared objective progress works for all six families;
- remote acceptance, incomplete claiming, duplicate claiming, and replay duplication fail safely;
- active progress survives save/reload and rotation rollover;
- faction-rank rewards are exact, persisted, and idempotent.
