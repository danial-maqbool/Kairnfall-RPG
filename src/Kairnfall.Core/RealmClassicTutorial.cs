namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private void SeedClassicTutorial()
    {
        if(!State.ClassicTutorialEnabled)return;
        var entries=new[]{("tree", "classic_tree",new Point(15.5,15.5)),("tree_b","classic_tree",new Point(17.5,17.5)),("stone","classic_stone_node",new Point(17.5,14.5)),("stone_b","classic_stone_node",new Point(20.5,16.5)),("tinder","classic_tinder_node",new Point(19.5,18.5)),("flint","classic_flint_node",new Point(22.5,17.5))};
        foreach(var (id,template,at) in entries)
        {
            string key=ClassicTutorialContent.ZoneId+"/"+id;
            if(!State.Nodes.ContainsKey(key))State.Nodes[key]=new(){Id=key,Template=template,Position=at,Zone=ClassicTutorialContent.ZoneId};
        }
        string rat=ClassicTutorialContent.ZoneId+"/rat";
        if(!State.Creatures.ContainsKey(rat))State.Creatures[rat]=new(){Id=rat,Template="field_rat",Zone=ClassicTutorialContent.ZoneId,Position=new(25.5,18.5),Home=new(25.5,18.5),Health=Data.Mob("field_rat").Health};
    }
    private void InitializeClassicTutorial(Character p)
    {
        if(!State.ClassicTutorialEnabled)return;
        p.Zone=ClassicTutorialContent.ZoneId;p.Position=Data.Zone(p.Zone).Spawn;
        p.ClassicTutorial=new(){Food=Data.ClassicTutorial!.StartingFood};
        Items.Add(p.Inventory,Items.Create(Data,"classic_berries",4),Data);
    }
    private void CompleteClassicMilestone(Character p,string id,string title)
    {
        if(p.ClassicTutorial is not { } progress || !progress.Completed.Add(id))return;
        int before=Progression.BaseLevel(p,ClassicTutorialContent.Questing);
        Progression.Train(p,ClassicTutorialContent.Questing,Data.ClassicTutorial!.MilestoneXp,1,Data);
        progress.NoticeId++;progress.Notice=(Progression.BaseLevel(p,ClassicTutorialContent.Questing)>before?"Questing up! ":"Quest completed: ")+title;
        EconomicDirty=true;
    }
    private void TickClassicTutorial(Character p,double dt)
    {
        if(p.ClassicTutorial is not { } progress)return;
        progress.Food=Math.Max(0,progress.Food-Data.ClassicTutorial!.FoodDrainPerSecond*dt);
        if(p.Zone==ClassicTutorialContent.ZoneId && p.Position.Distance(ClassicTutorialContent.Sites[0].Position)<=Data.ClassicTutorial.SignApproachRadius)
            CompleteClassicMilestone(p,"first_steps","First Steps");
    }
    private string InteractClassicTutorial(Character p,string id)
    {
        Need(p.Zone==ClassicTutorialContent.ZoneId && p.ClassicTutorial is not null,"This interaction belongs to an optional classic tutorial world.");
        var site=ClassicTutorialContent.Sites.FirstOrDefault(x=>x.Id==id)??throw new RuleException("Tutorial object not found.");
        Need(ClassicTutorialContent.FacingAdjacent(p,site.Position),"Face the adjacent object and use Space.");
        Need(WorldMap.LineOfSight(Data.Zone(p.Zone),p.Position,p.Position.Add(p.Position.Direction(site.Position).Scale(.45))),"The object is behind an obstacle.");
        CompleteClassicMilestone(p,site.Kind=="fountain"?"fountain":"read_sign",site.Name);
        return site.Name+": "+site.Text;
    }
    private void ObserveClassicTutorial(Character p,string action,string target)
    {
        if(p.ClassicTutorial is null)return;
        string id=(action,target) switch
        {
            ("gather","classic_wood")=>"wood",("gather","classic_stone")=>"stone",
            // Progress is observed only after the successful real consumption;
            // potions keep their normal effects without teaching the food lesson.
            ("consume",_) when Data.Item(target) is {Type:"food",Effect:"food"}=>"food",
            ("craft","classic_stone_pickaxe")=>"pickaxe",("build","structure_campfire")=>"fire",("kill","field_rat")=>"rat",_=>""
        };
        if(id!="")CompleteClassicMilestone(p,id,id switch {"wood"=>"Gather Wood","stone"=>"Gather Stone","food"=>"Eat Food","pickaxe"=>"Craft a Pickaxe","fire"=>"Build a Fire",_=>"Defeat a Rat"});
    }
}
