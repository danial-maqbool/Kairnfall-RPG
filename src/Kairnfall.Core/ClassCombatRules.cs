namespace Kairnfall.Core;

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
    private static string SpellbladeFamily(string skill,Element element)
        => skill is "swordsmanship" or "axe_mastery" or "mace_mastery" or "spear_mastery" or "dagger_mastery" or "unarmed_combat"
            ? "martial" : element==Element.Physical ? "martial" : "magic";

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
                string family = SpellbladeFamily(ability.Skill,ability.Element);
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
                string family = SpellbladeFamily(skill,element);
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
