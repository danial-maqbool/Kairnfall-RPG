# Network interface and local verification

The server source in `src/Kairnfall.Server/Program.cs` defines the live API.
It exposes `/health`, registration/login/logout, character list/create, catalog retrieval, and `/play` WebSocket entry.
Use `GameConnection` and shared models rather than creating a second incompatible client protocol.

`KAIRNFALL_DB` is required for the live server. `KAIRNFALL_CATALOG` selects the generated catalog.
Plain HTTP requires explicit `KAIRNFALL_ALLOW_LOCAL_HTTP=1`, Development/Testing environment,
and a loopback caller. Local launchers use `127.0.0.1:5077`. No public hosting is configured.

The WebSocket handshake includes the protocol version, character identity, and session token.
The server validates authentication and character ownership. The client must not supply final rewards or state.
Do not print tokens, full request bodies, or private account data in diagnostic reports.

Verify two simultaneous accounts, snapshots, movement, combat, loot ownership, chat scopes,
party/guild state, trades, zone changes, timeout, disconnect, reconnect, logout, and server restart.
Exercise invalid versions, malformed/null/oversized messages, replay, unknown IDs, and rate limits.
Preserve private trade and chat data from unrelated clients.

Ramp load-test logins within the existing authentication policy. Do not remove rate limits merely to reach a client-count target.
Measure sustained users, tick timing, queue/backpressure, memory, bandwidth, and database latency.
One working WebSocket or a three-client integration test does not establish 100-player capacity.
