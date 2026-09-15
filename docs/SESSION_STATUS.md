# Session status — New-player experience

**2026-09-15** · `danial-maqbool/Kairnfall-RPG` · `main` only.

Verified implementation baseline: **4214c57692bd70196f4c50db0a95ca6f2a510f31**.
Current evidence: `docs/handoff/CURRENT_EVIDENCE.json`.
Release status: **NOT APPROVED — human acceptance remains.**

## Completed repository work

The existing verified candidate was inspected and integrated rather than rebuilt. The persistent-world journey now presents one legitimate next objective, current-keybinding guidance, a safe optional combat introduction, loot and real equipment/rune improvements, the existing gathering/crafting quest, visible skill/character progression and the route to the next settlement. Social discovery and nearby appropriate public activity are visible without requiring other players or a party.

Presentation state uses existing saved discoveries. Creation eligibility and gameplay milestones are server-owned. Guide acknowledgements are allowlisted, sequenced, receipted and reward-neutral. Existing quest/event rewards retain their normal validation and replay protection. Old saves remain compatible and established characters are not forced into beginner hints. No authored overworld/content expansion, economy inflation, progression reset, new reward pipeline or production change was introduced.

Native-frame inspection caught invisible wrapped hints and notifications behind combat controls. Scaled glyph-height, containment and overlap regressions were added. The expanded matrix then caught an additional enlarged-desktop notice overlap at `3fdca6068b2e2688b9815ffd88541da34876b994`; `4214c57692bd70196f4c50db0a95ca6f2a510f31` fixed it without weakening assertions.

## Verified results and delivery

All 13 functional workflows passed at the stated baseline. The dedicated journey recorded 12/12 groups, native experience 328 checks, native control rules 1,165 checks, XP HUD 9 checks and the live-server/PostgreSQL experience 125 checks. Core, review, security, full world, database/network, adversarial, Windows compile/native/package, graphical multiplayer, load and recovery checks passed. See `docs/handoff/NEW_PLAYER_VERIFICATION.md` for exact run IDs and limits.

Only after these runs passed was this documentation synchronized. The documentation-only delivery head must retain the baseline and pass its own fresh Actions. The evidence contract validates the recorded implementation runs through the read-only GitHub Actions API, including exact SHA, workflow identity, repository, branch and completed-success state. It also enforces removal of temporary tooling, preservation of the old Task 22 evidence blob and an unchanged authored content footprint.

The candidate/edit/overlay request files and temporary workflows are removed; only the permanent exact-head journey workflow remains. The branch listing at implementation verification contained only `main`. Do not create a subsequent task, release, deployment, tag, branch, pull request or issue automatically.

## Evidence boundaries

The 15-minute and first-hour sequence is a design target. The automated probe uses bounded clocks and reachable proximity fixtures around real gameplay APIs; it is not an uncoached human playthrough or a retention study. Native screenshots were inspected for the onboarding changes, not used to approve the entire game's art. Physical Windows hardware, normal-play pacing, audio/art acceptance and owner release approval remain separate human gates in `CURRENT_EVIDENCE.json`.
