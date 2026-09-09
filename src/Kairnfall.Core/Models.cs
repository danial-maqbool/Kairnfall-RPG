using System.Text.Json;
using System.Text.Json.Serialization;

namespace Kairnfall.Core;

public static class Wire
{
    public const int Version = 1;
    public const int MaximumMessageBytes = 16384;
    public static readonly JsonSerializerOptions Json = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true,
        Converters = { new JsonStringEnumConverter() },
        MaxDepth = 48
    };
    public static T Copy<T>(T value) => JsonSerializer.Deserialize<T>(JsonSerializer.Serialize(value, Json), Json)!;
}

public enum Element { Physical, Fire, Frost, Lightning, Nature, Poison, Arcane, Radiant, Shadow }
public enum Rarity { Common, Uncommon, Rare, Epic, Legendary, Mythic, Relic }
public readonly record struct Point(double X, double Y)
{
    [JsonIgnore] public bool Finite => double.IsFinite(X) && double.IsFinite(Y);
    public double Distance(Point b) => Math.Sqrt((X-b.X)*(X-b.X)+(Y-b.Y)*(Y-b.Y));
    public Point Add(Point b) => new(X+b.X,Y+b.Y);
    public Point Scale(double s) => new(X*s,Y*s);
    public Point Direction(Point b)
    {
        var d=Distance(b); return d < 0.0001 ? new(0,0) : new((b.X-X)/d,(b.Y-Y)/d);
    }
}

public sealed class SkillDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Category { get; set; } = "";
    public string Action { get; set; } = "";
    public string Benefit { get; set; } = "";
    public int[] Unlocks { get; set; } = [1,10,25,50,75,100];
}
public sealed class ClassDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Role { get; set; } = "";
    public string Passive { get; set; } = "";
    public string Weapon { get; set; } = "";
    public string Armor { get; set; } = "";
    public string[] Affinity { get; set; } = [];
    public Dictionary<string,double> Stats { get; set; } = [];
    public string[] Abilities { get; set; } = [];
}
public sealed class ItemDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Type { get; set; } = "";
    public string Slot { get; set; } = "";
    public string Skill { get; set; } = "";
    public int Requirement { get; set; } = 1;
    public string Icon { get; set; } = "";
    public string Material { get; set; } = "";
    public string Description { get; set; } = "";
    public int StackMax { get; set; } = 1;
    public int Value { get; set; }
    public double Power { get; set; }
    public double Armor { get; set; }
    public double Speed { get; set; } = 1;
    public double Range { get; set; } = 1.7;
    public Element Element { get; set; }
    public Dictionary<string,double> Stats { get; set; } = [];
    public string[] Tags { get; set; } = [];
    public int Tier { get; set; } = 1;
    public string Effect { get; set; } = "";
}
public sealed class Affix
{
    public string Name { get; set; } = "";
    public string Stat { get; set; } = "";
    public double Value { get; set; }
}
public sealed class SocketedRune
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Template { get; set; } = "";
}
public sealed class Item
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Template { get; set; } = "";
    public int Quantity { get; set; } = 1;
    public Rarity Rarity { get; set; }
    public int Sockets { get; set; }
    public int Durability { get; set; } = 100;
    public List<Affix> Affixes { get; set; } = [];
    public List<SocketedRune> Runes { get; set; } = [];
}
public sealed class AbilityDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Class { get; set; } = "";
    public string Skill { get; set; } = "";
    public int Requirement { get; set; } = 1;
    public string Kind { get; set; } = "strike";
    public Element Element { get; set; }
    public double Power { get; set; } = 1;
    public double Range { get; set; } = 2;
    public double Radius { get; set; }
    public double Mana { get; set; }
    public double Stamina { get; set; }
    public double Cooldown { get; set; } = 1;
    public double Duration { get; set; }
    public string Status { get; set; } = "";
    public string Description { get; set; } = "";
}
public sealed class RecipeDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Skill { get; set; } = "";
    public string Station { get; set; } = "";
    public int Requirement { get; set; } = 1;
    public Dictionary<string,int> Ingredients { get; set; } = [];
    public string Output { get; set; } = "";
    public int Quantity { get; set; } = 1;
    public int Xp { get; set; } = 25;
}
public sealed class ExitDef
{
    public string Id { get; set; } = "";
    public string Target { get; set; } = "";
    public Point Position { get; set; }
    public Point Arrival { get; set; }
    public string Kind { get; set; } = "road";
    public int Requirement { get; set; } = 1;
}
public sealed class BuildingDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public int X { get; set; }
    public int Y { get; set; }
    public int Width { get; set; } = 5;
    public int Height { get; set; } = 4;
    public string Style { get; set; } = "cottage";
    public string Station { get; set; } = "";
}
public sealed class ZoneDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Biome { get; set; } = "plains";
    public string Layer { get; set; } = "Surface";
    public string Kind { get; set; } = "wilderness";
    public string Lore { get; set; } = "";
    public int Width { get; set; } = 96;
    public int Height { get; set; } = 96;
    public int Seed { get; set; }
    public int Level { get; set; } = 1;
    public Point Spawn { get; set; } = new(48,48);
    public int WorldX { get; set; }
    public int WorldY { get; set; }
    public List<ExitDef> Exits { get; set; } = [];
    public List<BuildingDef> Buildings { get; set; } = [];
    public List<FurnishingDef> Furnishings { get; set; } = [];
    public string[] Species { get; set; } = [];
    public string Boss { get; set; } = "";
    public string[] Resources { get; set; } = [];
}
public sealed class MobDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Family { get; set; } = "";
    public string Sprite { get; set; } = "";
    public string Anatomy { get; set; } = "";
    public string Biome { get; set; } = "";
    public string Ai { get; set; } = "aggressive";
    public bool Boss { get; set; }
    public bool Elite { get; set; }
    public int Level { get; set; } = 1;
    public double Health { get; set; } = 30;
    public double Power { get; set; } = 4;
    public double Armor { get; set; }
    public double Speed { get; set; } = 2;
    public double Range { get; set; } = 1.5;
    public double Aggro { get; set; } = 6;
    public int Gold { get; set; } = 3;
    public int Xp { get; set; } = 25;
    public Element Element { get; set; }
    public Dictionary<Element,double> Resistances { get; set; } = [];
    public string[] Attacks { get; set; } = [];
    public string[] Drops { get; set; } = [];
    public string Lore { get; set; } = "";
}
public sealed class ResourceDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Skill { get; set; } = "";
    public string Tool { get; set; } = "";
    public string Item { get; set; } = "";
    public string Sprite { get; set; } = "";
    public int Requirement { get; set; } = 1;
    public int Xp { get; set; } = 25;
    public double Respawn { get; set; } = 30;
}
public sealed class NpcDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Role { get; set; } = "";
    public string Zone { get; set; } = "";
    public string Faction { get; set; } = "";
    public Point Position { get; set; }
    public string Dialogue { get; set; } = "";
    public string[] Stock { get; set; } = [];
    public string Station { get; set; } = "";
    public string Sprite { get; set; } = "npc";
}
public sealed class ObjectiveDef
{
    public string Action { get; set; } = "";
    public string Target { get; set; } = "";
    public int Count { get; set; } = 1;
    public string Description { get; set; } = "";
}
public sealed class QuestDef
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Giver { get; set; } = "";
    public string Story { get; set; } = "";
    public string Category { get; set; } = "side";
    public string Prerequisite { get; set; } = "";
    public string Faction { get; set; } = "wayfarers";
    public List<ObjectiveDef> Objectives { get; set; } = [];
    public int Gold { get; set; } = 20;
    public string Reward { get; set; } = "";
    public bool Repeatable { get; set; }
}
public sealed class Appearance
{
    public int Body { get; set; }
    public int Skin { get; set; }
    public int Hair { get; set; }
    public int HairColor { get; set; }
}
public sealed class StatusEffect
{
    public string Kind { get; set; } = "";
    public Element Element { get; set; }
    public double Until { get; set; }
    public double Power { get; set; }
    public string Source { get; set; } = "";
}
public sealed class QuestProgress
{
    public List<int> Counts { get; set; } = [];
    public bool Complete { get; set; }
}
public sealed class Character
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Account { get; set; } = "";
    public string Name { get; set; } = "";
    public string Class { get; set; } = "vanguard";
    public Appearance Appearance { get; set; } = new();
    public string Zone { get; set; } = "wayfarers_rest";
    public Point Position { get; set; } = new(40,40);
    public Point Facing { get; set; } = new(0,1);
    public double Health { get; set; } = 100;
    public double Mana { get; set; } = 60;
    public double Stamina { get; set; } = 100;
    public long Gold { get; set; } = 40;
    public Dictionary<string,long> SkillXp { get; set; } = [];
    // Zero defaults preserve historical levels. New credit rates affect future training only.
    public long PracticeOnlyXp { get; set; }
    public double OverallCreditRemainder { get; set; }
    public Dictionary<string,double> CombatPracticeRemainders { get; set; } = [];
    public List<Item> Inventory { get; set; } = [];
    public List<Item> Bank { get; set; } = [];
    public Dictionary<string,string> Equipment { get; set; } = [];
    public Dictionary<string,QuestProgress> Quests { get; set; } = [];
    public HashSet<string> CompletedQuests { get; set; } = [];
    public HashSet<string> Discoveries { get; set; } = [];
    public HashSet<string> Waypoints { get; set; } = ["wayfarers_rest"];
    public HashSet<string> Achievements { get; set; } = [];
    public Dictionary<string,int> Reputation { get; set; } = [];
    public Dictionary<string,int> Bestiary { get; set; } = [];
    public Dictionary<string,double> Cooldowns { get; set; } = [];
    public List<StatusEffect> Statuses { get; set; } = [];
    public List<CommandReceipt> Receipts { get; set; } = [];
    public string Party { get; set; } = "";
    public string Guild { get; set; } = "";
    public string Pet { get; set; } = "";
    public HashSet<string> Ignored { get; set; } = [];
    public long LastAction { get; set; }
    public int Deaths { get; set; }
    public double LastCombat { get; set; } = -100;
    public double DeadUntil { get; set; }
}
public sealed class Creature
{
    public string Id { get; set; } = "";
    public string Template { get; set; } = "";
    public string Zone { get; set; } = "";
    public Point Position { get; set; }
    public Point Home { get; set; }
    public Point Facing { get; set; } = new(0,1);
    public double Health { get; set; }
    public double RespawnAt { get; set; }
    public double NextAttack { get; set; }
    public string Target { get; set; } = "";
    public string Owner { get; set; } = "";
    public Dictionary<string,double> Threat { get; set; } = [];
    public List<StatusEffect> Statuses { get; set; } = [];
    public int Generation { get; set; }
    public int Phase { get; set; }
}
public sealed class WorldNode
{
    public string Id { get; set; } = "";
    public string Template { get; set; } = "";
    public string Zone { get; set; } = "";
    public Point Position { get; set; }
    public double ReadyAt { get; set; }
    public string Owner { get; set; } = "";
}
public sealed class Chest
{
    public string Id { get; set; } = "";
    public string Zone { get; set; } = "";
    public Point Position { get; set; }
    public string Kind { get; set; } = "weathered";
    public double ReadyAt { get; set; }
    public int Requirement { get; set; } = 1;
    public bool Hidden { get; set; }
}
public sealed class Auction
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Seller { get; set; } = "";
    public Item Item { get; set; } = new();
    public long Price { get; set; }
    public double Expires { get; set; }
}
public sealed class SocialGroup
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = "";
    public string Leader { get; set; } = "";
    public HashSet<string> Members { get; set; } = [];
    public HashSet<string> Invites { get; set; } = [];
    public Dictionary<string,string> Roles { get; set; } = [];
    public string Message { get; set; } = "";
}
public sealed class TradeOffer
{
    public string Character { get; set; } = "";
    public Dictionary<string,int> Items { get; set; } = [];
    public long Gold { get; set; }
    public bool Ready { get; set; }
    public bool Confirmed { get; set; }
    public string ApprovedFingerprint { get; set; } = "";
}
public sealed class Trade
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public TradeOffer A { get; set; } = new();
    public TradeOffer B { get; set; } = new();
    public int Revision { get; set; }
    public double Expires { get; set; }
}
public sealed class WorldEvent
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Zone { get; set; } = "";
    public Point Position { get; set; }
    public double Ends { get; set; }
    public string Kind { get; set; } = "";
}
public sealed class Telegraph
{
    public string Skill { get; set; } = "";
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Zone { get; set; } = "";
    public string Source { get; set; } = "";
    public Point Position { get; set; }
    public Point Direction { get; set; }
    public string Shape { get; set; } = "circle";
    public Element Element { get; set; }
    public double Radius { get; set; } = 2;
    public double Power { get; set; }
    public double Resolves { get; set; }
}
public sealed class RealmState
{
    public int Schema { get; set; } = 1;
    public int HuntingRevision { get; set; }
    public long Revision { get; set; }
    public double Time { get; set; }
    public Dictionary<string,Character> Characters { get; set; } = [];
    public Dictionary<string,Creature> Creatures { get; set; } = [];
    public Dictionary<string,WorldNode> Nodes { get; set; } = [];
    public Dictionary<string,Chest> Chests { get; set; } = [];
    public Dictionary<string,Auction> Auctions { get; set; } = [];
    public Dictionary<string,SocialGroup> Parties { get; set; } = [];
    public Dictionary<string,SocialGroup> Guilds { get; set; } = [];
    public Dictionary<string,Trade> Trades { get; set; } = [];
    public List<WorldEvent> Events { get; set; } = [];
    public List<Telegraph> Telegraphs { get; set; } = [];
    public Dictionary<string,int> ShopStock { get; set; } = [];
    public double NextRestock { get; set; }
}
public sealed class GameCommand
{
    public int Version { get; set; } = Wire.Version;
    public string RequestId { get; set; } = Guid.NewGuid().ToString("N");
    public long Sequence { get; set; }
    public string Kind { get; set; } = "";
    public string Target { get; set; } = "";
    public string Item { get; set; } = "";
    public string Arg { get; set; } = "";
    public int Amount { get; set; } = 1;
    public double X { get; set; }
    public double Y { get; set; }
}
public sealed class CommandResult
{
    public string RequestId { get; set; } = "";
    public bool Ok { get; set; }
    public string Message { get; set; } = "";
    public long Sequence { get; set; }
}
public sealed class CommandReceipt
{
    public string RequestId { get; set; } = "";
    public CommandResult Result { get; set; } = new();
}
public sealed class PublicPlayer
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Class { get; set; } = "";
    public Appearance Appearance { get; set; } = new();
    public Point Position { get; set; }
    public Point Facing { get; set; }
    public double Health { get; set; }
    public double MaxHealth { get; set; }
    public int Level { get; set; }
    public Dictionary<string,string> Equipment { get; set; } = [];
}
public sealed class Snapshot
{
    public int Version { get; set; } = Wire.Version;
    public double Time { get; set; }
    public long Revision { get; set; }
    public Character Self { get; set; } = new();
    public List<PublicPlayer> Players { get; set; } = [];
    public List<Creature> Creatures { get; set; } = [];
    public List<WorldNode> Nodes { get; set; } = [];
    public List<Chest> Chests { get; set; } = [];
    public List<Telegraph> Telegraphs { get; set; } = [];
    public List<WorldEvent> Events { get; set; } = [];
    public List<Auction> Auctions { get; set; } = [];
    public List<Trade> Trades { get; set; } = [];
    public SocialGroup? Party { get; set; }
    public SocialGroup? Guild { get; set; }
    public Dictionary<string,int> ShopStock { get; set; } = [];
}
public sealed class ChatMessage
{
    public string Channel { get; set; } = "local";
    public string Sender { get; set; } = "";
    public string Name { get; set; } = "";
    public string Target { get; set; } = "";
    public string Text { get; set; } = "";
    public double Time { get; set; }
}
public sealed class ServerPacket
{
    public string Kind { get; set; } = "";
    public Snapshot? Snapshot { get; set; }
    public CommandResult? Result { get; set; }
    public ChatMessage? Chat { get; set; }
    public string Error { get; set; } = "";
}
public sealed class RuleException(string message) : Exception(message);
