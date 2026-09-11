# Walk-through map transitions — 2026-09-11

Map changes are now driven by authoritative movement rather than an `E` interaction.

## Player contract

- Walking through an authored building door changes to its interior automatically.
- Walking into authored cave, stair, tunnel, lift, gate, portal, or road entrances changes maps automatically.
- Connected surface-region borders change maps when the player walks outward through the authored border lane.
- A border without an authored exit stays solid and does not infer or invent a destination.
- Existing journey level gates remain server-authoritative. Locked entrances block movement and display their required level.
- Arrival positions are moved inward along the destination's real path so reciprocal entrances do not bounce the player back.
- Internal entrances are directional thresholds: crossing nearby traffic does not accidentally enter a door, cave, settlement, or gate.
- `E` remains the contextual key for NPCs, gathering, chests, loot, landmarks, and structures; exits are deliberately absent from the interaction target list.

## Entrance presentation

The deterministic environment pack now generates dedicated pixel-art sprites for roads, doors, gates, caves, tunnels, lifts, portals, and stairs. Surface-to-underground wilderness stairs render as cave mouths. These are structural/generated game assets; final artistic approval remains a human visual check.

## Automated acceptance

`WalkTransitionChecks` validates reciprocal authored exits, border topology, automatic door crossing, automatic wilderness-border crossing, exact level-gate enforcement, solid non-connected borders, safe arrival clearance, and removal of client `E` exit interactions. The real-network integration route to Dawnreach also crosses maps using movement only.

### Verification receipt

- Feature commit: `73e3ccb350a6b6a7f37d490fb9b6a67bc9379e59` (`feat: make map transitions walk-through`).
- Focused publish gate: GitHub Actions run `34637034943` — passed.
- Walk-transition acceptance: 6/6 groups passed.
- Full solution/client compilation, core/gameplay regressions, PostgreSQL real-network traversal, isolated save-conflict tests, deterministic entrance sprite generation, asset manifest checks, and `git diff --check` all passed before publication.
- The focused gate removed `tools/apply_walk_transitions.py`, `tools/refine_walk_transitions.py`, and `.github/workflows/walk-transitions-apply.yml` before publishing the feature commit.
- This receipt commit exists to trigger the ordinary repository CI workflow on the exact published feature state; its CI result is part of task closure.
