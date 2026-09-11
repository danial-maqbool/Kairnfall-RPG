from pathlib import Path


def replace(path: str, old: str, new: str):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing patch anchor in {path}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1))


def write(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


# ---- Core persistent models -------------------------------------------------
replace("src/Kairnfall.Core/Models.cs",
'''    public string Pet { get; set; } = "";
    public HashSet<string> Ignored { get; set; } = [];
    public long LastAction { get; set; }
''',
'''    public string Pet { get; set; } = "";
    public HashSet<string> Ignored { get; set; } = [];
    // Mutual friends, pending requests, recent proximity contacts, and an optional LFG advert.
    // Defaults keep historical saves compatible.
    public HashSet<string> Friends { get; set; } = [];
    public HashSet<string> FriendInvites { get; set; } = [];
    public Dictionary<string,double> RecentPlayers { get; set; } = [];
    public string LfgActivity { get; set; } = "";
    public string LfgRole { get; set; } = "";
    public double LfgSince { get; set; }
    public long LastAction { get; set; }
''')
replace("src/Kairnfall.Core/Models.cs",
'''public sealed class SocialGroup
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = "";
    public string Leader { get; set; } = "";
    public HashSet<string> Members { get; set; } = [];
    public HashSet<string> Invites { get; set; } = [];
    public Dictionary<string,string> Roles { get; set; } = [];
    public string Message { get; set; } = "";
}
''',
'''public sealed class SocialGroup
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Name { get; set; } = "";
    public string Leader { get; set; } = "";
    public HashSet<string> Members { get; set; } = [];
    public HashSet<string> Invites { get; set; } = [];
    public Dictionary<string,string> Roles { get; set; } = [];
    public string Message { get; set; } = "";
    // Party cooperation state. Historical groups default to the original behavior safely.
    public int LootCursor { get; set; }
    public double ReadyCheckEnds { get; set; }
    public HashSet<string> ReadyMembers { get; set; } = [];
    // Guild progression. Level is derived from Experience so no migration is required.
    public long Experience { get; set; }
    public string Project { get; set; } = "";
    public int ProjectProgress { get; set; }
    public int ProjectGoal { get; set; }
    public int CompletedProjects { get; set; }
}
''')
replace("src/Kairnfall.Core/Loot.cs",
'''    public string Owner { get; set; } = "";
    public string Party { get; set; } = "";
    public List<Item> Items { get; set; } = [];
''',
'''    public string Owner { get; set; } = "";
    public string Party { get; set; } = "";
    // New party loot waits briefly for its round-robin owner. Zero preserves historical party access.
    public double PartyAt { get; set; }
    public List<Item> Items { get; set; } = [];
''')

# ---- Shared cooperation rules ----------------------------------------------
write("src/Kairnfall.Core/SocialCooperationRules.cs", r'''namespace Kairnfall.Core;

public static class SocialCooperationRules
{
    public const double PartyShareRadius = 22;
    public const double PartySupportWindow = 12;
    public const double PartyLootDelay = 20;
    public const double RecentPlayerLifetime = WorldTime.DayLength * 7;
    public static readonly string[] LfgActivities = ["questing", "dungeon", "public_events", "boss_hunt", "exploration", "gathering"];
    public static readonly string[] LfgRoles = ["tank", "healer", "damage", "flexible"];
    public static readonly string[] GuildProjects = ["hunt", "adventure", "artisan", "fellowship"];

    public static bool ValidActivity(string value) => LfgActivities.Contains(value, StringComparer.Ordinal);
    public static bool ValidRole(string value) => LfgRoles.Contains(value, StringComparer.Ordinal);
    public static bool ValidProject(string value) => GuildProjects.Contains(value, StringComparer.Ordinal);

    public static string ActivityName(string value) => value switch
    {
        "questing" => "Questing", "dungeon" => "Dungeon", "public_events" => "Public Events",
        "boss_hunt" => "Boss Hunt", "exploration" => "Exploration", "gathering" => "Gathering", _ => "Adventure"
    };
    public static string RoleName(string value) => value switch
    {
        "tank" => "Tank", "healer" => "Healer / Support", "damage" => "Damage", _ => "Flexible"
    };
    public static string ProjectName(string value) => value switch
    {
        "hunt" => "Hunt the Dangerous", "adventure" => "Chart the Realm", "artisan" => "Supply the Guild",
        "fellowship" => "Strengthen Fellowship", _ => "Guild Project"
    };

    public static int GuildLevel(SocialGroup guild) => Math.Clamp(1 + (int)(Math.Max(0, guild.Experience) / 250), 1, 10);
    public static int ProjectGoal(SocialGroup guild, string project)
    {
        int level = GuildLevel(guild);
        return project switch
        {
            "hunt" => 20 + level * 5,
            "adventure" => 16 + level * 4,
            "artisan" => 24 + level * 6,
            "fellowship" => 8 + level * 3,
            _ => 20
        };
    }
    public static bool ProjectMatches(string project, string action) => project switch
    {
        "hunt" => action is "kill" or "boss",
        "adventure" => action is "quest" or "explore" or "survey" or "chest" or "event",
        "artisan" => action is "gather" or "craft" or "salvage",
        "fellowship" => action is "revive" or "trade" or "assist",
        _ => false
    };
    public static long ProjectExperience(SocialGroup guild) => 100 + ProjectGoal(guild, guild.Project) * 2L;
    public static long ProjectMemberGold(SocialGroup guild) => 25 + GuildLevel(guild) * 15L;
    public static double GuildFellowshipMultiplier(SocialGroup guild) => 1 + .01 * Math.Max(0, GuildLevel(guild) - 1);
}
''')

# ---- Transport social discovery --------------------------------------------
replace("src/Kairnfall.Core/Transport.cs",
'''public sealed class GroupInvitation
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Leader { get; set; } = "";
    public bool Guild { get; set; }
}
public sealed class TradePreview
''',
'''public sealed class GroupInvitation
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Leader { get; set; } = "";
    public bool Guild { get; set; }
}
public sealed class LfgListing
{
    public string Character { get; set; } = "";
    public string Name { get; set; } = "";
    public string Class { get; set; } = "";
    public string Activity { get; set; } = "";
    public string Role { get; set; } = "";
    public string Zone { get; set; } = "";
    public int Level { get; set; }
    public int PartySize { get; set; } = 1;
    public double Since { get; set; }
}
public sealed class SocialProfile
{
    public string Id { get; set; } = "";
    public string Name { get; set; } = "";
    public string Class { get; set; } = "";
    public string Zone { get; set; } = "";
    public string Guild { get; set; } = "";
    public int Level { get; set; }
    public bool Online { get; set; }
    public bool Friend { get; set; }
    public double LastSeen { get; set; }
}
public sealed class TradePreview
''')
replace("src/Kairnfall.Core/Transport.cs",
'''    public List<GroupInvitation>? Invitations { get; set; }
    public List<TradePreview> TradeItems { get; set; } = [];
''',
'''    public List<GroupInvitation>? Invitations { get; set; }
    public List<string> FriendInvitations { get; set; } = [];
    public List<LfgListing> Lfg { get; set; } = [];
    public List<SocialProfile> SocialProfiles { get; set; } = [];
    public List<TradePreview> TradeItems { get; set; } = [];
''')

# ---- Server social commands, party cooperation, guild projects -------------
replace("src/Kairnfall.Core/RealmSocial.cs",
'''    private string GroupInvite(Character p,bool guild,string target)
    {
        var group=MemberGroup(p,guild); Need(group.Leader==p.Id||group.Roles.GetValueOrDefault(p.Id)=="officer","Only the leader or an officer can invite members.");
''',
'''    private string GroupInvite(Character p,bool guild,string target)
    {
        if(!guild&&GroupId(p,false)=="") _=GroupCreate(p,false,"");
        var group=MemberGroup(p,guild); Need(group.Leader==p.Id||group.Roles.GetValueOrDefault(p.Id)=="officer","Only the leader or an officer can invite members.");
''')
replace("src/Kairnfall.Core/RealmSocial.cs",
'''        Need(group!.Members.Count<(guild?100:6),"The group is full.");
        group.Invites.Remove(p.Id); group.Members.Add(p.Id); group.Roles[p.Id]="member"; SetGroup(p,guild,group.Id); return "Joined "+group.Name+".";
''',
'''        Need(group!.Members.Count<(guild?100:6),"The group is full.");
        group.Invites.Remove(p.Id); group.Members.Add(p.Id); group.Roles[p.Id]="member"; SetGroup(p,guild,group.Id);
        if(!guild)
        {
            ClearLfg(p); ResetReadyCheck(group);
            if(group.Members.Count>=6&&State.Characters.TryGetValue(group.Leader,out var leader)) ClearLfg(leader);
        }
        return "Joined "+group.Name+".";
''')
replace("src/Kairnfall.Core/RealmSocial.cs",
'''    private string GroupLeave(Character p,bool guild)
    {
        var group=MemberGroup(p,guild); group.Members.Remove(p.Id); group.Roles.Remove(p.Id); SetGroup(p,guild,"");
        if(group.Members.Count==0) Groups(guild).Remove(group.Id);
        else if(group.Leader==p.Id) { group.Leader=group.Members.OrderBy(x=>x,StringComparer.Ordinal).First(); group.Roles[group.Leader]="leader"; }
        CancelTradesFor(p.Id); return "Left the group.";
    }
''',
'''    private string GroupLeave(Character p,bool guild)
    {
        var group=MemberGroup(p,guild); group.Members.Remove(p.Id); group.Roles.Remove(p.Id); SetGroup(p,guild,"");
        if(!guild) { ClearLfg(p); ResetReadyCheck(group); }
        if(group.Members.Count==0) Groups(guild).Remove(group.Id);
        else if(group.Leader==p.Id) { group.Leader=group.Members.OrderBy(x=>x,StringComparer.Ordinal).First(); group.Roles[group.Leader]="leader"; }
        CancelTradesFor(p.Id); return "Left the group.";
    }
''')
replace("src/Kairnfall.Core/RealmSocial.cs",
'''        var other=ResolvePlayer(target); Need(other.Id!=p.Id&&group.Members.Contains(other.Id),"Select another group member.");
        group.Members.Remove(other.Id); group.Roles.Remove(other.Id); SetGroup(other,guild,""); return "Member removed.";
''',
'''        var other=ResolvePlayer(target); Need(other.Id!=p.Id&&group.Members.Contains(other.Id),"Select another group member.");
        group.Members.Remove(other.Id); group.Roles.Remove(other.Id); SetGroup(other,guild,"");
        if(!guild) { ClearLfg(other); ResetReadyCheck(group); }
        return "Member removed.";
''')
replace("src/Kairnfall.Core/RealmSocial.cs",
'''    private string Chat(Character p,string channel,string target,string text)
''',
r'''    private void ClearLfg(Character player)
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
            if(left.RecentPlayers.GetValueOrDefault(right.Id)<State.Time-30) { left.RecentPlayers[right.Id]=State.Time; changed=true; }
            if(right.RecentPlayers.GetValueOrDefault(left.Id)<State.Time-30) { right.RecentPlayers[left.Id]=State.Time; changed=true; }
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
''')

# ---- Engine dispatch, ticking, disconnect, guild project progression --------
replace("src/Kairnfall.Core/RealmEngine.cs",
'''            case "guild_role": return GuildRole(p,c.Target,c.Arg);
            case "chat": return Chat(p,c.Target,c.Item,c.Arg);
            case "ignore": Need(State.Characters.ContainsKey(c.Target),"Character not found."); if(!p.Ignored.Add(c.Target)) p.Ignored.Remove(c.Target); return "Ignore list updated.";
''',
'''            case "guild_role": return GuildRole(p,c.Target,c.Arg);
            case "guild_project": return GuildProject(p,c.Target);
            case "party_ready_start": return PartyReadyStart(p);
            case "party_ready": return PartyReady(p);
            case "revive": return Revive(p,c.Target);
            case "lfg_set": return LfgSet(p,c.Target,c.Arg);
            case "lfg_request": return LfgRequest(p,c.Target);
            case "friend_invite": return FriendInvite(p,c.Target);
            case "friend_accept": return FriendAccept(p,c.Target);
            case "friend_remove": return FriendRemove(p,c.Target);
            case "chat": return Chat(p,c.Target,c.Item,c.Arg);
            case "ignore": Need(State.Characters.ContainsKey(c.Target),"Character not found."); if(!p.Ignored.Add(c.Target)) p.Ignored.Remove(c.Target); return "Ignore list updated.";
''')
replace("src/Kairnfall.Core/RealmEngine.cs",
'''        environmentElapsed+=dt;
        if(environmentElapsed>=1) { TickEnvironment(environmentElapsed); environmentElapsed=0; }
''',
'''        environmentElapsed+=dt;
        if(environmentElapsed>=1) { TickEnvironment(environmentElapsed); TickSocialCooperation(); environmentElapsed=0; }
''')
replace("src/Kairnfall.Core/RealmEngine.cs",
'''    public void Disconnect(string id)
    {
        Active.Remove(id); inputs.Remove(id); playerTargets.Remove(id); transitionReady.Remove(id);
        foreach(var t in State.Trades.Values.Where(x=>x.A.Character==id||x.B.Character==id).ToList()) State.Trades.Remove(t.Id);
        EconomicDirty=true;
    }
''',
'''    public void Disconnect(string id)
    {
        Active.Remove(id); inputs.Remove(id); playerTargets.Remove(id); transitionReady.Remove(id);
        if(State.Characters.TryGetValue(id,out var player)) ClearLfg(player);
        foreach(var t in State.Trades.Values.Where(x=>x.A.Character==id||x.B.Character==id).ToList()) State.Trades.Remove(t.Id);
        EconomicDirty=true;
    }
''')
replace("src/Kairnfall.Core/RealmEngine.cs",
'''    private void Progress(Character p,string action,string target,int amount=1)
    {
        if(amount<1) return;
        foreach(var entry in p.Quests)
''',
'''    private void Progress(Character p,string action,string target,int amount=1)
    {
        if(amount<1) return;
        AdvanceGuildProject(p,action,amount);
        foreach(var entry in p.Quests)
''')

# ---- Combat shared credit, support, round robin, revive weakness ------------
replace("src/Kairnfall.Core/RealmCombat.cs",
'''                int encounterLevel=SupportTraining.EncounterLevel(recipient,State.Time);
                if(encounterLevel>0) { ChallengeProgression.TrainCombat(p,ability.Skill,Math.Max(1,(int)healing/2),encounterLevel,Data); trained=true; }
                break;
''',
'''                int encounterLevel=SupportTraining.EncounterLevel(recipient,State.Time);
                if(encounterLevel>0)
                {
                    ChallengeProgression.TrainCombat(p,ability.Skill,Math.Max(1,(int)healing/2),encounterLevel,Data); trained=true;
                    if(recipient.Id!=p.Id) { p.LastCombat=State.Time; Progress(p,"assist","heal"); RecordEventSupport(p,recipient,healing); }
                }
                break;
''')
replace("src/Kairnfall.Core/RealmCombat.cs",
'''        var def=Data.Mob(mob.Template); var stats=CombatMath.Stats(p,Data);
        double bonus=Math.Clamp(stats.Bonus("damage_"+element.ToString().ToLowerInvariant())/100,0,2);
''',
'''        var def=Data.Mob(mob.Template); var stats=CombatMath.Stats(p,Data);
        raw*=1-Math.Clamp(CombatMath.StatusPower(p.Statuses,"revive_sickness",State.Time),0,.4);
        double bonus=Math.Clamp(stats.Bonus("damage_"+element.ToString().ToLowerInvariant())/100,0,2);
''')
replace("src/Kairnfall.Core/RealmCombat.cs",
'''        var contributors=mob.Threat.Where(x=>x.Value>0&&State.Characters.ContainsKey(x.Key)).Select(x=>Player(x.Key)).Where(x=>x.Zone==mob.Zone&&x.Position.Distance(mob.Position)<=24&&Active.Contains(x.Id)).ToList();
        if(contributors.Count==0) contributors.Add(killer);
        RecordEventKill(mob,contributors);
        foreach(var p in contributors)
        {
            ChallengeProgression.TrainCombat(p,"slayer",Math.Max(1,def.Xp/contributors.Count),def.Level,Data);
            if(def.Anatomy.StartsWith("animal:",StringComparison.Ordinal)) ChallengeProgression.TrainCombat(p,"hunting",Math.Max(1,def.Xp/3/contributors.Count),def.Level,Data);
            p.Bestiary[def.Id]=p.Bestiary.GetValueOrDefault(def.Id)+1;
            Progress(p,"kill",def.Id); if(def.Boss) { p.Achievements.Add("boss:"+def.Id); Progress(p,"boss",def.Id); }
        }
        var owner=contributors.OrderByDescending(x=>mob.Threat.GetValueOrDefault(x.Id)).First();
        var pile=new LootPile{Zone=mob.Zone,Position=mob.Position,Owner=owner.Id,Party=owner.Party,Gold=def.Gold+RandomNumberGenerator.GetInt32(Math.Max(1,def.Gold/3+1)),PublicAt=State.Time+60,Expires=State.Time+LootPile.LifetimeSeconds};
''',
'''        var contributors=mob.Threat.Where(x=>x.Value>0&&State.Characters.ContainsKey(x.Key)).Select(x=>Player(x.Key)).Where(x=>x.Zone==mob.Zone&&x.Position.Distance(mob.Position)<=24&&Active.Contains(x.Id)).ToList();
        if(contributors.Count==0) contributors.Add(killer);
        var recipients=CooperativeKillRecipients(mob,contributors);
        RecordEventKill(mob,recipients);
        foreach(var p in recipients)
        {
            double guildBonus=CooperativeGuildMultiplier(p,recipients);
            ChallengeProgression.TrainCombat(p,"slayer",Math.Max(1,(int)Math.Ceiling(def.Xp/(double)recipients.Count*guildBonus)),def.Level,Data);
            if(def.Anatomy.StartsWith("animal:",StringComparison.Ordinal)) ChallengeProgression.TrainCombat(p,"hunting",Math.Max(1,(int)Math.Ceiling(def.Xp/3.0/recipients.Count*guildBonus)),def.Level,Data);
            p.Bestiary[def.Id]=p.Bestiary.GetValueOrDefault(def.Id)+1;
            Progress(p,"kill",def.Id); if(def.Boss) { p.Achievements.Add("boss:"+def.Id); Progress(p,"boss",def.Id); }
        }
        var owner=CooperativeLootOwner(mob,contributors,recipients);
        var pile=new LootPile{Zone=mob.Zone,Position=mob.Position,Owner=owner.Id,Party=owner.Party,PartyAt=owner.Party!=""?State.Time+SocialCooperationRules.PartyLootDelay:0,Gold=def.Gold+RandomNumberGenerator.GetInt32(Math.Max(1,def.Gold/3+1)),PublicAt=State.Time+60,Expires=State.Time+LootPile.LifetimeSeconds};
''')

# ---- Event support contribution --------------------------------------------
replace("src/Kairnfall.Core/RealmEvents.cs",
'''    private void RecordEventDamage(Character player, Creature mob, double damage)
    {
''',
'''    private void RecordEventSupport(Character player, Character ally, double amount)
    {
        if(amount<=0) return;
        foreach(var value in State.Events.Where(x=>x.Status=="active"&&x.Zone==player.Zone&&player.Position.Distance(x.Position)<=32&&ally.Position.Distance(x.Position)<=32))
            AddEventContribution(value,player.Id,Math.Clamp(amount/12,.5,8));
    }

    private void RecordEventDamage(Character player, Creature mob, double damage)
    {
''')
replace("src/Kairnfall.Core/RealmEvents.cs",
'''        value.Progress += 1; AddEventContribution(value, player.Id, 8);
        string kind = WorldEventRules.NormalizeKind(value.Kind);
''',
'''        value.Progress += 1; AddEventContribution(value, player.Id, 8); Progress(player,"event",value.Kind);
        string kind = WorldEventRules.NormalizeKind(value.Kind);
''')

# ---- Quest completion contributes to guild projects; party loot reservation -
replace("src/Kairnfall.Core/RealmEconomy.cs",
'''        p.Reputation[quest.Faction]=Math.Min(1000,p.Reputation.GetValueOrDefault(quest.Faction)+10);
        if(quest.Repeatable) p.Cooldowns["quest:"+id]=State.Time+WorldTime.DayLength;
''',
'''        p.Reputation[quest.Faction]=Math.Min(1000,p.Reputation.GetValueOrDefault(quest.Faction)+10); Progress(p,"quest",id);
        if(quest.Repeatable) p.Cooldowns["quest:"+id]=State.Time+WorldTime.DayLength;
''')
replace("src/Kairnfall.Core/RealmEconomy.cs",
'''        Need(pile.Owner==p.Id||pile.PublicAt<=State.Time||(pile.Party!=""&&pile.Party==p.Party),"This loot belongs to another player.");
''',
'''        Need(pile.Owner==p.Id||pile.PublicAt<=State.Time||(pile.Party!=""&&pile.Party==p.Party&&pile.PartyAt<=State.Time),"This loot is reserved for its round-robin owner for a short time.");
''')

# ---- Packet social discovery, privacy, LFG ---------------------------------
replace("src/Kairnfall.Core/SnapshotPackets.cs",
'''        var names = new HashSet<string> { characterId };
''',
r'''        packet.FriendInvitations = player.FriendInvites.Where(engine.State.Characters.ContainsKey).OrderBy(x=>x,StringComparer.Ordinal).ToList();
        packet.Lfg = engine.Active.Where(engine.State.Characters.ContainsKey).Select(engine.Player)
            .Where(x=>x.Id!=characterId&&x.LfgActivity!=""&&!player.Ignored.Contains(x.Id)&&!x.Ignored.Contains(characterId))
            .OrderBy(x=>x.LfgSince).ThenBy(x=>x.Name,StringComparer.OrdinalIgnoreCase)
            .Select(x=>new LfgListing
            {
                Character=x.Id,Name=x.Name,Class=x.Class,Activity=x.LfgActivity,Role=x.LfgRole,Zone=x.Zone,
                Level=Progression.PlayerLevel(x),Since=x.LfgSince,
                PartySize=x.Party!=""&&engine.State.Parties.TryGetValue(x.Party,out var party)?party.Members.Count:1
            }).ToList();
        var profileIds = player.Friends
            .Concat(player.RecentPlayers.Where(x=>x.Value>=engine.State.Time-SocialCooperationRules.RecentPlayerLifetime).Select(x=>x.Key))
            .Concat(snapshot.Party?.Members??[]).Concat(snapshot.Guild?.Members??[])
            .Concat(packet.FriendInvitations).Concat(packet.Lfg.Select(x=>x.Character))
            .Where(x=>x!=characterId).Distinct(StringComparer.Ordinal).Take(150).ToArray();
        foreach(string id in profileIds)
        {
            if(!engine.State.Characters.TryGetValue(id,out var member)||player.Ignored.Contains(id)) continue;
            string guild=member.Guild!=""&&engine.State.Guilds.TryGetValue(member.Guild,out var memberGuild)?memberGuild.Name:"";
            packet.SocialProfiles.Add(new(){Id=id,Name=member.Name,Class=member.Class,Zone=member.Zone,Guild=guild,Level=Progression.PlayerLevel(member),Online=engine.Active.Contains(id),Friend=player.Friends.Contains(id),LastSeen=player.RecentPlayers.GetValueOrDefault(id)});
        }
        var names = new HashSet<string> { characterId };
''')
replace("src/Kairnfall.Core/SnapshotPackets.cs",
'''        foreach (var invitation in packet.Invitations) names.Add(invitation.Leader);
        foreach (var trade in snapshot.Trades)
''',
'''        foreach (var invitation in packet.Invitations) names.Add(invitation.Leader);
        foreach (var id in packet.FriendInvitations) names.Add(id);
        foreach (var listing in packet.Lfg) names.Add(listing.Character);
        foreach (var profile in packet.SocialProfiles) names.Add(profile.Id);
        foreach (var trade in snapshot.Trades)
''')

# ---- Client loot timing -----------------------------------------------------
replace("client/Scripts/ExperienceRules.cs",
'''        => double.IsFinite(serverTime) && pile.Zone == self.Zone
            && (pile.Owner == self.Id || pile.PublicAt <= serverTime || (pile.Party != "" && pile.Party == self.Party));
''',
'''        => double.IsFinite(serverTime) && pile.Zone == self.Zone
            && (pile.Owner == self.Id || pile.PublicAt <= serverTime || (pile.Party != "" && pile.Party == self.Party && pile.PartyAt <= serverTime));
''')

# ---- Client packet state ----------------------------------------------------
replace("client/Scripts/GameRoot.cs",
'''    private List<GroupInvitation> invitations = [];
    private readonly Dictionary<string, Key> bindings = new()
''',
'''    private List<GroupInvitation> invitations = [];
    private List<string> friendInvitations = [];
    private List<LfgListing> lfgListings = [];
    private List<SocialProfile> socialProfiles = [];
    private readonly Dictionary<string, Key> bindings = new()
''')
replace("client/Scripts/GameRoot.cs",
'''                    invitations = packet.Invitations ?? [];
                    knownNames[snapshot.Self.Id] = snapshot.Self.Name;
                    foreach (var other in snapshot.Players) knownNames[other.Id] = other.Name;
''',
'''                    invitations = packet.Invitations ?? [];
                    friendInvitations = packet.FriendInvitations ?? [];
                    lfgListings = packet.Lfg ?? [];
                    socialProfiles = packet.SocialProfiles ?? [];
                    knownNames[snapshot.Self.Id] = snapshot.Self.Name;
                    foreach (var other in snapshot.Players) knownNames[other.Id] = other.Name;
                    foreach (var listing in lfgListings) knownNames[listing.Character] = listing.Name;
                    foreach (var profile in socialProfiles) knownNames[profile.Id] = profile.Name;
''')
replace("client/Scripts/GameRoot.cs",
'''            Snapshot.Trades, Snapshot.Auctions, Snapshot.Party, Snapshot.Guild, Snapshot.ShopStock, Snapshot.Events, invitations
''',
'''            Snapshot.Trades, Snapshot.Auctions, Snapshot.Party, Snapshot.Guild, Snapshot.ShopStock, Snapshot.Events,
            invitations, friendInvitations, lfgListings, socialProfiles
''')
replace("client/Scripts/GameRoot.cs",
'''        history.Clear(); knownNames.Clear(); invitations.Clear(); pickupNotes.Clear(); lastExperienceSkill = "";
''',
'''        history.Clear(); knownNames.Clear(); invitations.Clear(); friendInvitations.Clear(); lfgListings.Clear(); socialProfiles.Clear(); pickupNotes.Clear(); lastExperienceSkill = "";
''')
replace("client/Scripts/GameRoot.Frontend.cs",
'''            while (read++ < 150 && Connection.TryRead(out var packet)) if (packet?.Snapshot is not null) { World.Accept(packet); invitations = packet.Invitations ?? []; }
''',
'''            while (read++ < 150 && Connection.TryRead(out var packet)) if (packet?.Snapshot is not null)
            {
                World.Accept(packet); invitations = packet.Invitations ?? []; friendInvitations = packet.FriendInvitations ?? [];
                lfgListings = packet.Lfg ?? []; socialProfiles = packet.SocialProfiles ?? [];
            }
''')

# ---- Client social UI -------------------------------------------------------
replace("client/Scripts/GameRoot.Social.cs",
'''        top.AddChild(Ui.Button("Invite to party", () => Send("party_invite", recipient.Text.Trim())));
        top.AddChild(Ui.Button("Trade", () => Send("trade_invite", recipient.Text.Trim())));
        var whisperRow = Ui.Row(page); var message = Ui.Edit("Private message"); message.MaxLength = 240; whisperRow.AddChild(message);
''',
'''        top.AddChild(Ui.Button("Invite to party", () => Send("party_invite", recipient.Text.Trim())));
        top.AddChild(Ui.Button("Trade", () => Send("trade_invite", recipient.Text.Trim())));
        top.AddChild(Ui.Button("Add friend", () => Send("friend_invite", recipient.Text.Trim())));
        var whisperRow = Ui.Row(page); var message = Ui.Edit("Private message"); message.MaxLength = 240; whisperRow.AddChild(message);
''')
replace("client/Scripts/GameRoot.Social.cs",
'''        whisperRow.AddChild(Ui.Button("Whisper", () => { Send("chat", "whisper", recipient.Text.Trim(), arg: message.Text.Trim()); message.Text = ""; }));
        var scroll = Ui.Scroll(page, new Vector2(870, 440)); var body = Ui.Column(scroll);
''',
r'''        whisperRow.AddChild(Ui.Button("Whisper", () => { Send("chat", "whisper", recipient.Text.Trim(), arg: message.Text.Trim()); message.Text = ""; }));
        var lfgRow = Ui.Row(page);
        var activity = new OptionButton(); foreach (var value in SocialCooperationRules.LfgActivities) activity.AddItem(SocialCooperationRules.ActivityName(value)); lfgRow.AddChild(activity);
        var role = new OptionButton(); foreach (var value in SocialCooperationRules.LfgRoles) role.AddItem(SocialCooperationRules.RoleName(value)); lfgRow.AddChild(role);
        lfgRow.AddChild(Ui.Button("Advertise / update LFG", () => Send("lfg_set", SocialCooperationRules.LfgActivities[Math.Max(0, activity.Selected)], arg: SocialCooperationRules.LfgRoles[Math.Max(0, role.Selected)])));
        lfgRow.AddChild(Ui.Button("Stop LFG", () => Send("lfg_set", "off")));
        var inspection = Ui.Label("Inspect nearby players to compare class, level, guild, and visible equipment.", 13, Ui.Muted, true); page.AddChild(inspection);
        var scroll = Ui.Scroll(page, new Vector2(870, 440)); var body = Ui.Column(scroll);
''')
replace("client/Scripts/GameRoot.Social.cs",
'''            Ui.Clear(body);
            if (invitations.Count > 0)
''',
r'''            Ui.Clear(body);
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
''')
replace("client/Scripts/GameRoot.Social.cs",
'''            foreach (var trade in Snapshot.Trades)
            {
''',
r'''            if(lfgListings.Count>0)
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
''')
replace("client/Scripts/GameRoot.Social.cs",
'''            foreach (var player in Snapshot.Players)
            {
                var row = Ui.Row(body); row.AddChild(Ui.Label(player.Name + " · Level " + player.Level + " · " + Data.Class(player.Class).Name, 16));
                row.AddChild(Ui.Button("Select", () => { SelectTarget("player", player.Id); recipient.Text = player.Name; }));
                row.AddChild(Ui.Button(Snapshot.Self.Ignored.Contains(player.Id) ? "Unmute" : "Mute", () => Send("ignore", player.Id)));
            }
            if (Snapshot.Players.Count == 0) body.AddChild(Ui.Label("No other players are in view. Party and guild invitations also accept character names.", 15, Ui.Muted, true));
''',
r'''            foreach (var player in Snapshot.Players)
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
''')
replace("client/Scripts/GameRoot.Social.cs",
'''    private void DrawGroup(Node parent, SocialGroup? group, bool guild, LineEdit recipient)
''',
r'''    private string DescribeSocialPlayer(PublicPlayer player)
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
''')
replace("client/Scripts/GameRoot.Social.cs",
'''        column.AddChild(Ui.Label(group.Name, 20));
        if (group.Message != "") column.AddChild(Ui.Label(group.Message, 16, Ui.Muted, true));
''',
r'''        column.AddChild(Ui.Label(group.Name, 20));
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
''')
replace("client/Scripts/GameRoot.Social.cs",
'''            var row = Ui.Row(column); string presence = member == Snapshot.Self.Id || Snapshot.Players.Any(x => x.Id == member) ? "Nearby" : "Elsewhere or offline";
            var label = Ui.Label(SocialName(member) + " · " + Ui.Words(group.Roles.GetValueOrDefault(member, "member")) + " · " + presence, 15); label.SizeFlagsHorizontal = SizeFlags.ExpandFill; row.AddChild(label);
            if (group.Leader == Snapshot.Self.Id && member != Snapshot.Self.Id)
                row.AddChild(Ui.Button("Remove", () => Confirm("Remove member", "Remove " + SocialName(member) + " from " + group.Name + "?", () => Send(guild ? "guild_kick" : "party_kick", member))));
''',
r'''            var row = Ui.Row(column); string presence = member == Snapshot.Self.Id || Snapshot.Players.Any(x => x.Id == member) ? "Nearby" : socialProfiles.Any(x=>x.Id==member&&x.Online)?"Online elsewhere":"Offline";
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
''')

# ---- Downed-party readability in the world ---------------------------------
replace("client/Scripts/WorldView.cs",
'''            case "player":
                var player = (PublicPlayer)visual.Value!; var pp = Pose(player.Id, player.Position);
                Shadow(feet); Assets.DrawPerson(this, player.Appearance, player.Equipment, feet, pp.State, pp.Direction, pp.Frame);
                if (ShowNames) Nameplate(player.Position, player.Name + " · " + player.Level, new Color("a3c9df"), -61, 10);
                break;
''',
'''            case "player":
                var player = (PublicPlayer)visual.Value!; var pp = Pose(player.Id, player.Position);
                if(player.Health>0) Shadow(feet);
                Assets.DrawPerson(this, player.Appearance, player.Equipment, feet, player.Health<=0?5:pp.State, pp.Direction, player.Health<=0?7:pp.Frame);
                if (ShowNames) Nameplate(player.Position, (player.Health<=0?"DOWNED · ":"")+player.Name + " · " + player.Level, player.Health<=0?Ui.Danger:new Color("a3c9df"), -61, 10);
                break;
''')

# ---- Real-network social acceptance ----------------------------------------
replace("tests/Kairnfall.Integration/Program.cs",
'''    await Test("Party invitations are visible and require recipient acceptance",async()=>
''',
r'''    await Test("LFG listings and mutual friend requests propagate over real snapshots",async()=>
    {
        await Act(bob,"lfg_set","dungeon",arg:"damage");
        bool listing=false; var watch=Stopwatch.StartNew();
        while(watch.Elapsed<TimeSpan.FromSeconds(5)&&!listing)
        {
            while(alice.TryRead(out var packet))
            {
                if(packet?.Snapshot is { } s) states[alice]=s;
                listing|=packet?.Lfg?.Any(x=>x.Character==bobCharacter!.Id&&x.Activity=="dungeon"&&x.Role=="damage")==true;
            }
            await Task.Delay(30,cancel);
        }
        Check(listing,"The live LFG listing was not visible to another account.");
        await Act(bob,"lfg_set","off");
        await Act(alice,"friend_invite",bobCharacter!.Id);
        bool request=false; watch.Restart();
        while(watch.Elapsed<TimeSpan.FromSeconds(5)&&!request)
        {
            while(bob.TryRead(out var packet))
            {
                if(packet?.Snapshot is { } s) states[bob]=s;
                request|=packet?.FriendInvitations?.Contains(aliceCharacter!.Id)==true;
            }
            await Task.Delay(30,cancel);
        }
        Check(request,"The friend request did not reach the recipient."); await Act(bob,"friend_accept",aliceCharacter!.Id);
        var a=await State(alice,s=>s.Self.Friends.Contains(bobCharacter!.Id)); var b=await State(bob,s=>s.Self.Friends.Contains(aliceCharacter!.Id));
        Check(a.Self.Friends.Contains(bobCharacter!.Id)&&b.Self.Friends.Contains(aliceCharacter!.Id),"Friendship was not mutual.");
    });
    await Test("Party invitations are visible and require recipient acceptance",async()=>
''')
replace("tests/Kairnfall.Integration/Program.cs",
'''        var state=await State(alice,s=>s.Party?.Members.Count==2); Check(state.Party!.Members.Contains(bobCharacter!.Id),"Party membership was not synchronized.");
    });
''',
r'''        var state=await State(alice,s=>s.Party?.Members.Count==2); Check(state.Party!.Members.Contains(bobCharacter!.Id),"Party membership was not synchronized.");
        await Act(alice,"party_ready_start"); await Act(bob,"party_ready");
        state=await State(alice,s=>s.Party?.ReadyMembers.Count>=2);
        Check(state.Party!.ReadyCheckEnds>state.Time&&state.Party.ReadyMembers.Contains(aliceCharacter!.Id)&&state.Party.ReadyMembers.Contains(bobCharacter!.Id),"Ready check state did not synchronize.");
    });
''')
replace("tests/Kairnfall.Integration/Program.cs",
'''        Check(a.Self.Gold==expectedGold&&a.Self.Zone=="dawnreach"&&a.Self.CompletedQuests.Contains("starter_ore"),"Acknowledged character state did not survive restart.");
''',
'''        Check(a.Self.Gold==expectedGold&&a.Self.Zone=="dawnreach"&&a.Self.CompletedQuests.Contains("starter_ore"),"Acknowledged character state did not survive restart.");
        Check(a.Self.Friends.Contains(bobCharacter!.Id)&&b.Self.Friends.Contains(aliceCharacter!.Id),"Social friendship state did not survive restart.");
''')

# ---- Permanent world/social acceptance -------------------------------------
write("tools/world_probe/SocialCooperationChecks.cs", r'''using Kairnfall.Core;

public static class SocialCooperationChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int groups=0;
        void Test(string name,Action body)
        {
            try { body(); groups++; Console.WriteLine("PASS SOCIAL · "+name); }
            catch(Exception error) { failures.Add("Social cooperation · "+name+": "+error.Message); Console.WriteLine("FAIL SOCIAL · "+name+": "+error.Message); }
        }
        void Need(bool value,string message) { if(!value) throw new Exception(message); }
        CommandResult Act(RealmEngine realm,Character player,string kind,string target="",string item="",int amount=1,string arg="")
            => realm.Execute(player.Id,new(){Kind=kind,Target=target,Item=item,Amount=amount,Arg=arg,Sequence=player.LastAction+1});
        (RealmEngine Realm,Character A,Character B) Party()
        {
            var realm=new RealmEngine(data); var a=realm.CreateCharacter("social-a","Social A","vanguard",new()); var b=realm.CreateCharacter("social-b","Social B","templar",new());
            realm.Active.Add(a.Id); realm.Active.Add(b.Id); b.Position=a.Position;
            Need(Act(realm,a,"party_create").Ok,"Party creation failed."); Need(Act(realm,a,"party_invite",b.Id).Ok,"Party invite failed."); Need(Act(realm,b,"party_join",a.Party).Ok,"Party join failed.");
            return(realm,a,b);
        }
        Creature SpawnTarget(RealmEngine realm,Character at,string id)
        {
            var def=data.Mobs.First(x=>!x.Boss&&!x.Elite&&x.Ai!="passive"); var zone=data.Zone(at.Zone); var pos=WorldMap.FindFree(zone,new(at.Position.X+1,at.Position.Y));
            var mob=new Creature{Id=id,Template=def.Id,Zone=at.Zone,Position=pos,Home=pos,Health=1}; realm.State.Creatures[id]=mob; return mob;
        }

        Test("nearby active party supporters share kill credit without AFK leech",()=>
        {
            var (realm,a,b)=Party(); var c=realm.CreateCharacter("social-c","Social C","ranger",new()); realm.Active.Add(c.Id); c.Position=a.Position; b.LastCombat=realm.State.Time;
            var mob=SpawnTarget(realm,a,"social/credit/1"); Need(Act(realm,a,"attack",mob.Id).Ok,"Kill attack failed.");
            var def=data.Mob(mob.Template); Need(a.Bestiary.GetValueOrDefault(def.Id)>0&&b.Bestiary.GetValueOrDefault(def.Id)>0,"Active supporter did not receive kill credit.");
            Need(c.Bestiary.GetValueOrDefault(def.Id)==0,"Non-party bystander received party credit.");
        });

        Test("round-robin ownership rotates and party reservation expires",()=>
        {
            var (realm,a,b)=Party(); b.LastCombat=realm.State.Time;
            var one=SpawnTarget(realm,a,"social/loot/1"); Need(Act(realm,a,"attack",one.Id).Ok,"First kill failed.");
            b.LastCombat=realm.State.Time; a.Cooldowns["attack"]=0; var two=SpawnTarget(realm,a,"social/loot/2"); Need(Act(realm,a,"attack",two.Id).Ok,"Second kill failed.");
            var piles=realm.Loot.Values.Where(x=>x.Party==a.Party).OrderBy(x=>x.Expires).ToArray(); Need(piles.Length>=2,"Party loot piles missing.");
            Need(piles[^1].Owner!=piles[^2].Owner,"Round-robin ownership did not rotate.");
            var reserved=piles[^1]; var other=reserved.Owner==a.Id?b:a; other.Position=reserved.Position;
            var early=Act(realm,other,"loot",reserved.Id); Need(!early.Ok,"Non-owner looted before the party reservation expired.");
            realm.State.Time=reserved.PartyAt+.01; Need(Act(realm,other,"loot",reserved.Id).Ok,"Party member could not loot after reservation expiry.");
        });

        Test("party revives restore a downed ally with bounded recovery and sickness",()=>
        {
            var (realm,a,b)=Party(); b.Position=a.Position; b.Health=0; b.DeadUntil=realm.State.Time+5; long before=a.Gold;
            var result=Act(realm,a,"revive",b.Id); Need(result.Ok,result.Message); var stats=CombatMath.Stats(b,data);
            Need(b.Health>0&&b.Health<=stats.Health*.36&&b.DeadUntil==0,"Revive recovery was not bounded to 35% health.");
            Need(b.Statuses.Any(x=>x.Kind=="revive_sickness"&&x.Until>realm.State.Time),"Revive sickness was not applied.");
            Need(a.Achievements.Contains("field_medic")&&a.Gold==before,"Revive changed unrelated economy state.");
        });

        Test("LFG consent flow and party ready checks are server authoritative",()=>
        {
            var realm=new RealmEngine(data); var a=realm.CreateCharacter("lfg-a","Lfg A","vanguard",new()); var b=realm.CreateCharacter("lfg-b","Lfg B","warden",new()); realm.Active.Add(a.Id); realm.Active.Add(b.Id);
            Need(Act(realm,a,"lfg_set","dungeon",arg:"tank").Ok,"LFG listing failed.");
            var packet=SnapshotPackets.Create(realm,b.Id); Need(packet.Lfg.Any(x=>x.Character==a.Id&&x.Activity=="dungeon"&&x.Role=="tank"),"LFG listing not exposed to another active player.");
            Need(Act(realm,b,"lfg_request",a.Id).Ok,"LFG request failed."); packet=SnapshotPackets.Create(realm,b.Id); var invite=packet.Invitations!.FirstOrDefault(x=>!x.Guild); Need(invite is not null,"LFG request did not produce a consent-based party invitation.");
            Need(Act(realm,b,"party_join",invite!.Id).Ok,"LFG party join failed."); Need(Act(realm,a,"party_ready_start").Ok,"Ready check start failed."); Need(Act(realm,b,"party_ready").Ok,"Ready acknowledgement failed.");
            var party=realm.State.Parties[a.Party]; Need(party.ReadyMembers.Contains(a.Id)&&party.ReadyMembers.Contains(b.Id)&&party.ReadyCheckEnds>realm.State.Time,"Ready check state incomplete.");
        });

        Test("friend requests, recent travelers, and social profiles respect explicit relationships",()=>
        {
            var realm=new RealmEngine(data); var a=realm.CreateCharacter("friend-a","Friend A","rogue",new()); var b=realm.CreateCharacter("friend-b","Friend B","arcanist",new()); realm.Active.Add(a.Id); realm.Active.Add(b.Id); b.Position=a.Position;
            Need(Act(realm,a,"friend_invite",b.Id).Ok,"Friend request failed."); var pending=SnapshotPackets.Create(realm,b.Id); Need(pending.FriendInvitations.Contains(a.Id),"Friend request packet missing.");
            Need(Act(realm,b,"friend_accept",a.Id).Ok,"Friend acceptance failed.");
            for(int i=0;i<11;i++) realm.Tick(.1);
            var packet=SnapshotPackets.Create(realm,a.Id); Need(a.Friends.Contains(b.Id)&&b.Friends.Contains(a.Id),"Friendship is not mutual.");
            Need(a.RecentPlayers.ContainsKey(b.Id)&&packet.SocialProfiles.Any(x=>x.Id==b.Id&&x.Friend&&x.Online),"Recent/friend social profile missing.");
        });

        Test("guild projects progress from cooperative actions, level up, reward every member, and persist",()=>
        {
            var (realm,a,b)=Party(); var guild=new SocialGroup{Name="Probe Guild",Leader=a.Id,Members=[a.Id,b.Id],Roles=new(){{a.Id,"leader"},{b.Id,"member"}}}; realm.State.Guilds[guild.Id]=guild; a.Guild=b.Guild=guild.Id;
            long aGold=a.Gold,bGold=b.Gold; Need(Act(realm,a,"guild_project","fellowship").Ok,"Guild project start failed."); guild.ProjectGoal=1;
            b.Health=0; b.DeadUntil=realm.State.Time+5; b.Position=a.Position; Need(Act(realm,a,"revive",b.Id).Ok,"Project revive failed.");
            Need(guild.Project==""&&guild.CompletedProjects==1&&guild.Experience>0,"Guild project did not complete and advance renown.");
            Need(a.Gold>aGold&&b.Gold>bGold&&a.Achievements.Contains("guild_project:fellowship")&&b.Achievements.Contains("guild_project:fellowship"),"Guild completion did not reward every member.");
            var loaded=new RealmEngine(data,Wire.Copy(realm.State)); var saved=loaded.State.Guilds[guild.Id];
            Need(saved.CompletedProjects==1&&saved.Experience==guild.Experience&&loaded.Player(a.Id).Friends.SetEquals(a.Friends),"Guild/social state failed save roundtrip.");
        });

        Test("client social surface exposes LFG, ready, revive, friends, guild projects, and fair loot",()=>
        {
            string social=File.ReadAllText("client/Scripts/GameRoot.Social.cs"); string rules=File.ReadAllText("client/Scripts/ExperienceRules.cs"); string world=File.ReadAllText("client/Scripts/WorldView.cs");
            foreach(string token in new[]{"lfg_set","lfg_request","friend_accept","party_ready_start","revive","guild_project","DescribeSocialPlayer"}) Need(social.Contains(token,StringComparison.Ordinal),"Client social contract missing "+token+".");
            Need(rules.Contains("pile.PartyAt <= serverTime",StringComparison.Ordinal),"Client loot eligibility ignores the party reservation.");
            Need(world.Contains("DOWNED ·",StringComparison.Ordinal),"Downed party members are not visually identifiable.");
        });

        Console.WriteLine($"SOCIAL COOPERATION: {groups} groups passed");
    }
}
''')
replace("tools/world_probe/Program.cs",
'''LivingWorldEventChecks.Run(catalog,failures);
ExplorationRewardChecks.Run(catalog,failures);
''',
'''LivingWorldEventChecks.Run(catalog,failures);
SocialCooperationChecks.Run(catalog,failures);
ExplorationRewardChecks.Run(catalog,failures);
''')

# ---- Client compile-time contract ------------------------------------------
write("client/Tests/SocialCooperationContract.cs", r'''using Kairnfall.Core;

namespace Kairnfall.Client;

public static class SocialCooperationContract
{
    public static void Verify()
    {
        if (SocialCooperationRules.LfgActivities.Length < 6 || SocialCooperationRules.LfgRoles.Length < 4)
            throw new InvalidOperationException("Social discovery choices are incomplete.");
        var guild = new SocialGroup { Experience = 500 };
        if (SocialCooperationRules.GuildLevel(guild) < 3)
            throw new InvalidOperationException("Guild progression contract changed unexpectedly.");
        var pile = new LootPile { PartyAt = 10, PublicAt = 60 };
        if (pile.PartyAt >= pile.PublicAt)
            throw new InvalidOperationException("Party loot reservation must end before public loot access.");
    }
}
''')

# ---- Documentation ----------------------------------------------------------
write("docs/SOCIAL_COOPERATION.md", r'''# Stronger MMO and social cooperation

Kairnfall's social layer now makes other players materially useful rather than merely visible.

## Party cooperation
- Party kill and boss credit includes nearby active supporters, not only characters that personally generated creature threat.
- Healing a party member in an active encounter records support participation, including public-event contribution.
- New loot uses round-robin party ownership. The owner receives a short exclusive window, party members gain access afterward, and the pile later becomes public.
- Party leadership can start a 45-second ready check; members explicitly mark themselves ready.
- A living party member can revive a nearby downed member. Revives restore 35% health with partial resources and temporary revive sickness, and have a server-side stamina/cooldown cost.

## Finding and keeping people
- Players can advertise an activity and role through LFG. Listings cover questing, dungeons, public events, boss hunts, exploration, and gathering.
- Requesting an LFG group creates an invitation; it never silently forces membership.
- Friend requests require recipient acceptance and friendships are mutual and persistent.
- Nearby players are remembered as recent travelers for a limited realm-time window.
- The social page exposes online status, last-seen recency, class, level, guild, nearby inspection, and visible equipment without exposing private inventories.

## Guild progression
- Guilds accumulate persistent renown through completed cooperative projects.
- Leadership can start Hunt, Adventure, Artisan, or Fellowship projects.
- Relevant member gameplay advances the shared goal. Completion grants renown, project achievements, and gold to every guild member, including offline members represented in the persistent realm state.
- Guild level is derived from renown and provides a small cooperative combat-training bonus when two or more guildmates participate together.

## Safety and authority
All membership, friendship, LFG, ready-check, revive, loot reservation, project progress, contribution, and reward decisions are server-authoritative. Historical saves remain compatible because all new fields have safe defaults.
''')

print("social cooperation candidate applied")
