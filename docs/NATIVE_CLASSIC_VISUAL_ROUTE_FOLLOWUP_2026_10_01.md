> This is the pre-approval visual/routing record. Its packaging blockers are superseded by the [verified local Windows checkpoint](NATIVE_CLASSIC_WINDOWS_CHECKPOINT_2026_10_01.md); earlier failed attempts remain historical evidence.

# Native visual and routing follow-up — October 1, 2026

This continues the [verified playable checkpoint](NATIVE_CLASSIC_PLAYABLE_CHECKPOINT_2026_10_01.md).
The Godot 4.7.2 .NET client, .NET 10 authoritative server and PostgreSQL architecture remain intact.
Changes are local and uncommitted on main, based on `192c8b50ce6ecac11e6327189af6208dd26c7944`.
Existing changes and all personal saves were preserved. This is a tested source checkpoint, not a release.

## Changes

The graphical route timeout exposed a game bug: the client consumed a point within 0.32 tiles,
while the server was still finishing its previous grid step. Held input could start another tile before
the next graphical frame, causing overshoot at corners and an exhausted route away from its destination.
The optional grid route now requests one server-owned step and waits for exact authoritative arrival.
The additive `move.Arg=classic_step` cannot repeat without another request. Manual held keys, ordinary
movement, speed, collision, stun/root, focus/modal cancellation and existing save fields remain unchanged.
A new core case verifies that a route step cannot overshoot without a release packet, including a corner.

The optional compact/classic presentation now draws original, locally generated dense grass and layered
round oak crowns with short visible trunks. Occasional decorative crowns have small red berries.
Existing images, resource lifecycle and pine/tree anatomy outside this optional treatment are retained.
It also adds a circular spiral Action button, reduces the central resource meter width and removes its
duplicate rectangular primary action from the compact row. All ten native abilities remain reachable.
Classic targets use yellow rings/health, enemy damage numbers are white, player damage red, and accepted
combat impact bursts use small red pixels. The expanded presentation remains available.

The new code is in `GameRoot.GridRoute.cs`, `WorldView.ClassicArt.cs`, `ClassicActionCircle.cs`, with
scoped integration in the existing WorldView/GameRoot and core movement/transport files.
No proprietary code or assets were extracted. Recipe, hunger, XP, cooldown or reward parity was invented.

## Verification and limits

| Check | Result |
|---|---|
| Release solution | Zero warnings/errors |
| Final native Debug compilation | Zero errors; existing CS8793 warning in PlayerExperienceContract.cs:76 |
| Core gameplay, eight grid cases and five drop cases | 54 passed, 0 failed |
| Retained gameplay review / security | 34 / 13 passed, 0 failed |
| Native classic presentation fixture | 113 checks passed, clean engine-error scan |
| Retained input / controls / layout | Passed / 1,184 / 1,639 checks, clean engine-error scans |
| Updated normal-account native/local-server loop | 100 checks passed; explicitly headless |
| Same new QA realm after server restart | 14 exact saved-state checks passed |
| Same new QA save in the actual Windows renderer | 15 checks passed; real restored character/campfire frame |

The complete account gate at 916×515 uses native key and mouse handlers and actual server actions:
movement/collision-valid routes, equipment, fishing with accepted hold/release repeat, food, partial drop
and Shift pickup, copper gathering and smelting, normally acquired timber, selected rat combat, loot,
road travel, campfire placement, construction XP and save/reload. No rewards or player state are injected.
The fixture was corrected to reacquire a widget if a legitimate panel refresh queued the previous one
for deletion, and to check that the intended button was enabled before clicking. Assertions were retained.

The restart compares exact character identity/region/valid position, item IDs and metadata, gold,
equipment, skills/quests, cooldown/death timers, owned structure identity/owner/position/recovery time,
non-rewinding clock and absence of stale action intentions. These comparisons apply only to a newly
generated QA account. No personal SQL realm was opened and no personal save reload is claimed.

Uninterrupted graphical play remains unverified. Real graphical attempts passed movement, equipment,
repeat gathering, drop/pickup, smelting and timber gathering. A later rat-combat attempt logged Windows
application focus loss, correctly cancelling its intention. Another attempt timed out during repeat
fishing; that log does not prove its cancellation cause. Focus safeguards were not bypassed.
The repaired route successfully traversed the former failing paths; these desktop interruptions are
separate from that proven route bug. Real 916×515 HUD, inventory and saved-campfire PNGs were inspected.
Automated layout checks do not approve physical monitor DPI, original art quality or human keyboard feel.

Earlier PostgreSQL review (5), XP fixture (9), player-experience (447) and character fixture (177) passes
remain earlier checkpoint evidence. They were not recast as a new exact-head CI or human art/audio approval.
The retained input/control/layout reruns precede the final test-only widget-lifetime repair; gameplay
implementation was unchanged by that fixture repair. Source hashes for 35 files are recorded separately.

## Launch and packaging

Use `Play-Classic-Native-Preview.cmd` in MysteraLegacyLocal, then Settings → Use classic local presentation.
It uses the retained separate preview realm and preferences, the cached local PostgreSQL binary and
native client; no personal realm, Docker, installer, download or unrelated service is used.
The preview and QA cannot run simultaneously against their shared private QA database: the existing
database-wide single-server lock correctly refused a concurrent check. No lock was weakened.

The standard self-contained export remains blocked by three uncached 10.0.11 Windows runtime packs.
The alternative framework-dependent managed build succeeded offline using the installed .NET 10.0.11.
Its local resource-pack/release-template startup exited with Windows access violation `0xC0000005` while
loading GameRoot.cs. Adding a byte-verified local copy of Microsoft's already-installed hostfxr.dll and
process-local runtime paths did not fix it. The underlying release-template startup cause is unresolved.
Those artifacts are marked failed and are not a usable package. No SDK/runtime/templates were installed,
no new packages downloaded and no security settings changed in this follow-up. The source preview is retained.

To attempt the standard self-contained export, the next authorization would be a task-local download
and NuGet signature/hash validation of these exact Microsoft-owned packages, then local export/startup
testing. The action would not install a system runtime, SDK or Windows service, or publish a release.
NuGet Gallery lists approximately 87.58 MB compressed in total:

| Exact package/version | Listed download size and official source |
|---|---|
| Microsoft.NETCore.App.Runtime.win-x64 10.0.11 | [38.05 MB](https://www.nuget.org/packages/Microsoft.NETCore.App.Runtime.win-x64/10.0.11) |
| Microsoft.WindowsDesktop.App.Runtime.win-x64 10.0.11 | [37.36 MB](https://www.nuget.org/packages/Microsoft.WindowsDesktop.App.Runtime.win-x64/10.0.11) |
| Microsoft.AspNetCore.App.Runtime.win-x64 10.0.11 | [12.17 MB](https://www.nuget.org/packages/Microsoft.AspNetCore.App.Runtime.win-x64/10.0.11) |

These are export-time packages; installing another runtime is not the proposed action.

## Evidence and remaining gaps

- `scratch/native_classic_live/classic_dff35f3c4b3c471dbecc382eea230975/live-results.json`
  and its normal/reload logs: final 100/14 pass.
- `scratch/native_classic_playable/graphical-reload-classic_dff35f3c4b3c471dbecc382eea230975/results.json`
  and `frames/09-server-reload.png`: final Windows 15 pass.
- `scratch/native_classic_results/native-results.json`, fixture logs and inspected
  `frames/02-compact-916.png` / `04-inventory-916.png` / `05-crafting-916.png`.
- `scratch/native_classic_playable/final-source-manifest.json`: current 35 source hashes.
- `scratch/native_classic_live/classic_9f01bbbb464747ad88a0d2dfd6eab51e`: route-bug trace.
- `scratch/native_classic_live/classic_ec4460f2043948f2be6a61b368503db6` and
  `classic_eaaf45d2061240f79e5c9c2e16e1180e`: repaired paths and logged desktop focus cancellation.
- `scratch/native_packaging/framework_bb12af37cd2c4dfab0ffb792fb19599e`: successful managed publish,
  failed release startup, host attempt and `FAILED-DRAFT.md`.
- Prepared-file manifests and byte-exact backups remain in `scratch/native_*` staging folders.

Generated QA password/connection files and private-qa-save.json contain local test secrets; do not attach,
commit or publish them. No personal save was reset, deleted or migrated. No commit, push, release or deployment occurred.

Remaining differences include native village/spawn geometry and scale, broader human/animal/art acceptance,
very sparse reference HUD feel, uninterrupted graphical/human play, audio, sustained load and Windows packaging.
Reference hunger, precise harvesting thresholds/chances, recipe/unlock/lifecycle balance and daily XP values
remain unknown or session-specific. Native mechanics remain authoritative; full Mystera/MMO parity is not claimed.

## Focused graphical diagnosis after the reporting checkpoint

A subsequent narrow Windows-rendered repeat-gather diagnostic passed 25 checks using a fresh normal
QA account, the real recovery interval and unchanged focus guards. It records instantaneous application
focus events and gathering-cancellation state. No gathering defect was reproduced in that bounded check.
Earlier logs explicitly prove focus cancellation in some route/combat attempts; the previous unexplained
fishing timeout remains unclassified. This diagnostic is not an uninterrupted full graphical gate.

Evidence: `scratch/native_classic_live/classic_adb9556535b444fdb6997e2bbc25212f/live-results.json`,
`ClassicLiveLoopContract.log` and `frames/focused-repeat-gather.png`. The runner labels this scope and
records `fullPlaythroughVerified=false`. A fixture-only notification type error was corrected; an
unintended attempt using the previous binary was stopped and is retained as failed evidence.
No production gameplay source changed after the 100/14 and graphical 15 passes. The fixture/source
manifest marks this later test-only change. Documentation was applied with before-file hash guards.
Cold preview startup passed again with the retained preview realm. The QA servers and private PostgreSQL
cluster were stopped afterward; no personal realm or unrelated service was changed.

Runtime-package approval remains pending. No package download or installation has occurred.
