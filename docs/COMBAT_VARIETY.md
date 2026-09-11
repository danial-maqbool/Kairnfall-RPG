# Combat and enemy variety

Status: implemented as Area 3 anti-repetition work.

- Ordinary enemies use authored tactical attack profiles instead of a single chase-and-hit behavior.
- Ranged kiters retreat whenever pressured at close range; pack hunters, ambushers, guards, berserkers, healers, casters and summoners preserve distinct roles.
- All 25 elites carry one deterministic modifier: Bulwark, Frenzied, Vampiric, Stormmarked or Fleet.
- All 20 bosses execute their three authored attacks. Phase 1 exposes the first attack, phase 2 the first two, and phase 3 the complete kit.
- Boss attacks include charges, cones, stomps, lines, rings, interruptible casts, poison fields, summons, roots and persistent hazard fields.
- Existing player interrupt abilities cancel enemy telegraphs, including long interruptible boss casts.
- Enemy telegraphs now label special attacks; ring attacks render as true danger rings. The target frame explains tactical role, elite modifier and boss phase attack set.
- Combat remains server-authoritative. New mechanics are covered by `CombatVarietyChecks` in the normal world-probe suite.
