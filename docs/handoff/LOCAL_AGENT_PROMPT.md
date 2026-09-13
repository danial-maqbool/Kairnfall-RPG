# Local agent prompt — current mainline acceptance

Current status as of 2026-09-13.

Repository: `https://github.com/danial-maqbool/Kairnfall-RPG`  
Branch: single authoritative `main`  
Stack: Godot 4.7.2 .NET, C#, .NET 10 authoritative server, PostgreSQL  
Current implementation baseline: `83a99948c7e96ff1ed568b5090b3138294b8e713`  
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`

Task 15 is repository-side complete. The permanent `src/release-operations.trigger` represents release engineering and operational recovery without publishing a release/tag. Ten technical workflows passed at the exact Task 15 implementation baseline. Task 16 was not started.

**NOT APPROVED — human acceptance remains.**

## Current evidence

Exact Task 15 implementation baseline: `83a99948c7e96ff1ed568b5090b3138294b8e713`. `CURRENT_EVIDENCE.json` and `VERIFICATION.md` record the ten successful exact-SHA run IDs spanning build/adversarial authority, transactions, load, Windows client/package, progression, graphical multiplayer and release operations.

Release operations prove disposable PostgreSQL backup/verify/fresh-restore, rollback boundary, duplicate-writer and future-schema fail-closed behavior, tamper rejection and restored reconnect. Windows packaging includes a client archive, server archive, operations archive, checksums, setup/limitations/audit material and a structured manifest that remains `publicationReady: false`.

The initial Task 15 candidate exposed a real reconnect-persistence race; `83a99948c7e96ff1ed568b5090b3138294b8e713` adds an authenticated graceful-disconnect acknowledgment so normal client disconnect completion follows authoritative detach/persist. Live progression passed at run `34772773727`.

Task 14 Windows display/input, visual and technical-audio evidence remains pinned to `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. Do not relabel historical evidence as Task 15 exact-SHA proof.

This is repository-side automation. It must not be described as independent approval, artistic approval, listening approval, physical-hardware approval, production-capacity proof, production disaster-recovery proof, or evidence that a public realm is deployed.

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

`tools/documentation_contract.py` compares `CURRENT_EVIDENCE.json` with the latest non-documentation implementation commit, validates the exact Task 15 run set, preserves Task 14 historical evidence provenance, validates both permanent sentinels and preserves the human-acceptance boundary.
