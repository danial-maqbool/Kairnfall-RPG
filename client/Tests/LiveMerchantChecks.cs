using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Native sale controls using the real connection, server, and disposable database.</summary>
internal static class LiveMerchantChecks
{
    public static async Task<(string ItemId, long Gold)> Run(Node host, GameRoot game, Action<bool,string> check)
    {
        var flags = BindingFlags.Instance | BindingFlags.NonPublic;
        Character Self() => game.Snapshot?.Self ?? throw new InvalidOperationException("The live merchant test requires a snapshot.");
        object? Call(string method, params object?[] args) => typeof(GameRoot).GetMethod(method, flags)!.Invoke(game, args);
        T Find<T>(string name) where T : Node => game.FindChildren(name, "", true, false).OfType<T>().Single(x => !x.IsQueuedForDeletion());
        async Task Frame() => await host.ToSignal(host.GetTree(), SceneTree.SignalName.ProcessFrame);
        async Task Delay(double seconds) => await host.ToSignal(host.GetTree().CreateTimer(seconds), SceneTreeTimer.SignalName.Timeout);
        async Task Until(Func<bool> condition, string failure, double seconds = 8)
        {
            double deadline = Time.GetTicksMsec() / 1000.0 + seconds;
            while (!condition()) { if (Time.GetTicksMsec() / 1000.0 >= deadline) throw new TimeoutException(failure); await Frame(); }
        }
        async Task Key(Key key)
        {
            using (var e = new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = true }) { Input.ParseInputEvent(e); Input.FlushBufferedEvents(); }
            await Frame();
            using (var e = new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = false }) { Input.ParseInputEvent(e); Input.FlushBufferedEvents(); }
            await Frame();
        }
        async Task Click(Button button)
        {
            check(button.IsVisibleInTree() && !button.Disabled && host.GetViewport().GetVisibleRect().Encloses(button.GetGlobalRect()), "The live merchant button is reachable: " + button.Name);
            var at = button.GetGlobalRect().GetCenter();
            using (var e = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, ButtonMask = MouseButtonMask.Left, Pressed = true }) { Input.ParseInputEvent(e); Input.FlushBufferedEvents(); }
            await Frame();
            using (var e = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, Pressed = false }) { Input.ParseInputEvent(e); Input.FlushBufferedEvents(); }
            await Frame();
        }

        Call("ClosePage"); Call("StopCombatInput"); host.GetViewport().GuiReleaseFocus();
        var npc = game.Data.Npcs.Where(n => n.Zone == Self().Zone && n.Role == "provisioner" && n.Stock.Length > 0)
            .OrderBy(n => n.Position.Distance(Self().Position)).First();
        var item = Self().Inventory.First(x => x.Template == "healing_potion" && x.Quantity >= 3);
        string id = item.Id; int initial = item.Quantity;
        double deadline = Time.GetTicksMsec() / 1000.0 + 30;
        // Setup uses ordinary movement intentions. It never edits authoritative position.
        while (Self().Position.Distance(npc.Position) > 2.4 || !WorldMap.LineOfSight(game.Data.Zone(Self().Zone), Self().Position, npc.Position))
        {
            if (Time.GetTicksMsec() / 1000.0 >= deadline) throw new TimeoutException("The village merchant has no reachable normal movement route.");
            var path = WorldMap.FindPath(game.Data.Zone(Self().Zone), Self().Position, npc.Position, 16000);
            var steps = path.Where(p => p.Distance(Self().Position) > .35).ToArray();
            if (steps.Length == 0) throw new InvalidOperationException("The village merchant path ended outside interaction range.");
            Point direction = Self().Position.Direction(steps[0]);
            await game.Connection!.MoveAsync(direction.X, direction.Y); await Delay(.08);
        }
        await game.Connection!.MoveAsync(0, 0); await Delay(.3);
        var talk = await game.Connection.ActAsync(new GameCommand { Kind = "talk", Target = npc.Id });
        check(talk.Ok, "The live server validates the merchant contact after normal movement");
        await Until(() => Self().LastAction >= talk.Sequence, "Merchant contact was not acknowledged in a snapshot.");
        typeof(GameRoot).GetField("selectedNpc", flags)!.SetValue(game, npc.Id);
        Call("OpenPage", "Shop"); await Delay(.3);
        await Click(Find<Button>("OpenMerchantSell")); await Delay(.3);
        var list = Find<ItemList>("SaleItems");
        var ordered = Self().Inventory.OrderBy(x => game.Data.Item(x.Template).Name, StringComparer.Ordinal).ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
        int index = Array.FindIndex(ordered, x => x.Id == id);
        check(index >= 0, "The real backpack potion is present in the merchant list");
        list.GrabFocus(); await Key(Godot.Key.Home);
        for (int i = 0; i < index; i++) await Key(Godot.Key.Down);
        await Delay(.25);
        var quantity = Find<LineEdit>("SaleQuantity"); quantity.GrabFocus(); await Frame(); quantity.SelectAll();
        using (var e = new InputEventKey { Keycode = (Godot.Key)50, PhysicalKeycode = (Godot.Key)50, Unicode = 50, Pressed = true }) { Input.ParseInputEvent(e); Input.FlushBufferedEvents(); }
        using (var e = new InputEventKey { Keycode = (Godot.Key)50, PhysicalKeycode = (Godot.Key)50, Pressed = false }) { Input.ParseInputEvent(e); Input.FlushBufferedEvents(); }
        await Frame();
        long gold = Self().Gold, unit = MerchantSales.UnitPrice(game.Data.Item(item.Template));
        check(quantity.Text == "2" && Find<Label>("SaleGoldTotal").Text.Contains((2 * unit).ToString("N0")), "Native typing gives the real two-item sale total");
        Call("SaveScreenshot", "13-merchant-live.png");
        await Click(Find<Button>("SellSelectedQuantity"));
        await Until(() => Self().Inventory.Any(x => x.Id == id && x.Quantity == initial - 2) && Self().Gold == gold + unit * 2, "The real server did not confirm the exact partial sale.");
        check(true, "Native Sell quantity transfers exactly two items and their gold over the real connection");
        await Until(() => !Find<Button>("SellAllQuantity").Disabled, "The sale controls did not unlock after the authoritative snapshot.");
        await Click(Find<Button>("SellAllQuantity"));
        await Until(() => !Self().Inventory.Any(x => x.Id == id) && Self().Gold == gold + unit * initial, "The real server did not confirm the remaining-stack sale.");
        check(true, "Native Sell all transfers the remaining selected stack and exact gold over the real connection");
        Call("SaveScreenshot", "14-merchant-after-sale.png");
        Call("ClosePage"); host.GetViewport().GuiReleaseFocus();
        return (id, Self().Gold);
    }
}
