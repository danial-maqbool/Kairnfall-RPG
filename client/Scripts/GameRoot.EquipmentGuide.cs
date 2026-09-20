using Godot;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private string equipmentRecipeSearch="";
    private void BuildEquipmentGuidePage()
    {
        if(page is null || Snapshot is null) return;
        var guide=new EquipmentGuidePanel
        {
            Data=Data,Assets=Assets,ReadCharacter=()=>Snapshot?.Self,
            OpenRecipe=id=>
            {
                var recipe=Data.Recipes.FirstOrDefault(r=>r.Id==id);
                if(recipe is null) return;
                selectedRecipe=id; equipmentRecipeSearch=recipe.Name; OpenPage("Crafting");
            }
        };
        page.AddChild(guide); refreshPage=guide.RefreshSnapshot;
    }
}
