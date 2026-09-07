# Local requirements

## Scope

These requirements describe the `handoff/local-qa` source checkout, not a finished binary release.
Use a local Windows x64 computer for graphical acceptance. Do not test against an Internet realm.

## Required software

| Component | Requirement | Verification |
| --- | --- | --- |
| Git | Git for Windows, available on PATH | `git --version` |
| Python | Python 3.12.x with venv and pip | `py -3.12 --version` or `python --version` |
| .NET | Stable .NET 10 SDK, not only a runtime | `dotnet --version`; `dotnet --list-sdks` |
| PowerShell | 7.4 or later for the provided wrappers | `pwsh --version` |
| Docker | Docker Desktop with the Linux engine running | `docker info --format '{{.OSType}}'` must print `linux` |
| Compose | Compose v2 with `up --wait` and `--wait-timeout` support | `docker compose version`; `docker compose up --help` |
| Godot | 4.7.2 .NET x64 and matching .NET export templates | Bootstrap verifies the official archive digest. |
| Graphics | A driver compatible with the project's Godot compatibility renderer | Run the real client. Headless success is not graphical acceptance. |

`global.json` requests SDK 10.0.100 with `latestFeature` roll-forward inside .NET 10.
The client pins `Godot.NET.Sdk/4.7.2` and targets `net10.0`.
NuGet project references remain the authoritative dependency list.
The build-only Python dependency is `Pillow==12.0.0` in `tools/requirements-art.txt`.
No external model API, pasted token, NumPy package, or third-party art account is required.

Bootstrap installs the Python dependency into `.venv/`.
It downloads the pinned official Godot .NET archive into `.tools/` and verifies its published digest.
The helper refuses missing digests and mismatched export-template versions.
Do not disable verification to make an unavailable download appear successful.
A verified manual installation can be selected with the `GODOT_BIN` environment variable.

The database image is `postgres:18-alpine`, matching the existing backend CI major version.
This is a major-version tag, not an immutable image digest. Record the resolved digest during local QA.
The local Compose volume mounts `/var/lib/postgresql`, as required by the PostgreSQL 18 image layout.
Do not substitute an older major version against an existing volume.

## Development resources

A practical starting allocation is 16 GB RAM and 12 GB free disk for SDKs, editor files, Docker, assets, and logs.
These are planning allowances, not measured minimums or a performance guarantee.
The 100-client test must report actual hardware, test duration, client count, and server measurements.

## Network access during setup

Allow normal HTTPS access to GitHub release assets, NuGet, PyPI, and the Docker registry.
Do not disable TLS checks or security software. Do not open router ports.
No paid hosting service is provisioned by these scripts.

## Ports and data separation

| Service | Local address | Storage |
| --- | --- | --- |
| Development game server | `127.0.0.1:5077` | PostgreSQL development database |
| Development PostgreSQL | `127.0.0.1:55432` | Per-checkout named `realm` volume |
| Disposable integration PostgreSQL | `127.0.0.1:55433` | Separate per-checkout `tests` volume |

All local launch commands bind to loopback. A port conflict fails without stopping an unrelated process.
The integration suite can reset its own test tables. It must never receive the development connection string.
Use `Test-Kairnfall-Local.ps1 -WithDatabase` to supply the explicit database-test opt-in and isolated connection.
The lower-level Python test command also requires `KAIRNFALL_ALLOW_DB_TESTS=1` for database suites.

Random local passwords are stored in `.local/database.json`, which Git ignores.
Keep the checkout on a private local disk. Restrict that directory to your Windows user.
POSIX creation requests owner-only file access. Windows access follows the workspace's file permissions.
Do not copy the credential file into bug reports, screenshots, source archives, or public artifacts.
Do not delete it while its database volume exists. The launcher refuses to replace missing credentials for an existing volume.

## First local run

1. Open the checkout in the local coding agent.
2. Read `docs/handoff/HANDOFF.md` and `docs/handoff/LOCAL_AGENT_PROMPT.md`.
3. Install the required software through its official distribution if it is missing.
4. Open Docker Desktop. Select Linux containers.
5. Run `pwsh -NoProfile -File .\bootstrap.ps1` from the repository root.
6. Run `pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase`.
7. Run `.\.venv\Scripts\python.exe tools/local_dev.py signals`.
8. Run `pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke`.
9. Inspect the four screenshots. Then run the normal development client and the full acceptance checklist.

For two clients, run `Run-Kairnfall-Server.ps1` in one terminal.
Run `Run-Kairnfall-Client.ps1` in two other terminals. Use separate accounts.
The server process initializes its existing schema during startup. Verify `/health` before using the client.
Do not invent an Entity Framework migration command; this server uses its own storage initialization.

## Shutdown and recovery

The combined development command stops only the server child that it started after the client exits.
Use Ctrl+C for a standalone server. Allow the graceful shutdown to finish.
Run `Stop-Kairnfall-Database.ps1` to stop this checkout's containers without deleting their volumes.
A forced process termination is not proof of a clean save. Test crash recovery separately.

Do not run `docker compose down -v`, volume prune, `git reset --hard`, or `git clean -fdx` as a repair shortcut.
Do not point older launchers from another branch at these volumes.
If the folder moved, a port is occupied, credentials are missing, or authentication fails, preserve the current state.
Inspect the private config, the named volumes, the resolved Compose configuration, and server logs before changing anything.
Never publish a resolved Compose configuration because it contains local passwords.

## Official references

Interrupted official toolchain downloads retain a `.partial` archive for the next
bootstrap attempt. Resume responses must match the requested byte range and the
official asset size; the complete archive must still pass the official SHA-256
digest before extraction. A timeout is a failed setup attempt, not an installed
toolchain. Sanitized partial output is retained in
`artifacts/local/toolchain-download.log`. Keep one bootstrap/downloader active per
checkout so concurrent processes do not write the same partial archive.

- Godot pinned release: https://godotengine.org/article/maintenance-release-godot-4-7-2/
- Godot Windows/.NET downloads: https://godotengine.org/download/windows/
- .NET SDK: https://dotnet.microsoft.com/download/dotnet/10.0
- Python: https://www.python.org/downloads/windows/
- PowerShell: https://learn.microsoft.com/powershell/scripting/install/installing-powershell-on-windows
- Docker startup readiness: https://docs.docker.com/compose/how-tos/startup-order/
- PostgreSQL official image and volume layout: https://hub.docker.com/_/postgres
