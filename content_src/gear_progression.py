"""Complete skill-level equipment tracks without replacing saved template IDs.

A tier is a matching-skill requirement, not the overall player level. Existing
items and recipes remain byte-for-byte equivalent. New alloys and textiles use
obtainable inputs; no unseeded ore or fictitious loot source is required.
"""
from __future__ import annotations
from copy import deepcopy
import math
from .items import Builder, MATERIALS, WEAPONS, SLOTS, ARMOR_TIERS

# level, key, metal name, cloth name, leather name, metal/cloth/leather palettes
TIERS = (
    (1,'copper','Copper','Linen','Tanned Leather','b97e55','788b78','96774f'),
    (5,'bronze','Bronze','Hempweave','Waxhide','b49a59','929676','987450'),
    (10,'iron','Iron','Wool','Boiled Leather','939da2','7c7088','89664a'),
    (15,'tempered_iron','Tempered Iron','Ridgeweave','Hardened Hide','818e9a','7b8798','826952'),
    (20,'blackiron','Blackiron','Duskcloth','Studded Leather','666f7a','71667e','6f5847'),
    (25,'steel','Steel','Silk','Reinforced Leather','b3bec4','965c75','826b52'),
    (27,'tempered_steel','Tempered Steel','Satinweave','Brigand Leather','a4b4ba','8b697d','866753'),
    (35,'dawnsteel','Dawnsteel','Sunweave','Sunhide','c5ad79','ad9968','9c7751'),
    (40,'silver','Silver','Moonweave','Wyvern Hide','c9ced3','829bb6','698273'),
    (45,'moonsteel','Moonsteel','Mistweave','Moonhide','a9bfc9','829bb0','707e85'),
    (50,'runesteel','Runesteel','Runeweave','Runebound Leather','97a3b7','9183a3','776781'),
    (55,'cobalt','Cobalt','Blueweave','Stormhide','6c91b7','668bac','6d7e93'),
    (60,'froststeel','Froststeel','Frostweave','Frosthide','94bdc7','83aeb2','849ba3'),
    (65,'stormsteel','Stormsteel','Stormweave','Tempest Hide','879cae','7c87a2','687b87'),
    (70,'mithril','Mithril','Starweave','Moonbound Leather','a3c2c7','909fc0','7a879a'),
    (75,'starforged_mithril','Starforged Mithril','Astralweave','Starhide','b6c7d8','a5a0bd','848092'),
    (80,'adamantite','Adamantite','Duskweave','Wyrmhide','789c89','785f89','6a6678'),
    (85,'obsidian','Obsidian','Ashweave','Emberhide','625b73','8e7479','86634f'),
    (90,'dragonsteel','Dragonsteel','Dragonweave','Drakeguard Leather','a78372','9b7578','966548'),
    (95,'celestium','Celestium','Celestial Weave','Celestial Hide','c5bdd8','b2a3c9','988eab'),
    (100,'aetherium','Aetherium','Aetherweave','Starguard Leather','b5b5d1','b19bc4','a598ad'),
)
TOOLS = (
    ('pickaxe','Prospector Pickaxe','mining','copper_pickaxe'),
    ('axe','Woodcutting Axe','woodcutting','woodcutters_axe'),
    ('rod','Fishing Rod','fishing','field_rod'),
    ('sickle','Harvest Sickle','herbalism','sickle'),
    ('shovel','Excavation Shovel','excavation','shovel'),
    ('knife','Skinning Knife','skinning','skinning_knife'),
    ('hammer','Crafting Hammer','smithing','crafting_hammer'),
)
OFFHANDS = (('shield','Kite Shield','shield_mastery','block'),
            ('focus','Spell Focus','arcane_magic','spell'),
            ('quiver','Leather Quiver','archery','accuracy'),
            ('orb','Focus Orb','runecasting','mana'))
ACCESSORIES = (('ring','Signet Ring','luck'),('necklace','Pendant','spirit'),
               ('charm','Traveler Charm','vitality'),('trinket','Engraved Brooch','resolve'))
ARMOR_NAMES = {
    'light': ('Hood','Robe','Handwraps','Trousers','Shoes','Sash','Mantle'),
    'medium': ('Coif','Jerkin','Bracers','Legguards','Riding Boots','Utility Belt','Travel Cloak'),
    'heavy': ('Plate Helm','Plate Cuirass','Gauntlets','Greaves','Sabatons','War Belt','Chainmantle'),
}


def material_at(level):
    return max((row for row in MATERIALS if row[2] <= level), key=lambda row: row[2])


def interpolate(level, column):
    """Interpolate strength or legacy material rank. Never increase attack speed."""
    points = [(row[2], row[3] if column == 'power' else index) for index,row in enumerate(MATERIALS)]
    if level <= points[0][0]: return float(points[0][1])
    for (lo,a),(hi,b) in zip(points,points[1:]):
        if level <= hi: return a + (b-a)*(level-lo)/(hi-lo)
    return float(points[-1][1])


def build(data):
    if data.get('equipmentTiers'):
        raise ValueError('Equipment progression must be built once, after the base catalog')
    b = Builder(data); b.ids = {i['id'] for i in data['items']}
    lookup = {i['id']:i for i in data['items']}
    legacy = deepcopy(lookup)
    recipes_before = {r['id']:deepcopy(r) for r in data['recipes']}
    created = set()
    def add(ident, name, kind='material', **kwargs):
        item = b.item(ident,name,kind,**kwargs); lookup[ident] = item; created.add(ident); return item
    def recipe(ident,name,skill,station,inputs,output,level,quantity=1):
        b.recipe(ident,name,skill,station,inputs,output,level,quantity=quantity,xp=25+level)
    def price(inputs,quantity=1):
        return max(5,math.ceil(sum(lookup[k]['value']*v for k,v in inputs.items())*1.15/quantity))
    def new_gear(template,ident,name,level,material,inputs,craft,station,**updates):
        item = deepcopy(template)
        for field in ('id','name','type'): item.pop(field,None)
        item.update(requirement=level,material=material,icon='items/'+ident+'.png',
                    value=price(inputs),tier=min(8,1+int(interpolate(level,'rank'))))
        item.update(updates)
        result = add(ident,name,template['type'],**item)
        recipe('make_'+ident,'Make '+name,craft,station,inputs,ident,level)
        return result
    # Tin is a merchant-sourced additive. Do not mislabel copper plus coal as bronze.
    add('tin_ore','Tin Ore','ore',material='tin',value=5,
        description='Buy from a miner or blacksmith. Refine three pieces into one tin ingot.')
    add('tin_bar','Tin Ingot',material='tin',value=16,requirement=5,
        description='A smelted alloying additive for bronze.')
    recipe('smelt_tin','Smelt Tin','smithing','forge',{'tin_ore':3},'tin_bar',5)
    data['equipmentTiers'] = []
    for level,key,label,cloth,leather,metal_color,cloth_color,leather_color in TIERS:
        base_key,_,base_level,_,wood,element = material_at(level)
        scale = interpolate(level,'power'); rank = interpolate(level,'rank')
        entries = {}
        metal = key+'_bar'
        if metal not in lookup:
            inputs = {'copper_bar':2,'tin_bar':1} if key=='bronze' else {base_key+'_bar':2,'coal':1}
            if level >= 35: inputs['rune_dust'] = 1+level//35
            if level >= 70: inputs['polished_gem'] = 1
            qty = 3 if key=='bronze' else 2
            add(metal,label+' Ingot',requirement=level,material=key,value=price(inputs,qty),
                description='Refine at a forge. Used for '+label+' equipment.',_color=metal_color)
            recipe('alloy_'+key,'Refine '+label,'smithing','forge',inputs,metal,level,qty)
        # Keep existing cloth supply chains. Add only the missing textiles.
        cloth_key = cloth.lower().replace(' ','')+'_cloth'
        if cloth_key not in lookup:
            parent = max((row for row in ARMOR_TIERS if row[1] <= level),key=lambda row:row[1])[0]+'_cloth'
            inputs = {parent:1,'thread':2}
            if level >= 27: inputs['rune_dust'] = 1+level//40
            add(cloth_key,cloth+' Cloth',requirement=level,material='cloth',value=price(inputs),_color=cloth_color,
                description='Weave at a loom. Used for '+cloth+' light armor.')
            recipe('weave_'+key+'_grade','Weave '+cloth,'tailoring','loom',inputs,cloth_key,level)
        hide_key = key+'_treated_leather'
        inputs = {'cured_leather':2,'thread':1}
        if level >= 27: inputs['rune_dust'] = 1+level//40
        add(hide_key,leather,material='leather',requirement=level,value=price(inputs),_color=leather_color,
            description='Prepare at a tannery. Used for '+label+'-grade leather armor and fittings.')
        recipe('tan_'+key+'_grade','Prepare '+leather,'leatherworking','tannery',inputs,hide_key,level)
        for family,name,skill,power,speed,reach,two_handed in WEAPONS:
            ident = key+'_'+family
            if ident not in lookup:
                craft = 'fletching' if family in ('bow','crossbow') else 'woodworking' if family in ('staff','wand') else 'scribing' if family=='tome' else 'leatherworking' if family=='knuckles' else 'smithing'
                station = {'fletching':'fletching_table','woodworking':'sawbench','scribing':'scriptorium','leatherworking':'tannery','smithing':'forge'}[craft]
                inputs = {metal:2,wood+'_plank':1,'cured_leather':1}
                if family=='tome': inputs = {metal:1,'parchment':4,'ink':2}
                if family=='knuckles': inputs = {metal:1,hide_key:2,'thread':1}
                new_gear(legacy['copper_'+family],ident,label+' '+name,level,key,inputs,craft,station,
                    power=round(power*scale,1),speed=speed,range=reach,
                    element=element if family in ('staff','wand','tome') else 'Physical',
                    stats={'spell':round(2*scale,2)} if family in ('staff','wand','tome') else {'accuracy':round(scale,2)},
                    _metal_color=metal_color,_wood=wood,
                    description=f'{label} fittings. Requires {skill.replace("_"," ")} {level}. {reach:g}-tile reach; {speed:g}-second base recovery. Craft at the {station.replace("_"," ")}.')
            entries['weapon/'+family] = ident
        # Reuse an existing armor set only when its grade agrees with the metal.
        old_armor = next((row for row in ARMOR_TIERS if row[1]==level and (row[4].lower()==key or level==1)),None)
        for weight,craft,station,mult,attr in (
            ('light','tailoring','loom',1.0,'intellect'),
            ('medium','leatherworking','tannery',1.7,'dexterity'),
            ('heavy','smithing','forge',2.5,'vitality')):
            for index,(slot,_,factor) in enumerate(SLOTS):
                ident = f'{old_armor[0]}_{weight}_{slot}' if old_armor else f'{key}_{weight}_{slot}'
                if ident not in lookup:
                    inputs = {cloth_key:2,'thread':1} if weight=='light' else {hide_key:2,'thread':1} if weight=='medium' else {metal:3,'cured_leather':1}
                    prefix = cloth if weight=='light' else leather if weight=='medium' else label
                    color = cloth_color if weight=='light' else leather_color if weight=='medium' else metal_color
                    new_gear(legacy[f'linen_{weight}_{slot}'],ident,prefix+' '+ARMOR_NAMES[weight][index],level,
                        key if weight=='heavy' else 'cloth' if weight=='light' else 'leather',inputs,craft,station,
                        armor=round((2+level*.35)*factor*mult,1),stats={attr:1+level//25},
                        _color=color,_metal_color=metal_color,
                        description=f'{weight.title()} armor; {label}-grade construction. Requires {weight} armor {level}. Craft at the {station}.')
                entries['armor/'+weight+'/'+slot] = ident
        for family,name,skill,stat in OFFHANDS:
            ident = key+'_'+family
            if ident not in lookup:
                craft,station = ('woodworking','sawbench') if family=='shield' else ('leatherworking','tannery') if family=='quiver' else ('enchanting','enchanter')
                new_gear(legacy['copper_'+family],ident,label+' '+name,level,key,{metal:1,hide_key:2},craft,station,
                    armor=round(3+level*.3,1) if family=='shield' else 0,stats={stat:round(2+rank*2,2)},
                    _metal_color=metal_color,_wood=wood,
                    description=('Use with a bow or crossbow. ' if family=='quiver' else 'Check weapon compatibility before equipping. ')+f'Requires {skill.replace("_"," ")} {level}.')
            entries['offhand/'+family] = ident
        for slot,name,stat in ACCESSORIES:
            ident = key+'_'+slot
            if ident not in lookup:
                new_gear(legacy['copper_'+slot],ident,label+' '+name,level,key,{metal:1,'polished_gem':1},'jewelcrafting','lapidary',
                    stats={stat:round(2+rank,2)},_metal_color=metal_color,
                    description=f'Engraved {label.lower()} setting with a fitted gemstone. Requires Jewelcrafting {level}.')
            entries['accessory/'+slot] = ident
        for tag,name,skill,starter_id in TOOLS:
            ident = starter_id if level==1 else key+'_tool_'+tag
            if ident not in lookup:
                efficiency=round(level*.15,2); tool_yield=round(level*.2,2)
                stats = {'tool_efficiency':efficiency}
                if tag!='hammer': stats['tool_yield']=tool_yield
                desc = f'Keep in your backpack. Requires {skill.replace("_"," ")} {level}. Best eligible tool is selected automatically. '
                desc += f'Reduces smithing action recovery by {efficiency:g}%.' if tag=='hammer' else f'{tool_yield:g}% chance of one extra gathered item; {efficiency:g}% less gathering stamina.'
                new_gear(legacy[starter_id],ident,label+' '+name,level,key,{metal:1,wood+'_plank':1,'cured_leather':1},'tinkering','workbench',
                    stats=stats,_metal_color=metal_color,_wood=wood,description=desc)
            entries['tool/'+tag] = ident
        data['equipmentTiers'].append(dict(id='equipment_'+str(level),level=level,name=label,cloth=cloth,leather=leather,entries=entries))
    # New materials remain obtainable without adding a mine or altering spawn geometry.
    for npc in data['npcs']:
        if npc['role'] in ('miner','blacksmith') and 'tin_ore' not in npc['stock']:
            npc['stock'].append('tin_ore')
    # Retail additions are bounded and role-specific. Every tier also has recipes.
    zones={z['id']:z for z in data['zones']}
    for npc in data['npcs']:
        cap=min(100,max(10,zones[npc['zone']]['level']+15))
        level=max(t[0] for t in TIERS if t[0]<=cap)
        row=next(t for t in data['equipmentTiers'] if t['level']==level)
        for family,ident in row['entries'].items():
            wanted=(npc['role']=='weaponsmith' and family.startswith('weapon/')) or (npc['role']=='armorer' and family.startswith('armor/')) or (npc['role']=='jeweler' and family.startswith('accessory/')) or (npc['role']=='blacksmith' and family.startswith('tool/')) or (npc['role']=='fletcher' and family in ('weapon/bow','weapon/crossbow','offhand/quiver')) or (npc['role']=='enchanter' and family in ('offhand/focus','offhand/orb'))
            if wanted and ident not in npc['stock']: npc['stock'].append(ident)
    # This is a save-compatibility invariant, not a snapshot of only catalog counts.
    if any(lookup[key] != value for key,value in legacy.items()):
        raise ValueError('A pre-existing item definition changed during progression extension')
    now={r['id']:r for r in data['recipes']}
    if any(now[key] != value for key,value in recipes_before.items()):
        raise ValueError('A pre-existing recipe changed during progression extension')
