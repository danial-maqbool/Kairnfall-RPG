from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def write(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")

def replace_once(path, old, new):
    text = read(path)
    if old not in text:
        raise SystemExit(f"expected text not found in {path}: {old[:120]!r}")
    write(path, text.replace(old, new, 1))

def regex_once(path, pattern, replacement):
    text = read(path)
    changed, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f"expected one regex match in {path}, got {count}: {pattern}")
    write(path, changed)

WORLD_EVENT_RULES = r'''namespace Kairnfall.Core;

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
'''

REALM_EVENTS = r'''namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private void TickEvents()
    {
        foreach (var value in State.Events.ToList()) UpgradeLegacyEvent(value);
        foreach (var value in State.Events.Where(x => x.Status == "active").ToList())
        {
            ScaleEventForParticipants(value);
            if (value.Kind == "caravan" && value.Stage == 0) TickCaravan(value);
            if (value.Progress >= Math.Max(1, value.Goal)) AdvanceEvent(value);
            else if (value.StageEnds > 0 && State.Time >= value.StageEnds) ResolveEvent(value, false);
        }
        if (WorldEventLifecycle.Expire(State, State.Time) > 0) EconomicDirty = true;

        long cycle = (long)(State.Time / WorldEventRules.SpawnCadence);
        if (cycle == lastEventCycle) return;
        lastEventCycle = cycle;
        if (State.Events.Count(x => x.Status == "active") >= 3) return;
        CreateScheduledEvent(cycle);
    }

    private void UpgradeLegacyEvent(WorldEvent value)
    {
        value.Kind = WorldEventRules.NormalizeKind(value.Kind);
        if (string.IsNullOrWhiteSpace(value.Status)) value.Status = "active";
        if (value.Status != "active")
        {
            if (value.EffectEnds <= 0) value.EffectEnds = value.Ends;
            return;
        }
        if (value.StageEnds > 0) return;
        if (!Data.Zones.Any(x => x.Id == value.Zone)) { value.Status = "failure"; value.Ends = State.Time; return; }
        WorldEventLifecycle.CleanupOwned(State, value.Id);
        if (value.Ends > 0 && value.Ends <= State.Time)
        {
            value.Status = "failure"; value.Effect = "regional_unrest";
            value.EffectEnds = State.Time + WorldEventRules.FailureAftermathSeconds; value.Ends = value.EffectEnds;
            EconomicDirty = true; return;
        }
        value.Started = value.Started > 0 ? value.Started : State.Time;
        value.Stage = Math.Clamp(value.Stage, 0, WorldEventRules.StageCount(value.Kind) - 1);
        value.Position = WorldMap.FindFree(Data.Zone(value.Zone), value.Position.Finite ? value.Position : Data.Zone(value.Zone).Spawn);
        StartEventStage(value);
    }

    private void CreateScheduledEvent(long cycle)
    {
        string kind = WorldEventRules.Kinds[(int)(Math.Abs(cycle) % WorldEventRules.Kinds.Length)];
        var candidates = Data.Zones.Where(x => WorldEventRules.EligibleZone(kind, x)).OrderBy(x => x.Id, StringComparer.Ordinal).ToArray();
        if (candidates.Length == 0) candidates = Data.Zones.Where(x => x.Kind == "wilderness" && x.Layer == "Surface").OrderBy(x => x.Id, StringComparer.Ordinal).ToArray();
        if (candidates.Length == 0) return;
        int start = (int)(WorldMap.Hash((int)(cycle % int.MaxValue), WorldEventRules.Kinds.Length, 1777) % (uint)candidates.Length);
        ZoneDef zone = candidates[start];
        for (int n = 0; n < candidates.Length; n++)
        {
            var candidate = candidates[(start + n) % candidates.Length];
            if (!State.Events.Any(x => x.Zone == candidate.Id && x.Ends > State.Time)) { zone = candidate; break; }
        }
        uint hash = WorldMap.Hash((int)(cycle % int.MaxValue), zone.Seed, 2711);
        var near = new Point(zone.Spawn.X + 7 + hash % 9, zone.Spawn.Y + 5 + (hash / 11) % 9);
        var value = new WorldEvent
        {
            Id = "event/" + cycle,
            Kind = kind,
            Name = WorldEventRules.Name(kind),
            Zone = zone.Id,
            Position = WorldMap.FindFree(zone, near),
            Status = "active",
            Started = State.Time
        };
        if (kind == "caravan") value.Destination = WorldMap.FindFree(zone, new(zone.Spawn.X - 13, zone.Spawn.Y - 8));
        State.Events.Add(value); StartEventStage(value); EconomicDirty = true;
    }

    private List<Character> EventParticipants(WorldEvent value, double radius = 32) => Active
        .Where(State.Characters.ContainsKey).Select(Player)
        .Where(x => x.Health > 0 && x.Zone == value.Zone && x.Position.Distance(value.Position) <= radius).ToList();

    private void StartEventStage(WorldEvent value)
    {
        WorldEventLifecycle.CleanupOwned(State, value.Id);
        int participants = Math.Max(1, EventParticipants(value).Count);
        value.Difficulty = participants; value.Progress = 0; value.Wave = 0; value.LastTick = 0;
        value.Goal = WorldEventRules.ScaledGoal(value.Kind, value.Stage, participants);
        value.StageStarted = State.Time; value.StageEnds = State.Time + WorldEventRules.StageDuration(value.Kind, value.Stage); value.Ends = value.StageEnds;
        SpawnStageObjects(value, (int)Math.Ceiling(value.Goal)); EconomicDirty = true;
    }

    private void ScaleEventForParticipants(WorldEvent value)
    {
        if (value.Stage != 0 || value.Progress >= value.Goal * .75) return;
        int participants = Math.Clamp(EventParticipants(value).Count, 1, 6);
        if (participants <= value.Difficulty) return;
        int oldGoal = (int)Math.Ceiling(value.Goal);
        int newGoal = WorldEventRules.ScaledGoal(value.Kind, value.Stage, participants);
        value.Difficulty = participants;
        if (newGoal > oldGoal)
        {
            value.Goal = newGoal; SpawnStageObjects(value, newGoal - oldGoal); EconomicDirty = true;
        }
    }

    private void SpawnStageObjects(WorldEvent value, int amount)
    {
        if (amount <= 0) return;
        string kind = WorldEventRules.NormalizeKind(value.Kind);
        if (kind == "meteor" && value.Stage == 0) SpawnEventNodes(value, amount);
        else if (kind == "treasure_surge" && value.Stage == 0) SpawnEventChests(value, amount);
        else if (WorldEventRules.IsCombatStage(kind, value.Stage))
            for (int n = 0; n < amount; n++) SpawnEventMob(value, value.Stage > 0 || kind == "world_boss", n);
    }

    private void SpawnEventNodes(WorldEvent value, int amount)
    {
        string template = Data.Resources.Any(x => x.Id == "meteor_ore") ? "meteor_ore" : Data.Resources.First(x => x.Skill == "mining").Id;
        var zone = Data.Zone(value.Zone); int serial = State.Nodes.Keys.Count(x => x.StartsWith(value.Id + "/node/", StringComparison.Ordinal));
        for (int n = 0; n < amount; n++)
        {
            double angle = (serial + n) * 2.399;
            var at = WorldMap.FindFree(zone, new(value.Position.X + Math.Cos(angle) * (3 + (serial + n) % 3), value.Position.Y + Math.Sin(angle) * (3 + (serial + n) % 3)));
            string id = $"{value.Id}/node/{serial + n}"; State.Nodes[id] = new() { Id = id, Template = template, Zone = value.Zone, Position = at };
        }
    }

    private void SpawnEventChests(WorldEvent value, int amount)
    {
        var zone = Data.Zone(value.Zone); int serial = State.Chests.Keys.Count(x => x.StartsWith(value.Id + "/chest/", StringComparison.Ordinal));
        for (int n = 0; n < amount; n++)
        {
            double angle = (serial + n) * 2.399;
            var at = WorldMap.FindFree(zone, new(value.Position.X + Math.Cos(angle) * 4, value.Position.Y + Math.Sin(angle) * 4));
            string id = $"{value.Id}/chest/{serial + n}";
            State.Chests[id] = new() { Id = id, Zone = value.Zone, Position = at, Kind = "royal", Requirement = Math.Clamp(zone.Level, 1, 100) };
        }
    }

    private MobDef EventMobDefinition(WorldEvent value, bool champion)
    {
        string kind = WorldEventRules.NormalizeKind(value.Kind); var zone = Data.Zone(value.Zone);
        IEnumerable<MobDef> pool = kind == "world_boss" ? Data.Mobs.Where(x => x.Boss)
            : champion ? Data.Mobs.Where(x => x.Elite)
            : Data.Mobs.Where(x => !x.Boss && !x.Elite && x.Ai != "passive");
        bool Theme(MobDef x) => kind switch
        {
            "undead" => x.Anatomy.StartsWith("undead:", StringComparison.Ordinal) || x.Family.Contains("skeleton", StringComparison.Ordinal),
            "arcane_rift" or "meteor" => x.Element == Element.Arcane || x.Family == "elemental" || x.Biome == "arcane_anomaly",
            "settlement_siege" or "caravan" => x.Anatomy.StartsWith("humanoid:", StringComparison.Ordinal),
            "migration" => x.Anatomy.StartsWith("animal:", StringComparison.Ordinal),
            _ => true
        };
        var themed = pool.Where(Theme).ToArray(); if (themed.Length > 0) pool = themed;
        var options = pool.OrderBy(x => Math.Abs(x.Level - zone.Level)).ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
        if (options.Length == 0) options = Data.Mobs.Where(x => !x.Boss && x.Ai != "passive").OrderBy(x => Math.Abs(x.Level - zone.Level)).ToArray();
        return options[0];
    }

    private void SpawnEventMob(WorldEvent value, bool champion, int offset)
    {
        var def = EventMobDefinition(value, champion); var zone = Data.Zone(value.Zone);
        int serial = State.Creatures.Keys.Count(x => x.StartsWith(value.Id + "/mob/", StringComparison.Ordinal));
        double angle = (serial + offset) * 2.399;
        var at = WorldMap.FindFree(zone, new(value.Position.X + Math.Cos(angle) * (2.5 + serial % 3), value.Position.Y + Math.Sin(angle) * (2.5 + serial % 3)));
        string id = $"{value.Id}/mob/{value.Stage}/{serial}";
        State.Creatures[id] = new() { Id = id, Template = def.Id, Zone = value.Zone, Position = at, Home = at, Health = def.Health };
    }

    private bool EventHasLivingMobs(WorldEvent value) => State.Creatures.Values.Any(x => WorldEventRules.Owns(value, x.Id) && x.Health > 0);

    private void TickCaravan(WorldEvent value)
    {
        if (value.LastTick > 0 && State.Time - value.LastTick < 1) return;
        value.LastTick = State.Time;
        if (EventHasLivingMobs(value)) return;
        var participants = EventParticipants(value, 7);
        if (participants.Count == 0) return;
        foreach (var player in participants) AddEventContribution(value, player.Id, 1.5);
        value.Progress += 1;
        var zone = Data.Zone(value.Zone);
        if (!value.Destination.Finite || value.Destination.Distance(new(0, 0)) < .01)
            value.Destination = WorldMap.FindFree(zone, new(zone.Spawn.X - 13, zone.Spawn.Y - 8));
        var direction = value.Position.Direction(value.Destination);
        value.Position = WorldMap.Move(zone, value.Position, direction.Scale(.65));
        int desiredWave = value.Progress >= value.Goal * .66 ? 2 : value.Progress >= value.Goal * .33 ? 1 : 0;
        while (value.Wave < desiredWave)
        {
            value.Wave++;
            for (int n = 0; n < 2 + Math.Min(3, value.Difficulty - 1); n++) SpawnEventMob(value, false, n);
        }
        EconomicDirty = true;
    }

    private void AddEventContribution(WorldEvent value, string player, double amount)
    {
        if (amount <= 0 || !double.IsFinite(amount)) return;
        value.Contributions[player] = Math.Min(1_000_000, value.Contributions.GetValueOrDefault(player) + amount); EconomicDirty = true;
    }

    private void RecordEventDamage(Character player, Creature mob, double damage)
    {
        var value = WorldEventRules.Owner(State, mob.Id);
        if (value is null || value.Status != "active" || damage <= 0) return;
        AddEventContribution(value, player.Id, Math.Max(.1, damage / 10));
    }

    private void RecordEventKill(Creature mob, IReadOnlyCollection<Character> contributors)
    {
        var value = WorldEventRules.Owner(State, mob.Id);
        if (value is null || value.Status != "active") return;
        foreach (var player in contributors) AddEventContribution(value, player.Id, 6);
        if (WorldEventRules.IsCombatStage(value.Kind, value.Stage)) value.Progress += 1;
        EconomicDirty = true;
    }

    private bool RecordEventGather(Character player, string nodeId)
    {
        var value = WorldEventRules.Owner(State, nodeId);
        if (value is null || value.Status != "active" || WorldEventRules.NormalizeKind(value.Kind) != "meteor" || value.Stage != 0) return false;
        value.Progress += 1; AddEventContribution(value, player.Id, 10); EconomicDirty = true; return true;
    }

    private bool RecordEventChest(Character player, string chestId)
    {
        var value = WorldEventRules.Owner(State, chestId);
        if (value is null || value.Status != "active" || WorldEventRules.NormalizeKind(value.Kind) != "treasure_surge" || value.Stage != 0) return false;
        value.Progress += 1; AddEventContribution(value, player.Id, 10); EconomicDirty = true; return true;
    }

    private string EventAction(Character player, string eventId)
    {
        var value = State.Events.FirstOrDefault(x => x.Id == eventId) ?? throw new RuleException("This public event is no longer active.");
        Need(WorldEventRules.SupportsInteraction(value), "This event advances through its current world objective.");
        Near(player, value.Zone, value.Position, 3.2); Ready(player, "event:" + value.Id, 2.5);
        Need(player.Stamina >= 4, "Recover stamina before helping the event."); player.Stamina -= 4;
        value.Progress += 1; AddEventContribution(value, player.Id, 8);
        string kind = WorldEventRules.NormalizeKind(value.Kind);
        Progression.Train(player, kind == "arcane_rift" ? "survival" : "exploration", kind == "arcane_rift" ? 8 : 4, Math.Clamp(Data.Zone(value.Zone).Level, 1, 100), Data);
        return WorldEventRules.InteractionVerb(value) + "d · " + WorldEventRules.ProgressText(value) + ".";
    }

    private void AdvanceEvent(WorldEvent value)
    {
        if (value.Status != "active") return;
        if (value.Stage + 1 >= WorldEventRules.StageCount(value.Kind)) { ResolveEvent(value, true); return; }
        value.Stage++; StartEventStage(value);
    }

    private void ResolveEvent(WorldEvent value, bool success)
    {
        if (value.Status != "active") return;
        WorldEventLifecycle.CleanupOwned(State, value.Id);
        value.Status = success ? "success" : "failure";
        value.Effect = success ? WorldEventRules.SuccessEffect(value.Kind) : "regional_unrest";
        value.EffectEnds = State.Time + (success ? WorldEventRules.SuccessAftermathSeconds : WorldEventRules.FailureAftermathSeconds);
        value.Ends = value.EffectEnds; value.StageEnds = 0;
        if (success) RewardEvent(value);
        EconomicDirty = true;
    }

    private void RewardEvent(WorldEvent value)
    {
        double top = value.Contributions.Values.DefaultIfEmpty(0).Max(); if (top <= 0) return;
        var zone = Data.Zone(value.Zone);
        foreach (var pair in value.Contributions.Where(x => x.Value >= 1).OrderByDescending(x => x.Value))
        {
            if (!State.Characters.TryGetValue(pair.Key, out var player) || !value.Rewarded.Add(pair.Key)) continue;
            double share = pair.Value / top; int tier = share >= .65 ? 3 : share >= .35 ? 2 : 1;
            long gold = 40 + zone.Level * (3 + tier) + tier * 30; Items.Grant(player, gold);
            Progression.Train(player, "exploration", 30 * tier, Math.Clamp(zone.Level, 1, 100), Data);
            Progression.Train(player, "survival", 20 * tier, Math.Clamp(zone.Level, 1, 100), Data);
            player.Reputation["wayfarers"] = Math.Min(1000, player.Reputation.GetValueOrDefault("wayfarers") + 2 * tier);
            player.PublicEventsCompleted++;
            if (player.PublicEventsCompleted >= 1) player.Achievements.Add("public_event_responder");
            if (player.PublicEventsCompleted >= 10) player.Achievements.Add("public_event_veteran");
            if (player.PublicEventsCompleted >= 25) player.Achievements.Add("public_event_guardian");
            string reward = WorldEventRules.NormalizeKind(value.Kind) switch
            {
                "meteor" => "storm_crystal",
                "arcane_rift" => "rough_gem",
                "treasure_surge" or "world_boss" => "relic_shard",
                _ => "healing_potion"
            };
            TryGrantEventItem(player, reward, tier >= 3 ? 2 : 1);
        }
    }

    private void TryGrantEventItem(Character player, string template, int quantity)
    {
        if (!Data.Items.Any(x => x.Id == template)) return;
        try { Items.Add(player.Inventory, Items.Create(Data, template, quantity), Data); return; }
        catch (RuleException) { }
        try { Items.Add(player.Bank, Items.Create(Data, template, quantity), Data, Items.BankCapacity); }
        catch (RuleException) { }
    }
}
'''

LIFECYCLE = r'''namespace Kairnfall.Core;

/// <summary>Exact event-owned cleanup plus expiry for staged events and historical saves.</summary>
public static class WorldEventLifecycle
{
    public static int CleanupOwned(RealmState state, string id)
    {
        bool Owned(string candidate) => candidate == id || candidate.StartsWith(id + "/", StringComparison.Ordinal);
        int removed = 0;
        foreach (var key in state.Nodes.Keys.Where(Owned).ToArray()) { state.Nodes.Remove(key); removed++; }
        foreach (var key in state.Chests.Keys.Where(Owned).ToArray()) { state.Chests.Remove(key); removed++; }
        foreach (var key in state.Creatures.Keys.Where(Owned).ToArray()) { state.Creatures.Remove(key); removed++; }
        removed += state.Telegraphs.RemoveAll(value => Owned(value.Source));
        return removed;
    }

    public static int Expire(RealmState state, double now)
    {
        if (!double.IsFinite(now)) throw new ArgumentOutOfRangeException(nameof(now));
        var expired = state.Events.Where(value => value.Ends <= now
                && (value.Status != "active" || value.StageEnds <= 0))
            .Select(value => value.Id).ToArray();
        foreach (var id in expired) CleanupOwned(state, id);
        state.Events.RemoveAll(value => expired.Contains(value.Id, StringComparer.Ordinal));
        return expired.Length;
    }
}
'''

CHECKS = r'''using Kairnfall.Core;

internal static class LivingWorldEventChecks
{
    public static void Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Need(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        void Test(string name, Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS LIVING WORLD: " + name); }
            catch (Exception error) { failures.Add("Living world: " + name); Console.WriteLine("FAIL LIVING WORLD: " + name + ": " + error.Message); }
        }
        RealmEngine Realm(double time = 20) => new(data, new RealmState { Time = time });
        Character Hero(RealmEngine realm, string suffix = "A")
        {
            var player = realm.CreateCharacter("living-world-" + suffix, "Event Hero " + suffix, "vanguard", new());
            realm.Active.Add(player.Id); return player;
        }
        ZoneDef ZoneFor(string kind) => data.Zones.First(x => WorldEventRules.EligibleZone(kind, x));
        CommandResult Act(RealmEngine realm, Character player, string kind, string target = "")
            => realm.Execute(player.Id, new GameCommand { Kind = kind, Target = target, Sequence = player.LastAction + 1 });

        Test("eight event families expose staged objectives and eligible regions", () =>
        {
            Need(WorldEventRules.Kinds.Length == 8 && WorldEventRules.Kinds.Distinct(StringComparer.Ordinal).Count() == 8, "Public-event taxonomy is incomplete.");
            foreach (string kind in WorldEventRules.Kinds)
            {
                Need(data.Zones.Any(x => WorldEventRules.EligibleZone(kind, x)), kind + " has no eligible region.");
                Need(WorldEventRules.Name(kind) != "Public Event", kind + " has no identity.");
                Need(WorldEventRules.StageCount(kind) is >= 1 and <= 2, kind + " has an invalid stage count.");
                Need(!string.IsNullOrWhiteSpace(WorldEventRules.StageLabel(kind, 0)), kind + " has no stage objective.");
                Need(!string.IsNullOrWhiteSpace(WorldEventRules.EffectLabel(WorldEventRules.SuccessEffect(kind))), kind + " has no aftermath.");
            }
        });

        Test("rift interaction chains into a champion and resolves with exact cleanup", () =>
        {
            var realm = Realm(); var player = Hero(realm); var zone = ZoneFor("arcane_rift"); player.Zone = zone.Id; player.Position = zone.Spawn;
            var value = new WorldEvent { Id = "event/check-rift", Kind = "arcane_rift", Name = WorldEventRules.Name("arcane_rift"), Zone = zone.Id, Position = player.Position, Status = "active", Stage = 0, Goal = 2, Difficulty = 1, Started = realm.State.Time, StageStarted = realm.State.Time, StageEnds = realm.State.Time + 100, Ends = realm.State.Time + 100 };
            realm.State.Events.Add(value);
            Need(Act(realm, player, "event", value.Id).Ok, "First rift stabilization failed."); realm.State.Time += 3;
            Need(Act(realm, player, "event", value.Id).Ok, "Second rift stabilization failed.");
            realm.Tick(.1);
            value = realm.State.Events.Single(x => x.Id == value.Id);
            Need(value.Stage == 1 && value.Status == "active", "Rift did not advance to its champion stage.");
            var champion = realm.State.Creatures.Values.Single(x => WorldEventRules.Owns(value, x.Id)); champion.Health = .1; player.Position = champion.Position; player.Stamina = 100;
            Need(Act(realm, player, "attack", champion.Id).Ok, "Champion attack failed."); realm.Tick(.1);
            value = realm.State.Events.Single(x => x.Id == value.Id);
            Need(value.Status == "success" && value.Effect == "arcane_clarity", "Rift did not resolve into its regional aftermath.");
            Need(!realm.State.Creatures.Keys.Any(x => WorldEventRules.Owns(value, x)), "Event-owned champion survived stage cleanup.");
        });

        Test("timeouts fail into unrest and event-owned objects are removed", () =>
        {
            var realm = Realm(); var zone = ZoneFor("meteor");
            var value = new WorldEvent { Id = "event/check-timeout", Kind = "meteor", Name = "Timeout", Zone = zone.Id, Position = zone.Spawn, Status = "active", Goal = 4, StageEnds = realm.State.Time + .05, Ends = realm.State.Time + .05 };
            realm.State.Events.Add(value); realm.State.Nodes[value.Id + "/node/0"] = new() { Id = value.Id + "/node/0", Template = "meteor_ore", Zone = zone.Id, Position = zone.Spawn };
            realm.Tick(.1); value = realm.State.Events.Single(x => x.Id == value.Id);
            Need(value.Status == "failure" && value.Effect == "regional_unrest" && value.EffectEnds > realm.State.Time, "Timeout did not produce regional unrest.");
            Need(!realm.State.Nodes.Keys.Any(x => WorldEventRules.Owns(value, x)), "Timed-out event object was not cleaned.");
        });

        Test("contribution tiers reward once and survive save roundtrip", () =>
        {
            var realm = Realm(); var a = Hero(realm, "RewardA"); var b = Hero(realm, "RewardB"); var zone = ZoneFor("world_boss");
            a.Zone = b.Zone = zone.Id; a.Position = b.Position = zone.Spawn;
            var value = new WorldEvent { Id = "event/check-reward", Kind = "world_boss", Name = "Reward", Zone = zone.Id, Position = zone.Spawn, Status = "active", Goal = 1, StageEnds = realm.State.Time + 100, Ends = realm.State.Time + 100, Contributions = new() { [a.Id] = 100, [b.Id] = 40 } };
            realm.State.Events.Add(value); var def = data.Mob("field_rat"); string mobId = value.Id + "/mob/0/0";
            realm.State.Creatures[mobId] = new() { Id = mobId, Template = def.Id, Zone = zone.Id, Position = zone.Spawn, Home = zone.Spawn, Health = .1 };
            long goldA = a.Gold, goldB = b.Gold; a.Stamina = 100;
            Need(Act(realm, a, "attack", mobId).Ok, "Event boss fixture could not be defeated."); realm.Tick(.1);
            value = realm.State.Events.Single(x => x.Id == value.Id);
            Need(value.Status == "success" && a.PublicEventsCompleted == 1 && b.PublicEventsCompleted == 1, "Meaningful contributors were not rewarded.");
            Need(a.Gold - goldA > b.Gold - goldB, "Contribution tiers did not differentiate rewards.");
            long after = a.Gold; realm.Tick(.1); Need(a.Gold == after && value.Rewarded.Count == 2, "Event rewards were granted twice.");
            var copy = Wire.Copy(realm.State); var saved = copy.Events.Single(x => x.Id == value.Id);
            Need(saved.Rewarded.SetEquals(value.Rewarded) && saved.Contributions.Count == 2 && copy.Characters[a.Id].PublicEventsCompleted == 1, "Event/reward state did not survive serialization.");
        });

        Test("participant scaling and caravan escort react to nearby players", () =>
        {
            Need(WorldEventRules.ScaledGoal("undead", 0, 4) > WorldEventRules.ScaledGoal("undead", 0, 1), "Combat events do not scale with participants.");
            var realm = Realm(); var a = Hero(realm, "EscortA"); var b = Hero(realm, "EscortB"); var c = Hero(realm, "EscortC"); var zone = ZoneFor("caravan");
            foreach (var p in new[] { a, b, c }) { p.Zone = zone.Id; p.Position = zone.Spawn; }
            var destination = WorldMap.FindFree(zone, new(zone.Spawn.X + 10, zone.Spawn.Y));
            var value = new WorldEvent { Id = "event/check-caravan", Kind = "caravan", Name = "Escort", Zone = zone.Id, Position = zone.Spawn, Destination = destination, Status = "active", Goal = WorldEventRules.BaseGoal("caravan", 0), Difficulty = 1, StageEnds = realm.State.Time + 200, Ends = realm.State.Time + 200 };
            realm.State.Events.Add(value); var before = value.Position; realm.Tick(.1);
            Need(value.Difficulty == 3 && value.Goal == WorldEventRules.ScaledGoal("caravan", 0, 3), "Nearby players did not scale the escort.");
            Need(value.Progress > 0 && value.Position.Distance(before) > 0 && value.Contributions.Count == 3, "Caravan did not move or credit its escort group.");
        });

        Test("aftermath modifiers are real gameplay hooks rather than UI-only text", () =>
        {
            var state = new RealmState { Time = 50 }; string zone = ZoneFor("caravan").Id;
            state.Events.Add(new() { Id = "event/effect", Kind = "caravan", Zone = zone, Status = "success", Effect = "safe_roads", EffectEnds = 200, Ends = 200 });
            Need(WorldEventRules.MovementMultiplier(state, zone, 50) > 1 && WorldEventRules.StaminaRegenBonus(state, zone, 50) > 0, "Safe-road aftermath has no gameplay effect.");
            state.Events[0].Effect = "regional_unrest";
            Need(WorldEventRules.MovementMultiplier(state, zone, 50) < 1 && WorldEventRules.EnemyPowerMultiplier(state, zone, 50) > 1, "Failure aftermath has no pressure tradeoff.");
            string engine = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), "src/Kairnfall.Core/RealmEngine.cs"));
            string economy = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), "src/Kairnfall.Core/RealmEconomy.cs"));
            string combat = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), "src/Kairnfall.Core/RealmCombat.cs"));
            Need(engine.Contains("WorldEventRules.MovementMultiplier", StringComparison.Ordinal) && engine.Contains("WorldEventRules.HealthRegenBonus", StringComparison.Ordinal), "Movement/regeneration are not wired to aftermath.");
            Need(economy.Contains("WorldEventRules.GatherYieldBonus", StringComparison.Ordinal) && economy.Contains("WorldEventRules.TreasureGoldMultiplier", StringComparison.Ordinal), "Gathering/treasure are not wired to aftermath.");
            Need(combat.Contains("WorldEventRules.EnemyPowerMultiplier", StringComparison.Ordinal), "Enemy pressure is not wired to failed events.");
        });

        Test("legacy events upgrade safely and clients expose the living world globally", () =>
        {
            var zone = ZoneFor("arcane_rift"); var state = new RealmState { Time = 40 };
            state.Events.Add(new() { Id = "event/legacy", Kind = "arcane_storm", Name = "Old storm", Zone = zone.Id, Position = zone.Spawn, Ends = 140 });
            state.Nodes["event/legacy/old"] = new() { Id = "event/legacy/old", Template = "meteor_ore", Zone = zone.Id, Position = zone.Spawn };
            var realm = new RealmEngine(data, state); realm.Tick(.1); var upgraded = realm.State.Events.Single(x => x.Id == "event/legacy");
            Need(upgraded.Kind == "arcane_rift" && upgraded.StageEnds > realm.State.Time && !realm.State.Nodes.ContainsKey("event/legacy/old"), "Historical arcane-storm event did not upgrade safely.");
            var player = Hero(realm, "Snapshot"); var otherZone = data.Zones.First(x => x.Id != player.Zone && x.Layer == "Surface");
            realm.State.Events.Add(new() { Id = "event/remote", Kind = "meteor", Name = "Remote", Zone = otherZone.Id, Position = otherZone.Spawn, Status = "active", Goal = 1, StageEnds = 100, Ends = 100 });
            Need(realm.Snapshot(player.Id).Events.Any(x => x.Id == "event/remote"), "Snapshot hides remote public events from the atlas.");
            string root = Directory.GetCurrentDirectory();
            string experience = File.ReadAllText(Path.Combine(root, "client/Scripts/GameRoot.Experience.cs"));
            string world = File.ReadAllText(Path.Combine(root, "client/Scripts/WorldView.cs"));
            string maps = File.ReadAllText(Path.Combine(root, "client/Scripts/Maps.cs"));
            string hunting = File.ReadAllText(Path.Combine(root, "client/Scripts/HuntingGuidePanel.cs"));
            Need(experience.Contains("PublicEventHud", StringComparison.Ordinal), "Combat HUD has no public-event state.");
            Need(world.Contains("\"event\"", StringComparison.Ordinal) && world.Contains("StageLabel", StringComparison.Ordinal), "World view has no event marker/identity.");
            Need(maps.Contains("Snapshot.Events", StringComparison.Ordinal) && maps.Contains("Events = () => Snapshot?.Events", StringComparison.Ordinal), "Minimap/atlas do not expose public events.");
            Need(hunting.Contains("ReadEvents", StringComparison.Ordinal) && hunting.Contains("PUBLIC EVENT", StringComparison.Ordinal), "Hunting Guide does not prioritize live events.");
        });

        Console.WriteLine($"LIVING WORLD EVENTS: {passed} groups passed; total failures {failures.Count}.");
    }
}
'''

DOC = r'''# Living world and public-event ecosystem

Kairnfall's public events are server-authoritative regional incidents layered onto the existing connected world. They are not separate instances and they reuse ordinary combat, gathering, treasure, movement, skill progression, party presence, and save persistence.

## Event families

Eight deterministic event families rotate through eligible regions:

- **Starfall Harvest** — gather fallen star fragments, then defeat a Starborn champion.
- **Wayfarer Caravan** — stay near the caravan to escort it, survive route ambushes, then break the final attack.
- **Restless Graves** — clear a graveborn wave, then destroy the Grave Herald.
- **Arcane Rift** — actively stabilize the rift, then defeat the Rift Sentinel.
- **Settlement Under Siege** — repel attackers and then their commander.
- **Wild Migration** — drive back a dangerous migration and its apex beast.
- **Treasure Surge** — recover temporary regional caches before the surge collapses.
- **Regional Terror** — a focused public world-boss encounter in higher-level wilderness.

Up to three active events can coexist. Placement respects region type and progression: settlement sieges use real settlements, higher-risk rifts and world bosses use later wilderness, and starter Wayfarer's Rest is never selected for a siege.

## Scaling, contribution, and rewards

Stage-zero objectives scale upward when multiple active players arrive together, up to a bounded six-player contribution target. Combat damage, event kills, event gathering, cache recovery, rift stabilization, and caravan escort presence are tracked server-side. Rewards are granted once to meaningful contributors and scale by contribution tier rather than last-hit ownership.

Successful contributors receive gold, Exploration and Survival training, Wayfarers reputation, and an existing themed material or consumable where available. Public-event milestones are recorded at the first completion and at 10 and 25 completions. Event reward state is serialized with the realm so reconnects or saves cannot duplicate payouts.

## Success, failure, and regional aftermath

An event that completes all of its stages leaves a temporary positive regional consequence. An event that misses its deadline leaves **Regional Unrest**. These effects alter real server rules rather than only changing UI text:

- Starfall/Wild Bounty improves gathering yield.
- Safe Roads improves movement and stamina recovery.
- Hallowed Ground improves health recovery.
- Arcane Clarity improves mana recovery.
- Settlement/Heroic Morale improves recovery.
- Fortune increases chest gold.
- Regional Unrest slows movement slightly and increases hostile attack pressure.

Aftermath expires automatically and event-owned mobs, nodes, chests, and telegraphs are cleaned by exact event ownership.

## Player presentation

The combat HUD displays the current local event, stage, progress, remaining time, and personal contribution. Event markers appear directly in the world and on the minimap. The world atlas receives all current public-event summaries so distant events can be discovered without exposing private player information. The regional Hunting Guide prioritizes an active local event over ordinary hunting suggestions.

Only Arcane Rift and caravan support stages use the context interaction key. Combat, gathering, treasure, escort proximity, and other objectives continue through their normal gameplay inputs.

## Compatibility and validation

Historical `arcane_storm` events are upgraded to the staged `arcane_rift` family when a saved realm is loaded. All new event fields have safe defaults for older saves. `LivingWorldEventChecks` permanently covers the eight event families, stage chaining, timeouts, exact cleanup, contribution rewards, persistence, scaling, caravan escort behavior, gameplay aftermath hooks, legacy upgrades, global snapshots, and client visibility contracts.

Subjective event cadence, reward excitement, and large-group social feel still require human multiplayer playtesting; automated checks validate rules and integration rather than claiming those judgments.
'''

write("src/Kairnfall.Core/WorldEventRules.cs", WORLD_EVENT_RULES)
write("src/Kairnfall.Core/RealmEvents.cs", REALM_EVENTS)
write("src/Kairnfall.Core/WorldEventLifecycle.cs", LIFECYCLE)
write("tools/world_probe/LivingWorldEventChecks.cs", CHECKS)
write("docs/LIVING_WORLD_EVENTS.md", DOC)

# Save-compatible model extensions.
replace_once("src/Kairnfall.Core/Models.cs",
'''    public int Deaths { get; set; }\n    public double LastCombat { get; set; } = -100;''',
'''    public int Deaths { get; set; }\n    public int PublicEventsCompleted { get; set; }\n    public double LastCombat { get; set; } = -100;''')
replace_once("src/Kairnfall.Core/Models.cs",
'''public sealed class WorldEvent\n{\n    public string Id { get; set; } = "";\n    public string Name { get; set; } = "";\n    public string Zone { get; set; } = "";\n    public Point Position { get; set; }\n    public double Ends { get; set; }\n    public string Kind { get; set; } = "";\n}''',
'''public sealed class WorldEvent\n{\n    public string Id { get; set; } = "";\n    public string Name { get; set; } = "";\n    public string Zone { get; set; } = "";\n    public Point Position { get; set; }\n    public double Ends { get; set; }\n    public string Kind { get; set; } = "";\n    public string Status { get; set; } = "active";\n    public int Stage { get; set; }\n    public double Started { get; set; }\n    public double StageStarted { get; set; }\n    public double StageEnds { get; set; }\n    public double Progress { get; set; }\n    public double Goal { get; set; }\n    public Point Destination { get; set; }\n    public string Effect { get; set; } = "";\n    public double EffectEnds { get; set; }\n    public int Wave { get; set; }\n    public int Difficulty { get; set; } = 1;\n    public double LastTick { get; set; }\n    public Dictionary<string,double> Contributions { get; set; } = [];\n    public HashSet<string> Rewarded { get; set; } = [];\n}''')

# Realm integration: scheduler cadence, interaction command, global snapshot, and real aftermath rules.
replace_once("src/Kairnfall.Core/RealmEngine.cs", 'if(state is not null) lastEventCycle=(long)(State.Time/300);', 'if(state is not null) lastEventCycle=(long)(State.Time/WorldEventRules.SpawnCadence);')
replace_once("src/Kairnfall.Core/RealmEngine.cs", '            case "chest": return OpenChest(p,c.Target);\n', '            case "chest": return OpenChest(p,c.Target);\n            case "event": return EventAction(p,c.Target);\n')
replace_once("src/Kairnfall.Core/RealmEngine.cs",
'                    p.Position=WorldMap.Move(zone,p.Position,direction.Scale(stats.MoveSpeed*slow*dt)); p.Facing=direction;',
'                    double eventMove=WorldEventRules.MovementMultiplier(State,p.Zone,State.Time);\n                    p.Position=WorldMap.Move(zone,p.Position,direction.Scale(stats.MoveSpeed*slow*eventMove*dt)); p.Facing=direction;')
replace_once("src/Kairnfall.Core/RealmEngine.cs",
'            p.Stamina=Math.Min(stats.Stamina,p.Stamina+dt*(8+Progression.Level(p,"endurance")*0.08));\n            double manaRegen=2+Progression.Level(p,"meditation")*0.04;',
'            p.Stamina=Math.Min(stats.Stamina,p.Stamina+dt*(8+Progression.Level(p,"endurance")*0.08+WorldEventRules.StaminaRegenBonus(State,p.Zone,State.Time)));\n            double manaRegen=2+Progression.Level(p,"meditation")*0.04+WorldEventRules.ManaRegenBonus(State,p.Zone,State.Time);')
replace_once("src/Kairnfall.Core/RealmEngine.cs",
'            if(State.Time-p.LastCombat>8) p.Health=Math.Min(stats.Health,p.Health+dt*(1.5+stats.Bonus("health_regen")));',
'            if(State.Time-p.LastCombat>8) p.Health=Math.Min(stats.Health,p.Health+dt*(1.5+stats.Bonus("health_regen")+WorldEventRules.HealthRegenBonus(State,p.Zone,State.Time)));')
replace_once("src/Kairnfall.Core/RealmEngine.cs",
'        snap.Events=State.Events.Where(x=>x.Zone==p.Zone).Select(Wire.Copy).ToList();',
'        snap.Events=State.Events.Select(Wire.Copy).ToList();')

# Combat participation, event mob no-respawn, failure pressure, and move TickEvents into RealmEvents.
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'        damage=Math.Min(mob.Health,Math.Max(0,damage)); mob.Health-=damage;\n        mob.Threat[p.Id]=mob.Threat.GetValueOrDefault(p.Id)+damage*(p.Class=="vanguard"?1.4:1);',
'        damage=Math.Min(mob.Health,Math.Max(0,damage)); mob.Health-=damage;\n        RecordEventDamage(p,mob,damage);\n        mob.Threat[p.Id]=mob.Threat.GetValueOrDefault(p.Id)+damage*(p.Class=="vanguard"?1.4:1);')
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'        var def=Data.Mob(mob.Template); mob.Health=0; mob.RespawnAt=State.Time+(def.Boss?300:def.Elite?90:25); mob.Generation++;',
'        var def=Data.Mob(mob.Template); var publicEvent=WorldEventRules.Owner(State,mob.Id); mob.Health=0; mob.RespawnAt=publicEvent is null?State.Time+(def.Boss?300:def.Elite?90:25):double.MaxValue; mob.Generation++;')
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'        if(contributors.Count==0) contributors.Add(killer);\n        foreach(var p in contributors)',
'        if(contributors.Count==0) contributors.Add(killer);\n        RecordEventKill(mob,contributors);\n        foreach(var p in contributors)')
replace_once("src/Kairnfall.Core/RealmCombat.cs",
'        double power=definition.Power*EnemyCombatRules.PowerMultiplier(definition,mob);',
'        double power=definition.Power*EnemyCombatRules.PowerMultiplier(definition,mob)*WorldEventRules.EnemyPowerMultiplier(State,mob.Zone,State.Time);')
regex_once("src/Kairnfall.Core/RealmCombat.cs", r'\n    private void TickEvents\(\)\n    \{.*?\n    \}\n\}', '\n}')

# Gathering and treasure become event objectives and consume aftermath modifiers.
replace_once("src/Kairnfall.Core/RealmEconomy.cs",
'        double yield=CombatMath.Stats(p,Data).Bonus("gather_yield")+ToolRules.Yield(tool);',
'        double yield=CombatMath.Stats(p,Data).Bonus("gather_yield")+ToolRules.Yield(tool)+WorldEventRules.GatherYieldBonus(State,p.Zone,State.Time);')
replace_once("src/Kairnfall.Core/RealmEconomy.cs",
'        if(crop) State.Nodes.Remove(node.Id); else node.ReadyAt=State.Time+def.Respawn;',
'        bool publicEventNode=RecordEventGather(p,node.Id);\n        if(publicEventNode||crop) State.Nodes.Remove(node.Id); else node.ReadyAt=State.Time+def.Respawn;')
replace_once("src/Kairnfall.Core/RealmEconomy.cs",
'        Items.Grant(p,10+chest.Requirement*3); chest.ReadyAt=State.Time+600;\n        Progression.Train(p,"treasure_hunting",80,chest.Requirement,Data); Progress(p,"chest",chest.Kind);',
'        long chestGold=(long)Math.Ceiling((10+chest.Requirement*3)*WorldEventRules.TreasureGoldMultiplier(State,p.Zone,State.Time));\n        Items.Grant(p,chestGold); bool publicEventChest=RecordEventChest(p,chest.Id);\n        if(publicEventChest) State.Chests.Remove(chest.Id); else chest.ReadyAt=State.Time+600;\n        Progression.Train(p,"treasure_hunting",80,chest.Requirement,Data); Progress(p,"chest",chest.Kind);')

# Client interaction contract.
replace_once("client/Scripts/ExperienceRules.cs",
'        => targets.Where(x => x.Kind is "npc" or "exit" or "node" or "chest" or "loot" or "landmark")',
'        => targets.Where(x => x.Kind is "npc" or "exit" or "node" or "chest" or "loot" or "landmark" or "event")')
replace_once("client/Scripts/ExperienceRules.cs",
'        "chest" => "Open", "loot" => "Pick up", "landmark" => "Survey", _ => "Use"',
'        "chest" => "Open", "loot" => "Pick up", "landmark" => "Survey", "event" => "Contribute to", _ => "Use"')
replace_once("client/Scripts/GameRoot.cs",
'        else if (target.Kind == "landmark") Send("inspect", target.Id);\n        else if (target.Kind == "chest") Send("chest", target.Id);',
'        else if (target.Kind == "landmark") Send("inspect", target.Id);\n        else if (target.Kind == "event") Send("event", target.Id);\n        else if (target.Kind == "chest") Send("chest", target.Id);')
replace_once("client/Scripts/GameRoot.cs",
'            Snapshot.Trades, Snapshot.Auctions, Snapshot.Party, Snapshot.Guild, Snapshot.ShopStock, invitations',
'            Snapshot.Trades, Snapshot.Auctions, Snapshot.Party, Snapshot.Guild, Snapshot.ShopStock, Snapshot.Events, invitations')

# Event markers in the actual world.
replace_once("client/Scripts/WorldView.cs",
'        if (Snapshot is { } snapshot)\n        {\n            foreach (var node in snapshot.Nodes)',
'''        if (Snapshot is { } snapshot)\n        {\n            foreach (var worldEvent in snapshot.Events.Where(x => x.Zone == zone.Id && IsWithinCameraBounds(x.Position, 8)))\n            {\n                visuals.Add(new Visual((float)worldEvent.Position.Y + .03f, "event", worldEvent.Id, worldEvent.Position, worldEvent));\n                if (WorldEventRules.SupportsInteraction(worldEvent)) interactions.Add(new WorldTarget("event", worldEvent.Id, worldEvent.Name, worldEvent.Position));\n            }\n            foreach (var node in snapshot.Nodes)''')
replace_once("client/Scripts/WorldView.cs",
'        switch (visual.Kind)\n        {\n            case "exit":',
'''        switch (visual.Kind)\n        {\n            case "event":\n                var worldEvent = (WorldEvent)visual.Value!;\n                Color eventColor = worldEvent.Status == "success" ? Ui.Success : worldEvent.Status == "failure" ? Ui.Danger : new Color("e0b868");\n                float pulse = 10 + 2 * (1 + MathF.Sin((float)Clock * 3));\n                DrawCircle(feet, pulse, new Color(eventColor, .10f));\n                DrawArc(feet, pulse, 0, MathF.Tau, 28, eventColor, 2);\n                DrawColoredPolygon([feet + new Vector2(0,-7), feet + new Vector2(7,0), feet + new Vector2(0,7), feet + new Vector2(-7,0)], new Color(eventColor,.55f));\n                if (worldEvent.Position.Distance(Camera) < 12)\n                    Nameplate(worldEvent.Position, worldEvent.Name + " · " + WorldEventRules.StageLabel(worldEvent), eventColor, -53, 10);\n                break;\n            case "exit":''')

# Public-event HUD, context verb, and transition notifications.
replace_once("client/Scripts/GameRoot.Experience.cs",
'    private Label classResourceText = null!;',
'    private Label classResourceText = null!, publicEventText = null!;')
replace_once("client/Scripts/GameRoot.Experience.cs",
'        if (target.Kind != "node") return ExperienceRules.InteractionVerb(target.Kind);',
'        if (target.Kind == "event" && Snapshot?.Events.FirstOrDefault(x => x.Id == target.Id) is { } worldEvent) return WorldEventRules.InteractionVerb(worldEvent);\n        if (target.Kind != "node") return ExperienceRules.InteractionVerb(target.Kind);')
replace_once("client/Scripts/GameRoot.Experience.cs",
'        classMeter.AddChild(classResourceText); classMeter.AddChild(classResourceBar); hud.AddChild(classMeter);\n        notice.OffsetTop = -252;',
'''        classMeter.AddChild(classResourceText); classMeter.AddChild(classResourceBar); hud.AddChild(classMeter);\n        publicEventText = Ui.Label("", 13, Ui.Gold, true);\n        publicEventText.Name = "PublicEventHud"; publicEventText.AnchorLeft = publicEventText.AnchorRight = .5f;\n        publicEventText.AnchorTop = publicEventText.AnchorBottom = 0; publicEventText.OffsetLeft = -310; publicEventText.OffsetRight = 310;\n        publicEventText.OffsetTop = 18; publicEventText.OffsetBottom = 78; publicEventText.HorizontalAlignment = HorizontalAlignment.Center;\n        publicEventText.MouseFilter = MouseFilterEnum.Ignore; publicEventText.AddThemeConstantOverride("outline_size", 4);\n        publicEventText.AddThemeColorOverride("font_outline_color", Ui.Ink); hud.AddChild(publicEventText);\n        notice.OffsetTop = -252;''')
replace_once("client/Scripts/GameRoot.Experience.cs",
'        UpdateMobControls(); UpdateClassResourceHud();',
'        UpdateMobControls(); UpdateClassResourceHud(); UpdatePublicEventHud();')
replace_once("client/Scripts/GameRoot.Experience.cs",
'    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)\n    {',
'''    private void UpdatePublicEventHud()\n    {\n        if (Snapshot is not { } snapshot || publicEventText is null) return;\n        var value = snapshot.Events.Where(x => x.Zone == snapshot.Self.Zone)\n            .OrderBy(x => x.Status == "active" ? 0 : 1).ThenByDescending(x => x.EffectEnds).FirstOrDefault();\n        if (value is null) { publicEventText.Text = ""; return; }\n        if (value.Status == "active")\n        {\n            int stage = Math.Min(WorldEventRules.StageCount(value.Kind), value.Stage + 1);\n            int remaining = Math.Max(0, (int)Math.Ceiling(value.StageEnds - snapshot.Time));\n            publicEventText.Text = $"PUBLIC EVENT · {value.Name}\\nStage {stage}/{WorldEventRules.StageCount(value.Kind)} · {WorldEventRules.StageLabel(value)} · {WorldEventRules.ProgressText(value)} · {remaining}s · You {WorldEventRules.Contribution(value,snapshot.Self.Id):0}";\n        }\n        else\n        {\n            int remaining = Math.Max(0, (int)Math.Ceiling(value.EffectEnds - snapshot.Time));\n            publicEventText.Text = $"REGIONAL AFTERMATH · {(value.Status == "success" ? "SUCCESS" : "FAILED")} · {WorldEventRules.EffectLabel(value.Effect)} · {remaining}s";\n        }\n    }\n\n    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)\n    {''')
replace_once("client/Scripts/GameRoot.Experience.cs",
'        if (previous.Self.Zone != current.Self.Zone)\n        {',
'''        foreach (var value in current.Events)\n        {\n            var beforeEvent = previous.Events.FirstOrDefault(x => x.Id == value.Id);\n            if (beforeEvent is null && value.Status == "active")\n            {\n                Notify("WORLD EVENT · " + value.Name + " · " + Data.Zone(value.Zone).Name); audio?.PlayEffect("ui");\n                if (value.Zone == current.Self.Zone) World.ClassBurst(value.Position, new Color("e0b868"));\n            }\n            else if (beforeEvent is not null && beforeEvent.Status != value.Status)\n            {\n                Notify(value.Status == "success" ? "EVENT COMPLETE · " + value.Name : "EVENT FAILED · " + value.Name, value.Status == "failure");\n                if (value.Zone == current.Self.Zone) World.ClassBurst(value.Position, value.Status == "success" ? Ui.Success : Ui.Danger);\n            }\n            else if (beforeEvent is not null && beforeEvent.Stage != value.Stage && value.Status == "active" && value.Zone == current.Self.Zone)\n                Notify("EVENT ADVANCED · " + WorldEventRules.StageLabel(value));\n        }\n        if (previous.Self.Zone != current.Self.Zone)\n        {''')

# Minimap and atlas global awareness.
replace_once("client/Scripts/Maps.cs",
'            foreach (var player in snapshot.Players) Dot(player.Position, center, scale, new Color("94bddd"));',
'            foreach (var worldEvent in snapshot.Events.Where(x => x.Zone == zone.Id)) Dot(worldEvent.Position, center, scale, worldEvent.Status == "failure" ? Ui.Danger : new Color("e0b868"));\n            foreach (var player in snapshot.Players) Dot(player.Position, center, scale, new Color("94bddd"));')
replace_once("client/Scripts/Maps.cs",
'    public Func<Character?> Player { get; set; } = () => null;\n    public string Layer { get; set; } = "Surface";',
'    public Func<Character?> Player { get; set; } = () => null;\n    public Func<IEnumerable<WorldEvent>> Events { get; set; } = () => [];\n    public string Layer { get; set; } = "Surface";')
replace_once("client/Scripts/Maps.cs",
'        var player = Player();\n        var zones = Data.Zones.Where',
'        var player = Player(); var publicEvents = Events().ToArray();\n        var zones = Data.Zones.Where')
replace_once("client/Scripts/Maps.cs",
'            if (zone.Id == player?.Zone) DrawArc(at, 13, 0, MathF.Tau, 24, new Color("a9cde2"), 2);',
'            if (zone.Id == player?.Zone) DrawArc(at, 13, 0, MathF.Tau, 24, new Color("a9cde2"), 2);\n            if (publicEvents.Any(x => x.Zone == zone.Id && x.Status == "active")) DrawArc(at, 17, 0, MathF.Tau, 28, new Color("e0b868"), 2);')
replace_once("client/Scripts/Maps.cs",
'        var atlas = new AtlasView { Data = Data, Player = () => Snapshot?.Self, Layer = layers[layer.Selected], Selected = selectedZone, CustomMinimumSize = new Vector2(0, 370), SizeFlagsHorizontal = SizeFlags.ExpandFill, SizeFlagsVertical = SizeFlags.ExpandFill };',
'        var atlas = new AtlasView { Data = Data, Player = () => Snapshot?.Self, Events = () => Snapshot?.Events ?? [], Layer = layers[layer.Selected], Selected = selectedZone, CustomMinimumSize = new Vector2(0, 370), SizeFlagsHorizontal = SizeFlags.ExpandFill, SizeFlagsVertical = SizeFlags.ExpandFill };')
replace_once("client/Scripts/Maps.cs",
'            if(locked)detail.AddChild(Ui.Label($"LOCKED · Reach character level {entryLevel} ({entryLevel-playerLevel} to go).",13,Ui.Danger,true));',
'''            foreach(var worldEvent in Snapshot.Events.Where(x=>x.Zone==zone.Id))\n            {\n                Color eventColor=worldEvent.Status=="success"?Ui.Success:worldEvent.Status=="failure"?Ui.Danger:new Color("e0b868");\n                string eventText=worldEvent.Status=="active"\n                    ? $"PUBLIC EVENT · {worldEvent.Name}\\n{WorldEventRules.StageLabel(worldEvent)} · {WorldEventRules.ProgressText(worldEvent)}"\n                    : $"AFTERMATH · {WorldEventRules.EffectLabel(worldEvent.Effect)}";\n                detail.AddChild(Ui.Label(eventText,13,eventColor,true));\n            }\n            if(locked)detail.AddChild(Ui.Label($"LOCKED · Reach character level {entryLevel} ({entryLevel-playerLevel} to go).",13,Ui.Danger,true));''')

# Hunting Guide prioritizes local public incidents and paints them on its regional map.
replace_once("client/Scripts/HuntingGuidePanel.cs",
'    public Func<Character?> ReadCharacter { get; set; }=()=>null!;\n    public Func<double> ReadTime { get; set; }=()=>0;',
'    public Func<Character?> ReadCharacter { get; set; }=()=>null!;\n    public Func<IEnumerable<WorldEvent>> ReadEvents { get; set; }=()=>[];\n    public Func<double> ReadTime { get; set; }=()=>0;')
# The exact source uses ()=>null, not null!; handle current spelling.
text = read("client/Scripts/HuntingGuidePanel.cs")
if 'public Func<IEnumerable<WorldEvent>> ReadEvents' not in text:
    old='    public Func<Character?> ReadCharacter { get; set; }=()=>null;\n    public Func<double> ReadTime { get; set; }=()=>0;'
    if old not in text: raise SystemExit('HuntingGuide ReadCharacter block not found')
    write("client/Scripts/HuntingGuidePanel.cs", text.replace(old, '    public Func<Character?> ReadCharacter { get; set; }=()=>null;\n    public Func<IEnumerable<WorldEvent>> ReadEvents { get; set; }=()=>[];\n    public Func<double> ReadTime { get; set; }=()=>0;', 1))
replace_once("client/Scripts/HuntingGuidePanel.cs",
'        map=new HuntingRegionMap{Data=Data,ReadCharacter=ReadCharacter,CustomMinimumSize=new Vector2(0,240),SizeFlagsHorizontal=SizeFlags.ExpandFill,SizeFlagsVertical=SizeFlags.ExpandFill};right.AddChild(map);',
'        map=new HuntingRegionMap{Data=Data,ReadCharacter=ReadCharacter,ReadEvents=ReadEvents,CustomMinimumSize=new Vector2(0,240),SizeFlagsHorizontal=SizeFlags.ExpandFill,SizeFlagsVertical=SizeFlags.ExpandFill};right.AddChild(map);')
replace_once("client/Scripts/HuntingGuidePanel.cs",
'        var lead=JourneyProgression.LocalQuest(Data,self,ReadTime());var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);\n        journey.Text=lead is not null?',
'''        var publicEvent=ReadEvents().Where(x=>x.Zone==zone.Id).OrderBy(x=>x.Status=="active"?0:1).ThenByDescending(x=>x.EffectEnds).FirstOrDefault();\n        var lead=JourneyProgression.LocalQuest(Data,self,ReadTime());var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);\n        journey.Text=publicEvent is { Status:"active" }?$"PUBLIC EVENT · {publicEvent.Name}\\n{WorldEventRules.StageLabel(publicEvent)} · {WorldEventRules.ProgressText(publicEvent)} · You {WorldEventRules.Contribution(publicEvent,self.Id):0}"\n            :lead is not null?''')
replace_once("client/Scripts/HuntingGuidePanel.cs",
'    public Func<Character?> ReadCharacter { get; set; }=()=>null;\n    public ZoneDef? Zone { get; set; }',
'    public Func<Character?> ReadCharacter { get; set; }=()=>null;\n    public Func<IEnumerable<WorldEvent>> ReadEvents { get; set; }=()=>[];\n    public ZoneDef? Zone { get; set; }')
replace_once("client/Scripts/HuntingGuidePanel.cs",
'        if(plan.FieldBoss!="")Boss(plan.FieldBossPosition);',
'        if(plan.FieldBoss!="")Boss(plan.FieldBossPosition);\n        foreach(var worldEvent in ReadEvents().Where(x=>x.Zone==zone.Id))DrawArc(At(worldEvent.Position),8,0,Mathf.Tau,20,worldEvent.Status=="failure"?Ui.Danger:new Color("e0b868"),2);')
replace_once("client/Scripts/HuntingGuidePanel.cs",
'        var guide=new HuntingGuidePanel{Data=Data,Assets=Assets,ReadCharacter=()=>Snapshot?.Self,ReadTime=()=>Snapshot?.Time??0};page.AddChild(guide);refreshPage=guide.RefreshSnapshot;',
'        var guide=new HuntingGuidePanel{Data=Data,Assets=Assets,ReadCharacter=()=>Snapshot?.Self,ReadEvents=()=>Snapshot?.Events??[],ReadTime=()=>Snapshot?.Time??0};page.AddChild(guide);refreshPage=guide.RefreshSnapshot;')

# Permanent acceptance coverage.
replace_once("tools/world_probe/Program.cs",
'ClassCombatIdentityChecks.Run(catalog,failures);\nExplorationRewardChecks.Run(catalog,failures);',
'ClassCombatIdentityChecks.Run(catalog,failures);\nLivingWorldEventChecks.Run(catalog,failures);\nExplorationRewardChecks.Run(catalog,failures);')

print("Living-world public event candidate applied.")
