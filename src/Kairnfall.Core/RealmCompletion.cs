namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private readonly Dictionary<string, double> disconnectGrace = [];

    public void Connect(string characterId)
    {
        disconnectGrace.Remove(characterId);
        Active.Add(characterId);
    }

    public void BeginDisconnect(string characterId)
    {
        inputs.Remove(characterId);
        playerTargets.Remove(characterId);
        foreach (var trade in State.Trades.Values.Where(value => value.A.Character == characterId || value.B.Character == characterId).ToList())
            State.Trades.Remove(trade.Id);

        if (State.Characters.TryGetValue(characterId, out var player) && player.Health > 0 && State.Time - player.LastCombat < 8)
        {
            disconnectGrace[characterId] = State.Time + 10;
            Active.Add(characterId);
        }
        else
        {
            disconnectGrace.Remove(characterId);
            Active.Remove(characterId);
        }

        EconomicDirty = true;
    }

    public void TickDisconnectGrace()
    {
        foreach (var entry in disconnectGrace.ToList())
        {
            if (!State.Characters.TryGetValue(entry.Key, out var player) || player.Health <= 0 || entry.Value <= State.Time)
            {
                disconnectGrace.Remove(entry.Key);
                Active.Remove(entry.Key);
            }
        }
    }

    private string GuildRole(Character player, string target, string requestedRole)
    {
        var guild = MemberGroup(player, true);
        Need(guild.Leader == player.Id, "Only the guild leader can change member roles.");

        var member = ResolvePlayer(target);
        Need(member.Id != player.Id && guild.Members.Contains(member.Id), "Select another guild member.");

        var role = requestedRole.Trim().ToLowerInvariant();
        Need(role is "member" or "officer", "Guild role must be member or officer.");
        guild.Roles[member.Id] = role;
        return role == "officer" ? "Guild member promoted to officer." : "Guild member changed to member.";
    }

    private string PetDismiss(Character player)
    {
        Need(player.Pet != "", "You have no companion to dismiss.");
        var petId = player.Pet;
        player.Pet = "";

        if (State.Creatures.TryGetValue(petId, out var pet) && pet.Owner == player.Id)
        {
            pet.Owner = "";
            pet.Target = "";
            pet.Threat.Clear();
            pet.Home = pet.Position;
        }

        return "Companion released.";
    }

    private string Dismantle(Character player, string target)
    {
        Need(State.Nodes.TryGetValue(target, out var node), "Structure not found.");
        Need(node!.Owner == player.Id && node.Template.StartsWith("structure_", StringComparison.Ordinal), "You do not own this structure.");
        Near(player, node.Zone, node.Position, 3);

        var recipe = Data.Recipes.FirstOrDefault(value => value.Output == node.Template);
        if (recipe is not null)
        {
            foreach (var ingredient in recipe.Ingredients)
            {
                var recovered = ingredient.Value / 2;
                if (recovered > 0) Items.Add(player.Inventory, Items.Create(Data, ingredient.Key, recovered), Data);
            }
        }

        State.Nodes.Remove(target);
        Progress(player, "dismantle", node.Template);
        return "Structure dismantled. Half of eligible materials were recovered.";
    }
}
