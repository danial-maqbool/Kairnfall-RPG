using System.Runtime.CompilerServices;
using System.Text.Json;
using Kairnfall.Core;

internal static class FirstHourPresentationChecks
{
    [ModuleInitializer]
    public static void Run()
    {
        string root=Directory.GetCurrentDirectory();string catalogPath=File.Exists(Path.Combine(root,"content","catalog.json"))?Path.Combine(root,"content","catalog.json"):Path.Combine(root,"client","Data","catalog.json");
        if(!File.Exists(catalogPath))return;
        var data=JsonSerializer.Deserialize<Catalog>(File.ReadAllText(catalogPath),Wire.Json)!;int passed=0;var failures=new List<string>();
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action body){try{body();passed++;Console.WriteLine("PASS FIRST HOUR: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL FIRST HOUR: "+name+": "+e.Message);}}
        Test("twelve ordered milestones cover the intended vertical slice",()=>
        {
            string[] expected=["movement","npc","gather","craft","combat","skill","level","equipment","interior","transition","social","miniboss"];
            Need(FirstHourExperience.Steps.Select(x=>x.Id).SequenceEqual(expected),"First-hour milestone order drifted.");
        });
        Test("milestones are persistent and sequential",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("first-hour-fixture","First Hour","vanguard",new());
            Need(FirstHourExperience.Current(data,p)?.Id=="movement","Fresh character does not begin with movement guidance.");
            foreach(string id in new[]{"movement","npc","gather","craft","combat"})FirstHourExperience.Mark(p,id);
            Need(FirstHourExperience.Current(data,p)?.Id=="skill","Persistent marker progression is not monotonic.");
        });
        Test("starter spaces support gathering crafting services and real interiors",()=>
        {
            var starter=data.Zone("wayfarers_rest");Need(starter.Resources.Length>=6,"Starter resources are too narrow.");Need(starter.Buildings.Count>=4,"Starter village lost named buildings.");
            Need(starter.Exits.Any(x=>data.Zone(x.Target).Kind=="interior"),"Starter buildings do not enter real interiors.");Need(starter.Exits.Any(x=>x.Target=="kingsmeadow"),"Starter road to Kingsmeadow missing.");
            Need(data.Npcs.Any(x=>x.Zone==starter.Id&&x.Station=="sawbench"),"Starter sawbench service missing.");
        });
        Test("first mini-boss is contextualized after the road transition",()=>
        {
            var meadow=data.Zone("kingsmeadow");Need(meadow.Species.Contains("rare_hay_golem"),"Kingsmeadow no longer contains the first rare elite.");
            var hunt=data.Quest("starter_hunt");Need(hunt.Prerequisite=="main_02"&&hunt.Objectives.Any(x=>x.Action=="kill"&&x.Target=="rare_hay_golem"),"First rare hunt is not gated after the arrival road.");
        });
        Test("objective guidance covers the starter interaction verbs",()=>
        {
            var p=new RealmEngine(data).CreateCharacter("guide-fixture","Guide Test","vanguard",new());var main=data.Quest("main_01");
            Need(main.Objectives.All(x=>JourneyProgression.ObjectiveGuidance(data,main,x,p).Length>20),"Main starter objectives lack actionable guidance.");
            Need(JourneyProgression.ObjectiveGuidance(data,data.Quest("starter_rune"),data.Quest("starter_rune").Objectives[0],p).Contains("Backpack",StringComparison.Ordinal),"Socket guidance does not name its UI surface.");
        });
        Test("first-hour tracker remains compact and coexists with the quest tracker",()=>
        {
            string hud=File.ReadAllText(Path.Combine(root,"client","Scripts","GameRoot.Hud.cs"));Need(hud.Contains("FirstHourPath",StringComparison.Ordinal)&&hud.Contains("WAYFARER'S PATH",StringComparison.Ordinal),"Compact first-hour tracker missing.");
            Need(hud.Contains("QuestTracker",StringComparison.Ordinal),"First-hour pass replaced the normal quest tracker.");
        });
        Test("maps distinguish route marker and exits without global marker spam",()=>
        {
            string maps=File.ReadAllText(Path.Combine(root,"client","Scripts","Maps.cs"));Need(maps.Contains("World.Waypoint is",StringComparison.Ordinal)&&maps.Contains("ExitMarker",StringComparison.Ordinal),"Minimap route/exit glyph contract missing.");
            Need(maps.Contains("EXITS ·",StringComparison.Ordinal),"Atlas immediate-exit summary missing.");
        });
        Test("rare foes receive a mini-boss presentation",()=>
        {
            string world=File.ReadAllText(Path.Combine(root,"client","Scripts","WorldView.cs"));Need(world.Contains("RARE ·",StringComparison.Ordinal)&&world.Contains("def.Elite",StringComparison.Ordinal),"Rare foe presentation missing.");
            Need(world.Contains("PresentationTint",StringComparison.Ordinal),"City/interior visual identity tint missing.");
        });
        Test("runtime audio exposes all requested feedback families",()=>
        {
            string audio=File.ReadAllText(Path.Combine(root,"client","Scripts","ClientAudio.cs"));foreach(string token in new[]{"PlayFootstep","PlayWeaponImpact","PlayCreature","musicKey=boss?\"boss\":combat?\"combat\"","class_","ambient_"})Need(audio.Contains(token,StringComparison.Ordinal),"Audio runtime binding missing: "+token);
        });
        Test("expanded audio acceptance is independently gated",()=>
        {
            string workflow=File.ReadAllText(Path.Combine(root,".github","workflows","audio-acceptance.yml"));
            Need(workflow.Contains("python tools/build_game_assets.py --audio-only"),"Audio acceptance no longer generates the focused runtime pack.");
            Need(workflow.Contains("python tools/audio_quality_audit.py"),"Audio acceptance no longer runs the permanent quality audit.");
        });
        Console.WriteLine($"FIRST HOUR PRESENTATION: {passed}/{passed+failures.Count} groups passed");if(failures.Count>0)throw new InvalidOperationException("First-hour presentation failures: "+string.Join(" | ",failures));
    }
}
