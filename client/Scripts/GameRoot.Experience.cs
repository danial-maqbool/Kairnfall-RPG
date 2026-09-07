using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private bool attackKeyHeld;
    private bool applicationFocused = true;
    private string hotbarCharacter = "";
    private readonly AttackRequestGate basicAttackGate = new();
    private Label interactionHint = null!;
    private Label progressionHint = null!;
    private VBoxContainer pickupFeed = null!;
    private Button interactionButton = null!;
    private Button basicAttackButton = null!;
    private double contextClock, progressionUntil;
    private string lastNoticeText = "";
    private double lastNoticeAt = -10;
    private readonly List<PickupNote> pickupNotes = [];
    private sealed record PickupNote(string Template, Rarity Rarity, int Quantity, double Until);

    private bool GameplayInputAllowed => ExperienceRules.AllowsWorldInput(
        Online, Typing, gameWindow is not null || frontend.Visible, applicationFocused, Snapshot?.Self.Health > 0);

    public override void _Input(InputEvent @event)
    {
        // Release must be seen even when the pointer or focus moved into a menu.
        if (InputMap.HasAction("basic_attack") && @event.IsActionReleased("basic_attack")) attackKeyHeld = false;
    }

    private void StopCombatInput()
    {
        attackKeyHeld = false;
        autoAttack = false;
    }

    private void BeginBasicAttack(bool held)
    {
        if (!GameplayInputAllowed) return;
        var snapshot = Snapshot!;
        var target = ExperienceRules.ChooseTarget(snapshot.Self, snapshot.Creatures, Data,
            selectedTargetKind == "creature" ? selectedTarget : "", ExperienceRules.WeaponRange(snapshot.Self, Data));
        if (target is null)
        {
            StopCombatInput();
            Notify("Move within weapon range of a hostile creature.");
            return;
        }
        SelectTarget("creature", target.Id);
        attackKeyHeld = held;
        TryBasicAttack();
    }

    private void TryBasicAttack()
    {
        if (!GameplayInputAllowed || actionBusy || selectedTargetKind != "creature") return;
        var snapshot = Snapshot!;
        var target = snapshot.Creatures.FirstOrDefault(x => x.Id == selectedTarget);
        if (target is null || target.Health <= 0 || target.Owner != "")
        {
            StopCombatInput();
            return;
        }
        bool disabled = snapshot.Self.Statuses.Any(x => x.Until > snapshot.Time && x.Kind is "stun" or "freeze");
        bool inRange = ExperienceRules.CanTarget(snapshot.Self, target, Data,
            ExperienceRules.WeaponRange(snapshot.Self, Data), true);
        double now = Time.GetTicksMsec() / 1000.0;
        if (basicAttackGate.TryTake(now, snapshot.Time, snapshot.Self.Cooldowns.GetValueOrDefault("attack"), !disabled && inRange))
            _ = SendAsync(new GameCommand { Kind = "attack", Target = target.Id }, true);
    }

    private WorldTarget? ContextTarget()
    {
        if (Snapshot is not { } snapshot) return null;
        bool Available(WorldTarget target)
        {
            if (target.Kind == "node") return snapshot.Nodes.Any(x => x.Id == target.Id && x.ReadyAt <= snapshot.Time);
            if (target.Kind == "chest") return snapshot.Chests.Any(x => x.Id == target.Id && x.ReadyAt <= snapshot.Time);
            return true;
        }
        return ExperienceRules.ChooseInteraction(snapshot.Self, World.Targets.Where(Available), Data);
    }

    private void InteractWithContext()
    {
        if (!GameplayInputAllowed) return;
        if (ContextTarget() is { } target) Activate(target);
        // Empty-space interaction deliberately sends no command and no chat message.
    }

    private void CycleHostileTarget()
    {
        if (!GameplayInputAllowed) return;
        var snapshot = Snapshot!;
        var targets = snapshot.Creatures.Where(x => ExperienceRules.CanTarget(snapshot.Self, x, Data, 12))
            .OrderBy(x => x.Position.Distance(snapshot.Self.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
        if (targets.Length == 0) return;
        int index = Array.FindIndex(targets, x => x.Id == selectedTarget);
        SelectTarget("creature", targets[(index + 1) % targets.Length].Id);
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
        basicAttackButton.TooltipText = "Click for one basic attack. Hold the attack key to repeat. Click a creature to select it.";
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
            OffsetLeft = -276, OffsetRight = -18, OffsetTop = 266,
            MouseFilter = MouseFilterEnum.Ignore
        };
        hud.AddChild(pickupFeed);
        foreach (var button in hotbarButtons) button.FocusMode = FocusModeEnum.None;
    }

    private void TickExperience(double delta)
    {
        if (!GameplayInputAllowed) StopCombatInput();
        if (attackKeyHeld && !Input.IsActionPressed("basic_attack")) attackKeyHeld = false;
        if (attackKeyHeld || autoAttack) TryBasicAttack();
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
            ? "[" + bindings["interact"] + "] " + ExperienceRules.InteractionVerb(target.Kind) + " " + target.Name
            : GameplayInputAllowed ? "Hold " + bindings["basic_attack"] + " to attack  ·  Tab selects a hostile  ·  1–0 uses abilities" : "";
        if (now > progressionUntil) progressionHint.Text = "";
        if (pickupNotes.RemoveAll(x => now > x.Until) > 0) RenderPickupFeed();
    }

    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
    {
        if (previous is null || previous.Self.Id != current.Self.Id) return;
        var before = previous.Self.Inventory.GroupBy(x => (x.Template, x.Rarity))
            .ToDictionary(x => x.Key, x => x.Sum(y => y.Quantity));
        double now = Time.GetTicksMsec() / 1000.0;
        bool changed = false;
        foreach (var group in current.Self.Inventory.GroupBy(x => (x.Template, x.Rarity)))
        {
            int gained = group.Sum(x => x.Quantity) - before.GetValueOrDefault(group.Key);
            if (gained <= 0) continue;
            pickupNotes.Add(new PickupNote(group.Key.Template, group.Key.Rarity, gained, now + 6));
            changed = true;
        }
        if (pickupNotes.Count > 20) pickupNotes.RemoveRange(0, pickupNotes.Count - 20);
        if (changed) RenderPickupFeed();
        var progress = new List<string>();
        foreach (var skill in Data.Skills)
        {
            long gained = current.Self.SkillXp.GetValueOrDefault(skill.Id) - previous.Self.SkillXp.GetValueOrDefault(skill.Id);
            if (gained <= 0) continue;
            int level = Progression.Level(current.Self, skill.Id);
            bool leveled = level > Progression.Level(previous.Self, skill.Id);
            progress.Add(leveled ? skill.Name + " reached " + level : "+" + gained + " " + skill.Name + " XP");
        }
        if (progress.Count > 0)
        {
            progressionHint.Text = string.Join(" · ", progress.Take(3));
            progressionUntil = now + 4;
        }
        int overall = Progression.PlayerLevel(current.Self);
        if (overall > Progression.PlayerLevel(previous.Self)) Notify("Overall level " + overall + " — advanced through skill training.");
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
        if (gameWindow is null || Snapshot is null) return;
        selectedItem = item.Id; selectedBag = bag; lastPageStamp = "";
        var menu = new EquipmentMenu();
        bool equipment = Data.Item(item.Template).Slot != "";
        if (equipment && bag == "inventory") menu.AddItem(Items.Equipped(Snapshot.Self, item.Id) ? "Unequip" : "Equip", 0);
        menu.AddItem("Inspect item", 1);
        if (bag == "inventory" && Data.Item(item.Template).Type is "food" or "potion" or "scroll") menu.AddItem("Use", 2);
        menu.SelectedAction = choice =>
        {
            if (choice == 0) ToggleEquipment(item.Id);
            if (choice == 1) { selectedItem = item.Id; selectedBag = bag; lastPageStamp = ""; }
            if (choice == 2) Send("consume", item: item.Id);
        };
        gameWindow.AddChild(menu);
        menu.Popup(new Rect2I((Vector2I)at, new Vector2I(1, 1)));
    }

    private void BuildEquipmentAction(Node parent, Item? item, string bag)
    {
        if (Snapshot is null || item is null || bag != "inventory" || Data.Item(item.Template).Slot == "") return;
        bool equipped = Items.Equipped(Snapshot.Self, item.Id);
        string problem = ExperienceRules.EquipmentProblem(Snapshot.Self, item, Data);
        var button = Ui.Button(equipped ? "UNEQUIP" : "EQUIP", () => ToggleEquipment(item.Id), problem != "");
        button.Name = "PrimaryEquipmentAction";
        button.CustomMinimumSize = new Vector2(0, 44);
        button.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        button.TooltipText = problem == "" ? "Double-click the item for the same action. Right-click for its menu." : problem;
        parent.AddChild(button);
        if (problem != "") parent.AddChild(Ui.Label(problem, 13, Ui.Danger, true));
    }
}

public partial class EquipmentMenu : PopupMenu
{
    public Action<long>? SelectedAction { get; set; }
    public override void _Ready() { IdPressed += Select; PopupHide += Closed; }
    private void Select(long id) { var action = SelectedAction; Hide(); action?.Invoke(id); }
    private void Closed() => QueueFree();
    public override void _ExitTree() { IdPressed -= Select; PopupHide -= Closed; SelectedAction = null; }
}
