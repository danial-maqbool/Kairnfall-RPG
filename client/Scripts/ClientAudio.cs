using Godot;
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
