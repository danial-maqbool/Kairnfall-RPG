# Meaningful regional objectives

Status: implemented and verified as the Area 2 anti-repetition pass.

Published implementation: `f1fe0ce54b216620aedec39fbbd036239c0b1528`.
Focused verification/publish workflow: run `34590693186` — passed before publication.

- Every one of the 20 surface wilderness regions has a one-time `Waymarks` survey chain.
- Each chain requires reaching the region and surveying its four authored landmarks; it contains no kill/boss objective.
- Regional landmarks are authoritative world interactions: approach them and press **E** to survey. First discovery grants Exploration XP; later inspections still satisfy accepted repeatable work without farming discovery XP.
- Repeatable field reports now require **exploration + landmark survey + local gathering** instead of `explore + kill 3 mobs`.
- Active quest tracking prioritizes main story, then regional direction, then generic side/repeatable work.
- The HUD resolves objective destinations where possible and names the region/landmark for survey objectives.
- The world/quest audit recognizes `survey` only when its target resolves to exactly one authored wilderness landmark with a valid interaction point.
- `MeaningfulObjectiveChecks` permanently verifies all 20 survey chains, all rewritten field reports, world-fit landmark points, server-authoritative survey progression, first-discovery XP behavior, and quest-priority ordering.

This pass deliberately leaves dedicated dungeon delves and class/combat quests intact: combat remains a supported activity, but regional progression no longer defaults to blind mob farming.

The normal Linux/Windows CI run triggered by this evidence receipt is the final exact-head acceptance gate for Area 2.
