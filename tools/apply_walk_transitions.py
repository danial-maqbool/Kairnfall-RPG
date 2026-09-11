#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def save(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")

def replace_once(path: str, old: str, new: str) -> None:
    text = load(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:100]!r}")
    save(path, text.replace(old, new, 1))

map_rules = r'''namespace Kairnfall.Core;

/// <summary>Server-authoritative rules for changing maps by physically walking through authored exits.</summary>
public static class MapTransitionRules
{
    public const double BorderMargin = 4.75;
    public const double WalkTriggerRadius = 0.68;
    public const double BorderLaneRadius = 1.45;
    public const double ArrivalClearance = 1.35;

    public static bool IsBorderExit(ZoneDef zone, ExitDef exit)
        => BorderOutward(zone, exit).Distance(new Point(0, 0)) > 0.01;

    public static Point BorderOutward(ZoneDef zone, ExitDef exit)
    {
        var choices = new (double Distance, Point Direction)[]
        {
            (exit.Position.X - 1, new Point(-1, 0)),
            ((zone.Width - 1) - exit.Position.X, new Point(1, 0)),
            (exit.Position.Y - 1, new Point(0, -1)),
            ((zone.Height - 1) - exit.Position.Y, new Point(0, 1))
        };
        var nearest = choices.OrderBy(x => x.Distance).First();
        return nearest.Distance <= BorderMargin ? nearest.Direction : new Point(0, 0);
    }

    public static ExitDef? TriggeredExit(ZoneDef zone, Point before, Point after, Point direction)
    {
        double length = direction.Distance(new Point(0, 0));
        if (length <= 0.01) return null;
        var unit = direction.Scale(1 / length);
        return zone.Exits
            .Where(exit => Triggered(zone, exit, before, after, unit))
            .OrderBy(exit => exit.Position.Distance(after))
            .ThenBy(exit => exit.Id, StringComparer.Ordinal)
            .FirstOrDefault();
    }

    private static bool Triggered(ZoneDef zone, ExitDef exit, Point before, Point after, Point unit)
    {
        var outward = BorderOutward(zone, exit);
        if (outward.Distance(new Point(0, 0)) > 0.01)
        {
            if (Dot(unit, outward) < 0.30) return false;
            double lateral = Math.Abs(outward.X) > 0.5
                ? Math.Abs(after.Y - exit.Position.Y)
                : Math.Abs(after.X - exit.Position.X);
            if (lateral > BorderLaneRadius) return false;
            if (outward.X < -0.5) return after.X <= exit.Position.X + 0.35;
            if (outward.X > 0.5) return after.X >= exit.Position.X - 0.35;
            if (outward.Y < -0.5) return after.Y <= exit.Position.Y + 0.35;
            return after.Y >= exit.Position.Y - 0.35;
        }

        if (SegmentDistance(before, after, exit.Position) > WalkTriggerRadius
            && after.Distance(exit.Position) > WalkTriggerRadius) return false;
        var toward = before.Direction(exit.Position);
        return toward.Distance(new Point(0, 0)) > 0.01 && Dot(unit, toward) > 0.05;
    }

    public static Point ArrivalPoint(Catalog data, ZoneDef source, ExitDef exit)
    {
        var target = data.Zone(exit.Target);
        var anchor = exit.Arrival;
        // Follow the actual target-zone path inward. This works for borders, doors,
        // caves and stairwells and guarantees we do not arrive on the reciprocal trigger.
        foreach (var point in WorldMap.FindPath(target, anchor, target.Spawn, target.Width * target.Height * 2))
            if (point.Distance(anchor) >= ArrivalClearance && WorldMap.Fits(target, point)) return point;

        var direction = anchor.Direction(target.Spawn);
        if (direction.Distance(new Point(0, 0)) > 0.01)
        {
            foreach (double distance in new[] { 2.0, 1.5, 1.0 })
            {
                var candidate = anchor.Add(direction.Scale(distance));
                if (WorldMap.Fits(target, candidate)) return candidate;
            }
        }
        return WorldMap.FindFree(target, anchor);
    }

    public static string EntranceVisualKey(ZoneDef source, ExitDef exit, ZoneDef target)
    {
        if (exit.Kind == "door") return "entrance_door";
        if (exit.Kind == "gate") return "entrance_gate";
        if (exit.Kind == "portal") return "entrance_portal";
        if (exit.Kind == "lift") return "entrance_lift";
        if (exit.Kind == "tunnel") return source.Layer == "Surface" ? "entrance_cave" : "entrance_tunnel";
        if (exit.Kind == "stairs")
            return source.Layer == "Surface" && (target.Layer != "Surface" || target.Kind == "dungeon")
                ? "entrance_cave" : "entrance_stairs";
        if (exit.Kind == "road") return "entrance_road";
        return "entrance_stairs";
    }

    private static double Dot(Point a, Point b) => a.X * b.X + a.Y * b.Y;

    private static double SegmentDistance(Point a, Point b, Point p)
    {
        double dx = b.X - a.X, dy = b.Y - a.Y;
        double lengthSquared = dx * dx + dy * dy;
        if (lengthSquared <= 0.000001) return p.Distance(a);
        double t = Math.Clamp(((p.X - a.X) * dx + (p.Y - a.Y) * dy) / lengthSquared, 0, 1);
        return p.Distance(new Point(a.X + dx * t, a.Y + dy * t));
    }
}
'''
save("src/Kairnfall.Core/MapTransitionRules.cs", map_rules)

walk_checks = r'''using Kairnfall.Core;

internal static class WalkTransitionChecks
{
    public static void Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Need(bool value, string text) { if (!value) throw new InvalidOperationException(text); }
        void Test(string name, Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS WALK TRANSITIONS: " + name); }
            catch (Exception error) { failures.Add("walk transition: " + name); Console.WriteLine("FAIL WALK TRANSITIONS: " + name + ": " + error.Message); }
        }
        Character AtLevel(int target)
        {
            var seeded = new Character { Class = "vanguard" };
            long remaining = Progression.PlayerThreshold(target);
            foreach (var skill in data.Skills)
            {
                long chunk = Math.Min(remaining, Progression.Threshold(Progression.SkillCap));
                seeded.SkillXp[skill.Id] = chunk; remaining -= chunk;
            }
            Need(remaining == 0 && Progression.PlayerLevel(seeded) == target, "Could not seed level " + target);
            return seeded;
        }
        Point Approach(ZoneDef zone, ExitDef exit)
        {
            var outward = MapTransitionRules.BorderOutward(zone, exit);
            var guess = outward.Distance(new Point(0, 0)) > 0.01
                ? exit.Position.Add(outward.Scale(-1.15))
                : exit.Position.Add(exit.Position.Direction(zone.Spawn).Scale(1.15));
            return WorldMap.FindFree(zone, guess);
        }
        Point Direction(ZoneDef zone, ExitDef exit, Point from)
        {
            var outward = MapTransitionRules.BorderOutward(zone, exit);
            return outward.Distance(new Point(0, 0)) > 0.01 ? outward : from.Direction(exit.Position);
        }
        bool WalkThrough(RealmEngine realm, Character player, ZoneDef source, ExitDef exit, int ticks = 80)
        {
            realm.Active.Add(player.Id);
            for (int i = 0; i < ticks && player.Zone == source.Id; i++)
            {
                if (i % 3 == 0)
                {
                    var dir = Direction(source, exit, player.Position);
                    var result = realm.Execute(player.Id, new GameCommand { Kind = "move", X = dir.X, Y = dir.Y });
                    Need(result.Ok, "Movement intent rejected: " + result.Message);
                }
                realm.Tick(0.05);
            }
            return player.Zone == exit.Target;
        }

        Test("authored exits are reciprocal and have typed walk-through visuals", () =>
        {
            int exits = 0, borders = 0, caves = 0;
            var allowed = new HashSet<string> { "entrance_road", "entrance_door", "entrance_gate", "entrance_cave", "entrance_tunnel", "entrance_lift", "entrance_portal", "entrance_stairs" };
            foreach (var source in data.Zones) foreach (var exit in source.Exits)
            {
                var target = data.Zone(exit.Target);
                var reciprocal = target.Exits.FirstOrDefault(x => x.Target == source.Id && x.Position.Distance(exit.Arrival) < 0.01 && x.Arrival.Distance(exit.Position) < 0.01);
                Need(reciprocal is not null, "Missing reciprocal exit for " + source.Id + "/" + exit.Id);
                string visual = MapTransitionRules.EntranceVisualKey(source, exit, target);
                Need(allowed.Contains(visual), "Unknown entrance visual " + visual + " for " + exit.Id);
                if (MapTransitionRules.IsBorderExit(source, exit)) borders++;
                if (source.Kind == "wilderness" && source.Layer == "Surface" && target.Layer != "Surface" && exit.Kind == "stairs")
                {
                    Need(visual == "entrance_cave", "Underground wilderness entrance is not cave-like: " + exit.Id);
                    caves++;
                }
                exits++;
            }
            Need(exits > 100, "Too few authored exits were checked.");
            Need(borders > 50, "Surface border network is unexpectedly sparse.");
            Need(caves >= 10, "Too few wilderness cave entrances were classified.");
        });

        Test("walking through a building door changes maps without an interact command", () =>
        {
            var pair = (from source in data.Zones
                        from exit in source.Exits
                        let target = data.Zone(exit.Target)
                        where exit.Kind == "door" && source.Kind != "interior" && target.Kind == "interior"
                        select (source, exit, target)).First();
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("walk-door", "Door Walker", "vanguard", new());
            player.Zone = pair.source.Id; player.Position = Approach(pair.source, pair.exit);
            Need(WalkThrough(realm, player, pair.source, pair.exit), "Walking onto the door did not enter the interior.");
            Need(WorldMap.Fits(pair.target, player.Position), "Door arrival is blocked.");
            Need(player.Position.Distance(pair.exit.Arrival) >= MapTransitionRules.ArrivalClearance - 0.25, "Door arrival remained on the reciprocal trigger.");
            string entered = player.Zone;
            var held = Direction(pair.source, pair.exit, pair.exit.Position);
            for (int i = 0; i < 12; i++)
            {
                if (i % 3 == 0) realm.Execute(player.Id, new GameCommand { Kind = "move", X = held.X, Y = held.Y });
                realm.Tick(0.05);
            }
            Need(player.Zone == entered, "Door arrival immediately bounced back to the previous map.");
        });

        Test("walking outward at a connected wilderness border enters the adjacent map", () =>
        {
            var pair = (from source in data.Zones
                        from exit in source.Exits
                        let target = data.Zone(exit.Target)
                        where source.Kind == "wilderness" && target.Kind == "wilderness" && MapTransitionRules.IsBorderExit(source, exit)
                        orderby JourneyProgression.ExitRequirement(data, exit)
                        select (source, exit, target)).First();
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("walk-border", "Border Walker", "vanguard", new());
            var level = AtLevel(Math.Max(1, JourneyProgression.ExitRequirement(data, pair.exit)));
            player.SkillXp = new(level.SkillXp); player.Zone = pair.source.Id; player.Position = Approach(pair.source, pair.exit);
            Need(WalkThrough(realm, player, pair.source, pair.exit), "Outward movement did not cross the authored border.");
            Need(player.Zone == pair.target.Id && WorldMap.Fits(pair.target, player.Position), "Border arrival is invalid.");
        });

        Test("level gates remain server-authoritative for automatic entrances", () =>
        {
            var candidate = (from source in data.Zones
                             from exit in source.Exits
                             let gate = JourneyProgression.ExitRequirement(data, exit)
                             where gate > 1 && source.Kind != "interior"
                             orderby gate
                             select (source, exit, gate)).First();
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("walk-gate", "Gate Walker Auto", "vanguard", new());
            var low = AtLevel(candidate.gate - 1); player.SkillXp = new(low.SkillXp);
            player.Zone = candidate.source.Id; player.Position = Approach(candidate.source, candidate.exit);
            Need(!WalkThrough(realm, player, candidate.source, candidate.exit, 50) && player.Zone == candidate.source.Id, "Below-level player crossed an automatic gate.");
            var ready = AtLevel(candidate.gate); player.SkillXp = new(ready.SkillXp); player.Position = Approach(candidate.source, candidate.exit);
            Need(WalkThrough(realm, player, candidate.source, candidate.exit), "Exact-level player could not walk through the gate.");
        });

        Test("a border with no authored exit stays solid", () =>
        {
            var zone = data.Zones.First(z => z.Kind == "wilderness" && z.WorldX == data.Zones.Where(x => x.Kind == "wilderness").Min(x => x.WorldX));
            Need(!zone.Exits.Any(e => MapTransitionRules.BorderOutward(zone, e).X < -0.5), "Fixture unexpectedly has a left-edge exit.");
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("walk-wall", "Edge Walker", "vanguard", new());
            player.Zone = zone.Id; player.Position = WorldMap.FindFree(zone, new Point(1.5, zone.Spawn.Y)); realm.Active.Add(player.Id);
            for (int i = 0; i < 30; i++)
            {
                if (i % 3 == 0) realm.Execute(player.Id, new GameCommand { Kind = "move", X = -1, Y = 0 });
                realm.Tick(0.05);
            }
            Need(player.Zone == zone.Id, "A non-connected border changed maps.");
            Need(WorldMap.Fits(zone, player.Position), "Solid border pushed the player into invalid terrain.");
        });

        Test("client exits are visual walk-throughs and are no longer E interactions", () =>
        {
            string world = File.ReadAllText("client/Scripts/WorldView.cs");
            string root = File.ReadAllText("client/Scripts/GameRoot.cs");
            string rules = File.ReadAllText("client/Scripts/ExperienceRules.cs");
            Need(!world.Contains("new WorldTarget(\"exit\"", StringComparison.Ordinal), "WorldView still registers exits as interaction targets.");
            Need(!root.Contains("target.Kind == \"exit\"", StringComparison.Ordinal), "GameRoot still sends transition commands from exit interactions.");
            Need(!rules.Contains("\"exit\" => \"Enter\"", StringComparison.Ordinal), "Interaction verb still advertises E-to-enter.");
            foreach (string key in new[] { "entrance_road", "entrance_door", "entrance_gate", "entrance_cave", "entrance_tunnel", "entrance_lift", "entrance_portal", "entrance_stairs" })
                Need(world.Contains("EntranceVisualKey", StringComparison.Ordinal), "WorldView is not using typed entrance visuals: " + key);
        });

        Console.WriteLine($"WALK TRANSITIONS: {passed} groups passed; total failures {failures.Count}.");
    }
}
'''
save("tools/world_probe/WalkTransitionChecks.cs", walk_checks)

# RealmEngine: remember a short post-transition guard, perform transition from movement, and clear it on disconnect.
replace_once("src/Kairnfall.Core/RealmEngine.cs",
'''    private readonly Dictionary<string,string> playerTargets=[];
    private double aiElapsed;''',
'''    private readonly Dictionary<string,string> playerTargets=[];
    private readonly Dictionary<string,double> transitionReady=[];
    private double aiElapsed;''')
replace_once("src/Kairnfall.Core/RealmEngine.cs",
'''                    p.Position=WorldMap.Move(zone,p.Position,direction.Scale(stats.MoveSpeed*slow*dt)); p.Facing=direction;
                }
            }
            p.Stamina=''',
'''                    var before=p.Position;
                    p.Position=WorldMap.Move(zone,p.Position,direction.Scale(stats.MoveSpeed*slow*dt)); p.Facing=direction;
                    if(slow>0) TryWalkTransition(p,zone,before,direction);
                    zone=Data.Zone(p.Zone);
                }
            }
            p.Stamina=''')
replace_once("src/Kairnfall.Core/RealmEngine.cs",
'''        Active.Remove(id); inputs.Remove(id); playerTargets.Remove(id);''',
'''        Active.Remove(id); inputs.Remove(id); playerTargets.Remove(id); transitionReady.Remove(id);''')

# RealmEconomy: share the old transition outcome with automatic walk triggers.
old_transition = '''    private string Transition(Character p,string exitId)
    {
        var source=Data.Zone(p.Zone);
        var exit=source.Exits.FirstOrDefault(x=>x.Id==exitId)??throw new RuleException("Unknown map exit.");
        Near(p,p.Zone,exit.Position,2.2);
        var target=Data.Zone(exit.Target);int currentLevel=Progression.PlayerLevel(p);
        int required=JourneyProgression.ExitRequirement(Data,exit);
        Need(currentLevel>=required,JourneyProgression.LockMessage(target,currentLevel,required));
        CancelTradesFor(p.Id); inputs.Remove(p.Id);
        p.Zone=target.Id; p.Position=WorldMap.FindFree(target,exit.Arrival);
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet)) { pet.Zone=p.Zone; pet.Position=p.Position; pet.Home=p.Position; }
        if(p.Discoveries.Add(p.Zone)) Progression.Train(p,"exploration",100,Math.Clamp(Data.Zone(p.Zone).Level,1,100),Data);
        Progress(p,"explore",p.Zone); return "Entered "+Data.Zone(p.Zone).Name+".";
    }
'''
new_transition = '''    private bool TryWalkTransition(Character p,ZoneDef source,Point before,Point direction)
    {
        if(transitionReady.GetValueOrDefault(p.Id)>State.Time) return false;
        var exit=MapTransitionRules.TriggeredExit(source,before,p.Position,direction);
        if(exit is null) return false;
        var target=Data.Zone(exit.Target);int currentLevel=Progression.PlayerLevel(p);
        int required=JourneyProgression.ExitRequirement(Data,exit);
        if(currentLevel<required) { p.Position=before; return false; }
        CompleteTransition(p,source,exit);return true;
    }
    private string CompleteTransition(Character p,ZoneDef source,ExitDef exit)
    {
        var target=Data.Zone(exit.Target);
        CancelTradesFor(p.Id);inputs.Remove(p.Id);transitionReady[p.Id]=State.Time+0.55;
        p.Zone=target.Id;p.Position=MapTransitionRules.ArrivalPoint(Data,source,exit);
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet)) { pet.Zone=p.Zone;pet.Position=p.Position;pet.Home=p.Position; }
        if(p.Discoveries.Add(p.Zone)) Progression.Train(p,"exploration",100,Math.Clamp(target.Level,1,100),Data);
        Progress(p,"explore",p.Zone);return "Entered "+target.Name+".";
    }
    private string Transition(Character p,string exitId)
    {
        var source=Data.Zone(p.Zone);
        var exit=source.Exits.FirstOrDefault(x=>x.Id==exitId)??throw new RuleException("Unknown map exit.");
        Near(p,p.Zone,exit.Position,2.2);
        var target=Data.Zone(exit.Target);int currentLevel=Progression.PlayerLevel(p);
        int required=JourneyProgression.ExitRequirement(Data,exit);
        Need(currentLevel>=required,JourneyProgression.LockMessage(target,currentLevel,required));
        return CompleteTransition(p,source,exit);
    }
'''
replace_once("src/Kairnfall.Core/RealmEconomy.cs", old_transition, new_transition)

# WorldView: entrances are scenery/wayfinding, not interaction targets.
old_exit_render = '''        foreach (var exit in zone.Exits)
        {
            if (!IsWithinCameraBounds(exit.Position, 4)) continue;
            string prop = exit.Kind is "road" ? "signpost" : exit.Kind.Contains("portal", StringComparison.Ordinal) ? "waystone" : "stairs";
            if (exit.Kind != "door") DrawProp("props/" + prop, exit.Position);
            else DrawArc(Pixels(exit.Position), 10, 0, MathF.PI, 12, new Color(.72f, .64f, .43f, .65f), 1);
            interactions.Add(new WorldTarget("exit", exit.Id, Data.Zone(exit.Target).Name, exit.Position));
            if (exit.Position.Distance(Camera) < 6) Nameplate(exit.Position, "→ " + Data.Zone(exit.Target).Name, Ui.Gold, -72);
        }
'''
new_exit_render = '''        foreach (var exit in zone.Exits)
        {
            if (!IsWithinCameraBounds(exit.Position, 5)) continue;
            visuals.Add(new Visual((float)exit.Position.Y + .05f, "exit", exit.Id, exit.Position, exit));
        }
'''
replace_once("client/Scripts/WorldView.cs", old_exit_render, new_exit_render)
replace_once("client/Scripts/WorldView.cs",
'''        switch (visual.Kind)
        {
            case "furnishing":''',
'''        switch (visual.Kind)
        {
            case "exit":
                var exit = (ExitDef)visual.Value!;
                var destination = Data.Zone(exit.Target);
                DrawProp("props/" + MapTransitionRules.EntranceVisualKey(zone, exit, destination), exit.Position);
                if (exit.Position.Distance(Camera) < 7 && Snapshot is { } travelSnapshot)
                {
                    int required = JourneyProgression.ExitRequirement(Data, exit);
                    int level = Progression.PlayerLevel(travelSnapshot.Self);
                    string text = level < required
                        ? $"LOCKED · Lv {required} · {destination.Name}"
                        : (MapTransitionRules.IsBorderExit(zone, exit) ? "Continue → " : "Walk through → ") + destination.Name;
                    Nameplate(exit.Position, text, level < required ? Ui.Danger : Ui.Gold, -72, 10);
                }
                break;
            case "furnishing":''')

# Client actions: E remains useful for NPCs/nodes/chests/etc, but never changes maps.
replace_once("client/Scripts/GameRoot.cs", '        else if (target.Kind == "exit") Send("transition", target.Id);\n', '')
replace_once("client/Scripts/ExperienceRules.cs",
'''        "npc" => "Talk to", "exit" => "Enter", "node" => "Gather",''',
'''        "npc" => "Talk to", "node" => "Gather",''')
replace_once("client/Scripts/GameRoot.Experience.cs",
'''    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
    {
        if (previous is null || previous.Self.Id != current.Self.Id) return;
        var before = previous.Self.Inventory.GroupBy''',
'''    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
    {
        if (previous is null || previous.Self.Id != current.Self.Id) return;
        if (previous.Self.Zone != current.Self.Zone)
        {
            route.Clear(); pendingInteraction = null; lastInput = Vector2.Zero; StopCombatInput();
        }
        var before = previous.Self.Inventory.GroupBy''')

# Integration navigation now proves the networked client crosses by movement alone.
old_reach = '''async Task ReachDawnreach(GameConnection client)
{
    foreach(var destination in new[]{"kingsmeadow","dawnreach"})
    {
        var state=await State(client); var exit=data.Zone(state.Self.Zone).Exits.First(x=>x.Target==destination);
        await Navigate(client,exit.Position); await Act(client,"transition",exit.Id); await State(client,s=>s.Self.Zone==destination);
    }
}
'''
new_reach = '''async Task WalkThrough(GameConnection client,string destination)
{
    var snapshot=await State(client);string sourceId=snapshot.Self.Zone;var source=data.Zone(sourceId);
    var exit=source.Exits.First(x=>x.Target==destination);
    var route=WorldMap.FindPath(source,snapshot.Self.Position,exit.Position,source.Width*source.Height);route.Add(exit.Position);
    int next=0;var watch=Stopwatch.StartNew();
    while(watch.Elapsed<TimeSpan.FromSeconds(100))
    {
        snapshot=await State(client);
        if(snapshot.Self.Zone==destination) { await client.MoveAsync(0,0,cancel);return; }
        Check(snapshot.Self.Zone==sourceId,"Walk-through navigation crossed an unexpected zone.");
        var position=snapshot.Self.Position;Point direction;
        var outward=MapTransitionRules.BorderOutward(source,exit);
        if(outward.Distance(new Point(0,0))>0.01&&position.Distance(exit.Position)<1.6) direction=outward;
        else
        {
            while(next<route.Count-1&&position.Distance(route[next])<0.7) next++;
            direction=position.Direction(route[Math.Min(next,route.Count-1)]);
        }
        await client.MoveAsync(direction.X,direction.Y,cancel);await Task.Delay(100,cancel);Pump(client);
    }
    await client.MoveAsync(0,0,cancel);throw new TimeoutException("Walking did not enter "+destination+" from "+sourceId);
}
async Task ReachDawnreach(GameConnection client)
{
    foreach(var destination in new[]{"kingsmeadow","dawnreach"}) await WalkThrough(client,destination);
}
'''
replace_once("tests/Kairnfall.Integration/Program.cs", old_reach, new_reach)

# Permanent probe registration.
replace_once("tools/world_probe/Program.cs",
'''JourneyPacingChecks.Run(catalog,failures);
MeaningfulObjectiveChecks.Run(catalog,failures);''',
'''JourneyPacingChecks.Run(catalog,failures);
WalkTransitionChecks.Run(catalog,failures);
MeaningfulObjectiveChecks.Run(catalog,failures);''')

# Deterministic original entrance art.
replace_once("tools/art/environment_pack.py",
"PROPS = ['oak','ancient_oak','pine','snow_pine','willow','palm','dead_tree','bush','flowers','rock','snow_rock','basalt','grass_tuft','reeds','mushrooms','cactus','crystal','signpost','waystone','stairs','stump','loot','shadow']",
"PROPS = ['oak','ancient_oak','pine','snow_pine','willow','palm','dead_tree','bush','flowers','rock','snow_rock','basalt','grass_tuft','reeds','mushrooms','cactus','crystal','signpost','waystone','stairs','entrance_road','entrance_door','entrance_gate','entrance_cave','entrance_tunnel','entrance_lift','entrance_portal','entrance_stairs','stump','loot','shadow']")
entrance_art = r'''    if kind.startswith('entrance_'):
        im=canvas((64,72)); p=Pixel(im); x=32; floor=68
        if kind=='entrance_cave':
            p.poly([(3,floor),(7,35),(15,19),(27,10),(43,13),(56,27),(62,floor)],'55595b')
            p.poly([(7,63),(11,37),(20,23),(31,16),(43,19),(54,35),(59,63)],'76766d',None)
            p.ellipse((16,29,50,70),'171b20'); p.ellipse((21,34,45,69),'25282b')
            p.line([(10,39),(20,26),(31,19)],'9b9a88',2); p.line([(46,23),(55,38)],'3d4144',2)
            for yy in range(50,69,5): p.rect((22,yy,44,yy+2),'6d6860','343638')
        elif kind=='entrance_tunnel':
            p.rect((7,31,57,68),'555a5e'); p.ellipse((7,9,57,57),'666b6d'); p.ellipse((15,18,49,66),'171b20')
            for xx in range(10,58,9): p.line([(xx,34),(xx+3,28)],'88877c')
            p.line([(12,65),(52,65)],'929083',2)
        elif kind=='entrance_door':
            p.rect((14,17,50,69),'654c38','2d2926'); p.poly([(14,18),(19,8),(45,8),(50,18)],'8f7655','2d2926')
            p.rect((20,20,44,68),'3d2f29','201d1b'); p.rect((23,23,31,65),'76573d'); p.rect((33,23,41,65),'725239')
            p.line([(32,23),(32,65)],'b28c60'); p.sphere((37,43,40,46),'d2b36d')
        elif kind=='entrance_gate':
            p.rect((5,22,15,69),'77766d','303235'); p.rect((49,22,59,69),'77766d','303235')
            p.poly([(4,23),(10,10),(20,20),(44,20),(54,10),(60,23)],'918e7d','303235')
            for xx in range(20,49,7): p.line([(xx,25),(xx,68)],'5d4937',3)
            p.line([(18,27),(50,27)],'9b7951',3)
        elif kind=='entrance_road':
            p.poly([(20,69),(24,42),(28,24),(36,24),(40,42),(45,69)],'9a805b')
            p.line([(27,67),(29,40),(32,27)],'c3a273'); p.line([(39,67),(36,39)],'6e5b45')
            p.rect((8,34,13,68),'70533b','2f2a25'); p.rect((51,34,56,68),'70533b','2f2a25')
            p.poly([(6,31),(18,31),(15,37),(6,37)],'b29362','4b3a2b'); p.poly([(46,31),(59,31),(59,37),(49,37)],'b29362','4b3a2b')
        elif kind=='entrance_lift':
            p.rect((8,12,56,69),'53595e','272b2e'); p.rect((14,20,50,66),'252a2d','151719')
            for xx in (17,27,37,47): p.line([(xx,21),(xx,65)],'8f8069',2)
            p.line([(12,17),(52,17)],'b19b75',3); p.line([(32,3),(32,17)],'8d7654',2); p.sphere((28,0,36,8),'bca36e')
        elif kind=='entrance_portal':
            p.ellipse((6,9,58,70),'4c4e63'); p.ellipse((12,15,52,67),'8180a8'); p.ellipse((18,21,46,65),'2b2148')
            p.ellipse((21,25,43,63),'6f58a6'); p.line([(32,23),(25,38),(39,49),(28,62)],'c7b6e8',2)
            for xx,yy in [(11,28),(51,31),(16,55),(48,57)]: p.sphere((xx-2,yy-2,xx+2,yy+2),'b9a8de')
        else:  # entrance_stairs
            p.poly([(11,69),(13,28),(21,16),(43,16),(51,28),(53,69)],'5c6166','292c2f')
            p.ellipse((18,23,46,58),'24282c')
            for i in range(6):
                yy=42+i*5; p.rect((19+i,yy,45-i,yy+3),'797c79','35383a'); p.line([(21+i,yy),(43-i,yy)],'a4a59b')
        return im
'''
replace_once("tools/art/environment_pack.py",
'''    im=canvas((48,64)); p=Pixel(im); x,y=24,58
''', entrance_art + '''    im=canvas((48,64)); p=Pixel(im); x,y=24,58
''')

# Documentation records the player-facing contract and human visual remainder.
doc = '''# Walk-through map transitions — 2026-09-11

Map changes are now driven by authoritative movement rather than an `E` interaction.

## Player contract

- Walking through an authored building door changes to its interior automatically.
- Walking into authored cave, stair, tunnel, lift, gate, portal, or road entrances changes maps automatically.
- Connected surface-region borders change maps when the player walks outward through the authored border lane.
- A border without an authored exit stays solid and does not infer or invent a destination.
- Existing journey level gates remain server-authoritative. Locked entrances block movement and display their required level.
- Arrival positions are moved inward along the destination's real path so reciprocal entrances do not bounce the player back.
- `E` remains the contextual key for NPCs, gathering, chests, loot, landmarks, and structures; exits are deliberately absent from the interaction target list.

## Entrance presentation

The deterministic environment pack now generates dedicated pixel-art sprites for roads, doors, gates, caves, tunnels, lifts, portals, and stairs. Surface-to-underground wilderness stairs render as cave mouths. These are structural/generated game assets; final artistic approval remains a human visual check.

## Automated acceptance

`WalkTransitionChecks` validates reciprocal authored exits, border topology, automatic door crossing, automatic wilderness-border crossing, exact level-gate enforcement, solid non-connected borders, safe arrival clearance, and removal of client `E` exit interactions. The real-network integration route to Dawnreach also crosses maps using movement only.
'''
save("docs/acceptance/WALK_THROUGH_TRANSITIONS.md", doc)

print("Walk-through map transition patch applied.")
