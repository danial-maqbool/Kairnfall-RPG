namespace Kairnfall.Core;

public readonly record struct BasicAttackProfile(double Range, bool Projectile, Element VisualElement);

/// <summary>Authoritative delivery profile for the ordinary Spacebar/basic attack.</summary>
public static class BasicAttackRules
{
    public const double CasterRange = 6.0;

    public static BasicAttackProfile Profile(Character player, ItemDef? weapon, Element damageElement)
    {
        double weaponRange = weapon?.Range ?? 1.6;
        bool projectile = HandEquipment.IsProjectileWeapon(weapon);
        return player.Class switch
        {
            "arcanist" => new(Math.Max(CasterRange, weaponRange), true, Element.Arcane),
            "templar" => new(Math.Max(CasterRange, weaponRange), true, Element.Radiant),
            _ => new(weaponRange, projectile, damageElement)
        };
    }

    public static double Range(Character player, ItemDef? weapon)
        => Profile(player, weapon, Element.Physical).Range;
}
