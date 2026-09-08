using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>Native inventory presentation fixtures. Server repair behavior has a separate transaction test.</summary>
internal static class EquipmentMaintenanceUiChecks
{
    public static async Task Run(Node host,GameRoot game,Action<bool,string> check)
    {
        object? Call(string name,params object?[] args)=>typeof(GameRoot).GetMethod(name,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
        FieldInfo Field(string name)=>typeof(GameRoot).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!;
        async Task Frame()=>await host.ToSignal(host.GetTree(),SceneTree.SignalName.ProcessFrame);
        var original=game.World.Snapshot;
        string priorItem=(string)Field("selectedItem").GetValue(game)!, priorBag=(string)Field("selectedBag").GetValue(game)!;
        var realm=new RealmEngine(game.Data);
        var self=realm.CreateCharacter("maintenance-ui","Tool Repair UI","vanguard",new());
        self.Inventory.Clear(); self.Equipment.Clear();
        var tool=Items.Create(game.Data,"bronze_tool_pickaxe"); tool.Durability=37; self.Inventory.Add(tool);
        var smith=game.Data.Npcs.First(n=>n.Role=="blacksmith");
        try
        {
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            {
                host.GetWindow().Size=size; host.GetWindow().ContentScaleSize=size;
                self.Zone=smith.Zone; self.Position=smith.Position;
                game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id)});
                Field("selectedItem").SetValue(game,tool.Id); Field("selectedBag").SetValue(game,"inventory");
                Call("OpenPage","Inventory"); await Frame(); await Frame(); await Frame();
                string text=(string)Call("ItemDescription",tool,false)!;
                check(text.Contains("Tool durability: 37%"),"The native item inspector explains tool condition at "+size);
                var action=game.FindChildren("RepairEquipmentAction","Button",true,false).OfType<Button>().Single();
                check(action.IsVisibleInTree()&&!action.Disabled,"Damaged backpack tools expose the blacksmith repair action");
                for(Node? parent=action.GetParent();parent is not null;parent=parent.GetParent())
                    if(parent is ScrollContainer scroll) { scroll.ScrollVertical=100000; break; }
                await Frame(); await Frame();
                var rect=action.GetGlobalRect(); var bounds=host.GetViewport().GetVisibleRect();
                check(rect.Position.X>=-1&&rect.Position.Y>=-1&&rect.End.X<=bounds.End.X+1&&rect.End.Y<=bounds.End.Y+1,
                    "The repair action is reachable through the inventory scroll area at "+size);
                Call("ClosePage"); await Frame(); await Frame();
                var zone=game.Data.Zones.First(z=>z.Kind=="wilderness"&&!game.Data.Npcs.Any(n=>n.Zone==z.Id&&n.Role=="blacksmith"));
                self.Zone=zone.Id; self.Position=zone.Spawn;
                game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id)});
                Call("OpenPage","Inventory"); await Frame(); await Frame();
                action=game.FindChildren("RepairEquipmentAction","Button",true,false).OfType<Button>().Single();
                check(action.Disabled,"A distant blacksmith cannot enable the native tool repair action");
                Call("ClosePage"); await Frame(); await Frame();
                tool.Durability=100; game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id)});
                Call("OpenPage","Inventory"); await Frame(); await Frame();
                check(!game.FindChildren("RepairEquipmentAction","Button",true,false).Any(),"Undamaged tools do not expose a chargeable repair action");
                Call("ClosePage"); await Frame(); await Frame(); tool.Durability=37;
            }
        }
        finally
        {
            Call("ClosePage"); await Frame(); await Frame();
            Field("selectedItem").SetValue(game,priorItem); Field("selectedBag").SetValue(game,priorBag);
            if(original is not null) game.World.Accept(new TransportPacket{Snapshot=original});
        }
    }
}
