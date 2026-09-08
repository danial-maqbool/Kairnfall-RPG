namespace Kairnfall.Core;

/// <summary>Presentation and validation of complete, skill-gated equipment tracks.</summary>
public sealed class EquipmentTierDef
{
    public string Id { get; set; } = "";
    public int Level { get; set; }
    public string Name { get; set; } = "";
    public string Cloth { get; set; } = "";
    public string Leather { get; set; } = "";
    public Dictionary<string,string> Entries { get; set; } = [];

    public static readonly string[] WeaponFamilies = ["sword","greatsword","axe","greataxe","mace","greatmace","spear","halberd","dagger","bow","crossbow","staff","wand","tome","knuckles"];
    public static readonly string[] ArmorSlots = ["helmet","chest","gloves","legs","boots","belt","cloak"];
    public static readonly string[] ToolFamilies = ["pickaxe","axe","rod","sickle","shovel","knife","hammer"];
    public static IReadOnlyList<string> Families { get; } = Array.AsReadOnly(
        WeaponFamilies.Select(x=>"weapon/"+x)
        .Concat(new[]{"light","medium","heavy"}.SelectMany(w=>ArmorSlots.Select(s=>"armor/"+w+"/"+s)))
        .Concat(new[]{"shield","focus","quiver","orb"}.Select(x=>"offhand/"+x))
        .Concat(new[]{"ring","necklace","charm","trinket"}.Select(x=>"accessory/"+x))
        .Concat(ToolFamilies.Select(x=>"tool/"+x)).ToArray());

    public static void Validate(Catalog data, List<string> errors)
    {
        var seen = new HashSet<int>();
        var items = data.Items.GroupBy(x=>x.Id).ToDictionary(x=>x.Key,x=>x.First());
        foreach (var tier in data.EquipmentTiers)
        {
            if (tier.Level is < 1 or > Progression.SkillCap || !seen.Add(tier.Level)
                || string.IsNullOrWhiteSpace(tier.Id) || string.IsNullOrWhiteSpace(tier.Name))
                errors.Add("Invalid equipment tier: " + tier.Id);
            if (tier.Entries.Count != Families.Count || Families.Any(x=>!tier.Entries.ContainsKey(x)))
                errors.Add("Incomplete equipment tier: " + tier.Id);
            foreach (var entry in tier.Entries)
            {
                if (!items.TryGetValue(entry.Value,out var def)) { errors.Add("Missing equipment tier item: " + entry.Value); continue; }
                var parts=entry.Key.Split('/');
                bool matches = parts.Length>=2 && def.Type==parts[0] && def.Requirement==tier.Level && def.Skill!="" && def.StackMax==1;
                if (parts.Length==3 && parts[0]=="armor") matches &= def.Tags.Contains(parts[1]) && def.Slot==parts[2];
                else if (parts.Length==2) matches &= parts[0]=="accessory" ? def.Slot==parts[1] : def.Tags.Contains(parts[1]);
                else matches=false;
                if (!matches) errors.Add("Wrong equipment tier family or level: " + entry.Key + "/" + entry.Value);
                if (!data.Recipes.Any(r=>r.Output==def.Id)) errors.Add("Equipment has no crafting route: " + def.Id);
                if (!double.IsFinite(def.Power) || !double.IsFinite(def.Armor) || !double.IsFinite(def.Speed)
                    || def.Power<0 || def.Armor<0 || def.Speed<=0 || def.Stats.Any(s=>!double.IsFinite(s.Value)))
                    errors.Add("Non-finite equipment stats: " + def.Id);
            }
        }
    }
}

/// <summary>Only usable, owned tools contribute. Inventory order never stacks bonuses.</summary>
public static class ToolRules
{
    public static ItemDef? Best(Character character, Catalog data, string tag, string skill)
        => character.Inventory.Where(i=>i.Durability>0)
            .Select(i=>data.Item(i.Template))
            .Where(d=>d.Type=="tool" && d.Tags.Contains(tag) && d.Skill==skill
                && Progression.Level(character,d.Skill)>=d.Requirement)
            .OrderByDescending(d=>d.Requirement).ThenBy(d=>d.Id,StringComparer.Ordinal).FirstOrDefault();

    public static double Efficiency(ItemDef? tool) => FiniteBonus(tool,"tool_efficiency",15);
    public static double Yield(ItemDef? tool) => FiniteBonus(tool,"tool_yield",20);
    private static double FiniteBonus(ItemDef? tool,string stat,double maximum)
    {
        double value=tool?.Stats.GetValueOrDefault(stat)??0;
        return double.IsFinite(value)?Math.Clamp(value,0,maximum):0;
    }
    public static double StaminaCost(ItemDef? tool) => 6*(1-Efficiency(tool)/100);
    public static double CraftRecovery(Character character,Catalog data,RecipeDef recipe,int quantity)
    {
        var tool=recipe.Skill=="smithing"?Best(character,data,"hammer","smithing"):null;
        return Math.Max(.85,Math.Max(1,quantity*.5)*(1-Efficiency(tool)/100));
    }
}
