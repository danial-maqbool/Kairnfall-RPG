using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private bool attackKeyHeld;
    private bool applicationFocused = true;
    private bool combatApproach, approachUsed;
    private double approachDeadline, nextApproachPlan, approachTravelled;
    private Point lastApproachPosition;
    private string hotbarCharacter = "";
    private readonly AttackRequestGate basicAttackGate = new();
    private readonly AttackRequestGate interactionGate = new();
    private Label interactionHint = null!;
    private Label progressionHint = null!;
    private VBoxContainer pickupFeed = null!;
    private Button interactionButton = null!;
    private Button basicAttackButton = null!;
    private double contextClock, progressionUntil, nextProgressionNote;
    private string lastNoticeText = "";
    private double lastNoticeAt = -10;
    private readonly List<PickupNote> pickupNotes = [];
    private readonly Dictionary<string, long> pendingSkillGains = [];
    private readonly Dictionary<string, int> pendingSkillLevels = [];
    private sealed record PickupNote(string Template, Rarity Rarity, int Quantity, double Until);

    private bool GameplayInputAllowed => !closing && awaitingBinding == "" && ExperienceRules.AllowsWorldInput(
        Online, Typing, gameWindow is not null || frontend.Visible, applicationFocused, Snapshot?.Self.Health > 0);

    public override void _Input(InputEvent @event)
    {
        // GUI focus can consume a release after the press reached the world.
        if (InputMap.HasAction("basic_attack") && @event.IsActionReleased("basic_attack")) StopCombatInput();
    }

    private void CancelCombatApproach()
    {
        if (combatApproach) route.Clear();
        combatApproach = false;
    }
    private void StopCombatInput()
    {
        attackKeyHeld = false;
        approachUsed = false;
        approachTravelled = 0; nextApproachPlan = 0;
        CancelCombatApproach();
    }

    private void BeginBasicAttack(bool held)
    {
        if (!GameplayInputAllowed) return;
        StopCombatInput();
        attackKeyHeld = held;
        var snapshot = Snapshot!;
        var target = ExperienceRules.ChooseTarget(snapshot.Self, snapshot.Creatures, Data,
            selectedTargetKind == "creature" ? selectedTarget : "", ExperienceRules.WeaponRange(snapshot.Self, Data));
        if (target is not null)
        {
            selectedTargetKind = "creature"; selectedTarget = target.Id; World.TargetId = target.Id;
        }
        string problem = ExperienceRules.AttackProblem(snapshot.Self, Data, snapshot.Time);
        if (problem != "") { Notify(problem); return; }
        if (target is null && selectedTargetKind != "creature") Notify("No hostile creature is within weapon range.");
        TryBasicAttack();
    }

    private void TryBasicAttack()
    {
        if (!GameplayInputAllowed || actionBusy) return;
        var snapshot = Snapshot!;
        double now = Time.GetTicksMsec() / 1000.0;
        if (approachUsed)
        {
            approachTravelled += lastApproachPosition.Distance(snapshot.Self.Position);
            lastApproachPosition = snapshot.Self.Position;
        }
        if (combatApproach && (now >= approachDeadline || approachTravelled >= 2.5)) { StopCombatInput(); return; }
        if (ExperienceRules.AttackProblem(snapshot.Self, Data, snapshot.Time) != "")
        {
            CancelCombatApproach(); return;
        }
        var target = selectedTargetKind == "creature" ? snapshot.Creatures.FirstOrDefault(x => x.Id == selectedTarget) : null;
        if (selectedTargetKind == "creature" && (target is null || target.Health <= 0 || target.Owner != "" || target.Zone != snapshot.Self.Zone))
        {
            StopCombatInput(); return;
        }
        target ??= ExperienceRules.ChooseTarget(snapshot.Self, snapshot.Creatures, Data, "", ExperienceRules.WeaponRange(snapshot.Self, Data));
        if (target is null) return;
        selectedTargetKind = "creature"; selectedTarget = target.Id; World.TargetId = target.Id;
        bool inRange = ExperienceRules.CanTarget(snapshot.Self, target, Data, ExperienceRules.WeaponRange(snapshot.Self, Data), true);
        if (!inRange)
        {
            if (Input.GetVector("move_left", "move_right", "move_up", "move_down").LengthSquared() > .01f)
            {
                CancelCombatApproach(); return;
            }
            if (!attackKeyHeld || !settings.GetValue("controls", "approach_attack", true).AsBool())
            {
                CancelCombatApproach(); return;
            }
            if (!approachUsed)
            {
                approachUsed = true; approachDeadline = now + 1.5;
                lastApproachPosition = snapshot.Self.Position; approachTravelled = 0;
            }
            // Replanning never resets the time or total travel budget of this key press.
            if (now >= approachDeadline || approachTravelled >= 2.5)
            {
                StopCombatInput(); return;
            }
            if (now >= nextApproachPlan)
            {
                nextApproachPlan = now + .12;
                var path = ExperienceRules.ApproachPath(snapshot.Self, target, Data, 2.5 - approachTravelled);
                if (path.Count == 0) { CancelCombatApproach(); return; }
                pendingInteraction = null; route.Clear(); route.AddRange(path);
                combatApproach = true;
            }
            return;
        }
        CancelCombatApproach();
        if (basicAttackGate.TryTake(now, snapshot.Time, snapshot.Self.Cooldowns.GetValueOrDefault("attack"), true,
            ExperienceRules.AttackInterval(snapshot.Self, Data)))
            _ = SendAsync(new GameCommand { Kind = "attack", Target = target.Id }, true);
    }

    private WorldTarget? ContextTarget()
    {
        if (Snapshot is not { } snapshot) return null;
        bool Available(WorldTarget target)
        {
            if (target.Kind == "loot") return World.Loot.Any(x => x.Id == target.Id && ExperienceRules.LootAvailable(snapshot.Self, x, snapshot.Time));
            if (target.Kind == "node") return snapshot.Nodes.Any(x => x.Id == target.Id && x.ReadyAt <= snapshot.Time);
            if (target.Kind == "chest") return snapshot.Chests.Any(x => x.Id == target.Id && x.ReadyAt <= snapshot.Time);
            return true;
        }
        return ExperienceRules.ChooseInteraction(snapshot.Self, World.Targets.Where(Available), Data);
    }

    private string ContextVerb(WorldTarget target)
    {
        if (target.Kind != "node") return ExperienceRules.InteractionVerb(target.Kind);
        string template = Snapshot?.Nodes.FirstOrDefault(x => x.Id == target.Id)?.Template ?? "";
        if (template.StartsWith("structure_", StringComparison.Ordinal)) return "Use";
        if (template.EndsWith("_vein", StringComparison.Ordinal)) return "Mine";
        if (template.EndsWith("_tree", StringComparison.Ordinal)) return "Chop";
        if (template.EndsWith("_pool", StringComparison.Ordinal)) return "Fish at";
        return "Gather";
    }

    private void InteractWithContext()
    {
        if (!GameplayInputAllowed || actionBusy || ContextTarget() is not { } target) return;
        double now = Time.GetTicksMsec() / 1000.0;
        if (interactionGate.TryTake(now, Snapshot!.Time, 0, true, .4)) Activate(target);
        // Empty-space input sends no request and adds nothing to chat.
    }

    private void CycleHostileTarget()
    {
        if (!GameplayInputAllowed) return;
        var snapshot = Snapshot!;
        if (ExperienceRules.CycleTarget(snapshot.Self, snapshot.Creatures, Data, selectedTarget) is { } target)
            SelectTarget("creature", target.Id);
    }

    private void BuildExperienceHud()
    {
        var controls = new HBoxContainer
        {
            Name = "CombatControls", AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = 1, AnchorBottom = 1,
            OffsetLeft = -245, OffsetRight = 245, OffsetTop = -142, OffsetBottom = -101,
            MouseFilter = MouseFilterEnum.Ignore
        };
        hud.AddChild(controls);
        basicAttackButton = Ui.Button("Attack [Space]", () => BeginBasicAttack(false));
        basicAttackButton.Name = "BasicAttack";
        basicAttackButton.FocusMode = FocusModeEnum.None;
        basicAttackButton.TooltipText = "Click to attack once. Hold Space to repeat. Click a creature to select it; double-click to attack once.";
        basicAttackButton.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        controls.AddChild(basicAttackButton);
        interactionButton = Ui.Button("Interact [E]", InteractWithContext);
        interactionButton.Name = "ContextAction";
        interactionButton.FocusMode = FocusModeEnum.None;
        interactionButton.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        controls.AddChild(interactionButton);
        interactionHint = Ui.Label("", 15, Ui.Gold, true);
        interactionHint.Name = "InteractionPrompt";
        interactionHint.AnchorLeft = interactionHint.AnchorRight = .5f;
        interactionHint.AnchorTop = interactionHint.AnchorBottom = 1;
        interactionHint.OffsetLeft = -285; interactionHint.OffsetRight = 285;
        interactionHint.OffsetTop = -182; interactionHint.OffsetBottom = -146;
        interactionHint.HorizontalAlignment = HorizontalAlignment.Center;
        interactionHint.AddThemeConstantOverride("outline_size", 4);
        interactionHint.AddThemeColorOverride("font_outline_color", Ui.Ink);
        hud.AddChild(interactionHint);
        progressionHint = Ui.Label("", 14, Ui.Success, true);
        progressionHint.Name = "ProgressionFeedback";
        progressionHint.AnchorLeft = progressionHint.AnchorRight = .5f;
        progressionHint.AnchorTop = progressionHint.AnchorBottom = 1;
        progressionHint.OffsetLeft = -285; progressionHint.OffsetRight = 285;
        progressionHint.OffsetTop = -213; progressionHint.OffsetBottom = -185;
        progressionHint.HorizontalAlignment = HorizontalAlignment.Center;
        progressionHint.AddThemeConstantOverride("outline_size", 4);
        progressionHint.AddThemeColorOverride("font_outline_color", Ui.Ink);
        hud.AddChild(progressionHint);
        notice.OffsetTop = -252; notice.OffsetBottom = -216;
        pickupFeed = new VBoxContainer
        {
            Name = "PickupFeed", AnchorLeft = 1, AnchorRight = 1,
            OffsetLeft = -276, OffsetRight = -18, OffsetTop = 266, MouseFilter = MouseFilterEnum.Ignore
        };
        hud.AddChild(pickupFeed);
        foreach (var button in hotbarButtons) button.FocusMode = FocusModeEnum.None;
    }

    private void TickExperience(double delta)
    {
        if (!GameplayInputAllowed) StopCombatInput();
        if (attackKeyHeld && !Input.IsActionPressed("basic_attack")) StopCombatInput();
        if (attackKeyHeld) TryBasicAttack();
        contextClock += delta;
        if (contextClock < .1 || interactionHint is null) return;
        contextClock = 0;
        double now = Time.GetTicksMsec() / 1000.0;
        var context = GameplayInputAllowed ? ContextTarget() : null;
        interactionButton.Disabled = context is null;
        basicAttackButton.Disabled = !GameplayInputAllowed;
        basicAttackButton.Text = "Attack [" + bindings["basic_attack"] + "]";
        interactionButton.Text = "Interact [" + bindings["interact"] + "]";
        interactionHint.Text = context is { } target
            ? "[" + bindings["interact"] + "] " + ContextVerb(target) + " " + target.Name
            : GameplayInputAllowed ? "Hold " + bindings["basic_attack"] + " to attack  ·  Tab selects a hostile  ·  1–0 uses abilities" : "";
        if (now >= nextProgressionNote && pendingSkillGains.Count > 0)
        {
            var keys = pendingSkillGains.Keys.OrderByDescending(x => pendingSkillLevels.ContainsKey(x)).Take(3).ToArray();
            progressionHint.Text = string.Join(" · ", keys.Select(x => pendingSkillLevels.TryGetValue(x, out int level)
                ? Data.Skill(x).Name + " reached Level " + level : "+" + pendingSkillGains[x] + " " + Data.Skill(x).Name + " XP"));
            foreach (var key in keys) { pendingSkillGains.Remove(key); pendingSkillLevels.Remove(key); }
            nextProgressionNote = now + 1.5; progressionUntil = now + 4;
        }
        if (now > progressionUntil) progressionHint.Text = "";
        if (pickupNotes.RemoveAll(x => now > x.Until) > 0) RenderPickupFeed();
    }

    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
    {
        if (previous is null || previous.Self.Id != current.Self.Id) return;
        var before = previous.Self.Inventory.GroupBy(x => (x.Template, x.Rarity)).ToDictionary(x => x.Key, x => x.Sum(y => y.Quantity));
        double now = Time.GetTicksMsec() / 1000.0;
        bool changed = false;
        foreach (var group in current.Self.Inventory.GroupBy(x => (x.Template, x.Rarity)))
        {
            int gained = group.Sum(x => x.Quantity) - before.GetValueOrDefault(group.Key);
            if (gained <= 0) continue;
            int index = pickupNotes.FindIndex(x => x.Template == group.Key.Template && x.Rarity == group.Key.Rarity && x.Until > now);
            if (index >= 0)
            {
                gained += pickupNotes[index].Quantity; pickupNotes.RemoveAt(index);
            }
            pickupNotes.Add(new PickupNote(group.Key.Template, group.Key.Rarity, gained, now + 6)); changed = true;
        }
        if (pickupNotes.Count > 20) pickupNotes.RemoveRange(0, pickupNotes.Count - 20);
        if (changed) RenderPickupFeed();
        foreach (var skill in Data.Skills)
        {
            long gained = current.Self.SkillXp.GetValueOrDefault(skill.Id) - previous.Self.SkillXp.GetValueOrDefault(skill.Id);
            if (gained <= 0) continue;
            pendingSkillGains[skill.Id] = pendingSkillGains.GetValueOrDefault(skill.Id) + gained;
            int level = Progression.Level(current.Self, skill.Id);
            if (level > Progression.Level(previous.Self, skill.Id)) pendingSkillLevels[skill.Id] = level;
        }
        int overall = Progression.PlayerLevel(current.Self);
        if (overall > Progression.PlayerLevel(previous.Self))
        {
            string key = "overall_" + current.Self.Id;
            bool explained = settings.GetValue("hints", key, false).AsBool();
            Notify("Overall Level " + overall + (explained ? "" : " — training any skill advances your overall level."));
            settings.SetValue("hints", key, true); settings.Save("user://settings.cfg");
        }
    }

    private void RenderPickupFeed()
    {
        if (pickupFeed is null) return;
        Ui.Clear(pickupFeed);
        foreach (var entry in pickupNotes.TakeLast(3))
        {
            var card = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
            card.AddThemeStyleboxOverride("panel", Ui.Box(Ui.Ink, Ui.RarityColor(entry.Rarity), 7));
            pickupFeed.AddChild(card);
            var row = Ui.Row(card); row.MouseFilter = MouseFilterEnum.Ignore;
            row.AddChild(Ui.Image(Assets.Icon(entry.Template), 34));
            var words = Ui.Column(row); words.MouseFilter = MouseFilterEnum.Ignore;
            words.AddChild(Ui.Label(Data.Item(entry.Template).Name + " ×" + entry.Quantity, 14, Ui.RarityColor(entry.Rarity), true));
            words.AddChild(Ui.Label("Received · " + entry.Rarity, 11, Ui.Muted));
            card.Modulate = new Color(1, 1, 1, 0);
            card.CreateTween().TweenProperty(card, "modulate:a", 1f, .15);
        }
        if (pickupNotes.Count > 3) pickupFeed.AddChild(Ui.Label("+" + (pickupNotes.Count - 3) + " other pickups · Open backpack [I]", 12, Ui.Muted, true));
    }

    private void ToggleEquipment(string itemId, string expectedSlot = "", bool equipOnly = false)
    {
        if (Snapshot is not { } snapshot) return;
        var item = snapshot.Self.Inventory.FirstOrDefault(x => x.Id == itemId);
        if (item is null) { Notify("Move this item to your backpack first.", true); return; }
        string problem = ExperienceRules.EquipmentProblem(snapshot.Self, item, Data, expectedSlot);
        if (problem != "") { Notify(problem, true); return; }
        var equipped = snapshot.Self.Equipment.FirstOrDefault(x => x.Value == item.Id);
        if (equipped.Key is not null)
        {
            if (!equipOnly) Send("unequip", arg: equipped.Key);
        }
        else Send("equip", item: item.Id);
    }

    private void ItemContext(Item item, string bag, Vector2 at)
    {
        if (gameWindow is null || Snapshot is not { } opened || !Online) return;
        if (bag is not ("inventory" or "bank")) return;
        foreach (var oldMenu in interfaceRoot.FindChildren("*", "Control", true, false).OfType<EquipmentMenu>())
            oldMenu.Close();
        selectedItem = item.Id; selectedBag = bag; lastPageStamp = "";
        var definition = Data.Item(item.Template);
        var ownerWindow = gameWindow;
        string ownerId = opened.Self.Id;
        bool wasEquipped = Items.Equipped(opened.Self, item.Id);
        var menu = new EquipmentMenu
        {
            ItemName = definition.Name, ItemIcon = Assets.Icon(item.Template),
            ItemColor = Ui.RarityColor(item.Rarity), Subtitle = item.Rarity + " · " + Ui.Words(definition.Type),
            ContextValid = () => Online && Snapshot?.Self.Id == ownerId
                && GodotObject.IsInstanceValid(ownerWindow) && !ownerWindow.IsQueuedForDeletion()
                && ownerWindow.IsInsideTree() && gameWindow == ownerWindow
        };
        if (definition.Slot != "" && bag == "inventory") menu.AddItem(wasEquipped ? "Unequip" : "Equip", 0);
        if (bag == "bank") menu.AddItem("Withdraw", 3, !NearRole("banker"));
        if (bag == "inventory" && definition.Type is "food" or "potion" or "scroll") menu.AddItem("Use", 2);
        if (bag == "inventory" && definition.Type is "book" or "treasure_map") menu.AddItem("Read", 4);
        menu.AddItem("Inspect item", 1);
        menu.SelectedAction = choice =>
        {
            if (Snapshot is not { } current || current.Self.Id != ownerId || !Online) return;
            var source = bag == "bank" ? current.Self.Bank : current.Self.Inventory;
            var currentItem = source.FirstOrDefault(x => x.Id == item.Id);
            if (currentItem is null) { Notify("This item moved. Open its actions again.", true); return; }
            if (choice == 0)
            {
                if (Items.Equipped(current.Self, item.Id) != wasEquipped)
                {
                    Notify("Equipment changed. Open its actions again.", true); return;
                }
                ToggleEquipment(item.Id);
            }
            else if (choice == 1) { selectedItem = item.Id; selectedBag = bag; lastPageStamp = ""; }
            else if (choice == 2) Send("consume", item: item.Id);
            else if (choice == 3)
            {
                if (NearRole("banker")) Send("withdraw", item: item.Id);
                else Notify("Move closer to the banker.", true);
            }
            else if (choice == 4) Send("read", item: item.Id);
        };
        interfaceRoot.AddChild(menu);
        menu.OpenAt(at);
    }

    private void BuildEquipmentAction(Node parent, Item? item, string bag)
    {
        if (Snapshot is null || item is null || bag != "inventory" || Data.Item(item.Template).Slot == "") return;
        bool equipped = Items.Equipped(Snapshot.Self, item.Id);
        string problem = ExperienceRules.EquipmentProblem(Snapshot.Self, item, Data);
        var button = Ui.Button(equipped ? "UNEQUIP" : "EQUIP", () => ToggleEquipment(item.Id), problem != "");
        button.Name = "PrimaryEquipmentAction";
        button.CustomMinimumSize = new Vector2(0, 44); button.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        button.TooltipText = problem == "" ? "Double-click for the same action. Right-click for item actions." : problem;
        parent.AddChild(button);
        if (problem != "") parent.AddChild(Ui.Label(problem, 13, Ui.Danger, true));
    }
}

