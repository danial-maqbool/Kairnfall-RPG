# Kairnfall current source handoff

Current status as of 2026-09-13.

Use live `main` as the authoritative source line. Current implementation baseline: `83a99948c7e96ff1ed568b5090b3138294b8e713`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 15 is repository-side complete. `src/release-operations.trigger` permanently identifies the release-engineering/recovery acceptance surface without authorizing publication. The accepted Task 15 technical baseline is `83a99948c7e96ff1ed568b5090b3138294b8e713`. Task 16 was not started.

**NOT APPROVED — human acceptance remains.**

## Current technical state

Ten Task 15 workflows are successful at `83a99948c7e96ff1ed568b5090b3138294b8e713`: Build and verify, Task 13 adversarial acceptance, load, both transaction gates, Windows client compilation, live progression, graphical multiplayer, Windows package, and release operations. Exact run IDs are in `VERIFICATION.md` and `CURRENT_EVIDENCE.json`.

Task 15 adds and verifies:

- fail-closed PostgreSQL schema-history compatibility;
- a reusable backup/verify/restore operations utility using `KAIRNFALL_DB` rather than database credentials in command arguments;
- fresh-target restore with checksum metadata and tamper rejection;
- rollback-boundary proof separating post-backup mutations from restored state;
- duplicate authoritative-writer rejection and future-schema rejection;
- a Windows operations archive plus per-file/archive checksums;
- a structured candidate manifest and bundle with `publicationReady: false`;
- release setup, limitations and audit documentation;
- a graceful client disconnect persistence boundary after the first candidate exposed post-disconnect defensive XP mutation.

The current live-progression retest is run `34772773727`; the recovery gate is `34772773748`; the Windows package gate is `34772773761`.

Task 14's display/input, visual and technical-audio results remain historical at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. They are retained with their original SHA rather than being restated as Task 15 exact-SHA proof.

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

Do not convert automated structural, rendered, hosted, protocol, recovery, release-candidate or same-agent adversarial results into those approvals.

`docs/handoff/VERIFICATION.md` is the narrative current evidence authority; `docs/handoff/CURRENT_EVIDENCE.json` is its machine-readable counterpart. `tools/documentation_contract.py` enforces the current Task 15 baseline/run set, historical Task 14 provenance, both permanent sentinels and the unchanged release boundary.
