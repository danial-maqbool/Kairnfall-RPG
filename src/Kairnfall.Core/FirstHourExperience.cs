namespace Kairnfall.Core;

public sealed record FirstHourMilestone(string Id,string Name,string Guidance);

/// <summary>Persistent, low-friction guidance for the first 45–60 minutes. Markers live in Discoveries so old saves remain compatible.</summary>
public static class FirstHourExperience
{
    public const string Prefix="first_hour:";
    public static readonly IReadOnlyList<FirstHourMilestone> Steps =
    [
        new("movement","Get your bearings","Move with WASD. Interact [E] works on nearby people, resources, doors and exits."),
        new("npc","Meet a Wayfarer","Follow the gold ! to a local quest giver and press Interact [E]."),
        new("gather","Gather your first material","Work an oak tree, copper vein or other nearby resource. Your starter tools are already in the backpack."),
        new("craft","Make something useful","Follow A Place by the Fire and make its wooden handle at the sawbench. Crafting [C] shows station and ingredient readiness."),
        new("combat","Win your first fight","Target a nearby creature with Tab, hold basic attack, move out of telegraphs, and try a class art from the hotbar."),
        new("skill","Raise a skill level","Keep doing one real activity until a skill reaches level 2. The green XP bar shows the skill you trained most recently."),
        new("level","Raise your character level","Training any skills contributes to overall level. Reach character level 2 to open the next part of the journey."),
        new("equipment","Improve your equipment","Complete A Spark in the Stone and socket the starter rune, or equip a better-quality drop."),
        new("interior","Enter a real building","Walk through one of Wayfarer's Rest's named doors. Interiors contain the same service NPCs and reciprocal exits."),
        new("transition","Take the western road","Use the road exit to Kingsmeadow. Entrances name their destination and the map [M] shows the route."),
        new("social","See the social layer","Open Social [P]. Use local chat, LFG, or create/join a party; nearby travelers also appear in Recent Players."),
        new("miniboss","Defeat your first rare foe","Hunt the gold RARE elite in Kingsmeadow. Rare enemies are mini-bosses with stronger health, traits and rewards.")
    ];

    public static string Key(string id)=>Prefix+id;
    public static void Mark(Character player,string id)
    {
        if(Steps.Any(x=>x.Id==id)) player.Discoveries.Add(Key(id));
    }
    public static bool Marked(Character player,string id)=>player.Discoveries.Contains(Key(id));

    public static bool Completed(Catalog data,Character player,FirstHourMilestone step)=>step.Id switch
    {
        "movement" or "npc" or "gather" or "craft" or "combat" or "interior" or "transition" or "miniboss" => Marked(player,step.Id),
        "skill" => data.Skills.Any(skill=>Progression.BaseLevel(player,skill.Id)>=2),
        "level" => Progression.PlayerLevel(player)>=2,
        "equipment" => Marked(player,"equipment") || player.Equipment.Values
            .Select(id=>player.Inventory.FirstOrDefault(item=>item.Id==id)).Where(item=>item is not null)
            .Any(item=>item!.Runes.Count>0||item.Rarity>Rarity.Common||item.Affixes.Count>0),
        "social" => Marked(player,"social")||player.RecentPlayers.Count>0||player.Friends.Count>0||player.Party!=""||player.Guild!=""||player.LfgActivity!="",
        _ => false
    };
    public static FirstHourMilestone? Current(Catalog data,Character player)=>Steps.FirstOrDefault(step=>!Completed(data,player,step));
    public static int CompletedCount(Catalog data,Character player)=>Steps.Count(step=>Completed(data,player,step));

    public static void ObserveCommand(Character player,GameCommand command)
    {
        switch(command.Kind)
        {
            case "talk": Mark(player,"npc"); break;
            case "gather": Mark(player,"gather"); break;
            case "craft": Mark(player,"craft"); break;
            case "attack": case "cast": Mark(player,"combat"); break;
            case "equip": case "socket": Mark(player,"equipment"); break;
            case "chat": case "party_create": case "party_invite": case "party_join": case "lfg_set": case "lfg_request": case "friend_invite": case "friend_accept": Mark(player,"social"); break;
        }
    }
    public static void ObserveTransition(Character player,ZoneDef source,ZoneDef target)
    {
        if(target.Kind=="interior") Mark(player,"interior");
        if(source.Kind!="interior"&&target.Kind!="interior"&&target.Id!="wayfarers_rest") Mark(player,"transition");
    }
}
