namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    /// <summary>
    /// Remove state whose authority depends on a live socket. Durable social membership,
    /// combat damage/status timers, loot, pets, cooldowns and world events are preserved.
    /// </summary>
    public void ResetTransientConnectionState()
    {
        Active.Clear();
        inputs.Clear();
        playerTargets.Clear();
        transitionReady.Clear();
        OutgoingChat.Clear();

        bool changed=State.Trades.Count>0;
        State.Trades.Clear();
        foreach(var player in State.Characters.Values)
        {
            if(player.LfgActivity!=""||player.LfgRole!=""||player.LfgSince!=0) changed=true;
            ClearLfg(player);
        }
        foreach(var party in State.Parties.Values)
        {
            if(party.ReadyCheckEnds!=0||party.ReadyMembers.Count>0) changed=true;
            ResetReadyCheck(party);
        }
        foreach(var creature in State.Creatures.Values)
        {
            if(creature.Target!=""||creature.Threat.Count>0) changed=true;
            creature.Target=""; creature.Threat.Clear();
        }
        if(changed) EconomicDirty=true;
    }
}
