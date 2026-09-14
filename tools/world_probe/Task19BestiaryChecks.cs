using Kairnfall.Core;
using System.Text.Json;

public static class Task19BestiaryChecks
{
    private static readonly IReadOnlyDictionary<string,string> ChampionSignatures = new Dictionary<string,string>(StringComparer.Ordinal)
    {
        ["rare_pine_wolf"] = "Binding Roots",
        ["rare_kobold_slinger"] = "Charge",
        ["rare_fire_beetle"] = "Hazard Field",
        ["rare_ice_elemental"] = "Shock Ring",
        ["rare_gilded_scarab"] = "Call Reinforcements",
        ["rare_arcane_sentinel"] = "Interruptible Cast"
    };

    public static void Run(Catalog data,List<string> failures)
    {
        void Need(bool value,string message) { if(!value) throw new Exception(message); }
        void Check(string name,Action body)
        {
            try { body(); Console.WriteLine("PASS TASK19 BESTIARY: "+name); }
            catch(Exception error) { failures.Add("Task19 "+name); Console.WriteLine("FAIL TASK19 BESTIARY: "+name+": "+error.Message); }
        }

        Check("Task 18 champions expose readable encounter knowledge",()=>
        {
            var champions=data.Mobs.Where(BestiaryKnowledge.IsChampion).OrderBy(x=>x.Id,StringComparer.Ordinal).ToArray();
            Need(champions.Length==ChampionSignatures.Count,"Expected the six established Task 18 champions.");
            foreach(var mob in champions)
            {
                var summary=BestiaryKnowledge.Describe(data,mob);
                Need(summary.Rank=="Champion",mob.Id+" rank is not readable as Champion.");
                Need(ChampionSignatures.TryGetValue(mob.Id,out var signature)&&summary.Attacks.Contains(signature,StringComparer.Ordinal),mob.Id+" omits its signature attack.");
                Need(summary.Attacks.All(x=>!x.Contains('_',StringComparison.Ordinal)),mob.Id+" exposes raw combat tokens.");
                Need(summary.Regions.Length>0,mob.Id+" has no readable encounter region.");
                Need(summary.Drops.Length==mob.Drops.Distinct(StringComparer.Ordinal).Count(),mob.Id+" drop summary does not match existing loot templates.");
                Need(summary.Gold==mob.Gold&&summary.Xp==mob.Xp,mob.Id+" bestiary summary changed authoritative rewards.");
            }
        });

        Check("Bestiary rank taxonomy distinguishes encounter tiers",()=>
        {
            Need(BestiaryKnowledge.Rank(data.Mobs.First(x=>x.Boss))=="Boss","Boss rank missing.");
            Need(BestiaryKnowledge.Rank(data.Mobs.First(x=>x.Elite&&!BestiaryKnowledge.IsChampion(x)))=="Rare / Elite","Rare/elite rank missing.");
            Need(BestiaryKnowledge.Rank(data.Mobs.First(x=>!x.Boss&&!x.Elite))=="Creature","Ordinary creature rank missing.");
        });

        Check("Bestiary knowledge is a read-only projection",()=>
        {
            string before=JsonSerializer.Serialize(data,Wire.Json);
            foreach(var mob in data.Mobs) _=BestiaryKnowledge.Describe(data,mob);
            Need(before==JsonSerializer.Serialize(data,Wire.Json),"Building bestiary summaries mutated the catalog.");
        });
    }
}
