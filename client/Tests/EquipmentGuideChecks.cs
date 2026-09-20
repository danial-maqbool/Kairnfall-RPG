using Godot;
using Kairnfall.Core;
using System.Reflection;

namespace Kairnfall.Client.Tests;

internal static class EquipmentGuideChecks
{
    public static async Task Run(Node host,GameRoot game,Catalog data,Character self,Action<bool,string> check)
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
            check(Fits(node),"Equipment guide action is reachable: "+node.Name);
            var at=node.GetGlobalRect().GetCenter();
            using(var press=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left,ButtonMask=MouseButtonMask.Left,Pressed=true}) host.GetViewport().PushInput(press,true);
            await Frame();
            using(var release=new InputEventMouseButton{Position=at,GlobalPosition=at,ButtonIndex=MouseButton.Left}) host.GetViewport().PushInput(release,true);
            await Frame(); await Frame();
        }
        foreach(var size in new[]{new Vector2I(1280,720),new Vector2I(1920,1080)})
        {
            host.GetWindow().Size=size; host.GetWindow().ContentScaleSize=size;
            Call("OpenPage","Equipment Guide"); await Frame(); await Frame(); await Frame();
            var guide=Find<EquipmentGuidePanel>(game,"EquipmentGuide","VBoxContainer");
            var recipe=Find<Button>(guide,"GearRecipeAction","Button");
            check(Fits(recipe),"The pinned recipe action fits "+size);
            foreach(string family in EquipmentTierDef.Families)
            {
                guide.SelectFamily(family); await Frame(); await Frame();
                check(guide.VisibleItems.Count==data.EquipmentTiers.Count,"The guide shows all levels for "+family);
                check(guide.VisibleItems.All(id=>data.Items.Any(i=>i.Id==id)),"Every displayed grade resolves to an actual item: "+family);
            }
            guide.SelectFamily("weapon/sword"); await Frame(); await Frame();
            string selected=data.EquipmentTiers.Single(t=>t.Level==5).Entries["weapon/sword"];
            var button=Find<Button>(guide,"GearChoice_"+selected,"Button"); ulong identity=button.GetInstanceId();
            await Click(button);
            check(guide.SelectedItem==selected,"Native mouse selection opens the Bronze sword inspection");
            check(GodotObject.IsInstanceValid(button) && button.GetInstanceId()==identity,"Selecting a tier retains its native button");
            guide.RefreshSnapshot(); await Frame();
            check(Find<Button>(guide,"GearChoice_"+selected,"Button").GetInstanceId()==identity,"Snapshot refresh retains tier rows");
            check(Find<Label>(guide,"GearRequirement","Label").Text.Contains("Swordsmanship 3"),"The exact named skill requirement is visible");
            check(Find<Label>(guide,"GearIngredients","Label").Text.Contains("Bronze Ingot"),"The real recipe ingredients are visible");
            await Click(recipe);
            var recipeId=(string)typeof(GameRoot).GetField("selectedRecipe",BindingFlags.Instance|BindingFlags.NonPublic)!.GetValue(game)!;
            check(data.Recipe(recipeId).Output==selected,"The guide opens the actual selected crafting recipe");
            check(!GodotObject.IsInstanceValid(guide),"The guide releases after navigation to crafting");
            Call("ClosePage"); await Frame(); await Frame();
        }
    }
}
