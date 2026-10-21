using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Optional client guidance over accepted tutorial state; it never records progress or supplies rewards.</summary>
public static class ClassicTutorialJourneyRules
{
    public static bool IsObjective(JourneyObjective objective) => objective.Stage.StartsWith("classic_", StringComparison.Ordinal);

    public static JourneyObjective? Recommend(Catalog data, Snapshot snapshot)
    {
        var self = snapshot.Self;
        if (!ClassicInteractionRules.InTutorial(self, data) || self.Health <= 0 || !self.Position.Finite || !double.IsFinite(snapshot.Time)) return null;
        var completed = self.ClassicTutorial!.Completed;
        const string title = "Optional · First Glade";
        JourneyObjective Plan(string stage, string text, string why, Point? at = null, string kind = "", string id = "", string panel = "Map")
            => new("classic_" + stage, title, text, why + " These lessons are optional; the eastern road remains open.",
                "Progress is recorded by the realm after the real action.", self.Zone, at, kind, id, panel);
        JourneyObjective Site(string id, string action)
        {
            var site = ClassicTutorialContent.Sites.First(x => x.Id == id);
            return Plan("site", action + " " + site.Name, "Select the object, stand on a cardinal adjacent tile and face it, then use Space or the Action Circle.",
                site.Position, "classic_site", site.Id);
        }
        JourneyObjective Gather(string template, string text)
        {
            var nodes = snapshot.Nodes.Where(x => x.Zone == self.Zone && x.Template == template && x.Position.Finite && double.IsFinite(x.ReadyAt));
            var node = nodes.OrderBy(x => x.ReadyAt > snapshot.Time ? 1 : 0).ThenBy(x => x.Position.Distance(self.Position))
                .ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
            string why = "Select the resource, move to a cardinal adjacent tile and face it. Use Space to start gathering; movement or Action again stops it.";
            if (node is not null && node.ReadyAt > snapshot.Time) why += $" This resource recovers in {Math.Ceiling(node.ReadyAt - snapshot.Time):0} seconds.";
            if (node is null) why = "No matching resource is visible in the latest snapshot. Explore the glade or review your materials in the backpack.";
            return Plan("gather", text, why, node?.Position, node is null ? "" : "node", node?.Id ?? "", node is null ? "Inventory" : "Hunting");
        }
        JourneyObjective Recipe(string id, bool build)
        {
            var recipe = data.Recipe(id);
            foreach (var ingredient in recipe.Ingredients)
                if (Items.Count(self, ingredient.Key) < ingredient.Value && data.Resources.FirstOrDefault(x => x.Item == ingredient.Key) is { } resource)
                    return Gather(resource.Id, $"Gather {data.Item(ingredient.Key).Name} · {Items.Count(self, ingredient.Key)}/{ingredient.Value}");
            string problem = ClassicCraftRules.Problem(self, recipe, data, snapshot.Time, recipe.Station == "hand", true);
            string why = build ? "Review the Fire recipe, choose Build, then choose clear wilderness within three tiles. The realm checks the site and materials."
                : "Open Build & Craft, review the Stone Pickaxe recipe and choose Craft. The realm checks materials, skill and backpack space.";
            if (problem != "") why += " " + problem;
            return Plan("recipe", (build ? "Build " : "Craft ") + recipe.Name, why, kind: "recipe", id: recipe.Id, panel: "Crafting");
        }
        JourneyObjective? Rat()
        {
            var rat = snapshot.Creatures.Where(x => x.Zone == self.Zone && x.Template == "field_rat" && x.Owner == "" && x.Health > 0 && x.Position.Finite)
                .OrderBy(x => x.Position.Distance(self.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
            return rat is null ? null : Plan("combat", "Defeat one Field Rat", "Click the rat to repeat attacks within weapon reach, or select it and hold Space. Selecting something else stops repeated attacks. Shift picks up owned loot under your feet.",
                rat.Position, "creature", rat.Id, "Hunting");
        }
        if (snapshot.Creatures.Any(x => x.Zone == self.Zone && x.Owner == "" && x.Health > 0 && (x.Target == self.Id || x.Threat.ContainsKey(self.Id))) && Rat() is { } fight) return fight;
        if (!completed.Contains("read_sign")) return Site("classic_first_sign", "Read");
        if (!completed.Contains("fountain")) return Site("classic_fountain", "Visit");
        if (!completed.Contains("wood")) return Gather("classic_tree", "Gather Wood from a Berry Oak");
        if (!completed.Contains("stone")) return Gather("classic_stone_node", "Gather Loose Stone");
        if (!completed.Contains("food") && self.Inventory.FirstOrDefault(x => x.Quantity > 0
                && data.Items.Any(def => def.Id == x.Template && def.Type == "food" && def.Effect == "food")) is { } food)
            return Plan("food", "Eat " + data.Item(food.Template).Name, "Open your backpack and choose Eat. Food and item recovery come from the latest realm snapshot.",
                kind: "inventory_item", id: food.Id, panel: "Inventory");
        if (!completed.Contains("pickaxe")) return Recipe("classic_make_pickaxe", false);
        if (!completed.Contains("rat") && Rat() is { } ratLesson) return ratLesson;
        if (!completed.Contains("fire")) return Recipe("classic_make_fire", true);
        var exit = data.Zone(self.Zone).Exits.FirstOrDefault(x => x.Target == OpeningJourney.Home
            && JourneyProgression.ExitRequirement(data, x) <= Progression.PlayerLevel(self));
        return exit is null ? Plan("continue", "Explore First Glade", "Review your supplies or continue exploring.")
            : Plan("exit", "Continue to Wayfarer's Rest", "Follow the eastern road whenever you are ready for the ordinary shared world.", exit.Position, "exit", exit.Id, "Map");
    }
}
