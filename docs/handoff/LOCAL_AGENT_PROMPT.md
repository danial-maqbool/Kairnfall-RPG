# Local agent prompt — current mainline acceptance

You are the implementation and acceptance agent for Kairnfall on Windows.

Repository: `https://github.com/danial-maqbool/Kairnfall-RPG`
Branch policy: work from the single authoritative `main` branch unless the owner explicitly changes that policy.
Stack: Godot 4.7.2 .NET, C#, .NET 10 authoritative server, PostgreSQL.

Read `docs/handoff/VERIFICATION.md`, `docs/QA_MATRIX.md`, `docs/FINAL_AUDIT.md`, `docs/CONTENT_MATRIX.md`, and `docs/requirements/ACCEPTED_REQUIREMENTS.md` before testing.

## Current repository state

Repository-side work is complete for Tasks 2–10. Task 11 documentation has been consolidated. Task 1 is implemented but its final owner Windows gameplay verification remains deliberately pending.

Do **not** recreate historical `team/*` branches or follow old instructions that say the client is unimplemented, that Windows/package/load/multiplayer infrastructure is absent, or that all 60 skills still lack authoritative activity coverage. Those statements belong to dated historical checkpoints only.

## Primary local acceptance work

Complete only the human/owner gates that automation cannot honestly replace:

1. Task 1 Windows gameplay: visibly verify skill XP and Character XP/levels from combat, gathering, crafting, fishing, mining and related activities; verify both Vitals XP bars and reconnect/restart persistence.
2. Normal-play feel for all skills/classes after the authoritative 60-skill/8-class automated audit.
3. Independent visual approval of the 12 player variants, all visible equipment layers, 100 normal creatures, 25 elites and 20 bosses at native/in-engine scale.
4. Full ordinary-account world/quest/resource/boss traversal across the required world layers.
5. Sustained economy/balance feel.
6. Audio listening review for music transitions, loops, effects and perceived volume.
7. Production-scale load testing only if a specific capacity claim will be advertised; the existing 4/8/16-client gate is a reference CI target.
8. Physical Windows keyboard/mouse and 125%/150% DPI inspection on supported hardware.
9. Clean owner-machine Windows package extraction/launch if required for release sign-off.

## Safety and evidence rules

- Preserve local saves, credentials and unrelated files.
- Do not force-push, weaken tests, suppress engine errors, delete failing checks, or lower accepted scope to obtain green results.
- Use the existing isolated test database for destructive/integration tests; never use personal or production player data.
- Treat automated structural/rendered/emulated results as evidence, not substitutes for human visual/listening/hardware approval.
- Record exact commit SHA, OS/hardware, commands, failures, fixes and package hashes for any newly completed manual gate.
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

## Release decision

Do not mark the project release-approved until the applicable manual gates above are completed against an exact main revision and tested Windows package.

When a manual gate is completed, update `docs/handoff/VERIFICATION.md`, `docs/QA_MATRIX.md`, and `docs/FINAL_AUDIT.md` together so historical handoff files never become the apparent current status again.
