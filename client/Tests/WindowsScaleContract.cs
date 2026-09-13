using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>Windows content-scale, accessibility, modal-focus, and native input fixture. Physical monitor DPI approval remains separate.</summary>
public partial class WindowsScaleContract : Node
{
    private int checks;
    private static T Field<T>(GameRoot game,string name)=> (T)typeof(GameRoot).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(game)!;
    private static object? Call(GameRoot game,string method,params object?[] args)=>typeof(GameRoot).GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
    private static void AttachConnectedFixture(GameRoot game,GameConnection connection)
    {
        typeof(GameConnection).GetField("connected",BindingFlags.Instance|BindingFlags.NonPublic)!.SetValue(connection,true);
        typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game,connection);
    }
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
        using(var press=new InputEventKey{PhysicalKeycode=key,Keycode=key,Pressed=true}) GetViewport().PushInput(press,true);
        await Frame();
        using(var release=new InputEventKey{PhysicalKeycode=key,Keycode=key,Pressed=false}) GetViewport().PushInput(release,true);
        await Frame(); await Frame();
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
        GameConnection? connection=null;
        try
        {
            Require(OS.GetName()=="Windows","Contract runs on the Windows engine build");
            var data=PixelAssets.LoadCatalog(); var realm=new RealmEngine(data);
            var self=realm.CreateCharacter("windows-scale","Windows Scale","vanguard",new()); realm.Active.Add(self.Id);
            using(var scene=GD.Load<PackedScene>("res://Main.tscn")) game=scene.Instantiate<GameRoot>();
            AddChild(game); game.SetProcess(false); await Frame(); await Frame();
            Field<Control>(game,"frontend").Hide(); GetViewport().GuiReleaseFocus(); game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id),Loot=[]}); Call(game,"UpdateHud"); await Frame();
            // The fixture uses a local authoritative snapshot and no remote server. Mark a loopback
            // transport fixture connected so the real GameRoot input gate follows its in-world path.
            connection=new GameConnection("http://127.0.0.1:1"); AttachConnectedFixture(game,connection);

            var backgroundFocus=new Button{Name="UiUxBackgroundFocus",Text="Background focus fixture",FocusMode=Control.FocusModeEnum.All};
            Field<Control>(game,"hud").AddChild(backgroundFocus); backgroundFocus.GrabFocus(); await Frame();
            Call(game,"OpenPage","Settings"); await Frame(); await Frame(); Call(game,"SynchronizeModalUx"); await Frame();
            var blocker=game.FindChildren("ModalInputBlocker","ColorRect",true,false).Cast<ColorRect>().Single();
            Require(Contained(blocker),"Modal input blocker covers the visible viewport");
            Require(backgroundFocus.FocusMode==Control.FocusModeEnum.None,"An open panel removes background HUD controls from keyboard focus traversal");
            var close=Field<PanelContainer>(game,"gameWindow").FindChildren("*","Button",true,false).OfType<Button>().First(button=>button.Text.StartsWith("Close",StringComparison.Ordinal));
            Require(GetViewport().GuiGetFocusOwner()==close,"A newly opened panel seeds keyboard focus on its close control");
            var selector=game.FindChildren("TextScaleSelector","OptionButton",true,false).Cast<OptionButton>().Single();
            Require(selector.ItemCount==4,"Settings exposes bounded text-size choices");
            Require(game.FindChildren("*","Label",true,false).OfType<Label>().Any(label=>label.Text.Contains("Shift+Tab",StringComparison.Ordinal)),"Settings explains keyboard panel navigation");
            Call(game,"ApplyUiTextScale",1.25d,false); await Frame();
            Require(Math.Abs(Ui.TextScale-1.25f)<.001f,"Text scale applies at 125 percent");
            Require(Field<Label>(game,"characterTitle").GetThemeFontSize("font_size")==Ui.ScaledFont(17),"Existing HUD text follows the accessibility scale");
            var freshScaledLabel=Ui.Label("Fresh scaled label",16); game.AddChild(freshScaledLabel); await Frame();
            Require(freshScaledLabel.GetThemeFontSize("font_size")==Ui.ScaledFont(16),"Newly created panel and tooltip text inherit the active accessibility scale");
            freshScaledLabel.QueueFree();
            Call(game,"Notify","A menu action failed.",true); Call(game,"EnsureAccessibleNotice");
            Require(Field<Label>(game,"notice").Text.StartsWith("Error · ",StringComparison.Ordinal),"Error feedback remains understandable without relying on color alone");
            Call(game,"ClosePage"); Call(game,"SynchronizeModalUx"); await Frame();
            Require(backgroundFocus.FocusMode==Control.FocusModeEnum.All&&GetViewport().GuiGetFocusOwner()==backgroundFocus,"Closing a panel restores its previous keyboard focus target");
            Call(game,"ApplyUiTextScale",1d,false); await Frame();

            int baseActivations=0;
            var baseSlot=new ItemSlot{Name="KeyboardItemSlot",Item=self.Inventory.First(),Clicked=()=>baseActivations++};
            game.AddChild(baseSlot); await Frame(); baseSlot.GrabFocus(); await Tap(Key.Space);
            Require(baseActivations==1,"Generic item slots are keyboard reachable and activate with Space");
            baseSlot.QueueFree(); await Frame();

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

                GetViewport().GuiReleaseFocus(); await Tap(Key.I); Require(Field<string>(game,"currentPage")=="Inventory",label+" physical I opens Inventory");
                var action=game.FindChildren("PrimaryEquipmentAction","Button",true,false).Cast<Button>().Single();
                Require(Contained(action)&&action.Size.Y>=40,label+" equipment comparison action remains reachable");
                var itemSlot=game.FindChildren("*","Control",true,false).OfType<EquipmentItemSlot>().First(slot=>slot.Item is not null&&!slot.IsQueuedForDeletion());
                int activated=0; itemSlot.Activated=()=>activated++;
                itemSlot.GrabFocus(); await Tap(Key.Space); Require(activated==1,label+" inventory equipment actions activate with Space from keyboard focus");
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

            GetWindow().ContentScaleFactor=1; GetWindow().Size=new Vector2I(1024,720); GetWindow().ContentScaleSize=new Vector2I(1024,720); await Frame(); await Frame();
            Call(game,"OpenPage","Settings"); await Frame(); await Frame(); Call(game,"SynchronizeModalUx");
            Require(Contained(Field<PanelContainer>(game,"gameWindow")),"A modal panel remains contained at the supported minimum Windows size");
            Call(game,"ClosePage"); await Frame(); await Frame();

            GD.Print($"WINDOWS_SCALE_CONTRACT: {checks} checks passed for accessibility, modal focus, keyboard items, and 125%/150% Windows scale emulation. Physical Windows monitor DPI approval is not inferred.");
            await NativeTestLifetime.ReleaseSceneAsync(this,game); connection=null; GetTree().Quit(0);
        }
        catch(Exception error)
        {
            GD.PushError("WINDOWS_SCALE_CONTRACT: "+error);
            if(game is not null&&GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this,game);
            else if(connection is not null) await connection.DisposeAsync();
            GetTree().Quit(1);
        }
    }
}
