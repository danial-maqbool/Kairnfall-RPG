using System.Text.Json;

namespace Kairnfall.Core;

/// <summary>Original optional local tutorial. Values are local tuning, not measured Mystera balance.</summary>
public sealed class ClassicTutorialTuning
{
    public double FoodDrainPerSecond { get; set; } = .04;
    public double FoodRestore { get; set; } = 25;
    public double StartingFood { get; set; } = 70;
    public int MilestoneXp { get; set; } = 120;
    public double ResourceRecoverySeconds { get; set; } = 3;
    public double SignApproachRadius { get; set; } = 1.25;
    public double TileZoom { get; set; } = 1.125;
    public double AvatarScale { get; set; } = .8;
    public void Validate()
    {
        if (!double.IsFinite(FoodDrainPerSecond) || FoodDrainPerSecond is <0 or >1
            || !double.IsFinite(FoodRestore) || FoodRestore is <1 or >100
            || !double.IsFinite(StartingFood) || StartingFood is <0 or >100
            || MilestoneXp is <1 or >10000 || !double.IsFinite(ResourceRecoverySeconds) || ResourceRecoverySeconds is <1 or >300
            || !double.IsFinite(SignApproachRadius) || SignApproachRadius is <1 or >2
            || !double.IsFinite(TileZoom) || TileZoom is <1 or >1.5
            || !double.IsFinite(AvatarScale) || AvatarScale is <.5 or >1)
            throw new InvalidDataException("Invalid classic tutorial tuning; no world was replaced.");
    }
}
public sealed class ClassicTutorialProgress
{
    public double Food { get; set; }
    public HashSet<string> Completed { get; set; } = [];
    public long NoticeId { get; set; }
    public string Notice { get; set; } = "";
}
public sealed record ClassicTutorialSite(string Id,string Name,string Kind,Point Position,string Text);
public static class ClassicTutorialContent
{
    public const string ZoneId="classic_first_glade",Questing="classic_questing";
    public static readonly ClassicTutorialSite[] Sites=
    [
        new("classic_first_sign","First Steps","sign",new(14.5,12.5),"Arrows or WASD move one tile at a time. Face a sign, tree or fountain and press Space, or use the Action Circle."),
        new("classic_fountain","Quiet Fountain","fountain",new(10.5,12.5),"Clear water runs over the stones. This local fountain is an interaction lesson; it does not grant unobserved healing or Food."),
        new("classic_craft_sign","Make Something","sign",new(19.5,12.5),"Open Tools to craft. Stone Pickaxe uses 10 Stone and 5 Wood, with base Damage +4. Fire uses 3 Tinder, 1 Flint and 5 Wood. Info lists each requirement."),
        new("classic_rat_sign","A Small Challenge","sign",new(24.5,16.5),"Click the rat to select it, then move into reach to attack. Shift picks up owned loot under your feet. Eat berries to restore Food.")
    ];
    public static readonly HashSet<string> Milestones=["first_steps","read_sign","fountain","wood","stone","food","pickaxe","fire","rat"];
    private static readonly string[] TutorialItems=["classic_wood","classic_stone","classic_tinder","classic_flint","classic_berries","classic_stone_pickaxe"];
    private static readonly (string Id,string Item,string Skill)[] TutorialResources=
    [
        ("classic_tree","classic_wood","woodcutting"),("classic_stone_node","classic_stone","mining"),
        ("classic_tinder_node","classic_tinder","herbalism"),("classic_flint_node","classic_flint","mining")
    ];
    public static void RequireLocalStartup(bool requested,bool hasTutorialCatalog,bool testingEnvironment,bool allowLocalHttp,IEnumerable<string> bindAddresses)
    {
        if(!requested&&!hasTutorialCatalog)return;
        var addresses=bindAddresses.ToArray();
        bool isolated=addresses.Length>0&&addresses.All(address=>
            Uri.TryCreate(address,UriKind.Absolute,out var uri)&&uri.Scheme is "http" or "https"
            &&uri.IsLoopback&&uri.UserInfo==""&&uri.AbsolutePath=="/"&&uri.Query==""&&uri.Fragment=="");
        if(!requested||!testingEnvironment||!allowLocalHttp||!isolated)
            throw new InvalidOperationException("Classic tutorial startup requires explicit opt-in and the authorized loopback Testing realm.");
    }
    public static void ValidateCatalog(Catalog data,List<string> errors)
    {
        if(data.ClassicTutorial is null)
        {
            if(data.Zones.Any(x=>x.Id==ZoneId)||data.Skills.Any(x=>x.Id==Questing)
                ||data.Items.Any(x=>TutorialItems.Contains(x.Id))
                ||data.Resources.Any(x=>TutorialResources.Any(required=>required.Id==x.Id))
                ||data.Recipes.Any(x=>x.Id is "classic_make_pickaxe" or "classic_make_fire")
                ||data.Zones.Any(x=>x.Furnishings.Any(f=>Sites.Any(site=>site.Id==f.Id))
                    ||x.Exits.Any(e=>e.Target==ZoneId)))
                errors.Add("Classic tutorial content requires its explicit catalog mode and tuning.");
            return;
        }
        try { data.ClassicTutorial.Validate(); }
        catch(InvalidDataException error) { errors.Add(error.Message); }
        foreach(string skill in new[]{Questing,"mining","woodcutting","construction","herbalism"})
            if(!data.Skills.Any(x=>x.Id==skill))errors.Add("Classic tutorial missing skill "+skill);
        foreach(string item in TutorialItems.Concat(["structure_campfire","healing_potion"]))
            if(!data.Items.Any(x=>x.Id==item))errors.Add("Classic tutorial missing item "+item);
        var berries=data.Items.FirstOrDefault(x=>x.Id=="classic_berries");
        if(berries is not null&&(berries.Type!="food"||berries.Effect!="food"))
            errors.Add("Classic tutorial berries must retain their food interaction.");
        var pickaxe=data.Items.FirstOrDefault(x=>x.Id=="classic_stone_pickaxe");
        if(pickaxe is not null&&(pickaxe.Type!="tool"||pickaxe.Slot!="weapon"||pickaxe.Skill!="mining"||!pickaxe.Tags.Contains("pickaxe")))
            errors.Add("Classic tutorial pickaxe must retain its equipment and gathering references.");
        if(!data.Mobs.Any(x=>x.Id=="field_rat"))errors.Add("Classic tutorial missing creature field_rat");
        if(data.Classes.Count==0)errors.Add("Classic tutorial requires starter classes.");
        foreach(var cls in data.Classes)
            if(!data.Items.Any(x=>x.Id==cls.Weapon)||!data.Items.Any(x=>x.Id==cls.Armor))
                errors.Add("Classic tutorial missing starter equipment "+cls.Id);
        foreach(var required in TutorialResources)
        {
            var node=data.Resources.FirstOrDefault(x=>x.Id==required.Id);
            if(node is null||node.Item!=required.Item||node.Skill!=required.Skill
                ||node.Respawn!=data.ClassicTutorial.ResourceRecoverySeconds)
                errors.Add("Classic tutorial missing or mismatched resource "+required.Id);
        }
        foreach(var (id,output,skill,ingredients) in new[]{
            ("classic_make_pickaxe","classic_stone_pickaxe","mining",new[]{"classic_stone","classic_wood"}),
            ("classic_make_fire","structure_campfire","construction",new[]{"classic_tinder","classic_flint","classic_wood"})})
        {
            var recipe=data.Recipes.FirstOrDefault(x=>x.Id==id);
            if(recipe is null||recipe.Output!=output||recipe.Skill!=skill||recipe.Station!="hand"
                ||recipe.Ingredients is null||ingredients.Any(item=>!recipe.Ingredients.ContainsKey(item)))
                errors.Add("Classic tutorial missing or mismatched recipe "+id);
        }
        var zone=data.Zones.FirstOrDefault(x=>x.Id==ZoneId);
        var city=data.Zones.FirstOrDefault(x=>x.Id=="wayfarers_rest");
        if(zone is null)errors.Add("Classic tutorial missing region "+ZoneId);
        if(city is null)errors.Add("Classic tutorial missing region wayfarers_rest");
        if(zone is not null)
        {
            foreach(var site in Sites)
                if(!zone.Furnishings.Any(x=>x.Id==site.Id&&x.Kind=="classic_"+site.Kind
                    &&x.X==(int)site.Position.X&&x.Y==(int)site.Position.Y&&x.Width==1&&x.Height==1&&x.Solid))
                    errors.Add("Classic tutorial missing or mismatched interaction site "+site.Id);
            if(!zone.Exits.Any(x=>x.Id=="classic_glade_to_wayfarers"&&x.Target=="wayfarers_rest"))
                errors.Add("Classic tutorial missing exit to Wayfarer's Rest.");
        }
        if(city is not null&&!city.Exits.Any(x=>x.Id=="wayfarers_to_classic_glade"&&x.Target==ZoneId))
            errors.Add("Classic tutorial missing return exit from Wayfarer's Rest.");
    }
    public static void Enable(Catalog data,ClassicTutorialTuning? tuning=null)
    {
        // Validate before cloning, including already-overlaid catalogs. Repeated
        // activation never silently replaces the authority's existing tuning.
        tuning?.Validate();
        var errors=data.Validate();
        if(errors.Count>0)throw new InvalidDataException(string.Join("\n",errors));
        if(data.ClassicTutorial is not null)
        {
            if(tuning is not null&&JsonSerializer.Serialize(tuning,Wire.Json)!=JsonSerializer.Serialize(data.ClassicTutorial,Wire.Json))
                throw new InvalidDataException("Classic tutorial catalog already contains different tuning; no catalog was changed.");
            return;
        }
        var staged=Wire.Copy(data);
        ApplyOverlay(staged,Wire.Copy(tuning??new ClassicTutorialTuning()));
        errors=staged.Validate();
        if(errors.Count>0)throw new InvalidDataException(string.Join("\n",errors));
        // No throwing operations remain: failed construction/validation cannot
        // modify the caller's catalog, city exits, list objects or tuning.
        data.Skills=staged.Skills;data.Items=staged.Items;data.Recipes=staged.Recipes;
        data.Resources=staged.Resources;data.Zones=staged.Zones;data.ClassicTutorial=staged.ClassicTutorial;
    }
    private static void ApplyOverlay(Catalog data,ClassicTutorialTuning tuning)
    {
        data.ClassicTutorial=tuning;
        data.Skills.Add(new(){Id=Questing,Name="Questing",Category="Exploration",Action="Complete original local tutorial milestones",Benefit="Records the local tutorial journey"});
        foreach(var (id,name,icon) in new[]{("classic_wood","Wood","oak_log"),("classic_stone","Stone","copper_ore"),("classic_tinder","Tinder","meadow_leaf"),("classic_flint","Flint","rough_gem")})
            data.Items.Add(new(){Id=id,Name=name,Type="material",Icon=icon,StackMax=999,Description="A material for the original local tutorial recipes."});
        data.Items.Add(new(){Id="classic_berries",Name="Berries",Type="food",Effect="food",Icon="bread",StackMax=99,Power=5,Description="Restores Food using this world's documented local tuning; also uses native food recovery."});
        data.Items.Add(new(){Id="classic_stone_pickaxe",Name="Stone Pickaxe",Type="tool",Slot="weapon",Skill="mining",Icon="copper_pickaxe",Power=4,Tags=["pickaxe"],Description="Base Damage +4. Made from 10 Stone and 5 Wood. Local rarity effects and native combat rules still apply."});
        data.Recipes.Add(new(){Id="classic_make_pickaxe",Name="Stone Pickaxe",Skill="mining",Station="hand",Ingredients=new(){{"classic_stone",10},{"classic_wood",5}},Output="classic_stone_pickaxe",Xp=25});
        data.Recipes.Add(new(){Id="classic_make_fire",Name="Fire",Skill="construction",Station="hand",Ingredients=new(){{"classic_tinder",3},{"classic_flint",1},{"classic_wood",5}},Output="structure_campfire",Xp=25});
        foreach(var (id,name,item,skill,sprite) in new[]{("classic_tree","Berry Oak","classic_wood","woodcutting","oak_tree"),("classic_stone_node","Loose Stone","classic_stone","mining","copper_vein"),("classic_tinder_node","Dry Tinder","classic_tinder","herbalism","meadow_leaf_patch"),("classic_flint_node","Flint Outcrop","classic_flint","mining","copper_vein")})
            data.Resources.Add(new(){Id=id,Name=name,Item=item,Skill=skill,Sprite=sprite,Respawn=tuning.ResourceRecoverySeconds,Xp=10});
        var zone=new ZoneDef{Id=ZoneId,Name="First Glade",Biome="plains",Kind="wilderness",Width=40,Height=32,Spawn=new(12.5,12.5),Seed=107,WorldX=-1,WorldY=-1,Lore="An original, optional local tutorial meadow."};
        foreach(var site in Sites)zone.Furnishings.Add(new(){Id=site.Id,Kind="classic_"+site.Kind,X=(int)site.Position.X,Y=(int)site.Position.Y,Solid=true,Rise=24});
        zone.Exits.Add(new(){Id="classic_glade_to_wayfarers",Target="wayfarers_rest",Position=new(36.5,12.5),Arrival=new(6.5,40.5)});
        data.Zone("wayfarers_rest").Exits.Add(new(){Id="wayfarers_to_classic_glade",Target=ZoneId,Position=new(4.5,40.5),Arrival=new(34.5,12.5)});
        data.Zones.Add(zone);
    }
    public static string ArtAlias(string id)=>id switch
    {
        "classic_wood"=>"oak_log","classic_stone"=>"copper_ore","classic_tinder"=>"meadow_leaf","classic_flint"=>"rough_gem",
        "classic_berries"=>"bread","classic_stone_pickaxe"=>"copper_pickaxe","classic_tree"=>"oak_tree",
        "classic_stone_node" or "classic_flint_node"=>"copper_vein","classic_tinder_node"=>"meadow_leaf_patch",_=>id
    };
    public static bool FacingAdjacent(Character p,Point target)
    {
        int dx=(int)Math.Floor(target.X)-(int)Math.Floor(p.Position.X),dy=(int)Math.Floor(target.Y)-(int)Math.Floor(p.Position.Y);
        return p.ClassicTutorial is not null && Math.Abs(dx)+Math.Abs(dy)==1 && p.Position.Distance(target)<=1.05
            && GridMovementRules.Cardinal(p.Facing)==new Point(dx,dy);
    }
    public static Terrain Ground(int x,int y)=>x is >=11 and <=13 && y is >=11 and <=13 ? Terrain.Stone
        : y==12 && x>=26 ? Terrain.Dirt : Terrain.Grass;
}
