using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    // The downloaded catalog and accepted character snapshot select this local
    // world mode. Saved preferences remain available when returning to a normal world.
    private bool ClassicSessionActive => Data.ClassicTutorial is not null && Snapshot?.Self.ClassicTutorial is not null;
    private string CharacterStartName => Data.Zone(Data.ClassicTutorial is null ? OpeningJourney.Home : ClassicTutorialContent.ZoneId).Name;
    private string classicPresentationCharacter = "";
    private bool classicPresentationMode;
    private string classicNoticeCharacter = "";
    private long classicNoticeBaseline;
    private Label classicFoodExpanded = null!, classicFoodCompact = null!;

    private Label BuildClassicFoodLabel(Node parent, string name)
    {
        var label = Ui.Label("", 12, Ui.Text);
        label.Name = name; label.Visible = false;
        label.MouseFilter = MouseFilterEnum.Ignore;
        parent.AddChild(label);
        return label;
    }

    private void UpdateClassicSessionPresentation(Snapshot snapshot)
    {
        bool active = ClassicSessionActive;
        if (classicPresentationCharacter != snapshot.Self.Id || classicPresentationMode != active)
        {
            classicPresentationCharacter = snapshot.Self.Id; classicPresentationMode = active;
            // Explicit zoom choices win over the tutorial's default. Never persist
            // a server's default into another character's settings.
            double zoom = active ? settings.GetValue("display", "native_world_zoom", Data.ClassicTutorial!.TileZoom).AsDouble()
                : PixelPresentation.WorldZoom(settings);
            World.Zoom = double.IsFinite(zoom) ? Math.Clamp((float)zoom, 1, 3) : 1;
            ApplyFocusHud();
        }
        foreach (var label in new[] { classicFoodExpanded, classicFoodCompact })
        {
            if (label is null) continue;
            label.Visible = active;
            if (!active) continue;
            double food = snapshot.Self.ClassicTutorial!.Food;
            label.Text = double.IsFinite(food) ? $"Food  {Math.Clamp(food, 0, 100):0} / 100" : "Food  unavailable";
            label.Modulate = double.IsFinite(food) && food < 25 ? Ui.Gold : Colors.White;
            label.TooltipText = $"Food from the latest realm snapshot. Eating restores {Data.ClassicTutorial!.FoodRestore:0.#} Food, up to 100; food recovery still applies.";
        }
        var progress = active ? snapshot.Self.ClassicTutorial : null;
        if (classicNoticeCharacter != snapshot.Self.Id || progress is null || progress.NoticeId < classicNoticeBaseline)
        {
            classicNoticeCharacter = snapshot.Self.Id;
            classicNoticeBaseline = progress?.NoticeId ?? 0;
            return;
        }
        if (progress.NoticeId <= classicNoticeBaseline) return;
        classicNoticeBaseline = progress.NoticeId;
        if (progress.Notice != "") Notify(progress.Notice);
    }
}
