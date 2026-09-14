"""Task 19: sparse regional profession resources and compact crafting loops.

This pass enriches existing regions only. Each rare resource is attached to one
established surface region; RealmEngine's existing deterministic resource seeder
therefore creates three shared nodes without adding any map or simulation layer.
"""
from .items import Builder

CHAINS = (
    dict(
        zone='old_boughs', resource='heartwood_stand', resource_name='Ancient Heartwood Stand',
        gather_item='heartwood_burl', gather_name='Heartwood Burl', skill='woodcutting', tool='axe',
        requirement=35, respawn=480, xp=90, sprite='resources/tree_elderwood.png',
        processed='seasoned_heartwood', processed_name='Seasoned Heartwood',
        process_recipe='season_heartwood', process_name='Season Heartwood', process_skill='woodworking', process_station='sawbench',
        process_inputs={'heartwood_burl':2,'salt':1}, process_requirement=35, process_value=38,
        specialty='heartwood_forester_axe', specialty_name='Heartwood Forester Axe', specialty_skill='woodcutting', specialty_tag='axe',
        specialty_recipe='make_heartwood_forester_axe', specialty_craft='tinkering', specialty_station='workbench', specialty_requirement=45,
        specialty_inputs={'seasoned_heartwood':2,'steel_bar':1,'cured_leather':1}, specialty_value=95,
        efficiency=10, yield_bonus=14,
        source='The Old Boughs'),
    dict(
        zone='mosswater', resource='ghost_reed_patch', resource_name='Ghost Reed Bed',
        gather_item='ghost_reed', gather_name='Ghost Reed', skill='herbalism', tool='sickle',
        requirement=35, respawn=420, xp=90, sprite='resources/herb_ghost_orchid.png',
        processed='ghost_reed_extract', processed_name='Ghost Reed Extract',
        process_recipe='distill_ghost_reed', process_name='Distill Ghost Reed', process_skill='alchemy', process_station='alchemy_table',
        process_inputs={'ghost_reed':2,'empty_vial':1}, process_requirement=35, process_value=32,
        specialty='ghost_reed_sickle', specialty_name='Ghost Reed Sickle', specialty_skill='herbalism', specialty_tag='sickle',
        specialty_recipe='make_ghost_reed_sickle', specialty_craft='tinkering', specialty_station='workbench', specialty_requirement=45,
        specialty_inputs={'ghost_reed_extract':2,'steel_bar':1,'yew_plank':1}, specialty_value=95,
        efficiency=10, yield_bonus=14,
        source='Mosswater Basin'),
    dict(
        zone='gull_isles', resource='moonfin_pool', resource_name='Moonfin Shoal',
        gather_item='moonfin', gather_name='Moonfin', skill='fishing', tool='rod',
        requirement=40, respawn=360, xp=95, sprite='resources/fishing.png',
        processed='moonfin_oil', processed_name='Moonfin Oil',
        process_recipe='press_moonfin_oil', process_name='Press Moonfin Oil', process_skill='cooking', process_station='kitchen',
        process_inputs={'moonfin':2,'salt':1}, process_requirement=40, process_value=38,
        specialty='moonfin_rod', specialty_name='Moonfin Rod', specialty_skill='fishing', specialty_tag='rod',
        specialty_recipe='make_moonfin_rod', specialty_craft='woodworking', specialty_station='sawbench', specialty_requirement=45,
        specialty_inputs={'moonfin_oil':2,'yew_plank':2,'thread':1}, specialty_value=105,
        efficiency=10, yield_bonus=14,
        source='The Gull Isles'),
    dict(
        zone='glassmere', resource='frostsilver_vein', resource_name='Frostsilver Vein',
        gather_item='frostsilver_ore', gather_name='Frostsilver Ore', skill='mining', tool='pickaxe',
        requirement=55, respawn=600, xp=120, sprite='resources/ore_silver.png',
        processed='frostsilver_bar', processed_name='Frostsilver Ingot',
        process_recipe='smelt_frostsilver', process_name='Smelt Frostsilver', process_skill='smithing', process_station='forge',
        process_inputs={'frostsilver_ore':3,'coal':1}, process_requirement=55, process_value=70,
        specialty='frostsilver_pickaxe', specialty_name='Frostsilver Prospector Pickaxe', specialty_skill='mining', specialty_tag='pickaxe',
        specialty_recipe='make_frostsilver_pickaxe', specialty_craft='tinkering', specialty_station='workbench', specialty_requirement=60,
        specialty_inputs={'frostsilver_bar':2,'blackwood_plank':1,'cured_leather':1}, specialty_value=165,
        efficiency=12, yield_bonus=16,
        source='Glassmere'),
)

RARE_RESOURCE_IDS = tuple(row['resource'] for row in CHAINS)
SPECIALTY_TOOL_IDS = tuple(row['specialty'] for row in CHAINS)
SPECIALTY_RECIPE_IDS = tuple(row['specialty_recipe'] for row in CHAINS)


def build(data):
    surface_before=sum(z['width']*z['height'] for z in data['zones'] if z['kind']=='wilderness' and z['layer']=='Surface')
    zone_count=len(data['zones'])
    zones={z['id']:z for z in data['zones']}
    existing_items={item['id'] for item in data['items']}
    existing_resources={resource['id'] for resource in data['resources']}
    existing_recipes={recipe['id'] for recipe in data['recipes']}
    b=Builder(data); b.ids=set(existing_items)

    for row in CHAINS:
        if row['zone'] not in zones: raise ValueError('Task 19 missing source region '+row['zone'])
        for ident in (row['gather_item'],row['processed'],row['specialty']):
            if ident in existing_items: raise ValueError('Task 19 duplicate item '+ident)
        if row['resource'] in existing_resources: raise ValueError('Task 19 duplicate resource '+row['resource'])
        for ident in (row['process_recipe'],row['specialty_recipe']):
            if ident in existing_recipes: raise ValueError('Task 19 duplicate recipe '+ident)

        source=row['source']
        b.item(row['gather_item'],row['gather_name'],'wood' if row['skill']=='woodcutting' else 'herb' if row['skill']=='herbalism' else 'ore' if row['skill']=='mining' else 'material',
               material='rare_resource',requirement=row['requirement'],value=max(12,row['process_value']//2),
               description=f'A scarce regional material gathered in {source}. Process it before specialist crafting.')
        b.item(row['processed'],row['processed_name'],'material',material='rare_resource',requirement=row['process_requirement'],value=row['process_value'],
               description=f'A processed profession component made from material gathered in {source}.')
        b.item(row['specialty'],row['specialty_name'],'tool',skill=row['specialty_skill'],requirement=row['specialty_requirement'],material='regional_specialty',
               value=row['specialty_value'],tags=[row['specialty_tag'],'regional_specialty'],
               stats={'tool_efficiency':row['efficiency'],'tool_yield':row['yield_bonus']},
               description=f'A regional specialty tool using materials from {source}. It improves gathering efficiency and yield until later masterwork tools overtake it.')

        data['resources'].append(dict(id=row['resource'],name=row['resource_name'],skill=row['skill'],tool=row['tool'],item=row['gather_item'],
                                      sprite=row['sprite'],requirement=row['requirement'],xp=row['xp'],respawn=row['respawn']))
        b.recipe(row['process_recipe'],row['process_name'],row['process_skill'],row['process_station'],row['process_inputs'],row['processed'],
                 row['process_requirement'],quantity=1,xp=row['xp'])
        b.recipe(row['specialty_recipe'],'Make '+row['specialty_name'],row['specialty_craft'],row['specialty_station'],row['specialty_inputs'],row['specialty'],
                 row['specialty_requirement'],quantity=1,xp=row['xp']+30)
        zones[row['zone']]['resources'].append(row['resource'])

    if len(data['zones'])!=zone_count: raise ValueError('Task 19 must not add world regions.')
    surface_after=sum(z['width']*z['height'] for z in data['zones'] if z['kind']=='wilderness' and z['layer']=='Surface')
    if surface_after!=surface_before: raise ValueError('Task 19 must not expand the surface footprint.')
    if len(set(RARE_RESOURCE_IDS))!=len(CHAINS) or len(set(SPECIALTY_TOOL_IDS))!=len(CHAINS):
        raise ValueError('Task 19 profession identities must be unique.')
    for row in CHAINS:
        if zones[row['zone']]['resources'].count(row['resource'])!=1:
            raise ValueError('Task 19 rare resource assignment is not deterministic: '+row['resource'])
        if row['respawn']<300:
            raise ValueError('Task 19 rare resources require controlled long respawns.')
        if row['efficiency']>15 or row['yield_bonus']>20:
            raise ValueError('Task 19 specialty tool exceeds ToolRules caps.')
