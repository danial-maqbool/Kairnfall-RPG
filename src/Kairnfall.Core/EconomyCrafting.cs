namespace Kairnfall.Core;

public sealed record ReclaimPlan(RecipeDef Recipe,string Material,int Quantity,long InputValue,long RecoveredValue);

/// <summary>Shared prices used by both the authoritative realm and client presentation.</summary>
public static class EconomyServices
{
    public static long RepairPrice(ItemDef definition,int durability)
        =>Math.Max(1,(long)Math.Ceiling((100-Math.Clamp(durability,0,100))*Math.Max(1,definition.Value)/500.0));

    public static long RuneExtractionPrice(ItemDef rune)=>Math.Max(20,rune.Value/2);

    public static long RestPrice(Character player)
    {
        int level=Progression.PlayerLevel(player);
        return 5L+Math.Max(0,(level-1)/10)*2L;
    }

    public static long TravelPrice(Catalog data,Character player,ZoneDef source,ZoneDef destination)
    {
        int distance=Math.Abs(destination.WorldX-source.WorldX)+Math.Abs(destination.WorldY-source.WorldY);
        int threat=JourneyProgression.ThreatLevel(data,destination);
        int level=Progression.PlayerLevel(player);
        return Math.Clamp(15L+distance*3L+threat/5L+Math.Max(0,(level-1)/10)*2L,15L,120L);
    }
}

/// <summary>Crafting-value, quality and reclaim rules. Reclaiming is deliberately lossy.</summary>
public static class CraftEconomy
{
    public static long RecipeInputValue(Catalog data,RecipeDef recipe)
        =>recipe.Ingredients.Sum(x=>checked((long)Math.Max(0,data.Item(x.Key).Value)*x.Value));

    public static long RecipeOutputValue(Catalog data,RecipeDef recipe)
        =>checked((long)Math.Max(0,data.Item(recipe.Output).Value)*recipe.Quantity);

    public static RecipeDef? RecipeForOutput(Catalog data,string template)
        =>data.Recipes.Where(x=>x.Output==template&&x.Quantity==1)
            .OrderBy(x=>x.Requirement).ThenBy(x=>x.Id,StringComparer.Ordinal).FirstOrDefault();

    public static ReclaimPlan? Reclaim(Catalog data,Item item)
    {
        var definition=data.Items.FirstOrDefault(x=>x.Id==item.Template);
        if(definition is null||item.Quantity!=1||definition.StackMax!=1||item.Runes.Count>0) return null;
        if(definition.Slot==""&&definition.Type!="tool") return null;
        if(definition.Tags.Contains("boss_unique",StringComparer.Ordinal)||definition.Tags.Contains("exploration_unique",StringComparer.Ordinal)) return null;
        var recipe=RecipeForOutput(data,definition.Id); if(recipe is null) return null;
        long input=RecipeInputValue(data,recipe); if(input<=1) return null;
        long budget=Math.Max(1,(long)Math.Floor(input*.49));
        (string Material,int Quantity,long Value)? best=null;
        foreach(var ingredient in recipe.Ingredients.OrderBy(x=>x.Key,StringComparer.Ordinal))
        {
            long unit=Math.Max(1,data.Item(ingredient.Key).Value);
            int quantity=(int)Math.Min(ingredient.Value,budget/unit);
            if(quantity<1) continue;
            long recovered=checked(unit*quantity);
            if(best is null||recovered>best.Value.Value||(recovered==best.Value.Value&&string.CompareOrdinal(ingredient.Key,best.Value.Material)<0))
                best=(ingredient.Key,quantity,recovered);
        }
        if(best is null) return null;
        return new(recipe,best.Value.Material,best.Value.Quantity,input,best.Value.Value);
    }

    public static string QualityHint(Character? player,RecipeDef recipe,Catalog data)
    {
        var output=data.Item(recipe.Output);
        if(output.StackMax>1) return "Stackable output · fixed Common quality.";
        int skill=player is null?0:Progression.Level(player,recipe.Skill);
        foreach(var rarity in Enum.GetValues<Rarity>().Where(x=>x>Rarity.Common))
        {
            int gate=Items.CraftRarityRequirement(rarity,recipe.Requirement);
            if(gate>skill) return $"Craft skill {skill} · next quality gate: {rarity} at {gate}.";
        }
        return $"Craft skill {skill} · every rarity gate unlocked; mastery still improves the roll.";
    }
}
