using System.Security.Cryptography;

namespace Kairnfall.Core;

public sealed record BuildLootSet(string Id,string Name,string TwoPiece,string ThreePiece);
public sealed record CraftSpecializationChoice(string Id,string Name,int Requirement,string Description);

/// <summary>
/// Authored build-defining equipment behavior layered on top of the existing deterministic
/// progression catalog. Effects reward particular play patterns without changing equipment
/// legality or removing access to off-class skills.
/// </summary>
public static class BuildDefiningLoot
{
    public const string EffectPrefix="effect:";

    private static readonly Dictionary<string,string> descriptions=new(StringComparer.Ordinal)
    {
        ["unique_vanguard_bastion"]="At Resolve READY, gain substantial block and armor. The signature remains equippable by other builds, but only Vanguard Resolve activates this engine.",
        ["unique_berserker_bloodprice"]="At Fury READY, gain brutal physical pressure; wounded enemies take extra finishing damage.",
        ["unique_ranger_quarry"]="At Focus READY, gain attack speed and critical pressure, with extra damage against elite and boss quarry.",
        ["unique_rogue_venomburst"]="At Momentum READY, gain speed and critical pressure; poisoned targets take extra damage.",
        ["unique_arcanist_resonance"]="At Resonance READY, gain spell power and cooldown recovery without consuming Resonance outside native Arcanist techniques.",
        ["unique_warden_bond"]="At Bond READY, gain healing and Nature-oriented spell pressure while preserving the ordinary Bond rules.",
        ["unique_templar_conviction"]="At Conviction READY, gain armor and Radiant damage while native Templar techniques remain the only automatic Conviction spenders.",
        ["unique_spellblade_weave"]="At Spellweave READY, the opposite combat school is strengthened, rewarding martial/magical alternation.",
        ["offhand_bastion"]="Shield stance: higher block and armor. Choose this when absorbing pressure matters more than an offensive offhand.",
        ["offhand_resonant_focus"]="Focus stance: spell power and cooldown recovery for active casting.",
        ["offhand_quarry_quiver"]="Quiver stance: faster attacks and higher critical pressure with compatible bows and crossbows.",
        ["offhand_flux_orb"]="Orb stance: larger mana reserve plus spell pressure for sustained casting.",
        ["rune_fire_conversion"]="Transforms offensive ability damage to Fire. If several conversion runes are equipped, only the highest-tier transform applies.",
        ["rune_lightning_conversion"]="Transforms offensive ability damage to Lightning. If several conversion runes are equipped, only the highest-tier transform applies.",
        ["rune_resonant_echo"]="Tightens offensive ability recovery while socketed; higher tiers remain bounded by the global cooldown-reduction cap.",
        ["rune_guard_store"]="Reinforces shield-oriented builds with additional block through the rune's ordinary stat contribution.",
        ["execute"]="Execution: deal 25% more damage to enemies below 25% health.",
        ["resource_ready"]="READY surge: when your class resource reaches its native READY threshold, gain power and cooldown recovery without changing who can spend that resource.",
        ["shieldbound"]="Holdfast: while a usable shield is equipped, gain substantial armor and offensive pressure.",
        ["elemental_attunement"]="Attuned craft: amplify damage matching this item's chosen non-Physical element.",
        ["supportive_aegis"]="Aegis weave: trade raw offense for stronger healing and protection-oriented stats."
    };

    public static readonly IReadOnlyDictionary<string,BuildLootSet> Sets=new Dictionary<string,BuildLootSet>(StringComparer.Ordinal)
    {
        ["roadwarden"]=new("roadwarden","Roadwarden","2 pieces: +6% block.","3 pieces: +12 armor and +8 physical pressure while holding the line."),
        ["stormrunner"]=new("stormrunner","Stormrunner","2 pieces: +8% attack speed.","3 pieces: at class-resource READY, +8% critical chance."),
        ["starweaver"]=new("starweaver","Starweaver","2 pieces: +7% cooldown recovery.","3 pieces: at class-resource READY, +15 spell power.")
    };

    private static bool Offensive(AbilityDef ability)=>ability.Kind is
        "strike" or "dot" or "drain" or "dash" or "cone" or "line" or "area" or "field" or "projectile" or "interrupt";

    public static bool IsEffectAffix(Affix affix)=>affix.Stat.StartsWith(EffectPrefix,StringComparison.Ordinal);
    public static string EffectId(Affix affix)=>IsEffectAffix(affix)?affix.Stat[EffectPrefix.Length..]:"";
    public static bool KnownEffect(string effect)=>effect!=""&&descriptions.ContainsKey(effect);
    public static string EffectDescription(string effect)=>descriptions.GetValueOrDefault(effect,"Unknown build effect.");
    public static bool CanReforgeAffix(Affix affix)=>!affix.Name.StartsWith("Crafted:",StringComparison.Ordinal);

    private static IEnumerable<(Item Item,ItemDef Def)> Equipped(Character player,Catalog data)
    {
        foreach(string id in player.Equipment.Values.Distinct(StringComparer.Ordinal))
        {
            var item=player.Inventory.FirstOrDefault(x=>x.Id==id);
            if(item is null||item.Durability<=0) continue;
            var def=data.Items.FirstOrDefault(x=>x.Id==item.Template);
            if(def is not null) yield return (item,def);
        }
    }

    private static IEnumerable<string> EquippedEffects(Character player,Catalog data)
    {
        foreach(var pair in Equipped(player,data))
        {
            if(KnownEffect(pair.Def.Effect)) yield return pair.Def.Effect;
            foreach(var affix in pair.Item.Affixes.Where(IsEffectAffix))
                if(KnownEffect(EffectId(affix))) yield return EffectId(affix);
            foreach(var socket in pair.Item.Runes)
            {
                var rune=data.Items.FirstOrDefault(x=>x.Id==socket.Template);
                if(rune is not null&&KnownEffect(rune.Effect)) yield return rune.Effect;
            }
        }
    }

    public static bool HasEffect(Character player,string effect,Catalog data)
        =>EquippedEffects(player,data).Contains(effect,StringComparer.Ordinal);

    public static int SetPieceCount(Character? player,string setId,Catalog data)
    {
        if(player is null||!Sets.ContainsKey(setId)) return 0;
        string tag="set:"+setId;
        return Equipped(player,data).Count(x=>x.Def.Tags.Contains(tag,StringComparer.Ordinal));
    }

    private static int UniqueLevel(ItemDef def)
    {
        string? tag=def.Tags.FirstOrDefault(x=>x.StartsWith("unique_level:",StringComparison.Ordinal));
        return tag is not null&&int.TryParse(tag["unique_level:".Length..],out int level)?Math.Clamp(level,1,100):1;
    }

    public static bool ClassSynergyActive(Character player,ItemDef def)
    {
        string? owner=def.Tags.FirstOrDefault(x=>x.StartsWith("class:",StringComparison.Ordinal));
        if(owner is null||owner["class:".Length..]!=player.Class) return false;
        return player.ClassResource>=ClassCombatRules.ReadyThreshold(player.Class);
    }

    public static void ApplyDynamicStats(Character player,Catalog data,Action<string,double> add)
    {
        var equipped=Equipped(player,data).ToArray();
        var uniqueEffects=new HashSet<string>(StringComparer.Ordinal);
        foreach(var pair in equipped)
        {
            if(pair.Def.Effect!="") uniqueEffects.Add(pair.Def.Effect);
            foreach(var affix in pair.Item.Affixes.Where(IsEffectAffix)) uniqueEffects.Add(EffectId(affix));
            foreach(var rune in pair.Item.Runes)
            {
                var runeDef=data.Items.FirstOrDefault(x=>x.Id==rune.Template);
                if(runeDef is not null&&runeDef.Effect!="") uniqueEffects.Add(runeDef.Effect);
            }
        }

        bool ready=player.ClassResource>=ClassCombatRules.ReadyThreshold(player.Class);
        bool shield=HandEquipment.HasUsableShield(player,data);
        if(uniqueEffects.Contains("execute")) { /* target-conditional; handled by TargetDamageMultiplier */ }
        if(uniqueEffects.Contains("resource_ready")&&ready) { add("physical",10);add("spell",10);add("cooldown",5); }
        if(uniqueEffects.Contains("shieldbound")&&shield) { add("armor",12);add("physical",7);add("spell",7); }
        if(uniqueEffects.Contains("supportive_aegis")) { add("healing",12);add("armor",6); }
        foreach(var pair in equipped.Where(x=>x.Item.Element is not null||x.Def.Element!=Element.Physical))
            if(pair.Item.Affixes.Any(a=>EffectId(a)=="elemental_attunement"))
            {
                Element element=Items.ElementOf(pair.Item,pair.Def);
                if(element!=Element.Physical) add("damage_"+element.ToString().ToLowerInvariant(),15);
            }

        if(uniqueEffects.Contains("offhand_bastion")) { add("block",5);add("armor",6); }
        if(uniqueEffects.Contains("offhand_resonant_focus")) { add("spell",5);add("cooldown",4); }
        if(uniqueEffects.Contains("offhand_quarry_quiver")) { add("crit",4);add("attack_speed",4); }
        if(uniqueEffects.Contains("offhand_flux_orb")) { add("mana",15);add("spell",4); }
        if(uniqueEffects.Contains("rune_resonant_echo")) add("cooldown",3);

        foreach(var pair in equipped.Where(x=>x.Def.Tags.Contains("boss_unique",StringComparer.Ordinal)&&ClassSynergyActive(player,x.Def)))
        {
            double scale=1+UniqueLevel(pair.Def)/50.0;
            switch(pair.Def.Effect)
            {
                case "unique_vanguard_bastion": add("block",4*scale);add("armor",8*scale);break;
                case "unique_berserker_bloodprice": add("physical",10*scale);add("crit_damage",8*scale);break;
                case "unique_ranger_quarry": add("attack_speed",7*scale);add("crit",5*scale);break;
                case "unique_rogue_venomburst": add("attack_speed",8*scale);add("crit",6*scale);break;
                case "unique_arcanist_resonance": add("spell",10*scale);add("cooldown",5*scale);break;
                case "unique_warden_bond": add("healing",10*scale);add("spell",6*scale);break;
                case "unique_templar_conviction": add("damage_radiant",10*scale);add("armor",7*scale);break;
                case "unique_spellblade_weave":
                    if(player.ClassState=="martial") add("spell",12*scale); else add("physical",12*scale);
                    break;
            }
        }

        int road=SetPieceCount(player,"roadwarden",data);
        if(road>=2)add("block",6);
        if(road>=3){add("armor",12);add("physical",8);}
        int storm=SetPieceCount(player,"stormrunner",data);
        if(storm>=2)add("attack_speed",8);
        if(storm>=3&&ready)add("crit",8);
        int star=SetPieceCount(player,"starweaver",data);
        if(star>=2)add("cooldown",7);
        if(star>=3&&ready)add("spell",15);
    }

    public static double TargetDamageMultiplier(Character player,Creature target,MobDef targetDef,Catalog data,double now)
    {
        double result=1;
        if(HasEffect(player,"execute",data)&&target.Health<=targetDef.Health*.25) result*=1.25;
        if(player.Class=="berserker"&&HasEffect(player,"unique_berserker_bloodprice",data)
            &&player.ClassResource>=ClassCombatRules.ReadyThreshold(player.Class)&&target.Health<=targetDef.Health*.35) result*=1.15;
        if(player.Class=="ranger"&&HasEffect(player,"unique_ranger_quarry",data)
            &&player.ClassResource>=ClassCombatRules.ReadyThreshold(player.Class)&&(targetDef.Boss||targetDef.Elite)) result*=1.12;
        if(player.Class=="rogue"&&HasEffect(player,"unique_rogue_venomburst",data)
            &&player.ClassResource>=ClassCombatRules.ReadyThreshold(player.Class)
            &&target.Statuses.Any(x=>x.Kind=="poison"&&x.Until>now)) result*=1.15;
        return Math.Min(1.6,result);
    }

    public static Element AbilityElement(Character player,AbilityDef ability,Catalog data)
    {
        if(!Offensive(ability)) return ability.Element;
        var conversions=Equipped(player,data)
            .SelectMany(x=>x.Item.Runes)
            .Select(x=>data.Items.FirstOrDefault(r=>r.Id==x.Template))
            .Where(x=>x is not null&&x.Effect is "rune_fire_conversion" or "rune_lightning_conversion")
            .Select(x=>x!)
            .OrderByDescending(x=>x.Tier).ThenBy(x=>x.Id,StringComparer.Ordinal)
            .ToArray();
        if(conversions.Length==0) return ability.Element;
        return conversions[0].Effect=="rune_fire_conversion"?Element.Fire:Element.Lightning;
    }

    public static Affix? RollConditionalAffix(ItemDef def,Rarity rarity)
    {
        if((int)rarity<(int)Rarity.Rare||def.StackMax>1||def.Slot==""||def.Tags.Contains("boss_unique",StringComparer.Ordinal)) return null;
        string[] pool=def.Slot switch
        {
            "weapon"=>["execute","resource_ready","elemental_attunement"],
            "offhand"=>["resource_ready","shieldbound","supportive_aegis"],
            _=>["resource_ready","shieldbound","supportive_aegis"]
        };
        string effect=pool[RandomNumberGenerator.GetInt32(pool.Length)];
        string name=effect switch
        {
            "execute"=>"Executioner's",
            "resource_ready"=>"Resonant",
            "elemental_attunement"=>"Attuned",
            "shieldbound"=>"Holdfast",
            _=>"Aegiswoven"
        };
        return new(){Name=name,Stat=EffectPrefix+effect,Value=1};
    }

    public static IReadOnlyList<CraftSpecializationChoice> CraftSpecializations(RecipeDef recipe,Catalog data)
    {
        var output=data.Item(recipe.Output);
        var choices=new List<CraftSpecializationChoice>{new("","Standard finish",recipe.Requirement,"Use the ordinary quality roll without a targeted finish.")};
        if(output.StackMax>1||output.Slot=="") return choices;
        int focused=Math.Min(100,recipe.Requirement+10),resource=Math.Min(100,recipe.Requirement+15),element=Math.Min(100,recipe.Requirement+25);
        choices.Add(new("offense","Execution finish",focused,"Adds an execute effect against badly wounded enemies."));
        choices.Add(new("defense","Holdfast finish",focused,"Adds a shield-dependent armor and pressure engine."));
        choices.Add(new("resource","Class-engine finish",resource,"Adds a bonus that becomes active at your native class-resource READY threshold."));
        foreach(string key in new[]{"fire","frost","lightning","poison","nature","arcane","radiant","shadow"})
            choices.Add(new("element:"+key,char.ToUpperInvariant(key[0])+key[1..]+" attunement",element,"Fixes the crafted item's element and adds matching elemental pressure."));
        return choices;
    }

    public static string CraftSpecializationProblem(Character player,RecipeDef recipe,string specialization,Catalog data)
    {
        var choices=CraftSpecializations(recipe,data);
        var choice=choices.FirstOrDefault(x=>x.Id==specialization);
        if(choice is null) return "Unknown crafting specialization.";
        int skill=Progression.Level(player,recipe.Skill);
        return skill<choice.Requirement?$"Requires {data.Skill(recipe.Skill).Name} {choice.Requirement} for {choice.Name}.":"";
    }

    public static void ApplyCraftSpecialization(Item item,Character player,RecipeDef recipe,string specialization,Catalog data)
    {
        if(specialization=="") return;
        string problem=CraftSpecializationProblem(player,recipe,specialization,data);
        if(problem!="") throw new RuleException(problem);
        void Effect(string name,string effect)=>item.Affixes.Add(new(){Name="Crafted: "+name,Stat=EffectPrefix+effect,Value=1});
        switch(specialization)
        {
            case "offense": Effect("Execution finish","execute");break;
            case "defense": Effect("Holdfast finish","shieldbound");break;
            case "resource": Effect("Class-engine finish","resource_ready");break;
            default:
                if(!specialization.StartsWith("element:",StringComparison.Ordinal)) throw new RuleException("Unknown crafting specialization.");
                string key=specialization["element:".Length..];
                if(!Enum.TryParse<Element>(key,true,out var element)||element==Element.Physical) throw new RuleException("Unknown elemental specialization.");
                item.Element=element;Effect(element+" attunement","elemental_attunement");break;
        }
    }

    public static long ReforgeGoldCost(Item item,ItemDef def)
        =>Math.Max(75,(long)Math.Ceiling(Math.Max(1,def.Value)*(.45+.12*(int)item.Rarity)));
    public static int ReforgeDustCost(Item item,ItemDef def)=>Math.Clamp(1+def.Tier/3+(int)item.Rarity/2,1,8);

    public static void RerollAffix(Item item,int index,ItemDef def)
    {
        if(index<0||index>=item.Affixes.Count) throw new RuleException("Choose an affix to reforge.");
        var old=item.Affixes[index];
        if(!CanReforgeAffix(old)) throw new RuleException("Crafted specialization affixes are fixed; re-craft the item to choose another specialization.");
        if(IsEffectAffix(old))
        {
            string[] pool=(def.Slot=="weapon"?["execute","resource_ready","elemental_attunement"]:["resource_ready","shieldbound","supportive_aegis"])
                .Where(x=>x!=EffectId(old)).ToArray();
            string effect=pool[RandomNumberGenerator.GetInt32(pool.Length)];
            item.Affixes[index]=new(){Name=effect switch{"execute"=>"Executioner's","resource_ready"=>"Resonant","elemental_attunement"=>"Attuned","shieldbound"=>"Holdfast",_=>"Aegiswoven"},Stat=EffectPrefix+effect,Value=1};
            return;
        }
        string[] stats=def.Slot=="weapon"?["strength","dexterity","physical","crit","attack_speed","intellect","spell"]:["vitality","resolve","armor","health","evasion","spirit","resist_fire","resist_frost"];
        var candidates=stats.Where(x=>x!=old.Stat&&item.Affixes.Where((_,i)=>i!=index).All(a=>a.Stat!=x)).ToArray();
        if(candidates.Length==0) candidates=stats.Where(x=>x!=old.Stat).ToArray();
        string stat=candidates[RandomNumberGenerator.GetInt32(candidates.Length)];
        double value=1+Math.Round((def.Requirement/6.0+2)*RandomNumberGenerator.GetInt32(1001)/1000.0,1);
        item.Affixes[index]=new(){Name=stat.Replace('_',' '),Stat=stat,Value=value};
    }

    public static IReadOnlyList<string> TooltipLines(Item item,ItemDef def,Catalog data,Character? wearer=null)
    {
        var lines=new List<string>();
        if(KnownEffect(def.Effect))
        {
            string label=def.Tags.Contains("boss_unique",StringComparer.Ordinal)?"SIGNATURE EFFECT":def.Type=="offhand"?"OFFHAND IDENTITY":def.Type=="rune"?"RUNE TRANSFORM":"BUILD EFFECT";
            lines.Add(label+" · "+EffectDescription(def.Effect));
        }
        foreach(string effect in item.Affixes.Where(IsEffectAffix).Select(EffectId).Where(KnownEffect).Distinct(StringComparer.Ordinal))
            lines.Add((item.Affixes.Any(a=>EffectId(a)==effect&&a.Name.StartsWith("Crafted:",StringComparison.Ordinal))?"CRAFTED SPECIALIZATION":"CONDITIONAL AFFIX")+" · "+EffectDescription(effect));
        foreach(var socket in item.Runes)
        {
            var rune=data.Items.FirstOrDefault(x=>x.Id==socket.Template);
            if(rune is not null&&KnownEffect(rune.Effect)) lines.Add("SOCKETED "+rune.Name.ToUpperInvariant()+" · "+EffectDescription(rune.Effect));
        }
        foreach(string tag in def.Tags.Where(x=>x.StartsWith("set:",StringComparison.Ordinal)))
        {
            string id=tag["set:".Length..];
            if(!Sets.TryGetValue(id,out var set)) continue;
            int count=SetPieceCount(wearer,id,data);
            lines.Add($"{set.Name.ToUpperInvariant()} SET · {count}/3 equipped · {set.TwoPiece} {set.ThreePiece}");
        }
        if(def.Tags.Contains("boss_unique",StringComparer.Ordinal))
        {
            var source=data.Mobs.FirstOrDefault(x=>x.Boss&&x.Drops.Contains(def.Id,StringComparer.Ordinal));
            if(source is not null) lines.Add("TARGET FARM · "+source.Name+" is this relic's authored boss source.");
        }
        return lines.Distinct(StringComparer.Ordinal).ToArray();
    }

    public static void ValidateItem(Item item,ItemDef def,Catalog data,List<string> errors)
    {
        foreach(var affix in item.Affixes)
        {
            if(!double.IsFinite(affix.Value)||Math.Abs(affix.Value)>1000) { errors.Add("Invalid item affix value: "+item.Id);continue; }
            if(IsEffectAffix(affix))
            {
                if(!KnownEffect(EffectId(affix))) errors.Add("Unknown build effect affix: "+item.Id);
            }
            else if(string.IsNullOrWhiteSpace(affix.Stat)||affix.Stat.Length>64) errors.Add("Invalid item affix stat: "+item.Id);
        }
        if(def.Effect!=""&&def.Type is "weapon" or "offhand" or "rune"&& !KnownEffect(def.Effect))
            errors.Add("Unknown authored build effect: "+def.Id);
    }
}
