using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public static class ClassicInteractionRules
{
    public static bool InTutorial(Character self, Catalog data)
        => data.ClassicTutorial is not null && self.ClassicTutorial is not null
            && self.Zone == ClassicTutorialContent.ZoneId;

    public static ClassicTutorialSite? TutorialSite(Character self, Catalog data, string id)
    {
        if (!InTutorial(self, data) || ClassicTutorialContent.Sites.FirstOrDefault(x => x.Id == id) is not { } site)
            return null;
        var zone = data.Zones.FirstOrDefault(x => x.Id == self.Zone);
        return zone?.Furnishings.Any(x => x.Id == site.Id && x.Kind == "classic_" + site.Kind
            && x.X == (int)site.Position.X && x.Y == (int)site.Position.Y
            && x.Width == 1 && x.Height == 1 && x.Solid && x.Rise == 24) == true ? site : null;
    }

    public static WorldTarget? ChooseTutorialSite(Character self, IEnumerable<WorldTarget> targets, Catalog data, double time)
        => targets.Where(x => x.Kind == "classic_site"
                && InteractionReadinessRules.TutorialSiteProblem(self, x, data, time) == "")
            .OrderBy(x => self.Position.Distance(x.Position)).ThenBy(x => x.Id, StringComparer.Ordinal)
            .Select(x => (WorldTarget?)x).FirstOrDefault();

    public static WorldTarget? Choose(Character self, IEnumerable<WorldTarget> targets, Catalog data)
    {
        var facing = default(Point).Direction(self.Facing);
        if (facing == default) facing = new(0, 1);
        bool InFront(WorldTarget target)
        {
            if (self.Position.Distance(target.Position) < .65) return true;
            var direction = self.Position.Direction(target.Position);
            return direction.X * facing.X + direction.Y * facing.Y >= .45;
        }
        return ExperienceRules.ChooseInteraction(self, targets.Where(InFront), data);
    }
}
