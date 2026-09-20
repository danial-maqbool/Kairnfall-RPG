namespace Kairnfall.Core;

public sealed record JourneyObjective(string Stage, string Title, string Objective, string Why,
    string Reward, string Zone, Point? Position = null, string TargetKind = "", string TargetId = "", string Panel = "Quests");
public sealed record JourneyNavigation(Point? Position, string TargetKind, string TargetId, string Description);
public sealed record JourneyHint(string Id, string Text);

/// <summary>
/// Read-only presentation over authoritative character/snapshot state. It never completes
/// a quest, grants a reward, changes a requirement, or supplies a movement destination to the server.
/// New characters opt in at creation; missing markers in historical saves deliberately opt out.
/// </summary>
public static class NewPlayerJourney
{
    public const string Prefix = "onboarding:v1:";
    public const string EligibleKey = Prefix + "eligible";
    public const string PublicScheduledKey = Prefix + "public_scheduled";
    private static readonly IReadOnlyDictionary<string, string> Hints = new Dictionary<string, string>(StringComparer.Ordinal)
    {
        ["movement"] = "{move_up}/{move_left}/{move_down}/{move_right} moves. {interact} interacts with a nearby target.",
        ["quest"] = "One objective is tracked here. Return to its giver when it is ready to claim.",
        ["combat"] = "{target_next} selects a foe. Hold {basic_attack} to attack; move out of marked attacks.",
        ["loot"] = "Approach the dropped loot and press {interact}. Your backpack opens with {inventory}.",
        ["equipment"] = "This is a usable upgrade, not just a rarer item. Review its gains, then choose Equip.",
        ["socket"] = "Select your weapon in {inventory}, then insert the starter rune into its empty socket.",
        ["level"] = "Training skills raises character level. The level-up card shows your real stat changes.",
        ["gather"] = "Use {interact} on an available resource. Your starter tools already work from the backpack.",
        ["craft"] = "At the sawbench, make oak planks before the handle. {crafting} shows the selected recipe.",
        ["navigation"] = "Show route follows walkable ground. Movement cancels it; {map} shows the wider road.",
        ["social"] = "This is a shared, persistent world. {social} opens nearby travelers and optional parties.",
        ["public"] = "An optional shared event is nearby. Contribute for rewards; no party or other player is required.",
        ["recovery"] = "Your equipment stays yours. Return to safety when ready, then repair at a smith.",
        ["dismiss"] = "Journey hints hidden. Objectives and all game systems remain available."
    };

    public static string HintKey(string id) => Prefix + "hint:" + id;
    public static string MilestoneKey(string id) => Prefix + "milestone:" + id;
    public static bool Seen(Character player, string id) => player.Discoveries.Contains(HintKey(id));
    public static bool Active(Character player) => player.Discoveries.Contains(EligibleKey)
        && !Seen(player, "dismiss") && Progression.PlayerLevel(player) < 20
        && !player.CompletedQuests.Contains("main_03");

    // This is the entire new command surface: a bounded set of presentation-only flags.
    // The caller uses the normal sequenced, receipted, persisted realm transaction.
    public static string Acknowledge(Character player, string id)
    {
        if (!player.Discoveries.Contains(EligibleKey) || !Hints.ContainsKey(id))
            throw new RuleException("That guidance acknowledgement is not available.");
        player.Discoveries.Add(HintKey(id));
        return "Guidance preference saved.";
    }

    public static void Observe(Catalog data, Character before, Character after, GameCommand command)
    {
        if (!after.Discoveries.Contains(EligibleKey)) return;
        string hint = command.Kind switch
        {
            "loot" or "chest" => "loot", "gather" => "gather", "craft" => "craft",
            "claim_quest" => "quest", "socket" => "socket", "respawn" => "recovery",
            "chat" or "party_create" or "party_join" or "friend_accept" or "lfg_set" => "social", _ => ""
        };
        if (hint != "") after.Discoveries.Add(HintKey(hint));
        if (command.Kind is "loot" or "chest") after.Discoveries.Add(MilestoneKey("loot"));
        if (command.Kind == "equip" && ProgressionFeedback.PowerChanges(data, before, after).Count > 0)
        {
            after.Discoveries.Add(MilestoneKey("equipment"));
            after.Discoveries.Add(HintKey("equipment"));
        }
    }

    public static bool Available(Character player, QuestDef quest, double now) => OpeningJourney.QuestVisible(player,quest.Id) && !player.Quests.ContainsKey(quest.Id)
        && (quest.Repeatable || !player.CompletedQuests.Contains(quest.Id))
        && Progression.PlayerLevel(player) >= quest.MinimumLevel
        && (quest.Prerequisite == "" || player.CompletedQuests.Contains(quest.Prerequisite))
        && player.Cooldowns.GetValueOrDefault("quest:" + quest.Id) <= now;

    private static bool StarterSocketReady(Catalog data, Character player) => player.Equipment.TryGetValue("weapon", out var id)
        && player.Inventory.Any(x => x.Id == id && x.Durability > 0 && x.Sockets > x.Runes.Count)
        && Items.Count(player, "rune_embers_1") > 0;

    public static JourneyObjective Recommend(Catalog data, Snapshot snapshot, IEnumerable<LootPile>? loot = null)
    {
        var player = snapshot.Self;
        if (player.Health <= 0) return new("recovery", "Your journey continues", "Return to safety when ready",
            "Equipment is retained. Resume your current quest after recovery.", "No tutorial penalty", player.Zone, Panel: "");
        if (OpeningJourney.Recommend(data,snapshot) is { } opening) return opening;
        bool beginner = Active(player);
        JourneyObjective Offer(QuestDef quest) => AtNpc(data, quest, "quest_offer", "Talk to " + data.Npc(quest.Giver).Name);
        if (beginner && Available(player, data.Quest("main_01"), snapshot.Time)) return Offer(data.Quest("main_01"));
        if (beginner)
        {
            var pile = (loot ?? []).Where(x => x.Zone == player.Zone && x.Expires > snapshot.Time
                && (x.Owner == player.Id || x.PublicAt <= snapshot.Time || x.Party != "" && x.Party == player.Party && x.PartyAt <= snapshot.Time))
                .OrderBy(x => x.Position.Distance(player.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
            if (!player.Discoveries.Contains(MilestoneKey("loot")) && pile is not null)
                return new("loot", "Your first spoils", "Collect the dropped loot", "Defeated foes leave supplies for your journey.",
                    pile.Gold > 0 ? pile.Gold + " gold + dropped items" : "Dropped items", player.Zone, pile.Position, "loot", pile.Id, "Inventory");
            if (!Seen(player, "equipment") && ProgressionFeedback.FindUpgrade(data, player) is { } upgrade)
                return new("equipment", "A stronger loadout", "Equip " + upgrade.Name, upgrade.Detail,
                    "Preview only; choose Equip to apply", player.Zone, TargetKind: "equipment", TargetId: upgrade.ItemId, Panel: "Inventory");
            if (player.Quests.ContainsKey("main_01") && !player.Bestiary.Any(x => x.Value > 0))
            {
                var foe = snapshot.Creatures.Where(x => x.Zone == player.Zone && x.Health > 0 && x.Owner == "")
                    .Where(x => data.Mob(x.Template) is { Boss: false, Elite: false, Level: <= 2 } mob && (mob.Id == "field_rat" || mob.Ai is not "passive" and not "fleeing"))
                    .OrderBy(x => x.Position.Distance(player.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
                if (foe is not null) return new("combat", "Protect the village road", "Defeat one " + data.Mob(foe.Template).Name,
                    "Practice your weapon before continuing the workshop errand. This detour is optional.", "Combat XP and normal loot",
                    player.Zone, foe.Position, "creature", foe.Id, "Hunting");
            }
            if (player.Quests.TryGetValue("starter_rune", out var runeProgress) && (runeProgress.Complete || StarterSocketReady(data, player)))
                return QuestObjective(data, snapshot, data.Quest("starter_rune"), runeProgress);
            if (player.Bestiary.Any(x => x.Value > 0) && StarterSocketReady(data, player)
                && Available(player, data.Quest("starter_rune"), snapshot.Time)) return Offer(data.Quest("starter_rune"));
            if (player.CompletedQuests.Contains("main_01") && !Seen(player, "public") && NearbyEvent(data, snapshot) is { } activity)
            {
                var chest = snapshot.Chests.Where(x => WorldEventRules.Owns(activity, x.Id) && x.ReadyAt <= snapshot.Time && !x.Hidden)
                    .OrderBy(x => x.Position.Distance(player.Position)).FirstOrDefault();
                return new("public", "Optional · " + activity.Name, WorldEventRules.StageLabel(activity),
                    "Share progress with nearby travelers, or participate alone. Not now keeps your quest route active.",
                    WorldEventRules.ContributionStatus(activity, player.Id), activity.Zone, chest?.Position ?? activity.Position,
                    chest is null ? "event" : "chest", chest?.Id ?? activity.Id, "Social");
            }
        }
        // Resolve dynamic faction contracts through the same resolver used by the realm.
        // Unknown historical IDs must not crash the entire HUD or erase valid quest state.
        var accepted = new List<(QuestDef Quest, QuestProgress Progress)>();
        foreach (var entry in player.Quests)
        {
            try { accepted.Add((EndgameLoops.ResolveQuest(data, entry.Key), entry.Value)); }
            catch (RuleException) { }
        }
        var tracked = accepted.OrderBy(x => x.Progress.Complete ? 0 : 1)
            .ThenBy(x => beginner && x.Quest.Id == "main_01" ? -1 : JourneyProgression.QuestPriority(x.Quest))
            .ThenBy(x => x.Quest.Id, StringComparer.Ordinal).FirstOrDefault();
        if (tracked.Quest is not null) return QuestObjective(data, snapshot, tracked.Quest, tracked.Progress);
        if (beginner && Available(player, data.Quest("main_02"), snapshot.Time)) return Offer(data.Quest("main_02"));
        var local = JourneyProgression.LocalQuest(data, player, snapshot.Time);
        if (local is not null) return Offer(data.Quest(local.QuestId));
        // An available main-story lead can be in another settlement. Check the actual exit graph,
        // including entry requirements, instead of recommending locked or unrelated content.
        var lead = data.Quests.Where(x => x.Category == "main" && Available(player, x, snapshot.Time))
            .OrderBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault(x => FirstExit(data, player, data.Npc(x.Giver).Zone) is not null);
        if (lead is not null) return Offer(lead);
        var zone = data.Zone(player.Zone);
        var exit = zone.Exits.Where(x => JourneyProgression.ExitRequirement(data, x) <= Progression.PlayerLevel(player))
            .OrderBy(x => data.Zone(x.Target).Kind == "interior" ? 1 : 0).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
        if (exit is not null) return new("continue", "Continue your journey", "Visit " + data.Zone(exit.Target).Name,
            "Follow an open road to discover legitimate quests and activities. No content is completed for you.",
            "New places and available quest leads", player.Zone, exit.Position, "exit", exit.Id, "Map");
        return new("continue", "Recommended next step", "Review local quests and training",
            "Train skills here until the next road opens. Your accepted quests remain in the journal.",
            "Skill XP contributes to character level", player.Zone, zone.Spawn, Panel: "Quests");
    }

    private static string Reward(Catalog data, QuestDef quest) => quest.Gold + " gold"
        + (quest.Reward == "" ? "" : " · " + data.Item(quest.Reward).Name);
    private static JourneyObjective AtNpc(Catalog data, QuestDef quest, string stage, string objective)
    {
        var npc = data.Npc(quest.Giver);
        return new(stage, quest.Name, objective, quest.Story, Reward(data, quest), npc.Zone, npc.Position, "npc", npc.Id, "Dialogue");
    }
    private static JourneyObjective QuestObjective(Catalog data, Snapshot snapshot, QuestDef quest, QuestProgress progress)
    {
        if (progress.Complete) return AtNpc(data, quest, "claim", "Claim your reward from " + data.Npc(quest.Giver).Name);
        int index = Enumerable.Range(0, quest.Objectives.Count).FirstOrDefault(i => progress.Counts.ElementAtOrDefault(i) < quest.Objectives[i].Count, -1);
        if (index < 0) return AtNpc(data, quest, "quest", "Check in with " + data.Npc(quest.Giver).Name);
        var objective = quest.Objectives[index]; var player = snapshot.Self;
        string count = $" · {progress.Counts.ElementAtOrDefault(index)}/{objective.Count}";
        JourneyObjective Plan(string stage, string text, string zone, Point? point, string kind = "", string id = "", string panel = "Quests")
            => new(stage, quest.Name, text, quest.Story, Reward(data, quest), zone, point, kind, id, panel);
        if (objective.Action == "talk")
        {
            var npc = data.Npc(objective.Target);
            return Plan("quest", "Talk to " + npc.Name + count, npc.Zone, npc.Position, "npc", npc.Id, "Dialogue");
        }
        if (objective.Action == "deliver") return AtNpc(data, quest, "quest", "Deliver " + data.Item(objective.Target).Name + count);
        if (objective.Action == "gather") return GatherObjective(data, snapshot, quest, objective.Target, count);
        if (objective.Action == "craft")
        {
            var recipe = data.Recipes.Where(x => x.Output == objective.Target).OrderBy(x => x.Requirement).FirstOrDefault();
            if (recipe is not null) return CraftObjective(data, snapshot, quest, recipe, 0);
        }
        if (objective.Action == "socket") return Plan("socket", "Insert a rune into your weapon", player.Zone, null,
            "socket", player.Equipment.GetValueOrDefault("weapon", ""), "Inventory");
        if (objective.Action is "kill" or "boss")
        {
            var mob = data.Mobs.FirstOrDefault(x => x.Id == objective.Target);
            var living = snapshot.Creatures.Where(x => x.Template == objective.Target && x.Health > 0 && x.Owner == "")
                .OrderBy(x => x.Position.Distance(player.Position)).FirstOrDefault();
            var site = data.Zones.Where(x => x.Boss == objective.Target || x.Species.Contains(objective.Target))
                .OrderBy(x => x.Id == player.Zone ? 0 : 1).FirstOrDefault();
            if (site is not null) return Plan("combat", "Defeat " + (mob?.Name ?? objective.Target) + count,
                living?.Zone ?? site.Id, living?.Position ?? site.Spawn, living is null ? "" : "creature", living?.Id ?? "", "Hunting");
        }
        if (objective.Action is "explore" or "chart" && data.Zones.FirstOrDefault(x => x.Id == objective.Target) is { } destination)
            return Plan("navigation", (objective.Action == "chart" ? "Record a regional chart" : "Reach " + destination.Name) + count,
                destination.Id, destination.Spawn, panel: "Map");
        if (objective.Action == "survey")
            foreach (var site in data.Zones)
                if (site.Buildings.FirstOrDefault(x => x.Id == objective.Target) is { } landmark)
                    return Plan("navigation", "Survey " + landmark.Name + count, site.Id, JourneyProgression.LandmarkPoint(landmark), "landmark", landmark.Id, "Map");
        return Plan("quest", objective.Description + count, player.Zone, null) with
        { Why = quest.Story + "\n" + JourneyProgression.ObjectiveGuidance(data, quest, objective, player) };
    }

    private static JourneyObjective GatherObjective(Catalog data, Snapshot snapshot, QuestDef quest, string material, string count)
    {
        var player = snapshot.Self;
        var resources = data.Resources.Where(x => x.Item == material && Progression.Level(player, x.Skill) >= x.Requirement).ToArray();
        var ids = resources.Select(x => x.Id).ToHashSet(StringComparer.Ordinal);
        var node = snapshot.Nodes.Where(x => ids.Contains(x.Template) && (x.Owner == "" || x.Owner == player.Id))
            .OrderBy(x => x.ReadyAt > snapshot.Time ? 1 : 0).ThenBy(x => x.Position.Distance(player.Position)).FirstOrDefault();
        var site = data.Zones.Where(x => x.Resources.Any(ids.Contains) && JourneyProgression.CanEnter(data, player, x))
            .OrderBy(x => x.Id == player.Zone ? 0 : 1).ThenBy(x => x.Level).FirstOrDefault();
        return new("gather", quest.Name, "Gather " + data.Item(material).Name + count,
            quest.Story + (node is not null && node.ReadyAt > snapshot.Time ? "\nThis resource is replenishing; other local nodes may be ready." : ""),
            Reward(data, quest), node?.Zone ?? site?.Id ?? player.Zone, node?.Position ?? site?.Spawn,
            node is null ? "" : "node", node?.Id ?? "", "Hunting");
    }
    private static JourneyObjective CraftObjective(Catalog data, Snapshot snapshot, QuestDef quest, RecipeDef recipe, int depth)
    {
        var player = snapshot.Self;
        if (depth < 4)
            foreach (var missing in recipe.Ingredients.Where(x => Items.Count(player, x.Key) < x.Value))
            {
                var intermediate = data.Recipes.Where(x => x.Output == missing.Key && Progression.Level(player, x.Skill) >= x.Requirement)
                    .OrderBy(x => x.Requirement).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
                if (intermediate is not null) return CraftObjective(data, snapshot, quest, intermediate, depth + 1);
                if (data.Resources.Any(x => x.Item == missing.Key))
                    return GatherObjective(data, snapshot, quest, missing.Key, $" · need {missing.Value - Items.Count(player, missing.Key)} more");
            }
        var station = data.Npcs.Where(x => x.Station == recipe.Station)
            .OrderBy(x => x.Zone == player.Zone ? 0 : 1).ThenBy(x => x.Position.Distance(player.Position)).FirstOrDefault();
        return new("craft", quest.Name, "Craft " + data.Item(recipe.Output).Name,
            "Prepare the required ingredients at the " + recipe.Station.Replace('_', ' ') + ". The recipe panel checks station, skill, and material readiness.",
            Reward(data, quest), station?.Zone ?? player.Zone, station?.Position, "recipe", recipe.Id, "Crafting");
    }

    public static ExitDef? FirstExit(Catalog data, Character player, string destination)
    {
        if (destination == player.Zone) return null;
        var visited = new HashSet<string>(StringComparer.Ordinal) { player.Zone };
        var queue = new Queue<(string Zone, ExitDef? First)>(); queue.Enqueue((player.Zone, null));
        while (queue.TryDequeue(out var item))
            foreach (var exit in data.Zone(item.Zone).Exits.OrderBy(x => x.Id, StringComparer.Ordinal))
            {
                if (JourneyProgression.ExitRequirement(data, exit) > Progression.PlayerLevel(player) || !visited.Add(exit.Target)) continue;
                var first = item.First ?? exit;
                if (exit.Target == destination) return first;
                queue.Enqueue((exit.Target, first));
            }
        return null;
    }
    public static JourneyNavigation Navigation(Catalog data, Character player, JourneyObjective objective)
    {
        if (objective.Zone != player.Zone)
        {
            var exit = FirstExit(data, player, objective.Zone);
            return exit is null ? new(null, "", "", "Check the entry requirements on the map")
                : new(exit.Position, "exit", exit.Id, Bearing(player.Position, exit.Position) + " · via " + data.Zone(exit.Target).Name);
        }
        return new(objective.Position, objective.TargetKind, objective.TargetId,
            objective.Position is { } point ? Bearing(player.Position, point) : "Here in " + data.Zone(player.Zone).Name);
    }
    public static string Bearing(Point origin, Point destination)
    {
        double distance = origin.Distance(destination);
        if (distance <= 3) return "Nearby";
        string[] directions = ["E", "SE", "S", "SW", "W", "NW", "N", "NE"];
        int octant = ((int)Math.Round(Math.Atan2(destination.Y - origin.Y, destination.X - origin.X) / (Math.PI / 4)) + 8) % 8;
        return $"Map {directions[octant]} · about {Math.Ceiling(distance):0} tiles";
    }
    public static bool ActivityRelevant(Catalog data, Character player, WorldEvent activity, double now)
    {
        if (activity.Ends <= now) return false;
        if (WorldEventRules.Contribution(activity, player.Id) > 0) return true;
        if (activity.Zone != player.Zone || activity.Position.Distance(player.Position) > 40) return false;
        var zone = data.Zones.FirstOrDefault(x => x.Id == activity.Zone);
        if (zone is null || !JourneyProgression.CanEnter(data, player, zone)) return false;
        int level = Progression.PlayerLevel(player);
        if (Active(player) && level < 10 && WorldEventRules.NormalizeKind(activity.Kind) != "treasure_surge") return false;
        return zone.Level <= level + 5 && (activity.Kind != "world_boss" || level >= zone.Level);
    }
    public static WorldEvent? NearbyEvent(Catalog data, Snapshot snapshot) => snapshot.Events
        .Where(x => x.Status == "active" && x.StageEnds > snapshot.Time && x.Zone == snapshot.Self.Zone
            && x.Position.Distance(snapshot.Self.Position) <= 40 && ActivityRelevant(data, snapshot.Self, x, snapshot.Time))
        .OrderBy(x => x.Position.Distance(snapshot.Self.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();

    public static JourneyHint? NextHint(Catalog data, Snapshot snapshot, JourneyObjective objective)
    {
        var player = snapshot.Self;
        if (!Active(player)) return null;
        string id = player.Health <= 0 ? "recovery"
            : !FirstHourExperience.Marked(player, "movement") && !Seen(player, "movement") ? "movement"
            : objective.Stage == "public" && !Seen(player, "public") ? "public"
            : Progression.PlayerLevel(player) >= 2 && !Seen(player, "level") ? "level"
            : objective.Stage == "equipment" ? "equipment"
            : objective.Stage == "socket" ? "socket"
            : objective.Stage == "loot" ? "loot"
            : objective.Stage == "combat" && objective.Position is { } foe && foe.Distance(player.Position) <= 12 ? "combat"
            : player.CompletedQuests.Contains("main_01") && !Seen(player, "social") ? "social"
            : objective.Stage == "craft" ? "craft"
            : objective.Stage == "gather" ? "gather"
            : player.Quests.Count > 0 && !Seen(player, "quest") ? "quest"
            : Navigation(data, player, objective).Position is { } destination && destination.Distance(player.Position) > 10 ? "navigation" : "";
        if (id == "craft" && OpeningJourney.Eligible(player) && !OpeningJourney.Finished(player))
            return !Seen(player,id) ? new(id,"At the village alchemy table, open {crafting}. Select Healing Potions and make one batch: 2 Meadow Leaves + 1 Empty Vial make 2 useful potions. The recipe shows costs and missing requirements before you commit.") : null;
        if (id == "combat" && OpeningJourney.Eligible(player) && !OpeningJourney.Finished(player))
            return !Seen(player,id) ? new(id,"Use {target_next} to select one Field Rat, then hold {basic_attack} in weapon range. Move away from the attack warning; {dash} helps you leave danger but does not make you invulnerable. Return to the village after two victories.") : null;
        return id != "" && !Seen(player, id) ? new(id, Hints[id]) : null;
    }
}
