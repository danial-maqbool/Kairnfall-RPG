using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Real Godot drawing and layout fixtures, not an account playthrough.</summary>
public partial class VisualPresentationContract : Node
{
    private int checks;
    private void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS VISUAL: " + message);
    }
    private static object? Call(GameRoot game, string name, params object?[] args)
        => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private static T Field<T>(GameRoot game, string name)
        => (T)typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private async Task Capture(string name)
    {
        if (DisplayServer.GetName() == "headless") return;
        await Frame(); await Frame();
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS")
            ?? ProjectSettings.GlobalizePath("user://visual-review");
        System.IO.Directory.CreateDirectory(root);
        using var image = GetViewport().GetTexture().GetImage();
        Check(image.SavePng(System.IO.Path.Combine(root, name + ".png")) == Error.Ok, "Saved rendered frame " + name);
    }
    private bool Contained(Control control)
    {
        Rect2 bounds = GetViewport().GetVisibleRect(), rect = control.GetGlobalRect();
        return control.IsVisibleInTree() && rect.Size.X > 0 && rect.Size.Y > 0
            && rect.Position.X >= -1 && rect.Position.Y >= -1
            && rect.End.X <= bounds.End.X + 1 && rect.End.Y <= bounds.End.Y + 1;
    }
    public override async void _Ready()
    {
        GameRoot? game = null; EquipmentGallery? gallery = null;
        try
        {
            Check(SpritePoseRules.Anchor(64) == new Vector2(32,55), "Humanoid art and client use the same integer anchor");
            Check(SpritePoseRules.Anchor(128) == new Vector2(64,110), "Boss frames retain their separate scale");
            Check(SpritePoseRules.Direction(new Point(.99,1),2)==2, "Near-diagonal movement keeps its facing row");
            Check(SpritePoseRules.Direction(new Point(.2,1),2)==0, "A deliberate turn switches the facing row");
            Check(SpritePoseRules.Direction(new Point(0,0),1)==1, "Stopping does not invent a new facing");
            Check(SpritePoseRules.Direction(new Point(double.NaN,0),3)==3, "Invalid presentation input retains a valid row");
            double whole = SpritePoseRules.AdvanceWalk(0,1.2), split=0;
            for(int i=0;i<12;i++) split=SpritePoseRules.AdvanceWalk(split,.1);
            Check(Math.Abs(whole-split)<.000001, "Walk phase is independent of packet subdivision");
            for(int direction=0;direction<4;direction++)
            {
                var layers=SpritePoseRules.Layers(direction);
                Check(layers.Count==layers.Distinct().Count(), "Each equipment layer draws once in direction " + direction);
                Check(layers.Contains("ring"), "Equipped ring presentation is not silently omitted");
            }
            var north=SpritePoseRules.Layers(3).ToList();
            Check(north.IndexOf("cloak")>north.IndexOf("chest"), "The north-facing cloak covers the back of the armor");
            Check(north.IndexOf("weapon")<north.IndexOf("body"), "The north-facing weapon uses rear occlusion");
            using(var packed=GD.Load<PackedScene>("res://Main.tscn")) game=packed.Instantiate<GameRoot>();
            AddChild(game); game.SetProcess(false); await Frame();
            var realm=new RealmEngine(game.Data); var self=realm.CreateCharacter("visual-fixture","Visual Review","vanguard",new());
            realm.Active.Add(self.Id);
            Field<Control>(game,"frontend").Hide();
            void Refresh()
            {
                game.World.Accept(new TransportPacket { Snapshot=realm.Snapshot(self.Id), Loot=realm.VisibleLoot(self.Id) });
                Call(game,"UpdateHud");
            }
            Refresh(); Call(game,"SetInitialHotbar");
            string description = (string)Call(game,"ItemDescription",self.Inventory[0],true)!;
            Check(!description.Contains('\r') && description.Contains('\n'),
                "Item statistics use native LF line endings on Windows without doubled paragraph gaps");
            var gradeGallery=new EquipmentTierGallery { Data=game.Data,Assets=game.Assets };
            AddChild(gradeGallery); await Frame();
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            {
                GetWindow().Size=size; GetWindow().ContentScaleSize=size; await Frame();
                foreach(int level in new[]{5,27,55,75,100})
                foreach(var pose in new[]{(State:0,Frame:0),(State:1,Frame:3),(State:2,Frame:3),(State:5,Frame:7)})
                {
                    gradeGallery.TierLevel=level; gradeGallery.State=pose.State; gradeGallery.FrameNumber=pose.Frame; gradeGallery.QueueRedraw();
                    await Capture($"equipment-tier-{level}-{size.X}-state-{pose.State}");
                }
            }
            Check(game.Assets.Missing.Count==0,"Every requested tier weapon and armor renders without missing assets");
            gradeGallery.QueueFree(); await Frame(); await Frame();
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            {
                GetWindow().Size=size; GetWindow().ContentScaleSize=size;
                await Frame(); await Frame(); Refresh();
                string suffix=size.X.ToString();
                game.World.Zoom=1; await Frame(); await Frame();
                await Capture("01-village-"+suffix);
                foreach(string page in new[]{"Inventory","Character","Skills","Abilities","Equipment Guide","Crafting","Map","Hunting"})
                {
                    Call(game,"OpenPage",page); await Frame(); await Frame();
                    Check(Contained(Field<PanelContainer>(game,"gameWindow")), page+" window fits "+size);
                    if(page=="Inventory")
                    {
                        var action=game.FindChildren("PrimaryEquipmentAction","Button",true,false).Cast<Button>().Single();
                        Check(Contained(action), "Equip action remains reachable at "+size);
                    }
                    if(page=="Equipment Guide" || page=="Crafting")
                    {
                        string actionName=page=="Crafting"?"CraftPrimaryAction":"GearRecipeAction";
                        var action=game.FindChildren(actionName,"Button",true,false).Cast<Button>().Single();
                        Check(Contained(action),actionName+" stays reachable at "+size);
                    }
                    await Capture("ui-"+page.ToLowerInvariant().Replace(' ','-')+"-"+suffix);
                    Call(game,"ClosePage"); await Frame(); await Frame();
                }
            }
            GetWindow().Size=new Vector2I(1920,1080); GetWindow().ContentScaleSize=new Vector2I(1920,1080);
            foreach(var door in game.Data.Zone("wayfarers_rest").Exits.Where(x=>x.Kind=="door"))
            {
                self.Zone=door.Target; self.Position=door.Arrival; Refresh();
                await Capture("interior-"+door.Target);
            }
            foreach(string region in new[]{"wayfarers_rest","kingsmeadow","thistle_woods","broken_mill","umbral_crossroads","wayfarer_burrows","silkroot_den"})
            {
                var zone=game.Data.Zone(region);var plan=HuntingGrounds.For(game.Data,zone);
                self.Zone=region; self.Position=plan.Patches.First().Position; Refresh(); await Frame(); await Frame();
                await Capture("hunting-"+region);
                Call(game,"OpenPage","Hunting"); await Frame(); await Capture("hunt-guide-"+region); Call(game,"ClosePage"); await Frame();
            }
            self.Zone="wayfarers_rest"; self.Position=game.Data.Zone(self.Zone).Spawn; Refresh();
            var previous=self.Position;
            for(int n=0;n<12;n++)
            {
                self.Position=WorldMap.Move(game.Data.Zone(self.Zone),self.Position,new Point(.06,0));
                self.Facing=new Point(1,0); Refresh(); await Frame(); await Frame();
            }
            Check(self.Position.Distance(previous)>0, "The movement fixture advances through valid world coordinates");
            await Capture("02-player-walk");
            game.World.Animate(self.Id,2,.65); await Capture("03-player-attack");
            game.World.Animate(self.Id,3,.65); await Capture("04-player-cast");
            await ItemCommerceUiChecks.Run(this,game,Check);
            await NativeTestLifetime.ReleaseSceneAsync(this,game); game=null;
            gallery=new EquipmentGallery(); AddChild(gallery); gallery.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);
            await Frame();
            for(int state=0;state<6;state++)
            {
                gallery.State=state;
                foreach(int frame in new[]{0,1,2,3,4,7})
                {
                    gallery.FrameNumber=frame; gallery.QueueRedraw();
                    await Capture($"equipment-state-{state}-frame-{frame}");
                }
            }
            Check(gallery.Assets.Missing.Count==0,"All requested equipment layers exist in the actual renderer");
            gallery.Creatures = true;
            for(int state=0;state<6;state++)
            {
                gallery.State=state;
                foreach(int frame in new[]{0,1,2,3,4,7})
                {
                    gallery.FrameNumber=frame; gallery.QueueRedraw();
                    await Capture($"mobs-state-{state}-frame-{frame}");
                }
            }
            Check(gallery.Assets.Missing.Count==0,"All eight common creature review sheets exist in the actual renderer");
            gallery.Icons=true; gallery.QueueRedraw(); await Capture("17-item-icons");
            Check(gallery.Assets.Missing.Count==0,"Representative item and chest icons exist in the native renderer");
            gallery.QueueFree(); await Frame(); await Frame(); gallery=null;
            GD.Print($"VISUAL_PRESENTATION_CONTRACT: {checks} checks passed. Rendered fixtures; visual approval and Windows DPI testing remain separate.");
            GetTree().Quit();
        }
        catch(Exception error)
        {
            GD.PushError("VISUAL_PRESENTATION_CONTRACT: "+error);
            if(gallery is not null && GodotObject.IsInstanceValid(gallery)) gallery.QueueFree();
            if(game is not null && GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this,game);
            GetTree().Quit(1);
        }
    }
}

public partial class EquipmentGallery : Control
{
    public PixelAssets Assets { get; } = new();
    public int State { get; set; }
    public int FrameNumber { get; set; }
    public bool Creatures { get; set; }
    public bool Icons { get; set; }
    private readonly string[] families=["sword","axe","mace","bow","staff","spear","wand","tome"];
    private readonly string[] species=["field_rat","wild_hare","pine_wolf","feral_boar","black_bear","wood_spider","sea_turtle","polar_bear"];
    private readonly List<Dictionary<string,string>> gear=[];
    private readonly List<(string Key,string Name)> icons=[];
    public override void _Ready()
    {
        MouseFilter=MouseFilterEnum.Ignore; TextureFilter=TextureFilterEnum.Nearest;
        var data=PixelAssets.LoadCatalog();
        foreach(string family in families)
        {
            var item=data.Items.First(x=>x.Slot=="weapon" && x.Tags.Contains(family));
            icons.Add(("items/"+item.Id,item.Name));
            var equipment=new Dictionary<string,string>{{"weapon",item.Id}};
            foreach(string slot in new[]{"helmet","chest","legs","boots","cloak","gloves"})
                equipment[slot]=data.Items.First(x=>x.Slot==slot).Id;
            if(family is "sword" or "axe" or "mace") equipment["offhand"]=data.Items.First(x=>x.Slot=="offhand" && x.Tags.Contains("shield")).Id;
            gear.Add(equipment);
        }
        foreach(string slot in new[]{"offhand","chest","helmet","gloves"})
        {
            var item=data.Items.First(x=>x.Slot==slot); icons.Add(("items/"+item.Id,item.Name));
        }
        foreach(string type in new[]{"potion","ore","wood","animal_material","food","rune"})
        {
            var item=data.Items.First(x=>x.Type==type); icons.Add(("items/"+item.Id,item.Name));
        }
        icons.Add(("chests/ancient_closed","Ancient chest"));
    }
    public override void _Draw()
    {
        DrawRect(new Rect2(Vector2.Zero,Size),new Color("20232a"));
        if(Icons)
        {
            DrawString(ThemeDB.FallbackFont,new Vector2(24,28),"KAIRNFALL · ITEM ICON RENDER FIXTURE",HorizontalAlignment.Left,-1,18,Ui.Text);
            for(int i=0;i<icons.Count;i++)
            {
                var at=new Vector2(24+(i%7)*268,70+(i/7)*310);
                var texture=Assets.Texture(icons[i].Key);
                DrawRect(new Rect2(at,new Vector2(250,280)),new Color("303238"));
                if(texture is not null)
                {
                    float scale=Math.Max(1,MathF.Floor(160/Math.Max(texture.GetWidth(),texture.GetHeight())));
                    var size=texture.GetSize()*scale;
                    DrawTextureRect(texture,new Rect2(at+new Vector2((250-size.X)/2,40),size),false);
                }
                DrawString(ThemeDB.FallbackFont,at+new Vector2(10,245),icons[i].Name,HorizontalAlignment.Left,230,14,Ui.Text);
            }
            return;
        }
        DrawString(ThemeDB.FallbackFont,new Vector2(24,28),"KAIRNFALL · "+(Creatures ? "COMMON CREATURE" : "EQUIPMENT")+" RENDER FIXTURE · state "+State+" / frame "+FrameNumber,HorizontalAlignment.Left,-1,18,Ui.Text);
        if(gear.Count!=8) return;
        float width=(Size.X-32)/8, height=(Size.Y-60)/4;
        for(int direction=0;direction<4;direction++) for(int column=0;column<8;column++)
        {
            var origin=new Vector2(16+column*width,46+direction*height);
            DrawRect(new Rect2(origin+Vector2.One,new Vector2(width-8,height-8)),new Color("303238"));
            var feet=(origin+new Vector2(width/2,height-43)).Round();
            DrawSetTransform(feet,0,new Vector2(2,2));
            if(Creatures) Assets.DrawFrame(this,"mobs/"+species[column],Vector2.Zero,State,direction,FrameNumber);
            else Assets.DrawPerson(this,new Appearance{Body=column%2,Skin=2,Hair=0,HairColor=1},gear[column],Vector2.Zero,State,direction,FrameNumber);
            DrawSetTransform(Vector2.Zero);
            DrawString(ThemeDB.FallbackFont,origin+new Vector2(10,height-18),(Creatures ? species[column] : families[column])+" · "+new[]{"S","W","E","N"}[direction],HorizontalAlignment.Left,-1,14,Ui.Text);
        }
    }
}
