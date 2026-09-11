using Kairnfall.Core;

internal static class ExplorationRewardChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check){try{check();passed++;Console.WriteLine("PASS EXPLORATION REWARDS: "+name);}catch(Exception e){failures.Add(name);Console.WriteLine("FAIL EXPLORATION REWARDS: "+name+": "+e.Message);}}
        var regions=data.Zones.Where(ExplorationRewards.Eligible).OrderBy(z=>z.Level).ThenBy(z=>z.Id,StringComparer.Ordinal).ToArray();

        Test("every surface wilderness region has one hidden cache and one unique mastery keepsake",()=>
        {
            Need(regions.Length==20,"Expected exactly 20 surface wilderness regions.");
            var rewardIds=new HashSet<string>(StringComparer.Ordinal);
            var realm=new RealmEngine(data);
            foreach(var zone in regions)
            {
                Need(ExplorationRewards.Landmarks(zone).Count==4,"Expected four authored waymarks in "+zone.Id);
                var cache=realm.State.Chests.GetValueOrDefault(ExplorationRewards.CacheId(zone));
                Need(cache is not null&&cache.Hidden,"Missing hidden regional cache in "+zone.Id);
                var reward=data.Items.SingleOrDefault(x=>x.Id==ExplorationRewards.RewardItemId(zone));
                Need(reward is not null&&reward.Type=="treasure"&&reward.Tags.Contains("exploration_unique",StringComparer.Ordinal),"Missing mastery keepsake for "+zone.Id);
                Need(rewardIds.Add(reward!.Id),"Duplicate regional keepsake ID.");
            }
        });

        Test("two real landmark surveys unlock a wider cache-search clue without globally revealing the cache",()=>
        {
            var zone=regions[0];var realm=new RealmEngine(data);var p=realm.CreateCharacter("exploration-clue","Clue Seeker","vanguard",new());p.Zone=zone.Id;
            var cache=realm.State.Chests[ExplorationRewards.CacheId(zone)];p.Position=cache.Position;
            Need(!realm.Snapshot(p.Id).Chests.Any(x=>x.Id==cache.Id),"Hidden cache leaked before clue or discovery.");
            long before=p.SkillXp["treasure_hunting"];
            foreach(var landmark in ExplorationRewards.Landmarks(zone).Take(2))
            {
                p.Position=JourneyProgression.LandmarkPoint(landmark);
                var result=realm.Execute(p.Id,new GameCommand{Kind="inspect",Target=landmark.Id,Sequence=p.LastAction+1});Need(result.Ok,"Landmark inspection failed: "+result.Message);
            }
            Need(ExplorationRewards.HasClue(p,zone),"Two waymarks did not persist a cache clue.");Need(p.SkillXp["treasure_hunting"]>before,"Cache clue granted no Treasure Hunting XP.");
            Need(!ExplorationRewards.CacheDiscovered(p,zone),"Clue incorrectly marked exact cache discovery.");
            p.Position=cache.Position;
            Need(realm.Snapshot(p.Id).Chests.Any(x=>x.Id==cache.Id),"Clue did not expand local cache visibility.");
        });

        Test("charting counts real terrain sectors rather than landmark metadata",()=>
        {
            var zone=regions[0];
            {
                var realm=new RealmEngine(data);var p=realm.CreateCharacter("exploration-chart-reject","Chart Reject","vanguard",new());p.Zone=zone.Id;p.Position=zone.Spawn;
                foreach(var marker in ExplorationRewards.Landmarks(zone))p.Discoveries.Add(ExplorationRewards.LandmarkKey(zone,marker));
                Items.Add(p.Inventory,Items.Create(data,"parchment"),data);Items.Add(p.Inventory,Items.Create(data,"ink"),data);
                var rejected=realm.Execute(p.Id,new GameCommand{Kind="chart",Sequence=p.LastAction+1});Need(!rejected.Ok,"Landmark metadata falsely satisfied map-sector charting.");
            }
            {
                var realm=new RealmEngine(data);var p=realm.CreateCharacter("exploration-chart-accept","Chart Accept","vanguard",new());p.Zone=zone.Id;p.Position=zone.Spawn;
                foreach(var marker in ExplorationRewards.Landmarks(zone))p.Discoveries.Add(ExplorationRewards.LandmarkKey(zone,marker));
                for(int i=0;i<ExplorationRewards.RequiredChartSectors;i++)p.Discoveries.Add($"{zone.Id}:{i}:0");
                Items.Add(p.Inventory,Items.Create(data,"parchment"),data);Items.Add(p.Inventory,Items.Create(data,"ink"),data);
                var accepted=realm.Execute(p.Id,new GameCommand{Kind="chart",Sequence=p.LastAction+1});var authoritative=realm.Player(p.Id);
                Need(accepted.Ok&&ExplorationRewards.Charted(authoritative,zone),"Real sector discoveries did not permit charting: "+accepted.Message);
            }
        });

        Test("first hidden-cache opening records a permanent regional objective and bonus",()=>
        {
            var zone=regions[0];var realm=new RealmEngine(data);var p=realm.CreateCharacter("exploration-cache","Cache Tester","vanguard",new());p.Zone=zone.Id;
            var cache=realm.State.Chests[ExplorationRewards.CacheId(zone)];p.Position=cache.Position;p.Discoveries.Add("secret:"+cache.Id);p.SkillXp["runecasting"]=Progression.Threshold(100);
            long beforeXp=p.SkillXp["treasure_hunting"];long beforeGold=p.Gold;
            var opened=realm.Execute(p.Id,new GameCommand{Kind="chest",Target=cache.Id,Sequence=p.LastAction+1});
            Need(opened.Ok,"Hidden cache opening failed: "+opened.Message);Need(ExplorationRewards.CacheOpened(p,zone),"First cache opening was not persisted.");
            Need(p.SkillXp["treasure_hunting"]>beforeXp&&p.Gold>beforeGold,"First cache provided no economic/skill reward.");Need(p.Achievements.Contains("cache:"+zone.Id),"First-cache achievement missing.");
        });

        Test("complete regional exploration grants exactly one persistent keepsake and mastery reward",()=>
        {
            var zone=regions[0];var realm=new RealmEngine(data);var p=realm.CreateCharacter("exploration-mastery","Mastery Tester","vanguard",new());p.Zone=zone.Id;
            foreach(var landmark in ExplorationRewards.Landmarks(zone))
            {
                p.Position=JourneyProgression.LandmarkPoint(landmark);
                var surveyed=realm.Execute(p.Id,new GameCommand{Kind="inspect",Target=landmark.Id,Sequence=p.LastAction+1});Need(surveyed.Ok,"Waymark survey failed.");
            }
            for(int i=0;i<ExplorationRewards.RequiredChartSectors;i++)p.Discoveries.Add($"{zone.Id}:{i}:0");
            var cache=realm.State.Chests[ExplorationRewards.CacheId(zone)];p.Position=cache.Position;p.Discoveries.Add("secret:"+cache.Id);p.SkillXp["runecasting"]=Progression.Threshold(100);
            var opened=realm.Execute(p.Id,new GameCommand{Kind="chest",Target=cache.Id,Sequence=p.LastAction+1});Need(opened.Ok,"Regional cache failed.");
            Items.Add(p.Inventory,Items.Create(data,"parchment"),data);Items.Add(p.Inventory,Items.Create(data,"ink"),data);long beforeGold=p.Gold;long beforeExploration=p.SkillXp["exploration"];
            var charted=realm.Execute(p.Id,new GameCommand{Kind="chart",Sequence=p.LastAction+1});Need(charted.Ok,"Regional chart failed: "+charted.Message);
            string reward=ExplorationRewards.RewardItemId(zone);
            int CountReward()=>p.Inventory.Concat(p.Bank).Count(x=>x.Template==reward);
            Need(ExplorationRewards.Rewarded(p,zone)&&CountReward()==1,"Regional mastery did not grant exactly one keepsake.");
            Need(p.Gold>beforeGold&&p.SkillXp["exploration"]>beforeExploration,"Regional mastery omitted bonus progression.");Need(p.Achievements.Contains("explorer:"+zone.Id),"Regional mastery achievement missing.");
            var saved=Wire.Copy(p);Need(saved.Discoveries.Contains(ExplorationRewards.RewardKey(zone))&&saved.Inventory.Concat(saved.Bank).Count(x=>x.Template==reward)==1,"Mastery did not survive serialization.");
            var firstLandmark=ExplorationRewards.Landmarks(zone)[0];p.Position=JourneyProgression.LandmarkPoint(firstLandmark);
            var revisit=realm.Execute(p.Id,new GameCommand{Kind="inspect",Target=firstLandmark.Id,Sequence=p.LastAction+1});Need(revisit.Ok&&CountReward()==1,"Repeated inspection duplicated mastery loot.");
        });

        Console.WriteLine($"EXPLORATION_REWARDS_AUDIT: {regions.Length} regions; {passed} groups passed; failures {failures.Count}.");
    }
}
