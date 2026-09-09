using Kairnfall.Core;
using System.Text.Json;

internal static class ChallengeProgressionChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string text){if(!value)throw new InvalidOperationException(text);}
        string Json<T>(T value)=>JsonSerializer.Serialize(value,Wire.Json);
        void Test(string name,Action action){try{action();passed++;Console.WriteLine("PASS XP CURVE: "+name);}catch(Exception e){failures.Add(name);Console.WriteLine("FAIL XP CURVE: "+name+": "+e);}}
        Character AtLevel(int target)
        {
            var p=new Character{Class="vanguard"};
            var support=data.Skills.Where(s=>s.Id!="slayer"&&s.Id!="swordsmanship").ToArray();
            long lo=0,hi=Progression.Threshold(100);
            while(lo<hi)
            {
                long mid=(lo+hi)/2; foreach(var skill in support)p.SkillXp[skill.Id]=mid;
                if(Progression.PlayerLevel(p)<target)lo=mid+1;else hi=mid;
            }
            foreach(var skill in support)p.SkillXp[skill.Id]=lo;
            return p;
        }
        Test("Overall retention falls at each ten-level boundary without changing monster statistics",()=>
        {
            double previous=1;
            for(int level=1;level<=200;level++)
            {
                double rate=ChallengeProgression.OverallRate(level);
                Need(double.IsFinite(rate)&&rate>0&&rate<=.25&&rate<=previous,"Invalid pacing at "+level);
                if(level>1&&(level-1)%10==0)Need(rate<previous,"No difficulty increase at "+level);
                previous=rate;
            }
        });
        Test("Twenty-level weaker enemies give little practice and much less overall credit",()=>
        {
            foreach(int level in new[]{25,40,60,80,100})
            {
                Need(ChallengeProgression.SkillPractice(level,level-20)>0&&ChallengeProgression.SkillPractice(level,level-20)<.10,"Trivial practice rate out of bounds");
                Need(ChallengeProgression.EnemyCredit(level,level-20)>0&&ChallengeProgression.EnemyCredit(level,level-20)<.02,"Trivial overall credit out of bounds");
                var matched=AtLevel(level);var weak=Wire.Copy(matched);
                long start=ChallengeProgression.OverallTraining(matched);
                long normal=ChallengeProgression.TrainCombat(matched,"slayer",10000,level,data);
                long small=ChallengeProgression.TrainCombat(weak,"slayer",10000,level-20,data);
                long normalCredit=ChallengeProgression.OverallTraining(matched)-start,smallCredit=ChallengeProgression.OverallTraining(weak)-start;
                Need(small>0&&small<normal/10,"Weak enemies give too much skill XP.");
                Need(smallCredit<Math.Max(1,normalCredit/20),"Weak enemies give too much overall XP.");
            }
        });
        Test("Fractional practice accumulates without granting one free whole XP per tiny hit",()=>
        {
            var p=AtLevel(40);long start=Progression.Total(p);int before=Progression.PlayerLevel(p);
            for(int i=0;i<1000;i++)ChallengeProgression.TrainCombat(p,"slayer",1,1,data);
            long gained=Progression.Total(p)-start;
            Need(gained>0&&gained<100,"Small practice either vanished or became a rounding exploit.");
            Need(p.CombatPracticeRemainders.Values.All(v=>double.IsFinite(v)&&v>=0&&v<1),"Unbounded practice carry");
            Need(Progression.PlayerLevel(p)>=before,"Training reduced player level");
        });
        Test("Skill XP and existing levels survive serialization while future overall gains slow",()=>
        {
            var p=AtLevel(30);int original=Progression.PlayerLevel(p);long start=Progression.Total(p);
            Progression.Train(p,"swordsmanship",1000,100,data);
            Need(p.SkillXp["swordsmanship"]==1100,"Noncombat/general skill award semantics changed.");
            Need(Progression.Total(p)-start==1100,"Raw skill XP was rewritten.");
            Need(p.PracticeOnlyXp>0&&Progression.PlayerLevel(p)>=original,"Crediting changed previous levels.");
            var copy=Wire.Copy(p);Need(Json(copy)==Json(p),"Training credit did not round-trip.");
            ChallengeProgression.TrainCombat(copy,"slayer",7,10,data);ChallengeProgression.TrainCombat(p,"slayer",7,10,data);
            Need(Json(copy)==Json(p),"Reconnection changed future fractional awards.");
            foreach(var skill in data.Skills)p.SkillXp[skill.Id]=Progression.Threshold(100);
            Need(Progression.PlayerLevel(p)==Progression.PlayerCap,"Complete skill mastery lost its final overall cap.");
        });
        Test("Late mastery approaches the overall cap without a final-point level jump",()=>
        {
            var p=new Character { Class="vanguard" };
            foreach(var skill in data.Skills)p.SkillXp[skill.Id]=Progression.Threshold(100);
            p.SkillXp["slayer"]-=100; p.PracticeOnlyXp=Progression.Total(p)*9/10;
            int before=Progression.PlayerLevel(p);
            p.SkillXp["slayer"]+=100; int after=Progression.PlayerLevel(p);
            Need(before>=199&&after==Progression.PlayerCap&&after-before<=1,"The last skill points caused an artificial level jump.");
        });
        Test("Invalid awards fail before state changes and zero awards do not manufacture XP",()=>
        {
            var p=AtLevel(30);
            foreach(var (xp,enemy) in new[]{(-1,10),(100001,10),(1,0),(1,101)})
            {
                string before=Json(p);bool rejected=false;
                try{ChallengeProgression.TrainCombat(p,"slayer",xp,enemy,data);}catch(RuleException){rejected=true;}
                Need(rejected&&Json(p)==before,"Invalid combat award mutated character.");
            }
            string old=Json(p);Need(ChallengeProgression.TrainCombat(p,"slayer",0,10,data)==0&&Json(p)==old,"Zero XP manufactured state.");
        });
        Test("Attack mastery has bounded diminishing returns and armor/resistance retain monotonic reduction",()=>
        {
            foreach(var curve in new Func<int,double>[] {CombatTrainingCurve.Physical,CombatTrainingCurve.Spell})
            {
                double prior=curve(1),priorGain=double.PositiveInfinity;
                for(int skill=2;skill<=100;skill++)
                {
                    double value=curve(skill),gain=value-prior;
                    Need(double.IsFinite(value)&&value>=prior&&value<1.6&&gain<=priorGain+.000001,"Invalid mastery curve");
                    prior=value;priorGain=gain;
                }
            }
            double previous=double.MaxValue;
            foreach(int armor in new[]{0,10,25,50,100,200,1000})
            {
                double value=CombatMath.Damage(100,armor,.25);
                Need(value>=0&&value<=previous,"Armor lost diminishing damage reduction");previous=value;
            }
            Need(CombatMath.Damage(100,100,0)==50,"Existing armor half-damage point changed");
        });
        Test("Real kill rewards use the encounter level and replay cannot duplicate XP credit",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("xp-curve","XP Curve","vanguard",new());
            var setup=AtLevel(40);p.SkillXp=setup.SkillXp;p.Mana=1000;p.Stamina=1000;
            var mob=realm.State.Creatures.Values.First(m=>m.Template=="field_rat"&&m.Health>0);
            p.Zone=mob.Zone;p.Position=mob.Position;mob.Health=1;
            string id=p.Id;long old=Progression.Total(p);
            var command=new GameCommand{Kind="attack",Target=mob.Id,Sequence=p.LastAction+1,RequestId="xp-once"};
            var result=realm.Execute(id,command);Need(result.Ok,result.Message);
            p=realm.Player(id);Need(p.CombatPracticeRemainders.ContainsKey("slayer"),"Kill reward bypassed the challenge formula");
            Need(Progression.Total(p)-old<10,"A trivial kill gave a large raw award");
            string before=Json(realm.State);var replay=realm.Execute(id,command);
            Need(replay.Ok&&Json(realm.State)==before,"Replay duplicated training, damage or credit");
        });
        Test("Simulation exports matched and trivial encounter rewards at all ten-level bands",()=>
        {
            var report=new List<object>();
            for(int level=10;level<=100;level+=10)
            foreach(int offset in new[]{0,5,10,20,30})
            {
                var p=AtLevel(level);int actualLevel=Progression.PlayerLevel(p),enemy=Math.Max(1,level-offset);
                long before=ChallengeProgression.OverallTraining(p),raw=Progression.Total(p);
                for(int i=0;i<100;i++)ChallengeProgression.TrainCombat(p,"slayer",20,enemy,data);
                report.Add(new{player=actualLevel,enemy,events=100,baseXp=2000,practiceXp=Progression.Total(p)-raw,overallCredit=ChallengeProgression.OverallTraining(p)-before,finalLevel=Progression.PlayerLevel(p)});
            }
            Directory.CreateDirectory("artifacts/experience/balance");
            File.WriteAllText("artifacts/experience/balance/xp-curves.json",Json(report));
            Console.WriteLine("XP_CURVE_SAMPLES="+report.Count);
        });
        Console.WriteLine($"XP CURVES: {passed} groups passed; total failures {failures.Count}.");
    }
}
