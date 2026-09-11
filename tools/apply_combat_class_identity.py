#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def save(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = load(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:120]!r}")
    save(path, text.replace(old, new, 1))


def replace_between(path: str, start: str, end: str, replacement: str) -> None:
    text = load(path)
    left = text.find(start)
    if left < 0:
        raise RuntimeError(f"{path}: start marker not found: {start!r}")
    right = text.find(end, left)
    if right < 0:
        raise RuntimeError(f"{path}: end marker not found: {end!r}")
    save(path, text[:left] + replacement + text[right:])


class_rules = r'''namespace Kairnfall.Core;

/// <summary>
/// A single authoritative class-resource contract. Classes keep access to every trainable skill;
/// these rules reward playing into a class identity without hard-banning off-class builds.
/// </summary>
public readonly record struct ClassCombatBonus(
    double PowerMultiplier,
    double ManaRefund,
    double StaminaRefund,
    string Effect,
    bool Empowered)
{
    public static ClassCombatBonus None => new(1, 0, 0, "", false);
}

public static class ClassCombatRules
{
    public const double MaximumResource = 100;

    public static string ResourceName(string classId) => classId switch
    {
        "vanguard" => "Resolve",
        "berserker" => "Fury",
        "ranger" => "Focus",
        "rogue" => "Momentum",
        "arcanist" => "Resonance",
        "warden" => "Bond",
        "templar" => "Conviction",
        "spellblade" => "Spellweave",
        _ => "Class Resource"
    };

    public static double ReadyThreshold(string classId) => classId switch
    {
        "berserker" or "ranger" or "rogue" => 40,
        "arcanist" => 60,
        "vanguard" or "warden" or "templar" or "spellblade" => 50,
        _ => MaximumResource
    };

    public static string PassiveDescription(string classId) => classId switch
    {
        "vanguard" => "Resolve — blocking or weathering hostile pressure builds Resolve. At 50 Resolve, a native shield, taunt, or defensive buff hardens your guard.",
        "berserker" => "Fury — dealing and taking damage builds Fury. Basic attacks scale with stored Fury; at 40 Fury, a native offensive ability consumes it for a stronger burst.",
        "ranger" => "Focus — damaging threats from range builds Focus. At 40 Focus, a native offensive technique hits harder and refunds stamina.",
        "rogue" => "Momentum — close attacks, evasions, and combat mobility build Momentum. Stealth empowers an opener; at 40 Momentum, a native offensive technique creates a stronger opening.",
        "arcanist" => "Resonance — elemental spell damage builds Resonance. At 60 Resonance, a native offensive spell consumes it for amplified power and a partial mana refund.",
        "warden" => "Bond — Nature, companion, and active support play builds Bond. At 50 Bond, a native heal, ward, cleanse, or summon strengthens the living bond.",
        "templar" => "Conviction — healing, protection, and Radiant damage build Conviction. At 50 Conviction, a native Radiant attack consumes it for a stronger judgment and protective aegis.",
        "spellblade" => "Spellweave — alternate martial and magical damage to build Spellweave quickly. At 50 Spellweave, an opposite-form native attack consumes it for a stronger weave.",
        _ => "All professions remain trainable."
    };

    public static void Normalize(Character player)
    {
        if (!double.IsFinite(player.ClassResource)) player.ClassResource = 0;
        player.ClassResource = Math.Clamp(player.ClassResource, 0, MaximumResource);
        if (player.Class != "spellblade") player.ClassState = "";
        else if (player.ClassState is not ("martial" or "magic")) player.ClassState = "";
    }

    public static bool IsReady(Character player)
    {
        Normalize(player);
        return player.ClassResource >= ReadyThreshold(player.Class);
    }

    public static string Hint(Character player)
    {
        Normalize(player);
        string name = ResourceName(player.Class);
        double threshold = ReadyThreshold(player.Class);
        if (player.ClassResource >= threshold) return name + " ready — your next matching class technique is empowered.";
        int remaining = (int)Math.Ceiling(Math.Max(0, threshold - player.ClassResource));
        return name + " " + Math.Round(player.ClassResource) + "/100 · " + remaining + " to empowered technique.";
    }

    private static void Gain(Character player, double amount)
    {
        Normalize(player);
        if (!double.IsFinite(amount) || amount <= 0) return;
        player.ClassResource = Math.Clamp(player.ClassResource + amount, 0, MaximumResource);
    }

    private static bool Spend(Character player, double amount)
    {
        Normalize(player);
        if (player.ClassResource + 0.0001 < amount) return false;
        player.ClassResource = Math.Max(0, player.ClassResource - amount);
        return true;
    }

    private static bool Offensive(AbilityDef ability) => ability.Kind is
        "strike" or "dot" or "drain" or "dash" or "cone" or "line" or "area" or "field" or "projectile" or "interrupt";

    private static bool Defensive(AbilityDef ability) => ability.Kind is "shield" or "taunt" or "buff";
    private static bool Support(AbilityDef ability) => ability.Kind is "heal" or "shield" or "summon" or "purge" or "buff";

    public static ClassCombatBonus PrepareBasicAttack(Character player, Element element, bool stealthed)
    {
        Normalize(player);
        return player.Class switch
        {
            "berserker" => new(1 + player.ClassResource / MaximumResource * 0.12, 0, 0, "", false),
            "rogue" when stealthed => new(1.25, 0, 0, "rogue_expose", true),
            "spellblade" when player.ClassState == "magic" && player.ClassResource >= 50 && Spend(player, 50)
                => new(1.20, 0, 2, "", true),
            _ => ClassCombatBonus.None
        };
    }

    public static ClassCombatBonus PrepareCast(Character player, AbilityDef ability, bool stealthed)
    {
        Normalize(player);
        if (ability.Class != player.Class) return ClassCombatBonus.None;
        switch (player.Class)
        {
            case "vanguard" when Defensive(ability) && player.ClassResource >= 50 && Spend(player, 50):
                return new(1.25, 0, 4, "vanguard_resolve", true);
            case "berserker" when Offensive(ability) && player.ClassResource >= 40 && Spend(player, 40):
                return new(1.20, 0, 0, "", true);
            case "ranger" when Offensive(ability) && player.ClassResource >= 40 && Spend(player, 40):
                return new(1.20, 0, 6, "", true);
            case "rogue" when Offensive(ability) && player.ClassResource >= 40 && Spend(player, 40):
                return new(stealthed ? 1.40 : 1.25, 0, 4, "rogue_expose", true);
            case "rogue" when Offensive(ability) && stealthed:
                return new(1.15, 0, 0, "rogue_expose", true);
            case "arcanist" when Offensive(ability) && ability.Element != Element.Physical && player.ClassResource >= 60 && Spend(player, 60):
                return new(1.25, 8, 0, "", true);
            case "warden" when Support(ability) && player.ClassResource >= 50 && Spend(player, 50):
                return new(1.25, 5, 5, "warden_bond", true);
            case "templar" when Offensive(ability) && ability.Element == Element.Radiant && player.ClassResource >= 50 && Spend(player, 50):
                return new(1.22, 0, 4, "templar_aegis", true);
            case "spellblade" when Offensive(ability):
            {
                string family = ability.Element == Element.Physical ? "martial" : "magic";
                if (player.ClassState != "" && player.ClassState != family && player.ClassResource >= 50 && Spend(player, 50))
                    return new(1.25, 5, 5, "", true);
                break;
            }
        }
        return ClassCombatBonus.None;
    }

    public static void RecordDamage(Character player, double damage, Element element, string skill, double distance)
    {
        Normalize(player);
        if (!double.IsFinite(damage) || damage <= 0 || !double.IsFinite(distance) || distance < 0) return;
        switch (player.Class)
        {
            case "berserker":
                Gain(player, 6); break;
            case "ranger" when distance >= 3.5 && skill is "archery" or "crossbow_mastery" or "hunting" or "stormcalling":
                Gain(player, distance >= 7 ? 15 : 12); break;
            case "rogue" when distance <= 3.0 && skill is "dagger_mastery" or "shadow_magic" or "evasion":
                Gain(player, 12); break;
            case "arcanist" when element != Element.Physical && skill is "pyromancy" or "cryomancy" or "stormcalling" or "geomancy" or "arcane_magic":
                Gain(player, 12); break;
            case "warden" when element == Element.Nature || skill is "nature_magic" or "summoning" or "animal_handling":
                Gain(player, 10); break;
            case "templar" when element == Element.Radiant || skill == "radiance":
                Gain(player, 10); break;
            case "spellblade":
            {
                string family = element == Element.Physical ? "martial" : "magic";
                Gain(player, player.ClassState != "" && player.ClassState != family ? 25 : 5);
                player.ClassState = family;
                break;
            }
        }
    }

    public static void RecordIncoming(Character player, double pressure, double healthDamage, bool blocked, bool evaded)
    {
        Normalize(player);
        if (evaded)
        {
            if (player.Class == "rogue") Gain(player, 12);
            return;
        }
        if (player.Class == "vanguard" && double.IsFinite(pressure) && pressure > 0) Gain(player, blocked ? 20 : 10);
        if (player.Class == "berserker" && double.IsFinite(healthDamage) && healthDamage > 0) Gain(player, 8);
    }

    public static void RecordCast(Character player, AbilityDef ability, bool combatContext)
    {
        Normalize(player);
        if (ability.Class != player.Class || !combatContext) return;
        if (player.Class == "warden" && Support(ability)) Gain(player, 18);
        else if (player.Class == "templar" && ability.Kind is "heal" or "shield" or "purge" or "taunt") Gain(player, 18);
        else if (player.Class == "rogue" && ability.Kind is "stealth" or "dash") Gain(player, 15);
    }

    public static void Tick(Character player, double dt, double now)
    {
        Normalize(player);
        if (!double.IsFinite(dt) || dt <= 0 || !double.IsFinite(now)) return;
        if (player.Health <= 0 || now - player.LastCombat > 8)
            player.ClassResource = Math.Max(0, player.ClassResource - dt * 12);
        if (player.ClassResource <= 0.0001 && player.Class == "spellblade") player.ClassState = "";
    }
}
'''
save("src/Kairnfall.Core/ClassCombatRules.cs", class_rules)

replace_once("src/Kairnfall.Core/Models.cs",
'''    public double Stamina { get; set; } = 100;
    public long Gold { get; set; } = 40;
''',
'''    public double Stamina { get; set; } = 100;
    // Server-authoritative 0-100 identity resource. Missing fields in historical saves safely default to zero.
    public double ClassResource { get; set; }
    // Spellblade uses this to remember the last successful martial/magical form; other classes keep it empty.
    public string ClassState { get; set; } = "";
    public long Gold { get; set; } = 40;
''')

# Make the class-selection text explain the real mechanic rather than an ornamental passive name.
skills = load("content_src/skills.py")
passives = {
    "Disciplined Guard": "Resolve — blocking or weathering hostile pressure builds Resolve. At 50 Resolve, a native shield, taunt, or defensive buff hardens your guard.",
    "Blood Fury": "Fury — dealing and taking damage builds Fury. Basic attacks scale with stored Fury; at 40 Fury, a native offensive ability consumes it for a stronger burst.",
    "Keen Trail": "Focus — damaging threats from range builds Focus. At 40 Focus, a native offensive technique hits harder and refunds stamina.",
    "Patient Blade": "Momentum — close attacks, evasions, and combat mobility build Momentum. Stealth empowers an opener; at 40 Momentum, a native offensive technique creates a stronger opening.",
    "Arcane Discipline": "Resonance — elemental spell damage builds Resonance. At 60 Resonance, a native offensive spell consumes it for amplified power and a partial mana refund.",
    "Living Bond": "Bond — Nature, companion, and active support play builds Bond. At 50 Bond, a native heal, ward, cleanse, or summon strengthens the living bond.",
    "Oath of Mercy": "Conviction — healing, protection, and Radiant damage build Conviction. At 50 Conviction, a native Radiant attack consumes it for a stronger judgment and protective aegis.",
    "Runebound Edge": "Spellweave — alternate martial and magical damage to build Spellweave quickly. At 50 Spellweave, an opposite-form native attack consumes it for a stronger weave.",
}
for old, new in passives.items():
    if skills.count("'" + old + "'") != 1:
        raise RuntimeError("content_src/skills.py passive mismatch: " + old)
    skills = skills.replace("'" + old + "'", repr(new), 1)
save("content_src/skills.py", skills)

# Basic attacks: preserve stealth long enough for Rogue openers; make Berserker/Spellblade loops tactile.
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'''        Ready(p,"attack",Math.Max(0.25,(weapon?.Speed??0.8)/stats.AttackSpeed));
        p.Stamina-=3; p.Facing=p.Position.Direction(mob.Position); p.Statuses.RemoveAll(x=>x.Kind=="stealth");
        playerTargets[p.Id]=mob.Id;
        double raw=stats.Physical*CombatTrainingCurve.Physical(Progression.Level(p,skill));
        if(p.Class=="berserker") raw*=1+0.25*(1-p.Health/stats.Health);
        if(CombatMath.Roll(stats.Crit)) raw*=stats.CritDamage;
        Element attackElement=weapon is null?Element.Physical:Items.ElementOf(weaponItem!,weapon);
''',
'''        Ready(p,"attack",Math.Max(0.25,(weapon?.Speed??0.8)/stats.AttackSpeed));
        bool stealthed=p.Statuses.Any(x=>x.Kind=="stealth"&&x.Until>State.Time);
        p.Stamina-=3; p.Facing=p.Position.Direction(mob.Position);
        playerTargets[p.Id]=mob.Id;
        Element attackElement=weapon is null?Element.Physical:Items.ElementOf(weaponItem!,weapon);
        var classBonus=ClassCombatRules.PrepareBasicAttack(p,attackElement,stealthed);
        double raw=stats.Physical*CombatTrainingCurve.Physical(Progression.Level(p,skill))*classBonus.PowerMultiplier;
        if(p.Class=="berserker") raw*=1+0.25*(1-p.Health/stats.Health);
        if(CombatMath.Roll(stats.Crit)) raw*=stats.CritDamage;
        p.Stamina=Math.Min(stats.Stamina,p.Stamina+classBonus.StaminaRefund);
        p.Statuses.RemoveAll(x=>x.Kind=="stealth");
''')

# Cast setup: native class techniques may consume the authoritative identity resource.
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'''        Ready(p,"ability:"+ability.Id,ability.Cooldown*(1-stats.CooldownReduction));
        Ready(p,"global_ability",0.25);
        p.Mana-=ability.Mana; p.Stamina-=ability.Stamina;
        double basePower=(ability.Element==Element.Physical?stats.Physical:stats.Spell)*ability.Power;
        basePower*=CombatTrainingCurve.Spell(Progression.Level(p,ability.Skill));
        var zone=Data.Zone(p.Zone);
''',
'''        Ready(p,"ability:"+ability.Id,ability.Cooldown*(1-stats.CooldownReduction));
        Ready(p,"global_ability",0.25);
        bool stealthed=p.Statuses.Any(x=>x.Kind=="stealth"&&x.Until>State.Time);
        bool combatContext=State.Time-p.LastCombat<=10;
        var classBonus=ClassCombatRules.PrepareCast(p,ability,stealthed);
        p.Mana-=ability.Mana; p.Stamina-=ability.Stamina;
        double basePower=(ability.Element==Element.Physical?stats.Physical:stats.Spell)*ability.Power;
        basePower*=CombatTrainingCurve.Spell(Progression.Level(p,ability.Skill))*classBonus.PowerMultiplier;
        var zone=Data.Zone(p.Zone);
''')

# Resolve class-specific empowered side effects after the normal ability contract succeeds.
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'''        if(!selfKind) { p.LastCombat=State.Time; p.Statuses.RemoveAll(x=>x.Kind=="stealth"); }
        int supportLevel=SupportTraining.EncounterLevel(p,State.Time,10);
        if(!trained&&selfKind&&supportLevel>0&&ability.Kind!="heal") ChallengeProgression.TrainCombat(p,ability.Skill,5,supportLevel,Data);
        Progress(p,"cast",ability.Id); return "";
''',
'''        if(classBonus.Effect=="vanguard_resolve") ApplyStatus(p.Statuses,"vanguard_resolve",Element.Physical,6,0.18,p.Id);
        else if(classBonus.Effect=="rogue_expose"&&selected is not null&&selected.Health>0) ApplyStatus(selected.Statuses,"vulnerable",Element.Arcane,4,0.15,p.Id);
        else if(classBonus.Effect=="warden_bond")
        {
            if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var companion)&&companion.Health>0)
            {
                ApplyStatus(companion.Statuses,"warden_bond",Element.Nature,8,0.30,p.Id);
                ApplyStatus(companion.Statuses,"fortify",Element.Nature,8,0.15,p.Id);
            }
            else ApplyStatus(p.Statuses,"regeneration",Element.Nature,6,Math.Max(1,stats.Healing),p.Id);
        }
        else if(classBonus.Effect=="templar_aegis") ApplyStatus(p.Statuses,"shield",Element.Radiant,5,Math.Max(8,stats.Health*0.10),p.Id);
        p.Mana=Math.Min(stats.Mana,p.Mana+classBonus.ManaRefund);
        p.Stamina=Math.Min(stats.Stamina,p.Stamina+classBonus.StaminaRefund);
        if(!selfKind) { p.LastCombat=State.Time; p.Statuses.RemoveAll(x=>x.Kind=="stealth"); }
        int supportLevel=SupportTraining.EncounterLevel(p,State.Time,10);
        if(!trained&&selfKind&&supportLevel>0&&ability.Kind!="heal") ChallengeProgression.TrainCombat(p,ability.Skill,5,supportLevel,Data);
        ClassCombatRules.RecordCast(p,ability,combatContext||supportLevel>0);
        Progress(p,"cast",ability.Id); return "";
''')

# Successful hostile damage is the shared generator for offensive class loops.
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'''        if(damage>0)
        {
            SupportTraining.Record(p,def.Level,State.Time);
            ChallengeProgression.TrainCombat(p,skill,Math.Clamp((int)damage,1,120),def.Level,Data);
''',
'''        if(damage>0)
        {
            SupportTraining.Record(p,def.Level,State.Time);
            ClassCombatRules.RecordDamage(p,damage,element,skill,p.Position.Distance(mob.Position));
            ChallengeProgression.TrainCombat(p,skill,Math.Clamp((int)damage,1,120),def.Level,Data);
''')

# Incoming pressure feeds Resolve/Fury, while an actual evade feeds Rogue Momentum.
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'''        if(mob.Owner=="") SupportTraining.Record(p,def.Level,State.Time);
        if(CombatMath.Roll(stats.Evasion)) { ChallengeProgression.TrainCombat(p,"evasion",12,def.Level,Data); return; }
''',
'''        if(mob.Owner=="") SupportTraining.Record(p,def.Level,State.Time);
        if(CombatMath.Roll(stats.Evasion))
        {
            ClassCombatRules.RecordIncoming(p,0,0,false,true);
            ChallengeProgression.TrainCombat(p,"evasion",12,def.Level,Data); return;
        }
''')

replace_once("src/Kairnfall.Core/RealmCombat.cs",
'''        double damage=CombatMath.Damage(raw*matchup,element==Element.Physical?stats.Armor:stats.Armor*0.2,CombatMath.Resist(stats,element));
        if(CombatMath.Roll(stats.Block)) { damage*=0.4; ChallengeProgression.TrainCombat(p,"shield_mastery",12,def.Level,Data); }
        damage*=1-Math.Clamp(CombatMath.StatusPower(p.Statuses,"guard",State.Time),0,0.6);
        foreach(var shield in p.Statuses.Where(x=>x.Kind=="shield"&&x.Until>State.Time).ToList())
''',
'''        double damage=CombatMath.Damage(raw*matchup,element==Element.Physical?stats.Armor:stats.Armor*0.2,CombatMath.Resist(stats,element));
        bool blocked=CombatMath.Roll(stats.Block);
        if(blocked) { damage*=0.4; ChallengeProgression.TrainCombat(p,"shield_mastery",12,def.Level,Data); }
        damage*=1-Math.Clamp(CombatMath.StatusPower(p.Statuses,"guard",State.Time),0,0.6);
        damage*=1-Math.Clamp(CombatMath.StatusPower(p.Statuses,"vanguard_resolve",State.Time),0,0.35);
        double pressure=damage;
        foreach(var shield in p.Statuses.Where(x=>x.Kind=="shield"&&x.Until>State.Time).ToList())
''')

replace_once("src/Kairnfall.Core/RealmCombat.cs",
'''        p.Health=Math.Max(0,p.Health-damage); p.LastCombat=State.Time; p.Statuses.RemoveAll(x=>x.Kind is "meditate" or "stealth");
''',
'''        p.Health=Math.Max(0,p.Health-damage); p.LastCombat=State.Time; p.Statuses.RemoveAll(x=>x.Kind is "meditate" or "stealth");
        ClassCombatRules.RecordIncoming(p,pressure,damage,blocked,false);
''')

# Empowered Warden Bond makes the existing authoritative companion loop visibly/mechanically stronger.
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'''            pet.NextAttack=State.Time+2;
            HitCreature(owner,enemy,def.Power,def.Element,pet.Id.StartsWith("summon/",StringComparison.Ordinal)?"summoning":"animal_handling");
''',
'''            pet.NextAttack=State.Time+2;
            double bond=CombatMath.StatusPower(pet.Statuses,"warden_bond",State.Time);
            HitCreature(owner,enemy,def.Power*(1+Math.Clamp(bond,0,0.35)),def.Element,pet.Id.StartsWith("summon/",StringComparison.Ordinal)?"summoning":"animal_handling");
''')

# Out-of-combat decay keeps resources as encounter rhythm rather than permanent stockpiles.
replace_once("src/Kairnfall.Core/RealmEngine.cs",
'''            p.Health=Math.Min(p.Health,stats.Health); p.Mana=Math.Min(p.Mana,stats.Mana);
            p.Statuses.RemoveAll(x=>x.Until<=State.Time);
''',
'''            p.Health=Math.Min(p.Health,stats.Health); p.Mana=Math.Min(p.Mana,stats.Mana);
            ClassCombatRules.Tick(p,dt,State.Time);
            p.Statuses.RemoveAll(x=>x.Until<=State.Time);
''')

# Client-side cooldown helper used by the short, non-authoritative input buffer.
replace_once("client/Scripts/ExperienceRules.cs",
'''    public static string AbilityProblem(Character self, AbilityDef ability, Catalog data, double serverTime)
    {
''',
'''    public static double AbilityReadyIn(Character self, AbilityDef ability, double serverTime)
        => Math.Max(0, Math.Max(self.Cooldowns.GetValueOrDefault("ability:" + ability.Id), self.Cooldowns.GetValueOrDefault("global_ability")) - serverTime);

    public static string AbilityProblem(Character self, AbilityDef ability, Catalog data, double serverTime)
    {
''')

# Replace hotbar activation with a 350ms buffer. The server remains the final cooldown/target authority.
new_hotbar = r'''    private const double AbilityBufferSeconds = .35;
    private int queuedHotbar = -1;
    private double queuedAbilityUntil;

    private void UseHotbar(int index) => TryUseHotbar(index, true);
    private void TryUseHotbar(int index, bool allowQueue)
    {
        if (!GameplayInputAllowed || index < 0 || index >= hotbar.Length || string.IsNullOrEmpty(hotbar[index])) return;
        var snapshot = Snapshot!;
        var ability = Data.Ability(hotbar[index]);
        double readyIn = ExperienceRules.AbilityReadyIn(snapshot.Self, ability, snapshot.Time);
        string problem = ExperienceRules.AbilityProblem(snapshot.Self, ability, Data, snapshot.Time);
        if (problem != "")
        {
            if (allowQueue && readyIn > 0 && readyIn <= AbilityBufferSeconds)
            {
                queuedHotbar = index; queuedAbilityUntil = Time.GetTicksMsec() / 1000.0 + AbilityBufferSeconds + .12;
                Notify("Queued " + ability.Name + ".");
                return;
            }
            Notify(problem); return;
        }
        if (actionBusy)
        {
            if (allowQueue)
            {
                queuedHotbar = index; queuedAbilityUntil = Time.GetTicksMsec() / 1000.0 + AbilityBufferSeconds;
            }
            return;
        }
        queuedHotbar = -1;
        var point = World.ScreenToWorld(GetGlobalMousePosition());
        string targetId = selectedTargetKind is "creature" or "player" ? selectedTarget : "";
        if (ability.Kind is "heal" or "shield" or "buff" or "stealth" or "summon" or "purge")
        {
            if (ability.Kind != "heal" || selectedTargetKind != "player") { targetId = snapshot.Self.Id; point = snapshot.Self.Position; }
        }
        else if (ability.Kind is "strike" or "projectile" or "interrupt" or "drain" or "dot")
        {
            var target = ExperienceRules.ChooseTarget(snapshot.Self, snapshot.Creatures, Data, targetId, ability.Range);
            if (target is null) { Notify("No hostile creature is within this ability's range."); return; }
            targetId = target.Id; point = target.Position;
        }
        else
        {
            targetId = "";
            if (snapshot.Self.Position.Distance(point) > ability.Range)
                point = snapshot.Self.Position.Add(snapshot.Self.Facing.Scale(Math.Max(0, ability.Range - .1)));
        }
        _ = SendAsync(new GameCommand { Kind = "cast", Item = ability.Id, Target = targetId, X = point.X, Y = point.Y }, true);
    }

    private void TickAbilityBuffer()
    {
        if (queuedHotbar < 0 || Snapshot is not { } snapshot) return;
        double now = Time.GetTicksMsec() / 1000.0;
        if (!GameplayInputAllowed || now > queuedAbilityUntil)
        {
            queuedHotbar = -1; return;
        }
        var ability = Data.Ability(hotbar[queuedHotbar]);
        if (!actionBusy && ExperienceRules.AbilityReadyIn(snapshot.Self, ability, snapshot.Time) <= .02
            && ExperienceRules.AbilityProblem(snapshot.Self, ability, Data, snapshot.Time) == "")
            TryUseHotbar(queuedHotbar, false);
    }
'''
replace_between("client/Scripts/GameRoot.cs", "    private void UseHotbar(int index)\n", "    private void SetInitialHotbar()", new_hotbar)

# HUD meter and feedback fields.
replace_once("client/Scripts/GameRoot.Experience.cs",
'''    private ProgressBar characterExperienceBar = null!, skillExperienceBar = null!;
    private Button interactionButton = null!;
''',
'''    private ProgressBar characterExperienceBar = null!, skillExperienceBar = null!, classResourceBar = null!;
    private Label classResourceText = null!;
    private Button interactionButton = null!;
''')

replace_once("client/Scripts/GameRoot.Experience.cs",
'''        interactionHint.AddThemeColorOverride("font_outline_color", Ui.Ink);
        hud.AddChild(interactionHint);
        notice.OffsetTop = -252; notice.OffsetBottom = -216;
''',
'''        interactionHint.AddThemeColorOverride("font_outline_color", Ui.Ink);
        hud.AddChild(interactionHint);
        var classMeter = new VBoxContainer
        {
            Name = "ClassResourceHud", AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = 1, AnchorBottom = 1,
            OffsetLeft = -235, OffsetRight = 235, OffsetTop = -214, OffsetBottom = -184,
            MouseFilter = MouseFilterEnum.Ignore
        };
        classResourceText = Ui.Label("", 12, Ui.Text, true); classResourceText.HorizontalAlignment = HorizontalAlignment.Center;
        classResourceBar = new ProgressBar { MinValue = 0, MaxValue = 100, ShowPercentage = false, CustomMinimumSize = new Vector2(0, 7), MouseFilter = MouseFilterEnum.Ignore };
        classMeter.AddChild(classResourceText); classMeter.AddChild(classResourceBar); hud.AddChild(classMeter);
        notice.OffsetTop = -252; notice.OffsetBottom = -216;
''')

replace_once("client/Scripts/GameRoot.Experience.cs",
'''    private void TickExperience(double delta)
    {
        if (!GameplayInputAllowed) StopCombatInput();
        if (attackKeyHeld && !Input.IsActionPressed("basic_attack")) StopCombatInput();
        if (attackKeyHeld) TryBasicAttack();
''',
'''    private void TickExperience(double delta)
    {
        if (!GameplayInputAllowed) StopCombatInput();
        if (attackKeyHeld && !Input.IsActionPressed("basic_attack")) StopCombatInput();
        if (attackKeyHeld) TryBasicAttack();
        TickAbilityBuffer();
''')

replace_once("client/Scripts/GameRoot.Experience.cs",
'''        var context = GameplayInputAllowed ? ContextTarget() : null;
        UpdateMobControls();
''',
'''        var context = GameplayInputAllowed ? ContextTarget() : null;
        UpdateMobControls(); UpdateClassResourceHud();
''')

# Insert class HUD helpers before ObservePlayerChanges.
replace_once("client/Scripts/GameRoot.Experience.cs",
'''    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
''',
r'''    private static Color ClassResourceColor(string classId) => classId switch
    {
        "vanguard" => new Color("84a8c5"), "berserker" => new Color("d06a62"),
        "ranger" => new Color("8fbd74"), "rogue" => new Color("b18ac8"),
        "arcanist" => new Color("889be0"), "warden" => new Color("79b98b"),
        "templar" => new Color("e3c873"), "spellblade" => new Color("7fc6d8"), _ => Ui.Gold
    };

    private void UpdateClassResourceHud()
    {
        if (Snapshot is not { } snapshot || classResourceBar is null || classResourceText is null) return;
        ClassCombatRules.Normalize(snapshot.Self);
        string name = ClassCombatRules.ResourceName(snapshot.Self.Class);
        double threshold = ClassCombatRules.ReadyThreshold(snapshot.Self.Class);
        bool ready = snapshot.Self.ClassResource >= threshold;
        classResourceBar.Value = snapshot.Self.ClassResource;
        classResourceBar.Modulate = ClassResourceColor(snapshot.Self.Class);
        classResourceText.Text = name.ToUpperInvariant() + "  " + Math.Round(snapshot.Self.ClassResource) + "/100" + (ready ? "  ·  READY" : "");
        string description = ClassCombatRules.PassiveDescription(snapshot.Self.Class) + "\n" + ClassCombatRules.Hint(snapshot.Self);
        classResourceBar.TooltipText = description; classResourceText.TooltipText = description;
    }

    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
''')

# Authoritative snapshot deltas drive impact, ready and spend feedback; no client prediction changes combat state.
replace_once("client/Scripts/GameRoot.Experience.cs",
'''        if (previous is null || previous.Self.Id != current.Self.Id) return;
        if (previous.Self.Zone != current.Self.Zone)
''',
'''        if (previous is null || previous.Self.Id != current.Self.Id) return;
        if (current.Self.Health < previous.Self.Health - .5)
        {
            World.CombatImpact(current.Self.Position, 3.2f); audio?.PlayEffect("hurt");
        }
        if (selectedTargetKind == "creature")
        {
            var beforeTarget = previous.Creatures.FirstOrDefault(x => x.Id == selectedTarget);
            var afterTarget = current.Creatures.FirstOrDefault(x => x.Id == selectedTarget);
            if (beforeTarget is not null && afterTarget is not null && afterTarget.Health < beforeTarget.Health - .5)
            {
                World.CombatImpact(afterTarget.Position, 2.1f); audio?.PlayEffect("impact");
            }
        }
        double beforeResource = double.IsFinite(previous.Self.ClassResource) ? previous.Self.ClassResource : 0;
        double afterResource = double.IsFinite(current.Self.ClassResource) ? current.Self.ClassResource : 0;
        double threshold = ClassCombatRules.ReadyThreshold(current.Self.Class);
        Color resourceColor = ClassResourceColor(current.Self.Class);
        if (afterResource >= beforeResource + 4)
            World.CombatNote(current.Self.Position, ClassCombatRules.ResourceName(current.Self.Class).ToUpperInvariant() + " +" + Math.Round(afterResource - beforeResource), resourceColor);
        if (beforeResource < threshold && afterResource >= threshold)
        {
            World.ClassBurst(current.Self.Position, resourceColor); audio?.PlayEffect("class_ready");
        }
        else if (beforeResource - afterResource >= Math.Min(40, threshold))
        {
            World.ClassBurst(current.Self.Position, resourceColor); audio?.PlayEffect("class_release");
        }
        if (previous.Self.Zone != current.Self.Zone)
''')

# WorldView: deterministic micro-shake/rings and public floating combat notes.
replace_once("client/Scripts/WorldView.cs",
'''    private readonly List<FloatingNumber> numbers = [];
    private readonly List<Visual> visuals = [];
''',
'''    private readonly List<FloatingNumber> numbers = [];
    private readonly List<CombatBurst> combatBursts = [];
    private double impactUntil;
    private float impactStrength;
    private readonly List<Visual> visuals = [];
''')

replace_once("client/Scripts/WorldView.cs",
'''    private sealed record FloatingNumber(Point At, string Text, Color Color, double Started);
    private readonly record struct Visual(float Depth, string Kind, string Id, Point At, object? Value = null);
''',
'''    private sealed record FloatingNumber(Point At, string Text, Color Color, double Started);
    private sealed record CombatBurst(Point At, Color Color, double Started, float Strength);
    private readonly record struct Visual(float Depth, string Kind, string Id, Point At, object? Value = null);
''')

replace_once("client/Scripts/WorldView.cs",
'''    public void Animate(string id, int state, double duration)
    {
        if (!tracks.TryGetValue(id, out var track)) return;
        track.State = state; track.StateStart = Clock; track.StateUntil = Clock + duration;
    }

    public override void _Process(double delta)
''',
'''    public void Animate(string id, int state, double duration)
    {
        if (!tracks.TryGetValue(id, out var track)) return;
        track.State = state; track.StateStart = Clock; track.StateUntil = Clock + duration;
    }

    public void CombatNote(Point at, string text, Color color)
    {
        if (!at.Finite || string.IsNullOrWhiteSpace(text)) return;
        numbers.Add(new FloatingNumber(at, text, color, Clock));
    }

    public void CombatImpact(Point at, float strength = 2.5f)
    {
        if (!at.Finite) return;
        impactUntil = Math.Max(impactUntil, Clock + .16);
        impactStrength = Math.Max(impactStrength, Math.Clamp(strength, .5f, 4f));
        combatBursts.Add(new CombatBurst(at, new Color("f0c49b"), Clock, Math.Clamp(strength, .5f, 4f)));
    }

    public void ClassBurst(Point at, Color color)
    {
        if (!at.Finite) return;
        combatBursts.Add(new CombatBurst(at, color, Clock, 3.4f));
    }

    public override void _Process(double delta)
''')

replace_once("client/Scripts/WorldView.cs",
'''        numbers.RemoveAll(x => Clock - x.Started > 1.3);
        double day = WorldTime.DayFraction(RealmTime);
''',
'''        numbers.RemoveAll(x => Clock - x.Started > 1.3);
        combatBursts.RemoveAll(x => Clock - x.Started > .65);
        if (Clock >= impactUntil) impactStrength = 0;
        double day = WorldTime.DayFraction(RealmTime);
''')

replace_once("client/Scripts/WorldView.cs",
'''        origin = (Size / 2 - Pixels(Camera) * Zoom).Round();
''',
'''        Vector2 shake = Vector2.Zero;
        if (Clock < impactUntil)
        {
            float fade = (float)Math.Clamp((impactUntil - Clock) / .16, 0, 1);
            shake = new Vector2(MathF.Sin((float)Clock * 93f), MathF.Cos((float)Clock * 117f)) * impactStrength * fade;
        }
        origin = (Size / 2 - Pixels(Camera) * Zoom + shake).Round();
''')

replace_once("client/Scripts/WorldView.cs",
'''        visuals.Sort((a, b) => a.Depth.CompareTo(b.Depth));
        foreach (var visual in visuals) DrawVisual(zone, visual);
        foreach (var number in numbers)
''',
'''        visuals.Sort((a, b) => a.Depth.CompareTo(b.Depth));
        foreach (var visual in visuals) DrawVisual(zone, visual);
        foreach (var burst in combatBursts)
        {
            float elapsed = (float)(Clock - burst.Started);
            float progress = Math.Clamp(elapsed / .65f, 0, 1);
            float radius = 7 + progress * 22 * burst.Strength / 3.4f;
            Color color = burst.Color; color.A = 1 - progress;
            DrawArc(Pixels(burst.At), radius, 0, MathF.Tau, 28, color, 1.5f);
        }
        foreach (var number in numbers)
''')

# Reuse the existing deterministic sound bank with cue-specific pitch/body so the full audio expansion remains scoped to later polish work.
replace_once("client/Scripts/ClientAudio.cs",
'''        string key = action switch
        {
            "attack" => "sword", "cast" => "spell", "gather" => "gather",
            "loot" or "chest" or "buy" or "sell" => "coins", "craft" or "build" => "hammer",
            "equip" or "unequip" or "socket" or "unsocket" => "equip", "consume" or "rest" => "drink", _ => "ui"
        };
''',
'''        string key = action switch
        {
            "attack" or "impact" => "sword", "cast" or "class_release" => "spell", "hurt" => "hammer", "class_ready" => "ui", "gather" => "gather",
            "loot" or "chest" or "buy" or "sell" => "coins", "craft" or "build" => "hammer",
            "equip" or "unequip" or "socket" or "unsocket" => "equip", "consume" or "rest" => "drink", _ => "ui"
        };
''')
replace_once("client/Scripts/ClientAudio.cs",
'''        var player = voices[voice++ % voices.Count]; player.Stop(); player.Stream = stream;
        player.PitchScale = 1 + (voice % 3 - 1) * .035f; player.Play();
''',
'''        var player = voices[voice++ % voices.Count]; player.Stop(); player.Stream = stream;
        float cuePitch = action switch { "hurt" => .72f, "impact" => .92f, "class_ready" => 1.22f, "class_release" => .84f, _ => 1f };
        player.PitchScale = cuePitch * (1 + (voice % 3 - 1) * .035f); player.Play();
''')

# The permanent CI must compile the Godot client too; combat presentation is now part of the accepted code path.
replace_once(".github/workflows/ci.yml",
'''      - name: Compile every implemented project
        run: dotnet build Kairnfall.slnx -c Release | tee artifacts/logs/build.log
''',
'''      - name: Compile every implemented project and the Godot client
        run: |
          dotnet build Kairnfall.slnx -c Release | tee artifacts/logs/build.log
          dotnet build client/Kairnfall.Client.csproj -c Release | tee artifacts/logs/client-build.log
''')

checks = r'''using Kairnfall.Core;

internal static class ClassCombatIdentityChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action body)
        {
            try{body();passed++;Console.WriteLine("PASS CLASS IDENTITY: "+name);}
            catch(Exception error){failures.Add("Class identity: "+name);Console.WriteLine("FAIL CLASS IDENTITY: "+name+": "+error.Message);}
        }
        Character Player(string cls,double resource=0)=>new(){Class=cls,ClassResource=resource,Health=100,Mana=100,Stamina=100,LastCombat=0};

        Test("all eight classes expose distinct visible combat resources",()=>
        {
            Need(data.Classes.Count==8,"Expected exactly eight classes.");
            var names=data.Classes.Select(x=>ClassCombatRules.ResourceName(x.Id)).ToArray();
            Need(names.Distinct(StringComparer.Ordinal).Count()==8,"Class resource names are not distinct.");
            foreach(var cls in data.Classes)
            {
                string resource=ClassCombatRules.ResourceName(cls.Id);
                Need(cls.Passive.Contains(resource,StringComparison.Ordinal),cls.Id+" character-creation passive does not explain "+resource+".");
                Need(ClassCombatRules.ReadyThreshold(cls.Id) is >=40 and <=60,cls.Id+" has an invalid empowered threshold.");
            }
        });

        Test("martial identities build resource from their intended combat behavior",()=>
        {
            var v=Player("vanguard");ClassCombatRules.RecordIncoming(v,20,8,true,false);Need(v.ClassResource>=20,"Vanguard did not build Resolve from a block.");
            var b=Player("berserker");ClassCombatRules.RecordDamage(b,20,Element.Physical,"axe_mastery",1.5);ClassCombatRules.RecordIncoming(b,10,5,false,false);Need(b.ClassResource>=14,"Berserker did not build Fury from trading damage.");
            var r=Player("ranger");ClassCombatRules.RecordDamage(r,20,Element.Physical,"archery",7.5);Need(r.ClassResource>=15,"Ranger did not build Focus at long range.");
            var q=Player("rogue");ClassCombatRules.RecordDamage(q,20,Element.Physical,"dagger_mastery",1.5);ClassCombatRules.RecordIncoming(q,0,0,false,true);Need(q.ClassResource>=24,"Rogue did not build Momentum from close pressure and an evade.");
        });

        Test("caster support and hybrid identities have distinct build-spend loops",()=>
        {
            var a=Player("arcanist");ClassCombatRules.RecordDamage(a,20,Element.Fire,"pyromancy",5);Need(a.ClassResource==12,"Arcanist Resonance gain changed.");
            var w=Player("warden");var heal=data.Abilities.First(x=>x.Class=="warden"&&x.Kind=="heal");ClassCombatRules.RecordCast(w,heal,true);Need(w.ClassResource==18,"Warden support did not build Bond.");
            var t=Player("templar");var ward=data.Abilities.First(x=>x.Class=="templar"&&x.Kind=="shield");ClassCombatRules.RecordCast(t,ward,true);ClassCombatRules.RecordDamage(t,10,Element.Radiant,"radiance",2);Need(t.ClassResource>=28,"Templar did not build Conviction through support plus Radiant pressure.");
            var s=Player("spellblade");ClassCombatRules.RecordDamage(s,10,Element.Arcane,"runecasting",2);double first=s.ClassResource;ClassCombatRules.RecordDamage(s,10,Element.Physical,"swordsmanship",2);Need(first==5&&s.ClassResource==30&&s.ClassState=="martial","Spellblade did not reward alternating forms.");
        });

        Test("native empowered techniques consume class resource without banning cross-class skills",()=>
        {
            foreach(var cls in data.Classes)
            {
                var p=Player(cls.Id,100); if(cls.Id=="spellblade")p.ClassState="magic";
                var ability=cls.Id switch
                {
                    "vanguard"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="shield"),
                    "berserker"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="strike"),
                    "ranger"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="projectile"),
                    "rogue"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="strike"),
                    "arcanist"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="projectile"),
                    "warden"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="shield"),
                    "templar"=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="strike"),
                    _=>data.Abilities.First(x=>x.Class==cls.Id&&x.Kind=="strike")
                };
                var bonus=ClassCombatRules.PrepareCast(p,ability,false);Need(bonus.Empowered&&p.ClassResource<100,cls.Id+" did not consume its ready resource.");
            }
            var cross=Player("vanguard",100);var foreign=data.Abilities.First(x=>x.Class=="arcanist"&&x.Kind=="projectile");var before=cross.ClassResource;
            var foreignBonus=ClassCombatRules.PrepareCast(cross,foreign,false);Need(!foreignBonus.Empowered&&cross.ClassResource==before,"Using trained off-class magic consumed Vanguard Resolve.");
        });

        Test("real RealmEngine casts exercise every class identity",()=>
        {
            string[] classes=["vanguard","berserker","ranger","rogue","arcanist","warden","templar","spellblade"];
            foreach(string cls in classes)
            {
                var realm=new RealmEngine(data);var p=realm.CreateCharacter("class-identity-"+cls,"Identity "+cls,cls,new());realm.Active.Add(p.Id);
                var zone=data.Zone(p.Zone);p.Position=zone.Spawn;p.ClassResource=100;if(cls=="spellblade")p.ClassState="magic";
                var ability=cls switch
                {
                    "vanguard"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="shield"),
                    "berserker"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="strike"),
                    "ranger"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="projectile"),
                    "rogue"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="strike"),
                    "arcanist"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="projectile"),
                    "warden"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="shield"),
                    "templar"=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="strike"),
                    _=>data.Abilities.First(x=>x.Class==cls&&x.Kind=="strike")
                };
                p.SkillXp[ability.Skill]=Progression.Threshold(ability.Requirement);p.Mana=100000;p.Stamina=100000;
                string target="";Point aim=p.Position;
                if(ability.Kind is "strike" or "projectile" or "dot" or "drain" or "interrupt")
                {
                    var definition=data.Mob("field_rat");var at=WorldMap.FindFree(zone,new(p.Position.X+1,p.Position.Y));
                    target="identity-target-"+cls;realm.State.Creatures[target]=new(){Id=target,Template=definition.Id,Zone=p.Zone,Position=at,Home=at,Health=definition.Health};aim=at;
                }
                double before=p.ClassResource;
                var result=realm.Execute(p.Id,new GameCommand{Kind="cast",Item=ability.Id,Target=target,X=aim.X,Y=aim.Y,Sequence=p.LastAction+1});
                Need(result.Ok,cls+" representative technique failed: "+result.Message);Need(p.ClassResource<before,cls+" representative technique did not spend its ready resource.");
            }
        });

        Test("class resource is save-safe bounded and decays outside combat",()=>
        {
            var p=Player("spellblade",100);p.ClassState="magic";p.LastCombat=0;ClassCombatRules.Tick(p,1,20);Need(p.ClassResource==88,"Out-of-combat decay changed.");
            var copy=Wire.Copy(p);Need(copy.ClassResource==88&&copy.ClassState=="magic","Class identity state did not survive serialization.");
            copy.ClassResource=double.NaN;ClassCombatRules.Normalize(copy);Need(copy.ClassResource==0,"Non-finite class resource did not fail closed.");
            ClassCombatRules.Tick(copy,20,40);Need(copy.ClassResource==0&&copy.ClassState=="","Empty Spellweave did not clear its alternating-form state.");
        });

        Test("client exposes meter buffering and authoritative impact feedback",()=>
        {
            string root=Directory.GetCurrentDirectory();
            string experience=File.ReadAllText(Path.Combine(root,"client/Scripts/GameRoot.Experience.cs"));
            string game=File.ReadAllText(Path.Combine(root,"client/Scripts/GameRoot.cs"));
            string world=File.ReadAllText(Path.Combine(root,"client/Scripts/WorldView.cs"));
            string audio=File.ReadAllText(Path.Combine(root,"client/Scripts/ClientAudio.cs"));
            Need(experience.Contains("ClassResourceHud",StringComparison.Ordinal)&&experience.Contains("READY",StringComparison.Ordinal),"Class meter is not visible in the combat HUD.");
            Need(game.Contains("AbilityBufferSeconds = .35",StringComparison.Ordinal)&&game.Contains("TickAbilityBuffer",StringComparison.Ordinal),"Short ability input buffer is absent.");
            Need(world.Contains("CombatImpact",StringComparison.Ordinal)&&world.Contains("ClassBurst",StringComparison.Ordinal),"Impact shake/class burst presentation is absent.");
            Need(audio.Contains("class_ready",StringComparison.Ordinal)&&audio.Contains("class_release",StringComparison.Ordinal)&&audio.Contains("impact",StringComparison.Ordinal),"Combat feedback audio cues are absent.");
        });

        Console.WriteLine($"CLASS COMBAT IDENTITY: {passed} groups passed; total failures {failures.Count}.");
    }
}
'''
save("tools/world_probe/ClassCombatIdentityChecks.cs", checks)
replace_once("tools/world_probe/Program.cs",
'''CombatVarietyChecks.Run(catalog,failures);
ExplorationRewardChecks.Run(catalog,failures);
''',
'''CombatVarietyChecks.Run(catalog,failures);
ClassCombatIdentityChecks.Run(catalog,failures);
ExplorationRewardChecks.Run(catalog,failures);
''')

doc = r'''# Combat feel and class identity

Status: implementation candidate; the publication workflow replaces this line with exact verification evidence after the feature is pushed.

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

## Verification boundary

`ClassCombatIdentityChecks` validates the eight distinct resource loops, native spend rules, cross-class freedom, real `RealmEngine` representative casts, save/decay safety, and client feedback contracts. Existing 60-skill, 120-class-ability, combat-variety, world, economy and network suites must remain green. Automation establishes mechanics and code integration; subjective timing, punch and class feel still benefit from hands-on play.
'''
save("docs/COMBAT_CLASS_IDENTITY.md", doc)

print("Combat feel and class identity candidate applied.")
