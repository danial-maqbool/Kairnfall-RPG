using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>Task-1 XP/HUD acceptance. Native fixture; live server XP is covered by LiveExperienceContract.</summary>
public partial class XpHudAcceptanceContract : Node
{
    private int checks;
    private void Require(bool value,string message)
    {
        if(!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS XP HUD: "+message);
    }
    private static T Field<T>(GameRoot game,string name)
        => (T)typeof(GameRoot).GetField(name,BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(game)!;
    private static object? Call(GameRoot game,string method,params object?[] args)
        => typeof(GameRoot).GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
    private async Task Frame()=>await ToSignal(GetTree(),SceneTree.SignalName.ProcessFrame);

    public override async void _Ready()
    {
        GameRoot? game=null;
        try
        {
            GetWindow().Size=new Vector2I(1280,720);
            var data=PixelAssets.LoadCatalog();
            var realm=new RealmEngine(data);
            var player=realm.CreateCharacter("xp-hud-acceptance","XP HUD Tester","vanguard",new());
            realm.Active.Add(player.Id);
            var before=realm.Snapshot(player.Id);
            int levelBefore=Progression.PlayerLevel(before.Self);

            using(var scene=GD.Load<PackedScene>("res://Main.tscn")) game=scene.Instantiate<GameRoot>();
            AddChild(game); game.SetProcess(false); await Frame(); await Frame();
            Field<Control>(game,"frontend").Hide();
            game.World.Accept(new TransportPacket{Snapshot=before,Loot=[]});
            Call(game,"UpdateHud"); await Frame();

            var characterBar=Field<ProgressBar>(game,"characterExperienceBar");
            var skillBar=Field<ProgressBar>(game,"skillExperienceBar");
            var skillText=Field<Label>(game,"skillExperienceText");
            Require(characterBar.IsVisibleInTree()&&characterBar.CustomMinimumSize.Y>=8,"Character XP bar is permanently visible in Vitals");
            Require(skillBar.IsVisibleInTree()&&skillBar.CustomMinimumSize.Y>=8,"Skill XP bar is permanently visible in Vitals");
            Require(skillText.IsVisibleInTree(),"Skill XP label is permanently visible in Vitals");

            long miningBefore=player.SkillXp.GetValueOrDefault("mining");
            Progression.Train(player,"mining",1000,1,data);
            var after=realm.Snapshot(player.Id);
            Require(after.Self.SkillXp["mining"]>miningBefore,"A successful skill award increases authoritative skill XP");
            Require(Progression.PlayerLevel(after.Self)>levelBefore,"The same awarded skill XP increases character level");

            game.World.Accept(new TransportPacket{Snapshot=after,Loot=[]});
            Call(game,"ObservePlayerChanges",before,after);
            Call(game,"UpdateHud"); await Frame();
            double expectedCharacter=Progression.PlayerLevelProgress(after.Self)*100;
            double expectedSkill=Progression.SkillLevelProgress(after.Self.SkillXp["mining"])*100;
            Require(Math.Abs(characterBar.Value-expectedCharacter)<.01,"Character XP bar shows the authoritative next-level fraction");
            Require(Math.Abs(skillBar.Value-expectedSkill)<.01,"Skill XP bar shows the trained skill fraction");
            Require(skillText.Text.Contains(data.Skill("mining").Name,StringComparison.OrdinalIgnoreCase),"Skill XP label follows the last skill that gained XP");
            Require(Field<Label>(game,"characterTitle").Text.Contains("Level "+Progression.PlayerLevel(after.Self)),"Visible character title reports the increased level");

            GD.Print($"XP_HUD_ACCEPTANCE_CONTRACT: {checks} checks passed. Native HUD fixture plus retained live-server contract; not human Windows playtesting.");
            await NativeTestLifetime.ReleaseSceneAsync(this,game);
            GetTree().Quit(0);
        }
        catch(Exception error)
        {
            GD.PushError("XP_HUD_ACCEPTANCE_CONTRACT: "+error);
            if(game is not null&&GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this,game);
            GetTree().Quit(1);
        }
    }
}
