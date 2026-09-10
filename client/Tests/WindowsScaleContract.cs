using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>Windows content-scale and native input fixture. Physical monitor DPI approval remains separate.</summary>
public partial class WindowsScaleContract : Node
{
    private int checks;
    private static T Field<T>(GameRoot game,string name)=> (T)typeof(GameRoot).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(game)!;
    private static object? Call(GameRoot game,string method,params object?[] args)=>typeof(GameRoot).GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
    private async Task Frame()=>await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
    private void Require(bool value,string message)
    {
        if(!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS WINDOWS SCALE: "+message);
    }
    private bool Contained(Control control)
    {
        var viewport=GetViewport().GetVisibleRect(); var rect=control.GetGlobalRect();
        return control.IsVisibleInTree()&&rect.Size.X>0&&rect.Size.Y>0&&rect.Position.X>=viewport.Position.X-1&&rect.Position.Y>=viewport.Position.Y-1&&rect.End.X<=viewport.End.X+1&&rect.End.Y<=viewport.End.Y+1;
    }
    private async Task Tap(Key key)
    {
        using(var press=new InputEventKey{PhysicalKeycode=key,Keycode=key,Pressed=true}) Input.ParseInputEvent(press);
        Input.FlushBufferedEvents(); await Frame();
        using(var release=new InputEventKey{PhysicalKeycode=key,Keycode=key,Pressed=false}) Input.ParseInputEvent(release);
        Input.FlushBufferedEvents(); await Frame(); await Frame();
    }
    private async Task Click(Control control)
    {
        var at=control.GetGlobalRect().GetCenter();
        using(var press=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left,ButtonMask=MouseButtonMask.Left,Pressed=true}) GetViewport().PushInput(press,true);
        await Frame();
        using(var release=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left,Pressed=false}) GetViewport().PushInput(release,true);
        await Frame(); await Frame();
    }

    public override async void _Ready()
    {
        GameRoot? game=null;
        try
        {
            Require(OS.GetName()=="Windows","Contract runs on the Windows engine build");
            var data=PixelAssets.LoadCatalog(); var realm=new RealmEngine(data);
            var self=realm.CreateCharacter("windows-scale","Windows Scale","vanguard",new()); realm.Active.Add(self.Id);
            using(var scene=GD.Load<PackedScene>("res://Main.tscn")) game=scene.Instantiate<GameRoot>();
            AddChild(game); game.SetProcess(false); await Frame(); await Frame();
            Field<Control>(game,"frontend").Hide(); game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id),Loot=[]}); Call(game,"UpdateHud"); await Frame();

            foreach(float scale in new[]{1.25f,1.50f})
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            {
                GetWindow().Size=size; GetWindow().ContentScaleSize=size; GetWindow().ContentScaleFactor=scale; await Frame(); await Frame();
                string label=$"{size.X}x{size.Y} at {scale*100:F0}%";
                Require(Math.Abs(GetWindow().ContentScaleFactor-scale)<.001,label+" content scale is active");
                Require(Contained(Field<ProgressBar>(game,"characterExperienceBar")),label+" Character XP bar fits Vitals");
                Require(Contained(Field<ProgressBar>(game,"skillExperienceBar")),label+" Skill XP bar fits Vitals");
                var minimap=game.FindChildren("MinimapPanel","Control",true,false).OfType<Control>().Single(); Require(Contained(minimap),label+" minimap fits the viewport");
                Require(Field<Button[]>(game,"hotbarButtons").All(Contained),label+" hotbar fits the viewport");

                await Tap(Key.I); Require(Field<string>(game,"currentPage")=="Inventory",label+" physical I opens Inventory");
                var action=game.FindChildren("PrimaryEquipmentAction","Button",true,false).Cast<Button>().Single();
                Require(Contained(action)&&action.Size.Y>=40,label+" equipment comparison action remains reachable");
                await Tap(Key.Escape); Require(Field<string>(game,"currentPage")=="",label+" physical Escape closes Inventory");

                Call(game,"OpenPage","Crafting"); await Frame(); await Frame(); await Frame();
                Require(Contained(Field<PanelContainer>(game,"gameWindow")),label+" Crafting window fits the viewport");
                Require(game.FindChildren("*","CraftingGuidePanel",true,false).Count>0||game.FindChildren("CraftingGuide","VBoxContainer",true,false).Count>0,label+" Crafting page is constructed");
                Call(game,"ClosePage"); await Frame(); await Frame();

                var mapButton=game.FindChildren("*","Button",true,false).OfType<Button>().First(button=>button.Text.StartsWith("World map",StringComparison.Ordinal));
                Require(Contained(mapButton),label+" minimap map button is reachable"); await Click(mapButton);
                Require(Field<string>(game,"currentPage")=="Map",label+" physical mouse click opens the world map");
                Require(Contained(Field<PanelContainer>(game,"gameWindow")),label+" world map window fits the viewport");
                Call(game,"ClosePage"); await Frame(); await Frame();
            }
            GetWindow().ContentScaleFactor=1;
            GD.Print($"WINDOWS_SCALE_CONTRACT: {checks} checks passed for 125% and 150% emulation at 1280x720 and 1920x1080. Physical Windows monitor DPI approval is not inferred.");
            await NativeTestLifetime.ReleaseSceneAsync(this,game); GetTree().Quit(0);
        }
        catch(Exception error)
        {
            GD.PushError("WINDOWS_SCALE_CONTRACT: "+error);
            if(game is not null&&GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this,game);
            GetTree().Quit(1);
        }
    }
}
