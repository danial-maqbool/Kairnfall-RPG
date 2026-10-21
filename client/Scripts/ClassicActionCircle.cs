using Godot;

namespace Kairnfall.Client;

public partial class ClassicActionCircle : Button
{
    public override void _Ready()
    {
        FocusMode = FocusModeEnum.None;
        MouseDefaultCursorShape = CursorShape.PointingHand;
        foreach (string state in new[] { "normal", "hover", "pressed", "disabled", "focus" })
            AddThemeStyleboxOverride(state, new StyleBoxEmpty());
        MouseEntered += QueueRedraw; MouseExited += QueueRedraw;
        ButtonDown += QueueRedraw; ButtonUp += QueueRedraw;
    }
    public override void _Draw()
    {
        var center = Size / 2;
        float radius = Math.Min(Size.X, Size.Y) / 2 - 2;
        var fill = new Color(.08f, .14f, .10f, .74f);
        if (IsHovered()) fill = new Color(.16f, .25f, .17f, .84f);
        if (ButtonPressed) fill = new Color(.23f, .32f, .19f, .9f);
        DrawCircle(center, radius, fill);
        DrawArc(center, radius, 0, MathF.Tau, 40, new Color("9baf88"), 2);
        var points = new Vector2[32];
        for (int i = 0; i < points.Length; i++)
        {
            float turn = i / 31f;
            float angle = turn * MathF.Tau * 1.45f;
            points[i] = (center + new Vector2(MathF.Cos(angle), MathF.Sin(angle)) * (2 + turn * 15)).Round();
        }
        DrawPolyline(points, new Color("d4dfb0"), 2);
    }
}
