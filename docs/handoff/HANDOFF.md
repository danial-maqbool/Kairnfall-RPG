# Kairnfall current source handoff

Current status as of 2026-09-13.

Use live `main` as the authoritative source line. Current implementation baseline: `3dce816eade22c93a8dad65eee6964be3e12fd52`.
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`.

Task 13 is repository-side complete. It adds `tests/IndependentQA`, Windows wiring through `Test-Kairnfall.ps1`, and the permanent `Task 13 adversarial acceptance` workflow. Findings/retests are in `docs/qa/INDEPENDENT_FINDINGS.md`. The work is same-agent adversarial verification, not independent approval. Task 14 was not started.

**NOT APPROVED — human acceptance remains.**

## Current technical state

- Exact Task 13 baseline `3dce816eade22c93a8dad65eee6964be3e12fd52`: Task 13 adversarial run `34768390034` and Build/verify run `34768386855` are successful.
- The Windows Build job executes the new audit and records 10/10 Task 13 scenarios passing.
- The dedicated Task 13 gate reruns transaction/privacy security, gameplay/malformed-input review, world/persistence/social checks, concurrency, PostgreSQL/network integration and isolated save-conflict checks.
- Task 13 did not alter production gameplay/client/art/package source. Retained product/client baseline `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f` remains the applicable evidence for load, client, live progression, graphical multiplayer, Windows package, display/input, visual and audio gates. Exact run IDs are in `VERIFICATION.md` and `CURRENT_EVIDENCE.json`.

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

Do not convert automated structural, rendered, emulated, protocol or same-agent adversarial results into those approvals.

`docs/handoff/VERIFICATION.md` is the narrative current evidence authority; `docs/handoff/CURRENT_EVIDENCE.json` is its machine-readable counterpart. `tools/documentation_contract.py` enforces synchronized date, baseline and release boundary.
