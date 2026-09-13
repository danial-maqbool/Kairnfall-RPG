# Local agent prompt — Task 16 owner acceptance handoff

Current status as of 2026-09-13.

Repository: `https://github.com/danial-maqbool/Kairnfall-RPG`  
Branch: single authoritative `main`  
Stack: Godot 4.7.2 .NET, C#, .NET 10 authoritative server, PostgreSQL  
Current implementation/candidate baseline: `2365a0df98beca178e22c099f0f31cd5adf65e6e`  
Machine-readable evidence: `docs/handoff/CURRENT_EVIDENCE.json`

**NOT APPROVED — human acceptance remains.**

Task 16 repository-side preparation is complete. Exact technical runs and the owner-candidate package identity are recorded in `CURRENT_EVIDENCE.json` and `VERIFICATION.md`. The owner procedure is `docs/qa/TASK16_OWNER_ACCEPTANCE.md`.

Final candidate: `Kairnfall-Release-Candidate-2365a0df98be.zip`; Windows package run `34775900170`; Actions artifact `10324090750`; SHA-256 `45e00144c910c0b79daa327c30086bb604896a8a425b9391e57a9340ab61b54e`. Treat it as a non-public release candidate. Do not rebuild or substitute another package for human acceptance without updating evidence.

Task 16 exact-SHA automation passes build, adversarial authority, transactions on Linux/Windows, reference load, native Windows client compilation, live progression/reconnect persistence, two-client graphical multiplayer, Windows packaging, and database/recovery operations.

Task 14 Windows display/input, visual and technical-audio evidence remains historical at `d4c8121bf6a3c8338ec9470d2072d6c98c79fa7a`; Task 15 release/recovery evidence remains historical at `83a99948c7e96ff1ed568b5090b3138294b8e713`. Do not relabel either as Task 16 exact-SHA proof.

Remaining work is human observation: clean owner-machine package validation, account/character/persistence, first-hour progression, class/combat feel, world/quest/resource/boss walkthrough, economy, social/multiplayer usability, UI/UX/accessibility, physical Windows DPI/input, artistic review and actual audio listening. Production-scale load is only needed for a separately advertised capacity.

Classify findings as RELEASE BLOCKER, HIGH, MEDIUM, LOW/POLISH, or SUBJECTIVE FEEDBACK. Reproduce objective defects, fix the smallest real cause, rerun relevant exact-head CI, produce a new candidate when executable/package content changes, and require only plausibly affected manual checks to be repeated.

Never commit secrets or real user/database data. Use isolated disposable databases for destructive tests. Do not weaken tests, suppress failures, fabricate human results, create a release/tag, deploy a public realm, or start Task 17 without explicit owner authorization.

`tools/documentation_contract.py` compares `CURRENT_EVIDENCE.json` with the latest non-documentation implementation commit, validates the exact Task 16 run set and owner-candidate identity, preserves Task 14/15 historical provenance, validates the permanent sentinels and preserves the human-acceptance boundary.
