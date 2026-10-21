using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Native draw and state-machine fixtures; not an account gameplay or artistic sign-off.</summary>
public partial class CharacterPresentationContract : Node
{
    private int checks;
    private void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS CHARACTER NATIVE: " + message);
    }
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private static (int State, int Direction, int Frame, Point Position) Pose(WorldView world, string id, Point at)
        => ((int, int, int, Point))typeof(WorldView).GetMethod("Pose", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(world, [id, at])!;
    private static bool Drawn(WorldView world, string kind, string id)
    {
        var visuals = (System.Collections.IEnumerable)typeof(WorldView).GetField("visuals", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
        return visuals.Cast<object>().Any(visual => (string)visual.GetType().GetProperty("Kind")!.GetValue(visual)! == kind
            && (string)visual.GetType().GetProperty("Id")!.GetValue(visual)! == id);
    }
    private static double StateUntil(WorldView world, string id)
    {
        var tracks = (System.Collections.IDictionary)typeof(WorldView).GetField("tracks", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
        var track = tracks[id]!;
        return (double)track.GetType().GetField("StateUntil")!.GetValue(track)!;
    }
    private static Point SnapshotVelocity(WorldView world, string id)
    {
        var tracks = (System.Collections.IDictionary)typeof(WorldView).GetField("tracks", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
        var track = tracks[id]!;
        return (Point)track.GetType().GetField("SnapshotVelocity")!.GetValue(track)!;
    }
    private void CheckAuthoritativeMotion(WorldView world, Snapshot initial)
    {
        world.ClearSession(); var sample = Wire.Copy(initial); sample.Time = 10;
        sample.Creatures = [new Creature { Id = "native-stop-resume-mob", Template = "field_rat", Zone = sample.Self.Zone,
            Position = sample.Self.Position.Add(new Point(1, 1)), Health = 20 }];
        string remoteId = sample.Players.First().Id, mobId = sample.Creatures[0].Id;
        string[] actors = [sample.Self.Id, remoteId, mobId];
        void MoveActors(Snapshot snapshot)
        {
            var step = new Point(.3, 0);
            snapshot.Self.Position = snapshot.Self.Position.Add(step);
            foreach (var player in snapshot.Players) player.Position = player.Position.Add(step);
            foreach (var creature in snapshot.Creatures) creature.Position = creature.Position.Add(step);
        }
        world.Accept(new TransportPacket { Snapshot = sample }); world.SetLocalMovementIntent(new Vector2(1, 0));
        sample = Wire.Copy(sample); sample.Time = 10.1; MoveActors(sample);
        world.Accept(new TransportPacket { Snapshot = sample });
        var velocity = SnapshotVelocity(world, sample.Self.Id);
        Check(velocity.X > 1 && Math.Abs(velocity.Y) < .001,
            "Coalesced snapshots estimate local velocity from authoritative sample time even without a renderer clock advance");
        sample = Wire.Copy(sample); sample.Time = 10.2; world.Accept(new TransportPacket { Snapshot = sample });
        Check(SnapshotVelocity(world, sample.Self.Id) == velocity,
            "One unchanged authoritative sample preserves visual travel across an interstitial packet");
        world.Accept(new TransportPacket { Snapshot = sample });
        Check(SnapshotVelocity(world, sample.Self.Id) == velocity,
            "A duplicate authoritative timestamp cannot count as a second unchanged movement sample");
        Check(actors.All(id => SnapshotVelocity(world, id).X > 1),
            "Remote players and creatures also retain velocity through one interstitial sample and its duplicate");
        sample = Wire.Copy(sample); sample.Time = 10.3; world.Accept(new TransportPacket { Snapshot = sample });
        Check(SnapshotVelocity(world, sample.Self.Id) == default(Point),
            "Two genuinely newer unchanged authoritative samples clear stale local velocity");
        Check(actors.All(id => SnapshotVelocity(world, id) == default(Point)),
            "The same two-sample stationary contract clears remote-player and creature estimates");
        sample = Wire.Copy(sample); sample.Time = 10.4; MoveActors(sample);
        world.Accept(new TransportPacket { Snapshot = sample });
        Check(SnapshotVelocity(world, sample.Self.Id).X > 1, "A new authoritative position change restores the visual movement estimate");
        Check(actors.All(id => SnapshotVelocity(world, id).X > 1),
            "The first resumed step uses the confirmed stationary baseline for every actor type");
        double unchangedRenderClock = world.Clock;
        for (int i = 5; i <= 15; i++)
        {
            sample = Wire.Copy(sample); sample.Time = 10 + i * .1;
            world.Accept(new TransportPacket { Snapshot = sample });
        }
        Check(world.Clock == unchangedRenderClock && actors.All(id => SnapshotVelocity(world, id) == default(Point)),
            "Coalesced authoritative snapshots can confirm a long stop without advancing the renderer clock");
        sample = Wire.Copy(sample); sample.Time = 11.6; MoveActors(sample);
        world.Accept(new TransportPacket { Snapshot = sample });
        Check(actors.All(id => SnapshotVelocity(world, id).X > 1),
            "Movement resumes on its first authoritative step after a long stop even with no render-clock advance");
        world.SetLocalMovementIntent(Vector2.Zero); world.SetLocalMovementIntent(new Vector2(1, 0));
        Check(SnapshotVelocity(world, sample.Self.Id) == default(Point),
            "A release and immediate tap cannot reuse the previous local velocity before a new authoritative sample");
        world.SetLocalMovementIntent(new Vector2(float.NaN, 1));
        var intent = (Vector2)typeof(WorldView).GetField("localMovementIntent", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
        Check(intent == Vector2.Zero, "Malformed local intent resets to the definitive zero movement vector");
        world.SetLocalMovementIntent(new Vector2(3, 4));
        intent = (Vector2)typeof(WorldView).GetField("localMovementIntent", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
        Check(Math.Abs(intent.Length() - 1) < .000001, "Local presentation intent normalizes oversized input without changing server positions");
        world.ClearSession(); world.Accept(new TransportPacket { Snapshot = initial });
    }
    private async Task Render(WorldView world)
    {
        world.QueueRedraw(); await Frame();
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
    }
    private async Task CheckOpeningGrass(WorldView world, Catalog data)
    {
        var zone = data.Zone("wayfarers_rest");
        int patch = ClassicTerrainRules.GrassVariant(zone, 40, 48);
        Check(Enumerable.Range(40, 4).All(x => Enumerable.Range(48, 4).All(y => ClassicTerrainRules.GrassVariant(zone, x, y) == patch)),
            "Opening grass variation forms stable four-tile patches instead of changing every tile");
        Check(Enumerable.Range(0, 64).Select(x => ClassicTerrainRules.GrassVariant(zone, x * 4, 52)).Distinct().Count() == 4,
            "Opening grass patches retain four deterministic surface variants");
        var glade = new ZoneDef { Id = ClassicTutorialContent.ZoneId, Seed = 107 };
        int lessonPatch = ClassicTerrainRules.GrassVariant(glade, 12, 12);
        Check(ClassicTerrainRules.IsOpeningRegion(glade)
            && Enumerable.Range(12, 4).All(x => Enumerable.Range(12, 4).All(y => ClassicTerrainRules.GrassVariant(glade, x, y) == lessonPatch)),
            "The optional lesson glade shares quieter stable patches around its interaction objects");
        var other = data.Zones.First(candidate => candidate.Id != zone.Id && candidate.Kind != "interior");
        Check(Enumerable.Range(0, 32).All(x => ClassicTerrainRules.GrassVariant(other, x, 12) == (int)(WorldMap.Hash(x, 12, other.Seed) % 4)),
            "Grass variation outside the opening retains the existing tile selection");
        var textureMethod = typeof(WorldView).GetMethod("ClassicGrass", BindingFlags.Instance | BindingFlags.NonPublic)!;
        byte[]? edgePixels = null;
        for (int variant = 0; variant < 4; variant++)
        {
            var texture = (Texture2D)textureMethod.Invoke(world, [variant, true])!;
            Check(ReferenceEquals(texture, textureMethod.Invoke(world, [variant, true])),
                "Opening grass reuses its generated texture cache: " + variant);
            using var image = texture.GetImage();
            Check(image.GetSize() == new Vector2I(32, 32) && Enumerable.Range(0, 32).All(y => Enumerable.Range(0, 32).All(x => image.GetPixel(x, y).A == 1)),
                "Opening grass keeps its opaque native tile dimensions: " + variant);
            Check(Enumerable.Range(0, 32).All(i => image.GetPixel(i, 0) == image.GetPixel(i, 31) && image.GetPixel(0, i) == image.GetPixel(31, i)),
                "Opening grass wraps both texture edges without a seam: " + variant);
            var edges = new List<byte>();
            for (int i = 0; i < 32; i++)
                foreach (var pixel in new[] { image.GetPixel(i, 0), image.GetPixel(0, i) })
                    edges.AddRange([(byte)MathF.Round(pixel.R * 255), (byte)MathF.Round(pixel.G * 255), (byte)MathF.Round(pixel.B * 255)]);
            if (edgePixels is null) edgePixels = edges.ToArray();
            else Check(edges.SequenceEqual(edgePixels), "All opening grass variants share matching boundary pixels: " + variant);
            int transitions = 0;
            for (int y = 0; y < 32; y++) for (int x = 0; x < 32; x++)
            {
                if (x < 31 && image.GetPixel(x, y) != image.GetPixel(x + 1, y)) transitions++;
                if (y < 31 && image.GetPixel(x, y) != image.GetPixel(x, y + 1)) transitions++;
            }
            Check(transitions < 400, "Opening grass uses connected low-frequency color clusters: " + variant);
            var legacy = (Texture2D)textureMethod.Invoke(world, [variant, false])!;
            Check(!ReferenceEquals(texture, legacy), "Opening and legacy grass caches do not alias: " + variant);
        }
        bool classic = world.ClassicPresentation;
        world.ClassicPresentation = true; await Render(world); await Capture("character-opening-grass");
        Check(WorldSurfaceRules.Surface(zone, (int)zone.Spawn.X, (int)zone.Spawn.Y) == Terrain.Stone
            && WorldSurfaceRules.Surface(zone, (int)zone.Spawn.X, (int)zone.Spawn.Y + 8) == Terrain.Dirt,
            "Opening grass presentation preserves the spawn paving and road surfaces");
        world.ClassicPresentation = classic; await Render(world);
    }
    private void CheckCharacterScale(Catalog data, Character ordinary)
    {
        Check(SpritePoseRules.CharacterScale(data, ordinary) == 1, "Ordinary world characters retain their exact original render scale");
        var optional = Wire.Copy(data); ClassicTutorialContent.Enable(optional);
        var accepted = Wire.Copy(ordinary); accepted.ClassicTutorial = new();
        Check(Math.Abs(SpritePoseRules.CharacterScale(optional, accepted) - .8f) < .000001,
            "An accepted tutorial character consumes the server's default avatar scale");
        Check(SpritePoseRules.CharacterScale(optional, ordinary) == 1 && SpritePoseRules.CharacterScale(data, accepted) == 1
            && SpritePoseRules.CharacterScale(optional, null) == 1,
            "A tutorial catalog or character alone cannot shrink an ordinary session or preview");
        var feet = new Vector2(320, 256);
        var original = new Rect2(feet - new Vector2(32, 55), new Vector2(64, 64));
        Check(SpritePoseRules.FrameDestination(feet, 64, 0, 64) == original,
            "Default sprite destinations preserve every original pixel coordinate");
        foreach (float scale in new[] { .5f, .8f, 1f })
        {
            optional.ClassicTutorial!.AvatarScale = scale;
            Check(SpritePoseRules.CharacterScale(optional, accepted) == scale, "Accepted avatar tuning reaches the renderer: " + scale);
            var whole = SpritePoseRules.FrameDestination(feet, 64, 0, 64, scale);
            var upper = SpritePoseRules.FrameDestination(feet, 64, 0, SpritePoseRules.WaistCut, scale);
            var lower = SpritePoseRules.FrameDestination(feet, 64, SpritePoseRules.WaistCut, 64, scale);
            Check((whole.Position + SpritePoseRules.Anchor(64) * scale).DistanceTo(feet) < .001f
                && whole.Size == new Vector2(64, 64) * scale,
                "Scaled body, hair and equipment share the same unchanged world floor point: " + scale);
            Check(Math.Abs(upper.End.Y - lower.Position.Y) < .001f && upper.Position.X == lower.Position.X
                && upper.Size.X == lower.Size.X && Math.Abs(lower.End.Y - whole.End.Y) < .001f,
                "Upper-body action and grounded locomotion slices remain joined at every avatar scale: " + scale);
        }
        foreach (double invalid in new[] { double.NaN, double.PositiveInfinity, .49, 1.01 })
        {
            optional.ClassicTutorial!.AvatarScale = invalid;
            Check(SpritePoseRules.CharacterScale(optional, accepted) == 1,
                "Invalid avatar tuning safely preserves ordinary destination geometry: " + invalid);
        }
        Check(SpritePoseRules.FrameDestination(feet, 64, 0, 64, float.NaN) == original,
            "Invalid direct presentation scale never produces a nonfinite draw rectangle");
    }

    private void CheckCurrentVisibleImport(PixelAssets assets, string key, Vector2I size)
    {
        var texture = assets.Texture(key);
        Check(texture is not null && texture.GetWidth() == size.X && texture.GetHeight() == size.Y,
            "The native opening view loads the authored texture dimensions: " + key);
        using var source = new Image();
        Check(source.LoadPngFromBuffer(Godot.FileAccess.GetFileAsBytes("res://Assets/" + key + ".png")) == Error.Ok,
            "The opening art comparison reads its actual source PNG: " + key);
        using var imported = texture!.GetImage();
        bool equal = source.GetSize() == imported.GetSize();
        for (int y = 0; equal && y < size.Y; y++) for (int x = 0; x < size.X; x++)
        {
            var expected = source.GetPixel(x, y); var actual = imported.GetPixel(x, y);
            if (expected.A != actual.A || expected.A > 0 && expected != actual) { equal = false; break; }
        }
        Check(equal, "The native texture preserves source alpha and every visible source pixel: " + key);
    }

    private async Task CheckOpeningArtView(WorldView world, Snapshot initial, Catalog data)
    {
        var snapshot = Wire.Copy(initial); snapshot.Self.Position = data.Zone("wayfarers_rest").Spawn;
        snapshot.Self.Zone = "wayfarers_rest"; snapshot.Players.Clear(); snapshot.Creatures.Clear(); snapshot.Nodes.Clear(); snapshot.Chests.Clear();
        float zoom = world.Zoom; bool classic = world.ClassicPresentation;
        world.ClearSession(); world.Zoom = 1; world.ClassicPresentation = true; world.Accept(new TransportPacket { Snapshot = snapshot });
        OpeningArtReviewLegend? legend = null;
        try
        {
            foreach (var building in data.Zone("wayfarers_rest").Buildings)
                CheckCurrentVisibleImport(world.Assets, "buildings/wayfarers_rest/" + building.Id, new Vector2I(224, 224));
            foreach (string rune in OpeningArtReviewLegend.Runes)
                CheckCurrentVisibleImport(world.Assets, "items/" + rune, new Vector2I(32, 32));
            legend = new OpeningArtReviewLegend { Assets = world.Assets, Position = new Vector2(380, 965), Size = new Vector2(1160, 102) };
            AddChild(legend); await Render(world);
            Check(data.Zone("wayfarers_rest").Buildings.All(building => Drawn(world, "building", building.Id)),
                "A native one-pixel town view draws all four varied opening facades");
            foreach (var building in data.Zone("wayfarers_rest").Buildings)
            {
                var topLeft = world.WorldToScreen(new Point(building.X, building.Y - 2));
                Check(topLeft.X >= 0 && topLeft.Y >= 0 && topLeft.X + 224 <= world.Size.X && topLeft.Y + 224 <= world.Size.Y,
                    "The opening facade is fully inside the native viewport: " + building.Id);
            }
            Check(world.Assets.Missing.Count == 0, "Native facade and rune review uses every actual texture without a missing request");
            await Capture("character-opening-facades-runes");
        }
        finally
        {
            if (legend is not null && GodotObject.IsInstanceValid(legend)) { legend.QueueFree(); await Frame(); await Frame(); }
            world.ClearSession(); world.Zoom = zoom; world.ClassicPresentation = classic; world.Accept(new TransportPacket { Snapshot = initial });
            await Render(world);
        }
    }

    private async Task CheckTutorialObjects(WorldView world, Snapshot initial, Catalog data)
    {
        var spriteMethod = typeof(WorldView).GetMethod("ResourceSpriteKey", BindingFlags.Instance | BindingFlags.NonPublic)!;
        var furnishingMethod = typeof(WorldView).GetMethod("ClassicTutorialFurnishing", BindingFlags.Instance | BindingFlags.NonPublic)!;
        string Key(string template) => (string)spriteMethod.Invoke(world, [template])!;
        Texture2D? Texture(FurnishingDef furnishing) => (Texture2D?)furnishingMethod.Invoke(world, [furnishing]);
        Check(data.Resources.All(resource => Key(resource.Id) == "resources/" + resource.Id),
            "Every ordinary resource retains its shipped template key rather than a missing historical Sprite path");
        Check(Key("oak_tree") == "resources/oak_tree" && Key("copper_vein") == "resources/copper_vein"
            && Key("structure_campfire") == "structures/structure_campfire",
            "Ordinary oak, copper and structure rendering keys are unchanged");
        var optional = Wire.Copy(data); ClassicTutorialContent.Enable(optional);
        var realm = new RealmEngine(optional);
        var player = realm.CreateCharacter("native-tutorial-art", "Native Tutorial Art", "vanguard", new());
        player.Position = new Point(18.5, 14.5); realm.Active.Add(player.Id);
        var snapshot = realm.Snapshot(player.Id);
        foreach (var mob in snapshot.Creatures) mob.NextAttack = snapshot.Time + 5;
        bool classic = world.ClassicPresentation; float zoom = world.Zoom;
        world.ClearSession(); world.Data = optional; world.Assets.BindCatalog(optional); world.Zoom = 2;
        world.ClassicPresentation = false; world.Accept(new TransportPacket { Snapshot = snapshot });
        var zone = optional.Zone(ClassicTutorialContent.ZoneId);
        var cachedBodyFrame = world.Assets.Frame("people/body_0_0", 0, 0, 0);
        var authoritativePosition = snapshot.Self.Position;
        var projectedFeet = world.WorldToScreen(authoritativePosition);
        var interactionTargets = world.Targets.ToArray();
        var pickTarget = interactionTargets.First(target => target.Kind == "node");
        var projectedTarget = world.WorldToScreen(pickTarget.Position);
        var originalHit = world.Pick(projectedTarget);
        optional.ClassicTutorial!.AvatarScale = 1; await Render(world);
        await Capture("character-tutorial-avatar-full");
        optional.ClassicTutorial.AvatarScale = .8; await Render(world);
        await Capture("character-tutorial-avatar-scaled");
        Check(snapshot.Self.Position == authoritativePosition && world.WorldToScreen(authoritativePosition) == projectedFeet
            && world.Targets.SequenceEqual(interactionTargets) && originalHit?.Id == pickTarget.Id && world.Pick(projectedTarget) == originalHit,
            "Real avatar rescaling preserves authoritative floor, pointer-hit and interaction target anchors");
        Check(ReferenceEquals(cachedBodyFrame, world.Assets.Frame("people/body_0_0", 0, 0, 0)),
            "Real avatar rescaling preserves cached source texture and atlas identities");
        foreach (var furnishing in zone.Furnishings)
        {
            var texture = Texture(furnishing);
            Check(texture is not null && texture.GetWidth() == 32 && texture.GetHeight() == 56,
                "The tutorial object has a native one-tile canvas and its authored rise: " + furnishing.Id);
            Check(ReferenceEquals(texture, Texture(furnishing)), "Tutorial object construction reuses the generated cache: " + furnishing.Id);
            using var image = texture!.GetImage();
            Check(Enumerable.Range(0, 32).All(x => image.GetPixel(x, 0).A == 0)
                && Enumerable.Range(0, 56).All(y => image.GetPixel(0, y).A == 0 && image.GetPixel(31, y).A == 0)
                && image.GetPixel(16, 55).A > 0,
                "The tutorial object keeps transparent borders and a visible ground foot: " + furnishing.Id);
            Check(furnishing.Width == 1 && furnishing.Height == 1 && furnishing.Solid
                && furnishing.Y * WorldMap.TileSize - furnishing.Rise + texture.GetHeight() == (furnishing.Y + furnishing.Height) * WorldMap.TileSize,
                "The object canvas ends at its unchanged server floor footprint: " + furnishing.Id);
            if (furnishing.Kind == "classic_sign")
                Check(image.GetPixel(4, 16).A == 1 && image.GetPixel(15, 45).A == 1
                    && image.GetPixel(4, 45).A == 0 && image.GetPixel(8, 16) != image.GetPixel(5, 16),
                    "Sign construction separates a readable plank board, light markings and a narrow grounded post");
            else
                Check(image.GetPixel(13, 18).A == 1 && image.GetPixel(5, 43).A == 1
                    && image.GetPixel(7, 18).A == 0 && image.GetPixel(12, 33).B > image.GetPixel(12, 33).R
                    && image.GetPixel(16, 22) != image.GetPixel(13, 22),
                    "Fountain construction separates the stone spout, basin wall, blue water and falling stream");
        }
        foreach (var (template, expected) in new[] {
            ("classic_tree", "resources/oak_tree"), ("classic_stone_node", "resources/copper_vein"),
            ("classic_tinder_node", "resources/meadow_leaf_patch"), ("classic_flint_node", "resources/copper_vein") })
        {
            string key = Key(template);
            Check(key == expected && world.Assets.Texture(key) is not null,
                "Tutorial resource declares a real shipped non-actor sprite: " + template);
        }
        Check(optional.Item("classic_tinder").Icon == "meadow_leaf" && optional.Resource("classic_tinder_node").Item == "classic_tinder"
            && world.Assets.Icon("classic_tinder") == world.Assets.Texture("items/meadow_leaf"),
            "Tinder uses its existing plant art while retaining the tutorial item and reward identity");
        var tinder = optional.Resource("classic_tinder_node"); tinder.Sprite = "resources/meadow_leaf_patch.png";
        Check(Key(tinder.Id) == "resources/meadow_leaf_patch", "Path-form tutorial Sprite aliases normalize to the same shipped resource key");
        tinder.Sprite = "../meadow_leaf_patch.png";
        bool unsafeRejected = false;
        try { Key(tinder.Id); } catch (TargetInvocationException error) when (error.InnerException is InvalidDataException) { unsafeRejected = true; }
        Check(unsafeRejected, "Tutorial Sprite normalization preserves strict traversal rejection");
        tinder.Sprite = "meadow_leaf_patch";
        Check(data.Resources.All(resource => Key(resource.Id) == "resources/" + resource.Id),
            "Optional mode also preserves all ordinary resource rendering keys");
        var sign = zone.Furnishings.First(f => f.Kind == "classic_sign");
        var mismatched = Wire.Copy(sign); mismatched.Width = 2;
        Check(Texture(mismatched) is null && Texture(new FurnishingDef { Kind = "classic_sign", Rise = 24 }) is null,
            "Procedural tutorial art cannot mask unknown sites or mismatched floor footprints");
        await Render(world);
        Check(zone.Furnishings.All(f => Drawn(world, "furnishing", f.Id)) && snapshot.Nodes.All(node => Drawn(world, "node", node.Id)),
            "The real optional viewport draws all authored sites and resources with expanded presentation");
        Check(world.Assets.Missing.Count == 0, "Tutorial object and resource rendering records no missing texture keys");
        await Capture("character-tutorial-objects-expanded");
        world.ClassicPresentation = true; await Render(world); await Capture("character-tutorial-objects-classic");
        var tree = snapshot.Nodes.First(node => node.Template == "classic_tree"); tree.ReadyAt = snapshot.Time + 3;
        world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(Drawn(world, "node", tree.Id) && world.Assets.Missing.Count == 0,
            "Depleted aliased tutorial trees keep their existing stump presentation without a missing request");
        world.ClearSession(); world.Data = data; world.Assets.BindCatalog(data); world.Zoom = zoom; world.ClassicPresentation = classic;
        world.Accept(new TransportPacket { Snapshot = initial });
        Check(Texture(sign) is null, "Tutorial object art is restricted to the accepted optional zone and catalog");
        await Render(world);
    }

    private async Task CheckMobCorpses(WorldView world, Snapshot initial, Catalog data)
    {
        var snapshot = Wire.Copy(initial); var at = snapshot.Self.Position;
        var pending = new Creature
        {
            Id = "native-pending-rare", Template = "rare_field_rat", Zone = snapshot.Self.Zone,
            Position = at.Add(new Point(-2, 0)), Home = at.Add(new Point(-2, 0)),
            Health = 0, Generation = 0, RespawnAt = snapshot.Time + 120, NextAttack = snapshot.Time + 5
        };
        var oldDead = new Creature
        {
            Id = "native-unwitnessed-death", Template = "field_rat", Zone = snapshot.Self.Zone,
            Position = at.Add(new Point(2, 0)), Home = at.Add(new Point(2, 0)),
            Health = 0, Generation = 7, RespawnAt = snapshot.Time + 20, NextAttack = snapshot.Time + 5
        };
        var witnessed = new Creature
        {
            Id = "native-witnessed-death", Template = "field_rat", Zone = snapshot.Self.Zone,
            Position = at.Add(new Point(0, 2)), Home = at.Add(new Point(0, 2)),
            Health = data.Mob("field_rat").Health, Generation = 3, NextAttack = snapshot.Time + 5
        };
        snapshot.Creatures = [pending, oldDead, witnessed];
        world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(!Drawn(world, "creature", pending.Id), "A Generation 0 deferred rare spawn never appears as a fabricated corpse");
        Check(!Drawn(world, "creature", oldDead.Id), "An unwitnessed dead mob is hidden without a reliable death time");
        Check(Drawn(world, "creature", witnessed.Id), "The same first snapshot renders a living creature normally");
        Check(!world.Targets.Any(x => x.Id == pending.Id || x.Id == oldDead.Id), "Pending and dead mobs are absent from interaction targets");
        world.Animate(pending.Id, 5, 6); await Render(world);
        Check(!Drawn(world, "creature", pending.Id), "A presentation-only animation request cannot fabricate a pending spawn's death");
        await Capture("character-mob-pending-spawn");

        double deathStarted = world.Clock;
        witnessed.Health = 0; witnessed.Generation++; witnessed.RespawnAt = snapshot.Time + 25;
        world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(Drawn(world, "creature", witnessed.Id) && Pose(world, witnessed.Id, witnessed.Position).State == 5
            && Pose(world, witnessed.Id, witnessed.Position).Frame == 0,
            "An authoritative living-to-dead transition renders the first collapse frame");
        double deadline = StateUntil(world, witnessed.Id);
        Check(Math.Abs(deadline - deathStarted - 6) < .000001, "Witnessed creature remains retain the existing six-second presentation lifetime");
        Check(!world.Targets.Any(x => x.Id == witnessed.Id), "A visible corpse cannot remain a combat interaction target");
        await Capture("character-mob-collapse");
        world._Process(.2); world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(Pose(world, witnessed.Id, witnessed.Position).Frame is > 0 and < 7,
            "A witnessed mob collapse advances through its intermediate frames");
        Check(StateUntil(world, witnessed.Id) == deadline, "Repeating a dead snapshot does not renew its corpse lifetime");
        witnessed.Health = -2; world.Accept(new TransportPacket { Snapshot = snapshot });
        Check(StateUntil(world, witnessed.Id) == deadline, "A later dead-health change cannot restart the corpse animation or lifetime");
        witnessed.Health = 0; world.Accept(new TransportPacket { Snapshot = snapshot });
        world._Process(.6); await Render(world);
        Check(Drawn(world, "creature", witnessed.Id) && Pose(world, witnessed.Id, witnessed.Position).Frame == 7,
            "Witnessed mob remains hold the final corpse pose after collapse");
        await Capture("character-mob-remains");
        world._Process(deadline - world.Clock); await Render(world);
        Check(!Drawn(world, "creature", witnessed.Id), "Witnessed remains disappear at the six-second deadline");
        world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(!Drawn(world, "creature", witnessed.Id) && StateUntil(world, witnessed.Id) == deadline,
            "A still-dead snapshot cannot restore expired remains");
        await Capture("character-mob-remains-expired");

        world.ClearSession(); world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(snapshot.Creatures.All(mob => !Drawn(world, "creature", mob.Id)), "Reconnect clears death witnesses and cannot give old dead mobs a fresh corpse lifetime");
        Check(Drawn(world, "self", snapshot.Self.Id) && snapshot.Players.All(player => Drawn(world, "player", player.Id)),
            "Creature corpse suppression preserves local and remote player rendering");
        await Capture("character-mob-reconnect");
        witnessed.Health = data.Mob(witnessed.Template).Health; world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(Drawn(world, "creature", witnessed.Id) && Pose(world, witnessed.Id, witnessed.Position).State == 0,
            "A respawned creature returns to living idle presentation without stale corpse state");
        world._Process(.1); witnessed.Health = 0; witnessed.Generation++; world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(Drawn(world, "creature", witnessed.Id) && Pose(world, witnessed.Id, witnessed.Position).Frame == 0
            && StateUntil(world, witnessed.Id) > deadline,
            "A witnessed death after respawn starts its own fresh collapse and lifetime");
        var outsideVisibility = Wire.Copy(snapshot); outsideVisibility.Creatures.RemoveAll(mob => mob.Id == witnessed.Id);
        world.Accept(new TransportPacket { Snapshot = outsideVisibility }); await Render(world);
        Check(!Drawn(world, "creature", witnessed.Id), "A mob leaving snapshot visibility clears its retained corpse presentation");
        world.Accept(new TransportPacket { Snapshot = snapshot }); await Render(world);
        Check(!Drawn(world, "creature", witnessed.Id), "Returning visibility with only a dead snapshot cannot reconstruct an unwitnessed corpse lifetime");
        world.ClearSession(); world.Accept(new TransportPacket { Snapshot = initial });
    }
    private async Task Capture(string name)
    {
        await Frame(); await Frame();
        if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("This contract requires a native rendered viewport.");
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS") ?? ProjectSettings.GlobalizePath("user://character-review");
        System.IO.Directory.CreateDirectory(root);
        using var image = GetViewport().GetTexture().GetImage();
        Check(image.SavePng(System.IO.Path.Combine(root, name + ".png")) == Error.Ok, "Saved native viewport " + name);
    }

    public override async void _Ready()
    {
        WorldView? world = null; CharacterMotionGallery? gallery = null;
        try
        {
            GetWindow().Size = new Vector2I(1920, 1080);
            GetWindow().ContentScaleSize = new Vector2I(1920, 1080);
            var assets = new PixelAssets(); var data = PixelAssets.LoadCatalog();
            var estimatedVelocity = MotionPresentationRules.EstimateVelocity(new Point(0, 0), new Point(.4, 0), .1, new Point(0, 0));
            Check(estimatedVelocity.X > 2 && estimatedVelocity.X < 4.1 && Math.Abs(estimatedVelocity.Y) < .001,
                "Snapshot velocity estimation smooths a 10 Hz authoritative movement sample");
            var led = MotionPresentationRules.VisualTarget(new Point(1, 1), new Point(3, 0), .09);
            Check(led.X > 1 && led.X <= 1 + MotionPresentationRules.MaxLeadTiles + .0001,
                "Remote visual extrapolation is positive and bounded by the presentation-only lead cap");
            double freshnessMidpoint = (MotionPresentationRules.SnapshotFreshSeconds + MotionPresentationRules.SnapshotStaleSeconds) / 2;
            Check(MotionPresentationRules.SnapshotFreshness(MotionPresentationRules.SnapshotFreshSeconds) == 1
                && MotionPresentationRules.SnapshotFreshness(freshnessMidpoint) is > 0 and < 1
                && MotionPresentationRules.SnapshotFreshness(MotionPresentationRules.SnapshotStaleSeconds + .01) == 0,
                "Snapshot extrapolation fades to zero after the configured short network stall window");
            var localLed = MotionPresentationRules.VisualTarget(
                new Point(1, 1), new Point(3, 0), .01, .12, new Point(1, 0));
            Check(localLed.X > led.X && localLed.X <= 1 + MotionPresentationRules.LocalIntentMaxLeadTiles + .0001,
                "Held local intent preserves bounded visual continuity across an unchanged packet");
            var released = MotionPresentationRules.VisualTarget(
                new Point(1, 1), new Point(3, 0), .01, .12, new Point(0, 0));
            Check(released.Distance(new Point(1, 1)) < .000001,
                "Released local intent suppresses extrapolation immediately");
            var projectile = new Telegraph { Shape = "projectile", Target = "native-projectile-target", Origin = new Point(1, 1), Position = new Point(5, 1), Started = 10, Resolves = 10.4, Element = Element.Physical };
            Check(ProjectilePresentationRules.Progress(projectile, 10) == 0
                && Math.Abs(ProjectilePresentationRules.Progress(projectile, 10.2) - .5) < .000001
                && ProjectilePresentationRules.Progress(projectile, 10.4) == 1,
                "Projectile presentation travels on the authoritative telegraph interval");
            Check(ProjectilePresentationRules.Travels(projectile)
                && ProjectilePresentationRules.Position(projectile, 10.2).Distance(new Point(3, 1)) < .000001,
                "Targeted projectile presentation preserves its authoritative origin and destination");
            var untargeted = new Telegraph { Shape = "projectile", Started = 10, Resolves = 10.4, Element = Element.Physical };
            Check(!ProjectilePresentationRules.Travels(untargeted)
                && Math.Abs(ProjectilePresentationRules.IntervalProgress(untargeted, 10.2) - .5) < .000001,
                "Untargeted spell telegraphs preserve their timed presentation without inventing an authoritative origin");
            Check(ProjectilePresentationRules.VisualElement("arcanist", Element.Physical) == Element.Arcane
                && ProjectilePresentationRules.VisualElement("templar", Element.Physical) == Element.Radiant
                && ProjectilePresentationRules.VisualElement("vanguard", Element.Physical) == Element.Physical,
                "Caster basics use arcane/holy visual language without changing server damage element");
            var snapped2 = MotionPresentationRules.SnapWorldPixel(new Vector2(10.24f, 20.26f), 2);
            var snapped3 = MotionPresentationRules.SnapWorldPixel(new Vector2(10.24f, 20.26f), 3);
            Check(Math.Abs(snapped2.X * 2 - MathF.Round(snapped2.X * 2)) < .0001f
                && Math.Abs(snapped3.Y * 3 - MathF.Round(snapped3.Y * 3)) < .0001f,
                "Dynamic actor coordinates align to final screen pixels at 2x and 3x zoom");
            var realm = new RealmEngine(data);
            var self = realm.CreateCharacter("native-motion-a", "Native Motion", "vanguard", new());
            var other = realm.CreateCharacter("native-motion-b", "Native Observer", "vanguard", new());
            realm.Active.Add(self.Id); realm.Active.Add(other.Id); other.Position = self.Position.Add(new Point(1, 0));
            world = new WorldView { Assets = assets, Data = data, WeatherEnabled = false };
            AddChild(world); world.SetProcess(false); await Frame();
            var snapshot = realm.Snapshot(self.Id);
            foreach (var mob in snapshot.Creatures) mob.NextAttack = snapshot.Time + 5;
            world.Accept(new TransportPacket { Snapshot = snapshot });
            foreach (var mob in snapshot.Creatures.Where(mob => mob.Health > 0))
                Check(Pose(world, mob.Id, mob.Position).State == 0, "Spawn cooldown does not invent an attack: " + mob.Id);
            CheckAuthoritativeMotion(world, snapshot);
            CheckCharacterScale(data, snapshot.Self);
            await CheckMobCorpses(world, snapshot, data);
            await CheckOpeningGrass(world, data);
            await CheckOpeningArtView(world, snapshot, data);
            await CheckTutorialObjects(world, snapshot, data);
            var remote = snapshot.Players.Single(p => p.Id == other.Id);
            snapshot.ActorCues.Add(new ActorPresentationCue { Actor = other.Id, Sequence = 1, State = 6, Started = snapshot.Time, Duration = .8, Facing = new(-1, 0) });
            world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).State == 6, "Remote interaction enters the explicit gesture state");
            world._Process(.3);
            int before = Pose(world, other.Id, other.Position).Frame;
            world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).Frame == before && before > 0, "Repeated snapshots do not restart an action");
            remote.Facing = new(1, 0); world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).Direction == 1, "Action facing remains stable through recovery");
            await Capture("character-remote-interaction");
            remote.Health = 0; world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).State == 5 && Pose(world, other.Id, other.Position).Frame == 0,
                "Remote death starts with collapse, not the last corpse frame");
            world._Process(.2);
            Check(Pose(world, other.Id, other.Position).Frame is > 0 and < 7, "Remote collapse advances through intermediate poses");
            world._Process(.6);
            Check(Pose(world, other.Id, other.Position).Frame == 7, "Remote corpse holds its final pose");
            await Capture("character-remote-corpse");
            remote.Health = remote.MaxHealth; snapshot.ActorCues.Clear(); world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).State != 5, "Respawn clears the terminal corpse state");
            world._Process(.10);
            remote.Position = remote.Position.Add(new Point(.3, 0)); world.Accept(new TransportPacket { Snapshot = snapshot });
            world._Process(.05);
            var firstInterpolated = Pose(world, other.Id, other.Position);
            world._Process(.04);
            var secondInterpolated = Pose(world, other.Id, other.Position);
            Check(firstInterpolated.State is 1 or 8 && secondInterpolated.Position.X > firstInterpolated.Position.X,
                "Rendered travel advances continuously between authoritative snapshots");
            Check(secondInterpolated.Position.Distance(remote.Position) <= MotionPresentationRules.MaxLeadTiles + .02,
                "Rendered interpolation stays within the bounded visual lead around authoritative position");
            world.Animate(other.Id, 2, .6); world._Process(1.0 / 60);
            int locomotion = (int)typeof(WorldView).GetMethod("LocomotionFrame", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(world, [other.Id])!;
            Check(locomotion >= 0 && Pose(world, other.Id, other.Position).State == 2, "Leg motion continues beneath an upper-body action");
            for (int i = 0; i < 120; i++) world._Process(1.0 / 60);
            Check(Pose(world, other.Id, other.Position).State == 0, "Stationary actors return to idle after stale visual velocity fades");
            snapshot.Players.Clear(); world.Accept(new TransportPacket { Snapshot = snapshot });
            var tracks = (System.Collections.IDictionary)typeof(WorldView).GetField("tracks", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
            Check(!tracks.Contains(other.Id), "Actors leaving visibility do not retain stale animation tracks");
            world.CombatImpact(self.Position); world.ClearSession();
            var bursts = (System.Collections.ICollection)typeof(WorldView).GetField("combatBursts", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
            Check(bursts.Count == 0 && world.Snapshot is null, "Logout clears actor and combat presentation state");
            world.QueueFree(); world = null; await Frame(); await Frame();
            gallery = new CharacterMotionGallery { Assets = assets, Data = data };
            AddChild(gallery); gallery.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect); await Frame();
            for (int state = 0; state <= 8; state++)
                for (int frame = 0; frame < 8; frame++)
                {
                    gallery.State = state; gallery.FrameNumber = frame; gallery.QueueRedraw();
                    await Capture($"character-state-{state}-frame-{frame}");
                }
            foreach (var item in data.Items.Where(i => i.Slot == "weapon" && i.Id.Contains("bow", StringComparison.OrdinalIgnoreCase)).Take(8))
            {
                var gear = new Dictionary<string, string> { ["weapon"] = item.Id };
                int pose = SpritePoseRules.WeaponPose(2, gear);
                Check(pose is 9 or 10, "Ranged weapons select their own articulated attack rig: " + item.Id);
                var frame = assets.Frame("people/body_0_0", pose, 2, 3);
                Check(frame is not null && frame.Region.Size == new Vector2(64, 64), "Ranged draw frame resolves a native-size atlas cell");
            }
            Check(assets.Missing.Count == 0, "All native action and equipment requests have an asset; no fallback was used");
            GD.Print($"CHARACTER_NATIVE_CONTRACT: {checks} checks passed; native frames, movement, remote actions, collapse, cleanup, and atlas routing.");
            gallery.QueueFree(); await Frame(); await Frame(); GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CHARACTER_NATIVE_FAILED: " + error);
            if (world is not null && GodotObject.IsInstanceValid(world)) world.QueueFree();
            if (gallery is not null && GodotObject.IsInstanceValid(gallery)) gallery.QueueFree();
            GetTree().Quit(1);
        }
    }
}

public partial class OpeningArtReviewLegend : Control
{
    public static readonly string[] Runes = ["rune_bulwark_1", "rune_echoes_1", "rune_embers_1", "rune_leeching_1", "rune_precision_1"];
    private static readonly string[] Labels = ["Bulwark", "Echoes", "Embers", "Leeching", "Precision"];
    public PixelAssets Assets { get; set; } = null!;
    public override void _Ready() { TextureFilter = TextureFilterEnum.Nearest; MouseFilter = MouseFilterEnum.Ignore; }
    public override void _Draw()
    {
        DrawRect(new Rect2(Vector2.Zero, Size), new Color("17231f"));
        var font = ThemeDB.FallbackFont;
        DrawString(font, new Vector2(14, 18), "ORIGINAL OPENING ART / native 32px + 2x inspection / runtime texture pixels", fontSize: 13, modulate: new Color("e8d7b0"));
        for (int i = 0; i < Runes.Length; i++)
        {
            var texture = Assets.Texture("items/" + Runes[i]);
            if (texture is null) continue;
            float x = 20 + i * 230;
            DrawTexture(texture, new Vector2(x, 37));
            DrawTextureRect(texture, new Rect2(new Vector2(x + 51, 24), new Vector2(64, 64)), false);
            DrawString(font, new Vector2(x + 122, 59), Labels[i], fontSize: 14, modulate: new Color("e8d7b0"));
        }
    }
}

public partial class CharacterMotionGallery : Control
{
    public PixelAssets Assets { get; set; } = null!;
    public Catalog Data { get; set; } = null!;
    public int State { get; set; }
    public int FrameNumber { get; set; }
    public override void _Ready() { TextureFilter = TextureFilterEnum.Nearest; MouseFilter = MouseFilterEnum.Ignore; }
    public override void _Draw()
    {
        DrawRect(new Rect2(Vector2.Zero, Size), new Color("171e2a"));
        var font = ThemeDB.FallbackFont;
        DrawString(font, new Vector2(40, 45), $"KAIRNFALL / NATIVE CHARACTER REVIEW / STATE {State} / FRAME {FrameNumber}", fontSize: 22, modulate: new Color("e8d7b0"));
        var classes = Data.Classes.ToArray();
        float cell = Math.Min(220, (Size.X - 80) / classes.Length);
        for (int i = 0; i < classes.Length; i++)
        {
            var cls = classes[i];
            DrawString(font, new Vector2(40 + i * cell, 90), cls.Name, fontSize: 18, modulate: new Color("e8d7b0"));
            var equipment = new Dictionary<string, string> { ["weapon"] = cls.Weapon, [Data.Item(cls.Armor).Slot] = cls.Armor };
            for (int direction = 0; direction < 4; direction++)
            {
                var feet = new Vector2(40 + i * cell + cell / 2, 245 + direction * 185);
                DrawSetTransform(feet.Round(), 0, new Vector2(2, 2));
                Assets.DrawPerson(this, new Appearance { Body = i % 2, Skin = i % 6, Hair = i % 6, HairColor = i % 8 }, equipment,
                    Vector2.Zero, State, direction, FrameNumber);
                DrawSetTransform(Vector2.Zero);
            }
        }
    }
}
