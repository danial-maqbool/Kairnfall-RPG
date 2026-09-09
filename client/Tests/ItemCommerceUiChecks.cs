using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

internal static class ItemCommerceUiChecks
{
    public static async Task Run(Node host, GameRoot game, Action<bool,string> check)
    {
        FieldInfo Field(string name) => typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!;
        object? Call(string name, params object?[] args) => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game,args);
        async Task Frame() => await host.ToSignal(host.GetTree(),SceneTree.SignalName.ProcessFrame);
        T Find<T>(string name) where T:Node => game.FindChildren(name,"",true,false).OfType<T>().First(x=>!x.IsQueuedForDeletion());
        bool Fits(Control c) { var a=c.GetGlobalRect();var b=host.GetViewport().GetVisibleRect();return c.IsVisibleInTree()&&a.Position.X>=0&&a.Position.Y>=0&&a.End.X<=b.End.X+1&&a.End.Y<=b.End.Y+1; }
        async Task Click(Button button)
        {
            check(Fits(button)&&!button.Disabled,"The sale action is visible and enabled before native input");
            var at=button.GetGlobalRect().GetCenter();
            using(var press=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left,ButtonMask=MouseButtonMask.Left,Pressed=true}) host.GetViewport().PushInput(press,true);
            await Frame();
            using(var release=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left,Pressed=false}) host.GetViewport().PushInput(release,true);
            await Frame();await Frame();
        }
        async Task TypeQuantity(LineEdit edit,string text)
        {
            edit.GrabFocus();await Frame();edit.SelectAll();
            using(var erase=new InputEventKey{Keycode=Key.Backspace,PhysicalKeycode=Key.Backspace,Pressed=true}) host.GetViewport().PushInput(erase,true);
            using(var erase=new InputEventKey{Keycode=Key.Backspace,PhysicalKeycode=Key.Backspace,Pressed=false}) host.GetViewport().PushInput(erase,true);
            foreach(char character in text)
            {
                var code=(Key)char.ToUpperInvariant(character);
                using(var press=new InputEventKey{Keycode=code,PhysicalKeycode=code,Unicode=character,Pressed=true})
                    host.GetViewport().PushInput(press,true);
                using(var release=new InputEventKey{Keycode=code,PhysicalKeycode=code,Pressed=false})
                    host.GetViewport().PushInput(release,true);
            }
            await Frame();
        }
        async Task Capture(string name)
        {
            if(DisplayServer.GetName()=="headless")return;
            await Frame();await host.ToSignal(RenderingServer.Singleton,RenderingServer.SignalName.FramePostDraw);
            string root=System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS")??ProjectSettings.GlobalizePath("user://visual-review");
            System.IO.Directory.CreateDirectory(root);
            using var image=host.GetViewport().GetTexture().GetImage();
            check(image.SavePng(System.IO.Path.Combine(root,name+".png"))==Error.Ok,"Saved native item/merchant frame "+name);
        }
        var original=game.World.Snapshot;
        string oldItem=(string)Field("selectedItem").GetValue(game)!,oldBag=(string)Field("selectedBag").GetValue(game)!,oldNpc=(string)Field("selectedNpc").GetValue(game)!;
        // Production keeps 99-item stacks. The copied realm also tests future bulk-stack quantities.
        var fixtureData=Wire.Copy(game.Data);fixtureData.Item("copper_ore").StackMax=999;
        var realm=new RealmEngine(fixtureData);var self=realm.CreateCharacter("commerce-ui","Commerce UI","vanguard",new());
        var merchant=game.Data.Npcs.First(x=>x.Role=="provisioner"&&x.Stock.Length>0);
        try
        {
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            {
                host.GetWindow().Size=size;host.GetWindow().ContentScaleSize=size;
                self=realm.Player(self.Id);self.Inventory.Clear();self.Equipment.Clear();self.Gold=100;self.Health=100;self.Zone=merchant.Zone;self.Position=merchant.Position;
                var old=Items.Create(game.Data,"copper_sword");old.Affixes=[new(){Stat="vitality",Value=6},new(){Stat="luck",Value=2}];
                var item=Items.Create(game.Data,"iron_sword",1,Rarity.Rare);item.Affixes=[new(){Stat="vitality",Value=1},new(){Stat="luck",Value=2}];
                self.Inventory.AddRange([old,item]);self.Equipment["weapon"]=old.Id;
                game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id)});
                Field("selectedItem").SetValue(game,item.Id);Field("selectedBag").SetValue(game,"inventory");
                Call("OpenPage","Inventory");await Frame();await Frame();await Frame();
                var value=Find<Label>("StatValue_vitality");var delta=Find<Label>("StatDelta_vitality");
                check(value.GetThemeColor("font_color")==Ui.Danger&&delta.Text=="-5","Each worse stat is red with its signed difference");
                check(Find<Label>("StatValue_item_power").GetThemeColor("font_color")==Ui.Success,"Better equipment power is green even when locked");
                check(Find<Label>("StatValue_luck").GetThemeColor("font_color")==Ui.Text&&Find<Label>("StatDelta_luck").Text=="0","Unchanged stats retain their normal color");
                check(Find<Label>("ItemBlocker").GetThemeColor("font_color")==Ui.Danger,"Unmet equipment requirements are red");
                check(value.HorizontalAlignment==HorizontalAlignment.Center&&value.VerticalAlignment==VerticalAlignment.Center,"Stat cells center text on both axes");
                check(Find<Control>("CompactItemCard").Size.X<=360,"The item card keeps a compact width at "+size);
                await Capture("item-compare-"+size.X);
                var slot=game.FindChildren("*","Control",true,false).OfType<EquipmentItemSlot>().First(x=>x.Item?.Id==item.Id&&!x.IsQueuedForDeletion());
                var tip=slot._MakeCustomTooltip(slot.TooltipText);
                try { check(tip is Control c&&c.CustomMinimumSize.X==CompactItemCard.Width,"Equipment slots use the compact comparison tooltip"); }
                finally { if(GodotObject.IsInstanceValid(tip)) ((Node)tip).Free(); }
                Call("ClosePage");await Frame();await Frame();
                var stackDef=fixtureData.Item("copper_ore");
                var stack=Items.Create(fixtureData,stackDef.Id,150);self.Inventory.Clear();self.Equipment.Clear();self.Inventory.Add(stack);
                game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id)});
                Field("selectedNpc").SetValue(game,merchant.Id);Call("OpenPage","Shop");await Frame();await Frame();
                await Click(Find<Button>("OpenMerchantSell"));await Frame();await Frame();
                var panel=Find<MerchantSellPanel>("MerchantSellPanel");int requests=0,lastCount=0;
                panel.Data=fixtureData;
                Character displayed=self;bool delaySnapshot=false;
                panel.ReadCharacter=()=>displayed;
                panel.SellItem=(id,count)=>
                {
                    requests++;lastCount=count;
                    var result=realm.Execute(self.Id,new GameCommand{Kind="sell",Target=merchant.Id,Item=id,Amount=count,Sequence=self.LastAction+1});
                    self=realm.Player(self.Id);if(!delaySnapshot)displayed=self;
                    return Task.FromResult<CommandResult?>(result);
                };
                panel.RefreshSnapshot();await Frame();await Frame();
                var quantity=Find<LineEdit>("SaleQuantity");await TypeQuantity(quantity,"7");
                check(quantity.Text=="7","Native typing leaves the intended unsubmitted sale quantity");
                panel.RefreshSnapshot();check(quantity.Text=="7","Snapshot refresh preserves an unsubmitted typed quantity");
                int savedCaret=quantity.CaretColumn;
                stack.Quantity=149;panel.RefreshSnapshot();
                check(quantity.Text=="7"&&quantity.CaretColumn==savedCaret,"A changed stack limit preserves the pending edit and caret");
                stack.Quantity=5;panel.RefreshSnapshot();
                check(quantity.Text=="7"&&Find<Button>("SellSelectedQuantity").Disabled,"A smaller remaining stack rejects rather than silently clamps the typed quantity");
                stack.Quantity=150;panel.RefreshSnapshot();
                await Click(Find<Button>("SaleQuantityIncrease"));check(quantity.Text=="8","The explicit plus button adjusts the selected quantity");
                await Click(Find<Button>("SaleQuantityDecrease"));check(quantity.Text=="7","The explicit minus button restores the selected quantity");
                long gold=self.Gold,unit=MerchantSales.UnitPrice(stackDef);
                check(Find<Label>("SaleGoldTotal").Text.Contains((unit*7).ToString("N0")),"The selected quantity shows the exact total gold");
                await Capture("merchant-sell-"+size.X);
                delaySnapshot=true;displayed=Wire.Copy(self);
                await Click(Find<Button>("SellSelectedQuantity"));
                check(Find<Button>("SellSelectedQuantity").Disabled&&Find<Button>("SellAllQuantity").Disabled,"A successful receipt keeps both sale actions disabled until inventory catches up");
                var blockedAt=Find<Button>("SellSelectedQuantity").GetGlobalRect().GetCenter();
                using(var press=new InputEventMouseButton{Position=blockedAt,GlobalPosition=blockedAt,ButtonIndex=MouseButton.Left,Pressed=true}) host.GetViewport().PushInput(press,true);
                await Frame();
                using(var release=new InputEventMouseButton{Position=blockedAt,GlobalPosition=blockedAt,ButtonIndex=MouseButton.Left,Pressed=false}) host.GetViewport().PushInput(release,true);
                await Frame();panel.RefreshSnapshot();
                check(requests==1&&Find<Button>("SellAllQuantity").Disabled,"Native repeat clicks and stale snapshots cannot submit a second sale");
                delaySnapshot=false;displayed=self;panel.RefreshSnapshot();await Frame();
                check(!Find<Button>("SellSelectedQuantity").Disabled,"The matching authoritative snapshot releases the sale guard");
                check(requests==1&&lastCount==7&&Items.Owned(self,stack.Id).Quantity==143&&self.Gold==gold+unit*7,"Native Sell quantity reaches the real realm transaction and transfers exact gold");
                await TypeQuantity(quantity,"invalid");
                quantity.ReleaseFocus();await Frame();panel.RefreshSnapshot();
                check(quantity.Text=="invalid","Invalid quantity text survives focus loss and snapshot refresh without coercion");
                check(Find<Button>("SellSelectedQuantity").Disabled&&requests==1,"Invalid text cannot become a silent sale quantity");
                check(!Find<Button>("SellAllQuantity").Disabled,"Sell all is independent of an invalid partial quantity");
                await Click(Find<Button>("SellAllQuantity"));
                check(requests==2&&lastCount==143&&self.Inventory.Count==0&&self.Gold==gold+unit*150,"Sell all transfers the full remaining stack in one transaction");
                check(Find<Button>("SellSelectedQuantity").Disabled&&Find<Button>("SellAllQuantity").Disabled,"No stale action remains after selling the complete stack");
                Call("ClosePage");await Frame();await Frame();
            }
            foreach(string text in new[]{"0","-1","1.5","1e2","999999999999",""})
                check(!MerchantSellPanel.TryQuantity(text,150,out _),"Invalid sale input is rejected: "+text);
        }
        finally
        {
            Call("ClosePage");await Frame();await Frame();
            Field("selectedItem").SetValue(game,oldItem);Field("selectedBag").SetValue(game,oldBag);Field("selectedNpc").SetValue(game,oldNpc);
            if(original is not null)game.World.Accept(new TransportPacket{Snapshot=original});
        }
    }
}
