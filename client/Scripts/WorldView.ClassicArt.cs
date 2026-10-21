using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

/// <summary>Deterministic surface decoration; it never changes terrain or collision.</summary>
public static class ClassicTerrainRules
{
    private static readonly Color[] OpeningPalette = [new("466846"), new("426242"), new("4a6d49"), new("4d714b")];

    public static bool IsOpeningRegion(ZoneDef zone)
        => zone.Id is "wayfarers_rest" or ClassicTutorialContent.ZoneId;

    public static int GrassVariant(ZoneDef zone, int x, int y)
        => (int)(IsOpeningRegion(zone)
            ? WorldMap.Hash((int)Math.Floor(x / 4.0), (int)Math.Floor(y / 4.0), zone.Seed) % 4
            : WorldMap.Hash(x, y, zone.Seed) % 4);

    private static float ClusterField(int seed, int x, int y)
    {
        float value = 0;
        for (int i = 0; i < 7; i++)
        {
            uint hash = WorldMap.Hash(i, i + 3, seed);
            int cx = (int)(hash % 31), cy = (int)((hash >> 5) % 31);
            float dx = Math.Abs(x - cx), dy = Math.Abs(y - cy);
            dx = Math.Min(dx, 31 - dx); dy = Math.Min(dy, 31 - dy);
            float rx = 5 + (hash >> 10) % 5, ry = 3 + (hash >> 14) % 4;
            float distance = dx * dx / (rx * rx) + dy * dy / (ry * ry);
            if (distance < 1) value += ((hash & 1) == 0 ? 1 : -1) * (1 - distance) * (1 - distance);
        }
        return value;
    }

    public static Color OpeningGrassPixel(int variant, int x, int y)
    {
        variant &= 3;
        // Every variant shares the same wrapping edge field. Interior deposits
        // form broad connected clusters instead of alternating individual pixels.
        int inset = Math.Min(Math.Min(x, 31 - x), Math.Min(y, 31 - y));
        float mix = Math.Clamp(inset / 6f, 0, 1); mix = mix * mix * (3 - 2 * mix);
        float value = ClusterField(7421, x, y) * (1 - mix) + ClusterField(7181 + variant * 173, x, y) * mix;
        uint blade = WorldMap.Hash(variant, 7, 9187);
        int bx = 5 + (int)(blade % 22), by = 6 + (int)((blade >> 7) % 21);
        if ((x == bx && (y == by || y == by - 1)) || (x == bx + 1 && y == by)) return OpeningPalette[3];
        return OpeningPalette[value < -.25f ? 1 : value > .45f ? 3 : value > .2f ? 2 : 0];
    }
}

public partial class WorldView
{
    public bool ClassicPresentation { get; set; }
    private readonly Dictionary<int, ImageTexture> classicGrass = [];
    private readonly Dictionary<int, ImageTexture> classicCrowns = [];
    private readonly Dictionary<string, ImageTexture> classicFurnishings = [];

    private Texture2D? ClassicTutorialFurnishing(FurnishingDef furnishing)
    {
        if (Data.ClassicTutorial is null || ZoneId != ClassicTutorialContent.ZoneId
            || furnishing.Kind is not ("classic_sign" or "classic_fountain")
            || furnishing.Width != 1 || furnishing.Height != 1 || furnishing.Rise != 24
            || !ClassicTutorialContent.Sites.Any(site => site.Id == furnishing.Id && "classic_" + site.Kind == furnishing.Kind
                && (int)site.Position.X == furnishing.X && (int)site.Position.Y == furnishing.Y)) return null;
        if (classicFurnishings.TryGetValue(furnishing.Kind, out var cached)) return cached;

        // Original static objects, one source pixel per world pixel. The 56-pixel
        // canvas ends at the authored one-tile floor anchor with its 24-pixel rise.
        using var image = Image.CreateEmpty(32, 56, false, Image.Format.Rgba8);
        image.Fill(Colors.Transparent);
        void Rect(int x, int y, int width, int height, string hex)
        {
            var color = new Color(hex);
            for (int py = y; py < y + height; py++) for (int px = x; px < x + width; px++) image.SetPixel(px, py, color);
        }
        void Ellipse(int cx, int cy, int rx, int ry, Color color)
        {
            for (int y = Math.Max(0, cy - ry); y <= Math.Min(55, cy + ry); y++)
            for (int x = Math.Max(0, cx - rx); x <= Math.Min(31, cx + rx); x++)
                if ((x - cx) * (x - cx) * ry * ry + (y - cy) * (y - cy) * rx * rx <= rx * rx * ry * ry)
                    image.SetPixel(x, y, color);
        }
        Ellipse(16, 53, furnishing.Kind == "classic_sign" ? 9 : 14, 2, new Color(0.08f, .13f, .08f, .28f));
        if (furnishing.Kind == "classic_sign")
        {
            Rect(14, 26, 5, 28, "3d3024"); Rect(14, 28, 1, 24, "ad8050"); Rect(15, 29, 2, 25, "795834");
            Rect(3, 12, 26, 17, "3b2d21"); Rect(5, 10, 22, 21, "3b2d21");
            Rect(5, 12, 22, 16, "8c683e"); Rect(4, 13, 24, 14, "8c683e");
            Rect(5, 11, 22, 2, "c49a62"); Rect(4, 13, 1, 14, "b88a53");
            Rect(5, 28, 22, 2, "60442d"); Rect(27, 14, 1, 13, "60442d");
            Rect(5, 20, 22, 1, "705032"); Rect(8, 16, 11, 2, "ead1a0");
            Rect(8, 23, 16, 2, "ead1a0"); Rect(21, 16, 3, 2, "ead1a0");
            foreach (int x in new[] { 6, 25 }) { Rect(x, 14, 1, 1, "e2bb7c"); Rect(x, 26, 1, 1, "392d24"); }
        }
        else
        {
            // A masonry spout rises behind an elliptical basin. The darker lower
            // courses and continuous stone rim keep the water distinct from grass.
            Rect(13, 14, 7, 22, "424f4d"); Rect(13, 15, 2, 18, "9ca59a"); Rect(15, 16, 3, 18, "727f77");
            Rect(11, 12, 11, 4, "424f4d"); Rect(11, 12, 10, 1, "b6b9a3"); Rect(12, 13, 8, 2, "89968a");
            Ellipse(16, 46, 12, 6, new Color("3b4947"));
            Rect(3, 34, 27, 12, "424f4d"); Rect(4, 35, 25, 11, "7d8b7f");
            Rect(5, 38, 6, 8, "96a191"); Rect(23, 37, 5, 10, "5d706a");
            Rect(7, 46, 18, 3, "677a70"); Rect(9, 49, 14, 2, "53655e");
            Rect(5, 42, 23, 1, "54665f"); Rect(12, 39, 1, 3, "54665f");
            Rect(21, 43, 1, 5, "435950"); Rect(8, 43, 1, 4, "65786b");
            Ellipse(16, 34, 14, 7, new Color("3b4947")); Ellipse(16, 33, 13, 6, new Color("9ca795"));
            Ellipse(16, 33, 10, 4, new Color("465e5b")); Ellipse(16, 33, 9, 3, new Color("417a84"));
            Rect(12, 32, 8, 1, "73b1ae"); Rect(17, 35, 5, 1, "366d7a");
            Rect(16, 18, 2, 15, "699ca3"); Rect(16, 19, 1, 13, "b8d1c4");
            Rect(15, 33, 4, 1, "c0d9ca"); Rect(14, 34, 1, 1, "83b7b2"); Rect(19, 32, 1, 1, "83b7b2");
        }
        return classicFurnishings[furnishing.Kind] = ImageTexture.CreateFromImage(image);
    }

    private Texture2D ClassicGrass(int variant, bool opening = false)
    {
        int key = variant + (opening ? 4 : 0);
        if (classicGrass.TryGetValue(key, out var cached)) return cached;
        using var image = Image.CreateEmpty(32, 32, false, Image.Format.Rgba8);
        if (opening)
        {
            for (int y = 0; y < 32; y++) for (int x = 0; x < 32; x++)
                image.SetPixel(x, y, ClassicTerrainRules.OpeningGrassPixel(variant, x, y));
            return classicGrass[key] = ImageTexture.CreateFromImage(image);
        }
        Color[] palette = [new("476947"), new("3b593c"), new("50764b"), new("5b8050"), new("426240")];
        image.Fill(palette[0]);
        for (int y = 0; y < 32; y++) for (int x = 0; x < 32; x++)
        {
            uint cluster = WorldMap.Hash(x / 2, y / 2, 7181 + variant * 173);
            uint grain = WorldMap.Hash(x, y, 9187 + variant * 131);
            if (grain % 4 != 0) image.SetPixel(x, y, palette[(cluster + grain % 2) % 5]);
            if (grain % 41 == 0 && y > 0) image.SetPixel(x, y - 1, palette[3]);
        }
        return classicGrass[key] = ImageTexture.CreateFromImage(image);
    }

    // Original pixel clusters generated locally. No reference-game files are used.
    private void DrawClassicCrown(Point at, bool fruit = false)
    {
        int variant = (int)(WorldMap.Hash((int)at.X, (int)at.Y, 12017) % 4) + (fruit ? 4 : 0);
        if (!classicCrowns.TryGetValue(variant, out var texture))
        {
            using var image = Image.CreateEmpty(32, 40, false, Image.Format.Rgba8);
            image.Fill(Colors.Transparent);
            Color[] leaves = [new("203c2a"), new("2d5131"), new("3a6537"), new("4c793e"), new("608949")];
            for (int y = 26; y < 38; y++) for (int x = 14; x <= 17; x++)
                image.SetPixel(x, y, new Color(x == 14 ? "513e2c" : x == 17 ? "342c22" : "765438"));
            for (int x = 11; x < 21; x++) image.SetPixel(x, 37, new Color("342c22"));
            (int X, int Y, int Radius)[] lobes = [(15, 15, 15), (10, 13, 9), (21, 12, 9), (12, 21, 9), (23, 20, 7), (15, 8, 7)];
            for (int layer = 0; layer < lobes.Length; layer++)
            {
                var lobe = lobes[layer];
                for (int y = Math.Max(0, lobe.Y - lobe.Radius); y <= Math.Min(31, lobe.Y + lobe.Radius); y++)
                for (int x = Math.Max(0, lobe.X - lobe.Radius); x <= Math.Min(31, lobe.X + lobe.Radius); x++)
                {
                    int distance = (x-lobe.X)*(x-lobe.X)+(y-lobe.Y)*(y-lobe.Y);
                    if (distance > lobe.Radius*lobe.Radius) continue;
                    uint grain = WorldMap.Hash(x / 2, y / 2, 3301 + variant * 97 + layer);
                    int shade = distance > (lobe.Radius-1)*(lobe.Radius-1) ? 0 : y > lobe.Y+3 ? 1 : 2+(int)(grain%3);
                    image.SetPixel(x, y, leaves[shade]);
                }
            }
            if (fruit)
                foreach (var berry in new[] { new Vector2I(8, 17), new Vector2I(23, 14), new Vector2I(18, 25) })
                {
                    image.SetPixel(berry.X, berry.Y, new Color("7a2631"));
                    image.SetPixel(berry.X+1, berry.Y, new Color("bf4d48"));
                    image.SetPixel(berry.X, berry.Y-1, new Color("e27762"));
                }
            classicCrowns[variant] = texture = ImageTexture.CreateFromImage(image);
        }
        DrawTexture(texture, (Pixels(at) - new Vector2(16, 35)).Round(), CanopyTint(at));
    }

    private void DrawClassicImpact(CombatBurst burst)
    {
        float age = (float)(Clock - burst.Started);
        if (age < 0 || age > .32f) return;
        var center = SnappedPixels(burst.At) - new Vector2(0, 15);
        var color = new Color("cf554c"); color.A = 1-age/.32f;
        for (int i = 0; i < 6; i++)
        {
            float angle = i * MathF.Tau / 6 + .3f;
            var offset = new Vector2(MathF.Cos(angle), MathF.Sin(angle)) * (3+age*32);
            DrawRect(new Rect2((center+offset).Round(), new Vector2(2, 2)), color);
        }
    }
}
