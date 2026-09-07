# Run Kairnfall on Windows

The development package is not the completed MMORPG specified in the project contract.
Use a package only after its build and launch workflow succeeds.

## Play a packaged development build

1. Install Docker Desktop from its official Windows download page. Open it and use Linux containers.
2. Download the `Kairnfall-Windows-Development` artifact from a successful `Build and launch the game` workflow run.
3. Extract the artifact ZIP. Then extract `Kairnfall-Windows-Development.zip` to a normal writable folder. Keep its `client`, `server`, and launcher files together.
4. Double-click `Play-Kairnfall.cmd`. The launcher starts a local PostgreSQL database and a local game server.
5. Leave the server address at `http://127.0.0.1:5077`. Register a game account, create a character, and enter the world. This game account is separate from GitHub and Zeiko.
6. Use WASD or arrow keys to move. Use E to interact. Use I for inventory, K for skills, J for quests, and M for the map.
7. Run `Stop-Kairnfall.ps1` when you need to stop the local realm. It does not delete saved characters.

The local launcher does not open an internet-accessible server. It binds the game port and PostgreSQL port to this computer only.
The server cannot remain online while this computer is shut down or asleep.
A public persistent server needs separate hosting, HTTPS/WSS configuration, backups, and an operational security review. None has been deployed by these scripts.

## Saves and logs

PostgreSQL saves use the Docker volume `kairnfall-local_realm-data`.
The local password and server logs use `%LOCALAPPDATA%\Kairnfall\local-realm`.
Windows protects the local password with the current Windows user's data-protection service.
Keep the password file and database volume. Do not run `docker compose down -v` unless you intend to delete your local realm.
Never commit saves, password files, or account data to GitHub.

## Build from source instead

Install Python 3.12 and the .NET 10 SDK. Install Docker Desktop for local PostgreSQL.
Open PowerShell in the repository root, then run:

```powershell
.\Run-Kairnfall-Dev.ps1
```

`Run-Kairnfall-Dev.ps1 -InstallDotNet` can install the .NET SDK in the repository's ignored `.tools` directory.
The source build verifies official Godot archive digests. It builds assets in `client/Assets`, imports them, exports the client, and publishes the server.
Do not change the system-wide PowerShell policy. `Play-Kairnfall.cmd` sets a policy only for its own PowerShell process.

## A successful build is not final acceptance

The workflow checks a live Godot client on Linux and a separate exported Windows startup.
It does not prove that every skill, quest, city, boss, or sprite meets the full game specification.
Generated image counts and atlas checks are not visual approval.
The art-review contact sheets and actual client screenshots belong in the build evidence.
