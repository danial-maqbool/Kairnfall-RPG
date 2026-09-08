# QA acceptance matrix

## Equipment and crafting QA — 2026-09-09

Current equipment results are in the [exact-source checkpoint](handoff/EQUIPMENT_PROGRESSION_2026-09-09.md). Every grade has skill-boundary and authoritative crafting coverage. Native tests cover guide selection, pinned actions, ingredient errors, bounded recipe pages, snapshot stability and scene cleanup. Server tests reject blocked or foreign workstations without state changes. Graphical renders cover 1280 by 720 and 1920 by 1080. Independent image review and Windows 125%/150% scaling remain open. Historical results below remain scoped to their stated revisions.

Current exact-source results: [action presentation checkpoint](handoff/ACTION_PRESENTATION_2026-09-08.md).
Full run `34258153781` and graphical run `34258153880` passed for source `dd3900bd1dcdb3baa3a7860bcdd7a306e47fa159`.
Results include 33/34/13/18/5 backend/database checks, five security probes, five migration groups,
seven furnishing checks, 94 Python tests, 51 native player checks, 601 native control checks,
83 live client/server checks, and 126 graphical fixture checks.
New coverage includes real WorldView timing, native objective clicks, ability-panel reattachment,
style resource reuse, icon geometry, and species-specific action phases.
Graphically rendered is not independently visually approved. Windows DPI, human playtesting,
audio listening, measured performance, and extracted packages remain unapproved.

Previous Windows evidence: [September 8 visual repair](handoff/LOCAL_VISUAL_REVIEW_2026-09-08.md).
Bootstrap, 103 backend/database checks, 74 Python tests, native signals/input,
102 visual-fixture checks, 83 isolated live checks and inspected graphical smoke
passed. Visual approval is incomplete. DPI, full manual gameplay, audio, load
and extracted Windows packages remain unapproved.

Historical evidence: [September 7 Windows acceptance](handoff/LOCAL_ACCEPTANCE_2026-09-07.md),
source `90143df`. Backend/database 99, security probes 5, save-migration groups 5,
Python tests 35, native
signals/input, structural assets, and focused world paths passed. Graphical smoke
and selected mouse flows passed; art approval failed. Full bootstrap timed out on
export templates. Keyboard/scaling, full gameplay, audio, sustained load, and
extracted packages remain open. The matrix below still defines mandatory gates.

This matrix defines required checks. Consult handoff/VERIFICATION.md for actual results.
Pending rows are not passed by document creation.

| Area | Required check | Evidence |
| --- | --- | --- |
| Source handoff | Fresh clone, required files, dependency pins, scripts, generated references. | CI plus local bootstrap log. |
| Local data safety | Distinct dev/test databases, no save deletion, password preservation, port conflicts. | Contract tests plus real local integration. |
| Backend | Core, review, security, network/PostgreSQL, save conflicts. | Native outputs and exact commit. |
| Native UI | Captured/node/plain-object/async callbacks, GC, reparent, repeated pages. | Godot SignalContract result. |
| Graphical startup | Real client login/world plus fresh world/inventory/skills/map captures. | Non-headless run and inspected screenshots. |
| Normal play | All 26 accepted clean-account steps without reward cheats. | Reproducible walkthrough/recording. |
| World | Graph and actual tile connectivity to cities/services/layers/objectives. | Automated routes plus in-game checks. |
| Progression | All 60 skills, class identity, unlocks, costs, overall level, persistence. | Per-skill and per-class records. |
| Economy | Craft chains, shops, bank, auction, trade/replay/races, gold sinks. | Invariants and balance outputs. |
| Combat | All ability kinds, status/element outcomes, equipment constraints, bosses. | Regressions and live encounters. |
| Art | Full species/boss review, equipment animation, cities, UI, telegraphs. | Named reviewed files and captures. |
| Audio | Actual playback, region changes, loops, clipping, volume, effects. | Listening review and defects. |
| Multiplayer | Independent clients, private data, shared state, reconnect, restart. | Real protocol traces with secrets removed. |
| Load | Sustained concurrency and resource measurements on known hardware. | Duration, count, tick/frame/DB metrics. |
| Windows package | Export, complete files, extract/run, space-containing path, restart. | Clean-directory execution and checksums. |
| Release | All accepted scope gates, no unresolved blockers, truthful docs. | FINAL_AUDIT and tested tag. |

Review TODO/FIXME/PLACEHOLDER/TEMP/MOCK/STUB occurrences individually.
Mocks in isolated tests can be valid. Runtime placeholders in required gameplay are unresolved work.
Do not delete failing tests, hide engine errors, or use allow-failure flags to pass acceptance.
