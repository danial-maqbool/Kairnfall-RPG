#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def edit(path, old, new):
    p=ROOT/path
    text=p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'anchor missing in {path}: {old[:120]!r}')
    p.write_text(text.replace(old,new,1),encoding='utf-8')

# Shared deterministic combat vocabulary and tactical labels.
(ROOT/'src/Kairnfall.Core/EnemyCombatRules.cs').write_text(r'''namespace Kairnfall.Core;

public static class EnemyCombatRules
{
    public static readonly string[] EliteTraits = ["elite_bulwark","elite_frenzy","elite_vampiric","elite_tempest","elite_skirmisher"];
    private static readonly HashSet<string> EnemyAttacks = new([
        "strike","lunge","slam","brace","frenzy","ambush","projectile","circle","charge","cone","stomp","line","ring",
        "interruptible","poison_field","summon","root","field","tempest"
    ],StringComparer.Ordinal);

    public static bool IsEliteTrait(string token)=>EliteTraits.Contains(token,StringComparer.Ordinal);
    public static bool IsKnownAttack(string token)=>EnemyAttacks.Contains(token);
    public static string EliteTrait(MobDef definition)=>definition.Attacks.FirstOrDefault(IsEliteTrait)??"";

    public static IReadOnlyList<string> AvailableBossAttacks(MobDef definition,int phase)
    {
        if(!definition.Boss||definition.Attacks.Length==0)return [];
        int count=Math.Clamp(phase+1,1,definition.Attacks.Length);
        return definition.Attacks.Take(count).ToArray();
    }

    public static string NextBossAttack(MobDef definition,Creature creature)
    {
        var choices=AvailableBossAttacks(definition,creature.Phase);
        if(choices.Count==0)return "strike";
        string attack=choices[creature.AttackStep%choices.Count];creature.AttackStep++;
        return attack;
    }

    public static string NextStandardAttack(MobDef definition,Creature creature)
    {
        var attacks=definition.Attacks.Where(x=>!IsEliteTrait(x)&&IsKnownAttack(x)).ToArray();
        if(attacks.Length==0)attacks=["strike"];
        int step=creature.AttackStep++;
        if(EliteTrait(definition)=="elite_tempest"&&step%3==2)return "tempest";
        return attacks[step%attacks.Length];
    }

    public static double AttackInterval(MobDef definition,Creature creature)
    {
        double interval=definition.Boss?2.8-creature.Phase*.3:definition.Ai switch
        {
            "pack_hunter"=>1.55,"ambusher"=>2.1,"ranged_kiter"=>2.0,"caster"=>2.2,"healer"=>2.25,"guard"=>2.2,"summoner"=>2.4,_=>1.8
        };
        if(EliteTrait(definition)=="elite_frenzy")interval*=.72;
        return Math.Max(.8,interval);
    }

    public static double MoveSpeedMultiplier(MobDef definition)=>EliteTrait(definition)=="elite_skirmisher"?1.28:1;
    public static double IncomingDamageMultiplier(MobDef definition)=>EliteTrait(definition)=="elite_bulwark"?.78:1;
    public static double PowerMultiplier(MobDef definition,Creature creature)
    {
        double result=1;
        if(definition.Ai=="berserker"&&creature.Health<definition.Health*.4)result*=1.6;
        if(EliteTrait(definition)=="elite_frenzy"&&creature.Health<definition.Health*.6)result*=1.3;
        return result;
    }

    public static string AttackLabel(string token)=>token switch
    {
        "strike"=>"Strike","lunge"=>"Lunge","slam"=>"Slam","brace"=>"Brace","frenzy"=>"Frenzy","ambush"=>"Ambush",
        "projectile"=>"Ranged Shot","circle"=>"Blast","charge"=>"Charge","cone"=>"Sweep","stomp"=>"Stomp","line"=>"Line Break",
        "ring"=>"Shock Ring","interruptible"=>"Interruptible Cast","poison_field"=>"Poison Field","summon"=>"Call Reinforcements",
        "root"=>"Binding Roots","field"=>"Hazard Field","tempest"=>"Tempest",_=>UiWords(token)
    };

    public static string TacticLabel(MobDef definition)
    {
        if(definition.Boss)return "Boss phases unlock authored attacks";
        string role=definition.Ai switch
        {
            "ranged_kiter"=>"Kiter · retreats when pressured","caster"=>"Caster · telegraphed area attacks","ambusher"=>"Ambusher · burst and bleed",
            "pack_hunter"=>"Pack hunter · shares threat","healer"=>"Support · heals wounded allies","summoner"=>"Summoner · calls reinforcements",
            "guard"=>"Guard · braces before heavy slams","berserker"=>"Berserker · stronger while wounded","fleeing"=>"Fleeing wildlife",
            "passive"=>"Passive wildlife","territorial"=>"Territorial bruiser",_=>"Aggressive skirmisher"
        };
        string elite=EliteTrait(definition) switch
        {
            "elite_bulwark"=>" · Bulwark","elite_frenzy"=>" · Frenzied","elite_vampiric"=>" · Vampiric","elite_tempest"=>" · Stormmarked","elite_skirmisher"=>" · Fleet",_=>""
        };
        return role+elite;
    }

    private static string UiWords(string value)=>string.Join(' ',value.Split('_',StringSplitOptions.RemoveEmptyEntries).Select(x=>char.ToUpperInvariant(x[0])+x[1..]));
}
''',encoding='utf-8')

# Save-compatible deterministic attack sequencing.
edit(Path('src/Kairnfall.Core/Models.cs'),
'''    public int Generation { get; set; }\n    public int Phase { get; set; }\n''',
'''    public int Generation { get; set; }\n    public int Phase { get; set; }\n    // Defaults to zero for historical saves; used only to rotate deterministic enemy attacks.\n    public int AttackStep { get; set; }\n''')

# Give ordinary enemies real attack profiles and elites deterministic mechanical traits.
p=ROOT/'content_src/mobs.py'
text=p.read_text(encoding='utf-8')
anchor="ELEMENTS={'volcanic':'Fire','glacier':'Frost','tundra':'Frost','swamp':'Poison','wetlands':'Poison','ancient_forest':'Nature','fungal':'Nature','crystal':'Arcane','ruins':'Physical','arcane_anomaly':'Arcane','wasteland':'Shadow'}\n\n"
if anchor not in text: raise SystemExit('mobs ELEMENTS anchor missing')
profiles="""ELEMENTS={'volcanic':'Fire','glacier':'Frost','tundra':'Frost','swamp':'Poison','wetlands':'Poison','ancient_forest':'Nature','fungal':'Nature','crystal':'Arcane','ruins':'Physical','arcane_anomaly':'Arcane','wasteland':'Shadow'}

ATTACK_PROFILES={
 'aggressive':['strike','lunge'],'territorial':['strike','slam'],'guard':['brace','slam'],'berserker':['strike','frenzy'],
 'pack_hunter':['lunge','strike'],'ambusher':['ambush','lunge'],'ranged_kiter':['projectile'],'caster':['projectile','circle'],
 'healer':['projectile'],'summoner':['summon','projectile'],'passive':['strike'],'fleeing':['strike']
}
ELITE_TRAITS=['elite_bulwark','elite_frenzy','elite_vampiric','elite_tempest','elite_skirmisher']

"""
text=text.replace(anchor,profiles,1)
old="attacks=attacks or [ai],drops=list(dict.fromkeys(drops))"
if old not in text: raise SystemExit('mobs attack profile anchor missing')
text=text.replace(old,"attacks=attacks or ATTACK_PROFILES.get(ai,['strike']),drops=list(dict.fromkeys(drops))",1)
old="elite['drops'].append('rune_precision_'+str(min(5,1+mob['level']//25))); data['mobs'].append(elite)"
if old not in text: raise SystemExit('elite trait anchor missing')
text=text.replace(old,"elite['drops'].append('rune_precision_'+str(min(5,1+mob['level']//25))); elite['attacks']=list(elite['attacks'])+[ELITE_TRAITS[i%len(ELITE_TRAITS)]]; data['mobs'].append(elite)",1)
p.write_text(text,encoding='utf-8')

# Fleet elites retain their movement identity while retreating.
edit(Path('src/Kairnfall.Core/CreatureMotion.cs'),
'''        if (mob.Position.Distance(plan.Goal) > .12) MoveCreature(mob, plan.Goal, dt, definition.Speed * 1.15);\n''',
'''        if (mob.Position.Distance(plan.Goal) > .12) MoveCreature(mob, plan.Goal, dt, definition.Speed * 1.15 * EnemyCombatRules.MoveSpeedMultiplier(definition));\n''')

# Damage mitigation / vampirism and full attack routing.
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''        double damage=CombatMath.Damage(raw*(1+bonus+empower)*matchup,element==Element.Physical?def.Armor:def.Armor*0.2,def.Resistances.GetValueOrDefault(element));\n        if(element==Element.Lightning&&WorldTime.Weather(Data.Zone(p.Zone),State.Time) is "rain" or "storm") damage*=1.15;\n        if(mob.Statuses.Any(x=>x.Kind=="vulnerable"&&x.Until>State.Time)) damage*=1.15;\n''',
'''        double damage=CombatMath.Damage(raw*(1+bonus+empower)*matchup,element==Element.Physical?def.Armor:def.Armor*0.2,def.Resistances.GetValueOrDefault(element));\n        damage*=EnemyCombatRules.IncomingDamageMultiplier(def);\n        damage*=1-Math.Clamp(CombatMath.StatusPower(mob.Statuses,"fortify",State.Time),0,.5);\n        if(element==Element.Lightning&&WorldTime.Weather(Data.Zone(p.Zone),State.Time) is "rain" or "storm") damage*=1.15;\n        if(mob.Statuses.Any(x=>x.Kind=="vulnerable"&&x.Until>State.Time)) damage*=1.15;\n''')
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''        p.Health=Math.Max(0,p.Health-damage); p.LastCombat=State.Time; p.Statuses.RemoveAll(x=>x.Kind is "meditate" or "stealth");\n''',
'''        p.Health=Math.Max(0,p.Health-damage); p.LastCombat=State.Time; p.Statuses.RemoveAll(x=>x.Kind is "meditate" or "stealth");\n        if(damage>0&&EnemyCombatRules.EliteTrait(def)=="elite_vampiric") mob.Health=Math.Min(def.Health,mob.Health+damage*.3);\n''')
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''    private void ResolveTelegraphs()\n    {\n''',
r'''    private void SummonEnemyAdds(Creature mob,MobDef definition,Character target)
    {
        int cap=definition.Boss?3:2;
        int alive=State.Creatures.Values.Count(x=>x.Id.StartsWith(mob.Id+"/add/",StringComparison.Ordinal)&&x.Health>0);
        if(alive>=cap)return;
        var addDef=Data.Mobs.Where(x=>!x.Boss&&!x.Elite&&x.Biome==definition.Biome&&x.Level<=definition.Level&&x.Ai!="passive")
            .OrderByDescending(x=>x.Level).ThenBy(x=>x.Id,StringComparer.Ordinal).FirstOrDefault()
            ??Data.Mobs.Where(x=>!x.Boss&&!x.Elite&&x.Level<=definition.Level).OrderByDescending(x=>x.Level).First();
        int count=definition.Boss?Math.Min(2,cap-alive):1;
        for(int n=0;n<count;n++)
        {
            string id=mob.Id+"/add/"+Guid.NewGuid().ToString("N");
            var pos=WorldMap.FindFree(Data.Zone(mob.Zone),new(mob.Position.X+1+n,mob.Position.Y+1));
            var add=new Creature{Id=id,Template=addDef.Id,Zone=mob.Zone,Position=pos,Home=pos,Health=addDef.Health,Target=target.Id};
            add.Threat[target.Id]=1;State.Creatures[id]=add;
        }
    }

    private void QueueEnemyAttack(Creature mob,MobDef definition,Character target,string attack)
    {
        double power=definition.Power*EnemyCombatRules.PowerMultiplier(definition,mob);
        var facing=mob.Position.Direction(target.Position);if(facing.Distance(new(0,0))>.01)mob.Facing=facing;
        void Telegraph(string shape,Point position,double radius,double multiplier,double delay,Element? element=null)
            =>State.Telegraphs.Add(new(){Zone=mob.Zone,Source=mob.Id,Position=position,Direction=mob.Facing,Shape=shape,Skill=attack,Element=element??definition.Element,Radius=radius,Power=power*multiplier,Resolves=State.Time+delay});
        switch(attack)
        {
            case "strike": HitPlayer(target,mob,power,definition.Element); break;
            case "frenzy": HitPlayer(target,mob,power*1.35,definition.Element); break;
            case "brace": ApplyStatus(mob.Statuses,"fortify",Element.Physical,3,.3,mob.Id); break;
            case "projectile": Telegraph("projectile",target.Position,1.0,1,.6); break;
            case "lunge": Telegraph("line",mob.Position,Math.Clamp(mob.Position.Distance(target.Position)+.5,2.5,4.5),1.15,.5); break;
            case "ambush": Telegraph("line",mob.Position,Math.Clamp(mob.Position.Distance(target.Position)+.5,2.5,4.5),1.25,.45); break;
            case "slam": Telegraph("circle",mob.Position,2.3,1.25,.7); break;
            case "circle": Telegraph("circle",target.Position,1.8,1.1,.75); break;
            case "cone": Telegraph("cone",mob.Position,definition.Boss?5.5:3.5,1.35,definition.Boss?1.0:.7); break;
            case "line": Telegraph("line",mob.Position,definition.Boss?8:4.5,1.4,definition.Boss?1.0:.7); break;
            case "ring": Telegraph("ring",mob.Position,4.5,1.45,1.05); break;
            case "stomp": Telegraph("circle",mob.Position,2.8,1.55,.85); break;
            case "charge": Telegraph("line",mob.Position,Math.Clamp(mob.Position.Distance(target.Position)+1,4,8),1.55,.9); break;
            case "interruptible": Telegraph("circle",target.Position,2.4,2.0,1.6); break;
            case "root": Telegraph("circle",target.Position,1.8,1.0,.8,Element.Nature); break;
            case "poison_field":
                for(int n=0;n<3;n++) State.Telegraphs.Add(new(){Zone=mob.Zone,Source=mob.Id,Position=target.Position,Direction=mob.Facing,Shape="circle",Skill=attack,Element=Element.Poison,Radius=2.2,Power=power*.55,Resolves=State.Time+.7+n});
                break;
            case "field":
                for(int n=0;n<3;n++) State.Telegraphs.Add(new(){Zone=mob.Zone,Source=mob.Id,Position=target.Position,Direction=mob.Facing,Shape="circle",Skill=attack,Element=definition.Element,Radius=2.3,Power=power*.6,Resolves=State.Time+.7+n});
                break;
            case "tempest": Telegraph("circle",target.Position,2.1,1.15,.8,Element.Lightning); break;
            case "summon": SummonEnemyAdds(mob,definition,target); break;
            default: HitPlayer(target,mob,power,definition.Element); break;
        }
    }

    private void ResolveTelegraphs()
    {
''')
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''            else if(State.Creatures.TryGetValue(t.Source,out var attacker)&&attacker.Health>0)\n            {\n                foreach(var id in Active.ToList())\n                {\n                    var p=Player(id); if(p.Zone==t.Zone&&p.Health>0&&InTelegraph(t,p.Position)&&WorldMap.LineOfSight(Data.Zone(t.Zone),t.Position,p.Position)) HitPlayer(p,attacker,t.Power,t.Element);\n                }\n            }\n''',
'''            else if(State.Creatures.TryGetValue(t.Source,out var attacker)&&attacker.Health>0)\n            {\n                foreach(var id in Active.ToList())\n                {\n                    var p=Player(id);\n                    if(p.Zone!=t.Zone||p.Health<=0||!InTelegraph(t,p.Position)||!WorldMap.LineOfSight(Data.Zone(t.Zone),t.Position,p.Position)) continue;\n                    double before=p.Health;HitPlayer(p,attacker,t.Power,t.Element);\n                    if(p.Health<before&&t.Skill=="root") ApplyStatus(p.Statuses,"root",Element.Nature,1.6,1,attacker.Id);\n                    if(p.Health<before&&t.Skill=="ambush") ApplyStatus(p.Statuses,"bleed",Element.Physical,4,Math.Max(1,t.Power*.05),attacker.Id);\n                }\n                if(t.Skill=="charge")\n                {\n                    var delta=t.Direction.Scale(Math.Min(4.5,t.Radius*.7));\n                    attacker.Position=WorldMap.Move(Data.Zone(attacker.Zone),attacker.Position,delta);attacker.Facing=t.Direction;\n                }\n            }\n''')
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''                if(mob.Owner==""&&mob.RespawnAt<=State.Time&&CanHuntRespawn(mob,live)) { mob.Health=def.Health; mob.Position=mob.Home; mob.Phase=0; mob.Threat.Clear(); mob.Statuses.Clear(); }\n''',
'''                if(mob.Owner==""&&mob.RespawnAt<=State.Time&&CanHuntRespawn(mob,live)) { mob.Health=def.Health; mob.Position=mob.Home; mob.Phase=0; mob.AttackStep=0; mob.Threat.Clear(); mob.Statuses.Clear(); }\n''')
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''            double distance=mob.Position.Distance(target.Position);\n            bool fleeing=def.Ai=="fleeing"||def.Ai=="passive"||(def.Ai=="ranged_kiter"&&distance<3);\n            if(fleeing&&mob.Health<def.Health*0.5) RetreatCreature(mob,target,def,dt);\n            else if(distance>def.Range||!WorldMap.LineOfSight(zone,mob.Position,target.Position)) MoveCreature(mob,target.Position,dt,def.Speed);\n''',
'''            double distance=mob.Position.Distance(target.Position);\n            bool closeKiter=def.Ai=="ranged_kiter"&&distance<Math.Max(3.0,def.Range*.65);\n            bool woundedFlee=def.Ai is "fleeing" or "passive"&&mob.Health<def.Health*.5;\n            bool eliteSkirmish=EnemyCombatRules.EliteTrait(def)=="elite_skirmisher"&&distance<2.6;\n            if(closeKiter||woundedFlee||eliteSkirmish) RetreatCreature(mob,target,def,dt);\n            else if(distance>def.Range||!WorldMap.LineOfSight(zone,mob.Position,target.Position)) MoveCreature(mob,target.Position,dt,def.Speed*EnemyCombatRules.MoveSpeedMultiplier(def));\n''')
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''            mob.Facing=mob.Position.Direction(target.Position); mob.NextAttack=State.Time+(def.Boss?2.8-mob.Phase*0.3:1.8);\n''',
'''            mob.Facing=mob.Position.Direction(target.Position); mob.NextAttack=State.Time+EnemyCombatRules.AttackInterval(def,mob);\n''')
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''            if(def.Ai=="summoner"&&State.Creatures.Values.Count(x=>x.Id.StartsWith(mob.Id+"/add/",StringComparison.Ordinal)&&x.Health>0)<2)\n            {\n                var addDef=Data.Mobs.Where(x=>!x.Boss&&!x.Elite&&x.Level<=def.Level).OrderBy(x=>x.Health).First();\n                string id=mob.Id+"/add/"+Guid.NewGuid().ToString("N"); var pos=WorldMap.FindFree(zone,new(mob.Position.X+1,mob.Position.Y));\n                State.Creatures[id]=new(){Id=id,Template=addDef.Id,Zone=mob.Zone,Position=pos,Home=pos,Health=addDef.Health,Target=target.Id};\n            }\n''','')
edit(Path('src/Kairnfall.Core/RealmCombat.cs'),
'''            if(def.Boss||def.Range>2||def.Ai is "caster" or "ambusher")\n            {\n                string shape=def.Boss?(mob.Phase==2?"ring":mob.Phase==1?"cone":"circle"):def.Range>2?"projectile":"line";\n                Point origin=shape is "ring" or "cone"?mob.Position:target.Position;\n                State.Telegraphs.Add(new(){Zone=mob.Zone,Source=mob.Id,Position=origin,Direction=mob.Facing,Shape=shape,Element=def.Element,Radius=def.Boss?3.5+mob.Phase:1.2,Power=def.Power*(def.Boss?1.8:1),Resolves=State.Time+(def.Boss?1.1:0.65)});\n            }\n            else HitPlayer(target,mob,def.Power*(def.Ai=="berserker"&&mob.Health<def.Health*0.4?1.6:1),def.Element);\n''',
'''            string attack=def.Boss?EnemyCombatRules.NextBossAttack(def,mob):EnemyCombatRules.NextStandardAttack(def,mob);\n            QueueEnemyAttack(mob,def,target,attack);\n''')

# Client combat cues: render rings as rings and label enemy special telegraphs.
edit(Path('client/Scripts/WorldView.cs'),
'''        else\n        {\n            DrawCircle(center, radius, new Color(color, color.A * .16f));\n            DrawArc(center, radius, 0, MathF.Tau, 48, color, 1.5f);\n            DrawArc(center, radius * .86f, 0, MathF.Tau, 48, new Color(color, color.A * .5f), 1);\n        }\n    }\n''',
'''        else if (effect.Shape == "ring")\n        {\n            DrawArc(center, radius, 0, MathF.Tau, 48, color, 2);\n            DrawArc(center, radius * .55f, 0, MathF.Tau, 48, color, 2);\n        }\n        else\n        {\n            DrawCircle(center, radius, new Color(color, color.A * .16f));\n            DrawArc(center, radius, 0, MathF.Tau, 48, color, 1.5f);\n            DrawArc(center, radius * .86f, 0, MathF.Tau, 48, new Color(color, color.A * .5f), 1);\n        }\n        if (EnemyCombatRules.IsKnownAttack(effect.Skill) && Snapshot?.Creatures.Any(x => x.Id == effect.Source) == true)\n            Text(center + new Vector2(0, -radius - 5), EnemyCombatRules.AttackLabel(effect.Skill), color, 9);\n    }\n''')

# Target frame explains tactics, elite trait, and boss phase attack set.
edit(Path('client/Scripts/GameRoot.Hud.cs'),
'''            targetDetail.Text += $"\\n{ChallengeProgression.ChallengeName(overallLevel, definition.Level)} · {practice:P0} practice · {credit:P1} overall credit";\n            targetDetail.TooltipText = "Practice scales the base combat skill award before skill mastery and affinity. Overall credit applies to the awarded practice, not the base reward. Twenty-level weaker enemies grant little progress.";\n''',
'''            targetDetail.Text += $"\\n{ChallengeProgression.ChallengeName(overallLevel, definition.Level)} · {practice:P0} practice · {credit:P1} overall credit";\n            targetDetail.Text += "\\n" + EnemyCombatRules.TacticLabel(definition);\n            if(definition.Boss) targetDetail.Text += " · Phase " + (target.Phase+1) + "/3 · " + string.Join(" / ",EnemyCombatRules.AvailableBossAttacks(definition,target.Phase).Select(EnemyCombatRules.AttackLabel));\n            targetDetail.TooltipText = "Practice scales the base combat skill award before skill mastery and affinity. Enemy tactic and boss attack cues describe authoritative server behavior; move out of telegraphs and interrupt long casts when possible.";\n''')

# Permanent authoritative regression coverage.
(ROOT/'tools/world_probe/CombatVarietyChecks.cs').write_text(r'''using Kairnfall.Core;

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
''',encoding='utf-8')
edit(Path('tools/world_probe/Program.cs'),
'''MeaningfulObjectiveChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n''',
'''MeaningfulObjectiveChecks.Run(catalog,failures);\nCombatVarietyChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n''')

(ROOT/'docs/COMBAT_VARIETY.md').write_text('''# Combat and enemy variety\n\nStatus: implemented as Area 3 anti-repetition work.\n\n- Ordinary enemies use authored tactical attack profiles instead of a single chase-and-hit behavior.\n- Ranged kiters retreat whenever pressured at close range; pack hunters, ambushers, guards, berserkers, healers, casters and summoners preserve distinct roles.\n- All 25 elites carry one deterministic modifier: Bulwark, Frenzied, Vampiric, Stormmarked or Fleet.\n- All 20 bosses execute their three authored attacks. Phase 1 exposes the first attack, phase 2 the first two, and phase 3 the complete kit.\n- Boss attacks include charges, cones, stomps, lines, rings, interruptible casts, poison fields, summons, roots and persistent hazard fields.\n- Existing player interrupt abilities cancel enemy telegraphs, including long interruptible boss casts.\n- Enemy telegraphs now label special attacks; ring attacks render as true danger rings. The target frame explains tactical role, elite modifier and boss phase attack set.\n- Combat remains server-authoritative. New mechanics are covered by `CombatVarietyChecks` in the normal world-probe suite.\n''',encoding='utf-8')

print('combat variety patch applied')
