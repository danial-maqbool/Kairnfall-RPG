using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private readonly AttackRequestGate dashGate = new();
    private Button dashButton = null!, targetNextButton = null!;
    private CombatReadabilityOverlay? combatReadability;

    private void RequestDash()
    {
        if (!GameplayInputAllowed || actionBusy || Snapshot is not { } snapshot) return;
        string problem = DashRules.Problem(snapshot.Self, snapshot.Time);
        if (problem != "") { if (!problem.Contains("recovering")) Notify(problem); return; }
        double now = Time.GetTicksMsec() / 1000.0;
        if (!dashGate.TryTake(now, snapshot.Time, snapshot.Self.Cooldowns.GetValueOrDefault("dash"), true, DashRules.Cooldown)) return;
        var vector = Input.GetVector("move_left", "move_right", "move_up", "move_down");
        var direction = DashRules.Direction(new Point(vector.X, vector.Y), snapshot.Self.Facing);
        StopCombatInput(); route.Clear(); pendingInteraction = null;
        _ = SendAsync(new GameCommand { Kind = "dash", X = direction.X, Y = direction.Y }, true);
    }

    private void EnsureCombatReadability()
    {
        if (combatReadability is not null && GodotObject.IsInstanceValid(combatReadability)) return;
        combatReadability = new CombatReadabilityOverlay { Name = "CombatReadability", World = World, Data = Data };
        hud.AddChild(combatReadability);
        hud.MoveChild(combatReadability, 0);
    }

    private void ReconcileCombatSelection(Snapshot snapshot)
    {
        if (selectedTargetKind != "creature" || selectedTarget == "") return;
        var target = snapshot.Creatures.FirstOrDefault(x => x.Id == selectedTarget);
        if (target is not null && target.Health > 0 && target.Owner == "" && target.Zone == snapshot.Self.Zone) return;
        selectedTargetKind = ""; selectedTarget = ""; World.TargetId = ""; StopCombatInput();
    }

    private void UpdateMobControls()
    {
        if (dashButton is null || Snapshot is not { } snapshot) return;
        ReconcileCombatSelection(snapshot);
        EnsureCombatReadability();
        combatReadability!.Accept(snapshot, selectedTargetKind == "creature" ? selectedTarget : "");

        double dashLeft = Math.Max(0, snapshot.Self.Cooldowns.GetValueOrDefault("dash") - snapshot.Time);
        dashButton.Disabled = !GameplayInputAllowed || actionBusy || DashRules.Problem(snapshot.Self, snapshot.Time) != "";
        dashButton.Text = dashLeft > 0 ? $"Dash {dashLeft:0.0}s" : "Dash [" + bindings["dash"] + "]";
        dashButton.TooltipText = "Dash in your movement direction, or facing direction while standing.\n4 mana · 0.65 s recovery · 2.5 tiles · No invulnerability.\nRepeated use consumes mana faster than ordinary regeneration.";

        if (basicAttackButton is not null)
        {
            double attackLeft = Math.Max(0, snapshot.Self.Cooldowns.GetValueOrDefault("attack") - snapshot.Time);
            double reach = ExperienceRules.BasicAttackRange(snapshot.Self, Data);
            double cadence = ExperienceRules.AttackInterval(snapshot.Self, Data);
            double local = Time.GetTicksMsec() / 1000.0;
            bool queued = BasicAttackBuffered(local) && attackLeft > .02;
            basicAttackButton.Text = queued ? $"Attack · QUEUED {attackLeft:0.0}s"
                : attackLeft > .04 ? $"Attack {attackLeft:0.0}s" : "Attack [" + bindings["basic_attack"] + "]";
            basicAttackButton.TooltipText = $"Server-authoritative basic attack · {reach:0.0} tile reach · {cadence:0.00}s recovery.\nHold the attack key to repeat. A tap up to {ExperienceRules.BasicAttackBufferSeconds:0.00}s before recovery queues one attack; the server still confirms every hit.";
        }

        targetNextButton.Disabled = !GameplayInputAllowed;
        targetNextButton.Text = "Target [" + bindings["target_next"] + "]";
    }
}
