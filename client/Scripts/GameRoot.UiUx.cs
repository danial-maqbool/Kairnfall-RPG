using Godot;

namespace Kairnfall.Client;

/// <summary>Shared keyboard, modal, scaling, and accessibility behavior for every client panel.</summary>
public partial class GameRoot
{
    private const string CapturedFontMetaPrefix = "kairnfall_captured_font_";
    private PanelContainer? uxTrackedWindow;
    private ColorRect? modalInputBlocker;
    private Control? modalReturnFocus;
    private readonly Dictionary<Control, FocusModeEnum> suspendedBackgroundFocus = [];
    private ulong settingsUxWindowId;
    private bool uiUxInitialized;
    private float uiTextScale = 1f;

    public override void _PhysicsProcess(double delta)
    {
        if (closing || !IsInsideTree()) return;
        if (!uiUxInitialized) InitializeUiUx();
        SynchronizeModalUx();
        EnsureAccessibleNotice();
    }

    private void InitializeUiUx()
    {
        uiUxInitialized = true;
        var stored = settings.GetValue("accessibility", "text_scale", 1.0);
        ApplyUiTextScale(stored.VariantType is Variant.Type.Float or Variant.Type.Int ? stored.AsDouble() : 1d, false);
    }

    private void SynchronizeModalUx()
    {
        if (gameWindow is null || !GodotObject.IsInstanceValid(gameWindow))
        {
            if (uxTrackedWindow is not null) ExitModalUx();
            return;
        }

        if (uxTrackedWindow != gameWindow) EnterModalUx(gameWindow);
        FitOpenPage();
        if (currentPage == "Settings" && settingsUxWindowId != gameWindow.GetInstanceId()) AddAccessibilityControls();
    }

    private void EnterModalUx(PanelContainer window)
    {
        bool firstModal = uxTrackedWindow is null;
        uxTrackedWindow = window;
        if (firstModal)
        {
            modalReturnFocus = GetViewport().GuiGetFocusOwner();
            SuspendBackgroundFocus(window);
            modalInputBlocker = new ColorRect
            {
                Name = "ModalInputBlocker",
                Color = new Color(0, 0, 0, 0),
                MouseFilter = MouseFilterEnum.Stop,
                FocusMode = FocusModeEnum.None,
                ZIndex = 100
            };
            interfaceRoot.AddChild(modalInputBlocker);
            modalInputBlocker.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            // GUI picking follows tree order, not CanvasItem.ZIndex.
            interfaceRoot.MoveChild(modalInputBlocker, window.GetIndex());
        }
        window.ZIndex = 101;
        ApplyScaledFontOverrides(window);
        FocusModalDefault();
    }

    private void SuspendBackgroundFocus(Control activeWindow)
    {
        suspendedBackgroundFocus.Clear();
        foreach (var control in interfaceRoot.FindChildren("*", "Control", true, false).OfType<Control>())
        {
            if (control == activeWindow || activeWindow.IsAncestorOf(control) || control.FocusMode == FocusModeEnum.None) continue;
            suspendedBackgroundFocus[control] = control.FocusMode;
            control.FocusMode = FocusModeEnum.None;
        }
    }

    private void ExitModalUx()
    {
        bool hadModal = uxTrackedWindow is not null;
        if (modalInputBlocker is not null && GodotObject.IsInstanceValid(modalInputBlocker))
        {
            modalInputBlocker.Hide();
            modalInputBlocker.QueueFree();
        }
        modalInputBlocker = null;
        foreach (var entry in suspendedBackgroundFocus)
            if (GodotObject.IsInstanceValid(entry.Key)) entry.Key.FocusMode = entry.Value;
        suspendedBackgroundFocus.Clear();

        var restore = modalReturnFocus;
        modalReturnFocus = null;
        uxTrackedWindow = null;
        settingsUxWindowId = 0;
        if (restore is not null && GodotObject.IsInstanceValid(restore) && !restore.IsQueuedForDeletion() && restore.IsVisibleInTree() && restore.FocusMode != FocusModeEnum.None && restore is not BaseButton { Disabled: true })
            restore.GrabFocus();
        else if (hadModal)
            GetViewport().GuiReleaseFocus();
    }

    private void FocusModalDefault()
    {
        if (gameWindow is null || !GodotObject.IsInstanceValid(gameWindow)) return;
        var focused = GetViewport().GuiGetFocusOwner();
        if (focused is not null && (focused == gameWindow || gameWindow.IsAncestorOf(focused))) return;
        var close = gameWindow.FindChildren("*", "Button", true, false).OfType<Button>()
            .FirstOrDefault(button => !button.Disabled && button.Visible && button.Text.StartsWith("Close", StringComparison.Ordinal));
        if (close is not null) close.GrabFocus();
    }

    private void FitOpenPage()
    {
        if (gameWindow is null || !GodotObject.IsInstanceValid(gameWindow)) return;
        Vector2 viewport = Size;
        if (viewport.X <= 0 || viewport.Y <= 0) viewport = GetViewport().GetVisibleRect().Size;
        if (viewport.X <= 0 || viewport.Y <= 0) return;

        var desired = new Vector2(
            Math.Max(320, Math.Min(1100, viewport.X - 80)),
            Math.Max(300, Math.Min(670, viewport.Y - 140)));
        gameWindow.Size = desired;
        var position = gameWindow.Position;
        position.X = Math.Clamp(position.X, 0, Math.Max(0, viewport.X - gameWindow.Size.X));
        position.Y = Math.Clamp(position.Y, 0, Math.Max(0, viewport.Y - gameWindow.Size.Y));
        gameWindow.Position = position;
    }

    private void AddAccessibilityControls()
    {
        if (page is null || gameWindow is null) return;
        settingsUxWindowId = gameWindow.GetInstanceId();
        var rows = page.FindChildren("*", "VBoxContainer", true, false).OfType<VBoxContainer>().FirstOrDefault() ?? page;
        rows.AddChild(new HSeparator());
        rows.AddChild(Ui.Label("Accessibility and keyboard navigation", 22, Ui.Gold));
        rows.AddChild(Ui.Label("Tab and Shift+Tab move through panel controls. Enter or Space activates the focused control. Escape closes the current panel; Enter opens chat while in the world.", 15, Ui.Muted, true));

        var scaleRow = Ui.Row(rows);
        var scaleTitle = Ui.Label("Text size", 16);
        scaleTitle.CustomMinimumSize = new Vector2(220, 0);
        scaleRow.AddChild(scaleTitle);
        var selector = new OptionButton { Name = "TextScaleSelector", CustomMinimumSize = new Vector2(180, 36) };
        var values = new[] { .9f, 1f, 1.15f, 1.25f };
        for (int i = 0; i < values.Length; i++) selector.AddItem($"{values[i] * 100:0}%", i);
        int selected = Array.FindIndex(values, value => Math.Abs(value - uiTextScale) < .01f);
        selector.Select(selected < 0 ? 1 : selected);
        selector.TooltipText = "Scales interface text without changing world-pixel rendering.";
        selector.ItemSelected += index =>
        {
            int choice = (int)index;
            if (choice < 0 || choice >= values.Length) return;
            ApplyUiTextScale(values[choice], true);
        };
        scaleRow.AddChild(selector);
        rows.AddChild(Ui.Label("Windows monitor DPI scaling remains enabled separately; this setting changes only interface text.", 14, Ui.Muted, true));
        ApplyScaledFontOverrides(rows);
    }

    private void ApplyUiTextScale(double requested, bool save)
    {
        uiTextScale = Ui.ConfigureTextScale(requested);
        Theme = Ui.BuildTheme();
        ApplyScaledFontOverrides(this);
        if (!save) return;
        settings.SetValue("accessibility", "text_scale", uiTextScale);
        settings.Save("user://settings.cfg");
        Notify($"Text size set to {uiTextScale * 100:0}%.");
    }

    private void ApplyScaledFontOverrides(Node root)
    {
        if (root is Control rootControl) ScaleControlOverrides(rootControl);
        foreach (var control in root.FindChildren("*", "Control", true, false).OfType<Control>()) ScaleControlOverrides(control);
    }

    private static void ScaleControlOverrides(Control control)
    {
        ScaleFontOverride(control, "font_size");
        ScaleFontOverride(control, "normal_font_size");
        ScaleFontOverride(control, "bold_font_size");
        ScaleFontOverride(control, "italics_font_size");
        ScaleFontOverride(control, "bold_italics_font_size");
        ScaleFontOverride(control, "mono_font_size");
    }

    private static void ScaleFontOverride(Control control, string themeName)
    {
        if (!control.HasThemeFontSizeOverride(themeName)) return;
        string meta = CapturedFontMetaPrefix + themeName;
        int baseSize;
        if (control.HasMeta(meta)) baseSize = (int)control.GetMeta(meta).AsInt64();
        else if (themeName == "font_size" && control.HasMeta(Ui.BaseFontSizeMeta))
        {
            baseSize = (int)control.GetMeta(Ui.BaseFontSizeMeta).AsInt64();
            control.SetMeta(meta, baseSize);
        }
        else
        {
            baseSize = control.GetThemeFontSize(themeName);
            control.SetMeta(meta, baseSize);
        }
        control.AddThemeFontSizeOverride(themeName, Ui.ScaledFont(baseSize));
    }

    private void EnsureAccessibleNotice()
    {
        if (notice is null || !GodotObject.IsInstanceValid(notice) || string.IsNullOrWhiteSpace(notice.Text)) return;
        if (!notice.GetThemeColor("font_color").IsEqualApprox(Ui.Danger) || notice.Text.StartsWith("Error · ", StringComparison.Ordinal)) return;
        notice.Text = "Error · " + notice.Text;
    }
}
