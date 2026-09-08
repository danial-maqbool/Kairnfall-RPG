using Godot;

namespace Kairnfall.Client;

/// <summary>Item actions use the same native buttons and viewport as the inventory.</summary>
public partial class EquipmentMenu : Control
{
    private readonly List<(int Id, string Text, bool Disabled)> entries = [];
    private readonly Dictionary<int, Button> buttons = [];
    private PanelContainer? panel;
    private Vector2 requestedPosition;
    private bool closing;

    public string ItemName { get; set; } = "Item actions";
    public string Subtitle { get; set; } = "";
    public Texture2D? ItemIcon { get; set; }
    public Color ItemColor { get; set; } = Ui.Gold;
    public Action<long>? SelectedAction { get; set; }
    public Func<bool>? ContextValid { get; set; }

    public void AddItem(string text, int id, bool disabled = false)
    {
        if (IsInsideTree()) throw new InvalidOperationException("Configure item actions before attaching the menu.");
        if (entries.Any(x => x.Id == id)) throw new ArgumentException("Duplicate item action ID.", nameof(id));
        entries.Add((id, text, disabled));
    }

    public Button GetActionButton(int id) => buttons[id];

    public override void _Ready()
    {
        Name = "ItemContextMenu";
        MouseFilter = MouseFilterEnum.Stop;
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        panel = new PanelContainer
        {
            Name = "ItemContextPanel",
            CustomMinimumSize = new Vector2(280, 0),
            MouseFilter = MouseFilterEnum.Stop
        };
        panel.AddThemeStyleboxOverride("panel", Ui.Box(Ui.Ink, ItemColor, 12));
        AddChild(panel);
        var body = Ui.Column(panel);
        var heading = Ui.Row(body);
        heading.AddChild(Ui.Image(ItemIcon, 40));
        var description = Ui.Column(heading);
        description.AddChild(Ui.Label(ItemName, 16, ItemColor, true));
        if (Subtitle != "") description.AddChild(Ui.Label(Subtitle, 12, Ui.Muted, true));
        body.AddChild(new HSeparator());
        foreach (var entry in entries)
        {
            int actionId = entry.Id;
            var button = Ui.Button(entry.Text, () => Select(actionId), entry.Disabled);
            button.Name = actionId == 0 ? "ItemContextPrimaryAction" : "ItemContextAction" + actionId;
            button.CustomMinimumSize = new Vector2(0, 44);
            button.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            body.AddChild(button);
            buttons.Add(actionId, button);
        }
        Resized += Reposition;
        panel.Resized += Reposition;
        Reposition();
        buttons.Values.FirstOrDefault(x => !x.Disabled)?.GrabFocus();
    }

    public void OpenAt(Vector2 position)
    {
        requestedPosition = position;
        Reposition();
    }

    private void Reposition()
    {
        if (panel is null || !IsInsideTree()) return;
        Vector2 local = GetGlobalTransform().AffineInverse() * requestedPosition;
        const float margin = 8;
        float maxX = Math.Max(margin, Size.X - panel.Size.X - margin);
        float maxY = Math.Max(margin, Size.Y - panel.Size.Y - margin);
        panel.Position = new Vector2(Math.Clamp(local.X + margin, margin, maxX), Math.Clamp(local.Y + margin, margin, maxY));
    }

    public override void _Input(InputEvent input)
    {
        if (closing || !Visible) return;
        if (input is InputEventKey { Pressed: true, Echo: false } key
            && (key.PhysicalKeycode == Key.Escape || key.Keycode == Key.Escape))
        {
            GetViewport().SetInputAsHandled();
            Close();
        }
    }

    public override void _GuiInput(InputEvent input)
    {
        if (input is not InputEventMouseButton { Pressed: true } mouse) return;
        if (mouse.ButtonIndex is not (MouseButton.Left or MouseButton.Right)) return;
        AcceptEvent();
        Close();
    }

    public override void _Process(double delta)
    {
        if (!closing && ContextValid?.Invoke() == false) Close();
    }

    private void Select(int id)
    {
        if (closing || !buttons.TryGetValue(id, out var button) || button.Disabled) return;
        if (ContextValid?.Invoke() == false) { Close(); return; }
        var action = SelectedAction;
        Close();
        action?.Invoke(id);
    }

    public void Close()
    {
        if (closing) return;
        closing = true;
        SelectedAction = null;
        ContextValid = null;
        Hide();
        SetProcess(false);
        SetProcessInput(false);
        QueueFree();
    }

    public override void _ExitTree()
    {
        Resized -= Reposition;
        if (GodotObject.IsInstanceValid(panel)) panel!.Resized -= Reposition;
        SelectedAction = null;
        ContextValid = null;
        ItemIcon = null;
        buttons.Clear();
    }
}
