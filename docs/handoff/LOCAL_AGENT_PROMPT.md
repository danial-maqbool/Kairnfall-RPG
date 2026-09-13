# Local agent prompt — current mainline acceptance

Current status as of 2026-09-13.

Repository: `https://github.com/danial-maqbool/Kairnfall-RPG`  
Branch: single authoritative `main`  
Stack: Godot 4.7.2 .NET, C#, .NET 10 authoritative server, PostgreSQL  
Current implementation baseline: `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`  
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`

Task 14 is repository-side complete. The permanent `src/release-candidate.trigger` makes it possible to run the accepted automation matrix against one exact source SHA, and all twelve technical gates passed at the current candidate baseline. See `docs/qa/RELEASE_CANDIDATE_ACCEPTANCE.md`. Task 15 was not started.

**NOT APPROVED — human acceptance remains.**

## Current evidence

Exact Task 14 source baseline: `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`. `CURRENT_EVIDENCE.json` and `VERIFICATION.md` record the twelve successful exact-SHA run IDs spanning build/adversarial authority, transactions, load, Windows client/package/display, progression, graphical multiplayer, visual acceptance and technical audio.

This is repository-side automation. It must not be described as independent approval, artistic approval, listening approval, physical-hardware approval, production-capacity proof or evidence that a public realm is deployed.

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

`tools/documentation_contract.py` compares `CURRENT_EVIDENCE.json` with the latest non-documentation implementation commit and validates the Task 14 exact workflow set, sentinel, synchronized date/baseline and release boundary.
