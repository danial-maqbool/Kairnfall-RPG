using System.Globalization;
using System.Security.Cryptography;

namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private NpcDef Merchant(Character p,string id)
    {
        var npc=Data.Npc(id); Near(p,npc.Zone,npc.Position,3);
        Need(npc.Stock.Length>0,"This NPC does not trade goods."); return npc;
    }
    public long BuyPrice(Character p,NpcDef merchant,ItemDef item)=>MerchantSales.BuyUnitPrice(p,merchant,item);
    private string Buy(Character p,string merchant,string template,int quantity)
    {
        Need(quantity is >0 and <=99,"Buy between 1 and 99 items.");
        var npc=Merchant(p,merchant); var def=Data.Item(template);
        Need(npc.Stock.Contains(template),"This merchant does not sell that item.");
        string stockKey=npc.Id+"/"+template;
        Need(State.ShopStock.GetValueOrDefault(stockKey)>=quantity,"The merchant has insufficient stock.");
        long cost=checked(BuyPrice(p,npc,def)*quantity);
        Items.Spend(p,cost); Items.Add(p.Inventory,Items.Create(Data,template,quantity),Data);
        State.ShopStock[stockKey]-=quantity;
        if(p.Cooldowns.GetValueOrDefault("barter_xp")<=State.Time)
        {
            Progression.Train(p,"bartering",Math.Min(50,(int)Math.Min(cost,50)),def.Requirement,Data);
            p.Cooldowns["barter_xp"]=State.Time+10;
        }
        Progress(p,"buy",template,quantity); return $"Bought {quantity} {def.Name} for {cost} gold.";
    }
    private string Sell(Character p,string merchant,string itemId,int quantity)
    {
        var npc=Merchant(p,merchant); var item=Items.Owned(p,itemId); var def=Data.Item(item.Template);
        long value=MerchantSales.Quote(p,npc,item,quantity,Data);
        Items.Take(p.Inventory,itemId,quantity,p); Items.Grant(p,value);
        if(p.Cooldowns.GetValueOrDefault("barter_xp")<=State.Time)
        {
            Progression.Train(p,"bartering",Math.Min(50,(int)Math.Min(value,50)),def.Requirement,Data);
            p.Cooldowns["barter_xp"]=State.Time+10;
        }
        Progress(p,"sell",def.Id,quantity); return $"Sold for {value} gold.";
    }
    private string Gather(Character p,string nodeId)
    {
        Need(State.Nodes.TryGetValue(nodeId,out var node),"Resource not found.");
        Near(p,node!.Zone,node.Position);
        Need(node.ReadyAt<=State.Time,"This resource has not recovered yet.");
        bool crop=node.Template=="crop_wheat";
        Need(!crop||node.Owner==p.Id,"This crop belongs to another player.");
        var def=Data.Resource(crop?"wheat_crop":node.Template);
        Need(Progression.Level(p,def.Skill)>=def.Requirement,"Requires "+Data.Skill(def.Skill).Name+" "+def.Requirement+".");
        var tool=def.Tool==""?null:ToolRules.Best(p,Data,def.Tool,def.Skill=="farming"&&def.Tool=="sickle"?"herbalism":def.Skill);
        if(def.Tool!="") Need(tool is not null,"Keep a usable "+def.Tool+" in your backpack and meet its skill requirement.");
        double staminaCost=ToolRules.StaminaCost(tool);
        Need(p.Stamina>=staminaCost,"Recover stamina before gathering."); Ready(p,"gather",1.8);
        int bonus=(Progression.Level(p,def.Skill)-def.Requirement)/25;
        int quantity=1+RandomNumberGenerator.GetInt32(1+Math.Max(0,bonus));
        double yield=CombatMath.Stats(p,Data).Bonus("gather_yield")+ToolRules.Yield(tool);
        if(CombatMath.Roll(Math.Clamp(yield/100,0,0.35))) quantity++;
        Items.Add(p.Inventory,Items.Create(Data,def.Item,quantity),Data);
        p.Stamina-=staminaCost;
        Progression.Train(p,def.Skill,def.Xp,def.Requirement,Data);
        Progression.Train(p,"endurance",4,def.Requirement,Data);
        if(crop) State.Nodes.Remove(node.Id); else node.ReadyAt=State.Time+def.Respawn;
        Progress(p,"gather",def.Item,quantity);
        if(def.Skill=="fishing"&&WorldTime.Weather(Data.Zone(p.Zone),State.Time)=="storm")
            Progression.Train(p,"survival",8,def.Requirement,Data);
        return $"Gathered {quantity} {Data.Item(def.Item).Name}.";
    }
    private string Craft(Character p,string id,int quantity)
    {
        Need(quantity is >0 and <=20,"Craft between 1 and 20 batches.");
        var recipe=Data.Recipe(id);
        Need(Progression.Level(p,recipe.Skill)>=recipe.Requirement,"Requires "+Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+".");
        Need(AtStation(p,recipe.Station),"Use the "+recipe.Station+" station.");
        Ready(p,"craft",ToolRules.CraftRecovery(p,Data,recipe,quantity));
        foreach(var ingredient in recipe.Ingredients)
            Need(Items.Count(p,ingredient.Key)>=checked(ingredient.Value*quantity),"Missing "+Data.Item(ingredient.Key).Name+".");
        int outputCount=checked(recipe.Quantity*quantity);
        Need(outputCount<=999,"The crafting batch is too large.");
        foreach(var ingredient in recipe.Ingredients) Items.Consume(p,ingredient.Key,ingredient.Value*quantity);
        var output=Data.Item(recipe.Output);
        if(output.StackMax==1)
        {
            for(int n=0;n<outputCount;n++)
            {
                var rarity=Items.RollCraftRarity(Progression.Level(p,recipe.Skill),recipe.Requirement);
                Items.Add(p.Inventory,Items.Create(Data,output.Id,1,rarity,p),Data);
            }
        }
        else Items.Add(p.Inventory,Items.Create(Data,output.Id,outputCount),Data);
        Progression.Train(p,recipe.Skill,Math.Min(100000,recipe.Xp*quantity),recipe.Requirement,Data);
        Progress(p,"craft",output.Id,outputCount); return $"Crafted {outputCount} {output.Name}.";
    }
    private string Salvage(Character p,string id)
    {
        var item=Items.Owned(p,id);var def=Data.Item(item.Template);
        Need(!Items.Equipped(p,id),"Unequip this item before reclaiming materials.");
        Need(item.Runes.Count==0,"Extract socketed runes before reclaiming this item.");
        var plan=CraftEconomy.Reclaim(Data,item);Need(plan is not null,"This item has no reclaimable crafting route.");
        Need(AtStation(p,plan!.Recipe.Station),"Use the "+plan.Recipe.Station+" station to reclaim this item.");
        Ready(p,"salvage",1.2);
        Items.Take(p.Inventory,id,1,p);Items.Add(p.Inventory,Items.Create(Data,plan.Material,plan.Quantity),Data);
        Progress(p,"salvage",def.Id);
        return $"Reclaimed {plan.Quantity} {Data.Item(plan.Material).Name} from {def.Name}.";
    }
    private string Unsocket(Character p,string id,int index)
    {
        Need(NearService(p,"enchanter")||AtStation(p,"rune_table"),"Visit an enchanter or rune table.");
        var item=Items.Owned(p,id);
        Need(index>=0&&index<item.Runes.Count,"Invalid rune socket.");
        var rune=item.Runes[index]; var def=Data.Item(rune.Template);
        Items.Spend(p,EconomyServices.RuneExtractionPrice(def));
        var restored=Items.Create(Data,rune.Template); restored.Id=rune.Id;
        item.Runes.RemoveAt(index); Items.Add(p.Inventory,restored,Data);
        return "Rune extracted without destroying the equipment.";
    }
    private string Repair(Character p,string id)
    {
        Service(p,"blacksmith"); var item=Items.Owned(p,id); var def=Data.Item(item.Template);
        Need((def.Slot!=""||def.Type=="tool")&&item.Durability<100,"This item does not need repair.");
        long price=EconomyServices.RepairPrice(def,item.Durability);
        Items.Spend(p,price); item.Durability=100; return $"Repaired for {price} gold.";
    }
    private string Talk(Character p,string id)
    {
        var npc=Data.Npc(id); Near(p,npc.Zone,npc.Position,3); Progress(p,"talk",id);
        return npc.Name+": "+npc.Dialogue;
    }
    private string AcceptQuest(Character p,string id)
    {
        var quest=Data.Quest(id); var npc=Data.Npc(quest.Giver); Near(p,npc.Zone,npc.Position,3);
        Need(!p.Quests.ContainsKey(id),"You already accepted this quest.");
        Need(quest.Repeatable||!p.CompletedQuests.Contains(id),"You already completed this quest.");
        Need(quest.Prerequisite==""||p.CompletedQuests.Contains(quest.Prerequisite),"Complete the previous quest first.");
        Need(p.Cooldowns.GetValueOrDefault("quest:"+id)<=State.Time,"This repeatable quest is not available yet.");
        p.Quests[id]=new(){Counts=Enumerable.Repeat(0,quest.Objectives.Count).ToList()};
        Progress(p,"talk",npc.Id); return "Accepted: "+quest.Name;
    }
    private string ClaimQuest(Character p,string id)
    {
        var quest=Data.Quest(id); var npc=Data.Npc(quest.Giver); Near(p,npc.Zone,npc.Position,3);
        Need(p.Quests.TryGetValue(id,out var progress)&&progress.Complete,"This quest is not complete.");
        Need(quest.Repeatable||!p.CompletedQuests.Contains(id),"Reward already claimed.");
        foreach(var objective in quest.Objectives.Where(x=>x.Action=="deliver"))
            Items.Consume(p,objective.Target,objective.Count);
        Items.Grant(p,quest.Gold);
        if(quest.Reward!="") Items.Add(p.Inventory,Items.Create(Data,quest.Reward),Data);
        p.CompletedQuests.Add(id); p.Quests.Remove(id);
        p.Reputation[quest.Faction]=Math.Min(1000,p.Reputation.GetValueOrDefault(quest.Faction)+10);
        if(quest.Repeatable) p.Cooldowns["quest:"+id]=State.Time+WorldTime.DayLength;
        if(p.CompletedQuests.Count==10) p.Achievements.Add("helping_hand");
        return "Completed: "+quest.Name;
    }
    private string InspectLandmark(Character p,string id)
    {
        var zone=Data.Zone(p.Zone);
        var landmark=zone.Buildings.FirstOrDefault(x=>x.Id==id&&JourneyProgression.IsLandmark(zone,x))??throw new RuleException("Landmark not found.");
        Near(p,p.Zone,JourneyProgression.LandmarkPoint(landmark),2.5);
        bool first=p.Discoveries.Add(ExplorationRewards.LandmarkKey(zone,landmark));
        string clue="";
        if(first)
        {
            Progression.Train(p,"exploration",50,Math.Clamp(zone.Level,1,100),Data);
            clue=ExplorationRewards.TryRevealCacheClue(p,zone,Data);
        }
        Progress(p,"survey",landmark.Id);
        string mastery=ExplorationRewards.TryGrantRegionalReward(p,zone,Data);
        string verb=first?$"Surveyed {landmark.Name} in {zone.Name}.":$"Reviewed {landmark.Name} in {zone.Name}.";
        return verb+"\n"+ExplorationRewards.LandmarkLore(zone,landmark)+"\n"+ExplorationRewards.ProgressSummary(p,zone)+clue+mastery;
    }
    private string Transition(Character p,string exitId)
    {
        var source=Data.Zone(p.Zone);
        var exit=source.Exits.FirstOrDefault(x=>x.Id==exitId)??throw new RuleException("Unknown map exit.");
        Near(p,p.Zone,exit.Position,2.2);
        var target=Data.Zone(exit.Target);int currentLevel=Progression.PlayerLevel(p);
        int required=JourneyProgression.ExitRequirement(Data,exit);
        Need(currentLevel>=required,JourneyProgression.LockMessage(target,currentLevel,required));
        CancelTradesFor(p.Id); inputs.Remove(p.Id);
        p.Zone=target.Id; p.Position=WorldMap.FindFree(target,exit.Arrival);
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet)) { pet.Zone=p.Zone; pet.Position=p.Position; pet.Home=p.Position; }
        if(p.Discoveries.Add(p.Zone)) Progression.Train(p,"exploration",100,Math.Clamp(Data.Zone(p.Zone).Level,1,100),Data);
        Progress(p,"explore",p.Zone); return "Entered "+Data.Zone(p.Zone).Name+".";
    }
    private string Travel(Character p,string destination)
    {
        Need(p.Waypoints.Contains(destination),"Discover the destination waystone first.");
        var source=Data.Zone(p.Zone); var dest=Data.Zone(destination);
        Need(source.Kind is "city" or "settlement","Fast travel starts at a settlement waystone.");
        int currentLevel=Progression.PlayerLevel(p),required=JourneyProgression.EntryRequirement(Data,dest);
        Need(currentLevel>=required,JourneyProgression.LockMessage(dest,currentLevel,required));
        Near(p,p.Zone,source.Spawn,3);
        Need(State.Time-p.LastCombat>10,"You cannot travel during combat.");
        Need(dest.Kind is "city" or "settlement","Invalid fast-travel destination.");
        Need(dest.Id!=p.Zone,"You are already here."); long price=EconomyServices.TravelPrice(Data,p,source,dest);Items.Spend(p,price);
        CancelTradesFor(p.Id); inputs.Remove(p.Id); p.Zone=dest.Id; p.Position=dest.Spawn;
        if(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out var pet)) { pet.Zone=p.Zone; pet.Position=p.Position; }
        return $"Arrived at {dest.Name} for {price} gold.";
    }
    private string Consume(Character p,string id)
    {
        var item=Items.Owned(p,id); var def=Data.Item(item.Template); var stats=CombatMath.Stats(p,Data);
        Need(def.Type is "potion" or "food" or "scroll","This item cannot be consumed.");
        switch(def.Effect)
        {
            case "heal": Need(p.Health<stats.Health,"Your health is full."); Ready(p,"potion",5); p.Health=Math.Min(stats.Health,p.Health+Math.Max(25,def.Power)); break;
            case "mana": Need(p.Mana<stats.Mana,"Your mana is full."); Ready(p,"potion",5); p.Mana=Math.Min(stats.Mana,p.Mana+Math.Max(25,def.Power)); break;
            case "food": Need(p.Health<stats.Health||p.Stamina<stats.Stamina,"You do not need food yet."); Ready(p,"food",8); ApplyStatus(p.Statuses,"regeneration",Element.Nature,12,Math.Max(2,def.Power/12),p.Id); p.Stamina=Math.Min(stats.Stamina,p.Stamina+20); break;
            case "purge": Need(p.Statuses.Any(x=>x.Kind is "poison" or "burn" or "curse"),"No harmful condition to remove."); Ready(p,"potion",5); p.Statuses.RemoveAll(x=>x.Kind is "poison" or "burn" or "curse"); break;
            default: throw new RuleException("This consumable effect is unavailable.");
        }
        Items.Take(p.Inventory,id,1,p); Progress(p,"consume",def.Id); return "Used "+def.Name+".";
    }
    private string Rest(Character p)
    {
        bool camp=State.Nodes.Values.Any(x=>x.Template=="structure_campfire"&&x.Zone==p.Zone&&x.Position.Distance(p.Position)<=3);
        Need(NearService(p,"innkeeper")||camp,"Rest at an inn or campfire.");
        Need(State.Time-p.LastCombat>10,"You cannot rest during combat.");
        var stats=CombatMath.Stats(p,Data);
        Need(p.Health<stats.Health||p.Mana<stats.Mana||p.Stamina<stats.Stamina,"You are already fully rested.");
        long price=camp?0:EconomyServices.RestPrice(p);Ready(p,"rest",10);if(price>0)Items.Spend(p,price);
        p.Health=stats.Health; p.Mana=stats.Mana; p.Stamina=stats.Stamina;
        Progression.Train(p,"survival",5,Math.Clamp(Data.Zone(p.Zone).Level,1,100),Data);
        return price==0?"Health, mana, and stamina restored at camp.":$"Health, mana, and stamina restored for {price} gold.";
    }
    private string Respawn(Character p)
    {
        Need(p.Health<=0,"You are not dead."); Need(State.Time>=p.DeadUntil,"Respawn is not ready yet.");
        string destination=p.Waypoints.Contains("dawnreach")?"dawnreach":"wayfarers_rest";
        p.Zone=destination; p.Position=Data.Zone(destination).Spawn;
        var stats=CombatMath.Stats(p,Data); p.Health=stats.Health; p.Mana=stats.Mana; p.Stamina=stats.Stamina;
        p.Statuses.Clear(); p.LastCombat=State.Time-20;
        return "You awaken at "+Data.Zone(destination).Name+".";
    }
    private string CollectLoot(Character p,string id)
    {
        Need(Loot.TryGetValue(id,out var pile),"Loot is no longer available."); Near(p,pile!.Zone,pile.Position);
        Need(pile.Owner==p.Id||pile.PublicAt<=State.Time||(pile.Party!=""&&pile.Party==p.Party),"This loot belongs to another player.");
        foreach(var item in pile.Items) { Items.Add(p.Inventory,item,Data); Progress(p,"loot",item.Template,item.Quantity); }
        Items.Grant(p,pile.Gold); Loot.Remove(id); return "Loot collected.";
    }
    private string OpenChest(Character p,string id)
    {
        Need(State.Chests.TryGetValue(id,out var chest),"Chest not found."); Near(p,chest!.Zone,chest.Position);
        Need(chest.ReadyAt<=State.Time,"This chest is empty.");
        Need(!chest.Hidden||p.Discoveries.Contains("secret:"+id),"Find this chest before opening it.");
        Ready(p,"chest",1);
        if(chest.Kind=="locked")
        {
            Need(Progression.Level(p,"lockpicking")>=chest.Requirement,"Your Lockpicking skill is too low.");
            Items.Consume(p,"lockpick",1); Progression.Train(p,"lockpicking",60,chest.Requirement,Data);
        }
        if(chest.Kind=="runic") Need(Progression.Level(p,"runecasting")>=Math.Max(1,chest.Requirement/2),"Your Runecasting skill is too low.");
        var candidates=Data.Items.Where(x=>x.Slot!=""&&x.Type!="tool"&&x.Requirement<=Math.Min(100,chest.Requirement+10)&&x.Requirement>=Math.Max(1,chest.Requirement-20)).ToArray();
        if(candidates.Length>0) Items.Add(p.Inventory,Items.Create(Data,candidates[RandomNumberGenerator.GetInt32(candidates.Length)].Id,1,Items.RollRarity(300)),Data);
        if(chest.Kind=="runic")
        {
            var runes=Data.Items.Where(x=>x.Type=="rune"&&x.Tier<=1+chest.Requirement/25).ToArray();
            if(runes.Length>0) Items.Add(p.Inventory,Items.Create(Data,runes[RandomNumberGenerator.GetInt32(runes.Length)].Id),Data);
            Progression.Train(p,"runecasting",50,chest.Requirement,Data);
        }
        Items.Grant(p,10+chest.Requirement*3); chest.ReadyAt=State.Time+600;
        Progression.Train(p,"treasure_hunting",80,chest.Requirement,Data); Progress(p,"chest",chest.Kind);
        string exploration="";var chestZone=Data.Zone(chest.Zone);
        if(chest.Hidden&&ExplorationRewards.Eligible(chestZone)&&id==ExplorationRewards.CacheId(chestZone)&&p.Discoveries.Add(ExplorationRewards.CacheOpenedKey(chestZone)))
        {
            Progression.Train(p,"treasure_hunting",60,chest.Requirement,Data);p.Achievements.Add("cache:"+chestZone.Id);
            exploration="\nFIRST CACHE · This region's hidden cache is now recorded in your exploration journal.";
        }
        string mastery=ExplorationRewards.TryGrantRegionalReward(p,chestZone,Data);
        return "Chest opened."+exploration+mastery+(ExplorationRewards.Eligible(chestZone)?"\n"+ExplorationRewards.ProgressSummary(p,chestZone):"");
    }
    private string AuctionList(Character p,string id,int quantity,string priceText)
    {
        Service(p,"auctioneer");
        Need(long.TryParse(priceText,NumberStyles.None,CultureInfo.InvariantCulture,out long price)&&price is >0 and <=1_000_000_000,"Enter a valid whole-gold price.");
        Need(State.Auctions.Values.Count(x=>x.Seller==p.Id)<20,"You have reached the auction listing limit.");
        var item=Items.Owned(p,id); Need(Data.Item(item.Template).Type!="quest","Quest items cannot be auctioned.");
        Items.Spend(p,Math.Max(1,price/50));
        var escrow=Items.Take(p.Inventory,id,quantity,p);
        var auction=new Auction{Seller=p.Id,Item=escrow,Price=price,Expires=State.Time+WorldTime.DayLength*24};
        State.Auctions.Add(auction.Id,auction); return "Auction listing created.";
    }
    private string AuctionBuy(Character p,string id)
    {
        Service(p,"auctioneer"); Need(State.Auctions.TryGetValue(id,out var auction),"This listing is no longer available.");
        Need(auction!.Seller!=p.Id,"You cannot purchase your own listing."); Need(auction.Expires>State.Time,"This listing has expired.");
        var seller=Player(auction.Seller); Items.Spend(p,auction.Price);
        Items.Add(p.Inventory,auction.Item,Data); Items.Grant(seller,auction.Price); State.Auctions.Remove(id);
        return "Auction purchase completed.";
    }
    private string AuctionCancel(Character p,string id)
    {
        Service(p,"auctioneer"); Need(State.Auctions.TryGetValue(id,out var auction)&&auction.Seller==p.Id,"You do not own this listing.");
        Items.Add(p.Inventory,auction!.Item,Data); State.Auctions.Remove(id); return "Auction cancelled. The listing fee is not refunded.";
    }
    private string Plant(Character p,Point at)
    {
        var zone=Data.Zone(p.Zone); Near(p,p.Zone,at,2);
        Need(zone.Layer=="Surface"&&WorldMap.TileAt(zone,(int)at.X,(int)at.Y) is Terrain.Grass or Terrain.Dirt or Terrain.Moss,"Crops need suitable surface soil.");
        Need(!State.Nodes.Values.Any(x=>x.Zone==p.Zone&&x.Position.Distance(at)<1),"A resource already occupies this plot.");
        Need(State.Nodes.Values.Count(x=>x.Owner==p.Id&&x.Template=="crop_wheat")<12,"You can maintain at most twelve crops.");
        Items.Consume(p,"wheat_seed",1); Ready(p,"plant",2);
        string id=Guid.NewGuid().ToString("N");
        State.Nodes[id]=new(){Id=id,Template="crop_wheat",Zone=p.Zone,Position=at,Owner=p.Id,ReadyAt=State.Time+Math.Max(30,90-Progression.Level(p,"farming")*0.4)};
        Progress(p,"plant","wheat"); return "Wheat planted. Harvest it after it matures.";
    }
    private string Build(Character p,string recipeId,Point at)
    {
        var recipe=Data.Recipe(recipeId); var item=Data.Item(recipe.Output);
        Need(item.Type=="structure","Select a structure recipe.");
        Near(p,p.Zone,at,3); var zone=Data.Zone(p.Zone);
        Need(zone.Kind=="wilderness"&&WorldMap.Fits(zone,at),"Build in clear wilderness terrain.");
        Need(zone.Exits.All(x=>x.Position.Distance(at)>5)&&zone.Spawn.Distance(at)>5,"Do not obstruct a travel point.");
        Need(State.Nodes.Values.Count(x=>x.Owner==p.Id&&x.Template.StartsWith("structure_",StringComparison.Ordinal))<5,"You can maintain at most five structures.");
        Need(Progression.Level(p,"construction")>=recipe.Requirement,"Your Construction skill is too low.");
        foreach(var ingredient in recipe.Ingredients) Items.Consume(p,ingredient.Key,ingredient.Value);
        string id=Guid.NewGuid().ToString("N"); State.Nodes[id]=new(){Id=id,Template=item.Id,Zone=p.Zone,Position=at,Owner=p.Id};
        Progression.Train(p,"construction",recipe.Xp,recipe.Requirement,Data); Progress(p,"build",item.Id); return "Built "+item.Name+".";
    }
    private string Tame(Character p,string target)
    {
        Need(State.Creatures.TryGetValue(target,out var mob)&&mob.Health>0,"Creature not found."); Near(p,mob!.Zone,mob.Position,2.5);
        var def=Data.Mob(mob.Template);
        Need(def.Anatomy.StartsWith("animal:",StringComparison.Ordinal)&&!def.Boss&&!def.Elite&&mob.Owner=="","This creature cannot be tamed.");
        Need(p.Pet==""||!State.Creatures.TryGetValue(p.Pet,out var previous)||previous.Health<=0,"You already have an active companion.");
        Need(Progression.Level(p,"animal_handling")>=def.Level,"Your Animal Handling skill is too low.");
        Need(mob.Health<=def.Health*0.5,"Weaken the creature before taming it.");
        Items.Consume(p,"animal_bait",1); Ready(p,"tame",10);
        mob.Owner=p.Id; mob.Target=""; mob.Threat.Clear(); mob.Health=def.Health; p.Pet=mob.Id;
        Progression.Train(p,"animal_handling",60,def.Level,Data); Progress(p,"tame",def.Id); return "The creature becomes your companion.";
    }
    private string Feed(Character p,string itemId)
    {
        Need(p.Pet!=""&&State.Creatures.TryGetValue(p.Pet,out _),"You have no companion."); var pet=State.Creatures[p.Pet]; Near(p,pet.Zone,pet.Position,3);
        var food=Items.Owned(p,itemId); Need(Data.Item(food.Template).Type=="food","Use a food item.");
        var def=Data.Mob(pet.Template); Need(pet.Health>0&&pet.Health<def.Health,"Your companion does not need healing.");
        Ready(p,"feed",10); Items.Take(p.Inventory,itemId,1,p); pet.Health=Math.Min(def.Health,pet.Health+30);
        Progression.Train(p,"animal_handling",10,def.Level,Data); return "Companion fed.";
    }
    private string Prospect(Character p,string nodeId)
    {
        Need(State.Nodes.TryGetValue(nodeId,out var node),"Ore deposit not found."); Near(p,node!.Zone,node.Position);
        var resource=Data.Resource(node.Template); Need(resource.Skill=="mining"&&node.ReadyAt<=State.Time,"Prospect an available ore deposit.");
        Need(Progression.Level(p,"prospecting")>=resource.Requirement,"Your Prospecting skill is too low.");
        Ready(p,"prospect:"+nodeId,resource.Respawn+5); Need(p.Stamina>=10,"Not enough stamina."); p.Stamina-=10;
        Progression.Train(p,"prospecting",20,resource.Requirement,Data);
        if(CombatMath.Roll(0.15+Progression.Level(p,"prospecting")*0.002)) { Items.Add(p.Inventory,Items.Create(Data,"rough_gem"),Data); return "Found a rough gemstone in the seam."; }
        return "The seam contains "+Data.Item(resource.Item).Name+".";
    }
    private string Chart(Character p)
    {
        var zone=Data.Zone(p.Zone); Need(!p.Discoveries.Contains("charted:"+zone.Id),"You have already charted this region.");
        int found=ExplorationRewards.SectorCount(p,zone);
        Need(found>=ExplorationRewards.RequiredChartSectors,$"Explore at least {ExplorationRewards.RequiredChartSectors} real map sectors before drawing a regional chart ({found}/{ExplorationRewards.RequiredChartSectors}).");
        Items.Consume(p,"parchment",1); Items.Consume(p,"ink",1);
        p.Discoveries.Add("charted:"+zone.Id); Progression.Train(p,"cartography",120,Math.Clamp(zone.Level,1,100),Data);
        Progress(p,"chart",zone.Id);string mastery=ExplorationRewards.TryGrantRegionalReward(p,zone,Data);
        return "Regional chart completed. Roads and known exits are now recorded."+mastery+(ExplorationRewards.Eligible(zone)?"\n"+ExplorationRewards.ProgressSummary(p,zone):"");
    }
    private string Read(Character p,string itemId)
    {
        var item=Items.Owned(p,itemId); var def=Data.Item(item.Template);
        Need(def.Type is "book" or "treasure_map","This item has no readable text.");
        if(p.Discoveries.Add("read:"+def.Id))
        {
            Progression.Train(p,def.Type=="treasure_map"?"treasure_hunting":"scribing",30,def.Requirement,Data);
            Progress(p,"read",def.Id);
        }
        return def.Description;
    }
}
