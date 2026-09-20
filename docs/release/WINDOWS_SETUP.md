# Windows release-candidate setup and recovery

This guide applies to the Task 16 owner-acceptance candidate. It does **not** authorize a public deployment or release/tag.

Machine-readable candidate/evidence authority: `docs/handoff/CURRENT_EVIDENCE.json`.
Owner acceptance procedure: `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

**NOT APPROVED — human acceptance remains.**

## Bundle identity and contents

Use only the candidate identified by `task16OwnerCandidate` in `CURRENT_EVIDENCE.json`. Verify the outer candidate ZIP SHA-256 before extraction.

The Windows package workflow produces three SHA-256-covered archives: the Godot Windows client, the framework-dependent .NET 10 Windows server, and the Kairnfall operations utility. The outer release-candidate archive carries:

- `Kairnfall-Windows-Client.zip`
- `Kairnfall-Windows-Server.zip`
- `Kairnfall-Windows-Operations.zip`
- `SHA256SUMS.txt`
- `release-candidate.json`
- `SETUP.md`
- `KNOWN_LIMITATIONS.md`
- `AUDIT.md`

`release-candidate.json` records the exact source SHA, Task 16 status, package/document hashes, non-publishable boundary, and GitHub Actions run/artifact provenance when produced by CI. The manifest document filenames intentionally match the actual names in the outer bundle.

Before using any inner archive, verify `SHA256SUMS.txt`. The manifest and evidence ledger must both keep `publicationReady: false` until human acceptance is actually completed.

## Server prerequisites

Use Windows x64, a supported .NET 10 runtime for the framework-dependent server, and PostgreSQL 18. Use a dedicated database/user and a secret store or process environment for the connection string. Never commit or paste real credentials into repository files or logs.

Set `KAIRNFALL_DB` in the server process environment. Configure HTTPS/WSS through normal ASP.NET Core/Kestrel or a reverse proxy for any real deployment. `KAIRNFALL_ALLOW_LOCAL_HTTP=1` is permitted only for isolated loopback development/owner acceptance and must not be used for an Internet-facing realm.

The packaged catalog is used by default. `KAIRNFALL_CATALOG` is only needed when an operator deliberately supplies another validated catalog path.

Start `Kairnfall.Server.exe`, then query `/health`. A deployable instance must return HTTP 200 with `ready: true`. The server refuses unsupported database schema history and refuses a second authoritative writer for the same realm database.

## Client

Extract the client archive into a clean directory and run `Kairnfall.exe`. Enter the intended realm address on the connection screen. For the isolated Task 16 owner-machine procedure, follow `docs/qa/TASK16_OWNER_ACCEPTANCE.md`; it uses loopback HTTP only inside the disposable local acceptance setup.

The release candidate does not embed or claim a public Kairnfall endpoint.

## Backup before a cutover

The operations archive contains `Kairnfall.Operations.exe`. Install PostgreSQL client utilities matching the PostgreSQL server major version so `pg_dump` and `pg_restore` are on `PATH`, or set `KAIRNFALL_PG_DUMP` and `KAIRNFALL_PG_RESTORE` to trusted matching executables.

Stop or quiesce the authoritative server for the cleanest cutover checkpoint, set `KAIRNFALL_DB` in the operations process environment, then run:

```powershell
.\Kairnfall.Operations.exe backup C:\KairnfallBackups\realm-before-deploy.dump
.\Kairnfall.Operations.exe verify C:\KairnfallBackups\realm-before-deploy.dump
```

The backup command refuses to overwrite an existing backup. It emits the custom-format dump plus `.json` metadata and a `.sha256` sidecar. The metadata records schema/revision/count/checksum information; it does not record the database connection string or account names.

## Restore and rollback model

Do not restore over the active realm database. Create a fresh empty PostgreSQL database, point the operations process at that fresh target with `KAIRNFALL_DB`, and run:

```powershell
.\Kairnfall.Operations.exe restore C:\KairnfallBackups\realm-before-deploy.dump
```

Restore verifies SHA-256 metadata first and refuses a target that already has public tables. After `pg_restore`, it checks supported schema history, realm revision, account count, and session count against the backup metadata. Start one server against the restored database, require `/health` ready, reconnect a test account, then perform an explicit service/secret cutover. Keep the old database unchanged until the new instance has been accepted.

If restore fails after writing part of a target, discard that target database and retry into another fresh database. Do not bypass the empty-target safeguard.

## Publication boundary

Task 16 technical preparation and a valid candidate artifact are still not release approval. Human Windows gameplay/persistence, normal-play feel, world/economy/social usability, artistic review, audio listening, physical DPI/input, and owner-machine package acceptance remain human observations until actually reported.

No release/tag or public deployment is authorized by this guide.
