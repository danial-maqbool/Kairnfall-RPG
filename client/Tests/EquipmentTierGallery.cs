using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client.Tests;

/// <summary>Actual renderer coverage for every weapon at representative equipment grades.</summary>
public partial class EquipmentTierGallery : Control
{
    public PixelAssets Assets { get; set; }=null!;
    public Catalog Data { get; set; }=null!;
    public int TierLevel { get; set; }=5;
    public int State { get; set; }
    public int FrameNumber { get; set; }
    public override void _Ready()
    {
        Name="EquipmentTierGallery"; TextureFilter=TextureFilterEnum.Nearest; MouseFilter=MouseFilterEnum.Ignore;
        SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
    }
    public override void _Draw()
    {
        if(Assets is null || Data is null) return;
        var tier=Data.EquipmentTiers.Single(t=>t.Level==TierLevel);
        DrawRect(new Rect2(Vector2.Zero,Size),Ui.Ink);
        var font=GetThemeDefaultFont();
        DrawString(font,new Vector2(20,28),tier.Name+" · Skill tier "+TierLevel+" · Actual equipment layers · state "+State+" frame "+FrameNumber,
            HorizontalAlignment.Left,-1,18,Ui.Gold);
        float width=(Size.X-32)/5, height=(Size.Y-64)/3;
        var gear=new Dictionary<string,string>();
        foreach(string slot in EquipmentTierDef.ArmorSlots) gear[slot]=tier.Entries["armor/heavy/"+slot];
        for(int index=0;index<EquipmentTierDef.WeaponFamilies.Length;index++)
        {
            string family=EquipmentTierDef.WeaponFamilies[index];
            var at=new Vector2(16+(index%5)*width,44+(index/5)*height);
            var rect=new Rect2(at+Vector2.One,new Vector2(width-4,height-4));
            DrawRect(rect,Ui.Panel); DrawRect(rect,new Color("78664a"),false,1);
            var item=Data.Item(tier.Entries["weapon/"+family]); gear["weapon"]=item.Id;
            var icon=Assets.Icon(item.Id);
            if(icon is not null) DrawTextureRect(icon,new Rect2(at+new Vector2(8,8),new Vector2(32,32)),false);
            DrawString(font,at+new Vector2(44,25),Ui.Words(family),HorizontalAlignment.Left,width-50,14,Ui.Text);
            for(int direction=0;direction<4;direction++)
            {
                var feet=at+new Vector2(width/2-36+(direction%2)*72,98+(direction/2)*72);
                Assets.DrawPerson(this,new Appearance{Body=0,Skin=2,Hair=0,HairColor=1},gear,feet.Round(),State,direction,FrameNumber);
            }
        }
    }
}
