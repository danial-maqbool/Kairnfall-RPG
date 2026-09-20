namespace Kairnfall.Core;

public sealed class LoginRequest
{
    public string Username { get; set; } = "";
    public string Password { get; set; } = "";
}
public sealed class LoginResponse
{
    public string Token { get; set; } = "";
    public string AccountId { get; set; } = "";
    public DateTimeOffset Expires { get; set; }
}
public sealed class CharacterRequest
{
    public string Name { get; set; } = "";
    public string Class { get; set; } = "vanguard";
    public Appearance Appearance { get; set; } = new();
}
public sealed class CharacterSummary
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Class { get; set; } = "";
    public string Zone { get; set; } = "";
    public int Level { get; set; }
    public Appearance Appearance { get; set; } = new();
}
public sealed class ConnectionHello
{
    public int Version { get; set; } = Wire.Version;
    public string Token { get; set; } = "";
    public string CharacterId { get; set; } = "";
}
public sealed class GroupInvitation
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Leader { get; set; } = "";
    public bool Guild { get; set; }
}
public sealed class LfgListing
{
    public string Character { get; set; } = "";
    public string Name { get; set; } = "";
    public string Class { get; set; } = "";
    public string Activity { get; set; } = "";
    public string Role { get; set; } = "";
    public string Zone { get; set; } = "";
    public int Level { get; set; }
    public int PartySize { get; set; } = 1;
    public double Since { get; set; }
}
public sealed class SocialProfile
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Class { get; set; } = "";
    public string Zone { get; set; } = "";
    public string Guild { get; set; } = "";
    public int Level { get; set; }
    public bool Online { get; set; }
    public bool Friend { get; set; }
    public double LastSeen { get; set; }
}
public sealed class TradePreview
{
    public string TradeId { get; set; } = "";
    public int Revision { get; set; }
    public string Owner { get; set; } = "";
    public Item Item { get; set; } = new();
}
public sealed class TransportPacket
{
    public string Kind { get; set; } = "";
    public Snapshot? Snapshot { get; set; }
    public CommandResult? Result { get; set; }
    public ChatMessage? Chat { get; set; }
    public List<LootPile>? Loot { get; set; }
    public List<GroupInvitation>? Invitations { get; set; }
    public List<string> FriendInvitations { get; set; } = [];
    public List<LfgListing> Lfg { get; set; } = [];
    public List<SocialProfile> SocialProfiles { get; set; } = [];
    public List<TradePreview> TradeItems { get; set; } = [];
    public Dictionary<string,string> Names { get; set; } = [];
    public string Error { get; set; } = "";
}
public sealed class RealmSave
{
    public int FormatVersion { get; set; } = 1;
    public RealmState State { get; set; } = new();
    public Dictionary<string,LootPile> Loot { get; set; } = [];
}
public sealed class ApiError { public string Error { get; set; } = ""; }
