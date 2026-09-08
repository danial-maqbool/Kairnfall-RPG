using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

/// <summary>Surface materials only. The server still decides every blocked tile.</summary>
public static class WorldSurfaceRules
{
    public static Terrain Surface(ZoneDef zone, int x, int y)
    {
        Terrain ground = WorldMap.GroundTileAt(zone, x, y);
        if (WorldMap.IsSolid(ground)) return ground;
        if (zone.Kind == "interior")
        {
            bool forge = zone.Furnishings.Any(f => f.Kind == "forge");
            if (forge && x >= 19 && y <= 12) return Terrain.Stone;
            return Terrain.Wood;
        }
        if (zone.Id != "wayfarers_rest") return ground;
        int sx = (int)zone.Spawn.X, sy = (int)zone.Spawn.Y;
        if (Math.Abs(x - sx) <= 4 && Math.Abs(y - sy) <= 4) return Terrain.Stone;
        if (Math.Abs(x - sx) <= 1 || Math.Abs(y - sy) <= 1) return Terrain.Dirt;
        foreach (var building in zone.Buildings)
        {
            int door = building.X + building.Width / 2, front = building.Y + building.Height;
            if (Math.Abs(y - front) <= 1 && x >= Math.Min(door, sx) && x <= Math.Max(door, sx))
                return Terrain.Dirt;
            if (x >= building.X - 1 && x <= building.X + building.Width && y >= front && y <= front + 3)
                return building.Style == "forge" ? Terrain.Stone : Terrain.Dirt;
        }
        // Unused paving becomes a green verge, not new collision or a blocked route.
        return ground is Terrain.Stone or Terrain.Dirt ? Terrain.Grass : ground;
    }
}

public partial class WorldView
{
    private ZoneDef? surfaceZone;
    private Terrain[,]? surfaceTiles;
    private byte[,]? surfaceEdges;

    private void PrepareSurface(ZoneDef zone)
    {
        if (ReferenceEquals(surfaceZone, zone)) return;
        surfaceZone = zone;
        surfaceTiles = null; surfaceEdges = null;
        if (zone.Id != "wayfarers_rest" && zone.Kind != "interior") return;
        surfaceTiles = new Terrain[zone.Width, zone.Height];
        surfaceEdges = new byte[zone.Width, zone.Height];
        for (int y = 0; y < zone.Height; y++) for (int x = 0; x < zone.Width; x++)
            surfaceTiles[x, y] = WorldSurfaceRules.Surface(zone, x, y);
        for (int y = 1; y < zone.Height - 1; y++) for (int x = 1; x < zone.Width - 1; x++)
        {
            if (surfaceTiles[x, y] is not (Terrain.Stone or Terrain.Dirt)) continue;
            int mask = (surfaceTiles[x,y-1] == Terrain.Grass ? 1 : 0)
                | (surfaceTiles[x+1,y] == Terrain.Grass ? 2 : 0)
                | (surfaceTiles[x,y+1] == Terrain.Grass ? 4 : 0)
                | (surfaceTiles[x-1,y] == Terrain.Grass ? 8 : 0);
            surfaceEdges[x,y] = (byte)mask;
        }
    }

    private Terrain SurfaceAt(ZoneDef zone, int x, int y)
        => surfaceTiles is not null && x >= 0 && y >= 0 && x < zone.Width && y < zone.Height
            ? surfaceTiles[x,y] : WorldMap.GroundTileAt(zone, x, y);

    private void DrawSurfaceEdge(ZoneDef zone, int x, int y)
    {
        if (surfaceEdges is null || x < 0 || y < 0 || x >= zone.Width || y >= zone.Height) return;
        int mask = surfaceEdges[x,y];
        if (mask == 0) return;
        var texture = Assets.Texture("terrain/grass_edge_" + mask);
        if (texture is not null) DrawTexture(texture, new Vector2(x * Tile, y * Tile));
    }

    private void GatherFurnishings(ZoneDef zone)
    {
        foreach (var furnishing in zone.Furnishings)
        {
            var foot = new Point(furnishing.X + furnishing.Width / 2.0, furnishing.Y + furnishing.Height);
            if (!IsWithinCameraBounds(foot, Math.Max(furnishing.Width, furnishing.Height) + furnishing.Rise / Tile)) continue;
            if (furnishing.Ground) DrawFurnishing(furnishing);
            else visuals.Add(new Visual((float)foot.Y, "furnishing", furnishing.Id, foot, furnishing));
        }
    }

    private void DrawFurnishing(FurnishingDef furnishing)
    {
        var texture = Assets.Texture("furnishings/" + furnishing.Kind);
        if (texture is null) return;
        // One source pixel per logical world pixel. Do not stretch the floor footprint.
        DrawTexture(texture, new Vector2(furnishing.X * Tile, furnishing.Y * Tile - furnishing.Rise));
    }
}
