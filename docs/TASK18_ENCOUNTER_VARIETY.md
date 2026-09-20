# Task 18 — Enemy Variety, Elites, Rare Spawns, and Mini-Bosses

Task 18 reuses the existing Kairnfall geography and the existing 25 elite templates rather than adding land or cloning stat-only enemies.

Six established rare templates become regional champions with recognizable names and one additional real combat mechanic drawn from the authoritative telegraph engine. All 25 elites retain their existing mechanical trait families. Regional elite hunting sites are anchored near existing landmarks when possible and are presented as patrol or ambush encounters.

Optional non-starter rares no longer appear permanently on a fresh realm. Their first appearance is deterministic and delayed; subsequent rare respawns use deterministic 6–9 minute windows, while champions use 10–15 minute windows and larger clear-reset radii. The required first-hour `rare_hay_golem` remains immediately available with its historical 90-second cadence so critical progression is never blocked by rare timing.

Champion rewards use bounded increases to existing XP/gold and existing loot templates. The server still owns kill credit, loot ownership, bestiary credit, cooldown state and respawn state. Replay/duplicate requests cannot create a second death generation or reward pile. Dead rare cadence is repaired on restart if a kill was saved before the first simulation tick.

Automated coverage validates unchanged overworld footprint, exactly one regional elite template per surface wilderness region, six mechanically distinct champions, deterministic spawn/cooldown behavior, two-player kill credit, exactly-once reward creation, restart persistence and clean reset behavior.
