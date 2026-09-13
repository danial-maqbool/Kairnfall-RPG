# Local agent prompt — current mainline acceptance

Current status as of 2026-09-13.

You are the implementation and acceptance agent for Kairnfall on Windows.

Repository: `https://github.com/danial-maqbool/Kairnfall-RPG`
Branch policy: work from the single authoritative `main` branch unless the owner explicitly changes that policy.
Stack: Godot 4.7.2 .NET, C#, .NET 10 authoritative server, PostgreSQL.
Current implementation baseline: `3c4b6195e23f00fd34ae61e861dc7be2a2dadee3`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 12 adds synchronous modal cleanup and focus restoration, correct mouse/layer ordering, keyboard-following overflow for all existing pages, context-item cleanup, text/display setting resilience and current keybind discovery. See the [Task 12 engineering record](../UI_UX_ENGINEERING.md). Task 13 was not started. These are automated engineering results; subjective usability and physical monitor DPI remain human evaluation.

Read `docs/handoff/CURRENT_EVIDENCE.json`, `docs/handoff/VERIFICATION.md`, `docs/QA_MATRIX.md`, `docs/FINAL_AUDIT.md`, `docs/CONTENT_MATRIX.md`, and `docs/requirements/ACCEPTED_REQUIREMENTS.md` before testing.

## Current repository state

Repository-side technical work is integrated and the exact current baseline passed the retained build, load, transaction-security/integrity, Windows client, live progression, graphical multiplayer and Windows package workflows. The current reference load gate is 2, 10, 25 and 50 clients. `/play` admission is bounded at 120 attempts/minute/source before handshake work and has real-network 429 regression coverage.

Do **not** recreate historical `team/*` branches or follow dated instructions that claim the client, package, load, multiplayer or authoritative progression infrastructure is absent. Historical files remain evidence only for the revisions where they were written.

## Primary local acceptance work

Complete only human/owner gates that automation cannot honestly replace:

1. Owner Windows gameplay: visibly verify skill XP and Character XP/levels across representative combat, gathering and crafting activities; verify Vitals feedback and reconnect/restart persistence.
2. Normal-play feel for progression and class identity after the retained authoritative audits.
3. Independent visual approval at native/in-engine scale.
4. Full ordinary-account world/quest/resource/boss traversal across required layers.
5. Sustained economy/balance feel.
6. Audio listening review for transitions, loops, effects and perceived volume.
7. Production-scale load testing only if a specific capacity claim will be advertised; the existing 2/10/25/50-client gate is reference CI evidence.
8. Physical Windows keyboard/mouse and DPI inspection on supported hardware.
9. Clean owner-machine Windows package extraction/launch if required for release sign-off.

## Safety and evidence rules

- Preserve local saves, credentials and unrelated files.
- Do not force-push, weaken tests, suppress engine errors, delete failing checks or lower accepted scope to obtain green results.
- Use the isolated test database for destructive/integration tests; never use personal or production player data.
- Treat automated structural/rendered/emulated results as evidence, not substitutes for human visual/listening/hardware approval.
- Record exact commit SHA, OS/hardware, commands, failures, fixes and package hashes for newly completed manual gates.
- Keep credentials, tokens, private Windows paths and account/database contents out of committed evidence.

## Typical Windows flow

```powershell
pwsh -NoProfile -File .\bootstrap.ps1
pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase
.\.venv\Scripts\python.exe tools/local_dev.py signals
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1
```

For multiple graphical clients, run the server separately and start two clients with different accounts.

## Documentation rule

When implementation or acceptance evidence changes, update `docs/handoff/CURRENT_EVIDENCE.json` and the current-facing status documents together. `tools/documentation_contract.py` compares the ledger baseline to the latest non-documentation implementation commit; stale evidence must fail the permanent documentation workflow rather than silently becoming current.

## Release decision

**NOT APPROVED — human acceptance remains.**

Do not mark the project release-approved until the applicable manual gates above are completed against an exact main revision and tested Windows package.
