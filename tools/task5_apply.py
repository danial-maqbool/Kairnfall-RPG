#!/usr/bin/env python3
"""One-shot Task #5 first-hour, presentation, and audio integration. Removed by its publisher."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(rel): return (ROOT/rel).read_text(encoding='utf-8')
def write(rel,text):
    path=ROOT/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')
def replace_once(rel,old,new):
    text=read(rel); count=text.count(old)
    if count!=1: raise RuntimeError(f'{rel}: expected one anchor, found {count}: {old[:100]!r}')
    write(rel,text.replace(old,new,1))
def replace_between(rel,start,end,new):
    text=read(rel); a=text.find(start)
    if a<0: raise RuntimeError(f'{rel}: start anchor missing: {start!r}')
    b=text.find(end,a)
    if b<0: raise RuntimeError(f'{rel}: end anchor missing: {end!r}')
    write(rel,text[:a]+new+text[b:])

write('src/Kairnfall.Core/FirstHourExperience.cs',r'''namespace Kairnfall.Core;

public sealed record FirstHourMilestone(string Id,string Name,string Guidance);

/// <summary>Persistent, low-friction guidance for the first 45–60 minutes. Markers live in Discoveries so old saves remain compatible.</summary>
public static class FirstHourExperience
{
    public const string Prefix="first_hour:";
    public static readonly IReadOnlyList<FirstHourMilestone> Steps =
    [
        new("movement","Get your bearings","Move with WASD. Interact [E] works on nearby people, resources, doors and exits."),
        new("npc","Meet a Wayfarer","Follow the gold ! to a local quest giver and press Interact [E]."),
        new("gather","Gather your first material","Work an oak tree, copper vein or other nearby resource. Your starter tools are already in the backpack."),
        new("craft","Make something useful","Follow A Place by the Fire and make its wooden handle at the sawbench. Crafting [C] shows station and ingredient readiness."),
        new("combat","Win your first fight","Target a nearby creature with Tab, hold basic attack, move out of telegraphs, and try a class art from the hotbar."),
        new("skill","Raise a skill level","Keep doing one real activity until a skill reaches level 2. The green XP bar shows the skill you trained most recently."),
        new("level","Raise your character level","Training any skills contributes to overall level. Reach character level 2 to open the next part of the journey."),
        new("equipment","Improve your equipment","Complete A Spark in the Stone and socket the starter rune, or equip a better-quality drop."),
        new("interior","Enter a real building","Walk through one of Wayfarer's Rest's named doors. Interiors contain the same service NPCs and reciprocal exits."),
        new("transition","Take the western road","Use the road exit to Kingsmeadow. Entrances name their destination and the map [M] shows the route."),
        new("social","See the social layer","Open Social [P]. Use local chat, LFG, or create/join a party; nearby travelers also appear in Recent Players."),
        new("miniboss","Defeat your first rare foe","Hunt the gold RARE elite in Kingsmeadow. Rare enemies are mini-bosses with stronger health, traits and rewards.")
    ];

    public static string Key(string id)=>Prefix+id;
    public static void Mark(Character player,string id)
    {
        if(Steps.Any(x=>x.Id==id)) player.Discoveries.Add(Key(id));
    }
    public static bool Marked(Character player,string id)=>player.Discoveries.Contains(Key(id));

    public static bool Completed(Catalog data,Character player,FirstHourMilestone step)=>step.Id switch
    {
        "movement" or "npc" or "gather" or "craft" or "combat" or "interior" or "transition" or "miniboss" => Marked(player,step.Id),
        "skill" => data.Skills.Any(skill=>Progression.BaseLevel(player,skill.Id)>=2),
        "level" => Progression.PlayerLevel(player)>=2,
        "equipment" => Marked(player,"equipment") || player.Equipment.Values
            .Select(id=>player.Inventory.FirstOrDefault(item=>item.Id==id)).Where(item=>item is not null)
            .Any(item=>item!.Runes.Count>0||item.Rarity>Rarity.Common||item.Affixes.Count>0),
        "social" => Marked(player,"social")||player.RecentPlayers.Count>0||player.Friends.Count>0||player.Party!=""||player.Guild!=""||player.LfgActivity!="",
        _ => false
    };
    public static FirstHourMilestone? Current(Catalog data,Character player)=>Steps.FirstOrDefault(step=>!Completed(data,player,step));
    public static int CompletedCount(Catalog data,Character player)=>Steps.Count(step=>Completed(data,player,step));

    public static void ObserveCommand(Character player,GameCommand command)
    {
        switch(command.Kind)
        {
            case "talk": Mark(player,"npc"); break;
            case "gather": Mark(player,"gather"); break;
            case "craft": Mark(player,"craft"); break;
            case "attack": case "cast": Mark(player,"combat"); break;
            case "equip": case "socket": Mark(player,"equipment"); break;
            case "chat": case "party_create": case "party_invite": case "party_join": case "lfg_set": case "lfg_request": case "friend_invite": case "friend_accept": Mark(player,"social"); break;
        }
    }
    public static void ObserveTransition(Character player,ZoneDef source,ZoneDef target)
    {
        if(target.Kind=="interior") Mark(player,"interior");
        if(source.Kind!="interior"&&target.Kind!="interior"&&target.Id!="wayfarers_rest") Mark(player,"transition");
    }
}
''')

# Authoritative first-hour markers: only successful commands and completed movement/transitions can advance them.
replace_once('src/Kairnfall.Core/RealmEngine.cs',
'''            string message=Dispatch(p,command);
            InvalidateTradeConsents();''',
'''            string message=Dispatch(p,command);
            FirstHourExperience.ObserveCommand(p,command);
            InvalidateTradeConsents();''')
replace_once('src/Kairnfall.Core/RealmEngine.cs',
'''                    p.Position=WorldMap.Move(zone,p.Position,direction.Scale(stats.MoveSpeed*slow*eventMove*dt)); p.Facing=direction;
                    if(slow>0) TryWalkTransition(p,zone,before,direction);''',
'''                    p.Position=WorldMap.Move(zone,p.Position,direction.Scale(stats.MoveSpeed*slow*eventMove*dt)); p.Facing=direction;
                    if(p.Zone=="wayfarers_rest"&&p.Position.Distance(Data.Zone("wayfarers_rest").Spawn)>=1.5) FirstHourExperience.Mark(p,"movement");
                    if(slow>0) TryWalkTransition(p,zone,before,direction);''')
replace_once('src/Kairnfall.Core/RealmEngine.cs',
'''    private void Progress(Character p,string action,string target,int amount=1)
    {
        if(amount<1) return;''',
'''    private void Progress(Character p,string action,string target,int amount=1)
    {
        if(amount<1) return;
        if(action=="kill"&&Data.Mobs.FirstOrDefault(x=>x.Id==target)?.Elite==true) FirstHourExperience.Mark(p,"miniboss");''')
replace_once('src/Kairnfall.Core/RealmEconomy.cs',
'''        p.Zone=target.Id;p.Position=MapTransitionRules.ArrivalPoint(Data,source,exit);
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet))''',
'''        p.Zone=target.Id;p.Position=MapTransitionRules.ArrivalPoint(Data,source,exit);
        FirstHourExperience.ObserveTransition(p,source,target);
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet))''')
replace_once('src/Kairnfall.Core/RealmEconomy.cs',
'''        CancelTradesFor(p.Id); inputs.Remove(p.Id); p.Zone=dest.Id; p.Position=dest.Spawn;
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet))''',
'''        CancelTradesFor(p.Id); inputs.Remove(p.Id); p.Zone=dest.Id; p.Position=dest.Spawn;
        FirstHourExperience.ObserveTransition(p,source,dest);
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet))''')

# Put a contextual rare hunt after the player has carried the first main-quest letter to Dawnreach.
replace_once('content_src/quests.py',
'''    add(data,'starter_ore','Copper by the Road','wayfarers_rest_blacksmith','Use the pickaxe in your inventory to work a copper vein. Bring three pieces of ore back.',[objective('gather','copper_ore',3)],reward='copper_bar',gold=25)''',
'''    add(data,'starter_ore','Copper by the Road','wayfarers_rest_blacksmith','Use the pickaxe in your inventory to work a copper vein. Bring three pieces of ore back.',[objective('gather','copper_ore',3)],reward='copper_bar',gold=25)
    add(data,'starter_hunt','The Straw Giant on the Road','dawnreach_trainer','Travelers report an ancient hay golem stalking the Kingsmeadow road. Treat the rare creature as your first field mini-boss: read its trait, avoid its heavy attacks, and bring it down.',[objective('kill','rare_hay_golem',1,'Defeat the rare hay golem in Kingsmeadow.')],prerequisite='main_02',reward='rune_precision_1',gold=60,minimum=2)''')

# Objective text gives actionable UI/station directions, with current-zone phrasing to avoid redundant navigation noise.
replace_between('src/Kairnfall.Core/JourneyProgression.cs',
'    public static string ObjectiveGuidance(Catalog data,QuestDef quest,ObjectiveDef objective)',
'    public static JourneyQuestLead? LocalQuest',r'''    public static string ObjectiveGuidance(Catalog data,QuestDef quest,ObjectiveDef objective,Character? player=null)
    {
        ZoneDef? zone=null;string suffix="";
        if(objective.Action=="survey")
        {
            foreach(var candidate in data.Zones)
            {
                var landmark=candidate.Buildings.FirstOrDefault(x=>x.Id==objective.Target&&IsLandmark(candidate,x));
                if(landmark is null)continue;zone=candidate;suffix="Survey "+landmark.Name+" with Interact [E].";break;
            }
        }
        else if(objective.Action is "explore" or "chart") { zone=data.Zones.FirstOrDefault(x=>x.Id==objective.Target); suffix=objective.Action=="chart"?"Explore four map sectors, then use Record regional chart on Map [M].":"Use Map [M] to mark the route."; }
        else if(objective.Action=="talk"&&data.Npcs.FirstOrDefault(x=>x.Id==objective.Target) is { } npc) { zone=data.Zones.FirstOrDefault(x=>x.Id==npc.Zone); suffix="Look for the gold !/? and use Interact [E]."; }
        else if(objective.Action is "boss" or "kill"&&data.Mobs.FirstOrDefault(x=>x.Id==objective.Target) is { } mob)
        { zone=data.Zones.FirstOrDefault(x=>x.Boss==mob.Id||x.Species.Contains(mob.Id)); suffix=(mob.Boss?"Boss":"Rare/creature")+" targets show a health bar and tactic cue when selected."; }
        else if(objective.Action=="gather"&&data.Resources.FirstOrDefault(x=>x.Item==objective.Target) is { } resource)
        { zone=data.Zones.FirstOrDefault(x=>x.Resources.Contains(resource.Id)); suffix="Select the resource and use Interact [E]; required tools are shown in the action result."; }
        else if(objective.Action=="deliver"&&data.Npcs.FirstOrDefault(x=>x.Id==quest.Giver) is { } giver)
        { zone=data.Zones.FirstOrDefault(x=>x.Id==giver.Zone); suffix="Return to the quest giver with the item in your backpack."; }
        else if(objective.Action=="craft"&&data.Recipes.FirstOrDefault(x=>x.Output==objective.Target) is { } recipe)
        {
            var stationNpc=data.Npcs.FirstOrDefault(x=>x.Station==recipe.Station);
            zone=stationNpc is null?null:data.Zones.FirstOrDefault(x=>x.Id==stationNpc.Zone);
            suffix="Open Crafting [C] near the "+recipe.Station.Replace('_',' ')+"; the panel shows missing ingredients and skill requirements.";
        }
        else if(objective.Action=="socket") return "Open Backpack [I], select the equipped weapon, then insert the starter rune into its open socket.";
        else if(objective.Action=="plant") return "Use the Farming action on clear surface soil; return when the crop is ready to harvest.";
        if(zone is null)return suffix;
        string lead=player?.Zone==zone.Id?"Here in ":"Go to ";
        return lead+zone.Name+(suffix==""?".":" · "+suffix);
    }

''')

# Compact Wayfarer's Path sits under the ordinary quest tracker rather than covering the world with tutorial markers.
replace_once('client/Scripts/GameRoot.Hud.cs',
'    private Label targetDetail = null!, objectiveText = null!, experiencePacing = null!;',
'    private Label targetDetail = null!, objectiveText = null!, firstHourText = null!, experiencePacing = null!;')
replace_once('client/Scripts/GameRoot.Hud.cs',
'''        objectiveText = Ui.Label("", 14, Ui.Text, true); objectiveText.CustomMinimumSize = new Vector2(264, 0);
        bool expanded = settings.GetValue("hud", "objectives", true).AsBool();
        objectiveText.Visible = expanded;''',
'''        objectiveText = Ui.Label("", 14, Ui.Text, true); objectiveText.CustomMinimumSize = new Vector2(264, 0);
        firstHourText = Ui.Label("", 12, Ui.Gold, true); firstHourText.Name="FirstHourPath"; firstHourText.CustomMinimumSize=new Vector2(264,0);
        bool expanded = settings.GetValue("hud", "objectives", true).AsBool();
        objectiveText.Visible = expanded; firstHourText.Visible=expanded;''')
replace_once('client/Scripts/GameRoot.Hud.cs',
'''            objectiveText.Visible = !objectiveText.Visible;
            objectiveToggle.Text = objectiveText.Visible ? "−" : "+";''',
'''            objectiveText.Visible = !objectiveText.Visible; firstHourText.Visible=objectiveText.Visible;
            objectiveToggle.Text = objectiveText.Visible ? "−" : "+";''')
replace_once('client/Scripts/GameRoot.Hud.cs',
'''        objectiveColumn.AddChild(objectiveText);
        var minimapPanel''',
'''        objectiveColumn.AddChild(objectiveText); objectiveColumn.AddChild(firstHourText);
        var minimapPanel''')
replace_once('client/Scripts/GameRoot.Hud.cs',
'''        var zone = Data.Zone(self.Zone); location.Text = zone.Name;
        location.TooltipText = zone.Layer + " · " + WorldTime.Weather(zone, snap.Time);''',
'''        var zone = Data.Zone(self.Zone); location.Text = zone.Name;
        location.TooltipText = zone.Layer + " · " + WorldTime.Weather(zone, snap.Time) + "\n" + zone.Lore;
        var firstHour=FirstHourExperience.Current(Data,self);
        firstHourText.Text=firstHour is null?"":$"WAYFARER'S PATH · {FirstHourExperience.CompletedCount(Data,self)}/{FirstHourExperience.Steps.Count}\n{firstHour.Name} · {firstHour.Guidance}";''')
replace_once('client/Scripts/GameRoot.Hud.cs',
'JourneyProgression.ObjectiveGuidance(Data,quest,quest.Objectives[next])',
'JourneyProgression.ObjectiveGuidance(Data,quest,quest.Objectives[next],self)')

# Stronger but bounded celebration/audio feedback for arrival, loot, quests, skill levels and overall levels.
replace_once('client/Scripts/GameRoot.Experience.cs',
'''    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
    {
        if (previous is null || previous.Self.Id != current.Self.Id) return;''',
'''    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
    {
        if(previous is null)
        {
            var first=FirstHourExperience.Current(Data,current.Self);
            if(first is not null){Notify("WAYFARER'S REST · Follow the Wayfarer's Path beneath your current objective.");audio?.PlayEffect("quest_accept");}
            return;
        }
        if(previous.Self.Id != current.Self.Id) return;
        if(previous.Self.Zone==current.Self.Zone&&previous.Self.Position.Distance(current.Self.Position)>.12)
            audio?.PlayFootstep(WorldMap.TileAt(Data.Zone(current.Self.Zone),(int)current.Self.Position.X,(int)current.Self.Position.Y));''')
replace_once('client/Scripts/GameRoot.Experience.cs',
'''                World.CombatImpact(afterTarget.Position, 2.1f); audio?.PlayEffect("impact");''',
'''                World.CombatImpact(afterTarget.Position, 2.1f); audio?.PlayWeaponImpact(current.Self,Data); audio?.PlayCreature(Data.Mob(afterTarget.Template),afterTarget.Health<=0);''')
replace_once('client/Scripts/GameRoot.Experience.cs',
'''                Notify("WORLD EVENT · " + value.Name + " · " + Data.Zone(value.Zone).Name); audio?.PlayEffect("ui");''',
'''                Notify("WORLD EVENT · " + value.Name + " · " + Data.Zone(value.Zone).Name); audio?.PlayEffect("event_start");''')
replace_once('client/Scripts/GameRoot.Experience.cs',
'''                Notify(value.Status == "success" ? "EVENT COMPLETE · " + value.Name : "EVENT FAILED · " + value.Name, value.Status == "failure");
                if (value.Zone == current.Self.Zone) World.ClassBurst(value.Position, value.Status == "success" ? Ui.Success : Ui.Danger);''',
'''                Notify(value.Status == "success" ? "EVENT COMPLETE · " + value.Name : "EVENT FAILED · " + value.Name, value.Status == "failure");
                audio?.PlayEffect(value.Status=="success"?"event_complete":"error");
                if (value.Zone == current.Self.Zone) World.ClassBurst(value.Position, value.Status == "success" ? Ui.Success : Ui.Danger);''')
replace_once('client/Scripts/GameRoot.Experience.cs',
'''        if (previous.Self.Zone != current.Self.Zone)
        {
            route.Clear(); pendingInteraction = null; lastInput = Vector2.Zero; StopCombatInput();
        }''',
'''        if (previous.Self.Zone != current.Self.Zone)
        {
            route.Clear(); pendingInteraction = null; lastInput = Vector2.Zero; StopCombatInput();
            var entered=Data.Zone(current.Self.Zone); Notify("ARRIVED · "+entered.Name+" · "+entered.Layer); audio?.PlayEffect("transition");
        }''')
replace_once('client/Scripts/GameRoot.Experience.cs',
'''        if (pickupNotes.Count > 20) pickupNotes.RemoveRange(0, pickupNotes.Count - 20);
        if (changed) RenderPickupFeed();
        foreach (var skill in Data.Skills)
        {
            long beforeXp=previous.Self.SkillXp.GetValueOrDefault(skill.Id);
            long currentXp=current.Self.SkillXp.GetValueOrDefault(skill.Id);
            if(currentXp>beforeXp) lastExperienceSkill=skill.Id;
        }
        int overall = Progression.PlayerLevel(current.Self);''',
'''        if (pickupNotes.Count > 20) pickupNotes.RemoveRange(0, pickupNotes.Count - 20);
        if (changed) { RenderPickupFeed(); audio?.PlayEffect("loot"); }
        foreach(string completed in current.Self.CompletedQuests.Except(previous.Self.CompletedQuests,StringComparer.Ordinal))
        {
            var quest=Data.Quests.FirstOrDefault(x=>x.Id==completed); if(quest is null)continue;
            Notify("QUEST COMPLETE · "+quest.Name); World.ClassBurst(current.Self.Position,Ui.Gold); audio?.PlayEffect("quest_complete");
        }
        foreach (var skill in Data.Skills)
        {
            long beforeXp=previous.Self.SkillXp.GetValueOrDefault(skill.Id);
            long currentXp=current.Self.SkillXp.GetValueOrDefault(skill.Id);
            if(currentXp>beforeXp) lastExperienceSkill=skill.Id;
            int beforeLevel=Progression.SkillLevel(beforeXp),afterLevel=Progression.SkillLevel(currentXp);
            if(afterLevel>beforeLevel)
            {
                Notify("SKILL UP · "+skill.Name+" "+afterLevel); World.ClassBurst(current.Self.Position,Ui.Success); audio?.PlayEffect("skill_up");
            }
        }
        int overall = Progression.PlayerLevel(current.Self);''')
replace_once('client/Scripts/GameRoot.Experience.cs',
'''            Notify("Overall Level " + overall + (explained ? "" : " — training any skill advances your overall level."));
            settings.SetValue("hints", key, true);''',
'''            Notify("LEVEL UP · " + overall + (explained ? "" : " · Training any skill advances your character level."));
            World.ClassBurst(current.Self.Position,Ui.Gold); audio?.PlayEffect("level_up");
            settings.SetValue("hints", key, true);''')

# Expanded runtime audio router: biome/interior ambience, adaptive combat music, footsteps, weapon identity, creature vocals and class cues.
write('client/Scripts/ClientAudio.cs',r'''using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class ClientAudio : Node
{
    private AudioStreamPlayer music=null!,ambience=null!;
    private readonly List<AudioStreamPlayer> voices=[];
    private readonly Dictionary<string,AudioStream> cache=[];
    private readonly HashSet<string> missing=[];
    private string region="",atmosphere="";
    private int voice,stepVariant;
    private double lastFootstep;
    private bool releasing,disabled;
    private float musicVolume=.35f,effectsVolume=.65f;
    public IReadOnlyCollection<string> Missing=>missing;

    public override void _Ready()
    {
        releasing=false;disabled=string.Equals(DisplayServer.GetName(),"headless",StringComparison.OrdinalIgnoreCase);if(disabled)return;
        music=new AudioStreamPlayer();ambience=new AudioStreamPlayer();AddChild(music);AddChild(ambience);
        music.Finished+=RestartMusic;ambience.Finished+=RestartAmbience;
        for(int i=0;i<12;i++){var player=new AudioStreamPlayer();voices.Add(player);AddChild(player);}
        ApplyVolume();PlayMusic("menu");
    }
    private void RestartMusic(){if(!releasing&&IsInsideTree()&&GodotObject.IsInstanceValid(music)&&music.Stream is not null)music.Play();}
    private void RestartAmbience(){if(!releasing&&IsInsideTree()&&GodotObject.IsInstanceValid(ambience)&&ambience.Stream is not null)ambience.Play();}
    public void ReleasePlayback()
    {
        if(releasing)return;releasing=true;
        if(GodotObject.IsInstanceValid(music)){music.Finished-=RestartMusic;music.Stop();music.Stream=null;}
        if(GodotObject.IsInstanceValid(ambience)){ambience.Finished-=RestartAmbience;ambience.Stop();ambience.Stream=null;}
        foreach(var player in voices)if(GodotObject.IsInstanceValid(player)){player.Stop();player.Stream=null;}
        cache.Clear();voices.Clear();region="";atmosphere="";
    }
    public override void _ExitTree()=>ReleasePlayback();
    public void SetVolumes(float melody,float effects){musicVolume=Math.Clamp(melody,0,1);effectsVolume=Math.Clamp(effects,0,1);ApplyVolume();}
    private void ApplyVolume()
    {
        if(music is null||releasing)return;
        music.VolumeDb=Mathf.LinearToDb(Math.Max(.0001f,musicVolume));ambience.VolumeDb=Mathf.LinearToDb(Math.Max(.0001f,effectsVolume*.32f));
        foreach(var player in voices)player.VolumeDb=Mathf.LinearToDb(Math.Max(.0001f,effectsVolume*.50f));
    }
    private AudioStream? Load(string key)
    {
        if(disabled||releasing)return null;if(cache.TryGetValue(key,out var stream))return stream;if(missing.Contains(key))return null;
        string path="res://Assets/audio/"+key+".wav";if(!ResourceLoader.Exists(path)){missing.Add(key);GD.PushWarning("Missing audio: "+path);return null;}
        stream=GD.Load<AudioStream>(path);if(stream is not null)cache[key]=stream;return stream;
    }
    private void PlayMusic(string key)
    {
        if(region==key||music is null||releasing)return;var stream=Load("music_"+key);if(stream is null)return;
        region=key;music.Stop();music.Stream=stream;music.Play();
    }
    private void PlayCue(string key,float pitch=1f)
    {
        if(voices.Count==0||releasing)return;var stream=Load(key);if(stream is null)return;
        var player=voices[voice++%voices.Count];player.Stop();player.Stream=stream;player.PitchScale=Math.Clamp(pitch*(1+(voice%3-1)*.018f),.65f,1.35f);player.Play();
    }
    public void SetRegion(ZoneDef zone,bool boss,bool combat=false)
    {
        if(releasing)return;
        string musicKey=boss?"boss":combat?"combat":zone.Kind=="interior"?"interior":zone.Kind=="city"?zone.Id:zone.Id=="wayfarers_rest"?zone.Id:zone.Layer!="Surface"?"dungeon":"wilderness";
        PlayMusic(musicKey);
        string ambient=zone.Kind=="interior"?"interior":zone.Id=="emberhold"?"forge":zone.Id=="gloamport"?"harbor":zone.Kind=="city"?"city":zone.Layer!="Surface"?(zone.Biome=="ruins"?"ruins":zone.Biome=="arcane_anomaly"?"arcane":"cave"):
            zone.Biome switch{"coast" or "archipelago"=>"coast","ancient_forest"=>"ancient_forest","forest" or "pine_forest"=>"forest","plains" or "farmland"=>"meadow","tundra" or "glacier"=>"tundra","swamp" or "wetlands"=>"swamp","arcane_anomaly"=>"arcane",_=>"wind"};
        if(ambient==atmosphere)return;var stream=Load("ambient_"+ambient);if(stream is null)return;
        atmosphere=ambient;ambience.Stop();ambience.Stream=stream;ambience.Play();
    }
    public void PlayFootstep(Terrain terrain)
    {
        double now=Time.GetTicksMsec()/1000.0;if(now-lastFootstep<.27)return;lastFootstep=now;
        string surface=terrain switch{Terrain.Grass or Terrain.Moss or Terrain.Marsh=>"grass",Terrain.Stone or Terrain.Crystal or Terrain.Wall=>"stone",Terrain.Wood=>"wood",Terrain.Water=>"water",Terrain.Snow=>"snow",_=>"dirt"};
        PlayCue($"step_{surface}_{stepVariant++%3+1}",.98f);
    }
    public void PlayWeaponImpact(Character player,Catalog data)
    {
        string identity="blade";
        if(player.Equipment.TryGetValue("weapon",out var equipped))
        {
            var item=player.Inventory.FirstOrDefault(x=>x.Id==equipped);var def=item is null?null:data.Items.FirstOrDefault(x=>x.Id==item.Template);
            if(def is not null)
            {
                string id=def.Id;
                if(id.Contains("bow",StringComparison.Ordinal)||id.Contains("crossbow",StringComparison.Ordinal))identity="bow";
                else if(id.Contains("mace",StringComparison.Ordinal)||id.Contains("hammer",StringComparison.Ordinal)||id.Contains("maul",StringComparison.Ordinal))identity="blunt";
                else if(id.Contains("staff",StringComparison.Ordinal)||id.Contains("wand",StringComparison.Ordinal)||id.Contains("focus",StringComparison.Ordinal))identity="magic";
            }
        }
        PlayCue($"impact_{identity}_{voice%3+1}");
    }
    public void PlayCreature(MobDef mob,bool death)
    {
        string family=mob.Anatomy.StartsWith("animal:",StringComparison.Ordinal)?"beast":mob.Anatomy.StartsWith("humanoid:",StringComparison.Ordinal)?"humanoid":mob.Anatomy.StartsWith("undead:",StringComparison.Ordinal)?"undead":mob.Anatomy.StartsWith("construct:",StringComparison.Ordinal)?"construct":mob.Anatomy.StartsWith("spirit:",StringComparison.Ordinal)?"spirit":"monster";
        PlayCue($"vocal_{family}_{(death?"death":"hurt")}",death?.88f:1f);
    }
    public void PlayEffect(string action,string classId="")
    {
        switch(action)
        {
            case "attack":PlayCue("effect_swing");return;
            case "cast":case "class_release":PlayCue("class_"+(classId==""?"arcanist":classId));return;
            case "hurt":PlayCue("vocal_humanoid_hurt",.82f);return;
            case "class_ready":PlayCue("effect_ui",1.18f);return;
        }
        string key=action switch
        {
            "gather"=>"gather","loot"=>"loot","chest"=>"chest","buy" or "sell"=>"coins","craft" or "build"=>"hammer","equip" or "unequip" or "socket" or "unsocket"=>"equip",
            "consume" or "rest"=>"drink","quest_accept"=>"quest_accept","quest_complete"=>"quest_complete","skill_up"=>"skill_up","level_up"=>"level_up","transition"=>"transition",
            "event_start"=>"event_start","event_complete"=>"event_complete","error"=>"error","social"=>"social","heal"=>"heal",_=>"ui"
        };
        PlayCue("effect_"+key);
    }
}
''')
replace_once('client/Scripts/GameRoot.cs',
'''            audio?.SetRegion(Data.Zone(self.Zone), Snapshot.Creatures.Any(x => Data.Mob(x.Template).Boss && x.Target == self.Id));''',
'''            bool bossAudio=Snapshot.Creatures.Any(x=>Data.Mob(x.Template).Boss&&x.Target==self.Id);
            bool combatAudio=Snapshot.Time-self.LastCombat<7;
            audio?.SetRegion(Data.Zone(self.Zone),bossAudio,combatAudio);''')
replace_once('client/Scripts/GameRoot.cs','audio?.PlayEffect(command.Kind); lastPageStamp = "";',
'audio?.PlayEffect(command.Kind,Snapshot?.Self.Class??""); lastPageStamp = "";')

# Readable maps: the destination marker and exits use distinct sparse glyphs; atlas details list immediate connections.
replace_once('client/Scripts/Maps.cs',
'''        foreach (var exit in zone.Exits.Where(x => x.Position.Distance(World.Camera) < radius)) Dot(exit.Position, center, scale, new Color("d9d4bb"));''',
'''        foreach (var exit in zone.Exits.Where(x => x.Position.Distance(World.Camera) < radius)) ExitMarker(exit.Position,center,scale,new Color("d9d4bb"));''')
replace_once('client/Scripts/Maps.cs',
'''        DrawColoredPolygon([center + new Vector2(0, -5), center + new Vector2(-4, 4), center + new Vector2(4, 4)], Ui.Text);''',
'''        if(World.Waypoint is { } waypoint&&waypoint.Distance(World.Camera)<radius) Ring(waypoint,center,scale,Ui.Gold,5);
        DrawColoredPolygon([center + new Vector2(0, -5), center + new Vector2(-4, 4), center + new Vector2(4, 4)], Ui.Text);''')
replace_once('client/Scripts/Maps.cs',
'''    private void Dot(Point at, Vector2 center, float scale, Color color)
    {
        var position = center + new Vector2((float)(at.X - World.Camera.X), (float)(at.Y - World.Camera.Y)) * scale;
        if (new Rect2(Vector2.Zero, Size).HasPoint(position)) DrawRect(new Rect2(position - Vector2.One, new Vector2(3, 3)), color);
    }''',
'''    private Vector2 MiniPoint(Point at,Vector2 center,float scale)=>center+new Vector2((float)(at.X-World.Camera.X),(float)(at.Y-World.Camera.Y))*scale;
    private void Dot(Point at,Vector2 center,float scale,Color color)
    {
        var position=MiniPoint(at,center,scale);if(new Rect2(Vector2.Zero,Size).HasPoint(position))DrawRect(new Rect2(position-Vector2.One,new Vector2(3,3)),color);
    }
    private void Ring(Point at,Vector2 center,float scale,Color color,float radius=4)
    {
        var position=MiniPoint(at,center,scale);if(new Rect2(Vector2.Zero,Size).HasPoint(position))DrawArc(position,radius,0,MathF.Tau,16,color,1.5f);
    }
    private void ExitMarker(Point at,Vector2 center,float scale,Color color){Dot(at,center,scale,color);Ring(at,center,scale,color,3.5f);}''')
replace_once('client/Scripts/Maps.cs',
'''            detail.AddChild(Ui.Label(zone.Lore, 14, Ui.Muted, true));''',
'''            detail.AddChild(Ui.Label(zone.Lore, 14, Ui.Muted, true));
            var exits=zone.Exits.Select(x=>Data.Zone(x.Target).Name+" · "+Ui.Words(x.Kind)).Distinct().Take(6).ToArray();
            if(exits.Length>0)detail.AddChild(Ui.Label("EXITS · "+string.Join("   •   ",exits),12,Ui.Text,true));''')

# Environmental presentation stays restrained: city/interior palette identities, story tooltip, readable starter buildings and rare mini-boss labels.
replace_once('client/Scripts/WorldView.cs',
'''    public override void _Process(double delta)
    {''',
'''    private static Color PresentationTint(ZoneDef zone)
    {
        if(zone.Kind=="interior")return zone.Id switch
        {
            "starter_building_0_inside"=>new Color("fff0dc"),"starter_building_1_inside"=>new Color("ffe0c8"),
            "starter_building_2_inside"=>new Color("eee6d8"),"starter_building_3_inside"=>new Color("f2e5d2"),_=>new Color("f3eadc")
        };
        if(zone.Kind=="city")return zone.Id switch
        {
            "dawnreach"=>new Color("fff4dc"),"emberhold"=>new Color("ffe0cf"),"thornhollow"=>new Color("e4f0dd"),
            "frostgate"=>new Color("e2edf2"),"gloamport"=>new Color("dce9e8"),_=>Colors.White
        };
        return Colors.White;
    }

    public override void _Process(double delta)
    {''')
replace_once('client/Scripts/WorldView.cs',
'''        SelfModulate = Colors.White.Lerp(new Color("61758d"), darkness);''',
'''        SelfModulate = PresentationTint(zone).Lerp(new Color("61758d"), darkness);''')
replace_once('client/Scripts/WorldView.cs',
'''        if (zone.Id == "wayfarers_rest" && Math.Abs(x - zone.Spawn.X) < 22 && Math.Abs(y - zone.Spawn.Y) < 22)
            return terrain == Terrain.Grass ? hash % 19 == 0 ? "grass_tuft" : hash % 67 == 0 ? "flowers" : null : null;''',
'''        if(zone.Id=="wayfarers_rest"&&((x==39&&y==45)||(x==45&&y==39)))return "signpost";
        if (zone.Id == "wayfarers_rest" && Math.Abs(x - zone.Spawn.X) < 22 && Math.Abs(y - zone.Spawn.Y) < 22)
            return terrain == Terrain.Grass ? hash % 19 == 0 ? "grass_tuft" : hash % 67 == 0 ? "flowers" : null : null;''')
replace_once('client/Scripts/WorldView.cs',
'''                if (ShowNames && visual.At.Distance(Camera) < 5) Nameplate(visual.At, building.Name, Ui.Muted, 11);''',
'''                double labelRange=zone.Id=="wayfarers_rest"?9:zone.Kind=="city"?7:5;
                if (ShowNames && visual.At.Distance(Camera) < labelRange) Nameplate(visual.At, building.Name, Ui.Muted, 11);''')
replace_once('client/Scripts/WorldView.cs',
'''                if (mob.Health > 0 && (mob.Id == TargetId || mob.Health < def.Health || def.Boss))
                {
                    float height = def.Boss ? -105 : -57;
                    HealthBar(feet + new Vector2(-16, height), mob.Health / def.Health, def.Boss ? new Color("ba7b5b") : new Color("a65052"));
                    Nameplate(mob.Position, def.Name + " · " + def.Level, def.Boss ? Ui.Gold : Ui.Text, height - 5, 9);
                }''',
'''                if (mob.Health > 0 && (mob.Id == TargetId || mob.Health < def.Health || def.Boss || def.Elite))
                {
                    float height = def.Boss ? -105 : def.Elite ? -72 : -57;
                    Color frameColor=def.Boss?new Color("ba7b5b"):def.Elite?new Color("c69b58"):new Color("a65052");
                    HealthBar(feet + new Vector2(-16, height), mob.Health / def.Health, frameColor);
                    Nameplate(mob.Position, (def.Elite?"RARE · ":"") + def.Name + " · " + def.Level, def.Boss||def.Elite ? Ui.Gold : Ui.Text, height - 5, 9);
                }''')

# Replace the small 22-file audio synthesizer with a categorized 96-file deterministic pack and add audio-only generation.
audio_pack=r'''def audio_pack(root:Path):
    sr=22050
    music=['menu','dawnreach','emberhold','thornhollow','frostgate','gloamport','wayfarers_rest','wilderness','dungeon','boss','combat','interior']
    ambient=['meadow','forest','ancient_forest','coast','wind','cave','city','forge','harbor','tundra','swamp','interior','ruins','arcane']
    surfaces=['grass','dirt','stone','wood','water','snow']
    impacts=['blade','blunt','bow','magic']
    vocals=['beast','humanoid','undead','construct','spirit','monster']
    classes=['vanguard','berserker','ranger','rogue','arcanist','warden','templar','spellblade']
    effects=['gather','coins','hammer','equip','drink','ui','click','error','loot','quest_accept','quest_complete','skill_up','level_up','transition','chest','social','event_start','event_complete','heal','swing']
    modes=[(0,2,3,7,10),(0,2,5,7,9),(0,3,5,7,10),(0,2,3,5,7)]
    for k,name in enumerate(music):
        duration=16;count=duration*sr;output=[0.0]*count;mode=modes[k%len(modes)];root_note=45+k%7;step=.25 if name in {'boss','combat'} else .5
        for note in range(round(duration/step)):
            tone=mode[(note*3+note//4+k)%len(mode)]+root_note+(12 if note%4==0 else 0);hz=440*2**((tone-69)/12);start=round(note*step*sr)
            for t in range(min(round(sr*1.25),count-start)):
                secs=t/sr;env=min(1,secs/.012)*math.exp(-secs*(3.5 if name in {'boss','combat'} else 4.4));pulse=math.sin(math.tau*hz*secs)+.27*math.sin(math.tau*hz*2*secs)+.10*math.sin(math.tau*hz*3.01*secs)
                output[start+t]+=.16*env*pulse
        bed=84+7*(k%5)
        for t in range(count):
            secs=t/sr;fade=max(0,min(1,secs/.12,(duration-secs)/.28));output[t]=(output[t]+.023*math.sin(math.tau*bed*secs))*fade
        write_wav(root/f'music_{name}.wav',output)
    for k,key in enumerate(ambient):
        r=random.Random(seed('ambient:'+key));duration=12;count=sr*duration;last=0.0;output=[];base=52+11*(k%7)
        for t in range(count):
            secs=t/sr;last=last*.986+r.uniform(-1,1)*.014;v=last*.78+.018*math.sin(math.tau*base*secs)
            if key in {'forest','ancient_forest','meadow'} and secs%2.7<.16:v+=.055*math.sin(math.tau*(1250+k*73)*secs)*math.sin((secs%2.7)/.16*math.pi)
            if key in {'coast','harbor','swamp'}:v*=.7+.5*math.sin(secs*(1.15+k*.03))**2
            if key in {'forge'} and secs%1.8<.12:v+=.065*math.sin(math.tau*115*secs)*math.exp(-(secs%1.8)*22)
            if key in {'arcane'}:v+=.018*math.sin(math.tau*(310+40*math.sin(secs*.7))*secs)
            fade=max(0,min(1,secs/.18,(duration-secs)/.18));output.append(v*fade)
        write_wav(root/f'ambient_{key}.wav',output)
    for surface in surfaces:
        for variant in range(1,4):
            key=f'{surface}_{variant}';r=random.Random(seed('step:'+key));duration=.18+.015*variant;output=[];hz=78+variant*11+(35 if surface in {'stone','wood'} else 0)
            for t in range(round(sr*duration)):
                secs=t/sr;env=min(1,secs/.004)*math.exp(-secs*(25+variant));noise=r.uniform(-1,1);tone=math.sin(math.tau*hz*secs)
                texture=.19 if surface in {'dirt','grass','snow'} else .12;output.append((tone*.12+noise*texture)*env)
            write_wav(root/f'step_{key}.wav',output)
    for identity in impacts:
        for variant in range(1,4):
            key=f'{identity}_{variant}';r=random.Random(seed('impact:'+key));duration=.27;output=[];hz={'blade':430,'blunt':105,'bow':245,'magic':720}[identity]*(1+(variant-2)*.045)
            for t in range(round(sr*duration)):
                secs=t/sr;env=min(1,secs/.003)*math.exp(-secs*(17 if identity=='magic' else 24));noise=r.uniform(-1,1)*(.16 if identity!='magic' else .04);tone=math.sin(math.tau*hz*secs)+.22*math.sin(math.tau*hz*2.43*secs)
                output.append((tone*.16+noise)*env)
            write_wav(root/f'impact_{key}.wav',output)
    for family in vocals:
        for state in ['hurt','death']:
            key=f'{family}_{state}';r=random.Random(seed('vocal:'+key));duration=.42 if state=='hurt' else .56;output=[];base={'beast':185,'humanoid':145,'undead':95,'construct':110,'spirit':310,'monster':125}[family]
            for t in range(round(sr*duration)):
                secs=t/sr;progress=secs/duration;freq=base*(1+(.28 if state=='hurt' else -.30)*progress)+18*math.sin(secs*23);env=min(1,secs/.012)*max(0,1-progress)**1.35
                output.append((.16*math.sin(math.tau*freq*secs)+.05*math.sin(math.tau*freq*2.1*secs)+r.uniform(-1,1)*.035)*env)
            write_wav(root/f'vocal_{key}.wav',output)
    for k,cls in enumerate(classes):
        duration=.44;output=[];base=310+k*43;r=random.Random(seed('class:'+cls))
        for t in range(round(sr*duration)):
            secs=t/sr;env=min(1,secs/.006)*math.exp(-secs*7);sweep=base*(1+secs*(.7 if k%2 else .35));output.append((.15*math.sin(math.tau*sweep*secs)+.07*math.sin(math.tau*(base*1.5)*secs)+r.uniform(-1,1)*.025)*env)
        write_wav(root/f'class_{cls}.wav',output)
    for k,key in enumerate(effects):
        r=random.Random(seed('effect:'+key));duration=.24 if key not in {'quest_complete','level_up'} else .42;output=[];hz=160+(k*83)%1200
        for t in range(round(sr*duration)):
            secs=t/sr;env=min(1,secs/.006)*math.exp(-secs*(14 if duration>.3 else 23));tone=math.sin(math.tau*hz*secs)+.23*math.sin(math.tau*hz*2.31*secs);noise=r.uniform(-1,1)*(.12 if key in {'gather','hammer','swing'} else .035)
            output.append((tone*.15+noise)*env)
        write_wav(root/f'effect_{key}.wav',output)
    print('ASSETS: synthesized',len(list(root.glob('*.wav'))),'runtime WAV files',flush=True)


'''
replace_between('tools/build_game_assets.py','def audio_pack(root:Path):','def preflight(data):',audio_pack)
replace_once('tools/build_game_assets.py',
'''    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='client/Assets'); args=parser.parse_args()''',
'''    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='client/Assets'); parser.add_argument('--audio-only',action='store_true'); args=parser.parse_args()''')
replace_once('tools/build_game_assets.py',
'''    root.mkdir(parents=True,exist_ok=True)
    catalog=ROOT/'content/catalog.json' ''',
'''    root.mkdir(parents=True,exist_ok=True)
    if args.audio_only:
        audio_pack(root/'audio'); return
    catalog=ROOT/'content/catalog.json' ''')

write('tools/audio_quality_audit.py',r'''#!/usr/bin/env python3
"""Measure shipped WAV files. Automated checks never approve perceived mix, composition, transitions, or artistic quality."""
from __future__ import annotations
import argparse,array,hashlib,json,math,sys,wave
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MUSIC=('menu','dawnreach','emberhold','thornhollow','frostgate','gloamport','wayfarers_rest','wilderness','dungeon','boss','combat','interior')
AMBIENT=('meadow','forest','ancient_forest','coast','wind','cave','city','forge','harbor','tundra','swamp','interior','ruins','arcane')
STEP=tuple(f'{surface}_{n}' for surface in ('grass','dirt','stone','wood','water','snow') for n in range(1,4))
IMPACT=tuple(f'{kind}_{n}' for kind in ('blade','blunt','bow','magic') for n in range(1,4))
VOCAL=tuple(f'{family}_{state}' for family in ('beast','humanoid','undead','construct','spirit','monster') for state in ('hurt','death'))
CLASS=('vanguard','berserker','ranger','rogue','arcanist','warden','templar','spellblade')
EFFECT=('gather','coins','hammer','equip','drink','ui','click','error','loot','quest_accept','quest_complete','skill_up','level_up','transition','chest','social','event_start','event_complete','heal','swing')
GROUPS={'music':MUSIC,'ambient':AMBIENT,'step':STEP,'impact':IMPACT,'vocal':VOCAL,'class':CLASS,'effect':EFFECT}
EXPECTED=tuple(f'{prefix}_{key}' for prefix,keys in GROUPS.items() for key in keys)
RANGES={'music':(15,20),'ambient':(10,14),'step':(.12,.35),'impact':(.16,.45),'vocal':(.25,.70),'class':(.25,.70),'effect':(.15,.60)}

def read_pcm(path:Path):
    with wave.open(str(path),'rb') as stream:
        channels=stream.getnchannels();width=stream.getsampwidth();rate=stream.getframerate();frames=stream.getnframes();compression=stream.getcomptype();raw=stream.readframes(frames)
    if width!=2:return channels,width,rate,frames,compression,[]
    values=array.array('h');values.frombytes(raw)
    if sys.byteorder!='little':values.byteswap()
    return channels,width,rate,frames,compression,[value/32768.0 for value in values]

def metrics(path:Path):
    channels,width,rate,frames,compression,samples=read_pcm(path);row={'file':path.name,'channels':channels,'sample_width':width,'sample_rate':rate,'frames':frames,'compression':compression,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    if not samples:return row
    peak=max(abs(value) for value in samples);rms=math.sqrt(sum(value*value for value in samples)/len(samples));dc=sum(samples)/len(samples);clipped=sum(1 for value in samples if abs(value)>=32767/32768)/len(samples);edge=min(max(1,rate//20),len(samples)//2);seam=sum(abs(samples[index]-samples[-edge+index]) for index in range(edge))/edge
    row.update(duration_seconds=frames/rate if rate else 0,peak=peak,rms=rms,dc_offset=dc,clipped_fraction=clipped,loop_edge_mean_difference=seam);return row

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--audio-root',type=Path,default=ROOT/'client/Assets/audio');parser.add_argument('--output',type=Path,default=ROOT/'artifacts/audio/audio-quality.json');args=parser.parse_args();root=args.audio_root.resolve();output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    errors=[];rows=[];found={path.stem for path in root.glob('*.wav')};missing=sorted(set(EXPECTED)-found);unexpected=sorted(found-set(EXPECTED))
    if missing:errors.append('Missing audio: '+', '.join(missing))
    if unexpected:errors.append('Unexpected audio: '+', '.join(unexpected))
    for key in EXPECTED:
        path=root/(key+'.wav')
        if not path.exists():continue
        row=metrics(path);rows.append(row);prefix=key.split('_',1)[0]
        if row.get('channels')!=1:errors.append(key+': expected mono PCM')
        if row.get('sample_width')!=2:errors.append(key+': expected 16-bit PCM')
        if row.get('sample_rate')!=22050:errors.append(key+': expected 22050 Hz')
        if row.get('compression')!='NONE':errors.append(key+': compressed WAV is not supported')
        if 'rms' not in row:continue
        lo,hi=RANGES[prefix];duration=row['duration_seconds']
        if not lo<=duration<=hi:errors.append(f'{key}: duration {duration:.3f}s outside {lo}-{hi}s')
        if not .03<=row['peak']<=.95:errors.append(f'{key}: peak {row["peak"]:.4f} is out of range')
        if not .002<=row['rms']<=.50:errors.append(f'{key}: RMS {row["rms"]:.5f} is out of range')
        if abs(row['dc_offset'])>.03:errors.append(f'{key}: DC offset {row["dc_offset"]:.5f} is too large')
        if row['clipped_fraction']>.0005:errors.append(f'{key}: clipped fraction {row["clipped_fraction"]:.6f} is too large')
        if prefix in {'music','ambient'} and row['loop_edge_mean_difference']>.20:errors.append(f'{key}: loop boundary mean difference {row["loop_edge_mean_difference"]:.4f} is too large')
    dupes=[digest for digest,count in Counter(row['sha256'] for row in rows).items() if count>1]
    if dupes:errors.append('Duplicate WAV payloads detected: '+str(len(dupes)))
    counts={prefix:sum(1 for row in rows if row['file'].startswith(prefix+'_')) for prefix in GROUPS}
    for prefix,keys in GROUPS.items():
        if counts[prefix]!=len(keys):errors.append(f'{prefix}: expected {len(keys)} files, measured {counts[prefix]}')
    report={'expected_files':len(EXPECTED),'measured_files':len(rows),'category_counts':counts,'unique_payloads':len({row['sha256'] for row in rows}),'human_listening_approved':False,'checks':rows,'errors':errors};output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if rows:print(f'AUDIO_QUALITY: measured {len(rows)} WAV files in {len(GROUPS)} categories; unique {report["unique_payloads"]}; technical errors {len(errors)}.')
    print('AUDIO_QUALITY: automated format, level, clipping, uniqueness and loop checks do not approve perceived mix, transitions, composition, or artistic quality.')
    if errors:
        for error in errors:print('AUDIO ERROR:',error)
        raise SystemExit(1)
if __name__=='__main__':main()
''')
replace_once('tools/validate_game_assets.py',
'''    audio_names={'music_'+key for key in ['menu','dawnreach','emberhold','thornhollow','frostgate','gloamport','wayfarers_rest','wilderness','dungeon','boss']}
    audio_names.update('ambient_'+key for key in ['forest','coast','wind','cave'])
    audio_names.update('effect_'+key for key in ['sword','spell','gather','coins','hammer','equip','drink','ui'])''',
'''    from audio_quality_audit import EXPECTED as AUDIO_EXPECTED
    audio_names=set(AUDIO_EXPECTED)''')
replace_once('.github/workflows/audio-acceptance.yml',
'''      - 'client/Scripts/ClientAudio.cs'
      - 'tools/build_game_assets.py' ''',
'''      - 'client/Scripts/ClientAudio.cs'
      - 'client/Scripts/GameRoot.Experience.cs'
      - 'client/Assets/audio/**'
      - 'tools/build_game_assets.py' ''')
replace_once('.github/workflows/audio-acceptance.yml','python tools/build_game_assets.py | tee artifacts/audio/assets.log','python tools/build_game_assets.py --audio-only | tee artifacts/audio/assets.log')
replace_once('.github/workflows/audio-acceptance.yml','Measure WAV format level clipping and loop boundaries','Measure WAV coverage format level clipping uniqueness and loop boundaries')

write('tools/world_probe/FirstHourPresentationChecks.cs',r'''using System.Runtime.CompilerServices;
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
            var starter=data.Zone("wayfarers_rest");Need(starter.Resources.Count>=6,"Starter resources are too narrow.");Need(starter.Buildings.Count>=4,"Starter village lost named buildings.");
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
        Test("expanded shipped audio pack is present",()=>
        {
            string audioDir=Path.Combine(root,"client","Assets","audio");int count=Directory.Exists(audioDir)?Directory.GetFiles(audioDir,"*.wav").Length:0;Need(count>=96,$"Expected at least 96 shipped WAV files, found {count}.");
        });
        Console.WriteLine($"FIRST HOUR PRESENTATION: {passed}/{passed+failures.Count} groups passed");if(failures.Count>0)throw new InvalidOperationException("First-hour presentation failures: "+string.Join(" | ",failures));
    }
}
''')

write('docs/FIRST_HOUR_PRESENTATION_AUDIO.md',r'''# First-hour presentation and audio pass

The first-hour vertical slice is deliberately layered on the authoritative game instead of creating a separate tutorial mode. `FirstHourExperience` records successful real actions in the character's existing discovery state, while the normal quest tracker remains visible.

The Wayfarer's Path sequence is: movement → NPC → gathering → crafting → combat → skill level → character level → equipment improvement → building entry → map transition → social exposure → rare mini-boss. Existing Wayfarer's Rest interiors, `main_01`, `starter_rune`, the road to Kingsmeadow, and the existing `rare_hay_golem` provide the playable content. `starter_hunt` contextualizes the rare enemy after the first main-quest delivery.

Presentation changes keep navigation sparse: named entrances remain proximity-based, the minimap distinguishes exits from its single route waypoint, atlas details list immediate connections, starter building labels read at a practical distance, and elite creatures use a gold `RARE` health treatment. City/interior tint identities and location lore provide environmental character without adding full-screen markers.

The deterministic runtime audio pack now contains 96 WAV files across music, biome/interior ambience, footsteps, weapon impacts, creature vocals, eight class cues, and interface/celebration effects. Runtime routing includes combat-vs-boss music priority, biome/city ambience, surface footsteps, weapon identity, creature hurt/death vocals, class casts, loot, quest completion, skill-up, level-up, transition and event feedback.

`tools/audio_quality_audit.py` validates exact coverage, format, duration, levels, clipping, DC offset, loop-boundary continuity and payload uniqueness. These automated checks **do not** certify composition, mix, transition feel, human listening quality, artwork quality, or normal-play feel; those remain explicit human acceptance gates.
''')

print('TASK 5 APPLY: first-hour, presentation, and audio source integration complete')
