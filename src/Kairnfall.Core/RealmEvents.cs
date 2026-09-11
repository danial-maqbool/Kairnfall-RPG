namespace Kairnfall.Core;

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

    private void RecordEventSupport(Character player, Character ally, double amount)
    {
        if(amount<=0) return;
        foreach(var value in State.Events.Where(x=>x.Status=="active"&&x.Zone==player.Zone&&player.Position.Distance(x.Position)<=32&&ally.Position.Distance(x.Position)<=32))
            AddEventContribution(value,player.Id,Math.Clamp(amount/12,.5,8));
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
        value.Progress += 1; AddEventContribution(value, player.Id, 8); Progress(player,"event",value.Kind);
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
