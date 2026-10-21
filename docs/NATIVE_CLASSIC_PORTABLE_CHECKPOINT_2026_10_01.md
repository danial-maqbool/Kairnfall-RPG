# Native portable offline checkpoint - October 1, 2026

The runnable local bundle is **`deliverables/Kairnfall-Offline-Windows-2026-10-01`** in MysteraLegacyLocal.
Start **`Play-Kairnfall.cmd`**; **`Stop-Kairnfall.cmd`** stops only recorded processes belonging to that folder.
The verified ZIP is **`deliverables/Kairnfall-Offline-Windows-2026-10-01.zip`** (191,065,296 bytes), SHA-256
`6a388d711a9aa4ba38c18e082571182d65f86a7198375c90b958b1170230d8d4`. The unlaunched folder has 2,061 files totaling 465,428,921 bytes.
No personal/QA saved realm, accounts, generated database credentials or private test record is distributed.

## Runtime and ownership

The folder includes the verified Godot 4.7.2 .NET client, self-contained .NET 10.0.11 server/launcher,
current native content catalog and cached PostgreSQL 18.6 Windows binaries. No further software download,
installer, Python, installed .NET runtime/SDK, Godot editor, Docker or cloud dependency is required to run it.
Windows x64, an OpenGL 3.3 graphics driver, writable folder/user profile and free loopback ports 5077/55435
are required. UI preferences use the ordinary Windows profile `Kairnfall-Classic-QA-Package`; this is documented
OS profile storage, not a development-checkout dependency. All world/account/database data is under `state/`
inside the folder and is generated on first use. Back up the whole stopped state folder including its credentials.

The server is published from a separate copy of current native source. Its local packaging-only
PortableStopObserver accepts an owning launcher's nonce file under the folder, checks explicit Testing/loopback
configuration and invokes normal hosted shutdown. It adds no network endpoint, game command, schema or save change.
The launcher waits for graceful server exit before stopping its own database. It validates file hashes and owned
PID/start-time/image paths, refuses occupied ports, and preserves incomplete initialization or missing credentials.
Shutdown failures produce a failure exit status. No unrelated process/service is stopped or restarted.

## Verified flow and limits

| Gate | Result |
|---|---|
| Self-contained server and native launcher publish | Passed with cached Npgsql, installed apphost and approved runtime packs only |
| Corrected client standard export / startup / normal close / classic graphical fixture | Passed / passed / passed / 134 |
| Clean relocated C: runtime folder, SDK/Python/dev paths unavailable | Cold startup passed |
| Normal generated account: movement, equipment, food, gathering, drops/Shift pickup, crafting, rat combat/loot, road travel, campfire/progression | 101 headless checks passed |
| Same database after graceful server restart | 14 exact item/progress/ownership/timer/valid-position checks passed |
| Saved character/campfire in Windows renderer | 15 passed |
| Stopped saved folder copied to a new path, then same saved character | 15 passed |
| Final app-local PostgreSQL CRT / client-server-launcher CLR / normal graphical startup and close | Passed; actual loaded module paths are inside the relocated bundle |
| Owned game/database endpoints after verification | All stopped |

The initial launcher verification hit a log writer/reader sharing error; its handle lifecycle was corrected.
A cold held-key fixture also asserted against a snapshot after a fixed 0.5-second delay. Read-only inspection
showed its final saved position was centered. The fixture now awaits fresh authoritative centered/stable snapshots
with a bounded timeout, then separately proves no extra tile follows key release; the assertion was retained and
strengthened. Production movement/speed/collision did not change. Login help now refers to the included local launcher
rather than requiring a development script. Earlier failed verification copies/logs and all generated QA data remain
separate and intact; the deliverable itself has never been launched.

An earlier normal-account run passed 90 assertions, then timed out while routing to the wilderness exit. A read-only
QA-position diagnostic found it stopped at a valid centered village position. A direct simulation using the bundled
Core crossed the road, and this later complete account run with transition tracing passed. This is an **unresolved
intermittent route finding**, not a demonstrated movement repair. Its failed proof is retained at
`scratch/native_portable_verification/36f4619ee21943d9a39ae1da34e95167/results.json`; the direct Core probe is
`scratch/portable-route-probe/route-result.log`. Do not describe the checkpoint as free of intermittent movement issues.

The full loop is **headless**. The two graphical checks are short saved reloads, not a repeat of the known
focus-interrupted full route. Human physical keyboard/mouse feel, uninterrupted graphical play, monitor DPI,
artwork/audio quality and load/stress remain unapproved. Native Git HEAD remains
`192c8b50ce6ecac11e6327189af6208dd26c7944`; changes are local/uncommitted and no push/public release occurred.
Existing source launchers and personal saved realms are preserved.

The final native dependency audit found PostgreSQL was relying on installed Visual C++ CRT DLLs. Ten unchanged
Microsoft-signed release CRT files are now included app-locally from the existing Build Tools redistributable directory,
with distribution-list provenance and notices. No extra download or installation occurred. The three required CRT
DLLs match the previously available installed bytes, and 2034 gameplay-verified native files/catalog
remain unchanged. A separate cold **normal graphical** launch confirmed PostgreSQL CRT plus client/server/launcher CLR
loaded from the relocated folder, then ordinary owned-window close completed scoped shutdown. The gameplay loop was
not unnecessarily repeated after this dependency-only addition. OS DLLs and an OpenGL driver remain platform prerequisites.

## Concrete fidelity gaps

See [full observed-reference inventory](NATIVE_REFERENCE_FIDELITY_GAPS_2026_10_01.md). Missing mechanics/content
include real hunger/Food behavior, the compact spawn/tutorial pocket, interactable signs/fountain, proximity tutorial
milestones and Questing XP, observed starter recipe/templates, and optional offline guest quick start. Native
classes/catalog/recipe costs, five HUD meters, ability/target layout and village/character art still differ.
Measured tile/avatar scale and HUD layout can be tuned in code; artwork quality and physical input/visual acceptance
need human judgment. Canonical hunger/XP curves, fountain effect, strict adjacency/gather success and unlock rules are
not comprehensively observed. A one-session daily bonus is not a universal balance rule. These evidence or implementation
gaps should not be labelled as waiting for user taste, and no full Mystera parity is claimed.

## Evidence

- `scratch/native_portable_build/final-package-results.json`: exact bundle/archive hash/counts and acceptance scope.
- `scratch/native_portable_verification/current-verification.json`: relocated folders, Windows-only PATH, unavailable
  installed runtime roots, four gates and endpoint shutdown. Its generated state/credentials are private and not packaged.
- `scratch/native_portable_verification/current-module-verification.json`: actual app-local native runtime DLL paths,
  final normal graphical cold launch/ordinary close and stopped endpoints.
- `scratch/native_portable_build/cached-crt-copy-results.json`: unchanged cached signed release CRT files and retained pre-CRT diagnostic archive.
- `scratch/native_portable_build/current-build.json` and build directory logs: source hashes, local publish provenance,
  log-lifetime/shutdown corrections and current client package.
- `scratch/native_packaging/approved_a6b811be5ceb4c58864cc2bdc191d59f`: current client export/runtime/134/frame evidence.
- `docs/NATIVE_REFERENCE_FIDELITY_GAPS_2026_10_01.md`: observed/measured versus implementable/taste/unknown inventory.

The ZIP passed member CRC validation. It is a local delivery artifact, not an approved public release.
