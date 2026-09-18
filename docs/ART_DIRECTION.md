# Current character source: Wayfarer

Player bodies, hair, equipment overlays, NPCs and creatures now come only from the new Wayfarer construction in `tools/art/characters.py`, `character_motion.py`, and `wildlife.py`. Committed runtime atlases and source hashes are in `art/wayfarer/Assets`. The earlier actor implementation and counts below are historical, not the active renderer.

Base compatibility remains 64-pixel actors, 128-pixel bosses, four directions and eight frames for six states. Separate one-action atlases add interaction, crafting, running, bow draw/release and crossbow handling. The client keeps legs grounded during upper-body actions. Accepted server cues synchronize public actions without changing rewards, saves or combat authority.

The rejected actor PNGs and authored masters are deleted from the working tree. Legacy actor publishing is disabled. Git history is retained. Structural and native rendering results are not independent artistic acceptance or release approval.

---

# Pixel-art direction and review contract

Status date: **2026-09-16**. This document describes the active repository-side visual contract. It does not constitute human artistic approval.

## Grounded-2026 active actor direction

Grounded-2026 is the sole active runtime source for player bodies and hair, worn equipment overlays, NPC role sheets, and mobs. Historical Atelier actor bytes are not an actor fallback path: `tools/integrate_atelier.py` fails closed for actor groups and the permanent migration validator requires zero active historical actor fallbacks. Compatible historical Atelier material may still be used for non-actor groups such as terrain, buildings, props, items, resources, chests, structures, and abilities.

Actors retain the existing native pixel contract: 64-pixel player/equipment/NPC/mob frames, four directions (south, west, east, north), six states (`idle`, `walk`, `attack`, `cast`, `hit`, `death`), and eight frames per state/direction. The client keeps the existing integer foot anchor and nearest-neighbor presentation. Boss presentation may use the existing larger boss canvas where already authored; this migration did not change world collision or tile coordinates.

The active construction lives under `atelier/forge/grounded_*.py` and is routed through `tools/art/people.py` and `tools/art/fauna.py`. Humanoids use shared anatomical joints, clothing, hands, boots, equipment and weapon/tool construction. Creature renderers use anatomy-specific quadruped, humanoid, bird/drake, serpent/worm, insect/arachnid/crustacean, spirit/elemental, construct/mineral and mimic paths rather than transforming historical standing sprites. Construct/mineral/mimic families use the dedicated articulated heavy-body renderer.

At verified implementation baseline `7b11027ba913781443871ece56c8ab13008408d5`, permanent Grounded actor acceptance run `35103673162` succeeded. The runtime set contains **1,245 active actor sheets** and **239,040 nonblank state/direction/frame cells**. The structural motion contract covers **5,322 anatomy-appropriate motion checks**, proves **1,237 historical actor hashes were replaced**, and requires **zero actor fallbacks**. The associated exact-head artifact is `grounded-actors-7b11027ba913781443871ece56c8ab13008408d5` (`10450285632`, SHA-256 `dd15ff16cc16dae7c32faecb25aac1bd2b586309310126635f413633ade86964`). The measured active actor PNG footprint is 21,305,167 bytes from the verified Grounded pack measurement; this is a footprint measurement, not a quality score.

## Required visual standard

Pixel art must be based on recognizable anatomy and real object construction. Different hashes alone do not establish different anatomy, and a duplicate warning must never be repaired with a meaningless pixel or invisible mark.

Use deliberate pixel clusters, controlled material ramps, consistent upper-left lighting, and nearest-neighbor presentation. Animals should remain identifiable with names hidden. Weapons should show working silhouettes and fittings; armor should preserve shared body anchors without floating, clipping, or swapping left/right lighting. Movement, action, hit and death states must produce meaningful silhouette or joint changes rather than static standing frames with cosmetic noise.

Review rats and mice for muzzle/tail proportions; rabbits for ears and folded hind legs; birds for beaks, wing feathers and feet; bats for finger-supported membranes; insects for six legs and body segmentation; spiders for eight legs; snakes for coherent coils; snails for shell and muscular foot; fish for fins; turtles and tortoises for appropriate limb construction. Fantasy creatures must retain coherent anatomy. Metal, wood, cloth, leather, stone and bone should read through material-specific edges, seams, straps, facets and joints at native scale.

## Migration and review gates

`tools/validate_grounded_actor_assets.py` is the permanent actor-migration contract. It verifies exact catalog coverage, RGBA/grid dimensions, nonblank frames, action/death motion, source-wrapper routing, historical-hash replacement and zero fallback. `VisualPresentationContract` and the Visual acceptance matrix render representative player, equipment, NPC and mob states in Godot rather than relying only on generated sheets. The first-hour migration manifest is `docs/ASSET_MIGRATION_FIRST_HOUR_UI.md`.

Automated rendering and structural checks do **not** approve artistic taste, animation feel, readability at a person's physical monitor distance, or the overall game-wide art direction. Independent human inspection of in-engine animation, clipping, foot sliding, lighting consistency, native-size readability and subjective quality remains required before release approval.

Release status: **NOT APPROVED — human acceptance remains.**
