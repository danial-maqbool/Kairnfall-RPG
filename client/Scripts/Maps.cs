using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class MinimapView : Control
{
    public WorldView World { get; set; } = null!;
    public Catalog Data { get; set; } = null!;
    private double elapsed;
    public override void _Ready() { MouseFilter = MouseFilterEnum.Ignore; }
    public override void _Process(double delta) { elapsed += delta; if (elapsed > .3) { elapsed = 0; QueueRedraw(); } }
    public static Color TerrainColor(Terrain terrain) => terrain switch
    {
        Terrain.Grass => new("617558"), Terrain.Moss => new("455e4e"), Terrain.Dirt => new("a48c65"), Terrain.Stone => new("8d948d"), Terrain.Sand => new("c5b487"), Terrain.Snow => new("bdccd0"), Terrain.Water => new("47778a"), Terrain.Lava => new("b96e46"), Terrain.Wall => new("414e51"), Terrain.Wood => new("967959"), Terrain.Crystal => new("887ca8"), Terrain.Marsh => new("647e69"), _ => new("696460")
    };
    public override void _Draw()
    {
        if (World is null || World.Data is null) return;
        var zone = World.Data.Zone(World.ZoneId); var self = World.Snapshot?.Self;
        int radius = 24; float scale = Math.Min(Size.X, Size.Y) / (radius * 2 + 1); var center = Size / 2;
        DrawRect(new Rect2(Vector2.Zero, Size), Ui.Ink);
        for (int y = -radius; y <= radius; y++) for (int x = -radius; x <= radius; x++)
        {
            int tx = (int)World.Camera.X + x, ty = (int)World.Camera.Y + y;
            bool seen = self is null || self.Discoveries.Contains($"{zone.Id}:{tx / 16}:{ty / 16}");
            var color = seen ? TerrainColor(WorldMap.TileAt(zone, tx, ty)) : new Color("273a3b");
            DrawRect(new Rect2(center + new Vector2(x * scale, y * scale), new Vector2(scale + .2f, scale + .2f)), color);
        }
        foreach (var npc in World.Data.Npcs.Where(x => x.Zone == zone.Id && x.Position.Distance(World.Camera) < radius)) Dot(npc.Position, center, scale, Ui.Gold);
        foreach (var exit in zone.Exits.Where(x => x.Position.Distance(World.Camera) < radius)) Dot(exit.Position, center, scale, new Color("d9d4bb"));
        if (World.Snapshot is { } snapshot)
        {
            foreach (var player in snapshot.Players) Dot(player.Position, center, scale, new Color("94bddd"));
            foreach (var creature in snapshot.Creatures.Where(x => x.Health > 0 && x.Position.Distance(World.Camera) < radius)) Dot(creature.Position, center, scale, creature.Owner == self?.Id ? Ui.Success : new Color("b06d63"));
        }
        DrawColoredPolygon([center + new Vector2(0, -5), center + new Vector2(-4, 4), center + new Vector2(4, 4)], Ui.Text);
        DrawString(ThemeDB.FallbackFont, new Vector2(5, 16), "N", HorizontalAlignment.Left, -1, 12, Ui.Gold);
    }
    private void Dot(Point at, Vector2 center, float scale, Color color)
    {
        var position = center + new Vector2((float)(at.X - World.Camera.X), (float)(at.Y - World.Camera.Y)) * scale;
        if (new Rect2(Vector2.Zero, Size).HasPoint(position)) DrawRect(new Rect2(position - Vector2.One, new Vector2(3, 3)), color);
    }
}

public partial class AtlasView : Control
{
    public Catalog Data { get; set; } = null!;
    public Func<Character?> Player { get; set; } = () => null;
    public string Layer { get; set; } = "Surface";
    public string Selected { get; set; } = "";
    public Action<string>? Chosen { get; set; }
    private readonly Dictionary<string, Vector2> positions = [];
    public override void _Ready() { MouseDefaultCursorShape = CursorShape.PointingHand; }
    public override void _Draw()
    {
        if (Data is null) return;
        DrawRect(new Rect2(Vector2.Zero, Size), new Color("202f32"));
        var player = Player();
        var zones = Data.Zones.Where(z => z.Layer == Layer && z.Kind != "interior" && (z.Kind == "city" || z.Id == player?.Zone || player?.Discoveries.Contains(z.Id) == true || player is null)).ToArray();
        if (zones.Length == 0) { DrawString(ThemeDB.FallbackFont, new Vector2(20, 35), "No regions discovered on this layer.", HorizontalAlignment.Left, -1, 17, Ui.Muted); return; }
        int minX = zones.Min(x => x.WorldX), maxX = zones.Max(x => x.WorldX), minY = zones.Min(x => x.WorldY), maxY = zones.Max(x => x.WorldY);
        positions.Clear();
        for (int i = 0; i < zones.Length; i++)
        {
            float x = maxX == minX ? .15f + .7f * (i % 4) / 3 : (zones[i].WorldX - minX) / (float)(maxX - minX);
            float y = maxY == minY ? .15f + .7f * (i / 4) / Math.Max(1, (zones.Length - 1) / 4) : (zones[i].WorldY - minY) / (float)(maxY - minY);
            var point = new Vector2(92 + x * Math.Max(1, Size.X - 184), 55 + y * Math.Max(1, Size.Y - 110));
            while (positions.Values.Any(p => p.DistanceTo(point) < 20)) point += new Vector2(18, 20);
            positions[zones[i].Id] = point;
        }
        foreach (var zone in zones) foreach (var exit in zone.Exits)
            if (positions.TryGetValue(exit.Target, out var target)) DrawLine(positions[zone.Id], target, new Color("7d8066"), 2);
        foreach (var zone in zones)
        {
            var at = positions[zone.Id];int gate=JourneyProgression.EntryRequirement(Data,zone);
            bool locked=player is not null&&Progression.PlayerLevel(player)<gate;
            Color color = zone.Id == Selected ? Ui.Text : locked ? Ui.Danger : zone.Kind == "city" ? Ui.Gold : new Color("91ae91");
            if (zone.Id == player?.Zone) DrawArc(at, 13, 0, MathF.Tau, 24, new Color("a9cde2"), 2);
            DrawRect(new Rect2(at - new Vector2(5, 5), new Vector2(10, 10)), color);
            DrawStringOutline(ThemeDB.FallbackFont, at + new Vector2(-88, 25), zone.Name, HorizontalAlignment.Center, 176, 13, 3, Ui.Ink);
            DrawString(ThemeDB.FallbackFont, at + new Vector2(-88, 25), zone.Name, HorizontalAlignment.Center, 176, 13, color);
            if (player?.Waypoints.Contains(zone.Id) == true) DrawString(ThemeDB.FallbackFont, at + new Vector2(-25, -13), "Waystone", HorizontalAlignment.Center, 50, 10, new Color("a5c4bd"));
        }
    }
    public override void _GuiInput(InputEvent @event)
    {
        if (@event is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } mouse && positions.Count > 0)
        {
            var closest = positions.OrderBy(x => x.Value.DistanceTo(mouse.Position)).First();
            if (closest.Value.DistanceTo(mouse.Position) < 45) { Selected = closest.Key; Chosen?.Invoke(Selected); QueueRedraw(); AcceptEvent(); }
        }
    }
}

public partial class GameRoot
{
    private void BuildMapPage()
    {
        if (page is null || Snapshot is null) return;
        // Keep the atlas readable while allowing its details and travel controls to
        // scroll into view when the available window height is smaller than the page.
        var scroll = Ui.Scroll(page, Vector2.Zero);
        var content = Ui.Column(scroll);
        var layers = Data.Zones.Select(x => x.Layer).Distinct().ToArray();
        var top = Ui.Row(content); var layer = new OptionButton(); foreach (string name in layers) layer.AddItem(name); layer.Selected = Math.Max(0, Array.IndexOf(layers, Data.Zone(Snapshot.Self.Zone).Layer)); top.AddChild(layer);
        top.AddChild(Ui.Button("Record regional chart", () => Send("chart")));
        var atlas = new AtlasView { Data = Data, Player = () => Snapshot?.Self, Layer = layers[layer.Selected], Selected = selectedZone, CustomMinimumSize = new Vector2(0, 370), SizeFlagsHorizontal = SizeFlags.ExpandFill, SizeFlagsVertical = SizeFlags.ExpandFill }; content.AddChild(atlas);
        var detail = Ui.Column(content);
        void RenderDetail()
        {
            Ui.Clear(detail); if (Snapshot is null) return;
            var zone = Data.Zones.FirstOrDefault(x => x.Id == selectedZone) ?? Data.Zone(Snapshot.Self.Zone);
            int playerLevel=Progression.PlayerLevel(Snapshot.Self),threat=JourneyProgression.ThreatLevel(Data,zone),entryLevel=JourneyProgression.EntryRequirement(Data,zone);
            bool locked=playerLevel<entryLevel;
            detail.AddChild(Ui.Label(zone.Name + " · " + Ui.Words(zone.Biome) + $" · Threat {threat} · Entry {entryLevel}+", 19, locked?Ui.Danger:Ui.Gold));
            detail.AddChild(Ui.Label(zone.Lore, 14, Ui.Muted, true));
            if(locked)detail.AddChild(Ui.Label($"LOCKED · Reach character level {entryLevel} ({entryLevel-playerLevel} to go).",13,Ui.Danger,true));
            var actions = Ui.Row(detail); actions.AddChild(Ui.Button("Mark route", () => MarkDestination(zone.Id, zone.Spawn)));
            bool canTravel = Snapshot.Self.Waypoints.Contains(zone.Id) && zone.Id != Snapshot.Self.Zone && !locked;
            actions.AddChild(Ui.Button("Waystone travel · 20 gold", () => Send("travel", zone.Id), !canTravel));
            detail.AddChild(Ui.Label("Frontiers open five character levels below the area's ordinary-mob threat. Fast travel still requires a discovered settlement waystone.", 13, Ui.Muted, true));
        }
        atlas.Chosen = id => { selectedZone = id; RenderDetail(); };
        layer.ItemSelected += index => { atlas.Layer = layers[index]; atlas.QueueRedraw(); };
        refreshPage = () => { atlas.QueueRedraw(); RenderDetail(); }; RenderDetail();
    }
    private void MarkDestination(string destination, Point point)
    {
        if (Snapshot is null) return;
        var self = Snapshot.Self;
        if (destination == self.Zone) { World.Waypoint = point; ClosePage(); Notify("Destination marked in the current region."); return; }
        var queue = new Queue<string>(); queue.Enqueue(self.Zone); var visited = new HashSet<string> { self.Zone }; var first = new Dictionary<string, ExitDef>();
        while (queue.TryDequeue(out var current))
        {
            foreach (var exit in Data.Zone(current).Exits)
            {
                if (JourneyProgression.ExitRequirement(Data,exit) > Progression.PlayerLevel(self) || !visited.Add(exit.Target)) continue;
                first[exit.Target] = current == self.Zone ? exit : first[current];
                if (exit.Target == destination)
                {
                    var passage = first[destination]; World.Waypoint = passage.Position; ClosePage();
                    Notify("Follow the marker toward " + Data.Zone(passage.Target).Name + ". Your destination is " + Data.Zone(destination).Name + "."); return;
                }
                queue.Enqueue(exit.Target);
            }
        }
        Notify("No route is available at your current overall level.", true);
    }
}
