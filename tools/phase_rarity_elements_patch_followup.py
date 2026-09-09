#!/usr/bin/env python3
from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one replacement, found {count}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


replace('client/Scripts/Ui.cs', '    public Element Element { get; set; } = Element.Physical;\n', '    public Element ItemElement { get; set; } = Element.Physical;\n')
replace('client/Scripts/Ui.cs', '''        if (Element != Element.Physical)
        {
            var badge = new Rect2(Size.X - 18, 3, 15, 15);
            DrawRect(badge, Ui.Ink); DrawRect(badge, Ui.ElementColor(Element), false, 1);
            DrawString(ThemeDB.FallbackFont, new Vector2(badge.Position.X + 4, badge.Position.Y + 12), Ui.ElementGlyph(Element), HorizontalAlignment.Left, -1, 10, Ui.ElementColor(Element));
        }
''', '''        if (ItemElement != Element.Physical)
        {
            var badge = new Rect2(Size.X - 18, 3, 15, 15);
            DrawRect(badge, Ui.Ink); DrawRect(badge, Ui.ElementColor(ItemElement), false, 1);
            DrawString(ThemeDB.FallbackFont, new Vector2(badge.Position.X + 4, badge.Position.Y + 12), Ui.ElementGlyph(ItemElement), HorizontalAlignment.Left, -1, 10, Ui.ElementColor(ItemElement));
        }
''')
replace('client/Scripts/GameRoot.Inventory.cs', 'Item = item, Icon = Assets.Icon(item.Template), Bag = bag, Element = Items.ElementOf(item,Data.Item(item.Template)),', 'Item = item, Icon = Assets.Icon(item.Template), Bag = bag, ItemElement = Items.ElementOf(item,Data.Item(item.Template)),')
replace('client/Scripts/GameRoot.Inventory.cs', '                slot.Element = Items.ElementOf(item,Data.Item(item.Template));\n', '                slot.ItemElement = Items.ElementOf(item,Data.Item(item.Template));\n')
replace('src/Kairnfall.Core/Mechanics.cs', '''    public static Element DominantElement(Character p,Catalog catalog)
    {
        return Enum.GetValues<Element>().Where(x=>x!=Element.Physical)
            .Select(x=>(Element:x,Points:EquippedElementPoints(p,x,catalog)))
            .OrderByDescending(x=>x.Points).ThenBy(x=>(int)x.Element).FirstOrDefault() is var best&&best.Points>0?best.Element:Element.Physical;
    }
''', '''    public static Element DominantElement(Character p,Catalog catalog)
    {
        var best=Enum.GetValues<Element>().Where(x=>x!=Element.Physical)
            .Select(x=>(Element:x,Points:EquippedElementPoints(p,x,catalog)))
            .OrderByDescending(x=>x.Points).ThenBy(x=>(int)x.Element).First();
        return best.Points>0?best.Element:Element.Physical;
    }
''')

print('rarity/element follow-up patch applied')
