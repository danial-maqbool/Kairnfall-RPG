using Godot;
using Kairnfall.Core;
using System.Text.RegularExpressions;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private HBoxContainer journeyActions = null!;
    private Button journeyAction = null!, journeyUnderstood = null!, nearbyTravelers = null!, journeyMenu = null!;
    private HudPanel progressionBanner = null!;
    private Label progressionTitle = null!, progressionDetail = null!;
    private JourneyObjective? journeyObjective;
    private JourneyHint? journeyHint;
    private string journeyCharacter = "", feedbackCharacter = "";
    private readonly HashSet<string> pendingGuidance = new(StringComparer.Ordinal);
    private readonly HashSet<string> displayedProgression = new(StringComparer.Ordinal);
    private readonly Queue<ProgressionMoment> progressionQueue = new();
    private double progressionUntil;
    private HudPanel journeyPanel = null!;
    private VBoxContainer journeyHome = null!;
    private bool compactJourneyLayout;
    private bool journeyLayoutReady;

    private string CompactJourneyLine(string text, int length = 36)
    {
        int limit = Math.Max(16, (int)(length * (journeyPanel?.Size.X ?? 290) / 290 / Ui.TextScale));
        return text.Length <= limit ? text : text[..(limit - 1)] + "…";
    }
    private string JourneyKey(string action)
    {
        if (bindings.TryGetValue(action, out var binding)) return binding.ToString();
        if (InputMap.HasAction(action) && InputMap.ActionGetEvents(action).OfType<InputEventKey>().FirstOrDefault() is { } key)
            return key.PhysicalKeycode.ToString();
        return action.Replace('_', ' ');
    }
    private string JourneyHintText(string text) => Regex.Replace(text, @"\{([a-z_]+)\}", match => JourneyKey(match.Groups[1].Value));

    private void BuildNewPlayerHud(VBoxContainer objectiveColumn)
    {
        journeyPanel = (HudPanel)objectiveColumn.GetParent();
        journeyHome = (VBoxContainer)journeyPanel.GetParent();
        var objectiveHeader = objectiveColumn.GetChildren().OfType<HBoxContainer>().First();
        objectiveHeader.GetChildren().OfType<Label>().First().Hide();
        journeyMenu = Ui.Button("Menu", () => OpenPage("Menu"));
        journeyMenu.Name = "JourneyGameMenu"; journeyMenu.FocusMode = FocusModeEnum.None;
        journeyMenu.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        journeyMenu.SetMeta(Ui.BaseFontSizeMeta, 12); journeyMenu.AddThemeFontSizeOverride("font_size", Ui.ScaledFont(12));
        journeyMenu.TooltipText = "Game panels · inventory, equipment, quests, skills, crafting, social and settings.";
        objectiveHeader.AddChild(journeyMenu); objectiveHeader.MoveChild(journeyMenu, 0);
        objectiveText.Name = "RecommendedObjective";
        objectiveText.SetMeta(Ui.BaseFontSizeMeta, 13);
        objectiveText.AddThemeFontSizeOverride("font_size", Ui.ScaledFont(13));
        objectiveText.MouseFilter = MouseFilterEnum.Pass;
        firstHourText.MouseFilter = MouseFilterEnum.Pass;
        objectiveText.AutowrapMode = TextServer.AutowrapMode.Off; objectiveText.ClipText = true;
        firstHourText.ClipText = true;
        objectiveText.MaxLinesVisible = 4;
        firstHourText.MaxLinesVisible = 2;
        journeyActions = Ui.Row(objectiveColumn); journeyActions.Name = "JourneyActions";
        journeyAction = Ui.Button("Walk to objective", FollowJourneyObjective);
        journeyAction.ClipText = true; journeyAction.Name = "JourneyPrimaryAction"; journeyAction.FocusMode = FocusModeEnum.None;
        journeyAction.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        journeyAction.SetMeta(Ui.BaseFontSizeMeta, 12); journeyAction.AddThemeFontSizeOverride("font_size", Ui.ScaledFont(12)); journeyActions.AddChild(journeyAction);
        journeyUnderstood = Ui.Button("Got it", () => AcknowledgeJourney(journeyObjective?.Stage == "public" ? "public" : journeyHint?.Id ?? ""));
        journeyUnderstood.Name = "JourneyHintUnderstood"; journeyUnderstood.FocusMode = FocusModeEnum.None;
        journeyUnderstood.SetMeta(Ui.BaseFontSizeMeta, 12); journeyUnderstood.AddThemeFontSizeOverride("font_size", Ui.ScaledFont(12)); journeyActions.AddChild(journeyUnderstood);
        nearbyTravelers = Ui.Button("Social · shared world", () => OpenPage("Social"));
        nearbyTravelers.Name = "NearbyTravelerAwareness"; nearbyTravelers.FocusMode = FocusModeEnum.None;
        nearbyTravelers.Text = "Social · 0";
        nearbyTravelers.SetMeta(Ui.BaseFontSizeMeta, 12);
        nearbyTravelers.AddThemeFontSizeOverride("font_size", Ui.ScaledFont(12));
        objectiveHeader.AddChild(nearbyTravelers); objectiveHeader.MoveChild(nearbyTravelers, 1);
        // Preserve the existing visual language and font/DPI scaling, but avoid
        // wasting two rows of large-button padding in the compact objective.
        foreach (var button in new[] { journeyMenu, nearbyTravelers, objectiveToggle, journeyAction, journeyUnderstood })
        {
            foreach (string state in new[] { "normal", "hover", "pressed", "disabled" })
            {
                var style = (StyleBox)button.GetThemeStylebox(state).Duplicate();
                style.ContentMarginTop = style.ContentMarginBottom = 6;
                button.AddThemeStyleboxOverride(state, style);
            }
        }
        progressionBanner = new HudPanel
        {
            Name = "ProgressionFeedback", AnchorLeft = .5f, AnchorRight = .5f,
            OffsetLeft = -230, OffsetRight = 230, OffsetTop = 204, Visible = false,
            MouseFilter = MouseFilterEnum.Ignore
        };
        var words = Ui.Column(progressionBanner); words.MouseFilter = MouseFilterEnum.Ignore;
        progressionTitle = Ui.Label("", 16, Ui.Gold, true); progressionTitle.Name = "ProgressionTitle";
        progressionTitle.MaxLinesVisible = 2; progressionTitle.MouseFilter = MouseFilterEnum.Ignore;
        progressionDetail = Ui.Label("", 13, Ui.Text, true); progressionDetail.Name = "ProgressionChanges";
        progressionDetail.MaxLinesVisible = 4; progressionDetail.MouseFilter = MouseFilterEnum.Ignore;
        words.AddChild(progressionTitle); words.AddChild(progressionDetail); hud.AddChild(progressionBanner);
    }

    private void UpdateNewPlayerHud(Snapshot snapshot)
    {
        FitJourneyHud();
        var self = snapshot.Self;
        if (journeyCharacter != self.Id)
        {
            journeyCharacter = self.Id; pendingGuidance.Clear();
            // A global collapsed-HUD preference from another character must not conceal
            // a completely new character's first objective. Later manual choices are respected.
            if (NewPlayerJourney.Active(self) && !NewPlayerJourney.Seen(self, "movement") && !FirstHourExperience.Marked(self, "movement"))
            {
                objectiveText.Visible = true; firstHourText.Visible = true; objectiveToggle.Text = "−";
            }
        }
        pendingGuidance.RemoveWhere(id => NewPlayerJourney.Seen(self, id));
        journeyObjective = NewPlayerJourney.Recommend(Data, snapshot, World.Loot);
        journeyHint = NewPlayerJourney.NextHint(Data, snapshot, journeyObjective);
        var navigation = NewPlayerJourney.Navigation(Data, self, journeyObjective);
        objectiveText.SetMeta("journey_stage", journeyObjective.Stage);
        objectiveText.SetMeta("journey_target", journeyObjective.TargetId);
        string[] lines = objectiveText.MaxLinesVisible <= 2 ? [journeyObjective.Objective, navigation.Description]
            : objectiveText.MaxLinesVisible == 3 ? [journeyObjective.Title, journeyObjective.Objective, navigation.Description]
            : [journeyObjective.Title, journeyObjective.Objective, navigation.Description, journeyObjective.Reward];
        objectiveText.Text = string.Join("\n", lines.Select(x => CompactJourneyLine(x)));
        objectiveText.TooltipText = journeyObjective.Title + "\n" + journeyObjective.Objective
            + "\nDestination: " + Data.Zone(journeyObjective.Zone).Name + " · " + navigation.Description
            + "\nWhy: " + journeyObjective.Why + "\nWhen finished: " + journeyObjective.Reward;
        string hintText = journeyHint?.Text ?? "";
        if (firstHourText.MaxLinesVisible == 1 && journeyHint is not null)
            hintText = journeyHint.Id switch
            {
                "movement" => "{move_up}/{move_left}/{move_down}/{move_right}: move · {interact}: interact",
                "combat" => "{target_next}: target · {basic_attack}: attack",
                "loot" => "{interact}: loot · {inventory}: backpack",
                "equipment" => "Review the upgrade, then Equip.",
                "socket" => "{inventory}: insert your starter rune.",
                _ => hintText
            };
        firstHourText.Text = journeyHint is null ? "" : (firstHourText.MaxLinesVisible == 1 ? "" : "TIP · ") + JourneyHintText(hintText);
        firstHourText.TooltipText = journeyHint is null ? "" : JourneyHintText(journeyHint.Text);
        firstHourText.SetMeta("guidance_id", journeyHint?.Id ?? "");
        firstHourText.Visible = objectiveText.Visible && journeyHint is not null;
        journeyActions.Visible = objectiveText.Visible;
        bool distant = navigation.Position is { } point && point.Distance(self.Position) > 2.5;
        journeyAction.Text = self.Health <= 0 ? "Recovery shown below"
            : journeyObjective.Zone != self.Zone && navigation.Position is null ? "View entry requirements"
            : distant || navigation.TargetKind == "exit" ? "Walk to objective"
            : journeyObjective.TargetKind == "equipment" ? "Review upgrade"
            : journeyObjective.TargetKind == "creature" ? "Select target"
            : journeyObjective.TargetKind == "npc" ? "Talk"
            : journeyObjective.TargetKind == "loot" ? "Collect loot"
            : journeyObjective.TargetKind == "chest" ? "Open event cache"
            : journeyObjective.Panel == "Crafting" ? "Open crafting"
            : journeyObjective.Panel == "Inventory" ? "Open backpack" : "Open " + journeyObjective.Panel;
        journeyAction.TooltipText = objectiveText.TooltipText;
        journeyAction.Disabled = !Online || self.Health <= 0 || actionBusy;
        journeyUnderstood.Visible = journeyHint is not null || journeyObjective.Stage == "public";
        journeyUnderstood.Text = journeyObjective.Stage == "public" ? "Not now" : "Got it";
        string hintId = journeyObjective.Stage == "public" ? "public" : journeyHint?.Id ?? "";
        journeyUnderstood.Disabled = !Online || self.Health <= 0 || actionBusy || pendingGuidance.Contains(hintId);
        nearbyTravelers.Text = "Social · " + snapshot.Players.Count;
        nearbyTravelers.SetMeta("nearby_count", snapshot.Players.Count);
        nearbyTravelers.TooltipText = "Social [" + JourneyKey("social") + "] · Shared persistent world · " + (snapshot.Players.Count == 0 ? "No other travelers are nearby. Your journey works solo."
            : string.Join(" · ", snapshot.Players.OrderBy(x => x.Position.Distance(self.Position)).Take(3)
                .Select(x => x.Name + " · Lv " + x.Level + " " + Data.Class(x.Class).Name
                    + (snapshot.Party?.Members.Contains(x.Id) == true ? " · Party" : ""))))
            + "\nOpen nearby players, parties, friends and LFG. Chat is optional; grouping is never required for this journey.";
        FitJourneyHud();
    }

    // Reuse the existing card and containers; no duplicate tutorial panel or UI
    // framework. Short logical viewports place the card below the minimap instead
    // of letting the vitals/objective column collide with chat and the hotbar.
    private void FitJourneyHud()
    {
        if (journeyPanel is null || hud.Size.Y <= 0) return;
        bool compact = hud.Size.Y < 760 * Ui.TextScale;
        if (!journeyLayoutReady || compactJourneyLayout != compact)
        {
            compactJourneyLayout = compact; journeyLayoutReady = true;
            Node parent = compact ? hud : journeyHome;
            if (journeyPanel.GetParent() != parent) journeyPanel.Reparent(parent, false);
            journeyPanel.SetAnchorsAndOffsetsPreset(compact ? LayoutPreset.TopRight : LayoutPreset.TopLeft);
        }
        bool shortView = compact && hud.Size.Y < 600;
        bool smallest = compact && hud.Size.Y < 540;
        objectiveText.MaxLinesVisible = shortView ? (smallest || Ui.TextScale > 1.1f ? 2 : 3) : 4;
        firstHourText.MaxLinesVisible = shortView ? 1 : 2;
        firstHourText.AutowrapMode = shortView ? TextServer.AutowrapMode.Off : TextServer.AutowrapMode.WordSmart;
        // Leave a gap beside the unchanged central combat target frame, including
        // a 1280x720 window at 150% content scaling. No font size is reduced.
        float width = compact ? Math.Clamp(hud.Size.X * .5f - 194, 226, 290) : 286;
        journeyPanel.CustomMinimumSize = new Vector2(width, 0);
        objectiveText.CustomMinimumSize = new Vector2(width - 24, 0);
        // A clipped, autowrapped Label can otherwise report zero minimum height
        // to its VBoxContainer. Reserve actual scaled-font rows, not just a text
        // marker that passes tests while the hint is invisible in rendered play.
        float hintLineHeight = firstHourText.GetThemeFont("font").GetHeight(firstHourText.GetThemeFontSize("font_size"));
        float hintHeight = firstHourText.Visible ? MathF.Ceiling(hintLineHeight) * firstHourText.MaxLinesVisible
            + firstHourText.GetThemeConstant("line_spacing") * Math.Max(0, firstHourText.MaxLinesVisible - 1) : 0;
        firstHourText.CustomMinimumSize = new Vector2(width - 24, hintHeight);
        var minimap = hud.FindChild("MinimapPanel", true, false) as HudPanel;
        if (minimap is not null)
        {
            var surface = minimap.GetChildren().OfType<VBoxContainer>().First().GetChildren().OfType<Control>().First();
            // Keep the full map button at every scale; the compact map surface
            // yields space before guidance or combat controls become obscured.
            surface.CustomMinimumSize = new Vector2(172, smallest ? 48 : 122);
            minimap.Size = new Vector2(minimap.Size.X, minimap.GetCombinedMinimumSize().Y);
        }
        if (compact)
        {
            journeyPanel.AnchorLeft = journeyPanel.AnchorRight = 1;
            journeyPanel.OffsetLeft = -width - 16; journeyPanel.OffsetRight = -16;
            journeyPanel.OffsetTop = (minimap?.GetRect().End.Y ?? 194) + 8;
            journeyPanel.Size = new Vector2(width, journeyPanel.GetCombinedMinimumSize().Y);
        }
        // The same page actions remain discoverable through Menu. The old nine-
        // button grid must not occupy the compact objective's screen area.
        if (hud.FindChild("Navigation", true, false) is Control navigation) navigation.Visible = !compact;
        if (notice is not null)
        {
            notice.AnchorLeft = notice.AnchorRight = compact ? 0 : .5f;
            float left = journeyHome.GetGlobalRect().End.X + 12;
            float right = journeyPanel.GetGlobalRect().Position.X - 12;
            float noticeWidth = Math.Max(120, Math.Min(440, right - left));
            notice.OffsetLeft = compact ? (left + right - noticeWidth) / 2 : -300;
            notice.OffsetRight = compact ? notice.OffsetLeft + noticeWidth : 300;
            // Notifications belong above the class meter, never in the attack/
            // interact button row. Both paths preserve the existing scaled font.
            notice.OffsetTop = compact ? -284 : -250; notice.OffsetBottom = compact ? -226 : -215;
            notice.MaxLinesVisible = compact ? 2 : -1;
            notice.TooltipText = notice.Text;
            notice.Visible = !compact || progressionBanner is null || !progressionBanner.Visible;
        }
        if (publicEventText is not null)
        {
            float top = compact ? journeyPanel.GetRect().End.Y + 8 : 202;
            publicEventText.OffsetTop = top; publicEventText.OffsetBottom = top + 60;
            publicEventText.Visible = top + 60 < hud.Size.Y - 96;
            if (pickupFeed is not null)
            {
                pickupFeed.OffsetTop = top + 72;
                pickupFeed.Visible = top + 152 < hud.Size.Y - 96;
            }
        }
        journeyPanel.SetMeta("journey_compact_layout", compact);
    }

    private void BuildJourneyMenu()
    {
        if (page is null || hud.FindChild("Navigation", true, false) is not Control navigation) return;
        page.AddChild(Ui.Label("Follow your current objective; open other systems when you need them.", 14, Ui.Muted, true));
        var panels = new GridContainer { Columns = 2, SizeFlagsHorizontal = SizeFlags.ExpandFill };
        panels.AddThemeConstantOverride("h_separation", 8); panels.AddThemeConstantOverride("v_separation", 8); page.AddChild(panels);
        foreach (var source in navigation.FindChildren("*", "Button", true, false).OfType<Button>().Where(x => x.HasMeta("navigation_page")))
        {
            string destination = source.GetMeta("navigation_page").AsString();
            var action = Ui.Button(destination == "Settings" ? "Settings" : source.Text, () => OpenPage(destination));
            action.SetMeta("menu_page", destination); panels.AddChild(action);
        }
    }

    private async void AcknowledgeJourney(string id)
    {
        if (id == "" || !Online || actionBusy || !pendingGuidance.Add(id)) return;
        var result = await SendAsync(new GameCommand { Kind = "guide_ack", Arg = id }, true);
        if (result?.Ok != true) pendingGuidance.Remove(id);
    }
    private void FollowJourneyObjective()
    {
        if (!GameplayInputAllowed || Snapshot is not { } snapshot) return;
        // Recompute on click: a stale pickup, dead creature, completed quest or expired
        // event cannot turn an old HUD button into an action for the wrong target.
        var objective = NewPlayerJourney.Recommend(Data, snapshot, World.Loot);
        var navigation = NewPlayerJourney.Navigation(Data, snapshot.Self, objective);
        if (objective.Zone != snapshot.Self.Zone && navigation.Position is null) { OpenPage("Map"); return; }
        if (navigation.Position is { } point && (point.Distance(snapshot.Self.Position) > 2.5 || navigation.TargetKind == "exit"))
        {
            SelectTarget(navigation.TargetKind, navigation.TargetId); World.Waypoint = point; WalkTo(point); return;
        }
        if (objective.TargetKind == "creature") { SelectTarget("creature", objective.TargetId); return; }
        if (objective.TargetKind is "npc" or "loot" or "chest" or "node")
        {
            Activate(new WorldTarget(objective.TargetKind, objective.TargetId, objective.Title, objective.Position ?? snapshot.Self.Position)); return;
        }
        if (objective.TargetKind == "event" && snapshot.Events.FirstOrDefault(x => x.Id == objective.TargetId) is { } activity && WorldEventRules.SupportsInteraction(activity))
        {
            Activate(new WorldTarget("event", activity.Id, activity.Name, activity.Position)); return;
        }
        if (objective.TargetKind is "equipment" or "socket") { selectedItem = objective.TargetId; selectedBag = "inventory"; }
        if (objective.TargetKind == "recipe") selectedRecipe = objective.TargetId;
        if (objective.Panel != "") OpenPage(objective.Panel);
    }

    private void ObserveJourneyProgression(Snapshot? previous, Snapshot current)
    {
        if (feedbackCharacter != current.Self.Id || previous is null || previous.Self.Id != current.Self.Id)
        {
            feedbackCharacter = current.Self.Id; progressionQueue.Clear(); displayedProgression.Clear();
            progressionUntil = 0;
            if (progressionBanner is not null) progressionBanner.Visible = false;
            return; // Login/reconnect establishes a baseline, never a fictitious level-up.
        }
        foreach (var moment in ProgressionFeedback.Between(Data, previous.Self, current.Self))
        {
            if (!displayedProgression.Add(moment.Id)) continue;
            if (progressionQueue.Count >= 8) progressionQueue.Dequeue();
            progressionQueue.Enqueue(moment);
        }
        if (displayedProgression.Count > 256) displayedProgression.Clear();
    }
    private void TickJourneyFeedback()
    {
        FitJourneyHud();
        if (progressionBanner is null) return;
        double now = Time.GetTicksMsec() / 1000.0;
        if (now >= progressionUntil)
        {
            if (!progressionQueue.TryDequeue(out var moment)) { progressionBanner.Visible = false; return; }
            progressionTitle.Text = moment.Title;
            progressionDetail.Text = moment.Detail;
            progressionBanner.TooltipText = moment.Title + "\n" + moment.Detail;
            progressionBanner.SetMeta("progression_kind", moment.Kind);
            progressionUntil = now + 6;
        }
        float left = journeyHome.GetGlobalRect().End.X + 12;
        float right = (compactJourneyLayout ? journeyPanel.GetGlobalRect().Position.X : hud.Size.X - 306) - 12;
        float width = Math.Clamp(right - left, 160, 460);
        progressionBanner.AnchorLeft = progressionBanner.AnchorRight = 0;
        progressionBanner.OffsetLeft = (left + right - width) / 2;
        progressionBanner.OffsetRight = progressionBanner.OffsetLeft + width;
        float top = targetFrame.Visible ? Math.Max(204, targetFrame.GetRect().End.Y + 10) : 158;
        progressionBanner.OffsetTop = Math.Min(top, Math.Max(204, hud.Size.Y - 380));
        progressionBanner.Visible = Snapshot is not null && !frontend.Visible;
    }
}
