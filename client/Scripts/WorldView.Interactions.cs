using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class WorldView
{
    // Input availability belongs to authoritative snapshots, not renderer callbacks.
    // Keep the same visibility and lifetime rules used by world presentation.
    private void RefreshInteractionTargets()
    {
        interactions.Clear();
        if (Data is null) return;
        var zone = Data.Zone(ZoneId);
        foreach (var building in zone.Buildings)
        {
            var at = new Point(building.X + building.Width / 2.0, building.Y + building.Height);
            if (IsWithinCameraBounds(at, building.Width + building.Height) && JourneyProgression.IsLandmark(zone, building))
                interactions.Add(new WorldTarget("landmark", building.Id, building.Name, JourneyProgression.LandmarkPoint(building)));
        }
        foreach (var npc in Data.Npcs.Where(x => x.Zone == zone.Id && IsWithinCameraBounds(x.Position, 5)))
            interactions.Add(new WorldTarget("npc", npc.Id, npc.Name, npc.Position));
        if (Snapshot is not { } snapshot) return;
        if (ClassicInteractionRules.InTutorial(snapshot.Self, Data))
            foreach (var site in ClassicTutorialContent.Sites.Where(x => IsWithinCameraBounds(x.Position, 5)
                && ClassicInteractionRules.TutorialSite(snapshot.Self, Data, x.Id) is not null))
                interactions.Add(new WorldTarget("classic_site", site.Id, site.Name, site.Position));
        foreach (var worldEvent in snapshot.Events.Where(x => x.Zone == zone.Id && IsWithinCameraBounds(x.Position, 8) && WorldEventRules.SupportsInteraction(x)))
            interactions.Add(new WorldTarget("event", worldEvent.Id, worldEvent.Name, worldEvent.Position));
        foreach (var node in snapshot.Nodes.Where(x => IsWithinCameraBounds(x.Position, 5)))
        {
            string name = Data.Resources.FirstOrDefault(x => x.Id == node.Template)?.Name ?? Ui.Words(node.Template);
            interactions.Add(new WorldTarget("node", node.Id, name, node.Position));
        }
        foreach (var chest in snapshot.Chests)
            interactions.Add(new WorldTarget("chest", chest.Id, Ui.Words(chest.Kind) + " Chest", chest.Position));
        foreach (var pile in Loot.Where(x => double.IsFinite(x.Expires) && x.Expires > RealmTime))
            interactions.Add(new WorldTarget("loot", pile.Id, "Dropped loot", pile.Position));
        foreach (var mob in snapshot.Creatures.Where(x => x.Health > 0 && IsWithinCameraBounds(x.Position, 5)))
            interactions.Add(new WorldTarget("creature", mob.Id, Data.Mob(mob.Template).Name, mob.Position));
        foreach (var player in snapshot.Players)
            interactions.Add(new WorldTarget("player", player.Id, player.Name, player.Position));
    }

    private void UpdateWorldProjection()
    {
        Zoom = Math.Clamp(Zoom, 1, 3);
        Vector2 shake = Vector2.Zero;
        if (Clock < impactUntil)
        {
            float fade = (float)Math.Clamp((impactUntil - Clock) / .16, 0, 1);
            shake = new Vector2(MathF.Sin((float)Clock * 93f), MathF.Cos((float)Clock * 117f)) * impactStrength * fade;
        }
        origin = (Size / 2 - Pixels(Camera) * Zoom + shake).Round();
    }
}
