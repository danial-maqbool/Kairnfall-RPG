# Kairnfall RPG — current handoff

## New-player experience

Status date: **2026-09-15**.
Repository: `danial-maqbool/Kairnfall-RPG`. Persistent branch: **main only**.
Verified implementation: **4214c57692bd70196f4c50db0a95ca6f2a510f31**.

The repository-side new-player journey is implemented and its 13 functional exact-head workflows passed. This handoff is synchronized only after that verification. Machine-readable truth is `docs/handoff/CURRENT_EVIDENCE.json`; detailed run IDs, test limits and the repaired native-layout failure are in `docs/handoff/NEW_PLAYER_VERIFICATION.md`.

The opening now connects the existing innkeeper quest, contextual movement/combat guidance, real loot and equipment improvements, the starter rune, the oak-log/plank/handle crafting chain, actual level feedback, the road to Dawnreach and optional shared public activity. One recommended objective supplies the next action, route and reward context. Guidance persists without granting rewards; old characters are not forced through a new tutorial.

The dedicated journey probe passed 12/12 groups. Native experience passed 328 checks across 14 supported resolution/scaling combinations; control rules passed 1,165 checks and the real-server/PostgreSQL experience passed 125 checks. Windows client, native input, package extraction/reconnect, existing world/security/adversarial suites, and retained Task 20/21/22 behavior remain verified. These are automated repository results, not measured human session duration or retention.

## Continuation boundary

Read `AGENTS.md`, `docs/NEW_PLAYER_JOURNEY.md`, `docs/handoff/NEW_PLAYER_CURRENT.md` and `docs/handoff/CURRENT_EVIDENCE.json`. Do not restart completed onboarding work or begin another task without explicit authorization. The delivery commit changes documentation only; verify its exact-main Actions rather than substituting older green runs.

Seven obsolete candidate/edit/overlay files and workflows have been removed. The permanent `New-player journey` workflow checks the exact main revision with read-only repository permissions and disposable services. Keep only `main`; do not create branches, pull requests or issues. Do not force-push, reset existing progression, or resurrect temporary candidate instructions. The previous current Task 22 evidence is archived verbatim in `docs/handoff/TASK22_EVIDENCE.json`; earlier task evidence remains historical and intact.

## Release boundary

**NOT APPROVED — human acceptance remains.**

No release, publication, deployment, release tag or production infrastructure change was authorized or performed. CI packages are test artifacts. Manual/live testing follows repository development and is not a reason to leave implementation or CI fixes unfinished. Human pacing, retention, art/audio, physical Windows hardware and release approval remain separate from repository-side completion.
