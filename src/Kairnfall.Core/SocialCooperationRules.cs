namespace Kairnfall.Core;

public static class SocialCooperationRules
{
    public const double PartyShareRadius = 22;
    public const double PartySupportWindow = 12;
    public const double PartyLootDelay = 20;
    public const double RecentPlayerLifetime = WorldTime.DayLength * 7;
    public static readonly string[] LfgActivities = ["questing", "dungeon", "public_events", "boss_hunt", "exploration", "gathering"];
    public static readonly string[] LfgRoles = ["tank", "healer", "damage", "flexible"];
    public static readonly string[] GuildProjects = ["hunt", "adventure", "artisan", "fellowship"];

    public static bool ValidActivity(string value) => LfgActivities.Contains(value, StringComparer.Ordinal);
    public static bool ValidRole(string value) => LfgRoles.Contains(value, StringComparer.Ordinal);
    public static bool ValidProject(string value) => GuildProjects.Contains(value, StringComparer.Ordinal);

    public static string ActivityName(string value) => value switch
    {
        "questing" => "Questing", "dungeon" => "Dungeon", "public_events" => "Public Events",
        "boss_hunt" => "Boss Hunt", "exploration" => "Exploration", "gathering" => "Gathering", _ => "Adventure"
    };
    public static string RoleName(string value) => value switch
    {
        "tank" => "Tank", "healer" => "Healer / Support", "damage" => "Damage", _ => "Flexible"
    };
    public static string ProjectName(string value) => value switch
    {
        "hunt" => "Hunt the Dangerous", "adventure" => "Chart the Realm", "artisan" => "Supply the Guild",
        "fellowship" => "Strengthen Fellowship", _ => "Guild Project"
    };

    public static int GuildLevel(SocialGroup guild) => Math.Clamp(1 + (int)(Math.Max(0, guild.Experience) / 250), 1, 10);
    public static int ProjectGoal(SocialGroup guild, string project)
    {
        int level = GuildLevel(guild);
        return project switch
        {
            "hunt" => 20 + level * 5,
            "adventure" => 16 + level * 4,
            "artisan" => 24 + level * 6,
            "fellowship" => 8 + level * 3,
            _ => 20
        };
    }
    public static bool ProjectMatches(string project, string action) => project switch
    {
        "hunt" => action is "kill" or "boss",
        "adventure" => action is "quest" or "explore" or "survey" or "chest" or "event",
        "artisan" => action is "gather" or "craft" or "salvage",
        "fellowship" => action is "revive" or "trade" or "assist",
        _ => false
    };
    public static long ProjectExperience(SocialGroup guild) => 100 + ProjectGoal(guild, guild.Project) * 2L;
    public static long ProjectMemberGold(SocialGroup guild) => 25 + GuildLevel(guild) * 15L;
    public static double GuildFellowshipMultiplier(SocialGroup guild) => 1 + .01 * Math.Max(0, GuildLevel(guild) - 1);
}
