namespace Kairnfall.Core;

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
