# Combat feel and class identity

Status: implemented and repository-verified. Feature commit: `db4b40caac12fe4da3e5a3e9cbe3971ca10821c2`. Focused verification/publish run: `34643559112` — passed.

## Class combat engines

Kairnfall keeps all 60 trainable skills available to every class. Class identity is now an additive combat engine rather than a hard skill restriction:

- **Vanguard — Resolve:** blocking and weathering hostile pressure builds Resolve; empowered defensive class techniques harden the guard.
- **Berserker — Fury:** dealing and taking damage builds Fury; stored Fury strengthens basic pressure and empowers native offensive bursts.
- **Ranger — Focus:** successful long-range pressure builds Focus; an empowered native technique gains power and refunds stamina.
- **Rogue — Momentum:** close pressure, evasions and deliberate combat mobility build Momentum; stealth openers and empowered techniques create stronger openings.
- **Arcanist — Resonance:** elemental spell damage builds Resonance; an empowered native spell hits harder and refunds mana.
- **Warden — Bond:** Nature, companion and support play builds Bond; empowered support strengthens healing/wards and the active companion bond.
- **Templar — Conviction:** healing/protection and Radiant pressure build Conviction; empowered Radiant offense also grants a protective aegis.
- **Spellblade — Spellweave:** alternating martial and magical damage builds Spellweave quickly; an opposite-form class technique consumes the weave for a stronger hybrid burst.

The class resource is server-authoritative, persists safely through reconnect/save, is bounded to 0–100, and decays after leaving combat so it remains encounter rhythm rather than a permanently banked buff.

## Combat feel layer

- The combat HUD exposes the current class resource and a READY state with a mechanic tooltip.
- A 350 ms client input buffer accepts a deliberate ability press just before cooldown completion; the server still enforces every cooldown and target rule.
- Authoritative snapshot deltas drive damage impact rings, micro camera shake, class-resource gain text, ready/release bursts and differentiated combat audio cues.
- Existing deterministic sounds are pitch/body-remapped for hit, hurt, ready and release feedback; a larger audio-library expansion remains a later presentation task.
- Character creation now explains the real class mechanic instead of showing an ornamental passive name.

## Verification evidence

`ClassCombatIdentityChecks` passed all **7/7 groups** in focused run `34643559112`: eight distinct visible class resources, intended resource generation, caster/support/hybrid build-spend loops, native spend rules with cross-class skill freedom, real `RealmEngine` representative casts for all eight classes, save/decay safety, and client meter/input-buffer/impact-feedback contracts.

The same focused run rebuilt the full deterministic game asset set and passed **55,687 / 55,687 technical asset checks** with zero failures or warnings. Full solution and Godot client builds completed with zero warnings/errors. Existing 60-skill, class-kit, combat-variety, world, exploration, economy and mid/late-game suites remained green.

Automation establishes mechanics and integration. Subjective timing, punch, audio preference, and class feel still benefit from hands-on play and are not claimed as human-approved by this document.
