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
    private async Task ClickGuideControl(Control control)
    {
        var at = control.GetGlobalRect().GetCenter();
        Require(Contained(control), "The skill control is visible and reachable: " + control.Name);
        using (var press = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, ButtonMask = MouseButtonMask.Left, Pressed = true })
            GetViewport().PushInput(press, true);
        await Frame();
        using (var release = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, Pressed = false })
            GetViewport().PushInput(release, true);
        await Frame(); await Frame();
    }

    private async Task TypeGuideSearch(SkillGuidePanel guide, string text)
    {
        var search = guide.SearchBox;
        search.GrabFocus(); search.SelectAll();
        using (var press = new InputEventKey { Keycode = Key.Backspace, PhysicalKeycode = Key.Backspace, Pressed = true })
            GetViewport().PushInput(press, true);
        using (var release = new InputEventKey { Keycode = Key.Backspace, PhysicalKeycode = Key.Backspace, Pressed = false })
            GetViewport().PushInput(release, true);
        await Frame();
        foreach (char character in text)
        {
            var key = (Key)char.ToUpperInvariant(character);
            using (var press = new InputEventKey { Keycode = key, PhysicalKeycode = key, Unicode = character, Pressed = true })
                GetViewport().PushInput(press, true);
            using (var release = new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = false })
                GetViewport().PushInput(release, true);
            await Frame();
        }
        await Frame(); await Frame();
        Require(search.Text == text, "Native keyboard input reaches the skill search");
    }

    private async Task VerifySkillGuide(GameRoot game, Catalog data, Character self)
    {
        var actor = Wire.Copy(self); actor.Position = data.Zone(actor.Zone).Spawn;
        double reach = ExperienceRules.WeaponRange(actor, data);
        var approaching = new Creature { Id = "approach-fixture", Zone = actor.Zone, Template = "field_rat", Health = 100, Position = new Point(actor.Position.X + reach + .5, actor.Position.Y) };
        var approach = ExperienceRules.ApproachPath(actor, approaching, data);
        Require(approach.Count > 0, "A nearby moving target has a bounded approach route");
        Require(approach[^1].Distance(approaching.Position) + .32 < reach, "The final waypoint includes movement tolerance inside weapon range");
        Require(ExperienceRules.ApproachPath(actor, approaching, data, .1).Count == 0, "An exhausted total approach budget does not create another path");
        Require(ExperienceRules.ApproachPath(actor, approaching, data, double.NaN).Count == 0, "Nonfinite approach budgets fail closed");
        Require(data.Skills.All(skill => SkillGuideRules.Categories.Contains(SkillGuideRules.Group(skill))), "Every skill has one of the six player-facing categories");
        Require(SkillGuideRules.Categories.Sum(category => SkillGuideRules.Filter(data, category, "").Count) == data.Skills.Count, "The category filters cover every skill exactly once");
        Require(SkillGuideRules.Group(data.Skill("shield_mastery")) == "Defense", "Shield training appears under Defense");
        Require(SkillGuideRules.Filter(data, "All", "  mInInG  ").Any(skill => skill.Id == "mining"), "Skill search ignores case and surrounding spaces");
        foreach (var skill in data.Skills)
        {
            var unlocks = SkillGuideRules.FutureUnlocks(data, self, skill.Id);
            Require(unlocks.All(unlock => unlock.Level > Progression.Level(self, skill.Id) && unlock.Level <= 100), "Future unlocks use real later requirements for " + skill.Id);
        }
        foreach (var size in new[] { new Vector2I(1280, 720), new Vector2I(1920, 1080) })
        {
            GetWindow().Size = size; GetWindow().ContentScaleSize = size;
            Call(game, "OpenPage", "Skills");
            await Frame(); await Frame(); await Frame();
            var guide = game.FindChildren("SkillGuide", "VBoxContainer", true, false).OfType<SkillGuidePanel>().Single();
            Require(guide.VisibleSkillCount == data.Skills.Count, "The skill browser initially exposes the full catalog at " + size);
            var gathering = guide.FindChildren("SkillCategory_Gathering", "Button", true, false).Cast<Button>().Single();
            await ClickGuideControl(gathering);
            Require(guide.ActiveCategory == "Gathering" && guide.VisibleSkillCount == SkillGuideRules.Filter(data, "Gathering", "").Count, "A native category click filters the skill list");
            await TypeGuideSearch(guide, "Mining");
            Require(guide.VisibleSkillCount == 1 && guide.SelectedSkillId == "mining", "The search signal selects the matching skill");
            var training = guide.FindChildren("SkillTrainingAction", "Label", true, false).Cast<Label>().Single();
            Require(training.Text == data.Skill("mining").Action, "The detail panel states the actual catalog training action");
            var item = guide.FindChildren("SkillEntry_mining", "Button", true, false).Cast<Button>().Single();
            ulong identity = item.GetInstanceId();
            long original = self.SkillXp.GetValueOrDefault("mining");
            self.SkillXp["mining"] = original + 1; guide.RefreshSnapshot(); await Frame();
            Require(guide.FindChildren("SkillEntry_mining", "Button", true, false).Cast<Button>().Single().GetInstanceId() == identity, "A live XP refresh preserves the navigation node and scroll state");
            self.SkillXp["mining"] = original; guide.RefreshSnapshot();
            await TypeGuideSearch(guide, "NoSuchSkillFixture");
            Require(guide.VisibleSkillCount == 0 && guide.SelectedSkillId == "", "An empty search clears stale skill details");
            await TypeGuideSearch(guide, "");
            Require(guide.VisibleSkillCount == SkillGuideRules.Filter(data, "Gathering", "").Count, "Clearing search restores the active category");
            Require(Contained(guide.SearchBox), "The skill search stays in the viewport at " + size);
            Call(game, "ClosePage"); await Frame(); await Frame();
            Require(!GodotObject.IsInstanceValid(guide), "Closing the skill browser releases the native panel");
        }
    }

    public override async void _Ready()
    {
        GameRoot? game = null;
        try
        {
            GetWindow().Size = new Vector2I(1280, 720);
            await Frame(); await Frame();
            Require(GetViewport().GetVisibleRect().Size.IsEqualApprox(new Vector2(1280, 720)), "The native control fixture uses supported physical window dimensions");
            var data = PixelAssets.LoadCatalog(); var realm = new RealmEngine(data);
            var self = realm.CreateCharacter("control-fixture", "Control Fixture", "vanguard", new());
            var weapon = self.Inventory.Single(x => self.Equipment.GetValueOrDefault("weapon") == x.Id);
            Require(ExperienceRules.AttackProblem(self, data, 10) == "", "The valid starter attack is available");
            self.Stamina = 2;
            Require(ExperienceRules.AttackProblem(self, data, 10).Contains("stamina"), "Low stamina prevents repeated rejected attacks");
            self.Stamina = 100; weapon.Durability = 0;
            Require(ExperienceRules.AttackProblem(self, data, 10).Contains("repair"), "A broken weapon reports repair instead of retrying");
            weapon.Durability = 100; self.Statuses.Add(new StatusEffect { Kind = "stun", Until = 11 });
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

            var carcass = new WorldTarget("node", "a-carcass", "Carcass", self.Position.Add(new Point(1, 0)));
            var pickup = new WorldTarget("loot", "z-pickup", "Supplies", carcass.Position);
            Require(ExperienceRules.ChooseInteraction(self, [carcass, pickup], data)?.Id == pickup.Id, "Overlapping loot has priority over a carcass regardless of its identifier");
            Require(ExperienceRules.ChooseInteraction(self, [pickup, closeNpc], data)?.Id == closeNpc.Id, "Loot priority does not override a nearer NPC");
            var pile = new LootPile { Zone = self.Zone, Owner = "foreign", PublicAt = 100, Party = "" };
            Require(!ExperienceRules.LootAvailable(self, pile, 10), "Private foreign loot does not promise a pickup action");
            pile.Owner = self.Id;
            Require(ExperienceRules.LootAvailable(self, pile, 10), "Owned loot remains eligible");
            pile.Owner = "foreign";
            Require(ExperienceRules.LootAvailable(self, pile, 100), "Loot becomes eligible at its authoritative public time");
            Require(!ExperienceRules.LootAvailable(self, pile, double.NaN), "Invalid loot time fails closed");
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
            string starterAbility = Field<string[]>(game, "hotbar")[0];
            self.Cooldowns["ability:" + starterAbility] = 12;
            Call(game, "UpdateHud");
            var firstSlot = (AbilitySlot)Field<Button[]>(game, "hotbarButtons")[0];
            Require(firstSlot.CooldownSeconds == 2 && firstSlot.BlockReason.Contains("cooldown"), "The HUD reads the server ability cooldown key");
            self.Cooldowns.Clear();
            double savedMana = self.Mana, savedStamina = self.Stamina;
            self.Mana = 0; self.Stamina = 0; Call(game, "UpdateHud");
            Require(firstSlot.BlockReason.Contains("mana") || firstSlot.BlockReason.Contains("stamina"), "The HUD explains insufficient ability resources");
            self.Mana = savedMana; self.Stamina = savedStamina; Call(game, "UpdateHud");
            Require(firstSlot.KeyLabel == "1" && firstSlot.TooltipText.Contains("Range") && firstSlot.TooltipText.Contains("Requires"), "The first ability shows its key, range, and requirement");
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
            await VerifySkillGuide(game, data, self);
            await AbilityGuideChecks.Run(this, game, data, self, Require);
            await PresentationChecks.Run(this, game, Require);
            await EquipmentGuideChecks.Run(this,game,data,self,Require);
            await CraftingGuideChecks.Run(this,game,data,Require);
            await EquipmentMaintenanceUiChecks.Run(this,game,Require);
            await JourneyUiChecks.Run(this,game,Require);
            await HuntingGuideChecks.Run(this,game,Require);
            await NativePixelChecks.Run(this,game,Require);
            await InventoryRefreshChecks.Run(this,game,Require);
            await ChallengeHudChecks.Run(this,game,Require);
            await NativeTestLifetime.ReleaseSceneAsync(this, game);
            Require(!GodotObject.IsInstanceValid(game), "The real scene releases after repeated layouts");
            GD.Print($"CONTROL_RULES_CONTRACT: {checks} checks passed. Rule fixtures and native input/layout checks only.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CONTROL_RULES_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this, game);
            GetTree().Quit(1);
        }
    }
}
