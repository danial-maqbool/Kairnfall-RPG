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
            var settingsProfile=global::PageLayoutProfiles.For("Settings");
            Require(Field<PanelContainer>(game,"gameWindow").TooltipText==settingsProfile.Summary,"Settings uses the shared page-specific purpose summary");
            Require(global::PageLayoutProfiles.SizeFor("Dialogue",new Vector2(1920,1080)).X<global::PageLayoutProfiles.SizeFor("Inventory",new Vector2(1920,1080)).X,"Content-specific profiles keep conversation more compact than inventory");
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
            Call(game,"ClosePage"); Call(game,"SynchronizeModalUx");
            Require(!blocker.Visible,"Closing synchronously hides the input blocker before the next physics tick");
            await Frame();
            Require(backgroundFocus.FocusMode==Control.FocusModeEnum.All&&GetViewport().GuiGetFocusOwner()==backgroundFocus,"Closing a panel restores its previous keyboard focus target");
            Call(game,"ApplyUiTextScale",1d,false); await Frame();

            Call(game,"OpenPage","Inventory");
            var modal=Field<PanelContainer>(game,"gameWindow");
            Require(Field<ColorRect>(game,"modalInputBlocker").GetIndex()<modal.GetIndex(),"Modal GUI hit order places the active window above its blocker");
            await Tap(Key.Tab);
            Require(GetViewport().GuiGetFocusOwner() is {} tabFocus&&modal.IsAncestorOf(tabFocus),"Tab navigates inside the modal without reaching HUD controls");
            GetViewport().GuiReleaseFocus(); await Tap(Key.Enter);
            Require(GetViewport().GuiGetFocusOwner()!=Field<LineEdit>(game,"chatInput"),"Unhandled Enter cannot focus background chat through a modal");
            Call(game,"ClosePage");
            backgroundFocus.Disabled=true; backgroundFocus.GrabFocus();
            Call(game,"OpenPage","Settings"); Call(game,"ClosePage");
            Require(GetViewport().GuiGetFocusOwner()!=backgroundFocus,"A disabled return target does not regain keyboard focus");
            backgroundFocus.Disabled=false;
            Call(game,"OpenPage","Settings");
            typeof(GameRoot).GetField("awaitingBinding",BindingFlags.Instance|BindingFlags.NonPublic)!.SetValue(game,"inventory");
            await Tap(Key.Enter);
            Require(Field<string>(game,"awaitingBinding")=="inventory","Reserved Enter is rejected by rebinding before the focused button activates");
            await Tap(Key.Escape);
            Require(Field<string>(game,"awaitingBinding")==""&&Field<string>(game,"currentPage")=="Settings","Escape cancels rebinding and retains Settings");
            Call(game,"ClosePage"); await Frame();
            foreach(double invalid in new[]{double.NaN,double.PositiveInfinity,double.NegativeInfinity})
                Require(Ui.ConfigureTextScale(invalid)==1f,"Non-finite text settings fall back to readable defaults");
            var config=Field<ConfigFile>(game,"settings");
            config.SetValue("accessibility","text_scale","invalid"); Call(game,"InitializeUiUx");
            Require(Ui.TextScale==1f,"A malformed persisted text setting loads safely");
            config.SetValue("accessibility","text_scale",1.15d); Call(game,"InitializeUiUx");
            Require(Math.Abs(Ui.TextScale-1.15f)<.001f,"A valid saved text setting is restored");
            Call(game,"ApplyUiTextScale",1d,false);
            string settingsPath=System.IO.Path.Combine(System.IO.Path.GetTempPath(),"kairnfall-ui-"+Guid.NewGuid()+".cfg");
            try
            {
                config.SetValue("display","fullscreen",true);
                Require(config.Save(settingsPath)==Error.Ok,"Display and accessibility settings serialize successfully");
                using var restored=new ConfigFile();
                Require(restored.Load(settingsPath)==Error.Ok&&restored.GetValue("display","fullscreen").AsBool()
                    &&Math.Abs(restored.GetValue("accessibility","text_scale").AsDouble()-1.15)<.001,"Settings survive a disk round trip");
            }
            finally { System.IO.File.Delete(settingsPath); config.SetValue("display","fullscreen",false); }
            var savedBindings=Field<Dictionary<string,Key>>(game,"bindings");
            savedBindings["inventory"]=Key.O; Call(game,"UpdateHud");
            Require(game.FindChildren("*","Button",true,false).OfType<Button>().Any(button=>button.Text=="Bag [O]"),"HUD key discovery reflects the current binding");
            savedBindings["inventory"]=Key.I; Call(game,"UpdateHud");

            Call(game,"OpenPage","Inventory"); await Frame();
            var ownerWindow=Field<PanelContainer>(game,"gameWindow");
            var ownerSlot=game.FindChildren("*","Control",true,false).OfType<EquipmentItemSlot>().First(slot=>slot.Item is not null&&!slot.IsQueuedForDeletion());
            ownerSlot.GrabFocus(); Call(game,"ItemContext",ownerSlot.Item!,"inventory",ownerSlot.GetGlobalRect().GetCenter()); await Frame();
            var context=game.FindChildren("*","Control",true,false).OfType<EquipmentMenu>().Single(menu=>!menu.IsQueuedForDeletion());
            Require(context.ZIndex>ownerWindow.ZIndex,"Item context actions render above the modal panel");
            await Tap(Key.Tab);
            Require(GetViewport().GuiGetFocusOwner() is {} contextFocus&&context.IsAncestorOf(contextFocus),"Context menu keeps Tab inside its action controls");
            await Tap(Key.Escape);
            Require(Field<string>(game,"currentPage")=="Inventory"&&GetViewport().GuiGetFocusOwner()==ownerSlot,"Escape closes only the context menu and restores its item focus");
            Call(game,"ItemContext",ownerSlot.Item!,"inventory",ownerSlot.GetGlobalRect().GetCenter()); await Frame();
            var currentInventory=game.World.Snapshot!.Self.Inventory;
            var removed=currentInventory.Single(item=>item.Id==ownerSlot.Item!.Id);
            currentInventory.Remove(removed); await Frame(); await Frame();
            Require(!game.FindChildren("*","Control",true,false).OfType<EquipmentMenu>().Any(menu=>menu.Visible),"A removed item dismisses its stale context actions");
            currentInventory.Add(removed);
            Call(game,"ItemContext",ownerSlot.Item!,"inventory",ownerSlot.GetGlobalRect().GetCenter()); await Frame();
            Call(game,"ClosePage");
            Require(!game.FindChildren("*","Control",true,false).OfType<EquipmentMenu>().Any(menu=>menu.Visible),"Closing the owner immediately dismisses item context blockers");
            await Frame();

            int baseActivations=0;
            var baseSlot=new ItemSlot{Name="KeyboardItemSlot",Item=self.Inventory.First(),Clicked=()=>baseActivations++};
            game.AddChild(baseSlot); await Frame(); baseSlot.GrabFocus(); await Tap(Key.Space);
            Require(baseActivations==1,"Generic item slots are keyboard reachable and activate with Space");
            baseSlot.QueueFree(); await Frame();

            foreach(float scale in new[]{1.25f,1.50f})
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080),new Vector2I(2560,1440)})
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

            foreach(var matrixSize in new[]{new Vector2I(1024,720),new Vector2I(1280,720),new Vector2I(1920,1080),new Vector2I(2560,1440)})
            foreach(double textScale in new[]{.9d,1d,1.15d,1.25d})
            {
                GetWindow().ContentScaleFactor=1; GetWindow().Size=matrixSize; GetWindow().ContentScaleSize=matrixSize; await Frame(); await Frame();
                Call(game,"ApplyUiTextScale",textScale,false);
                string layoutLabel=$"{matrixSize.X}x{matrixSize.Y} at text scale {textScale:0.##}";
                foreach(string pageName in new[]{"Inventory","Bank","Character","Equipment Guide","Shop","Sell","Skills","Abilities","Quests","Dialogue","Crafting","Social","Trade","Auction","Map","Bestiary","Hunting","Achievements","Settings"})
                {
                    Call(game,"OpenPage",pageName); await Frame(); await Frame(); Call(game,"FitOpenPage");
                    var window=Field<PanelContainer>(game,"gameWindow");
                    Require(Contained(window),pageName+" fits "+layoutLabel);
                    Require(window.TooltipText==global::PageLayoutProfiles.For(pageName).Summary,pageName+" exposes its page-specific purpose summary at "+layoutLabel);
                    var closeButton=window.FindChildren("*","Button",true,false).OfType<Button>().First(button=>button.Text.StartsWith("Close",StringComparison.Ordinal));
                    Require(Contained(closeButton),pageName+" close remains reachable at "+layoutLabel);
                    var overflow=window.FindChild("PageOverflow",true,false) as ScrollContainer;
                    Require(overflow is { FollowFocus:true },pageName+" overflow follows keyboard focus at "+layoutLabel);
                    await Click(closeButton);
                    Require(Field<string>(game,"currentPage")=="",pageName+" closes via actual mouse input at "+layoutLabel);
                }
            }
            Call(game,"ApplyUiTextScale",1d,false);

            GD.Print($"WINDOWS_SCALE_CONTRACT: {checks} checks passed for accessibility, modal focus, keyboard items, and 1024/1280/1920/2560 layout and 125%/150% Windows scale emulation. Physical Windows monitor DPI approval is not inferred.");
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
