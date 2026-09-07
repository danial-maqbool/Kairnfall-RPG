# Isolated security defect probes

From the repository root, after generating the catalog and installing the pinned .NET SDK:

```powershell
dotnet run --project tools/security_probe/SecurityProbe.csproj -c Release -- content/catalog.json
```

The executable returns 1 when any security invariant fails. Keep failing
output visible; these assertions must not be inverted merely to make the probe
pass against the handoff implementation.

The expiry probe wires an isolated `RealmHost` with an expired session and
calls its actual command handler. Reflection supplies the in-memory engine and
connected-peer registry. Movement avoids persistence. No database, listening
socket, account lookup, credentials, or existing saves are used.

Positive controls check that a valid session can still move and that an expired
session cannot attach. The combat-logout probe compares identical lethal-poison fixtures, one active
and one disconnected until after the effect deadline, then reconnects the
second fixture. It also checks lethal damage followed by regeneration, and that
offline damage processing does not award healing, resources, or skill XP.
It tests damage avoidance, not a required disconnect penalty.

These probes run in the local test wrapper and Windows/Linux transaction-security CI.
They are neither a real-network test nor normal-play acceptance. Independently
test the authenticated transport and disposable PostgreSQL path.
