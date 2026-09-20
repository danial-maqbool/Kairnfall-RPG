# Independent adversarial and acceptance review

This workstream reviews implementation independently. It must not claim an audit passed without reproducible evidence.

## Ownership

Own new tests under `tests/IndependentQA/` and reports under `docs/qa/`. Do not change production client, server, world data, art, or release files. Return confirmed defects to the responsible implementation PR. Do not repair a defect and then present the same pass as an independent review of another author's fix.

## Review targets

Read AGENTS.md and current main. Review the Godot client, .NET authoritative server, PostgreSQL persistence, catalog, source-art contracts, and existing tests. Track implementation PRs #9 (creature art), #10 (server transactions), #11 (Windows packaging), #12 (world/content), and #14 (client refinement) where accessible. State the exact commit reviewed. Do not assume an open PR is integrated.

## Required tests

- Reproduce economic failures with negative, excessive, repeated, stale, concurrent, or ownership-forged commands in an isolated test realm.
- Check trade consent against mutations of offered item contents, quantities, runes, durability, and gold. Check private trade preview and chat isolation.
- Check actual movement, collision, map transitions, resource/service reachability, death, respawn, item identity, disconnect, and persisted restart behavior.
- Check every claimed skill and UI feature against a real command, progression event, and observable gameplay effect. Catalog counts and empty windows are not completion.
- Check client input/focus, UI refresh during editing, key rebinding, hotbar cooldowns, quest availability/turn-in, crop IDs, services, rune operations, bank, auctions, party, guild, and trade. Add reproducible focused tests or exact manual reproduction steps.
- Run the existing suites and any new independent tests. Do not weaken production validation or alter tests simply to obtain green results.
- For art, inspect actual rendered frames/contact sheets and in-engine screenshots when available. Numeric color counts and image dimensions do not prove visual quality. Check real-object anatomy/materials, four directional views, frame alignment, equipment layers, recognizability, and absence of placeholder actors. The asset pipeline is a known dependency; do not fabricate images or claim unavailable rendering was reviewed.
- Evaluate Windows packaging and real-client smoke evidence. Distinguish source compilation, export, native execution, live multiplayer, and measured load performance.

## Report

Write `docs/qa/INDEPENDENT_FINDINGS.md` with severity, exact file/line or scenario, reproduction, expected versus actual result, tested commit, responsible workstream, and status. Include passing and blocked checks, exact commands, and test counts. Keep initial findings separate from retest results. Do not merge, publish a release, alter billing, enable paid services, or bypass tool restrictions.
