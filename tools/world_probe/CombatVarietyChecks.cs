using Kairnfall.Core;

internal static class CombatVarietyChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check){try{check();passed++;Console.WriteLine("PASS COMBAT VARIETY: "+name);}catch(Exception e){failures.Add(name);Console.WriteLine("FAIL COMBAT VARIETY: "+name+": "+e.Message);}}

        Test("ordinary enemies expose distinct tactical attack profiles",()=>
        {
            var normal=data.Mobs.Where(x=>!x.Boss&&!x.Elite).ToArray();Need(normal.Length==100,"Expected 100 normal species.");
            Need(normal.All(x=>x.Attacks.Length>0&&x.Attacks.All(EnemyCombatRules.IsKnownAttack)),"Normal roster contains unknown or empty attack profiles.");
            Need(normal.SelectMany(x=>x.Attacks).Distinct(StringComparer.Ordinal).Count()>=10,"Ordinary roster does not contain enough distinct combat actions.");
            foreach(var role in new[]{"ranged_kiter","caster","ambusher","pack_hunter","healer","summoner","guard","berserker"})
                Need(normal.Any(x=>x.Ai==role),"Missing tactical AI role "+role+".");
        });

        Test("all elites carry one of five deterministic mechanical modifiers",()=>
        {
            var elites=data.Mobs.Where(x=>x.Elite).ToArray();Need(elites.Length==25,"Expected 25 elite variants.");
            foreach(var elite in elites)Need(elite.Attacks.Count(EnemyCombatRules.IsEliteTrait)==1,"Elite trait count mismatch for "+elite.Id);
            foreach(var trait in EnemyCombatRules.EliteTraits)Need(elites.Count(x=>EnemyCombatRules.EliteTrait(x)==trait)==5,"Elite trait distribution mismatch for "+trait);
            Need(EnemyCombatRules.IncomingDamageMultiplier(elites.First(x=>EnemyCombatRules.EliteTrait(x)=="elite_bulwark"))<1,"Bulwark has no mitigation.");
            Need(EnemyCombatRules.MoveSpeedMultiplier(elites.First(x=>EnemyCombatRules.EliteTrait(x)=="elite_skirmisher"))>1,"Fleet elite has no movement bonus.");
        });

        Test("all bosses use three valid authored attacks with phase expansion",()=>
        {
            var bosses=data.Mobs.Where(x=>x.Boss).ToArray();Need(bosses.Length==20,"Expected 20 bosses.");
            foreach(var boss in bosses)
            {
                Need(boss.Attacks.Length==3,boss.Id+" does not have exactly three authored attacks.");
                Need(boss.Attacks.All(EnemyCombatRules.IsKnownAttack),boss.Id+" contains an unsupported authored attack.");
                Need(EnemyCombatRules.AvailableBossAttacks(boss,0).Count==1,"Phase one attack set mismatch for "+boss.Id);
                Need(EnemyCombatRules.AvailableBossAttacks(boss,1).Count==2,"Phase two attack set mismatch for "+boss.Id);
                Need(EnemyCombatRules.AvailableBossAttacks(boss,2).Count==3,"Phase three attack set mismatch for "+boss.Id);
            }
            var mill=data.Mob("millbreaker");var creature=new Creature{Template=mill.Id,Health=mill.Health,Phase=0};
            Need(EnemyCombatRules.NextBossAttack(mill,creature)=="charge","Millbreaker did not open with authored Charge.");
            creature.Phase=1;Need(EnemyCombatRules.NextBossAttack(mill,creature)=="cone","Millbreaker phase two did not expose authored Sweep.");
            creature.Phase=2;Need(EnemyCombatRules.NextBossAttack(mill,creature)=="stomp","Millbreaker phase three did not expose authored Stomp.");
        });

        Test("real ranged kiter creates distance under close pressure",()=>
        {
            var realm=new RealmEngine(data);var definition=data.Mobs.First(x=>!x.Boss&&!x.Elite&&x.Ai=="ranged_kiter");
            var mob=realm.State.Creatures.Values.First(x=>x.Template==definition.Id);var zone=data.Zone(mob.Zone);
            var player=realm.CreateCharacter("combat-variety-kiter","Kiter Tester","vanguard",new());player.Zone=mob.Zone;
            player.Position=WorldMap.FindFree(zone,new(mob.Position.X+1.2,mob.Position.Y));
            if(player.Position.Distance(mob.Position)>=3)player.Position=WorldMap.FindFree(zone,new(mob.Position.X-1.2,mob.Position.Y));
            Need(player.Position.Distance(mob.Position)<3,"Could not arrange close kiter fixture.");
            mob.Home=mob.Position;mob.Threat[player.Id]=100;mob.Target=player.Id;mob.NextAttack=double.MaxValue;realm.Active.Add(player.Id);
            double before=player.Position.Distance(mob.Position);
            for(int i=0;i<12;i++)realm.Tick(.1);
            Need(player.Position.Distance(mob.Position)>before+.2,"Ranged kiter did not retreat from close pressure.");
        });

        Test("real boss queues authored charge and moves when it resolves",()=>
        {
            var realm=new RealmEngine(data);var boss=realm.State.Creatures.Values.First(x=>x.Template=="millbreaker");var definition=data.Mob(boss.Template);var zone=data.Zone(boss.Zone);
            boss.Position=zone.Spawn;boss.Home=zone.Spawn;boss.Health=definition.Health;boss.Phase=0;boss.AttackStep=0;boss.NextAttack=0;
            var player=realm.CreateCharacter("combat-variety-boss","Boss Tester","vanguard",new());player.Zone=boss.Zone;player.Position=WorldMap.FindFree(zone,new(zone.Spawn.X+2,zone.Spawn.Y));
            Need(player.Position.Distance(boss.Position)<4,"Could not arrange boss fixture.");boss.Threat[player.Id]=100;boss.Target=player.Id;realm.Active.Add(player.Id);
            realm.Tick(.1);realm.Tick(.1);
            var telegraph=realm.State.Telegraphs.FirstOrDefault(x=>x.Source==boss.Id&&x.Skill=="charge");Need(telegraph is not null,"Boss did not queue authored Charge telegraph.");
            var before=boss.Position;
            for(int i=0;i<12;i++)realm.Tick(.1);
            Need(before.Distance(boss.Position)>.2,"Charge resolved without moving the boss.");
        });

        Console.WriteLine($"COMBAT_VARIETY_AUDIT: 100 normal species, 25 elites and 20 bosses checked; {passed} groups passed; failures {failures.Count}.");
    }
}
