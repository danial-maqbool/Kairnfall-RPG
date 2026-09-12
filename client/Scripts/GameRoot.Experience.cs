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
    private Label interactionHint = null!, skillExperienceText = null!;
    private VBoxContainer pickupFeed = null!;
    private ProgressBar characterExperienceBar = null!, skillExperienceBar = null!, classResourceBar = null!;
    private Label classResourceText = null!, publicEventText = null!;
    private Button interactionButton = null!;
    private Button basicAttackButton = null!;
    private double contextClock;
    private string lastNoticeText = "";
    private double lastNoticeAt = -10;
    private readonly List<PickupNote> pickupNotes = [];
    private string lastExperienceSkill = "";
    private sealed record PickupNote(string Template, Rarity Rarity, int Quantity, double Until);

    private bool GameplayInputAllowed => !closing && awaitingBinding == "" && ExperienceRules.AllowsWorldInput(
        Online, Typing, gameWindow is not null || frontend.Visible, applicationFocused, Snapshot?.Self.Health > 0);

    public override void _Input(InputEvent @event)
    {
        // Godot runs GUI focus traversal before _UnhandledInput. Reserve the target
        // key only in active gameplay; never steal Tab from text or an open menu.
        if (@event is InputEventKey { Pressed: true } targetKey && GameplayInputAllowed
            && !targetKey.CtrlPressed && !targetKey.AltPressed && !targetKey.MetaPressed
            && bindings.TryGetValue("target_next", out var targetBinding)
            && targetKey.PhysicalKeycode == targetBinding)
        {
            if (!targetKey.Echo) CycleHostileTarget(targetKey.ShiftPressed);
            GetViewport().SetInputAsHandled(); return;
        }
        // GUI focus can consume a release after the press reached the world.
        if (InputMap.HasAction("basic_attack") && @event.IsActionReleased("basic_attack")) StopCombatInput();
    }

    private void CancelCombatApproach()
    {
        if (combatApproach) route.Clear();
        combatApproach = false;
    }
    private Kairnfall.Core.Point engagementOrigin;
    private bool engagementStarted;
    private double observedAttackCooldown;

    private void StopCombatInput()
    {
        engagementStarted = false;
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
        engagementOrigin = snapshot.Self.Position; engagementStarted = true;
        observedAttackCooldown = snapshot.Self.Cooldowns.GetValueOrDefault("attack");
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
        if (attackKeyHeld && engagementStarted && engagementOrigin.Distance(snapshot.Self.Position) >= 6)
        {
            StopCombatInput(); Notify("Target moved beyond the short pursuit area. Move closer to continue."); return;
        }
        double acknowledged = snapshot.Self.Cooldowns.GetValueOrDefault("attack");
        if (engagementStarted && acknowledged > observedAttackCooldown)
        {
            // Only accepted authoritative attacks start a fresh short approach.
            observedAttackCooldown = acknowledged; approachUsed = false; approachTravelled = 0;
            nextApproachPlan = 0; CancelCombatApproach();
        }
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
            // Replanning never resets this window. Confirmed hits may refresh the
            // short window, but never the fixed engagement-origin distance bound.
            if (now >= approachDeadline || approachTravelled >= 2.5)
            {
                StopCombatInput(); return;
            }
            if (now >= nextApproachPlan)
            {
                nextApproachPlan = now + .12;
                double remaining = Math.Min(2.5 - approachTravelled, Math.Max(0, 6 - engagementOrigin.Distance(snapshot.Self.Position)));
                var path = ExperienceRules.ApproachPath(snapshot.Self, target, Data, remaining);
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
        if (target.Kind == "event" && Snapshot?.Events.FirstOrDefault(x => x.Id == target.Id) is { } worldEvent) return WorldEventRules.InteractionVerb(worldEvent);
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

    private void CycleHostileTarget(bool reverse = false)
    {
        if (!GameplayInputAllowed) return;
        var snapshot = Snapshot!;
        if (ExperienceRules.CycleTarget(snapshot.Self, snapshot.Creatures, Data, selectedTarget, reverse) is { } target)
            SelectTarget("creature", target.Id);
        else
        {
            StopCombatInput(); SelectTarget("", "");
            Notify("No living creature within " + ExperienceRules.TargetCycleRadius + " tiles and clear sight.");
        }
    }

    private void BuildExperienceHud()
    {
        var controls = new HBoxContainer
        {
            Name = "CombatControls", AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = 1, AnchorBottom = 1,
            OffsetLeft = -330, OffsetRight = 330, OffsetTop = -142, OffsetBottom = -101,
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
        targetNextButton = Ui.Button("Target [Tab]", () => CycleHostileTarget());
        targetNextButton.Name = "CycleHostileTarget"; targetNextButton.FocusMode = FocusModeEnum.None;
        targetNextButton.TooltipText = "Tab: next living creature within 12 tiles. Shift+Tab: previous. Walls, pets and corpses are excluded. Typing keeps normal UI navigation.";
        controls.AddChild(targetNextButton);
        dashButton = Ui.Button("Dash [Q]", RequestDash); dashButton.Name = "DashAction";
        dashButton.FocusMode = FocusModeEnum.None; controls.AddChild(dashButton);
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
        var classMeter = new VBoxContainer
        {
            Name = "ClassResourceHud", AnchorLeft = .5f, AnchorRight = .5f, AnchorTop = 1, AnchorBottom = 1,
            OffsetLeft = -235, OffsetRight = 235, OffsetTop = -214, OffsetBottom = -184,
            MouseFilter = MouseFilterEnum.Ignore
        };
        classResourceText = Ui.Label("", 12, Ui.Text, true); classResourceText.HorizontalAlignment = HorizontalAlignment.Center;
        classResourceBar = new ProgressBar { MinValue = 0, MaxValue = 100, ShowPercentage = false, CustomMinimumSize = new Vector2(0, 7), MouseFilter = MouseFilterEnum.Ignore };
        classMeter.AddChild(classResourceText); classMeter.AddChild(classResourceBar); hud.AddChild(classMeter);
        publicEventText = Ui.Label("", 13, Ui.Gold, true);
        publicEventText.Name = "PublicEventHud"; publicEventText.AnchorLeft = publicEventText.AnchorRight = .5f;
        publicEventText.AnchorTop = publicEventText.AnchorBottom = 0; publicEventText.OffsetLeft = -310; publicEventText.OffsetRight = 310;
        publicEventText.OffsetTop = 18; publicEventText.OffsetBottom = 78; publicEventText.HorizontalAlignment = HorizontalAlignment.Center;
        publicEventText.MouseFilter = MouseFilterEnum.Ignore; publicEventText.AddThemeConstantOverride("outline_size", 4);
        publicEventText.AddThemeColorOverride("font_outline_color", Ui.Ink); hud.AddChild(publicEventText);
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
        TickAbilityBuffer();
        contextClock += delta;
        if (contextClock < .1 || interactionHint is null) return;
        contextClock = 0;
        double now = Time.GetTicksMsec() / 1000.0;
        var context = GameplayInputAllowed ? ContextTarget() : null;
        UpdateMobControls(); UpdateClassResourceHud(); UpdatePublicEventHud();
        interactionButton.Disabled = context is null;
        basicAttackButton.Disabled = !GameplayInputAllowed;
        basicAttackButton.Text = "Attack [" + bindings["basic_attack"] + "]";
        interactionButton.Text = "Interact [" + bindings["interact"] + "]";
        interactionHint.Text = context is { } target
            ? "[" + bindings["interact"] + "] " + ContextVerb(target) + " " + target.Name
            : GameplayInputAllowed ? "Hold " + bindings["basic_attack"] + " to attack · " + bindings["target_next"] + " cycles targets · " + bindings["dash"] + " dashes (4 mana)" : "";
        if (pickupNotes.RemoveAll(x => now > x.Until) > 0) RenderPickupFeed();
    }

    private static Color ClassResourceColor(string classId) => classId switch
    {
        "vanguard" => new Color("84a8c5"), "berserker" => new Color("d06a62"),
        "ranger" => new Color("8fbd74"), "rogue" => new Color("b18ac8"),
        "arcanist" => new Color("889be0"), "warden" => new Color("79b98b"),
        "templar" => new Color("e3c873"), "spellblade" => new Color("7fc6d8"), _ => Ui.Gold
    };

    private void UpdateClassResourceHud()
    {
        if (Snapshot is not { } snapshot || classResourceBar is null || classResourceText is null) return;
        ClassCombatRules.Normalize(snapshot.Self);
        string name = ClassCombatRules.ResourceName(snapshot.Self.Class);
        double threshold = ClassCombatRules.ReadyThreshold(snapshot.Self.Class);
        bool ready = snapshot.Self.ClassResource >= threshold;
        classResourceBar.Value = snapshot.Self.ClassResource;
        classResourceBar.Modulate = ClassResourceColor(snapshot.Self.Class);
        classResourceText.Text = name.ToUpperInvariant() + "  " + Math.Round(snapshot.Self.ClassResource) + "/100" + (ready ? "  ·  READY" : "");
        string description = ClassCombatRules.PassiveDescription(snapshot.Self.Class) + "\n" + ClassCombatRules.Hint(snapshot.Self);
        classResourceBar.TooltipText = description; classResourceText.TooltipText = description;
    }

    private void UpdatePublicEventHud()
    {
        if (Snapshot is not { } snapshot || publicEventText is null) return;
        var value = snapshot.Events.Where(x => x.Zone == snapshot.Self.Zone)
            .OrderBy(x => x.Status == "active" ? 0 : 1).ThenByDescending(x => x.EffectEnds).FirstOrDefault();
        if (value is null) { publicEventText.Text = ""; return; }
        if (value.Status == "active")
        {
            int stage = Math.Min(WorldEventRules.StageCount(value.Kind), value.Stage + 1);
            int remaining = Math.Max(0, (int)Math.Ceiling(value.StageEnds - snapshot.Time));
            publicEventText.Text = $"PUBLIC EVENT · {value.Name}\nStage {stage}/{WorldEventRules.StageCount(value.Kind)} · {WorldEventRules.StageLabel(value)} · {WorldEventRules.ProgressText(value)} · {remaining}s · You {WorldEventRules.Contribution(value,snapshot.Self.Id):0}";
        }
        else
        {
            int remaining = Math.Max(0, (int)Math.Ceiling(value.EffectEnds - snapshot.Time));
            publicEventText.Text = $"REGIONAL AFTERMATH · {(value.Status == "success" ? "SUCCESS" : "FAILED")} · {WorldEventRules.EffectLabel(value.Effect)} · {remaining}s";
        }
    }

    private void ObservePlayerChanges(Snapshot? previous, Snapshot current)
    {
        if(previous is null)
        {
            var first=FirstHourExperience.Current(Data,current.Self);
            if(first is not null){Notify("WAYFARER'S REST · Follow the Wayfarer's Path beneath your current objective.");audio?.PlayEffect("quest_accept");}
            return;
        }
        if(previous.Self.Id != current.Self.Id) return;
        if(previous.Self.Zone==current.Self.Zone&&previous.Self.Position.Distance(current.Self.Position)>.12)
            audio?.PlayFootstep(WorldMap.TileAt(Data.Zone(current.Self.Zone),(int)current.Self.Position.X,(int)current.Self.Position.Y));
        if (current.Self.Health < previous.Self.Health - .5)
        {
            World.CombatImpact(current.Self.Position, 3.2f); audio?.PlayEffect("hurt");
        }
        if (selectedTargetKind == "creature")
        {
            var beforeTarget = previous.Creatures.FirstOrDefault(x => x.Id == selectedTarget);
            var afterTarget = current.Creatures.FirstOrDefault(x => x.Id == selectedTarget);
            if (beforeTarget is not null && afterTarget is not null && afterTarget.Health < beforeTarget.Health - .5)
            {
                World.CombatImpact(afterTarget.Position, 2.1f); audio?.PlayWeaponImpact(current.Self,Data); audio?.PlayCreature(Data.Mob(afterTarget.Template),afterTarget.Health<=0);
            }
        }
        double beforeResource = double.IsFinite(previous.Self.ClassResource) ? previous.Self.ClassResource : 0;
        double afterResource = double.IsFinite(current.Self.ClassResource) ? current.Self.ClassResource : 0;
        double threshold = ClassCombatRules.ReadyThreshold(current.Self.Class);
        Color resourceColor = ClassResourceColor(current.Self.Class);
        if (afterResource >= beforeResource + 4)
            World.CombatNote(current.Self.Position, ClassCombatRules.ResourceName(current.Self.Class).ToUpperInvariant() + " +" + Math.Round(afterResource - beforeResource), resourceColor);
        if (beforeResource < threshold && afterResource >= threshold)
        {
            World.ClassBurst(current.Self.Position, resourceColor); audio?.PlayEffect("class_ready");
        }
        else if (beforeResource - afterResource >= Math.Min(40, threshold))
        {
            World.ClassBurst(current.Self.Position, resourceColor); audio?.PlayEffect("class_release");
        }
        foreach (var value in current.Events)
        {
            var beforeEvent = previous.Events.FirstOrDefault(x => x.Id == value.Id);
            if (beforeEvent is null && value.Status == "active")
            {
                Notify("WORLD EVENT · " + value.Name + " · " + Data.Zone(value.Zone).Name); audio?.PlayEffect("event_start");
                if (value.Zone == current.Self.Zone) World.ClassBurst(value.Position, new Color("e0b868"));
            }
            else if (beforeEvent is not null && beforeEvent.Status != value.Status)
            {
                Notify(value.Status == "success" ? "EVENT COMPLETE · " + value.Name : "EVENT FAILED · " + value.Name, value.Status == "failure");
                audio?.PlayEffect(value.Status=="success"?"event_complete":"error");
                if (value.Zone == current.Self.Zone) World.ClassBurst(value.Position, value.Status == "success" ? Ui.Success : Ui.Danger);
            }
            else if (beforeEvent is not null && beforeEvent.Stage != value.Stage && value.Status == "active" && value.Zone == current.Self.Zone)
                Notify("EVENT ADVANCED · " + WorldEventRules.StageLabel(value));
        }
        if (previous.Self.Zone != current.Self.Zone)
        {
            route.Clear(); pendingInteraction = null; lastInput = Vector2.Zero; StopCombatInput();
            var entered=Data.Zone(current.Self.Zone); Notify("ARRIVED · "+entered.Name+" · "+entered.Layer); audio?.PlayEffect("transition");
        }
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
        if (changed) { RenderPickupFeed(); audio?.PlayEffect("loot"); }
        foreach(string completed in current.Self.CompletedQuests.Except(previous.Self.CompletedQuests,StringComparer.Ordinal))
        {
            var quest=Data.Quests.FirstOrDefault(x=>x.Id==completed); if(quest is null)continue;
            Notify("QUEST COMPLETE · "+quest.Name); World.ClassBurst(current.Self.Position,Ui.Gold); audio?.PlayEffect("quest_complete");
        }
        foreach (var skill in Data.Skills)
        {
            long beforeXp=previous.Self.SkillXp.GetValueOrDefault(skill.Id);
            long currentXp=current.Self.SkillXp.GetValueOrDefault(skill.Id);
            if(currentXp>beforeXp) lastExperienceSkill=skill.Id;
            int beforeLevel=Progression.SkillLevel(beforeXp),afterLevel=Progression.SkillLevel(currentXp);
            if(afterLevel>beforeLevel)
            {
                Notify("SKILL UP · "+skill.Name+" "+afterLevel); World.ClassBurst(current.Self.Position,Ui.Success); audio?.PlayEffect("skill_up");
            }
        }
        int overall = Progression.PlayerLevel(current.Self);
        if (overall > Progression.PlayerLevel(previous.Self))
        {
            string key = "overall_" + current.Self.Id;
            bool explained = settings.GetValue("hints", key, false).AsBool();
            Notify("LEVEL UP · " + overall + (explained ? "" : " · Training any skill advances your character level."));
            World.ClassBurst(current.Self.Position,Ui.Gold); audio?.PlayEffect("level_up");
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
        // Opening actions for the selected item must not tear down its control
        // on the next UI tick. Rebuild only when the inspector selection changes.
        if (selectedItem != item.Id || selectedBag != bag)
        {
            selectedItem = item.Id; selectedBag = bag; lastPageStamp = "";
        }
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
        var reclaim=bag=="inventory"?CraftEconomy.Reclaim(Data,item):null;
        if(reclaim is not null) menu.AddItem($"Reclaim → {reclaim.Quantity} {Data.Item(reclaim.Material).Name}",5,wasEquipped||!ClientAtStation(reclaim.Recipe.Station));
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
            else if(choice==5&&CraftEconomy.Reclaim(Data,currentItem) is { } plan)
                Confirm("Reclaim materials",$"Destroy {Data.Item(currentItem.Template).Name} and recover {plan.Quantity} {Data.Item(plan.Material).Name}?",()=>Send("salvage",item:currentItem.Id));
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
