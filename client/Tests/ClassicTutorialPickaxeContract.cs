using Godot;
using Kairnfall.Core;
using System.Globalization;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>
/// Opt-in offline art fixture. The held tool is earned in a detached authority;
/// pose previews are presentation only, not live combat or human art acceptance.
/// </summary>
public partial class ClassicTutorialPickaxeContract : Node
{
    internal const string Pickaxe = "classic_stone_pickaxe", HeldKey = "equipment/" + Pickaxe;
    internal static readonly string[] Actions = ["idle", "walk", "attack", "cast", "hit", "death", "interact", "craft", "run", "bow_attack", "crossbow_attack"];
    internal static readonly string[] Directions = ["south", "west", "east", "north"];
    private static readonly Point[] Steps = [new(1, 0), new(-1, 0), new(0, 1), new(0, -1)];
    private int checks, comparedPixels, atlasAddresses, heldAddresses, captures;

    private static string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
    private void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS TUTORIAL PICKAXE: " + message);
    }
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);

    private void Execute(RealmEngine realm, string id, GameCommand command)
    {
        command.Sequence = realm.Player(id).LastAction + 1;
        Check(Guid.TryParseExact(command.RequestId, "N", out _), "Command has a fresh protocol GUID: " + command.Kind);
        var result = realm.Execute(id, command);
        Check(result.Ok && result.RequestId == command.RequestId,
            "Detached authority accepted " + command.Kind + ": " + result.Message);
        if (command.Kind != "move")
            Check(realm.Player(id).LastAction == command.Sequence, "Accepted action advances its real sequence: " + command.Kind);
    }

    private void Step(RealmEngine realm, string id, Point target)
    {
        var player = realm.Player(id);
        var direction = GridMovementRules.Cardinal(target.Add(player.Position.Scale(-1)));
        Check(direction != default && GridMovementRules.Next(player.Position, direction).Distance(target) < .000001,
            "Route uses a single cardinal tile intention");
        Execute(realm, id, new GameCommand { Kind = "move", Arg = GridMovementRules.Step, X = direction.X, Y = direction.Y });
        for (int tick = 0; tick < 25 && realm.Player(id).Position.Distance(target) > .000001; tick++) realm.Tick(.1);
        Check(realm.Player(id).Position.Distance(target) < .000001
            && realm.Player(id).Zone == ClassicTutorialContent.ZoneId && realm.Player(id).Health > 0,
            "Real movement reaches the authored tile without teleporting or dying");
    }

    private void Approach(RealmEngine realm, string id, WorldNode node)
    {
        var player = realm.Player(id); var zone = realm.Data.Zone(player.Zone);
        var approaches = new List<(Point Adjacent, List<Point> Path)>();
        foreach (var facing in Steps)
        {
            var adjacent = node.Position.Add(facing.Scale(-1));
            var entry = node.Position.Add(facing.Scale(-2));
            if (!WorldMap.Fits(zone, entry) || !WorldMap.Fits(zone, adjacent)
                || !WorldMap.LineOfSight(zone, entry, adjacent) || !WorldMap.LineOfSight(zone, adjacent, node.Position)) continue;
            var path = WorldMap.FindPath(zone, player.Position, entry, 4096);
            if (path.Count > 0 || player.Position.Distance(entry) < .000001) approaches.Add((adjacent, path));
        }
        Check(approaches.Count > 0, "A reachable cardinal resource approach exists: " + node.Id);
        var chosen = approaches.OrderBy(x => x.Path.Count).First();
        foreach (var tile in chosen.Path) Step(realm, id, tile);
        Step(realm, id, chosen.Adjacent);
        Check(ClassicTutorialContent.FacingAdjacent(realm.Player(id), node.Position),
            "Real tile movement faces the adjacent resource: " + node.Id);
    }

    private void GatherIngredients(RealmEngine realm, string id, RecipeDef recipe)
    {
        foreach (var ingredient in recipe.Ingredients)
        {
            var node = realm.State.Nodes.Values.Where(x => x.Zone == ClassicTutorialContent.ZoneId
                && x.Template.StartsWith("classic_", StringComparison.Ordinal)
                && realm.Data.Resource(x.Template).Item == ingredient.Key)
                .OrderBy(x => x.Position.Distance(realm.Player(id).Position)).FirstOrDefault();
            Check(node is not null, "The real recipe ingredient has an authored resource: " + ingredient.Key);
            Approach(realm, id, node!);
            int gathers = 0;
            while (Items.Count(realm.Player(id), ingredient.Key) < ingredient.Value && gathers++ < 40)
            {
                // Advance only the authority's normal clock; do not rewrite ready times,
                // cooldowns, stamina, skill XP, Food, resource quantities or positions.
                double staminaCost = ToolRules.StaminaCost(null);
                int waited = 0;
                while (waited++ < 3100 && (node!.ReadyAt > realm.State.Time
                    || realm.Player(id).Cooldowns.GetValueOrDefault("gather") > realm.State.Time
                    || realm.Player(id).Stamina < staminaCost)) realm.Tick(.1);
                Check(node!.ReadyAt <= realm.State.Time
                    && realm.Player(id).Cooldowns.GetValueOrDefault("gather") <= realm.State.Time
                    && realm.Player(id).Stamina >= staminaCost,
                    "Resource recovery, action cooldown and stamina recover through normal ticks");
                int before = Items.Count(realm.Player(id), ingredient.Key);
                Execute(realm, id, new GameCommand { Kind = "gather", Target = node.Id });
                Check(Items.Count(realm.Player(id), ingredient.Key) > before,
                    "Accepted gathering grants the real ingredient: " + ingredient.Key);
            }
            Check(Items.Count(realm.Player(id), ingredient.Key) >= ingredient.Value,
                "Normal gathering supplies the current recipe amount: " + ingredient.Key);
        }
    }

    private void CheckImportedSheet(PixelAssets assets, string key, int height)
    {
        var texture = assets.Texture(key); var size = new Vector2I(512, height);
        Check(texture is not null && texture.GetWidth() == size.X && texture.GetHeight() == size.Y,
            "Runtime held sheet has eight native 64px frames and all direction rows: " + key);
        using var source = new Image();
        Check(source.LoadPngFromBuffer(Godot.FileAccess.GetFileAsBytes("res://Assets/" + key + ".png")) == Error.Ok
            && source.GetSize() == size, "Decode the current source sheet: " + key);
        using var imported = texture!.GetImage();
        Check(imported is not null && imported.GetSize() == size, "Decode the actual runtime import: " + key);
        var visible = new int[8 * height / 64]; string? mismatch = null;
        for (int y = 0; y < height; y++)
            for (int x = 0; x < 512; x++)
            {
                var expected = source.GetPixel(x, y); var actual = imported!.GetPixel(x, y);
                comparedPixels++;
                // Godot may fix RGB at fully transparent borders. Alpha is exact
                // everywhere, and every visible pixel must retain all four channels.
                if ((expected.A != actual.A || expected.A > 0 && expected != actual) && mismatch is null)
                    mismatch = $"{key} pixel ({x},{y}) source={expected} imported={actual}";
                if (expected.A > 0) visible[(y / 64) * 8 + x / 64]++;
            }
        Check(mismatch is null, "Every source alpha and visible RGBA matches the runtime import: " + (mismatch ?? key));
        Check(visible.All(count => count > 0), "Every authored held-tool frame contains visible source pixels: " + key);
    }

    private void CheckAddresses(PixelAssets assets, Appearance appearance, IReadOnlyDictionary<string, string> equipment)
    {
        var keys = equipment.Values.Select(x => "equipment/" + x).Append($"people/body_{appearance.Body}_{appearance.Skin}")
            .Append($"people/hair_{appearance.Hair}_{appearance.HairColor}").Distinct().ToArray();
        foreach (string key in keys)
            for (int state = 0; state < Actions.Length; state++)
            {
                string expectedKey = state < 6 ? key : "motions/" + Actions[state] + "/" + key;
                int expectedState = state < 6 ? state : 0;
                var address = SpritePoseRules.SheetAddress(key, state);
                Check(address.Key == expectedKey && address.State == expectedState,
                    "SheetAddress preserves the literal layer and action: " + key + " / " + Actions[state]);
                var texture = assets.Texture(expectedKey); string? invalid = null;
                for (int direction = 0; direction < Directions.Length; direction++)
                    for (int frame = 0; frame < PixelAssets.Frames; frame++)
                    {
                        var region = new Rect2(frame * 64, (expectedState * 4 + direction) * 64, 64, 64);
                        var atlas = assets.Frame(key, state, direction, frame); atlasAddresses++;
                        if (key == HeldKey) heldAddresses++;
                        if (atlas is null || texture is null || atlas.Atlas != texture || atlas.Region != region
                            || region.End.X > texture.GetWidth() || region.End.Y > texture.GetHeight())
                            invalid ??= $"{expectedKey} / {Directions[direction]} / frame {frame}";
                    }
                Check(invalid is null, "All 32 direction/frame atlas cells resolve within the runtime sheet: " + (invalid ?? expectedKey));
            }
    }

    private async Task Capture(string name)
    {
        if (DisplayServer.GetName() == "headless") return;
        await Frame(); await Frame();
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS")
            ?? throw new InvalidOperationException("Provide isolated screenshots for the opt-in art fixture.");
        System.IO.Directory.CreateDirectory(root);
        using var image = GetViewport().GetTexture().GetImage();
        Check(image.SavePng(System.IO.Path.Combine(root, name + ".png")) == Error.Ok, "Saved offline native art sheet: " + name);
        captures++;
    }

    private async Task Release(ClassicTutorialPickaxeGallery? gallery)
    {
        if (gallery is not null && GodotObject.IsInstanceValid(gallery))
        {
            gallery.SetProcess(false); gallery.QueueFree();
            await Frame(); await Frame();
            await ToSignal(GetTree().CreateTimer(.06), SceneTreeTimer.SignalName.Timeout);
        }
    }

    public override async void _Ready()
    {
        ClassicTutorialPickaxeGallery? gallery = null;
        try
        {
            Check(ProjectSettings.GlobalizePath("user://").Contains("Kairnfall-Classic-QA", StringComparison.Ordinal), "Native fixture settings stay isolated");
            var ordinary = PixelAssets.LoadCatalog(); string ordinaryBefore = Json(ordinary);
            Check(ordinary.ClassicTutorial is null, "The retained catalog starts in ordinary-world mode");
            var optional = Wire.Copy(ordinary); ClassicTutorialContent.Enable(optional);
            Check(Json(ordinary) == ordinaryBefore && optional.Validate().Count == 0,
                "Optional art fixture uses a valid detached catalog without changing the retained catalog");
            var realm = new RealmEngine(optional);
            string id = realm.CreateCharacter("offline-pickaxe-art", "Pickaxe Wayfarer", "vanguard", new()).Id;
            var initialEquipment = Wire.Copy(realm.Player(id).Equipment);
            Check(realm.State.Characters.Count == 1 && realm.Player(id).Position == optional.Zone(ClassicTutorialContent.ZoneId).Spawn
                && realm.Player(id).ClassicTutorial is not null && Items.Count(realm.Player(id), Pickaxe) == 0,
                "The detached character starts at its real spawn without a granted pickaxe");
            var recipe = optional.Recipe("classic_make_pickaxe");
            Check(recipe.Output == Pickaxe && recipe.Quantity == 1 && recipe.Ingredients.All(x => Items.Count(realm.Player(id), x.Key) == 0),
                "The current real recipe starts with no fabricated ingredients");
            realm.Active.Add(id); GatherIngredients(realm, id, recipe);
            var ingredientCounts = recipe.Ingredients.ToDictionary(x => x.Key, x => Items.Count(realm.Player(id), x.Key));
            Execute(realm, id, new GameCommand { Kind = "craft", Item = recipe.Id, Amount = 1 });
            Check(recipe.Ingredients.All(x => Items.Count(realm.Player(id), x.Key) == ingredientCounts[x.Key] - x.Value),
                "Actual crafting consumes each current recipe ingredient exactly once");
            var tool = realm.Player(id).Inventory.Single(x => x.Template == Pickaxe);
            Check(Guid.TryParseExact(tool.Id, "N", out _) && tool.Quantity == 1,
                "Actual crafting produces one owned tool with its real item GUID and rarity");
            Execute(realm, id, new GameCommand { Kind = "equip", Item = tool.Id });
            var player = realm.Player(id); var equipment = PixelAssets.VisibleEquipment(player);
            Check(player.Equipment["weapon"] == tool.Id && equipment["weapon"] == Pickaxe,
                "Real equip selects the owned pickaxe and literal held-tool art identity");
            Check(initialEquipment.Where(x => x.Key != "weapon").All(x => player.Equipment.GetValueOrDefault(x.Key) == x.Value)
                && player.Inventory.Any(x => x.Id == initialEquipment["weapon"]),
                "Real equip preserves starter armor and retains the former weapon in the backpack");
            Check(player.ClassicTutorial!.Completed.IsSupersetOf(new[] { "wood", "stone", "pickaxe" })
                && Items.Validate(realm.State, optional).Count == 0, "Only accepted gather/craft actions earned milestones and ownership remains valid");
            var snapshot = realm.Snapshot(id); var appearance = snapshot.Self.Appearance;
            float acceptedScale = SpritePoseRules.CharacterScale(optional, snapshot.Self);
            Check(Math.Abs(acceptedScale - .8f) < .000001f, "The unchanged optional character uses the accepted 0.8 draw scale");
            string stateBefore = Json(realm.State), lootBefore = Json(realm.Loot), snapshotBefore = Json(snapshot), optionalBefore = Json(optional);
            var assets = new PixelAssets(); assets.BindCatalog(optional);
            CheckImportedSheet(assets, HeldKey, 1536);
            for (int state = 6; state < Actions.Length; state++) CheckImportedSheet(assets, "motions/" + Actions[state] + "/" + HeldKey, 256);
            CheckAddresses(assets, appearance, equipment);
            Check(heldAddresses == 352 && SpritePoseRules.WeaponPose(2, equipment) == 2,
                "The held pickaxe covers all 352 poses and keeps the real melee attack rig");

            bool graphical = DisplayServer.GetName() != "headless";
            if (graphical)
            {
                // This is a dedicated fixture window. No owner configuration is loaded
                // or saved, and the game/world values remain the earned authority values.
                GetWindow().Size = new Vector2I(1280, 720); await Frame(); await Frame();
                gallery = new ClassicTutorialPickaxeGallery { Assets = assets, Appearance = appearance, Equipment = equipment, AcceptedScale = acceptedScale };
                AddChild(gallery); gallery.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect); await Frame();
                Check(gallery.Size.X >= 1240 && gallery.Size.Y >= 700, "The dedicated native art viewport can show all labeled frame pairs");
                for (int state = 0; state < Actions.Length; state++)
                    foreach (float scale in new[] { 1f, acceptedScale })
                    {
                        gallery.State = state; gallery.ModelScale = scale; gallery.Focus = false; gallery.QueueRedraw();
                        await Capture($"pickaxe-runtime-{state:D2}-{Actions[state]}-scale-{scale.ToString("0.0", CultureInfo.InvariantCulture)}");
                    }
                foreach (int state in new[] { 0, 2, 6, 7, 5 })
                {
                    gallery.State = state; gallery.Focus = true; gallery.QueueRedraw();
                    await Capture($"pickaxe-detail-{state:D2}-{Actions[state]}-grip-work-collapse");
                }
                Check(captures == 27 && gallery.ComposedPoses.Count == 704,
                    "Native draw callbacks render all 704 composed poses at 1.0/0.8 plus five labeled grip, work and collapse inspections");
            }
            Check(assets.Missing.Count == 0, "All held-tool, body, hair and actual armor layers load without fallback");
            Check(Json(realm.State) == stateBefore && Json(realm.Loot) == lootBefore && Json(snapshot) == snapshotBefore
                && Json(optional) == optionalBefore && Json(ordinary) == ordinaryBefore,
                "Art reads and pose previews preserve every earned character/world/catalog value");
            await Release(gallery); gallery = null;
            GD.Print($"CLASSIC_TUTORIAL_PICKAXE_CONTRACT: {checks} checks passed; six imports, {comparedPixels} source pixels, {atlasAddresses} layer addresses ({heldAddresses} held), {captures} native captures. "
                + $"Offline art fixture; graphicalRendered={graphical}. Default Vanguard appearance/armor only. Static poses including unperformed combat/death/ranged actions; no live realm, physical-input, anatomy/grip judgment or human art approval.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CLASSIC_TUTORIAL_PICKAXE_CONTRACT: " + error);
            await Release(gallery); GetTree().Quit(1);
        }
    }
}

/// <summary>Draws production composition/layer routing, with labels; never writes character state.</summary>
public partial class ClassicTutorialPickaxeGallery : Control
{
    public PixelAssets Assets { get; set; } = null!;
    public Appearance Appearance { get; set; } = null!;
    public IReadOnlyDictionary<string, string> Equipment { get; set; } = null!;
    public float AcceptedScale { get; set; }
    public float ModelScale { get; set; } = 1;
    public int State { get; set; }
    public bool Focus { get; set; }
    public HashSet<string> ComposedPoses { get; } = [];
    public override void _Ready() { TextureFilter = TextureFilterEnum.Nearest; MouseFilter = MouseFilterEnum.Ignore; }
    private void Label(string text, Vector2 position, int size = 13) => DrawString(ThemeDB.FallbackFont, position, text, fontSize: size, modulate: new Color("eadcbb"));
    private void Person(Vector2 feet, int direction, int frame, float scale)
    {
        Assets.DrawPerson(this, Appearance, Equipment, feet, State, direction, frame, scale: scale);
        ComposedPoses.Add($"{State}:{direction}:{frame}:{scale.ToString("0.0", CultureInfo.InvariantCulture)}");
    }
    public override void _Draw()
    {
        DrawRect(new Rect2(Vector2.Zero, Size), new Color("17232c"));
        string action = ClassicTutorialPickaxeContract.Actions[State];
        var address = SpritePoseRules.SheetAddress(ClassicTutorialPickaxeContract.HeldKey, State);
        Label($"KAIRNFALL / HELD STONE PICKAXE / {action} / "
            + (Focus ? "2x display inspection: native 1.0 and accepted 0.8" : $"native display; draw scale {ModelScale.ToString("0.0", CultureInfo.InvariantCulture)}"), new(20, 28), 18);
        Label("Earned detached authority loadout: body/hair + " + string.Join(" + ", Equipment.OrderBy(x => x.Key).Select(x => x.Key + ":" + x.Value)), new(20, 49));
        Label($"Runtime sheet: {address.Key}.png | sheet state {address.State} | direction rows south/west/east/north", new(20, 69));
        Label(Focus ? "Selected frames 0, 2, 4, 7; left=1.0, right=0.8; both magnified 2x for review. No pose changes to the realm."
            : "Each cell: composed character (left), actual held layer (right). Source cells 64x64; nearest texture filter; shared floor anchors.", new(20, 90));
        float left = 74, cellWidth = (Size.X - left - 18) / (Focus ? 4 : 8), rowHeight = (Size.Y - 151) / 4;
        for (int direction = 0; direction < 4; direction++)
        {
            float rowY = 108 + direction * rowHeight;
            Label(ClassicTutorialPickaxeContract.Directions[direction], new(8, rowY + 56));
            int columns = Focus ? 4 : 8;
            for (int column = 0; column < columns; column++)
            {
                int frame = Focus ? new[] { 0, 2, 4, 7 }[column] : column;
                float x = left + column * cellWidth;
                DrawRect(new Rect2(x + 2, rowY, cellWidth - 4, rowHeight - 4), new Color(direction % 2 == 0 ? "22323b" : "263943"));
                if (!Focus) Label($"frame {frame} / person + tool", new(x + 8, rowY + 18));
                else if (direction == 0) Label($"frame {frame} / 1.0       0.8", new(x + 8, 104));
                float floor = rowY + (Focus ? rowHeight - 25 : 91);
                DrawLine(new(x + 6, floor), new(x + cellWidth - 6, floor), new Color("57766b"));
                if (Focus)
                {
                    DrawSetTransform(new Vector2(x + cellWidth * .27f, floor).Round(), 0, new Vector2(2, 2));
                    Person(Vector2.Zero, direction, frame, 1);
                    DrawSetTransform(new Vector2(x + cellWidth * .75f, floor).Round(), 0, new Vector2(2, 2));
                    Person(Vector2.Zero, direction, frame, AcceptedScale);
                    DrawSetTransform(Vector2.Zero);
                }
                else
                {
                    Person(new Vector2(x + 39, floor).Round(), direction, frame, ModelScale);
                    Assets.DrawFrame(this, ClassicTutorialPickaxeContract.HeldKey, new Vector2(x + 110, floor).Round(), State, direction, frame, scale: ModelScale);
                }
            }
        }
        Label("ART / OFFLINE FIXTURE. Static pose previews; no live combat, physical input, animation pacing, anatomy/grip judgment or human art approval.", new(20, Size.Y - 16), 12);
    }
}
