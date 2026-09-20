namespace Kairnfall.Core;

public readonly record struct BasicAttackProfile(double Range, bool Projectile, Element VisualElement);

/// <summary>
/// Authoritative range/delivery profile for the ordinary Spacebar/basic attack.
/// Damage and recovery continue to use the existing weapon/combat formulas.
/// </summary>
public static class BasicAttackRules
{
    // Six tiles sits inside the authored 5-8 tile caster/support spell band;
    // dedicated 8-tile projectiles still outrange this ordinary basic attack.
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
