using Godot;
using Kairnfall.Core;
using System.Text.RegularExpressions;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private HBoxContainer journeyActions = null!;
    private Button journeyAction = null!, journeyUnderstood = null!, nearbyTravelers = null!;
    private HudPanel progressionBanner = null!;
    private Label progressionTitle = null!, progressionDetail = null!;
    private JourneyObjective? journeyObjective;
    private JourneyHint? journeyHint;
    private string journeyCharacter = "", feedbackCharacter = "";
    private readonly HashSet<string> pendingGuidance = new(StringComparer.Ordinal);
    private readonly HashSet<string> displayedProgression = new(StringComparer.Ordinal);
    private readonly Queue<ProgressionMoment> progressionQueue = new();
    private double progressionUntil;

    private static string CompactJourneyLine(string text, int length = 36)
        => text.Length <= length ? text : text[..(length - 1)] + "…";
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
        objectiveText.Name = "RecommendedObjective";
        objectiveText.AddThemeFontSizeOverride("font_size", 13);
        objectiveText.MaxLinesVisible = 4;
        firstHourText.MaxLinesVisible = 2;
        journeyActions = Ui.Row(objectiveColumn); journeyActions.Name = "JourneyActions";
        journeyAction = Ui.Button("Walk to objective", FollowJourneyObjective);
        journeyAction.Name = "JourneyPrimaryAction"; journeyAction.FocusMode = FocusModeEnum.None;
        journeyAction.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        journeyAction.AddThemeFontSizeOverride("font_size", 12); journeyActions.AddChild(journeyAction);
        journeyUnderstood = Ui.Button("Got it", () => AcknowledgeJourney(journeyObjective?.Stage == "public" ? "public" : journeyHint?.Id ?? ""));
        journeyUnderstood.Name = "JourneyHintUnderstood"; journeyUnderstood.FocusMode = FocusModeEnum.None;
        journeyUnderstood.AddThemeFontSizeOverride("font_size", 12); journeyActions.AddChild(journeyUnderstood);
        nearbyTravelers = Ui.Button("Social · shared world", () => OpenPage("Social"));
        nearbyTravelers.Name = "NearbyTravelerAwareness"; nearbyTravelers.FocusMode = FocusModeEnum.None;
        nearbyTravelers.AnchorLeft = nearbyTravelers.AnchorRight = 1;
        nearbyTravelers.OffsetLeft = -276; nearbyTravelers.OffsetRight = -16;
        nearbyTravelers.OffsetTop = 202; nearbyTravelers.OffsetBottom = 230;
        nearbyTravelers.AddThemeFontSizeOverride("font_size", 12); hud.AddChild(nearbyTravelers);
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
        progressionDetail.MaxLinesVisible = 3; progressionDetail.MouseFilter = MouseFilterEnum.Ignore;
        words.AddChild(progressionTitle); words.AddChild(progressionDetail); hud.AddChild(progressionBanner);
    }

    private void UpdateNewPlayerHud(Snapshot snapshot)
    {
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
        objectiveText.Text = string.Join("\n", new[] { journeyObjective.Title, journeyObjective.Objective, navigation.Description, journeyObjective.Reward }
            .Select(x => CompactJourneyLine(x)));
        objectiveText.TooltipText = journeyObjective.Title + "\n" + journeyObjective.Objective
            + "\nDestination: " + Data.Zone(journeyObjective.Zone).Name + " · " + navigation.Description
            + "\nWhy: " + journeyObjective.Why + "\nWhen finished: " + journeyObjective.Reward;
        firstHourText.Text = journeyHint is null ? "" : "TIP · " + JourneyHintText(journeyHint.Text);
        firstHourText.TooltipText = firstHourText.Text;
        firstHourText.SetMeta("guidance_id", journeyHint?.Id ?? "");
        journeyActions.Visible = objectiveText.Visible;
        bool distant = navigation.Position is { } point && point.Distance(self.Position) > 2.5;
        journeyAction.Text = self.Health <= 0 ? "Recovery shown below"
            : journeyObjective.Zone != self.Zone && navigation.Position is null ? "View entry requirements"
            : distant ? "Walk to objective"
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
        nearbyTravelers.Text = "Social [" + JourneyKey("social") + "] · " + snapshot.Players.Count + " nearby";
        nearbyTravelers.SetMeta("nearby_count", snapshot.Players.Count);
        nearbyTravelers.TooltipText = "Shared persistent world · " + (snapshot.Players.Count == 0 ? "No other travelers are nearby. Your journey works solo."
            : string.Join(" · ", snapshot.Players.OrderBy(x => x.Position.Distance(self.Position)).Take(3)
                .Select(x => x.Name + " · Lv " + x.Level + " " + Data.Class(x.Class).Name
                    + (snapshot.Party?.Members.Contains(x.Id) == true ? " · Party" : ""))))
            + "\nOpen nearby players, parties, friends and LFG. Chat is optional; grouping is never required for this journey.";
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
        if (navigation.Position is { } point && point.Distance(snapshot.Self.Position) > 2.5)
        {
            SelectTarget(navigation.TargetKind, navigation.TargetId); WalkTo(point); return;
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
        float top = targetFrame.Visible ? Math.Max(204, targetFrame.GetRect().End.Y + 10) : 158;
        progressionBanner.OffsetTop = Math.Min(top, Math.Max(204, hud.Size.Y - 380));
        progressionBanner.Visible = Snapshot is not null && !frontend.Visible;
    }
}
