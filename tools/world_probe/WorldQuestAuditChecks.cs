using Kairnfall.Core;
using System.Runtime.CompilerServices;
using System.Text.Json;

/// <summary>Full automated world anchor audit. It does not replace a human objective-by-objective playthrough.</summary>
internal static class WorldQuestAuditChecks
{
    [ModuleInitializer]
    internal static void RunOnWorldProbeStart()
    {
        var args=Environment.GetCommandLineArgs();
        string path=args.Length>1?args[1]:"content/catalog.json";
        var data=JsonSerializer.Deserialize<Catalog>(File.ReadAllText(path),Wire.Json)??throw new InvalidDataException("Empty world catalog.");
        var failures=new List<string>();
        Run(data,failures);
        if(failures.Count>0) throw new InvalidDataException("World/quest audit failed: "+string.Join(" | ",failures.Take(20)));
    }

    private static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message) { if(!value) throw new InvalidOperationException(message); }
        void Test(string name,Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS WORLD QUEST: "+name); }
            catch(Exception error) { failures.Add(name+": "+error.Message); Console.WriteLine("FAIL WORLD QUEST: "+name+": "+error.Message); }
        }

        var expectedLayers=new HashSet<string>(["Surface","Deepways","Umbral Depths","Aether Rift"],StringComparer.Ordinal);
        Test("all four authored layers and every zone are connected from the start",()=>
        {
            Need(data.Zones.Select(z=>z.Layer).ToHashSet(StringComparer.Ordinal).SetEquals(expectedLayers),"World layer set changed.");
            var byId=data.Zones.ToDictionary(z=>z.Id,StringComparer.Ordinal);
            Need(byId.ContainsKey("wayfarers_rest"),"Starting village is missing.");
            var reached=new HashSet<string>(StringComparer.Ordinal); var queue=new Queue<string>(); queue.Enqueue("wayfarers_rest");
            while(queue.TryDequeue(out var id))
            {
                if(!reached.Add(id)) continue;
                foreach(var exit in byId[id].Exits) if(byId.ContainsKey(exit.Target)&&!reached.Contains(exit.Target)) queue.Enqueue(exit.Target);
            }
            var missing=data.Zones.Where(z=>!reached.Contains(z.Id)).Select(z=>z.Id).OrderBy(x=>x).ToArray();
            Need(missing.Length==0,"Zones disconnected from normal travel: "+string.Join(", ",missing));
            foreach(var layer in expectedLayers)
            {
                Need(data.Zones.Any(z=>z.Layer==layer),"No zone exists in "+layer+".");
                if(layer!="Surface") Need(data.Zones.Any(z=>z.Layer==layer&&data.Zones.Any(source=>source.Layer!=layer&&source.Exits.Any(e=>e.Target==z.Id))),"No physical entry reaches "+layer+" from another layer.");
            }
        });

        var realm=new RealmEngine(data);
        int nodeCount=0,chestCount=0,creatureCount=0,bossCount=0,npcCount=0;
        foreach(var zone in data.Zones)
        {
            Test("reachable anchors in "+zone.Id,()=>
            {
                var reached=Flood(zone);
                void Reach(Point at,string label)
                {
                    Need(WorldMap.Fits(zone,at),label+" does not fit actor collision.");
                    Need(reached.Contains(((int)Math.Floor(at.X),(int)Math.Floor(at.Y))),label+" cannot be reached from the zone spawn.");
                }
                Reach(zone.Spawn,"spawn");
                foreach(var exit in zone.Exits) Reach(exit.Position,"exit "+exit.Id);
                foreach(var npc in data.Npcs.Where(n=>n.Zone==zone.Id)) { npcCount++; Reach(npc.Position,"NPC/service "+npc.Id); }
                foreach(var node in realm.State.Nodes.Values.Where(n=>n.Zone==zone.Id)) { nodeCount++; Reach(node.Position,"resource "+node.Id); }
                foreach(var chest in realm.State.Chests.Values.Where(c=>c.Zone==zone.Id)) { chestCount++; Reach(chest.Position,"chest "+chest.Id); }
                foreach(var mob in realm.State.Creatures.Values.Where(c=>c.Zone==zone.Id))
                {
                    creatureCount++; Reach(mob.Position,"creature "+mob.Id); Reach(mob.Home,"creature home "+mob.Id);
                    if(data.Mob(mob.Template).Boss) bossCount++;
                }
            });
        }

        var knownActions=new HashSet<string>(["gather","craft","talk","deliver","chart","explore","boss","read","build","trade","socket","chest","kill","cast","plant"],StringComparer.Ordinal);
        foreach(var quest in data.Quests)
        {
            Test("quest anchors "+quest.Id,()=>
            {
                Need(data.Npcs.Any(n=>n.Id==quest.Giver),"Quest giver does not exist.");
                Need(quest.Objectives.Count>0,"Quest has no objective.");
                foreach(var objective in quest.Objectives)
                {
                    Need(knownActions.Contains(objective.Action),"Unknown objective action "+objective.Action+".");
                    Need(objective.Count>0,"Objective count is not positive.");
                    bool resolved=objective.Action switch
                    {
                        "talk" => data.Npcs.Any(n=>n.Id==objective.Target),
                        "explore" or "chart" => data.Zones.Any(z=>z.Id==objective.Target),
                        "boss" => data.Mobs.Any(m=>m.Id==objective.Target&&m.Boss)&&realm.State.Creatures.Values.Any(c=>c.Template==objective.Target),
                        "kill" => data.Mobs.Any(m=>m.Id==objective.Target)&&realm.State.Creatures.Values.Any(c=>c.Template==objective.Target),
                        "gather" => data.Items.Any(i=>i.Id==objective.Target)&&(data.Resources.Any(r=>r.Item==objective.Target)||objective.Target=="wheat"),
                        "craft" => data.Items.Any(i=>i.Id==objective.Target)&&data.Recipes.Any(r=>r.Output==objective.Target),
                        "deliver" or "read" => data.Items.Any(i=>i.Id==objective.Target),
                        "cast" => data.Abilities.Any(a=>a.Id==objective.Target),
                        "build" => objective.Target.StartsWith("structure_",StringComparison.Ordinal),
                        "trade" or "socket" => objective.Target=="*",
                        "chest" => objective.Target is "locked" or "runic" or "*",
                        "plant" => objective.Target=="wheat"||data.Items.Any(i=>i.Id==objective.Target||i.Id==objective.Target+"_seed"),
                        _ => false
                    };
                    Need(resolved,$"Objective {objective.Action}/{objective.Target} has no real content anchor.");
                }
            });
        }

        Test("every authored resource and boss has a seeded reachable world instance",()=>
        {
            foreach(var resource in data.Resources)
            {
                if(resource.Id=="wheat_crop") continue;
                Need(realm.State.Nodes.Values.Any(n=>n.Template==resource.Id),"No seeded node uses resource "+resource.Id+".");
            }
            foreach(var boss in data.Mobs.Where(m=>m.Boss))
                Need(realm.State.Creatures.Values.Any(c=>c.Template==boss.Id),"No world arena contains boss "+boss.Id+".");
        });

        Console.WriteLine($"WORLD_QUEST_AUDIT: {data.Zones.Count} zones; 4 layers; {npcCount} NPC/service anchors; {nodeCount} resource nodes; {chestCount} chests; {creatureCount} creature anchors; {bossCount} boss arenas; {data.Quests.Count} quests; {passed} groups passed; failures {failures.Count}. Automated reachability/reference audit; human walkthrough remains separate.");
    }

    private static HashSet<(int X,int Y)> Flood(ZoneDef zone)
    {
        var reached=new HashSet<(int X,int Y)>(); var queue=new Queue<(int X,int Y)>();
        queue.Enqueue(((int)Math.Floor(zone.Spawn.X),(int)Math.Floor(zone.Spawn.Y)));
        while(queue.TryDequeue(out var tile))
        {
            if(tile.X<1||tile.Y<1||tile.X>=zone.Width-1||tile.Y>=zone.Height-1||reached.Contains(tile)) continue;
            if(!WorldMap.Fits(zone,new Point(tile.X+.5,tile.Y+.5))) continue;
            reached.Add(tile);
            queue.Enqueue((tile.X+1,tile.Y)); queue.Enqueue((tile.X-1,tile.Y)); queue.Enqueue((tile.X,tile.Y+1)); queue.Enqueue((tile.X,tile.Y-1));
        }
        return reached;
    }
}
