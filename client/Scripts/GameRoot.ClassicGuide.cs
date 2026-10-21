using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private JourneyObjective SessionJourneyObjective(Snapshot snapshot)
        => ClassicTutorialJourneyRules.Recommend(Data, snapshot) ?? NewPlayerJourney.Recommend(Data, snapshot, World.Loot);

    private string? ClassicJourneyAction(JourneyObjective objective)
        => !ClassicTutorialJourneyRules.IsObjective(objective) ? null : objective.TargetKind switch
        {
            "classic_site" => "Select object",
            "node" => "Select resource",
            "recipe" => objective.TargetId == "classic_make_fire" ? "Review build" : "Review craft",
            "inventory_item" => "Open food",
            _ => null
        };

    private bool FollowClassicJourneyObjective(Snapshot snapshot, JourneyObjective objective)
    {
        if (!ClassicTutorialJourneyRules.IsObjective(objective)) return false;
        if (objective.TargetKind == "classic_site" && ClassicInteractionRules.TutorialSite(snapshot.Self, Data, objective.TargetId) is { } site)
        {
            SelectTarget("classic_site", site.Id); ClearRoute(); pendingInteraction = null; World.Waypoint = null;
            Notify("Stand on a cardinal adjacent tile and face " + site.Name + ", then use Space or the Action Circle.");
            return true;
        }
        if (objective.TargetKind == "node" && snapshot.Nodes.FirstOrDefault(x => x.Id == objective.TargetId && x.Zone == snapshot.Self.Zone) is { } node)
        {
            SelectTarget("node", node.Id); ClearRoute(); pendingInteraction = null; World.Waypoint = null;
            Notify("Stand on a cardinal adjacent tile and face the resource. Use Space to start gathering; movement or Action again stops it.");
            return true;
        }
        if (objective.TargetKind == "inventory_item")
        {
            if (snapshot.Self.Inventory.Any(x => x.Id == objective.TargetId)) { selectedItem = objective.TargetId; selectedBag = "inventory"; }
            OpenPage("Inventory"); return true;
        }
        if (objective.TargetKind == "recipe")
        {
            // A deliberate lesson click reveals its recipe even after a previous search.
            selectedRecipe = objective.TargetId; classicRecipeSearch = "";
            OpenPage("Crafting"); return true;
        }
        return false;
    }
}
