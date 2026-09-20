# Combat and enemy variety

Status: implemented and repository-verified as Area 3 anti-repetition work.

- Ordinary enemies use authored tactical attack profiles instead of a single chase-and-hit behavior. The normal roster now exposes at least ten distinct server-recognized attack actions.
- Ranged kiters retreat whenever pressured at close range; pack hunters, ambushers, guards, berserkers, healers, casters and summoners preserve distinct roles. Support enemies can mix ranged pressure with short binding-root telegraphs.
- All 25 elites carry one deterministic modifier: Bulwark, Frenzied, Vampiric, Stormmarked or Fleet, with five elites assigned to each modifier.
- All 20 bosses execute their three authored attacks. Phase 1 exposes the first attack, phase 2 the first two, and phase 3 the complete kit.
- Boss attacks include charges, cones, stomps, lines, rings, interruptible casts, poison fields, summons, roots and persistent hazard fields.
- Existing player interrupt abilities cancel enemy telegraphs, including long interruptible boss casts.
- Enemy telegraphs label special attacks; ring attacks render as true danger rings. The target frame explains tactical role, elite modifier and boss phase attack set.
- Combat remains server-authoritative. `CombatVarietyChecks` exercises the 100 normal species, all 25 elites, all 20 bosses, real close-pressure kiting, and a real authored boss charge through `RealmEngine.Tick`.

Focused publish gate: GitHub Actions run `34597410316` passed after the first review correctly rejected a nine-action ordinary roster. The unchanged variety threshold passed after support enemies received Binding Roots. Feature commit: `09351e326145b228774683f099d1b1ce27ab668f`.

Human combat-feel playtesting remains useful for tuning timing and damage, but is not a substitute for these authoritative mechanics checks.
