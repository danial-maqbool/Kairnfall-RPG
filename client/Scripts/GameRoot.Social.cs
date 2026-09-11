using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private string SocialName(string id) => Connection?.LastSnapshot?.Names.GetValueOrDefault(id) ?? PlayerName(id);

    private void BuildSocialPage()
    {
        if (page is null || Snapshot is null) return;
        var top = Ui.Row(page); var recipient = Ui.Edit("Character name or selected player", selectedTargetKind == "player" ? SocialName(selectedTarget) : ""); top.AddChild(recipient);
        top.AddChild(Ui.Button("Invite to party", () => Send("party_invite", recipient.Text.Trim())));
        top.AddChild(Ui.Button("Trade", () => Send("trade_invite", recipient.Text.Trim())));
        top.AddChild(Ui.Button("Add friend", () => Send("friend_invite", recipient.Text.Trim())));
        var whisperRow = Ui.Row(page); var message = Ui.Edit("Private message"); message.MaxLength = 240; whisperRow.AddChild(message);
        whisperRow.AddChild(Ui.Button("Whisper", () => { Send("chat", "whisper", recipient.Text.Trim(), arg: message.Text.Trim()); message.Text = ""; }));
        var lfgRow = Ui.Row(page);
        var activity = new OptionButton(); foreach (var value in SocialCooperationRules.LfgActivities) activity.AddItem(SocialCooperationRules.ActivityName(value)); lfgRow.AddChild(activity);
        var role = new OptionButton(); foreach (var value in SocialCooperationRules.LfgRoles) role.AddItem(SocialCooperationRules.RoleName(value)); lfgRow.AddChild(role);
        lfgRow.AddChild(Ui.Button("Advertise / update LFG", () => Send("lfg_set", SocialCooperationRules.LfgActivities[Math.Max(0, activity.Selected)], arg: SocialCooperationRules.LfgRoles[Math.Max(0, role.Selected)])));
        lfgRow.AddChild(Ui.Button("Stop LFG", () => Send("lfg_set", "off")));
        var inspection = Ui.Label("Inspect nearby players to compare class, level, guild, and visible equipment.", 13, Ui.Muted, true); page.AddChild(inspection);
        var scroll = Ui.Scroll(page, new Vector2(870, 440)); var body = Ui.Column(scroll);
        void Render()
        {
            if (Snapshot is null) return;
            Ui.Clear(body);
            if(Snapshot.Self.LfgActivity!="") body.AddChild(Ui.Label("YOUR LFG · "+SocialCooperationRules.ActivityName(Snapshot.Self.LfgActivity)+" · "+SocialCooperationRules.RoleName(Snapshot.Self.LfgRole),14,Ui.Success,true));
            if(friendInvitations.Count>0)
            {
                body.AddChild(Ui.Label("Friend requests",21,Ui.Gold));
                foreach(string id in friendInvitations)
                {
                    var row=Ui.Row(body); row.AddChild(Ui.Label(SocialName(id),16));
                    row.AddChild(Ui.Button("Accept",()=>Send("friend_accept",id)));
                    row.AddChild(Ui.Button("Dismiss",()=>Send("friend_remove",id)));
                }
            }
            if (invitations.Count > 0)
            {
                body.AddChild(Ui.Label("Invitations", 21, Ui.Gold));
                foreach (var invitation in invitations)
                {
                    var row = Ui.Row(body); row.AddChild(Ui.Label(invitation.Name + " · " + SocialName(invitation.Leader), 16));
                    row.AddChild(Ui.Button("Join", () => Send(invitation.Guild ? "guild_join" : "party_join", invitation.Id)));
                }
            }
            if(lfgListings.Count>0)
            {
                body.AddChild(Ui.Label("Looking for group",21,Ui.Gold));
                foreach(var listing in lfgListings)
                {
                    var row=Ui.Row(body); string zone=Data.Zones.Any(x=>x.Id==listing.Zone)?Data.Zone(listing.Zone).Name:listing.Zone;
                    var text=Ui.Label($"{listing.Name} · Lv {listing.Level} {Data.Class(listing.Class).Name} · {SocialCooperationRules.RoleName(listing.Role)} · {SocialCooperationRules.ActivityName(listing.Activity)} · {zone} · {listing.PartySize}/6",14,Ui.Text,true);
                    text.SizeFlagsHorizontal=SizeFlags.ExpandFill; row.AddChild(text);
                    row.AddChild(Ui.Button("Request group",()=>Send("lfg_request",listing.Character),Snapshot.Self.Party!=""));
                    row.AddChild(Ui.Button("Select",()=>{recipient.Text=listing.Name;SelectTarget("player",listing.Character);}));
                }
            }
            foreach (var trade in Snapshot.Trades)
            {
                var other = trade.A.Character == Snapshot.Self.Id ? trade.B.Character : trade.A.Character;
                body.AddChild(Ui.Button("Review trade with " + SocialName(other), () => { selectedTrade = trade.Id; OpenPage("Trade"); }));
            }
            DrawGroup(body, Snapshot.Party, false, recipient);
            DrawGroup(body, Snapshot.Guild, true, recipient);
            body.AddChild(Ui.Label("Nearby travelers", 21, Ui.Gold));
            foreach (var player in Snapshot.Players)
            {
                var row = Ui.Row(body); row.AddChild(Ui.Label((player.Health<=0?"DOWNED · ":"")+player.Name + " · Level " + player.Level + " · " + Data.Class(player.Class).Name, 16, player.Health<=0?Ui.Danger:Ui.Text));
                row.AddChild(Ui.Button("Inspect", () => { SelectTarget("player", player.Id); recipient.Text = player.Name; inspection.Text=DescribeSocialPlayer(player); }));
                row.AddChild(Ui.Button(Snapshot.Self.Friends.Contains(player.Id)?"Friend":"Add friend", () => { if(!Snapshot.Self.Friends.Contains(player.Id)) Send("friend_invite",player.Id); }, Snapshot.Self.Friends.Contains(player.Id)));
                row.AddChild(Ui.Button(Snapshot.Self.Ignored.Contains(player.Id) ? "Unmute" : "Mute", () => Send("ignore", player.Id)));
            }
            if (Snapshot.Players.Count == 0) body.AddChild(Ui.Label("No other players are in view. Party and guild invitations also accept character names.", 15, Ui.Muted, true));
            var friends=socialProfiles.Where(x=>x.Friend).OrderByDescending(x=>x.Online).ThenBy(x=>x.Name,StringComparer.OrdinalIgnoreCase).ToArray();
            if(friends.Length>0)
            {
                body.AddChild(Ui.Label("Friends",21,Ui.Gold));
                foreach(var profile in friends) DrawSocialProfile(body,profile,recipient);
            }
            var recent=socialProfiles.Where(x=>!x.Friend&&x.LastSeen>0).OrderByDescending(x=>x.LastSeen).Take(12).ToArray();
            if(recent.Length>0)
            {
                body.AddChild(Ui.Label("Recent travelers",21,Ui.Gold));
                foreach(var profile in recent) DrawSocialProfile(body,profile,recipient);
            }
        }
        refreshPage = Render; Render();
    }

    private string DescribeSocialPlayer(PublicPlayer player)
    {
        string guild=socialProfiles.FirstOrDefault(x=>x.Id==player.Id)?.Guild??"";
        string gear=player.Equipment.Count==0?"No visible equipment":string.Join(", ",player.Equipment.OrderBy(x=>x.Key,StringComparer.Ordinal).Select(x=>Ui.Words(x.Key)+": "+Data.Item(x.Value).Name));
        return $"{player.Name} · Level {player.Level} {Data.Class(player.Class).Name}"+(guild==""?"":" · "+guild)+"\n"+gear;
    }
    private void DrawSocialProfile(Node parent,SocialProfile profile,LineEdit recipient)
    {
        if(Snapshot is null)return;
        var row=Ui.Row(parent); string zone=Data.Zones.Any(x=>x.Id==profile.Zone)?Data.Zone(profile.Zone).Name:profile.Zone;
        string presence=profile.Online?"Online · "+zone:profile.LastSeen>0?$"Last seen {Math.Max(0,(Snapshot.Time-profile.LastSeen)/60):0} realm min ago":"Offline";
        var label=Ui.Label($"{profile.Name} · Lv {profile.Level} {Data.Class(profile.Class).Name}"+(profile.Guild==""?"":" · "+profile.Guild)+" · "+presence,14,profile.Online?Ui.Text:Ui.Muted,true);
        label.SizeFlagsHorizontal=SizeFlags.ExpandFill; row.AddChild(label);
        row.AddChild(Ui.Button("Select",()=>{recipient.Text=profile.Name;SelectTarget("player",profile.Id);}));
        if(profile.Friend) row.AddChild(Ui.Button("Remove friend",()=>Confirm("Remove friend","Remove "+profile.Name+" from your friends?",()=>Send("friend_remove",profile.Id))));
    }

    private void DrawGroup(Node parent, SocialGroup? group, bool guild, LineEdit recipient)
    {
        if (Snapshot is null) return;
        var card = new PanelContainer(); parent.AddChild(card); var column = Ui.Column(card);
        column.AddChild(Ui.Label(guild ? "Guild" : "Party", 22, Ui.Gold));
        if (group is null)
        {
            if (guild)
            {
                var row = Ui.Row(column); var name = Ui.Edit("Guild name"); name.MaxLength = 24; row.AddChild(name);
                row.AddChild(Ui.Button("Found guild · 200 gold", () => Confirm("Found a guild", "Create this guild for 200 gold?", () => Send("guild_create", arg: name.Text.Trim())), !NearRole("guild_registrar")));
                column.AddChild(Ui.Label("Visit a guild registrar to found a guild. Existing guilds can invite you by character name.", 14, Ui.Muted, true));
            }
            else column.AddChild(Ui.Button("Create party", () => Send("party_create")));
            return;
        }
        column.AddChild(Ui.Label(group.Name, 20));
        bool leadership=group.Leader==Snapshot.Self.Id||group.Roles.GetValueOrDefault(Snapshot.Self.Id)=="officer";
        if(guild)
        {
            int level=SocialCooperationRules.GuildLevel(group);
            column.AddChild(Ui.Label($"Guild level {level} · {group.Experience:N0} renown · {group.CompletedProjects} projects completed",14,Ui.Success,true));
            if(group.Project!="") column.AddChild(Ui.Label($"PROJECT · {SocialCooperationRules.ProjectName(group.Project)} · {group.ProjectProgress}/{group.ProjectGoal}",14,Ui.Gold,true));
            else if(leadership)
            {
                var projects=Ui.Row(column);
                foreach(string project in SocialCooperationRules.GuildProjects) projects.AddChild(Ui.Button(SocialCooperationRules.ProjectName(project),()=>Send("guild_project",project)));
            }
        }
        else
        {
            bool ready=group.ReadyCheckEnds>Snapshot.Time;
            int online=group.Members.Count(id=>id==Snapshot.Self.Id||socialProfiles.Any(x=>x.Id==id&&x.Online));
            int readyCount=group.ReadyMembers.Count(id=>group.Members.Contains(id));
            if(ready)
            {
                var readyRow=Ui.Row(column); readyRow.AddChild(Ui.Label($"READY CHECK · {readyCount}/{Math.Max(1,online)} online members · {Math.Max(0,Math.Ceiling(group.ReadyCheckEnds-Snapshot.Time))}s",14,Ui.Gold,true));
                if(!group.ReadyMembers.Contains(Snapshot.Self.Id)) readyRow.AddChild(Ui.Button("I'm ready",()=>Send("party_ready")));
            }
            else if(leadership) column.AddChild(Ui.Button("Start ready check",()=>Send("party_ready_start")));
        }
        if (group.Message != "") column.AddChild(Ui.Label(group.Message, 16, Ui.Muted, true));
        foreach (string member in group.Members)
        {
            var row = Ui.Row(column); string presence = member == Snapshot.Self.Id || Snapshot.Players.Any(x => x.Id == member) ? "Nearby" : socialProfiles.Any(x=>x.Id==member&&x.Online)?"Online elsewhere":"Offline";
            string readyMark=!guild&&group.ReadyCheckEnds>Snapshot.Time?(group.ReadyMembers.Contains(member)?" · READY":" · not ready"):"";
            var label = Ui.Label(SocialName(member) + " · " + Ui.Words(group.Roles.GetValueOrDefault(member, "member")) + " · " + presence+readyMark, 15); label.SizeFlagsHorizontal = SizeFlags.ExpandFill; row.AddChild(label);
            if(!guild&&member!=Snapshot.Self.Id&&Snapshot.Players.FirstOrDefault(x=>x.Id==member) is {Health:<=0}) row.AddChild(Ui.Button("Revive",()=>Send("revive",member),Snapshot.Self.Health<=0));
            if(guild&&group.Leader==Snapshot.Self.Id&&member!=Snapshot.Self.Id)
            {
                string current=group.Roles.GetValueOrDefault(member,"member");
                row.AddChild(Ui.Button(current=="officer"?"Demote":"Promote",()=>Send("guild_role",member,arg:current=="officer"?"member":"officer")));
            }
            if (group.Leader == Snapshot.Self.Id && member != Snapshot.Self.Id)
                row.AddChild(Ui.Button("Remove", () => Confirm("Remove member", "Remove " + SocialName(member) + " from " + group.Name + "?", () => Send(guild ? "guild_kick" : "party_kick", member))));
        }
        var actions = Ui.Row(column);
        actions.AddChild(Ui.Button("Invite selected name", () => Send(guild ? "guild_invite" : "party_invite", recipient.Text.Trim()), group.Leader != Snapshot.Self.Id && group.Roles.GetValueOrDefault(Snapshot.Self.Id) != "officer"));
        actions.AddChild(Ui.Button("Leave", () => Confirm("Leave group", "Leave " + group.Name + "?", () => Send(guild ? "guild_leave" : "party_leave"))));
        if (guild && (group.Leader == Snapshot.Self.Id || group.Roles.GetValueOrDefault(Snapshot.Self.Id) == "officer"))
        {
            var row = Ui.Row(column); var announcement = Ui.Edit("Guild announcement", group.Message); announcement.MaxLength = 200; row.AddChild(announcement); row.AddChild(Ui.Button("Update message", () => Send("guild_message", arg: announcement.Text)));
        }
    }

    private void BuildTradePage()
    {
        if (page is null || Snapshot is null) return;
        var trade = Snapshot.Trades.FirstOrDefault(x => x.Id == selectedTrade) ?? Snapshot.Trades.FirstOrDefault();
        if (trade is null) { page.AddChild(Ui.Label("No active trade. Select a nearby player and send a trade invitation.", 18, Ui.Muted, true)); return; }
        selectedTrade = trade.Id;
        page.AddChild(Ui.Label("Review both offers. Any offer change resets both readiness and confirmation. Items transfer only after both final confirmations.", 15, Ui.Muted, true));
        var top = Ui.Row(page); var inventory = Snapshot.Self.Inventory.Where(x => !Items.Equipped(Snapshot.Self, x.Id) && Data.Item(x.Template).Type != "quest").ToArray();
        var pick = new OptionButton { SizeFlagsHorizontal = SizeFlags.ExpandFill }; foreach (var item in inventory) pick.AddItem(Data.Item(item.Template).Name + " ×" + item.Quantity); top.AddChild(pick);
        var amount = new SpinBox { MinValue = 1, MaxValue = 999, Value = 1, CustomMinimumSize = new Vector2(92, 32) }; top.AddChild(amount);
        top.AddChild(Ui.Button("Add item", () => { if (pick.Selected >= 0 && pick.Selected < inventory.Length) Send("trade_offer", selectedTrade, inventory[pick.Selected].Id, Quantity(amount)); }, inventory.Length == 0));
        var goldRow = Ui.Row(page); var gold = Ui.Edit("Gold offered", "0"); gold.MaxLength = 13; goldRow.AddChild(gold); goldRow.AddChild(Ui.Button("Set gold offer", () => Send("trade_offer", selectedTrade, arg: gold.Text.Trim())));
        var state = Ui.Label("", 15, Ui.Muted, true); page.AddChild(state);
        var offers = Ui.Row(page); offers.SizeFlagsVertical = SizeFlags.ExpandFill;
        var mine = Ui.Column(Ui.Scroll(offers, new Vector2(400, 310))); var theirs = Ui.Column(Ui.Scroll(offers, new Vector2(400, 310)));
        var controls = Ui.Row(page);
        Button ready = null!, confirm = null!;
        int shownRevision = -1; bool inspected = false;
        ready = Ui.Button("1. Mark ready", () => { if (inspected) Send("trade_ready", selectedTrade, amount: shownRevision); }); controls.AddChild(ready);
        confirm = Ui.Button("2. Confirm trade", () => { if (inspected) Send("trade_confirm", selectedTrade, amount: shownRevision); }); controls.AddChild(confirm);
        controls.AddChild(Ui.Button("Cancel trade", () => Send("trade_cancel", selectedTrade)));
        void Render()
        {
            if (Snapshot is null) return;
            Ui.Clear(mine); Ui.Clear(theirs);
            var current = Snapshot.Trades.FirstOrDefault(x => x.Id == selectedTrade);
            if (current is null) { state.Text = "This trade has ended. Inspect your backpack and gold balance."; ready.Disabled = true; confirm.Disabled = true; return; }
            shownRevision = current.Revision;
            var myOffer = current.A.Character == Snapshot.Self.Id ? current.A : current.B;
            var otherOffer = current.A.Character == Snapshot.Self.Id ? current.B : current.A;
            var previews = Connection?.LastSnapshot?.TradeItems.Where(x => x.TradeId == current.Id && x.Revision == current.Revision).ToArray() ?? [];
            inspected = new[] { myOffer, otherOffer }.All(offer => offer.Items.All(entry => previews.Any(p => p.Owner == offer.Character && p.Item.Id == entry.Key && p.Item.Quantity == entry.Value)));
            DrawOffer(mine, myOffer, previews, true); DrawOffer(theirs, otherOffer, previews, false);
            state.Text = $"Offer revision {current.Revision} · Your gold {Snapshot.Self.Gold:N0}\n" + (!inspected ? "Waiting for current item details. Confirmation is disabled." : "Inspect rarity, runes, quantities, and statistics before confirming.");
            ready.Disabled = !inspected || myOffer.Ready; confirm.Disabled = !inspected || !current.A.Ready || !current.B.Ready || myOffer.Confirmed;
            ready.Text = myOffer.Ready ? "Ready" : "1. Mark ready"; confirm.Text = myOffer.Confirmed ? "Confirmed · waiting" : "2. Confirm trade";
        }
        refreshPage = Render; Render();
    }
    private void DrawOffer(Node parent, TradeOffer offer, TradePreview[] previews, bool own)
    {
        parent.AddChild(Ui.Label(own ? "Your offer" : SocialName(offer.Character) + " offers", 22, Ui.Gold));
        parent.AddChild(Ui.Label(offer.Gold.ToString("N0") + " gold", 19, Ui.Success));
        parent.AddChild(Ui.Label(offer.Confirmed ? "Final confirmation received" : offer.Ready ? "Ready for final review" : "Editing offer", 14, Ui.Muted));
        foreach (var entry in offer.Items)
        {
            var preview = previews.FirstOrDefault(x => x.Owner == offer.Character && x.Item.Id == entry.Key);
            if (preview is null) { parent.AddChild(Ui.Label("Waiting for item inspection data…", 15, Ui.Danger)); continue; }
            var row = Ui.Row(parent); row.AddChild(Ui.Image(Assets.Icon(preview.Item.Template), 48)); var details = Ui.Column(row);
            details.AddChild(Ui.Label(Data.Item(preview.Item.Template).Name + " ×" + entry.Value, 17, Ui.RarityColor(preview.Item.Rarity), true));
            details.AddChild(Ui.Label(preview.Item.Rarity + " · Runes " + preview.Item.Runes.Count + "/" + preview.Item.Sockets + " · Durability " + preview.Item.Durability + "%", 13, Ui.Muted, true)); row.TooltipText = ItemDescription(preview.Item, false);
            if (own) row.AddChild(Ui.Button("Remove", () => Send("trade_offer", selectedTrade, entry.Key, 0)));
        }
    }

    private void BuildAuctionPage()
    {
        if (page is null || Snapshot is null) return;
        page.AddChild(Ui.Label("Listings sell as complete stacks. Listing fees are 2% of the price, with a one-gold minimum. Cancelled listings do not refund the fee.", 15, Ui.Muted, true));
        var search = Ui.Edit("Search listed items, rarity, or material"); page.AddChild(search);
        var row = Ui.Row(page); var inventory = Snapshot.Self.Inventory.Where(x => !Items.Equipped(Snapshot.Self, x.Id) && Data.Item(x.Template).Type != "quest").ToArray();
        var pick = new OptionButton { SizeFlagsHorizontal = SizeFlags.ExpandFill }; foreach (var item in inventory) pick.AddItem(Data.Item(item.Template).Name + " ×" + item.Quantity); row.AddChild(pick);
        var quantity = new SpinBox { MinValue = 1, MaxValue = 999, Value = 1, CustomMinimumSize = new Vector2(80, 34) }; row.AddChild(quantity);
        var price = Ui.Edit("Total price in gold"); price.MaxLength = 10; row.AddChild(price);
        row.AddChild(Ui.Button("Create listing", () =>
        {
            if (pick.Selected < 0 || pick.Selected >= inventory.Length) return;
            if (!long.TryParse(price.Text, out long value) || value is < 1 or > 1_000_000_000) { Notify("Use a whole-gold price from 1 to 1,000,000,000.", true); return; }
            var selected = inventory[pick.Selected]; int count = Quantity(quantity);
            Confirm("Create auction listing", $"List {count} {Data.Item(selected.Template).Name} for {value:N0} gold?\nListing fee: {Math.Max(1, value / 50):N0} gold.", () => Send("auction_list", value.ToString(System.Globalization.CultureInfo.InvariantCulture), selected.Id, count));
        }, inventory.Length == 0 || !NearRole("auctioneer")));
        var money = Ui.Label("", 15, Ui.Muted); page.AddChild(money); var rows = Ui.Column(Ui.Scroll(page, new Vector2(860, 350)));
        void Render()
        {
            if (Snapshot is null) return;
            Ui.Clear(rows); money.Text = $"Your gold: {Snapshot.Self.Gold:N0}  ·  Listings shown: {Snapshot.Auctions.Count}" + (!NearRole("auctioneer") ? "  ·  Move closer to an auctioneer." : "");
            foreach (var auction in Snapshot.Auctions.Where(x => (Data.Item(x.Item.Template).Name + " " + x.Item.Rarity + " " + Data.Item(x.Item.Template).Material).Contains(search.Text, StringComparison.OrdinalIgnoreCase)).OrderBy(x => x.Price))
            {
                var line = Ui.Row(rows); line.AddChild(Ui.Image(Assets.Icon(auction.Item.Template), 48)); var text = Ui.Column(line);
                text.AddChild(Ui.Label(Data.Item(auction.Item.Template).Name + " ×" + auction.Item.Quantity, 18, Ui.RarityColor(auction.Item.Rarity)));
                text.AddChild(Ui.Label($"{auction.Item.Rarity} · {auction.Price:N0} gold total · {Math.Max(0, (auction.Expires - Snapshot.Time) / 60):0} realm minutes left", 13, Ui.Muted)); line.TooltipText = ItemDescription(auction.Item, false);
                if (auction.Seller == Snapshot.Self.Id) line.AddChild(Ui.Button("Cancel listing", () => Send("auction_cancel", auction.Id), !NearRole("auctioneer")));
                else line.AddChild(Ui.Button("Purchase", () => Confirm("Purchase listing", $"Buy {auction.Item.Quantity} {Data.Item(auction.Item.Template).Name} for {auction.Price:N0} gold?", () => Send("auction_buy", auction.Id)), !NearRole("auctioneer") || Snapshot.Self.Gold < auction.Price));
            }
            if (rows.GetChildCount() == 0) rows.AddChild(Ui.Label("No matching listings. Players can list crafted equipment, materials, and other tradeable items here.", 17, Ui.Muted, true));
        }
        refreshPage = Render; search.TextChanged += _ => Render(); Render();
    }
}
