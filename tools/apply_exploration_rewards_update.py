#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def edit(path, old, new):
    p=ROOT/path
    text=p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'anchor missing in {path}: {old[:140]!r}')
    p.write_text(text.replace(old,new,1),encoding='utf-8')

# Generate one non-combat, non-power-creeping keepsake for every surface wilderness region.
(ROOT/'content_src/exploration_rewards.py').write_text(r'''"""One-time regional exploration trophies generated from authored wilderness regions."""
from .items import Builder


def build(data):
    b=Builder(data)
    regions=sorted(
        (z for z in data['zones'] if z['kind']=='wilderness' and z['layer']=='Surface'),
        key=lambda z:(z['level'],z['id']))
    for zone in regions:
        ident='keepsake_'+zone['id']
        b.item(
            ident,
            zone['name']+' Keepsake',
            'treasure',
            material='relic',
            requirement=max(1,min(100,zone['level'])),
            value=80+max(1,zone['level'])*5,
            tags=['exploration_unique','zone:'+zone['id']],
            description=(
                'A one-of-a-kind regional trophy awarded for surveying every waymark, '
                'finding the hidden cache, and charting '+zone['name']+'. '+zone['lore']))
''',encoding='utf-8')

edit(Path('tools/build_content.py'),
'''from content_src import skills, items, abilities, mobs, boss_uniques, world, quests, presentation, gear_progression\n''',
'''from content_src import skills, items, abilities, mobs, boss_uniques, world, exploration_rewards, quests, presentation, gear_progression\n''')
edit(Path('tools/build_content.py'),
'''    for module in [skills,items,abilities,mobs,boss_uniques,world,quests,presentation,gear_progression]: module.build(data)\n''',
'''    for module in [skills,items,abilities,mobs,boss_uniques,world,exploration_rewards,quests,presentation,gear_progression]: module.build(data)\n''')

# Shared, save-compatible region completion rules. All durable state uses existing discovery/achievement sets.
(ROOT/'src/Kairnfall.Core/ExplorationRewards.cs').write_text(r'''namespace Kairnfall.Core;

public static class ExplorationRewards
{
    public const int CacheClueLandmarks=2;
    public const int RequiredChartSectors=4;
    public const double CacheClueRevealRadius=12;

    public static bool Eligible(ZoneDef zone)=>zone.Kind=="wilderness"&&zone.Layer=="Surface";
    public static IReadOnlyList<BuildingDef> Landmarks(ZoneDef zone)=>zone.Buildings
        .Where(x=>JourneyProgression.IsLandmark(zone,x)).OrderBy(x=>x.Id,StringComparer.Ordinal).ToArray();
    public static string LandmarkKey(ZoneDef zone,BuildingDef landmark)=>zone.Id+":landmark:"+landmark.Id;
    public static string ClueKey(ZoneDef zone)=>"cache_clue:"+zone.Id;
    public static string CacheId(ZoneDef zone)=>zone.Id+"/chest/2";
    public static string CacheOpenedKey(ZoneDef zone)=>"cache_opened:"+zone.Id;
    public static string RewardKey(ZoneDef zone)=>"region_reward:"+zone.Id;
    public static string RewardItemId(ZoneDef zone)=>"keepsake_"+zone.Id;

    public static int LandmarkCount(Character player,ZoneDef zone)=>Landmarks(zone).Count(x=>player.Discoveries.Contains(LandmarkKey(zone,x)));
    public static int SectorCount(Character player,ZoneDef zone)
    {
        int total=0;
        foreach(string discovery in player.Discoveries)
        {
            var parts=discovery.Split(':');
            if(parts.Length==3&&parts[0]==zone.Id&&int.TryParse(parts[1],out _)&&int.TryParse(parts[2],out _)) total++;
        }
        return total;
    }
    public static bool HasClue(Character player,ZoneDef zone)=>player.Discoveries.Contains(ClueKey(zone));
    public static bool CacheDiscovered(Character player,ZoneDef zone)=>player.Discoveries.Contains("secret:"+CacheId(zone));
    public static bool CacheOpened(Character player,ZoneDef zone)=>player.Discoveries.Contains(CacheOpenedKey(zone));
    public static bool Charted(Character player,ZoneDef zone)=>player.Discoveries.Contains("charted:"+zone.Id);
    public static bool Rewarded(Character player,ZoneDef zone)=>player.Discoveries.Contains(RewardKey(zone));
    public static bool MasteryReady(Character player,ZoneDef zone)
        =>Eligible(zone)&&LandmarkCount(player,zone)>=Landmarks(zone).Count&&Charted(player,zone)&&CacheOpened(player,zone);

    public static bool VisibleChest(Character player,Chest chest,Catalog data)
    {
        if(!chest.Hidden)return true;
        if(player.Discoveries.Contains("secret:"+chest.Id))return true;
        var zone=data.Zone(chest.Zone);
        return Eligible(zone)&&chest.Id==CacheId(zone)&&HasClue(player,zone)&&chest.Position.Distance(player.Position)<=CacheClueRevealRadius;
    }

    public static string TryRevealCacheClue(Character player,ZoneDef zone,Catalog data)
    {
        if(!Eligible(zone)||LandmarkCount(player,zone)<CacheClueLandmarks||!player.Discoveries.Add(ClueKey(zone)))return "";
        Progression.Train(player,"treasure_hunting",25,Math.Clamp(zone.Level,1,100),data);
        player.Achievements.Add("trail:"+zone.Id);
        return $"\nCACHE CLUE · Two waymarks align. Search away from the road; the hidden cache becomes visible within {CacheClueRevealRadius:0} tiles.";
    }

    public static string TryGrantRegionalReward(Character player,ZoneDef zone,Catalog data)
    {
        if(!MasteryReady(player,zone)||Rewarded(player,zone))return "";
        var reward=data.Items.FirstOrDefault(x=>x.Id==RewardItemId(zone));
        if(reward is null)return "\nRegional mastery reward is unavailable because its catalog item is missing.";
        bool banked=false;
        if(player.Inventory.Count<Items.InventoryCapacity)
            Items.Add(player.Inventory,Items.Create(data,reward.Id),data);
        else if(player.Bank.Count<Items.BankCapacity)
        {
            Items.Add(player.Bank,Items.Create(data,reward.Id),data,Items.BankCapacity);banked=true;
        }
        else return "\nREGIONAL MASTERY READY · Free one backpack or bank slot, then inspect any waymark again to claim the keepsake.";

        player.Discoveries.Add(RewardKey(zone));
        Progression.Train(player,"exploration",200,Math.Clamp(zone.Level,1,100),data);
        Progression.Train(player,"treasure_hunting",120,Math.Clamp(zone.Level,1,100),data);
        long gold=Math.Min(Items.GoldCap-player.Gold,50L+zone.Level*4L);if(gold>0)Items.Grant(player,gold);
        player.Achievements.Add("explorer:"+zone.Id);
        int mastered=player.Discoveries.Count(x=>x.StartsWith("region_reward:",StringComparison.Ordinal));
        if(mastered>=5)player.Achievements.Add("pathfinder");
        if(mastered>=10)player.Achievements.Add("trailblazer");
        if(mastered>=20)player.Achievements.Add("worldwalker");
        return $"\nREGIONAL MASTERY · {reward.Name} earned{(banked?" and sent to your bank":"")}, plus {gold} gold and bonus Exploration/Treasure Hunting XP.";
    }

    public static string ProgressSummary(Character player,ZoneDef zone)
    {
        if(!Eligible(zone))return "Exploration rewards are tracked in surface wilderness regions.";
        int landmarks=LandmarkCount(player,zone),total=Landmarks(zone).Count,sectors=SectorCount(player,zone);
        string chart=Charted(player,zone)?"charted":$"chart {Math.Min(sectors,RequiredChartSectors)}/{RequiredChartSectors} sectors";
        string cache=CacheOpened(player,zone)?"cache opened":CacheDiscovered(player,zone)?"cache found":HasClue(player,zone)?"cache clue active":"cache unknown";
        string reward=Rewarded(player,zone)?"mastery claimed":MasteryReady(player,zone)?"mastery ready":"mastery pending";
        return $"Exploration · Waymarks {landmarks}/{total} · {chart} · {cache} · {reward}";
    }

    public static string LandmarkLore(ZoneDef zone,BuildingDef landmark)
    {
        string structure=landmark.Style.Replace('_',' ');
        return $"{landmark.Name} · {UiWords(zone.Biome)} {structure}. {zone.Lore}";
    }

    private static string UiWords(string value)=>string.Join(' ',value.Split('_',StringSplitOptions.RemoveEmptyEntries).Select(x=>char.ToUpperInvariant(x[0])+x[1..]));
}
''',encoding='utf-8')

# Integrate clues, hidden-cache first-open rewards, real-sector charting and final regional mastery.
edit(Path('src/Kairnfall.Core/RealmEconomy.cs'),
'''        bool first=p.Discoveries.Add(zone.Id+":landmark:"+landmark.Id);\n        if(first)Progression.Train(p,"exploration",50,Math.Clamp(zone.Level,1,100),Data);\n        Progress(p,"survey",landmark.Id);\n        return first?$"Surveyed {landmark.Name} in {zone.Name}.":$"Reviewed {landmark.Name} in {zone.Name}.";\n''',
'''        bool first=p.Discoveries.Add(ExplorationRewards.LandmarkKey(zone,landmark));\n        string clue="";\n        if(first)\n        {\n            Progression.Train(p,"exploration",50,Math.Clamp(zone.Level,1,100),Data);\n            clue=ExplorationRewards.TryRevealCacheClue(p,zone,Data);\n        }\n        Progress(p,"survey",landmark.Id);\n        string mastery=ExplorationRewards.TryGrantRegionalReward(p,zone,Data);\n        string verb=first?$"Surveyed {landmark.Name} in {zone.Name}.":$"Reviewed {landmark.Name} in {zone.Name}.";\n        return verb+"\\n"+ExplorationRewards.LandmarkLore(zone,landmark)+"\\n"+ExplorationRewards.ProgressSummary(p,zone)+clue+mastery;\n''')

edit(Path('src/Kairnfall.Core/RealmEconomy.cs'),
'''        Items.Grant(p,10+chest.Requirement*3); chest.ReadyAt=State.Time+600;\n        Progression.Train(p,"treasure_hunting",80,chest.Requirement,Data); Progress(p,"chest",chest.Kind);\n        return "Chest opened.";\n''',
'''        Items.Grant(p,10+chest.Requirement*3); chest.ReadyAt=State.Time+600;\n        Progression.Train(p,"treasure_hunting",80,chest.Requirement,Data); Progress(p,"chest",chest.Kind);\n        string exploration="";var chestZone=Data.Zone(chest.Zone);\n        if(chest.Hidden&&ExplorationRewards.Eligible(chestZone)&&id==ExplorationRewards.CacheId(chestZone)&&p.Discoveries.Add(ExplorationRewards.CacheOpenedKey(chestZone)))\n        {\n            Progression.Train(p,"treasure_hunting",60,chest.Requirement,Data);p.Achievements.Add("cache:"+chestZone.Id);\n            exploration="\\nFIRST CACHE · This region's hidden cache is now recorded in your exploration journal.";\n        }\n        string mastery=ExplorationRewards.TryGrantRegionalReward(p,chestZone,Data);\n        return "Chest opened."+exploration+mastery+(ExplorationRewards.Eligible(chestZone)?"\\n"+ExplorationRewards.ProgressSummary(p,chestZone):"");\n''')

edit(Path('src/Kairnfall.Core/RealmEconomy.cs'),
'''        int found=p.Discoveries.Count(x=>x.StartsWith(zone.Id+":",StringComparison.Ordinal));\n        Need(found>=4,"Explore at least four sectors before drawing a regional chart.");\n        Items.Consume(p,"parchment",1); Items.Consume(p,"ink",1);\n        p.Discoveries.Add("charted:"+zone.Id); Progression.Train(p,"cartography",120,Math.Clamp(zone.Level,1,100),Data);\n        Progress(p,"chart",zone.Id); return "Regional chart completed. Roads and known exits are now recorded.";\n''',
'''        int found=ExplorationRewards.SectorCount(p,zone);\n        Need(found>=ExplorationRewards.RequiredChartSectors,$"Explore at least {ExplorationRewards.RequiredChartSectors} real map sectors before drawing a regional chart ({found}/{ExplorationRewards.RequiredChartSectors}).");\n        Items.Consume(p,"parchment",1); Items.Consume(p,"ink",1);\n        p.Discoveries.Add("charted:"+zone.Id); Progression.Train(p,"cartography",120,Math.Clamp(zone.Level,1,100),Data);\n        Progress(p,"chart",zone.Id);string mastery=ExplorationRewards.TryGrantRegionalReward(p,zone,Data);\n        return "Regional chart completed. Roads and known exits are now recorded."+mastery+(ExplorationRewards.Eligible(zone)?"\\n"+ExplorationRewards.ProgressSummary(p,zone):"");\n''')

# A clue enlarges discovery visibility without revealing a secret cache globally or through the atlas.
edit(Path('src/Kairnfall.Core/RealmEngine.cs'),
'''        snap.Chests=State.Chests.Values.Where(x=>x.Zone==p.Zone&&x.Position.Distance(p.Position)<=range&&(!x.Hidden||p.Discoveries.Contains("secret:"+x.Id))).Select(Wire.Copy).ToList();\n''',
'''        snap.Chests=State.Chests.Values.Where(x=>x.Zone==p.Zone&&x.Position.Distance(p.Position)<=range&&ExplorationRewards.VisibleChest(p,x,Data)).Select(Wire.Copy).ToList();\n''')

# Hunting guide presents progress and clues but deliberately does not reveal exact cache coordinates.
edit(Path('client/Scripts/HuntingGuidePanel.cs'),
'''        right.AddChild(Ui.Label("Circle: hunting patch · Diamond: boss · Gold square: open exit · Red square: locked frontier\\nTravel on foot. Q dashes; Tab changes target. Hidden caches are not exposed by this map.",12,Ui.Muted,true));\n''',
'''        right.AddChild(Ui.Label("Circle: hunting patch · Diamond: boss · Gold square: open exit · Red square: locked frontier\\nTravel on foot. Q dashes; Tab changes target. Cache clues improve search range but never expose exact cache coordinates on this map.",12,Ui.Muted,true));\n''')
edit(Path('client/Scripts/HuntingGuidePanel.cs'),
'''        overview.Text=zone.Name+" · "+plan.Specialty+$"\\nCharacter {playerLevel} · Threat {JourneyProgression.ThreatLevel(Data,zone)} · "+plan.OrdinaryCount+" ordinary spawn slots · "+plan.Patches.Count+" patches";\n''',
'''        overview.Text=zone.Name+" · "+plan.Specialty+$"\\nCharacter {playerLevel} · Threat {JourneyProgression.ThreatLevel(Data,zone)} · "+plan.OrdinaryCount+" ordinary spawn slots · "+plan.Patches.Count+" patches";\n        if(ExplorationRewards.Eligible(zone))overview.Text+="\\n"+ExplorationRewards.ProgressSummary(self,zone);\n''')
edit(Path('client/Scripts/HuntingGuidePanel.cs'),
'''            :activity is not null?$"CHANGE OF PACE · {activity.Name} level {Progression.BaseLevel(self,activity.Id)}\\n{activity.Action}":"Explore, quest, craft and hunt to build your character.";\n        if(sites.TryGetValue(SelectedSite,out var selected))\n''',
'''            :activity is not null?$"CHANGE OF PACE · {activity.Name} level {Progression.BaseLevel(self,activity.Id)}\\n{activity.Action}":"Explore, quest, craft and hunt to build your character.";\n        if(ExplorationRewards.Eligible(zone)&&ExplorationRewards.HasClue(self,zone)&&!ExplorationRewards.CacheDiscovered(self,zone))\n            journey.Text+=$"\\nCACHE CLUE · Search off-road. The regional cache appears in-world when you are within {ExplorationRewards.CacheClueRevealRadius:0} tiles.";\n        else if(ExplorationRewards.Eligible(zone)&&ExplorationRewards.CacheDiscovered(self,zone)&&!ExplorationRewards.CacheOpened(self,zone))\n            journey.Text+="\\nCACHE FOUND · Return to the discovered chest and open it for the first-cache bonus.";\n        if(sites.TryGetValue(SelectedSite,out var selected))\n''')

# Atlas shows completion state and the named trophy, while never drawing hidden-cache coordinates.
edit(Path('client/Scripts/Maps.cs'),
'''            if (zone.Id == player?.Zone) DrawArc(at, 13, 0, MathF.Tau, 24, new Color("a9cde2"), 2);\n            DrawRect(new Rect2(at - new Vector2(5, 5), new Vector2(10, 10)), color);\n''',
'''            if (zone.Id == player?.Zone) DrawArc(at, 13, 0, MathF.Tau, 24, new Color("a9cde2"), 2);\n            if(player is not null&&ExplorationRewards.Eligible(zone)&&ExplorationRewards.Rewarded(player,zone))DrawArc(at,10,0,MathF.Tau,20,Ui.Success,2);\n            DrawRect(new Rect2(at - new Vector2(5, 5), new Vector2(10, 10)), color);\n''')
edit(Path('client/Scripts/Maps.cs'),
'''            detail.AddChild(Ui.Label(zone.Lore, 14, Ui.Muted, true));\n            if(locked)detail.AddChild(Ui.Label($"LOCKED · Reach character level {entryLevel} ({entryLevel-playerLevel} to go).",13,Ui.Danger,true));\n''',
'''            detail.AddChild(Ui.Label(zone.Lore, 14, Ui.Muted, true));\n            if(ExplorationRewards.Eligible(zone)&&(zone.Id==Snapshot.Self.Zone||Snapshot.Self.Discoveries.Contains(zone.Id)))\n            {\n                detail.AddChild(Ui.Label(ExplorationRewards.ProgressSummary(Snapshot.Self,zone),13,Ui.Success,true));\n                var prize=Data.Item(ExplorationRewards.RewardItemId(zone));\n                detail.AddChild(Ui.Label("Regional mastery reward · "+prize.Name+"\\nSurvey every waymark, open the hidden cache, and chart four real map sectors.",12,Ui.Muted,true));\n            }\n            if(locked)detail.AddChild(Ui.Label($"LOCKED · Reach character level {entryLevel} ({entryLevel-playerLevel} to go).",13,Ui.Danger,true));\n''')

# Distinct deterministic icons for exploration trophies instead of generic supply bags.
edit(Path('tools/art/items.py'),
'''    elif kind=='structure':\n''',
r'''    elif kind=='treasure':
        h=abs(seed(ident)); tones=['c9a45e','83a7a1','a9829d','8fa06a','9d8061','8197b1','b28b68','8d85ad']; base=tones[h%len(tones)]; c=palette(base)
        p.sphere((5,5,27,27),base); p.sphere((8,8,24,24),shade(base,.72,0)); p.line([(9,9),(22,9),(24,16),(21,23),(10,23),(7,16),(9,9)],c[4])
        variant=(h//len(tones))%4
        if variant==0:
            p.line([(16,9),(16,23)],c[5],2); p.line([(10,16),(22,16)],c[5],2); p.poly([(16,10),(19,15),(16,13),(13,15)],'f1ddad')
        elif variant==1:
            p.poly([(16,9),(22,16),(16,23),(10,16)],c[4]); p.poly([(16,12),(19,16),(16,20),(13,16)],'e7d19f'); p.dot(16,16,'fff1c8')
        elif variant==2:
            p.line([(10,21),(13,12),(18,10),(22,14),(20,22)],c[5],2); p.line([(12,18),(21,18)],'ead7aa'); p.dot(16,13,'fff0c6')
        else:
            for angle in range(0,360,90):
                rad=math.radians(angle); p.line([(16,16),(16+math.cos(rad)*7,16+math.sin(rad)*7)],c[5],2)
            p.sphere((13,13,19,19),'e9d5a4')
        p.line([(9,25),(23,25)],c[1]); p.dot(8+(h%17),27,c[5])
    elif kind=='structure':
''')

# Permanent authoritative exploration reward regression suite.
(ROOT/'tools/world_probe/ExplorationRewardChecks.cs').write_text(r'''using Kairnfall.Core;

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
            var zone=regions[0];var realm=new RealmEngine(data);var p=realm.CreateCharacter("exploration-chart","Chart Tester","vanguard",new());p.Zone=zone.Id;p.Position=zone.Spawn;
            foreach(var landmark in ExplorationRewards.Landmarks(zone))p.Discoveries.Add(ExplorationRewards.LandmarkKey(zone,landmark));
            Items.Add(p.Inventory,Items.Create(data,"parchment"),data);Items.Add(p.Inventory,Items.Create(data,"ink"),data);
            var rejected=realm.Execute(p.Id,new GameCommand{Kind="chart",Sequence=p.LastAction+1});Need(!rejected.Ok,"Landmark metadata falsely satisfied map-sector charting.");
            for(int i=0;i<ExplorationRewards.RequiredChartSectors;i++)p.Discoveries.Add($"{zone.Id}:{i}:0");
            var accepted=realm.Execute(p.Id,new GameCommand{Kind="chart",Sequence=p.LastAction+1});Need(accepted.Ok&&ExplorationRewards.Charted(p,zone),"Real sector discoveries did not permit charting: "+accepted.Message);
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
            var landmark=ExplorationRewards.Landmarks(zone)[0];p.Position=JourneyProgression.LandmarkPoint(landmark);
            var revisit=realm.Execute(p.Id,new GameCommand{Kind="inspect",Target=landmark.Id,Sequence=p.LastAction+1});Need(revisit.Ok&&CountReward()==1,"Repeated inspection duplicated mastery loot.");
        });

        Console.WriteLine($"EXPLORATION_REWARDS_AUDIT: {regions.Length} regions; {passed} groups passed; failures {failures.Count}.");
    }
}
''',encoding='utf-8')

edit(Path('tools/world_probe/Program.cs'),
'''MeaningfulObjectiveChecks.Run(catalog,failures);\nCombatVarietyChecks.Run(catalog,failures);\n''',
'''MeaningfulObjectiveChecks.Run(catalog,failures);\nCombatVarietyChecks.Run(catalog,failures);\nExplorationRewardChecks.Run(catalog,failures);\n''')

(ROOT/'docs/EXPLORATION_REWARDS.md').write_text(r'''# World exploration rewards

Status: implemented as Area 5 exploration-reward work.

The 20 surface wilderness regions now share one coherent exploration loop rather than isolated discovery counters:

1. **Survey waymarks.** First-time landmark surveys grant Exploration XP and surface the region's authored lore.
2. **Earn a cache clue.** Surveying two of the region's four waymarks grants a permanent clue and Treasure Hunting XP. The clue never reveals an exact atlas coordinate; it only lets the hidden cache appear in-world when the player searches within 12 tiles.
3. **Find and open the hidden cache.** Every surface wilderness region already had one hidden cache. Its first opening now records a permanent regional objective and grants an additional Treasure Hunting bonus.
4. **Chart real terrain.** Regional charts now require four actual 16x16 map sectors; landmark metadata can no longer satisfy the chart requirement by itself.
5. **Claim regional mastery.** Surveying all four waymarks, opening the hidden cache, and charting the region grants a one-time regional keepsake, bonus gold, Exploration XP and Treasure Hunting XP. Five, ten and twenty mastered regions award Pathfinder, Trailblazer and Worldwalker achievements.

There are 20 deterministic `exploration_unique` keepsakes, one per surface wilderness region. They are trophy/treasure items rather than combat gear, so exploration rewards do not create mandatory power creep. If the backpack is full, the keepsake goes to the bank; if both are full, mastery remains claimable by inspecting a waymark after freeing a slot.

The Hunt guide and Atlas show exploration progress, clue state and the named mastery prize without exposing hidden-cache coordinates. Server-side discovery, cache visibility, first-open bonuses, chart validation and one-time reward issuance are covered by `ExplorationRewardChecks` in the normal world-probe suite.
''',encoding='utf-8')

print('exploration rewards patch applied')
