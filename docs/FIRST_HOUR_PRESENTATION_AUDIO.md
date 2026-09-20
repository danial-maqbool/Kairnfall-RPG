# First-hour presentation and audio pass

The first-hour vertical slice is deliberately layered on the authoritative game instead of creating a separate tutorial mode. `FirstHourExperience` records successful real actions in the character's existing discovery state, while the normal quest tracker remains visible.

The Wayfarer's Path sequence is: movement → NPC → gathering → crafting → combat → skill level → character level → equipment improvement → building entry → map transition → social exposure → rare mini-boss. Existing Wayfarer's Rest interiors, `main_01`, `starter_rune`, the road to Kingsmeadow, and the existing `rare_hay_golem` provide the playable content. `starter_hunt` contextualizes the rare enemy after the first main-quest delivery.

Presentation changes keep navigation sparse: named entrances remain proximity-based, the minimap distinguishes exits from its single route waypoint, atlas details list immediate connections, starter building labels read at a practical distance, and elite creatures use a gold `RARE` health treatment. City/interior tint identities and location lore provide environmental character without adding full-screen markers.

The deterministic runtime audio pack now contains 96 WAV files across music, biome/interior ambience, footsteps, weapon impacts, creature vocals, eight class cues, and interface/celebration effects. Runtime routing includes combat-vs-boss music priority, biome/city ambience, surface footsteps, weapon identity, creature hurt/death vocals, class casts, loot, quest completion, skill-up, level-up, transition and event feedback.

`tools/audio_quality_audit.py` validates exact coverage, format, duration, levels, clipping, DC offset, loop-boundary continuity and payload uniqueness. These automated checks **do not** certify composition, mix, transition feel, human listening quality, artwork quality, or normal-play feel; those remain explicit human acceptance gates.
