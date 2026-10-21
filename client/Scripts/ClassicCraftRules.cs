using Kairnfall.Core;

namespace Kairnfall.Client;

public static class ClassicCraftRules
{
    public static string Problem(Character? self, RecipeDef? recipe, Catalog data, double time, bool atStation, bool canSubmit)
    {
        if (self is null || recipe is null) return "Choose a recipe.";
        if (self.Health <= 0) return "Respawn before crafting.";
        if (Progression.Level(self, recipe.Skill) < recipe.Requirement) return "Requires " + data.Skill(recipe.Skill).Name + " " + recipe.Requirement + ".";
        string specialization = BuildDefiningLoot.CraftSpecializationProblem(self, recipe, "", data);
        if (specialization != "") return specialization;
        foreach (var ingredient in recipe.Ingredients)
            if (Items.Count(self, ingredient.Key) < ingredient.Value) return "Need " + ingredient.Value + " " + data.Item(ingredient.Key).Name + ".";
        if (data.Item(recipe.Output).Type != "structure")
        {
            if (!atStation) return "Move closer to the " + Ui.Words(recipe.Station) + ".";
            if (self.Cooldowns.GetValueOrDefault("craft") > time) return "Wait for crafting recovery.";
        }
        if (!canSubmit) return "Wait for the realm to confirm the current action.";
        return "";
    }
}
