#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def edit(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"anchor missing in {path}: {old[:180]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")

def write(path: str, text: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

edit(
    "content_src/quests.py",
    """def add(data,ident,name,giver,story,objectives,category='side',prerequisite='',reward='',gold=30,faction='wayfarers',repeatable=False):\n    data['quests'].append(dict(id=ident,name=name,giver=giver,story=story,objectives=objectives,category=category,prerequisite=prerequisite,reward=reward,gold=gold,faction=faction,repeatable=repeatable))\n""",
    """def add(data,ident,name,giver,story,objectives,category='side',prerequisite='',reward='',gold=30,faction='wayfarers',repeatable=False,minimum=1):\n    data['quests'].append(dict(id=ident,name=name,giver=giver,story=story,objectives=objectives,category=category,prerequisite=prerequisite,reward=reward,gold=gold,faction=faction,repeatable=repeatable,minimumLevel=minimum))\n"""
)

edit(
    "content_src/quests.py",
    """            objectives,'regional',reward='parchment',gold=70+level*4)\n""",
    """            objectives,'regional',reward='parchment',gold=70+level*4,minimum=max(1,level-5))\n"""
)

edit(
    "content_src/quests.py",
    """            [objective('explore',region_id),objective('survey',region_id+'_'+suffix,1,'Recheck '+label+' in '+region_name+'.'),objective('gather',resource['item'],2,'Gather 2 '+resource['item'].replace('_',' ')+' in '+region_name+'.')],\n            'repeatable',gold=50+level*3,repeatable=True)\n    for i,(dungeon_id,name,parent,layer,biome,boss_id) in enumerate(DUNGEONS[:10]):\n        giver=CITIES[i%5][0]+'_guild_registrar'\n        add(data,'delve_'+dungeon_id,'Guild Delve: '+name,giver,'The guild will reward a verified return from '+name+'. Defeat its guardian after accepting this contract.',[objective('boss',boss_id)],'repeatable',gold=100+i*35,repeatable=True)\n""",
    """            [objective('explore',region_id),objective('survey',region_id+'_'+suffix,1,'Recheck '+label+' in '+region_name+'.'),objective('gather',resource['item'],2,'Gather 2 '+resource['item'].replace('_',' ')+' in '+region_name+'.')],\n            'repeatable',gold=50+level*3,repeatable=True,minimum=max(1,level-5))\n\n    # Mid/late-game guild circuits give the six optional dungeons a narrative hook\n    # instead of leaving them as disconnected boss rooms.\n    add(data,'veteran_deepways_circuit','The Roads the Ledger Missed','dawnreach_guild_registrar',\n        'Two Deepway sites never entered the capital ledger. Verify both routes and their guardians before the guild treats them as safe expedition destinations.',\n        [objective('explore','drowned_cistern'),objective('boss','saltjaw'),\n         objective('explore','glasswing_grotto'),objective('boss','glasswing')],\n        'regional','main_18','rune_wanderer_3',650,'wayfarers',minimum=40)\n    add(data,'veteran_umbral_circuit','Four Seals of the Umbral Roads','emberhold_guild_registrar',\n        'The Umbral Crossroads opens onto four sealed routes outside the main road. Clear all four guardians so later expeditions have an established return path.',\n        [objective('explore','regents_tomb'),objective('boss','dune_regent'),\n         objective('explore','rime_abbey'),objective('boss','rime_abbess'),\n         objective('explore','cinder_barracks'),objective('boss','cinder_marshal'),\n         objective('explore','reef_sanctum'),objective('boss','reef_colossus')],\n        'regional','main_20','rune_warding_4',1400,'wayfarers',minimum=50)\n\n    repeatable_gate={\n      'broken_mill':'main_04','bell_crypt':'main_07','silken_tollhouse':'main_09','root_court':'main_10',\n      'sunken_foundry':'main_12','watchers_nest':'main_13','drowned_cistern':'veteran_deepways_circuit',\n      'unmoored_vault':'main_16','ivory_archive':'main_18','glasswing_grotto':'veteran_deepways_circuit',\n      'regents_tomb':'veteran_umbral_circuit','chorus_caverns':'main_19','winterhorn_pass':'main_15',\n      'rime_abbey':'veteran_umbral_circuit','cinder_barracks':'veteran_umbral_circuit',\n      'reef_sanctum':'veteran_umbral_circuit','hollow_throne':'main_21',\n      'prism_observatory':'main_23','unwritten_library':'main_24','engine_of_dawn':'main_25'\n    }\n    # Every dungeon has a daily expedition. High-level delves require a relic\n    # sample as well as the boss, so the loop also touches gathering/crafting supply.\n    for i,(dungeon_id,name,parent,layer,biome,boss_id) in enumerate(DUNGEONS):\n        boss=next(m for m in data['mobs'] if m['id']==boss_id)\n        giver=('dawnreach' if layer=='Aether Rift' else 'emberhold' if layer=='Umbral Depths' else CITIES[i%5][0])+'_guild_registrar'\n        objectives=[objective('explore',dungeon_id),objective('boss',boss_id)]\n        if boss['level']>=50:\n            objectives.append(objective('gather','relic_shard',1,'Recover one relic shard during the expedition.'))\n        add(data,'delve_'+dungeon_id,'Guild Expedition: '+name,giver,\n            'The guild will reward a verified return from '+name+'. Enter the site after accepting this contract, defeat its guardian, and bring back field evidence from veteran routes.',\n            objectives,'repeatable',repeatable_gate[dungeon_id],gold=80+boss['level']*6,repeatable=True,minimum=max(1,boss['level']-5))\n"""
)

edit(
    "src/Kairnfall.Core/Models.cs",
    """    public string Faction { get; set; } = \"wayfarers\";\n    public List<ObjectiveDef> Objectives { get; set; } = [];\n""",
    """    public string Faction { get; set; } = \"wayfarers\";\n    public int MinimumLevel { get; set; } = 1;\n    public List<ObjectiveDef> Objectives { get; set; } = [];\n"""
)

edit(
    "src/Kairnfall.Core/Catalog.cs",
    """            if(!npcs.Contains(quest.Giver)||quest.Objectives.Count==0||quest.Objectives.Any(x=>x.Count<1)||quest.Gold<0) errors.Add($\"Invalid quest {quest.Id}\");\n""",
    """            if(!npcs.Contains(quest.Giver)||quest.Objectives.Count==0||quest.Objectives.Any(x=>x.Count<1)||quest.Gold<0||quest.MinimumLevel<1||quest.MinimumLevel>Progression.PlayerCap) errors.Add($\"Invalid quest {quest.Id}\");\n"""
)

edit(
    "src/Kairnfall.Core/RealmEconomy.cs",
    """        Need(!p.Quests.ContainsKey(id),\"You already accepted this quest.\");\n        Need(quest.Repeatable||!p.CompletedQuests.Contains(id),\"You already completed this quest.\");\n        Need(quest.Prerequisite==\"\"||p.CompletedQuests.Contains(quest.Prerequisite),\"Complete the previous quest first.\");\n""",
    """        Need(!p.Quests.ContainsKey(id),\"You already accepted this quest.\");\n        Need(quest.Repeatable||!p.CompletedQuests.Contains(id),\"You already completed this quest.\");\n        int playerLevel=Progression.PlayerLevel(p);\n        Need(playerLevel>=quest.MinimumLevel,$\"Requires character level {quest.MinimumLevel}. You are level {playerLevel}.\");\n        Need(quest.Prerequisite==\"\"||p.CompletedQuests.Contains(quest.Prerequisite),\"Complete the previous quest first.\");\n"""
)

edit(
    "src/Kairnfall.Core/JourneyProgression.cs",
    """    public static JourneyQuestLead? LocalQuest(Catalog data,Character player)\n    {\n        foreach(var quest in data.Quests\n            .Where(q=>!player.Quests.ContainsKey(q.Id)&&!player.CompletedQuests.Contains(q.Id)\n                &&(q.Prerequisite==\"\"||player.CompletedQuests.Contains(q.Prerequisite)))\n            .OrderBy(QuestPriority)\n            .ThenBy(q=>q.Id,StringComparer.Ordinal))\n        {\n            var giver=data.Npc(quest.Giver);\n            if(giver.Zone==player.Zone)return new(quest.Id,quest.Name,giver.Id,giver.Name,giver.Zone);\n        }\n        return null;\n    }\n""",
    """    public static JourneyQuestLead? LocalQuest(Catalog data,Character player,double now=0)\n    {\n        int level=Progression.PlayerLevel(player);\n        foreach(var quest in data.Quests\n            .Where(q=>!player.Quests.ContainsKey(q.Id)\n                &&(q.Repeatable||!player.CompletedQuests.Contains(q.Id))\n                &&level>=q.MinimumLevel\n                &&(q.Prerequisite==\"\"||player.CompletedQuests.Contains(q.Prerequisite))\n                &&(!q.Repeatable||player.Cooldowns.GetValueOrDefault(\"quest:\"+q.Id)<=now))\n            .OrderBy(QuestPriority)\n            .ThenBy(q=>q.MinimumLevel)\n            .ThenBy(q=>q.Id,StringComparer.Ordinal))\n        {\n            var giver=data.Npc(quest.Giver);\n            if(giver.Zone==player.Zone)return new(quest.Id,quest.Name,giver.Id,giver.Name,giver.Zone);\n        }\n        return null;\n    }\n"""
)

edit(
    "client/Scripts/GameRoot.Panels.cs",
    """                bool unlocked = quest.Prerequisite == \"\" || Snapshot.Self.CompletedQuests.Contains(quest.Prerequisite);\n                bool cooldown = Snapshot.Self.Cooldowns.GetValueOrDefault(\"quest:\" + quest.Id) > Snapshot.Time;\n                if (!active && ((!quest.Repeatable && complete) || !unlocked || cooldown)) continue;\n                var card = new PanelContainer(); offers.AddChild(card); var body = Ui.Column(card);\n                body.AddChild(Ui.Label(quest.Name + (quest.Repeatable ? \" · Repeatable\" : \"\"), 20, Ui.Gold)); body.AddChild(Ui.Label(quest.Story, 15, Ui.Text, true));\n                foreach (var objective in quest.Objectives) body.AddChild(Ui.Label(\"• \" + objective.Description, 14, Ui.Muted, true));\n                body.AddChild(Ui.Label($\"Reward: {quest.Gold} gold\" + (quest.Reward != \"\" ? \" · \" + Data.Item(quest.Reward).Name : \"\"), 14, Ui.Success));\n                if (!active) body.AddChild(Ui.Button(\"Accept quest\", () => Send(\"accept_quest\", item: quest.Id), !NearNpc(npc)));\n""",
    """                bool unlocked = quest.Prerequisite == \"\" || Snapshot.Self.CompletedQuests.Contains(quest.Prerequisite);\n                bool cooldown = Snapshot.Self.Cooldowns.GetValueOrDefault(\"quest:\" + quest.Id) > Snapshot.Time;\n                bool levelReady = Progression.PlayerLevel(Snapshot.Self) >= quest.MinimumLevel;\n                if (!active && ((!quest.Repeatable && complete) || !unlocked || cooldown)) continue;\n                var card = new PanelContainer(); offers.AddChild(card); var body = Ui.Column(card);\n                body.AddChild(Ui.Label(quest.Name + (quest.Repeatable ? \" · Repeatable\" : \"\"), 20, Ui.Gold)); body.AddChild(Ui.Label(quest.Story, 15, Ui.Text, true));\n                foreach (var objective in quest.Objectives) body.AddChild(Ui.Label(\"• \" + objective.Description, 14, Ui.Muted, true));\n                if (!levelReady) body.AddChild(Ui.Label($\"Requires character level {quest.MinimumLevel}.\", 14, Ui.Danger));\n                body.AddChild(Ui.Label($\"Reward: {quest.Gold} gold\" + (quest.Reward != \"\" ? \" · \" + Data.Item(quest.Reward).Name : \"\"), 14, Ui.Success));\n                if (!active) body.AddChild(Ui.Button(\"Accept quest\", () => Send(\"accept_quest\", item: quest.Id), !NearNpc(npc) || !levelReady));\n"""
)

edit(
    "client/Scripts/GameRoot.Hud.cs",
    """            var lead=JourneyProgression.LocalQuest(Data,self);var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);\n""",
    """            var lead=JourneyProgression.LocalQuest(Data,self,snap.Time);var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);\n"""
)

edit(
    "client/Scripts/HuntingGuidePanel.cs",
    """    public Func<Character?> ReadCharacter { get; set; }=()=>null;\n    public string SelectedSite { get; private set; }=\"\";\n""",
    """    public Func<Character?> ReadCharacter { get; set; }=()=>null;\n    public Func<double> ReadTime { get; set; }=()=>0;\n    public string SelectedSite { get; private set; }=\"\";\n"""
)
edit(
    "client/Scripts/HuntingGuidePanel.cs",
    """        var lead=JourneyProgression.LocalQuest(Data,self);var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);\n""",
    """        var lead=JourneyProgression.LocalQuest(Data,self,ReadTime());var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);\n"""
)
edit(
    "client/Scripts/HuntingGuidePanel.cs",
    """        var guide=new HuntingGuidePanel{Data=Data,Assets=Assets,ReadCharacter=()=>Snapshot?.Self};page.AddChild(guide);refreshPage=guide.RefreshSnapshot;\n""",
    """        var guide=new HuntingGuidePanel{Data=Data,Assets=Assets,ReadCharacter=()=>Snapshot?.Self,ReadTime=()=>Snapshot?.Time??0};page.AddChild(guide);refreshPage=guide.RefreshSnapshot;\n"""
)

write("tools/world_probe/MidLateGameContentChecks.cs", r'''using Kairnfall.Core;

internal static class MidLateGameContentChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check)
        {
            try{check();passed++;Console.WriteLine("PASS MID/LATE CONTENT: "+name);}
            catch(Exception error){failures.Add(name);Console.WriteLine("FAIL MID/LATE CONTENT: "+name+": "+error.Message);}
        }

        var dungeons=data.Zones.Where(z=>z.Kind=="dungeon").OrderBy(z=>z.Level).ThenBy(z=>z.Id,StringComparer.Ordinal).ToArray();
        var regions=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").OrderBy(z=>z.Level).ThenBy(z=>z.Id,StringComparer.Ordinal).ToArray();

        Test("every authored dungeon has a level-gated repeatable expedition",()=>
        {
            Need(dungeons.Length==20,"Expected exactly 20 authored dungeons.");
            int veteran=0;
            foreach(var zone in dungeons)
            {
                var boss=data.Mob(zone.Boss);
                var quest=data.Quests.SingleOrDefault(q=>q.Id=="delve_"+zone.Id);
                Need(quest is not null,"Missing repeatable expedition for "+zone.Id);
                Need(quest!.Repeatable&&quest.Category=="repeatable",quest.Id+" lost repeatable semantics.");
                Need(quest.MinimumLevel==Math.Max(1,boss.Level-5),quest.Id+" has the wrong character-level gate.");
                Need(quest.Objectives.Any(o=>o.Action=="explore"&&o.Target==zone.Id),quest.Id+" does not require entering the dungeon.");
                Need(quest.Objectives.Any(o=>o.Action=="boss"&&o.Target==boss.Id),quest.Id+" does not require its authored boss.");
                Need(quest.Gold>=100&&quest.Gold<=800,quest.Id+" reward is outside the bounded daily range.");
                if(boss.Level>=50)
                {
                    veteran++;
                    Need(quest.Prerequisite!="",quest.Id+" veteran expedition has no story gate.");
                    Need(quest.Objectives.Any(o=>o.Action=="gather"&&o.Target=="relic_shard"),quest.Id+" lacks the veteran relic-sample objective.");
                }
            }
            Console.WriteLine($"MID/LATE CONTENT METRIC dungeons={dungeons.Length} veteran_expeditions={veteran}");
            Need(veteran>=10,"Too few veteran expeditions.");
        });

        Test("optional dungeon circuits give every dungeon a one-time narrative hook",()=>
        {
            string[] deepways={"drowned_cistern","glasswing_grotto"};
            string[] umbral={"regents_tomb","rime_abbey","cinder_barracks","reef_sanctum"};
            var deep=data.Quest("veteran_deepways_circuit");
            var umb=data.Quest("veteran_umbral_circuit");
            Need(!deep.Repeatable&&deep.Category=="regional"&&deep.MinimumLevel==40&&deep.Prerequisite=="main_18","Deepways circuit gate changed.");
            Need(!umb.Repeatable&&umb.Category=="regional"&&umb.MinimumLevel==50&&umb.Prerequisite=="main_20","Umbral circuit gate changed.");
            foreach(var id in deepways)
            {
                var zone=data.Zone(id);
                Need(deep.Objectives.Any(o=>o.Action=="explore"&&o.Target==id),"Deepways circuit omits "+id);
                Need(deep.Objectives.Any(o=>o.Action=="boss"&&o.Target==zone.Boss),"Deepways circuit omits boss "+zone.Boss);
            }
            foreach(var id in umbral)
            {
                var zone=data.Zone(id);
                Need(umb.Objectives.Any(o=>o.Action=="explore"&&o.Target==id),"Umbral circuit omits "+id);
                Need(umb.Objectives.Any(o=>o.Action=="boss"&&o.Target==zone.Boss),"Umbral circuit omits boss "+zone.Boss);
            }
            var oneTimeDungeonTargets=data.Quests.Where(q=>!q.Repeatable)
                .SelectMany(q=>q.Objectives.Where(o=>o.Action=="explore").Select(o=>o.Target))
                .ToHashSet(StringComparer.Ordinal);
            foreach(var zone in dungeons)Need(oneTimeDungeonTargets.Contains(zone.Id),"Dungeon has no one-time narrative objective: "+zone.Id);
        });

        Test("regional and field work unlock at the same frontier band as their region",()=>
        {
            Need(regions.Length==20,"Expected 20 surface wilderness regions.");
            foreach(var zone in regions)
            {
                int expected=Math.Max(1,zone.Level-5);
                Need(data.Quest("survey_"+zone.Id).MinimumLevel==expected,"Survey level gate mismatch for "+zone.Id);
                Need(data.Quest("field_"+zone.Id).MinimumLevel==expected,"Field-report level gate mismatch for "+zone.Id);
            }
        });

        Test("server enforces expedition level story and daily cooldown gates",()=>
        {
            var quest=data.Quest("delve_prism_observatory");
            var giver=data.Npc(quest.Giver);
            var realm=new RealmEngine(data);
            var p=realm.CreateCharacter("mid-late-content","Expedition Tester","vanguard",new());
            p.Zone=giver.Zone;p.Position=giver.Position;
            var low=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(!low.Ok&&low.Message.Contains("character level",StringComparison.OrdinalIgnoreCase),"Under-level expedition was not rejected by level.");
            p.SkillXp["exploration"]=Progression.PlayerThreshold(quest.MinimumLevel);
            Need(Progression.PlayerLevel(p)>=quest.MinimumLevel,"Fixture did not reach the expedition level gate.");
            p.CompletedQuests.Add(quest.Prerequisite);
            var accepted=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(accepted.Ok&&p.Quests.ContainsKey(quest.Id),"Eligible expedition could not be accepted: "+accepted.Message);
            var progress=p.Quests[quest.Id];
            progress.Counts=quest.Objectives.Select(o=>o.Count).ToList();progress.Complete=true;
            long before=p.Gold;
            var claimed=realm.Execute(p.Id,new GameCommand{Kind="claim_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(claimed.Ok&&p.Gold==before+quest.Gold,"Expedition reward was not claimed exactly.");
            double ready=p.Cooldowns.GetValueOrDefault("quest:"+quest.Id);
            Need(ready>realm.State.Time,"Repeatable expedition did not set a daily cooldown.");
            var early=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(!early.Ok,"Expedition could be immediately repeated.");
            realm.State.Time=ready+.01;
            var again=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(again.Ok,"Expedition did not reopen after its cooldown: "+again.Message);
        });

        Test("journey guidance can surface ready repeatables after one-time work is exhausted",()=>
        {
            var quest=data.Quest("delve_prism_observatory");
            var giver=data.Npc(quest.Giver);
            var p=new Character{Id="guidance",Name="Guidance",Class="vanguard",Zone=giver.Zone};
            p.SkillXp["exploration"]=Progression.PlayerThreshold(quest.MinimumLevel);
            foreach(var oneTime in data.Quests.Where(q=>!q.Repeatable))p.CompletedQuests.Add(oneTime.Id);
            p.CompletedQuests.Add(quest.Id);
            p.Cooldowns["quest:"+quest.Id]=100;
            Need(JourneyProgression.LocalQuest(data,p,50)?.QuestId!=quest.Id,"Guidance ignored the repeatable cooldown.");
            var lead=JourneyProgression.LocalQuest(data,p,101);
            Need(lead is not null,"No ready repeatable was surfaced after one-time work.");
            Need(data.Quest(lead!.QuestId).Repeatable,"Guidance surfaced non-repeatable work after all one-time quests were completed.");
        });

        Console.WriteLine($"MID_LATE_GAME_CONTENT: {passed} groups passed; failures {failures.Count}. Human long-session variety and reward feel remain separate.");
    }
}
''')

edit(
    "tools/world_probe/Program.cs",
    """EconomyCraftingFeelChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n""",
    """EconomyCraftingFeelChecks.Run(catalog,failures);\nMidLateGameContentChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n"""
)

write("docs/MID_LATE_GAME_CONTENT.md", """# Mid/late-game content\n\nStatus: implemented as Area 7 mid/late-game content work.\n\nThis pass extends existing world systems rather than adding a separate endgame mode.\n\n- All 20 authored dungeons now have a daily guild expedition. Each contract requires entering the real dungeon and defeating its authored boss.\n- Bosses at level 50 and above add a relic-shard field objective, so veteran expeditions feed the existing crafting/material economy instead of becoming pure boss-reset loops.\n- Expedition offers have authoritative character-level gates at five levels below the boss and story prerequisites. The server enforces both; the client shows the required character level before acceptance.\n- The six optional dungeons omitted by the 25-quest main chain now have one-time guild circuits: two Deepways sites and four Umbral sites. This gives every dungeon a narrative objective before it becomes repeatable work.\n- Regional survey and field-report quests now unlock at the same five-level frontier band as their wilderness region, reducing high-level quest clutter and making progression bands easier to read.\n- Journey/Hunt guidance can surface repeatable work again after its daily cooldown once one-time local work is exhausted.\n\n`MidLateGameContentChecks` verifies complete dungeon coverage, veteran objective composition, optional-dungeon narrative coverage, regional level bands, authoritative level/story/cooldown enforcement, exact repeatable rewards, and post-story repeatable guidance.\n\nRepository automation establishes content wiring and gate correctness. Long-session variety, reward satisfaction, and perceived repetition remain hands-on playtest judgments.\n""")

print("mid/late-game content update applied")
