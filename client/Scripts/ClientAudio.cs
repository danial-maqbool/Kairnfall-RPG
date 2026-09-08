using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class ClientAudio : Node
{
    private AudioStreamPlayer music = null!, ambience = null!;
    private readonly List<AudioStreamPlayer> voices = [];
    private readonly Dictionary<string, AudioStream> cache = [];
    private readonly HashSet<string> missing = [];
    private string region = "";
    private string atmosphere = "";
    private int voice;
    private float musicVolume = .35f, effectsVolume = .65f;
    private bool disabled;
    public IReadOnlyCollection<string> Missing => missing;
    public override void _Ready()
    {
        disabled = string.Equals(DisplayServer.GetName(), "headless", StringComparison.OrdinalIgnoreCase);
        if (disabled) return;

        music = new AudioStreamPlayer(); ambience = new AudioStreamPlayer(); AddChild(music); AddChild(ambience);
        music.Finished += () => music.Play(); ambience.Finished += () => ambience.Play();
        for (int i = 0; i < 8; i++) { var player = new AudioStreamPlayer(); voices.Add(player); AddChild(player); }
        ApplyVolume(); PlayMusic("menu");
    }
    public void SetVolumes(float melody, float effects)
    {
        musicVolume = Math.Clamp(melody, 0, 1); effectsVolume = Math.Clamp(effects, 0, 1); ApplyVolume();
    }
    private void ApplyVolume()
    {
        if (music is null) return;
        music.VolumeDb = Mathf.LinearToDb(Math.Max(.0001f, musicVolume));
        ambience.VolumeDb = Mathf.LinearToDb(Math.Max(.0001f, effectsVolume * .35f));
        foreach (var player in voices) player.VolumeDb = Mathf.LinearToDb(Math.Max(.0001f, effectsVolume * .5f));
    }
    private AudioStream? Load(string key)
    {
        if (disabled) return null;
        if (cache.TryGetValue(key, out var stream)) return stream;
        if (missing.Contains(key)) return null;
        string path = "res://Assets/audio/" + key + ".wav";
        if (!ResourceLoader.Exists(path)) { missing.Add(key); GD.PushWarning("Missing audio: " + path); return null; }
        stream = GD.Load<AudioStream>(path); if (stream is not null) cache[key] = stream; return stream;
    }
    private void PlayMusic(string key)
    {
        if (region == key || music is null) return;
        var stream = Load("music_" + key); if (stream is null) return;
        region = key; music.Stop(); music.Stream = stream; music.Play();
    }
    public void SetRegion(ZoneDef zone, bool boss)
    {
        string musicKey = boss ? "boss" : zone.Kind == "city" ? zone.Id : zone.Id == "wayfarers_rest" ? zone.Id : zone.Layer != "Surface" ? "dungeon" : "wilderness";
        PlayMusic(musicKey);
        string ambient = zone.Layer != "Surface" ? "cave" : zone.Biome is "coast" or "archipelago" ? "coast" : zone.Biome.Contains("forest", StringComparison.Ordinal) || zone.Biome is "plains" or "farmland" ? "forest" : "wind";
        if (ambient == atmosphere) return;
        var stream = Load("ambient_" + ambient); if (stream is null) return;
        atmosphere = ambient; ambience.Stop(); ambience.Stream = stream; ambience.Play();
    }
    public void PlayEffect(string action)
    {
        if (voices.Count == 0) return;
        string key = action switch { "attack" => "sword", "cast" => "spell", "gather" => "gather", "loot" or "chest" or "buy" or "sell" => "coins", "craft" or "build" => "hammer", "equip" or "unequip" or "socket" or "unsocket" => "equip", "consume" or "rest" => "drink", _ => "ui" };
        var stream = Load("effect_" + key); if (stream is null) return;
        var player = voices[voice++ % voices.Count]; player.Stop(); player.Stream = stream; player.PitchScale = 1 + (voice % 3 - 1) * .035f; player.Play();
    }
    public override void _ExitTree()
    {
        if (music is not null)
        {
            music.Stop();
            music.Stream = null;
        }

        if (ambience is not null)
        {
            ambience.Stop();
            ambience.Stream = null;
        }

        foreach (var player in voices)
        {
            player.Stop();
            player.Stream = null;
        }

        cache.Clear();
        missing.Clear();
    }
}
