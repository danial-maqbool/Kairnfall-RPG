using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public static class Ui
{
    public static readonly Color Ink = new("111c26"), Panel = new("17252e"), Raised = new("253740"), Gold = new("d1b87c"), Text = new("ece4cf"), Muted = new("a5b5b0"), Danger = new("d98976"), Success = new("a9c78b");
    public static readonly Color[] RarityColors = [new("c1c5bd"), new("8abd8b"), new("81b0d3"), new("b099d4"), new("dbad69"), new("d5808c"), new("e7d99b")];
    public static Color RarityColor(Rarity rarity) => RarityColors[Math.Clamp((int)rarity, 0, RarityColors.Length - 1)];
    public static string Words(string text) => System.Globalization.CultureInfo.InvariantCulture.TextInfo.ToTitleCase(text.Replace('_', ' '));

    public static StyleBoxFlat Box(Color color, Color? border = null, int padding = 10)
    {
        var box = new StyleBoxFlat { BgColor = color, BorderColor = border ?? new Color("4f5e60"), ContentMarginLeft = padding, ContentMarginRight = padding, ContentMarginTop = padding, ContentMarginBottom = padding };
        box.SetBorderWidthAll(1);
        box.SetCornerRadiusAll(3);
        return box;
    }

    public static Theme BuildTheme()
    {
        var theme = new Theme { DefaultFontSize = 16 };
        theme.SetColor("font_color", "Label", Text);
        theme.SetColor("font_color", "Button", Text);
        theme.SetColor("font_hover_color", "Button", Colors.White);
        theme.SetColor("font_pressed_color", "Button", Gold);
        theme.SetColor("font_disabled_color", "Button", new Color("64787a"));
        theme.SetStylebox("normal", "Button", Box(Raised));
        theme.SetStylebox("hover", "Button", Box(new Color("354953"), Gold));
        theme.SetStylebox("pressed", "Button", Box(Ink, Gold));
        theme.SetStylebox("disabled", "Button", Box(new Color("1a292f"), new Color("314348")));
        theme.SetStylebox("focus", "Button", Box(new Color(0, 0, 0, 0), Gold, 0));
        theme.SetStylebox("panel", "PanelContainer", Box(Panel, new Color("627471"), 16));
        theme.SetStylebox("normal", "LineEdit", Box(Ink, new Color("566c70")));
        theme.SetStylebox("focus", "LineEdit", Box(Ink, Gold));
        theme.SetColor("font_color", "LineEdit", Text);
        theme.SetColor("caret_color", "LineEdit", Gold);
        theme.SetColor("font_placeholder_color", "LineEdit", Muted);
        theme.SetStylebox("normal", "TextEdit", Box(Ink));
        theme.SetColor("default_color", "RichTextLabel", Text);
        theme.SetColor("font_color", "OptionButton", Text);
        theme.SetStylebox("normal", "OptionButton", Box(Raised));
        theme.SetStylebox("hover", "OptionButton", Box(Raised, Gold));
        theme.SetStylebox("panel", "PopupMenu", Box(Panel));
        theme.SetColor("font_color", "PopupMenu", Text);
        theme.SetStylebox("panel", "TooltipPanel", Box(Ink, Gold));
        theme.SetColor("font_color", "TooltipLabel", Text);
        theme.SetFontSize("font_size", "TooltipLabel", 15);
        theme.SetStylebox("background", "ProgressBar", Box(Ink, new Color("536366"), 0));
        theme.SetStylebox("fill", "ProgressBar", Box(new Color("8b4548"), new Color("ac6761"), 0));
        theme.SetConstant("separation", "VBoxContainer", 8);
        theme.SetConstant("separation", "HBoxContainer", 8);
        theme.SetConstant("h_separation", "GridContainer", 7);
        theme.SetConstant("v_separation", "GridContainer", 7);
        return theme;
    }

    public static Label Label(string text, int size = 16, Color? color = null, bool wrap = false)
    {
        var label = new Label { Text = text, MouseFilter = Control.MouseFilterEnum.Ignore };
        label.AddThemeFontSizeOverride("font_size", size);
        label.AddThemeColorOverride("font_color", color ?? Text);
        if (wrap) { label.AutowrapMode = TextServer.AutowrapMode.WordSmart; label.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill; }
        return label;
    }
    public static Button Button(string text, Action action, bool disabled = false)
    {
        ArgumentNullException.ThrowIfNull(action);
        return new ActionButton
        {
            Text = text,
            Disabled = disabled,
            PressedAction = action,
            CustomMinimumSize = new Vector2(0, 36),
            MouseDefaultCursorShape = Control.CursorShape.PointingHand
        };
    }
    public static LineEdit Edit(string placeholder, string text = "", bool secret = false)
        => new() { PlaceholderText = placeholder, Text = text, Secret = secret, MaxLength = 128, CustomMinimumSize = new Vector2(0, 38), SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
    public static VBoxContainer Column(Node parent, bool expand = false)
    {
        var box = new VBoxContainer { SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
        if (expand) box.SizeFlagsVertical = Control.SizeFlags.ExpandFill;
        parent.AddChild(box); return box;
    }
    public static HBoxContainer Row(Node parent)
    {
        var box = new HBoxContainer { SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
        parent.AddChild(box); return box;
    }
    public static ScrollContainer Scroll(Node parent, Vector2 minimum)
    {
        var scroll = new ScrollContainer { CustomMinimumSize = minimum, SizeFlagsHorizontal = Control.SizeFlags.ExpandFill, SizeFlagsVertical = Control.SizeFlags.ExpandFill, HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled };
        parent.AddChild(scroll); return scroll;
    }
    public static void Clear(Node parent)
    {
        foreach (Node child in parent.GetChildren()) { parent.RemoveChild(child); child.QueueFree(); }
    }
    public static TextureRect Image(Texture2D? texture, int size)
        => new() { Texture = texture, CustomMinimumSize = new Vector2(size, size), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, TextureFilter = CanvasItem.TextureFilterEnum.Nearest, MouseFilter = Control.MouseFilterEnum.Ignore };
    public static ProgressBar Bar(Color color, int width = 230)
    {
        var bar = new ProgressBar { CustomMinimumSize = new Vector2(width, 15), ShowPercentage = false, MaxValue = 100 };
        bar.AddThemeStyleboxOverride("fill", Box(color, color.Lightened(.15f), 0));
        return bar;
    }
}

public partial class ItemSlot : Control
{
    public Texture2D? Icon { get; set; }
    public Item? Item { get; set; }
    public string Bag { get; set; } = "inventory";
    public bool Equipped { get; set; }
    public bool Selected { get; set; }
    public Action? Clicked { get; set; }
    public Action? DoubleClicked { get; set; }
    public Action? RightClicked { get; set; }
    public Action<string, string>? Dropped { get; set; }
    public override void _Ready() { CustomMinimumSize = new Vector2(62, 62); MouseDefaultCursorShape = CursorShape.PointingHand; TextureFilter = TextureFilterEnum.Nearest; }
    public override void _Draw()
    {
        Color border = Selected ? Ui.Gold : Item is null ? new Color("425359") : Ui.RarityColor(Item.Rarity);
        DrawStyleBox(Ui.Box(Ui.Ink, border, 0), new Rect2(Vector2.Zero, Size));
        if (Icon is not null) DrawTextureRect(Icon, new Rect2(7, 5, Size.X - 14, Size.Y - 14), false);
        if (Equipped) DrawString(ThemeDB.FallbackFont, new Vector2(4, 14), "E", HorizontalAlignment.Left, -1, 11, Ui.Gold);
        if (Item is { Quantity: > 1 })
        {
            string count = Item.Quantity.ToString();
            DrawStringOutline(ThemeDB.FallbackFont, new Vector2(4, Size.Y - 4), count, HorizontalAlignment.Right, Size.X - 8, 13, 3, Ui.Ink);
            DrawString(ThemeDB.FallbackFont, new Vector2(4, Size.Y - 4), count, HorizontalAlignment.Right, Size.X - 8, 13, Ui.Text);
        }
    }
    public override void _GuiInput(InputEvent @event)
    {
        if (@event is not InputEventMouseButton { Pressed: true } mouse)
            return;

        if (mouse.ButtonIndex == MouseButton.Left)
        {
            if (mouse.DoubleClick && DoubleClicked is not null)
                DoubleClicked.Invoke();
            else
                Clicked?.Invoke();

            AcceptEvent();
            return;
        }

        if (mouse.ButtonIndex == MouseButton.Right)
        {
            RightClicked?.Invoke();
            AcceptEvent();
        }
    }
    public override Variant _GetDragData(Vector2 position)
    {
        if (Item is null) return default;
        var preview = Ui.Image(Icon, 48); SetDragPreview(preview);
        return new Godot.Collections.Dictionary { ["item"] = Item.Id, ["bag"] = Bag };
    }
    public override bool _CanDropData(Vector2 position, Variant data)
        => Dropped is not null && data.VariantType == Variant.Type.Dictionary && data.AsGodotDictionary().ContainsKey("item") && data.AsGodotDictionary().ContainsKey("bag");
    public override void _DropData(Vector2 position, Variant data)
    {
        if (!_CanDropData(position, data)) return;
        var value = data.AsGodotDictionary(); Dropped?.Invoke(value["item"].AsString(), value["bag"].AsString());
    }
}
