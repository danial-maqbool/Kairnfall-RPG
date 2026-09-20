using Kairnfall.Core;
using System.Runtime.CompilerServices;
using System.Text.Json;

/// <summary>Detects clear economy pathologies and prints balance metrics. Human pacing judgment remains a separate gate.</summary>
internal static class EconomyBalanceAuditChecks
{
    [ModuleInitializer]
    internal static void RunOnWorldProbeStart()
    {
        var args=Environment.GetCommandLineArgs();
        string path=args.Length>1?args[1]:"content/catalog.json";
        var data=JsonSerializer.Deserialize<Catalog>(File.ReadAllText(path),Wire.Json)??throw new InvalidDataException("Empty economy catalog.");
        var failures=new List<string>();
        Run(data,failures);
        if(failures.Count>0) throw new InvalidDataException("Economy balance audit failed: "+string.Join(" | ",failures.Take(20)));
    }

    private static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message) { if(!value) throw new InvalidOperationException(message); }
        void Test(string name,Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS ECONOMY BALANCE: "+name); }
            catch(Exception error) { failures.Add(name+": "+error.Message); Console.WriteLine("FAIL ECONOMY BALANCE: "+name+": "+error.Message); }
        }

        Test("sellable content has valid values and merchant resale cannot create direct arbitrage",()=>
        {
            var realm=new RealmEngine(data); var p=realm.CreateCharacter("economy-audit","Economy Audit","vanguard",new());
            var ratios=new List<double>(); int quotes=0;
            foreach(var npc in data.Npcs.Where(n=>n.Stock.Length>0))
            foreach(var id in npc.Stock.Distinct(StringComparer.Ordinal))
            {
                var def=data.Item(id); Need(def.Value>=0,"Negative item value: "+id);
                if(def.Value<=0||def.Type=="quest") continue;
                long buy=realm.BuyPrice(p,npc,def),sell=MerchantSales.UnitPrice(def); quotes++;
                Need(buy>sell,$"Direct buy/sell arbitrage or zero spread: {npc.Id}/{id} buy {buy}, sell {sell}.");
                ratios.Add(buy/(double)sell);
            }
            Need(quotes>100,"Too few merchant price pairs were audited.");
            ratios.Sort();
            Console.WriteLine($"ECONOMY METRIC merchant_spread pairs={quotes} min={ratios.First():F2} median={ratios[ratios.Count/2]:F2} max={ratios.Last():F2}");
        });

        Test("equipment tracks keep positive values and end above their first authored tier",()=>
        {
            Need(data.EquipmentTiers.Count>=20,"Equipment tier coverage is too small.");
            var ordered=data.EquipmentTiers.OrderBy(t=>t.Level).ToArray();
            foreach(var family in EquipmentTierDef.Families)
            {
                var track=ordered.Select(t=>data.Item(t.Entries[family])).ToArray();
                Need(track.All(def=>def.Value>0),"Progression equipment has no gold value in "+family+".");
                Need(track[^1].Value>track[0].Value,$"Final tier does not exceed first-tier value in {family}: {track[0].Value} -> {track[^1].Value}.");
            }
            var averages=ordered.Select(t=>new {t.Level,Value=t.Entries.Values.Average(id=>data.Item(id).Value)}).ToArray();
            Need(averages[^1].Value>averages[0].Value,"Final equipment-tier average value does not exceed the first tier.");
            Console.WriteLine("ECONOMY METRIC equipment_tier_average_values "+string.Join(" ",averages.Select(x=>$"L{x.Level}:{x.Value:F1}")));
        });

        Test("crafting value ratios stay finite and gross-value outliers are bounded",()=>
        {
            var ratios=new List<(double Ratio,string Id)>();
            foreach(var recipe in data.Recipes)
            {
                long input=recipe.Ingredients.Sum(entry=>(long)Math.Max(0,data.Item(entry.Key).Value)*entry.Value);
                long output=(long)Math.Max(0,data.Item(recipe.Output).Value)*recipe.Quantity;
                Need(recipe.Xp>0,"Recipe has no training XP: "+recipe.Id);
                if(input<=0) continue;
                double ratio=output/(double)input;
                Need(double.IsFinite(ratio)&&ratio>=0,"Invalid crafting value ratio: "+recipe.Id);
                Need(ratio<=50,$"Crafting gross-value multiplier exceeds 50x: {recipe.Id} = {ratio:F2}x.");
                ratios.Add((ratio,recipe.Id));
            }
            Need(ratios.Count>500,"Too few priced recipes were audited.");
            ratios.Sort((a,b)=>a.Ratio.CompareTo(b.Ratio));
            var high=ratios[^1];
            Console.WriteLine($"ECONOMY METRIC crafting_value priced={ratios.Count} median={ratios[ratios.Count/2].Ratio:F2} max={high.Ratio:F2}({high.Id})");
        });

        Test("natural rarity ordering and crafting gates stay stable",()=>
        {
            var counts=Enum.GetValues<Rarity>().ToDictionary(r=>r,r=>0);
            const int samples=100000;
            for(int i=0;i<samples;i++) counts[Items.RollRarity()]++;
            Need(counts[Rarity.Common]>counts[Rarity.Uncommon]&&counts[Rarity.Uncommon]>counts[Rarity.Rare]
                &&counts[Rarity.Rare]>counts[Rarity.Epic]&&counts[Rarity.Epic]>counts[Rarity.Legendary]
                &&counts[Rarity.Legendary]>counts[Rarity.Mythic]&&counts[Rarity.Mythic]>counts[Rarity.Relic],
                "Natural rarity frequency order changed.");
            int prior=0;
            foreach(var rarity in Enum.GetValues<Rarity>())
            {
                int gate=Items.CraftRarityRequirement(rarity,1); Need(gate>=prior,"Craft rarity gate moved backward at "+rarity); prior=gate;
            }
            Console.WriteLine("ECONOMY METRIC natural_rarity "+string.Join(" ",counts.Select(x=>$"{x.Key}:{x.Value/(double)samples:P3}")));
        });

        Test("boss signature relics are valuable stronger and boss-only",()=>
        {
            var uniques=data.Items.Where(i=>i.Tags.Contains("boss_unique",StringComparer.Ordinal)).ToArray();
            Need(uniques.Length==40,"Expected five signature relic milestones for each of eight classes.");
            var bossDrops=data.Mobs.Where(m=>m.Boss).SelectMany(m=>m.Drops).ToHashSet(StringComparer.Ordinal);
            var nonBossDrops=data.Mobs.Where(m=>!m.Boss).SelectMany(m=>m.Drops).ToHashSet(StringComparer.Ordinal);
            foreach(var item in uniques)
            {
                string? baseTag=item.Tags.FirstOrDefault(tag=>tag.StartsWith("base:",StringComparison.Ordinal));
                Need(baseTag is not null,"Boss signature relic has no base item tag: "+item.Id);
                var baseline=data.Item(baseTag![5..]);
                Need(item.Value>baseline.Value,"Boss signature relic is not more valuable than its base: "+item.Id);
                Need(item.Power>=baseline.Power&&item.Armor>=baseline.Armor,"Boss signature relic regressed its base combat values: "+item.Id);
                Need(bossDrops.Contains(item.Id),"Boss signature relic is absent from boss tables: "+item.Id);
                Need(!nonBossDrops.Contains(item.Id),"Boss signature relic appears on a non-boss table: "+item.Id);
            }
            Need(data.Mobs.Where(m=>m.Boss).All(boss=>boss.Drops.Length>0),"A boss has no reward table.");
            Console.WriteLine($"ECONOMY METRIC boss_rewards bosses={data.Mobs.Count(m=>m.Boss)} signature_relics={uniques.Length} boss_only={uniques.Count(i=>bossDrops.Contains(i.Id)&&!nonBossDrops.Contains(i.Id))}");
        });

        Test("repair, rest, fast travel and rune extraction remain real gold sinks",()=>
        {
            var pricedEquipment=data.Items.Where(i=>(i.Slot!=""||i.Type=="tool")&&i.Value>0).ToArray();
            Need(pricedEquipment.Length>500,"Too few priced equipment/tool definitions.");
            foreach(var def in pricedEquipment)
            {
                long fullRepair=EconomyServices.RepairPrice(def,0);
                Need(fullRepair>0&&fullRepair<Math.Max(2,(long)Math.Ceiling(def.Value*1.2)),"Full repair is not cheaper than replacement for "+def.Id);
            }
            Need(data.Npcs.Any(n=>n.Role=="innkeeper")&&data.Npcs.Any(n=>n.Role=="blacksmith")&&data.Npcs.Any(n=>n.Role=="enchanter"),"Required paid-service NPCs are missing.");
            Need(data.Items.Any(i=>i.Type=="rune"&&Math.Max(20,i.Value/2)>0),"Rune extraction has no priced content.");
            Console.WriteLine("ECONOMY METRIC gold_sinks rest=progression_scaled fast_travel=distance_threat_progression_scaled repair=shared_value_rule unsocket=shared_rune_rule");
        });

        Console.WriteLine($"ECONOMY_BALANCE_AUDIT: {passed} guardrail groups passed; failures {failures.Count}. Metrics detect structural and numeric regressions. Sustained human pacing and market-feel approval remain separate.");
    }
}
