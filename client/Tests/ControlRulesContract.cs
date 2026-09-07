using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Bounded rule fixtures and native release/layout checks, not normal progression.</summary>
public partial class ControlRulesContract : Node
{
    private int checks;
    private void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS CONTROL: " + message);
    }
    private static FieldInfo Member(string name) => typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!;
    private static T Field<T>(GameRoot game, string name) => (T)Member(name).GetValue(game)!;
    private static object? Call(GameRoot game, string method, params object?[] args)
        => typeof(GameRoot).GetMethod(method, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private bool Contained(Control control)
    {
        var bounds = GetViewport().GetVisibleRect(); var rect = control.GetGlobalRect();
        return control.IsVisibleInTree() && rect.Size.X > 0 && rect.Size.Y > 0
            && rect.Position.X >= bounds.Position.X && rect.Position.Y >= bounds.Position.Y
            && rect.End.X <= bounds.End.X + 1 && rect.End.Y <= bounds.End.Y + 1;
    }

    public override async void _Ready()
    {
        GameRoot? game = null;
        try
        {
            var data = PixelAssets.LoadCatalog(); var realm = new RealmEngine(data);
            var self = realm.CreateCharacter("control-fixture", "Control Fixture", "vanguard", new());
            var weapon = self.Inventory.Single(x => self.Equipment.GetValueOrDefault("weapon") == x.Id);
            Require(ExperienceRules.AttackProblem(self, data, 10) == "", "The valid starter attack is available");
            self.Stamina = 2;
            Require(ExperienceRules.AttackProblem(self, data, 10).Contains("stamina"), "Low stamina prevents repeated rejected attacks");
            self.Stamina = 100;
            weapon.Durability = 0;
            Require(ExperienceRules.AttackProblem(self, data, 10).Contains("repair"), "A broken weapon reports repair instead of retrying");
            weapon.Durability = 100;
            self.Statuses.Add(new StatusEffect { Kind = "stun", Until = 11 });
            Require(ExperienceRules.AttackProblem(self, data, 10).Contains("stunned"), "An active stun pauses the attack request");
            Require(ExperienceRules.AttackProblem(self, data, 12) == "", "An expired stun does not block attacks");
            self.Statuses.Clear();
            var bare = Wire.Copy(self); bare.Equipment.Remove("weapon");
            Require(ExperienceRules.WeaponRange(bare, data) == 1.6, "Unarmed client range matches the server");
            Require(Math.Abs(ExperienceRules.AttackInterval(bare, data) - Math.Max(.25, .8 / CombatMath.Stats(bare, data).AttackSpeed)) < .00001,
                "Unarmed cadence uses the server formula");
            var gate = new AttackRequestGate(); int requests = 0;
            for (int i = 0; i < 600; i++) if (gate.TryTake(i / 120.0, 10, 0, true, 1.2)) requests++;
            Require(requests == 5, "A stale snapshot cannot turn a 1.2-second weapon into per-frame requests");
            Require(!gate.TryTake(9, 10, 11, true, 1.2), "Local elapsed time cannot bypass server cooldown");
            Require(!gate.TryTake(9, 12, 11, false, 1.2), "Disabled controls do not consume the request gate");
            Require(gate.TryTake(9, 12, 11, true, 1.2), "A later valid request remains possible");
            Require(!gate.TryTake(9.01, 12, 0, true, 1.2), "Release and re-press cannot reset attack cadence");
            Require(!gate.TryTake(20, 20, 0, true, double.NaN), "Invalid cadence is rejected");
            var interactions = new AttackRequestGate(); requests = 0;
            for (int i = 0; i < 100; i++) if (interactions.TryTake(1, 10, 0, true, .4)) requests++;
            Require(requests == 1, "An interaction burst can send only one request");

            string species = data.Mobs.First(x => x.Ai is not "passive" and not "fleeing").Id;
            Creature Target(string id, double x, double y) => new() { Id = id, Template = species, Health = 10, Zone = self.Zone, Position = self.Position.Add(new Point(x, y)) };
            self.Facing = new Point(1, 0);
            var front = Target("front", 1, 0); var back = Target("back", -1, 0);
            Require(ExperienceRules.ChooseTarget(self, [back, front], data, "", 2)?.Id == "front", "Facing breaks equal-distance automatic target choices");
            Require(ExperienceRules.ChooseTarget(self, [front, back], data, "back", 2)?.Id == "back", "A valid explicit target keeps priority");
            Require(ExperienceRules.CycleTarget(self, [front, back], data, "back")?.Id == "front", "Tab advances through the stable target order");
            Require(ExperienceRules.CycleTarget(self, [front, back], data, "front")?.Id == "back", "Tab wraps through the same target order");
            back.Health = 0;
            Require(ExperienceRules.CycleTarget(self, [front, back], data, "front")?.Id == "front", "Tab excludes dead creatures");
            front.Owner = self.Id;
            Require(ExperienceRules.CycleTarget(self, [front, back], data, "") is null, "Tab excludes owned companions");
            front.Owner = "";
            Require(!ExperienceRules.CanTarget(self, front, data, double.NaN), "Invalid targeting distance fails closed");
            double reach = ExperienceRules.WeaponRange(self, data);
            var nearby = Target("approach", reach + .75, 0);
            var path = ExperienceRules.ApproachPath(self, nearby, data);
            Require(path.Count > 0, "A selected nearby enemy has a short approach path");
            double length = 0; var last = self.Position;
            foreach (var point in path) { length += last.Distance(point); last = point; }
            Require(length <= 2.5 && last.Distance(nearby.Position) <= reach, "Approach stops within range and within its path budget");
            Require(ExperienceRules.ApproachPath(self, Target("far", reach + 2, 0), data).Count == 0, "Distant selection never starts long-distance pursuit");
            nearby.Owner = self.Id;
            Require(ExperienceRules.ApproachPath(self, nearby, data).Count == 0, "Approach cannot pursue an owned companion");
            var closeNpc = new WorldTarget("npc", "close", "Guide", self.Position.Add(new Point(.6, 0)));
            var farDoor = new WorldTarget("exit", "far", "Inn", self.Position.Add(new Point(1.8, 0)));
            Require(ExperienceRules.ChooseInteraction(self, [farDoor, closeNpc], data)?.Id == "close", "Interaction uses distance rather than draw order");

            var foreign = data.Abilities.First(x => x.Class != "" && x.Class != self.Class && x.Requirement == 1);
            int requirement = ExperienceRules.AbilityRequirement(self, foreign);
            Require(requirement == foreign.Requirement + 20, "Cross-class abilities retain the server's extra skill requirement");
            var trained = Wire.Copy(self); trained.SkillXp[foreign.Skill] = Progression.Threshold(requirement);
            trained.Mana = 1000; trained.Stamina = 1000;
            Require(ExperienceRules.StarterAbilities(trained, data).Any(x => x.Id == foreign.Id), "A trained cross-class ability can remain assigned");
            Require(ExperienceRules.AbilityProblem(trained, foreign, data, 10) == "", "Client validation does not invent a class ban");
            trained.Cooldowns["ability:" + foreign.Id] = 12;
            Require(ExperienceRules.AbilityProblem(trained, foreign, data, 10).Contains("cooldown"), "Ability cooldown produces a local explanation");

            using (var scene = GD.Load<PackedScene>("res://Main.tscn")) game = scene.Instantiate<GameRoot>();
            AddChild(game); game.SetProcess(false); await Frame();
            game.World.Accept(new TransportPacket { Snapshot = new Snapshot { Self = self, Time = 10 } });
            Field<Control>(game, "frontend").Hide();
            Call(game, "UpdateHud"); Call(game, "SetInitialHotbar");
            var input = Field<LineEdit>(game, "chatInput"); input.GrabFocus(); await Frame();
            Member("attackKeyHeld").SetValue(game, true);
            Member("combatApproach").SetValue(game, true);
            Field<List<Point>>(game, "route").Add(self.Position.Add(new Point(1, 0)));
            using (var release = new InputEventKey { PhysicalKeycode = Key.Space, Keycode = Key.Space, Pressed = false })
                Input.ParseInputEvent(release);
            await Frame();
            Require(!Field<bool>(game, "attackKeyHeld"), "Native release clears held attack while chat owns focus");
            Require(Field<List<Point>>(game, "route").Count == 0, "Native release cancels the combat approach route");
            Member("attackKeyHeld").SetValue(game, true);
            game.Notification(checked((int)NotificationApplicationFocusOut)); await Frame();
            Require(!Field<bool>(game, "attackKeyHeld"), "Native application-focus notification cancels held attack");
            game.Notification(checked((int)NotificationApplicationFocusIn)); GetViewport().GuiReleaseFocus();
            foreach (var size in new[] { new Vector2I(1280, 720), new Vector2I(1920, 1080) })
            {
                GetWindow().Size = size; GetWindow().ContentScaleSize = size;
                Call(game, "OpenPage", "Inventory"); await Frame(); await Frame(); await Frame();
                var action = game.FindChildren("PrimaryEquipmentAction", "Button", true, false).Cast<Button>().Single();
                Require(Contained(action) && action.Size.Y >= 40, "Equipment action fits the " + size + " viewport");
                Call(game, "ClosePage"); await Frame(); await Frame();
                Require(Field<Button[]>(game, "hotbarButtons").All(Contained), "All ten hotbar buttons fit the " + size + " viewport");
            }
            game.QueueFree(); await Frame(); await Frame();
            Require(!GodotObject.IsInstanceValid(game), "The real scene releases after repeated layouts");
            GD.Print($"CONTROL_RULES_CONTRACT: {checks} checks passed. Rule fixtures and native input/layout checks only.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CONTROL_RULES_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game)) { game.QueueFree(); await Frame(); await Frame(); }
            GetTree().Quit(1);
        }
    }
}
