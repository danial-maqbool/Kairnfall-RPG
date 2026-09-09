using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>Boundary fixtures for visible sale totals and fresh equipment comparisons.</summary>
internal static class MerchantBoundaryUiChecks
{
    public static async Task Run(Node host, GameRoot game, Action<bool, string> check)
    {
        var flags = BindingFlags.Instance | BindingFlags.NonPublic;
        FieldInfo Field(string name) => typeof(GameRoot).GetField(name, flags)!;
        object? Call(string name, params object?[] args) => typeof(GameRoot).GetMethod(name, flags)!.Invoke(game, args);
        async Task Frame() => await host.ToSignal(host.GetTree(), SceneTree.SignalName.ProcessFrame);
        T Find<T>(string name) where T : Node => game.FindChildren(name, "", true, false).OfType<T>().First(x => !x.IsQueuedForDeletion());
        bool Fits(Control control) => control.IsVisibleInTree() && control.Size.X > 0 && control.Size.Y > 0
            && host.GetViewport().GetVisibleRect().Encloses(control.GetGlobalRect());
        async Task Click(Button button)
        {
            check(Fits(button) && !button.Disabled, "A large-total sale button is visible and usable before native input");
            var at = button.GetGlobalRect().GetCenter();
            using (var e = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, ButtonMask = MouseButtonMask.Left, Pressed = true }) host.GetViewport().PushInput(e, true);
            await Frame();
            using (var e = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, Pressed = false }) host.GetViewport().PushInput(e, true);
            await Frame(); await Frame();
        }
        async Task TypeQuantity(LineEdit edit, string text)
        {
            edit.GrabFocus(); await Frame(); edit.SelectAll();
            using (var e = new InputEventKey { Keycode = Key.Backspace, PhysicalKeycode = Key.Backspace, Pressed = true }) host.GetViewport().PushInput(e, true);
            using (var e = new InputEventKey { Keycode = Key.Backspace, PhysicalKeycode = Key.Backspace, Pressed = false }) host.GetViewport().PushInput(e, true);
            foreach (char character in text)
            {
                var code = (Key)char.ToUpperInvariant(character);
                using (var e = new InputEventKey { Keycode = code, PhysicalKeycode = code, Unicode = character, Pressed = true }) host.GetViewport().PushInput(e, true);
                using (var e = new InputEventKey { Keycode = code, PhysicalKeycode = code, Pressed = false }) host.GetViewport().PushInput(e, true);
                await Frame();
            }
            await Frame();
            check(edit.Text == text, "Native keyboard events enter the exact high-value sale quantity");
        }
        async Task Capture(string name)
        {
            if (DisplayServer.GetName() == "headless") return;
            await Frame(); await host.ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
            string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS") ?? ProjectSettings.GlobalizePath("user://visual-review");
            System.IO.Directory.CreateDirectory(root);
            using var image = host.GetViewport().GetTexture().GetImage();
            check(image.SavePng(System.IO.Path.Combine(root, name + ".png")) == Error.Ok, "Saved native merchant boundary frame " + name);
        }
        var original = game.World.Snapshot;
        string oldNpc = (string)Field("selectedNpc").GetValue(game)!;
        // A copied catalog exercises bulk and high prices without changing the live economy.
        var data = Wire.Copy(game.Data); var ore = data.Item("copper_ore");
        ore.StackMax = 999; ore.Value = 3_000_000;
        var realm = new RealmEngine(data); var self = realm.CreateCharacter("merchant-boundary", "Merchant Boundary", "vanguard", new());
        var merchant = data.Npcs.First(n => n.Role == "provisioner" && n.Stock.Length > 0);
        try
        {
            foreach (var size in new[] { new Vector2I(1280, 720), new Vector2I(1920, 1080) })
            {
                host.GetWindow().Size = size; host.GetWindow().ContentScaleSize = size;
                self = realm.Player(self.Id); self.Inventory.Clear(); self.Equipment.Clear();
                self.Health = 100; self.Gold = 100; self.Zone = merchant.Zone; self.Position = merchant.Position;
                var stack = Items.Create(data, ore.Id, 999); self.Inventory.Add(stack);
                game.World.Accept(new TransportPacket { Snapshot = realm.Snapshot(self.Id) });
                Field("selectedNpc").SetValue(game, merchant.Id); Call("OpenPage", "Sell");
                await Frame(); await Frame(); await Frame();
                var panel = Find<MerchantSellPanel>("MerchantSellPanel"); panel.Data = data; panel.Merchant = merchant;
                panel.ReadCharacter = () => self;
                int requests = 0;
                panel.SellItem = (id, quantity) =>
                {
                    requests++;
                    var result = realm.Execute(self.Id, new GameCommand { Kind = "sell", Target = merchant.Id, Item = id, Amount = quantity, Sequence = self.LastAction + 1 });
                    self = realm.Player(self.Id); return Task.FromResult<CommandResult?>(result);
                };
                panel.RefreshSnapshot();
                var amount = Find<LineEdit>("SaleQuantity"); await TypeQuantity(amount, "777");
                await Frame(); await Frame(); await Frame();
                var partial = Find<Button>("SellSelectedQuantity"); var all = Find<Button>("SellAllQuantity");
                long unit = MerchantSales.UnitPrice(ore), gold = self.Gold;
                check(partial.Text.Contains((unit * 777).ToString("N0")) && all.Text.Contains((unit * 999).ToString("N0")), "Both high-value sale buttons retain their full exact totals");
                check(Fits(partial) && Fits(all) && Fits(amount), "High-value sale actions and quantity remain inside the " + size + " viewport");
                check(!partial.GetGlobalRect().Intersects(all.GetGlobalRect()), "The two large-total sale actions do not overlap");
                await Capture("merchant-large-totals-" + size.X);
                await Click(partial);
                check(requests == 1 && self.Gold == gold + unit * 777 && Items.Owned(self, stack.Id).Quantity == 222,
                    "Native high-value partial sale retains exact integer gold and the remaining stack");
                check(amount.Text == "777" && partial.Disabled && !all.Disabled, "A now-excessive partial amount remains unchanged while Sell all stays available");
                await Click(all);
                check(requests == 2 && self.Gold == gold + unit * 999 && !self.Inventory.Any(x => x.Id == stack.Id), "Native Sell all completes only the high-value selected stack with exact gold");
                Call("ClosePage"); await Frame(); await Frame();

                // The equipped item's data may change without changing its instance ID.
                self = realm.Player(self.Id); self.Inventory.Clear(); self.Equipment.Clear(); self.Gold = 100;
                var equipped = Items.Create(data, "copper_sword"); equipped.Affixes = [new() { Stat = "vitality", Value = 6 }];
                var inspected = Items.Create(data, "iron_sword"); inspected.Affixes = [new() { Stat = "vitality", Value = 1 }];
                self.Inventory.AddRange([equipped, inspected]); self.Equipment["weapon"] = equipped.Id;
                game.World.Accept(new TransportPacket { Snapshot = realm.Snapshot(self.Id) }); Call("OpenPage", "Sell");
                await Frame(); await Frame(); await Frame();
                panel = Find<MerchantSellPanel>("MerchantSellPanel"); panel.Data = data; panel.ReadCharacter = () => self;
                var ordered = self.Inventory.OrderBy(x => data.Item(x.Template).Name, StringComparer.Ordinal).ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
                int index = Array.FindIndex(ordered, x => x.Id == inspected.Id);
                var list = Find<ItemList>("SaleItems"); list.Select(index); list.EmitSignal(ItemList.SignalName.ItemSelected, (long)index);
                panel.RefreshSnapshot(); await Frame(); await Frame();
                check(Find<Label>("StatDelta_vitality").Text == "-5", "The merchant inspection initially compares against the actual equipped bonus");
                amount = Find<LineEdit>("SaleQuantity"); amount.Text = "1"; amount.GrabFocus(); amount.CaretColumn = 1;
                equipped.Affixes[0].Value = 2;
                panel.RefreshSnapshot(); await Frame(); await Frame();
                check(Find<Label>("StatDelta_vitality").Text == "-1" && Find<Label>("StatDelta_vitality").GetThemeColor("font_color") == Ui.Danger,
                    "An equipped-stat snapshot change refreshes its signed comparison without an equipment-ID change");
                check(amount.Text == "1" && amount.CaretColumn == 1, "Refreshing comparison data preserves pending quantity and caret");
                equipped.Durability = 0;
                panel.RefreshSnapshot(); await Frame(); await Frame();
                check(Find<Label>("StatDelta_vitality").Text == "+1" && Find<Label>("StatDelta_vitality").GetThemeColor("font_color") == Ui.Success,
                    "Broken equipped gear cannot leave a stale red stat comparison");
                await Capture("merchant-fresh-comparison-" + size.X);
                Call("ClosePage"); await Frame(); await Frame();
            }
        }
        finally
        {
            Call("ClosePage"); await Frame(); await Frame(); Field("selectedNpc").SetValue(game, oldNpc);
            if (original is not null) game.World.Accept(new TransportPacket { Snapshot = original });
        }
    }
}
