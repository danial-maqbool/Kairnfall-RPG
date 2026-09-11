using Kairnfall.Core;

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
