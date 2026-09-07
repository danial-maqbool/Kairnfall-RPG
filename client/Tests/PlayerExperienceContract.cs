using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Native control tests and bounded offline fixtures; not a multiplayer playthrough.</summary>
public partial class PlayerExperienceContract : Node
{
    private int checks;
    private void Require(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++;
        GD.Print("PASS EXPERIENCE: " + message);
    }
    private static object? Call(GameRoot game, string method, params object?[] arguments)
        => typeof(GameRoot).GetMethod(method, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, arguments);
    private static T Field<T>(GameRoot game, string name)
        => (T)typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private void Mouse(Control control, MouseButton button, bool pressed, bool doubleClick = false)
    {
        Vector2 position = control.GetGlobalRect().GetCenter();
        using var input = new InputEventMouseButton
        {
            Position = position, GlobalPosition = position, ButtonIndex = button,
            ButtonMask = pressed ? button == MouseButton.Left ? MouseButtonMask.Left : MouseButtonMask.Right : 0,
            Pressed = pressed, DoubleClick = doubleClick
        };
        GetViewport().PushInput(input, true);
    }

    public override async void _Ready()
    {
        try
        {
            var data = PixelAssets.LoadCatalog();
            var realm = new RealmEngine(data);
            var self = realm.CreateCharacter("experience-fixture", "Experience Tester", "vanguard", new());
            Require(ExperienceRules.AllowsWorldInput(true, false, false, true, true), "World input is available during normal play");
            Require(!ExperienceRules.AllowsWorldInput(true, true, false, true, true), "Typing blocks world input");
            Require(!ExperienceRules.AllowsWorldInput(true, false, true, true, true), "Menus block world input");
            Require(!ExperienceRules.AllowsWorldInput(true, false, false, false, true), "Lost focus blocks world input");
            Require(!ExperienceRules.AllowsWorldInput(true, false, false, true, false), "Death blocks world input");
            Require(!ExperienceRules.AllowsWorldInput(false, false, false, true, true), "Disconnect blocks world input");
            var gate = new AttackRequestGate();
            Require(gate.TryTake(1, 10, 10, true), "A ready attack may request once");
            Require(!gate.TryTake(1.01, 10, 10, true), "Repeated held input cannot request each frame");
            Require(!gate.TryTake(1.2, 10, 11, true), "Server cooldown prevents an early attack request");
            Require(!gate.TryTake(1.2, 12, 11, false), "Disabled input does not consume an attack");
            Require(gate.TryTake(1.2, 12, 11, true), "A later valid attack is allowed");
            Require(!gate.TryTake(double.NaN, 12, 11, true), "Invalid time is rejected");

            var zone = data.Zone(self.Zone);
            var near = Enumerable.Range(-10, 21).SelectMany(x => Enumerable.Range(-10, 21).Select(y => self.Position.Add(new Point(x * .1, y * .1))))
                .First(x => x.Distance(self.Position) > .8 && WorldMap.Fits(zone, x) && WorldMap.LineOfSight(zone, self.Position, x));
            string aggressive = data.Mobs.First(x => x.Ai is not "passive" and not "fleeing").Id;
            var target = new Creature { Id = "target", Template = aggressive, Zone = self.Zone, Position = near, Home = near, Health = 10 };
            Require(ExperienceRules.ChooseTarget(self, [target], data, "", 2)?.Id == target.Id, "Space can choose a nearby hostile without a mouse target");
            var pet = Wire.Copy(target); pet.Id = "pet"; pet.Owner = self.Id;
            Require(ExperienceRules.ChooseTarget(self, [pet], data, pet.Id, 2) is null, "Owned companions cannot be attack targets");
            var dead = Wire.Copy(target); dead.Health = 0;
            Require(ExperienceRules.ChooseTarget(self, [dead], data, "", 2) is null, "Dead creatures cannot be selected");
            var distant = Wire.Copy(target); distant.Position = self.Position.Add(new Point(20, 0));
            Require(!ExperienceRules.CanTarget(self, distant, data, 2), "Out-of-range creatures are rejected");
            var foreign = Wire.Copy(target); foreign.Zone = "other-zone";
            Require(!ExperienceRules.CanTarget(self, foreign, data, 2), "Other regions cannot be targeted");
            var blocked = Enumerable.Range(0, zone.Width).SelectMany(x => Enumerable.Range(0, zone.Height).Select(y => new Point(x + .5, y + .5)))
                .First(x => !WorldMap.LineOfSight(zone, self.Position, x));
            var hidden = Wire.Copy(target); hidden.Position = blocked;
            Require(!ExperienceRules.CanTarget(self, hidden, data, 1000), "Line of sight prevents targeting through obstacles");
            var passiveDefinition = data.Mobs.FirstOrDefault(x => x.Ai == "passive");
            if (passiveDefinition is not null)
            {
                var passive = Wire.Copy(target); passive.Template = passiveDefinition.Id;
                Require(!ExperienceRules.CanTarget(self, passive, data, 2), "Automatic targeting leaves peaceful wildlife alone");
                Require(ExperienceRules.CanTarget(self, passive, data, 2, true), "Explicit selection still permits hunting wildlife");
            }
            Require(ExperienceRules.ChooseInteraction(self, [], data) is null, "Empty-space interaction has no action");
            var nearbyNpc = new WorldTarget("npc", "near", "Nearby guide", near);
            Require(ExperienceRules.ChooseInteraction(self, [nearbyNpc], data)?.Id == "near", "A nearby visible service is selected");
            Require(ExperienceRules.ChooseInteraction(self, [new WorldTarget("creature", "mob", "Mob", near)], data) is null, "Interact does not turn into an accidental attack");
            Require(ExperienceRules.ChooseInteraction(self, [new WorldTarget("exit", "blocked", "Door", blocked)], data) is null, "Blocked interactions are excluded");
            var weapon = self.Inventory.First(x => data.Item(x.Template).Slot == "weapon");
            string before = System.Text.Json.JsonSerializer.Serialize(self, Wire.Json);
            Require(ExperienceRules.EquipmentProblem(self, weapon, data) == "", "Usable equipment gets an available action");
            Require(ExperienceRules.EquipmentProblem(self, weapon, data, "helmet") != "", "Wrong paper-doll slot returns an explanation");
            Require(before == System.Text.Json.JsonSerializer.Serialize(self, Wire.Json), "Equipment previews do not mutate authoritative state");
            foreach (var cls in data.Classes)
            {
                var player = realm.CreateCharacter("class-" + cls.Id, "Tester " + cls.Name, cls.Id, new());
                var abilities = ExperienceRules.StarterAbilities(player, data);
                Require(abilities.Count > 0 && abilities[0].Class == cls.Id, "Starter hotbar prioritizes " + cls.Name + " identity");
            }

            int selected = 0, activated = 0, context = 0;
            var slot = new EquipmentItemSlot
            {
                Position = new Vector2(100, 100), Size = new Vector2(62, 62), Item = weapon,
                Clicked = () => selected++, Activated = () => activated++, ContextRequested = _ => context++
            };
            AddChild(slot); await Frame(); await Frame();
            Mouse(slot, MouseButton.Left, true);
            Require(selected == 0, "Pressing a slot does not rebuild it before drag detection");
            Mouse(slot, MouseButton.Left, false);
            Require(selected == 1, "Releasing a slot selects it once");
            Mouse(slot, MouseButton.Left, true, true);
            Mouse(slot, MouseButton.Left, false);
            Require(activated == 1 && selected == 1, "Native double-click invokes the equipment action once");
            Mouse(slot, MouseButton.Right, true);
            Mouse(slot, MouseButton.Right, false);
            Require(context == 1, "Native right-click requests the item menu");
            slot.QueueFree(); await Frame(); await Frame();
            Require(!GodotObject.IsInstanceValid(slot), "Item callbacks release their native node");

            GameRoot game;
            using (var scene = GD.Load<PackedScene>("res://Main.tscn")) game = scene.Instantiate<GameRoot>();
            AddChild(game); game.SetProcess(false);
            await Frame();
            Require(game.World is not null, "The real main scene initializes with experience controls");
            var snapshot = new Snapshot { Self = self, Time = 10 };
            game.World.Accept(new TransportPacket { Snapshot = snapshot });
            Field<Control>(game, "frontend").Hide();
            GetViewport().GuiReleaseFocus();
            for (int n = 0; n < 10; n++) Call(game, "Notify", "Move closer to the forge.", false);
            Require(Field<List<string>>(game, "history").Count == 0, "Repeated system feedback never enters player chat");
            Require(Field<Label>(game, "notice").Text == "Move closer to the forge.", "System feedback still has a visible notification");
            Require(InputMap.ActionGetEvents("basic_attack").OfType<InputEventKey>().Any(x => x.PhysicalKeycode == Key.Space), "The native input map includes Space attack");
            Call(game, "SetInitialHotbar");
            Require(data.Ability(Field<string[]>(game, "hotbar")[0]).Class == self.Class, "The first live hotbar slot uses the player's class");
            Call(game, "OpenPage", "Inventory");
            await Frame(); await Frame();
            var action = game.FindChildren("PrimaryEquipmentAction", "Button", true, false).Cast<Button>().Single();
            Require(action.IsVisibleInTree() && action.GetGlobalRect().Intersection(GetViewport().GetVisibleRect()).Size.Y >= 40,
                "The primary equipment action is visible inside the viewport");
            Require(action.GetParent().Name == "EquipmentActionBar", "Equip remains outside the statistics scroller");
            Call(game, "OpenPage", "Character"); await Frame(); await Frame();
            Require(game.FindChildren("Equipment_weapon", "Control", true, false).Count == 1, "The equipment page exposes the weapon drop slot");
            Require(game.FindChildren("*", "EquipmentItemSlot", true, false).Count >= self.Inventory.Count,
                "Equipment and backpack controls coexist for dragging");
            Call(game, "ClosePage");
            game.QueueFree(); await Frame(); await Frame();
            Require(!GodotObject.IsInstanceValid(game), "Experience UI releases the complete native scene");
            GD.Print($"PLAYER_EXPERIENCE_CONTRACT: {checks} checks passed. Offline native fixtures; not a full graphical playthrough.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("PLAYER_EXPERIENCE_CONTRACT: " + error);
            GetTree().Quit(1);
        }
    }
}
