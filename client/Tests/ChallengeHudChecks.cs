using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

internal static class ChallengeHudChecks
{
    public static async Task Run(Node host,GameRoot game,Action<bool,string> check)
    {
        var old=game.Snapshot;
        var flags=BindingFlags.Instance|BindingFlags.NonPublic;
        var targetField=typeof(GameRoot).GetField("selectedTarget",flags)!;
        var kindField=typeof(GameRoot).GetField("selectedTargetKind",flags)!;
        string oldTarget=(string)targetField.GetValue(game)!,oldKind=(string)kindField.GetValue(game)!;
        async Task Frame()=>await host.ToSignal(host.GetTree(),SceneTree.SignalName.ProcessFrame);
        void Refresh()=>typeof(GameRoot).GetMethod("UpdateHud",flags)!.Invoke(game,null);
        T Find<T>(string name)where T:Node=>game.FindChildren(name,"",true,false).OfType<T>().Single();
        bool Fits(Control c)
        {
            var r=c.GetGlobalRect();var v=host.GetViewport().GetVisibleRect();
            return c.IsVisibleInTree()&&r.Position.X>=0&&r.Position.Y>=0&&r.End.X<=v.End.X+1&&r.End.Y<=v.End.Y+1;
        }
        try
        {
            var realm=new RealmEngine(game.Data);var p=realm.CreateCharacter("challenge-hud","Challenge HUD","vanguard",new());
            foreach(var skill in game.Data.Skills)p.SkillXp[skill.Id]=50000;
            var snap=realm.Snapshot(p.Id);snap.Creatures.Clear();
            var mob=new Creature{Id="challenge-hud-rat",Template="field_rat",Zone=p.Zone,Position=p.Position,Health=20};
            snap.Creatures.Add(mob);game.World.Accept(new TransportPacket{Snapshot=snap});
            targetField.SetValue(game,mob.Id);kindField.SetValue(game,"creature");
            foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
            {
                host.GetWindow().Size=size;host.GetWindow().ContentScaleSize=size;await Frame();Refresh();await Frame();await Frame();
                var pacing=Find<Label>("ExperiencePacing");var target=Find<Label>("TargetChallenge");
                check(Fits(pacing)&&Fits(target),"XP pacing and selected-target feedback fit "+size);
                check(pacing.Text.Contains("Overall XP")&&pacing.TooltipText.Contains("skill"),"HUD distinguishes skill practice from overall advancement");
                check(target.Text.Contains("Trivial hunt")&&target.Text.Contains("practice"),"The target frame identifies under-level farming and its low practice rate");
                var quest=Find<Control>("QuestTracker");
                check(Find<Control>("Vitals").GetGlobalRect().End.Y<=quest.GetGlobalRect().Position.Y+1,"XP feedback does not overlap the objective tracker");
                check(Fits(quest)&&Fits(Find<Control>("Vitals")),"Complete objective and status panels fit the supported viewport");
                string normal=pacing.Text; pacing.Text += "\nExtended experience explanation\nSkill practice is separate.";
                await Frame();await Frame();
                check(Find<Control>("Vitals").GetGlobalRect().End.Y+5<=quest.GetGlobalRect().Position.Y,"Wrapped status information moves the objective panel rather than covering it");
                pacing.Text=normal;await Frame();await Frame();
            }
        }
        finally
        {
            targetField.SetValue(game,oldTarget);kindField.SetValue(game,oldKind);
            if(old is not null)game.World.Accept(new TransportPacket{Snapshot=old});Refresh();await Frame();
        }
    }
}
