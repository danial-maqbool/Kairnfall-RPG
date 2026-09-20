using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>A game panel with a timber field, metal edge, and fixed decorative details.</summary>
public partial class HudPanel : PanelContainer
{
    public override void _Ready()
    {
        AddThemeStyleboxOverride("panel", Ui.Box(new Color("211e19"), new Color("78664a"), 10));
    }
    public override void _Draw()
    {
        if (Size.X < 8 || Size.Y < 8) return;
        var grain = new Color(.65f, .55f, .35f, .045f);
        for (int y = 12; y < Size.Y - 7; y += 9)
            DrawLine(new Vector2(6, y), new Vector2(Size.X - 6, y + (y % 3 - 1)), grain);
        DrawLine(new Vector2(5, 3), new Vector2(Size.X - 5, 3), new Color("a18a5e"));
        DrawLine(new Vector2(5, Size.Y - 4), new Vector2(Size.X - 5, Size.Y - 4), new Color("100f0e"));
        foreach (var point in new[] { new Vector2(4, 4), new Vector2(Size.X - 5, 4), new Vector2(4, Size.Y - 5), new Vector2(Size.X - 5, Size.Y - 5) })
            DrawRect(new Rect2(point, new Vector2(2, 2)), new Color("a38e67"));
    }
}

/// <summary>Native button input with a readable key, icon, cooldown, and blocked-state marker.</summary>
public partial class AbilitySlot : ActionButton
{
    public Texture2D? AbilityIcon { get; private set; }
    public string KeyLabel { get; private set; } = "";
    public double CooldownSeconds { get; private set; }
    public string BlockReason { get; private set; } = "";
    public Element AbilityElement { get; private set; } = Element.Physical;
    private double cooldownLength = 1;
    private double activeUntil;

    public void Present(Texture2D? icon, string key, double remaining, double duration, Element element, string reason, string tooltip, bool connected)
    {
        AbilityIcon = icon; KeyLabel = key; CooldownSeconds = Math.Max(0, remaining); AbilityElement=element;
        cooldownLength = Math.Max(.01, duration); BlockReason = reason;
        Text = ""; Icon = null; TooltipText = tooltip;
        Disabled = !connected || icon is null || reason != "";
        QueueRedraw();
    }
    public void ShowActivation() { activeUntil = Time.GetTicksMsec() / 1000.0 + .4; QueueRedraw(); }

    public static Rect2 IconBounds(Vector2 size)
    {
        if (!float.IsFinite(size.X) || !float.IsFinite(size.Y) || size.X <= 16 || size.Y <= 18) return new Rect2();
        float width = size.X - 16, height = size.Y - 18;
        float side = MathF.Floor(MathF.Min(width, height));
        return new Rect2(new Vector2(MathF.Floor(8 + (width - side) / 2), MathF.Floor(10 + (height - side) / 2)), new Vector2(side, side));
    }
    public override void _Draw()
    {
        var area = IconBounds(Size);
        if (AbilityIcon is not null && area.Size.X > 0)
        {
            DrawTextureRect(AbilityIcon, area, false, Disabled ? new Color(.64f, .62f, .57f) : Colors.White);
            if (CooldownSeconds > 0)
                DrawRect(new Rect2(area.Position, new Vector2(area.Size.X, area.Size.Y * (float)Math.Clamp(CooldownSeconds / cooldownLength, 0, 1))), new Color(0, 0, 0, .72f));
            if(AbilityElement!=Element.Physical)
            {
                var badge=new Rect2(area.Position.X+area.Size.X-14,area.Position.Y+1,13,13);
                DrawRect(badge,Ui.Ink); DrawRect(badge,Ui.ElementColor(AbilityElement),false,1);
                DrawString(GetThemeDefaultFont(),new Vector2(badge.Position.X+3,badge.Position.Y+11),Ui.ElementGlyph(AbilityElement),HorizontalAlignment.Left,-1,9,Ui.ElementColor(AbilityElement));
            }
        }
        var font = GetThemeDefaultFont();
        DrawRect(new Rect2(2, 2, 19, 18), new Color("171512"));
        DrawString(font, new Vector2(6, 16), KeyLabel, HorizontalAlignment.Left, -1, 13, Ui.Text);
        if (CooldownSeconds > 0)
        {
            string seconds = CooldownSeconds >= 1 ? Math.Ceiling(CooldownSeconds).ToString("0") : CooldownSeconds.ToString("0.0");
            DrawStringOutline(font, new Vector2(0, Size.Y - 7), seconds, HorizontalAlignment.Center, Size.X, 18, 3, Ui.Ink);
            DrawString(font, new Vector2(0, Size.Y - 7), seconds, HorizontalAlignment.Center, Size.X, 18, Ui.Text);
        }
        else if (BlockReason != "" && AbilityIcon is not null)
            DrawString(font, new Vector2(Size.X - 15, Size.Y - 5), "!", HorizontalAlignment.Left, -1, 16, Ui.Danger);
        if (Time.GetTicksMsec() / 1000.0 < activeUntil)
            DrawRect(new Rect2(2, 2, Size.X - 4, Size.Y - 4), Ui.Gold, false, 2);
    }
}
