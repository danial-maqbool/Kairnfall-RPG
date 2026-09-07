# World and content implementation

This task describes required work, not completed content.

## Scope and ownership

Own `content_src/`, `src/Kairnfall.Core/WorldMap.cs`, new world/content tests, and world/skill traceability documentation. Do not edit other server/core files, client files, art generators, or deployment files. Preserve stable content IDs and JSON schema because art and client workstreams use them.

## Required work

1. Inspect the existing five cities, settlements, biomes, four map layers, dungeons, exits, shops, resource distributions, and story chains. Fix unreachable or contradictory content. Preserve at least five major cities, ten smaller settlements, fifteen biomes, twenty dungeons, one hundred normal species, twenty-five elite variants, twenty bosses, sixty trainable skills, 450 items, 120 abilities, 150 named NPCs, and 100 side quests. Counts alone do not prove completion.
2. Make city layouts and surrounding routes physically distinct. Dawnreach is the civic plains capital; Emberhold is a mountain forge city; Thornhollow is an ancient-forest settlement; Frostgate is the northern fortress; Gloamport is the coastal trading city. Keep Wayfarer's Rest as the fixed start west of Dawnreach. Use meaningful landmarks and logical service placement. Do not fill the map with renamed duplicate regions.
3. Unify decorative solid-object placement with authoritative collision. Read the prop keys and current decoration rules in `client/Scripts/WorldView.cs`. Add shared `WorldMap.DecorationAt(ZoneDef zone, int x, int y)` returning a supported prop key or null. Add an explicit shared collision rule for solid trunks and rocks. Keep roads, exits, NPC interaction points, starting areas, and resource access usable. Do not put surface trees in underground moss areas. The client workstream will consume this shared API; document the required renderer change rather than editing the client here.
4. Prove real traversability with walkable-tile or path tests, not only abstract graph reachability. Check all city-to-city routes, reverse passages, dungeon floors, arrival clearance, resource access, and service interaction distances. Avoid unintended roads through building walls and visual/collision contradictions.
5. Validate quest objectives against actual RealmEngine progress events. Repair impossible targets, bad prerequisites, unavailable rewards, dead-end chains, repeated quests that cannot recur, and gathering/crafting requirements that cannot be obtained. Improve varied authored objectives and story context instead of satisfying counts with kill-ten copies.
6. Trace every skill to a legitimate repeatable training action, server-side XP award, gameplay effect, unlock, and client interaction. Create a precise matrix. Do not report a skill as functional merely because it exists in the catalog. For engine or UI gaps outside ownership, provide exact files, missing behavior, and reproduction in `docs/qa/SKILL_HANDOFF.md`.

## Evidence

Run deterministic content generation, core regression tests, and new world/content tests. Keep failed checks explicit. Write `docs/WORLD_BIBLE.md`, `docs/CONTENT_MATRIX.md`, and `docs/qa/WORLD_CONTENT_REVIEW.md` with actual results and remaining gaps. Commit tested changes to this branch. Do not merge, publish a release, enable paid services, modify billing, or bypass tool restrictions.
