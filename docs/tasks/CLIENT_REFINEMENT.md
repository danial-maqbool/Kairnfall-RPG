# Client refinement and interaction

This is an implementation task, not a statement that the game is finished.

## Ownership

Own `client/`, new client tests, and `docs/qa/CLIENT_REFINEMENT_REVIEW.md`. Do not modify server/core, content IDs, art generators, or release scripts. Read current main after the recent client merges. Preserve one functional Godot entry point that uses the real GameConnection and authoritative server. Do not substitute a local mock or unrelated demo scene.

## Required work

1. Compile and review the whole C# client. Fix lifecycle, input, focus, layout, navigation, and race defects. Verify one working main scene and assembly. Set proper close handling and dispose network state. Reconnect must preserve the persisted character and must not replay arbitrary economic actions.
2. Fix quest markers and completion UI using the actual server `QuestProgress.Complete` semantics. Handle repeatable-quest availability and cooldowns. Check crop_wheat versus wheat_crop resource IDs and growth presentation.
3. Keep search boxes, quantity inputs, selected items, and scroll positions stable while snapshots arrive. A periodic panel refresh must not destroy a focused editor or reset an offer silently. Verify 1440x900 and 1024x720 layouts. Avoid clipping, overlapping panels, unreadable tooltips, and disappearing buttons.
4. Complete usable controls for existing legitimate commands: meditate, track, prospect, tame, feed, chart, plant, read, build, gathering, loot, rune insertion/extraction, shops, bank, auctions, party, guild, and two-stage trade. Do not invent client-owned rewards or unsupported server commands. Check ability cooldown key names against RealmCombat, not assumptions.
5. Implement inventory stack-splitting UI against the authoritative `split` command after server PR #10 provides it. Keep quantity conservation, ownership, and error handling. Do not fake splitting only on the client.
6. Validate rebind conflicts and reserved keys. Arrow-key movement must remain usable. Chat must use the server's actual 240-character bound, literal text rather than executable markup, correct channels, timestamps, and mute behavior.
7. World PR #12 is adding `WorldMap.DecorationAt(ZoneDef,int,int)` and shared solid-prop collision. Consume that API when integrated. Do not maintain contradictory local geometry or put forest trees in underground moss. If the dependency is not yet present, report that exact integration dependency without breaking the current build.
8. Preserve native pixel alignment, nearest-neighbor sampling, layered equipment, directional animation, and server interpolation. Use actual generated assets, not rectangles or colored circles as final actors. Make the HUD, inventory, skills, classes, abilities, quests, map, services, and settings look like one game.

## Evidence and dependencies

Compile the Godot 4.7.2 .NET client. Run available client tests. Run the real networked `-- --smoke` test with actual assets and an isolated server when the asset pipeline is integrated. Capture and inspect real viewport screenshots. Mark unexecuted render tests as unexecuted. Art generation is owned by the orchestrator and PR #9; do not fabricate placeholder assets to force a green run. Commit working fixes on this branch. Do not merge, publish a final release, alter billing, enable paid services, or bypass permissions.
