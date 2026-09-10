using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Graphical breadth check against a disposable real server. This is automated acceptance, not a human Windows playthrough.</summary>
public partial class LiveProgressionBreadthContract : Node
{
    private GameRoot game = null!;
    private int checks;
    private static double Now => Time.GetTicksMsec() / 1000.0;
    private Character Self => game.Snapshot?.Self ?? throw new InvalidOperationException("No authoritative snapshot.");
    private static T Field<T>(GameRoot value,string name)
        => (T)typeof(GameRoot).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(value)!;
    private object? Call(string method,params object?[] args)
        => typeof(GameRoot).GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
    private void Attach(GameConnection? connection)
        => typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game,connection);
    private void Require(bool value,string message)
    {
        if(!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS LIVE PROGRESSION: "+message);
    }
    private async Task Frame()=>await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);
    private async Task Delay(double seconds)=>await ToSignal(GetTree().CreateTimer(seconds),SceneTreeTimer.SignalName.Timeout);
    private async Task Until(Func<bool> condition,string failure,double timeout=12)
    {
        double deadline=Now+timeout;
        while(!condition())
        {
            if(Now>=deadline) throw new TimeoutException(failure);
            await Frame();
        }
    }
    private async Task WalkNear(Point target,double distance=1.9)
    {
        double deadline=Now+25;
        while(Self.Position.Distance(target)>distance)
        {
            if(Now>=deadline) throw new TimeoutException("Normal movement did not reach the progression target.");
            var path=WorldMap.FindPath(game.Data.Zone(Self.Zone),Self.Position,target,16000);
            if(path.Count==0) throw new InvalidOperationException("The progression target has no walkable route.");
            var next=path.FirstOrDefault(x=>Self.Position.Distance(x)>.35);
            var direction=Self.Position.Direction(next);
            await game.Connection!.MoveAsync(direction.X,direction.Y);
            await Delay(.08);
        }
        await game.Connection!.MoveAsync(0,0); await Delay(.25);
    }
    private WorldNode ReadyNode(string skill)
    {
        var snapshot=game.Snapshot ?? throw new InvalidOperationException("No snapshot for node selection.");
        return snapshot.Nodes
            .Where(x=>x.ReadyAt<=snapshot.Time && game.Data.Resources.Any(r=>r.Id==x.Template&&r.Skill==skill))
            .OrderBy(x=>Self.Position.Distance(x.Position))
            .FirstOrDefault() ?? throw new InvalidOperationException("No ready "+skill+" node is visible in the starter area.");
    }
    private async Task<long> Gather(string skill)
    {
        var node=ReadyNode(skill); var resource=game.Data.Resource(node.Template);
        long before=Self.SkillXp.GetValueOrDefault(skill),totalBefore=Progression.Total(Self);
        double characterBefore=Field<ProgressBar>(game,"characterExperienceBar").Value;
        await WalkNear(node.Position);
        Call("Activate",new WorldTarget("node",node.Id,resource.Name,node.Position));
        await Until(()=>Self.SkillXp.GetValueOrDefault(skill)>before,"The server did not award "+skill+" XP.");
        await Delay(.35);
        long gain=Self.SkillXp.GetValueOrDefault(skill)-before;
        Require(gain>=resource.Xp && gain<=Math.Ceiling(resource.Xp*1.10),resource.Name+" gives a bounded starter XP award");
        Require(Progression.Total(Self)>totalBefore,resource.Name+" increases accumulated character XP");
        var characterBar=Field<ProgressBar>(game,"characterExperienceBar");
        var skillBar=Field<ProgressBar>(game,"skillExperienceBar");
        var skillText=Field<Label>(game,"skillExperienceText");
        await Until(()=>skillText.Text.Contains(game.Data.Skill(skill).Name,StringComparison.OrdinalIgnoreCase),"The Skill XP HUD did not follow "+skill+".");
        Require(characterBar.IsVisibleInTree()&&skillBar.IsVisibleInTree(),"Character XP and Skill XP bars remain visible after "+skill);
        Require(Math.Abs(characterBar.Value-Progression.PlayerLevelProgress(Self)*100)<.02,"Character XP bar matches authoritative progress after "+skill);
        Require(Math.Abs(skillBar.Value-Progression.SkillLevelProgress(Self.SkillXp[skill])*100)<.02,"Skill XP bar matches authoritative "+skill+" progress");
        Require(characterBar.Value!=characterBefore||Progression.PlayerLevel(Self)>1,"Character XP HUD visibly changes after "+skill);
        await Delay(2.0);
        return Self.SkillXp[skill];
    }
    private static int Count(Character character,string template)
        => character.Inventory.Where(x=>x.Template==template).Sum(x=>x.Quantity);

    public override async void _Ready()
    {
        GameConnection? connection=null;
        try
        {
            if(DisplayServer.GetName()=="headless") throw new InvalidOperationException("This contract requires graphical rendering.");
            if(System.Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT")!="Testing")
                throw new InvalidOperationException("Use the disposable Testing realm.");
            string address=System.Environment.GetEnvironmentVariable("KAIRNFALL_SMOKE_URL")??"http://127.0.0.1:5079";
            if(!Uri.TryCreate(address,UriKind.Absolute,out var uri)||!uri.IsLoopback)
                throw new InvalidOperationException("Live progression QA must use a loopback realm.");
            string suffix=Guid.NewGuid().ToString("N")[..8];
            string username="progress_"+suffix,password="QA_"+Guid.NewGuid().ToString("N");
            connection=new GameConnection(address);
            await connection.SignInAsync(username,password,true);
            var created=await connection.CreateCharacterAsync(new CharacterRequest{Name="Progress "+suffix,Class="vanguard",Appearance=new()});
            await connection.ConnectAsync(created.Id);
            using(var scene=GD.Load<PackedScene>("res://Main.tscn")) game=scene.Instantiate<GameRoot>();
            AddChild(game); Attach(connection); Field<Control>(game,"frontend").Hide(); GetViewport().GuiReleaseFocus();
            await Until(()=>game.Snapshot is not null,"The graphical client did not receive its first snapshot."); await Delay(.4);

            var characterBar=Field<ProgressBar>(game,"characterExperienceBar");
            var skillBar=Field<ProgressBar>(game,"skillExperienceBar");
            Require(characterBar.IsVisibleInTree()&&characterBar.CustomMinimumSize.Y>=8,"Character XP bar is permanently visible in Vitals");
            Require(skillBar.IsVisibleInTree()&&skillBar.CustomMinimumSize.Y>=8,"Skill XP bar is permanently visible in Vitals");
            int levelBefore=Progression.PlayerLevel(Self); long totalBefore=Progression.Total(Self);

            long mining=await Gather("mining");
            long fishing=await Gather("fishing");
            long woodcutting=await Gather("woodcutting");
            if(Count(Self,"oak_log")<2) woodcutting=await Gather("woodcutting");
            Require(Count(Self,"oak_log")>=2,"Normal woodcutting supplies the oak logs required for starter woodworking");

            var saw=game.Data.Npcs.First(x=>x.Zone==Self.Zone&&x.Station=="sawbench");
            await WalkNear(saw.Position,2.6);
            var recipe=game.Data.Recipes.First(x=>x.Skill=="woodworking"&&x.Station=="sawbench"&&x.Output=="oak_plank");
            Require(recipe.Ingredients.All(x=>Count(Self,x.Key)>=x.Value),"Gathered inventory satisfies the real oak-board recipe");
            long woodworkingBefore=Self.SkillXp.GetValueOrDefault("woodworking"),craftTotalBefore=Progression.Total(Self);
            Call("Send","craft","",recipe.Id,1,"");
            await Until(()=>Self.SkillXp.GetValueOrDefault("woodworking")>woodworkingBefore,"The live sawbench craft did not award Woodworking XP.");
            await Delay(.35);
            long woodworking=Self.SkillXp["woodworking"];
            long craftGain=woodworking-woodworkingBefore;
            Require(craftGain>=recipe.Xp&&craftGain<=Math.Ceiling(recipe.Xp*1.10),"Starter woodworking gives a bounded XP award");
            Require(Progression.Total(Self)>craftTotalBefore,"Crafting contributes directly to character XP");
            await Until(()=>Field<Label>(game,"skillExperienceText").Text.Contains(game.Data.Skill("woodworking").Name,StringComparison.OrdinalIgnoreCase),"Skill XP HUD did not follow Woodworking.");
            Require(Math.Abs(characterBar.Value-Progression.PlayerLevelProgress(Self)*100)<.02,"Character XP bar matches authoritative progress after crafting");
            Require(Math.Abs(skillBar.Value-Progression.SkillLevelProgress(woodworking)*100)<.02,"Skill XP bar matches authoritative Woodworking progress");
            Require(Progression.Total(Self)>totalBefore&&Progression.PlayerLevelValue(Self)>levelBefore,"Normal starter activities advance character-level value");
            Call("SaveScreenshot","11-live-progression.png");

            string characterId=Self.Id; long total=Progression.Total(Self);
            await connection.DisposeAsync(); Attach(null); game.World.ClearSession(); connection=null;
            var reconnected=new GameConnection(address);
            await reconnected.SignInAsync(username,password,false); await reconnected.ConnectAsync(characterId); Attach(reconnected); connection=reconnected;
            await Until(()=>game.Snapshot?.Self.Id==characterId,"Reconnect did not restore the progression character."); await Delay(.3);
            Require(Self.SkillXp["mining"]==mining&&Self.SkillXp["fishing"]==fishing&&Self.SkillXp["woodcutting"]==woodcutting&&Self.SkillXp["woodworking"]==woodworking,
                "Mining, fishing, woodcutting and woodworking XP survive reconnect");
            Require(Progression.Total(Self)==total,"Accumulated character XP survives reconnect");
            Require(characterBar.IsVisibleInTree()&&skillBar.IsVisibleInTree(),"Both XP bars remain visible after reconnect");
            GD.Print($"LIVE_PROGRESSION_BREADTH_CONTRACT: {checks} checks passed. Automated graphical Godot client, real server and PostgreSQL; not human Windows hardware playtesting.");
            await (Task)Call("ShutdownClientAsync",0)!;
        }
        catch(Exception error)
        {
            GD.PushError("LIVE_PROGRESSION_BREADTH_CONTRACT: "+error);
            if(game is not null&&GodotObject.IsInstanceValid(game)) await (Task)Call("ShutdownClientAsync",1)!;
            else GetTree().Quit(1);
        }
        finally
        {
            if(connection is not null) await connection.DisposeAsync();
        }
    }
}
