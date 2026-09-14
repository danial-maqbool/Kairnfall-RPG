using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

internal static class NewPlayerJourneyUiChecks
{
    private static object? Call(GameRoot game, string name, params object?[] arguments)
        => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, arguments);
    private static T Field<T>(GameRoot game, string name)
        => (T)typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
    private static async Task Frame(Node owner) => await owner.ToSignal(owner.GetTree(), SceneTree.SignalName.ProcessFrame);

    internal static async Task Run(Node owner, GameRoot game, Catalog data, Action<bool, string> check)
    {
        var realm = new RealmEngine(data); var player = realm.CreateCharacter("journey-native", "Native Newcomer", "vanguard", new());
        realm.Active.Add(player.Id);
        foreach (var size in new[] { new Vector2I(1280, 720), new Vector2I(1920, 1080) })
        {
            owner.GetWindow().Size = size; await Frame(owner); await Frame(owner);
            var snapshot = realm.Snapshot(player.Id); game.World.Accept(new TransportPacket { Snapshot = snapshot });
            Call(game, "UpdateHud"); await Frame(owner); await Frame(owner);
            var objective = Field<Label>(game, "objectiveText"); var hint = Field<Label>(game, "firstHourText");
            var action = Field<Button>(game, "journeyAction"); var social = Field<Button>(game, "nearbyTravelers");
            var chat = Field<HudPanel>(game, "chatFrame");
            check(objective.IsVisibleInTree() && objective.GetMeta("journey_stage").AsString() == "quest_offer", "A fresh native HUD exposes the real first objective at " + size);
            check(objective.TooltipText.Contains(data.Quest("main_01").Name, StringComparison.Ordinal) && objective.TooltipText.Contains(data.Item("sealed_letter").Name, StringComparison.Ordinal),
                "Objective details preserve the real quest and reward preview at " + size);
            check(hint.GetMeta("guidance_id").AsString() == "movement" && !hint.Text.Contains('{'), "Movement guidance resolves actual input bindings at " + size);
            check(action.IsVisibleInTree() && !action.GetGlobalRect().Intersects(chat.GetGlobalRect()), "The journey action does not overlap chat at " + size);
            check(objective.GetGlobalRect().End.Y <= chat.GetGlobalRect().Position.Y, "The compact objective stays above chat at " + size);
            check(social.GetMeta("nearby_count").AsInt32() == 0 && social.IsVisibleInTree(), "Multiplayer discovery remains visible on an empty server at " + size);
            check(owner.GetViewport().GetVisibleRect().Encloses(social.GetGlobalRect()), "Nearby-player discovery remains inside the supported viewport at " + size);
        }
        player.CompletedQuests.Add("main_01"); player.Zone = "kingsmeadow"; player.Position = data.Zone(player.Zone).Spawn;
        var active = realm.Snapshot(player.Id);
        active.Events.Add(new WorldEvent { Id = "native-introduction", Kind = "treasure_surge", Name = WorldEventRules.Name("treasure_surge"),
            Zone = player.Zone, Position = player.Position, Status = "active", StageEnds = active.Time + 100, Ends = active.Time + 100, Goal = 4 });
        game.World.Accept(new TransportPacket { Snapshot = active }); Call(game, "UpdateHud"); Call(game, "UpdatePublicEventHud");
        await Frame(owner); await Frame(owner);
        var activity = Field<Label>(game, "publicEventText");
        check(activity.Text != "" && !activity.GetGlobalRect().Intersects(Field<Label>(game, "locationText").GetGlobalRect()),
            "Public activity does not overlap the location heading");
        check(Field<Button>(game, "journeyUnderstood").Visible && Field<Label>(game, "objectiveText").GetMeta("journey_stage").AsString() == "public",
            "The optional event has a visible return-to-journey action");
        Call(game, "ObserveJourneyProgression", null, active);
        Call(game, "TickJourneyFeedback");
        check(!Field<HudPanel>(game, "progressionBanner").Visible, "Login does not fabricate a level-up banner");
        var gained = Wire.Copy(active); gained.Self.SkillXp[data.Skills[0].Id] = Progression.PlayerThreshold(2);
        Call(game, "ObserveJourneyProgression", active, gained); Call(game, "TickJourneyFeedback");
        await Frame(owner); await Frame(owner);
        check(Field<HudPanel>(game, "progressionBanner").Visible && Field<HudPanel>(game, "progressionBanner").GetMeta("progression_kind").AsString() == "level",
            "A real progression difference produces a non-modal level-up banner");
        var old = Wire.Copy(active); old.Self.Discoveries.Remove(NewPlayerJourney.EligibleKey);
        game.World.Accept(new TransportPacket { Snapshot = old }); Call(game, "UpdateHud");
        check(Field<Label>(game, "firstHourText").Text == "", "Historical characters do not receive the new-player hint sequence");
    }
}
