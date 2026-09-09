using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;
internal static class HuntingGuideChecks
{
    public static async Task Run(Node host,GameRoot game,Action<bool,string> check)
    {
        object? Call(string method,params object?[] args)=>typeof(GameRoot).GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
        async Task Frame()=>await host.ToSignal(host.GetTree(),SceneTree.SignalName.ProcessFrame);
        var old=game.World.Snapshot;
        var realm=new RealmEngine(game.Data);var self=realm.CreateCharacter("hunt-ui-fixture","Hunt Guide","vanguard",new());
        try
        {
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            foreach(string zone in new[]{"wayfarers_rest","kingsmeadow","broken_mill","umbral_crossroads"})
            {
                host.GetWindow().Size=size;host.GetWindow().ContentScaleSize=size;
                self.Zone=zone;self.Position=game.Data.Zone(zone).Spawn;
                game.World.Accept(new TransportPacket{Snapshot=realm.Snapshot(self.Id)});
                Call("OpenPage","Hunting");await Frame();await Frame();await Frame();
                var guide=game.FindChildren("HuntingGuide","VBoxContainer",true,false).OfType<HuntingGuidePanel>().Single();
                var plan=HuntingGrounds.For(game.Data,game.Data.Zone(zone));
                check(guide.SelectedSite!="","A real hunting site is selected in "+zone);
                var first=guide.FindChildren("HuntSite_*","Button",true,false).OfType<Button>().First();
                ulong identity=first.GetInstanceId();
                foreach(var patch in plan.Patches)guide.SelectSite(patch.Id);
                guide.RefreshSnapshot();await Frame();
                check(GodotObject.IsInstanceValid(first)&&identity==first.GetInstanceId(),"Hunting snapshots preserve native controls");
                var directions=guide.FindChildren("HuntDirections","Label",true,false).OfType<Label>().Single();
                var bounds=host.GetViewport().GetVisibleRect();var rect=directions.GetGlobalRect();
                check(rect.Position.X>=-1&&rect.Position.Y>=-1&&rect.End.X<=bounds.End.X+1&&rect.End.Y<=bounds.End.Y+1,"Hunting directions fit "+size+" in "+zone);
                check(directions.Text.Length>0,"The selected hunting site gives travel directions");
                if(plan.FieldBoss!="")check(guide.FindChildren("FieldBossSite","Button",true,false).Any(),"The wilderness guide exposes the real field boss");
                if(game.Data.Zone(zone).Boss!="")check(guide.FindChildren("DungeonBossSite","Button",true,false).Any(),"The dungeon guide exposes its existing boss");
                Call("ClosePage");await Frame();await Frame();check(!GodotObject.IsInstanceValid(guide),"Hunting guide controls release after closing");
            }
        }
        finally
        {
            Call("ClosePage");await Frame();await Frame();
            if(old is not null)game.World.Accept(new TransportPacket{Snapshot=old});
        }
    }
}
