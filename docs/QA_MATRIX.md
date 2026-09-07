# QA acceptance matrix

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
