using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public static class LocalRealmAddressRules
{
    public const string Default = "http://127.0.0.1:5077";
    public static bool Allowed(string address)
        => Uri.TryCreate(address, UriKind.Absolute, out var uri)
            && uri.Scheme is "http" or "https" && uri.UserInfo == "" && uri.Query == "" && uri.Fragment == ""
            && (uri.IsLoopback || System.Net.IPAddress.TryParse(uri.Host, out var ip) && System.Net.IPAddress.IsLoopback(ip));
}

public static class ClassicLootRules
{
    public static LootPile? Underfoot(Character self, IEnumerable<LootPile> piles, double time)
        => self.Health <= 0 || !self.Position.Finite || !double.IsFinite(time) ? null
            : piles.Where(p => p.Zone == self.Zone && p.Position.Finite
                && Math.Floor(p.Position.X) == Math.Floor(self.Position.X)
                && Math.Floor(p.Position.Y) == Math.Floor(self.Position.Y)
                && ExperienceRules.LootAvailable(self, p, time))
                .OrderBy(p => p.Position.Distance(self.Position)).ThenBy(p => p.Id, StringComparer.Ordinal).FirstOrDefault();
}

public static class ClassicTargetRules
{
    public static bool Valid(Character self, Creature? target)
        => self.Health > 0 && self.Position.Finite && target is not null
            && target.Health > 0 && target.Position.Finite && target.Owner == ""
            && target.Zone == self.Zone && self.Position.Distance(target.Position) <= ExperienceRules.TargetCycleRadius;

    public static bool Ready(Character self, Creature? target, Catalog data, double time)
        => double.IsFinite(time) && Valid(self, target)
            && ExperienceRules.AttackProblem(self, data, time) == ""
            && ExperienceRules.CanTarget(self, target!, data, ExperienceRules.WeaponRange(self, data), true);
}

public partial class GameRoot
{
    private string classicAttackTarget = "";
    private bool gridWasAllowed;
    private bool GridControls => ClassicSessionActive || ClassicControls && settings.GetValue("controls", "classic_grid", false).AsBool();
    private bool ClassicControls => ClassicSessionActive || settings.GetValue("controls", "classic_target_attack", false).AsBool();

    private void PickupUnderfoot()
    {
        if (!GameplayInputAllowed || actionBusy || Snapshot is not { } snapshot
            || ClassicLootRules.Underfoot(snapshot.Self, World.Loot, snapshot.Time) is not { } pile) return;
        string readiness = InteractionReadinessRules.LootProblem(snapshot.Self, pile, Data, snapshot.Time);
        if (readiness != "") { Notify(readiness, true); return; }
        double now = Time.GetTicksMsec() / 1000.0;
        if (!interactionGate.TryTake(now, snapshot.Time, 0, true, .4)) return;
        StopCombatInput(); ClearRoute(); pendingInteraction = null;
        Send("loot", pile.Id);
    }

    private void ArmClassicTarget(string id)
    {
        StopCombatInput(); ClearRoute(); pendingInteraction = null;
        if (!ClassicControls || Snapshot is not { } snapshot) return;
        var target = snapshot.Creatures.FirstOrDefault(x => x.Id == id);
        if (ClassicTargetRules.Valid(snapshot.Self, target)) classicAttackTarget = id;
    }

    private void PrimaryAction(bool held)
    {
        if (!GameplayInputAllowed) return;
        if (classicGatherTarget != "") { StopCombatInput(); Notify("Gathering stopped."); return; }
        if (Snapshot is { } siteSnapshot && selectedTargetKind == "classic_site"
            && ClassicInteractionRules.TutorialSite(siteSnapshot.Self, Data, selectedTarget) is null)
        {
            SelectTarget("", ""); ClearRoute(); pendingInteraction = null; World.Waypoint = null;
            Notify("Tutorial object is no longer available.", true); return;
        }
        if (Snapshot is { } tutorialSnapshot && ClassicInteractionRules.InTutorial(tutorialSnapshot.Self, Data)
            && selectedTargetKind == "node"
            && !tutorialSnapshot.Nodes.Any(x => x.Id == selectedTarget && x.Zone == tutorialSnapshot.Self.Zone))
        {
            StopCombatInput(); ClearRoute(); pendingInteraction = null;
            Notify("Resource is no longer available.", true); return;
        }
        if (ClassicControls && selectedTargetKind != "creature" && ContextTarget() is not null)
        {
            if (classicGatherTarget != "") { StopCombatInput(); Notify("Gathering stopped."); return; }
            if (ClassicGatherEnabled && ContextTarget() is { Kind: "node" } node
                && Snapshot!.Nodes.Any(x => x.Id == node.Id && !x.Template.StartsWith("structure_", StringComparison.Ordinal)))
            { BeginClassicGather(node); return; }
            StopCombatInput(); InteractWithContext(); return;
        }
        BeginBasicAttack(held);
    }

    private void TickClassicTargetAttack()
    {
        if (classicAttackTarget == "" || !GameplayInputAllowed || actionBusy || Snapshot is not { } snapshot) return;
        var target = snapshot.Creatures.FirstOrDefault(x => x.Id == classicAttackTarget);
        if (!ClassicControls || selectedTargetKind != "creature" || selectedTarget != classicAttackTarget
            || !ClassicTargetRules.Valid(snapshot.Self, target))
        {
            classicAttackTarget = ""; return;
        }
        // No path planning, target replacement, invented hit, or predicted reward.
        if (!ClassicTargetRules.Ready(snapshot.Self, target, Data, snapshot.Time)) return;
        double now = Time.GetTicksMsec() / 1000.0;
        if (basicAttackGate.TryTake(now, snapshot.Time, snapshot.Self.Cooldowns.GetValueOrDefault("attack"), true,
            ExperienceRules.AttackInterval(snapshot.Self, Data)))
            _ = SendAsync(new GameCommand { Kind = "attack", Target = target!.Id }, true);
    }

    private bool FocusHudEnabled => settings.GetValue("hud", "focus_world", ClassicSessionActive).AsBool();
    private Control focusHud = null!;
    private Label focusObjective = null!;
    private readonly List<(Label Label, ProgressBar Bar)> focusMeters = [];

    private void BuildFocusHud()
    {
        focusHud = new Control { Name = "CompactWorldHud", MouseFilter = MouseFilterEnum.Ignore };
        hud.AddChild(focusHud); focusHud.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        var vitals = new VBoxContainer { Position = new Vector2(16, 16), CustomMinimumSize = new Vector2(254, 0), MouseFilter = MouseFilterEnum.Ignore };
        vitals.AddThemeConstantOverride("separation", 2); focusHud.AddChild(vitals);
        foreach (var color in new[] { new Color("70a765"), new Color("507fbb"), new Color("889957"), new Color("b89a58"), new Color("6da8df") })
        {
            var row = new HBoxContainer { MouseFilter = MouseFilterEnum.Ignore };
            var label = Ui.Label("", 12, Ui.Text); label.CustomMinimumSize = new Vector2(103, 0);
            label.ClipText = true; label.MouseFilter = MouseFilterEnum.Ignore;
            label.AddThemeConstantOverride("outline_size", 3); label.AddThemeColorOverride("font_outline_color", Ui.Ink);
            var bar = Ui.Bar(color, 145); bar.CustomMinimumSize = new Vector2(145, 12); bar.MouseFilter = MouseFilterEnum.Ignore;
            row.AddChild(label); row.AddChild(bar); vitals.AddChild(row); focusMeters.Add((label, bar));
        }
        classicFoodCompact = BuildClassicFoodLabel(vitals, "ClassicFoodCompact");
        focusObjective = Ui.Label("", 12, Ui.Text, true); focusObjective.CustomMinimumSize = new Vector2(254, 0);
        focusObjective.MaxLinesVisible = 4; focusObjective.MouseFilter = MouseFilterEnum.Ignore;
        focusObjective.AddThemeConstantOverride("outline_size", 3); focusObjective.AddThemeColorOverride("font_outline_color", Ui.Ink);
        vitals.AddChild(focusObjective);
        var navigation = new HBoxContainer
        {
            Name = "CompactWorldNavigation", AnchorLeft = 1, AnchorRight = 1,
            OffsetLeft = -294, OffsetRight = -16, OffsetTop = 16, MouseFilter = MouseFilterEnum.Ignore
        };
        foreach (var item in new[] { ("Character", "Character"), ("Bag", "Inventory"), ("Menu", "Menu") })
        {
            var button = Ui.Button(item.Item1, () => OpenPage(item.Item2)); button.FocusMode = FocusModeEnum.None;
            navigation.AddChild(button);
        }
        focusHud.AddChild(navigation); BuildClassicConsumables();
        var action = new ClassicActionCircle { Name = "ClassicActionCircle", AnchorLeft = .5f, AnchorRight = .5f,
            AnchorTop = 1, AnchorBottom = 1, OffsetLeft = 242, OffsetRight = 306, OffsetTop = -168, OffsetBottom = -104,
            TooltipText = "Action [Space] — use the object you face, gather, or attack the selected creature." };
        action.Pressed += () => PrimaryAction(false); focusHud.AddChild(action);
        ApplyFocusHud();
    }

    private void ApplyFocusHud()
    {
        if (focusHud is null) return;
        bool compact = FocusHudEnabled;
        focusHud.Visible = compact; World.ClassicPresentation = compact; FitClassicWorldHud(compact);
        foreach (string name in new[] { "VitalsAndObjectives", "QuestTracker", "MinimapPanel", "Navigation" })
            if (hud.FindChild(name, true, false) is Control control) control.Visible = !compact;
        UpdateFocusHud();
    }

    private void FitClassicWorldHud(bool compact)
    {
        if (hud.FindChild("AbilityBar", true, false) is Control bar)
        {
            bar.PivotOffset = new Vector2(bar.Size.X / 2, bar.Size.Y);
            bar.Scale = compact ? new Vector2(.8f, .8f) : Vector2.One;
            if (bar is PanelContainer panel) panel.AddThemeStyleboxOverride("panel", compact
                ? Ui.Box(new Color(.075f, .12f, .08f, .72f), new Color("778475"), 10)
                : Ui.Box(new Color("211e19"), new Color("78664a"), 10));
        }
        if (hud.FindChild("CombatControls", true, false) is Control controls)
        {
            controls.PivotOffset = new Vector2(controls.Size.X / 2, controls.Size.Y);
            controls.Scale = compact ? new Vector2(.8f, .8f) : Vector2.One;
            controls.OffsetLeft = compact ? -185 : -330; controls.OffsetRight = compact ? 185 : 330;
            if (basicAttackButton is not null) basicAttackButton.Visible = !compact;
        }
        if (hud.FindChild("ClassResourceHud", true, false) is Control resource)
        { resource.OffsetLeft = compact ? -117 : -235; resource.OffsetRight = compact ? 117 : 235; }
        if (chatFrame is not null)
        {
            chatFrame.PivotOffset = new Vector2(0, chatFrame.Size.Y);
            chatFrame.Scale = compact ? new Vector2(.85f, .85f) : Vector2.One;
            chatFrame.OffsetBottom = compact ? -150 : -106;
            chatFrame.OffsetTop = compact ? -302 : -258;
            chatFrame.AddThemeStyleboxOverride("panel", compact
                ? Ui.Box(new Color(.075f, .12f, .08f, .68f), new Color("778475"), 10)
                : Ui.Box(new Color("211e19"), new Color("78664a"), 10));
        }
        if (targetHealth is not null) targetHealth.AddThemeStyleboxOverride("fill", Ui.Box(compact ? new Color("d5b760") : new Color("a94c46"), null, 0));
    }

    private bool? classicProgressionStyle;
    private bool FitClassicProgressionFeedback()
    {
        bool compact = FocusHudEnabled;
        if (classicProgressionStyle != compact)
        {
            classicProgressionStyle = compact;
            progressionBanner.AddThemeStyleboxOverride("panel", compact
                ? Ui.Box(new Color(.045f, .085f, .05f, .58f), new Color(.45f, .52f, .43f, .55f), 8)
                : Ui.Box(new Color("211e19"), new Color("78664a"), 10));
            progressionTitle.SetMeta(Ui.BaseFontSizeMeta, compact ? 12 : 16);
            progressionDetail.SetMeta(Ui.BaseFontSizeMeta, compact ? 12 : 13);
            progressionTitle.AddThemeFontSizeOverride("font_size", Ui.ScaledFont(compact ? 12 : 16));
            progressionDetail.AddThemeFontSizeOverride("font_size", Ui.ScaledFont(compact ? 12 : 13));
            progressionTitle.MaxLinesVisible = compact ? 1 : 2;
            progressionDetail.MaxLinesVisible = compact ? 2 : 4;
            progressionTitle.ClipText = compact;
            progressionTitle.AutowrapMode = compact ? TextServer.AutowrapMode.Off : TextServer.AutowrapMode.WordSmart;
            progressionTitle.CustomMinimumSize = compact ? new Vector2(0,
                progressionTitle.GetThemeFont("font").GetHeight(progressionTitle.GetThemeFontSize("font_size"))) : Vector2.Zero;
            progressionDetail.CustomMinimumSize = compact ? new Vector2(0,
                progressionDetail.GetThemeFont("font").GetHeight(progressionDetail.GetThemeFontSize("font_size")) * 2) : Vector2.Zero;
            progressionTitle.AddThemeColorOverride("font_color", Ui.Gold);
        }
        if (!compact) return false;
        // Accepted progression stays visible in a small feed beside the world,
        // leaving the centered avatar and its next interaction unobscured.
        float width = Math.Min(320, hud.Size.X * .36f);
        progressionBanner.AnchorLeft = progressionBanner.AnchorRight = 0;
        progressionBanner.OffsetLeft = 16; progressionBanner.OffsetRight = 16 + width;
        progressionBanner.OffsetTop = focusObjective.GetGlobalRect().End.Y + 10;
        progressionBanner.Size = new Vector2(width, progressionBanner.GetCombinedMinimumSize().Y);
        progressionTitle.AddThemeColorOverride("font_color", progressionBanner.GetMeta("progression_kind", "").AsString() == "skill"
            ? new Color("82bde9") : Ui.Gold);
        return true;
    }

    private void UpdateFocusHud()
    {
        if (focusHud is null || !focusHud.Visible || Snapshot is not { } snapshot) return;
        foreach (string name in new[] { "VitalsAndObjectives", "QuestTracker", "MinimapPanel", "Navigation" })
            if (hud.FindChild(name, true, false) is Control control) control.Hide();
        var labels = new[] { "Health", "Mana", "Stamina", "Experience", skillExperienceText.Text.Split(" XP")[0] };
        var originals = new[] { health, mana, stamina, characterExperienceBar, skillExperienceBar };
        for (int i = 0; i < focusMeters.Count; i++)
        {
            focusMeters[i].Label.Text = labels[i];
            focusMeters[i].Bar.MaxValue = originals[i].MaxValue;
            focusMeters[i].Bar.Value = originals[i].Value;
            focusMeters[i].Bar.TooltipText = i < 3 ? labels[i] + " " + originals[i].Value.ToString("0") + "/" + originals[i].MaxValue.ToString("0") : originals[i].TooltipText;
        }
        var objective = journeyObjective ?? SessionJourneyObjective(snapshot);
        var navigation = NewPlayerJourney.Navigation(Data, snapshot.Self, objective);
        focusObjective.Text = snapshot.Self.Name + " · Level " + Progression.PlayerLevel(snapshot.Self)
            + "\n" + objective.Objective + " [" + JourneyKey("quests") + "]"
            + "\n" + navigation.Description;
        focusObjective.TooltipText = objectiveText.TooltipText; UpdateClassicConsumables(); FitClassicWorldHud(true);
    }
}
