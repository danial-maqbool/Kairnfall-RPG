# Targeting, population and XP checkpoint — 2026-09-09

## Integration status at this checkpoint

Task 1 is tested and integrated on main at `1628b73770393980bb2d1e8017345f2f830786d7`. It handles the configured target key before Godot GUI focus traversal during active gameplay only. Tab and Shift+Tab select eligible living creatures within 12 tiles and clear line of sight. Pets, corpses and other regions remain excluded. Chat and menus retain ordinary keyboard navigation. Targeting does not attack automatically.

Exact tested Task 1 source: `f83381386a83644e5a6c9c5e3e3f045dc6212e0e`. Full run `34304010081` passed. Native generated-input tests exercise Tab, reverse selection, focused HUD buttons, text/menu priority, key-repeat suppression, range and stale-target cleanup. The last source comparison confirmed only current request metadata differs from the integration.

Tasks 2 and 3 are implemented as a retained candidate but are NOT yet approved or installed in main at the time of this record.

Current verification candidate: `e64810f6adf2d85eacea51bedb87f875e1ce8fda`.
Current full run: `34306324468`, verify job `102323699095`.
Current test-request commit: `ddf4175c57bc6caf8bf7bc21baf0e8b7ed2cbd24`.
Starting source: `4d45f8b7aff4c06152645d71c394f81baee78c38`.

Do not interpret a prepared candidate or request commit as source integration. Read the current run result and live main ref before continuing. Preserve intervening changes and use only non-forced fast-forward updates to main.

## Task 2: more mobs across the map

Candidate hunting revision 3 doubles ordinary population from 30/20/15/10/5 to 60/40/30/20/10 for region levels 0-20/21-40/41-60/61-80/81+. Boss and elite counts remain one. Safe interiors, services, arrival points, collision and initial actor separation remain protected.

One introductory patch per species remains near the arrival area. Later patches use deterministic 4-by-4 sectors across the reachable floor rather than an expanding arrival-centered ring. The existing layout search fails rather than silently dropping requested creatures.

The first density candidate `bae2e5f614d398a3cf6cc3b342f5d3e6defce2ef` passed its backend/database, migration, population, Python and native-control stages. Its census was 9,302 creatures in 109 regions. Two-axis coverage checks passed on 20 eligible wilderness maps. Its separate graphical workflow `34304864218` passed.

Its full run `34304864206` FAILED at the live starter encounter: two attacks left the target at 0.2 HP, but the single initial approach budget had expired. The held attack stopped while the target escaped. The original live encounter timeout was not extended.

The current candidate corrects that control path. Only a newer server-acknowledged attack cooldown can reopen a short 2.5-tile/1.5-second approach window. Replanning or rejected requests cannot reset it. An absolute six-tile engagement-origin bound prevents uncontrolled pursuit. The native fixture checks accepted versus unchanged acknowledgements and the absolute bound. Release, typing, menus, death and disconnection retain their existing cancellation behavior.

## Task 3: nonlinear growth, enemy challenge and HUD

The candidate separates raw skill practice from future overall-level credit. Matching-level combat earns normal practice before the existing skill and class factors. A monster 20 levels below the player earns little practice and much less overall credit. Fractional awards accumulate; tiny hits do not each receive a free whole XP point.

Future overall credit falls at levels 11, 21, 31 and subsequent ten-level boundaries. Noncombat raw skill awards retain their existing formula, while their overall contribution uses the same pacing bands. No monster health, damage, armor or loot definition is scaled with the player's level.

Legacy raw skill XP and earned levels are preserved. New fields track practice-only XP and fractional credits. A gradual late-game mastery floor preserves access to overall level 200 without a last-point jump. Attack skill factors use bounded diminishing-return curves. Existing armor/resistance, critical, weather and health-damage caps remain.

The candidate HUD adds an overall-credit rate and next band to the vitals area. The selected-target panel explains challenge, practice and credit rates. Native tests require readable bounds at 1280x720 and 1920x1080, including separation from the objective tracker.

The first combined run `34306021562` passed compilation, core, gameplay-review, transaction-security and eight of nine added XP groups. Its real-kill replay fixture used an invalid short request ID and was rejected before combat. Candidate `e64810f6adf2d85eacea51bedb87f875e1ce8fda` changes only that test identifier to a standard GUID. Production validation and replay assertions remain unchanged. The complete suite must be rerun.

The 50-scenario balance output is `artifacts/experience/balance/xp-curves.json`. Distribution output is `artifacts/experience/hunting/distribution.json`. A simulation is not human balance acceptance.

## Research and review boundaries

Godot's official input-flow documentation explains why GUI traversal consumed the original Tab key: https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html .

Blizzard's official experience guide uses level-gap penalties and slower high-level advancement: https://classic.battle.net/diablo2exp/basics/experience.shtml . This informed the design principles only. The KAIRNFALL equations are original tuning, not copied game constants or proven optimal balance. The complete candidate explanation is `docs/CHALLENGE_BALANCE.md`.

No independent coding-agent team ran. The discovered Zeiko actions are customer-support tools, not coding agents. No suitable installed coding-team runtime was available after plugin discovery. CI jobs and different test suites must not be presented as independent agents.

Container execution and Python access were unavailable in this session. Graphical workflows produce native screenshots, but independent image inspection, physical Windows input/DPI, long-term balance, sustained multiplayer performance, audio listening and package acceptance remain open.

## Safe continuation

Check full run `34306324468` first. If it fails, read its diagnostics and repair the actual defect or invalid fixture without reducing assertions. If it passes, compare the candidate to current main and integrate the exact passing source without overwriting newer work.

The documentation-only candidate `765d03bf288ff04a0112e87f7780df9ccdfea644` contains reviewed README, player-guide and handoff updates. It was based on the previous source before the test-GUID correction. Copy only its documentation blobs, never its entire tree over the corrected source.

Do not delete saves, local credentials, downloaded tools, partial verified downloads or Docker volumes. Do not create a release or mark the entire game complete. Respect the user's 60-minute session limit and request another message at the 55-minute checkpoint if verification is still incomplete.
