using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public readonly record struct WorldTarget(string Kind, string Id, string Name, Point Position);

public partial class WorldView : Control
{
    public PixelAssets Assets { get; set; } = null!;
    public Catalog Data { get; set; } = null!;
    public Snapshot? Snapshot { get; private set; }
    public List<LootPile> Loot { get; private set; } = [];
    public string PreviewZone { get; set; } = "wayfarers_rest";
    public string TargetId { get; set; } = "";
    public Point? Waypoint { get; set; }
    public float Zoom { get; set; } = 2;
    public bool ShowNames { get; set; } = true;
    public bool WeatherEnabled { get; set; } = true;
    public double Clock { get; private set; }
    public Point Camera { get; private set; }
    public string ZoneId => Snapshot?.Self.Zone ?? PreviewZone;
    public double RealmTime => (Snapshot?.Time ?? 370) + sinceSnapshot;
    private double sinceSnapshot;
    private string lastZone = "";
    private readonly Dictionary<string, ActorTrack> tracks = [];
    private readonly List<FloatingNumber> numbers = [];
    private readonly List<Visual> visuals = [];
    private readonly List<WorldTarget> interactions = [];
    private Vector2 origin;
    private const float Tile = WorldMap.TileSize;

    private sealed class ActorTrack
    {
        public Point Position;
        public Point Target;
        public Point Facing = new(0, 1);
        public double LastMoved;
        public double WalkPhase;
        public int FacingDirection;
        public double Health;
        public double LastAttack;
        public double StateStart;
        public double StateUntil;
        public int State;
    }
    private sealed record FloatingNumber(Point At, string Text, Color Color, double Started);
    private readonly record struct Visual(float Depth, string Kind, string Id, Point At, object? Value = null);

    public override void _Ready()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.Nearest;
        ClipContents = true;
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
    }

    public void ClearSession()
    {
        Snapshot = null; Loot.Clear(); tracks.Clear(); interactions.Clear(); numbers.Clear(); lastZone = ""; TargetId = ""; Waypoint = null;
    }

    public void Accept(TransportPacket packet)
    {
        if (packet.Snapshot is not { } snapshot) return;
        if (snapshot.Self.Zone != lastZone)
        {
            tracks.Clear(); numbers.Clear(); TargetId = ""; Waypoint = null;
            Camera = snapshot.Self.Position; lastZone = snapshot.Self.Zone;
        }
        Snapshot = snapshot; sinceSnapshot = 0;
        Loot = packet.Loot ?? [];
        Track(snapshot.Self.Id, snapshot.Self.Position, snapshot.Self.Facing, snapshot.Self.Health);
        foreach (var player in snapshot.Players) Track(player.Id, player.Position, player.Facing, player.Health);
        foreach (var creature in snapshot.Creatures)
        {
            var track = Track(creature.Id, creature.Position, creature.Facing, creature.Health);
            if (creature.NextAttack > track.LastAttack + .01 && creature.Health > 0)
            {
                track.LastAttack = creature.NextAttack;
                Animate(creature.Id, 2, .6);
            }
        }
    }

    private ActorTrack Track(string id, Point position, Point facing, double health)
    {
        if (!tracks.TryGetValue(id, out var track))
        {
            track = new ActorTrack { Position = position, Target = position, Facing = facing, FacingDirection = SpritePoseRules.Direction(facing, 0), Health = health, LastMoved = -10 };
            tracks[id] = track;
        }
        if (track.Target.Distance(position) > .008) track.LastMoved = Clock;
        if (Math.Abs(track.Health - health) >= .8)
        {
            bool hurt = health < track.Health;
            numbers.Add(new FloatingNumber(position, (hurt ? "−" : "+") + Math.Abs(Math.Round(health - track.Health)).ToString(), hurt ? new Color("edb08a") : Ui.Success, Clock));
            if (hurt) Animate(id, health <= 0 ? 5 : 4, health <= 0 ? 6 : .3);
        }
        if (track.Health > 0 && health <= 0) Animate(id, 5, 6);
        track.FacingDirection = SpritePoseRules.Direction(facing, track.FacingDirection);
        if (track.Health <= 0 && health > 0) { track.StateUntil = 0; track.State = 0; }
        track.Target = position; track.Facing = facing; track.Health = health;
        return track;
    }

    public void Animate(string id, int state, double duration)
    {
        if (!tracks.TryGetValue(id, out var track)) return;
        track.State = state; track.StateStart = Clock; track.StateUntil = Clock + duration;
    }

    public override void _Process(double delta)
    {
        Clock += delta; sinceSnapshot += delta;
        if (Data is null || Assets is null) return;
        var zone = Data.Zone(ZoneId);
        if (lastZone != zone.Id && Snapshot is null) { Camera = zone.Spawn; lastZone = zone.Id; }
        foreach (var track in tracks.Values)
        {
            var previousPosition = track.Position;
            double weight = 1 - Math.Exp(-18 * delta);
            if (track.Position.Distance(track.Target) > 6) track.Position = track.Target;
            else track.Position = new Point(track.Position.X + (track.Target.X - track.Position.X) * weight, track.Position.Y + (track.Target.Y - track.Position.Y) * weight);
            double travelled = previousPosition.Distance(track.Position);
            track.WalkPhase = travelled > 6 ? 0 : SpritePoseRules.AdvanceWalk(track.WalkPhase, travelled);
        }
        if (Snapshot is { } snapshot && tracks.TryGetValue(snapshot.Self.Id, out var self)) Camera = self.Position;
        numbers.RemoveAll(x => Clock - x.Started > 1.3);
        double day = WorldTime.DayFraction(RealmTime);
        float darkness = zone.Kind == "interior" ? 0 : zone.Layer != "Surface" ? .1f : (float)Math.Clamp((Math.Cos(day * Math.Tau) - .1) * .23, 0, .22);
        SelfModulate = Colors.White.Lerp(new Color("61758d"), darkness);
        QueueRedraw();
    }

    public Point ScreenToWorld(Vector2 point)
    {
        float zoom = Math.Clamp(Zoom, 1, 3);
        return new Point((point.X - origin.X) / zoom / Tile, (point.Y - origin.Y) / zoom / Tile);
    }
    public Vector2 WorldToScreen(Point point) => origin + new Vector2((float)point.X * Tile, (float)point.Y * Tile) * Zoom;

    public WorldTarget? Pick(Vector2 screen)
    {
        var point = ScreenToWorld(screen);
        return interactions.Where(x => x.Position.Distance(point) < (x.Kind == "creature" ? 1.15 : .85)).OrderBy(x => x.Position.Distance(point)).Cast<WorldTarget?>().FirstOrDefault();
    }
    public WorldTarget? Nearest(Point point)
        => interactions.Where(x => x.Kind != "creature" && x.Kind != "player" && x.Position.Distance(point) < 3).OrderBy(x => x.Position.Distance(point)).Cast<WorldTarget?>().FirstOrDefault();
    public IEnumerable<WorldTarget> Targets => interactions;

    private static Vector2 Pixels(Point p) => new((float)p.X * Tile, (float)p.Y * Tile);
    private int Direction(Point p) => Math.Abs(p.X) > Math.Abs(p.Y) ? p.X < 0 ? 1 : 2 : p.Y < 0 ? 3 : 0;
    private (int State, int Direction, int Frame, Point Position) Pose(string id, Point at)
    {
        if (!tracks.TryGetValue(id, out var t)) return (0, 0, (int)(Clock * 6) % 8, at);
        int state = t.Health <= 0 ? 5 : Clock < t.StateUntil ? t.State : Clock - t.LastMoved < .35 ? 1 : 0;
        int frame = state is 2 or 3 or 4 or 5
            ? SpritePoseRules.ActionFrame(state, Clock - t.StateStart, t.StateUntil - t.StateStart)
            : state == 1 ? (int)t.WalkPhase : (int)(Clock * 5) % 8;
        return (state, t.FacingDirection, frame, t.Position);
    }

    public override void _Draw()
    {
        if (Data is null || Assets is null) return;
        var zone = Data.Zone(ZoneId);
        PrepareSurface(zone);
        Zoom = Math.Clamp(Zoom, 1, 3);
        origin = (Size / 2 - Pixels(Camera) * Zoom).Round();
        DrawSetTransform(origin, 0, new Vector2(Zoom, Zoom));
        int minX = Math.Max(-1, (int)(Camera.X - Size.X / Zoom / Tile / 2) - 4);
        int maxX = Math.Min(zone.Width + 1, (int)(Camera.X + Size.X / Zoom / Tile / 2) + 4);
        int minY = Math.Max(-1, (int)(Camera.Y - Size.Y / Zoom / Tile / 2) - 7);
        int maxY = Math.Min(zone.Height + 1, (int)(Camera.Y + Size.Y / Zoom / Tile / 2) + 7);
        visuals.Clear(); interactions.Clear();
        for (int y = minY; y <= maxY; y++) for (int x = minX; x <= maxX; x++)
        {
            var terrain = SurfaceAt(zone, x, y);
            uint hash = WorldMap.Hash(x, y, zone.Seed);
            int variant = terrain is Terrain.Water or Terrain.Lava ? (int)(Clock * 3) % 4 : (int)(hash % 4);
            var texture = Assets.Texture("terrain/" + terrain.ToString().ToLowerInvariant() + "_" + variant);
            if (texture is not null) DrawTextureRect(texture, new Rect2(x * Tile, y * Tile, Tile, Tile), false);
            DrawSurfaceEdge(zone, x, y);
            string? decoration = Decoration(zone, terrain, hash, x, y);
            var at = new Point(x + .5, y + .75);
            if (decoration is not null && !zone.Furnishings.Any(f => f.Covers(x, y)) && zone.Buildings.All(b => x < b.X - 1 || x > b.X + b.Width || y < b.Y - 3 || y > b.Y + b.Height + 1))
                visuals.Add(new Visual((float)at.Y, "decoration", decoration, at));
        }
        GatherFurnishings(zone);
        foreach (var exit in zone.Exits)
        {
            if (!IsWithinCameraBounds(exit.Position, 4)) continue;
            string prop = exit.Kind is "road" ? "signpost" : exit.Kind.Contains("portal", StringComparison.Ordinal) ? "waystone" : "stairs";
            if (exit.Kind != "door") DrawProp("props/" + prop, exit.Position);
            else DrawArc(Pixels(exit.Position), 10, 0, MathF.PI, 12, new Color(.72f, .64f, .43f, .65f), 1);
            interactions.Add(new WorldTarget("exit", exit.Id, Data.Zone(exit.Target).Name, exit.Position));
            if (exit.Position.Distance(Camera) < 6) Nameplate(exit.Position, "→ " + Data.Zone(exit.Target).Name, Ui.Gold, -72);
        }
        if (Waypoint is { } waypoint)
        {
            DrawArc(Pixels(waypoint), 12, 0, MathF.Tau, 20, Ui.Gold, 1.5f);
            DrawLine(Pixels(waypoint) + new Vector2(0, -27), Pixels(waypoint) + new Vector2(0, -15), Ui.Gold, 2);
        }
        foreach (var building in zone.Buildings)
        {
            var at = new Point(building.X + building.Width / 2.0, building.Y + building.Height);
            if (IsWithinCameraBounds(at, building.Width + building.Height)) visuals.Add(new Visual((float)at.Y, "building", building.Id, at, building));
        }
        foreach (var npc in Data.Npcs.Where(x => x.Zone == zone.Id))
        {
            if (!IsWithinCameraBounds(npc.Position, 5)) continue;
            visuals.Add(new Visual((float)npc.Position.Y, "npc", npc.Id, npc.Position, npc));
            interactions.Add(new WorldTarget("npc", npc.Id, npc.Name, npc.Position));
        }
        if (Snapshot is { } snapshot)
        {
            foreach (var node in snapshot.Nodes)
            {
                if (!IsWithinCameraBounds(node.Position, 5)) continue;
                visuals.Add(new Visual((float)node.Position.Y, "node", node.Id, node.Position, node));
                string name = Data.Resources.FirstOrDefault(x => x.Id == node.Template)?.Name ?? Ui.Words(node.Template);
                interactions.Add(new WorldTarget("node", node.Id, name, node.Position));
            }
            foreach (var chest in snapshot.Chests)
            {
                visuals.Add(new Visual((float)chest.Position.Y, "chest", chest.Id, chest.Position, chest));
                interactions.Add(new WorldTarget("chest", chest.Id, Ui.Words(chest.Kind) + " Chest", chest.Position));
            }
            foreach (var pile in Loot)
            {
                visuals.Add(new Visual((float)pile.Position.Y, "loot", pile.Id, pile.Position, pile));
                interactions.Add(new WorldTarget("loot", pile.Id, "Dropped loot", pile.Position));
            }
            foreach (var mob in snapshot.Creatures)
            {
                if (!IsWithinCameraBounds(mob.Position, 5)) continue;
                if (mob.Health <= 0 && tracks.TryGetValue(mob.Id, out var dead) && Clock > dead.StateUntil) continue;
                var pose = Pose(mob.Id, mob.Position);
                visuals.Add(new Visual((float)pose.Position.Y, "creature", mob.Id, pose.Position, mob));
                if (mob.Health > 0) interactions.Add(new WorldTarget("creature", mob.Id, Data.Mob(mob.Template).Name, mob.Position));
            }
            foreach (var player in snapshot.Players)
            {
                var pose = Pose(player.Id, player.Position);
                visuals.Add(new Visual((float)pose.Position.Y, "player", player.Id, pose.Position, player));
                interactions.Add(new WorldTarget("player", player.Id, player.Name, player.Position));
            }
            var localPose = Pose(snapshot.Self.Id, snapshot.Self.Position);
            visuals.Add(new Visual((float)localPose.Position.Y, "self", snapshot.Self.Id, localPose.Position, snapshot.Self));
            foreach (var telegraph in snapshot.Telegraphs) DrawTelegraph(telegraph);
        }
        visuals.Sort((a, b) => a.Depth.CompareTo(b.Depth));
        foreach (var visual in visuals) DrawVisual(zone, visual);
        foreach (var number in numbers)
        {
            float elapsed = (float)(Clock - number.Started);
            var position = Pixels(number.At) + new Vector2(0, -44 - elapsed * 22);
            Color color = number.Color; color.A = Math.Clamp(1.3f - elapsed, 0, 1);
            Text(position, number.Text, color, 12);
        }
        DrawSetTransform(Vector2.Zero);
        if (WeatherEnabled && zone.Layer == "Surface" && zone.Kind != "interior") DrawWeather(zone);
    }

    private bool IsWithinCameraBounds(Point p, double margin)
        => Math.Abs(p.X - Camera.X) < Size.X / Zoom / Tile / 2 + margin && Math.Abs(p.Y - Camera.Y) < Size.Y / Zoom / Tile / 2 + margin;

    private static string? Decoration(ZoneDef zone, Terrain terrain, uint hash, int x, int y)
    {
        if (zone.Kind == "interior") return null;
        if (zone.Id == "wayfarers_rest" && Math.Abs(x - zone.Spawn.X) < 22 && Math.Abs(y - zone.Spawn.Y) < 22)
            return terrain == Terrain.Grass ? hash % 19 == 0 ? "grass_tuft" : hash % 67 == 0 ? "flowers" : null : null;
        if (terrain is Terrain.Grass or Terrain.Moss)
        {
            uint density = zone.Biome.Contains("forest", StringComparison.Ordinal) ? 29u : 89u;
            if (hash % density == 0) return zone.Biome == "pine_forest" ? "pine" : zone.Biome == "ancient_forest" ? "ancient_oak" : "oak";
            if (hash % 47 == 1) return "bush";
            if (hash % 37 == 2) return "flowers";
            if (hash % 59 == 3) return "rock";
            if (hash % 31 == 4) return "grass_tuft";
        }
        if (terrain == Terrain.Marsh) return hash % 31 == 0 ? "willow" : hash % 17 == 1 ? "reeds" : hash % 43 == 2 ? "mushrooms" : null;
        if (terrain == Terrain.Snow) return hash % 79 == 0 ? "snow_pine" : hash % 41 == 1 ? "snow_rock" : null;
        if (terrain == Terrain.Sand) return hash % 109 == 0 ? zone.Biome == "badlands" ? "cactus" : "palm" : hash % 47 == 1 ? "rock" : null;
        if (terrain == Terrain.Ash) return hash % 43 == 0 ? "dead_tree" : hash % 37 == 1 ? "basalt" : null;
        if (terrain == Terrain.Crystal && hash % 47 == 0) return "crystal";
        if (terrain == Terrain.Moss && zone.Layer != "Surface" && hash % 23 == 0) return "mushrooms";
        return null;
    }

    private void DrawVisual(ZoneDef zone, Visual visual)
    {
        Vector2 feet = Pixels(visual.At).Round();
        if (visual.Id == TargetId) DrawArc(feet, 12, 0, MathF.Tau, 24, Ui.Gold, 1.5f);
        switch (visual.Kind)
        {
            case "furnishing":
                DrawFurnishing((FurnishingDef)visual.Value!);
                break;
            case "decoration":
                DrawProp("props/" + visual.Id, visual.At, visual.Id.Contains("tree", StringComparison.Ordinal) || visual.Id.Contains("oak", StringComparison.Ordinal) || visual.Id.Contains("pine", StringComparison.Ordinal) ? CanopyTint(visual.At) : Colors.White);
                break;
            case "building":
                var building = (BuildingDef)visual.Value!;
                var house = Assets.Texture("buildings/" + zone.Id + "/" + building.Id);
                if (house is not null) DrawTexture(house, new Vector2(building.X * Tile, (building.Y - 2) * Tile));
                if (ShowNames && visual.At.Distance(Camera) < 5) Nameplate(visual.At, building.Name, Ui.Muted, 11);
                break;
            case "npc":
                var npc = (NpcDef)visual.Value!;
                Shadow(feet);
                Assets.DrawFrame(this, "npcs/" + npc.Role, feet, 0, npc.Position.X > Camera.X + 2 ? 1 : npc.Position.X < Camera.X - 2 ? 2 : 0, (int)(Clock * 5) % 8);
                if (ShowNames && npc.Position.Distance(Camera) < 7)
                {
                    Nameplate(npc.Position, npc.Name, new Color("f1e2c7"), -59, 12);
                    Nameplate(npc.Position, Ui.Words(npc.Role), new Color("c2d7c9"), -45, 10);
                }
                if (Snapshot is { } s)
                {
                    bool turnIn = Data.Quests.Any(q => q.Giver == npc.Id && s.Self.Quests.TryGetValue(q.Id, out var progress) && !progress.Complete && q.Objectives.Select((objective, i) => i < progress.Counts.Count && progress.Counts[i] >= objective.Count).All(x => x));
                    bool available = Data.Quests.Any(q => q.Giver == npc.Id && !s.Self.Quests.ContainsKey(q.Id) && !s.Self.CompletedQuests.Contains(q.Id) && (q.Prerequisite == "" || s.Self.CompletedQuests.Contains(q.Prerequisite)));
                    if (turnIn || available) Text(feet + new Vector2(0, -67), turnIn ? "?" : "!", Ui.Gold, 15);
                }
                break;
            case "node":
                var node = (WorldNode)visual.Value!;
                bool depleted = node.ReadyAt > RealmTime;
                string key = node.Template.StartsWith("structure_", StringComparison.Ordinal) ? "structures/" + node.Template : "resources/" + node.Template;
                if (depleted && Data.Resources.FirstOrDefault(x => x.Id == node.Template)?.Skill == "woodcutting") key = "props/stump";
                DrawProp(key, node.Position, depleted ? new Color(1, 1, 1, .55f) : Colors.White);
                if (visual.Id == TargetId) Nameplate(node.Position, depleted ? "Ready in " + Math.Ceiling(node.ReadyAt - RealmTime) + "s" : Data.Resources.FirstOrDefault(x => x.Id == node.Template)?.Name ?? "Structure", Ui.Text, -50);
                break;
            case "chest":
                var chest = (Chest)visual.Value!;
                DrawProp("chests/" + chest.Kind + (chest.ReadyAt > RealmTime ? "_open" : "_closed"), chest.Position);
                break;
            case "loot":
                var pile = (LootPile)visual.Value!;
                DrawProp("props/loot", pile.Position);
                if (pile.Items.Any(x => x.Rarity >= Rarity.Epic)) DrawArc(feet, 9, (float)Clock, (float)Clock + MathF.PI, 15, Ui.RarityColor(pile.Items.Max(x => x.Rarity)), 1.5f);
                break;
            case "creature":
                var mob = (Creature)visual.Value!; var def = Data.Mob(mob.Template); var pose = Pose(mob.Id, mob.Position);
                if (mob.Health > 0) Shadow(feet);
                Assets.DrawFrame(this, "mobs/" + mob.Template, feet, pose.State, pose.Direction, pose.Frame);
                if (mob.Health > 0 && (mob.Id == TargetId || mob.Health < def.Health || def.Boss))
                {
                    float height = def.Boss ? -105 : -57;
                    HealthBar(feet + new Vector2(-16, height), mob.Health / def.Health, def.Boss ? new Color("ba7b5b") : new Color("a65052"));
                    Nameplate(mob.Position, def.Name + " · " + def.Level, def.Boss ? Ui.Gold : Ui.Text, height - 5, 9);
                }
                if (mob.Owner != "") Nameplate(mob.Position, "Companion", Ui.Success, 10, 8);
                break;
            case "player":
                var player = (PublicPlayer)visual.Value!; var pp = Pose(player.Id, player.Position);
                Shadow(feet); Assets.DrawPerson(this, player.Appearance, player.Equipment, feet, pp.State, pp.Direction, pp.Frame);
                if (ShowNames) Nameplate(player.Position, player.Name + " · " + player.Level, new Color("a3c9df"), -61, 10);
                break;
            case "self":
                var character = (Character)visual.Value!; var self = Pose(character.Id, character.Position);
                if (character.Health > 0) Shadow(feet);
                Assets.DrawPerson(this, character.Appearance, PixelAssets.VisibleEquipment(character), feet, self.State, self.Direction, self.Frame);
                foreach (var status in character.Statuses.Where(x => x.Until > RealmTime)) DrawStatus(feet, status);
                break;
        }
    }

    private Color CanopyTint(Point at)
    {
        if (Snapshot is not { } snap) return Colors.White;
        return Math.Abs(at.X - snap.Self.Position.X) < 1.1 && snap.Self.Position.Y < at.Y && snap.Self.Position.Y > at.Y - 3 ? new Color(1, 1, 1, .55f) : Colors.White;
    }
    private void DrawProp(string key, Point at, Color? tint = null)
    {
        var texture = Assets.Texture(key); if (texture is null) return;
        var position = Pixels(at) - new Vector2(texture.GetWidth() / 2f, texture.GetHeight() - 5);
        DrawTexture(texture, position.Round(), tint ?? Colors.White);
    }
    private void Shadow(Vector2 feet)
    {
        var texture = Assets.Texture("props/shadow");
        if (texture is not null) DrawTextureRect(texture, new Rect2(feet - new Vector2(16, 6), new Vector2(32, 12)), false);
    }
    private void HealthBar(Vector2 position, double fraction, Color color)
    {
        DrawRect(new Rect2(position, new Vector2(32, 4)), Ui.Ink);
        DrawRect(new Rect2(position + Vector2.One, new Vector2((float)Math.Clamp(fraction, 0, 1) * 30, 2)), color);
    }
    private void Nameplate(Point at, string text, Color color, float offset, int size = 10)
    {
        var position = Pixels(at) + new Vector2(0, offset);
        var font = ThemeDB.FallbackFont;
        float width = Math.Min(240, font.GetStringSize(text, HorizontalAlignment.Left, -1, size).X);
        DrawRect(new Rect2(position - new Vector2(width / 2 + 3, font.GetAscent(size)),
            new Vector2(width + 6, font.GetHeight(size))), new Color(.06f, .055f, .045f, .78f));
        Text(position, text, color, size);
    }
    private void Text(Vector2 position, string text, Color color, int size)
    {
        var at = position - new Vector2(120, 0);
        DrawStringOutline(ThemeDB.FallbackFont, at, text, HorizontalAlignment.Center, 240, size, 3, new Color(0, 0, 0, .8f));
        DrawString(ThemeDB.FallbackFont, at, text, HorizontalAlignment.Center, 240, size, color);
    }
    public static Color ElementColor(Element element) => element switch
    {
        Element.Fire => new("e39b63"), Element.Frost => new("97d2db"), Element.Lightning => new("e2d98a"), Element.Nature => new("9ac77d"), Element.Poison => new("b6cc78"), Element.Arcane => new("b49ad9"), Element.Radiant => new("f0e0ae"), Element.Shadow => new("a38ebb"), _ => new("ceb49d")
    };
    private void DrawTelegraph(Telegraph effect)
    {
        var center = Pixels(effect.Position); var color = ElementColor(effect.Element);
        color.A = .35f + (float)Math.Clamp(1 - (effect.Resolves - RealmTime), 0, 1) * .25f;
        float radius = (float)effect.Radius * Tile;
        if (effect.Shape == "line")
        {
            var direction = new Vector2((float)effect.Direction.X, (float)effect.Direction.Y).Normalized();
            var perpendicular = direction.Orthogonal() * 10;
            var end = center + direction * radius;
            DrawColoredPolygon([center - perpendicular, end - perpendicular, end + perpendicular, center + perpendicular], new Color(color, color.A * .4f));
            DrawLine(center - perpendicular, end - perpendicular, color, 1); DrawLine(center + perpendicular, end + perpendicular, color, 1);
        }
        else if (effect.Shape == "cone")
        {
            float angle = MathF.Atan2((float)effect.Direction.Y, (float)effect.Direction.X);
            var points = new List<Vector2> { center };
            for (int i = 0; i <= 16; i++) points.Add(center + Vector2.FromAngle(angle - .6f + i * 1.2f / 16) * radius);
            DrawColoredPolygon(points.ToArray(), new Color(color, color.A * .4f));
            DrawArc(center, radius, angle - .6f, angle + .6f, 24, color, 1.5f);
        }
        else
        {
            DrawCircle(center, radius, new Color(color, color.A * .16f));
            DrawArc(center, radius, 0, MathF.Tau, 48, color, 1.5f);
            DrawArc(center, radius * .86f, 0, MathF.Tau, 48, new Color(color, color.A * .5f), 1);
        }
    }
    private void DrawStatus(Vector2 feet, StatusEffect status)
    {
        if (status.Kind is not ("burn" or "poison" or "shield" or "arcane" or "radiance" or "chill")) return;
        Color color = ElementColor(status.Element); color.A = .7f;
        for (int i = 0; i < 4; i++)
        {
            float angle = (float)Clock * 2 + i * MathF.Tau / 4;
            var at = feet + new Vector2(MathF.Cos(angle) * 10, -17 + MathF.Sin(angle) * 5);
            DrawRect(new Rect2(at.Round(), new Vector2(2, 2)), color);
        }
    }
    private void DrawWeather(ZoneDef zone)
    {
        string weather = WorldTime.Weather(zone, RealmTime);
        if (weather is "clear" or "underground") return;
        int count = weather is "storm" or "blizzard" ? 120 : 55;
        for (int i = 0; i < count; i++)
        {
            float x = (float)((WorldMap.Hash(i, 3, zone.Seed) % 10000 / 10000.0 * Size.X + Clock * (weather is "snow" or "blizzard" ? 18 : 42)) % Math.Max(1, Size.X));
            float y = (float)((WorldMap.Hash(i, 5, zone.Seed) % 10000 / 10000.0 * Size.Y + Clock * (weather is "rain" or "storm" ? 470 : 32)) % Math.Max(1, Size.Y));
            if (weather is "rain" or "storm") DrawLine(new Vector2(x, y), new Vector2(x - 3, y + 12), new Color(.64f, .76f, .85f, .2f), 1);
            else if (weather is "snow" or "blizzard") DrawRect(new Rect2(x, y, 2, 2), new Color(.86f, .91f, .92f, .45f));
            else if (weather is "ash" or "dust") DrawRect(new Rect2(x, y, 2, 1), new Color(.71f, .63f, .48f, .25f));
        }
        if (weather == "fog") DrawRect(new Rect2(Vector2.Zero, Size), new Color(.65f, .72f, .69f, .08f));
    }
}
