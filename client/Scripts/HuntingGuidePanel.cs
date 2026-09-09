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
    public string SelectedSite { get; private set; }="";
    private Label overview=null!,details=null!,directions=null!;
    private VBoxContainer list=null!;
    private HuntingRegionMap map=null!;
    private string region="";
    private HuntingPlan plan=null!;
    private readonly Dictionary<string,(string Name,Point Position,string Description)> sites=[];
    public override void _Ready()
    {
        Name="HuntingGuide"; SizeFlagsHorizontal=SizeFlags.ExpandFill;SizeFlagsVertical=SizeFlags.ExpandFill;
        overview=Ui.Label("",15,Ui.Gold,true);AddChild(overview);
        var body=Ui.Row(this);body.SizeFlagsVertical=SizeFlags.ExpandFill;
        list=Ui.Column(Ui.Scroll(body,new Vector2(270,100)));
        var right=Ui.Column(body,true);right.SizeFlagsStretchRatio=1.5f;
        map=new HuntingRegionMap{Data=Data,ReadCharacter=ReadCharacter,CustomMinimumSize=new Vector2(0,240),SizeFlagsHorizontal=SizeFlags.ExpandFill,SizeFlagsVertical=SizeFlags.ExpandFill};right.AddChild(map);
        details=Ui.Label("Choose a hunting area.",14,Ui.Text,true);details.Name="HuntDetails";right.AddChild(details);
        directions=Ui.Label("",14,Ui.Gold,true);directions.Name="HuntDirections";right.AddChild(directions);
        right.AddChild(Ui.Label("Circle: hunting patch · Diamond: boss · Square: exit\nTravel on foot. Q dashes; Tab changes target. Hidden caches are not exposed by this map.",12,Ui.Muted,true));
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
        var zone=Data.Zone(self.Zone);
        if(region!=zone.Id)
        {
            region=zone.Id;plan=HuntingGrounds.For(Data,zone);sites.Clear();Ui.Clear(list);
            overview.Text=zone.Name+" · "+plan.Specialty+"\n"+plan.OrdinaryCount+" ordinary spawn slots · "+plan.Patches.Count+" separate patches";
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
                var target=Data.Zone(exit.Target);string id=exit.Id;
                sites[id]=("Exit: "+target.Name,exit.Position,$"{target.Name} · {target.Layer} · Suggested level {target.Level}\n{target.Lore}");
                var button=Ui.Button("To "+target.Name,()=>SelectSite(id));button.Name="HuntExit_"+id;button.ClipText=true;list.AddChild(button);
            }
            SelectedSite=sites.Keys.FirstOrDefault()??"";map.Zone=zone;map.Plan=plan;
        }
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
        foreach(var exit in zone.Exits)DrawRect(new Rect2(At(exit.Position)-new Vector2(2,2),new Vector2(5,5)),Ui.Gold);
        if(ReadCharacter() is { } self&&self.Zone==zone.Id)DrawCircle(At(self.Position),3,Colors.White);
        DrawArc(At(Selected),7,0,Mathf.Tau,20,Ui.Gold,2);
    }
}

public partial class GameRoot
{
    private void BuildHuntingPage()
    {
        if(page is null||Snapshot is null)return;
        var guide=new HuntingGuidePanel{Data=Data,Assets=Assets,ReadCharacter=()=>Snapshot?.Self};page.AddChild(guide);refreshPage=guide.RefreshSnapshot;
    }
}
