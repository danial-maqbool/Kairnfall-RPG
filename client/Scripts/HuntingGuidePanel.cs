using Godot;
using Kairnfall.Core;
using Point=Kairnfall.Core.Point;

namespace Kairnfall.Client;

/// <summary>Public region knowledge, not a scanner for hidden chests or private players.</summary>
public partial class HuntingGuidePanel : VBoxContainer
{
    public Catalog Data { get; set; }=null!;
    public PixelAssets Assets { get; set; }=null!;
    public Func<Character?> ReadCharacter { get; set; }=()=>null;
    public Func<double> ReadTime { get; set; }=()=>0;
    public string SelectedSite { get; private set; }="";
    private Label overview=null!,journey=null!,details=null!,directions=null!;
    private VBoxContainer list=null!;
    private HuntingRegionMap map=null!;
    private string region="";
    private int shownLevel=-1;
    private HuntingPlan plan=null!;
    private readonly Dictionary<string,(string Name,Point Position,string Description)> sites=[];
    public override void _Ready()
    {
        Name="HuntingGuide"; SizeFlagsHorizontal=SizeFlags.ExpandFill;SizeFlagsVertical=SizeFlags.ExpandFill;
        overview=Ui.Label("",15,Ui.Gold,true);AddChild(overview);
        journey=Ui.Label("",13,Ui.Text,true);journey.Name="JourneySuggestion";AddChild(journey);
        var body=Ui.Row(this);body.SizeFlagsVertical=SizeFlags.ExpandFill;
        list=Ui.Column(Ui.Scroll(body,new Vector2(270,100)));
        var right=Ui.Column(body,true);right.SizeFlagsStretchRatio=1.5f;
        map=new HuntingRegionMap{Data=Data,ReadCharacter=ReadCharacter,CustomMinimumSize=new Vector2(0,240),SizeFlagsHorizontal=SizeFlags.ExpandFill,SizeFlagsVertical=SizeFlags.ExpandFill};right.AddChild(map);
        details=Ui.Label("Choose a hunting area.",14,Ui.Text,true);details.Name="HuntDetails";right.AddChild(details);
        directions=Ui.Label("",14,Ui.Gold,true);directions.Name="HuntDirections";right.AddChild(directions);
        right.AddChild(Ui.Label("Circle: hunting patch · Diamond: boss · Gold square: open exit · Red square: locked frontier\nTravel on foot. Q dashes; Tab changes target. Cache clues improve search range but never expose exact cache coordinates on this map.",12,Ui.Muted,true));
        RefreshSnapshot();
    }
    public void SelectSite(string id)
    {
        if(!sites.ContainsKey(id))return;
        SelectedSite=id;map.Selected=sites[id].Position;RefreshSnapshot();
    }
    public void RefreshSnapshot()
    {
        if(!IsInsideTree()||overview is null||ReadCharacter() is not { } self)return;
        var zone=Data.Zone(self.Zone);int playerLevel=Progression.PlayerLevel(self);
        if(region!=zone.Id||shownLevel!=playerLevel)
        {
            region=zone.Id;shownLevel=playerLevel;plan=HuntingGrounds.For(Data,zone);sites.Clear();Ui.Clear(list);
            foreach(var patch in plan.Patches)
            {
                var mob=Data.Mob(patch.Template);
                string drops=string.Join(", ",mob.Drops.Take(3).Select(id=>Data.Item(id).Name));
                string description=$"{mob.Name} · Level {mob.Level} · {Ui.Words(patch.Pattern)} · {patch.Count} spawn slots\nPotential loot: {drops}. Drops and rarity are not guaranteed.";
                sites[patch.Id]=(patch.Name,patch.Position,description);
                string id=patch.Id;var button=Ui.Button(patch.Name,()=>SelectSite(id));button.Name="HuntSite_"+id.Replace('/','_');button.ClipText=true;
                button.Icon=Assets.Frame("mobs/"+mob.Id,0,0,0);button.ExpandIcon=true;button.AddThemeConstantOverride("icon_max_width",28);button.TooltipText=description;list.AddChild(button);
            }
            if(plan.FieldBoss!="")
            {
                var boss=Data.Mob(plan.FieldBoss);string id=zone.Id+"/field-boss";
                sites[id]=("Field boss: "+boss.Name,plan.FieldBossPosition,$"Field boss · {boss.Name} · Level {boss.Level}\nGroup encounter. Watch telegraphed attacks. One field instance; boss respawn is separate from ordinary creatures.");
                var button=Ui.Button("Field boss: "+boss.Name,()=>SelectSite(id));button.Name="FieldBossSite";button.ClipText=true;list.AddChild(button);
            }
            if(zone.Boss!="")
            {
                string id=zone.Id+"/boss";var boss=Data.Mob(zone.Boss);
                var at=WorldMap.FindFree(zone,new Point(zone.Spawn.X+6,zone.Spawn.Y+3));
                sites[id]=("Dungeon boss: "+boss.Name,at,$"{boss.Name} · Level {boss.Level}\n{zone.Layer} dungeon boss. Observe its warning shapes before approaching.");
                var button=Ui.Button(boss.Name,()=>SelectSite(id));button.Name="DungeonBossSite";button.ClipText=true;list.AddChild(button);
            }
            foreach(var exit in zone.Exits)
            {
                var target=Data.Zone(exit.Target);string id=exit.Id;int threat=JourneyProgression.ThreatLevel(Data,target);int gate=JourneyProgression.ExitRequirement(Data,exit);bool locked=playerLevel<gate;
                string status=locked?$"LOCKED · Level {gate}+ · {gate-playerLevel} to go":$"OPEN · Level {gate}+";
                sites[id]=("Exit: "+target.Name,exit.Position,$"{target.Name} · {target.Layer} · Threat {threat} · {status}\n{target.Lore}");
                var button=Ui.Button((locked?"LOCKED · ":"")+"To "+target.Name+" · Lv "+gate+"+",()=>SelectSite(id));button.Name="HuntExit_"+id;button.ClipText=true;button.TooltipText=sites[id].Description;list.AddChild(button);
            }
            SelectedSite=sites.Keys.FirstOrDefault()??"";map.Zone=zone;map.Plan=plan;
        }
        overview.Text=zone.Name+" · "+plan.Specialty+$"\nCharacter {playerLevel} · Threat {JourneyProgression.ThreatLevel(Data,zone)} · "+plan.OrdinaryCount+" ordinary spawn slots · "+plan.Patches.Count+" patches";
        if(ExplorationRewards.Eligible(zone))overview.Text+="\n"+ExplorationRewards.ProgressSummary(self,zone);
        var lead=JourneyProgression.LocalQuest(Data,self,ReadTime());var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);
        journey.Text=lead is not null?$"NEXT LEAD · {lead.QuestName}\nTalk to {lead.GiverName} in {zone.Name}."
            :next is not null?(next.Locked?$"NEXT FRONTIER · {next.ZoneName} · LOCKED at {next.EntryLevel}+ ({next.LevelsNeeded} to go)\nTrain skills, craft, gather or finish local quests while you prepare."
                :$"NEXT FRONTIER · {next.ZoneName} · Threat {next.ThreatLevel} · Entry {next.EntryLevel}+ · READY\nSelect its exit below and follow the route marker.")
            :activity is not null?$"CHANGE OF PACE · {activity.Name} level {Progression.BaseLevel(self,activity.Id)}\n{activity.Action}":"Explore, quest, craft and hunt to build your character.";
        if(ExplorationRewards.Eligible(zone)&&ExplorationRewards.HasClue(self,zone)&&!ExplorationRewards.CacheDiscovered(self,zone))
            journey.Text+=$"\nCACHE CLUE · Search off-road. The regional cache appears in-world when you are within {ExplorationRewards.CacheClueRevealRadius:0} tiles.";
        else if(ExplorationRewards.Eligible(zone)&&ExplorationRewards.CacheDiscovered(self,zone)&&!ExplorationRewards.CacheOpened(self,zone))
            journey.Text+="\nCACHE FOUND · Return to the discovered chest and open it for the first-cache bonus.";
        if(sites.TryGetValue(SelectedSite,out var selected))
        {
            details.Text=selected.Description;map.Selected=selected.Position;
            double dx=selected.Position.X-self.Position.X,dy=selected.Position.Y-self.Position.Y;
            string vertical=Math.Abs(dy)>2?(dy<0?"north":"south"):"",horizontal=Math.Abs(dx)>2?(dx<0?"west":"east"):"";
            string direction=vertical+(vertical!=""&&horizontal!=""?"-":"")+horizontal;
            directions.Text=selected.Position.Distance(self.Position)<3?"You are near this site.":$"{selected.Position.Distance(self.Position):0} tiles {direction} · ({selected.Position.X:0}, {selected.Position.Y:0})";
        }
        map.QueueRedraw();
    }
}

public partial class HuntingRegionMap : Control
{
    public Catalog Data { get; set; }=null!;
    public Func<Character?> ReadCharacter { get; set; }=()=>null;
    public ZoneDef? Zone { get; set; }
    public HuntingPlan? Plan { get; set; }
    public Point Selected { get; set; }
    public override void _Ready(){MouseFilter=MouseFilterEnum.Ignore;TextureFilter=TextureFilterEnum.Nearest;}
    public override void _Draw()
    {
        if(Zone is not { } zone||Plan is not { } plan)return;
        DrawRect(new Rect2(Vector2.Zero,Size),Ui.Ink);
        float scale=Math.Min((Size.X-12)/zone.Width,(Size.Y-12)/zone.Height);if(scale<=0)return;
        var origin=(Size-new Vector2(zone.Width,zone.Height)*scale)/2;
        Vector2 At(Point p)=>origin+new Vector2((float)p.X,(float)p.Y)*scale;
        int step=zone.Width>128?3:2;
        for(int y=0;y<zone.Height;y+=step)for(int x=0;x<zone.Width;x+=step)
        {
            var tile=WorldMap.TileAt(zone,x,y);
            DrawRect(new Rect2(origin+new Vector2(x,y)*scale,new Vector2(step,step)*scale),MinimapView.TerrainColor(tile));
        }
        foreach(var patch in plan.Patches)DrawArc(At(patch.Position),Math.Max(3,(float)patch.Radius*scale),0,Mathf.Tau,16,new Color("b5bc87"),1);
        void Boss(Point p){var at=At(p);DrawPolyline([at+new Vector2(0,-5),at+new Vector2(5,0),at+new Vector2(0,5),at+new Vector2(-5,0),at+new Vector2(0,-5)],Ui.Danger,2);}
        if(plan.FieldBoss!="")Boss(plan.FieldBossPosition);
        if(zone.Boss!="")Boss(WorldMap.FindFree(zone,new Point(zone.Spawn.X+6,zone.Spawn.Y+3)));
        foreach(var exit in zone.Exits)
        {
            bool locked=ReadCharacter() is { } viewer&&Progression.PlayerLevel(viewer)<JourneyProgression.ExitRequirement(Data,exit);
            DrawRect(new Rect2(At(exit.Position)-new Vector2(2,2),new Vector2(5,5)),locked?Ui.Danger:Ui.Gold);
        }
        if(ReadCharacter() is { } self&&self.Zone==zone.Id)DrawCircle(At(self.Position),3,Colors.White);
        DrawArc(At(Selected),7,0,Mathf.Tau,20,Ui.Gold,2);
    }
}

public partial class GameRoot
{
    private void BuildHuntingPage()
    {
        if(page is null||Snapshot is null)return;
        var guide=new HuntingGuidePanel{Data=Data,Assets=Assets,ReadCharacter=()=>Snapshot?.Self,ReadTime=()=>Snapshot?.Time??0};page.AddChild(guide);refreshPage=guide.RefreshSnapshot;
    }
}
