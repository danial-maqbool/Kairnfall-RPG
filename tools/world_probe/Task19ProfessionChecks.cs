using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Kairnfall.Core;

internal static class Task19ProfessionChecks
{
    private sealed record Chain(string Zone,string Resource,string Gather,string ProcessRecipe,string Processed,string ToolRecipe,string Tool,string Skill,int Requirement,double Respawn);
    private static readonly Chain[] Chains =
    [
        new("old_boughs","heartwood_stand","heartwood_burl","season_heartwood","seasoned_heartwood","make_heartwood_forester_axe","heartwood_forester_axe","woodcutting",35,480),
        new("mosswater","ghost_reed_patch","ghost_reed","distill_ghost_reed","ghost_reed_extract","make_ghost_reed_sickle","ghost_reed_sickle","herbalism",35,420),
        new("gull_isles","moonfin_pool","moonfin","press_moonfin_oil","moonfin_oil","make_moonfin_rod","moonfin_rod","fishing",40,360),
        new("glassmere","frostsilver_vein","frostsilver_ore","smelt_frostsilver","frostsilver_bar","make_frostsilver_pickaxe","frostsilver_pickaxe","mining",55,600)
    ];

    [ModuleInitializer]
    internal static void VerifyTask19Professions()
    {
        const string catalogPath="content/catalog.json";
        if(!File.Exists(catalogPath))throw new InvalidDataException("Task 19 checks require content/catalog.json.");
        var data=Catalog.Load(catalogPath);var failures=new List<string>();int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Check(string name,Action body){try{body();passed++;Console.WriteLine("PASS TASK19 PROFESSIONS: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL TASK19 PROFESSIONS: "+name+": "+e.Message);}}
        GameCommand Command(Character p,string kind,string target="",string item="",int amount=1,string arg="")
            =>new(){Kind=kind,Target=target,Item=item,Amount=amount,Arg=arg,Sequence=p.LastAction+1,RequestId=Guid.NewGuid().ToString("N")};
        void Train(Character p,string skill,int level)=>p.SkillXp[skill]=Math.Max(p.SkillXp.GetValueOrDefault(skill),Progression.Threshold(level));
        NpcDef Station(string station)=>data.Npcs.First(n=>n.Station==station);
        void Place(Character p,NpcDef station){p.Zone=station.Zone;p.Position=station.Position;}

        Check("rare resources reuse four existing regions without enlarging the overworld",()=>
        {
            var surface=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").ToArray();
            Need(surface.Length==20&&surface.Sum(z=>(long)z.Width*z.Height)==2_048_000,"Task 19 changed the established surface footprint.");
            var realm=new RealmEngine(data);
            foreach(var chain in Chains)
            {
                var zone=data.Zone(chain.Zone);var resource=data.Resource(chain.Resource);
                Need(zone.Resources.Count(id=>id==chain.Resource)==1,chain.Resource+" is not assigned to exactly one regional resource table.");
                Need(resource.Item==chain.Gather&&resource.Skill==chain.Skill&&Math.Abs(resource.Respawn-chain.Respawn)<.001,chain.Resource+" definition drifted.");
                Need(resource.Respawn>=300,chain.Resource+" respawns too quickly for a rare shared node.");
                var nodes=realm.State.Nodes.Values.Where(n=>n.Template==chain.Resource).ToArray();
                Need(nodes.Length==3,chain.Resource+" should have exactly three deterministic shared nodes in its one source region.");
                Need(nodes.All(n=>n.Zone==chain.Zone&&WorldMap.Fits(zone,n.Position)),chain.Resource+" seeded outside its authored reachable region.");
            }
        });

        Check("rare gathering is authoritative replay safe and restart persistent",()=>
        {
            var chain=Chains[0];var realm=new RealmEngine(data);var first=realm.CreateCharacter("task19-gather-a","Gather Tester A","vanguard",new());var second=realm.CreateCharacter("task19-gather-b","Gather Tester B","vanguard",new());
            Train(first,chain.Skill,chain.Requirement);Train(second,chain.Skill,chain.Requirement);first.Stamina=second.Stamina=100;
            var node=realm.State.Nodes.Values.First(n=>n.Template==chain.Resource);first.Zone=second.Zone=node.Zone;first.Position=second.Position=node.Position;
            int firstBefore=Items.Count(first,chain.Gather),secondBefore=Items.Count(second,chain.Gather);long xpBefore=first.SkillXp[chain.Skill];
            var command=Command(first,"gather",node.Id);var result=realm.Execute(first.Id,command);Need(result.Ok,"Rare gather failed: "+result.Message);
            first=realm.Player(first.Id);node=realm.State.Nodes[node.Id];int firstAfter=Items.Count(first,chain.Gather);
            Need(firstAfter>firstBefore&&first.SkillXp[chain.Skill]>xpBefore,"Rare gather granted neither material nor profession XP.");
            Need(Math.Abs((node.ReadyAt-realm.State.Time)-chain.Respawn)<.001,"Rare node did not enter its controlled respawn window.");
            var replay=realm.Execute(first.Id,command);Need(replay.Ok&&Items.Count(realm.Player(first.Id),chain.Gather)==firstAfter,"Replayed gather duplicated rare material.");
            var contested=realm.Execute(second.Id,Command(second,"gather",node.Id));Need(!contested.Ok&&Items.Count(realm.Player(second.Id),chain.Gather)==secondBefore,"A second player harvested a recovering rare node.");
            double ready=node.ReadyAt;var saved=Wire.Copy(realm.State);var restarted=new RealmEngine(data,saved);var restored=restarted.State.Nodes[node.Id];
            Need(Math.Abs(restored.ReadyAt-ready)<.001&&restored.ReadyAt>restarted.State.Time,"Restart lost rare-node recovery state.");
        });

        Check("processing and specialty crafting consume exact quantities and replay once",()=>
        {
            var chain=Chains[0];var realm=new RealmEngine(data);var player=realm.CreateCharacter("task19-craft","Profession Crafter","vanguard",new());
            var process=data.Recipe(chain.ProcessRecipe);Train(player,process.Skill,process.Requirement);var station=Station(process.Station);Place(player,station);player.Stamina=100;
            foreach(var ingredient in process.Ingredients)Items.Add(player.Inventory,Items.Create(data,ingredient.Key,ingredient.Value*2),data);
            var beforeInputs=process.Ingredients.ToDictionary(x=>x.Key,x=>Items.Count(player,x.Key));int beforeOutput=Items.Count(player,process.Output);
            var processCommand=Command(player,"craft",item:process.Id,amount:2);var processed=realm.Execute(player.Id,processCommand);Need(processed.Ok,"Rare processing failed: "+processed.Message);player=realm.Player(player.Id);
            foreach(var ingredient in process.Ingredients)Need(Items.Count(player,ingredient.Key)==beforeInputs[ingredient.Key]-ingredient.Value*2,"Processing consumed the wrong "+ingredient.Key+" quantity.");
            Need(Items.Count(player,process.Output)==beforeOutput+process.Quantity*2,"Processing output count is wrong.");
            int afterProcess=Items.Count(player,process.Output);var replay=realm.Execute(player.Id,processCommand);Need(replay.Ok&&Items.Count(realm.Player(player.Id),process.Output)==afterProcess,"Replayed processing duplicated output.");

            player=realm.Player(player.Id);var toolRecipe=data.Recipe(chain.ToolRecipe);Train(player,toolRecipe.Skill,toolRecipe.Requirement);player.Cooldowns["craft"]=0;Place(player,Station(toolRecipe.Station));
            foreach(var ingredient in toolRecipe.Ingredients)
            {
                int missing=Math.Max(0,ingredient.Value-Items.Count(player,ingredient.Key));if(missing>0)Items.Add(player.Inventory,Items.Create(data,ingredient.Key,missing),data);
            }
            int beforeTool=Items.Count(player,toolRecipe.Output);var made=realm.Execute(player.Id,Command(player,"craft",item:toolRecipe.Id));Need(made.Ok,"Specialty tool craft failed: "+made.Message);player=realm.Player(player.Id);
            Need(Items.Count(player,toolRecipe.Output)==beforeTool+1,"Specialty tool was not created exactly once.");
            Train(player,chain.Skill,data.Item(chain.Tool).Requirement);
            Need(ToolRules.Best(player,data,"axe","woodcutting")?.Id==chain.Tool,"Crafted specialty tool is not selected as the best usable regional tool.");
            var master=data.EquipmentTiers.Single(t=>t.Level==70).Entries["tool/axe"];Items.Add(player.Inventory,Items.Create(data,master),data);Train(player,"woodcutting",70);
            Need(ToolRules.Best(player,data,"axe","woodcutting")?.Id==master,"Later masterwork tool does not overtake the regional specialty.");
        });

        Check("failed specialty crafts roll back without consuming inputs or cooldown",()=>
        {
            var chain=Chains[3];var realm=new RealmEngine(data);var player=realm.CreateCharacter("task19-fail","Profession Failure","vanguard",new());var recipe=data.Recipe(chain.ToolRecipe);
            Train(player,recipe.Skill,recipe.Requirement);Place(player,Station(recipe.Station));player.Cooldowns.Remove("craft");
            Items.Add(player.Inventory,Items.Create(data,recipe.Ingredients.First().Key,1),data);
            var before=player.Inventory.Select(x=>(x.Id,x.Template,x.Quantity)).OrderBy(x=>x.Id).ToArray();long xp=player.SkillXp[recipe.Skill];long action=player.LastAction;
            var result=realm.Execute(player.Id,Command(player,"craft",item:recipe.Id));Need(!result.Ok,"Craft with missing rare materials was accepted.");player=realm.Player(player.Id);
            var after=player.Inventory.Select(x=>(x.Id,x.Template,x.Quantity)).OrderBy(x=>x.Id).ToArray();
            Need(before.SequenceEqual(after)&&player.SkillXp[recipe.Skill]==xp&&player.LastAction==action&&player.Cooldowns.GetValueOrDefault("craft")==0,"Failed craft partially mutated authoritative state.");
        });

        Check("profession chains are economic sinks with bounded utility",()=>
        {
            foreach(var chain in Chains)
            {
                var process=data.Recipe(chain.ProcessRecipe);var specialty=data.Recipe(chain.ToolRecipe);var tool=data.Item(chain.Tool);
                Need(CraftEconomy.RecipeOutputValue(data,process)<=CraftEconomy.RecipeInputValue(data,process),chain.ProcessRecipe+" creates base item value.");
                Need(CraftEconomy.RecipeOutputValue(data,specialty)<=CraftEconomy.RecipeInputValue(data,specialty),chain.ToolRecipe+" creates base item value.");
                Need(tool.Type=="tool"&&tool.Tags.Contains("regional_specialty",StringComparer.Ordinal),chain.Tool+" is not a specialty tool.");
                Need(ToolRules.Efficiency(tool)<=15&&ToolRules.Yield(tool)<=20,chain.Tool+" exceeds gathering caps.");
                Need(tool.Description.Contains(data.Zone(chain.Zone).Name,StringComparison.Ordinal),chain.Tool+" does not tell players where its regional material comes from.");
            }
        });

        Console.WriteLine($"TASK19 PROFESSION DEPTH: {passed} checks passed; {failures.Count} failed.");
        if(failures.Count>0)throw new InvalidDataException("Task 19 profession regression failed: "+string.Join(" | ",failures));
    }
}
