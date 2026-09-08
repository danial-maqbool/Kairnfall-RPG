using System.Text.Json;

namespace Kairnfall.Core;

public sealed class Catalog
{
    public List<SkillDef> Skills { get; set; } = [];
    public List<ClassDef> Classes { get; set; } = [];
    public List<ItemDef> Items { get; set; } = [];
    public List<AbilityDef> Abilities { get; set; } = [];
    public List<RecipeDef> Recipes { get; set; } = [];
    public List<ZoneDef> Zones { get; set; } = [];
    public List<MobDef> Mobs { get; set; } = [];
    public List<ResourceDef> Resources { get; set; } = [];
    public List<NpcDef> Npcs { get; set; } = [];
    public List<QuestDef> Quests { get; set; } = [];
    public ItemDef Item(string id) => Items.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown item.");
    public SkillDef Skill(string id) => Skills.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown skill.");
    public ClassDef Class(string id) => Classes.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown class.");
    public ZoneDef Zone(string id) => Zones.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown zone.");
    public MobDef Mob(string id) => Mobs.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown creature.");
    public AbilityDef Ability(string id) => Abilities.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown ability.");
    public RecipeDef Recipe(string id) => Recipes.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown recipe.");
    public NpcDef Npc(string id) => Npcs.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown NPC.");
    public QuestDef Quest(string id) => Quests.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown quest.");
    public ResourceDef Resource(string id) => Resources.FirstOrDefault(x=>x.Id==id) ?? throw new RuleException("Unknown resource.");
    public static Catalog Load(string path)
    {
        var value=JsonSerializer.Deserialize<Catalog>(File.ReadAllText(path),Wire.Json) ?? throw new InvalidDataException("Empty catalog.");
        var errors=value.Validate();
        if(errors.Count>0) throw new InvalidDataException(string.Join("\n",errors));
        return value;
    }
    public List<string> Validate()
    {
        var errors=new List<string>();
        void Unique(IEnumerable<string> ids,string group)
        {
            var seen=new HashSet<string>();
            foreach(var id in ids) if(string.IsNullOrWhiteSpace(id)||!seen.Add(id)) errors.Add($"{group}: duplicate or empty ID {id}");
        }
        Unique(Skills.Select(x=>x.Id),"skills"); Unique(Classes.Select(x=>x.Id),"classes");
        Unique(Items.Select(x=>x.Id),"items"); Unique(Abilities.Select(x=>x.Id),"abilities");
        Unique(Recipes.Select(x=>x.Id),"recipes"); Unique(Zones.Select(x=>x.Id),"zones");
        Unique(Mobs.Select(x=>x.Id),"mobs"); Unique(Resources.Select(x=>x.Id),"resources");
        Unique(Npcs.Select(x=>x.Id),"NPCs"); Unique(Quests.Select(x=>x.Id),"quests");
        var skills=Skills.Select(x=>x.Id).ToHashSet(); var items=Items.Select(x=>x.Id).ToHashSet();
        var zones=Zones.Select(x=>x.Id).ToHashSet(); var mobs=Mobs.Select(x=>x.Id).ToHashSet();
        var npcs=Npcs.Select(x=>x.Id).ToHashSet(); var quests=Quests.Select(x=>x.Id).ToHashSet();
        foreach(var item in Items)
        {
            if(item.StackMax<1||item.StackMax>999||item.Value<0||item.Requirement<1||item.Requirement>100||string.IsNullOrEmpty(item.Icon)) errors.Add($"Invalid item {item.Id}");
            if(item.Skill!=""&&!skills.Contains(item.Skill)) errors.Add($"Item skill {item.Id}");
        }
        foreach(var recipe in Recipes)
        {
            if(!skills.Contains(recipe.Skill)||!items.Contains(recipe.Output)||recipe.Ingredients.Count==0||recipe.Quantity<1) errors.Add($"Invalid recipe {recipe.Id}");
            if(recipe.Ingredients.Any(x=>!items.Contains(x.Key)||x.Value<1)) errors.Add($"Recipe ingredient {recipe.Id}");
        }
        foreach(var ability in Abilities) if(!skills.Contains(ability.Skill)||ability.Cooldown<0.1||ability.Mana<0||ability.Stamina<0||ability.Range<0||!double.IsFinite(ability.Power)) errors.Add($"Invalid ability {ability.Id}");
        foreach(var node in Resources) if(!items.Contains(node.Item)||!skills.Contains(node.Skill)||node.Respawn<1) errors.Add($"Invalid resource {node.Id}");
        foreach(var mob in Mobs) if(mob.Health<=0||mob.Drops.Any(x=>!items.Contains(x))) errors.Add($"Invalid creature {mob.Id}");
        foreach(var npc in Npcs) if(!zones.Contains(npc.Zone)||npc.Stock.Any(x=>!items.Contains(x))) errors.Add($"Invalid NPC {npc.Id}");
        foreach(var quest in Quests)
        {
            if(!npcs.Contains(quest.Giver)||quest.Objectives.Count==0||quest.Objectives.Any(x=>x.Count<1)||quest.Gold<0) errors.Add($"Invalid quest {quest.Id}");
            if(quest.Reward!=""&&!items.Contains(quest.Reward)) errors.Add($"Quest reward {quest.Id}");
            if(quest.Prerequisite!=""&&!quests.Contains(quest.Prerequisite)) errors.Add($"Quest prerequisite {quest.Id}");
            var current=quest; var visited=new HashSet<string>{quest.Id};
            while(current.Prerequisite!="" && quests.Contains(current.Prerequisite))
            {
                if(!visited.Add(current.Prerequisite)) { errors.Add($"Quest prerequisite cycle {quest.Id}"); break; }
                current=Quests.First(x=>x.Id==current.Prerequisite);
            }
        }
        foreach(var zone in Zones)
        {
            FurnishingDef.Validate(zone,errors);
            if(zone.Width<16||zone.Height<16||!WorldMap.Walkable(zone,zone.Spawn)) errors.Add($"Invalid spawn {zone.Id}");
            if(zone.Species.Any(x=>!mobs.Contains(x))||(zone.Boss!=""&&!mobs.Contains(zone.Boss))) errors.Add($"Invalid zone creature {zone.Id}");
            foreach(var exit in zone.Exits)
            {
                if(!zones.Contains(exit.Target)) { errors.Add($"Missing exit target {zone.Id}/{exit.Id}"); continue; }
                var dest=Zone(exit.Target);
                if(!WorldMap.Walkable(zone,exit.Position)||!WorldMap.Walkable(dest,exit.Arrival)) errors.Add($"Blocked transition {zone.Id}/{exit.Id}");
                if(!dest.Exits.Any(x=>x.Target==zone.Id)) errors.Add($"No return transition {zone.Id}/{exit.Id}");
            }
        }
        if(Zones.Count>0)
        {
            var reached=new HashSet<string>(); var queue=new Queue<string>(); queue.Enqueue(Zones[0].Id);
            while(queue.TryDequeue(out var id))
            {
                if(!reached.Add(id)) continue;
                foreach(var e in Zone(id).Exits) if(zones.Contains(e.Target)) queue.Enqueue(e.Target);
            }
            foreach(var z in Zones) if(!reached.Contains(z.Id)) errors.Add($"Unreachable zone {z.Id}");
        }
        return errors;
    }
}
