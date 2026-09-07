# Implementation status

This repository is not a finished game or a playable Windows release.

## Verified evidence

The authoritative core and content regression run at commit `2c7c83cdcb92ab48d9e47f39da4bb9bd02215540` passed 29 tests in GitHub Actions run `34099179504`.

The generated catalog contains 530 item templates and 132 ability definitions. Counts describe data records. They do not prove that the corresponding presentation, balance, or end-to-end gameplay is complete.

The verified regression suite covers progression, movement constraints, physical map connectivity, inventory identity, purchases, banking, crafting, socketing, auction double-purchase rejection, trade consent, chat visibility, quest reward replay, serialization, damage bounds, chest cooldowns, and basic combat.

## Later implementation requiring verification

Additional source implements a PostgreSQL realm store, account registration, password hashing, expiring sessions, authenticated WebSockets, a reusable client transport, and real network integration tests. Do not describe those integration tests as passed until their actual run logs establish the result.

The network test harness includes account ownership, three connected clients, whisper privacy, trade confirmation, rune insertion, rejected forged operations, parties, gathering, crafting, map transitions, banking, auction purchases, single-writer protection, forced restart recovery, and logout revocation.

## Incomplete release requirements

- No tested playable Godot Windows client has been delivered.
- No complete sprite set has passed visual inspection. The art requirement remains detailed, recognizable pixel-art objects with anatomical or construction detail and aligned animation layers. A color variation is not a distinct species.
- No Windows release, final release tag, or production deployment has been verified.
- No 100-player load test has been verified.
- No independent multi-agent team execution has been verified. Role separation in documents is not evidence of separate agents.
- Audio, final UI, world presentation, full content uniqueness, balance, and the complete acceptance playthrough remain unverified or incomplete.

## Known code review findings

1. Delayed attacks need to retain the originating weapon or ability skill when awarding experience.
2. Some skills need additional actionable progression content before level 100 is reachable.
3. Shield block must require an actual shield, not any offhand item. Quiver and two-handed bow rules need a compatible slot model.
4. Low-level dungeon populations must not inherit high-level biome creatures without level-aware encounter selection.
5. Repeated regional quest templates do not satisfy a requirement for genuinely distinct side quests.
6. Boss attack definitions must drive their implemented encounter behavior.
7. Resource and creature placement needs regional coverage beyond the central spawn area.
8. Expired world events must remove or retire their associated world objects and avoid duplicate creation after restart.
9. Pet dismissal, structure dismantling, guild role management, and corpse ownership need complete behavior and tests.
10. Disconnect behavior needs adversarial review for combat escape and reward abuse.
11. Whole-realm cloning and full snapshot persistence per command require profiling and likely transaction batching before claiming 100 concurrent players.
12. The database writer must reject an unexpected missing snapshot row during a revisioned update.

## Runtime status

The local execution environment stopped responding after a large development-tool artifact download. Subsequent local execution and image inspection could not be verified. GitHub Actions is the source of the confirmed build and test evidence above.

Keep implementation work on the development branch. Do not label the project complete, claim unobserved tests, or publish a final release until the outstanding acceptance gates pass.
