using Kairnfall.Core;

internal static class CombatReadabilityChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check){try{check();passed++;Console.WriteLine("PASS COMBAT READABILITY: "+name);}catch(Exception error){failures.Add("Combat readability · "+name+": "+error.Message);Console.WriteLine("FAIL COMBAT READABILITY: "+name+": "+error.Message);}}
        GameCommand Command(Character player,string kind,string target="",string item="")=>new(){Kind=kind,Target=target,Item=item,Sequence=player.LastAction+1,RequestId=Guid.NewGuid().ToString("N")};

        Test("telegraph countdown and combat labels are deterministic",()=>
        {
            var telegraph=new Telegraph{Skill="interruptible",Resolves=12.5};
            Need(Math.Abs(CombatReadabilityRules.TelegraphRemaining(telegraph,12)-.5)<.0001,"Telegraph remaining time diverged from authoritative resolve time.");
            Need(CombatReadabilityRules.TelegraphUrgency(telegraph,11.5)==0&&CombatReadabilityRules.TelegraphUrgency(telegraph,12.5)==1,"Telegraph urgency is not bounded by authoritative time.");
            Need(CombatReadabilityRules.TelegraphLabel(telegraph).Contains("INTERRUPT",StringComparison.Ordinal),"Interruptible casts lack an explicit cue.");
            Need(CombatReadabilityRules.StatusLabel("stun")=="STUNNED"&&CombatReadabilityRules.IsCrowdControl("root"),"Crowd-control labels are not stable.");
            foreach(var elite in data.Mobs.Where(x=>x.Elite))Need(CombatReadabilityRules.EliteTraitLabel(elite)!="","An elite has no readable trait label: "+elite.Id);
        });

        Test("authoritative ranged attacks delay damage until projectile impact",()=>
        {
            var realm=new RealmEngine(data);var player=realm.CreateCharacter("readability-projectile","Projectile Tester","ranger",new());
            var weapon=Items.Owned(player,player.Equipment["weapon"]);var weaponDef=data.Item(weapon.Template);
            Need(weaponDef.Type is "bow" or "crossbow" or "wand" or "tome","Ranger fixture does not use a delayed projectile weapon.");
            var target=realm.State.Creatures.Values.First(x=>x.Owner==""&&data.Mob(x.Template).Ai!="passive");var zone=data.Zone(target.Zone);
            player.Zone=target.Zone;player.Position=WorldMap.FindFree(zone,new(target.Position.X-Math.Min(2,weaponDef.Range-.2),target.Position.Y));
            if(player.Position.Distance(target.Position)>weaponDef.Range)player.Position=WorldMap.FindFree(zone,new(target.Position.X+1,target.Position.Y));
            target.Health=Math.Max(10000,data.Mob(target.Template).Health);double before=target.Health;
            var result=realm.Execute(player.Id,Command(player,"attack",target.Id));Need(result.Ok,result.Message);
            Need(Math.Abs(target.Health-before)<.0001,"Projectile attack applied damage before its delayed hit resolved.");
            var shot=realm.State.Telegraphs.SingleOrDefault(x=>x.Source==player.Id);
            Need(shot is not null&&shot.Resolves>realm.State.Time&&shot.Resolves-realm.State.Time<=.61,"Projectile impact timing is missing or outside its server bound.");
            for(int i=0;i<8&&realm.State.Telegraphs.Any(x=>x.Id==shot!.Id);i++)realm.Tick(.1);
            Need(!realm.State.Telegraphs.Any(x=>x.Id==shot!.Id)&&target.Health<before,"Projectile telegraph did not resolve into authoritative damage.");
        });

        Test("interrupt abilities cancel pending enemy casts and delay retaliation",()=>
        {
            var ability=data.Abilities.First(x=>x.Kind=="interrupt");var realm=new RealmEngine(data);var player=realm.CreateCharacter("readability-interrupt","Interrupt Tester",ability.Class==""?"vanguard":ability.Class,new());
            player.SkillXp[ability.Skill]=Progression.Threshold(Math.Max(1,ability.Requirement));player.Mana=100000;player.Stamina=100000;
            var target=realm.State.Creatures.Values.First(x=>x.Owner==""&&data.Mob(x.Template).Ai!="passive");var zone=data.Zone(target.Zone);
            player.Zone=target.Zone;player.Position=WorldMap.FindFree(zone,new(target.Position.X+Math.Min(1.5,Math.Max(.5,ability.Range-.2)),target.Position.Y));
            target.Health=100000;target.NextAttack=0;
            var cast=new Telegraph{Zone=target.Zone,Source=target.Id,Position=player.Position,Skill="interruptible",Shape="circle",Radius=2,Resolves=realm.State.Time+1.6};
            realm.State.Telegraphs.Add(cast);
            var result=realm.Execute(player.Id,Command(player,"cast",target.Id,ability.Id));Need(result.Ok,result.Message);
            Need(!realm.State.Telegraphs.Any(x=>x.Source==target.Id),"Successful interrupt left the enemy cast telegraph active.");
            Need(target.NextAttack>=realm.State.Time+1.99,"Successful interrupt did not delay enemy retaliation.");
        });

        Test("simultaneous projectile events resolve independently without duplicate telegraphs",()=>
        {
            var realm=new RealmEngine(data);var left=realm.CreateCharacter("readability-left","Left Ranger","ranger",new());var right=realm.CreateCharacter("readability-right","Right Ranger","ranger",new());
            var target=realm.State.Creatures.Values.First(x=>x.Owner==""&&data.Mob(x.Template).Ai!="passive");var zone=data.Zone(target.Zone);target.Health=100000;
            double range=data.Item(Items.Owned(left,left.Equipment["weapon"]).Template).Range;
            left.Zone=right.Zone=target.Zone;left.Position=WorldMap.FindFree(zone,new(target.Position.X-1,target.Position.Y));right.Position=WorldMap.FindFree(zone,new(target.Position.X+1,target.Position.Y));
            Need(left.Position.Distance(target.Position)<=range&&right.Position.Distance(target.Position)<=range,"Could not arrange simultaneous ranged fixture.");
            Need(realm.Execute(left.Id,Command(left,"attack",target.Id)).Ok,"Left projectile was rejected.");
            Need(realm.Execute(right.Id,Command(right,"attack",target.Id)).Ok,"Right projectile was rejected.");
            var ids=realm.State.Telegraphs.Where(x=>x.Source==left.Id||x.Source==right.Id).Select(x=>x.Id).ToArray();Need(ids.Length==2&&ids.Distinct().Count()==2,"Simultaneous attacks did not retain distinct event identities.");
            double before=target.Health;for(int i=0;i<8&&ids.Any(id=>realm.State.Telegraphs.Any(x=>x.Id==id));i++)realm.Tick(.1);
            Need(ids.All(id=>realm.State.Telegraphs.All(x=>x.Id!=id))&&target.Health<before,"Simultaneous impacts did not resolve independently.");
        });

        Test("boss phase thresholds immediately expose the expanded attack set",()=>
        {
            var realm=new RealmEngine(data);var boss=realm.State.Creatures.Values.First(x=>data.Mob(x.Template).Boss);var definition=data.Mob(boss.Template);
            boss.Health=definition.Health*.64;boss.NextAttack=double.MaxValue;realm.Tick(.1);realm.Tick(.1);
            Need(boss.Phase==1&&EnemyCombatRules.AvailableBossAttacks(definition,boss.Phase).Count==2,"Boss did not enter phase two at the authoritative health threshold.");
            boss.Health=definition.Health*.29;boss.NextAttack=double.MaxValue;realm.Tick(.1);realm.Tick(.1);
            Need(boss.Phase==2&&EnemyCombatRules.AvailableBossAttacks(definition,boss.Phase).Count==3,"Boss did not enter phase three at the authoritative health threshold.");
            Need(CombatReadabilityRules.EnemyBanner(definition,boss).Contains("PHASE 3/3",StringComparison.Ordinal),"Boss phase presentation does not match authoritative phase state.");
        });

        Test("party revive readiness is derived from server-visible state",()=>
        {
            var self=new Character{Id="self",Zone="wayfarers_rest",Position=new(10,10),Health=20,Stamina=40};
            var other=new PublicPlayer{Id="other",Position=new(11,10),Health=0};var party=new SocialGroup{Members=["self","other"]};
            Need(CombatReadabilityRules.CanRevive(self,other,party,10),"Nearby downed party member was not marked revivable.");
            self.Stamina=19;Need(!CombatReadabilityRules.CanRevive(self,other,party,10),"Revive cue ignored the authoritative stamina requirement.");
            self.Stamina=40;self.Cooldowns["revive"]=11;Need(!CombatReadabilityRules.CanRevive(self,other,party,10),"Revive cue ignored the authoritative cooldown.");
        });

        Console.WriteLine($"COMBAT_READABILITY_AUDIT: {passed}/6 groups passed; failures {failures.Count}. Objective state/presentation contracts only; subjective combat feel remains a manual playtest concern.");
    }
}
