#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def edit(path,old,new):
    p=ROOT/path
    text=p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'anchor missing in {path}: {old[:160]!r}')
    p.write_text(text.replace(old,new,1),encoding='utf-8')

def write(path,text):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')

write('src/Kairnfall.Core/EconomyCrafting.cs',r'''namespace Kairnfall.Core;

public sealed record ReclaimPlan(RecipeDef Recipe,string Material,int Quantity,long InputValue,long RecoveredValue);

/// <summary>Shared prices used by both the authoritative realm and client presentation.</summary>
public static class EconomyServices
{
    public static long RepairPrice(ItemDef definition,int durability)
        =>Math.Max(1,(long)Math.Ceiling((100-Math.Clamp(durability,0,100))*Math.Max(1,definition.Value)/500.0));

    public static long RuneExtractionPrice(ItemDef rune)=>Math.Max(20,rune.Value/2);

    public static long RestPrice(Character player)
    {
        int level=Progression.PlayerLevel(player);
        return 5L+Math.Max(0,(level-1)/10)*2L;
    }

    public static long TravelPrice(Catalog data,Character player,ZoneDef source,ZoneDef destination)
    {
        int distance=Math.Abs(destination.WorldX-source.WorldX)+Math.Abs(destination.WorldY-source.WorldY);
        int threat=JourneyProgression.ThreatLevel(data,destination);
        int level=Progression.PlayerLevel(player);
        return Math.Clamp(15L+distance*3L+threat/5L+Math.Max(0,(level-1)/10)*2L,15L,120L);
    }
}

/// <summary>Crafting-value, quality and reclaim rules. Reclaiming is deliberately lossy.</summary>
public static class CraftEconomy
{
    public static long RecipeInputValue(Catalog data,RecipeDef recipe)
        =>recipe.Ingredients.Sum(x=>checked((long)Math.Max(0,data.Item(x.Key).Value)*x.Value));

    public static long RecipeOutputValue(Catalog data,RecipeDef recipe)
        =>checked((long)Math.Max(0,data.Item(recipe.Output).Value)*recipe.Quantity);

    public static RecipeDef? RecipeForOutput(Catalog data,string template)
        =>data.Recipes.Where(x=>x.Output==template&&x.Quantity==1)
            .OrderBy(x=>x.Requirement).ThenBy(x=>x.Id,StringComparer.Ordinal).FirstOrDefault();

    public static ReclaimPlan? Reclaim(Catalog data,Item item)
    {
        var definition=data.Items.FirstOrDefault(x=>x.Id==item.Template);
        if(definition is null||item.Quantity!=1||definition.StackMax!=1||item.Runes.Count>0) return null;
        if(definition.Slot==""&&definition.Type!="tool") return null;
        if(definition.Tags.Contains("boss_unique",StringComparer.Ordinal)||definition.Tags.Contains("exploration_unique",StringComparer.Ordinal)) return null;
        var recipe=RecipeForOutput(data,definition.Id); if(recipe is null) return null;
        long input=RecipeInputValue(data,recipe); if(input<=1) return null;
        long budget=Math.Max(1,(long)Math.Floor(input*.49));
        (string Material,int Quantity,long Value)? best=null;
        foreach(var ingredient in recipe.Ingredients.OrderBy(x=>x.Key,StringComparer.Ordinal))
        {
            long unit=Math.Max(1,data.Item(ingredient.Key).Value);
            int quantity=(int)Math.Min(ingredient.Value,budget/unit);
            if(quantity<1) continue;
            long recovered=checked(unit*quantity);
            if(best is null||recovered>best.Value.Value||(recovered==best.Value.Value&&string.CompareOrdinal(ingredient.Key,best.Value.Material)<0))
                best=(ingredient.Key,quantity,recovered);
        }
        if(best is null) return null;
        return new(recipe,best.Value.Material,best.Value.Quantity,input,best.Value.Value);
    }

    public static string QualityHint(Character? player,RecipeDef recipe,Catalog data)
    {
        var output=data.Item(recipe.Output);
        if(output.StackMax>1) return "Stackable output · fixed Common quality.";
        int skill=player is null?0:Progression.Level(player,recipe.Skill);
        foreach(var rarity in Enum.GetValues<Rarity>().Where(x=>x>Rarity.Common))
        {
            int gate=Items.CraftRarityRequirement(rarity,recipe.Requirement);
            if(gate>skill) return $"Craft skill {skill} · next quality gate: {rarity} at {gate}.";
        }
        return $"Craft skill {skill} · every rarity gate unlocked; mastery still improves the roll.";
    }
}
''')

write('src/Kairnfall.Core/MerchantSales.cs',r'''namespace Kairnfall.Core;

/// <summary>One sale quote for both the interface and authoritative transaction.</summary>
public static class MerchantSales
{
    public static long UnitPrice(ItemDef definition)=>Math.Max(1,checked((long)definition.Value*3)/10);

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

    public static long UnitPrice(Character self,NpcDef merchant,Item item,Catalog data)
    {
        var definition=data.Item(item.Template);
        double price=UnitPrice(definition)*(1+MarketBonus(self,merchant))*QualityMultiplier(item);
        return Math.Max(1,(long)Math.Floor(price));
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
''')

edit('src/Kairnfall.Core/RealmEngine.cs',
'''            case "craft": return Craft(p,c.Item,c.Amount);\n            case "socket": Items.Socket(p,c.Target,c.Item,Data); Progression.Train(p,"runecrafting",30,Math.Max(1,Progression.Level(p,"runecrafting")),Data); Progress(p,"socket","*"); return "Rune inserted.";\n''',
'''            case "craft": return Craft(p,c.Item,c.Amount);\n            case "salvage": return Salvage(p,c.Item);\n            case "socket": Items.Socket(p,c.Target,c.Item,Data); Progression.Train(p,"runecrafting",30,Math.Max(1,Progression.Level(p,"runecrafting")),Data); Progress(p,"socket","*"); return "Rune inserted.";\n''')

edit('src/Kairnfall.Core/RealmEconomy.cs',
'''        long value=MerchantSales.Quote(p,npc,item,quantity,Data);\n        Items.Take(p.Inventory,itemId,quantity,p); Items.Grant(p,value);\n        Progress(p,"sell",def.Id,quantity); return $"Sold for {value} gold.";\n''',
'''        long value=MerchantSales.Quote(p,npc,item,quantity,Data);\n        Items.Take(p.Inventory,itemId,quantity,p); Items.Grant(p,value);\n        if(p.Cooldowns.GetValueOrDefault("barter_xp")<=State.Time)\n        {\n            Progression.Train(p,"bartering",Math.Min(50,(int)Math.Min(value,50)),def.Requirement,Data);\n            p.Cooldowns["barter_xp"]=State.Time+10;\n        }\n        Progress(p,"sell",def.Id,quantity); return $"Sold for {value} gold.";\n''')

edit('src/Kairnfall.Core/RealmEconomy.cs',
'''        Progression.Train(p,recipe.Skill,Math.Min(100000,recipe.Xp*quantity),recipe.Requirement,Data);\n        Progress(p,"craft",output.Id,outputCount); return $"Crafted {outputCount} {output.Name}.";\n    }\n    private string Unsocket(Character p,string id,int index)\n''',
'''        Progression.Train(p,recipe.Skill,Math.Min(100000,recipe.Xp*quantity),recipe.Requirement,Data);\n        Progress(p,"craft",output.Id,outputCount); return $"Crafted {outputCount} {output.Name}.";\n    }\n    private string Salvage(Character p,string id)\n    {\n        var item=Items.Owned(p,id);var def=Data.Item(item.Template);\n        Need(!Items.Equipped(p,id),"Unequip this item before reclaiming materials.");\n        Need(item.Runes.Count==0,"Extract socketed runes before reclaiming this item.");\n        var plan=CraftEconomy.Reclaim(Data,item);Need(plan is not null,"This item has no reclaimable crafting route.");\n        Need(AtStation(p,plan!.Recipe.Station),"Use the "+plan.Recipe.Station+" station to reclaim this item.");\n        Ready(p,"salvage",1.2);\n        Items.Take(p.Inventory,id,1,p);Items.Add(p.Inventory,Items.Create(Data,plan.Material,plan.Quantity),Data);\n        Progress(p,"salvage",def.Id);\n        return $"Reclaimed {plan.Quantity} {Data.Item(plan.Material).Name} from {def.Name}.";\n    }\n    private string Unsocket(Character p,string id,int index)\n''')

edit('src/Kairnfall.Core/RealmEconomy.cs',
'''        var rune=item.Runes[index]; var def=Data.Item(rune.Template);\n        Items.Spend(p,Math.Max(20,def.Value/2));\n''',
'''        var rune=item.Runes[index]; var def=Data.Item(rune.Template);\n        Items.Spend(p,EconomyServices.RuneExtractionPrice(def));\n''')
edit('src/Kairnfall.Core/RealmEconomy.cs',
'''        Need((def.Slot!=""||def.Type=="tool")&&item.Durability<100,"This item does not need repair.");\n        long price=Math.Max(1,(long)Math.Ceiling((100-item.Durability)*Math.Max(1,def.Value)/500.0));\n''',
'''        Need((def.Slot!=""||def.Type=="tool")&&item.Durability<100,"This item does not need repair.");\n        long price=EconomyServices.RepairPrice(def,item.Durability);\n''')
edit('src/Kairnfall.Core/RealmEconomy.cs',
'''        Need(dest.Kind is "city" or "settlement","Invalid fast-travel destination.");\n        Need(dest.Id!=p.Zone,"You are already here."); Items.Spend(p,20);\n        CancelTradesFor(p.Id); inputs.Remove(p.Id); p.Zone=dest.Id; p.Position=dest.Spawn;\n        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet)) { pet.Zone=p.Zone; pet.Position=p.Position; }\n        return "Arrived at "+dest.Name+".";\n''',
'''        Need(dest.Kind is "city" or "settlement","Invalid fast-travel destination.");\n        Need(dest.Id!=p.Zone,"You are already here."); long price=EconomyServices.TravelPrice(Data,p,source,dest);Items.Spend(p,price);\n        CancelTradesFor(p.Id); inputs.Remove(p.Id); p.Zone=dest.Id; p.Position=dest.Spawn;\n        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet)) { pet.Zone=p.Zone; pet.Position=p.Position; }\n        return $"Arrived at {dest.Name} for {price} gold.";\n''')
edit('src/Kairnfall.Core/RealmEconomy.cs',
'''        Need(p.Health<stats.Health||p.Mana<stats.Mana||p.Stamina<stats.Stamina,"You are already fully rested.");\n        Ready(p,"rest",10); if(!camp) Items.Spend(p,5);\n        p.Health=stats.Health; p.Mana=stats.Mana; p.Stamina=stats.Stamina;\n        Progression.Train(p,"survival",5,Math.Clamp(Data.Zone(p.Zone).Level,1,100),Data);\n        return "Health, mana, and stamina restored.";\n''',
'''        Need(p.Health<stats.Health||p.Mana<stats.Mana||p.Stamina<stats.Stamina,"You are already fully rested.");\n        long price=camp?0:EconomyServices.RestPrice(p);Ready(p,"rest",10);if(price>0)Items.Spend(p,price);\n        p.Health=stats.Health; p.Mana=stats.Mana; p.Stamina=stats.Stamina;\n        Progression.Train(p,"survival",5,Math.Clamp(Data.Zone(p.Zone).Level,1,100),Data);\n        return price==0?"Health, mana, and stamina restored at camp.":$"Health, mana, and stamina restored for {price} gold.";\n''')

# Reprice every equipment-tier recipe from its actual ingredients and make matching-grade hides meaningful.
edit('content_src/gear_progression.py',
'''    # New materials remain obtainable without adding a mine or altering spawn geometry.\n''',
r'''    # Economy pass: every progression item uses materials from its own grade and its
    # base value follows the real recipe instead of inherited legacy price formulas.
    # Saved template IDs and combat fields remain stable; only recipe inputs and gold value change.
    recipes_by_output={}
    for entry in data['recipes']:
        if entry['quantity']==1: recipes_by_output.setdefault(entry['output'],[]).append(entry)
    tier_rows={row[0]:row for row in TIERS}
    for tier in data['equipmentTiers']:
        level=tier['level']; key=next(row[1] for row in TIERS if row[0]==level)
        _,_,_,cloth,_,_,_,_=tier_rows[level]
        base_key,_,_,_,wood,_=material_at(level)
        metal=key+'_bar'; cloth_key=cloth.lower().replace(' ','')+'_cloth'; hide_key='cured_leather' if level==1 else key+'_treated_leather'
        for family,ident in tier['entries'].items():
            if family.startswith('armor/light/'):
                inputs={cloth_key:2,'thread':1}
            elif family.startswith('armor/medium/'):
                inputs={hide_key:2,'thread':1}
            elif family.startswith('armor/heavy/'):
                inputs={metal:3,hide_key:1}
            elif family.startswith('weapon/'):
                weapon_family=family.split('/',1)[1]
                inputs={metal:1,'parchment':4,'ink':2} if weapon_family=='tome' else ({metal:1,hide_key:2,'thread':1} if weapon_family=='knuckles' else {metal:2,wood+'_plank':1,hide_key:1})
            elif family.startswith('offhand/'):
                inputs={metal:1,hide_key:2}
            elif family.startswith('accessory/'):
                inputs={metal:1,'polished_gem':1}
            elif family.startswith('tool/'):
                inputs={metal:1,wood+'_plank':1,hide_key:1}
            else:
                continue
            routes=recipes_by_output.get(ident,[])
            if not routes: raise ValueError('Missing recipe for progression item '+ident)
            route=min(routes,key=lambda r:(r['requirement'],r['id']))
            route['ingredients']=inputs
            lookup[ident]['value']=price(inputs)
    # New materials remain obtainable without adding a mine or altering spawn geometry.
''')
edit('content_src/gear_progression.py',
'''    # This is a save-compatibility invariant, not a snapshot of only catalog counts.\n    if any(lookup[key] != value for key,value in legacy.items()):\n        raise ValueError('A pre-existing item definition changed during progression extension')\n    now={r['id']:r for r in data['recipes']}\n    if any(now[key] != value for key,value in recipes_before.items()):\n        raise ValueError('A pre-existing recipe changed during progression extension')\n''',
'''    # Save compatibility protects identities and combat semantics while allowing deliberate economy rebalancing.\n    protected_item_fields=('id','name','type','slot','skill','requirement','power','armor','speed','range','element','stats','tags','tier')\n    for key,before in legacy.items():\n        after=lookup[key]\n        if any(after.get(field)!=before.get(field) for field in protected_item_fields):\n            raise ValueError('A pre-existing item combat/identity field changed: '+key)\n    now={r['id']:r for r in data['recipes']}\n    protected_recipe_fields=('id','name','skill','station','output','requirement','quantity','xp')\n    for key,before in recipes_before.items():\n        after=now[key]\n        if any(after.get(field)!=before.get(field) for field in protected_recipe_fields):\n            raise ValueError('A pre-existing recipe identity/progression field changed: '+key)\n''')

# Merchant UI uses the exact authoritative quote, including rarity, specialization, skill and reputation.
edit('client/Scripts/MerchantSellPanel.cs',
'''                list.SetItemText(i, Data.Item(item.Template).Name + " ×" + item.Quantity);\n                list.SetItemCustomFgColor(i, problem == "" ? Ui.Text : Ui.Danger);\n                list.SetItemTooltip(i, problem == "" ? MerchantSales.UnitPrice(Data.Item(item.Template)) + " gold each" : problem);\n''',
'''                list.SetItemText(i, Data.Item(item.Template).Name + " ×" + item.Quantity);\n                list.SetItemCustomFgColor(i, problem == "" ? Ui.Text : Ui.Danger);\n                list.SetItemTooltip(i, problem == "" ? MerchantSales.UnitPrice(self,Merchant,item,Data) + " gold each · specialist, Bartering, reputation and quality included" : problem);\n''')
edit('client/Scripts/MerchantSellPanel.cs',
'''            money.Text = $"Gold: {self.Gold:N0} · One backpack: {self.Inventory.Count}/{Items.InventoryCapacity} slots";\n''',
'''            money.Text = $"Gold: {self.Gold:N0} · One backpack: {self.Inventory.Count}/{Items.InventoryCapacity} slots · Specialists, Bartering, reputation and item quality improve sale quotes.";\n''')
edit('client/Scripts/MerchantSellPanel.cs',
'''        long unit = MerchantSales.UnitPrice(Data.Item(item.Template));\n''',
'''        long unit = MerchantSales.UnitPrice(self!,Merchant,item,Data);\n''')

# Craft browser explains the actual material economy and quality progression.
edit('client/Scripts/CraftingGuidePanel.cs',
'''        requirement.Text=Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+" · "+Ui.Words(recipe.Station)+\n            "\\nOutput: "+checked(recipe.Quantity*quantity)+" · Base skill XP per batch: "+recipe.Xp+"\\nXP depends on challenge and class affinity.";\n''',
'''        long inputValue=CraftEconomy.RecipeInputValue(Data,recipe),outputValue=CraftEconomy.RecipeOutputValue(Data,recipe);\n        var reclaim=CraftEconomy.Reclaim(Data,new Item{Template=recipe.Output,Quantity=1});\n        requirement.Text=Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+" · "+Ui.Words(recipe.Station)+\n            "\\nOutput: "+checked(recipe.Quantity*quantity)+" · Base skill XP per batch: "+recipe.Xp+\n            $"\\nMaterial value {inputValue:N0} → output base {outputValue:N0} · base merchant resale {MerchantSales.UnitPrice(item)*recipe.Quantity:N0}"+\n            "\\n"+CraftEconomy.QualityHint(self,recipe,Data)+(reclaim is null?"":$"\\nReclaim preview: {reclaim.Quantity} {Data.Item(reclaim.Material).Name} at {Ui.Words(reclaim.Recipe.Station)}.")+\n            "\\nXP depends on challenge and class affinity.";\n''')

# Inventory exposes exact maintenance prices and safe lossy reclaiming.
edit('client/Scripts/GameRoot.Inventory.cs',
'''            var repair = Ui.Button("Repair at blacksmith", () => Send("repair", item: item.Id), !NearRole("blacksmith"));\n''',
'''            long repairPrice=EconomyServices.RepairPrice(def,item.Durability);\n            var repair = Ui.Button($"Repair at blacksmith · {repairPrice:N0} gold", () => Send("repair", item: item.Id), !NearRole("blacksmith")||self.Gold<repairPrice);\n''')
edit('client/Scripts/GameRoot.Inventory.cs',
'''            parent.AddChild(Ui.Button("Extract " + Data.Item(item.Runes[i].Template).Name,\n                () => Confirm("Extract rune", "The enchanter charges an extraction fee. The rune is returned intact.", () => Send("unsocket", item.Id, amount: index)), !NearRole("enchanter")));\n''',
'''            var runeDef=Data.Item(item.Runes[i].Template);long extraction=EconomyServices.RuneExtractionPrice(runeDef);\n            parent.AddChild(Ui.Button("Extract " + runeDef.Name+$" · {extraction:N0} gold",\n                () => Confirm("Extract rune", $"Extraction costs {extraction:N0} gold. The rune is returned intact.", () => Send("unsocket", item.Id, amount: index)), !NearRole("enchanter")||self.Gold<extraction));\n''')
edit('client/Scripts/GameRoot.Inventory.cs',
'''        if (selectedNpc != "" && Data.Npcs.Any(x => x.Id == selectedNpc && x.Stock.Length > 0))\n            parent.AddChild(Ui.Button("Merchant selling", () => OpenPage("Sell")));\n''',
'''        if(CraftEconomy.Reclaim(Data,item) is { } reclaim)\n        {\n            bool blocked=Items.Equipped(self,item.Id)||!ClientAtStation(reclaim.Recipe.Station);\n            string label=$"Reclaim at {Ui.Words(reclaim.Recipe.Station)} → {reclaim.Quantity} {Data.Item(reclaim.Material).Name}";\n            parent.AddChild(Ui.Button(label,()=>Confirm("Reclaim materials",$"Destroy {def.Name} and recover {reclaim.Quantity} {Data.Item(reclaim.Material).Name}? Reclaiming is deliberately lossy.",()=>Send("salvage",item:item.Id)),blocked));\n        }\n        if (selectedNpc != "" && Data.Npcs.Any(x => x.Id == selectedNpc && x.Stock.Length > 0))\n            parent.AddChild(Ui.Button("Merchant selling", () => OpenPage("Sell")));\n''')

edit('client/Scripts/GameRoot.Experience.cs',
'''        if (bag == "inventory" && definition.Type is "book" or "treasure_map") menu.AddItem("Read", 4);\n        menu.AddItem("Inspect item", 1);\n''',
'''        if (bag == "inventory" && definition.Type is "book" or "treasure_map") menu.AddItem("Read", 4);\n        var reclaim=bag=="inventory"?CraftEconomy.Reclaim(Data,item):null;\n        if(reclaim is not null) menu.AddItem($"Reclaim → {reclaim.Quantity} {Data.Item(reclaim.Material).Name}",5,wasEquipped||!ClientAtStation(reclaim.Recipe.Station));\n        menu.AddItem("Inspect item", 1);\n''')
edit('client/Scripts/GameRoot.Experience.cs',
'''            else if (choice == 4) Send("read", item: item.Id);\n''',
'''            else if (choice == 4) Send("read", item: item.Id);\n            else if(choice==5&&CraftEconomy.Reclaim(Data,currentItem) is { } plan)\n                Confirm("Reclaim materials",$"Destroy {Data.Item(currentItem.Template).Name} and recover {plan.Quantity} {Data.Item(plan.Material).Name}?",()=>Send("salvage",item:currentItem.Id));\n''')

edit('client/Scripts/GameRoot.Panels.cs',
'''        if (npc.Role == "innkeeper") services.AddChild(Ui.Button("Rest · 5 gold", () => Send("rest")));\n''',
'''        if (npc.Role == "innkeeper")\n        {\n            long restPrice=EconomyServices.RestPrice(Snapshot.Self);\n            services.AddChild(Ui.Button($"Rest · {restPrice:N0} gold", () => Send("rest"),Snapshot.Self.Gold<restPrice));\n        }\n''')

edit('client/Scripts/Maps.cs',
'''            var actions = Ui.Row(detail); actions.AddChild(Ui.Button("Mark route", () => MarkDestination(zone.Id, zone.Spawn)));\n            bool canTravel = Snapshot.Self.Waypoints.Contains(zone.Id) && zone.Id != Snapshot.Self.Zone && !locked;\n            actions.AddChild(Ui.Button("Waystone travel · 20 gold", () => Send("travel", zone.Id), !canTravel));\n''',
'''            var actions = Ui.Row(detail); actions.AddChild(Ui.Button("Mark route", () => MarkDestination(zone.Id, zone.Spawn)));\n            var source=Data.Zone(Snapshot.Self.Zone);long travelPrice=EconomyServices.TravelPrice(Data,Snapshot.Self,source,zone);\n            bool canTravel = Snapshot.Self.Waypoints.Contains(zone.Id) && zone.Id != Snapshot.Self.Zone && !locked && Snapshot.Self.Gold>=travelPrice;\n            actions.AddChild(Ui.Button($"Waystone travel · {travelPrice:N0} gold", () => Send("travel", zone.Id), !canTravel));\n            if(Snapshot.Self.Waypoints.Contains(zone.Id)&&zone.Id!=Snapshot.Self.Zone&&!locked&&Snapshot.Self.Gold<travelPrice)\n                detail.AddChild(Ui.Label($"Need {travelPrice-Snapshot.Self.Gold:N0} more gold for this waystone route.",12,Ui.Danger,true));\n''')

# Update the legacy audit's sink wording to the shared dynamic rules.
edit('tools/world_probe/EconomyBalanceAuditChecks.cs',
'''                long fullRepair=Math.Max(1,(long)Math.Ceiling(100*Math.Max(1,def.Value)/500.0));\n''',
'''                long fullRepair=EconomyServices.RepairPrice(def,0);\n''')
edit('tools/world_probe/EconomyBalanceAuditChecks.cs',
'''            Console.WriteLine("ECONOMY METRIC gold_sinks rest=5 fast_travel=20 repair=ceil(missing_durability*value/500) unsocket=max(20,rune_value/2)");\n''',
'''            Console.WriteLine("ECONOMY METRIC gold_sinks rest=progression_scaled fast_travel=distance_threat_progression_scaled repair=shared_value_rule unsocket=shared_rune_rule");\n''')

write('tools/world_probe/EconomyCraftingFeelChecks.cs',r'''using Kairnfall.Core;

internal static class EconomyCraftingFeelChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check){try{check();passed++;Console.WriteLine("PASS ECONOMY CRAFTING: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL ECONOMY CRAFTING: "+name+": "+e.Message);}}

        Test("progression equipment recipes use grade materials and fair base values",()=>
        {
            int checkedGear=0;var ratios=new List<double>();
            foreach(var tier in data.EquipmentTiers)
            foreach(var entry in tier.Entries)
            {
                var recipe=CraftEconomy.RecipeForOutput(data,entry.Value);Need(recipe is not null,"Missing recipe for "+entry.Value);
                long input=CraftEconomy.RecipeInputValue(data,recipe!),output=CraftEconomy.RecipeOutputValue(data,recipe!);Need(input>0,"Zero material value: "+recipe!.Id);
                double ratio=output/(double)input;ratios.Add(ratio);checkedGear++;
                Need(ratio>=1.0&&ratio<=1.30,$"Gear value no longer tracks materials: {recipe.Id} {ratio:F2}x.");
                if(tier.Level>1&&entry.Key.StartsWith("armor/medium/",StringComparison.Ordinal))
                    Need(recipe.Ingredients.Keys.Any(x=>x.EndsWith("_treated_leather",StringComparison.Ordinal)),"High-tier medium armor still uses starter leather: "+recipe.Id);
                if(tier.Level>1&&entry.Key.StartsWith("armor/heavy/",StringComparison.Ordinal))
                    Need(recipe.Ingredients.Keys.Any(x=>x.EndsWith("_treated_leather",StringComparison.Ordinal)),"High-tier heavy armor has no matching hide fitting: "+recipe.Id);
            }
            Need(checkedGear>900,"Too few tier recipes checked.");
            Console.WriteLine($"ECONOMY CRAFTING METRIC gear_recipes={checkedGear} ratio_min={ratios.Min():F2} ratio_median={ratios.Order().ElementAt(ratios.Count/2):F2} ratio_max={ratios.Max():F2}");
        });

        Test("common vendor ingredients cannot be converted into guaranteed merchant profit",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("economy-loop","Market Auditor","vanguard",new());
            p.SkillXp["bartering"]=Progression.Threshold(100);foreach(var faction in data.Npcs.Select(x=>x.Faction).Where(x=>x!="").Distinct())p.Reputation[faction]=1000;
            int audited=0;
            foreach(var recipe in data.Recipes)
            {
                long inputCost=0;bool purchasable=true;
                foreach(var ingredient in recipe.Ingredients)
                {
                    var def=data.Item(ingredient.Key);var sellers=data.Npcs.Where(n=>n.Stock.Contains(def.Id)).ToArray();
                    if(sellers.Length==0){purchasable=false;break;}
                    inputCost=checked(inputCost+sellers.Min(n=>realm.BuyPrice(p,n,def))*ingredient.Value);
                }
                if(!purchasable)continue;
                var output=data.Item(recipe.Output);var buyers=data.Npcs.Where(n=>MerchantSales.Accepts(n,output,data)).ToArray();if(buyers.Length==0)continue;
                var instance=Items.Create(data,output.Id,1,Rarity.Common,p);long sale=buyers.Max(n=>MerchantSales.UnitPrice(p,n,instance,data))*recipe.Quantity;
                Need(sale<inputCost,$"Guaranteed vendor craft arbitrage: {recipe.Id} buy inputs {inputCost}, sell common output {sale}.");audited++;
            }
            Need(audited>=10,"Too few fully vendor-supplied crafting loops audited.");
            Console.WriteLine("ECONOMY CRAFTING METRIC vendor_craft_loops="+audited);
        });

        Test("specialists Bartering reputation and quality improve sale quotes without buyback arbitrage",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("economy-sales","Sale Auditor","vanguard",new());
            var merchant=data.Npcs.First(n=>n.Role!="provisioner"&&n.Stock.Any(id=>data.Item(id).Value>=20));var def=data.Item(merchant.Stock.First(id=>data.Item(id).Value>=20));
            var item=Items.Create(data,def.Id,1,Rarity.Epic,p);long basePrice=MerchantSales.UnitPrice(def);
            p.SkillXp["bartering"]=Progression.Threshold(100);p.Reputation[merchant.Faction]=1000;
            long quote=MerchantSales.UnitPrice(p,merchant,item,data),buy=realm.BuyPrice(p,merchant,def);
            Need(quote>basePrice,"Skill/specialist/quality did not improve the sale quote.");Need(quote<buy,"Improved sell quote reached merchant buy price.");
            p.Zone=merchant.Zone;p.Position=merchant.Position;p.Gold=0;Items.Add(p.Inventory,item,data);long expected=MerchantSales.Quote(p,merchant,item,1,data);
            var result=realm.Execute(p.Id,new GameCommand{Kind="sell",Target=merchant.Id,Item=item.Id,Amount=1,Sequence=p.LastAction+1});
            Need(result.Ok&&p.Gold==expected,"Authoritative sale did not use displayed quote.");
        });

        Test("service sinks remain gentle early and scale into late progression",()=>
        {
            var realm=new RealmEngine(data);var low=realm.CreateCharacter("economy-low","Low Traveler","vanguard",new());
            long earlyRest=EconomyServices.RestPrice(low);
            foreach(var skill in data.Skills)low.SkillXp[skill.Id]=Progression.Threshold(100);
            long lateRest=EconomyServices.RestPrice(low);Need(earlyRest==5&&lateRest>earlyRest,"Inn rest did not scale from the early-game floor.");
            var settlements=data.Zones.Where(z=>z.Kind is "city" or "settlement").ToArray();var source=settlements.OrderBy(z=>z.Level).First();var near=settlements.OrderBy(z=>Math.Abs(z.WorldX-source.WorldX)+Math.Abs(z.WorldY-source.WorldY)).Skip(1).First();var far=settlements.OrderByDescending(z=>Math.Abs(z.WorldX-source.WorldX)+Math.Abs(z.WorldY-source.WorldY)+z.Level).First();
            long nearCost=EconomyServices.TravelPrice(data,low,source,near),farCost=EconomyServices.TravelPrice(data,low,source,far);Need(farCost>=nearCost&&nearCost>=15,"Travel cost does not reflect route/progression.");
            Need(EconomyServices.RepairPrice(data.Items.First(x=>x.Slot!=""),50)>0,"Repair sink disappeared.");
            Console.WriteLine($"ECONOMY CRAFTING METRIC rest_early={earlyRest} rest_late={lateRest} travel_near={nearCost} travel_far={farCost}");
        });

        Test("reclaiming gear is useful lossy station-bound and replay-safe",()=>
        {
            var recipe=data.Recipes.First(r=>data.Item(r.Output).Slot!=""&&CraftEconomy.Reclaim(data,Items.Create(data,r.Output)) is not null);
            var plan=CraftEconomy.Reclaim(data,Items.Create(data,recipe.Output))!;Need(plan.RecoveredValue>0&&plan.RecoveredValue*2<=plan.InputValue,"Reclaim exceeds half of recipe material value.");
            var stationNpc=data.Npcs.FirstOrDefault(n=>n.Station==plan.Recipe.Station);Need(stationNpc is not null,"No NPC station for reclaim fixture: "+plan.Recipe.Station);
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("economy-reclaim","Reclaim Tester","vanguard",new());p.Zone=stationNpc!.Zone;p.Position=stationNpc.Position;
            var gear=Items.Create(data,recipe.Output);Items.Add(p.Inventory,gear,data);int before=Items.Count(p,plan.Material);
            var command=new GameCommand{Kind="salvage",Item=gear.Id,Sequence=p.LastAction+1};var result=realm.Execute(p.Id,command);Need(result.Ok,"Reclaim rejected: "+result.Message);
            Need(p.Inventory.All(x=>x.Id!=gear.Id)&&Items.Count(p,plan.Material)==before+plan.Quantity,"Reclaim did not exchange gear for exact preview materials.");
            int after=Items.Count(p,plan.Material);var replay=realm.Execute(p.Id,command);Need(replay.Ok&&Items.Count(p,plan.Material)==after,"Replayed reclaim duplicated materials.");
            var remote=Items.Create(data,recipe.Output);Items.Add(p.Inventory,remote,data);p.Position=new Point(stationNpc.Position.X+20,stationNpc.Position.Y+20);
            var rejected=realm.Execute(p.Id,new GameCommand{Kind="salvage",Item=remote.Id,Sequence=p.LastAction+1});Need(!rejected.Ok&&p.Inventory.Any(x=>x.Id==remote.Id),"Remote reclaim consumed gear.");
        });

        Test("craft quality guidance exposes progression without changing rarity gates",()=>
        {
            var recipe=data.Recipes.First(r=>data.Item(r.Output).StackMax==1);var p=new Character();foreach(var skill in data.Skills)p.SkillXp[skill.Id]=0;
            string hint=CraftEconomy.QualityHint(p,recipe,data);Need(hint.Contains("next quality gate",StringComparison.Ordinal),"Crafting UI has no quality progression hint.");
            int previous=0;foreach(var rarity in Enum.GetValues<Rarity>()){int gate=Items.CraftRarityRequirement(rarity,recipe.Requirement);Need(gate>=previous,"Rarity gate order changed.");previous=gate;}
        });

        Console.WriteLine($"ECONOMY_CRAFTING_FEEL: {passed} groups passed; failures {failures.Count}.");
    }
}
''')

edit('tools/world_probe/Program.cs',
'''ExplorationRewardChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n''',
'''ExplorationRewardChecks.Run(catalog,failures);\nEconomyCraftingFeelChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n''')

write('docs/ECONOMY_CRAFTING.md',r'''# Economy and crafting feel

Status: implemented as Area 6 economy/crafting work.

The economy pass keeps the existing item IDs, combat statistics, skill gates and crafting professions, but makes the value loop easier to read and harder to exploit.

- Progression gear now consumes materials from its own grade. High-level medium/heavy armor and fittings no longer fall back to starter cured leather, and progression equipment base value is derived from its real recipe inputs.
- Common vendor-bought ingredients cannot be turned into guaranteed merchant profit by crafting and immediately reselling the output. Exceptional crafted quality can still be worth more, so mastery has upside without a deterministic gold-print loop.
- Specialist merchants, Bartering, faction reputation and item quality all improve sale quotes. The client displays the exact server quote rather than a generic base resale number.
- Bartering can train from selling as well as buying, on the same bounded cooldown.
- Inn rest and waystone travel remain inexpensive early but scale gradually with progression, destination threat and route distance. Repair and rune-extraction fees use the same shared server/client price functions shown in the UI.
- Unwanted non-unique gear with a real crafting route can be reclaimed at that route's station. Reclaiming destroys the item and returns one deterministic material stack worth less than half of the original recipe inputs. Equipped gear, socketed gear, boss signatures and regional exploration keepsakes cannot be reclaimed.
- The Crafting guide now shows material value, output base value, baseline merchant resale, the next rarity gate and a reclaim preview so players can make informed production choices.

`EconomyCraftingFeelChecks` audits progression recipe value, common vendor-crafting arbitrage, exact specialist sale quotes, scalable service sinks, authoritative/replay-safe reclaiming and unchanged rarity gate ordering in the normal world-probe suite.
''')

print('economy/crafting update applied')
