using Godot;
using Kairnfall.Core;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Kairnfall.Client;

public sealed class PixelAssets
{
    private readonly Dictionary<string, Texture2D> textures = [];
    private readonly Dictionary<string, AtlasTexture> frames = [];
    private readonly HashSet<string> missing = [];
    public IReadOnlyCollection<string> Missing => missing;
    public const int Frames = 8;
    public static readonly string[] LayerOrder = ["cloak", "body", "legs", "boots", "chest", "belt", "hair", "helmet", "necklace", "charm", "trinket", "gloves", "offhand", "weapon"];

    public Texture2D? Texture(string key)
    {
        if (!Regex.IsMatch(key, @"\A[a-zA-Z0-9_/-]+\z")) throw new InvalidDataException("Unsafe asset identifier.");
        if (textures.TryGetValue(key, out var found)) return found;
        if (missing.Contains(key)) return null;
        string path = "res://Assets/" + key + ".png";
        if (!ResourceLoader.Exists(path))
        {
            missing.Add(key);
            GD.PushError("Required art is missing: " + path);
            return null;
        }
        var texture = GD.Load<Texture2D>(path);
        if (texture is null) { missing.Add(key); return null; }
        textures.Add(key, texture);
        return texture;
    }

    public Texture2D? Icon(string item) => Texture("items/" + item);
    public Texture2D? AbilityIcon(string ability) => Texture("abilities/" + ability);

    public AtlasTexture? Frame(string key, int state, int direction, int frame)
    {
        var texture = Texture(key);
        if (texture is null) return null;
        int size = texture.GetWidth() / Frames;
        string cache = key + ":" + state + ":" + direction + ":" + frame;
        if (!frames.TryGetValue(cache, out var result))
        {
            result = new AtlasTexture { Atlas = texture, Region = new Rect2(Math.Clamp(frame, 0, 7) * size, (Math.Clamp(state, 0, 5) * 4 + Math.Clamp(direction, 0, 3)) * size, size, size) };
            frames[cache] = result;
        }
        return result;
    }

    public void DrawFrame(CanvasItem canvas, string key, Vector2 feet, int state, int direction, int frame, Color? tint = null)
    {
        var texture = Texture(key);
        if (texture is null) return;
        float size = texture.GetWidth() / (float)Frames;
        var source = new Rect2(Math.Clamp(frame, 0, 7) * size, (Math.Clamp(state, 0, 5) * 4 + Math.Clamp(direction, 0, 3)) * size, size, size);
        canvas.DrawTextureRectRegion(texture, new Rect2(feet - new Vector2(size * .5f, size * .86f), new Vector2(size, size)), source, tint ?? Colors.White);
    }

    public void DrawPerson(CanvasItem canvas, Appearance appearance, IReadOnlyDictionary<string, string> equipment, Vector2 feet, int state, int direction, int frame)
    {
        foreach (string layer in LayerOrder)
        {
            string? key = layer switch
            {
                "body" => $"people/body_{Math.Clamp(appearance.Body, 0, 1)}_{Math.Clamp(appearance.Skin, 0, 5)}",
                "hair" => $"people/hair_{Math.Clamp(appearance.Hair, 0, 5)}_{Math.Clamp(appearance.HairColor, 0, 7)}",
                _ => equipment.TryGetValue(layer, out var template) ? "equipment/" + template : null
            };
            if (key is not null) DrawFrame(canvas, key, feet, state, direction, frame);
        }
    }

    public static Dictionary<string, string> VisibleEquipment(Character character)
    {
        var result = new Dictionary<string, string>();
        foreach (var entry in character.Equipment)
        {
            var item = character.Inventory.FirstOrDefault(x => x.Id == entry.Value);
            if (item is not null) result[entry.Key] = item.Template;
        }
        return result;
    }

    public static Catalog LoadCatalog()
    {
        string path = "res://Assets/catalog.json";
        if (!Godot.FileAccess.FileExists(path)) throw new InvalidDataException("The content pack is missing. Run bootstrap.ps1 before opening the client.");
        var data = JsonSerializer.Deserialize<Catalog>(Godot.FileAccess.GetFileAsString(path), Wire.Json) ?? throw new InvalidDataException("The content pack is empty.");
        var errors = data.Validate();
        if (errors.Count != 0) throw new InvalidDataException(string.Join("\n", errors.Take(12)));
        return data;
    }
}

public partial class AvatarPreview : Control
{
    public PixelAssets Assets { get; set; } = null!;
    public Appearance Appearance { get; set; } = new();
    public Dictionary<string, string> Equipment { get; set; } = [];
    public int Direction { get; set; }
    private double clock;
    public override void _Ready() { TextureFilter = TextureFilterEnum.Nearest; MouseFilter = MouseFilterEnum.Ignore; }
    public override void _Process(double delta) { clock += delta; QueueRedraw(); }
    public override void _Draw()
    {
        if (Assets is null) return;
        float scale = Math.Min(Size.X / 72, Size.Y / 72);
        DrawSetTransform(new Vector2(Size.X / 2, Size.Y * .85f), 0, new Vector2(scale, scale));
        DrawEllipseShadow();
        Assets.DrawPerson(this, Appearance, Equipment, Vector2.Zero, 0, Direction, (int)(clock * 6) % 8);
        DrawSetTransform(Vector2.Zero);
    }
    private void DrawEllipseShadow()
    {
        var texture = Assets.Texture("props/shadow");
        if (texture is not null) DrawTextureRect(texture, new Rect2(-16, -6, 32, 12), false);
    }
}
