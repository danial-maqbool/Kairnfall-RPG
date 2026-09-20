# Guided journey and character-XP pacing

This update responds to hands-on playtest feedback that progression became repetitive and directionless. It adds an explicit sense of "where should I go next?" without turning the game into a linear quest corridor.

## Level-gated frontiers

Area entry is now server-authoritative and based on the destination's ordinary enemies.

- The area's **threat level** is the median level of its ordinary species. Bosses and elites do not inflate the gate.
- The normal **entry level** is `threat level - 5`, clamped to the valid character-level range.
- An explicitly authored passage requirement may be stricter, but never weaker.
- Example: an area whose ordinary enemies are level 22 opens at character level 17.
- Both physical transitions and settlement waystone fast travel enforce the same rule on the server.
- Rejected entry explains the required level and how many levels remain.

The world map and Hunting Guide use the same shared rule. Locked destinations are red, open exits are gold, and the selected area shows its threat and entry levels.

## Direction instead of blind grinding

When no quest is currently tracked, the HUD now chooses a useful next step:

1. a locally available quest lead;
2. a reachable next frontier;
3. the nearest locked frontier and its required level; or
4. an undertrained gathering/crafting/exploration activity for a change of pace.

`Hunt [H]` is now visible in the HUD navigation. The Hunting Guide shows the current character level and area threat, labels exits as OPEN or LOCKED, and gives a next-lead/frontier/activity suggestion. This is intended to keep combat, gathering, crafting, exploration and quests rotating naturally instead of encouraging indefinite mob farming.

## Character-XP curve

Character XP is still exactly the sum of awarded skill XP. Existing saves keep every earned skill XP point and skill level; no skill progress is rewritten. The derived character level is recalculated from the new thresholds.

The new curve is deliberately quick through the opening game and then widens progressively:

| Character level | Total character XP required |
| ---: | ---: |
| 2 | 100 |
| 5 | 520 |
| 10 | 1,620 |
| 15 | 3,220 |
| 20 | 5,320 |
| 21 | 5,870 |
| 25 | 8,820 |
| 30 | 14,195 |
| 40 | 34,445 |
| 50 | 77,945 |
| 60 | 169,945 |
| 80 | 619,945 |
| 100 | 1,794,945 |
| 125 | 5,844,945 |
| 150 | 16,594,945 |
| 175 | 43,344,945 |
| 200 | 113,344,945 |

Individual level costs never decrease. Levels 1–20 are intentionally forgiving; 20–30 is a noticeable but modest step up, and later bands continue to increase rather than introducing one sudden grind wall.

The permanent Character XP bar now shows XP remaining to the next character level.

## Verification

Production feature commit: `f7099811e26b45f6eb9a7639e31d2c1f8a631522`.

Dedicated verification run `34563364763` passed before publication. It rebuilt the solution and client and ran the retained world probe plus the new Journey Pacing contract. The new contract verifies:

- monotone XP costs and the intended early/mid pacing;
- every frontier's `ordinary threat - 5` rule;
- a real server transition rejecting a character one level below the gate;
- the same transition accepting a character at the exact gate level; and
- availability of quest/frontier/activity guidance.

The same run retained all existing progression, economy, world/quest, hunting, equipment, crafting, save-migration and XP challenge checks, and the Godot C# client compiled with zero warnings and zero errors.

Human playtesting remains important for tuning the feel of the thresholds after longer sessions. The formulas above are deliberately centralized so later pacing adjustments can be made without changing saved skill XP.
