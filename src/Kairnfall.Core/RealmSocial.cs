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
        var group=MemberGroup(p,guild); Need(group.Leader==p.Id||group.Roles.GetValueOrDefault(p.Id)=="officer","Only the leader or an officer can invite members.");
        var other=ResolvePlayer(target); Need(other.Id!=p.Id&&GroupId(other,guild)=="","That player is already in a group.");
        Need(group.Members.Count<(guild?100:6),"The group is full."); group.Invites.Add(other.Id); return "Invitation sent.";
    }
    private string GroupJoin(Character p,bool guild,string target)
    {
        Need(GroupId(p,guild)=="","Leave your current group first.");
        Need(Groups(guild).TryGetValue(target,out var group)&&group.Invites.Contains(p.Id),"You do not have an invitation to this group.");
        Need(group!.Members.Count<(guild?100:6),"The group is full.");
        group.Invites.Remove(p.Id); group.Members.Add(p.Id); group.Roles[p.Id]="member"; SetGroup(p,guild,group.Id); return "Joined "+group.Name+".";
    }
    private string GroupLeave(Character p,bool guild)
    {
        var group=MemberGroup(p,guild); group.Members.Remove(p.Id); group.Roles.Remove(p.Id); SetGroup(p,guild,"");
        if(group.Members.Count==0) Groups(guild).Remove(group.Id);
        else if(group.Leader==p.Id) { group.Leader=group.Members.OrderBy(x=>x,StringComparer.Ordinal).First(); group.Roles[group.Leader]="leader"; }
        CancelTradesFor(p.Id); return "Left the group.";
    }
    private string GroupKick(Character p,bool guild,string target)
    {
        var group=MemberGroup(p,guild); Need(group.Leader==p.Id,"Only the group leader can remove members.");
        var other=ResolvePlayer(target); Need(other.Id!=p.Id&&group.Members.Contains(other.Id),"Select another group member.");
        group.Members.Remove(other.Id); group.Roles.Remove(other.Id); SetGroup(other,guild,""); return "Member removed.";
    }
    private string GuildMessage(Character p,string text)
    {
        var group=MemberGroup(p,true); Need(group.Leader==p.Id||group.Roles.GetValueOrDefault(p.Id)=="officer","Only guild leadership can change the message.");
        Need(text.Length<=200&&!text.Any(char.IsControl),"The guild message must have at most 200 printable characters."); group.Message=text; return "Guild message updated.";
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
