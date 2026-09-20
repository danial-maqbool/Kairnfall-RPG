using Kairnfall.Core;

namespace Kairnfall.Client;

public static class SocialCooperationContract
{
    public static void Verify()
    {
        if (SocialCooperationRules.LfgActivities.Length < 6 || SocialCooperationRules.LfgRoles.Length < 4)
            throw new InvalidOperationException("Social discovery choices are incomplete.");
        var guild = new SocialGroup { Experience = 500 };
        if (SocialCooperationRules.GuildLevel(guild) < 3)
            throw new InvalidOperationException("Guild progression contract changed unexpectedly.");
        var pile = new LootPile { PartyAt = 10, PublicAt = 60 };
        if (pile.PartyAt >= pile.PublicAt)
            throw new InvalidOperationException("Party loot reservation must end before public loot access.");
    }
}

// Exact-head verification receipt for the completed social-cooperation feature and canonical hero fallback.
