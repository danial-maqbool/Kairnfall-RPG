namespace Kairnfall.Core;

/// <summary>Shared server/client contract for staged public events and their temporary regional aftermath.</summary>
public static class WorldEventRules
{
    public const double SpawnCadence = 240;
    public const double SuccessAftermathSeconds = 180;
    public const double FailureAftermathSeconds = 120;
    public static readonly string[] Kinds =
    [
        "meteor", "caravan", "undead", "arcane_rift",
        "settlement_siege", "migration", "treasure_surge", "world_boss"
    ];

    public static string NormalizeKind(string kind) => kind == "arcane_storm" ? "arcane_rift" : kind;
    public static string Name(string kind) => NormalizeKind(kind) switch
    {
        "meteor" => "Starfall Harvest",
        "caravan" => "Wayfarer Caravan",
        "undead" => "Restless Graves",
        "arcane_rift" => "Arcane Rift",
        "settlement_siege" => "Settlement Under Siege",
        "migration" => "Wild Migration",
        "treasure_surge" => "Treasure Surge",
        "world_boss" => "Regional Terror",
        _ => "Public Event"
    };
    public static int StageCount(string kind) => NormalizeKind(kind) is "treasure_surge" or "world_boss" ? 1 : 2;
    public static string StageLabel(string kind, int stage) => (NormalizeKind(kind), stage) switch
    {
        ("meteor", 0) => "Harvest fallen star fragments",
        ("meteor", _) => "Defeat the Starborn champion",
        ("caravan", 0) => "Escort the caravan through danger",
        ("caravan", _) => "Break the final ambush",
        ("undead", 0) => "Break the graveborn wave",
        ("undead", _) => "Destroy the Grave Herald",
        ("arcane_rift", 0) => "Stabilize the unstable rift",
        ("arcane_rift", _) => "Defeat the Rift Sentinel",
        ("settlement_siege", 0) => "Repel the attackers",
        ("settlement_siege", _) => "Defeat the siege commander",
        ("migration", 0) => "Drive back the migration",
        ("migration", _) => "Defeat the apex beast",
        ("treasure_surge", _) => "Recover the surge caches",
        ("world_boss", _) => "Defeat the regional terror",
        _ => "Respond to the event"
    };
    public static string StageLabel(WorldEvent value) => value.Status == "active"
        ? StageLabel(value.Kind, value.Stage)
        : value.Status == "success" ? "SUCCESS · " + EffectLabel(value.Effect) : "FAILED · " + EffectLabel(value.Effect);

    public static bool SupportsInteraction(WorldEvent value)
        => value.Status == "active" && value.Stage == 0 && NormalizeKind(value.Kind) is "arcane_rift" or "caravan";
    public static string InteractionVerb(WorldEvent value) => NormalizeKind(value.Kind) switch
    {
        "arcane_rift" => "Stabilize",
        "caravan" => "Rally",
        _ => "Aid"
    };
    public static bool IsCombatStage(string kind, int stage) => (NormalizeKind(kind), stage) switch
    {
        ("meteor", 1) => true,
        ("caravan", 1) => true,
        ("undead", _) => true,
        ("arcane_rift", 1) => true,
        ("settlement_siege", _) => true,
        ("migration", _) => true,
        ("world_boss", _) => true,
        _ => false
    };
    public static int BaseGoal(string kind, int stage) => (NormalizeKind(kind), stage) switch
    {
        ("meteor", 0) => 4,
        ("meteor", _) => 1,
        ("caravan", 0) => 18,
        ("caravan", _) => 4,
        ("undead", 0) => 5,
        ("undead", _) => 1,
        ("arcane_rift", 0) => 5,
        ("arcane_rift", _) => 1,
        ("settlement_siege", 0) => 6,
        ("settlement_siege", _) => 1,
        ("migration", 0) => 5,
        ("migration", _) => 1,
        ("treasure_surge", _) => 4,
        ("world_boss", _) => 1,
        _ => 1
    };
    public static int ScaledGoal(string kind, int stage, int participants)
    {
        int baseGoal = BaseGoal(kind, stage);
        participants = Math.Clamp(participants, 1, 6);
        if (stage > 0 || NormalizeKind(kind) == "world_boss") return baseGoal;
        int extra = NormalizeKind(kind) switch
        {
            "caravan" => 4,
            "undead" or "settlement_siege" => 2,
            _ => 1
        };
        return baseGoal + (participants - 1) * extra;
    }
    public static double StageDuration(string kind, int stage) => (NormalizeKind(kind), stage) switch
    {
        ("world_boss", _) => 300,
        ("caravan", 0) => 240,
        ("arcane_rift", 0) => 180,
        (_, 0) => 210,
        _ => 150
    };
    public static string SuccessEffect(string kind) => NormalizeKind(kind) switch
    {
        "meteor" => "starfall_bounty",
        "caravan" => "safe_roads",
        "undead" => "hallowed_ground",
        "arcane_rift" => "arcane_clarity",
        "settlement_siege" => "settlement_morale",
        "migration" => "wild_bounty",
        "treasure_surge" => "fortune",
        "world_boss" => "heroic_morale",
        _ => "heroic_morale"
    };
    public static string EffectLabel(string effect) => effect switch
    {
        "starfall_bounty" => "Starfall bounty · richer gathering",
        "safe_roads" => "Safe roads · faster travel and stamina recovery",
        "hallowed_ground" => "Hallowed ground · stronger health recovery",
        "arcane_clarity" => "Arcane clarity · stronger mana recovery",
        "settlement_morale" => "High morale · health and stamina recovery",
        "wild_bounty" => "Wild bounty · richer gathering",
        "fortune" => "Fortune · richer treasure chests",
        "heroic_morale" => "Heroic morale · health and stamina recovery",
        "regional_unrest" => "Regional unrest · slower travel and stronger enemies",
        _ => "The region is settling"
    };
    public static bool EligibleZone(string kind, ZoneDef zone)
    {
        kind = NormalizeKind(kind);
        if (zone.Layer != "Surface" || zone.Kind == "interior") return false;
        return kind switch
        {
            "settlement_siege" => zone.Kind is "city" or "settlement" && zone.Id != "wayfarers_rest",
            "world_boss" => zone.Kind == "wilderness" && zone.Level >= 35,
            "arcane_rift" => zone.Kind == "wilderness" && zone.Level >= 25,
            "undead" => zone.Kind == "wilderness" && zone.Level >= 12,
            _ => zone.Kind == "wilderness"
        };
    }
    public static bool Owns(WorldEvent value, string candidate) => candidate == value.Id || candidate.StartsWith(value.Id + "/", StringComparison.Ordinal);
    public static WorldEvent? Owner(RealmState state, string candidate) => state.Events
        .Where(value => Owns(value, candidate)).OrderByDescending(value => value.Id.Length).FirstOrDefault();
    public static double Contribution(WorldEvent value, string player) => value.Contributions.GetValueOrDefault(player);
    public static string ProgressText(WorldEvent value)
    {
        if (value.Status != "active") return EffectLabel(value.Effect);
        double goal = Math.Max(1, value.Goal);
        return $"{Math.Min(goal, Math.Max(0, value.Progress)):0}/{goal:0}";
    }
    public static string ActiveEffect(RealmState state, string zone, double now) => state.Events
        .Where(value => value.Zone == zone && value.Status is "success" or "failure" && value.EffectEnds > now)
        .OrderByDescending(value => value.EffectEnds).Select(value => value.Effect).FirstOrDefault() ?? "";
    public static double MovementMultiplier(RealmState state, string zone, double now) => ActiveEffect(state, zone, now) switch
    {
        "safe_roads" => 1.12,
        "regional_unrest" => .94,
        _ => 1
    };
    public static double StaminaRegenBonus(RealmState state, string zone, double now) => ActiveEffect(state, zone, now) switch
    {
        "safe_roads" => 2.5,
        "settlement_morale" => 1.5,
        "heroic_morale" => 1.5,
        _ => 0
    };
    public static double ManaRegenBonus(RealmState state, string zone, double now)
        => ActiveEffect(state, zone, now) == "arcane_clarity" ? 2 : 0;
    public static double HealthRegenBonus(RealmState state, string zone, double now) => ActiveEffect(state, zone, now) switch
    {
        "hallowed_ground" => 1.5,
        "settlement_morale" => 1,
        "heroic_morale" => 1,
        _ => 0
    };
    public static double GatherYieldBonus(RealmState state, string zone, double now) => ActiveEffect(state, zone, now) switch
    {
        "starfall_bounty" => 18,
        "wild_bounty" => 12,
        _ => 0
    };
    public static double TreasureGoldMultiplier(RealmState state, string zone, double now)
        => ActiveEffect(state, zone, now) == "fortune" ? 1.35 : 1;
    public static double EnemyPowerMultiplier(RealmState state, string zone, double now)
        => ActiveEffect(state, zone, now) == "regional_unrest" ? 1.10 : 1;
}
