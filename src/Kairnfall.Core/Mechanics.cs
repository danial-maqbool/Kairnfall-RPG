using System.Security.Cryptography;

namespace Kairnfall.Core;

public static class Progression
{
    public const int SkillCap=100;
    public const int PlayerCap=200;
    public static long Threshold(int level)
    {
        long n=Math.Clamp(level,1,SkillCap)-1; return 100*n*n+20*n*n*n;
    }
    public static int SkillLevel(long xp)
    {
        int low=1,high=SkillCap;
        while(low<high) { int mid=(low+high+1)/2; if(Threshold(mid)<=xp) low=mid; else high=mid-1; }
        return low;
    }
    public static int BaseLevel(Character p,string skill) => SkillLevel(p.SkillXp.GetValueOrDefault(skill));
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
    public static long PlayerLevelCost(int level)
    {
        int current=Math.Clamp(level,1,PlayerCap);
        if(current>=PlayerCap)return 0;
        return current switch
        {
            <20 => 100L+20L*(current-1),
            <30 => 550L+75L*(current-20),
            <40 => 1350L+150L*(current-30),
            <50 => 3000L+300L*(current-40),
            <60 => 6500L+600L*(current-50),
            <80 => 13000L+1000L*(current-60),
            <100 => 35000L+2500L*(current-80),
            <125 => 90000L+6000L*(current-100),
            <150 => 250000L+15000L*(current-125),
            <175 => 650000L+35000L*(current-150),
            _ => 1600000L+100000L*(current-175)
        };
    }
    public static long PlayerThreshold(int level)
    {
        int target=Math.Clamp(level,1,PlayerCap);
        long total=0;
        for(int current=1;current<target;current++)total=checked(total+PlayerLevelCost(current));
        return total;
    }
    public static double PlayerLevelValue(Character p)
    {
        // Character XP remains the exact sum of awarded skill XP. The visible level
        // curve is intentionally easy through 20, then each ten-level band asks for
        // gradually more practice instead of hiding a single late-game grind wall.
        long total=Total(p);int low=1,high=PlayerCap;
        while(low<high){int mid=(low+high+1)/2;if(PlayerThreshold(mid)<=total)low=mid;else high=mid-1;}
        if(low>=PlayerCap)return PlayerCap;
        long floor=PlayerThreshold(low),ceiling=PlayerThreshold(low+1);
        return low+Math.Clamp((total-floor)/(double)Math.Max(1,ceiling-floor),0,1);
    }
    public static int PlayerLevel(Character p)=>Math.Clamp((int)Math.Floor(PlayerLevelValue(p)),1,PlayerCap);
    public static double PlayerLevelProgress(Character p)
    {
        int level=PlayerLevel(p);
        return level>=PlayerCap?1:Math.Clamp(PlayerLevelValue(p)-level,0,1);
    }
    public static double SkillLevelProgress(long xp)
    {
        int level=SkillLevel(xp);
        if(level>=SkillCap)return 1;
        long floor=Threshold(level),ceiling=Threshold(level+1);
        return Math.Clamp((Math.Clamp(xp,floor,ceiling)-floor)/(double)(ceiling-floor),0,1);
    }
    public static long Train(Character p,string skill,int xp,int difficulty,Catalog catalog)
    {
        catalog.Skill(skill);
        if(xp<0||xp>100000||difficulty<1||difficulty>100) throw new RuleException("Invalid skill award.");
        if(xp==0)return 0;
        int over=Level(p,skill)-difficulty;
        // Successful trivial practice stays useful at five percent of base XP.
        // Fractional carry avoids both zero-XP dead zones and one-free-XP rounding exploits.
        double challenge=Math.Clamp((30.0-over)/30.0,.05,1);
        double affinity=catalog.Class(p.Class).Affinity.Contains(skill)?1.10:1;
        int overallBefore=PlayerLevel(p);
        long old=p.SkillXp.GetValueOrDefault(skill),cap=Threshold(SkillCap);
        double carry=p.GeneralPracticeRemainders.GetValueOrDefault(skill);
        if(!double.IsFinite(carry)||carry<0||carry>=1)carry=0;
        double pending=xp*challenge*affinity+carry;
        long whole=(long)Math.Floor(pending);
        long actual=Math.Max(0,Math.Min(cap-old,whole));
        p.SkillXp[skill]=old+actual;
        p.GeneralPracticeRemainders[skill]=p.SkillXp[skill]>=cap?0:pending-whole;
        ChallengeProgression.Credit(p,actual,overallBefore);
        return actual;
    }
}

public sealed class DerivedStats
{
    public double Health { get; set; }
    public double Mana { get; set; }
    public double Stamina { get; set; }
    public double Physical { get; set; }
    public double Spell { get; set; }
    public double Armor { get; set; }
    public double MoveSpeed { get; set; }
    public double Crit { get; set; }
    public double CritDamage { get; set; }
    public double Evasion { get; set; }
    public double Block { get; set; }
    public double Healing { get; set; }
    public double AttackSpeed { get; set; }
    public double CooldownReduction { get; set; }
    public Dictionary<string,double> Bonuses { get; set; } = [];
    public double Bonus(string key)=>Bonuses.GetValueOrDefault(key);
}
public static class CombatMath
{
    public static DerivedStats Stats(Character p,Catalog data)
    {
        var b=new Dictionary<string,double>(data.Class(p.Class).Stats);
        void Add(string key,double value)=>b[key]=b.GetValueOrDefault(key)+value;
        double armor=0,weapon=4;
        foreach(var id in p.Equipment.Values.Distinct())
        {
            var item=p.Inventory.FirstOrDefault(x=>x.Id==id);
            if(item is null||item.Durability<=0) continue;
            var def=data.Item(item.Template); double quality=1+0.10*(int)item.Rarity;
            armor+=def.Armor*quality;
            if(def.Slot=="weapon") weapon=def.Power*quality;
            foreach(var stat in def.Stats) Add(stat.Key,stat.Value);
            foreach(var affix in item.Affixes) if(!BuildDefiningLoot.IsEffectAffix(affix)) Add(affix.Stat,affix.Value);
            foreach(var rune in item.Runes)
            {
                var rd=data.Item(rune.Template);
                foreach(var stat in rd.Stats) Add(stat.Key,stat.Value);
            }
        }
        BuildDefiningLoot.ApplyDynamicStats(p,data,Add);
        double v=b.GetValueOrDefault("vitality",10),s=b.GetValueOrDefault("strength",10),d=b.GetValueOrDefault("dexterity",10),i=b.GetValueOrDefault("intellect",10),sp=b.GetValueOrDefault("spirit",10),r=b.GetValueOrDefault("resolve",10);
        int level=Progression.PlayerLevel(p);
        return new()
        {
            Health=80+v*8+level*3+b.GetValueOrDefault("health"),
            Mana=35+i*5+sp*2+b.GetValueOrDefault("mana"),
            Stamina=70+v*2+r*2,
            Physical=weapon+s*0.65+b.GetValueOrDefault("physical"),
            Spell=7+i*1.1+weapon*0.4+b.GetValueOrDefault("spell"),
            Armor=armor+r*0.35+b.GetValueOrDefault("armor"),
            MoveSpeed=4*(1+Math.Clamp(b.GetValueOrDefault("movement")/100,0,0.30)),
            Crit=Math.Clamp(0.03+d*0.0015+b.GetValueOrDefault("crit")/100,0,0.5),
            CritDamage=Math.Clamp(1.5+b.GetValueOrDefault("crit_damage")/100,1.5,2.5),
            Evasion=Math.Clamp(d*0.001+Progression.Level(p,"evasion")*0.001+b.GetValueOrDefault("evasion")/100,0,0.45),
            Block=HandEquipment.HasUsableShield(p,data)?Math.Clamp(0.05+Progression.Level(p,"shield_mastery")*0.0015+b.GetValueOrDefault("block")/100,0,0.5):0,
            Healing=1+sp*0.01+b.GetValueOrDefault("healing")/100,
            AttackSpeed=Math.Clamp(1+b.GetValueOrDefault("attack_speed")/100,0.5,2),
            CooldownReduction=Math.Clamp(b.GetValueOrDefault("cooldown")/100,0,0.35),
            Bonuses=b
        };
    }
    public static double Damage(double raw,double armor,double resistance)
    {
        if(!double.IsFinite(raw)||!double.IsFinite(armor)||!double.IsFinite(resistance)||raw<0) throw new RuleException("Invalid damage parameters.");
        return Math.Max(0,raw*(100/(100+Math.Max(0,armor)))*(1-Math.Clamp(resistance,-0.5,1)));
    }
    public static double Resist(DerivedStats stats,Element e)=>Math.Clamp(stats.Bonus("resist_"+e.ToString().ToLowerInvariant())/100,-0.5,0.75);
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
    public static double RandomUnit()=>RandomNumberGenerator.GetInt32(1000000)/1000000.0;
    public static double StatusPower(IEnumerable<StatusEffect> effects,string kind,double now)=>effects.Where(x=>x.Kind==kind&&x.Until>now).Sum(x=>x.Power);
}

public static class Items
{
    public const int InventoryCapacity=64;
    public const int BankCapacity=256;
    public const long GoldCap=1_000_000_000_000;
    public static Rarity RollRarity(int bonus=0)
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
        var best=Enum.GetValues<Element>().Where(x=>x!=Element.Physical)
            .Select(x=>(Element:x,Points:EquippedElementPoints(p,x,catalog)))
            .OrderByDescending(x=>x.Points).ThenBy(x=>(int)x.Element).First();
        return best.Points>0?best.Element:Element.Physical;
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
            if(BuildDefiningLoot.RollConditionalAffix(def,item.Rarity) is { } special) item.Affixes.Add(special);
        }
        return item;
    }
    public static bool Equipped(Character p,string id)=>p.Equipment.Values.Contains(id);
    public static Item Owned(Character p,string id)=>p.Inventory.FirstOrDefault(x=>x.Id==id)??throw new RuleException("Item is not in your inventory.");
    public static void Add(List<Item> destination,Item item,Catalog catalog,int capacity=InventoryCapacity)
    {
        var def=catalog.Item(item.Template);
        if(item.Quantity<1||item.Quantity>999) throw new RuleException("Invalid item quantity.");
        bool stackable=def.StackMax>1&&item.Affixes.Count==0&&item.Runes.Count==0&&item.SkillBonuses.Count==0&&item.Element is null;
        var stacks=stackable?destination.Where(x=>x.Template==item.Template&&x.Rarity==item.Rarity&&x.Affixes.Count==0&&x.Runes.Count==0&&x.SkillBonuses.Count==0&&x.Element is null).ToList():[];
        int free=stacks.Sum(x=>def.StackMax-x.Quantity);
        int needed=Math.Max(0,item.Quantity-free);
        int slots=(needed+def.StackMax-1)/def.StackMax;
        if(destination.Count+slots>capacity) throw new RuleException("Not enough storage space.");
        int remaining=item.Quantity;
        foreach(var stack in stacks)
        {
            int n=Math.Min(remaining,def.StackMax-stack.Quantity); stack.Quantity+=n; remaining-=n;
            if(remaining==0) return;
        }
        bool first=true;
        while(remaining>0)
        {
            var copy=Wire.Copy(item); copy.Quantity=Math.Min(remaining,def.StackMax);
            if(!first||destination.Any(x=>x.Id==copy.Id)) copy.Id=Guid.NewGuid().ToString("N");
            destination.Add(copy); remaining-=copy.Quantity; first=false;
        }
    }
    public static Item Take(List<Item> source,string id,int amount,Character? owner=null)
    {
        var item=source.FirstOrDefault(x=>x.Id==id)??throw new RuleException("Item is no longer available.");
        if(amount<1||amount>item.Quantity) throw new RuleException("Invalid item quantity.");
        if(owner is not null&&Equipped(owner,id)) throw new RuleException("Unequip this item first.");
        var result=Wire.Copy(item); result.Quantity=amount;
        if(amount==item.Quantity) source.Remove(item);
        else { item.Quantity-=amount; result.Id=Guid.NewGuid().ToString("N"); }
        return result;
    }
    public static int Count(Character p,string template)=>p.Inventory.Where(x=>x.Template==template&&!Equipped(p,x.Id)).Sum(x=>x.Quantity);
    public static void Consume(Character p,string template,int amount)
    {
        if(amount<1||Count(p,template)<amount) throw new RuleException("Missing ingredients.");
        foreach(var i in p.Inventory.Where(x=>x.Template==template&&!Equipped(p,x.Id)).ToList())
        {
            int n=Math.Min(amount,i.Quantity); Take(p.Inventory,i.Id,n,p); amount-=n; if(amount==0) return;
        }
    }
    public static void Spend(Character p,long amount)
    {
        if(amount<0||amount>GoldCap||p.Gold<amount) throw new RuleException("Not enough gold.");
        p.Gold-=amount;
    }
    public static void Grant(Character p,long amount)
    {
        if(amount<0||amount>GoldCap||p.Gold>GoldCap-amount) throw new RuleException("Gold limit reached.");
        p.Gold+=amount;
    }
    public static void Equip(Character p,string id,Catalog catalog)
    {
        var item=Owned(p,id); var def=catalog.Item(item.Template);
        if(def.Slot==""||item.Durability==0) throw new RuleException("This item cannot be equipped.");
        int required = BeginnerProgression.EquipmentRequirement(def);
        if(def.Skill!=""&&Progression.BaseLevel(p,def.Skill)<required) throw new RuleException($"Requires {catalog.Skill(def.Skill).Name} {required}. Your trained level: {Progression.BaseLevel(p,def.Skill)}. Equipment skill bonuses do not satisfy equipment requirements.");
        if(def.Slot=="weapon"&&!HandEquipment.Compatible(def,HandEquipment.Definition(p,"offhand",catalog)))
            p.Equipment.Remove("offhand");
        if(def.Slot=="offhand"&&!HandEquipment.Compatible(HandEquipment.Definition(p,"weapon",catalog),def))
            throw new RuleException("This offhand item is incompatible with your weapon.");
        p.Equipment[def.Slot]=id;
    }
    public static void Unequip(Character p,string slot,Catalog catalog)
    {
        if(!p.Equipment.Remove(slot)) throw new RuleException("That equipment slot is empty.");
        if(slot=="weapon"&&!HandEquipment.Compatible(null,HandEquipment.Definition(p,"offhand",catalog)))
            p.Equipment.Remove("offhand");
    }
    public static void Socket(Character p,string equipmentId,string runeId,Catalog catalog)
    {
        if(equipmentId==runeId) throw new RuleException("Invalid rune target.");
        var equipment=Owned(p,equipmentId); var rune=Owned(p,runeId); var def=catalog.Item(rune.Template);
        if(def.Type!="rune"||equipment.Sockets<=equipment.Runes.Count) throw new RuleException("No compatible empty socket.");
        if(Progression.Level(p,"runecrafting")<Math.Max(1,(def.Tier-1)*15)) throw new RuleException("Your Runecrafting skill is too low.");
        var removed=Take(p.Inventory,runeId,1,p);
        equipment.Runes.Add(new(){Id=removed.Id,Template=removed.Template});
    }
    public static List<string> Validate(RealmState state,Catalog data)
    {
        var errors=new List<string>(); var ids=new HashSet<string>();
        void Check(Item i)
        {
            if(!ids.Add(i.Id)||!Guid.TryParseExact(i.Id,"N",out _)) errors.Add("Duplicate or malformed item ID: "+i.Id);
            var def=data.Items.FirstOrDefault(x=>x.Id==i.Template);
            if(def is null||i.Quantity<1||i.Quantity>def.StackMax||i.Sockets<0||i.Sockets>4||i.Runes.Count>i.Sockets||i.Durability<0||i.Durability>100) errors.Add("Invalid item: "+i.Id);
            if(def is not null) BuildDefiningLoot.ValidateItem(i,def,data,errors);
            if(i.SkillBonuses.Any(x=>data.Skills.All(s=>s.Id!=x.Key)||x.Value<1||x.Value>7)||i.SkillBonuses.Values.Sum()>7) errors.Add("Invalid item skill bonus: "+i.Id);
            if(def is not null&&def.StackMax>1&&(i.SkillBonuses.Count>0||i.Element is not null)) errors.Add("Stackable item has instance equipment modifiers: "+i.Id);
            foreach(var r in i.Runes) if(!ids.Add(r.Id)||data.Items.All(x=>x.Id!=r.Template||x.Type!="rune")) errors.Add("Invalid socketed rune: "+r.Id);
        }
        foreach(var p in state.Characters.Values)
        {
            if(p.Gold<0||p.Gold>GoldCap||p.Inventory.Count>InventoryCapacity||p.Bank.Count>BankCapacity) errors.Add("Invalid character storage: "+p.Id);
            foreach(var i in p.Inventory.Concat(p.Bank)) Check(i);
            foreach(var e in p.Equipment) if(!p.Inventory.Any(x=>x.Id==e.Value&&data.Item(x.Template).Slot==e.Key)) errors.Add("Invalid equipment: "+p.Id);
            if(!HandEquipment.Compatible(HandEquipment.Definition(p,"weapon",data),HandEquipment.Definition(p,"offhand",data))) errors.Add("Incompatible hand equipment: "+p.Id);
            if(p.SkillXp.Any(x=>!data.Skills.Any(s=>s.Id==x.Key)||x.Value<0||x.Value>Progression.Threshold(100))) errors.Add("Invalid skill XP: "+p.Id);
            if(p.GeneralPracticeRemainders.Any(x=>!data.Skills.Any(s=>s.Id==x.Key)||!double.IsFinite(x.Value)||x.Value<0||x.Value>=1)) errors.Add("Invalid general practice remainder: "+p.Id);
            if(p.CombatPracticeRemainders.Any(x=>!data.Skills.Any(s=>s.Id==x.Key)||!double.IsFinite(x.Value)||x.Value<0||x.Value>=1)) errors.Add("Invalid combat practice remainder: "+p.Id);
        }
        foreach(var a in state.Auctions.Values) Check(a.Item);
        return errors;
    }
}
