using System.Globalization;
using System.Text.RegularExpressions;

namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private void CancelTradesFor(string character)
    {
        foreach(var trade in State.Trades.Values.Where(x=>x.A.Character==character||x.B.Character==character).ToList()) State.Trades.Remove(trade.Id);
    }
    private Character ResolvePlayer(string idOrName)
    {
        return State.Characters.GetValueOrDefault(idOrName)??State.Characters.Values.FirstOrDefault(x=>x.Name.Equals(idOrName,StringComparison.OrdinalIgnoreCase))??throw new RuleException("Character not found.");
    }
    private Trade GetTrade(Character p,string id)
    {
        Need(State.Trades.TryGetValue(id,out var trade),"Trade is no longer active.");
        Need(trade!.A.Character==p.Id||trade.B.Character==p.Id,"You are not part of this trade.");
        var a=Player(trade.A.Character); var b=Player(trade.B.Character);
        Need(Active.Contains(a.Id)&&Active.Contains(b.Id),"Both players must be online.");
        Near(a,b.Zone,b.Position,3); Need(trade.Expires>State.Time,"The trade has expired.");
        return trade;
    }
    private string TradeInvite(Character p,string target)
    {
        var other=ResolvePlayer(target); Need(other.Id!=p.Id&&Active.Contains(other.Id),"Select another online player.");
        Near(p,other.Zone,other.Position,3);
        Need(!State.Trades.Values.Any(x=>x.A.Character==p.Id||x.B.Character==p.Id||x.A.Character==other.Id||x.B.Character==other.Id),"One of the players already has an active trade.");
        var t=new Trade{A=new(){Character=p.Id},B=new(){Character=other.Id},Expires=State.Time+120}; State.Trades.Add(t.Id,t);
        return "Trade invitation sent. Both players must review and confirm the final offer.";
    }
    private string TradeChange(Character p,string id,string item,int amount,string gold)
    {
        var trade=GetTrade(p,id); var offer=trade.A.Character==p.Id?trade.A:trade.B;
        if(item!="")
        {
            if(amount==0) offer.Items.Remove(item);
            else
            {
                var owned=Items.Owned(p,item); Need(!Items.Equipped(p,item)&&amount>0&&amount<=owned.Quantity,"Invalid trade quantity or equipped item.");
                Need(Data.Item(owned.Template).Type!="quest","Quest items cannot be traded.");
                Need(offer.Items.Count<12||offer.Items.ContainsKey(item),"A trade can contain at most twelve item stacks."); offer.Items[item]=amount;
            }
        }
        if(gold!="")
        {
            Need(long.TryParse(gold,NumberStyles.None,CultureInfo.InvariantCulture,out var value)&&value>=0&&value<=p.Gold,"Invalid gold offer."); offer.Gold=value;
        }
        trade.Revision++; trade.A.Ready=false; trade.B.Ready=false; trade.A.Confirmed=false; trade.B.Confirmed=false; trade.A.ApprovedFingerprint=""; trade.B.ApprovedFingerprint=""; trade.Expires=State.Time+120;
        return "Offer changed. Both players must review it again.";
    }
    private string TradeReady(Character p,string id,int revision,bool confirm)
    {
        var trade = GetTrade(p, id);
        // Persist the reset as an acknowledged state change. Throwing here would
        // restore the stale consent through Execute's transaction rollback.
        if (InvalidateTradeConsent(trade))
            return "The trade contents changed. Both players must review the new offer.";
        Need(trade.Revision == revision, "The offer changed. Review the current revision.");
        Need(CanFulfillTradeOffer(trade.A) && CanFulfillTradeOffer(trade.B),
            "An offered item or the offered gold is no longer available.");
        var offer = trade.A.Character == p.Id ? trade.A : trade.B;
        if (!confirm)
        {
            offer.Ready = true;
            offer.Confirmed = false;
            // Each player approves BOTH offers, including the full item instance.
            offer.ApprovedFingerprint = TradeContentFingerprint(trade);
            return "Offer marked ready. Confirm after both players are ready.";
        }
        Need(trade.A.Ready && trade.B.Ready, "Both players must first mark their offers ready.");
        offer.Confirmed = true;
        if (!trade.A.Confirmed || !trade.B.Confirmed) return "Confirmed. Waiting for the other player.";
        var a=Player(trade.A.Character); var b=Player(trade.B.Character);
        var aItems=trade.A.Items.Select(x=>Items.Take(a.Inventory,x.Key,x.Value,a)).ToList();
        var bItems=trade.B.Items.Select(x=>Items.Take(b.Inventory,x.Key,x.Value,b)).ToList();
        Items.Spend(a,trade.A.Gold); Items.Spend(b,trade.B.Gold);
        foreach(var item in aItems) Items.Add(b.Inventory,item,Data);
        foreach(var item in bItems) Items.Add(a.Inventory,item,Data);
        Items.Grant(a,trade.B.Gold); Items.Grant(b,trade.A.Gold);
        State.Trades.Remove(id); Progress(a,"trade","*"); Progress(b,"trade","*");
        return "Trade completed.";
    }
    private string TradeCancel(Character p,string id)
    {
        var trade=GetTrade(p,id); State.Trades.Remove(trade.Id); return "Trade cancelled.";
    }
    private Dictionary<string,SocialGroup> Groups(bool guild)=>guild?State.Guilds:State.Parties;
    private string GroupId(Character p,bool guild)=>guild?p.Guild:p.Party;
    private void SetGroup(Character p,bool guild,string value) { if(guild) p.Guild=value; else p.Party=value; }
    private SocialGroup MemberGroup(Character p,bool guild)
    {
        Need(Groups(guild).TryGetValue(GroupId(p,guild),out var group)&&group.Members.Contains(p.Id),"You are not a member of this group."); return group!;
    }
    private string GroupCreate(Character p,bool guild,string name)
    {
        Need(GroupId(p,guild)=="","Leave your current group first.");
        if(guild)
        {
            Service(p,"guild_registrar"); Need(Regex.IsMatch(name,@"\A[A-Za-z][A-Za-z0-9 ]{2,23}\z"),"Use a guild name with 3–24 letters, digits, or spaces.");
            Need(!State.Guilds.Values.Any(x=>x.Name.Equals(name,StringComparison.OrdinalIgnoreCase)),"That guild name is taken."); Items.Spend(p,200);
        }
        var group=new SocialGroup{Name=guild?name:p.Name+"'s party",Leader=p.Id,Members=[p.Id],Roles=new(){{p.Id,"leader"}}};
        Groups(guild).Add(group.Id,group); SetGroup(p,guild,group.Id); return guild?"Guild created.":"Party created.";
    }
    private string GroupInvite(Character p,bool guild,string target)
    {
        if(!guild&&GroupId(p,false)=="") _=GroupCreate(p,false,"");
        var group=MemberGroup(p,guild); Need(group.Leader==p.Id||group.Roles.GetValueOrDefault(p.Id)=="officer","Only the leader or an officer can invite members.");
        var other=ResolvePlayer(target); Need(other.Id!=p.Id&&GroupId(other,guild)=="","That player is already in a group.");
        Need(group.Members.Count<(guild?100:6),"The group is full."); group.Invites.Add(other.Id); return "Invitation sent.";
    }
    private string GroupJoin(Character p,bool guild,string target)
    {
        Need(GroupId(p,guild)=="","Leave your current group first.");
        Need(Groups(guild).TryGetValue(target,out var group)&&group.Invites.Contains(p.Id),"You do not have an invitation to this group.");
        Need(group!.Members.Count<(guild?100:6),"The group is full.");
        group.Invites.Remove(p.Id); group.Members.Add(p.Id); group.Roles[p.Id]="member"; SetGroup(p,guild,group.Id);
        if(!guild)
        {
            ClearLfg(p); ResetReadyCheck(group);
            if(group.Members.Count>=6&&State.Characters.TryGetValue(group.Leader,out var leader)) ClearLfg(leader);
        }
        return "Joined "+group.Name+".";
    }
    private string GroupLeave(Character p,bool guild)
    {
        var group=MemberGroup(p,guild); group.Members.Remove(p.Id); group.Roles.Remove(p.Id); SetGroup(p,guild,"");
        if(!guild) { ClearLfg(p); ResetReadyCheck(group); }
        if(group.Members.Count==0) Groups(guild).Remove(group.Id);
        else if(group.Leader==p.Id) { group.Leader=group.Members.OrderBy(x=>x,StringComparer.Ordinal).First(); group.Roles[group.Leader]="leader"; }
        CancelTradesFor(p.Id); return "Left the group.";
    }
    private string GroupKick(Character p,bool guild,string target)
    {
        var group=MemberGroup(p,guild); Need(group.Leader==p.Id,"Only the group leader can remove members.");
        var other=ResolvePlayer(target); Need(other.Id!=p.Id&&group.Members.Contains(other.Id),"Select another group member.");
        group.Members.Remove(other.Id); group.Roles.Remove(other.Id); SetGroup(other,guild,"");
        if(!guild) { ClearLfg(other); ResetReadyCheck(group); }
        return "Member removed.";
    }
    private string GuildMessage(Character p,string text)
    {
        var group=MemberGroup(p,true); Need(group.Leader==p.Id||group.Roles.GetValueOrDefault(p.Id)=="officer","Only guild leadership can change the message.");
        Need(text.Length<=200&&!text.Any(char.IsControl),"The guild message must have at most 200 printable characters."); group.Message=text; return "Guild message updated.";
    }
    private void ClearLfg(Character player)
    {
        player.LfgActivity=""; player.LfgRole=""; player.LfgSince=0;
    }
    private void ResetReadyCheck(SocialGroup group)
    {
        group.ReadyCheckEnds=0; group.ReadyMembers.Clear();
    }
    private string LfgSet(Character player,string activity,string role)
    {
        activity=activity.Trim().ToLowerInvariant(); role=role.Trim().ToLowerInvariant();
        if(activity is "" or "off") { ClearLfg(player); return "Looking-for-group listing removed."; }
        Need(SocialCooperationRules.ValidActivity(activity),"Choose a valid group activity.");
        Need(SocialCooperationRules.ValidRole(role),"Choose tank, healer, damage, or flexible.");
        if(player.Party!="")
        {
            var party=MemberGroup(player,false);
            Need((party.Leader==player.Id||party.Roles.GetValueOrDefault(player.Id)=="officer")&&party.Members.Count<6,
                "Only party leadership can advertise an open party.");
        }
        player.LfgActivity=activity; player.LfgRole=role; player.LfgSince=State.Time;
        return $"LFG · {SocialCooperationRules.ActivityName(activity)} · {SocialCooperationRules.RoleName(role)}.";
    }
    private string LfgRequest(Character player,string target)
    {
        Need(player.Party=="","Leave your current party before requesting another group.");
        var listed=ResolvePlayer(target);
        Need(listed.Id!=player.Id&&Active.Contains(listed.Id)&&listed.LfgActivity!="","That listing is no longer available.");
        Need(!listed.Ignored.Contains(player.Id)&&!player.Ignored.Contains(listed.Id),"Group request unavailable.");
        if(listed.Party!="")
        {
            var party=MemberGroup(listed,false);
            Need(party.Leader==listed.Id||party.Roles.GetValueOrDefault(listed.Id)=="officer","That listing can no longer invite players.");
            Need(party.Members.Count<6,"That party is full.");
        }
        GroupInvite(listed,false,player.Id);
        return "Group invitation received from "+listed.Name+". Review it before joining.";
    }
    private string FriendInvite(Character player,string target)
    {
        var other=ResolvePlayer(target); Need(other.Id!=player.Id,"Select another player.");
        Need(!player.Friends.Contains(other.Id),"You are already friends.");
        Need(!other.Ignored.Contains(player.Id)&&!player.Ignored.Contains(other.Id),"Friend request unavailable.");
        if(player.FriendInvites.Contains(other.Id)) return FriendAccept(player,other.Id);
        other.FriendInvites.Add(player.Id); return "Friend request sent.";
    }
    private string FriendAccept(Character player,string target)
    {
        var other=ResolvePlayer(target); Need(player.FriendInvites.Remove(other.Id),"No friend request from that player.");
        Need(!other.Ignored.Contains(player.Id)&&!player.Ignored.Contains(other.Id),"Friend request unavailable.");
        player.Friends.Add(other.Id); other.Friends.Add(player.Id); other.FriendInvites.Remove(player.Id);
        return "You and "+other.Name+" are now friends.";
    }
    private string FriendRemove(Character player,string target)
    {
        var other=ResolvePlayer(target); bool changed=player.Friends.Remove(other.Id)|other.Friends.Remove(player.Id);
        changed|=player.FriendInvites.Remove(other.Id); changed|=other.FriendInvites.Remove(player.Id);
        Need(changed,"No friendship or pending request exists with that player."); return "Friend connection removed.";
    }
    private string PartyReadyStart(Character player)
    {
        var party=MemberGroup(player,false);
        Need(party.Leader==player.Id||party.Roles.GetValueOrDefault(player.Id)=="officer","Only party leadership can start a ready check.");
        party.ReadyMembers.Clear(); party.ReadyMembers.Add(player.Id); party.ReadyCheckEnds=State.Time+45;
        return "Ready check started for 45 seconds.";
    }
    private string PartyReady(Character player)
    {
        var party=MemberGroup(player,false); Need(party.ReadyCheckEnds>State.Time,"There is no active ready check.");
        party.ReadyMembers.Add(player.Id);
        int online=party.Members.Count(Active.Contains), ready=party.ReadyMembers.Count(Active.Contains);
        return ready>=online?$"Party ready · {ready}/{online}.":$"Ready · {ready}/{online} online members.";
    }
    private string GuildProject(Character player,string project)
    {
        var guild=MemberGroup(player,true);
        Need(guild.Leader==player.Id||guild.Roles.GetValueOrDefault(player.Id)=="officer","Only guild leadership can start projects.");
        project=project.Trim().ToLowerInvariant(); Need(SocialCooperationRules.ValidProject(project),"Choose a valid guild project.");
        Need(guild.Project=="","Finish the current guild project first.");
        guild.Project=project; guild.ProjectProgress=0; guild.ProjectGoal=SocialCooperationRules.ProjectGoal(guild,project);
        return $"Guild project started · {SocialCooperationRules.ProjectName(project)} · 0/{guild.ProjectGoal}.";
    }
    private void AdvanceGuildProject(Character player,string action,int amount)
    {
        if(player.Guild==""||amount<=0||!State.Guilds.TryGetValue(player.Guild,out var guild)||guild.Project==""||!SocialCooperationRules.ProjectMatches(guild.Project,action)) return;
        string project=guild.Project; int oldLevel=SocialCooperationRules.GuildLevel(guild);
        guild.ProjectProgress=Math.Min(guild.ProjectGoal,guild.ProjectProgress+Math.Clamp(amount,1,5));
        if(guild.ProjectProgress<guild.ProjectGoal) { EconomicDirty=true; return; }
        guild.Experience+=SocialCooperationRules.ProjectExperience(guild); guild.CompletedProjects++;
        int newLevel=SocialCooperationRules.GuildLevel(guild); long gold=SocialCooperationRules.ProjectMemberGold(guild);
        foreach(string id in guild.Members)
        {
            if(!State.Characters.TryGetValue(id,out var member)) continue;
            Items.Grant(member,gold); member.Achievements.Add("guild_project:"+project);
            if(newLevel>oldLevel) member.Achievements.Add("guild_level:"+newLevel);
        }
        guild.Project=""; guild.ProjectProgress=0; guild.ProjectGoal=0;
        guild.Message=$"{SocialCooperationRules.ProjectName(project)} completed · Guild level {newLevel} · {gold} gold awarded to every member.";
        EconomicDirty=true;
    }
    private string Revive(Character player,string target)
    {
        var other=ResolvePlayer(target); Need(other.Id!=player.Id,"You cannot revive yourself.");
        Need(player.Party!=""&&other.Party==player.Party,"You can revive a party member.");
        Need(Active.Contains(other.Id),"That party member is offline."); Need(other.Health<=0,"That party member is not downed.");
        Near(player,other.Zone,other.Position,2.6); Ready(player,"revive",10); Need(player.Stamina>=20,"You need 20 stamina to revive an ally.");
        player.Stamina-=20; var stats=CombatMath.Stats(other,Data); double restored=Math.Max(1,stats.Health*.35);
        other.Health=restored; other.Mana=Math.Max(1,stats.Mana*.20); other.Stamina=Math.Max(1,stats.Stamina*.25); other.DeadUntil=0;
        other.Statuses.Clear(); ApplyStatus(other.Statuses,"revive_sickness",Element.Radiant,10,.20,player.Id); other.LastCombat=State.Time;
        player.Achievements.Add("field_medic"); Progress(player,"revive","*"); RecordEventSupport(player,other,restored);
        return "Revived "+other.Name+" at 35% health.";
    }
    private List<Character> CooperativeKillRecipients(Creature mob,IReadOnlyCollection<Character> direct)
    {
        var recipients=direct.ToDictionary(x=>x.Id,x=>x,StringComparer.Ordinal);
        foreach(var contributor in direct.Where(x=>x.Party!=""))
        {
            if(!State.Parties.TryGetValue(contributor.Party,out var party)) continue;
            foreach(string id in party.Members)
            {
                if(!State.Characters.TryGetValue(id,out var member)||!Active.Contains(id)||member.Health<=0||member.Zone!=mob.Zone||member.Position.Distance(mob.Position)>SocialCooperationRules.PartyShareRadius) continue;
                if(recipients.ContainsKey(id)||State.Time-member.LastCombat<=SocialCooperationRules.PartySupportWindow) recipients[id]=member;
            }
        }
        return recipients.Values.OrderBy(x=>x.Id,StringComparer.Ordinal).ToList();
    }
    private Character CooperativeLootOwner(Creature mob,IReadOnlyCollection<Character> direct,IReadOnlyCollection<Character> recipients)
    {
        var anchor=direct.OrderByDescending(x=>mob.Threat.GetValueOrDefault(x.Id)).First();
        if(anchor.Party==""||!State.Parties.TryGetValue(anchor.Party,out var party)) return anchor;
        var eligible=recipients.Where(x=>x.Party==anchor.Party).OrderBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        if(eligible.Length==0) return anchor;
        int index=((party.LootCursor%eligible.Length)+eligible.Length)%eligible.Length; party.LootCursor=(party.LootCursor+1)%1000000;
        return eligible[index];
    }
    private double CooperativeGuildMultiplier(Character player,IReadOnlyCollection<Character> recipients)
    {
        if(player.Guild==""||!State.Guilds.TryGetValue(player.Guild,out var guild)||recipients.Count(x=>x.Guild==player.Guild)<2) return 1;
        return SocialCooperationRules.GuildFellowshipMultiplier(guild);
    }
    private void TickSocialCooperation()
    {
        bool changed=false;
        var online=Active.Where(State.Characters.ContainsKey).Select(Player).ToArray();
        for(int a=0;a<online.Length;a++) for(int b=a+1;b<online.Length;b++)
        {
            var left=online[a]; var right=online[b];
            if(left.Zone!=right.Zone||left.Position.Distance(right.Position)>24) continue;
            if(!left.RecentPlayers.ContainsKey(right.Id)||left.RecentPlayers[right.Id]<State.Time-30) { left.RecentPlayers[right.Id]=State.Time; changed=true; }
            if(!right.RecentPlayers.ContainsKey(left.Id)||right.RecentPlayers[left.Id]<State.Time-30) { right.RecentPlayers[left.Id]=State.Time; changed=true; }
        }
        foreach(var player in State.Characters.Values)
            foreach(var id in player.RecentPlayers.Where(x=>x.Value<State.Time-SocialCooperationRules.RecentPlayerLifetime).Select(x=>x.Key).ToArray()) { player.RecentPlayers.Remove(id); changed=true; }
        foreach(var party in State.Parties.Values)
        {
            party.ReadyMembers.RemoveWhere(id=>!party.Members.Contains(id));
            if(party.ReadyCheckEnds>0&&party.ReadyCheckEnds<=State.Time) { ResetReadyCheck(party); changed=true; }
        }
        if(changed) EconomicDirty=true;
    }

    private string Chat(Character p,string channel,string target,string text)
    {
        Need(new[]{"local","global","party","guild","whisper"}.Contains(channel),"Invalid chat channel.");
        text=text.Trim(); Need(text.Length is >0 and <=240&&!text.Any(char.IsControl),"Messages must have 1–240 printable characters.");
        Ready(p,"chat",0.75);
        if(channel=="party") MemberGroup(p,false);
        if(channel=="guild") MemberGroup(p,true);
        if(channel=="whisper") { var recipient=ResolvePlayer(target); Need(Active.Contains(recipient.Id),"The recipient is offline."); target=recipient.Id; }
        OutgoingChat.Add(new(){Channel=channel,Sender=p.Id,Name=p.Name,Target=target,Text=text,Time=State.Time}); return "";
    }
    public bool CanReceiveChat(string recipient,ChatMessage message)
    {
        if(!State.Characters.TryGetValue(recipient,out var p)||!State.Characters.TryGetValue(message.Sender,out var sender)||p.Ignored.Contains(sender.Id)) return false;
        return message.Channel switch
        {
            "global" => true,
            "local" => p.Zone==sender.Zone&&p.Position.Distance(sender.Position)<=24,
            "party" => p.Party!=""&&p.Party==sender.Party,
            "guild" => p.Guild!=""&&p.Guild==sender.Guild,
            "whisper" => p.Id==message.Target||p.Id==sender.Id,
            _ => false
        };
    }
}
