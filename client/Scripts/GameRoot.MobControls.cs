using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private readonly AttackRequestGate dashGate = new();
    private Button dashButton = null!, targetNextButton = null!;
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
    private void UpdateMobControls()
    {
        if (dashButton is null || Snapshot is not { } snapshot) return;
        double left = snapshot.Self.Cooldowns.GetValueOrDefault("dash") - snapshot.Time;
        dashButton.Disabled = !GameplayInputAllowed || actionBusy || DashRules.Problem(snapshot.Self, snapshot.Time) != "";
        dashButton.Text = left > 0 ? $"Dash {left:0.0}s" : "Dash [" + bindings["dash"] + "]";
        dashButton.TooltipText = "Dash in your movement direction, or facing direction while standing.\n4 mana · 0.65 s recovery · 2.5 tiles · No invulnerability.\nRepeated use consumes mana faster than ordinary regeneration.";
        targetNextButton.Disabled = !GameplayInputAllowed;
        targetNextButton.Text = "Target [" + bindings["target_next"] + "]";
    }
}
