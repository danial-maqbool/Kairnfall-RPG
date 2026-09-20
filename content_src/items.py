"""Equipment families, material progression, runes, supplies, and recipes."""

MATERIALS = [
 ('copper','Copper',1,1.0,'oak','Physical'),
 ('iron','Iron',10,1.6,'ash','Physical'),
 ('steel','Steel',25,2.5,'yew','Physical'),
 ('silver','Silver',40,3.5,'ironwood','Radiant'),
 ('cobalt','Cobalt',55,4.5,'blackwood','Frost'),
 ('mithril','Mithril',70,5.7,'elderwood','Arcane'),
 ('obsidian','Obsidian',85,7.0,'emberwood','Fire'),
 ('aetherium','Aetherium',100,8.5,'starwood','Arcane')
]
WEAPONS = [
 ('sword','Arming Sword','swordsmanship',9,1.0,1.8,False),
 ('greatsword','Greatsword','swordsmanship',16,1.65,2.0,True),
 ('axe','Hand Axe','axe_mastery',11,1.25,1.6,False),
 ('greataxe','Bearded Greataxe','axe_mastery',20,1.9,1.9,True),
 ('mace','Flanged Mace','mace_mastery',12,1.35,1.6,False),
 ('greatmace','War Maul','mace_mastery',22,2.1,1.9,True),
 ('spear','Winged Spear','spear_mastery',10,1.15,2.6,True),
 ('halberd','Halberd','spear_mastery',17,1.7,2.8,True),
 ('dagger','Rondel Dagger','dagger_mastery',6,0.6,1.4,False),
 ('bow','Longbow','archery',12,1.25,7.0,True),
 ('crossbow','Windlass Crossbow','crossbow_mastery',20,2.1,8.0,True),
 ('staff','Traveler Staff','staff_mastery',8,1.2,2.2,True),
 ('wand','Channeling Wand','wand_mastery',7,0.85,6.0,False),
 ('tome','War Grimoire','arcane_magic',9,1.2,5.5,False),
 ('knuckles','Cestus','unarmed_combat',7,0.7,1.5,False)
]
SLOTS = [('helmet','Helm',0.6),('chest','Cuirass',1.6),('gloves','Gloves',0.35),('legs','Leggings',1.0),('boots','Boots',0.45),('belt','Belt',0.25),('cloak','Cloak',0.4)]
ARMOR_TIERS = [('linen',1,'Linen','Tanned','Riveted'),('wool',10,'Wool','Boiled','Iron'),('silk',25,'Silk','Reinforced','Steel'),('moonweave',40,'Moonweave','Wyvern','Silver'),('frostweave',60,'Frostweave','Frosthide','Cobalt'),('duskweave',80,'Duskweave','Wyrmhide','Mithril'),('aetherweave',100,'Aetherweave','Starguard','Aetherium')]

class Builder:
    def __init__(self,data): self.data=data; self.ids=set()
    def item(self,ident,name,kind='material',**kwargs):
        assert ident not in self.ids, ident
        self.ids.add(ident)
        item=dict(id=ident,name=name,type=kind,slot='',skill='',requirement=1,icon='items/'+ident+'.png',material='organic',description='',stackMax=99 if kind in {'material','ore','wood','herb','animal_material','food','potion','scroll','seed','rune','gem','ammo'} else 1,value=5,power=0,armor=0,speed=1,range=1.7,element='Physical',stats={},tags=[],tier=1,effect='')
        item.update(kwargs); self.data['items'].append(item); return item
    def recipe(self,ident,name,skill,station,ingredients,output,level=1,quantity=1,xp=25):
        self.data['recipes'].append(dict(id=ident,name=name,skill=skill,station=station,ingredients=ingredients,output=output,requirement=level,quantity=quantity,xp=xp))

def build(data):
    b=Builder(data)
    # Minerals and timber preserve the complete supply chain.
    for key,label,level,mult,wood,element in MATERIALS:
        b.item(key+'_ore',label+' Ore','ore',material=key,requirement=level,value=int(4*mult),description='A rock seam containing '+label.lower()+'. Refine it at a forge.')
        b.item(key+'_bar',label+' Ingot',material=key,requirement=level,value=int(12*mult),description='A refined metal ingot with chamfered corners and a stamped assay mark.')
        b.recipe('smelt_'+key,'Smelt '+label,'smithing','forge',{key+'_ore':3},key+'_bar',level,xp=20+level)
        b.item(wood+'_log',wood.title()+' Log','wood',material=wood,requirement=level,value=int(4*mult),description='A cut log with bark, growth rings, and a pale cut face.')
        b.item(wood+'_plank',wood.title()+' Plank','wood',material=wood,requirement=level,value=int(10*mult),description='A planed board used for handles, frames, furniture, and bow limbs.')
        b.recipe('saw_'+wood,'Saw '+wood.title()+' Boards','woodworking','sawbench',{wood+'_log':2},wood+'_plank',level,quantity=2,xp=20+level)
    supplies=[
      ('raw_hide','Raw Hide','animal_material','leather',4),('cured_leather','Cured Leather','material','leather',12),('sinew','Sinew','animal_material','organic',3),('bone','Bone','animal_material','bone',4),('fang','Fang','animal_material','bone',6),('feather','Feather','animal_material','feather',3),
      ('fiber','Plant Fiber','material','fiber',2),('thread','Spun Thread','material','fiber',6),('linen_cloth','Linen Cloth','material','linen',10),('wool_cloth','Wool Cloth','material','wool',14),('silk_cloth','Silk Cloth','material','silk',25),('moonweave_cloth','Moonweave Cloth','material','silk',40),('frostweave_cloth','Frostweave Cloth','material','wool',60),('duskweave_cloth','Duskweave Cloth','material','silk',80),('aetherweave_cloth','Aetherweave Cloth','material','silk',110),
      ('coal','Coal','ore','coal',4),('salt','Salt','material','salt',3),('glass','Glass','material','glass',6),('empty_vial','Empty Vial','material','glass',8),('parchment','Parchment','material','paper',8),('ink','Ink','material','ink',9),('rough_gem','Rough Gemstone','gem','crystal',20),('polished_gem','Polished Gemstone','gem','crystal',50),('rune_dust','Rune Dust','material','crystal',15),('rune_stone','Blank Rune Stone','material','stone',20),('ancient_fragment','Ancient Fragment','material','stone',20),('relic_shard','Relic Shard','material','crystal',60),('ectoplasm','Ectoplasm','material','ectoplasm',25),('venom_gland','Venom Gland','animal_material','organic',18),('drake_scale','Drake Scale','animal_material','scale',40),('frost_pelt','Frost Pelt','animal_material','fur',45),('ember_core','Ember Core','material','ember',50),('storm_crystal','Storm Crystal','gem','crystal',55),('aether_mote','Aether Mote','material','crystal',70)
    ]
    for ident,name,kind,mat,value in supplies: b.item(ident,name,kind,material=mat,value=value,description='A crafting component. Its source and use appear in the recipe journal.')
    b.recipe('cure_leather','Cure Leather','leatherworking','tannery',{'raw_hide':2,'salt':1},'cured_leather',quantity=1)
    b.recipe('spin_thread','Spin Thread','tailoring','loom',{'fiber':3},'thread',quantity=2)
    for index,(tier,level,*_) in enumerate(ARMOR_TIERS):
        ingredients={'thread':2+index}
        if index: ingredients['rune_dust']=max(1,index)
        b.recipe('weave_'+tier,'Weave '+tier.title(),'tailoring','loom',ingredients,tier+'_cloth',level,quantity=1,xp=30+level)
    b.recipe('make_parchment','Prepare Parchment','scribing','scriptorium',{'fiber':2,'raw_hide':1},'parchment',quantity=2)
    b.recipe('grind_ink','Grind Ink','scribing','scriptorium',{'coal':1,'rune_dust':1},'ink',quantity=3)
    b.recipe('cut_gem','Cut a Gemstone','jewelcrafting','lapidary',{'rough_gem':2},'polished_gem',xp=45)
    b.recipe('carve_rune','Carve Rune Stone','runecrafting','rune_table',{'ancient_fragment':2},'rune_stone',xp=35)
    b.recipe('blow_vial','Shape a Glass Vial','tinkering','workbench',{'glass':1},'empty_vial',quantity=2)
    # Fifteen weapon families have different reach, timing, and material construction.
    for key,label,level,mult,wood,element in MATERIALS:
        for family,name,skill,power,speed,reach,two_handed in WEAPONS:
            ident=key+'_'+family
            display=(wood.title()+' '+name) if family in {'bow','staff','wand'} else label+' '+name
            crafting='fletching' if family in {'bow','crossbow'} else 'woodworking' if family in {'staff','wand'} else 'scribing' if family=='tome' else 'leatherworking' if family=='knuckles' else 'smithing'
            station={'fletching':'fletching_table','woodworking':'sawbench','scribing':'scriptorium','leatherworking':'tannery','smithing':'forge'}[crafting]
            tags=[family]+(['two_handed'] if two_handed else [])
            stats={'spell':round(2*mult,1)} if family in {'staff','wand','tome'} else {'accuracy':round(mult,1)}
            b.item(ident,display,'weapon',slot='weapon',skill=skill,requirement=level,material=key,value=int(45*mult),power=round(power*mult,1),speed=speed,range=reach,element=element if family in {'staff','wand','tome'} else 'Physical',stats=stats,tags=tags,tier=MATERIALS.index((key,label,level,mult,wood,element))+1,description=f'{name}: {reach:g}-tile reach, {speed:g}-second base recovery.')
            ingredients={key+'_bar':2,wood+'_plank':1,'cured_leather':1}
            if family=='tome': ingredients={'parchment':4,'ink':2,key+'_bar':1}
            b.recipe('forge_'+ident,'Make '+display,crafting,station,ingredients,ident,level,xp=40+level)
    for tier,level,cloth,leather,metal in ARMOR_TIERS:
        for weight,material,prefix,skill,station,mult in [('light','cloth',cloth,'tailoring','loom',1.0),('medium','leather',leather,'leatherworking','tannery',1.7),('heavy','metal',metal,'smithing','forge',2.5)]:
            for slot,name,factor in SLOTS:
                ident=f'{tier}_{weight}_{slot}'
                armor=round((2+level*0.35)*factor*mult,1)
                label=prefix+' '+({'light':'Robe','medium':'Jerkin','heavy':'Cuirass'}[weight] if slot=='chest' else name)
                attr={'light':'intellect','medium':'dexterity','heavy':'vitality'}[weight]
                b.item(ident,label,'armor',slot=slot,skill=weight+'_armor',requirement=level,material=material,value=20+level*3,armor=armor,stats={attr:1+level//25},tags=[weight,slot],description=f'{weight.title()} armor. Seams, fasteners, and articulated joints distinguish its construction.')
                metal_key=MATERIALS[min(7,ARMOR_TIERS.index((tier,level,cloth,leather,metal)))][0]
                ingredients={tier+'_cloth':2,'thread':1} if weight=='light' else {'cured_leather':3,'thread':1} if weight=='medium' else {metal_key+'_bar':3,'cured_leather':1}
                b.recipe('make_'+ident,'Make '+label,skill,station,ingredients,ident,level,xp=35+level)
    for index,(key,label,level,mult,wood,element) in enumerate(MATERIALS):
        for family,name,skill,stat in [('shield','Kite Shield','shield_mastery','block'),('focus','Spell Focus','arcane_magic','spell'),('quiver','Leather Quiver','archery','accuracy'),('orb','Focus Orb','runecasting','mana')]:
            ident=key+'_'+family
            b.item(ident,label+' '+name,'offhand',slot='offhand',skill=skill,requirement=level,material=key,value=35+level*3,armor=(3+level*0.3) if family=='shield' else 0,stats={stat:2+index*2},tags=[family],description='An offhand item with a distinct silhouette and visible construction.')
            b.recipe('make_'+ident,'Make '+label+' '+name,'woodworking' if family=='shield' else 'leatherworking' if family=='quiver' else 'enchanting','sawbench' if family=='shield' else 'tannery' if family=='quiver' else 'enchanter', {key+'_bar':1,'cured_leather':2},ident,level,xp=35+level)
        for slot,name,stat in [('ring','Signet Ring','luck'),('necklace','Pendant','spirit'),('charm','Traveler Charm','vitality'),('trinket','Engraved Brooch','resolve')]:
            ident=key+'_'+slot
            b.item(ident,label+' '+name,'accessory',slot=slot,skill='jewelcrafting',requirement=level,material=key,value=60+level*4,stats={stat:2+index},tags=[slot],description='A worked metal setting with engraved detail and a fitted gemstone.')
            b.recipe('make_'+ident,'Make '+label+' '+name,'jewelcrafting','lapidary',{key+'_bar':1,'polished_gem':1},ident,level,xp=45+level)
    tools=[('copper_pickaxe','Copper Pickaxe','pickaxe','mining'),('woodcutters_axe',"Woodcutter's Axe",'axe','woodcutting'),('field_rod','Field Fishing Rod','rod','fishing'),('sickle','Harvest Sickle','sickle','herbalism'),('shovel','Field Shovel','shovel','excavation'),('skinning_knife','Skinning Knife','knife','skinning'),('crafting_hammer','Crafting Hammer','hammer','smithing')]
    for ident,name,tag,skill in tools:
        b.item(ident,name,'tool',skill=skill,material='wood_metal',value=20,tags=[tag],description='A fitted wooden handle supports a recognizable working head. Keep it in your inventory to use it.')
        b.recipe('make_'+ident,'Make '+name,'tinkering','workbench',{'copper_bar':1,'oak_plank':1},ident,xp=30)
    b.item('lockpick','Lockpick','material',material='iron',value=6,description='A narrow steel pick and tension wrench. One set is consumed when opening a locked chest.')
    b.recipe('bend_lockpicks','Bend Lockpicks','tinkering','workbench',{'copper_bar':1},'lockpick',quantity=4,xp=25)
    rune_kinds=[('embers','Embers','damage_fire','Fire'),('winter','Winter','resist_frost','Frost'),('bulwark','Bulwark','block','Physical'),('precision','Precision','crit','Physical'),('leeching','Leeching','leech','Shadow'),('echoes','Echoes','spell','Arcane'),('prospector','Prospector','gather_yield','Physical'),('wanderer','Wanderer','movement','Nature'),('radiance','Radiance','healing','Radiant'),('vigor','Vigor','vitality','Nature'),('storm','Storm','damage_lightning','Lightning'),('warding','Warding','armor','Arcane')]
    for key,label,stat,element in rune_kinds:
        for tier in range(1,6):
            ident=f'rune_{key}_{tier}'; value=tier if stat=='leech' else tier*2
            b.item(ident,f'Rune of {label} {"I II III IV V".split()[tier-1]}','rune',material='runestone',value=30*tier*tier,tier=tier,element=element,stats={stat:value},description=f'Insert into an empty equipment socket. Adds {value:g} {stat.replace("_"," ")}. Effects obey global stat caps.')
            b.recipe('inscribe_'+ident,'Inscribe '+label+' '+str(tier),'runecrafting','rune_table',{'rune_stone':1,'rune_dust':2*tier},ident,1+(tier-1)*15,xp=40*tier)
    herbs=[('meadow_leaf','Meadow Leaf',1),('silverleaf','Silverleaf',10),('bloodroot','Bloodroot',25),('moonblossom','Moonblossom',40),('frostmint','Frostmint',55),('emberpetal','Emberpetal',70),('ghost_orchid','Ghost Orchid',85),('star_lotus','Star Lotus',100)]
    for ident,name,level in herbs: b.item(ident,name,'herb',material='leaf',requirement=level,value=4+level//4,description='A recognizable medicinal plant with shaped leaves, stems, and flowers.')
    foods=[('wheat','Wheat',1),('wild_berry','Wild Berries',1),('field_mushroom','Field Mushroom',5),('river_trout','River Trout',1),('silver_carp','Silver Carp',10),('marsh_eel','Marsh Eel',25),('ice_pike','Ice Pike',40),('red_snapper','Red Snapper',55),('abyssal_cod','Abyssal Cod',70),('storm_ray','Storm Ray',85),('starfin','Starfin',100),('raw_meat','Raw Meat',1)]
    for ident,name,level in foods: b.item(ident,name,'material',material='food',requirement=level,value=4+level//3,description='A cooking ingredient. Prepare it at a cooking station.')
    b.item('wheat_seed','Wheat Seed','seed',material='seed',value=2,description='Plant in clear surface soil. Harvest mature wheat with Farming.')
    b.item('healing_potion','Healing Potion','potion',material='red_glass',value=10,power=60,effect='heal',description='Restores 60 health. Shares a five-second potion cooldown.')
    b.item('mana_potion','Mana Potion','potion',material='blue_glass',value=10,power=60,effect='mana',description='Restores 60 mana. Shares the potion cooldown.')
    b.item('antidote','Antidote','potion',material='green_glass',value=14,effect='purge',description='Removes poison, burning, and curses.')
    b.recipe('brew_healing','Brew Healing Potion','alchemy','alchemy_table',{'meadow_leaf':2,'empty_vial':1},'healing_potion',quantity=2,xp=35)
    b.recipe('brew_mana','Brew Mana Potion','alchemy','alchemy_table',{'silverleaf':2,'empty_vial':1},'mana_potion',10,quantity=2,xp=45)
    b.recipe('brew_antidote','Brew Antidote','alchemy','alchemy_table',{'bloodroot':1,'empty_vial':1},'antidote',25,xp=60)
    for index,base in enumerate(['river_trout','silver_carp','marsh_eel','ice_pike','red_snapper','abyssal_cod','storm_ray','starfin','raw_meat']):
        name='Roasted '+base.replace('_',' ').title(); ident='cooked_'+base; requirement=1 if base=='raw_meat' else [1,10,25,40,55,70,85,100][index]
        b.item(ident,name,'food',material='food',value=12+requirement,power=48+requirement,effect='food',requirement=requirement,description='Restores health over twelve seconds and restores stamina.')
        b.recipe('cook_'+base,name,'cooking','kitchen',{base:2,'salt':1},ident,requirement,xp=30+requirement)
    b.item('bread','Hearth Bread','food',material='bread',value=8,power=36,effect='food',description='A scored loaf with a browned crust. Restores health over time.')
    b.recipe('bake_bread','Bake Hearth Bread','cooking','kitchen',{'wheat':3,'salt':1},'bread',quantity=2)
    b.item('animal_bait','Animal Bait','food',material='meat',value=10,power=12,effect='food',description='Use to tame a weakened animal. Can also serve as emergency food.')
    b.recipe('prepare_bait','Prepare Animal Bait','cooking','kitchen',{'raw_meat':1,'wild_berry':1},'animal_bait',quantity=2)
    b.item('wooden_handle','Shaped Handle',material='oak',value=8,description='A sanded handle with a fitted tang socket.')
    b.recipe('shape_handle','Shape a Handle','woodworking','sawbench',{'oak_plank':1},'wooden_handle',quantity=2)
    b.item('arrow_bundle','Arrow Bundle','ammo',material='wood_metal',value=8,description='Fletched arrows with barbed metal heads.')
    b.recipe('fletch_arrows','Fletch Arrows','fletching','fletching_table',{'oak_plank':1,'feather':2,'copper_bar':1},'arrow_bundle',quantity=10)
    structures=[('campfire','Stone-ring Campfire',1,{'oak_log':4,'copper_ore':2}),('workbench','Joiner Workbench',10,{'oak_plank':6,'iron_bar':2}),('sawbench','Sawbench',15,{'ash_plank':6,'iron_bar':2}),('kitchen','Field Cooking Hearth',20,{'iron_bar':3,'oak_plank':4}),('rune_table','Portable Rune Table',35,{'yew_plank':5,'rune_stone':3})]
    for name,label,level,ingredients in structures:
        ident='structure_'+name
        b.item(ident,label,'structure',material='wood_stone',value=40+level*3,requirement=level,tags=[name],description='Place in clear wilderness terrain. Its service becomes available nearby.')
        b.recipe('build_'+name,'Build '+label,'construction','hand',ingredients,ident,level,xp=100+level)
        if name!='campfire': b.recipe('join_'+name,'Join '+label,'carpentry','workbench',ingredients,ident,level,xp=80+level)
    b.item('enchanted_thread','Enchanted Thread',material='silk',value=25,description='Thread bound with a small arcane charge.')
    b.recipe('enchant_thread','Enchant Thread','enchanting','enchanter',{'thread':3,'rune_dust':2},'enchanted_thread',10,quantity=2,xp=45)
    for index,title in enumerate(['The Five Road Oaths','A Miner\'s Weather Book','The Thornhollow Almanac','Northern Signal Fires','Harbor Bells at Dusk','A Map of Lost Wells','Aetheric Bearings','The Names Below Stone']):
        ident='lore_book_'+str(index+1)
        b.item(ident,title,'book',material='book',value=20+index*10,requirement=1+index*10,description=[
          'Five roads were built to keep the cities from fighting over winter supplies. A traveler who carries food and ore can read the old agreement in every bridge and toll house.',
          'Warm air rising from an abandoned shaft can mean an underground fire. Emberhold miners leave blue ribbons at such entrances. Never mistake an empty mine for a safe mine.',
          'The oldest trees grow around buried stone, not fertile soil. Follow the pale roots where three small streams meet. A sealed stair lies beneath them.',
          'Frostgate signal fires burn in pairs. A single flame means a scout has returned. Three mean the watchers have seen something moving beneath the ice.',
          'Gloamport rings the west bell before a storm. A ship that answers after midnight is not on any harbor ledger.',
          'The seventh well lies east of a broken milestone. Its water reflects stars at noon. A worn ladder remains under the rim.',
          'A compass needle turns twice near an Aether fracture. Mark the real road before entering. The road shown in the glass may not lead home.',
          'The Deepways were a network of workshops before they became tombs. Their builders signed each doorway with a trade symbol. The hammer marks are the safest route.'
        ][index])
        b.recipe('copy_'+ident,'Copy '+title,'scribing','scriptorium',{'parchment':3,'ink':2},ident,1+index*10,xp=60+index*10)
    for i in range(8):
        b.item('treasure_map_'+str(i+1),'Tattered Survey '+str(i+1),'treasure_map',material='paper',value=25+i*15,requirement=1+i*10,description='Search the hidden cache northeast of the regional waystone. Look behind the broken masonry, not on the road. The marked cache may require a lockpick or rune skill.')
    for ident,name in [('sealed_letter','Sealed Wayfarer Letter'),('forge_charter','Forge Charter'),('root_tablet','Root-covered Tablet'),('watcher_insignia','Watcher Insignia'),('harbor_manifest','Lost Harbor Manifest'),('aether_compass','Broken Aether Compass')]:
        b.item(ident,name,'quest',material='paper' if 'letter' in ident or 'charter' in ident or 'manifest' in ident else 'metal',value=0,description='A quest object. It cannot be sold, traded, or auctioned.')
    # Resource entries define the actual gathering action and tool contract.
    for key,label,level,mult,wood,_ in MATERIALS:
        data['resources'].append(dict(id=key+'_vein',name=label+' Vein',skill='mining',tool='pickaxe',item=key+'_ore',sprite='resources/ore_'+key+'.png',requirement=level,xp=25+level,respawn=20+level/2))
        data['resources'].append(dict(id=wood+'_tree',name=wood.title()+' Timber',skill='woodcutting',tool='axe',item=wood+'_log',sprite='resources/tree_'+wood+'.png',requirement=level,xp=25+level,respawn=25+level/2))
    for ident,name,level in herbs:
        data['resources'].append(dict(id=ident+'_patch',name=name+' Patch',skill='herbalism',tool='sickle',item=ident,sprite='resources/herb_'+ident+'.png',requirement=level,xp=20+level,respawn=30))
    for ident,name,level in foods[3:11]:
        data['resources'].append(dict(id=ident+'_pool',name=name+' Waters',skill='fishing',tool='rod',item=ident,sprite='resources/fishing.png',requirement=level,xp=25+level,respawn=12))
    extras=[('berry_bush','Berry Bush','foraging','','wild_berry',1),('mushroom_patch','Mushroom Patch','foraging','','field_mushroom',5),('flax_patch','Wild Flax','foraging','','fiber',1),('wheat_crop','Mature Wheat','farming','sickle','wheat',1),('animal_carcass','Animal Remains','skinning','knife','raw_hide',1),('buried_pottery','Buried Pottery','excavation','shovel','ancient_fragment',1),('relic_deposit','Buried Relic','excavation','shovel','relic_shard',45),('meteor_ore','Meteor Fragment','mining','pickaxe','storm_crystal',1)]
    for ident,name,skill,tool,item,level in extras: data['resources'].append(dict(id=ident,name=name,skill=skill,tool=tool,item=item,sprite='resources/'+ident+'.png',requirement=level,xp=25+level,respawn=40))
