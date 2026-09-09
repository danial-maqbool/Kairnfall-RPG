namespace Kairnfall.Core;

/// <summary>Latest real hostile contact. Saved with the character so reconnect cannot raise its difficulty.</summary>
public sealed class LearningEncounter
{
    public int EnemyLevel { get; set; }
    public string Zone { get; set; } = "";
    public double At { get; set; }
}

/// <summary>Support practice uses actual encounters, never the advertised level of the region.</summary>
public static class SupportTraining
{
    public static void Record(Character character, int enemyLevel, double now)
    {
        if (enemyLevel is < 1 or > 100 || !double.IsFinite(now))
            throw new RuleException("Invalid learning encounter.");
        character.RecentLearningEncounter = new LearningEncounter
        {
            EnemyLevel = enemyLevel, Zone = character.Zone, At = now
        };
    }

    public static int EncounterLevel(Character recipient, double now, double window = 15)
    {
        var encounter = recipient.RecentLearningEncounter;
        if (encounter is null || recipient.Health <= 0 || encounter.EnemyLevel is < 1 or > 100
            || encounter.Zone != recipient.Zone || !double.IsFinite(now) || !double.IsFinite(encounter.At)
            || !double.IsFinite(window) || window <= 0 || window > 15)
            return 0;
        double age = now - encounter.At;
        return age >= 0 && age < window ? encounter.EnemyLevel : 0;
    }
}
