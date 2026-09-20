using Godot;

/// <summary>
/// Content-driven window geometry for the existing GameRoot page system.
/// Values are logical pixels before Godot content scaling. The caller retains
/// the existing modal blocker, focus trail, scroll container and input rules.
/// </summary>
internal readonly record struct PageLayoutProfile(float Width, float Height, string Summary);

internal static class PageLayoutProfiles
{
    private static readonly Dictionary<string, PageLayoutProfile> Profiles = new(StringComparer.Ordinal)
    {
        ["Dialogue"] = new(860, 580, "Conversation, quest context and the next available action."),
        ["Menu"] = new(720, 600, "Navigation, help and session controls."),
        ["Character"] = new(820, 620, "Equipped statistics, identity and combat readiness."),
        ["Settings"] = new(900, 640, "Display, text, audio and input preferences."),
        ["Sell"] = new(840, 620, "Select a stack, review the exact return, then confirm the sale."),
        ["Skills"] = new(960, 640, "Training progress, unlocks and current skill benefits."),
        ["Abilities"] = new(960, 640, "Available class actions, requirements and hotbar information."),
        ["Quests"] = new(980, 650, "Tracked purpose first; objectives, rewards and story detail follow."),
        ["Bestiary"] = new(960, 640, "Known creatures, encounter context and earned knowledge."),
        ["Achievements"] = new(940, 630, "Completed milestones and remaining achievement goals."),
        ["Hunting"] = new(980, 650, "Nearby hunting grounds, target value and encounter guidance."),
        ["Inventory"] = new(1080, 660, "Backpack and equipment with comparison and primary item actions."),
        ["Bank"] = new(1040, 650, "Stored items with deliberate deposit and withdrawal actions."),
        ["Crafting"] = new(1080, 660, "Recipe, station, quantity, ingredients and readiness in one view."),
        ["Shop"] = new(1040, 650, "Merchant stock, price and item usefulness before purchase."),
        ["Trade"] = new(1080, 660, "Both offers, revisions and consent remain visible together."),
        ["Auction"] = new(1080, 660, "Listings, price and availability with stale-state feedback."),
        ["Map"] = new(1100, 670, "Current region, route context, exits and discovered destinations."),
        ["Social"] = new(1040, 650, "Nearby travelers, parties, friends and group-finding tools."),
        ["Equipment Guide"] = new(1040, 650, "Upgrade paths, requirements and equipment progression."),
        ["Upgrade guide"] = new(1040, 650, "Upgrade paths, requirements and equipment progression."),
    };

    internal static PageLayoutProfile For(string page)
        => Profiles.GetValueOrDefault(page, new(960, 640, "Relevant actions first; details remain scrollable when needed."));

    internal static Vector2 SizeFor(string page, Vector2 viewport)
    {
        var profile = For(page);
        float horizontalMargin = viewport.X <= 1100 ? 48 : 80;
        float verticalMargin = viewport.Y <= 760 ? 70 : 120;
        // Supported Windows sizes keep their page-specific targets. Extremely compact
        // or safe-mode viewports still clamp inside the available logical canvas instead
        // of forcing the former 560x480 minimum beyond the viewport.
        float maxWidth = Math.Max(320, viewport.X - horizontalMargin);
        float maxHeight = Math.Max(300, viewport.Y - verticalMargin);
        return new Vector2(
            Math.Clamp(profile.Width, 320, maxWidth),
            Math.Clamp(profile.Height, 300, maxHeight));
    }

    internal static bool IsCompact(string page)
        => Profiles.TryGetValue(page, out var profile) && profile.Width <= 900;
}
