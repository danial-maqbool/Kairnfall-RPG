using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Presentation-only preflight; the realm remains authoritative for every transfer and random reward.</summary>
public static class InteractionReadinessRules
{
    public static string TutorialSiteProblem(Character self, WorldTarget target, Catalog data, double time)
    {
        if (target.Kind != "classic_site" || ClassicInteractionRules.TutorialSite(self, data, target.Id) is not { } site)
            return "This object belongs to an optional First Glade tutorial.";
        if (self.Health <= 0) return "Respawn before interacting.";
        if (!double.IsFinite(time) || !double.IsFinite(self.Health) || !self.Position.Finite || !self.Facing.Finite)
            return "Wait for a fresh realm snapshot.";
        if (target.Position != site.Position) return "Tutorial object is no longer available.";
        // Solid furnishings block full endpoint LOS. Match the realm's short
        // approach check, and derive facing only from its accepted snapshot.
        if (self.Position.Distance(site.Position) > 1.05 || !ClassicTutorialContent.FacingAdjacent(self, site.Position))
            return "Move to an adjacent tile and face " + site.Name + ".";
        var zone = data.Zones.FirstOrDefault(x => x.Id == self.Zone);
        if (zone is null) return "Wait for a fresh realm snapshot.";
        var approach = self.Position.Add(self.Position.Direction(site.Position).Scale(.45));
        return WorldMap.LineOfSight(zone, self.Position, approach) ? "" : "The object is behind an obstacle.";
    }

    private static string PositionProblem(Character self, string zone, Point at, Catalog data, double time)
    {
        if (self.Health <= 0) return "Respawn before interacting.";
        if (!double.IsFinite(time)) return "Wait for a fresh realm snapshot.";
        if (self.Zone != zone || !self.Position.Finite || !at.Finite || self.Position.Distance(at) > 2.5)
            return "Move closer to the target.";
        return WorldMap.LineOfSight(data.Zone(self.Zone), self.Position, at) ? "" : "The target is behind an obstacle.";
    }

    public static string ChestProblem(Character self, Chest? chest, Catalog data, double time)
    {
        if (chest is null) return "Chest is no longer available.";
        string position = PositionProblem(self, chest.Zone, chest.Position, data, time);
        if (position != "") return position;
        if (!double.IsFinite(chest.ReadyAt) || chest.ReadyAt > time) return "This chest is empty. Return after it restocks.";
        if (chest.Hidden && !self.Discoveries.Contains("secret:" + chest.Id)) return "Find this chest before opening it.";
        if (!(self.Cooldowns.GetValueOrDefault("chest") <= time)) return "Wait for chest-opening recovery.";
        if (chest.Kind == "locked")
        {
            if (Progression.Level(self, "lockpicking") < chest.Requirement) return "Requires Lockpicking " + chest.Requirement + ".";
            if (Items.Count(self, "lockpick") < 1) return "Keep a Lockpick in your backpack.";
        }
        if (chest.Kind == "runic" && Progression.Level(self, "runecasting") < Math.Max(1, chest.Requirement / 2))
            return "Requires Runecasting " + Math.Max(1, chest.Requirement / 2) + ".";
        // Opening can consume the last lockpick and random rune rewards may stack.
        // The realm's atomic grant owns randomized reward capacity, never a guessed slot count.
        return "";
    }

    public static string LootProblem(Character self, LootPile? pile, Catalog data, double time, bool checkStorage = true)
    {
        if (pile is null) return "Ground loot is no longer available.";
        string position = PositionProblem(self, pile.Zone, pile.Position, data, time);
        if (position != "") return position;
        if (!double.IsFinite(pile.Expires) || pile.Expires <= time) return "This ground loot has expired.";
        if (!ExperienceRules.LootAvailable(self, pile, time)) return "This loot is reserved for another player. Wait for public access.";
        if (pile.Gold < 0 || pile.Gold > Items.GoldCap || self.Gold > Items.GoldCap - pile.Gold) return "Gold limit reached.";
        if (!checkStorage) return "";
        // Use the real stack/metadata/capacity rules only on an action attempt,
        // on a detached bag. HUD frame updates never copy or simulate inventory.
        var bag = Wire.Copy(self.Inventory);
        try
        {
            foreach (var item in pile.Items) Items.Add(bag, Wire.Copy(item), data);
        }
        catch (RuleException error) { return error.Message; }
        return "";
    }
}

public partial class GameRoot
{
    private string InteractionProblem(WorldTarget target, bool checkStorage = true)
    {
        if (Snapshot is not { } snapshot) return "Wait for a fresh realm snapshot.";
        return target.Kind switch
        {
            "classic_site" => InteractionReadinessRules.TutorialSiteProblem(snapshot.Self, target, Data, snapshot.Time),
            "node" when ClassicInteractionRules.InTutorial(snapshot.Self, Data) => TutorialResourceProblem(snapshot, target),
            "chest" => InteractionReadinessRules.ChestProblem(snapshot.Self, snapshot.Chests.FirstOrDefault(x => x.Id == target.Id), Data, snapshot.Time),
            "loot" => InteractionReadinessRules.LootProblem(snapshot.Self, World.Loot.FirstOrDefault(x => x.Id == target.Id), Data, snapshot.Time, checkStorage),
            _ => ""
        };
    }

    private string TutorialResourceProblem(Snapshot snapshot, WorldTarget target)
    {
        var node = snapshot.Nodes.FirstOrDefault(x => x.Id == target.Id);
        if (node is null) return "Resource is no longer available.";
        if (!node.Template.StartsWith("classic_", StringComparison.Ordinal)) return "";
        if (target.Position != node.Position) return "Resource is no longer available.";
        return ClassicGatherRules.Problem(snapshot.Self, node, Data, snapshot.Time);
    }
}
