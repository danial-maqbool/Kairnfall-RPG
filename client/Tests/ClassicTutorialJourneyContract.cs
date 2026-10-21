using Godot;
using Kairnfall.Core;
using System.Reflection;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Offline accepted-state presentation fixtures; no human pacing or live realm claim.</summary>
public partial class ClassicTutorialJourneyContract : Node
{
    private int checks;
    private static FieldInfo Member(string name) => typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!;
    private static T Field<T>(GameRoot game, string name) => (T)Member(name).GetValue(game)!;
    private static object? Call(GameRoot game, string name, params object?[] args)
        => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private static string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
    private void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS TUTORIAL JOURNEY: " + message);
    }
    private static void Accept(GameRoot game, Snapshot snapshot)
    {
        game.World.Accept(new TransportPacket { Snapshot = snapshot }); Call(game, "UpdateHud");
    }
    public override async void _Ready()
    {
        GameRoot? game = null;
        try
        {
            Check(ProjectSettings.GlobalizePath("user://").Contains("Kairnfall-Classic-QA", StringComparison.Ordinal), "Settings stay isolated");
            game = new GameRoot { LayoutMode = 1 }; AddChild(game); game.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);
            game.SetProcess(false); await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            var ordinaryData = game.Data; var data = Wire.Copy(ordinaryData); ClassicTutorialContent.Enable(data);
            typeof(GameRoot).GetProperty("Data")!.SetValue(game, data); game.World.Data = data;
            var realm = new RealmEngine(data); var player = realm.CreateCharacter("journey-glade", "Glade Guide", "vanguard", new());
            player.Position = new(14.5, 13.5); player.Facing = new(0, -1); realm.Active.Add(player.Id); realm.Tick(.1);
            var snapshot = realm.Snapshot(player.Id); string before = Json(snapshot);
            for (int read = 0; read < 8; read++)
                Check(ClassicTutorialJourneyRules.Recommend(data, snapshot) is { TargetKind: "classic_site", TargetId: "classic_first_sign" }, "Fresh accepted progress recommends the First Steps sign");
            Check(Json(snapshot) == before, "Repeated recommendations cannot award XP, items, Food or completed milestones");
            Field<Control>(game, "frontend").Hide(); Accept(game, snapshot);
            Check(Field<Label>(game, "objectiveText").GetMeta("journey_target").AsString() == "classic_first_sign"
                && Field<Button>(game, "journeyAction").Text == "Select object" && !Field<Button>(game, "journeyUnderstood").Visible,
                "Tutorial HUD uses its optional object objective without a gameplay or hint acknowledgement action");
            var route = Field<List<Point>>(game, "route"); route.Add(new(20.5, 12.5)); game.World.Waypoint = new(20.5, 12.5);
            var objective = ClassicTutorialJourneyRules.Recommend(data, snapshot)!;
            Check((bool)Call(game, "FollowClassicJourneyObjective", snapshot, objective)!
                && Field<string>(game, "selectedTarget") == "classic_first_sign" && route.Count == 0 && game.World.Waypoint is null
                && Field<string>(game, "lastNoticeText").Contains("adjacent", StringComparison.Ordinal), "Object guidance selects and explains facing without routing into a solid sign");
            Check(Json(snapshot) == before && !player.ClassicTutorial!.Completed.Contains("read_sign"), "Selecting guidance cannot change authoritative position, facing or earn a sign milestone");
            var result = realm.Execute(player.Id, new GameCommand { Kind = "classic_interact", Target = "classic_first_sign", Sequence = 1 });
            Check(result.Ok && ClassicTutorialJourneyRules.Recommend(data, realm.Snapshot(player.Id))?.TargetId == "classic_fountain", "Only the real accepted sign action advances its lesson");

            // Detached accepted-state variants isolate recommendation boundaries;
            // they are not fabricated gameplay credit in the realm above.
            snapshot = realm.Snapshot(player.Id);
            snapshot.Self.ClassicTutorial!.Completed.UnionWith(new[] { "fountain", "wood", "stone", "food" });
            var recipe = data.Recipe("classic_make_pickaxe");
            objective = ClassicTutorialJourneyRules.Recommend(data, snapshot)!;
            Check(objective.TargetKind == "node" && objective.Objective.Contains("0/10", StringComparison.Ordinal), "Pickaxe guidance derives the Stone deficit from current inventory and recipe");
            var changedRecipe = Wire.Copy(data); changedRecipe.Recipe(recipe.Id).Ingredients["classic_stone"] = 13;
            Check(ClassicTutorialJourneyRules.Recommend(changedRecipe, snapshot)!.Objective.Contains("0/13", StringComparison.Ordinal), "Guidance follows actual recipe amounts rather than fixed lesson counts");
            foreach (var cost in recipe.Ingredients) Items.Add(snapshot.Self.Inventory, Items.Create(data, cost.Key, cost.Value), data);
            before = Json(snapshot); objective = ClassicTutorialJourneyRules.Recommend(data, snapshot)!;
            Check(objective.TargetKind == "recipe" && objective.TargetId == recipe.Id, "Ready materials lead to the real pickaxe recipe without crafting automatically");
            Member("classicRecipeSearch").SetValue(game, "unrelated prior search"); Accept(game, snapshot);
            Check(Field<string>(game, "classicRecipeSearch") == "unrelated prior search", "Reading the lesson preserves an existing recipe search");
            Call(game, "FollowClassicJourneyObjective", snapshot, objective);
            Check(Field<string>(game, "selectedRecipe") == recipe.Id && Field<string>(game, "classicRecipeSearch") == ""
                && Field<string>(game, "currentPage") == "Crafting" && Json(snapshot) == before, "A deliberate recipe click reveals the matching recipe without consuming materials or crafting");
            Call(game, "ClosePage"); snapshot.Self.ClassicTutorial.Completed.Add("pickaxe");
            Check(ClassicTutorialJourneyRules.Recommend(data, snapshot) is { TargetKind: "creature" }, "Accepted pickaxe milestone leads to a living real rat");
            var combatLesson = ClassicTutorialJourneyRules.Recommend(data, snapshot)!;
            Check(combatLesson.Why.Contains("repeat attacks", StringComparison.Ordinal)
                && combatLesson.Why.Contains("hold Space", StringComparison.Ordinal)
                && combatLesson.Why.Contains("stops", StringComparison.Ordinal),
                "Combat guidance explains click repetition, the Space alternative and how to stop it");
            snapshot.Creatures.Where(x => x.Template == "field_rat").ToList().ForEach(x => x.Health = 0);
            Check(ClassicTutorialJourneyRules.Recommend(data, snapshot)!.TargetKind != "creature", "A dead or unavailable rat cannot become a fake live target");
            var fire = data.Recipe("classic_make_fire");
            foreach (var cost in fire.Ingredients)
            {
                int missing = cost.Value - Items.Count(snapshot.Self, cost.Key);
                if (missing > 0) Items.Add(snapshot.Self.Inventory, Items.Create(data, cost.Key, missing), data);
            }
            objective = ClassicTutorialJourneyRules.Recommend(data, snapshot)!;
            Check(objective.TargetId == fire.Id && objective.Why.Contains("clear wilderness", StringComparison.Ordinal), "Fire guidance explains the actual recipe and placement requirement");
            Accept(game, snapshot); before = Json(snapshot); string placement = Field<string>(game, "placement");
            Call(game, "FollowClassicJourneyObjective", snapshot, objective);
            Check(Field<string>(game, "selectedRecipe") == fire.Id && Field<string>(game, "placement") == placement && Json(snapshot) == before, "Reviewing Fire cannot begin placement, build or award its milestone");
            Call(game, "ClosePage"); snapshot.Self.ClassicTutorial.Completed.UnionWith(new[] { "fire", "rat" });
            Check(ClassicTutorialJourneyRules.Recommend(data, snapshot) is { TargetKind: "exit", TargetId: "classic_glade_to_wayfarers" }, "Completed optional lessons lead to the existing eastern exit");
            snapshot.Self.ClassicTutorial.Completed.Remove("food");
            objective = ClassicTutorialJourneyRules.Recommend(data, snapshot)!; before = Json(snapshot); Accept(game, snapshot);
            Call(game, "FollowClassicJourneyObjective", snapshot, objective);
            Check(objective.TargetKind == "inventory_item" && Field<string>(game, "selectedItem") == objective.TargetId && Json(snapshot) == before, "Food guidance selects an actual owned edible without consuming it or changing Food");
            Call(game, "ClosePage");
            snapshot.Self.Zone = OpeningJourney.Home; snapshot.Self.Position = data.Zone(OpeningJourney.Home).Spawn;
            Check(ClassicTutorialJourneyRules.Recommend(data, snapshot) is null, "Leaving First Glade restores ordinary-world guidance");
            Accept(game, snapshot);
            Check(Json(Call(game, "SessionJourneyObjective", snapshot)) == Json(NewPlayerJourney.Recommend(data, snapshot, game.World.Loot)), "Session guidance preserves the ordinary world's existing recommendation");
            snapshot.Self.Zone = ClassicTutorialContent.ZoneId; snapshot.Self.Health = 0;
            Check(ClassicTutorialJourneyRules.Recommend(data, snapshot) is null, "Death recovery takes priority over optional lessons");
            snapshot.Self.Health = 100;
            Check(ClassicTutorialJourneyRules.Recommend(ordinaryData, snapshot) is null, "Character progress alone cannot opt an ordinary catalog into tutorial guidance");
            snapshot.Self.ClassicTutorial = null;
            Check(ClassicTutorialJourneyRules.Recommend(data, snapshot) is null, "Catalog mode alone cannot opt an ordinary character into tutorial guidance");
            await NativeTestLifetime.ReleaseSceneAsync(this, game); game = null;
            GD.Print($"CLASSIC_TUTORIAL_JOURNEY_CONTRACT: {checks} checks passed. Offline native fixture; no live realm or human pacing approval."); GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CLASSIC_TUTORIAL_JOURNEY_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this, game);
            GetTree().Quit(1);
        }
    }
}
