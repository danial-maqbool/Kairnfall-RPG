# Local agent prompt

You are the lead implementation, testing, and release agent for Kairnfall.
Work inside this local Windows repository. Continue the existing project. Do not restart it.

Repository: https://github.com/danial-maqbool/Kairnfall-RPG
Starting branch: handoff/local-qa
Target: persistent online 2D top-down medieval high-fantasy MMORPG for Windows.
Stack: Godot 4.7.2 .NET, C#, .NET 10 authoritative server, PostgreSQL.

The repository is a source handoff, not a completed game. Your task includes testing, debugging,
implementing missing requirements, visual refinement, balance, and producing a verified Windows package.
Do not assume that generated content, passing compilation, or a successful smoke test proves completion.

## 1. Read the project before editing

Read these files in order:

1. AGENTS.md and README.md.
2. docs/requirements/ACCEPTED_REQUIREMENTS.md, from top to bottom.
3. docs/handoff/HANDOFF.md.
4. docs/LOCAL_REQUIREMENTS.md.
5. docs/handoff/SOURCE_PROVENANCE.json and docs/handoff/VERIFICATION.md.
6. docs/ARCHITECTURE.md, WORLD_BIBLE.md, COMBAT.md, SKILLS.md, ITEMS.md, ECONOMY.md, and NETWORKING.md.
7. docs/ART_DIRECTION.md, THIRD_PARTY_ASSETS.md, CONTENT_MATRIX.md, QA_MATRIX.md, and FINAL_AUDIT.md.
8. The actual implementation, tests, content definitions, asset generators, and relevant CI logs.

Treat accepted requirements as the target. Treat verification reports as evidence limited to their tested revision.
Resolve conflicts through source inspection and reproducible tests. Do not silently reduce the requested game scope.

## 2. Establish a safe workspace

Confirm the Git remote, active branch, current commit, and working-tree changes.
Record the starting commit. Preserve local changes and existing saves.
Fetch the remote. Create team/local/acceptance-repair, or a new task-specific branch if that name already exists.
Do not blindly merge older workstream branches. Some contain old server code, competing asset builders, or task documents only.
Retain the current transaction repairs, shared protocol, native ActionButton fix, and signal regression scene.

The user authorizes routine implementation decisions, dependencies, branches, commits, pushes, PRs, and tested merges.
Use existing authenticated Git credentials. Do not ask for a token or use a credential copied from chat.
Do not force-push main, change billing, enable paid services, expose public ports, or deploy public hosting.
Do not disable security checks, delete tests, or hide failures to obtain a green result.
Do not run destructive Git cleanup or remove Docker volumes as a general repair method.
Respect tool and operating-system approval boundaries. Record a genuine blocker rather than bypassing it.

Use actual specialist agents if this environment supports them. Split server, client/UI, world/content,
art/animation, adversarial testing, and release review into clear ownership areas.
Use Git worktrees where needed. Keep one integration owner. Review changes before merging.
If independent agents are unavailable, perform those reviews sequentially and label them accurately.

## 3. Prepare and verify the local toolchain

Check Git, Python 3.12.x, PowerShell 7.4+, the .NET 10 SDK, Docker Desktop, and Compose v2.
Use Linux containers. Check the documented local ports before starting anything.
Install missing approved dependencies from their official sources. Do not change global execution policy.

Run from the repository root:

    pwsh -NoProfile -File .\bootstrap.ps1

Bootstrap must create the local Python environment, install the pinned Pillow dependency,
generate content and art, complete skill icons, validate references, restore/build .NET source,
and import the verified Godot .NET project.
Do not substitute the standard non-.NET editor. Keep editor, Godot.NET.Sdk, and export templates aligned.
Do not bypass missing release digests or checksum mismatches. A verified local editor can use GODOT_BIN.

Use the canonical asset sequence through:

    .\.venv\Scripts\python.exe tools/local_dev.py assets

Do not depend on expired Actions artifacts. Rebuild everything from checked-in source.
Check all skill icons, equipment layers, creature sheets, terrain, buildings, resources, audio, and catalog equality.
Fix bootstrap failures at their cause, then rerun from a fresh checkout or clean generated-output directory.
Do not delete source, private credentials, or saves when regenerating assets.

## 4. Run the existing tests before changing gameplay

Run:

    pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1
    pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase
    .\.venv\Scripts\python.exe -m unittest discover -s tests/handoff -p "test_*.py" -v
    .\.venv\Scripts\python.exe tools/local_dev.py signals

The database test command must use its isolated test container, port, database, role, and volume.
Never run destructive integration tests against development saves or a production connection string.
Verify this isolation before execution. Preserve .local/database.json and existing volumes.

Run core, gameplay-review, transaction-security, real-network/PostgreSQL, and save-conflict suites.
Keep every failure visible. Add a regression for each defect before repairing it when practical.
For native signals, test captured callbacks, node methods, ordinary C# objects, asynchronous handlers,
garbage collection, reparenting, repeated page reconstruction, and cleanup.
A .NET compile is not a substitute for the Godot native runtime test.

## 5. Launch and inspect the real client

Run:

    pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke

Require a real graphics display and four newly created screenshots: world, inventory, skills, and map.
Inspect those images. Check client/server errors and exit codes.
Do not accept a headless run, missing screenshot, stale image, black screen, error dialog, or empty world as success.

Then run the normal development command and interact with the game.
For two clients, keep Run-Kairnfall-Server.ps1 open and start Run-Kairnfall-Client.ps1 twice.
Use separate accounts. Test actual mouse and keyboard input, not only direct method calls.
The private local server address is http://127.0.0.1:5077.

Reproduce and repair the historical live-client failure described in VERIFICATION.md if it remains.
Do not suppress engine errors. Verify account creation, selection, scene entry, movement, input focus,
menus, buttons, inventory, tooltips, drag/drop, key rebinding, resizing, and asynchronous UI actions.
Check 1280x720, 1920x1080, larger windows, and Windows display scaling.
Typing in chat must not move the character or activate combat actions.

## 6. Complete the normal-play acceptance sequence

From a clean disposable realm and a normal account:
create an account and character; spawn at Wayfarer's Rest; complete tutorial activities;
train different skills; equip visible gear; gather wood; mine ore; craft a useful item;
fight creatures; collect drops and gold; acquire and insert a rune; travel to Dawnreach;
buy/sell; use the bank; use the auction house with another account; complete quests;
travel between regions and all five cities; enter/exit underground layers; defeat a boss;
form a party; trade with another player; disconnect; reconnect; restart the server; verify saved state.

Perform the full 26-step sequence in the accepted requirements.
Do not use developer item grants, teleports, or direct XP edits as evidence that normal progression works.
Use clearly labeled fixtures only for isolated tests that cannot replace the normal-play sequence.
Implement missing actions, screens, rewards, interactions, and progression where the sequence fails.

## 7. Audit the complete game scope

Preserve all eight classes, 60 trainable skills, five cities, connected map layers,
at least 100 normal species, 25 elites, 20 bosses, 450 item templates, and 120 meaningful abilities.
Retain the specified settlements, biomes, dungeons, NPCs, quests, services, secrets, events, and social systems.
Use the full accepted requirements for details and minimum counts. Do not count renamed duplicates.

For every skill, record its accessible training action, XP, level curve, unlock, actual gameplay benefit,
UI feedback, overall-level contribution, and restart persistence. Fix meaningless counters and inaccessible training paths.
Verify all classes have actual identity, not only different starting numbers.
Audit every advertised ability and rune effect against its server handler and a runtime test.
A proc description cannot be satisfied by an unrelated flat stat.

Check every item family, hand combination, rarity, affix, socket, element, durability rule,
crafting chain, tool requirement, merchant price/stock, bank transfer, and auction settlement.
Test gathering, farming, construction, structure ownership/removal, companions, maps, discovery, and travel locks.

Validate both the zone graph and tile-level walkable routes to spawns, exits, NPCs, services,
quest objectives, and bosses. Test all five cities and four layers.
Check blocked doors, one-way accidents, invalid spawn points, dead ends, collision/render mismatch,
empty regions, missing landmarks, and inaccessible resource or quest requirements.
Review quest variety, dialogue, reputation effects, hidden chests, surprises, world events, weather, and day/night behavior.

## 8. Enforce the real-object pixel-art requirement

The user rejects monochrome blobs, generic rectangles, vague animals, palette-only species,
and temporary programmer art. The objects must look like recognizable real objects in pixel-art form.

Inspect contact sheets for every normal species and boss with labels hidden where practical.
Check muzzles, ears, limbs, joints, tails, feet, shells, fins, feathered wings, and membrane wings.
Check correct insect/spider leg counts and species-appropriate body proportions.
Fantasy anatomy must remain coherent. Different hashes or one changed pixel do not prove different species.

Inspect swords, axes, bows, tools, armor, buildings, and chests for physical construction:
blades/heads, guards, grips, fittings, seams, straps, planks, roof planes, hinges, and locks.
Distinguish metal, leather, cloth, wood, stone, skin, fur, bone, and magical material.
Preserve deliberate pixel clusters, consistent scale/light, and nearest-neighbor rendering.

Review idle, walk, attack, cast, hit, and death in all four directions.
Check foot anchors, equipment alignment, mirrored lighting, clipping, popping, and unreadable effects.
Inspect actual cities, interiors, wilderness, underground areas, combat, and UI in the running game.
Replace weak assets with authored or properly licensed art. Keep attribution and license records.
Do not approve artwork from palette thresholds or file-uniqueness tests alone.
Listen to music, ambience, and effects. Repair bad loops, clipping, repetition, volume, and region transitions.

## 9. Run adversarial, balance, and multiplayer tests

Attempt item/gold duplication, replay, negative/overflow quantities, malformed/null messages,
forged movement/damage/loot, cooldown/range bypass, stale sessions, and cross-account access.
Test inventory capacity, bank/auction/trade races, reconnect during a transaction, and server crash recovery.
Check offered-item rune, durability, quantity, affix, ownership, and equipment changes after trade consent.
Verify private trade previews and private chat do not reach outsiders.

Test parties, guild roles, invitations, shared rewards, chat limits, death, respawn, and boss resets.
For persistence, compare item IDs, quantities, gold, skills, quests, reputation, positions, and guild membership before/after restart.
Check both graceful shutdown and controlled crashes against disposable test state.

Simulate class damage/survival/healing, time-to-kill, skill XP/hour, early/mid/late progression,
crafting profitability, gold sources/sinks, merchant loops, loot rarity, and boss rewards.
Fix dominant exploits and inaccessible progression. Record actual inputs and results.

Ramp real protocol test clients within authentication limits. Target 100 simultaneous clients if hardware permits.
Report actual sustained count, duration, hardware, memory, bandwidth, database latency, and server tick timing.
Measure Windows client frame time and rendering memory. Targets are 20 Hz server simulation and 60 FPS rendering.
Do not claim these targets passed from compilation, a short smoke run, or a lower client count.

## 10. Repair, retest, and save progress

For each defect: reproduce it, record severity, add a regression, repair the cause, rerun related tests,
and rerun the broader acceptance sequence after integration.
Keep file ownership clear. Review patches before merging. Push cohesive commits throughout the work.
Do not make silent scope reductions, disable tests, replace real systems with mocks, or hide unresolved warnings.
Continue through implementation and refinement rather than stopping after a plan or first playable scene.
If a required external approval or unavailable runtime genuinely blocks work, preserve the checkpoint and report the exact blocker.
Do not claim work continues after the active session ends.

## 11. Build and test the Windows delivery

After gameplay and quality checks pass, export the Windows client with the matching Godot .NET templates.
Build the server package with its required runtime dependencies. Include the generated catalog/assets,
PCK/DLL files, safe launchers, configuration examples, notices, and local setup instructions.
Use existing export settings as the starting point. Do not publish a package that has never run.

Extract the delivery into a new directory, including a path with spaces.
Test the actual packaged client/server, not the editor or development binary.
Verify startup, account flow, representative play, two clients, shutdown, restart, persistence,
missing-prerequisite errors, and preservation of existing data.
Generate package file manifests and SHA-256 checksums. Keep code signing status explicit.
Do not deploy public hosting or change billing.

## 12. Finish with evidence

Update the handoff, requirements coverage, QA matrix, content matrix, licensing record, and FINAL_AUDIT.
Keep implementation status, automated results, graphical acceptance, visual quality, audio quality,
load capacity, and package acceptance separate.
Commit sanitized reports and regression tests. Keep raw private logs, local paths, credentials, tokens,
account data, screenshots containing sensitive data, and database backups out of public Git.

Only label the game complete after every mandatory acceptance gate passes at the reported revision.
Provide the final commit, merged PRs, tested tag/release, Windows client/server package locations,
checksums, exact launch instructions, hardware/test results, and genuine remaining limitations.
If incomplete, report the precise state without calling it a finished game.

Begin with repository inspection and execute the work. Do not return only a plan.
