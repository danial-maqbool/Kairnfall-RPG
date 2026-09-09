# Targeting, density and XP: session-end checkpoint — 2026-09-09

This checkpoint respects the requested 60-minute session limit. The user was asked to send another message at the 55-minute checkpoint. It is not a claim that every requested update passed or is integrated.

## Already tested and pushed

Task 1 is integrated at `1628b73770393980bb2d1e8017345f2f830786d7`. It fixes the reported Tab-to-chat focus problem by handling only the configured target key before GUI focus traversal during active gameplay. Tab and Shift+Tab cycle eligible living creatures within 12 tiles and clear line of sight. Pets, corpses and other regions remain excluded. Chat, menus and rebind capture retain their normal priority. Selection does not issue an attack request.

Exact Task 1 source `f83381386a83644e5a6c9c5e3e3f045dc6212e0e` passed the full retained workflow `34304010081`, including native target-key checks. The integration preserves the original main history. No branch, force push, reset or release was used.

## Latest combined candidate and active verification

HUD-corrected candidate: `2a71d4970515ccf824330c21888993225ea6ed72`.
Candidate tree: `e671fc522acf442de9f57be25dd4361ed3348c84`.
Full run: `34307091318`.
Verify job: `102325962323`.
Test-request commit: `abc23621e75543f12677466f730b9c7a68b2edd5`.

At the last read, compilation had passed and the backend stage was in progress. Native and live-game verification had not finished. Do not install this candidate into main before the full required checks pass.

The candidate retains the doubled ordinary population and map-wide hunting layout, nonlinear XP formulas, preserved legacy levels, fractional weak-enemy practice, bounded attack mastery, short pursuit-window correction and challenge feedback in the HUD.

The latest main read before this documentation write was `238eced12e72ae7ce69903015805f2ea8c8576b9`. That newer commit changes only the preparation request for an additional support-XP refinement. Its request base is `eab1406ab5b17ba975b5a0fba1875ffa713a60ad`. It proposes actual recent-enemy context for support training instead of region-level difficulty, and extra adaptive HUD checks. Preserve that work. Inspect its preparation output and tests before choosing the newest candidate. This session-end record does not claim that the additional refinement has passed or is integrated.

## Most recent completed full verification

Run `34306324468` tested `e64810f6adf2d85eacea51bedb87f875e1ce8fda` and failed at the new native HUD overlap assertion. Diagnostic job `102325392876` was read.

Passed before that failure:

| Suite | Result |
| --- | --- |
| Solution and client compilation | Passed; client zero warnings/errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session and status security | 5 passed |
| Real-network/PostgreSQL / save conflicts | 18 / 5 passed |
| Retained world, migration, furnishings, equipment and hunting | Passed |
| Added population and distribution checks | 2 groups passed |
| Added challenge-XP and attack-curve checks | 9 groups passed |
| XP simulation scenarios | 50 produced |
| Python handoff and importer tests | 118 passed |
| Native signal lifetime and input routing | Passed |
| Native player-experience checks | 52 passed |
| Native control/HUD contract | Failed on vitals/objective overlap |
| Live graphical server/client stage | Not run after the failure |

The native regression correctly found that adding the XP row increased the vitals panel's height beyond the fixed objective-panel offset. The corrected candidate uses a shared vertical container with ten pixels of separation. Widget identities, initial screen position and input filtering remain intact. The overlap assertion, fixture resolutions and live encounter timeout were not relaxed.

Corrected `client/Scripts/GameRoot.Hud.cs` blob: `42decdce2c01e6dab5614eef6ccab84f90618865`.

## Retained task details

The density candidate's verified census is 9,302 initial creatures across 109 regions. Ordinary species use 60/40/30/20/10 spawn slots by the existing region-level bands. Boss and elite counts remain one. Services, interiors, arrivals, collision, separated spawn positions and saved pets remain protected. One introductory patch stays nearby; later patches cover deterministic sectors of the reachable map. Coverage checks passed on 20 eligible wilderness maps.

The earlier density-only live encounter failed when the initial short approach allowance expired after two confirmed hits, leaving a target at 0.2 HP. The current pursuit correction allows a newer authoritative attack acknowledgement to refresh a short 2.5-tile/1.5-second window. An absolute six-tile engagement bound still prevents uncontrolled pursuit. Replanning and rejected requests do not refresh the window. Full live verification remains required.

The XP candidate lowers the future overall contribution of training at levels 11, 21, 31 and later ten-level boundaries. A monster 20 levels lower gives approximately 9.4% skill practice before mastery/affinity and approximately 1.69% encounter credit before the overall pacing factor. Fractions accumulate instead of granting a whole XP point for every tiny hit. Raw skill XP and old earned levels remain unchanged. A gradual late mastery floor avoids a last-point jump at the cap. Monster statistics do not scale with player level.

The attack candidate replaces linear skill multipliers with bounded diminishing-return curves while retaining the established armor, resistance, critical, weather and damage-cap behavior. The target HUD explains practice and advancement separately.

## Recovery instructions

1. Fetch live main and inspect the latest `.ci` requests.
2. Read run `34307091318` and any newer support-XP preparation/verification results. Recover their exact candidate SHAs.
3. Repair actual failures without reducing the existing assertions or weakening server validation.
4. Integrate only the exact fully passing source onto the current main tree. Preserve intervening commits and candidate histories. Use `force: false` and confirm the remote ref afterward.
5. Copy documentation from candidate `765d03bf288ff04a0112e87f7780df9ccdfea644` only where still correct. Do not use its full source tree: it predates the corrected replay fixture, adaptive HUD and possible newer support changes.
6. Keep this and the earlier `TARGET_DENSITY_XP_2026-09-09.md` as scoped history. Publish a new final verification record when the combined source actually passes and is integrated.

Do not use prepared tree `acd98b413cb7c007f5975a852055bcbd088637a0` as a final integration. It predates the container-layout fix and newer main metadata.

## Research and acceptance limits

The input repair follows Godot's documented ordering of `_Input`, GUI handling and `_UnhandledInput`. The experience design uses the general level-gap/high-level slowdown principles documented in Blizzard's Diablo II experience guide. The numeric KAIRNFALL coefficients are original design choices, not copied reference-game formulas or proof of final balance. References and equations are retained in the candidate's `docs/CHALLENGE_BALANCE.md`.

No independent coding-agent team ran. Discovery exposed customer-support agents, not a suitable coding-agent team. CI jobs and separate test suites are not independent coding agents.

Independent image inspection, human progression/balance testing, physical Windows input, DPI, audio listening, sustained multiplayer load, measured client frame rate and package/release acceptance remain open. The runtime did not provide working local execution or image inspection in this session. No whole-game completion, packaged release, tag, credential change or save deletion is asserted.
