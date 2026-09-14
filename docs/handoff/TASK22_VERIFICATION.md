# Task 22 verification

Status date: 2026-09-15. Exact implementation baseline: `d83aa0f9d09a081cd5ebe7f43fe2e2ed9c34baec`. Evidence authority: `docs/handoff/CURRENT_EVIDENCE.json`. Historical Task 21 evidence: `docs/handoff/TASK21_EVIDENCE.json`.

**NOT APPROVED — human acceptance remains.**

## Exact-head functional matrix

- Transaction security regression — `34885269493` — success
- Compile Windows client source — `34885269419` — success
- Live progression breadth — `34885269509` — success
- Windows package acceptance — `34885269513` — success
- Graphical multiplayer acceptance — `34885269398` — success
- Load acceptance — `34885269448` — success
- Build and verify — `34885269413` — success
- Task 13 adversarial acceptance — `34885269459` — success
- Release operations acceptance — `34885269453` — success
- Transaction integrity on Windows and Linux — `34885269575` — success

Pre-sync Documentation evidence contract run `34885269511` failed as expected because `CURRENT_EVIDENCE.json` still identified Task 21 before this synchronization commit.

## Task 22 assertions

Five existing factions (`crown`, `forge_clans`, `circle`, `wardens`, and `league`) receive deterministic daily boards through existing guild registrars. Each board exposes exactly three unique contracts selected from six established loop types: elite hunt, gathering, crafting, dungeon, boss, and public event. This yields fifteen faction contracts per world day without creating new overworld regions.

The server validates that accepted contracts belong to the current rotation, resolves generated contract IDs deterministically, advances generated objectives only from authoritative gameplay hooks, persists active/completed contracts and reputation through the existing character state, and rejects duplicate claims. Reputation is capped at 1,000; Trusted/Honored/Revered/Exalted threshold rewards are guarded by persistent achievements so each milestone pays once.

The Task 22 world probe covers deterministic rotation, no-map-growth invariants, persistence, rejected-command rollback behavior, replay/idempotency, and rank-reward anti-duplication. The Godot client surfaces faction boards, contract tracking, claims, abandonment, and reputation progress. Initial client workflow `34884785169` caught an invalid conditional-expression callback; the explicit callback branch repair is verified by exact-head client run `34885269419`.

Windows package acceptance run `34885269513` retained publication-disabled release-candidate behavior. No release, tag, deployment, infrastructure publication, DNS change, or credential action was authorized or performed.
