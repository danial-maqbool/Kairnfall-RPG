# Challenge-sensitive progression and combat

## References and design boundary

Godot's official input documentation places `_Input` before GUI routing and `_UnhandledInput` after GUI consumption: https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html . Only the configured target key is intercepted during active gameplay. Chat and menus retain normal navigation.

Blizzard's official Diablo II experience rules reduce rewards for level gaps and slow advancement at higher levels: https://classic.battle.net/diablo2exp/basics/experience.shtml . These principles informed the separation of practice and advancement. The equations below are original KAIRNFALL tuning, not Blizzard constants or proof of optimal balance.

## Experience equations

P is current overall player level. M is target monster level. S is trained skill level.

```text
b = floor((P - 1) / 10)
pacing(P) = 0.25 / (1 + 0.14*b + 0.035*b*b)
g = max(0, P - M - 3)
practice(P,M) = max(0.04, 1 / (1 + (g/8)^3))
encounterCredit(P,M) = max(0.005, exp(-0.24*g))
mastery(S,M) = clamp((30 - (S-M))/30, 0.05, 1)
combatSkillXP = baseXP * practice(P,M) * mastery(S,M) * classAffinity
overallContribution = awardedSkillXP * pacing(P) * encounterCredit(P,M)
```

Class affinity remains 1.10 for an affiliated skill and 1 otherwise. Fractions accumulate before integer awards. Tiny hits do not each receive a free whole XP point. Twenty-level weaker targets give approximately 9.4% practice before mastery/affinity and approximately 1.69% encounter credit before pacing. Targets within three levels have no level-gap penalty. Very strong targets do not grant an uncapped reward multiplier.

Pacing changes at 11, 21, 31 and later ten-level boundaries. It also applies to the overall contribution of noncombat training. Noncombat raw skill awards retain their existing formula. Crafting and movement therefore cannot bypass the requested overall slowdown. Monster health, damage, armor, aggro and loot definitions do not scale with player level.

Saved raw skill XP stays intact. `PracticeOnlyXp` records the part of future skill gains excluded from overall advancement. Missing legacy fields default to zero. Old levels remain unchanged. Fractional practice and credit persist with the character. The prior overall XP-to-level mapping runs on credited training rather than destructively recalculating past progress. A gradual late-game mastery floor prevents a character from being stranded below the overall cap after all skills cap. With q = raw total skill XP / (60 * skill-cap XP), the floor is 1 + floor(199 * q^1.5). Overall level is the greater of that floor and the credited-XP level. This floor is negligible during early play and approaches level 200 continuously; it does not create a last-point jump. Trivial combat still earns only its reduced practice before it contributes to mastery.

Direct hits, delayed hits, companion hits, kills and defensive training share the authoritative combat helper. Support actions retain the existing region-difficulty input. Meditation remains noncombat training. The displayed target estimate applies to individual encounters, not support actions.

## Combat equations

```text
physicalMastery(S) = 1 + 0.9*S/(S+75)
spellMastery(S) = 1 + 0.75*S/(S+100)
physicalBase = weaponPower + 0.65*strength + physicalBonus
spellBase = 7 + 1.1*intellect + 0.4*weaponPower + spellBonus
mitigatedDamage = rawDamage * 100/(100 + max(armor,0))
                  * (1 - clamp(resistance,-0.5,1))
```

The new mastery factors have diminishing gains and finite bounds. Critical caps, element modifiers, weather, vulnerability, shields and actual-health damage caps remain. Armor 100 still halves unresisted raw damage. No opaque level-based damage inflation or additional random miss system is introduced.

## Interface and tests

Vitals show the current overall-credit rate and next boundary. The selected target shows challenge category, practice rate and overall credit. Tooltips explain factor order. The native HUD fixture checks both supported resolutions and separation from the objective panel.

ChallengeProgressionChecks covers band boundaries, 20-level weaker enemies, accumulated fractions, unchanged legacy levels, serialization, replay, actual kill rewards, bounded formulas and 50 progression scenarios. Its data goes to `artifacts/experience/balance/xp-curves.json`. Existing authority, save, database, input, graphical and live-client suites remain mandatory.

Read the final session handoff for measured results. Formula checks do not establish human progression time, complete class balance, physical Windows input, independent visual acceptance or a finished release.
