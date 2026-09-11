using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Bounded recipe list with stable selection and a pinned, validated action.</summary>
public partial class CraftingGuidePanel : VBoxContainer
{
    public const int PageLength=32;
    public Catalog Data { get; set; } = null!;
    public PixelAssets Assets { get; set; } = null!;
    public Func<Character?> ReadCharacter { get; set; } = () => null;
    public Func<double> ReadTime { get; set; } = () => 0;
    public Func<string,bool> AtStation { get; set; } = _ => false;
    public Func<bool> CanSubmit { get; set; } = () => false;
    public Action<string,int>? CraftRequested { get; set; }
    public Action<string>? PlaceRequested { get; set; }
    public Action? PlantRequested { get; set; }
    public Action<string>? RecipeSelected { get; set; }
    public string InitialRecipe { get; set; } = "";
    public string InitialSearch { get; set; } = "";
    public string SelectedRecipe { get; private set; } = "";
    public IReadOnlyList<string> VisibleRecipes => visible.AsReadOnly();
    public int MatchingCount => matches.Count;
    private readonly List<string> visible=[];
    private readonly List<RecipeDef> matches=[];
    private readonly List<string> professions=[];
    private readonly Dictionary<string,string> searchable=[];
    private readonly Dictionary<string,Button> choices=[];
    private readonly Dictionary<string,Label> ingredientLabels=[];
    private LineEdit search=null!;
    private OptionButton profession=null!, learned=null!;
    private VBoxContainer rows=null!, ingredientRows=null!;
    private Label count=null!, title=null!, description=null!, requirement=null!, readiness=null!;
    private TextureRect icon=null!;
    private SpinBox amount=null!;
    private Button previous=null!, next=null!, primary=null!, plant=null!;
    private StyleBoxFlat selectedStyle=null!, normalStyle=null!;
    private int pageIndex;
    private string signature="", detailRecipe="";
    private bool built,connected;

    public override void _Ready()
    {
        Name="CraftingGuide"; SizeFlagsHorizontal=SizeFlags.ExpandFill; SizeFlagsVertical=SizeFlags.ExpandFill;
        bool compactHeight=GetViewport().GetVisibleRect().Size.Y<520;
        selectedStyle=Ui.Box(Ui.Raised.Lightened(.12f),Ui.Gold,8); normalStyle=Ui.Box(Ui.Ink,new Color("665941"),8);
        foreach(var recipe in Data.Recipes)
            searchable[recipe.Id]=recipe.Name+" "+Data.Skill(recipe.Skill).Name+" "+Ui.Words(recipe.Station)+" "+string.Join(" ",recipe.Ingredients.Keys.Select(k=>Data.Item(k).Name));
        var filters=Ui.Row(this);
        search=Ui.Edit("Search recipes, ingredients, or stations"); search.Name="CraftSearch"; search.Text=InitialSearch; filters.AddChild(search);
        profession=new OptionButton{Name="CraftProfession"}; profession.AddItem("All professions"); professions.Add("");
        foreach(string id in Data.Recipes.Select(r=>r.Skill).Distinct().OrderBy(id=>Data.Skill(id).Name,StringComparer.Ordinal))
        { professions.Add(id); profession.AddItem(Data.Skill(id).Name); }
        filters.AddChild(profession);
        learned=new OptionButton{Name="CraftAvailability"}; learned.AddItem("All recipes"); learned.AddItem("Skill learned"); filters.AddChild(learned);
        plant=Ui.Button("Plant wheat",()=>PlantRequested?.Invoke()); plant.Name="PlantWheat"; filters.AddChild(plant);
        count=Ui.Label("",compactHeight?13:14,Ui.Muted,true); AddChild(count);
        var body=Ui.Row(this); body.SizeFlagsVertical=SizeFlags.ExpandFill;
        var listColumn=Ui.Column(body,true); listColumn.SizeFlagsStretchRatio=1;
        var list=Ui.Scroll(listColumn,new Vector2(310,compactHeight?64:100)); list.Name="CraftRecipeList"; rows=Ui.Column(list);
        var navigation=Ui.Row(listColumn);
        previous=Ui.Button("Previous",()=>ChangePage(-1)); previous.Name="CraftPrevious"; navigation.AddChild(previous);
        next=Ui.Button("Next",()=>ChangePage(1)); next.Name="CraftNext"; navigation.AddChild(next);
        var detail=new PanelContainer{Name="CraftInspector",SizeFlagsHorizontal=SizeFlags.ExpandFill,SizeFlagsVertical=SizeFlags.ExpandFill,SizeFlagsStretchRatio=1.35f}; body.AddChild(detail);
        var inspector=Ui.Column(detail,true); var heading=Ui.Row(inspector);
        icon=Ui.Image(null,compactHeight?44:56); heading.AddChild(icon); title=Ui.Label("Choose a recipe",compactHeight?19:21,Ui.Gold,true); heading.AddChild(title);
        var information=Ui.Column(Ui.Scroll(inspector,new Vector2(0,compactHeight?36:70)));
        description=Ui.Label("",compactHeight?14:15,Ui.Text,true); information.AddChild(description);
        requirement=Ui.Label("",compactHeight?13:14,Ui.Gold,true); requirement.Name="CraftRequirements"; information.AddChild(requirement);
        ingredientRows=Ui.Column(information);
        readiness=Ui.Label("",compactHeight?13:14,Ui.Danger,true); readiness.Name="CraftReadiness"; inspector.AddChild(readiness);
        var actions=Ui.Row(inspector); actions.AddChild(Ui.Label("Batches",compactHeight?13:14,Ui.Muted));
        amount=new SpinBox{Name="CraftBatches",MinValue=1,MaxValue=20,Step=1,Value=1,CustomMinimumSize=new Vector2(105,compactHeight?34:38)}; actions.AddChild(amount);
        primary=Ui.Button("Craft",()=>TrySubmit()); primary.Name="CraftPrimaryAction"; primary.CustomMinimumSize=new Vector2(180,compactHeight?36:42); primary.SizeFlagsHorizontal=SizeFlags.ExpandFill; actions.AddChild(primary);
        built=true; SelectedRecipe=InitialRecipe; Connect(); RefreshSnapshot();
    }
    public override void _EnterTree() { if(built) Connect(); }
    public override void _ExitTree()
    {
        if(!connected) return;
        search.TextChanged-=SearchChanged; profession.ItemSelected-=FilterChanged; learned.ItemSelected-=FilterChanged; amount.ValueChanged-=AmountChanged; connected=false;
    }
    private void Connect()
    {
        if(connected) return;
        search.TextChanged+=SearchChanged; profession.ItemSelected+=FilterChanged; learned.ItemSelected+=FilterChanged; amount.ValueChanged+=AmountChanged; connected=true;
    }
    private void SearchChanged(string _) { signature=""; pageIndex=0; RefreshSnapshot(); }
    private void FilterChanged(long _) { signature=""; pageIndex=0; RefreshSnapshot(); }
    private void AmountChanged(double _) => RefreshDetails();
    private void ChangePage(int delta)
    {
        int target=Math.Clamp(pageIndex+delta,0,Math.Max(0,(matches.Count-1)/PageLength));
        if(target==pageIndex) return; pageIndex=target; RenderPage(); RefreshDetails();
    }
    public void RefreshSnapshot()
    {
        if(!built || !IsInsideTree()) return;
        var self=ReadCharacter();
        if(self is null) { primary.Disabled=true; plant.Disabled=true; return; }
        string current=self.Id+":"+profession.Selected+":"+learned.Selected+":"+search.Text+":"+
            (learned.Selected==1?string.Join(",",professions.Skip(1).Select(s=>Progression.Level(self,s))):"");
        if(current!=signature)
        {
            signature=current; matches.Clear(); string needle=search.Text.Trim();
            matches.AddRange(Data.Recipes.Where(r=>(profession.Selected==0 || r.Skill==professions[profession.Selected])
                && (learned.Selected==0 || Progression.Level(self,r.Skill)>=r.Requirement)
                && searchable[r.Id].Contains(needle,StringComparison.OrdinalIgnoreCase))
                .OrderBy(r=>r.Requirement).ThenBy(r=>r.Name,StringComparer.Ordinal));
            pageIndex=Math.Clamp(pageIndex,0,Math.Max(0,(matches.Count-1)/PageLength));
            if(matches.All(r=>r.Id!=SelectedRecipe)) SelectedRecipe=matches.FirstOrDefault()?.Id??"";
            RenderPage();
        }
        RefreshDetails();
    }
    private void RenderPage()
    {
        Ui.Clear(rows); choices.Clear(); visible.Clear();
        foreach(var recipe in matches.Skip(pageIndex*PageLength).Take(PageLength))
        {
            string id=recipe.Id;
            var button=Ui.Button(recipe.Name+" · "+recipe.Requirement,()=>SelectRecipe(id)); button.Name="CraftChoice_"+id;
            button.Icon=Assets.Icon(recipe.Output); button.ExpandIcon=true; button.AddThemeConstantOverride("icon_max_width",28);
            button.Alignment=HorizontalAlignment.Left; button.ClipText=true; button.CustomMinimumSize=new Vector2(0,46);
            button.TooltipText=recipe.Name+"\n"+Data.Skill(recipe.Skill).Name+" "+recipe.Requirement;
            rows.AddChild(button); choices.Add(id,button); visible.Add(id);
        }
        if(visible.Count==0) rows.AddChild(Ui.Label("No recipes match these filters.",15,Ui.Muted,true));
        previous.Disabled=pageIndex==0; next.Disabled=(pageIndex+1)*PageLength>=matches.Count;
        count.Text=matches.Count+" recipes · Page "+(pageIndex+1)+" / "+Math.Max(1,(matches.Count+PageLength-1)/PageLength)+" · Equipped items are not consumed as ingredients.";
    }
    public void SelectRecipe(string id)
    {
        if(!visible.Contains(id)) return; SelectedRecipe=id; RecipeSelected?.Invoke(id); RefreshDetails();
    }
    private int Batches => Math.Clamp((int)amount.Value,1,20);
    private string Problem(Character? self,RecipeDef? recipe)
    {
        if(self is null || recipe is null) return "Choose a recipe.";
        if(self.Health<=0) return "Respawn before crafting.";
        if(Progression.Level(self,recipe.Skill)<recipe.Requirement) return "Requires "+Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+".";
        bool structure=Data.Item(recipe.Output).Type=="structure";
        int quantity=structure?1:Batches;
        foreach(var ingredient in recipe.Ingredients)
            if(Items.Count(self,ingredient.Key)<checked(ingredient.Value*quantity))
                return "Need "+checked(ingredient.Value*quantity)+" "+Data.Item(ingredient.Key).Name+".";
        if(!structure && !AtStation(recipe.Station)) return "Move closer to the "+Ui.Words(recipe.Station)+".";
        if(!structure && self.Cooldowns.GetValueOrDefault("craft")>ReadTime()) return "Wait for the crafting recovery to finish.";
        if(!CanSubmit()) return "Connect to the realm and wait for the current action.";
        return "";
    }
    private void RefreshDetails()
    {
        if(!built || !IsInsideTree()) return;
        var self=ReadCharacter(); var recipe=Data.Recipes.FirstOrDefault(r=>r.Id==SelectedRecipe);
        foreach(var entry in choices) entry.Value.AddThemeStyleboxOverride("normal",entry.Key==SelectedRecipe?selectedStyle:normalStyle);
        plant.Disabled=self is null || self.Health<=0 || Items.Count(self,"wheat_seed")<1 || !CanSubmit() || PlantRequested is null;
        if(recipe is null)
        {
            title.Text="Choose a recipe"; description.Text="Find a recipe, inspect its ingredients, then use its work station.";
            requirement.Text=""; icon.Texture=null; Ui.Clear(ingredientRows); ingredientLabels.Clear(); detailRecipe="";
            primary.Disabled=true; readiness.Text=""; return;
        }
        var item=Data.Item(recipe.Output); bool structure=item.Type=="structure"; int quantity=structure?1:Batches;
        amount.Editable=!structure;
        if(detailRecipe!=recipe.Id)
        {
            detailRecipe=recipe.Id; icon.Texture=Assets.Icon(recipe.Output); title.Text=recipe.Name; description.Text=item.Description;
            Ui.Clear(ingredientRows); ingredientLabels.Clear();
            foreach(var ingredient in recipe.Ingredients)
            {
                var row=Ui.Row(ingredientRows); row.AddChild(Ui.Image(Assets.Icon(ingredient.Key),28));
                var label=Ui.Label("",14,Ui.Text,true); row.AddChild(label); ingredientLabels[ingredient.Key]=label;
            }
        }
        foreach(var ingredient in recipe.Ingredients)
        {
            int owned=self is null?0:Items.Count(self,ingredient.Key), needed=checked(ingredient.Value*quantity);
            var label=ingredientLabels[ingredient.Key]; label.Text=Data.Item(ingredient.Key).Name+"  "+owned+" / "+needed;
            label.Modulate=owned>=needed?Ui.Success:Ui.Danger;
        }
        requirement.Text=Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+" · "+Ui.Words(recipe.Station)+
            "\nOutput: "+checked(recipe.Quantity*quantity)+" · Base skill XP per batch: "+recipe.Xp+"\nXP depends on challenge and class affinity.";
        string problem=Problem(self,recipe); readiness.Text=problem;
        primary.Text=structure?"Place structure":"Craft "+quantity+(quantity==1?" batch":" batches");
        primary.Disabled=problem!="" || (structure?PlaceRequested is null:CraftRequested is null);
    }
    public bool TrySubmit()
    {
        if(!built || !IsInsideTree() || IsQueuedForDeletion()) return false;
        var recipe=Data.Recipes.FirstOrDefault(r=>r.Id==SelectedRecipe);
        if(Problem(ReadCharacter(),recipe)!="" || recipe is null) { RefreshDetails(); return false; }
        if(Data.Item(recipe.Output).Type=="structure")
        {
            if(PlaceRequested is null) return false; PlaceRequested(recipe.Id);
        }
        else { if(CraftRequested is null) return false; CraftRequested(recipe.Id,Batches); }
        return true;
    }
}
