#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

# Normalize every remaining legacy equipment recipe, not only the entries
# selected by the 21-step progression matrix. This closes old high-tier
# cured-leather shortcuts while preserving item IDs and combat stats.
p=ROOT/'content_src/gear_progression.py'
text=p.read_text(encoding='utf-8')
anchor='    # New materials remain obtainable without adding a mine or altering spawn geometry.\n'
block=r'''    # Economy normalization also covers legacy craftable equipment that is not the
    # selected representative for a modern progression tier.
    weapon_families={row[0] for row in WEAPONS}
    for route in data['recipes']:
        if route['quantity']!=1: continue
        output=lookup.get(route['output'])
        if output is None or (output.get('slot','')=='' and output.get('type')!='tool'): continue
        if 'boss_unique' in output.get('tags',[]) or 'exploration_unique' in output.get('tags',[]): continue
        level=max(1,int(output.get('requirement',route['requirement'])))
        tier_level,key,_,cloth,_,_,_,_=max((row for row in TIERS if row[0]<=level),key=lambda row:row[0])
        base_key,_,_,_,wood,_=material_at(level)
        metal=key+'_bar';hide_key='cured_leather' if tier_level==1 else key+'_treated_leather'
        cloth_key=cloth.lower().replace(' ','')+'_cloth'
        tags=set(output.get('tags',[]));kind=output.get('type','')
        if kind=='armor':
            weight=next((x for x in ('light','medium','heavy') if x in tags),None)
            if weight=='light': inputs={cloth_key:2,'thread':1}
            elif weight=='medium': inputs={hide_key:2,'thread':1}
            elif weight=='heavy': inputs={metal:3,hide_key:1}
            else: continue
        elif kind=='weapon':
            family=next((x for x in tags if x in weapon_families),None)
            if family=='tome': inputs={metal:1,'parchment':4,'ink':2}
            elif family=='knuckles': inputs={metal:1,hide_key:2,'thread':1}
            else: inputs={metal:2,wood+'_plank':1,hide_key:1}
        elif kind=='offhand': inputs={metal:1,hide_key:2}
        elif kind=='accessory': inputs={metal:1,'polished_gem':1}
        elif kind=='tool': inputs={metal:1,wood+'_plank':1,hide_key:1}
        else: continue
        if any(part not in lookup for part in inputs): continue
        route['ingredients']=inputs
        output['value']=price(inputs)
'''
if anchor not in text:
    raise SystemExit('legacy equipment normalization anchor missing')
p.write_text(text.replace(anchor,block+anchor,1),encoding='utf-8')

# Use one exact buy formula everywhere and cap Common resale below the
# cheapest fully vendor-supplied recipe. Better random quality can still
# command a premium, but vendor ingredients can never guarantee gold.
p=ROOT/'src/Kairnfall.Core/MerchantSales.cs'
p.write_text(r'''namespace Kairnfall.Core;

/// <summary>One sale quote for both the interface and authoritative transaction.</summary>
public static class MerchantSales
{
    public static long UnitPrice(ItemDef definition)=>Math.Max(1,checked((long)definition.Value*3)/10);

    public static long BuyUnitPrice(Character self,NpcDef merchant,ItemDef definition)
    {
        double reputation=Math.Clamp(self.Reputation.GetValueOrDefault(merchant.Faction),0,1000)/20000.0;
        double reduction=Math.Min(.15,Progression.Level(self,"bartering")*.001+reputation);
        return Math.Max(1,(long)Math.Ceiling(definition.Value*(1.2-reduction)));
    }

    public static bool Accepts(NpcDef merchant,ItemDef definition,Catalog data)
        =>merchant.Stock.Length>0&&definition.Type!="quest"&&definition.Value>0
            &&(merchant.Role=="provisioner"||merchant.Stock.Any(x=>data.Item(x).Type==definition.Type));

    public static double MarketBonus(Character self,NpcDef merchant)
    {
        double bartering=Math.Min(.10,Progression.Level(self,"bartering")*.001);
        double reputation=Math.Min(.05,Math.Clamp(self.Reputation.GetValueOrDefault(merchant.Faction),0,1000)/20000.0);
        double specialist=merchant.Role=="provisioner"?0:.08;
        return bartering+reputation+specialist;
    }

    public static double QualityMultiplier(Item item)
        =>1+.08*Math.Clamp((int)item.Rarity,0,6)+.02*Math.Min(4,item.Affixes.Count)+.03*Math.Min(4,item.Runes.Count);

    private static long GuaranteedCommonCraftCap(Character self,ItemDef definition,Catalog data)
    {
        long best=long.MaxValue;
        foreach(var recipe in data.Recipes.Where(x=>x.Output==definition.Id&&x.Quantity>0))
        {
            long cost=0;bool fullyRetail=true;
            foreach(var ingredient in recipe.Ingredients)
            {
                var ingredientDef=data.Item(ingredient.Key);
                long cheapest=long.MaxValue;
                foreach(var seller in data.Npcs.Where(x=>x.Stock.Contains(ingredient.Key)))
                    cheapest=Math.Min(cheapest,BuyUnitPrice(self,seller,ingredientDef));
                if(cheapest==long.MaxValue){fullyRetail=false;break;}
                cost=checked(cost+cheapest*ingredient.Value);
            }
            if(!fullyRetail||cost<=1)continue;
            best=Math.Min(best,Math.Max(1,(cost-1)/recipe.Quantity));
        }
        return best;
    }

    public static long UnitPrice(Character self,NpcDef merchant,Item item,Catalog data)
    {
        var definition=data.Item(item.Template);
        double price=UnitPrice(definition)*(1+MarketBonus(self,merchant))*QualityMultiplier(item);
        long quote=Math.Max(1,(long)Math.Floor(price));
        if(item.Rarity==Rarity.Common)
        {
            long cap=GuaranteedCommonCraftCap(self,definition,data);
            if(cap!=long.MaxValue)quote=Math.Min(quote,cap);
        }
        return quote;
    }

    public static long Quote(Character self,NpcDef merchant,Item item,int quantity,Catalog data)
    {
        var owned=self.Inventory.FirstOrDefault(x=>x.Id==item.Id)??throw new RuleException("The item is not in your backpack.");
        var def=data.Item(owned.Template);
        if(self.Health<=0) throw new RuleException("Respawn before trading.");
        if(self.Zone!=merchant.Zone||!self.Position.Finite||self.Position.Distance(merchant.Position)>3
            ||!WorldMap.LineOfSight(data.Zone(merchant.Zone),self.Position,merchant.Position))
            throw new RuleException("Move closer to the merchant.");
        if(quantity<=0||quantity>owned.Quantity||quantity>Math.Min(999,def.StackMax))
            throw new RuleException("Choose a quantity within this item's stack.");
        if(Items.Equipped(self,owned.Id)) throw new RuleException("Unequip this item before selling.");
        if(!Accepts(merchant,def,data))
            throw new RuleException(def.Type=="quest"||def.Value<=0?"This item cannot be sold.":"This merchant does not buy this item type.");
        long total=checked(UnitPrice(self,merchant,owned,data)*quantity);
        if(total>Items.GoldCap-self.Gold) throw new RuleException("Gold limit reached.");
        return total;
    }
    public static string Problem(Character self,NpcDef merchant,Item item,int quantity,Catalog data)
    {
        try { Quote(self,merchant,item,quantity,data); return ""; }
        catch(RuleException error) { return error.Message; }
    }
}
''',encoding='utf-8')

# The realm's public buy-price helper and the arbitrage guard must use exactly
# the same formula.
p=ROOT/'src/Kairnfall.Core/RealmEconomy.cs'
text=p.read_text(encoding='utf-8')
old='''    public long BuyPrice(Character p,NpcDef merchant,ItemDef item)\n    {\n        double reputation=Math.Clamp(p.Reputation.GetValueOrDefault(merchant.Faction),0,1000)/20000.0;\n        double reduction=Math.Min(0.15,Progression.Level(p,"bartering")*0.001+reputation);\n        return Math.Max(1,(long)Math.Ceiling(item.Value*(1.2-reduction)));\n    }\n'''
new='''    public long BuyPrice(Character p,NpcDef merchant,ItemDef item)=>MerchantSales.BuyUnitPrice(p,merchant,item);\n'''
if old not in text:
    raise SystemExit('buy-price anchor missing')
p.write_text(text.replace(old,new,1),encoding='utf-8')

# Strengthen the permanent regression so future legacy recipes cannot fall
# back to starter leather again.
p=ROOT/'tools/world_probe/EconomyCraftingFeelChecks.cs'
text=p.read_text(encoding='utf-8')
anchor='''            Need(checkedGear>900,"Too few tier recipes checked.");\n'''
addition='''            foreach(var recipe in data.Recipes.Where(r=>r.Quantity==1))\n            {\n                var output=data.Item(recipe.Output);\n                if(output.Type!="armor"||output.Requirement<=1||!output.Tags.Any(x=>x is "medium" or "heavy"))continue;\n                Need(!recipe.Ingredients.ContainsKey("cured_leather"),"High-tier legacy armor still consumes starter cured leather: "+recipe.Id);\n            }\n'''
if anchor not in text:
    raise SystemExit('economy audit strengthening anchor missing')
p.write_text(text.replace(anchor,anchor+addition,1),encoding='utf-8')

print('systemic economy arbitrage fix applied')
