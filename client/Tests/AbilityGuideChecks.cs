using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>Native input and lifetime checks for the actual ability panel.</summary>
internal static class AbilityGuideChecks
{
    public static async Task Run(Node host, GameRoot game, Catalog data, Character self, Action<bool, string> check)
    {
        object? Call(string method, params object?[] args) => typeof(GameRoot)
            .GetMethod(method, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
        T Find<T>(Node root, string name, string type) where T : Node
            => root.FindChildren(name, type, true, false).OfType<T>().Single();
        async Task Frame() => await host.ToSignal(host.GetTree(), SceneTree.SignalName.ProcessFrame);
        bool Fits(Control control)
        {
            var rect = control.GetGlobalRect(); var bounds = host.GetViewport().GetVisibleRect();
            return control.IsVisibleInTree() && rect.Size.X > 0 && rect.Size.Y > 0
                && rect.Position.X >= -1 && rect.Position.Y >= -1
                && rect.End.X <= bounds.End.X + 1 && rect.End.Y <= bounds.End.Y + 1;
        }
        async Task Click(Control control)
        {
            check(Fits(control), "Ability action is visible: " + control.Name);
            var at = control.GetGlobalRect().GetCenter();
            using (var press = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, ButtonMask = MouseButtonMask.Left, Pressed = true })
                host.GetViewport().PushInput(press, true);
            await Frame();
            using (var release = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, Pressed = false })
                host.GetViewport().PushInput(release, true);
            await Frame(); await Frame();
        }
        async Task Type(LineEdit search, string value)
        {
            search.GrabFocus(); search.SelectAll();
            using (var press = new InputEventKey { Keycode = Key.Backspace, PhysicalKeycode = Key.Backspace, Pressed = true }) host.GetViewport().PushInput(press, true);
            using (var release = new InputEventKey { Keycode = Key.Backspace, PhysicalKeycode = Key.Backspace }) host.GetViewport().PushInput(release, true);
            await Frame();
            foreach (char c in value)
            {
                var key = c == ' ' ? Key.Space : (Key)char.ToUpperInvariant(c);
                using (var press = new InputEventKey { Keycode = key, PhysicalKeycode = key, Unicode = c, Pressed = true }) host.GetViewport().PushInput(press, true);
                using (var release = new InputEventKey { Keycode = key, PhysicalKeycode = key }) host.GetViewport().PushInput(release, true);
                await Frame();
            }
            await Frame(); await Frame();
            check(search.Text == value, "Native keyboard text reaches the ability search");
        }
        foreach (var size in new[] { new Vector2I(1280,720), new Vector2I(1920,1080) })
        {
            host.GetWindow().Size = size; host.GetWindow().ContentScaleSize = size;
            Call("OpenPage", "Abilities"); await Frame(); await Frame(); await Frame();
            var guide = Find<AbilityGuidePanel>(game, "AbilityGuide", "VBoxContainer");
            var search = Find<LineEdit>(guide, "AbilitySearch", "LineEdit");
            var assign = Find<Button>(guide, "AssignAbility", "Button");
            check(guide.VisibleAbilityIds.Count > 1, "Starter ability choices are available at " + size);
            check(guide.VisibleAbilityIds.All(id => Progression.Level(self, data.Ability(id).Skill) >= ExperienceRules.AbilityRequirement(self, data.Ability(id))),
                "The initial browser hides locked abilities without changing the catalog");
            check(guide.VisibleAbilityIds.All(id => data.Ability(id).Class == "" || data.Ability(id).Class == self.Class), "Initial choices match the current class or shared skills");
            string first = guide.VisibleAbilityIds[0], second = guide.VisibleAbilityIds[1];
            var button = Find<Button>(guide, "AbilityChoice_" + second, "Button");
            ulong identity = button.GetInstanceId();
            await Click(button);
            check(guide.SelectedAbility == second, "A native pointer click selects ability details");
            check(GodotObject.IsInstanceValid(button) && button.GetInstanceId() == identity, "Ability selection does not dispose the pressed control");
            double mana = self.Mana, stamina = self.Stamina;
            self.Mana = 0; self.Stamina = 0; guide.RefreshSnapshot(); await Frame();
            check(Find<Button>(guide, "AbilityChoice_" + second, "Button").GetInstanceId() == identity, "Resource changes preserve ability list nodes and scroll state");
            check(!assign.Disabled, "Learning eligibility, not current mana, controls hotbar assignment");
            self.Mana = mana; self.Stamina = stamina; guide.RefreshSnapshot();
            await Click(assign);
            var hotbar = (string[])typeof(GameRoot).GetField("hotbar", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
            check(hotbar[0] == second, "The actual GameRoot callback assigns the selected ability to key 1");
            check(Find<Label>(guide, "AbilityAssignedSlots", "Label").Text.Contains("1"), "Assigned hotbar keys are shown in the inspector");
            ulong selectedStyle = button.GetThemeStylebox("normal").GetInstanceId();
            for (int repeat = 0; repeat < 12; repeat++) guide.RefreshSnapshot();
            check(button.GetThemeStylebox("normal").GetInstanceId() == selectedStyle, "Repeated snapshots reuse the selected ability style resource");
            var parent = guide.GetParent(); int childIndex = guide.GetIndex();
            for (int repeat = 0; repeat < 2; repeat++)
            {
                parent.RemoveChild(guide); await Frame();
                parent.AddChild(guide); parent.MoveChild(guide, childIndex); await Frame(); await Frame();
                await Type(search, "Shield");
                check(guide.VisibleAbilityIds.Contains("vanguard_shield_breaker"), "Reattached ability search retains its native signal subscription");
                await Type(search, "");
            }
            await Type(search, "Shield");
            check(guide.VisibleAbilityIds.Contains("vanguard_shield_breaker"), "Native search finds the starter class strike");
            check(Fits(assign) && Fits(search), "The search and pinned assignment action fit " + size);
            await Type(search, "NoSuchAbilityFixture");
            check(guide.VisibleAbilityIds.Count == 0 && guide.SelectedAbility == "" && assign.Disabled, "Empty search clears stale actions and selection");
            await Type(search, "");
            var scope = Find<OptionButton>(guide, "AbilityScope", "OptionButton");
            var levels = Find<OptionButton>(guide, "AbilityAvailability", "OptionButton");
            scope.Select(3); scope.EmitSignal(OptionButton.SignalName.ItemSelected, 3L);
            levels.Select(2); levels.EmitSignal(OptionButton.SignalName.ItemSelected, 2L);
            await Frame(); await Frame();
            check(guide.VisibleAbilityIds.Count > 0, "The locked filter exposes future learning choices");
            check(guide.VisibleAbilityIds.All(id => Progression.Level(self, data.Ability(id).Skill) < ExperienceRules.AbilityRequirement(self, data.Ability(id))), "Locked choices use authoritative cross-class requirements");
            var foreign = guide.VisibleAbilityIds.Select(data.Ability).First(a => a.Class != "" && a.Class != self.Class);
            guide.SelectAbility(foreign.Id);
            check(assign.Disabled && !guide.TryAssignSelected(), "A locked foreign-class ability cannot be assigned through a stale action");
            check(Find<Label>(guide, "AbilityRequirement", "Label").Text.Contains("20 skill levels"), "Cross-class learning cost is explained");
            scope.Select(1); scope.EmitSignal(OptionButton.SignalName.ItemSelected, 1L);
            levels.Select(0); levels.EmitSignal(OptionButton.SignalName.ItemSelected, 0L);
            await Frame(); await Frame();
            string weaponSkill = data.Item(Items.Owned(self, self.Equipment["weapon"]).Template).Skill;
            check(guide.VisibleAbilityIds.Count > 0 && guide.VisibleAbilityIds.All(id => data.Ability(id).Skill == weaponSkill), "Equipped-weapon filtering matches the actual item skill");
            Call("ClosePage"); await Frame(); await Frame();
            check(!GodotObject.IsInstanceValid(guide), "The native ability panel releases after repeated input and filtering");
        }
        foreach (var ability in data.Abilities)
            check(!AbilityGuideText.Effect(ability).Contains("implementation review"), "Implemented ability behavior has an explanation: " + ability.Id);
    }
}
