# First-hour art and UI migration manifest

Status date: 2026-09-16. This is repository-side migration evidence, not human artistic or usability approval.

## Active actor migration

Grounded-2026 is the sole active runtime source for player bodies/hair, equipment overlays, NPC roles and mobs. Historical Atelier actor bytes are fail-closed and actor fallback count is zero. The active grid is six real states (`idle`, `walk`, `attack`, `cast`, `hit`, `death`) × four directions × eight frames.

| Family | Active sheets | Runtime policy |
| --- | ---: | --- |
| Player bodies | 12 | Grounded-2026 procedural construction |
| Player hair | 48 | Grounded-2026 procedural construction |
| Equipment overlays | 1014 | Grounded-2026 articulated overlays |
| NPC role sheets | 26 | Grounded-2026 humanoid role construction |
| Mob sheets | 145 | Grounded-2026 beast/spirit constructions |
| **Total** | **1245** | **239040 nonblank state/direction/frame cells validated** |

The permanent `tools/validate_grounded_actor_assets.py` contract verifies exact active coverage, RGBA/grid dimensions, nonblank cells, motion-distinct action/death states, manifest hashes, rejected historical hashes, and zero actor fallback. The source wrappers are `tools/art/people.py` and `tools/art/fauna.py`; articulated construction lives under `atelier/forge/grounded_*.py`. Clean regeneration therefore cannot silently restore the replaced actor families.

## Non-actor sprite direction

Non-actor art was retained where it already fits the coherent pixel presentation rather than churned cosmetically. Atelier integration remains active only for compatible non-actor groups: `{"abilities": 132, "buildings": 164, "chests": 14, "items": 1426, "props": 23, "resources": 41, "structures": 5, "terrain": 52}`. Terrain, props, buildings, resources, chests, structures, item icons and ability presentation remain covered by the permanent visual/game-asset validators and native review matrices. Newly introduced opening-reward icons are generated project art when no historical Atelier source exists and are explicitly counted by the full runtime coverage audit.

## UI migration

The existing Task 12 modal/focus/input architecture is preserved. `PageLayoutProfiles` now controls real window geometry and purpose summaries. Permanent Windows tests cover all existing pages at 1024×720, 1280×720, 1920×1080 and 2560×1440 across supported text scales, with additional content-scale emulation and keyboard/mouse/focus/error-state assertions.

## Human-only gates

Automated coverage does **not** assert artistic taste, animation feel, human onboarding duration/retention, physical Windows monitor DPI, or subjective usability/readability. Those remain explicit human acceptance gates; repository-side implementation and integrity checks do not convert them into approvals.
