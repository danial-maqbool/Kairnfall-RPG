using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Native target-key routing with an authenticated client and explicitly substituted scene data.</summary>
internal static class TargetKeyChecks
{
    public static async Task Run(Node host, GameRoot game, Action<bool,string> check)
    {
        var original = game.Snapshot ?? throw new InvalidOperationException("An authenticated snapshot is required.");
        var flags = BindingFlags.Instance | BindingFlags.NonPublic;
        FieldInfo Member(string name) => typeof(GameRoot).GetField(name, flags)!;
        T Read<T>(string name) => (T)Member(name).GetValue(game)!;
        async Task Frame() => await host.ToSignal(host.GetTree(), SceneTree.SignalName.ProcessFrame);
        void Send(Key key, bool pressed, bool reverse = false, bool echo = false)
        {
            using var input = new InputEventKey { PhysicalKeycode = key, Keycode = key, Pressed = pressed, ShiftPressed = reverse, Echo = echo };
            Input.ParseInputEvent(input); Input.FlushBufferedEvents();
        }
        async Task Tap(bool reverse = false) { Send(Key.Tab,true,reverse); await Frame(); Send(Key.Tab,false,reverse); await Frame(); }
        string savedTarget = Read<string>("selectedTarget"), savedKind = Read<string>("selectedTargetKind");
        bool processing = game.IsProcessing();
        var bindings = Read<Dictionary<string,Key>>("bindings"); Key savedBinding = bindings["target_next"];
        var data = Wire.Copy(original); data.Creatures.Clear();
        var zone = game.Data.Zone(data.Self.Zone);
        var positions = new List<Point>();
        for (int y=-3;y<=3;y++) for(int x=-3;x<=3;x++)
        {
            var at = data.Self.Position.Add(new Point(x,y));
            if ((x!=0 || y!=0) && WorldMap.Fits(zone,at) && WorldMap.LineOfSight(zone,data.Self.Position,at)) positions.Add(at);
        }
        positions = positions.OrderBy(p=>p.Distance(data.Self.Position)).ToList();
        check(positions.Count >= 2,"The native target fixture has two nearby reachable positions");
        var a = new Creature { Id="tab-a",Template="field_rat",Zone=zone.Id,Position=positions[0],Health=20 };
        var b = new Creature { Id="tab-b",Template="wild_hare",Zone=zone.Id,Position=positions[1],Health=20 };
        data.Creatures.AddRange([a,b,
            new Creature {Id="tab-far",Template="field_rat",Zone=zone.Id,Position=data.Self.Position.Add(new Point(ExperienceRules.TargetCycleRadius+.1,0)),Health=20},
            new Creature {Id="tab-dead",Template="field_rat",Zone=zone.Id,Position=data.Self.Position,Health=0},
            new Creature {Id="tab-pet",Template="field_rat",Zone=zone.Id,Position=data.Self.Position,Health=20,Owner=data.Self.Id}]);
        var focusButton = new Button { Name="TargetFocusFixture",Text="UI focus fixture",FocusMode=Control.FocusModeEnum.All };
        game.AddChild(focusButton);
        try
        {
            game.SetProcess(false); bindings["target_next"]=Key.Tab;
            game.World.Accept(new TransportPacket {Snapshot=data});
            Member("selectedTarget").SetValue(game,""); Member("selectedTargetKind").SetValue(game,"");
            host.GetViewport().GuiReleaseFocus(); await Frame();
            await Tap();
            check(Read<string>("selectedTarget")==a.Id,"Tab selects the nearest eligible mob before GUI focus traversal");
            check(host.GetViewport().GuiGetFocusOwner() is not LineEdit,"World Tab does not transfer focus to chat");
            await Tap(); check(Read<string>("selectedTarget")==b.Id,"Second native Tab advances to the other mob");
            await Tap(true); check(Read<string>("selectedTarget")==a.Id,"Shift-Tab cycles backwards before GUI traversal");
            Send(Key.Tab,true,echo:true); await Frame(); Send(Key.Tab,false);
            check(Read<string>("selectedTarget")==a.Id,"Key-repeat does not race through targets");
            focusButton.GrabFocus(); await Tap();
            check(Read<string>("selectedTarget")==b.Id && host.GetViewport().GuiGetFocusOwner()==focusButton,"A focused non-text HUD control cannot consume the target key");
            Read<LineEdit>("chatInput").GrabFocus(); await Frame(); await Tap();
            check(Read<string>("selectedTarget")==b.Id,"Typing retains GUI navigation without targeting a creature");
            host.GetViewport().GuiReleaseFocus();
            typeof(GameRoot).GetMethod("OpenPage",flags)!.Invoke(game,["Inventory"]); await Frame(); await Tap();
            check(Read<string>("selectedTarget")==b.Id,"Open inventory preserves UI keyboard navigation and blocks targeting");
            typeof(GameRoot).GetMethod("ClosePage",flags)!.Invoke(game,null); await Frame();
            host.GetViewport().GuiReleaseFocus();
            data.Creatures.Remove(a); data.Creatures.Remove(b); game.World.Accept(new TransportPacket {Snapshot=data}); await Tap();
            check(Read<string>("selectedTarget")=="" && game.World.TargetId=="","No eligible mob in 12 tiles clears the stale target, not chat focus");
            check(ExperienceRules.CycleTarget(data.Self,data.Creatures,game.Data,"") is null,"Distant mobs, pets and corpses remain excluded");
            for(int y=-10;y<=10;y++) for(int x=-10;x<=10;x++)
            {
                var at=data.Self.Position.Add(new Point(x,y));
                if(at.Distance(data.Self.Position)>ExperienceRules.TargetCycleRadius || WorldMap.LineOfSight(zone,data.Self.Position,at)) continue;
                var blocked=new Creature {Id="blocked",Template="field_rat",Zone=zone.Id,Position=at,Health=20};
                check(ExperienceRules.CycleTarget(data.Self,[blocked],game.Data,"") is null,"Target cycling rejects a blocked line of sight inside the radius");
                y=11; break;
            }
            check(data.Self.LastAction==original.Self.LastAction,"Target selection does not issue server combat or movement commands");
        }
        finally
        {
            typeof(GameRoot).GetMethod("ClosePage",flags)!.Invoke(game,null);
            bindings["target_next"]=savedBinding;
            Member("selectedTarget").SetValue(game,savedTarget); Member("selectedTargetKind").SetValue(game,savedKind);
            game.World.Accept(new TransportPacket {Snapshot=original}); game.World.TargetId=savedTarget;
            host.GetViewport().GuiReleaseFocus(); focusButton.QueueFree(); game.SetProcess(processing); await Frame();
        }
    }
}
