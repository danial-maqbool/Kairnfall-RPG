using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Isolated native controls, authority boundaries and rendered fixtures; no personal account.</summary>
public partial class ClassicExperienceContract : Node
{
    private int checks;
    private static FieldInfo Member(string name) => typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!;
    private static T Field<T>(GameRoot game, string name) => (T)Member(name).GetValue(game)!;
    private static object? Call(GameRoot game, string name, params object?[] args)
        => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private void Check(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS CLASSIC: " + message);
    }
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private void Mouse(Control control, MouseButton button, bool pressed, bool doubleClick = false)
    {
        Vector2 position = control.GetGlobalRect().GetCenter();
        using var input = new InputEventMouseButton
        {
            Position = position, GlobalPosition = position, ButtonIndex = button,
            ButtonMask = pressed ? button == MouseButton.Left ? MouseButtonMask.Left : MouseButtonMask.Right : 0,
            Pressed = pressed, DoubleClick = doubleClick
        };
        GetViewport().PushInput(input, true);
    }
    private async Task Capture(string name)
    {
        if (DisplayServer.GetName() == "headless") return;
        await Frame(); await Frame();
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS")
            ?? throw new InvalidOperationException("Provide an isolated screenshot directory.");
        System.IO.Directory.CreateDirectory(root);
        using var image = GetViewport().GetTexture().GetImage();
        Check(image.SavePng(System.IO.Path.Combine(root, name + ".png")) == Error.Ok, "Saved real native frame " + name);
    }
    private bool Fits(Control control)
    {
        var rect = control.GetGlobalRect(); var bounds = GetViewport().GetVisibleRect();
        return control.IsVisibleInTree() && rect.Position.X >= 0 && rect.Position.Y >= 0
            && rect.End.X <= bounds.End.X + 1 && rect.End.Y <= bounds.End.Y + 1;
    }
    private void CheckInteractionReadiness(Catalog data, Character initial, double time)
    {
        var self = Wire.Copy(initial); self.Inventory.Clear(); self.Equipment.Clear();
        var chest = new Chest { Id = "readiness-chest", Zone = self.Zone, Position = self.Position, ReadyAt = time, Kind = "weathered" };
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time) == "", "A restocked weathered chest permits an opening intention");
        chest.ReadyAt = time + 1;
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time).Contains("empty"), "Chest restock time produces an explicit empty-chest reason");
        chest.ReadyAt = time; self.Cooldowns["chest"] = time + 1;
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time).Contains("recovery"), "Character chest-opening recovery is distinct from chest restock time");
        self.Cooldowns["chest"] = time;
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time) == "", "Chest-opening recovery ends exactly at its authoritative deadline");
        chest.Hidden = true;
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time).StartsWith("Find"), "Undiscovered hidden chests expose their actual discovery requirement");
        self.Discoveries.Add("secret:" + chest.Id);
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time) == "", "A recorded hidden-chest discovery permits the existing opening path");
        chest.Hidden = false; chest.Kind = "locked"; chest.Requirement = 8; self.SkillXp["lockpicking"] = 0;
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time) == "Requires Lockpicking 8.", "Locked chests state the actual unmet skill level");
        self.SkillXp["lockpicking"] = Progression.Threshold(8);
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time).Contains("Lockpick"), "A learned lockpicker still needs a backpack lockpick");
        self.Inventory.Add(new Item { Id = "only-lockpick", Template = "lockpick", Quantity = 1 });
        for (int i = 1; i < Items.InventoryCapacity; i++) self.Inventory.Add(new Item { Id = "full-bag-" + i, Template = "iron_sword", Quantity = 1 });
        string before = System.Text.Json.JsonSerializer.Serialize(self, Wire.Json);
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time) == "", "A full bag with the last lockpick is not falsely denied before the server consumes it");
        chest.Kind = "runic"; self.SkillXp["runecasting"] = 0;
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time) == "Requires Runecasting 4.", "Runic chests use half the chest requirement with the server's minimum level");
        self.SkillXp["runecasting"] = Progression.Threshold(4);
        Check(InteractionReadinessRules.ChestProblem(self, chest, data, time) == "", "Randomized chest rewards leave capacity resolution to the realm");
        self.SkillXp["runecasting"] = 0;
        Check(System.Text.Json.JsonSerializer.Serialize(self, Wire.Json) == before, "Chest preflight never consumes a key, changes cooldowns, or grants rewards");

        self.Inventory.Clear(); int stackMax = data.Item("bread").StackMax;
        self.Inventory.Add(new Item { Id = "nearly-full-bread", Template = "bread", Quantity = stackMax - 1 });
        for (int i = 1; i < Items.InventoryCapacity; i++) self.Inventory.Add(new Item { Id = "loot-bag-" + i, Template = "iron_sword", Quantity = 1 });
        var pile = new LootPile { Id = "readiness-loot", Zone = self.Zone, Position = self.Position, Owner = self.Id, Expires = time + 30, PublicAt = time + 20,
            Items = [new Item { Id = "last-bread", Template = "bread", Quantity = 1 }], Gold = 1 };
        before = System.Text.Json.JsonSerializer.Serialize(self, Wire.Json);
        string pileBefore = System.Text.Json.JsonSerializer.Serialize(pile, Wire.Json);
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time) == "", "A full bag can collect a reward that fits its actual existing stack");
        Check(System.Text.Json.JsonSerializer.Serialize(self, Wire.Json) == before && System.Text.Json.JsonSerializer.Serialize(pile, Wire.Json) == pileBefore,
            "Successful loot preflight leaves both authoritative bag and ground pile unchanged");
        pile.Items.Add(new Item { Id = "overflow-bread", Template = "bread", Quantity = 1 });
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time) == "Not enough storage space.", "Loot preflight checks the whole pile rather than each reward against the same original bag");
        Check(System.Text.Json.JsonSerializer.Serialize(self, Wire.Json) == before, "A later reward that exceeds capacity cannot partly fill the real bag during preflight");
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time, false) == "", "HUD readiness avoids per-frame inventory simulation and retains the collection intention");
        pile.Items.RemoveAt(1); pile.Items[0].Element = Element.Fire;
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time) == "Not enough storage space.", "Loot carrying distinct item metadata does not merge into an ordinary supply stack");
        pile.Items[0].Element = null; pile.Owner = "foreign";
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time).Contains("reserved"), "Private foreign loot explains its owner restriction before a request");
        self.Party = "readiness-party"; pile.Party = self.Party; pile.PartyAt = time + 1;
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time).Contains("reserved"), "Party loot preserves the round-robin owner's exclusive interval");
        pile.PartyAt = time;
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time) == "", "Party loot becomes available at its authoritative party deadline");
        pile.Party = ""; pile.PublicAt = time;
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time) == "", "Unowned-party loot becomes public exactly at its public deadline");
        pile.Expires = time;
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time).Contains("expired"), "Expiry takes precedence over public loot access");
        pile.Expires = double.NaN;
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time).Contains("expired"), "Invalid ground-loot expiry cannot advertise a collection");
        pile.Expires = time + 30; self.Gold = Items.GoldCap;
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time) == "Gold limit reached.", "Ground gold cannot exceed the authoritative wallet limit");
        pile.Gold = 0;
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time) == "", "A capped wallet can still collect an item-only ground pile");
        pile.Zone = "foreign-zone";
        Check(InteractionReadinessRules.LootProblem(self, pile, data, time).StartsWith("Move closer"), "Ground-loot preflight cannot act across regions");
    }
    private async Task CheckUrgentLootPresentation(GameRoot game, Snapshot initial)
    {
        var snapshot = Wire.Copy(initial); snapshot.Self.LastCombat = snapshot.Time - 10; snapshot.Creatures = [];
        var pile = new LootPile { Id = "native-first-spoils", Owner = snapshot.Self.Id, Zone = snapshot.Self.Zone,
            Position = snapshot.Self.Position, Expires = snapshot.Time + 30, Gold = 3 };
        var settings = Field<ConfigFile>(game, "settings");
        foreach (double textScale in new[] { 1d, 1.25d })
        {
            Call(game, "ApplyUiTextScale", textScale, false);
            foreach (bool compact in new[] { false, true })
            {
                settings.SetValue("hud", "focus_world", compact); Call(game, "ApplyFocusHud");
                game.World.Accept(new TransportPacket { Snapshot = snapshot, Loot = [pile] }); Call(game, "UpdateHud");
                await Frame(); await Frame();
                var text = Field<Label>(game, compact ? "focusObjective" : "objectiveText");
                Check(text.IsVisibleInTree() && text.Text.Contains("30s", StringComparison.Ordinal)
                    && text.GetVisibleLineCount() > 0 && Fits(text),
                    "First-spoils countdown is visible in " + (compact ? "compact" : "expanded") + " HUD at text scale " + textScale);
                Check(Field<JourneyHint>(game, "journeyHint").Id == "loot",
                    "Visible urgency acknowledges the loot hint, not an unrelated opening tip");
            }
        }
        await Capture("first-spoils-countdown-1280");
        Call(game, "ApplyUiTextScale", 1d, false);
        game.World.Accept(new TransportPacket { Snapshot = initial }); Call(game, "UpdateHud");
        Check(Field<Label>(game, "focusObjective").Text.Contains(NewPlayerJourney.Recommend(game.Data, initial).Objective, StringComparison.Ordinal),
            "Loss of loot visibility immediately restores ordinary guidance");
    }

    public override async void _Ready()
    {
        GameRoot? game = null;
        try
        {
            Check(ProjectSettings.GlobalizePath("user://").Contains("Kairnfall-Classic-QA", StringComparison.Ordinal),
                "Native fixture user settings are isolated from the player project");
            foreach (string address in new[] { "http://127.0.0.1:5077", "http://localhost:5077", "http://[::1]:5077", "https://localhost:5077" })
                Check(LocalRealmAddressRules.Allowed(address), "Local realm address remains available: " + address);
            foreach (string address in new[] { "https://www.mysteralegacy.com", "https://example.com", "http://192.168.1.4:5077", "http://localhost.example.com", "http://user@127.0.0.1:5077", "http://127.0.0.1:5077?token=x", "file:///local", "" })
                Check(!LocalRealmAddressRules.Allowed(address), "Nonlocal or malformed server input cannot create a connection");
            using (var scene = GD.Load<PackedScene>("res://Main.tscn")) game = scene.Instantiate<GameRoot>();
            AddChild(game); game.SetProcess(false); await Frame();
            var data = game.Data; var realm = new RealmEngine(data);
            var self = realm.CreateCharacter("classic-fixture", "Local Wayfarer", "vanguard", new());
            realm.Active.Add(self.Id);
            CheckInteractionReadiness(data, self, 10);
            var zone = data.Zone(self.Zone);
            Point Clear(double lower, double upper) => Enumerable.Range(-100, 201)
                .SelectMany(x => Enumerable.Range(-100, 201).Select(y => self.Position.Add(new Point(x * .05, y * .05))))
                .First(x => x.Distance(self.Position) > lower && x.Distance(self.Position) <= upper
                    && WorldMap.Fits(zone, x) && WorldMap.LineOfSight(zone, self.Position, x));
            var pile = new LootPile { Id = "underfoot", Zone = self.Zone, Position = self.Position, Owner = self.Id, PublicAt = 20, Expires = 180 };
            Check(ClassicLootRules.Underfoot(self, [pile], 10)?.Id == pile.Id, "Shift pickup chooses eligible loot on the player's tile");
            pile.Owner = "foreign";
            Check(ClassicLootRules.Underfoot(self, [pile], 10) is null, "Shift cannot take private foreign loot");
            Check(ClassicLootRules.Underfoot(self, [pile], 20)?.Id == pile.Id, "Public loot retains authoritative availability time");
            pile.Position = self.Position.Add(new Point(1, 0));
            Check(ClassicLootRules.Underfoot(self, [pile], 20) is null, "Shift cannot collect an adjacent tile remotely");
            pile.Position = self.Position; pile.Zone = "foreign-zone";
            Check(ClassicLootRules.Underfoot(self, [pile], 20) is null, "Shift cannot collect across region boundaries");
            pile.Zone = self.Zone;
            Check(ClassicLootRules.Underfoot(self, [pile], double.NaN) is null, "Shift pickup rejects invalid clocks");
            var lootSelf = Wire.Copy(self); lootSelf.Party = "classic-fixture-party";
            foreach (string access in new[] { "owner", "party", "public" })
            {
                var stalePile = new LootPile
                {
                    Id = "stale-" + access, Zone = self.Zone, Position = self.Position,
                    Owner = access == "owner" ? self.Id : "foreign",
                    Party = access == "party" ? lootSelf.Party : "", PartyAt = 0,
                    PublicAt = access == "public" ? 0 : 60, Expires = 21
                };
                Check(ClassicLootRules.Underfoot(lootSelf, [stalePile], 20)?.Id == stalePile.Id,
                    "Fresh retained " + access + " loot remains eligible for Shift pickup");
                foreach (double expiry in new[] { 20d, 19d, double.NaN, double.PositiveInfinity })
                {
                    stalePile.Expires = expiry;
                    Check(ClassicLootRules.Underfoot(lootSelf, [stalePile], 20) is null,
                        "Expired or invalid " + access + " loot cannot be picked up from a stale snapshot: " + expiry);
                }
            }
            var front = new WorldTarget("node", "front", "Front", self.Position.Add(new Point(1, 0)));
            var back = new WorldTarget("node", "back", "Back", self.Position.Add(new Point(-.8, 0)));
            var oldFacing = self.Facing; self.Facing = new Point(1, 0);
            Check(ClassicInteractionRules.Choose(self, [back, front], data)?.Id == "front", "Tile-mode contextual action prefers the facing object over a closer object behind");
            Check(ClassicInteractionRules.Choose(self, [back], data) is null, "A facing action cannot silently select an object behind the player");
            Check(ClassicInteractionRules.Choose(self, [new WorldTarget("loot", "feet", "Underfoot", self.Position)], data)?.Id == "feet", "Underfoot interaction remains available regardless of facing");
            self.Facing = oldFacing;
            double reach = ExperienceRules.WeaponRange(self, data);
            var target = new Creature { Id = "classic-rat", Template = "field_rat", Zone = self.Zone,
                Position = Clear(.8, Math.Min(1.2, reach)), Health = 100 };
            Check(ClassicTargetRules.Ready(self, target, data, 10), "Selected creature is attackable only inside actual weapon reach");
            target.Position = Clear(reach + .3, reach + .8);
            Check(ClassicTargetRules.Valid(self, target) && !ClassicTargetRules.Ready(self, target, data, 10), "Selection can remain armed outside reach without an attack or route");
            target.Position = Clear(.8, Math.Min(1.2, reach));
            target.Owner = self.Id;
            Check(!ClassicTargetRules.Valid(self, target), "Owned companions cannot arm automatic attacks"); target.Owner = "";
            target.Health = 0;
            Check(!ClassicTargetRules.Valid(self, target), "Defeated targets cancel repeated attacks"); target.Health = 100;
            target.Zone = "foreign-zone";
            Check(!ClassicTargetRules.Valid(self, target), "Region changes invalidate selection"); target.Zone = self.Zone;
            Check(!ClassicTargetRules.Ready(self, target, data, double.NaN), "Nonfinite clocks cannot request attacks");
            var dead = Wire.Copy(self); dead.Health = 0;
            Check(!ClassicTargetRules.Ready(dead, target, data, 10), "Dead players cannot attack");
            var stunned = Wire.Copy(self); stunned.Statuses.Add(new StatusEffect { Kind = "stun", Until = 11 });
            Check(!ClassicTargetRules.Ready(stunned, target, data, 10), "Authoritative crowd control prevents attacks");
            var hidden = Enumerable.Range(-200, 401).SelectMany(x => Enumerable.Range(-200, 401)
                .Select(y => self.Position.Add(new Point(x * .1, y * .1))))
                .First(x => x.Distance(self.Position) < 12 && WorldMap.Fits(zone, x)
                    && !WorldMap.LineOfSight(zone, self.Position, x));
            var blocked = Wire.Copy(target); blocked.Position = hidden;
            Check(!ClassicTargetRules.Ready(self, blocked, data, 10), "A selected target behind terrain never sends an attack");
            var snapshot = realm.Snapshot(self.Id); snapshot.Time = 10; snapshot.Creatures = [target];
            game.World.Accept(new TransportPacket { Snapshot = snapshot });
            Check(game.World.Targets.Any(x => x.Id == target.Id && x.Kind == "creature"), "An accepted snapshot makes living targets available before the next render");
            var inputNode = new WorldNode { Id = "before-draw", Template = "oak_tree", Zone = self.Zone, Position = self.Position };
            var inputSnapshot = Wire.Copy(snapshot); inputSnapshot.Nodes = [inputNode];
            game.World.Accept(new TransportPacket { Snapshot = inputSnapshot });
            Check(game.World.Targets.Any(x => x.Id == inputNode.Id), "Context resources are available without a renderer callback");
            Check(game.World.ScreenToWorld(game.World.WorldToScreen(self.Position)).Distance(self.Position) < .05, "World pointer projection is initialized independently of drawing");
            var interactionSnapshot = Wire.Copy(inputSnapshot);
            var emptyChest = new Chest { Id = "selected-empty-chest", Zone = self.Zone, Position = Clear(.7, 1.1), ReadyAt = 11 };
            interactionSnapshot.Chests = [emptyChest];
            var reservedLoot = new LootPile { Id = "selected-private-loot", Zone = self.Zone, Position = self.Position,
                Owner = "foreign", PublicAt = 20, Expires = 180 };
            game.World.Accept(new TransportPacket { Snapshot = interactionSnapshot, Loot = [reservedLoot] });
            Call(game, "SelectTarget", "chest", emptyChest.Id);
            Check(Call(game, "ContextTarget") is WorldTarget selectedChest && selectedChest.Id == emptyChest.Id,
                "A deliberately selected empty chest keeps its explanation instead of changing the action to a nearer resource");
            Call(game, "Activate", game.World.Targets.Single(x => x.Id == emptyChest.Id));
            Check(Field<string>(game, "lastNoticeText").Contains("empty") && !Field<bool>(game, "actionBusy"),
                "Direct chest activation explains restock readiness before reaching the command sender");
            Call(game, "SelectTarget", "loot", reservedLoot.Id);
            Check(Call(game, "ContextTarget") is WorldTarget selectedLoot && selectedLoot.Id == reservedLoot.Id,
                "A deliberately selected private pile retains its ownership explanation");
            Call(game, "Activate", game.World.Targets.Single(x => x.Id == reservedLoot.Id));
            Check(Field<string>(game, "lastNoticeText").Contains("reserved") && !Field<bool>(game, "actionBusy"),
                "Direct ground-loot activation explains owner access before reaching the command sender");
            game.World.ClearSession(); Check(!game.World.Targets.Any(), "Session clear immediately removes all interaction targets");
            game.World.Accept(new TransportPacket { Snapshot = snapshot });
            Field<Control>(game, "frontend").Hide(); Call(game, "SetInitialHotbar");
            var settings = Field<ConfigFile>(game, "settings"); settings.SetValue("hud", "focus_world", false);
            settings.SetValue("controls", "classic_target_attack", true);
            Call(game, "ApplyFocusHud"); Call(game, "SelectTarget", "creature", target.Id);
            Field<List<Point>>(game, "route").Add(target.Position);
            Call(game, "ArmClassicTarget", target.Id);
            Check(Field<string>(game, "classicAttackTarget") == target.Id, "Click selection arms exactly the selected creature");
            Check(Field<List<Point>>(game, "route").Count == 0 && !Field<bool>(game, "combatApproach"), "Classic selection cannot start or retain a chase route");
            Call(game, "TickExperience", .01);
            Check(Field<string>(game, "classicAttackTarget") == "", "Disconnected clients cancel classic attacks");
            Call(game, "ArmClassicTarget", target.Id); Call(game, "OpenPage", "Inventory"); Call(game, "TickExperience", .01);
            Check(Field<string>(game, "classicAttackTarget") == "", "Opening a modal cancels classic attacks"); Call(game, "ClosePage");
            Call(game, "SelectTarget", "creature", target.Id); Call(game, "ArmClassicTarget", target.Id);
            game.Notification(checked((int)NotificationApplicationFocusOut));
            Check(Field<string>(game, "classicAttackTarget") == "", "Losing application focus cancels armed attacks");
            game.Notification(checked((int)NotificationApplicationFocusIn));
            settings.SetValue("controls", "classic_target_attack", false); Call(game, "ArmClassicTarget", target.Id);
            Check(Field<string>(game, "classicAttackTarget") == "", "Turning classic controls off retains explicit attack behavior");
            Call(game, "SelectTarget", "", "");
            GetWindow().Size = new Vector2I(1280, 720); GetWindow().ContentScaleSize = new Vector2I(1280, 720);
            Call(game, "UpdateHud"); await Frame(); await Frame(); await Capture("01-expanded-hud");
            settings.SetValue("hud", "focus_world", true); Call(game, "ApplyFocusHud");
            foreach (var size in new[] { new Vector2I(916, 515), new Vector2I(1024, 720), new Vector2I(1280, 720), new Vector2I(1920, 1080) })
            {
                GetWindow().Size = size; GetWindow().ContentScaleSize = size;
                Call(game, "UpdateHud"); await Frame(); await Frame();
                Check(!game.FindChild("VitalsAndObjectives", true, false)!.GetNode<Control>(".").Visible,
                    "Compact HUD hides the large status column at " + size);
                Check(!game.FindChild("QuestTracker", true, false)!.GetNode<Control>(".").Visible,
                    "Guidance layout cannot restore an opaque objective panel at " + size);
                var navigation = (Control)game.FindChild("CompactWorldNavigation", true, false)!;
                Check(Fits(navigation), "Character, Bag and Menu remain reachable at " + size);
                Check(Fits(Field<HudPanel>(game, "chatFrame")), "Compact chat stays inside the viewport at " + size);
                Check(Field<Button[]>(game, "hotbarButtons").All(Fits), "All ten ability slots remain reachable at " + size);
                var compact = (Control)game.FindChild("CompactWorldHud", true, false)!;
                var objective = Field<JourneyObjective>(game, "journeyObjective");
                var focus = Field<Label>(game, "focusObjective");
                Check(focus.Text.Contains(objective.Objective) && focus.Text.Contains(NewPlayerJourney.Navigation(data, game.Snapshot!.Self, objective).Description),
                    "Compact guidance retains the actual next action and direction independently of expanded layout at " + size);
                Check(compact.FindChildren("*", "ProgressBar", true, false).Count == 5,
                    "Compact HUD preserves health, mana, stamina and both XP meters");
                Check(Fits((Control)game.FindChild("ClassicActionCircle", true, false)!), "Action Circle remains reachable at " + size);
                Field<Queue<ProgressionMoment>>(game, "progressionQueue").Enqueue(new("rendered-feedback", "level", "LEVEL UP", "Native character rewards remain available in the progression feed."));
                Member("progressionUntil").SetValue(game, 0d); Call(game, "TickJourneyFeedback");
                await Frame(); await Frame(); Call(game, "TickJourneyFeedback");
                await Frame(); await Frame();
                var feedback = Field<HudPanel>(game, "progressionBanner");
                var title = Field<Label>(game, "progressionTitle");
                Check(Fits(title) && title.Size.Y >= title.GetThemeFont("font").GetHeight(title.GetThemeFontSize("font_size")),
                    "The progression title has an actual visible text row at " + size);
                Check(Fits(feedback), "Accepted progression feedback stays inside the viewport at " + size);
                Check(feedback.GetGlobalRect().End.X < GetViewport().GetVisibleRect().Size.X / 2 - 32,
                    "Progression feedback leaves the centered avatar unobscured at " + size);
                Check(feedback.MouseFilter == Control.MouseFilterEnum.Ignore,
                    "Progression feed cannot intercept movement or world targeting at " + size);
                Check(feedback.TooltipText.Contains("Native character rewards"),
                    "Compact feedback retains its full reward detail at " + size);
                if (size.X == 916) await Capture("03-compact-progression-916");
                Check(game.World.ClassicPresentation, "Compact HUD enables original classic world presentation");
                await Capture("02-compact-" + size.X);
            }
            GetWindow().Size = new Vector2I(1280, 720); GetWindow().ContentScaleSize = new Vector2I(1280, 720);
            var before = Wire.Copy(snapshot); var after = Wire.Copy(snapshot);
            after.Self.SkillXp["mining"] = before.Self.SkillXp.GetValueOrDefault("mining") + 1200;
            game.World.Accept(new TransportPacket { Snapshot = after }); Call(game, "ObservePlayerChanges", before, after); Call(game, "UpdateHud");
            Check(Field<Label>(game, "skillExperienceText").Text.StartsWith(data.Skill("mining").Name), "Only authoritative XP changes choose the displayed active skill");
            await Capture("03-authoritative-xp-feedback");
            // Native pointer/keyboard events reach the compact slot's actual input
            // handler. The isolated callbacks cannot send gameplay commands.
            var rareItem = Items.Create(data, "iron_sword", 1, Rarity.Rare);
            rareItem.Element = Element.Fire; rareItem.Durability = 37;
            int inspectedSlots = 0, activatedSlots = 0, contextualSlots = 0;
            var inputSlot = new ClassicItemSlot
            {
                Name = "ClassicInputProbe", Position = new Vector2(380, 180), Size = new Vector2(62, 62), ZIndex = 200,
                Item = rareItem, Icon = game.Assets.Icon(rareItem.Template), ItemElement = Element.Fire,
                Clicked = () => inspectedSlots++, Activated = () => activatedSlots++, ContextRequested = _ => contextualSlots++
            };
            var emptySlot = new ClassicItemSlot { Position = new Vector2(450, 180), Size = new Vector2(62, 62), ZIndex = 200 };
            AddChild(inputSlot); AddChild(emptySlot); await Frame(); await Frame();
            Check(emptySlot.FocusMode == Control.FocusModeEnum.None && emptySlot.MouseFilter == Control.MouseFilterEnum.Ignore
                && emptySlot.MouseDefaultCursorShape == Control.CursorShape.Arrow,
                "Empty compact slots cannot trap keyboard focus or advertise an item action");
            Mouse(inputSlot, MouseButton.Left, true);
            Check(inspectedSlots == 0, "Compact item selection waits for release and leaves drag detection available");
            Mouse(inputSlot, MouseButton.Left, false);
            Check(inspectedSlots == 1 && activatedSlots == 0, "A single compact-slot click inspects without equipping");
            Mouse(inputSlot, MouseButton.Left, true, true); Mouse(inputSlot, MouseButton.Left, false);
            Check(activatedSlots == 1 && inspectedSlots == 1, "A compact-slot double-click activates once without a second release action");
            Mouse(inputSlot, MouseButton.Right, true); Mouse(inputSlot, MouseButton.Right, false);
            Check(contextualSlots == 1, "A compact-slot right-click reaches the contextual action callback");
            inputSlot.GrabFocus(); await Frame();
            foreach (var key in new[] { Key.Enter, Key.Space })
            {
                using var press = new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = true };
                GetViewport().PushInput(press, true);
                using var release = new InputEventKey { Keycode = key, PhysicalKeycode = key, Pressed = false };
                GetViewport().PushInput(release, true);
            }
            Check(inspectedSlots == 3 && activatedSlots == 1, "Enter and Space inspect compact items without accidentally equipping them");
            inputSlot.Hide(); emptySlot.Hide(); inputSlot.QueueFree(); emptySlot.QueueFree(); await Frame();
            after.Self.Inventory.Insert(0, rareItem); game.World.Accept(new TransportPacket { Snapshot = after });
            Member("selectedItem").SetValue(game, rareItem.Id);
            // Inspect the actual native 3-by-5 overlays, including overflow-safe detail actions.
            foreach (var size in new[] { new Vector2I(916, 515), new Vector2I(1280, 720) })
            {
                GetWindow().Size = size; GetWindow().ContentScaleSize = size;
                Call(game, "OpenPage", "Inventory"); await Frame(); await Frame();
                var overlay = Field<PanelContainer>(game, "gameWindow");
                var grid = (GridContainer)overlay.FindChild("ClassicGrid", true, false)!;
                Check(grid.Columns == 3 && grid.GetChildCount() == 15, "Compact inventory contains exactly 3 by 5 slots");
                Check(grid.GetChildren().OfType<Control>().All(Fits), "All 15 inventory slots fit at " + size);
                Check(Fits(overlay) && Fits((Control)overlay.FindChild("ClassicClose", true, false)!), "Compact inventory and Close remain inside the viewport");
                Check(overlay.FindChildren("*", "Button", true, false).OfType<Button>().Any(x => x.Text == "Full item details"), "Detailed equipment and maintenance actions remain reachable");
                var rareSlot = grid.GetChildren().OfType<ClassicItemSlot>().Single(x => x.Item?.Id == rareItem.Id);
                Check(rareSlot.ItemElement == Element.Fire && rareSlot.Activated is not null && rareSlot.ContextRequested is not null,
                    "Actual compact inventory slots retain rolled elements and authoritative equipment/context callbacks");
                Check(rareSlot.TooltipText.Contains("Double-click: equip or unequip.") && rareSlot.TooltipText.Contains("Right-click: item actions."),
                    "Compact equipment hints describe supported input actions");
                var tooltip = rareSlot._MakeCustomTooltip(rareSlot.TooltipText);
                var tooltipNodes = tooltip.FindChildren("*", "Node", true, false).Cast<Node>().Prepend(tooltip).ToArray();
                try
                {
                    Check(tooltip.FindChildren("*", "Label", true, false).OfType<Label>().Any(x => x.Text.Contains("Right-click: item actions.")),
                        "The actual custom compact tooltip preserves the advertised action hints");
                }
                finally
                {
                    // A direct test call bypasses Godot's popup ownership. Dispose
                    // releases a wrapper, while Free destroys the detached node tree.
                    if (GodotObject.IsInstanceValid(tooltip)) tooltip.Free();
                }
                Check(tooltipNodes.Length > 1 && tooltipNodes.All(x => !GodotObject.IsInstanceValid(x)),
                    "Directly inspected compact tooltips release their complete native node hierarchy");
                Check(((Label)overlay.FindChild("ClassicItemIdentity", true, false)!).Text.Contains("Rare")
                    && ((Label)overlay.FindChild("ClassicItemIdentity", true, false)!).Text.Contains("Fire"),
                    "Compact inspection names rarity and rolled element without relying on border colors");
                Check(((Label)overlay.FindChild("ClassicItemRequirement", true, false)!).Text
                    == "Requires " + data.Skill(data.Item(rareItem.Template).Skill).Name + " " + BeginnerProgression.EquipmentRequirement(data.Item(rareItem.Template)),
                    "Compact inspection shows the actual trained-skill equipment requirement");
                Check(((Label)overlay.FindChild("ClassicItemDurability", true, false)!).Text == "Durability 37%",
                    "Compact inspection exposes the item's current durability");
                var amountEditor = (SpinBox)overlay.FindChild("ClassicDropAmount", true, false)!;
                Check(amountEditor.Value == 1, "A newly inspected item defaults to dropping one; Drop all remains explicit");
                ulong amountId = amountEditor.GetInstanceId(); amountEditor.Value = 1;
                Field<Action>(game, "refreshPage")(); await Frame();
                Check(((SpinBox)overlay.FindChild("ClassicDropAmount", true, false)!).GetInstanceId() == amountId && amountEditor.Value == 1,
                    "A repeated inventory refresh preserves the amount editor and its selected quantity");
                await Capture("04-inventory-" + size.X); Call(game, "ClosePage");
                Call(game, "OpenPage", "Crafting"); await Frame(); await Frame();
                overlay = Field<PanelContainer>(game, "gameWindow"); grid = (GridContainer)overlay.FindChild("ClassicGrid", true, false)!;
                Check(grid.Columns == 3 && grid.GetChildCount() == 15, "Compact crafting contains exactly 3 by 5 recipe slots");
                Check(grid.GetChildren().OfType<Control>().All(Fits) && Fits(overlay), "Compact crafting fits at " + size);
                Check(Fits((LineEdit)overlay.FindChild("ClassicRecipeSearch", true, false)!), "Compact recipe search fits beside the inspector at " + size);
                var craftAction = overlay.FindChildren("*", "Button", true, false).OfType<Button>().First(x => x.Text is "Craft" or "Build");
                ulong craftId = craftAction.GetInstanceId(); Field<Action>(game, "refreshPage")(); await Frame();
                Check(GodotObject.IsInstanceValid(craftAction) && craftAction.GetInstanceId() == craftId && !craftAction.IsQueuedForDeletion(),
                    "A repeated crafting refresh preserves the current action button");
                await Capture("05-crafting-" + size.X); Call(game, "ClosePage");
            }
            var pagedSnapshot = Wire.Copy(after);
            pagedSnapshot.Self.Inventory = [Wire.Copy(rareItem)]; pagedSnapshot.Self.Equipment.Clear();
            for (int i = 0; i < 16; i++) pagedSnapshot.Self.Inventory.Add(new Item { Id = "classic-page-item-" + i, Template = "bread", Quantity = 3 });
            game.World.Accept(new TransportPacket { Snapshot = pagedSnapshot });
            Member("selectedItem").SetValue(game, pagedSnapshot.Self.Inventory[16].Id);
            Call(game, "OpenPage", "Inventory"); await Frame(); await Frame();
            var pageOverlay = Field<PanelContainer>(game, "gameWindow");
            var pageGrid = (GridContainer)pageOverlay.FindChild("ClassicGrid", true, false)!;
            Check(Field<int>(game, "classicInventoryPage") == 1 && pageGrid.GetChildren().OfType<ClassicItemSlot>().Any(x => x.Item?.Id == Field<string>(game, "selectedItem")),
                "Opening compact inventory follows a preselected item to its actual page");
            ((Button)pageOverlay.FindChild("ClassicPreviousPage", true, false)!).EmitSignal(Button.SignalName.Pressed);
            await Frame(); await Frame();
            Check(Field<int>(game, "classicInventoryPage") == 0 && pageGrid.GetChildren().OfType<ClassicItemSlot>().Any(x => x.Item?.Id == Field<string>(game, "selectedItem") && x.Selected),
                "Changing inventory pages keeps the inspected item on the visible page");
            ((Button)pageOverlay.FindChild("ClassicNextPage", true, false)!).EmitSignal(Button.SignalName.Pressed);
            await Frame(); await Frame();
            Check(Field<int>(game, "classicInventoryPage") == 1 && pageGrid.GetChildren().OfType<ClassicItemSlot>().Any(x => x.Item?.Id == Field<string>(game, "selectedItem") && x.Selected),
                "Returning to a later inventory page updates the inspector to one of its visible items");
            var stackSlot = pageGrid.GetChildren().OfType<ClassicItemSlot>().First(x => x.Item?.Template == "bread");
            stackSlot.Clicked?.Invoke(); await Frame();
            Check(((SpinBox)pageOverlay.FindChild("ClassicDropAmount", true, false)!).Value == 1,
                "Selecting a new stack defaults to one rather than silently dropping the whole stack");
            Check(!stackSlot.TooltipText.Contains("Double-click: equip"), "Supply-item tooltips do not advertise equipment actions");
            var consumeSnapshot = Wire.Copy(pagedSnapshot); var consumeStats = CombatMath.Stats(consumeSnapshot.Self, data);
            consumeSnapshot.Self.Health = consumeStats.Health; consumeSnapshot.Self.Stamina = consumeStats.Stamina;
            consumeSnapshot.Self.Cooldowns.Remove("food");
            game.World.Accept(new TransportPacket { Snapshot = consumeSnapshot }); Field<Action>(game, "refreshPage")(); await Frame();
            var useItem = (Button)pageOverlay.FindChild("ClassicUseItem", true, false)!;
            var useReason = (Label)pageOverlay.FindChild("ClassicConsumeReadiness", true, false)!;
            var consumeAmount = (SpinBox)pageOverlay.FindChild("ClassicDropAmount", true, false)!; consumeAmount.Value = 2;
            ulong useId = useItem.GetInstanceId(), consumeAmountId = consumeAmount.GetInstanceId();
            Check(useItem.Disabled && useItem.TooltipText == "You do not need food yet." && useReason.Visible,
                "The actual compact Use action explains why full health and stamina need no food");
            object consumePageStamp = Call(game, "PageStamp")!;
            consumeSnapshot = Wire.Copy(consumeSnapshot); consumeSnapshot.Self.Stamina -= 20;
            game.World.Accept(new TransportPacket { Snapshot = consumeSnapshot }); Call(game, "TickExperience", .11); await Frame();
            Check(Equals(consumePageStamp, Call(game, "PageStamp")), "A stamina-only snapshot stays outside the inventory layout stamp");
            Check(useItem.GetInstanceId() == useId && !useItem.IsQueuedForDeletion() && useItem.TooltipText == "" && !useReason.Visible,
                "Authoritative stamina changes refresh the existing Use action's readiness without rebuilding its controls");
            Check(useItem.Disabled, "An eligible food item still cannot be submitted from the disconnected native fixture");
            Check(((SpinBox)pageOverlay.FindChild("ClassicDropAmount", true, false)!).GetInstanceId() == consumeAmountId && consumeAmount.Value == 2,
                "Food readiness refreshes preserve a player's live drop-amount edit");
            consumeSnapshot = Wire.Copy(consumeSnapshot); consumeSnapshot.Self.Cooldowns["food"] = consumeSnapshot.Time + 8;
            game.World.Accept(new TransportPacket { Snapshot = consumeSnapshot }); Call(game, "TickExperience", .11); await Frame();
            Check(useItem.GetInstanceId() == useId && useItem.Disabled && useItem.TooltipText.StartsWith("Recovering") && useReason.Text == useItem.TooltipText,
                "The actual compact Use action reflects authoritative food recovery on the same button");
            consumeSnapshot = Wire.Copy(consumeSnapshot); consumeSnapshot.Time += 8;
            game.World.Accept(new TransportPacket { Snapshot = consumeSnapshot }); Call(game, "TickExperience", .11); await Frame();
            Check(useItem.GetInstanceId() == useId && useItem.TooltipText == "" && !useReason.Visible,
                "The compact Use action clears its recovery reason at the authoritative cooldown boundary");
            game.World.Accept(new TransportPacket { Snapshot = pagedSnapshot });
            Call(game, "ClosePage");
            Check(Field<Action?>(game, "classicConsumeReadinessTick") is null, "Closing compact inventory releases its eligibility callback before freeing controls");
            Call(game, "TickExperience", .11);
            Call(game, "OpenPage", "Crafting"); await Frame(); await Frame();
            pageOverlay = Field<PanelContainer>(game, "gameWindow"); pageGrid = (GridContainer)pageOverlay.FindChild("ClassicGrid", true, false)!;
            ((Button)pageOverlay.FindChild("ClassicNextPage", true, false)!).EmitSignal(Button.SignalName.Pressed);
            await Frame(); await Frame();
            Check(pageGrid.GetChildren().OfType<ClassicItemSlot>().Any(x => x.Item?.Id == Field<string>(game, "selectedRecipe") && x.Selected),
                "Changing crafting pages keeps the inspected recipe on the visible page");
            var recipeSlot = pageGrid.GetChildren().OfType<ClassicItemSlot>().Last(x => x.Item is not null);
            recipeSlot.Activated?.Invoke(); await Frame();
            Check(Field<string>(game, "selectedRecipe") == recipeSlot.Item!.Id && !Field<bool>(game, "actionBusy"),
                "Double-clicking a compact recipe inspects it without submitting a craft");
            var search = (LineEdit)pageOverlay.FindChild("ClassicRecipeSearch", true, false)!;
            search.Text = "  cOpPeR  SmElT  "; search.EmitSignal(LineEdit.SignalName.TextChanged, search.Text);
            await Frame(); await Frame();
            Check(Field<int>(game, "classicCraftPage") == 0 && pageGrid.GetChildren().OfType<ClassicItemSlot>().Any(x => x.Item?.Id == "smelt_copper"),
                "A case-insensitive multiword search finds the copper-smelting recipe and resets paging");
            search.Text = "no-such-recipe-qa"; search.EmitSignal(LineEdit.SignalName.TextChanged, search.Text);
            await Frame(); await Frame();
            Check(pageGrid.GetChildren().OfType<ClassicItemSlot>().All(x => x.Item is null)
                && pageOverlay.FindChildren("*", "Label", true, false).OfType<Label>().Any(x => x.Text == "No matching recipes")
                && !pageOverlay.FindChildren("*", "Button", true, false).OfType<Button>().Any(x => x.Text is "Craft" or "Build"),
                "An empty search clears obsolete recipes and their craft action with an explicit recovery hint");
            search.Text = ""; search.EmitSignal(LineEdit.SignalName.TextChanged, search.Text);
            await Frame(); await Frame();
            Check(pageGrid.GetChildren().OfType<ClassicItemSlot>().Count(x => x.Item is not null) == 15,
                "Clearing recipe search restores the complete paginated catalog without crafting");
            await Capture("06-crafting-search-restored");
            Call(game, "ClosePage");
            var recipe = data.Recipe("smelt_copper"); var craftingSelf = Wire.Copy(self);
            Check(ClassicCraftRules.Problem(craftingSelf, recipe, data, snapshot.Time, true, true).StartsWith("Need"), "Missing materials disable compact crafting");
            Items.Add(craftingSelf.Inventory, Items.Create(data, "copper_ore", 3), data);
            Check(ClassicCraftRules.Problem(craftingSelf, recipe, data, snapshot.Time, false, true).StartsWith("Move closer"), "Compact crafting validates the real required station");
            Check(ClassicCraftRules.Problem(craftingSelf, recipe, data, snapshot.Time, true, true) == "", "Actual recipe materials and station enable the standard craft");
            Check(ClassicCraftRules.Problem(craftingSelf, recipe, data, snapshot.Time, true, false) != "", "A busy or disconnected client cannot submit a compact craft");
            var food = Items.Create(data, "bread", 2); Items.Add(craftingSelf.Inventory, food, data); food = craftingSelf.Inventory.First(x => x.Template == "bread");
            Check(ClassicConsumeRules.Problem(craftingSelf, food, data, snapshot.Time) != "", "Quick food cannot consume an item when health and stamina are full");
            craftingSelf.Stamina -= 30;
            Check(ClassicConsumeRules.Problem(craftingSelf, food, data, snapshot.Time) == "", "Food advertises the actual stamina and regeneration benefit");
            craftingSelf.Cooldowns["food"] = snapshot.Time + 8;
            Check(ClassicConsumeRules.Problem(craftingSelf, food, data, snapshot.Time).StartsWith("Recovering"), "Quick food respects the authoritative food cooldown");
            var hungrySelf = Wire.Copy(self); hungrySelf.Inventory.Add(Wire.Copy(food));
            hungrySelf.ClassicTutorial = new ClassicTutorialProgress { Food = 70 };
            Check(ClassicConsumeRules.Problem(hungrySelf, food, data, snapshot.Time) == "",
                "A hungry optional tutorial character can use food with full health and stamina");
            hungrySelf.ClassicTutorial.Food = 100;
            Check(ClassicConsumeRules.Problem(hungrySelf, food, data, snapshot.Time) != "",
                "Full Food with full health and stamina prevents unnecessary consumption");
            hungrySelf.ClassicTutorial.Food = 70; hungrySelf.Cooldowns["food"] = snapshot.Time + 8;
            Check(ClassicConsumeRules.Problem(hungrySelf, food, data, snapshot.Time).StartsWith("Recovering"),
                "Hunger does not bypass the authoritative food cooldown");
            hungrySelf.Cooldowns.Remove("food"); hungrySelf.Inventory.RemoveAll(x => x.Id == food.Id);
            Check(ClassicConsumeRules.Problem(hungrySelf, food, data, snapshot.Time) == "No item in your backpack.",
                "Hunger cannot consume food absent from the character's backpack");
            var node = new WorldNode { Id = "gather-fixture", Template = "oak_tree", Zone = self.Zone, Position = self.Position };
            Check(ClassicGatherRules.Problem(self, node, data, snapshot.Time) == "", "An adjacent oak tree uses the existing backpack tool rules");
            node.Position = self.Position.Add(new Point(4, 0));
            Check(ClassicGatherRules.Problem(self, node, data, snapshot.Time) != "", "Gathering cannot target a distant resource");
            Member("classicGatherTarget").SetValue(game, "gather-fixture"); Member("classicGatherConfirmed").SetValue(game, false); Call(game, "ReleaseBasicAttack");
            Check(Field<string>(game, "classicGatherTarget") == "", "Release before an accepted gather clears the repeat intention");
            Member("classicGatherTarget").SetValue(game, "gather-fixture"); Member("classicGatherConfirmed").SetValue(game, true); Call(game, "ReleaseBasicAttack");
            Check(Field<string>(game, "classicGatherTarget") != "", "Release after an accepted gather keeps only the selected resource armed");
            Call(game, "StopCombatInput"); Check(Field<string>(game, "classicGatherTarget") == "", "Cancellation clears gathering as well as combat");
            GetWindow().Size = new Vector2I(1280, 720); GetWindow().ContentScaleSize = new Vector2I(1280, 720);
            settings.SetValue("hud", "focus_world", false); Call(game, "ApplyFocusHud"); Call(game, "UpdateHud");
            Check(((Control)game.FindChild("VitalsAndObjectives", true, false)!).Visible, "Expanded HUD can be restored without rebuilding or relogging");
            await CheckUrgentLootPresentation(game, snapshot);
            await NativeTestLifetime.ReleaseSceneAsync(this, game); game = null;
            GD.Print($"CLASSIC_EXPERIENCE_CONTRACT: {checks} checks passed. Native fixtures; PostgreSQL/live account play remains separate.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CLASSIC_EXPERIENCE_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this, game);
            GetTree().Quit(1);
        }
    }
}
