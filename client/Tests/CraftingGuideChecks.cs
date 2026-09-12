using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

/// <summary>Native recipe browsing and action-request fixtures; the world probe tests crafting authority.</summary>
internal static class CraftingGuideChecks
{
    public static async Task Run(Node host,GameRoot game,Catalog data,Action<bool,string> check)
    {
        object? Call(string method,params object?[] args)=>typeof(GameRoot).GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic)!.Invoke(game,args);
        T Find<T>(Node root,string name,string type) where T:Node=>root.FindChildren(name,type,true,false).OfType<T>().Single();
        async Task Frame()=>await host.ToSignal(host.GetTree(),SceneTree.SignalName.ProcessFrame);
        bool Fits(Control node)
        {
            var a=node.GetGlobalRect(); var b=host.GetViewport().GetVisibleRect();
            return node.IsVisibleInTree() && a.Size.X>0 && a.Size.Y>0 && a.Position.X>=-1 && a.Position.Y>=-1 && a.End.X<=b.End.X+1 && a.End.Y<=b.End.Y+1;
        }
        async Task Click(Control node)
        {
            check(Fits(node),"Crafting action is reachable: "+node.Name); var at=node.GetGlobalRect().GetCenter();
            using(var press=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left,ButtonMask=MouseButtonMask.Left,Pressed=true}) host.GetViewport().PushInput(press,true);
            await Frame();
            using(var release=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left}) host.GetViewport().PushInput(release,true);
            await Frame(); await Frame();
        }
        async Task Type(LineEdit edit,string text)
        {
            edit.GrabFocus(); edit.SelectAll();
            using(var press=new InputEventKey{Keycode=Key.Backspace,PhysicalKeycode=Key.Backspace,Pressed=true}) host.GetViewport().PushInput(press,true);
            using(var release=new InputEventKey{Keycode=Key.Backspace,PhysicalKeycode=Key.Backspace}) host.GetViewport().PushInput(release,true);
            foreach(char c in text)
            {
                var key=c==' '?Key.Space:(Key)char.ToUpperInvariant(c);
                using(var press=new InputEventKey{Keycode=key,PhysicalKeycode=key,Unicode=c,Pressed=true}) host.GetViewport().PushInput(press,true);
                using(var release=new InputEventKey{Keycode=key,PhysicalKeycode=key}) host.GetViewport().PushInput(release,true);
                await Frame();
            }
            await Frame(); await Frame(); check(edit.Text==text,"Native text reaches the recipe search");
        }
        foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
        {
            host.GetWindow().Size=size; host.GetWindow().ContentScaleSize=size;
            Call("OpenPage","Crafting"); await Frame(); await Frame(); await Frame();
            var panel=Find<CraftingGuidePanel>(game,"CraftingGuide","VBoxContainer");
            var search=Find<LineEdit>(panel,"CraftSearch","LineEdit"); var next=Find<Button>(panel,"CraftNext","Button");
            var primary=Find<Button>(panel,"CraftPrimaryAction","Button"); var amount=Find<SpinBox>(panel,"CraftBatches","SpinBox");
            check(Fits(primary) && Fits(amount),"Craft and batch controls stay outside the scroll area at "+size);
            check(panel.VisibleRecipes.Count<=CraftingGuidePanel.PageLength && panel.MatchingCount>CraftingGuidePanel.PageLength,"Recipe rendering is bounded independently of catalog size");
            string first=panel.VisibleRecipes[0]; await Click(next);
            check(panel.VisibleRecipes[0]!=first && panel.VisibleRecipes.Count<=CraftingGuidePanel.PageLength,"Native page navigation changes only the bounded recipe slice");
            var recipe=data.Recipes.Single(r=>r.Output=="bronze_sword");
            await Type(search,recipe.Name);
            check(panel.VisibleRecipes.Contains(recipe.Id),"Search finds the requested Bronze weapon recipe");
            var choice=Find<Button>(panel,"CraftChoice_"+recipe.Id,"Button"); ulong identity=choice.GetInstanceId();
            await Click(choice);
            check(panel.SelectedRecipe==recipe.Id && GodotObject.IsInstanceValid(choice),"Native selection keeps the pressed recipe control alive");
            var original=panel.ReadCharacter()!; var actor=Wire.Copy(original); actor.Inventory.Clear(); actor.Equipment.Clear(); actor.Cooldowns.Clear();
            actor.Health=100; actor.SkillXp[recipe.Skill]=Progression.Threshold(recipe.Requirement);
            panel.ReadCharacter=()=>actor; panel.CanSubmit=()=>true; panel.AtStation=_=>true;
            var requests=new List<(string Id,int Batches,string Specialization)>(); panel.CraftRequested=(id,batches,specialization)=>requests.Add((id,batches,specialization));
            panel.RefreshSnapshot(); await Frame();
            var finish=Find<OptionButton>(panel,"CraftSpecialization","OptionButton");
            check(finish.ItemCount>=4 && finish.Selected==0,"Craft specialization exposes standard plus authored finish choices");
            check(finish.GetItemText(1).Contains("skill",StringComparison.OrdinalIgnoreCase),"Advanced craft finish visibly reports its mastery gate");
            check(primary.Disabled && !panel.TrySubmit(),"Missing ingredients block a native crafting request");
            foreach(var ingredient in recipe.Ingredients) Items.Add(actor.Inventory,Items.Create(data,ingredient.Key,ingredient.Value*2),data);
            panel.RefreshSnapshot(); await Frame();
            check(Find<Button>(panel,"CraftChoice_"+recipe.Id,"Button").GetInstanceId()==identity,"Inventory changes preserve recipe controls and scroll position");
            amount.Value=2; await Frame(); await Click(primary);
            check(requests.Count==1 && requests[0]==(recipe.Id,2,""),"Native Craft requests the selected recipe, batch count, and standard finish exactly once");
            actor.SkillXp[recipe.Skill]=Progression.Threshold(Math.Min(100,recipe.Requirement+10));
            panel.RefreshSnapshot(); await Frame();
            finish=Find<OptionButton>(panel,"CraftSpecialization","OptionButton");
            check(!finish.GetItemText(1).Contains("skill",StringComparison.OrdinalIgnoreCase),"Qualified craft mastery unlocks the first targeted finish");
            finish.Select(1); await Frame();
            check(panel.TrySubmit(),"Qualified targeted finish can submit through the native crafting panel");
            check(requests.Count==2 && requests[1]==(recipe.Id,2,"offense"),"Native Craft forwards the selected targeted finish without client-side crafting authority");
            check(actor.Inventory.Sum(i=>i.Quantity)==recipe.Ingredients.Sum(i=>i.Value*2),"The client does not consume materials or grant crafting output");
            panel.AtStation=_=>false; panel.RefreshSnapshot();
            check(primary.Disabled && !panel.TrySubmit(),"Moving away from the station blocks stale crafting actions");
            panel.AtStation=_=>true; actor.Health=0; panel.RefreshSnapshot();
            check(primary.Disabled && !panel.TrySubmit(),"Dead characters cannot submit crafting requests");
            actor.Health=100; panel.CanSubmit=()=>false; panel.RefreshSnapshot();
            check(primary.Disabled && !panel.TrySubmit(),"A disconnected or busy client cannot submit crafting requests");
            panel.CanSubmit=()=>true; actor.Cooldowns["craft"]=panel.ReadTime()+20; panel.RefreshSnapshot();
            check(primary.Disabled && !panel.TrySubmit(),"Crafting cooldown is shown without rebuilding the recipe list");
            actor.Cooldowns.Clear(); await Type(search,"NoRecipeMatchesThis");
            check(panel.VisibleRecipes.Count==0 && panel.SelectedRecipe=="" && primary.Disabled,"An empty search clears stale recipe actions");
            await Type(search,recipe.Name);
            var parent=panel.GetParent(); parent.RemoveChild(panel); await Frame(); parent.AddChild(panel); await Frame();
            await Type(search,"NoRecipeMatchesThis");
            check(panel.VisibleRecipes.Count==0,"Search signals reconnect after native scene reattachment");
            Call("ClosePage"); await Frame(); await Frame();
            check(!GodotObject.IsInstanceValid(panel),"The recipe panel releases after repeated native input and reattachment");
        }
    }
}
