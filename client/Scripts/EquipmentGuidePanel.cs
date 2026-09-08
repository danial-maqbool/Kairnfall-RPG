using Godot;
using Kairnfall.Core;
using System.Text;

namespace Kairnfall.Client;

/// <summary>One equipment family at a time. This panel never grants items or changes state.</summary>
public partial class EquipmentGuidePanel : VBoxContainer
{
    public Catalog Data { get; set; } = null!;
    public PixelAssets Assets { get; set; } = null!;
    public Func<Character?> ReadCharacter { get; set; } = () => null;
    public Action<string>? OpenRecipe { get; set; }
    public string SelectedItem { get; private set; } = "";
    public string Family { get; private set; } = "weapon/sword";
    public IReadOnlyList<string> VisibleItems => visible.AsReadOnly();
    private readonly List<string> visible=[];
    private readonly Dictionary<string,Button> choices=[];
    private readonly string[] prefixes=["weapon/","armor/light/","armor/medium/","armor/heavy/","offhand/","accessory/","tool/"];
    private readonly List<string> familyIds=[];
    private OptionButton category=null!, family=null!;
    private VBoxContainer rows=null!;
    private Label summary=null!, title=null!, details=null!, ingredients=null!, sources=null!, status=null!;
    private TextureRect icon=null!;
    private Button recipeButton=null!;
    private bool built,connected;
    private StyleBoxFlat selectedStyle=null!, ordinaryStyle=null!;

    public override void _Ready()
    {
        Name="EquipmentGuide"; SizeFlagsHorizontal=SizeFlags.ExpandFill; SizeFlagsVertical=SizeFlags.ExpandFill;
        selectedStyle=Ui.Box(Ui.Raised.Lightened(.12f),Ui.Gold,8);
        ordinaryStyle=Ui.Box(Ui.Ink,new Color("665941"),8);
        AddChild(Ui.Label("EQUIPMENT PROGRESSION",20,Ui.Gold));
        AddChild(Ui.Label("Tier levels require the named skill, not your overall level. Rarity and runes are separate from the material tier.",14,Ui.Muted,true));
        var filters=Ui.Row(this);
        category=new OptionButton{Name="GearCategory",SizeFlagsHorizontal=SizeFlags.ExpandFill};
        foreach(string name in new[]{"Weapons","Light armor","Medium armor","Heavy armor","Offhands","Accessories","Working tools"}) category.AddItem(name);
        filters.AddChild(category);
        family=new OptionButton{Name="GearFamily",SizeFlagsHorizontal=SizeFlags.ExpandFill}; filters.AddChild(family);
        summary=Ui.Label("",14,Ui.Text,true); summary.Name="GearProgressSummary"; AddChild(summary);
        var body=Ui.Row(this); body.SizeFlagsVertical=SizeFlags.ExpandFill;
        var list=Ui.Scroll(body,new Vector2(300,100)); list.Name="GearTierList"; list.SizeFlagsStretchRatio=1;
        rows=Ui.Column(list);
        var panel=new PanelContainer{Name="GearInspector",SizeFlagsHorizontal=SizeFlags.ExpandFill,SizeFlagsVertical=SizeFlags.ExpandFill,SizeFlagsStretchRatio=1.4f}; body.AddChild(panel);
        var inspector=Ui.Column(panel,true); var heading=Ui.Row(inspector);
        icon=Ui.Image(null,64); heading.AddChild(icon); title=Ui.Label("",21,Ui.Gold,true); heading.AddChild(title);
        var info=Ui.Column(Ui.Scroll(inspector,new Vector2(0,80)));
        details=Ui.Label("",15,Ui.Text,true); details.Name="GearDetails"; info.AddChild(details);
        ingredients=Ui.Label("",14,Ui.Muted,true); ingredients.Name="GearIngredients"; info.AddChild(ingredients);
        sources=Ui.Label("",14,Ui.Muted,true); info.AddChild(sources);
        status=Ui.Label("",14,Ui.Gold,true); status.Name="GearRequirement"; inspector.AddChild(status);
        recipeButton=Ui.Button("Inspect crafting recipe",()=>
        {
            var recipe=Data.Recipes.FirstOrDefault(r=>r.Output==SelectedItem);
            if(recipe is not null && ReadCharacter() is not null) OpenRecipe?.Invoke(recipe.Id);
        });
        recipeButton.Name="GearRecipeAction"; inspector.AddChild(recipeButton);
        built=true; Connect();
        var self=ReadCharacter();
        if(self is not null && self.Equipment.TryGetValue("weapon",out var id))
        {
            var item=self.Inventory.FirstOrDefault(i=>i.Id==id);
            if(item is not null)
            {
                var def=Data.Item(item.Template);
                var tag=def.Tags.FirstOrDefault(t=>EquipmentTierDef.WeaponFamilies.Contains(t));
                if(tag is not null) Family="weapon/"+tag;
            }
        }
        RebuildFamilies();
    }
    public override void _EnterTree() { if(built) Connect(); }
    public override void _ExitTree()
    {
        if(!connected) return;
        category.ItemSelected-=CategoryChanged; family.ItemSelected-=FamilyChanged; connected=false;
    }
    private void Connect()
    {
        if(connected) return;
        category.ItemSelected+=CategoryChanged; family.ItemSelected+=FamilyChanged; connected=true;
    }
    private void CategoryChanged(long _) => RebuildFamilies();
    private void FamilyChanged(long index)
    {
        if(index>=0 && index<familyIds.Count) { Family=familyIds[(int)index]; RebuildList(); }
    }
    private void RebuildFamilies()
    {
        family.Clear(); familyIds.Clear();
        foreach(string id in EquipmentTierDef.Families.Where(x=>x.StartsWith(prefixes[category.Selected],StringComparison.Ordinal)))
        {
            familyIds.Add(id); family.AddItem(Ui.Words(id.Split('/')[^1]));
        }
        int index=Math.Max(0,familyIds.IndexOf(Family)); family.Select(index);
        Family=familyIds[index]; RebuildList();
    }
    public void SelectFamily(string id)
    {
        if(!built || !EquipmentTierDef.Families.Contains(id)) return;
        Family=id; int index=Array.FindIndex(prefixes,p=>id.StartsWith(p,StringComparison.Ordinal));
        if(index<0) return; category.Select(index); RebuildFamilies();
    }
    private void RebuildList()
    {
        Ui.Clear(rows); visible.Clear(); choices.Clear();
        foreach(var tier in Data.EquipmentTiers.OrderBy(t=>t.Level))
        {
            if(!tier.Entries.TryGetValue(Family,out var id)) continue;
            var item=Data.Item(id);
            var button=Ui.Button("Level "+tier.Level+" · "+item.Name,()=>SelectItem(id));
            button.Name="GearChoice_"+id; button.Icon=Assets.Icon(id); button.ExpandIcon=true;
            button.Alignment=HorizontalAlignment.Left; button.ClipText=true;
            button.AddThemeConstantOverride("icon_max_width",32); button.CustomMinimumSize=new Vector2(0,48);
            button.TooltipText=item.Name+"\nRequires "+Data.Skill(item.Skill).Name+" "+item.Requirement;
            rows.AddChild(button); choices.Add(id,button); visible.Add(id);
        }
        if(!visible.Contains(SelectedItem))
        {
            var self=ReadCharacter();
            SelectedItem=self is null?visible.FirstOrDefault()??"":visible.FirstOrDefault(id=>Data.Item(id).Requirement>Progression.Level(self,Data.Item(id).Skill))??visible.LastOrDefault()??"";
        }
        RefreshSnapshot();
    }
    public void SelectItem(string id)
    {
        if(!visible.Contains(id)) return; SelectedItem=id; RefreshSnapshot();
    }
    public void RefreshSnapshot()
    {
        if(!built || !IsInsideTree()) return;
        foreach(var entry in choices) entry.Value.AddThemeStyleboxOverride("normal",entry.Key==SelectedItem?selectedStyle:ordinaryStyle);
        var self=ReadCharacter();
        var item=Data.Items.FirstOrDefault(i=>i.Id==SelectedItem);
        recipeButton.Disabled=item is null || self is null || OpenRecipe is null;
        if(item is null) { title.Text="No equipment selected"; return; }
        int trained=self is null?0:Progression.Level(self,item.Skill);
        summary.Text=Ui.Words(Family.Replace('/',' '))+" · "+visible.Count+" tiers · "+Data.Skill(item.Skill).Name+" "+trained;
        title.Text=item.Name; icon.Texture=Assets.Icon(item.Id);
        var text=new StringBuilder();
        if(item.Power>0) text.AppendLine($"Base power {item.Power:0.##}");
        if(item.Armor>0) text.AppendLine($"Base armor {item.Armor:0.##}");
        if(item.Slot=="weapon") text.AppendLine($"Range {item.Range:0.#} tiles · Recovery {item.Speed:0.##} s · {item.Element}");
        foreach(var stat in item.Stats) text.AppendLine($"{Ui.Words(stat.Key)} +{stat.Value:0.##}");
        text.AppendLine().Append(item.Description);
        details.Text=text.ToString().ReplaceLineEndings("\n");
        status.Text="Requires "+Data.Skill(item.Skill).Name+" "+item.Requirement+". Your skill: "+trained+".\n"+
            (trained>=item.Requirement?(item.Type=="tool"?"Usable from your backpack.":"Skill requirement met. Hand compatibility still applies."):"Train this skill before using the item.");
        var recipe=Data.Recipes.FirstOrDefault(r=>r.Output==item.Id);
        ingredients.Text=recipe is null?"No recipe found.":"CRAFT AT "+Ui.Words(recipe.Station)+"\n"+Data.Skill(recipe.Skill).Name+" "+recipe.Requirement+"\n"+
            string.Join("\n",recipe.Ingredients.Select(x=>Data.Item(x.Key).Name+"  "+(self is null?0:Items.Count(self,x.Key))+" / "+x.Value));
        var vendors=Data.Npcs.Where(n=>n.Stock.Contains(item.Id)).OrderBy(n=>n.Zone,StringComparer.Ordinal).ToArray();
        sources.Text=vendors.Length==0?"Craft this item or obtain it through player trade. No guaranteed creature drop is advertised.":
            "MERCHANTS\n"+string.Join("\n",vendors.Take(3).Select(n=>n.Name+" · "+Data.Zone(n.Zone).Name))+(vendors.Length>3?"\nAlso stocked by "+(vendors.Length-3)+" other merchants.":"");
    }
}
