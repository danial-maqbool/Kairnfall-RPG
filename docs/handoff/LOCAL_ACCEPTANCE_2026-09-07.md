# Local Windows acceptance checkpoint — 2026-09-07

**Incomplete development checkpoint. No completion approval, tested release tag,
or Windows delivery package is established by this report.** The full accepted
requirements remain the target. Catalog and asset checks do not establish
finished content, visual quality, or normal progression.

## Revision and review boundaries

- Starting source: `fe569b4f56641d8495e1ecb322feaf82240b265c`.
- Pushed security repair checkpoint: `7f284b3`.
- Integrated source checkpoint: `922d429ffa0112c4de34208a85a1b5502ae872e9`.
  Combined automated and bounded graphical checks below passed on this source tree.
  Full-game acceptance remains incomplete.
- Actual specialist agents produced server/security, client/UI, and world/art
  results. The server/security author also reviewed the integration's regression
  wiring; this is not an independent review of that author's own security code.
- Evidence below belongs to the stated baseline or repair phase. It does not
  automatically approve later working-tree changes or future commits.

## Environment

Windows local execution used Git `2.54.0.windows.1`, Python `3.12.10`, pinned
Pillow `12.0.0`, PowerShell `7.6.5`, stable .NET SDK `10.0.400`, Docker Engine
`29.6.1`, and Docker Compose `5.1.4`. Native editor execution reported
`4.7.2.stable.mono.official.ed1daf0bf`.

The graphical smoke used NVIDIA GeForce RTX 4060 Laptop GPU, OpenGL 3.3
Compatibility, driver `595.71`. This is graphics-startup evidence, not a measured
60 FPS or rendering-memory result. CPU: Intel Core i7-13620H; RAM: 16,869,351,424 bytes.
Matching export templates remain incomplete;
full bootstrap completion and package readiness are not established.

Development PostgreSQL uses loopback port `55432`; disposable integration
PostgreSQL uses `55433` with separate test database configuration. No existing
saves were deleted and no Docker volumes were removed for these checks. Private
configuration and raw local evidence remain outside public source.

## Observed checks

| Phase/check | Recorded result | Limit |
| --- | --- | --- |
| Baseline Windows core | 29 passed, 0 failed; exit 0 | Automated core fixtures |
| Baseline gameplay review | 34 passed, 0 failed; exit 0 | Focused regressions |
| Baseline transaction security | 13 passed, 0 failed; exit 0 | Existing adversarial coverage |
| Baseline network/PostgreSQL | 18 passed, 0 failed; exit 0 | Three real clients, not 100-client capacity |
| Baseline save conflicts | 5 passed, 0 failed; exit 0 | Disposable PostgreSQL checks |
| Baseline total | 99 passed, 0 failed | Does not replace gameplay acceptance |
| New security probes before repair | 0 passed, 2 failed; exit 1 | Defects reproduced with isolated fixtures |
| New security probes after repair | 5 passed, 0 failed; exit 0 | Host boundary/in-memory status checks |
| Post-security full backend rerun | 29 + 34 + 13 + 18 + 5 = 99 passed; exit 0 | Before complete world/UI integration approval |
| Python handoff checks | 17 tests; exit 0 | Later helper/test changes require rerun |
| Baseline asset technical checks | 45,248 passed, 0 failed | No visual or audio approval |
| Native Godot signal scene | Passed; exit 0 | Captures, methods, ordinary objects, async, GC, detach/reattach, reparenting, cleanup |
| Baseline real graphical smoke | World, inventory, skills, map: four fresh captures; exit 0; no engine errors observed | Startup/menu evidence only |
| Manual account flow | Account and character created with actual mouse interaction | Full clean-account sequence not completed |
| Integrated backend/database | 99 existing checks plus 5 security probes passed; exit 0 | `integrated-tests.log` |
| Integrated world paths | 103 zones, 3,588 masonry tiles, 949 destinations, zero failures | Spawn/door/NPC/exit/arrival coverage only |
| Integrated client build | Zero warnings/errors; exit 0 | `integrated-client-build.log` |
| Integrated native contracts | Signal and input contracts passed without engine errors; exit 0 | `integrated-native.log`; native synthetic input, not OS keyboard acceptance |
| Integrated asset build | 45,248 structural assertions passed; exit 0 | `assets-after-world.log`; artwork remains unapproved |
| Integrated graphical smoke | Four fresh images inspected; no engine errors; exit 0 | `integrated-smoke.log`; real OpenGL display |
| Repaired manual mouse paths | Reconnected saved character after restart; right-click walking and map scrolling worked | `interactive-repaired.log` plus active Windows observations; full walkthrough incomplete |
| Visual art acceptance | Failed | Mandatory art gate remains open |
| Listening, sustained load, extracted package | Unrun | Mandatory acceptance remains open |

The fresh baseline smoke capture directory is
`artifacts/local/smoke/1788787620660920600`, containing `01-world.png`,
`02-inventory.png`, `03-skills.png`, and `04-map.png`. These are local gameplay
captures, not concept images. Their presence does not certify every species,
animation, city, layer, or screen.

Integrated captures are in `artifacts/local/smoke/1788788553219837400` with the same
four filenames. All ten hotbar slots are visible at 1280x720. The map scroll bar
was exercised with actual mouse input, revealing the lower route/travel controls.
The current generated catalog SHA-256 is
`96a78856b06d03b76b8d6e8ab35fbdb1c7c6791ed2b8824fa568316a3d50f876`.
PostgreSQL image digest:
`sha256:d3e1620b530c944afa6e887d22eb899824da68e19c52024bf98f5220c88a65b2`.

## Commands and local evidence

Commands were run from the repository root. Logs are retained locally; this
report publishes summaries rather than private configuration or raw account data.

```powershell
pwsh -NoProfile -File ./bootstrap.ps1
pwsh -NoProfile -File ./Test-Kairnfall-Local.ps1
pwsh -NoProfile -File ./Test-Kairnfall-Local.ps1 -WithDatabase
.venv/Scripts/python.exe -m unittest discover -s tests/handoff -p "test_*.py" -v
.venv/Scripts/python.exe tools/local_dev.py assets
.venv/Scripts/python.exe tools/local_dev.py signals
pwsh -NoProfile -File ./Run-Kairnfall-Dev.ps1 -Smoke
pwsh -NoProfile -File ./Run-Kairnfall-Dev.ps1
dotnet run --project tools/security_probe/SecurityProbe.csproj --artifacts-path artifacts/local/security-build -c Release -- content/catalog.json
```

The post-security isolated core, review, and security runs used the same
`--artifacts-path artifacts/local/security-build -c Release -- content/catalog.json`
arguments with their respective `tests/<project>/<project>.csproj` paths.
Evidence includes `artifacts/local/baseline-tests-retry.log`,
`baseline-network.log`, `baseline-save-conflicts.log`,
`after-repairs-database.log`, `security-probes-before.log`,
`security-probes-after.log`, and `security-after-Kairnfall.*.log`.
Other local evidence includes `handoff-tests.log`, `native-signals.log`,
`first-smoke.log`, `bootstrap.log`, and `asset-checks.log`.

## Reproduced defects and bounded repairs

**Session expiry, R03/R22:** an expired session installed a movement intention at
the actual `RealmHost.HandleCommandAsync` boundary. Before repair the isolated
probe reported `expired_session_movement_accepted=True`. The repair checks
expiry after acquiring the authoritative gate, rejects closed connections, and
rejects expired attachment. Post-repair negative and valid-session controls pass.
The fixture does not test a live session expiring over WebSocket or a concurrent
database revocation race.

**Disconnect damage avoidance, R17/R22:** a connected lethal-poison control died,
while the disconnected/rejoined character retained health 1 after poison expired.
The repair continues pending poison/burn/bleed while disconnected, leaves
offline regeneration/resources/training paused, and stops status processing at
lethal damage. Both lethal controls now die; offline no-healing/no-XP checks pass.
This does not establish a complete combat-logout or boss-reset policy.

Existing transaction consent fingerprints, unique stack splitting, rollback,
private trade projections, and existing security assertions were retained.
Integration wiring adds the probes to the solution, local wrapper, and
Windows/Linux transaction workflow. The workflow's runtime result at the final
integration revision is still required.

World baseline reported 482 failures: 476 walkable masonry tiles and six inaccessible
doors. Building collision now precedes roads, physical door approaches connect to
streets, seven obstructed NPCs were relocated, and Thornhollow's stairs and return
arrival were relocated. The integrated path checks pass, without claiming resource,
quest-objective, or boss-arena coverage.

Native input testing reproduced the main root control swallowing world clicks.
Its mouse filter now lets world input reach the handler while HUD controls still
consume their clicks. Real right-click walking worked after repair. Physical-key
routing passes inside Godot; OS-injected shortcuts did not produce a response in
manual testing and remain unresolved. HUD placement and map scrolling were repaired.
The visibility helper rename resolves CS0108 without suppressing warnings.

## Visual review failure evidence

The world/art specialist inspected `artifacts/screenshots/creature-contact-sheet.png`
(145 idle thumbnails) and the original-detail native sheets
`client/Assets/mobs/sea_turtle.png` and `client/Assets/mobs/polar_bear.png` before
the collision repair. The polar bear's elevated small head, long upright neck,
and compact torso read as a camelid rather than a bear. The turtle repeats its
upward body/head orientation across south/east/north rows; attack/cast largely
repeat neutral anatomy, and death rotates the whole sprite. Boss thumbnails
repeat family silhouettes with crowns, including the Millbreaker boar, Mother
of Silk spider, and skeletal Bell Warden/Ivory Librarian/Cinder Marshal.

These are actual reviewed-image findings, not palette/hash deductions. They
fail the anatomy, genuine direction/state animation, and authored boss identity
requirements. The contact sheet is not gameplay evidence. Only those two full
native sheets received detailed frame inspection; the remaining sheets still
require review. The later world collision repair has numerical/path evidence
but no in-engine visual approval. No audio listening review occurred.

## Failures and interruptions retained

- Initial database setup exceeded its 180-second image/setup wait. The image pull
  was subsequently completed and database suites were retried sequentially;
  the successful 18 network and 5 save-conflict results are listed separately.
- Concurrent/active-process DLL locks produced MSBuild copy retries and a failed
  build (`MSB3027`/`MSB3021`, exit 1). The running server was not killed to bypass
  the lock. The post-repair probe and focused suites were built into an isolated
  artifact path and passed. `security-probes-build-locked.log` retains the failure.
- The initial missing-SDK probe attempt failed before execution; it is not a
  test result. Runtime failures and later passes were recorded after SDK setup.
- Full bootstrap failed: matching export-template download exceeded 1,200 seconds.
  Its partial archive was 127,926,272 bytes; expected official size is 1,202,598,411.
  The complete editor archive was verified and executed, but matching templates
  are not installed. No digest checks, TLS checks, or version requirements were bypassed.
- Interim native-input runs failed due to the expected root-click defect, then
  temporary catalog inconsistency and test resource leaks. Final integrated native
  contracts passed after catalog regeneration and explicit test-resource cleanup.

## Remaining mandatory work

Complete all 26 clean-account actions without progression grants or teleports,
including normal rune acquisition, useful crafting, all-city/layer travel,
quests, a genuine boss encounter, two-player auctions/trade/party, reconnect,
and saved-state verification after restart. Audit accessible and meaningful
training for all 60 skills, all advertised ability/rune handlers, class mechanics,
world destinations, economy, ownership, social permissions, and progression.

Security gaps still needing reproduction/repair or stronger acceptance include
unauthenticated WebSocket admission bounds, live expiry/revocation races,
crafting-station obstacle checks, broader combat logout/boss resets, transaction
and capacity races, crash recovery, and privacy under real multiplayer traffic.
The existing checks do not close this full adversarial list.

Review every required species, boss, real-object asset, animation direction,
equipment layer, running region, and UI at native resolution. Audio listening,
balance simulations, two graphical clients, actual keyboard/mouse progression,
resizing/scaling/rebinding, sustained 100-client testing where feasible, 20 Hz
server timing, and 60 FPS client measurements remain required.

After all mandatory gates pass, obtain aligned export templates, build client
and server packages, extract into a new directory including spaces, test actual
packaged account/gameplay/restart behavior with two clients, exclude private
state, and generate manifests/checksums. No tested tag, package locations,
package checksums, signing approval, or public deployment is claimed here.

## Verified-editor development launch while template setup is incomplete

The existing downloaded editor was digest-verified by `get_godot.py` and its native
version checked. From this checkout, it can be selected explicitly for development:

```powershell
$env:GODOT_BIN = (Resolve-Path '.tools/godot/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe').Path
pwsh -NoProfile -File ./Run-Kairnfall-Dev.ps1
```

This is a source development launch, not a Windows delivery package. Retry full
bootstrap to complete the verified template path. Test clients and their child
servers were closed; PostgreSQL volumes and private configuration were retained.
