# Kairnfall implementation contract

Continue the accepted MMORPG specification and the current player-experience repair request.
The user rejected the present sprites, interface, onboarding, controls, and encounter pacing.
Fix those problems before increasing catalog counts. Preserve server authority and existing saves.

## Single-main workflow

Keep only `main`. Do not create local or remote branches or pull requests.
This supersedes branch instructions in historical prompts and handoff files.
Preserve existing changes. Never force-push, rewrite history, or delete saves.
Use cohesive tested commits and ordinary fast-forward pushes to main.
Specialist reviews may run concurrently, but one integration owner publishes changes.

When local execution is unavailable, a Git commit object may hold a candidate without a branch.
The read-only candidate workflow tests an exact SHA named in `.ci/experience-candidate.json`.
That test request is not a claim that the candidate is installed in main.
Integrate candidate source only after its required checks pass, and record the tested SHA.
The workflow cannot push, deploy, publish a release, or access production data.

## Evidence

Do not claim independent agents ran unless their runtime produced task results.
Do not count compilation, generated records, or image uniqueness as gameplay or art acceptance.
Keep failed and unrun checks visible. Inspect real frames and native game output when available.
The whole game remains incomplete until all gameplay, multiplayer, artwork, performance,
and Windows-package requirements pass at a stated revision.

## Security

The server owns gameplay state. Clients send intentions, not rewards or results.
Preserve session expiry, transaction consent, stack splitting, and save migration regressions.
Never commit credentials, private chat, account data, database backups, or local configuration.
Do not use tokens copied from chat. Do not expose public services during local development.
Do not bypass tool approval, TLS, checksum validation, or branch protection.

## Art

Use recognizable human and animal anatomy and real object construction.
Do not approve box-like characters, inappropriate species silhouettes, rotated standing death
frames, misaligned equipment, or animation jitter. Review all directions and action states.
A sword needs a blade, guard, grip, and pommel. Materials need deliberate pixel clusters.
Structural tests alone cannot approve art or audio.
