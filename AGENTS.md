# Kairnfall implementation contract

Continue the accepted MMORPG specification and the current new-player experience request.
Fix clarity, onboarding, controls, and encounter presentation before increasing catalog counts.
Preserve server authority, the persistent world, existing rewards, and existing saves.
Read HANDOFF.md, docs/SESSION_STATUS.md, and docs/handoff/CURRENT_EVIDENCE.json for verified state.
The journey design and authority model are in docs/NEW_PLAYER_JOURNEY.md.

## Single-main workflow

Keep only `main`. Do not create local or remote branches, pull requests, or issues.
This supersedes branch instructions in historical prompts and handoff files.
Preserve existing changes. Never force-push, rewrite history, or delete saves.
Use cohesive tested commits and ordinary fast-forward pushes to main.
Specialist reviews may run concurrently, but one integration owner commits changes.
Do not release, publish, deploy, tag a release, or change production infrastructure without
separate explicit authorization. CI package artifacts are test outputs, not released builds.

The permanent New-player journey workflow checks the exact main/delivery SHA, including
native Godot controls and real-server/PostgreSQL reconnect behavior. It has read-only repository
permissions and uses disposable services. Temporary candidate/edit/overlay workflows were
removed when their verified source was integrated; do not resurrect stale candidate requests.
The standalone tools/new_player_probe runner is also linked into the retained world probe.
Implementation verification precedes current-evidence synchronization. A documentation-only
handoff commit must retain the verified implementation and pass delivery-head checks.

## Evidence

Do not claim independent agents ran unless their runtime produced task results.
Do not count compilation, generated records, or image uniqueness as gameplay or art acceptance.
Keep failed and unrun checks visible. Inspect real frames and native game output when available.
The whole game remains incomplete until all gameplay, multiplayer, artwork, performance,
and Windows-package requirements pass at a stated revision. Human release approval is separate
from repository-side task completion; do not stop repository work merely for manual testing.
Preserve historical Task 20, Task 21, and Task 22 evidence when changing the current workstream.
Do not begin subsequent tasks without explicit authorization.

## Security

The server owns gameplay state. Clients send intentions, not rewards or results.
Onboarding hints and acknowledgements are presentation-only and never grant gameplay rewards.
Preserve session expiry, request sequencing, replay receipts, transaction consent, stack splitting,
public contribution rewards, dungeon/boss behavior, faction prerequisites, and old-save regressions.
Never commit credentials, private chat, account data, database backups, or local configuration.
Do not use tokens copied from chat. Do not expose public services during local development.
Do not bypass tool approval, TLS, checksum validation, or branch protection.

## Art

Use recognizable human and animal anatomy and real object construction.
Do not approve box-like characters, inappropriate species silhouettes, rotated standing death
frames, misaligned equipment, or animation jitter. Review all directions and action states.
A sword needs a blade, guard, grip, and pommel. Materials need deliberate pixel clusters.
Structural tests alone cannot approve art or audio.
