# Furnishing source integration — 2026-09-08

This commit installs actual source changes, not only a test request. It preserves the live main tree and copies the fourteen implementation/test files from the verified candidate. No branch or pull request is created. No history is rewritten.

Tested candidate: `b81425e0a16d24d123b714f796e1d9db75a2911e`.
Source baseline: `1a257f8f53413b0989699e6341bf2f79455ba2ef`.
Full verification: Actions run `34254704287`, verify job `102157495915`, SUCCESS.
Graphical fixture workflow: Actions run `34254704278`, render job `102157447828`, SUCCESS.

## Implemented

- Authored inn, forge, shop, workshop and hall furnishing layouts for existing service interiors.
- Tables, counters, beds, shelves, racks, hearths, anvils, workbenches, containers, floor textiles, practice markings and related props.
- Village service-yard placement and role-specific building details.
- Cached village surface treatment and terrain-edge sprites. The surface treatment does not change authoritative ground types.
- Shared solid furniture footprints. Rendering and server collision use the same catalog dimensions.
- Validation rejects unsafe asset keys, invalid dimensions, overlapping solid furniture, and ground art that conceals existing solid terrain.
- Bounded recovery for previously valid saved occupants and loot that overlap newly placed furniture. Existing corruption checks remain in force.

## Retained failures and repairs

The first candidate put a village anvil on the river. Catalog validation correctly rejected it. The anvil now occupies its dry forecourt. The practice ring also moved off river-adjacent ground. Validation now checks ground-only art as well as solid furniture.

The next run passed the backend, security, world, migration and database suites, then failed the practice-ring image construction check. Paired chalk stance outlines now provide deliberate training-area detail. The test threshold was not reduced.

The final full workflow passed content compilation, client and server builds, backend/security/world/database suites, all Python handoff tests, asset reconstruction/validation, native Godot contracts, authenticated graphical smoke and live native-input checks. The separate visual workflow rendered the native presentation fixtures successfully.

## Evidence boundaries

Implemented: YES. Automatically tested: YES. Graphically rendered: YES.
Independent image inspection in this chat runtime: NOT COMPLETED. The container/Python tools failed, so generated screenshots could not be opened here.
Windows physical keyboard/DPI review: NOT RUN in this continuation.
Visual acceptance and whole-game acceptance: NOT PASSED.

This checkpoint supersedes the unintegrated status in `VISUAL_FURNISHING_CANDIDATE_2026-09-08.md` for these fourteen source files. Bow handling, the ability browser and further interface work are separate follow-up changes and are not certified by this checkpoint. No package, tag, public deployment or release approval is included.
