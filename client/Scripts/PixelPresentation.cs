using Godot;

namespace Kairnfall.Client;

/// <summary>Native source pixels for the world and inventory. Interface text is not downsampled.</summary>
public static class PixelPresentation
{
    public static float WorldZoom(ConfigFile settings)
    {
        // Preserve the historical key so this preference migration is reversible.
        // The new native-pixel preset defaults to one; later explicit zoom choices persist.
        double value=settings.GetValue("display","native_world_zoom",1).AsDouble();
        return double.IsFinite(value)?Math.Clamp((float)Math.Round(value),1,3):1;
    }
    public static Rect2 InventoryIconRect(Vector2 slot,Vector2 image)
    {
        if(!float.IsFinite(slot.X)||!float.IsFinite(slot.Y)||!float.IsFinite(image.X)||!float.IsFinite(image.Y)
            ||slot.X<=0||slot.Y<=0||image.X<=0||image.Y<=0)return new Rect2();
        float available=Math.Min((slot.X-12)/image.X,(slot.Y-14)/image.Y);
        float scale=Math.Min(1,Math.Max(0,available));
        var size=(image*scale).Floor();
        return new Rect2(((slot-size)/2).Floor(),size);
    }
}

public partial class GameRoot
{
    private void AddPixelPresentationControls(Node rows)
    {
        rows.AddChild(Ui.Label("Pixel scale",20,Ui.Gold));
        rows.AddChild(Ui.Label("Native pixels show more terrain and finer sprite detail. Mouse wheel adjusts only world zoom. Item slots retain their source resolution.",14,Ui.Muted,true));
        var row=Ui.Row(rows);
        foreach(int scale in new[]{1,2,3})
        {
            int value=scale;
            var button=Ui.Button(scale==1?"Native detail · 1×":scale+"× world zoom",()=>
            {
                World.Zoom=value;settings.SetValue("display","native_world_zoom",value);settings.Save("user://settings.cfg");
            });
            button.Name="WorldPixelScale_"+scale;row.AddChild(button);
        }
        rows.AddChild(Ui.Label("The Atelier art pack uses the existing item identities and animation grid. Independent gear/gear_worn records do not replace your saved equipment.",13,Ui.Muted,true));
    }
}
