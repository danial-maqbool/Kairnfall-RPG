# Equipment update: final automated checks — 2026-09-09

This record closes the automated verification of the equipment extension. It does not close whole-game acceptance or approve a Windows release.

## Published implementation

The inspected main ref was `fc479635221934c51825ad605fc5b28acb9ce7e4`. The branch listing contained only `main`.

Actual implementation commits retained in that history:

- `b9dadef30bfd5747ff8a44c85c534bf22852dae7`: complete equipment tiers and bounded crafting browser.
- `4c560ccadf6a43ab4d0601844a8e200190795bd9`: workstation line-of-sight and ownership checks.
- `10ff887834d487b4ad5c721461a6835c2a2b2563`: equipment/tool maintenance and native maintenance controls.

`fc479635221934c51825ad605fc5b28acb9ce7e4` requests final exact-source verification of the integrated source at `10ff887834d487b4ad5c721461a6835c2a2b2563`. The implementation is already in main. It is not held only in an unreferenced candidate.

See [Equipment progression](../EQUIPMENT_PROGRESSION.md) for the complete grade table and player instructions. See [the equipment checkpoint](EQUIPMENT_PROGRESSION_2026-09-09.md) for source files, acquisition rules and earlier exact-source evidence.

## Final executed workflows

| Workflow | Run | Result |
| --- | --- | --- |
| Full exact-source verification | [34274766312](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34274766312) | Passed |
| Native graphical fixtures | [34274766337](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34274766337) | Passed |
| Main core and Windows core | [34274766345](https://github.com/danial-maqbool/Kairnfall-RPG/actions/runs/34274766345) | Both jobs passed |

The full run's diagnostic job is `102227501067`. Its revision record identifies the integrated source at `10ff887834d487b4ad5c721461a6835c2a2b2563`.

| Retained or added suite | Observed result |
| --- | --- |
| Client Debug compilation | Zero warnings and errors |
| Core / gameplay review / transaction security | 33 / 34 / 13 passed |
| Session and status-damage security probes | 5 passed |
| Real-network/PostgreSQL / save conflicts | 18 / 5 passed |
| Save migration / furnishing groups | 5 / 7 passed |
| Equipment progression groups | 11 passed |
| Equip-boundary cases | 924 passed |
| Authoritative crafting paths | 1,071 passed |
| Workstation-access groups | 2 passed |
| Equipment-maintenance groups | 4 passed |
| Python handoff tests | 107 passed |
| Native signal lifetime and input routing | Passed |
| Native player-experience checks | 51 passed |
| Native control/layout checks | 887 passed |
| Live Godot/server/PostgreSQL checks | 83 passed |
| Authenticated graphical smoke | Passed |

The earlier maintenance candidate's graphical run `34273676520` passed 179 native presentation checks. Its logs retain successful construction of the 21 grade review sheets and the representative equipment galleries. The final integrated graphical workflow above also completed its rendering and evidence-upload steps.

The crafting paths use isolated `RealmEngine.Execute` fixtures. They are not 1,071 manual or network playthroughs. The separate network tests use real HTTP/WebSocket and PostgreSQL. Native UI tests use generated Godot input. Windows core tests do not establish Windows graphical or display-scaling acceptance.

## Scope retained

The extension contains 21 matching-skill tiers through 100 and 51 families per tier. It includes weapons, three armor weights, offhands, accessories and working tools. It retains original saved template identifiers, existing recipes and the established skill cap. Material grade remains separate from rarity and runes.

The Upgrade guide exposes actual item requirements and crafting routes. The crafting browser limits its visible recipe list to 32 entries per page and keeps the Craft action outside the scroll area. Server checks remain responsible for materials, skill requirements, ownership, station access, action sequence and output.

Maintenance now handles damaged backpack tools as well as equipped gear. Repair and salvage preserve server-side ownership and reject inappropriate material targets. Native checks cover the maintenance controls. These are scoped repairs, not proof that every other game system has passed acceptance.

## Evidence limits and continuation

Independent inspection of the new image outputs was not completed in this chat. Container and Python execution returned `ClientError`. Attempts to open public image previews did not produce an image view. Successful generation and rendering therefore remain separate from visual approval.

Still open:

- Independent review of every required grade icon and representative equipped animation.
- Ordinary-account progression, acquisition pacing and a complete manual gameplay acceptance sequence.
- Windows physical input and 125%/150% display scaling.
- Two simultaneous graphical clients, audio listening, sustained load and measured performance targets.
- Verified Windows exports, extracted-package tests, package checksums and release approval.

No release tag, package approval or whole-game completion is asserted. Preserve saves, credentials, local tools and Docker volumes. Rebuild the client and server from the same current catalog before the next local test. Do not restore an older candidate over main.
