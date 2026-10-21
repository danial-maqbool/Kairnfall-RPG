using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public static class ClassicGatherRules
{
    public static string Problem(Character self, WorldNode? node, Catalog data, double time)
    {
        if (node is not null && node.Template.StartsWith("classic_", StringComparison.Ordinal))
        {
            if (!ClassicInteractionRules.InTutorial(self, data)) return "This resource belongs to an optional First Glade tutorial.";
            if (self.Health <= 0) return "Respawn before gathering.";
            if (!double.IsFinite(time) || !double.IsFinite(self.Health) || !double.IsFinite(node.ReadyAt)
                || !self.Position.Finite || !self.Facing.Finite || !node.Position.Finite)
                return "Wait for a fresh realm snapshot.";
            if (node.Zone != self.Zone || !ClassicTutorialContent.FacingAdjacent(self, node.Position))
                return "Move to a cardinal adjacent tile and face the resource.";
        }
        if (self.Health <= 0) return "Respawn before gathering.";
        if (node is null || node.Zone != self.Zone || !node.Position.Finite || !self.Position.Finite
            || self.Position.Distance(node.Position) > 2.15
            || !WorldMap.LineOfSight(data.Zone(self.Zone), self.Position, node.Position)) return "Move beside the resource.";
        if (node.Template.StartsWith("structure_", StringComparison.Ordinal)) return "Use this structure through Crafting.";
        if (node.Template == "crop_wheat" && node.Owner != self.Id) return "This crop belongs to another player.";
        var resource = data.Resources.FirstOrDefault(x => x.Id == (node.Template == "crop_wheat" ? "wheat_crop" : node.Template));
        if (resource is null) return "This resource cannot be gathered.";
        if (Progression.Level(self, resource.Skill) < resource.Requirement) return "Requires " + data.Skill(resource.Skill).Name + " " + resource.Requirement + ".";
        var tool = resource.Tool == "" ? null : ToolRules.Best(self, data, resource.Tool,
            resource.Skill == "farming" && resource.Tool == "sickle" ? "herbalism" : resource.Skill);
        if (resource.Tool != "" && tool is null) return "Keep a usable " + resource.Tool + " in your backpack.";
        if (self.Stamina < ToolRules.StaminaCost(tool)) return "Recover stamina before gathering.";
        return "";
    }
}

public partial class GameRoot
{
    private string classicGatherTarget = "";
    private bool classicGatherConfirmed;
    private Kairnfall.Core.Point classicGatherOrigin;
    private readonly AttackRequestGate classicGatherGate = new();
    private bool ClassicGatherEnabled => ClassicControls && settings.GetValue("controls", "classic_gather", true).AsBool();

    private bool RetainTutorialGatherOnRelease()
        => GameplayInputAllowed && ClassicGatherEnabled && Snapshot is { } snapshot
            && ClassicInteractionRules.InTutorial(snapshot.Self, Data)
            && selectedTargetKind == "node" && selectedTarget == classicGatherTarget
            && snapshot.Nodes.FirstOrDefault(x => x.Id == classicGatherTarget) is { } node
            && node.Template.StartsWith("classic_", StringComparison.Ordinal)
            && ClassicGatherRules.Problem(snapshot.Self, node, Data, snapshot.Time) == "";

    private void BeginClassicGather(WorldTarget target)
    {
        if (!GameplayInputAllowed || Snapshot is not { } snapshot) return;
        var node = snapshot.Nodes.FirstOrDefault(x => x.Id == target.Id);
        string problem = ClassicGatherRules.Problem(snapshot.Self, node, Data, snapshot.Time);
        if (problem != "") { Notify(problem, true); return; }
        SelectTarget("node", target.Id); ClearRoute(); pendingInteraction = null;
        classicGatherTarget = target.Id; classicGatherOrigin = snapshot.Self.Position;
        classicGatherConfirmed = false; TickClassicGather();
    }

    private void TickClassicGather()
    {
        if (classicGatherTarget == "" || actionBusy || Snapshot is not { } snapshot) return;
        var node = snapshot.Nodes.FirstOrDefault(x => x.Id == classicGatherTarget);
        if (!GameplayInputAllowed || !ClassicGatherEnabled || selectedTarget != classicGatherTarget
            || selectedTargetKind != "node" || snapshot.Self.Position.Distance(classicGatherOrigin) > .15
            || Input.GetVector("move_left", "move_right", "move_up", "move_down").LengthSquared() > .01f
            || ClassicGatherRules.Problem(snapshot.Self, node, Data, snapshot.Time) != "")
        { classicGatherTarget = ""; classicGatherConfirmed = false; return; }
        if (node!.ReadyAt > snapshot.Time) return;
        if (!classicGatherGate.TryTake(Time.GetTicksMsec() / 1000.0, snapshot.Time,
            snapshot.Self.Cooldowns.GetValueOrDefault("gather"), true, 1.8)) return;
        _ = SendClassicGatherAsync(node.Id);
    }

    private async Task SendClassicGatherAsync(string id)
    {
        var result = await SendAsync(new GameCommand { Kind = "gather", Target = id });
        if (classicGatherTarget != id) return;
        if (result?.Ok == true) classicGatherConfirmed = true;
        else { classicGatherTarget = ""; classicGatherConfirmed = false; }
    }
}
