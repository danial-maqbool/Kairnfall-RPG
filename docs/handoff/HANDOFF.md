# Kairnfall current source handoff

Current status as of 2026-09-13.

Use live `main` as the authoritative source line. Current implementation baseline: `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 14 is repository-side complete. `src/release-candidate.trigger` permanently forces the accepted automated matrix onto one exact source candidate; Windows display/input, visual and audio workflows were extended to watch the sentinel because the remaining accepted workflows already watched `src/**`. See `docs/qa/RELEASE_CANDIDATE_ACCEPTANCE.md`. Task 15 was not started.

**NOT APPROVED — human acceptance remains.**

## Current technical state

All twelve Task 14 technical workflows are successful at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`: Build and verify, Task 13 adversarial acceptance, load, both transaction gates, Windows client compilation, live progression, graphical multiplayer, Windows package, Windows display/input, visual acceptance and audio acceptance. Exact run IDs are in `VERIFICATION.md` and `CURRENT_EVIDENCE.json`.

The matrix covers Linux/Windows core behavior, adversarial authority, PostgreSQL/network/save conflicts, concurrency, 2/10/25/50-client load, native Godot/client contracts, progression, two-client graphical multiplayer, Windows export/restart/reconnect, display/input, structural/native visual validation and technical audio.

## Local development

Godot 4.7.2 .NET, .NET 10 and PostgreSQL remain the project stack. Preserve local saves/settings and use only isolated disposable databases for destructive tests.

Typical Windows flow:

```powershell
pwsh -NoProfile -File .\bootstrap.ps1
pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase
.\.venv\Scripts\python.exe tools/local_dev.py signals
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1
```

## Human acceptance still pending

Owner Windows gameplay/persistence, subjective progression/class/economy feel, independent human QA where required, independent visual/art approval, full ordinary-account traversal, audio listening, physical Windows DPI/hardware-input review, owner-machine package verification where required, and production-scale validation for any advertised capacity remain human gates.

Do not convert automated structural, rendered, emulated, protocol, release-candidate or same-agent adversarial results into those approvals.

`docs/handoff/VERIFICATION.md` is the narrative current evidence authority; `docs/handoff/CURRENT_EVIDENCE.json` is its machine-readable counterpart. `tools/documentation_contract.py` enforces synchronized date, baseline, exact Task 14 workflow set, sentinel and release boundary.
