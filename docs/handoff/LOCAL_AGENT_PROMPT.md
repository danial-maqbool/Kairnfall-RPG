# Local agent prompt — current mainline acceptance

Current status as of 2026-09-13.

Repository: `https://github.com/danial-maqbool/Kairnfall-RPG`  
Branch: single authoritative `main`  
Stack: Godot 4.7.2 .NET, C#, .NET 10 authoritative server, PostgreSQL  
Current implementation baseline: `3dce816eade22c93a8dad65eee6964be3e12fd52`  
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`

Task 13 is repository-side complete. `tests/IndependentQA` and the permanent `Task 13 adversarial acceptance` workflow cover forged ownership, invalid quantities, replay, private transaction state, cross-region cleanup, death/respawn, stale social commands, persistence identity and LFG ignore boundaries, while rerunning retained security/world/concurrency/database suites. Windows executes the new audit through `Test-Kairnfall.ps1`. See `docs/qa/INDEPENDENT_FINDINGS.md`.

This was same-agent adversarial verification and **must not be described as independent approval**. Task 14 was not started.

## Current evidence

- Exact Task 13 baseline: adversarial run `34768390034` and Build/verify run `34768386855`, both successful at `3dce816eade22c93a8dad65eee6964be3e12fd52`.
- Product/client/art/package source was unchanged by Task 13. Applicable retained gates remain verified at `d4d1b4ef409e4eec5cf6bfecfac197c2a764fc2f`; see `VERIFICATION.md` and `CURRENT_EVIDENCE.json` for exact IDs.
- The visual artifact is structural/render evidence only; artistic approval remains human.

## Local acceptance work still requiring humans/owner hardware

1. Owner Windows gameplay, XP/HUD visibility and reconnect/restart persistence.
2. Normal-play progression/class and sustained economy feel.
3. Independent human adversarial/gameplay review if independent approval is required.
4. Independent visual/art review at native/in-engine scale.
5. Full ordinary-account world/quest/resource/boss traversal.
6. Audio listening review.
7. Physical Windows keyboard/mouse/DPI inspection.
8. Owner-machine package extraction/launch where required.
9. Production-scale load testing only for a separately advertised capacity target.

Do not weaken tests, suppress engine failures, delete failing checks, or relabel automation as human approval. Use isolated test databases and keep credentials/private paths/database contents out of committed evidence.

Typical Windows flow:

```powershell
pwsh -NoProfile -File .\bootstrap.ps1
pwsh -NoProfile -File .\Test-Kairnfall-Local.ps1 -WithDatabase
.\.venv\Scripts\python.exe tools/local_dev.py signals
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1 -Smoke
pwsh -NoProfile -File .\Run-Kairnfall-Dev.ps1
```

`tools/documentation_contract.py` compares `CURRENT_EVIDENCE.json` with the latest non-documentation implementation commit and checks all current-facing status files for synchronized date, baseline and release boundary.

**NOT APPROVED — human acceptance remains.**
