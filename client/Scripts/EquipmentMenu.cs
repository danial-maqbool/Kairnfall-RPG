using Godot;

namespace Kairnfall.Client;

/// <summary>An in-viewport item menu using the same native buttons as the rest of the UI.</summary>
public partial class EquipmentMenu : Control
{
    private readonly List<(string Text, int Id)> items = [];
    private readonly Dictionary<int, Button> buttons = [];
    private PanelContainer panel = null!;
    private Vector2 requestedPosition;
    private bool closed;
    public string Title { get; set; } = "Item actions";
    public string Subtitle { get; set; } = "";
    public Texture2D? Icon { get; set; }
    public Color Accent { get; set; } = Ui.Gold;
    public Action<int>? SelectedAction { get; set; }
    public Func<bool>? ContextValid { get; set; }

    public void AddItem(string text, int id)
    {
        if (IsInsideTree()) throw new InvalidOperationException("Configure item actions before showing the menu.");
        if (items.Any(x => x.Id == id)) throw new ArgumentException("Duplicate item action ID.", nameof(id));
        items.Add((text, id));
    }

    public Button GetActionButton(int id) => buttons[id];

    public override void _Ready()
    {
        MouseFilter = MouseFilterEnum.Stop;
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        panel = new PanelContainer { Name = "ItemActionPanel", CustomMinimumSize = new Vector2(280, 0) };
        panel.AddThemeStyleboxOverride("panel", Ui.Box(Ui.Ink, Accent, 12));
        AddChild(panel);
        var body = Ui.Column(panel);
        var heading = Ui.Row(body);
        if (Icon is not null) heading.AddChild(Ui.Image(Icon, 40));
        var words = Ui.Column(heading);
        words.AddChild(Ui.Label(Title, 16, Accent, true));
        if (Subtitle != "") words.AddChild(Ui.Label(Subtitle, 12, Ui.Muted, true));
        body.AddChild(new HSeparator());
        foreach (var item in items)
        {
            int id = item.Id;
            var button = Ui.Button(item.Text, () => SelectAction(id));
            button.Name = id == 0 ? "ItemContextPrimaryAction" : "ItemContextAction_" + id;
            button.CustomMinimumSize = new Vector2(0, 44);
            button.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            body.AddChild(button);
            buttons.Add(id, button);
        }
        Resized += PlacePanel;
        panel.Resized += PlacePanel;
        if (buttons.Count > 0) buttons.Values.First().GrabFocus();
    }

    public void OpenAt(Vector2 globalPosition)
    {
        requestedPosition = GetGlobalTransform().AffineInverse() * globalPosition + new Vector2(8, 8);
        Show(); PlacePanel();
    }

    private void PlacePanel()
    {
        if (panel is null || closed) return;
        const float margin = 8;
        panel.Position = new Vector2(
            Math.Clamp(requestedPosition.X, margin, Math.Max(margin, Size.X - panel.Size.X - margin)),
            Math.Clamp(requestedPosition.Y, margin, Math.Max(margin, Size.Y - panel.Size.Y - margin)));
    }

    private void SelectAction(int id)
    {
        if (closed) return;
        bool valid = ContextValid?.Invoke() != false;
        var action = SelectedAction;
        Close();
        if (valid) action?.Invoke(id);
    }

    public void Close()
    {
        if (closed) return;
        closed = true;
        Hide(); SetProcess(false); SetProcessInput(false);
        SelectedAction = null; ContextValid = null;
        QueueFree();
    }

    public override void _Process(double delta)
    {
        if (ContextValid?.Invoke() == false) Close();
    }

    public override void _Input(InputEvent input)
    {
        if (!closed && input is InputEventKey { Pressed: true, PhysicalKeycode: Key.Escape })
        {
            GetViewport().SetInputAsHandled(); Close();
        }
    }

    public override void _GuiInput(InputEvent input)
    {
        if (closed || input is not InputEventMouseButton { Pressed: true } mouse) return;
        if (mouse.ButtonIndex is MouseButton.Left or MouseButton.Right)
        {
            AcceptEvent(); Close();
        }
    }

    public override void _ExitTree()
    {
        Resized -= PlacePanel;
        if (panel is not null && GodotObject.IsInstanceValid(panel)) panel.Resized -= PlacePanel;
        SelectedAction = null; ContextValid = null; buttons.Clear(); items.Clear(); Icon = null;
        closed = true;
    }
}
