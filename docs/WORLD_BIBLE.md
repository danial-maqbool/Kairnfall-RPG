# World implementation and verification guide

Local repair `922d429` gives building masonry precedence over roads, connects
door approaches, and relocates obstructed NPCs and Thornhollow stairs. The local
test wrapper runs `tools/world_probe` across actual actor-fitting tile paths.
Its 949 tested destinations do not cover every resource, quest objective, or boss.

The required geography and identities are in accepted requirements R10-R12 and R16-R18.
The authored source is `content_src/world.py`, `content_src/mobs.py`, and `content_src/quests.py`.
The catalog is generated. Do not hand-edit it as the only fix.

The masonry-priority repair includes a narrow saved-position recovery: coordinates
valid under the historical road geometry but now blocked move to a nearby connected
walkable point. Valid positions and non-position data are retained, including saved
creature homes, structures/nodes, chests, and loot. Corrupt character coordinates
outside that geometry change still reject startup. The world probe verifies saved
progress preservation and repeated-load stability alongside fresh-world routes.

Wayfarer's Rest is the fixed starting village west of Dawnreach.
Dawnreach, Emberhold, Thornhollow, Frostgate, and Gloamport must each provide distinct city architecture,
services, inhabitants, quests, secrets, travel routes, and nearby encounters.
Surface, Deepways, Umbral Depths, and Aether Rift need actual connected entrances and exits.

During local QA, derive the zone graph from the catalog and verify every required destination.
Then verify walkable tile paths between each spawn, exit, NPC/service, boss arena, and quest objective.
A graph edge is not sufficient if terrain or a building blocks the route.
Test return paths, death/respawn destinations, layer changes, exploration discovery, and fast-travel locks.

Measure content density, landmarks, road readability, travel time, resource distribution, encounters, and biome transitions.
Do not count empty large regions as complete world content. Do not count five reskinned copies as distinct cities.
Record scene captures, routes tested, inaccessible points, repaired coordinates, and exact source revision.
