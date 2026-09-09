#!/usr/bin/env python3
from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one replacement, found {count}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


replace('src/Kairnfall.Core/Models.cs', '''    public int Quantity { get; set; } = 1;
    public Rarity Rarity { get; set; }
    public int Sockets { get; set; }
    public int Durability { get; set; } = 100;
    public List<Affix> Affixes { get; set; } = [];
    public List<SocketedRune> Runes { get; set; } = [];
''', '''    public int Quantity { get; set; } = 1;
    public Rarity Rarity { get; set; }
    // Null keeps historical saves compatible and falls back to the template element.
    public Element? Element { get; set; }
    // Rolled equipment skill levels are temporary while equipped and never satisfy equipment gates.
    public Dictionary<string,int> SkillBonuses { get; set; } = [];
    public int Sockets { get; set; }
    public int Durability { get; set; } = 100;
    public List<Affix> Affixes { get; set; } = [];
    public List<SocketedRune> Runes { get; set; } = [];
''')

replace('src/Kairnfall.Core/Mechanics.cs', '''    public static int Level(Character p,string skill) => SkillLevel(p.SkillXp.GetValueOrDefault(skill));
    public static long Total(Character p) => p.SkillXp.Values.Sum(x=>Math.Clamp(x,0,Threshold(SkillCap)));
''', '''    public static int BaseLevel(Character p,string skill) => SkillLevel(p.SkillXp.GetValueOrDefault(skill));
    public static int EquipmentSkillBonus(Character p,string skill)
    {
        int bonus=0;
        foreach(var id in p.Equipment.Values.Distinct())
        {
            var item=p.Inventory.FirstOrDefault(x=>x.Id==id);
            if(item is not null&&item.Durability>0) bonus+=Math.Max(0,item.SkillBonuses.GetValueOrDefault(skill));
        }
        return Math.Clamp(bonus,0,SkillCap-1);
    }
    public static int Level(Character p,string skill) => Math.Clamp(BaseLevel(p,skill)+EquipmentSkillBonus(p,skill),1,SkillCap);
    public static long Total(Character p) => p.SkillXp.Values.Sum(x=>Math.Clamp(x,0,Threshold(SkillCap)));
''')

replace('src/Kairnfall.Core/Mechanics.cs', '''    public static double Resist(DerivedStats stats,Element e)=>Math.Clamp(stats.Bonus("resist_"+e.ToString().ToLowerInvariant())/100,-0.5,0.75);
    public static bool Roll(double probability)=>RandomNumberGenerator.GetInt32(1000000)<Math.Clamp(probability,0,1)*1000000;
''', '''    public static double Resist(DerivedStats stats,Element e)=>Math.Clamp(stats.Bonus("resist_"+e.ToString().ToLowerInvariant())/100,-0.5,0.75);
    public static bool ElementStrongAgainst(Element attack,Element target)=> (attack,target) switch
    {
        (Element.Fire,Element.Nature) or (Element.Fire,Element.Frost) => true,
        (Element.Nature,Element.Lightning) or (Element.Nature,Element.Poison) => true,
        (Element.Lightning,Element.Frost) or (Element.Lightning,Element.Arcane) => true,
        (Element.Frost,Element.Poison) or (Element.Frost,Element.Shadow) => true,
        (Element.Poison,Element.Arcane) or (Element.Poison,Element.Radiant) => true,
        (Element.Arcane,Element.Shadow) or (Element.Arcane,Element.Fire) => true,
        (Element.Shadow,Element.Radiant) or (Element.Shadow,Element.Nature) => true,
        (Element.Radiant,Element.Fire) or (Element.Radiant,Element.Lightning) => true,
        _ => false
    };
    public static int ElementRelationship(Element attack,Element target)
    {
        if(attack==Element.Physical||target==Element.Physical||attack==target) return 0;
        return ElementStrongAgainst(attack,target)?1:ElementStrongAgainst(target,attack)?-1:0;
    }
    public static double ElementMultiplier(Element attack,Element target,int attackerPoints=0,int defenderPoints=0)
    {
        int relation=ElementRelationship(attack,target);
        if(relation==0) return 1;
        // Attunement increases both the reward and the risk of elemental specialization.
        double magnitude=Math.Min(.25,.05+.0125*Math.Clamp(attackerPoints+defenderPoints,0,16));
        return 1+relation*magnitude;
    }
    public static bool Roll(double probability)=>RandomNumberGenerator.GetInt32(1000000)<Math.Clamp(probability,0,1)*1000000;
''')

old_items = '''    public static Rarity RollRarity(int bonus=0)
    {
        int n=RandomNumberGenerator.GetInt32(10000)-Math.Clamp(bonus,0,500);
        return n<5?Rarity.Relic:n<25?Rarity.Mythic:n<100?Rarity.Legendary:n<350?Rarity.Epic:n<1200?Rarity.Rare:n<3500?Rarity.Uncommon:Rarity.Common;
    }
    public static Item Create(Catalog catalog,string template,int quantity=1,Rarity rarity=Rarity.Common)
    {
        var def=catalog.Item(template);
        if(quantity<1||quantity>999) throw new RuleException("Invalid item quantity.");
        var item=new Item{Template=template,Quantity=quantity,Rarity=def.StackMax>1?Rarity.Common:rarity};
        if(def.Slot!=""&&def.Type!="tool")
        {
            item.Sockets=Math.Min(4,(int)item.Rarity/2+(CombatMath.Roll(0.1)?1:0));
            string[] pool=def.Slot=="weapon"?["strength","dexterity","physical","crit","attack_speed","intellect","spell"]:["vitality","resolve","armor","health","evasion","spirit","resist_fire","resist_frost"];
            for(int n=0;n<Math.Min(4,(int)item.Rarity);n++)
            {
                var key=pool[RandomNumberGenerator.GetInt32(pool.Length)];
                if(item.Affixes.Any(x=>x.Stat==key)) continue;
                item.Affixes.Add(new(){Name=key.Replace('_',' '),Stat=key,Value=1+Math.Round((def.Requirement/6.0+2)*CombatMath.RandomUnit(),1)});
            }
        }
        return item;
    }
'''
new_items = '''    public static Rarity RollRarity(int bonus=0)
    {
        // Approximate natural drop rates: 65% Common, 23% Uncommon, 8.5% Rare,
        // 2.5% Epic, 0.75% Legendary, 0.2% Mythic and 0.05% Relic.
        int n=RandomNumberGenerator.GetInt32(10000)-Math.Clamp(bonus,0,500);
        return n<5?Rarity.Relic:n<25?Rarity.Mythic:n<100?Rarity.Legendary:n<350?Rarity.Epic:n<1200?Rarity.Rare:n<3500?Rarity.Uncommon:Rarity.Common;
    }
    public static (int Min,int Max) SkillBonusRange(Rarity rarity)
    {
        int minimum=(int)rarity;
        return (minimum,minimum+1);
    }
    public static int CraftRarityRequirement(Rarity rarity,int baseRequirement)
    {
        int[] offsets=[0,3,8,15,25,35,45];
        return Math.Clamp(baseRequirement+offsets[Math.Clamp((int)rarity,0,offsets.Length-1)],1,Progression.SkillCap);
    }
    public static Rarity RollCraftRarity(int skillLevel,int baseRequirement)
    {
        skillLevel=Math.Clamp(skillLevel,1,Progression.SkillCap);
        (Rarity rarity,double chance)[] rolls=[
            (Rarity.Relic,.00035),(Rarity.Mythic,.0015),(Rarity.Legendary,.006),
            (Rarity.Epic,.025),(Rarity.Rare,.08),(Rarity.Uncommon,.22)];
        foreach(var (rarity,baseChance) in rolls)
        {
            int gate=CraftRarityRequirement(rarity,baseRequirement);
            if(skillLevel<gate) continue;
            double mastery=1+Math.Min(1,(skillLevel-gate)/25.0);
            if(CombatMath.Roll(baseChance*mastery)) return rarity;
        }
        return Rarity.Common;
    }
    private static int RollSkillBonusTotal(Rarity rarity)
    {
        var range=SkillBonusRange(rarity);
        double upperChance=Math.Max(.08,.20-.02*(int)rarity);
        return range.Min+(CombatMath.Roll(upperChance)?1:0);
    }
    private static string RollSkill(Catalog catalog,ItemDef def,Character? source)
    {
        if(source is not null)
        {
            var affinity=catalog.Class(source.Class).Affinity.Where(x=>catalog.Skills.Any(s=>s.Id==x)).ToArray();
            if(affinity.Length>0&&CombatMath.Roll(.65)) return affinity[RandomNumberGenerator.GetInt32(affinity.Length)];
        }
        if(def.Skill!=""&&catalog.Skills.Any(x=>x.Id==def.Skill)&&CombatMath.Roll(.35)) return def.Skill;
        return catalog.Skills[RandomNumberGenerator.GetInt32(catalog.Skills.Count)].Id;
    }
    private static Element RollElement(ItemDef def,Rarity rarity)
    {
        if(def.Element!=Element.Physical||def.Tags.Contains("boss_unique",StringComparer.Ordinal)) return def.Element;
        double[] chances=[.05,.10,.18,.30,.45,.65,.85];
        if(!CombatMath.Roll(chances[Math.Clamp((int)rarity,0,chances.Length-1)])) return Element.Physical;
        return (Element)RandomNumberGenerator.GetInt32(1,Enum.GetValues<Element>().Length);
    }
    public static Element ElementOf(Item item,ItemDef def)=>item.Element??def.Element;
    public static int ElementPoints(Item item,ItemDef def)
    {
        if(ElementOf(item,def)==Element.Physical||item.Durability<=0) return 0;
        return 1+(int)item.Rarity+(def.Tags.Contains("boss_unique",StringComparer.Ordinal)?2:0);
    }
    public static int EquippedElementPoints(Character p,Element element,Catalog catalog)
    {
        if(element==Element.Physical) return 0;
        int total=0;
        foreach(var id in p.Equipment.Values.Distinct())
        {
            var item=p.Inventory.FirstOrDefault(x=>x.Id==id);
            if(item is null) continue;
            var def=catalog.Item(item.Template);
            if(ElementOf(item,def)==element) total+=ElementPoints(item,def);
        }
        return total;
    }
    public static Element DominantElement(Character p,Catalog catalog)
    {
        return Enum.GetValues<Element>().Where(x=>x!=Element.Physical)
            .Select(x=>(Element:x,Points:EquippedElementPoints(p,x,catalog)))
            .OrderByDescending(x=>x.Points).ThenBy(x=>(int)x.Element).FirstOrDefault() is var best&&best.Points>0?best.Element:Element.Physical;
    }
    public static Item Create(Catalog catalog,string template,int quantity=1,Rarity rarity=Rarity.Common,Character? source=null)
    {
        var def=catalog.Item(template);
        if(quantity<1||quantity>999) throw new RuleException("Invalid item quantity.");
        if(def.Tags.Contains("boss_unique",StringComparer.Ordinal)) rarity=Rarity.Relic;
        var item=new Item{Template=template,Quantity=quantity,Rarity=def.StackMax>1?Rarity.Common:rarity};
        if(def.Slot!=""&&def.Type!="tool")
        {
            item.Element=RollElement(def,item.Rarity);
            int skillPoints=RollSkillBonusTotal(item.Rarity);
            for(int point=0;point<skillPoints;point++)
            {
                string skill=RollSkill(catalog,def,source);
                item.SkillBonuses[skill]=item.SkillBonuses.GetValueOrDefault(skill)+1;
            }
            item.Sockets=Math.Min(4,(int)item.Rarity/2+(CombatMath.Roll(0.1)?1:0));
            string[] pool=def.Slot=="weapon"?["strength","dexterity","physical","crit","attack_speed","intellect","spell"]:["vitality","resolve","armor","health","evasion","spirit","resist_fire","resist_frost"];
            for(int n=0;n<Math.Min(4,(int)item.Rarity);n++)
            {
                var key=pool[RandomNumberGenerator.GetInt32(pool.Length)];
                if(item.Affixes.Any(x=>x.Stat==key)) continue;
                item.Affixes.Add(new(){Name=key.Replace('_',' '),Stat=key,Value=1+Math.Round((def.Requirement/6.0+2)*CombatMath.RandomUnit(),1)});
            }
        }
        return item;
    }
'''
replace('src/Kairnfall.Core/Mechanics.cs', old_items, new_items)

replace('src/Kairnfall.Core/Mechanics.cs', '''        bool stackable=def.StackMax>1&&item.Affixes.Count==0&&item.Runes.Count==0;
        var stacks=stackable?destination.Where(x=>x.Template==item.Template&&x.Rarity==item.Rarity&&x.Affixes.Count==0&&x.Runes.Count==0).ToList():[];
''', '''        bool stackable=def.StackMax>1&&item.Affixes.Count==0&&item.Runes.Count==0&&item.SkillBonuses.Count==0&&item.Element is null;
        var stacks=stackable?destination.Where(x=>x.Template==item.Template&&x.Rarity==item.Rarity&&x.Affixes.Count==0&&x.Runes.Count==0&&x.SkillBonuses.Count==0&&x.Element is null).ToList():[];
''')

replace('src/Kairnfall.Core/Mechanics.cs', '''        if(def.Skill!=""&&Progression.Level(p,def.Skill)<required) throw new RuleException($"Requires {catalog.Skill(def.Skill).Name} {required}. Your level: {Progression.Level(p,def.Skill)}.");
''', '''        if(def.Skill!=""&&Progression.BaseLevel(p,def.Skill)<required) throw new RuleException($"Requires {catalog.Skill(def.Skill).Name} {required}. Your trained level: {Progression.BaseLevel(p,def.Skill)}. Equipment skill bonuses do not satisfy equipment requirements.");
''')

replace('src/Kairnfall.Core/Mechanics.cs', '''            if(def is null||i.Quantity<1||i.Quantity>def.StackMax||i.Sockets<0||i.Sockets>4||i.Runes.Count>i.Sockets||i.Durability<0||i.Durability>100) errors.Add("Invalid item: "+i.Id);
            foreach(var r in i.Runes) if(!ids.Add(r.Id)||data.Items.All(x=>x.Id!=r.Template||x.Type!="rune")) errors.Add("Invalid socketed rune: "+r.Id);
''', '''            if(def is null||i.Quantity<1||i.Quantity>def.StackMax||i.Sockets<0||i.Sockets>4||i.Runes.Count>i.Sockets||i.Durability<0||i.Durability>100) errors.Add("Invalid item: "+i.Id);
            if(i.SkillBonuses.Any(x=>data.Skills.All(s=>s.Id!=x.Key)||x.Value<1||x.Value>7)||i.SkillBonuses.Values.Sum()>7) errors.Add("Invalid item skill bonus: "+i.Id);
            if(def is not null&&def.StackMax>1&&(i.SkillBonuses.Count>0||i.Element is not null)) errors.Add("Stackable item has instance equipment modifiers: "+i.Id);
            foreach(var r in i.Runes) if(!ids.Add(r.Id)||data.Items.All(x=>x.Id!=r.Template||x.Type!="rune")) errors.Add("Invalid socketed rune: "+r.Id);
''')

replace('src/Kairnfall.Core/EquipmentComparison.cs', '''            if (def.Skill != "" && Progression.Level(self, def.Skill) < required)
                blocked.Add($"Requires {data.Skill(def.Skill).Name} {required} (current {Progression.Level(self, def.Skill)}).");
''', '''            if (def.Skill != "" && Progression.BaseLevel(self, def.Skill) < required)
                blocked.Add($"Requires {data.Skill(def.Skill).Name} {required} (trained {Progression.BaseLevel(self, def.Skill)}; equipment bonuses do not count).");
''')

replace('src/Kairnfall.Core/RealmEconomy.cs', '''                double quality=(Progression.Level(p,recipe.Skill)-recipe.Requirement)*0.002;
                var rarity=CombatMath.Roll(0.04+quality)?Rarity.Rare:CombatMath.Roll(0.2+quality)?Rarity.Uncommon:Rarity.Common;
                Items.Add(p.Inventory,Items.Create(Data,output.Id,1,rarity),Data);
''', '''                var rarity=Items.RollCraftRarity(Progression.Level(p,recipe.Skill),recipe.Requirement);
                Items.Add(p.Inventory,Items.Create(Data,output.Id,1,rarity,p),Data);
''')

replace('src/Kairnfall.Core/RealmCombat.cs', '''        var stats=CombatMath.Stats(p,Data);
        ItemDef? weapon=null;
        if(p.Equipment.TryGetValue("weapon",out var weaponId))
        {
            var instance=Items.Owned(p,weaponId); Need(instance.Durability>0,"Your weapon needs repair."); weapon=Data.Item(instance.Template);
        }
''', '''        var stats=CombatMath.Stats(p,Data);
        ItemDef? weapon=null; Item? weaponItem=null;
        if(p.Equipment.TryGetValue("weapon",out var weaponId))
        {
            var instance=Items.Owned(p,weaponId); Need(instance.Durability>0,"Your weapon needs repair."); weapon=Data.Item(instance.Template); weaponItem=instance;
        }
''')

replace('src/Kairnfall.Core/RealmCombat.cs', '''        if(HandEquipment.IsProjectileWeapon(weapon))
        {
            State.Telegraphs.Add(new(){Zone=p.Zone,Source=p.Id,Position=mob.Position,Direction=p.Facing,Shape="projectile",Skill=skill,Element=weapon?.Element??Element.Physical,Radius=0.8,Power=raw,Resolves=State.Time+Math.Min(0.6,p.Position.Distance(mob.Position)/15)});
        }
        else HitCreature(p,mob,raw,weapon?.Element??Element.Physical,skill);
''', '''        Element attackElement=weapon is null?Element.Physical:Items.ElementOf(weaponItem!,weapon);
        if(HandEquipment.IsProjectileWeapon(weapon))
        {
            State.Telegraphs.Add(new(){Zone=p.Zone,Source=p.Id,Position=mob.Position,Direction=p.Facing,Shape="projectile",Skill=skill,Element=attackElement,Radius=0.8,Power=raw,Resolves=State.Time+Math.Min(0.6,p.Position.Distance(mob.Position)/15)});
        }
        else HitCreature(p,mob,raw,attackElement,skill);
''')

replace('src/Kairnfall.Core/RealmCombat.cs', '''        double bonus=Math.Clamp(stats.Bonus("damage_"+element.ToString().ToLowerInvariant())/100,0,2);
        double empower=Math.Clamp(CombatMath.StatusPower(p.Statuses,"empower",State.Time),0,0.5);
        double damage=CombatMath.Damage(raw*(1+bonus+empower),element==Element.Physical?def.Armor:def.Armor*0.2,def.Resistances.GetValueOrDefault(element));
''', '''        double bonus=Math.Clamp(stats.Bonus("damage_"+element.ToString().ToLowerInvariant())/100,0,2);
        double empower=Math.Clamp(CombatMath.StatusPower(p.Statuses,"empower",State.Time),0,0.5);
        int attunement=Items.EquippedElementPoints(p,element,Data);
        double matchup=CombatMath.ElementMultiplier(element,def.Element,attunement,0);
        double damage=CombatMath.Damage(raw*(1+bonus+empower)*matchup,element==Element.Physical?def.Armor:def.Armor*0.2,def.Resistances.GetValueOrDefault(element));
''')

replace('src/Kairnfall.Core/RealmCombat.cs', '''        foreach(var template in def.Drops)
        {
            var item=Data.Item(template); bool guaranteed=item.Type is "material" or "ore" or "wood" or "animal_material";
            if(guaranteed||CombatMath.Roll(def.Boss?0.8:0.25)) pile.Items.Add(Items.Create(Data,template,1,item.StackMax==1?Items.RollRarity(def.Boss?300:0):Rarity.Common));
        }
        if(pile.Items.Count==0&&def.Drops.Length>0) pile.Items.Add(Items.Create(Data,def.Drops[0]));
''', '''        var ordinaryDrops=def.Drops.Where(template=>!Data.Item(template).Tags.Contains("boss_unique",StringComparer.Ordinal)).ToArray();
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
''')

replace('src/Kairnfall.Core/RealmCombat.cs', '''        double damage=CombatMath.Damage(raw,element==Element.Physical?stats.Armor:stats.Armor*0.2,CombatMath.Resist(stats,element));
''', '''        Element defenseElement=Items.DominantElement(p,Data);
        int defensePoints=Items.EquippedElementPoints(p,defenseElement,Data);
        double matchup=CombatMath.ElementMultiplier(element,defenseElement,0,defensePoints);
        double damage=CombatMath.Damage(raw*matchup,element==Element.Physical?stats.Armor:stats.Armor*0.2,CombatMath.Resist(stats,element));
''')

replace('tools/build_content.py', '''from content_src import skills, items, abilities, mobs, world, quests, presentation, gear_progression
''', '''from content_src import skills, items, abilities, mobs, boss_uniques, world, quests, presentation, gear_progression
''')
replace('tools/build_content.py', '''    for module in [skills,items,abilities,mobs,world,quests,presentation,gear_progression]: module.build(data)
''', '''    for module in [skills,items,abilities,mobs,boss_uniques,world,quests,presentation,gear_progression]: module.build(data)
''')

boss_uniques = '''"""Boss-only signature relics: five milestone weapons for each playable class."""
from copy import deepcopy

MILESTONES = [
    (25, 'steel', 'kilnheart'),
    (45, 'silver', 'glasswing'),
    (65, 'cobalt', 'cinder_marshal'),
    (85, 'obsidian', 'the_unwritten'),
    (100, 'aetherium', 'aether_heart'),
]

SIGNATURES = {
    'vanguard': ('sword', 'Radiant', ['Oathsteel','Gatewarden','Bastion Edge','Crownward','Last Citadel'], {'vitality':2,'resolve':2}),
    'berserker': ('greataxe', 'Fire', ['Red Wake','Skullstorm','Ashhowl','Ruin Feast','Worldsplitter'], {'strength':3,'crit':1}),
    'ranger': ('bow', 'Lightning', ['Gale Thorn','Skytrace','Tempest String','Starhunter','Horizon Piercer'], {'dexterity':3,'accuracy':2}),
    'rogue': ('dagger', 'Poison', ['Whisperfang','Nightglass','Venom Psalm','Eclipse Needle','Kingless Mercy'], {'dexterity':3,'crit':2}),
    'arcanist': ('staff', 'Arcane', ['Prism Reed','Astral Measure','Null Canticle','Eventide Spire','Aether Equation'], {'intellect':3,'spell':3}),
    'warden': ('staff', 'Nature', ['Rootsong','Hartwood','Briar Covenant','Verdant Moon','First Grove'], {'spirit':3,'healing':3}),
    'templar': ('mace', 'Radiant', ['Dawn Bell','Mercy Weight','Sunward Vow','Saintfire','Last Benediction'], {'spirit':3,'armor':3}),
    'spellblade': ('sword', 'Shadow', ['Riftbrand','Hexsteel','Mirror Edge','Void Accord','Kairnfall Edge'], {'intellect':2,'spell':3}),
}


def _slug(text):
    return ''.join(c.lower() if c.isalnum() else '_' for c in text).strip('_').replace('__','_')


def build(data):
    items = {item['id']: item for item in data['items']}
    bosses = {mob['id']: mob for mob in data['mobs'] if mob.get('boss')}
    classes = {entry['id'] for entry in data['classes']}
    if classes != set(SIGNATURES):
        raise ValueError('Boss unique signatures must cover every playable class exactly once.')
    for class_id, (family, element, names, bonus_stats) in SIGNATURES.items():
        if len(names) != len(MILESTONES):
            raise ValueError(class_id + ': expected one unique name per milestone')
        for index, ((level, material, boss_id), name) in enumerate(zip(MILESTONES, names)):
            base_id = material + '_' + family
            base = deepcopy(items[base_id])
            ident = 'boss_' + class_id + '_' + str(level) + '_' + _slug(name)
            base['id'] = ident
            base['name'] = name
            base['requirement'] = level
            base['icon'] = 'items/' + ident + '.png'
            base['element'] = element
            base['power'] = round(base.get('power', 0) * 1.22 + level * 0.04, 1)
            base['value'] = int(base.get('value', 1) * 3 + level * 12)
            stats = dict(base.get('stats', {}))
            scale = 1 + index // 2
            for key, value in bonus_stats.items():
                stats[key] = round(stats.get(key, 0) + value * scale, 1)
            base['stats'] = stats
            tags = list(dict.fromkeys(list(base.get('tags', [])) + [
                'boss_unique', 'class:' + class_id, 'unique_level:' + str(level), 'base:' + base_id]))
            base['tags'] = tags
            base['description'] = (name + ' is a boss-forged signature relic. It is stronger than ordinary ' +
                                   family.replace('_',' ') + ' equipment near skill level ' + str(level) +
                                   ' and can enter the world only through its assigned boss loot table.')
            data['items'].append(base)
            items[ident] = base
            bosses[boss_id]['drops'].append(ident)
'''
Path('content_src/boss_uniques.py').write_text(boss_uniques, encoding='utf-8')

replace('client/Scripts/Ui.cs', '''    public static Color RarityColor(Rarity rarity) => RarityColors[Math.Clamp((int)rarity, 0, RarityColors.Length - 1)];
    public static string Words(string text) => System.Globalization.CultureInfo.InvariantCulture.TextInfo.ToTitleCase(text.Replace('_', ' '));
''', '''    public static Color RarityColor(Rarity rarity) => RarityColors[Math.Clamp((int)rarity, 0, RarityColors.Length - 1)];
    public static Color ElementColor(Element element) => element switch
    {
        Element.Fire => new("e39b63"), Element.Frost => new("97d2db"), Element.Lightning => new("e2d98a"), Element.Nature => new("9ac77d"),
        Element.Poison => new("b6cc78"), Element.Arcane => new("b49ad9"), Element.Radiant => new("f0e0ae"), Element.Shadow => new("a38ebb"), _ => new("ceb49d")
    };
    public static string ElementGlyph(Element element) => element switch
    {
        Element.Fire => "F", Element.Frost => "I", Element.Lightning => "L", Element.Nature => "N", Element.Poison => "P",
        Element.Arcane => "A", Element.Radiant => "R", Element.Shadow => "S", _ => ""
    };
    public static string Words(string text) => System.Globalization.CultureInfo.InvariantCulture.TextInfo.ToTitleCase(text.Replace('_', ' '));
''')

replace('client/Scripts/Ui.cs', '''    public string Bag { get; set; } = "inventory";
    public bool Equipped { get; set; }
''', '''    public string Bag { get; set; } = "inventory";
    public Element Element { get; set; } = Element.Physical;
    public bool Equipped { get; set; }
''')

replace('client/Scripts/Ui.cs', '''        if (Icon is not null) DrawTextureRect(Icon, PixelPresentation.InventoryIconRect(Size,Icon.GetSize()), false);
        if (Equipped) DrawString(ThemeDB.FallbackFont, new Vector2(4, 14), "E", HorizontalAlignment.Left, -1, 11, Ui.Gold);
''', '''        if (Icon is not null) DrawTextureRect(Icon, PixelPresentation.InventoryIconRect(Size,Icon.GetSize()), false);
        if (Element != Element.Physical)
        {
            var badge = new Rect2(Size.X - 18, 3, 15, 15);
            DrawRect(badge, Ui.Ink); DrawRect(badge, Ui.ElementColor(Element), false, 1);
            DrawString(ThemeDB.FallbackFont, new Vector2(badge.Position.X + 4, badge.Position.Y + 12), Ui.ElementGlyph(Element), HorizontalAlignment.Left, -1, 10, Ui.ElementColor(Element));
        }
        if (Equipped) DrawString(ThemeDB.FallbackFont, new Vector2(4, 14), "E", HorizontalAlignment.Left, -1, 11, Ui.Gold);
''')

replace('client/Scripts/GameRoot.Inventory.cs', '''        var def = Data.Item(item.Template); var text = new StringBuilder();
        text.AppendLine(def.Name).AppendLine(item.Rarity + " · " + Ui.Words(def.Type));
''', '''        var def = Data.Item(item.Template); var text = new StringBuilder();
        Element itemElement=Items.ElementOf(item,def);
        text.AppendLine(def.Name).AppendLine(item.Rarity + " · " + Ui.Words(def.Type) + (itemElement==Element.Physical?"":" · "+itemElement));
''')

replace('client/Scripts/GameRoot.Inventory.cs', '''        if (def.Slot == "weapon") text.AppendLine($"Range: {def.Range:0.0} tiles · {def.Element}");
        foreach (var stat in def.Stats) text.AppendLine($"{stat.Value:+0.0;-0.0;0} {Ui.Words(stat.Key)}");
        foreach (var affix in item.Affixes) text.AppendLine($"{affix.Value:+0.0;-0.0;0} {Ui.Words(affix.Stat)}");
''', '''        if (def.Slot == "weapon") text.AppendLine($"Range: {def.Range:0.0} tiles");
        if (def.Slot != "" && itemElement != Element.Physical) text.AppendLine($"Element: {itemElement} · {Items.ElementPoints(item,def)} attunement points");
        foreach (var stat in def.Stats) text.AppendLine($"{stat.Value:+0.0;-0.0;0} {Ui.Words(stat.Key)}");
        foreach (var affix in item.Affixes) text.AppendLine($"{affix.Value:+0.0;-0.0;0} {Ui.Words(affix.Stat)}");
        foreach (var skill in item.SkillBonuses.OrderBy(x=>x.Key)) text.AppendLine($"+{skill.Value} {Data.Skill(skill.Key).Name} level while equipped");
''')

replace('client/Scripts/GameRoot.Inventory.cs', '''            Item = item, Icon = Assets.Icon(item.Template), Bag = bag,
            Equipped = Snapshot is { } s && Items.Equipped(s.Self, item.Id), Selected = item.Id == selectedItem,
''', '''            Item = item, Icon = Assets.Icon(item.Template), Bag = bag, Element = Items.ElementOf(item,Data.Item(item.Template)),
            Equipped = Snapshot is { } s && Items.Equipped(s.Self, item.Id), Selected = item.Id == selectedItem,
''')

replace('client/Scripts/GameRoot.Inventory.cs', '''                slot.Item = item; slot.Selected = item.Id == selectedItem; slot.Equipped = Items.Equipped(self, item.Id);
                slot.TooltipText = SlotTooltip(item) + (group.Key == 2 ? "\n" + ExperienceRules.EquipmentProblem(self, item, Data) : "");
''', '''                slot.Item = item; slot.Selected = item.Id == selectedItem; slot.Equipped = Items.Equipped(self, item.Id);
                slot.Element = Items.ElementOf(item,Data.Item(item.Template));
                slot.TooltipText = SlotTooltip(item) + (group.Key == 2 ? "\n" + ExperienceRules.EquipmentProblem(self, item, Data) : "");
''')

replace('client/Scripts/CompactItemCard.cs', '''        var metadata = Centered(item.Rarity + " · " + Ui.Words(def.Type) + (self is not null && Items.Equipped(self, item.Id) ? " · Equipped" : ""), metaSize, Ui.Muted);
''', '''        int skillTotal=item.SkillBonuses.Values.Sum();
        Element actualElement=Items.ElementOf(item,def);
        string rolledMeta=(skillTotal>0?$" · +{skillTotal} skill":"")+(actualElement!=Element.Physical?$" · {actualElement}":"");
        var metadata = Centered(item.Rarity + " · " + Ui.Words(def.Type) + rolledMeta + (self is not null && Items.Equipped(self, item.Id) ? " · Equipped" : ""), metaSize, Ui.Muted);
''')

replace('client/Scripts/CompactItemCard.cs', '''        if (info.ComparedWith != "")
        {
''', '''        if (!compact && item.SkillBonuses.Count > 0)
        {
            foreach (var skill in item.SkillBonuses.OrderBy(x=>x.Key))
            {
                var bonus = Centered($"+{skill.Value} {data.Skill(skill.Key).Name} level while equipped", metaSize, Ui.Success);
                bonus.Name = "ItemSkillBonus"; box.AddChild(bonus);
            }
        }

        if (info.ComparedWith != "")
        {
''')

replace('client/Scripts/CompactItemCard.cs', '''        if (def.Slot == "weapon")
        {
            var element = Centered(compact ? "Element: " + def.Element : def.Element + " · Lower attack interval is faster", compact ? metaSize : 11, Ui.Muted);
            element.Name = "ItemElement";
            box.AddChild(element);
        }
''', '''        if (!compact && (def.Slot == "weapon" || actualElement != Element.Physical))
        {
            string points=actualElement==Element.Physical?"":$" · {Items.ElementPoints(item,def)} attunement points";
            var element = Centered(actualElement + points + (def.Slot=="weapon"?" · Lower attack interval is faster":""), 11, Ui.Muted);
            element.Name = "ItemElement";
            box.AddChild(element);
        }
''')

replace('client/Scripts/HudWidgets.cs', '''using Godot;

namespace Kairnfall.Client;
''', '''using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;
''')

replace('client/Scripts/HudWidgets.cs', '''    public string BlockReason { get; private set; } = "";
    private double cooldownLength = 1;
''', '''    public string BlockReason { get; private set; } = "";
    public Element AbilityElement { get; private set; } = Element.Physical;
    private double cooldownLength = 1;
''')

replace('client/Scripts/HudWidgets.cs', '''    public void Present(Texture2D? icon, string key, double remaining, double duration, string reason, string tooltip, bool connected)
    {
        AbilityIcon = icon; KeyLabel = key; CooldownSeconds = Math.Max(0, remaining);
''', '''    public void Present(Texture2D? icon, string key, double remaining, double duration, Element element, string reason, string tooltip, bool connected)
    {
        AbilityIcon = icon; KeyLabel = key; CooldownSeconds = Math.Max(0, remaining); AbilityElement=element;
''')

replace('client/Scripts/HudWidgets.cs', '''            if (CooldownSeconds > 0)
                DrawRect(new Rect2(area.Position, new Vector2(area.Size.X, area.Size.Y * (float)Math.Clamp(CooldownSeconds / cooldownLength, 0, 1))), new Color(0, 0, 0, .72f));
        }
        var font = GetThemeDefaultFont();
''', '''            if (CooldownSeconds > 0)
                DrawRect(new Rect2(area.Position, new Vector2(area.Size.X, area.Size.Y * (float)Math.Clamp(CooldownSeconds / cooldownLength, 0, 1))), new Color(0, 0, 0, .72f));
            if(AbilityElement!=Element.Physical)
            {
                var badge=new Rect2(area.Position.X+area.Size.X-14,area.Position.Y+1,13,13);
                DrawRect(badge,Ui.Ink); DrawRect(badge,Ui.ElementColor(AbilityElement),false,1);
                DrawString(GetThemeDefaultFont(),new Vector2(badge.Position.X+3,badge.Position.Y+11),Ui.ElementGlyph(AbilityElement),HorizontalAlignment.Left,-1,9,Ui.ElementColor(AbilityElement));
            }
        }
        var font = GetThemeDefaultFont();
''')

replace('client/Scripts/GameRoot.Hud.cs', '''                button.Present(null, key, 0, 1, "", "Assign an ability from Arts [B].", Online); continue;
''', '''                button.Present(null, key, 0, 1, Element.Physical, "", "Assign an ability from Arts [B].", Online); continue;
''')
replace('client/Scripts/GameRoot.Hud.cs', '''            button.Present(Assets.AbilityIcon(id), key, cooldown, ability.Cooldown, problem,
                AbilityTooltip(self, ability) + (problem == "" ? "" : "\n" + problem), Online && gameWindow is null && !Typing && applicationFocused);
''', '''            button.Present(Assets.AbilityIcon(id), key, cooldown, ability.Cooldown, ability.Element, problem,
                AbilityTooltip(self, ability) + (problem == "" ? "" : "\n" + problem), Online && gameWindow is null && !Typing && applicationFocused);
''')

replace('atelier/forge/smith.py', '''from PIL import Image
''', '''from PIL import Image, ImageChops, ImageDraw, ImageFilter
''')

boss_finish = '''\n\ndef _boss_unique_finish(image, item):
    """Give boss-only relics a hard-edged elemental aura and an ID-stable sigil."""
    if 'boss_unique' not in item.get('tags', ()) or image.mode != 'RGBA':
        return image
    alpha = image.getchannel('A')
    outer = alpha.filter(ImageFilter.MaxFilter(5))
    inner = alpha.filter(ImageFilter.MaxFilter(3))
    ring = ImageChops.subtract(outer, inner).point(lambda value: min(170, value))
    element = item.get('element', 'Arcane')
    hex_color = pigment.ELEMENTS.get(element, '#d7c47f').lstrip('#')
    rgb = tuple(int(hex_color[index:index + 2], 16) for index in (0, 2, 4))
    aura = Image.new('RGBA', image.size, rgb + (0,))
    aura.putalpha(ring)
    out = Image.alpha_composite(aura, image)
    draw = ImageDraw.Draw(out)
    seed = pigment.keyed(str(item.get('id', '')) + '|boss-unique-aura', 2**24)
    bright = tuple(min(255, channel + 58) for channel in rgb) + (235,)
    # Four two-pixel sparks orbit the silhouette. The stable item ID controls placement.
    placed = 0
    for attempt in range(32):
        x = 2 + ((seed >> ((attempt * 3) % 20)) + attempt * 7) % 28
        y = 2 + ((seed >> ((attempt * 5 + 2) % 20)) + attempt * 11) % 28
        if alpha.getpixel((x, y)) != 0:
            continue
        draw.point((x, y), fill=bright)
        nx = x + (1 if (seed >> attempt) & 1 else -1)
        if 0 <= nx < 32 and alpha.getpixel((nx, y)) == 0:
            draw.point((nx, y), fill=rgb + (190,))
        placed += 1
        if placed == 4:
            break
    # A tiny deliberate corner sigil makes same-family relics visually distinct without blur.
    sx, sy = 3, 3
    shape = seed % 4
    if shape == 0:
        draw.line([(sx, sy + 3), (sx + 2, sy), (sx + 4, sy + 3)], fill=bright, width=1)
    elif shape == 1:
        draw.rectangle((sx + 1, sy, sx + 3, sy + 3), outline=bright, width=1)
    elif shape == 2:
        draw.line([(sx, sy), (sx + 4, sy + 4)], fill=bright, width=1); draw.line([(sx + 4, sy), (sx, sy + 4)], fill=bright, width=1)
    else:
        draw.line([(sx + 2, sy), (sx + 2, sy + 4)], fill=bright, width=1); draw.line([(sx, sy + 2), (sx + 4, sy + 2)], fill=bright, width=1)
    return out
'''
replace('atelier/forge/smith.py', '''\n\nTYPE_ICONS = {
''', boss_finish + '''\n\nTYPE_ICONS = {
''')
replace('atelier/forge/smith.py', '''    return _polish_icon(image, item)
''', '''    return _boss_unique_finish(_polish_icon(image, item), item)
''')

replace('tests/Kairnfall.Tests/Program.cs', '''Test("All classes create valid characters and starter equipment",()=>
''', '''Test("Rarity skill bonus ranges and crafting gates are ordered",()=>
{
    int previous=0;
    foreach(Rarity rarity in Enum.GetValues<Rarity>())
    {
        var range=Items.SkillBonusRange(rarity);
        Check(range.Min==(int)rarity&&range.Max==(int)rarity+1,"Unexpected skill bonus range for "+rarity);
        int gate=Items.CraftRarityRequirement(rarity,10); Check(gate>=previous,"Craft rarity gate moved backward."); previous=gate;
        var r=NewRealm(); var p=NewPlayer(r,"Rarity "+rarity);
        var item=Items.Create(data,"steel_sword",1,rarity,p);
        int total=item.SkillBonuses.Values.Sum(); Check(total>=range.Min&&total<=range.Max,"Rolled skill bonus outside rarity range: "+rarity);
        Check(item.SkillBonuses.Keys.All(skill=>data.Skills.Any(x=>x.Id==skill)),"Unknown rolled skill.");
    }
    for(int n=0;n<100;n++) Check(Items.RollCraftRarity(1,1)==Rarity.Common,"Craft rarity bypassed its skill gate.");
});
Test("Equipment skill levels work but never satisfy equipment requirements",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var targetDef=data.Item("steel_sword");
    int required=BeginnerProgression.EquipmentRequirement(targetDef);
    p.SkillXp[targetDef.Skill]=Progression.Threshold(Math.Max(1,required-1));
    var belt=Items.Create(data,"linen_heavy_belt",1,Rarity.Common,p); belt.SkillBonuses.Clear(); belt.SkillBonuses[targetDef.Skill]=1;
    Items.Add(p.Inventory,belt,data); Items.Equip(p,belt.Id,data);
    Check(Progression.BaseLevel(p,targetDef.Skill)==Math.Max(1,required-1),"Base level changed from equipment.");
    Check(Progression.Level(p,targetDef.Skill)>=required,"Equipment skill bonus did not raise effective level.");
    var target=Items.Create(data,targetDef.Id,1,Rarity.Common,p); Items.Add(p.Inventory,target,data);
    bool rejected=false; try { Items.Equip(p,target.Id,data); } catch(RuleException) { rejected=true; }
    Check(rejected,"Equipment bonus incorrectly satisfied another equipment requirement.");
});
Test("Element relationships are balanced and attunement scales matchup magnitude",()=>
{
    var elements=Enum.GetValues<Element>().Where(x=>x!=Element.Physical).ToArray();
    foreach(var element in elements)
    {
        Check(elements.Count(target=>CombatMath.ElementRelationship(element,target)==1)==2,"Element does not have exactly two strengths: "+element);
        Check(elements.Count(target=>CombatMath.ElementRelationship(element,target)==-1)==2,"Element does not have exactly two weaknesses: "+element);
        foreach(var target in elements) Check(CombatMath.ElementRelationship(element,target)==-CombatMath.ElementRelationship(target,element),"Element relationship is not reciprocal.");
    }
    double strong=CombatMath.ElementMultiplier(Element.Fire,Element.Nature);
    double attuned=CombatMath.ElementMultiplier(Element.Fire,Element.Nature,8,0);
    double weak=CombatMath.ElementMultiplier(Element.Fire,Element.Arcane,8,0);
    Check(strong>1&&attuned>strong&&weak<1,"Element matchup or attunement scaling failed.");
    Check(CombatMath.ElementMultiplier(Element.Physical,Element.Fire,20,20)==1,"Physical must remain neutral.");
});
Test("All classes create valid characters and starter equipment",()=>
''')

rarity_test = '''import hashlib
import unittest

from tools import build_content
from atelier.forge import smith


class RarityElementUniqueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_content.build()
        cls.items = {item['id']: item for item in cls.data['items']}
        cls.mobs = {mob['id']: mob for mob in cls.data['mobs']}
        cls.uniques = [item for item in cls.data['items'] if 'boss_unique' in item.get('tags', [])]

    def test_five_boss_uniques_per_class_at_requested_milestones(self):
        self.assertEqual(40, len(self.uniques))
        for entry in self.data['classes']:
            owned = [item for item in self.uniques if 'class:' + entry['id'] in item['tags']]
            self.assertEqual([25,45,65,85,100], sorted(item['requirement'] for item in owned), entry['id'])

    def test_uniques_are_stronger_and_boss_only(self):
        recipe_outputs = {recipe['output'] for recipe in self.data['recipes']}
        nonboss_drops = {drop for mob in self.data['mobs'] if not mob.get('boss') for drop in mob['drops']}
        boss_drops = {drop for mob in self.data['mobs'] if mob.get('boss') for drop in mob['drops']}
        for item in self.uniques:
            base_tag = next(tag for tag in item['tags'] if tag.startswith('base:'))
            base = self.items[base_tag.split(':',1)[1]]
            self.assertGreater(item['power'], base['power'], item['id'])
            self.assertNotIn(item['id'], recipe_outputs)
            self.assertNotIn(item['id'], nonboss_drops)
            self.assertIn(item['id'], boss_drops)
            self.assertNotEqual('Physical', item['element'])
        assigned = [mob for mob in self.data['mobs'] if mob.get('boss') and any(drop in {u['id'] for u in self.uniques} for drop in mob['drops'])]
        self.assertEqual(5, len(assigned))
        self.assertTrue(all(sum(drop in {u['id'] for u in self.uniques} for drop in mob['drops']) == 8 for mob in assigned))

    def test_unique_icons_are_distinct_pixel_art_with_aura(self):
        hashes = []
        for item in self.uniques:
            image = smith.icon(item)
            self.assertEqual((32,32), image.size)
            self.assertEqual('RGBA', image.mode)
            self.assertGreater(image.getchannel('A').getbbox()[2], 0)
            hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
        self.assertEqual(40, len(set(hashes)))


if __name__ == '__main__':
    unittest.main()
'''
Path('tests/handoff/test_rarity_elements_uniques.py').write_text(rarity_test, encoding='utf-8')

print('rarity/element/boss-unique source patch applied')
