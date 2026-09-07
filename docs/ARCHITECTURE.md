# Architecture map

## Current source boundaries

`client/` is the Godot C# graphical client. GameRoot coordinates account/UI/input behavior.
WorldView renders the world. PixelAssets loads generated textures and layered actor sheets.
The ActionButton helper owns native signal subscriptions and invokes ordinary C# callbacks.

`src/Kairnfall.Core/` contains Catalog, Models, Mechanics, RealmEngine, combat/economy/social source,
shared protocol support, and GameConnection. Keep game-critical state on the server.
`src/Kairnfall.Server/Program.cs` exposes account/character/catalog endpoints and the `/play` WebSocket.
The server registers account storage, realm storage, and the hosted realm simulation.
PostgreSQL is required. The local launcher does not replace it with a fake in-memory server.

`content_src/` compiles to a validated catalog. `tools/art/` compiles to PNG/WAV resources.
The local setup copies the same catalog into the client asset pack and checks byte equality.
The local test runner supplies a separate disposable database. Development saves use their own volume.

## Integration policy

Use `docs/handoff/SOURCE_PROVENANCE.json` to identify incorporated revisions.
Do not replace the current source with an older branch's entire tree.
Do not introduce a second protocol, competing launch script convention, or new engine merely to avoid debugging.
Separate account, simulation, transport, asset, UI, and release evidence.

## Local acceptance work

Inspect queue limits, snapshot size, interest management, tick timing, transactions, fault handling,
database initialization/migration, UI lifetime, world streaming, and asset memory in actual execution.
This source map does not establish production scale or completed features.
