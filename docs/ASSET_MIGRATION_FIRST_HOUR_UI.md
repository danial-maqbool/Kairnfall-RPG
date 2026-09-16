# First-hour art and UI migration manifest

Status date: **2026-09-16**. Verified implementation baseline: **`7b11027ba913781443871ece56c8ab13008408d5`**. This is repository-side migration evidence, not human artistic or usability approval.

## Active actor migration

Grounded-2026 is the sole active runtime source for player bodies/hair, equipment overlays, NPC roles and mobs. Historical Atelier actor bytes are fail-closed and actor fallback count is zero. The active grid is six real states (`idle`, `walk`, `attack`, `cast`, `hit`, `death`) × four directions × eight frames.

| Family | Active sheets | Runtime policy | Measured PNG bytes |
| --- | ---: | --- | ---: |
| Player bodies + hair | 60 | Grounded-2026 procedural humanoid construction | 1,649,840 |
| Equipment overlays | 1,014 | Grounded-2026 articulated overlays | 12,726,680 |
| NPC role sheets | 26 | Grounded-2026 humanoid role construction | 2,180,429 |
| Mob sheets | 145 | Grounded-2026 anatomy-specific creature construction | 4,748,218 |
| **Total** | **1,245** | **239,040 nonblank state/direction/frame cells validated** | **21,305,167** |

The permanent `tools/validate_grounded_actor_assets.py` contract verifies exact active coverage, RGBA/grid dimensions, nonblank cells, motion-distinct action/death states, manifest hashes, rejected historical hashes and zero actor fallback. It performed **5,322 anatomy-appropriate motion checks** and verified **1,237 historical actor hashes were replaced**. The active source wrappers are `tools/art/people.py` and `tools/art/fauna.py`; authored construction lives under `atelier/forge/grounded_*.py`. Clean regeneration therefore cannot silently restore historical actor families.

Exact-head Grounded actor acceptance run **`35103673162`** succeeded. Its retained artifact is `grounded-actors-7b11027ba913781443871ece56c8ab13008408d5` (artifact `10450285632`, 24,799,957 bytes, SHA-256 `dd15ff16cc16dae7c32faecb25aac1bd2b586309310126635f413633ade86964`). The artifact includes logs, measured footprint data and native-size Godot presentation evidence. Structural/native rendering acceptance does not imply artistic approval.

## Non-actor sprite direction

Non-actor art is retained where it already fits the coherent native-pixel presentation rather than churned cosmetically. Historical Atelier integration is permitted only for compatible non-actor groups such as abilities, buildings, chests, items, props, resources, structures and terrain. Terrain, props, buildings, resources, chests, structures, item icons and ability presentation remain covered by the permanent general asset validators and native visual matrices. Newly introduced opening-reward icons are generated project art when no historical source exists and remain part of full catalog coverage.

The art-direction contract is `docs/ART_DIRECTION.md`. It requires recognizable anatomy/object construction, meaningful motion rather than cosmetic pixel changes, consistent lighting, shared equipment anchors and nearest-neighbor/native-scale presentation.

## UI migration

The existing Task #12 modal/focus/input architecture is preserved. `PageLayoutProfiles` drives the real modal window geometry and page-purpose summaries. The UI path retains modal input blocking, background-focus suspension/restoration, overflow scrolling, Escape behavior, keyboard/mouse activation, text scaling, settings persistence and non-color-only error feedback.

Permanent Windows acceptance covers all supported page families at **1024×720, 1280×720, 1920×1080 and 2560×1440** across supported text scales, with additional content-scale emulation and keyboard/mouse/focus/error-state assertions. Exact-head Windows display and input acceptance run **`35103673222`** succeeded.

## Human-only gates

Automated coverage does **not** assert artistic taste, animation feel, human onboarding duration/retention, physical Windows monitor DPI, subjective usability/readability, or production capacity. Those remain explicit human acceptance gates. The migration is technically complete only in the repository/testing sense; release approval remains **NOT APPROVED — human acceptance remains.**
