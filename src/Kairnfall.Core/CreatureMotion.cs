namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private sealed class CreatureMotionPlan
    {
        public Point Goal;
        public double NextDecision;
        public int Cycle;
        public string Threat = "";
        public bool Retreat;
    }
    private readonly Dictionary<string, CreatureMotionPlan> creatureMotion = [];

    private static uint MotionSeed(string id)
    {
        uint value = 2166136261;
        foreach (char character in id) value = unchecked((value ^ character) * 16777619);
        return value;
    }

    private void PruneCreatureMotion()
    {
        foreach (string id in creatureMotion.Keys.Where(id => !State.Creatures.TryGetValue(id, out var mob) || mob.Health <= 0 || mob.Owner != "").ToArray())
            creatureMotion.Remove(id);
    }

    private void WanderCreature(Creature mob, MobDef definition, double dt)
    {
        if (definition.Boss || CombatMath.StatusPower(mob.Statuses, "stun", State.Time) > 0) return;
        if (PatrolHuntingCreature(mob,definition,dt)) return;
        var zone = Data.Zone(mob.Zone);
        uint seed = MotionSeed(mob.Id);
        if (!creatureMotion.TryGetValue(mob.Id, out var plan) || plan.Threat != "")
        {
            plan = new CreatureMotionPlan { Goal = mob.Position, NextDecision = State.Time + 1 + seed % 25 / 10.0 };
            creatureMotion[mob.Id] = plan;
        }
        if (mob.Position.Distance(mob.Home) > 6)
        {
            plan.Goal = mob.Home; plan.NextDecision = State.Time + 2;
            MoveCreature(mob, mob.Home, dt, definition.Speed * .65);
            return;
        }
        if (State.Time < plan.NextDecision)
        {
            if (mob.Position.Distance(plan.Goal) > .15) MoveCreature(mob, plan.Goal, dt, definition.Speed * .5);
            return;
        }
        plan.Cycle++;
        // Alternate a deliberate walk with a pause. Each creature has its own stable seed.
        if (plan.Cycle % 2 == 0)
        {
            plan.Goal = mob.Position;
            plan.NextDecision = State.Time + 1 + WorldMap.Hash(plan.Cycle, 3, unchecked((int)seed)) % 26 / 10.0;
            return;
        }
        for (int attempt = 0; attempt < 8; attempt++)
        {
            uint value = WorldMap.Hash(plan.Cycle, attempt, unchecked((int)seed));
            double angle = value % 6283 / 1000.0;
            double radius = 1.5 + (value / 6283) % 25 / 10.0;
            var goal = new Point(mob.Home.X + Math.Cos(angle) * radius, mob.Home.Y + Math.Sin(angle) * radius);
            if (mob.Position.Distance(goal) < 1 || !WorldMap.Fits(zone, goal) || !WorldMap.LineOfSight(zone, mob.Position, goal)) continue;
            plan.Goal = goal; plan.NextDecision = State.Time + 4;
            MoveCreature(mob, goal, dt, definition.Speed * .5);
            return;
        }
        plan.Goal = mob.Position; plan.NextDecision = State.Time + 1.5;
    }

    private void RetreatCreature(Creature mob, Character threat, MobDef definition, double dt)
    {
        // A small wounded animal takes cover, then pauses. It must not run forever
        // just beyond melee reach after the player has nearly defeated it.
        if (!creatureMotion.TryGetValue(mob.Id, out var plan) || plan.Threat != threat.Id || !plan.Retreat)
        {
            plan = new CreatureMotionPlan { Goal = mob.Position, Threat = threat.Id, Retreat = true };
            creatureMotion[mob.Id] = plan;
        }
        if (State.Time >= plan.NextDecision)
        {
            double distance = definition.Level <= 5 ? 1.25 : 2.75;
            var away = threat.Position.Direction(mob.Position);
            if (away.Distance(new Point(0, 0)) < .01) away = mob.Facing;
            var delta = away.Scale(distance);
            plan.Goal = WorldMap.Move(Data.Zone(mob.Zone), mob.Position, delta);
            plan.NextDecision = State.Time + 4;
        }
        if (mob.Position.Distance(plan.Goal) > .12) MoveCreature(mob, plan.Goal, dt, definition.Speed * 1.15 * EnemyCombatRules.MoveSpeedMultiplier(definition));
    }
}
