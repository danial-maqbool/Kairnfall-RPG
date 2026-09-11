using System.Security.Cryptography;

namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private Creature Hostile(Character p,string id,double range)
    {
        Need(State.Creatures.TryGetValue(id,out var mob)&&mob.Health>0,"Select a living creature.");
        Need(mob!.Owner=="","You cannot attack a companion."); Near(p,mob.Zone,mob.Position,range); return mob;
    }
    private string Attack(Character p,string target)
    {
        var stats=CombatMath.Stats(p,Data);
        ItemDef? weapon=null; Item? weaponItem=null;
        if(p.Equipment.TryGetValue("weapon",out var weaponId))
        {
            var instance=Items.Owned(p,weaponId); Need(instance.Durability>0,"Your weapon needs repair."); weapon=Data.Item(instance.Template); weaponItem=instance;
        }
        string skill=weapon?.Skill is {Length:>0} ws?ws:"unarmed_combat";
        var mob=Hostile(p,target,weapon?.Range??1.6);
        Need(p.Stamina>=3,"Not enough stamina.");
        Need(!p.Statuses.Any(x=>x.Kind=="stun"&&x.Until>State.Time),"You are stunned.");
        Ready(p,"attack",Math.Max(0.25,(weapon?.Speed??0.8)/stats.AttackSpeed));
        bool stealthed=p.Statuses.Any(x=>x.Kind=="stealth"&&x.Until>State.Time);
        p.Stamina-=3; p.Facing=p.Position.Direction(mob.Position);
        playerTargets[p.Id]=mob.Id;
        Element attackElement=weapon is null?Element.Physical:Items.ElementOf(weaponItem!,weapon);
        var classBonus=ClassCombatRules.PrepareBasicAttack(p,attackElement,stealthed);
        double raw=stats.Physical*CombatTrainingCurve.Physical(Progression.Level(p,skill))*classBonus.PowerMultiplier;
        if(p.Class=="berserker") raw*=1+0.25*(1-p.Health/stats.Health);
        if(CombatMath.Roll(stats.Crit)) raw*=stats.CritDamage;
        p.Stamina=Math.Min(stats.Stamina,p.Stamina+classBonus.StaminaRefund);
        p.Statuses.RemoveAll(x=>x.Kind=="stealth");
        if(HandEquipment.IsProjectileWeapon(weapon))
        {
            State.Telegraphs.Add(new(){Zone=p.Zone,Source=p.Id,Position=mob.Position,Direction=p.Facing,Shape="projectile",Skill=skill,Element=attackElement,Radius=0.8,Power=raw,Resolves=State.Time+Math.Min(0.6,p.Position.Distance(mob.Position)/15)});
        }
        else HitCreature(p,mob,raw,attackElement,skill);
        return "";
    }
    private string Cast(Character p,string abilityId,string target,Point location)
    {
        var ability=Data.Ability(abilityId); var stats=CombatMath.Stats(p,Data);
        int requirement=ability.Requirement+(ability.Class!=""&&ability.Class!=p.Class?20:0);
        Need(Progression.Level(p,ability.Skill)>=requirement,"Your skill level is too low for this ability.");
        Need(!p.Statuses.Any(x=>x.Kind is "stun" or "silence"&&x.Until>State.Time),"You cannot cast while stunned or silenced.");
        Need(p.Mana>=ability.Mana&&p.Stamina>=ability.Stamina,"Not enough mana or stamina.");
        Ready(p,"ability:"+ability.Id,ability.Cooldown*(1-stats.CooldownReduction));
        Ready(p,"global_ability",0.25);
        bool stealthed=p.Statuses.Any(x=>x.Kind=="stealth"&&x.Until>State.Time);
        bool combatContext=State.Time-p.LastCombat<=10;
        var classBonus=ClassCombatRules.PrepareCast(p,ability,stealthed);
        p.Mana-=ability.Mana; p.Stamina-=ability.Stamina;
        double basePower=(ability.Element==Element.Physical?stats.Physical:stats.Spell)*ability.Power;
        basePower*=CombatTrainingCurve.Spell(Progression.Level(p,ability.Skill))*classBonus.PowerMultiplier;
        var zone=Data.Zone(p.Zone);
        Creature? selected=target!=""&&State.Creatures.TryGetValue(target,out var creature)?creature:null;
        Point aim=selected?.Position??location;
        bool selfKind=ability.Kind is "heal" or "shield" or "buff" or "stealth" or "summon" or "purge";
        if(!selfKind)
        {
            Need(selected is null||selected.Zone==p.Zone,"The ability target is in another region.");
            Need(aim.Finite&&p.Position.Distance(aim)<=ability.Range,"The ability target is out of range.");
            Need(WorldMap.LineOfSight(zone,p.Position,aim),"The target is behind an obstacle.");
            p.Facing=p.Position.Direction(aim);
        }
        bool trained=false;
        switch(ability.Kind)
        {
            case "heal":
            {
                var recipient=p;
                if(target!=""&&State.Characters.TryGetValue(target,out var ally))
                {
                    Need(ally.Id==p.Id||(p.Party!=""&&ally.Party==p.Party),"You can heal yourself or a party member.");
                    Near(p,ally.Zone,ally.Position,ability.Range); recipient=ally;
                }
                Need(recipient.Health>0,"This spell cannot resurrect the dead.");
                double maximum=CombatMath.Stats(recipient,Data).Health;
                Need(recipient.Health<maximum,"The target is at full health.");
                double healing=Math.Min(maximum-recipient.Health,basePower*stats.Healing);
                recipient.Health+=healing;
                if(ability.Duration>0) ApplyStatus(recipient.Statuses,"regeneration",ability.Element,ability.Duration,healing/10,p.Id);
                int encounterLevel=SupportTraining.EncounterLevel(recipient,State.Time);
                if(encounterLevel>0) { ChallengeProgression.TrainCombat(p,ability.Skill,Math.Max(1,(int)healing/2),encounterLevel,Data); trained=true; }
                break;
            }
            case "shield": ApplyStatus(p.Statuses,"shield",ability.Element,ability.Duration,basePower,p.Id); break;
            case "buff": ApplyStatus(p.Statuses,ability.Status==""?"empower":ability.Status,ability.Element,ability.Duration,Math.Clamp(ability.Power,0.1,1),p.Id); break;
            case "stealth": ApplyStatus(p.Statuses,"stealth",Element.Shadow,ability.Duration,1,p.Id); break;
            case "purge":
                Need(p.Statuses.Any(x=>x.Kind is "poison" or "burn" or "curse" or "root"),"There is no removable harmful effect.");
                p.Statuses.RemoveAll(x=>x.Kind is "poison" or "burn" or "curse" or "root"); break;
            case "dash":
            {
                var delta=new Point(aim.X-p.Position.X,aim.Y-p.Position.Y);
                Need(delta.Distance(new(0,0))>0.5,"Select a different position.");
                var end=WorldMap.Move(zone,p.Position,delta);
                Need(end.Distance(aim)<0.5,"The movement path is blocked."); p.Position=end;
                foreach(var m in State.Creatures.Values.Where(x=>x.Zone==p.Zone&&x.Owner==""&&x.Health>0&&x.Position.Distance(end)<=Math.Max(1,ability.Radius)).ToList()) HitCreature(p,m,basePower,ability.Element,ability.Skill);
                break;
            }
            case "summon":
            {
                Need(p.Pet==""||!State.Creatures.TryGetValue(p.Pet,out var oldPet)||oldPet.Health<=0,"You already have an active companion.");
                var def=Data.Mobs.Where(x=>!x.Boss&&!x.Elite&&x.Anatomy.StartsWith("animal:",StringComparison.Ordinal)&&x.Level<=Math.Max(1,Progression.Level(p,"summoning"))).OrderByDescending(x=>x.Level).FirstOrDefault()??throw new RuleException("No compatible summon is available.");
                string id="summon/"+Guid.NewGuid().ToString("N"); var at=WorldMap.FindFree(zone,new(p.Position.X+1,p.Position.Y));
                State.Creatures[id]=new(){Id=id,Template=def.Id,Zone=p.Zone,Position=at,Home=at,Health=def.Health,Owner=p.Id}; p.Pet=id;
                break;
            }
            case "taunt":
                foreach(var m in State.Creatures.Values.Where(x=>x.Zone==p.Zone&&x.Owner==""&&x.Health>0&&x.Position.Distance(p.Position)<=ability.Radius))
                { m.Threat[p.Id]=m.Threat.Values.DefaultIfEmpty(0).Max()+100; m.Target=p.Id; }
                ApplyStatus(p.Statuses,"guard",Element.Physical,ability.Duration,0.35,p.Id); break;
            case "projectile":
                Need(selected is not null&&selected.Health>0&&selected.Owner=="","Select a living hostile creature.");
                State.Telegraphs.Add(new(){Zone=p.Zone,Source=p.Id,Position=aim,Direction=p.Facing,Shape="projectile",Skill=ability.Skill,Element=ability.Element,Radius=Math.Max(0.8,ability.Radius),Power=basePower,Resolves=State.Time+Math.Clamp(p.Position.Distance(aim)/12,0.1,0.8)}); break;
            case "area": case "cone": case "line": case "field":
            {
                string shape=ability.Kind=="area"?"circle":ability.Kind=="field"?"circle":ability.Kind;
                Point origin=ability.Kind is "cone" or "line"?p.Position:aim;
                State.Telegraphs.Add(new(){Zone=p.Zone,Source=p.Id,Position=origin,Direction=p.Facing,Shape=shape,Skill=ability.Skill,Element=ability.Element,Radius=ability.Kind is "cone" or "line"?ability.Range:Math.Max(1,ability.Radius),Power=basePower,Resolves=State.Time+0.35});
                if(ability.Kind=="field") for(int n=1;n<=Math.Min(5,(int)ability.Duration);n++) State.Telegraphs.Add(new(){Zone=p.Zone,Source=p.Id,Position=aim,Shape="circle",Skill=ability.Skill,Element=ability.Element,Radius=Math.Max(1,ability.Radius),Power=basePower*0.3,Resolves=State.Time+n});
                break;
            }
            case "interrupt":
                Need(selected is not null&&selected.Health>0&&selected.Owner=="","Select a hostile caster.");
                Near(p,selected!.Zone,selected.Position,ability.Range);
                State.Telegraphs.RemoveAll(x=>x.Source==selected.Id); selected.NextAttack=State.Time+2;
                HitCreature(p,selected,basePower,ability.Element,ability.Skill); break;
            case "strike": case "drain": case "dot":
                Need(selected is not null&&selected.Health>0&&selected.Owner=="","Select a hostile creature.");
                Near(p,selected!.Zone,selected.Position,ability.Range);
                double damage=HitCreature(p,selected,basePower,ability.Element,ability.Skill);
                if(ability.Status!="") ApplyStatus(selected.Statuses,ability.Status,ability.Element,ability.Duration,ability.Status is "root" or "stun"?1:Math.Max(1,basePower*0.12),p.Id);
                if(ability.Kind=="drain") p.Health=Math.Min(stats.Health,p.Health+damage*0.25); break;
            default: throw new RuleException("Unsupported ability kind.");
        }
        if(classBonus.Effect=="vanguard_resolve") ApplyStatus(p.Statuses,"vanguard_resolve",Element.Physical,6,0.18,p.Id);
        else if(classBonus.Effect=="rogue_expose"&&selected is not null&&selected.Health>0) ApplyStatus(selected.Statuses,"vulnerable",Element.Arcane,4,0.15,p.Id);
        else if(classBonus.Effect=="warden_bond")
        {
            if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var companion)&&companion.Health>0)
            {
                ApplyStatus(companion.Statuses,"warden_bond",Element.Nature,8,0.30,p.Id);
                ApplyStatus(companion.Statuses,"fortify",Element.Nature,8,0.15,p.Id);
            }
            else ApplyStatus(p.Statuses,"regeneration",Element.Nature,6,Math.Max(1,stats.Healing),p.Id);
        }
        else if(classBonus.Effect=="templar_aegis") ApplyStatus(p.Statuses,"shield",Element.Radiant,5,Math.Max(8,stats.Health*0.10),p.Id);
        p.Mana=Math.Min(stats.Mana,p.Mana+classBonus.ManaRefund);
        p.Stamina=Math.Min(stats.Stamina,p.Stamina+classBonus.StaminaRefund);
        if(!selfKind) { p.LastCombat=State.Time; p.Statuses.RemoveAll(x=>x.Kind=="stealth"); }
        int supportLevel=SupportTraining.EncounterLevel(p,State.Time,10);
        if(!trained&&selfKind&&supportLevel>0&&ability.Kind!="heal") ChallengeProgression.TrainCombat(p,ability.Skill,5,supportLevel,Data);
        ClassCombatRules.RecordCast(p,ability,combatContext||supportLevel>0);
        Progress(p,"cast",ability.Id); return "";
    }
    private double HitCreature(Character p,Creature mob,double raw,Element element,string skill)
    {
        if(mob.Health<=0||mob.Owner!="") return 0;
        var def=Data.Mob(mob.Template); var stats=CombatMath.Stats(p,Data);
        double bonus=Math.Clamp(stats.Bonus("damage_"+element.ToString().ToLowerInvariant())/100,0,2);
        double empower=Math.Clamp(CombatMath.StatusPower(p.Statuses,"empower",State.Time),0,0.5);
        int attunement=Items.EquippedElementPoints(p,element,Data);
        double matchup=CombatMath.ElementMultiplier(element,def.Element,attunement,0);
        double damage=CombatMath.Damage(raw*(1+bonus+empower)*matchup,element==Element.Physical?def.Armor:def.Armor*0.2,def.Resistances.GetValueOrDefault(element));
        damage*=EnemyCombatRules.IncomingDamageMultiplier(def);
        damage*=1-Math.Clamp(CombatMath.StatusPower(mob.Statuses,"fortify",State.Time),0,.5);
        if(element==Element.Lightning&&WorldTime.Weather(Data.Zone(p.Zone),State.Time) is "rain" or "storm") damage*=1.15;
        if(mob.Statuses.Any(x=>x.Kind=="vulnerable"&&x.Until>State.Time)) damage*=1.15;
        damage=Math.Min(mob.Health,Math.Max(0,damage)); mob.Health-=damage;
        RecordEventDamage(p,mob,damage);
        mob.Threat[p.Id]=mob.Threat.GetValueOrDefault(p.Id)+damage*(p.Class=="vanguard"?1.4:1);
        p.LastCombat=State.Time; mob.Target=p.Id; playerTargets[p.Id]=mob.Id;
        if(damage>0)
        {
            SupportTraining.Record(p,def.Level,State.Time);
            ClassCombatRules.RecordDamage(p,damage,element,skill,p.Position.Distance(mob.Position));
            ChallengeProgression.TrainCombat(p,skill,Math.Clamp((int)damage,1,120),def.Level,Data);
            double leech=Math.Clamp(stats.Bonus("leech")/100,0,0.08);
            p.Health=Math.Min(stats.Health,p.Health+damage*leech);
            switch(element)
            {
                case Element.Fire: ApplyStatus(mob.Statuses,"burn",element,4,Math.Max(1,damage*0.08),p.Id); break;
                case Element.Frost: ApplyStatus(mob.Statuses,"chill",element,4,0.3,p.Id); break;
                case Element.Poison: ApplyStatus(mob.Statuses,"poison",element,5,Math.Max(1,damage*0.05),p.Id); break;
                case Element.Nature: if(CombatMath.Roll(0.2)) ApplyStatus(mob.Statuses,"root",element,1.5,1,p.Id); break;
                case Element.Shadow: ApplyStatus(mob.Statuses,"curse",element,5,0.15,p.Id); break;
                case Element.Arcane: ApplyStatus(mob.Statuses,"vulnerable",element,4,0.15,p.Id); break;
            }
        }
        if(mob.Health<=0) KillCreature(p,mob);
        return damage;
    }
    private void KillCreature(Character killer,Creature mob)
    {
        var def=Data.Mob(mob.Template); var publicEvent=WorldEventRules.Owner(State,mob.Id); mob.Health=0; mob.RespawnAt=publicEvent is null?State.Time+(def.Boss?300:def.Elite?90:25):double.MaxValue; mob.Generation++;
        mob.Target=""; mob.Statuses.Clear(); State.Telegraphs.RemoveAll(x=>x.Source==mob.Id);
        var contributors=mob.Threat.Where(x=>x.Value>0&&State.Characters.ContainsKey(x.Key)).Select(x=>Player(x.Key)).Where(x=>x.Zone==mob.Zone&&x.Position.Distance(mob.Position)<=24&&Active.Contains(x.Id)).ToList();
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
        var ordinaryDrops=def.Drops.Where(template=>!Data.Item(template).Tags.Contains("boss_unique",StringComparer.Ordinal)).ToArray();
        foreach(var template in ordinaryDrops)
        {
            var item=Data.Item(template); bool guaranteed=item.Type is "material" or "ore" or "wood" or "animal_material";
            if(guaranteed||CombatMath.Roll(def.Boss?0.8:0.25)) pile.Items.Add(Items.Create(Data,template,1,item.StackMax==1?Items.RollRarity(def.Boss?300:0):Rarity.Common,owner));
        }
        if(def.Boss)
        {
            var uniques=def.Drops.Where(template=>Data.Item(template).Tags.Contains("boss_unique",StringComparer.Ordinal)).ToArray();
            if(uniques.Length>0&&CombatMath.Roll(.04))
            {
                var classPool=uniques.Where(template=>Data.Item(template).Tags.Contains("class:"+owner.Class,StringComparer.Ordinal)).ToArray();
                var choices=classPool.Length>0&&CombatMath.Roll(.70)?classPool:uniques;
                string unique=choices[RandomNumberGenerator.GetInt32(choices.Length)];
                pile.Items.Add(Items.Create(Data,unique,1,Rarity.Relic,owner));
            }
        }
        if(pile.Items.Count==0&&ordinaryDrops.Length>0) pile.Items.Add(Items.Create(Data,ordinaryDrops[0],1,Rarity.Common,owner));
        Loot[pile.Id]=pile; mob.Threat.Clear(); EconomicDirty=true;
        if(def.Anatomy.StartsWith("animal:",StringComparison.Ordinal)&&Data.Resources.Any(x=>x.Id=="animal_carcass"))
        {
            string id="carcass/"+mob.Id+"/"+mob.Generation;
            State.Nodes[id]=new(){Id=id,Template="animal_carcass",Zone=mob.Zone,Position=mob.Position,Owner=owner.Id,ReadyAt=State.Time};
        }
    }
    private void HitPlayer(Character p,Creature mob,double raw,Element element)
    {
        if(p.Health<=0) return;
        var stats=CombatMath.Stats(p,Data); var def=Data.Mob(mob.Template);
        if(mob.Owner=="") SupportTraining.Record(p,def.Level,State.Time);
        if(CombatMath.Roll(stats.Evasion))
        {
            ClassCombatRules.RecordIncoming(p,0,0,false,true);
            ChallengeProgression.TrainCombat(p,"evasion",12,def.Level,Data); return;
        }
        Element defenseElement=Items.DominantElement(p,Data);
        int defensePoints=Items.EquippedElementPoints(p,defenseElement,Data);
        double matchup=CombatMath.ElementMultiplier(element,defenseElement,0,defensePoints);
        double damage=CombatMath.Damage(raw*matchup,element==Element.Physical?stats.Armor:stats.Armor*0.2,CombatMath.Resist(stats,element));
        bool blocked=CombatMath.Roll(stats.Block);
        if(blocked) { damage*=0.4; ChallengeProgression.TrainCombat(p,"shield_mastery",12,def.Level,Data); }
        damage*=1-Math.Clamp(CombatMath.StatusPower(p.Statuses,"guard",State.Time),0,0.6);
        damage*=1-Math.Clamp(CombatMath.StatusPower(p.Statuses,"vanguard_resolve",State.Time),0,0.35);
        double pressure=damage;
        foreach(var shield in p.Statuses.Where(x=>x.Kind=="shield"&&x.Until>State.Time).ToList())
        {
            double absorbed=Math.Min(shield.Power,damage); shield.Power-=absorbed; damage-=absorbed;
            if(shield.Power<=0) p.Statuses.Remove(shield);
        }
        p.Health=Math.Max(0,p.Health-damage); p.LastCombat=State.Time; p.Statuses.RemoveAll(x=>x.Kind is "meditate" or "stealth");
        ClassCombatRules.RecordIncoming(p,pressure,damage,blocked,false);
        if(damage>0&&EnemyCombatRules.EliteTrait(def)=="elite_vampiric") mob.Health=Math.Min(def.Health,mob.Health+damage*.3);
        string armorSkill="light_armor";
        if(p.Equipment.TryGetValue("chest",out var armorId))
        {
            var skill=Data.Item(Items.Owned(p,armorId).Template).Skill; if(Data.Skills.Any(x=>x.Id==skill)) armorSkill=skill;
        }
        ChallengeProgression.TrainCombat(p,armorSkill,Math.Clamp((int)damage,1,50),def.Level,Data);
        ChallengeProgression.TrainCombat(p,"endurance",3,def.Level,Data);
        if(damage>0&&element==Element.Poison) ApplyStatus(p.Statuses,"poison",element,4,Math.Max(1,damage*0.06),mob.Id);
        if(p.Health<=0) KillPlayer(p);
        EconomicDirty=true;
    }
    private void KillPlayer(Character p)
    {
        if(p.DeadUntil>State.Time) return;
        p.Health=0; p.DeadUntil=State.Time+5; p.Deaths++; p.Statuses.Clear(); inputs.Remove(p.Id); CancelTradesFor(p.Id);
        p.RecentLearningEncounter=null;
        foreach(var item in p.Inventory.Where(x=>Items.Equipped(p,x.Id))) item.Durability=Math.Max(0,item.Durability-10);
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet)) { pet.Health=0; pet.RespawnAt=double.MaxValue; p.Pet=""; }
        EconomicDirty=true;
    }
    private bool InTelegraph(Telegraph t,Point p)
    {
        double distance=t.Position.Distance(p); if(distance>t.Radius) return false;
        if(t.Shape is "circle" or "projectile") return true;
        var direction=t.Position.Direction(p); double dot=direction.X*t.Direction.X+direction.Y*t.Direction.Y;
        if(t.Shape=="cone") return dot>=0.5;
        if(t.Shape=="line") return dot>=0&&Math.Abs((p.X-t.Position.X)*t.Direction.Y-(p.Y-t.Position.Y)*t.Direction.X)<0.9;
        if(t.Shape=="ring") return distance>=t.Radius*0.55;
        return false;
    }
    private void SummonEnemyAdds(Creature mob,MobDef definition,Character target)
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
        double power=definition.Power*EnemyCombatRules.PowerMultiplier(definition,mob)*WorldEventRules.EnemyPowerMultiplier(State,mob.Zone,State.Time);
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
        foreach(var t in State.Telegraphs.Where(x=>x.Resolves<=State.Time).ToList())
        {
            State.Telegraphs.Remove(t);
            if(State.Characters.TryGetValue(t.Source,out var player))
            {
                if(player.Health<=0||player.Zone!=t.Zone||!Data.Skills.Any(skill=>skill.Id==t.Skill)) continue;
                foreach(var mob in State.Creatures.Values.Where(x=>x.Health>0&&x.Owner==""&&x.Zone==t.Zone&&InTelegraph(t,x.Position)).ToList())
                    if(WorldMap.LineOfSight(Data.Zone(t.Zone),t.Position,mob.Position)) HitCreature(player,mob,t.Power,t.Element,t.Skill);
            }
            else if(State.Creatures.TryGetValue(t.Source,out var attacker)&&attacker.Health>0)
            {
                foreach(var id in Active.ToList())
                {
                    var p=Player(id);
                    if(p.Zone!=t.Zone||p.Health<=0||!InTelegraph(t,p.Position)||!WorldMap.LineOfSight(Data.Zone(t.Zone),t.Position,p.Position)) continue;
                    double before=p.Health;HitPlayer(p,attacker,t.Power,t.Element);
                    if(p.Health<before&&t.Skill=="root") ApplyStatus(p.Statuses,"root",Element.Nature,1.6,1,attacker.Id);
                    if(p.Health<before&&t.Skill=="ambush") ApplyStatus(p.Statuses,"bleed",Element.Physical,4,Math.Max(1,t.Power*.05),attacker.Id);
                }
                if(t.Skill=="charge")
                {
                    var delta=t.Direction.Scale(Math.Min(4.5,t.Radius*.7));
                    attacker.Position=WorldMap.Move(Data.Zone(attacker.Zone),attacker.Position,delta);attacker.Facing=t.Direction;
                }
            }
        }
    }
    private void TickCreatures(double dt)
    {
        PruneCreatureMotion();
        var live=Active.Where(State.Characters.ContainsKey).Select(Player).Where(x=>x.Health>0).ToList();
        var zones=live.Select(x=>x.Zone).ToHashSet();
        var activeCreatures=State.Creatures.Values.Where(x=>zones.Contains(x.Zone)).ToArray();
        var byZone=activeCreatures.GroupBy(x=>x.Zone).ToDictionary(g=>g.Key,g=>g.ToArray());
        IndexCreatures(activeCreatures);
        foreach(var mob in activeCreatures)
        {
            var def=Data.Mob(mob.Template); var zone=Data.Zone(mob.Zone);
            if(mob.Health<=0)
            {
                if(mob.Owner==""&&mob.RespawnAt<=State.Time&&CanHuntRespawn(mob,live)) { mob.Health=def.Health; mob.Position=mob.Home; mob.Phase=0; mob.AttackStep=0; mob.Threat.Clear(); mob.Statuses.Clear(); }
                continue;
            }
            mob.Statuses.RemoveAll(x=>x.Until<=State.Time);
            if(mob.Owner!="") { TickCompanion(mob,dt); continue; }
            var nearby=live.Where(x=>x.Zone==mob.Zone&&x.Position.Distance(mob.Position)<=28).ToList();
            if(nearby.Count==0) continue;
            var target=nearby.Where(x=>mob.Threat.ContainsKey(x.Id)).OrderByDescending(x=>mob.Threat.GetValueOrDefault(x.Id)).FirstOrDefault();
            if(target is null&&def.Ai!="passive") target=nearby.Where(x=>x.Position.Distance(mob.Position)<=def.Aggro&&!x.Statuses.Any(s=>s.Kind=="stealth"&&s.Until>State.Time)&&WorldMap.LineOfSight(zone,mob.Position,x.Position)).OrderBy(x=>x.Position.Distance(mob.Position)).FirstOrDefault();
            if(mob.Position.Distance(mob.Home)>25)
            {
                mob.Target=""; mob.Threat.Clear(); creatureMotion.Remove(mob.Id); MoveCreature(mob,mob.Home,dt,def.Speed*1.3);
                mob.Health=Math.Min(def.Health,mob.Health+def.Health*dt/4); continue;
            }
            if(target is null)
            {
                mob.Target="";
                WanderCreature(mob,def,dt);
                continue;
            }
            mob.Target=target.Id;
            if(def.Ai=="pack_hunter") foreach(var ally in byZone[mob.Zone].Where(x=>x.Owner==""&&x.Health>0&&x.Position.Distance(mob.Position)<5&&Data.Mob(x.Template).Family==def.Family))
                if(!huntMembership.TryGetValue(mob.Id,out var homePatch)||!huntMembership.TryGetValue(ally.Id,out var allyPatch)||homePatch.Id==allyPatch.Id) ally.Threat.TryAdd(target.Id,1);
            if(CombatMath.StatusPower(mob.Statuses,"stun",State.Time)>0) continue;
            double distance=mob.Position.Distance(target.Position);
            bool closeKiter=def.Ai=="ranged_kiter"&&distance<Math.Max(3.0,def.Range*.65);
            bool woundedFlee=def.Ai is "fleeing" or "passive"&&mob.Health<def.Health*.5;
            bool eliteSkirmish=EnemyCombatRules.EliteTrait(def)=="elite_skirmisher"&&distance<2.6;
            if(closeKiter||woundedFlee||eliteSkirmish) RetreatCreature(mob,target,def,dt);
            else if(distance>def.Range||!WorldMap.LineOfSight(zone,mob.Position,target.Position)) MoveCreature(mob,target.Position,dt,def.Speed*EnemyCombatRules.MoveSpeedMultiplier(def));
            if(def.Boss)
            {
                int phase=mob.Health<def.Health*0.3?2:mob.Health<def.Health*0.65?1:0;
                if(phase>mob.Phase) { mob.Phase=phase; mob.NextAttack=Math.Min(mob.NextAttack,State.Time+0.5); }
            }
            if(State.Time<mob.NextAttack||distance>Math.Max(def.Range,def.Boss?9:def.Range)||!WorldMap.LineOfSight(zone,mob.Position,target.Position)) continue;
            mob.Facing=mob.Position.Direction(target.Position); mob.NextAttack=State.Time+EnemyCombatRules.AttackInterval(def,mob);
            if(def.Ai=="healer")
            {
                var ally=byZone[mob.Zone].Where(x=>x.Owner==""&&x.Health>0&&x.Position.Distance(mob.Position)<6).OrderBy(x=>x.Health/Data.Mob(x.Template).Health).FirstOrDefault();
                if(ally is not null&&ally.Health<Data.Mob(ally.Template).Health*0.8) { ally.Health=Math.Min(Data.Mob(ally.Template).Health,ally.Health+def.Power*2); continue; }
            }
            string attack=def.Boss?EnemyCombatRules.NextBossAttack(def,mob):EnemyCombatRules.NextStandardAttack(def,mob);
            QueueEnemyAttack(mob,def,target,attack);
        }
    }
    private void MoveCreature(Creature mob,Point goal,double dt,double speed)
    {
        if(CombatMath.StatusPower(mob.Statuses,"root",State.Time)>0||CombatMath.StatusPower(mob.Statuses,"stun",State.Time)>0) return;
        double remaining=mob.Position.Distance(goal); if(remaining<.08) return;
        var zone=Data.Zone(mob.Zone); Point direction=mob.Position.Direction(goal);
        if(!WorldMap.LineOfSight(zone,mob.Position,goal))
        {
            var path=WorldMap.FindPath(zone,mob.Position,goal,512); if(path.Count==0) return; direction=mob.Position.Direction(path[0]);
        }
        speed*=Math.Clamp(1-CombatMath.StatusPower(mob.Statuses,"chill",State.Time),0.3,1);
        mob.Position=SeparatedMove(mob,direction,Math.Min(remaining,speed*dt)); mob.Facing=direction;
    }
    private void TickCompanion(Creature pet,double dt)
    {
        if(!State.Characters.TryGetValue(pet.Owner,out var owner)||!Active.Contains(owner.Id)||owner.Health<=0) return;
        var def=Data.Mob(pet.Template);
        if(pet.Zone!=owner.Zone) { pet.Zone=owner.Zone; pet.Position=owner.Position; }
        Creature? enemy=null;
        if(playerTargets.TryGetValue(owner.Id,out var target)&&State.Creatures.TryGetValue(target,out var candidate)&&candidate.Health>0&&candidate.Owner==""&&candidate.Zone==pet.Zone&&candidate.Position.Distance(owner.Position)<=12) enemy=candidate;
        if(enemy is null) { if(pet.Position.Distance(owner.Position)>2) MoveCreature(pet,owner.Position,dt,def.Speed+1); return; }
        if(pet.Position.Distance(enemy.Position)>def.Range) MoveCreature(pet,enemy.Position,dt,def.Speed+1);
        else if(pet.NextAttack<=State.Time)
        {
            pet.NextAttack=State.Time+2;
            double bond=CombatMath.StatusPower(pet.Statuses,"warden_bond",State.Time);
            HitCreature(owner,enemy,def.Power*(1+Math.Clamp(bond,0,0.35)),def.Element,pet.Id.StartsWith("summon/",StringComparison.Ordinal)?"summoning":"animal_handling");
        }
    }
    private void TickEnvironment(double dt)
    {
        foreach(var p in State.Characters.Values.ToList())
        {
            if(p.Health<=0) continue;
            bool online=Active.Contains(p.Id);
            // Logging out does not cancel damage already applied by combat.
            // Other offline activities, including healing and XP, remain paused.
            if(!online&&!p.Statuses.Any(x=>x.Until>State.Time&&x.Kind is "poison" or "burn" or "bleed")) continue;
            var stats=CombatMath.Stats(p,Data);
            foreach(var status in p.Statuses.Where(x=>x.Until>State.Time).ToList())
            {
                if(online&&status.Kind=="regeneration") p.Health=Math.Min(stats.Health,p.Health+status.Power*dt);
                if(status.Kind is "poison" or "burn" or "bleed") p.Health=Math.Max(0,p.Health-status.Power*dt*(1-CombatMath.Resist(stats,status.Element)));
                if(p.Health<=0) break;
                if(online&&status.Kind=="meditate"&&p.Mana<stats.Mana-1) Progression.Train(p,"meditation",1,Math.Clamp(Data.Zone(p.Zone).Level,1,100),Data);
            }
            if(p.Health<=0) KillPlayer(p);
            if(!online) continue;
            foreach(var entry in p.Quests)
            {
                var q=Data.Quest(entry.Key);
                for(int i=0;i<q.Objectives.Count;i++) if(q.Objectives[i].Action=="deliver") entry.Value.Counts[i]=Math.Min(q.Objectives[i].Count,Items.Count(p,q.Objectives[i].Target));
                entry.Value.Complete=q.Objectives.Select((x,i)=>entry.Value.Counts[i]>=x.Count).All(x=>x);
            }
        }
        var zones=Active.Select(Player).Select(x=>x.Zone).ToHashSet();
        foreach(var mob in State.Creatures.Values.Where(x=>x.Health>0&&x.Owner==""&&zones.Contains(x.Zone)).ToList())
        {
            foreach(var status in mob.Statuses.Where(x=>x.Until>State.Time&&x.Kind is "poison" or "burn" or "bleed").ToList())
            {
                if(!State.Characters.TryGetValue(status.Source,out var source)||source.Zone!=mob.Zone) continue;
                double damage=Math.Min(mob.Health,CombatMath.Damage(status.Power*dt,0,Data.Mob(mob.Template).Resistances.GetValueOrDefault(status.Element)));
                mob.Health-=damage;
                if(mob.Health<=0) { KillCreature(source,mob); break; }
            }
        }
        foreach(var pair in State.Nodes.Where(x=>x.Key.StartsWith("carcass/",StringComparison.Ordinal)&&x.Value.ReadyAt>State.Time).ToList()) State.Nodes.Remove(pair.Key);
        foreach(var c in State.Creatures.Values.Where(x=>x.Id.Contains("/add/",StringComparison.Ordinal)&&x.Health<=0).ToList()) State.Creatures.Remove(c.Id);
        EconomicDirty=true;
    }
}
