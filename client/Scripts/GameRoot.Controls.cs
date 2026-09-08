using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot
{
    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is InputEventKey { Pressed: true, Echo: false } key)
        {
            if (awaitingBinding != "")
            {
                StopCombatInput();
                if (key.PhysicalKeycode != Key.Escape)
                {
                    string? conflict = bindings.FirstOrDefault(x => x.Key != awaitingBinding && x.Value == key.PhysicalKeycode).Key;
                    int code = (int)key.PhysicalKeycode;
                    bool reserved = key.PhysicalKeycode == Key.Enter || code is >= 48 and <= 57
                        || key.PhysicalKeycode is Key.Left or Key.Right or Key.Up or Key.Down;
                    if (conflict is not null || reserved)
                    {
                        Notify(reserved ? "This key is reserved for movement, chat, or the hotbar."
                            : "That key already controls " + Ui.Words(conflict!) + ". Choose another key.", true);
                        GetViewport().SetInputAsHandled(); return;
                    }
                    bindings[awaitingBinding] = key.PhysicalKeycode;
                    ApplyBinding(awaitingBinding);
                    settings.SetValue("keys", awaitingBinding, (long)key.PhysicalKeycode);
                    settings.Save("user://settings.cfg");
                }
                awaitingBinding = "";
                OpenPage("Settings");
                GetViewport().SetInputAsHandled(); return;
            }
            if (key.PhysicalKeycode == Key.Escape)
            {
                StopCombatInput(); route.Clear(); pendingInteraction = null;
                if (Typing) GetViewport().GuiReleaseFocus();
                else if (placement != "") { placement = ""; Notify("Placement cancelled."); }
                else if (gameWindow is not null) ClosePage();
                else if (Online) OpenPage("Settings");
                GetViewport().SetInputAsHandled(); return;
            }
            if (!Online || Typing) return;
            if (key.PhysicalKeycode == Key.Enter)
            {
                StopCombatInput(); route.Clear(); pendingInteraction = null;
                ShowChat(true); chatInput.GrabFocus(); GetViewport().SetInputAsHandled(); return;
            }
            foreach (string action in new[] { "inventory", "character", "skills", "quests", "map", "abilities", "crafting", "social" })
            {
                if (!key.IsActionPressed(action)) continue;
                StopCombatInput(); route.Clear(); pendingInteraction = null;
                string name = Ui.Words(action);
                if (currentPage == name) ClosePage(); else OpenPage(name);
                GetViewport().SetInputAsHandled(); return;
            }
            if (!GameplayInputAllowed) return;
            if (key.IsActionPressed("basic_attack"))
            {
                BeginBasicAttack(true); GetViewport().SetInputAsHandled(); return;
            }
            if (key.IsActionPressed("interact"))
            {
                InteractWithContext(); GetViewport().SetInputAsHandled(); return;
            }
            if (key.IsActionPressed("target_next"))
            {
                CycleHostileTarget(); GetViewport().SetInputAsHandled(); return;
            }
            int hotkey = (int)key.PhysicalKeycode;
            if (hotkey is >= 48 and <= 57)
            {
                UseHotbar(hotkey == 48 ? 9 : hotkey - 49);
                GetViewport().SetInputAsHandled(); return;
            }
        }
        if (!GameplayInputAllowed || @event is not InputEventMouseButton { Pressed: true } mouse) return;
        if (mouse.ButtonIndex is MouseButton.WheelUp or MouseButton.WheelDown)
        {
            World.Zoom = Math.Clamp(World.Zoom + (mouse.ButtonIndex == MouseButton.WheelUp ? 1 : -1), 1, 3);
            settings.SetValue("display", "zoom", World.Zoom);
            settings.Save("user://settings.cfg");
            GetViewport().SetInputAsHandled(); return;
        }
        Point point = World.ScreenToWorld(mouse.Position);
        if (placement != "" && mouse.ButtonIndex == MouseButton.Left)
        {
            StopCombatInput();
            _ = SendAsync(new GameCommand { Kind = placement, Item = structureRecipe, X = point.X, Y = point.Y });
            placement = ""; GetViewport().SetInputAsHandled(); return;
        }
        if (mouse.ButtonIndex == MouseButton.Right)
        {
            StopCombatInput(); WalkTo(point); GetViewport().SetInputAsHandled(); return;
        }
        if (mouse.ButtonIndex != MouseButton.Left || World.Pick(mouse.Position) is not { } hit) return;
        SelectTarget(hit.Kind, hit.Id);
        if (hit.Kind == "creature")
        {
            // A single click selects. Only a deliberate attack input sends an attack.
            if (mouse.DoubleClick) BeginBasicAttack(false);
        }
        else if (hit.Kind == "player") OpenPage("Social");
        else if (Snapshot!.Self.Position.Distance(hit.Position) <= 2.15
            && WorldMap.LineOfSight(Data.Zone(Snapshot.Self.Zone), Snapshot.Self.Position, hit.Position)) Activate(hit);
        else
        {
            pendingInteraction = hit;
            WalkTo(hit.Position, keepInteraction: true);
        }
        GetViewport().SetInputAsHandled();
    }
}
