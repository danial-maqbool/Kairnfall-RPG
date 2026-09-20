using Kairnfall.Core;

internal static class EconomyCraftingFeelChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check){try{check();passed++;Console.WriteLine("PASS ECONOMY CRAFTING: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL ECONOMY CRAFTING: "+name+": "+e.Message);}}

        Test("progression equipment recipes use grade materials and fair base values",()=>
        {
            int checkedGear=0;var ratios=new List<double>();
            foreach(var tier in data.EquipmentTiers)
            foreach(var entry in tier.Entries)
            {
                var recipe=CraftEconomy.RecipeForOutput(data,entry.Value);Need(recipe is not null,"Missing recipe for "+entry.Value);
                long input=CraftEconomy.RecipeInputValue(data,recipe!),output=CraftEconomy.RecipeOutputValue(data,recipe!);Need(input>0,"Zero material value: "+recipe!.Id);
                double ratio=output/(double)input;ratios.Add(ratio);checkedGear++;
                Need(ratio>=1.0&&ratio<=1.30,$"Gear value no longer tracks materials: {recipe.Id} {ratio:F2}x.");
                if(tier.Level>1&&entry.Key.StartsWith("armor/medium/",StringComparison.Ordinal))
                    Need(recipe.Ingredients.Keys.Any(x=>x.EndsWith("_treated_leather",StringComparison.Ordinal)),"High-tier medium armor still uses starter leather: "+recipe.Id);
                if(tier.Level>1&&entry.Key.StartsWith("armor/heavy/",StringComparison.Ordinal))
                    Need(recipe.Ingredients.Keys.Any(x=>x.EndsWith("_treated_leather",StringComparison.Ordinal)),"High-tier heavy armor has no matching hide fitting: "+recipe.Id);
            }
            Need(checkedGear>900,"Too few tier recipes checked.");
            foreach(var recipe in data.Recipes.Where(r=>r.Quantity==1))
            {
                var output=data.Item(recipe.Output);
                if(output.Type!="armor"||output.Requirement<=1||!output.Tags.Any(x=>x is "medium" or "heavy"))continue;
                Need(!recipe.Ingredients.ContainsKey("cured_leather"),"High-tier legacy armor still consumes starter cured leather: "+recipe.Id);
            }
            Console.WriteLine($"ECONOMY CRAFTING METRIC gear_recipes={checkedGear} ratio_min={ratios.Min():F2} ratio_median={ratios.Order().ElementAt(ratios.Count/2):F2} ratio_max={ratios.Max():F2}");
        });

        Test("common vendor ingredients cannot be converted into guaranteed merchant profit",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("economy-loop","Market Auditor","vanguard",new());
            p.SkillXp["bartering"]=Progression.Threshold(100);foreach(var faction in data.Npcs.Select(x=>x.Faction).Where(x=>x!="").Distinct())p.Reputation[faction]=1000;
            int audited=0;
            foreach(var recipe in data.Recipes)
            {
                long inputCost=0;bool purchasable=true;
                foreach(var ingredient in recipe.Ingredients)
                {
                    var def=data.Item(ingredient.Key);var sellers=data.Npcs.Where(n=>n.Stock.Contains(def.Id)).ToArray();
                    if(sellers.Length==0){purchasable=false;break;}
                    inputCost=checked(inputCost+sellers.Min(n=>realm.BuyPrice(p,n,def))*ingredient.Value);
                }
                if(!purchasable)continue;
                var output=data.Item(recipe.Output);var buyers=data.Npcs.Where(n=>MerchantSales.Accepts(n,output,data)).ToArray();if(buyers.Length==0)continue;
                var instance=Items.Create(data,output.Id,1,Rarity.Common,p);long sale=buyers.Max(n=>MerchantSales.UnitPrice(p,n,instance,data))*recipe.Quantity;
                Need(sale<inputCost,$"Guaranteed vendor craft arbitrage: {recipe.Id} buy inputs {inputCost}, sell common output {sale}.");audited++;
            }
            Need(audited>=10,"Too few fully vendor-supplied crafting loops audited.");
            Console.WriteLine("ECONOMY CRAFTING METRIC vendor_craft_loops="+audited);
        });

        Test("specialists Bartering reputation and quality improve sale quotes without buyback arbitrage",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("economy-sales","Sale Auditor","vanguard",new());
            var merchant=data.Npcs.First(n=>n.Role!="provisioner"&&n.Stock.Any(id=>data.Item(id).Value>=20));var def=data.Item(merchant.Stock.First(id=>data.Item(id).Value>=20));
            var item=Items.Create(data,def.Id,1,Rarity.Epic,p);long basePrice=MerchantSales.UnitPrice(def);
            p.SkillXp["bartering"]=Progression.Threshold(100);p.Reputation[merchant.Faction]=1000;
            long quote=MerchantSales.UnitPrice(p,merchant,item,data),buy=realm.BuyPrice(p,merchant,def);
            Need(quote>basePrice,"Skill/specialist/quality did not improve the sale quote.");Need(quote<buy,"Improved sell quote reached merchant buy price.");
            p.Zone=merchant.Zone;p.Position=merchant.Position;p.Gold=0;Items.Add(p.Inventory,item,data);long expected=MerchantSales.Quote(p,merchant,item,1,data);
            var result=realm.Execute(p.Id,new GameCommand{Kind="sell",Target=merchant.Id,Item=item.Id,Amount=1,Sequence=p.LastAction+1});
            Need(result.Ok&&p.Gold==expected,"Authoritative sale did not use displayed quote.");
        });

        Test("service sinks remain gentle early and scale into late progression",()=>
        {
            var realm=new RealmEngine(data);var low=realm.CreateCharacter("economy-low","Low Traveler","vanguard",new());
            long earlyRest=EconomyServices.RestPrice(low);
            foreach(var skill in data.Skills)low.SkillXp[skill.Id]=Progression.Threshold(100);
            long lateRest=EconomyServices.RestPrice(low);Need(earlyRest==5&&lateRest>earlyRest,"Inn rest did not scale from the early-game floor.");
            var settlements=data.Zones.Where(z=>z.Kind is "city" or "settlement").ToArray();var source=settlements.OrderBy(z=>z.Level).First();var near=settlements.OrderBy(z=>Math.Abs(z.WorldX-source.WorldX)+Math.Abs(z.WorldY-source.WorldY)).Skip(1).First();var far=settlements.OrderByDescending(z=>Math.Abs(z.WorldX-source.WorldX)+Math.Abs(z.WorldY-source.WorldY)+z.Level).First();
            long nearCost=EconomyServices.TravelPrice(data,low,source,near),farCost=EconomyServices.TravelPrice(data,low,source,far);Need(farCost>=nearCost&&nearCost>=15,"Travel cost does not reflect route/progression.");
            Need(EconomyServices.RepairPrice(data.Items.First(x=>x.Slot!=""),50)>0,"Repair sink disappeared.");
            Console.WriteLine($"ECONOMY CRAFTING METRIC rest_early={earlyRest} rest_late={lateRest} travel_near={nearCost} travel_far={farCost}");
        });

        Test("reclaiming gear is useful lossy station-bound and replay-safe",()=>
        {
            var recipe=data.Recipes.First(r=>data.Item(r.Output).Slot!=""&&CraftEconomy.Reclaim(data,Items.Create(data,r.Output)) is not null);
            var plan=CraftEconomy.Reclaim(data,Items.Create(data,recipe.Output))!;Need(plan.RecoveredValue>0&&plan.RecoveredValue*2<=plan.InputValue,"Reclaim exceeds half of recipe material value.");
            var stationNpc=data.Npcs.FirstOrDefault(n=>n.Station==plan.Recipe.Station);Need(stationNpc is not null,"No NPC station for reclaim fixture: "+plan.Recipe.Station);
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("economy-reclaim","Reclaim Tester","vanguard",new());p.Zone=stationNpc!.Zone;p.Position=stationNpc.Position;
            var gear=Items.Create(data,recipe.Output);Items.Add(p.Inventory,gear,data);int before=Items.Count(p,plan.Material);
            var command=new GameCommand{Kind="salvage",Item=gear.Id,Sequence=p.LastAction+1};var result=realm.Execute(p.Id,command);Need(result.Ok,"Reclaim rejected: "+result.Message);
            Need(p.Inventory.All(x=>x.Id!=gear.Id)&&Items.Count(p,plan.Material)==before+plan.Quantity,"Reclaim did not exchange gear for exact preview materials.");
            int after=Items.Count(p,plan.Material);var replay=realm.Execute(p.Id,command);Need(replay.Ok&&Items.Count(p,plan.Material)==after,"Replayed reclaim duplicated materials.");
            var remote=Items.Create(data,recipe.Output);Items.Add(p.Inventory,remote,data);p.Position=new Point(stationNpc.Position.X+20,stationNpc.Position.Y+20);
            var rejected=realm.Execute(p.Id,new GameCommand{Kind="salvage",Item=remote.Id,Sequence=p.LastAction+1});Need(!rejected.Ok&&p.Inventory.Any(x=>x.Id==remote.Id),"Remote reclaim consumed gear.");
        });

        Test("craft quality guidance exposes progression without changing rarity gates",()=>
        {
            var recipe=data.Recipes.First(r=>data.Item(r.Output).StackMax==1);var p=new Character();foreach(var skill in data.Skills)p.SkillXp[skill.Id]=0;
            string hint=CraftEconomy.QualityHint(p,recipe,data);Need(hint.Contains("next quality gate",StringComparison.Ordinal),"Crafting UI has no quality progression hint.");
            int previous=0;foreach(var rarity in Enum.GetValues<Rarity>()){int gate=Items.CraftRarityRequirement(rarity,recipe.Requirement);Need(gate>=previous,"Rarity gate order changed.");previous=gate;}
        });

        Console.WriteLine($"ECONOMY_CRAFTING_FEEL: {passed} groups passed; failures {failures.Count}.");
    }
}
