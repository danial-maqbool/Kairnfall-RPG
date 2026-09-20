using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

internal static class JourneyUiChecks
{
    public static async Task Run(Node host,GameRoot game,Action<bool,string> check)
    {
        object? Call(string name,params object?[] args)=>typeof(GameRoot).GetMethod(name,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
        FieldInfo Field(string name)=>typeof(GameRoot).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!;
        async Task Frame()=>await host.ToSignal(host.GetTree(),SceneTree.SignalName.ProcessFrame);
        T Find<T>(string name) where T:Node=>game.FindChildren(name,"",true,false).OfType<T>().Single(n=>!n.IsQueuedForDeletion());
        bool Fits(Control c)
        {
            var r=c.GetGlobalRect(); var v=host.GetViewport().GetVisibleRect();
            return c.IsVisibleInTree()&&r.Position.X>=-1&&r.Position.Y>=-1&&r.End.X<=v.End.X+1&&r.End.Y<=v.End.Y+1;
        }
        var original=game.World.Snapshot;
        string priorItem=(string)Field("selectedItem").GetValue(game)!, priorBag=(string)Field("selectedBag").GetValue(game)!;
        var realm=new RealmEngine(game.Data); var self=realm.CreateCharacter("grouped-inventory","Grouped Inventory","vanguard",new());
        self.SkillXp["swordsmanship"]=Progression.Threshold(3);
        var ready=Items.Create(game.Data,"bronze_sword"); self.Inventory.Add(ready);
        var locked=Items.Create(game.Data,"mithril_sword"); self.Inventory.Add(locked);
        var broken=Items.Create(game.Data,"copper_sword"); broken.Durability=0; self.Inventory.Add(broken);
        check(InventorySections.Group(self,ready,game.Data)==1,"Grade-five equipment is ready at the lowered skill-three gate");
        check(InventorySections.Group(self,locked,game.Data)==2&&InventorySections.Group(self,broken,game.Data)==2,"Locked and broken gear remain separate from usable equipment");
        check(InventorySections.Group(self,self.Inventory.First(i=>game.Data.Item(i.Template).Type=="tool"),game.Data)==3,"Backpack tools do not appear as wearable gear");
        int count=self.Inventory.Count;
        try
        {
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            {
                host.GetWindow().Size=size; host.GetWindow().ContentScaleSize=size;
                game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id)});
                Field("selectedItem").SetValue(game,ready.Id); Field("selectedBag").SetValue(game,"inventory");
                Call("OpenPage","Inventory"); await Frame(); await Frame(); await Frame();
                foreach(int group in new[]{0,1,2,3}) check(Find<GridContainer>("InventoryGroup"+group).GetChildCount()>0,"The native backpack displays group "+group);
                var view=Find<OptionButton>("InventoryView");
                check(Fits(view)&&Fits(Find<Button>("PrimaryEquipmentAction")),"Inventory filters and pinned Equip fit "+size);
                view.Select(1); view.EmitSignal(OptionButton.SignalName.ItemSelected,1L); await Frame(); await Frame();
                var shown=Find<GridContainer>("InventoryGroup1").GetChildren().OfType<EquipmentItemSlot>().ToArray();
                check(shown.Any(s=>s.Item?.Id==ready.Id)&&shown.All(s=>s.Item is not null&&InventorySections.Group(self,s.Item,game.Data)==1),"Ready filter contains only equipment that can actually be equipped");
                check(self.Inventory.Count==count&&Items.InventoryCapacity==64,"Filtering does not create inventory slots or move items");
                view.Select(2); view.EmitSignal(OptionButton.SignalName.ItemSelected,2L); await Frame(); await Frame();
                check(Find<GridContainer>("InventoryGroup2").GetChildren().OfType<EquipmentItemSlot>().Any(s=>s.Item?.Id==locked.Id&&s.TooltipText.Contains("Requires")),"Locked gear retains its exact requirement explanation");
                Call("ClosePage"); await Frame(); await Frame();
                var target=Find<Button>("CycleHostileTarget"); var dash=Find<Button>("DashAction");
                check(Fits(target)&&Fits(dash),"Native dash and target buttons fit "+size);
            }
            // Target rules operate on the same living-creature list as the native Tab handler.
            var zone=game.Data.Zone(self.Zone); var at=WorldMap.FindFree(zone,zone.Spawn);
            self.Position=at;
            var a=new Creature{Id="a",Template="field_rat",Zone=self.Zone,Position=at,Home=at,Health=20};
            var b=new Creature{Id="b",Template="wild_hare",Zone=self.Zone,Position=at,Home=at,Health=20};
            var dead=new Creature{Id="dead",Template="field_rat",Zone=self.Zone,Position=at,Health=0};
            var pet=new Creature{Id="pet",Template="field_rat",Zone=self.Zone,Position=at,Health=20,Owner=self.Id};
            Creature[] targets=[a,b,dead,pet];
            check(ExperienceRules.CycleTarget(self,targets,game.Data,"")?.Id=="a","Tab can deliberately select neutral animals");
            check(ExperienceRules.CycleTarget(self,targets,game.Data,"a")?.Id=="b","Tab advances to another living creature");
            check(ExperienceRules.CycleTarget(self,targets,game.Data,"a",true)?.Id=="b","Shift-Tab wraps backwards without selecting pets or corpses");
            check(ExperienceRules.CycleTarget(self,targets,game.Data,"b")?.Id=="a","Forward targeting wraps deterministically");
        }
        finally
        {
            Call("ClosePage"); await Frame(); await Frame();
            Field("selectedItem").SetValue(game,priorItem); Field("selectedBag").SetValue(game,priorBag);
            if(original is not null) game.World.Accept(new TransportPacket{Snapshot=original});
        }
    }
}
