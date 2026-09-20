# Task 16 Windows owner acceptance

Task 16 is the final owner/human acceptance phase for the technically verified Kairnfall release candidate.

Machine-readable candidate/evidence authority: `docs/handoff/CURRENT_EVIDENCE.json`.

**NOT APPROVED — human acceptance remains.**

Do not use this procedure against a production database or public realm. Use a disposable local PostgreSQL database and the exact Windows candidate identified by `task16OwnerCandidate` in `CURRENT_EVIDENCE.json`. Do not substitute a different ZIP, rebuild, source checkout, or later commit without restarting the affected checks.

## Before you begin

Record these values before testing:

| Field | Value to record |
| --- | --- |
| Task 16 implementation SHA | From `implementationBaseline` |
| Windows package workflow run ID | From `task16OwnerCandidate.workflowRunId` |
| Actions artifact name | From `task16OwnerCandidate.actionsArtifactName` |
| Candidate ZIP filename | From `task16OwnerCandidate.candidateFile` |
| Expected candidate SHA-256 | From `task16OwnerCandidate.candidateSha256` |
| Actual candidate SHA-256 | Compute locally before extraction |
| Windows version/build | `winver` |
| CPU / GPU | Owner-machine values |
| Display resolution(s) | Owner-machine values |
| Windows scaling tested | 100%, 125%, 150% where practical |
| Input devices | Mouse/keyboard details |
| Audio output device | Device actually used for listening |
| PostgreSQL version | Local disposable server version |
| .NET runtime | `dotnet --list-runtimes` result relevant to .NET 10 |

Stop immediately if the implementation SHA, workflow run, artifact name, candidate filename, or candidate SHA-256 does not match the evidence ledger.

Use ordinary accounts and ordinary gameplay unless a step explicitly says otherwise. Do not use developer reward injection, database edits, debug teleports, or source-tree launchers for acceptance results.

## Finding severity

Classify every observation separately:

- **RELEASE BLOCKER** — data loss/corruption, authentication or authority failure, item/currency duplication, unrecoverable progression blocker, package cannot launch, server cannot restart/recover, major crash, or serious privacy/consent failure.
- **HIGH** — major functional defect with a workaround, but unacceptable for release.
- **MEDIUM** — meaningful defect that does not prevent core completion.
- **LOW / POLISH** — minor visual, wording, usability, or cosmetic issue.
- **SUBJECTIVE FEEDBACK** — pacing, combat feel, art preference, audio preference, or similar human judgement without an objective malfunction.

For each finding record: section/check ID, severity, objective vs subjective, exact steps, expected result, actual result, account/character, screenshot/video/log filename if useful, whether it reproduced, and whether retest is required.

Do not convert subjective feedback into an objective failure unless a documented requirement is actually violated.

## Clean package validation

### A1. Obtain the exact artifact

Download the Actions artifact named by `task16OwnerCandidate.actionsArtifactName` from the recorded Windows package workflow run. The artifact is CI evidence, not a public release.

Record: artifact name and run ID.

### A2. Verify the outer candidate checksum

In PowerShell, from the directory containing the candidate ZIP:

```powershell
$expected = "<candidateSha256 from CURRENT_EVIDENCE.json>"
$zip = ".\<candidateFile from CURRENT_EVIDENCE.json>"
$actual = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLowerInvariant()
$actual
if ($actual -ne $expected) { throw "Candidate SHA-256 mismatch" }
```

Record: expected hash, actual hash, PASS/FAIL.

### A3. Extract through a path containing spaces

Use a new empty directory, for example:

```powershell
$root = "C:\Kairnfall Task16 Candidate"
Remove-Item $root -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $root | Out-Null
Expand-Archive $zip $root
Get-ChildItem $root
```

Expected outer contents include:

- `Kairnfall-Windows-Client.zip`
- `Kairnfall-Windows-Server.zip`
- `Kairnfall-Windows-Operations.zip`
- `SHA256SUMS.txt`
- `release-candidate.json`
- `SETUP.md`
- `KNOWN_LIMITATIONS.md`
- `AUDIT.md`

Open `release-candidate.json`. Confirm:

- `task` is `16`;
- `sourceSha` equals the recorded implementation SHA;
- `releaseStatus` is `NOT APPROVED — human acceptance remains.`;
- `publicationReady` is `false`;
- the Actions provenance run ID/artifact name matches the evidence ledger;
- the three package hashes match `SHA256SUMS.txt`;
- document filenames in the manifest actually exist in the extracted outer bundle.

Record: PASS/FAIL and any mismatch.

### A4. Verify inner archive checksums

```powershell
$sumFile = Join-Path $root "SHA256SUMS.txt"
Get-Content $sumFile | ForEach-Object {
    if ($_ -match '^([0-9a-fA-F]{64})\s+(.+)$') {
        $expected = $Matches[1].ToLowerInvariant()
        $name = $Matches[2].Trim()
        $actual = (Get-FileHash (Join-Path $root $name) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $expected) { throw "Checksum mismatch: $name" }
        "$name  OK"
    } else {
        throw "Malformed checksum line: $_"
    }
}
```

Record: PASS/FAIL for client, server, operations archives.

### A5. Extract runtime archives without a source tree

```powershell
Expand-Archive (Join-Path $root "Kairnfall-Windows-Client.zip") (Join-Path $root "client")
Expand-Archive (Join-Path $root "Kairnfall-Windows-Server.zip") (Join-Path $root "server")
Expand-Archive (Join-Path $root "Kairnfall-Windows-Operations.zip") (Join-Path $root "operations")
Get-ChildItem $root -Recurse -Include *.cs,*.csproj,project.godot
```

Expected: no source/project files are required to run the packaged client/server.

Record: PASS/FAIL.

### A6. Confirm prerequisites and understandable failure

The server archive is framework-dependent. Confirm a .NET 10 runtime is installed. Use PostgreSQL 18 for the owner acceptance database.

Before setting `KAIRNFALL_DB`, launch the packaged server once from a disposable PowerShell window and confirm it refuses to become a ready realm with an actionable database/configuration error. Do not treat the expected fail-closed exit as a defect unless the message is misleading or unusable.

Record: error text/screenshot and whether it clearly identifies the missing/invalid configuration.

### A7. Create a disposable local realm and start the packaged server

Create a fresh database dedicated to this acceptance pass. Do not reuse production or unknown data.

Set the connection string only in the current process environment. Example shape:

```powershell
$env:KAIRNFALL_DB = "Host=127.0.0.1;Port=5432;Database=kairnfall_task16;Username=<local-test-user>;Password=<local-test-password>"
$env:KAIRNFALL_ALLOW_LOCAL_HTTP = "1"
$env:ASPNETCORE_ENVIRONMENT = "Testing"
$env:ASPNETCORE_URLS = "http://127.0.0.1:5091"
Set-Location (Join-Path $root "server")
.\Kairnfall.Server.exe *>&1 | Tee-Object (Join-Path $root "task16-server.log")
```

`KAIRNFALL_ALLOW_LOCAL_HTTP=1` is only for this loopback owner-machine test. Do not use it for an Internet-facing realm.

From another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:5091/health
```

Expected: HTTP 200 and ready state.

Record: server start result, health result, server log filename.

### A8. Launch the exported client

Run only:

```powershell
Start-Process (Join-Path $root "client\Kairnfall.exe")
```

At the connection screen use `http://127.0.0.1:5091` for this isolated loopback acceptance realm.

Expected: the exported client reaches connection/account flow without a source checkout or Godot editor.

Record: PASS/FAIL and any startup error.

## Account and character flow

Use a normal new account.

### B1. Registration/sign-in

Register, sign out if available, and sign in again. Exercise one deliberate invalid login.

Record: successful path, invalid-login feedback, account identifier used for the test (do not record a password).

### B2. Character creation

Create a character using normal appearance/class controls. Check name validation and visible appearance preview.

Record: character name, class, selected appearance summary, validation observations.

### B3. Character selection and realm entry

Select the character and enter the realm.

Expected: correct identity/class/appearance and Wayfarer's Rest start for a new character.

Record: PASS/FAIL, spawn location, screenshot if useful.

### B4. Disconnect/reconnect

Move and perform at least one state-changing action. Disconnect through the normal client path, reconnect, and verify the same character.

Record: pre-disconnect state, post-reconnect state, any stale duplicate player or target.

### B5. Quit/relaunch

Quit the client normally, relaunch `Kairnfall.exe`, sign in, and re-enter with the same character.

Record: PASS/FAIL and state differences.

### B6. Server restart

Exit/disconnect the client cleanly. Stop the server cleanly with Ctrl+C, confirm the process exits, restart it with the same disposable database, require `/health` ready, then reconnect.

Record: shutdown behavior, restart behavior, reconnect result, server log observations.

## Persistence

Durable state is expected for: accounts, characters, appearance, position, inventory, bank contents, equipment, gold/currency, skill XP/levels (including gathering/crafting professions), quests, reputation, achievements, guild state, known travel points, and discovery.

Do **not** require persistence for live combat target/aggro, temporary combat effects, transient invitations, trade readiness/confirmation, current session/socket state, temporary UI focus/modal state, or other short-lived interaction state unless the game explicitly presents it as durable.

For each representative durable field below, make a visible change through ordinary play, record the value, disconnect/reconnect, then repeat after the server restart from B6:

| State | Before disconnect | After reconnect | After server restart | Result |
| --- | --- | --- | --- | --- |
| Position |  |  |  |  |
| Gold/currency |  |  |  |  |
| Skill XP + level |  |  |  |  |
| Inventory item/quantity |  |  |  |  |
| Equipped item |  |  |  |  |
| Quest progress |  |  |  |  |
| Gathering/crafting skill progress |  |  |  |  |
| Reputation/achievement/discovery when changed |  |  |  |  |
| Guild state if exercised |  |  |  |  |

Any durable-state loss, duplication, ownership corruption, or rollback beyond documented semantics is at least HIGH and may be a RELEASE BLOCKER.

## First-hour progression

Perform a normal-play session from a fresh character. Do not use debug shortcuts.

### D1. Starter guidance

Follow the playable introduction from Wayfarer's Rest. Evaluate whether movement, interaction, combat, loot, inventory, equipment, skill XP, gathering, crafting, shops, maps, quests, death/respawn are discoverable in normal play.

Record: unclear step, where you got stuck, whether external documentation was needed.

### D2. Progression feedback and pacing

Record approximately every 10–15 minutes:

- overall level;
- notable skill levels/XP;
- current quest objective;
- useful equipment acquired;
- currency;
- meaningful reward received;
- time spent with no clear objective/reward.

Record subjective pacing separately from objective blockers.

### D3. Resource/enemy availability

Verify ordinary nearby enemies and starter gathering resources are available without excessive waiting or route abuse.

Record: unavailable/overcrowded resources, respawn issues, dead time.

### D4. Quest/equipment/crafting introduction

Acquire/equip a useful item, complete representative starter quest progress, gather at least two resource types where available, and craft a useful output through the normal UI.

Record: discovery path, required station/tool, result, XP/reward feedback.

## Class and combat feel

Test every playable class/archetype with enough ordinary combat to observe its core identity. The required classes are Vanguard, Berserker, Ranger, Rogue, Arcanist, Warden, Templar, and Spellblade.

For each class record:

- core identity is understandable;
- at least one offensive and one defensive/utility ability used where available;
- cooldown display/readability;
- resource cost/use;
- target selection/cycling;
- damage/heal/support feedback;
- server result visibly agrees with client feedback;
- stale target is cleared when invalid/dead/out of context;
- enemy threat/aggro response;
- death/recovery behavior if encountered.

Where practical, include at least one boss/elite encounter and record telegraph/readability, phase/mechanic clarity, reset/leash behavior, and reward.

Treat “fun”, “weight”, “speed”, “too easy/hard”, or similar feel as subjective unless an objective mechanic is broken.

## World, quests, resources, and bosses

Perform an ordinary-account walkthrough through representative:

- Wayfarer's Rest and Dawnreach;
- additional settlements/cities reachable in the session;
- outdoor biome/region transitions;
- normal travel links and return travel;
- interiors/interactables;
- quest NPCs and objective locations;
- resource nodes;
- merchants;
- crafting stations;
- hostile mobs;
- an elite/boss encounter;
- map/minimap/discovery.

Look specifically for:

- unreachable or blocked required geometry;
- soft locks/navigation traps;
- one-way transitions that are not intentional;
- stale/incorrect quest markers;
- quest objectives that cannot spawn/complete;
- duplicate quest rewards;
- bad resource/mob respawn;
- boss reset/reward anomalies;
- persistence loss after region travel or reconnect.

Record exact region/NPC/quest/resource/boss identifiers for every objective issue.

## Economy

Exercise ordinary acquisition and spending:

1. obtain loot and currency;
2. merchant buy;
3. merchant sell;
4. crafting ingredient/cost consumption;
5. verify resulting currency/item totals;
6. two-player trade if available;
7. auction listing/purchase if available.

For every transaction record before/after item quantities and currency. Repeat one cancellation/failure path where safe.

Objective defects include duplication, negative price/count, incorrect totals, item loss, stale consent, authority bypass, replayed completion, or transaction result disagreement.

“Too expensive/cheap” is SUBJECTIVE FEEDBACK unless it violates a documented target or creates a reproducible exploit.

## Social and multiplayer

Use two normal accounts/clients where practical. A second extracted client copy or a second Windows user/session is acceptable; do not use source-tree clients.

Exercise:

- nearby player visibility and movement synchronization;
- local/global/private chat as available;
- party create/invite/accept/leave and shared state;
- guild create/join/role/message behavior where practical;
- LFG behavior where available;
- trade consent, offer changes, cancellation, confirmation;
- reconnect one client while participating in social state.

Verify private messages/trade offer data are not exposed to outsiders.

Record synchronization issues separately from usability preferences. Active party/trade/LFG invitations may be intentionally transient; guild membership/message is durable and should survive reconnect/restart when changed.

## UI/UX and accessibility

Using mouse and keyboard, inspect and exercise:

- HUD and target frame;
- inventory/equipment/item comparison;
- crafting;
- quests/tracking;
- map/minimap;
- social/party/guild/LFG/chat;
- merchants/trade/auction;
- tooltips/combat messages;
- settings/keybind discovery;
- loading/transition/error feedback.

Verify:

- keyboard focus and mouse focus are visible and predictable;
- text entry does not also move/attack/activate gameplay;
- modals block underlying gameplay activation;
- Escape/back behavior is consistent;
- stale target/panel/transaction state clears appropriately;
- text is readable;
- scaling does not hide essential controls;
- panel layering is correct;
- useful UI state is preserved/reset sensibly.

Record the exact panel/control and input sequence for any defect.

## Physical Windows DPI/input

This is an owner-hardware inspection and must not be replaced by hosted/emulated CI.

Test 100%, 125%, and 150% Windows display scaling where practical. If a scaling change requires sign-out/relaunch, record that fact and relaunch the candidate normally.

At each tested scaling record:

- display resolution and scaling percentage;
- readable/unclipped text;
- panel clipping;
- click alignment;
- hover alignment;
- keyboard focus navigation;
- mouse interaction;
- fullscreen/windowed transition;
- at least one resolution change;
- whether UI remains usable after changing mode/resolution.

Capture a screenshot for any clipping/alignment problem.

## Art/visual review

Review at actual gameplay/native scale, not only enlarged source images.

Inspect:

- player/class appearance and equipment layering;
- NPCs;
- normal enemies and elites;
- bosses;
- animation states;
- combat/VFX;
- terrain;
- buildings/props/interactables;
- inventory/skill/quest/resource icons;
- UI consistency and background readability.

Record obvious placeholder/debug art, missing/broken sprites, incorrect layering, clipping, anchor jumps, scaling artifacts, unreadable contrast, or mismatched event/visual feedback.

Artistic preference without malfunction remains SUBJECTIVE FEEDBACK.

## Audio listening review

Use the recorded physical audio output device and actually listen.

Exercise:

- menu/music;
- city/wilderness/dungeon/boss music where reached;
- ambience;
- melee/ranged/spell combat SFX;
- creature/enemy feedback;
- gathering/interactions;
- UI clicks/notifications;
- level/reward feedback;
- region/combat transitions.

Listen for missing events, excessive repetition, clipping/distortion, extreme volume imbalance, mismatched sound/event, loops that fail to stop, duplicated playback, and abrupt transitions.

Record the event, region, approximate volume setting, and observed problem. Audio preference remains subjective unless playback is technically wrong.

## Final result record

Create one result table:

| ID | Section/check | PASS/FAIL/NOTE | Severity | Objective/subjective | Evidence / reproduction | Retest required |
| --- | --- | --- | --- | --- | --- | --- |

Then record:

- candidate SHA and SHA-256 actually tested;
- checks completed;
- checks not completed and why;
- RELEASE BLOCKER count;
- HIGH count;
- MEDIUM count;
- LOW/POLISH count;
- SUBJECTIVE FEEDBACK count;
- explicit owner decision: **approve candidate**, **do not approve**, or **acceptance incomplete**.

A repository/CI pass does not fill this human result record. Human results are added to repository evidence only after the owner reports them.

Even after human acceptance, do not create a public release/tag or deploy a public realm unless the owner explicitly authorizes that separate action.
