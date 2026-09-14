namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private QuestDef CurrentEndgameContract(string id)
    {
        var board=EndgameLoops.Today(Data,State.Time);
        int expected=EndgameLoops.Factions.Count*EndgameLoops.ContractsPerBoard;
        Need(board.Count==expected&&board.Select(x=>x.Id).Distinct(StringComparer.Ordinal).Count()==expected,"Faction contract rotation is invalid.");
        return board.FirstOrDefault(x=>x.Id==id)??throw new RuleException("That faction contract is not in the current rotation.");
    }

    private string AcceptEndgame(Character player,string id)
    {
        var quest=CurrentEndgameContract(id);var registrar=Data.Npc(quest.Giver);Near(player,registrar.Zone,registrar.Position,3);
        Need(Progression.PlayerLevel(player)>=quest.MinimumLevel,$"Requires character level {quest.MinimumLevel}.");
        Need(!player.Quests.ContainsKey(id),"You already accepted this faction contract.");
        Need(!player.CompletedQuests.Contains(id),"This faction contract was already claimed for this rotation.");
        Need(player.Quests.Keys.Count(EndgameLoops.IsContractId)<6,"Finish or abandon an active faction contract before taking another.");
        player.Quests[id]=new(){Counts=Enumerable.Repeat(0,quest.Objectives.Count).ToList()};
        return $"Accepted: {quest.Name} · {EndgameLoops.FactionName(quest.Faction)} {EndgameLoops.ReputationReward(quest)} reputation.";
    }

    private string ClaimEndgame(Character player,string id)
    {
        Need(EndgameLoops.IsContractId(id),"Unknown faction contract.");var quest=EndgameLoops.ResolveQuest(Data,id);var registrar=Data.Npc(quest.Giver);Near(player,registrar.Zone,registrar.Position,3);
        Need(player.Quests.TryGetValue(id,out var progress)&&progress.Complete,"This faction contract is not complete.");
        Need(!player.CompletedQuests.Contains(id),"This faction contract reward was already claimed.");
        Items.Grant(player,quest.Gold);
        var reputation=EndgameLoops.GrantReputation(player,quest.Faction,EndgameLoops.ReputationReward(quest));
        player.CompletedQuests.Add(id);player.Quests.Remove(id);
        int completed=player.CompletedQuests.Count(EndgameLoops.IsContractId);
        if(completed>=1)player.Achievements.Add("endgame_contract_1");
        if(completed>=10)player.Achievements.Add("endgame_contract_10");
        if(completed>=50)player.Achievements.Add("endgame_contract_50");
        string milestone=reputation.BonusGold>0?$" Rank milestone bonus: {reputation.BonusGold} gold.":"";
        return $"Completed: {quest.Name} · {quest.Gold} gold · +{reputation.Added} {EndgameLoops.FactionName(quest.Faction)} reputation ({reputation.Rank})."+milestone;
    }

    private string AbandonEndgame(Character player,string id)
    {
        Need(EndgameLoops.IsContractId(id)&&player.Quests.ContainsKey(id),"Faction contract not active.");
        player.Quests.Remove(id);return "Faction contract abandoned. No reward was granted.";
    }
}
