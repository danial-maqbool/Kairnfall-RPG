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
        foreach (float scale in new[] { 1f, 1.25f, 1.5f })
        foreach (double textScale in new[] { 1d, 1.25d })
        foreach (var size in new[] { new Vector2I(1024, 720), new Vector2I(1280, 720), new Vector2I(1920, 1080) })
        {
            // The existing minimum-size contract uses 1024x720 at native scale.
            // Higher DPI follows the repository's supported 1280/1920 matrix.
            if (size.X == 1024 && scale != 1) continue;
            owner.GetWindow().Size = size; owner.GetWindow().ContentScaleSize = size; owner.GetWindow().ContentScaleFactor = scale;
            Call(game, "ApplyUiTextScale", textScale, false);
            await Frame(owner); await Frame(owner);
            var snapshot = realm.Snapshot(player.Id); game.World.Accept(new TransportPacket { Snapshot = snapshot });
            Call(game, "UpdateHud"); await Frame(owner); await Frame(owner);
            Call(game, "FitJourneyHud"); Call(game, "UpdateHud"); await Frame(owner); await Frame(owner);
            var objective = Field<Label>(game, "objectiveText"); var hint = Field<Label>(game, "firstHourText");
            var action = Field<Button>(game, "journeyAction"); var social = Field<Button>(game, "nearbyTravelers");
            var chat = Field<HudPanel>(game, "chatFrame");
            check(objective.IsVisibleInTree() && objective.GetMeta("journey_stage").AsString() == "quest_offer", "A fresh native HUD exposes the real first objective at " + size);
            bool legacyPreview = objective.TooltipText.Contains(data.Quest("main_01").Name, StringComparison.Ordinal)
                && objective.TooltipText.Contains(data.Item("sealed_letter").Name, StringComparison.Ordinal);
            bool openingPreview = objective.TooltipText.Contains("Medicine for the Road", StringComparison.Ordinal)
                && objective.TooltipText.Contains("Rare class weapon", StringComparison.Ordinal);
            check(legacyPreview || openingPreview,
                "Objective details preserve the real quest and deterministic reward preview at " + size);
            check(objective.MouseFilter == Control.MouseFilterEnum.Pass && hint.MouseFilter == Control.MouseFilterEnum.Pass, "Full guidance details accept tooltip hover at " + size);
            check(hint.GetMeta("guidance_id").AsString() == "movement" && !hint.Text.Contains('{'), "Movement guidance resolves actual input bindings at " + size);
            float fontHeight = hint.GetThemeFont("font").GetHeight(hint.GetThemeFontSize("font_size"));
            check(hint.IsVisibleInTree() && hint.GetGlobalRect().Size.Y >= MathF.Ceiling(fontHeight) && hint.GetVisibleLineCount() > 0,
                "The movement tip has readable rendered glyph height, not just a presentation marker at " + size + " / " + scale + " / " + textScale);
            check(Field<Button>(game, "journeyUnderstood").IsVisibleInTree() && hint.IsVisibleInTree() && hint.Text.Length > 0,
                "A fresh character is asked to acknowledge only a visible, nonempty explanation at " + size + " / " + scale + " / " + textScale);
            check(action.IsVisibleInTree() && !action.GetGlobalRect().Intersects(chat.GetGlobalRect()), "The journey action does not overlap chat at " + size);
            var card = Field<HudPanel>(game, "journeyPanel");
            var viewport = owner.GetViewport().GetVisibleRect();
            var minimap = game.FindChildren("MinimapPanel", "Control", true, false).OfType<Control>().Single();
            var controls = game.FindChildren("CombatControls", "Control", true, false).OfType<Control>().Single();
            GD.Print($"NEW_PLAYER_LAYOUT: {size} dpi={scale} text={textScale} viewport={viewport} objective={card.GetGlobalRect()} hint={hint.GetGlobalRect()} controls={controls.GetGlobalRect()} chat={chat.GetGlobalRect()}");
            check(card.GetGlobalRect().Encloses(hint.GetGlobalRect()) && !hint.GetGlobalRect().Intersects(action.GetGlobalRect()),
                "Guidance is inside its card and clear of the objective action at " + size + " / " + scale + " / " + textScale);
            check(!card.GetGlobalRect().Intersects(controls.GetGlobalRect()),
                "The objective and tip cannot cover attack, interaction, target or dash buttons at " + size + " / " + scale + " / " + textScale);
            check(!card.GetGlobalRect().Intersects(chat.GetGlobalRect()), "The objective card avoids chat at " + size + " / " + scale + " / " + textScale);
            check(viewport.Encloses(card.GetGlobalRect()) && viewport.Encloses(action.GetGlobalRect()), "The objective and its action remain fully contained at " + size + " / " + scale + " / " + textScale);
            check(!card.GetGlobalRect().Intersects(minimap.GetGlobalRect()), "The objective card avoids the minimap at " + size);
            check(Field<Button[]>(game, "hotbarButtons").All(button => !card.GetGlobalRect().Intersects(button.GetGlobalRect())), "The objective card avoids the hotbar at " + size);
            var navigation = game.FindChildren("Navigation", "Control", true, false).OfType<Control>().Single();
            check(!navigation.IsVisibleInTree() || !card.GetGlobalRect().Intersects(navigation.GetGlobalRect()), "The objective avoids the legacy navigation grid at " + size);
            check(Field<Button>(game, "journeyMenu").IsVisibleInTree(), "Every game panel stays discoverable through Menu at " + size);
            Call(game, "Notify", "Welcome to Wayfarer's Rest · Your current objective shows the next step.", false);
            Call(game, "FitJourneyHud"); await Frame(owner); await Frame(owner);
            var notification = Field<Label>(game, "notice");
            var meter = game.FindChildren("ClassResourceHud", "Control", true, false).OfType<Control>().Single();
            check(notification.IsVisibleInTree() && viewport.Encloses(notification.GetGlobalRect())
                && !notification.GetGlobalRect().Intersects(controls.GetGlobalRect())
                && !notification.GetGlobalRect().Intersects(Field<Label>(game, "interactionHint").GetGlobalRect())
                && !notification.GetGlobalRect().Intersects(meter.GetGlobalRect()),
                "Welcome and reward notifications remain readable above combat controls at " + size + " / " + scale + " / " + textScale);
            var foe = snapshot.Creatures.First(x => x.Health > 0 && x.Owner == "");
            Call(game, "SelectTarget", "creature", foe.Id); Call(game, "UpdateHud"); await Frame(owner); await Frame(owner);
            check(!card.GetGlobalRect().Intersects(Field<HudPanel>(game, "targetFrame").GetGlobalRect()), "The objective does not cover the combat target at " + size + " / " + scale);
            Call(game, "SelectTarget", "", ""); Call(game, "UpdateHud");
            check(social.GetMeta("nearby_count").AsInt32() == 0 && social.IsVisibleInTree(), "Multiplayer discovery remains visible on an empty server at " + size);
            check(owner.GetViewport().GetVisibleRect().Encloses(social.GetGlobalRect()), "Nearby-player discovery remains inside the supported viewport at " + size);
        }
        owner.GetWindow().Size = new Vector2I(1920, 1080); owner.GetWindow().ContentScaleSize = new Vector2I(1920, 1080); owner.GetWindow().ContentScaleFactor = 1;
        Call(game, "ApplyUiTextScale", 1d, false); await Frame(owner); await Frame(owner);
        Call(game, "OpenPage", "Menu"); await Frame(owner);
        var menuPages = game.FindChildren("*", "Button", true, false).OfType<Button>().Where(x => x.HasMeta("menu_page")).Select(x => x.GetMeta("menu_page").AsString()).ToHashSet(StringComparer.Ordinal);
        check(new[] { "Inventory", "Character", "Skills", "Abilities", "Quests", "Hunting", "Crafting", "Social", "Settings" }.All(menuPages.Contains), "The compact Menu preserves every existing navigation destination");
        Call(game, "ClosePage"); await Frame(owner);
        player.CompletedQuests.Add("main_01"); player.Zone = "kingsmeadow"; player.Position = data.Zone(player.Zone).Spawn;
        var active = realm.Snapshot(player.Id);
        active.Events.Add(new WorldEvent { Id = "native-introduction", Kind = "treasure_surge", Name = WorldEventRules.Name("treasure_surge"),
            Zone = player.Zone, Position = player.Position, Status = "active", StageEnds = active.Time + 100, Ends = active.Time + 100, Goal = 4 });
        game.World.Accept(new TransportPacket { Snapshot = active }); Call(game, "UpdateHud"); Call(game, "UpdatePublicEventHud");
        await Frame(owner); await Frame(owner);
        var activity = Field<Label>(game, "publicEventText");
        Call(game, "FitJourneyHud"); await Frame(owner);
        check(activity.IsVisibleInTree() && activity.Text != "" && !activity.GetGlobalRect().Intersects(Field<Label>(game, "location").GetGlobalRect()),
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
        check(Field<Label>(game, "firstHourText").Text == "" && !Field<Label>(game, "firstHourText").Visible,
            "Historical characters do not receive the new-player hint sequence");
    }
}
