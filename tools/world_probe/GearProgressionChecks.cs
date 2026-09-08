using Kairnfall.Core;
using System.Text.Json;

internal static class GearProgressionChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0, equipmentChecked=0, recipesChecked=0;
        void Need(bool condition,string message) { if(!condition) throw new InvalidOperationException(message); }
        void Test(string name,Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS GEAR: "+name); }
            catch(Exception error) { failures.Add("GEAR: "+name); Console.WriteLine("FAIL GEAR: "+name+": "+error); }
        }
        string Json<T>(T value)=>JsonSerializer.Serialize(value,Wire.Json);
        (RealmEngine,Character) Fixture(string name)
        {
            var engine=new RealmEngine(data);
            var player=engine.CreateCharacter("gear-"+name,"Gear "+name,"vanguard",new());
            player.Inventory.Clear(); player.Equipment.Clear();
            return (engine,player);
        }
        CommandResult Command(RealmEngine engine,string id,string kind,string item="",string target="",int amount=1)
            =>engine.Execute(id,new GameCommand { Kind=kind,Item=item,Target=target,Amount=amount,
                RequestId=Guid.NewGuid().ToString("N"),Sequence=engine.Player(id).LastAction+1 });
        Test("Complete family coverage and skill-level boundaries",()=>
        {
            int[] required=[5,10,15,20,27,35,45,50,55,60,65,70,75,80,85,90,95,100];
            Need(required.All(level=>data.EquipmentTiers.Any(t=>t.Level==level)),"Missing requested tier.");
            Need(EquipmentTierDef.Families.Count==51,"Family coverage changed unexpectedly.");
            var errors=new List<string>(); EquipmentTierDef.Validate(data,errors);
            Need(errors.Count==0,string.Join("; ",errors));
        });
        Test("Every armor weapon offhand and accessory accepts exactly its named skill requirement",()=>
        {
            var (_,p)=Fixture("Boundary");
            foreach(var tier in data.EquipmentTiers)
            foreach(var entry in tier.Entries.Where(x=>!x.Key.StartsWith("tool/",StringComparison.Ordinal)))
            {
                p.Inventory.Clear(); p.Equipment.Clear(); p.SkillXp.Clear();
                var def=data.Item(entry.Value); var item=Items.Create(data,def.Id); Items.Add(p.Inventory,item,data);
                if(entry.Key=="offhand/quiver")
                {
                    var bow=Items.Create(data,"copper_bow"); Items.Add(p.Inventory,bow,data);
                    Items.Equip(p,bow.Id,data);
                }
                if(tier.Level>1)
                {
                    p.SkillXp[def.Skill]=Progression.Threshold(tier.Level-1);
                    bool rejected=false;
                    try { Items.Equip(p,item.Id,data); } catch(RuleException) { rejected=true; }
                    Need(rejected,"Equipment ignored its skill gate: "+def.Id);
                    Need(!Items.Equipped(p,item.Id),"Rejected item became equipped.");
                }
                p.SkillXp[def.Skill]=Progression.Threshold(tier.Level);
                Items.Equip(p,item.Id,data);
                Need(p.Equipment.GetValueOrDefault(def.Slot)==item.Id,"Boundary equip failed: "+def.Id);
                equipmentChecked++;
            }
        });
        Test("Every tier rejects under-level server commands without consuming sequence or changing inventory",()=>
        {
            var (engine,p)=Fixture("Server"); string id=p.Id;
            foreach(var tier in data.EquipmentTiers.Where(t=>t.Level>1))
            {
                p=engine.Player(id); p.Inventory.Clear(); p.Equipment.Clear();
                var def=data.Item(tier.Entries["weapon/sword"]); var item=Items.Create(data,def.Id);
                Items.Add(p.Inventory,item,data); p.SkillXp[def.Skill]=Progression.Threshold(tier.Level-1);
                string before=Json(p);
                var result=Command(engine,id,"equip",item.Id);
                Need(!result.Ok && result.Message.Contains(data.Skill(def.Skill).Name),"Missing useful skill error: "+def.Id);
                Need(Json(engine.Player(id))==before,"Rejected command mutated the character.");
                p=engine.Player(id); p.SkillXp[def.Skill]=Progression.Threshold(tier.Level);
                Need(Command(engine,id,"equip",item.Id).Ok,"Valid server equip failed.");
                Need(engine.Player(id).Equipment["weapon"]==item.Id,"Server did not retain item identity.");
            }
        });
        Test("All tier recipes use real station validation and preserve ingredients on rejected craft",()=>
        {
            var (engine,p)=Fixture("Craft"); string id=p.Id;
            // Keep the fixture small; the unmodified world suites cover the full seeded realm.
            engine.State.Creatures.Clear(); engine.State.Nodes.Clear(); engine.State.Chests.Clear();
            foreach(var tier in data.EquipmentTiers)
            foreach(var output in tier.Entries.Values)
            {
                p=engine.Player(id); p.Inventory.Clear(); p.Equipment.Clear(); p.Cooldowns.Clear(); p.SkillXp.Clear();
                var recipe=data.Recipes.First(r=>r.Output==output);
                var station=data.Npcs.FirstOrDefault(n=>n.Station==recipe.Station);
                Need(station is not null,"Missing real station for "+recipe.Id);
                p.Zone=station!.Zone; p.Position=station.Position;
                foreach(var ingredient in recipe.Ingredients) Items.Add(p.Inventory,Items.Create(data,ingredient.Key,ingredient.Value),data);
                if(recipe.Requirement>1)
                {
                    p.SkillXp[recipe.Skill]=Progression.Threshold(recipe.Requirement-1);
                    string before=Json(p); Need(!Command(engine,id,"craft",recipe.Id).Ok,"Under-level craft passed.");
                    Need(Json(engine.Player(id))==before,"Rejected craft consumed ingredients or sequence."); p=engine.Player(id);
                }
                p.SkillXp[recipe.Skill]=Progression.Threshold(recipe.Requirement);
                var result=Command(engine,id,"craft",recipe.Id);
                Need(result.Ok,recipe.Id+": "+result.Message); p=engine.Player(id);
                Need(p.Inventory.Any(i=>i.Template==output),"Crafted output is absent: "+output);
                Need(recipe.Ingredients.All(i=>Items.Count(p,i.Key)==0),"Ingredient conservation failed: "+recipe.Id);
                recipesChecked++;
            }
        });
        Test("Advanced tools ignore bank storage broken tools locked tools and foreign tool skills",()=>
        {
            var (_,p)=Fixture("Tools");
            var low=data.EquipmentTiers.Single(t=>t.Level==5); var high=data.EquipmentTiers.Single(t=>t.Level==100);
            p.SkillXp["mining"]=Progression.Threshold(5);
            var starter=Items.Create(data,"copper_pickaxe"); var bronze=Items.Create(data,low.Entries["tool/pickaxe"]);
            var top=Items.Create(data,high.Entries["tool/pickaxe"]);
            Items.Add(p.Inventory,starter,data); Items.Add(p.Inventory,top,data); Items.Add(p.Inventory,bronze,data);
            Need(ToolRules.Best(p,data,"pickaxe","mining")?.Id==bronze.Template,"An unlearned tool displaced a usable one.");
            p.Inventory.Reverse(); Need(ToolRules.Best(p,data,"pickaxe","mining")?.Id==bronze.Template,"Inventory order changes selection.");
            p.Inventory.Single(i=>i.Id==bronze.Id).Durability=0;
            Need(ToolRules.Best(p,data,"pickaxe","mining")?.Id==starter.Template,"Broken tool was selected.");
            p.Inventory.Clear(); Items.Add(p.Bank,bronze,data,Items.BankCapacity);
            Need(ToolRules.Best(p,data,"pickaxe","mining") is null,"Bank storage supplied a tool.");
            Items.Add(p.Inventory,Items.Create(data,high.Entries["tool/axe"]),data);
            Need(ToolRules.Best(p,data,"pickaxe","mining") is null,"Wrong tool family was selected.");
        });
        Test("Tool bonuses are finite bounded and do not stack",()=>
        {
            var (_,p)=Fixture("Bonuses"); p.SkillXp["mining"]=Progression.Threshold(100);
            var tier=data.EquipmentTiers.Single(t=>t.Level==100); var tool=data.Item(tier.Entries["tool/pickaxe"]);
            for(int i=0;i<4;i++) Items.Add(p.Inventory,Items.Create(data,tool.Id),data);
            Need(ToolRules.Yield(ToolRules.Best(p,data,"pickaxe","mining"))==20,"Yield stacked or lost its cap.");
            Need(Math.Abs(ToolRules.StaminaCost(tool)-5.1)<.00001,"Stamina reduction differs from advertised value.");
            var invalid=Wire.Copy(tool); invalid.Stats["tool_yield"]=double.NaN; invalid.Stats["tool_efficiency"]=double.PositiveInfinity;
            Need(ToolRules.Yield(invalid)==0 && ToolRules.Efficiency(invalid)==0,"Invalid tool stats escaped finite checks.");
        });
        Test("Authoritative gathering uses the eligible tool and rejects an unlearned replacement",()=>
        {
            var (engine,p)=Fixture("Gather"); string id=p.Id;
            var node=engine.State.Nodes.Values.First(n=>n.Template=="copper_vein");
            p.Zone=node.Zone; p.Position=node.Position; p.Stamina=100;
            var tier=data.EquipmentTiers.Single(t=>t.Level==5);
            var tool=Items.Create(data,tier.Entries["tool/pickaxe"]); Items.Add(p.Inventory,tool,data);
            string before=Json(p); Need(!Command(engine,id,"gather",target:node.Id).Ok,"Unlearned tool bypassed the gate.");
            p=engine.Player(id); Need(Json(p)==before,"Rejected gather mutated resources.");
            p.SkillXp["mining"]=Progression.Threshold(5); double stamina=p.Stamina;
            var result=Command(engine,id,"gather",target:node.Id); Need(result.Ok,result.Message);
            p=engine.Player(id); Need(Math.Abs(p.Stamina-(stamina-ToolRules.StaminaCost(data.Item(tool.Template))))<.00001,"Gather did not use the tool stamina cost.");
            Need(Items.Count(p,"copper_ore")>=1,"Gather did not produce actual ore.");
        });
        Test("Smithing hammers reduce recovery only for smithing and only when learned",()=>
        {
            var (_,p)=Fixture("Hammer"); var tier=data.EquipmentTiers.Single(t=>t.Level==100);
            Items.Add(p.Inventory,Items.Create(data,tier.Entries["tool/hammer"]),data);
            var smith=data.Recipes.First(r=>r.Skill=="smithing"); var tailor=data.Recipes.First(r=>r.Skill=="tailoring");
            Need(ToolRules.CraftRecovery(p,data,smith,10)==5,"Locked hammer provided a benefit.");
            p.SkillXp["smithing"]=Progression.Threshold(100);
            Need(Math.Abs(ToolRules.CraftRecovery(p,data,smith,10)-4.25)<.00001,"Hammer efficiency differs from its stated benefit.");
            Need(ToolRules.CraftRecovery(p,data,tailor,10)==5,"Hammer changed unrelated crafting.");
        });
        Test("Every tier can retain a complete equipment set through serialization",()=>
        {
            var (engine,p)=Fixture("Saves");
            foreach(var tier in data.EquipmentTiers)
            {
                p.Inventory.Clear(); p.Equipment.Clear(); p.Bank.Clear();
                foreach(var skill in data.Skills) p.SkillXp[skill.Id]=Progression.Threshold(100);
                foreach(var id in tier.Entries.Values.Distinct()) Items.Add(p.Inventory,Items.Create(data,id),data);
                foreach(var key in new[]{"weapon/sword","offhand/shield","accessory/ring","accessory/necklace","accessory/charm","accessory/trinket"}.Concat(EquipmentTierDef.ArmorSlots.Select(s=>"armor/heavy/"+s)))
                {
                    var item=p.Inventory.Single(i=>i.Template==tier.Entries[key]); Items.Equip(p,item.Id,data);
                }
                var copy=Wire.Copy(p); Need(Json(copy)==Json(p),"Tier roundtrip changed IDs, stats or equipment.");
                Need(Items.Validate(engine.State,data).Count==0,"Tier creates invalid ownership state.");
                Need(double.IsFinite(CombatMath.Stats(copy,data).Armor),"Tier stats are not finite.");
            }
        });
        Test("Catalog validation rejects missing families and wrong requirement records",()=>
        {
            var copy=Wire.Copy(data); copy.EquipmentTiers[0].Entries.Remove("weapon/sword");
            Need(copy.Validate().Any(e=>e.Contains("equipment tier",StringComparison.OrdinalIgnoreCase)),"Incomplete tier accepted.");
            copy=Wire.Copy(data); copy.EquipmentTiers[1].Entries["weapon/sword"]="copper_sword";
            Need(copy.Validate().Any(e=>e.Contains("equipment tier",StringComparison.OrdinalIgnoreCase)),"Wrong-level tier accepted.");
        });
        Console.WriteLine($"GEAR PROGRESSION CONTRACT: {passed} groups passed; {equipmentChecked} equip boundaries; {recipesChecked} authoritative crafting paths; total probe failures {failures.Count}.");
    }
}
