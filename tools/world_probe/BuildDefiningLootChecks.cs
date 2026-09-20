using Kairnfall.Core;
using System.Text.Json;

public static class BuildDefiningLootChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check)
        {
            try{check();passed++;Console.WriteLine("PASS BUILD LOOT: "+name);}
            catch(Exception error){failures.Add("build loot: "+name);Console.WriteLine("FAIL BUILD LOOT: "+name+": "+error.Message);}
        }
        string Json<T>(T value)=>JsonSerializer.Serialize(value,Wire.Json);
        void Train(Character p,string skill,int level)=>p.SkillXp[skill]=Progression.Threshold(Math.Clamp(level,1,100));
        Item Equip(Character p,ItemDef def)
        {
            if(def.Skill!="") Train(p,def.Skill,BeginnerProgression.EquipmentRequirement(def));
            var item=Items.Create(data,def.Id);Items.Add(p.Inventory,item,data);Items.Equip(p,item.Id,data);return item;
        }

        Test("authored behavior spans unique weapons, offhands, runes, sets and conditional affixes",()=>
        {
            var uniques=data.Items.Where(x=>x.Tags.Contains("boss_unique",StringComparer.Ordinal)).ToArray();
            Need(uniques.Length==40&&uniques.All(x=>BuildDefiningLoot.KnownEffect(x.Effect)),"Boss signatures are not fully authored.");
            Need(data.Items.Where(x=>x.Type=="offhand").All(x=>BuildDefiningLoot.KnownEffect(x.Effect)),"An offhand is still stat-only.");
            Need(data.Items.Count(x=>x.Type=="rune"&&BuildDefiningLoot.KnownEffect(x.Effect))>=20,"Too few runes have transformations.");
            Need(BuildDefiningLoot.Sets.Count==3&&BuildDefiningLoot.Sets.Keys.All(id=>data.Items.Count(x=>x.Tags.Contains("set:"+id,StringComparer.Ordinal))==3),"Micro-set authoring is incomplete.");
            Need(BuildDefiningLoot.RollConditionalAffix(data.Items.First(x=>x.Type=="weapon"&&!x.Tags.Contains("boss_unique",StringComparer.Ordinal)),Rarity.Rare) is { } affix&&BuildDefiningLoot.IsEffectAffix(affix),"Rare equipment has no conditional affix family.");
        });

        Test("every named boss unique has one real authored boss source",()=>
        {
            foreach(var item in data.Items.Where(x=>x.Tags.Contains("boss_unique",StringComparer.Ordinal)))
            {
                var sources=data.Mobs.Where(x=>x.Boss&&x.Drops.Contains(item.Id,StringComparer.Ordinal)).ToArray();
                Need(sources.Length==1,item.Id+" must resolve to exactly one boss source.");
                Need(BuildDefiningLoot.TooltipLines(new Item{Template=item.Id,Rarity=Rarity.Relic},item,data).Any(x=>x.Contains(sources[0].Name,StringComparison.Ordinal)),item.Id+" source is not readable in its tooltip.");
            }
        });

        Test("unique and set effect resolution is deterministic",()=>
        {
            var def=data.Items.First(x=>x.Tags.Contains("boss_unique",StringComparer.Ordinal));
            var item=Items.Create(data,def.Id,1,Rarity.Relic);
            string first=string.Join("\n",BuildDefiningLoot.TooltipLines(item,def,data));
            string second=string.Join("\n",BuildDefiningLoot.TooltipLines(Wire.Copy(item),def,data));
            Need(first==second&&first.Contains("SIGNATURE EFFECT",StringComparison.Ordinal),"Unique effect resolution changed across a copy.");
            foreach(var set in BuildDefiningLoot.Sets) Need(data.Items.Count(x=>x.Tags.Contains("set:"+set.Key,StringComparer.Ordinal))==3,set.Key+" piece map changed.");
        });

        Test("class-resource gear only activates its intended class engine",()=>
        {
            var def=data.Items.First(x=>x.Tags.Contains("boss_unique",StringComparer.Ordinal)&&x.Tags.Contains("class:vanguard",StringComparer.Ordinal));
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("build-class","Build Class","vanguard",new());
            Equip(p,def);p.ClassResource=ClassCombatRules.ReadyThreshold("vanguard");
            Need(BuildDefiningLoot.ClassSynergyActive(p,def),"Vanguard relic did not recognize Resolve READY.");
            double readyArmor=CombatMath.Stats(p,data).Armor;p.ClassResource=0;double idleArmor=CombatMath.Stats(p,data).Armor;
            Need(readyArmor>idleArmor,"Resolve READY produces no relic gameplay change.");
            p.Class="ranger";p.ClassResource=100;
            Need(!BuildDefiningLoot.ClassSynergyActive(p,def),"Vanguard relic activated the Ranger class engine.");
            double resource=p.ClassResource;_ = BuildDefiningLoot.AbilityElement(p,data.Abilities.First(x=>x.Kind=="strike"),data);
            Need(p.ClassResource==resource,"Loot transformation consumed class resource outside native class rules.");
        });

        Test("off-class boss equipment remains legal when its skill requirement is met",()=>
        {
            var def=data.Items.First(x=>x.Tags.Contains("boss_unique",StringComparer.Ordinal)&&x.Tags.Contains("class:vanguard",StringComparer.Ordinal));
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("build-offclass","Offclass Hero","ranger",new());
            var item=Equip(p,def);
            Need(Items.Equipped(p,item.Id),"Off-class signature equipment was prohibited.");
        });

        Test("micro-set bonuses activate at two and three pieces and deactivate when removed",()=>
        {
            var pieces=data.Items.Where(x=>x.Tags.Contains("set:roadwarden",StringComparer.Ordinal)).ToArray();
            Need(pieces.Length==3&&pieces.Select(x=>x.Slot).Distinct().Count()==3,"Roadwarden pieces collide in one slot.");
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("build-set","Set Hero","vanguard",new());
            var equipped=pieces.Select(x=>Equip(p,x)).ToArray();
            Need(BuildDefiningLoot.SetPieceCount(p,"roadwarden",data)==3,"Three-piece set did not activate.");
            double full=CombatMath.Stats(p,data).Armor;
            Items.Unequip(p,pieces[2].Slot,data);
            Need(BuildDefiningLoot.SetPieceCount(p,"roadwarden",data)==2,"Set did not fall back to two pieces.");
            double two=CombatMath.Stats(p,data).Armor;Need(full>two,"Three-piece set bonus did not deactivate.");
            Items.Unequip(p,pieces[1].Slot,data);Need(BuildDefiningLoot.SetPieceCount(p,"roadwarden",data)==1,"Two-piece set did not deactivate.");
        });

        Test("rune element transformation is bounded and deterministic",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("build-rune","Rune Hero","spellblade",new());
            var weapon=p.Inventory.First(x=>Items.Equipped(p,x.Id)&&data.Item(x.Template).Slot=="weapon");weapon.Sockets=2;
            weapon.Runes.Add(new(){Template="rune_storm_5"});weapon.Runes.Add(new(){Template="rune_embers_5"});
            var ability=data.Abilities.First(x=>(x.Kind is "strike" or "projectile" or "area")&&x.Element!=Element.Physical);
            double before=p.ClassResource;var one=BuildDefiningLoot.AbilityElement(p,ability,data);var two=BuildDefiningLoot.AbilityElement(p,ability,data);
            Need(one==two&&one is Element.Fire or Element.Lightning,"Rune conversion is order/proc dependent.");
            Need(p.ClassResource==before,"Rune conversion mutated class resource.");
            weapon.Runes.RemoveAt(0);Need(BuildDefiningLoot.AbilityElement(p,ability,data)==Element.Fire,"Single Ember transform did not resolve to Fire.");
        });

        Test("crafting specialization choices obey crafting-skill requirements",()=>
        {
            var recipe=data.Recipes.First(x=>data.Item(x.Output).Slot!=""&&x.Requirement>=20&&x.Requirement<=70);
            var choices=BuildDefiningLoot.CraftSpecializations(recipe,data);var choice=choices.First(x=>x.Id=="resource");
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("build-craft","Craft Hero","arcanist",new());
            Train(p,recipe.Skill,Math.Max(1,choice.Requirement-1));
            Need(BuildDefiningLoot.CraftSpecializationProblem(p,recipe,choice.Id,data)!="","Under-skilled specialization was accepted.");
            Train(p,recipe.Skill,choice.Requirement);
            Need(BuildDefiningLoot.CraftSpecializationProblem(p,recipe,choice.Id,data)=="","Qualified specialization was rejected.");
            var item=Items.Create(data,recipe.Output);int before=item.Affixes.Count;BuildDefiningLoot.ApplyCraftSpecialization(item,p,recipe,choice.Id,data);
            Need(item.Affixes.Count==before+1&&item.Affixes.Any(a=>a.Name.StartsWith("Crafted:",StringComparison.Ordinal)&&BuildDefiningLoot.IsEffectAffix(a)),"Crafted choice was not persisted on the item.");
        });

        Test("reforge spends value once, preserves affix count, and reclaim stays lossy",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("build-reforge","Reforge Hero","vanguard",new());
            var enchanter=data.Npcs.First(x=>x.Role=="enchanter");p.Zone=enchanter.Zone;p.Position=enchanter.Position;p.Gold=100000;
            Items.Add(p.Inventory,Items.Create(data,"rune_dust",20),data);
            var def=data.Items.First(x=>x.Slot!=""&&!x.Tags.Contains("boss_unique",StringComparer.Ordinal)&&data.Recipes.Any(r=>r.Output==x.Id));
            var gear=Items.Create(data,def.Id,1,Rarity.Rare);gear.Affixes.Clear();gear.Affixes.Add(new(){Name="strength",Stat="strength",Value=3});gear.Affixes.Add(new(){Name="vitality",Stat="vitality",Value=3});Items.Add(p.Inventory,gear,data);
            int count=gear.Affixes.Count,dust=Items.Count(p,"rune_dust");long gold=p.Gold;double quality=MerchantSales.QualityMultiplier(gear);
            var command=new GameCommand{Kind="reforge",Item=gear.Id,Amount=0,Sequence=p.LastAction+1,RequestId=Guid.NewGuid().ToString("N")};
            var result=realm.Execute(p.Id,command);Need(result.Ok,"Reforge rejected: "+result.Message);
            Need(gear.Affixes.Count==count&&Items.Count(p,"rune_dust")<dust&&p.Gold<gold,"Reforge duplicated value or changed affix count.");
            Need(Math.Abs(MerchantSales.QualityMultiplier(gear)-quality)<.0001,"Reforge increased merchant quality multiplier.");
            int afterDust=Items.Count(p,"rune_dust");long afterGold=p.Gold;var replay=realm.Execute(p.Id,command);
            Need(replay.Ok&&Items.Count(p,"rune_dust")==afterDust&&p.Gold==afterGold,"Replayed reforge spent or granted resources twice.");
            var reclaim=CraftEconomy.Reclaim(data,gear);Need(reclaim is not null,"Craftable gear lost reclaim route after reforge.");
            long input=CraftEconomy.RecipeInputValue(data,reclaim!.Recipe);long returned=data.Item(reclaim.Material).Value*reclaim.Quantity;
            Need(returned<input*.5,"Reforge made reclaim non-lossy.");
        });

        Test("save and load preserve build-defining instance state",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("build-save","Save Hero","ranger",new());
            var def=data.Items.First(x=>x.Slot=="weapon"&&!x.Tags.Contains("boss_unique",StringComparer.Ordinal));var item=Items.Create(data,def.Id,1,Rarity.Rare);
            item.Affixes.Add(new(){Name="Crafted: Execution finish",Stat="effect:execute",Value=1});item.Sockets=Math.Max(1,item.Sockets);item.Runes.Add(new(){Template="rune_embers_1"});Items.Add(p.Inventory,item,data);
            string before=Json(item);var loaded=new RealmEngine(data,Wire.Copy(realm.State));var restored=loaded.Player(p.Id).Inventory.First(x=>x.Id==item.Id);
            Need(before==Json(restored),"Save/load stripped a special affix or rune transformation.");
        });

        Test("bank, auction and item transfer serialization retain special properties",()=>
        {
            var def=data.Items.First(x=>x.Slot=="weapon"&&!x.Tags.Contains("boss_unique",StringComparer.Ordinal));var item=Items.Create(data,def.Id,1,Rarity.Rare);item.Affixes.Add(new(){Name="Crafted: Class-engine finish",Stat="effect:resource_ready",Value=1});item.Sockets=Math.Max(1,item.Sockets);item.Runes.Add(new(){Template="rune_storm_1"});
            var bank=Wire.Copy(new List<Item>{item})[0];var auction=Wire.Copy(new Auction{Item=item}).Item;
            Need(Json(bank)==Json(item)&&Json(auction)==Json(item),"Bank or auction serialization stripped special item state.");
            var owner=new Character();owner.Inventory.Add(Wire.Copy(item));var moved=Items.Take(owner.Inventory,item.Id,1);var recipient=new Character();Items.Add(recipient.Inventory,moved,data);
            Need(Json(recipient.Inventory.Single())==Json(item),"Trade-style item transfer stripped special state.");
        });

        Test("merchant pricing remains bounded under specialization and reforge",()=>
        {
            var recipe=data.Recipes.First(x=>data.Item(x.Output).Slot!=""&&x.Requirement>=20&&x.Requirement<=60);var def=data.Item(recipe.Output);
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("build-market","Market Hero","vanguard",new());var choice=BuildDefiningLoot.CraftSpecializations(recipe,data).First(x=>x.Id=="offense");Train(p,recipe.Skill,choice.Requirement);
            var item=Items.Create(data,def.Id,1,Rarity.Common);BuildDefiningLoot.ApplyCraftSpecialization(item,p,recipe,choice.Id,data);
            Need(MerchantSales.QualityMultiplier(item)<=1.03,"Craft specialization created an excessive resale multiplier.");
            Need(MerchantSales.UnitPrice(def)*MerchantSales.QualityMultiplier(item)<Math.Max(1,def.Value),"Specialized common gear sells above its authored base value.");
            if(item.Affixes.Count<2)item.Affixes.Add(new(){Name="vitality",Stat="vitality",Value=2});
            double before=MerchantSales.QualityMultiplier(item);int index=item.Affixes.FindIndex(BuildDefiningLoot.CanReforgeAffix);Need(index>=0,"No reforge candidate available.");BuildDefiningLoot.RerollAffix(item,index,def);
            Need(MerchantSales.QualityMultiplier(item)==before,"Reforge changed affix-count resale quality.");
        });

        Test("client item card and comparison surface authored special effects",()=>
        {
            string card=File.ReadAllText(Path.Combine("client","Scripts","CompactItemCard.cs"));
            Need(card.Contains("BuildDefiningLoot.TooltipLines",StringComparison.Ordinal)&&card.Contains("ItemBuildEffect",StringComparison.Ordinal),"Compact/full item cards do not render build effects.");
            string comparison=File.ReadAllText(Path.Combine("src","Kairnfall.Core","EquipmentComparison.cs"));
            Need(comparison.Contains("BuildDefiningLoot.IsEffectAffix",StringComparison.Ordinal),"Comparison table still treats effect IDs as numeric stats.");
        });

        Test("special item asset paths remain authored and unchanged",()=>
        {
            var affected=data.Items.Where(x=>x.Tags.Contains("boss_unique",StringComparer.Ordinal)||x.Tags.Any(t=>t.StartsWith("set:",StringComparison.Ordinal))||x.Type=="offhand"||BuildDefiningLoot.KnownEffect(x.Effect)).ToArray();
            Need(affected.Length>60,"Asset coverage sample is unexpectedly small.");
            foreach(var item in affected)
            {
                Need(item.Icon.StartsWith("items/",StringComparison.Ordinal)&&item.Icon.EndsWith(".png",StringComparison.Ordinal),item.Id+" changed its deterministic item-icon contract.");
                Need(!item.Icon.Contains("..",StringComparison.Ordinal)&&item.Icon==item.Icon.ToLowerInvariant(),item.Id+" has an unstable icon path.");
            }
        });

        Test("offhand identities remain mutually distinct without changing compatibility rules",()=>
        {
            var families=new[]{"shield","focus","quiver","orb"};
            var effects=families.Select(f=>data.Items.First(x=>x.Type=="offhand"&&x.Tags.Contains(f,StringComparer.Ordinal)).Effect).ToArray();
            Need(effects.Distinct(StringComparer.Ordinal).Count()==families.Length,"Offhand families share the same build identity.");
            var quiver=data.Items.First(x=>x.Type=="offhand"&&x.Tags.Contains("quiver",StringComparer.Ordinal));var bow=data.Items.First(x=>x.Type=="weapon"&&x.Tags.Contains("bow",StringComparer.Ordinal));var sword=data.Items.First(x=>x.Type=="weapon"&&x.Tags.Contains("sword",StringComparer.Ordinal));
            Need(HandEquipment.Compatible(bow,quiver)&&!HandEquipment.Compatible(sword,quiver),"Build pass regressed quiver compatibility.");
        });

        Console.WriteLine($"BUILD DEFINING LOOT: {passed}/15 groups passed.");
    }
}
