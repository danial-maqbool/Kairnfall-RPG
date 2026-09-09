using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>Selection and snapshot updates must retain the actual native item controls.</summary>
internal static class InventoryRefreshChecks
{
    public static async Task Run(Node host,GameRoot game,Action<bool,string> check)
    {
        const BindingFlags Private=BindingFlags.Instance|BindingFlags.NonPublic;
        object? Call(string method,params object?[] arguments)=>typeof(GameRoot).GetMethod(method,Private)!.Invoke(game,arguments);
        FieldInfo Field(string name)=>typeof(GameRoot).GetField(name,Private)!;
        async Task Frame()=>await host.ToSignal(host.GetTree(),SceneTree.SignalName.ProcessFrame);
        void Refresh()=>((Action?)Field("refreshPage").GetValue(game))?.Invoke();
        EquipmentItemSlot Slot(string id)=>game.FindChildren("*","",true,false).OfType<EquipmentItemSlot>()
            .Single(slot=>!slot.IsQueuedForDeletion()&&slot.Item?.Id==id&&slot.Bag=="inventory");
        async Task Click(Control control)
        {
            var bounds=host.GetViewport().GetVisibleRect();var rect=control.GetGlobalRect();
            check(control.IsVisibleInTree()&&rect.Position.X>=0&&rect.Position.Y>=0&&rect.End.X<=bounds.End.X&&rect.End.Y<=bounds.End.Y,
                "The inventory refresh fixture clicks a visible native slot");
            var at=rect.GetCenter();
            using(var down=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left,ButtonMask=MouseButtonMask.Left,Pressed=true})
                host.GetViewport().PushInput(down,true);
            await Frame();
            using(var up=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left})
                host.GetViewport().PushInput(up,true);
            await Frame();Refresh();await Frame();await Frame();
        }
        var original=game.World.Snapshot;
        string oldItem=(string)Field("selectedItem").GetValue(game)!,oldBag=(string)Field("selectedBag").GetValue(game)!;
        var realm=new RealmEngine(game.Data);var self=realm.CreateCharacter("inventory-refresh","Inventory Refresh","vanguard",new());
        self.Inventory.Clear();self.Equipment.Clear();self.SkillXp["swordsmanship"]=Progression.Threshold(3);
        var copper=Items.Create(game.Data,"copper_sword");var bronze=Items.Create(game.Data,"bronze_sword");
        var potion=Items.Create(game.Data,"healing_potion",2);
        self.Inventory.Add(copper);self.Inventory.Add(bronze);self.Inventory.Add(potion);
        void Snapshot()=>game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id)});
        try
        {
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            {
                host.GetWindow().Size=size;host.GetWindow().ContentScaleSize=size;
                self.Equipment.Clear();copper.Durability=100;potion.Quantity=2;
                Snapshot();Field("selectedItem").SetValue(game,copper.Id);Field("selectedBag").SetValue(game,"inventory");
                Call("OpenPage","Inventory");await Frame();await Frame();await Frame();
                var first=Slot(copper.Id);var second=Slot(bronze.Id);ulong firstId=first.GetInstanceId(),secondId=second.GetInstanceId();
                await Click(second);
                check(Slot(copper.Id).GetInstanceId()==firstId&&Slot(bronze.Id).GetInstanceId()==secondId,
                    "Selecting another item retains both native controls at "+size);
                check(!first.Selected&&second.Selected&&second.HasFocus(),"Selected border and keyboard focus follow the retained control");
                var firstSnapshotItem=first.Item;
                copper.Durability=73;potion.Quantity=5;Snapshot();Refresh();await Frame();await Frame();
                check(first.GetInstanceId()==Slot(copper.Id).GetInstanceId()&&!ReferenceEquals(firstSnapshotItem,first.Item),
                    "A new server snapshot replaces slot data without replacing the native slot");
                check(first.Item?.Durability==73&&first.TooltipText.Contains("73%"),"Retained slots show current authoritative durability");
                check(Slot(potion.Id).Item?.Quantity==5,"Retained supply slots show current stack quantities");
                for(int n=0;n<10;n++){Snapshot();Refresh();await Frame();}
                check(second.GetInstanceId()==Slot(bronze.Id).GetInstanceId()&&second.HasFocus(),
                    "Repeated snapshots retain focus and native double-click identity");
                Items.Equip(self,bronze.Id,game.Data);Snapshot();Refresh();await Frame();await Frame();
                var equipped=Slot(bronze.Id);
                check(equipped.Equipped&&equipped.GetParent().Name=="InventoryGroup0", "Server equip moves the item to the equipped section");
                check(!GodotObject.IsInstanceValid(second),"A changed group releases the obsolete slot instead of leaving a duplicate");
                self.Inventory.Remove(potion);Snapshot();Refresh();await Frame();await Frame();
                check(!game.FindChildren("*","",true,false).OfType<EquipmentItemSlot>().Any(s=>s.Item?.Id==potion.Id&&!s.IsQueuedForDeletion()),
                    "Removed items leave no stale supply controls");
                var view=game.FindChildren("InventoryView","OptionButton",true,false).OfType<OptionButton>().Single();
                view.Select(1);view.EmitSignal(OptionButton.SignalName.ItemSelected,1L);await Frame();await Frame();
                check(game.FindChildren("*","",true,false).OfType<EquipmentItemSlot>().Where(s=>s.Item is not null&&!s.IsQueuedForDeletion())
                    .All(s=>s.Item!.Id==copper.Id),"Ready-to-equip filtering shows the valid item without adding storage capacity");
                check(self.Inventory.Count==2&&Items.InventoryCapacity==64,"Section refresh preserves the shared backpack limit and item ownership");
                Call("ClosePage");await Frame();await Frame();
                check(!GodotObject.IsInstanceValid(equipped),"Closing the grouped inventory releases its retained native slots");
                self.Inventory.Add(potion);
            }
        }
        finally
        {
            Call("ClosePage");await Frame();await Frame();
            Field("selectedItem").SetValue(game,oldItem);Field("selectedBag").SetValue(game,oldBag);
            if(original is not null)game.World.Accept(new TransportPacket{Snapshot=original});
        }
    }
}
