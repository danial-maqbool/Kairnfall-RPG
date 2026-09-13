# Windows release-candidate setup and recovery

This guide applies to the Task 15 release-candidate bundle. It does **not** authorize a public deployment or release/tag.

**NOT APPROVED — human acceptance remains.**

## Bundle contents

The Windows package workflow produces three SHA-256-covered archives: the Godot Windows client, the framework-dependent .NET 10 Windows server, and the Kairnfall operations utility. The outer release-candidate archive also carries `release-candidate.json`, `SHA256SUMS.txt`, this setup guide, the candidate audit, and the known-limitations record.

Before using any archive, verify the checksum recorded in `SHA256SUMS.txt`. The structured `release-candidate.json` must have `publicationReady: false` until the human acceptance gates are actually complete.

## Server prerequisites

Use Windows x64, a supported .NET 10 runtime for the framework-dependent server, and PostgreSQL 18. Use a dedicated database/user and a secret store or service environment for the connection string. Never commit or paste real credentials into repository files or logs.

Set `KAIRNFALL_DB` in the server process environment. Configure HTTPS/WSS through normal ASP.NET Core/Kestrel or reverse-proxy deployment. Do not set `KAIRNFALL_ALLOW_LOCAL_HTTP=1` or run as Development/Testing for an Internet-facing realm. The server intentionally refuses ordinary plaintext HTTP outside the explicit loopback development/test boundary.

The packaged catalog is used by default. `KAIRNFALL_CATALOG` is only needed when an operator deliberately supplies another validated catalog path.

Start `Kairnfall.Server.exe`, then query `/health` over HTTPS. A deployable instance must return HTTP 200 with `ready: true`. The server refuses an unsupported database schema history and refuses a second authoritative writer for the same realm database.

## Client

Extract the client archive into a clean directory and run `Kairnfall.exe`. At the connection screen enter the HTTPS realm address. The release candidate does not embed or claim a public Kairnfall endpoint.

## Backup before a cutover

The operations archive contains `Kairnfall.Operations.exe`. Install PostgreSQL client utilities matching the PostgreSQL server major version so `pg_dump` and `pg_restore` are on `PATH`, or set `KAIRNFALL_PG_DUMP` and `KAIRNFALL_PG_RESTORE` to trusted matching executables.

Stop or quiesce the authoritative server for the cleanest cutover checkpoint, set `KAIRNFALL_DB` in the operations process environment, then run:

```powershell
.\Kairnfall.Operations.exe backup C:\KairnfallBackups\realm-before-deploy.dump
.\Kairnfall.Operations.exe verify C:\KairnfallBackups\realm-before-deploy.dump
```

The backup command refuses to overwrite an existing backup. It emits the custom-format dump plus `.json` metadata and a `.sha256` sidecar. The metadata records only schema/revision/count/checksum information; it does not record the database connection string or account names.

## Restore and rollback model

Do not restore over the active realm database. Create a fresh empty PostgreSQL database, point the operations process at that fresh target with `KAIRNFALL_DB`, and run:

```powershell
.\Kairnfall.Operations.exe restore C:\KairnfallBackups\realm-before-deploy.dump
```

Restore verifies the SHA-256 metadata first and refuses a target that already has public tables. After `pg_restore`, it checks the supported schema history, realm revision, account count, and session count against the backup metadata. Start one server against the restored database, require `/health` to become ready, reconnect a test account, then perform an explicit service/secret cutover. Keep the old database unchanged until the new instance has been accepted.

If restore fails after writing part of a target, discard that target database and retry into another fresh database. Do not bypass the empty-target safeguard.

## Publication boundary

A technically valid bundle is still only a candidate. Release/tag creation remains blocked until the recorded human Windows gameplay/persistence, feel/balance, independent QA where required, artistic review, ordinary-account traversal, audio listening, physical DPI/input, owner-machine package, and any advertised production-capacity gates are complete.
