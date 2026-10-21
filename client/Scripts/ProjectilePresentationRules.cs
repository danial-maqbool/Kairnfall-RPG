using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public static class ProjectilePresentationRules
{
    public static bool Travels(Telegraph effect)
        => effect.Shape == "projectile" && effect.Target != "" && effect.Origin.Finite && effect.Position.Finite
            && double.IsFinite(effect.Started) && double.IsFinite(effect.Resolves) && effect.Resolves > effect.Started;

    public static double Progress(Telegraph effect, double realmTime)
        => !Travels(effect) || !double.IsFinite(realmTime) ? 0
            : Math.Clamp((realmTime - effect.Started) / (effect.Resolves - effect.Started), 0, 1);

    public static Point Position(Telegraph effect, double realmTime)
    {
        double progress = Progress(effect, realmTime);
        return new Point(
            effect.Origin.X + (effect.Position.X - effect.Origin.X) * progress,
            effect.Origin.Y + (effect.Position.Y - effect.Origin.Y) * progress);
    }

    // Untargeted spell telegraphs predate authored projectile origins. Keep their
    // interval presentation separate from the verified targeted travel contract.
    public static double IntervalProgress(Telegraph effect, double realmTime)
    {
        if (!double.IsFinite(realmTime) || !double.IsFinite(effect.Started) || !double.IsFinite(effect.Resolves)
            || effect.Started <= 0 || effect.Resolves <= effect.Started)
            return 1;
        return Math.Clamp((realmTime - effect.Started) / (effect.Resolves - effect.Started), 0, 1);
    }

    public static Element VisualElement(string sourceClass, Element damageElement) => sourceClass switch
    {
        "arcanist" => Element.Arcane,
        "templar" => Element.Radiant,
        _ => damageElement
    };
}
