#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def replace(path,old,new,count=1):
    p=ROOT/path
    text=p.read_text(encoding='utf-8')
    found=text.count(old)
    if found!=count:
        raise SystemExit(f'{path}: expected {count} replacement target(s), found {found}')
    p.write_text(text.replace(old,new,count),encoding='utf-8')

def write(path,content):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content,encoding='utf-8')

write('src/Kairnfall.Core/EndgameLoops.cs',r'''namespace Kairnfall.Core;

public readonly record struct ReputationAward(int Added,long BonusGold,string Rank);

public static class EndgameLoops
{
    public const int ContractsPerBoard=3;
    public static readonly string[] Kinds=["elite","gather","craft","dungeon","boss","event"];
    private static readonly (string Faction,string City)[] Boards=
    [
        ("crown","dawnreach"),
        ("forge_clans","emberhold"),
        ("circle","thornhollow"),
        ("wardens","frostgate"),
        ("league","gloamport")
    ];
    public static IReadOnlyList<string> Factions=>Boards.Select(x=>x.Faction).ToArray();
    public static bool IsFaction(string faction)=>Boards.Any(x=>x.Faction==faction);
    public static bool IsContractId(string id)=>id.StartsWith("endgame:",StringComparison.Ordinal);
    public static long RotationDay(double time)=>Math.Max(0,(long)Math.Floor(Math.Max(0,time)/WorldTime.DayLength));
    public static double SecondsUntilRotation(double time)
    {
        double within=Math.Max(0,time)%WorldTime.DayLength;
        return Math.Max(0,WorldTime.DayLength-within);
    }
    private static int FactionIndex(string faction)
    {
        for(int i=0;i<Boards.Length;i++)if(Boards[i].Faction==faction)return i;
        throw new RuleException("Unknown faction contract board.");
    }
    private static int Pick(long seed,int count)
    {
        if(count<=0)throw new InvalidDataException("Task 22 endgame pool is empty.");
        long value=seed%count;if(value<0)value+=count;return (int)value;
    }
    public static string FactionName(string faction)=>faction switch
    {
        "crown"=>"Crown",
        "forge_clans"=>"Forge Clans",
        "circle"=>"Circle",
        "wardens"=>"Wardens",
        "league"=>"League",
        "wayfarers"=>"Wayfarers",
        _=>string.Join(' ',faction.Split('_',StringSplitOptions.RemoveEmptyEntries).Select(x=>char.ToUpperInvariant(x[0])+x[1..]))
    };
    public static string RankName(int reputation)=>Math.Clamp(reputation,0,1000) switch
    {
        >=1000=>"Exalted",
        >=750=>"Revered",
        >=500=>"Honored",
        >=250=>"Trusted",
        _=>"Known"
    };
    public static int NextRankThreshold(int reputation)=>Math.Clamp(reputation,0,1000) switch
    {
        <250=>250,<500=>500,<750=>750,<1000=>1000,_=>0
    };
    public static long RankRewardGold(int threshold)=>threshold switch{250=>250,500=>600,750=>1000,1000=>1600,_=>0};
    public static ReputationAward GrantReputation(Character player,string faction,int amount)
    {
        if(string.IsNullOrWhiteSpace(faction)||amount<=0)return new(0,0,RankName(player.Reputation.GetValueOrDefault(faction)));
        int before=Math.Clamp(player.Reputation.GetValueOrDefault(faction),0,1000);
        int after=Math.Min(1000,before+amount);player.Reputation[faction]=after;
        long bonus=0;
        if(IsFaction(faction))
        {
            foreach(var row in new[]{(250,"trusted"),(500,"honored"),(750,"revered"),(1000,"exalted")})
            {
                if(after<row.Item1)continue;
                string achievement=$"faction_{faction}_{row.Item2}";
                if(!player.Achievements.Add(achievement))continue;
                long gold=RankRewardGold(row.Item1);Items.Grant(player,gold);bonus+=gold;
            }
        }
        return new(after-before,bonus,RankName(after));
    }
    public static NpcDef Registrar(Catalog data,string faction)
    {
        string city=Boards.FirstOrDefault(x=>x.Faction==faction).City??"";
        if(city=="")throw new RuleException("Unknown faction contract board.");
        return data.Npcs.FirstOrDefault(x=>x.Zone==city&&x.Faction==faction&&x.Role=="guild_registrar")
            ??throw new InvalidDataException($"Faction {faction} has no guild registrar in {city}.");
    }
    private static ZoneDef HomeRegion(Catalog data,string faction)
    {
        string cityId=Boards.First(x=>x.Faction==faction).City;var city=data.Zone(cityId);
        var linked=city.Exits.Select(x=>data.Zone(x.Target)).Where(x=>x.Kind=="wilderness"&&x.Layer=="Surface")
            .OrderBy(x=>Math.Abs(x.Level-city.Level)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        if(linked.Length>0)return linked[0];
        return data.Zones.Where(x=>x.Kind=="wilderness"&&x.Layer=="Surface")
            .OrderBy(x=>Math.Abs(x.Level-city.Level)).ThenBy(x=>x.Id,StringComparer.Ordinal).First();
    }
    private static MobDef Elite(Catalog data,ZoneDef region,long day,int factionIndex)
    {
        var local=region.Species.Select(data.Mob).Where(x=>x.Elite&&!x.Boss).OrderBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        var pool=local.Length>0?local:data.Mobs.Where(x=>x.Elite&&!x.Boss).OrderBy(x=>Math.Abs(x.Level-region.Level)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        return pool[Pick(day+factionIndex*7,pool.Length)];
    }
    private static ResourceDef Resource(Catalog data,ZoneDef region,long day,int factionIndex)
    {
        var pool=region.Resources.Where(id=>data.Resources.Any(r=>r.Id==id)).Select(data.Resource)
            .OrderByDescending(x=>x.Requirement).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        if(pool.Length==0)pool=data.Resources.OrderBy(x=>Math.Abs(x.Requirement-region.Level)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        return pool[Pick(day+factionIndex*11,pool.Length)];
    }
    private static RecipeDef Recipe(Catalog data,string faction,ZoneDef region,long day,int factionIndex)
    {
        string city=Boards[factionIndex].City;
        var stations=data.Npcs.Where(x=>x.Zone==city&&x.Station!="").Select(x=>x.Station).Append("hand").ToHashSet(StringComparer.Ordinal);
        int target=Math.Max(35,region.Level+10);
        var pool=data.Recipes.Where(x=>stations.Contains(x.Station)&&data.Items.Any(i=>i.Id==x.Output&&i.Type!="quest"&&i.Type!="structure"))
            .OrderBy(x=>Math.Abs(x.Requirement-target)).ThenByDescending(x=>x.Requirement).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        if(pool.Length==0)pool=data.Recipes.OrderBy(x=>Math.Abs(x.Requirement-target)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        return pool[Pick(day+factionIndex*13,pool.Length)];
    }
    private static ZoneDef Dungeon(Catalog data,ZoneDef region,long day,int factionIndex,int offset)
    {
        int target=Math.Max(35,region.Level+15);
        var pool=data.Zones.Where(x=>x.Kind=="dungeon"&&x.Boss!="")
            .OrderBy(x=>Math.Abs(x.Level-target)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        return pool[Pick(day+factionIndex*17+offset,pool.Length)];
    }
    private static QuestDef Build(Catalog data,long day,string faction,string kind)
    {
        if(day<0||!IsFaction(faction)||!Kinds.Contains(kind,StringComparer.Ordinal))throw new RuleException("Unknown faction contract.");
        int fi=FactionIndex(faction);var registrar=Registrar(data,faction);var region=HomeRegion(data,faction);
        string target;int minimum;int gold;List<ObjectiveDef> objectives;string name;string story;
        switch(kind)
        {
            case "elite":
            {
                var elite=Elite(data,region,day,fi);target=elite.Id;minimum=Math.Clamp(Math.Max(35,elite.Level-3),1,100);gold=180+minimum*7;
                name="Elite Hunt: "+elite.Name;story=$"{FactionName(faction)} scouts have marked a dangerous veteran threat on established roads near {region.Name}.";
                objectives=[new(){Action="kill",Target=elite.Id,Count=2,Description=$"Defeat 2 {elite.Name}."}];break;
            }
            case "gather":
            {
                var resource=Resource(data,region,day,fi);target=resource.Item;var item=data.Item(resource.Item);minimum=Math.Clamp(Math.Max(35,resource.Requirement),1,100);gold=150+minimum*6;
                name="Supply Muster: "+item.Name;story=$"{FactionName(faction)} needs traceable materials gathered from the existing routes around {region.Name}.";
                objectives=[new(){Action="gather",Target=item.Id,Count=8,Description=$"Gather 8 {item.Name}."}];break;
            }
            case "craft":
            {
                var recipe=Recipe(data,faction,region,day,fi);target=recipe.Output;var item=data.Item(recipe.Output);minimum=Math.Clamp(Math.Max(35,recipe.Requirement),1,100);gold=170+minimum*7;
                name="Guild Order: "+item.Name;story=$"The {FactionName(faction)} workshops are issuing a rotating order through their existing {recipe.Station.Replace('_',' ')} services.";
                objectives=[new(){Action="craft",Target=item.Id,Count=Math.Max(1,Math.Min(3,recipe.Quantity==1?2:recipe.Quantity)),Description=$"Craft {Math.Max(1,Math.Min(3,recipe.Quantity==1?2:recipe.Quantity))} {item.Name}."}];break;
            }
            case "dungeon":
            {
                var dungeon=Dungeon(data,region,day,fi,0);target=dungeon.Id;var boss=data.Mob(dungeon.Boss);minimum=Math.Clamp(Math.Max(35,dungeon.Level-5),1,100);gold=240+minimum*8;
                name="Expedition Circuit: "+dungeon.Name;story=$"{FactionName(faction)} is rotating veteran expeditions through established dungeons instead of opening new territory.";
                objectives=[new(){Action="explore",Target=dungeon.Id,Count=1,Description="Enter "+dungeon.Name+"."},new(){Action="boss",Target=boss.Id,Count=1,Description="Defeat "+boss.Name+"."}];break;
            }
            case "boss":
            {
                var dungeon=Dungeon(data,region,day,fi,5);var boss=data.Mob(dungeon.Boss);target=boss.Id;minimum=Math.Clamp(Math.Max(35,boss.Level-5),1,100);gold=260+minimum*9;
                name="Boss Writ: "+boss.Name;story=$"A {FactionName(faction)} writ calls experienced adventurers back to {dungeon.Name} to contain its known guardian.";
                objectives=[new(){Action="boss",Target=boss.Id,Count=1,Description="Defeat "+boss.Name+"."}];break;
            }
            case "event":
                target="public";minimum=Math.Clamp(Math.Max(35,region.Level+10),1,100);gold=220+minimum*7;
                name="Regional Response";story=$"{FactionName(faction)} is assigning veterans to complete one public event anywhere on the established world routes.";
                objectives=[new(){Action="event_complete",Target="*",Count=1,Description="Complete a public world event as an eligible contributor."}];break;
            default:throw new RuleException("Unknown faction contract kind.");
        }
        string id=$"endgame:{day}:{faction}:{kind}:{target}";
        int rep=kind switch{"elite"=>22,"gather"=>18,"craft"=>20,"dungeon"=>28,"boss"=>30,"event"=>24,_=>20};
        return new(){Id=id,Name=name,Giver=registrar.Id,Story=story,Category="endgame",Faction=faction,MinimumLevel=minimum,Objectives=objectives,Gold=gold+rep,Repeatable=true};
    }
    public static QuestDef ForDay(Catalog data,long day,string faction,string kind)=>Build(data,day,faction,kind);
    public static IReadOnlyList<QuestDef> Today(Catalog data,double time,string faction)
    {
        if(!IsFaction(faction))return [];
        long day=RotationDay(time);int start=Pick(day+FactionIndex(faction)*3,Kinds.Length);
        int[] slots=[start,(start+2)%Kinds.Length,(start+3)%Kinds.Length];
        return slots.Select(i=>Build(data,day,faction,Kinds[i])).ToArray();
    }
    public static IReadOnlyList<QuestDef> Today(Catalog data,double time)=>Factions.SelectMany(f=>Today(data,time,f)).ToArray();
    public static QuestDef ResolveQuest(Catalog data,string id)
    {
        if(!IsContractId(id))return data.Quest(id);
        var parts=id.Split(new[]{':'},5,StringSplitOptions.None);
        if(parts.Length!=5||parts[0]!="endgame"||!long.TryParse(parts[1],out long day))throw new RuleException("Unknown faction contract.");
        var expected=Build(data,day,parts[2],parts[3]);
        if(!string.Equals(expected.Id,id,StringComparison.Ordinal))throw new RuleException("Unknown faction contract.");
        return expected;
    }
    public static int ReputationReward(QuestDef quest)
    {
        if(!IsContractId(quest.Id))return 0;
        var parts=quest.Id.Split(new[]{':'},5,StringSplitOptions.None);
        return parts[3] switch{"elite"=>22,"gather"=>18,"craft"=>20,"dungeon"=>28,"boss"=>30,"event"=>24,_=>0};
    }
    public static string ContractKind(QuestDef quest)
    {
        if(!IsContractId(quest.Id))return "";
        var parts=quest.Id.Split(new[]{':'},5,StringSplitOptions.None);return parts.Length==5?parts[3]:"";
    }
    public static void Advance(QuestDef quest,QuestProgress progress,string action,string target,int amount=1)
    {
        if(amount<1)return;
        while(progress.Counts.Count<quest.Objectives.Count)progress.Counts.Add(0);
        for(int i=0;i<quest.Objectives.Count;i++)
        {
            var objective=quest.Objectives[i];
            if(objective.Action==action&&(objective.Target=="*"||objective.Target==target))progress.Counts[i]=Math.Min(objective.Count,progress.Counts[i]+amount);
        }
        progress.Complete=quest.Objectives.Select((objective,i)=>progress.Counts[i]>=objective.Count).All(x=>x);
    }
}
''')

write('src/Kairnfall.Core/RealmEndgame.cs',r'''namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private QuestDef CurrentEndgameContract(string id)
        =>EndgameLoops.Today(Data,State.Time).FirstOrDefault(x=>x.Id==id)??throw new RuleException("That faction contract is not in the current rotation.");

    private string AcceptEndgame(Character player,string id)
    {
        var quest=CurrentEndgameContract(id);var registrar=Data.Npc(quest.Giver);Near(player,registrar.Zone,registrar.Position,3);
        Need(Progression.PlayerLevel(player)>=quest.MinimumLevel,$"Requires character level {quest.MinimumLevel}.");
        Need(!player.Quests.ContainsKey(id),"You already accepted this faction contract.");
        Need(!player.CompletedQuests.Contains(id),"This faction contract was already claimed for this rotation.");
        Need(player.Quests.Keys.Count(EndgameLoops.IsContractId)<6,"Finish or abandon an active faction contract before taking another.");
        player.Quests[id]=new(){Counts=Enumerable.Repeat(0,quest.Objectives.Count).ToList()};
        return $"Accepted: {quest.Name} · {EndgameLoops.FactionName(quest.Faction)} {EndgameLoops.ReputationReward(quest)} reputation.";
    }

    private string ClaimEndgame(Character player,string id)
    {
        Need(EndgameLoops.IsContractId(id),"Unknown faction contract.");var quest=EndgameLoops.ResolveQuest(Data,id);var registrar=Data.Npc(quest.Giver);Near(player,registrar.Zone,registrar.Position,3);
        Need(player.Quests.TryGetValue(id,out var progress)&&progress.Complete,"This faction contract is not complete.");
        Need(!player.CompletedQuests.Contains(id),"This faction contract reward was already claimed.");
        Items.Grant(player,quest.Gold);
        var reputation=EndgameLoops.GrantReputation(player,quest.Faction,EndgameLoops.ReputationReward(quest));
        player.CompletedQuests.Add(id);player.Quests.Remove(id);
        int completed=player.CompletedQuests.Count(EndgameLoops.IsContractId);
        if(completed>=1)player.Achievements.Add("endgame_contract_1");
        if(completed>=10)player.Achievements.Add("endgame_contract_10");
        if(completed>=50)player.Achievements.Add("endgame_contract_50");
        string milestone=reputation.BonusGold>0?$" Rank milestone bonus: {reputation.BonusGold} gold.":"";
        return $"Completed: {quest.Name} · {quest.Gold} gold · +{reputation.Added} {EndgameLoops.FactionName(quest.Faction)} reputation ({reputation.Rank})."+milestone;
    }

    private string AbandonEndgame(Character player,string id)
    {
        Need(EndgameLoops.IsContractId(id)&&player.Quests.ContainsKey(id),"Faction contract not active.");
        player.Quests.Remove(id);return "Faction contract abandoned. No reward was granted.";
    }
}
''')

replace('src/Kairnfall.Core/RealmEngine.cs',
'''            case "accept_quest": return AcceptQuest(p,c.Item);\n            case "claim_quest": return ClaimQuest(p,c.Item);''',
'''            case "accept_quest": return AcceptQuest(p,c.Item);\n            case "claim_quest": return ClaimQuest(p,c.Item);\n            case "endgame_accept": return AcceptEndgame(p,c.Target);\n            case "endgame_claim": return ClaimEndgame(p,c.Target);\n            case "endgame_abandon": return AbandonEndgame(p,c.Target);''')
replace('src/Kairnfall.Core/RealmEngine.cs',
'''        foreach(var entry in p.Quests)\n        {\n            var q=Data.Quest(entry.Key); var progress=entry.Value;\n            for(int i=0;i<q.Objectives.Count;i++)\n            {\n                var o=q.Objectives[i];\n                if(o.Action==action&&(o.Target=="*"||o.Target==target)) progress.Counts[i]=Math.Min(o.Count,progress.Counts[i]+amount);\n            }\n            progress.Complete=q.Objectives.Select((o,i)=>progress.Counts[i]>=o.Count).All(x=>x);\n        }''',
'''        foreach(var entry in p.Quests)\n        {\n            var q=EndgameLoops.ResolveQuest(Data,entry.Key);\n            EndgameLoops.Advance(q,entry.Value,action,target,amount);\n        }''')
replace('src/Kairnfall.Core/RealmCombat.cs','var q=Data.Quest(entry.Key);','var q=EndgameLoops.ResolveQuest(Data,entry.Key);')
replace('src/Kairnfall.Core/RealmEconomy.cs',
'''        p.Reputation[quest.Faction]=Math.Min(1000,p.Reputation.GetValueOrDefault(quest.Faction)+10); Progress(p,"quest",id);''',
'''        EndgameLoops.GrantReputation(p,quest.Faction,10); Progress(p,"quest",id);''')
replace('src/Kairnfall.Core/RealmEvents.cs',
'''            player.Reputation["wayfarers"] = Math.Min(1000, player.Reputation.GetValueOrDefault("wayfarers") + 2 * tier);\n            player.PublicEventsCompleted++;''',
'''            EndgameLoops.GrantReputation(player,"wayfarers",2*tier);\n            Progress(player,"event_complete",value.Kind);\n            player.PublicEventsCompleted++;''')

replace('client/Scripts/GameRoot.Panels.cs','var quest = Data.Quest(entry.Key); listing.AddChild', 'var quest = EndgameLoops.ResolveQuest(Data, entry.Key); listing.AddChild')
replace('client/Scripts/GameRoot.Panels.cs',
'''            var selected = Data.Quests.FirstOrDefault(x => x.Id == selectedQuest && Snapshot.Self.Quests.ContainsKey(x.Id));\n            selected ??= Snapshot.Self.Quests.Count > 0 ? Data.Quest(Snapshot.Self.Quests.Keys.First()) : null;''',
'''            QuestDef? selected = Snapshot.Self.Quests.ContainsKey(selectedQuest) ? EndgameLoops.ResolveQuest(Data, selectedQuest) : null;\n            selected ??= Snapshot.Self.Quests.Count > 0 ? EndgameLoops.ResolveQuest(Data, Snapshot.Self.Quests.Keys.First()) : null;''')
replace('client/Scripts/GameRoot.Panels.cs',
'''            detail.AddChild(Ui.Label($"Reward: {selected.Gold} gold" + (selected.Reward == "" ? "" : " · " + Data.Item(selected.Reward).Name), 16, Ui.Success));\n            detail.AddChild(Ui.Label("Return to " + giver.Name + " in " + Data.Zone(giver.Zone).Name + ".", 15, Ui.Muted, true));\n            var questId = selected.Id;\n            detail.AddChild(Ui.Button("Mark quest giver", () => MarkDestination(giver.Zone, giver.Position)));\n            if (progress.Complete) detail.AddChild(Ui.Button("Claim reward", () => Send("claim_quest", item: questId), !NearNpc(giver)));''',
'''            bool endgame = EndgameLoops.IsContractId(selected.Id);\n            string repReward=endgame?$" · {EndgameLoops.ReputationReward(selected)} {EndgameLoops.FactionName(selected.Faction)} reputation":"";\n            detail.AddChild(Ui.Label($"Reward: {selected.Gold} gold" + (selected.Reward == "" ? "" : " · " + Data.Item(selected.Reward).Name) + repReward, 16, Ui.Success));\n            detail.AddChild(Ui.Label("Return to " + giver.Name + " in " + Data.Zone(giver.Zone).Name + ".", 15, Ui.Muted, true));\n            var questId = selected.Id;\n            detail.AddChild(Ui.Button("Mark quest giver", () => MarkDestination(giver.Zone, giver.Position)));\n            if (progress.Complete) detail.AddChild(Ui.Button("Claim reward", () => endgame?Send("endgame_claim",target:questId):Send("claim_quest", item:questId), !NearNpc(giver)));\n            if(endgame) detail.AddChild(Ui.Button("Abandon contract",()=>Send("endgame_abandon",target:questId)));''')
replace('client/Scripts/GameRoot.Panels.cs',
'''            if (offers.GetChildCount() == 0) offers.AddChild(Ui.Label("No further work is available here at present.", 16, Ui.Muted, true));''',
'''            if(npc.Role=="guild_registrar"&&EndgameLoops.IsFaction(npc.Faction))\n            {\n                int reputation=Snapshot.Self.Reputation.GetValueOrDefault(npc.Faction);\n                offers.AddChild(Ui.Label($"Daily faction contracts · {EndgameLoops.RankName(reputation)} {reputation}/1000",20,Ui.Gold));\n                foreach(var contract in EndgameLoops.Today(Data,Snapshot.Time,npc.Faction))\n                {\n                    bool active=Snapshot.Self.Quests.TryGetValue(contract.Id,out var progress);\n                    if(Snapshot.Self.CompletedQuests.Contains(contract.Id))continue;\n                    bool levelReady=Progression.PlayerLevel(Snapshot.Self)>=contract.MinimumLevel;\n                    var card=new PanelContainer();offers.AddChild(card);var body=Ui.Column(card);\n                    body.AddChild(Ui.Label(contract.Name+" · "+Ui.Words(EndgameLoops.ContractKind(contract)),19,Ui.Gold));\n                    body.AddChild(Ui.Label(contract.Story,14,Ui.Text,true));\n                    foreach(var objective in contract.Objectives)body.AddChild(Ui.Label("• "+objective.Description,14,Ui.Muted,true));\n                    if(!levelReady)body.AddChild(Ui.Label($"Requires character level {contract.MinimumLevel}.",14,Ui.Danger));\n                    body.AddChild(Ui.Label($"Reward: {contract.Gold} gold · {EndgameLoops.ReputationReward(contract)} reputation",14,Ui.Success));\n                    if(!active)body.AddChild(Ui.Button("Accept faction contract",()=>Send("endgame_accept",target:contract.Id),!NearNpc(npc)||!levelReady));\n                    else if(progress!.Complete)body.AddChild(Ui.Button("Claim faction reward",()=>Send("endgame_claim",target:contract.Id),!NearNpc(npc)));\n                    else body.AddChild(Ui.Button("Track contract",()=>{selectedQuest=contract.Id;OpenPage("Quests");}));\n                }\n            }\n            if (offers.GetChildCount() == 0) offers.AddChild(Ui.Label("No further work is available here at present.", 16, Ui.Muted, true));''')
replace('client/Scripts/GameRoot.Panels.cs',
'''            int reputation = Snapshot.Self.Reputation.GetValueOrDefault(faction); rows.AddChild(Ui.Label(Ui.Words(faction) + " · " + reputation + "/1000", 17)); var bar = Ui.Bar(new Color("94aa7b"), 650); bar.MaxValue = 1000; bar.Value = reputation; rows.AddChild(bar);''',
'''            int reputation = Snapshot.Self.Reputation.GetValueOrDefault(faction); int next=EndgameLoops.NextRankThreshold(reputation); string nextText=next>0?$" · next rank {next}":" · maximum rank"; rows.AddChild(Ui.Label(EndgameLoops.FactionName(faction) + " · " + EndgameLoops.RankName(reputation) + " · " + reputation + "/1000" + nextText, 17)); var bar = Ui.Bar(new Color("94aa7b"), 650); bar.MaxValue = 1000; bar.Value = reputation; rows.AddChild(bar);''')
replace('client/Scripts/GameRoot.Panels.cs',
'''        rows.AddChild(Ui.Label($"Completed quests: {Snapshot.Self.CompletedQuests.Count}\\nDiscovered waystones: {Snapshot.Self.Waypoints.Count}", 17, Ui.Muted));''',
'''        rows.AddChild(Ui.Label("Veteran faction boards",24,Ui.Gold));\n        foreach(string faction in EndgameLoops.Factions)\n        {\n            int active=Snapshot.Self.Quests.Keys.Count(id=>EndgameLoops.IsContractId(id)&&EndgameLoops.ResolveQuest(Data,id).Faction==faction);\n            int claimed=EndgameLoops.Today(Data,Snapshot.Time,faction).Count(q=>Snapshot.Self.CompletedQuests.Contains(q.Id));\n            rows.AddChild(Ui.Label($"{EndgameLoops.FactionName(faction)} · {active} active · {claimed}/{EndgameLoops.ContractsPerBoard} claimed this rotation",16,Ui.Muted));\n        }\n        rows.AddChild(Ui.Label($"Completed quests: {Snapshot.Self.CompletedQuests.Count}\\nDiscovered waystones: {Snapshot.Self.Waypoints.Count}", 17, Ui.Muted));''')

write('tools/world_probe/Task22EndgameChecks.cs',r'''using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Kairnfall.Core;

internal static class Task22EndgameChecks
{
    [ModuleInitializer]
    internal static void VerifyTask22Endgame()
    {
        const string path="content/catalog.json";
        if(!File.Exists(path))throw new InvalidDataException("Task 22 checks require content/catalog.json.");
        var data=Catalog.Load(path);var failures=new List<string>();int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Check(string name,Action body){try{body();passed++;Console.WriteLine("PASS TASK22 ENDGAME: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL TASK22 ENDGAME: "+name+": "+e.Message);}}
        void MaxLevel(Character p){p.SkillXp["exploration"]=Progression.PlayerThreshold(100);}
        GameCommand Command(Character p,string kind,string target,string? request=null)=>new(){Kind=kind,Target=target,Sequence=p.LastAction+1,RequestId=request??Guid.NewGuid().ToString("N")};

        Check("canonical faction boards rotate all six loop families without expanding the world",()=>
        {
            var surface=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").ToArray();
            Need(surface.Length==20&&surface.Sum(z=>(long)z.Width*z.Height)==2_048_000,"Task 22 changed the overworld footprint.");
            Need(EndgameLoops.Factions.SequenceEqual(new[]{"crown","forge_clans","circle","wardens","league"}),"Faction boards no longer match the five authored city factions.");
            foreach(string faction in EndgameLoops.Factions)
            {
                var registrar=EndgameLoops.Registrar(data,faction);Need(registrar.Faction==faction&&registrar.Role=="guild_registrar","Faction board is not anchored to its existing registrar.");
                var kinds=new HashSet<string>();
                for(int day=0;day<6;day++)
                {
                    var today=EndgameLoops.Today(data,day*WorldTime.DayLength+1,faction);Need(today.Count==3&&today.Select(q=>q.Id).Distinct().Count()==3,"Daily board must contain exactly three unique contracts.");
                    foreach(var q in today){kinds.Add(EndgameLoops.ContractKind(q));Need(q.Faction==faction&&q.Giver==registrar.Id&&q.MinimumLevel>=35,"Generated contract escaped its faction/endgame gate.");Need(EndgameLoops.ResolveQuest(data,q.Id).Id==q.Id,"Generated contract cannot be deterministically resolved.");}
                }
                Need(kinds.SetEquals(EndgameLoops.Kinds),"Six-day rotation does not cover elite/gather/craft/dungeon/boss/event loops for "+faction);
            }
        });

        Check("all contract objective families use the shared authoritative quest progress semantics",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task22-families","Loop Auditor","vanguard",new());MaxLevel(p);
            foreach(string kind in EndgameLoops.Kinds)
            {
                var quest=EndgameLoops.ForDay(data,0,"crown",kind);var progress=new QuestProgress{Counts=Enumerable.Repeat(0,quest.Objectives.Count).ToList()};p.Quests[quest.Id]=progress;
                foreach(var objective in quest.Objectives)EndgameLoops.Advance(quest,progress,objective.Action,objective.Target=="*"?"fixture":objective.Target,objective.Count);
                Need(progress.Complete,"Contract family did not complete through authoritative objective progress: "+kind);p.Quests.Remove(quest.Id);
            }
        });

        Check("accept and claim are proximity/level gated and replay-safe",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task22-authority","Faction Auditor","vanguard",new());MaxLevel(p);string faction="crown";var registrar=EndgameLoops.Registrar(data,faction);var quest=EndgameLoops.Today(data,realm.State.Time,faction)[0];
            var accept=Command(p,"endgame_accept",quest.Id);var far=realm.Execute(p.Id,accept);Need(!far.Ok,"Remote faction contract acceptance bypassed registrar proximity.");
            p.Zone=registrar.Zone;p.Position=registrar.Position;accept=Command(p,"endgame_accept",quest.Id);var accepted=realm.Execute(p.Id,accept);Need(accepted.Ok,accepted.Message);Need(p.Quests.ContainsKey(quest.Id),"Accepted faction contract was not persisted in quest state.");
            var early=realm.Execute(p.Id,Command(p,"endgame_claim",quest.Id));Need(!early.Ok,"Incomplete faction contract was claimable.");
            var progress=p.Quests[quest.Id];foreach(var objective in quest.Objectives)EndgameLoops.Advance(quest,progress,objective.Action,objective.Target=="*"?"fixture":objective.Target,objective.Count);Need(progress.Complete,"Fixture contract did not complete.");
            long gold=p.Gold;int reputation=p.Reputation.GetValueOrDefault(faction);string request=Guid.NewGuid().ToString("N");var claim=Command(p,"endgame_claim",quest.Id,request);var claimed=realm.Execute(p.Id,claim);Need(claimed.Ok,claimed.Message);
            Need(p.Gold==gold+quest.Gold&&p.Reputation.GetValueOrDefault(faction)==reputation+EndgameLoops.ReputationReward(quest),"Faction claim reward was not exact.");Need(!p.Quests.ContainsKey(quest.Id)&&p.CompletedQuests.Contains(quest.Id),"Faction claim did not atomically retire the active contract.");
            long after=p.Gold;int repAfter=p.Reputation.GetValueOrDefault(faction);var replay=realm.Execute(p.Id,claim);Need(replay.Ok&&p.Gold==after&&p.Reputation.GetValueOrDefault(faction)==repAfter,"Request replay duplicated faction rewards.");
            var second=realm.Execute(p.Id,Command(p,"endgame_claim",quest.Id));Need(!second.Ok&&p.Gold==after&&p.Reputation.GetValueOrDefault(faction)==repAfter,"Second claim duplicated faction rewards.");
        });

        Check("active contract progress survives save roundtrip and remains resolvable after rotation",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task22-persist","Persistent Veteran","vanguard",new());MaxLevel(p);var registrar=EndgameLoops.Registrar(data,"circle");p.Zone=registrar.Zone;p.Position=registrar.Position;var quest=EndgameLoops.Today(data,realm.State.Time,"circle")[0];
            Need(realm.Execute(p.Id,Command(p,"endgame_accept",quest.Id)).Ok,"Could not accept persistence fixture contract.");var progress=p.Quests[quest.Id];var first=quest.Objectives[0];EndgameLoops.Advance(quest,progress,first.Action,first.Target=="*"?"fixture":first.Target,Math.Max(1,first.Count-1));
            var loaded=new RealmEngine(data,Wire.Copy(realm.State));var restored=loaded.Player(p.Id);Need(restored.Quests.ContainsKey(quest.Id),"Active faction contract was lost on save roundtrip.");Need(restored.Quests[quest.Id].Counts.SequenceEqual(progress.Counts),"Faction contract progress changed on save roundtrip.");
            loaded.State.Time+=WorldTime.DayLength*2;Need(EndgameLoops.ResolveQuest(data,quest.Id).Id==quest.Id,"Accepted contract became unresolvable after rotation rollover.");loaded.Tick(.1);
        });

        Check("reputation rank milestone gold is idempotent and persisted through the same claim",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task22-rank","Trusted Candidate","vanguard",new());MaxLevel(p);string faction="league";p.Reputation[faction]=240;var registrar=EndgameLoops.Registrar(data,faction);p.Zone=registrar.Zone;p.Position=registrar.Position;
            var quest=EndgameLoops.Today(data,realm.State.Time,faction).First(q=>EndgameLoops.ReputationReward(q)>=18);Need(realm.Execute(p.Id,Command(p,"endgame_accept",quest.Id)).Ok,"Could not accept rank fixture.");var progress=p.Quests[quest.Id];foreach(var objective in quest.Objectives)EndgameLoops.Advance(quest,progress,objective.Action,objective.Target=="*"?"fixture":objective.Target,objective.Count);
            long before=p.Gold;var result=realm.Execute(p.Id,Command(p,"endgame_claim",quest.Id));Need(result.Ok,result.Message);Need(p.Reputation[faction]>=250&&p.Achievements.Contains("faction_league_trusted"),"Trusted rank milestone was not recorded.");Need(p.Gold==before+quest.Gold+EndgameLoops.RankRewardGold(250),"Trusted rank milestone gold was not exact.");
            long after=p.Gold;var award=EndgameLoops.GrantReputation(p,faction,1);Need(award.BonusGold==0&&p.Gold==after,"Reputation update duplicated an already-earned rank reward.");
            var copy=Wire.Copy(realm.State);Need(copy.Characters[p.Id].Achievements.Contains("faction_league_trusted")&&copy.Characters[p.Id].Reputation[faction]==p.Reputation[faction],"Rank milestone did not persist in realm state.");
        });

        Console.WriteLine($"TASK22 ENDGAME LOOPS: {passed} checks passed; {failures.Count} failed.");
        if(failures.Count>0)throw new InvalidDataException("Task 22 endgame regression failed: "+string.Join(" | ",failures));
    }
}
''')

write('docs/TASK22_ENDGAME_LOOPS.md',r'''# Task 22 — factions, reputation, and repeatable endgame loops

Task 22 enriches the existing Kairnfall world rather than expanding its footprint. The five authored city factions—Crown, Forge Clans, Circle, Wardens, and League—now expose deterministic veteran contract boards through their existing guild registrars.

## Daily rotation

Each faction offers three contracts per realm day. Across the rotation the board covers six existing gameplay systems: elite hunts, gathering supply musters, crafting orders, dungeon expeditions, boss writs, and public-event response. Targets are selected deterministically from existing creatures, resources, recipes, dungeons, bosses, events, cities, and wilderness regions. No new overworld region, dungeon footprint, or arbitrary faction is introduced.

Contract identifiers contain the rotation day and canonical target. The server regenerates and validates the expected contract before accepting it, so a client cannot forge targets or rewards. Accepted contracts use the existing persisted quest-progress dictionary; completed contract identifiers use the existing persisted completed-quest set. This keeps old saves compatible while making acceptance, progress, claims, restart recovery, and duplicate prevention server-authoritative.

## Reputation and rewards

Faction contracts grant 18–30 reputation depending on loop type, plus level-scaled gold. Reputation remains capped at 1000 and continues to feed the existing merchant pricing system. Canonical city factions now have persisted rank milestones at 250 Trusted, 500 Honored, 750 Revered, and 1000 Exalted reputation. Each milestone records an achievement and grants its gold bonus exactly once; the achievement is the idempotency key, so later reputation changes cannot duplicate the reward.

Normal authored quests and public events still use the same reputation store. Task 22 routes reputation changes through the shared helper so caps remain consistent; Wayfarer event reputation remains supported without inventing a new city board.

## Authority and anti-duplication

Faction contracts can only be accepted and claimed near the matching existing guild registrar and after the server verifies the character-level gate. Claims are atomic under `RealmEngine.Execute`: gold, reputation, rank milestones, completed state, and active-contract removal roll back together on any rule failure. Existing request receipts make network retries idempotent, while the completed contract identifier prevents a second fresh claim for the same daily contract.

Accepted progress survives realm-state roundtrips. A contract accepted before a daily rotation can still be resolved and completed afterward because its identifier contains the original deterministic rotation day and target.

## Player presentation

Guild registrar dialogue now shows the current faction board, objectives, level gate, gold, and reputation reward. Active veteran contracts appear in the normal quest tracker and can be claimed or abandoned there. The Achievements/Factions page now shows reputation rank, next threshold, and active/claimed rotation status for all five canonical boards.

## Automated coverage

`tools/world_probe/Task22EndgameChecks.cs` verifies:

- the unchanged 20-region / 2,048,000-tile Surface wilderness footprint;
- all five boards are anchored to existing faction guild registrars;
- six-day rotation covers elite, gather, craft, dungeon, boss, and event loops;
- generated contract IDs resolve deterministically;
- shared objective progress works for all six families;
- remote acceptance, incomplete claiming, duplicate claiming, and replay duplication fail safely;
- active progress survives save/reload and rotation rollover;
- faction-rank rewards are exact, persisted, and idempotent.
''')
print('Task 22 source patch staged successfully.')
