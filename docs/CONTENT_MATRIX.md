# Content acceptance matrix

## Current hunting and underground coverage — 2026-09-09

The integrated world seeds 4,682 creatures across 109 regions. Ordinary species use 30x/20x/15x/10x/5x level-banded spawn counts in separated reachable patches. Interiors and service cores remain protected; bosses and elites are not multiplied. Wayfarer's Burrows and Silkroot Den add reciprocal beginner dungeon routes and reuse real existing bosses. The latter also connects to the Dawnreach Deepway. Over-level ordinary beginner dungeon slots are corrected with owned-pet and boss-state preservation. Current equipment-template and recipe counts remain 1,354 and 1,286. [Details](HUNTING_AND_JOURNEY.md) and [verification](handoff/HUNTING_AND_PRESENTATION_2026-09-09.md). Older count statements below are scoped to their original revisions.

## Equipment coverage — 2026-09-09

[Complete gear tracks](EQUIPMENT_PROGRESSION.md): 21 skill tiers, 51 families and 1,071 tracked entries. Generated totals are 1,354 item templates and 1,286 recipes. All original 530 templates and 463 recipes are retained unchanged. Each new track has server-tested equip/craft behavior and reachable supplies. These counts do not prove artwork, economy pacing or full-world completion. [Acceptance evidence](handoff/EQUIPMENT_PROGRESSION_2026-09-09.md).

Latest bounded repair: [action presentation and native UI](handoff/ACTION_PRESENTATION_2026-09-08.md).
No classes, quests, items, zones, rewards, or creature records were added in this pass.
Spider/quartz-spider and turtle/tortoise attack/hit presentation changed. Short action playback,
ability-browser lifecycle, hotbar framing, and objective feedback were repaired.
Status: implemented, automatically tested, and graphically rendered. Individual artwork
acceptance, the complete roster review, and full manual gameplay remain open.

### Previous Windows checkpoint

The [September 8 visual checkpoint](handoff/LOCAL_VISUAL_REVIEW_2026-09-08.md)
changes presentation and existing NPC positions without increasing scope or
content counts. Current path probes cover 107 zones and 1,013 destinations.
Eight common creatures and eight equipment families have sampled native render
evidence; this is not acceptance of every species, boss, ability or item.
The counts and failures in the September 7 paragraph below are historical.

The [2026-09-07 Windows record](handoff/LOCAL_ACCEPTANCE_2026-09-07.md) reports
source `922d429`: generated records include 530 items, 132 abilities, 103 zones,
170 NPCs, and 166 quests. These remain records, not accepted finished content.
World checks passed for 949 spawn/door/NPC/exit/arrival destinations across 103 zones;
resource, quest-objective, and boss-arena paths still require coverage.
Actual creature review failed anatomy/direction/boss-distinction requirements.

Counts below are minimum acceptance targets from the user's specification, not verified finished content.
Regenerate the current catalog and record its counts and hash in each test report.

| Content | Target | Required evidence beyond a count |
| --- | ---: | --- |
| Classes | 8 | Distinct mechanics, progression, equipment affinity, and playable kit. |
| Trainable skills | 60 | Valid action, XP, effect, unlock, interface, persistence. |
| Player abilities | 120 | Distinct functional effects and valid targeting/cost/cooldown. |
| Item templates | 450 | Acquisition, stats, art, usable category, requirements. |
| Weapons / armor | 100 / 100 | Useful family/slot/material variation and aligned equipped appearance. |
| Normal species / elites / bosses | 100 / 25 / 20 | Distinct anatomy, behavior, placement, encounters, drops. |
| Major cities | 5 | Different cities, complete services, roads, NPCs, quests, visuals. |
| Smaller settlements | 10 | Reachable and useful locations, not renamed empty maps. |
| Biomes / major dungeons | 15 / 20 | Different environments, connected routes, encounters, objectives. |
| Named NPCs | 150 | Role, dialogue, location, interactions, purpose. |
| Main / side / repeatable quests | 25 / 100 / 30 | Accessible objective chains and valid nonduplicated rewards. |
| Map layers | 4 | Surface, Deepways, Umbral Depths, Aether Rift with physical links. |

For each row, track source count, implemented behavior, automated tests, graphical review,
normal-play evidence, unresolved defects, and reviewed commit separately.
Do not copy historical catalog totals from another branch. Do not declare content complete from IDs alone.
