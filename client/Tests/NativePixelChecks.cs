using Godot;
using Kairnfall.Core;
using System.Reflection;
using System.Text.Json;

namespace Kairnfall.Client.Tests;
internal static class NativePixelChecks
{
    public static async Task Run(Node host,GameRoot game,Action<bool,string> check)
    {
        async Task Frame()=>await host.ToSignal(host.GetTree(),SceneTree.SignalName.ProcessFrame);
        object? Call(string method,params object?[] args)=>typeof(GameRoot).GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
        using(var preferences=new ConfigFile())
        {
            preferences.SetValue("display","zoom",3);
            check(PixelPresentation.WorldZoom(preferences)==1,"Native detail defaults to one without destroying the historical zoom setting");
            check(preferences.GetValue("display","zoom").AsInt32()==3,"The old zoom preference remains recoverable");
            preferences.SetValue("display","native_world_zoom",2);
            check(PixelPresentation.WorldZoom(preferences)==2,"Explicit native-presentation zoom choices are retained");
        }
        foreach(float size in new[]{32,48,62,96,128})
        {
            var slot=new Vector2(size,size);var rect=PixelPresentation.InventoryIconRect(slot,new Vector2(32,32));
            check(rect.Size.X==rect.Size.Y&&rect.Size.X<=32,"Inventory icons do not stretch or magnify source pixels");
            check(rect.Position.X>=0&&rect.Position.Y>=0&&rect.End.X<=size&&rect.End.Y<=size,"Native inventory icon remains inside its slot");
        }
        check(PixelPresentation.InventoryIconRect(new Vector2(float.NaN,10),new Vector2(32,32)).Size==Vector2.Zero,"Invalid icon geometry does not reach the renderer");
        const string report="res://Assets/atelier-integration.json";
        check(Godot.FileAccess.FileExists(report),"The actual runtime pack includes its Atelier integration audit");
        using(var document=JsonDocument.Parse(Godot.FileAccess.GetFileAsString(report)))
        {
            var root=document.RootElement;var groups=root.GetProperty("groups");
            check(groups.GetProperty("items").GetInt32()==game.Data.Items.Count,"Every catalog item uses its matching Atelier icon");
            check(groups.GetProperty("equipment").GetInt32()==game.Data.Items.Count(i=>i.Slot!=""),"Every equipped item belongs to the complete Atelier rig cohort");
            check(groups.GetProperty("people").GetInt32()==60,"Both bodies and every hair layer come from the same rig");
            check(!root.GetProperty("catalog_ids_changed").GetBoolean()&&!root.GetProperty("independent_gear_ladder_imported").GetBoolean(),"Atelier integration changes no saved item identity or tier ladder");
        }
        float oldZoom=game.World.Zoom;
        foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
        {
            host.GetWindow().Size=size;host.GetWindow().ContentScaleSize=size;game.World.Zoom=1;
            await Frame();await Frame();
            var a=game.World.WorldToScreen(new Point(10,10));var b=game.World.WorldToScreen(new Point(11,10));
            check(Math.Abs(b.X-a.X-WorldMap.TileSize)<.01,"One world tile renders at native pixel width at "+size);
            Call("OpenPage","Settings");await Frame();await Frame();
            foreach(int zoom in new[]{1,2,3})check(game.FindChildren("WorldPixelScale_"+zoom,"Button",true,false).Any(),"Settings expose the "+zoom+"× world scale");
            Call("ClosePage");await Frame();await Frame();
        }
        game.World.Zoom=oldZoom;
    }
}
