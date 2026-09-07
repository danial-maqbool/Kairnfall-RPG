"""Quest chains with concrete objectives and server-owned rewards."""
from .world import CITIES, REGIONS, DUNGEONS


def objective(action,target,count=1,description=''):
    return dict(action=action,target=target,count=count,description=description or f'{action.title()} {target.replace("_"," ")} ({count}).')


def add(data,ident,name,giver,story,objectives,category='side',prerequisite='',reward='',gold=30,faction='wayfarers',repeatable=False):
    data['quests'].append(dict(id=ident,name=name,giver=giver,story=story,objectives=objectives,category=category,prerequisite=prerequisite,reward=reward,gold=gold,faction=faction,repeatable=repeatable))


def build(data):
    main=[
      ('A Place by the Fire','wayfarers_rest_innkeeper','The village will shelter you, but its workshop needs a pair of hands. Gather timber, prepare a handle at the sawbench, and speak with the smith.',[objective('gather','oak_log',3),objective('craft','wooden_handle'),objective('talk','wayfarers_rest_blacksmith')],'sealed_letter',40),
      ('The Letter on the Road','dawnreach_traveler','Carry the Wayfarer letter to Dawnreach. The capital traveler knows why the western inns have begun taking in displaced miners.',[objective('deliver','sealed_letter')],'forge_charter',60),
      ('A Road Worth Recording','dawnreach_scribe','Visit at least four sectors of Kingsmeadow. Use parchment and ink to make a regional chart, then return to the scribe.',[objective('chart','kingsmeadow')],'lore_book_1',70),
      ('The Mill Has Fallen Silent','millcross_traveler','The grain carts have stopped. Enter the Broken Mill and defeat the scarred boar that has made it its den.',[objective('explore','broken_mill'),objective('boss','millbreaker')],'',120),
      ('Terms of the Forge','emberhold_traveler','The forge clans will open their records when they see the old charter. Take it through the Ember Marches to Emberhold.',[objective('deliver','forge_charter'),objective('talk','emberhold_scholar')],'lore_book_2',100),
      ('Metal from Below','emberhold_blacksmith','The lower mines still produce ore. Bring iron from a vein and refine it at the forge so its origin can be checked.',[objective('gather','iron_ore',6),objective('craft','iron_bar',2)],'',110),
      ('A Bell without Hands','dawnreach_scholar','A bell rings under the capital, although its chapel has collapsed. Follow the stair to Bell Crypt and confront its keeper.',[objective('explore','bell_crypt'),objective('boss','bell_warden')],'lore_book_6',150),
      ('Where the Roots Remember','thornhollow_traveler','Thornhollow remembers roads that the capital has removed from its maps. Reach the forest council and read its almanac.',[objective('talk','thornhollow_scholar'),objective('read','lore_book_3')],'',120),
      ('Threads across the Toll Road','stonebridge_traveler','A web has sealed the old tollhouse. The hidden road cannot reopen while the Mother of Silk remains inside.',[objective('explore','silken_tollhouse'),objective('boss','mother_of_silk')],'rune_winter_1',170),
      ('The Crown in the Tree','thornhollow_scholar','The Bracken King carries a metal crown inside living wood. Defeat the guardian without losing the route through the Root Court.',[objective('explore','root_court'),objective('boss','bracken_king')],'root_tablet',200),
      ('The Names under Stone','emberhold_scribe','Deliver the root-covered tablet to a reader of the old scripts. The marks are trade symbols, not royal titles.',[objective('deliver','root_tablet'),objective('explore','emberhold_deepway')],'lore_book_8',150),
      ('The Foundry That Still Burns','emberhold_blacksmith','The oldest furnace has begun moving. Enter the Sunken Foundry and stop Kilnheart before another shaft collapses.',[objective('explore','sunken_foundry'),objective('boss','kilnheart')],'rune_embers_2',230),
      ('A Watch in the Pines','pinewatch_traveler','The northern watch road has lost its scouts. Defeat the Sable Matron above the abandoned post.',[objective('explore','watchers_nest'),objective('boss','sable_matron')],'watcher_insignia',220),
      ('North of the Last Field','frostgate_traveler','The watcher insignia proves that you found the missing patrol route. Carry it to Frostgate before the next storm.',[objective('deliver','watcher_insignia'),objective('talk','frostgate_guard')],'lore_book_4',180),
      ('Under the Winter Road','frostgate_scholar','Winterhorn blocks a route below the frozen moor. The fortress needs that road before its stores run out.',[objective('explore','winterhorn_pass'),objective('boss','winterhorn')],'',300),
      ('The Harbor Answers','gloamport_traveler','A ship has answered the harbor bell from beneath the water. Follow its story to the Unmoored Vault.',[objective('explore','unmoored_vault'),objective('boss','captain_neris')],'harbor_manifest',280),
      ('Names Missing from the Ledger','gloamport_scribe','The lost manifest lists shipments to a city that no longer exists. Deliver it to the harbor scribe and read the account of its bells.',[objective('deliver','harbor_manifest'),objective('read','lore_book_5')],'',190),
      ('A Library of Bone','dawnreach_scholar','The Ivory Archive holds the builders\' names. Its librarian has forgotten the difference between a borrower and a thief.',[objective('explore','ivory_archive'),objective('boss','ivory_librarian')],'aether_compass',320),
      ('The Chorus in the Deepways','thornhollow_scholar','The buried roads speak through a fungal colony. Enter the Chorus Caverns and silence the threat beneath the miners\' voices.',[objective('explore','chorus_caverns'),objective('boss','chorus_below')],'',350),
      ('Three Cities beneath the Earth','emberhold_traveler','Trace the service tunnels before entering the lower crossroads. Record the route in person, not from a purchased map.',[objective('explore','dawnreach_deepway'),objective('explore','thornhollow_deepway'),objective('explore','umbral_crossroads')],'rune_warding_3',280),
      ('The Crown without a Kingdom','dawnreach_scholar','The Hollow Crown guards a road beyond the old war. Defeat it and leave the buried throne behind.',[objective('explore','hollow_throne'),objective('boss','hollow_crown')],'',400),
      ('The Compass Turns Twice','emberhold_scribe','The broken compass points toward an Aether fracture. Deliver it for calibration, then enter the crossing beneath the Umbral roads.',[objective('deliver','aether_compass'),objective('explore','aether_crossing')],'lore_book_7',300),
      ('The Light That Lies','frostgate_scholar','The Prism Observatory creates false paths. Defeat its archon and follow the physical return stair rather than the light.',[objective('explore','prism_observatory'),objective('boss','prism_archon')],'rune_precision_4',500),
      ('The Unwritten Names','gloamport_scholar','Something in the lost library is erasing the builders from every record. Defeat the Unwritten before the last route is forgotten.',[objective('explore','unwritten_library'),objective('boss','the_unwritten')],'',600),
      ('The Engine of Dawn','dawnreach_scholar','The five roads were built over an older engine. Reach its heart, defeat its assembled guardian, and return with the route intact.',[objective('explore','engine_of_dawn'),objective('boss','aether_heart'),objective('talk','dawnreach_traveler')],'rune_warding_5',1000)
    ]
    previous=''
    for i,(name,giver,story,objectives,reward,gold) in enumerate(main):
        ident=f'main_{i+1:02d}'; add(data,ident,name,giver,story,objectives,'main',previous,reward,gold); previous=ident
    # Twenty authored service contracts per capital. Objectives cover different systems.
    side_templates=[
      ('A Handle That Fits','woodworker','A workshop apprentice has cut the tang socket too wide. Make a new handle rather than buying a finished weapon.','craft','wooden_handle',2,'wooden_handle',35),
      ('The Assay Stamp','blacksmith','The assay office needs ingots made from traceable ore. Mine and smelt them yourself.','craft','copper_bar',3,'copper_pickaxe',45),
      ('A Clean Hem','tailor','The quartermaster needs cloth for bandages and travel repairs. Prepare thread at the loom.','craft','thread',4,'linen_cloth',40),
      ('Salt and Patience','tanner','Several hides arrived without preservation. Prepare leather that will survive the journey.','craft','cured_leather',3,'salt',45),
      ('Feathers in Balance','fletcher','The fletcher needs a matched arrow bundle for a caravan escort.','craft','arrow_bundle',10,'feather',50),
      ('The Empty Medicine Shelf','alchemist','The roadside shelters need medicine, not another untested herb mixture. Brew healing potions.','craft','healing_potion',4,'empty_vial',50),
      ('Bread before Sunrise','innkeeper','A late caravan has used the inn\'s food stores. Bake enough bread for the next travelers.','craft','bread',4,'wheat_seed',45),
      ('The First Inscription','rune_merchant','Carve a blank stone before trying a finished rune. The shape of the channel matters.','craft','rune_stone',2,'rune_dust',50),
      ('A Gem without Cracks','jeweler','The jeweler needs a stone with a clean face for a new setting.','craft','polished_gem',1,'rough_gem',60),
      ('A Page That Will Last','scribe','Prepare durable parchment for the regional records.','craft','parchment',4,'ink',50),
      ('A Meal from the River','fisher','Bring a fresh catch from a marked fishing pool. A purchased fish does not prove the waters are safe.','gather','river_trout',4,'salt',45),
      ('Leaves with Silver Edges','herbalist','The apothecary has run short of a common healing plant. Gather it before the road grows dangerous.','gather','meadow_leaf',6,'healing_potion',40),
      ('The Grain Ledger','provisioner','The kitchen will buy locally grown wheat. Deliver the grain after harvesting your crop.','deliver','wheat',3,'bread',45),
      ('A Place off the Road','carpenter','Build a safe wilderness camp away from a gate or travel point.','build','structure_campfire',1,'cooked_raw_meat',75),
      ('An Honest Exchange','traveler','Complete a reviewed trade with another traveler. Neither player should accept an offer they have not checked.','trade','*',1,'parchment',35),
      ('The Stone in the Hilt','enchanter','Insert a rune into a weapon or armor socket. Check its description before committing it.','socket','*',1,'rune_stone',55),
      ('A Worn Lock','guard','Open a locked chest with a lockpick. The guard wants proof of practice, not a broken lid.','chest','locked',1,'lockpick',65),
      ('The Story in the Margins','scholar','Read the account of the Five Road Oaths. The margin explains why the capitals share a market road.','read','lore_book_1',1,'treasure_map_1',45),
      ('Marks on the Regional Road','ferryman','Record the region around this city in a proper chart.','chart','@region',1,'ink',75),
      ('A Quiet Threat','trainer','Find the local dungeon entrance and identify the threat within it.','explore','@dungeon',1,'mana_potion',70)
    ]
    for city_index,(city_id,city_name,parent,biome,level,faction,*_) in enumerate(CITIES):
        nearby_dungeon=next((d[0] for d in DUNGEONS if d[2]==parent),DUNGEONS[city_index][0])
        for i,(name,role,story,action,target,count,reward,gold) in enumerate(side_templates):
            target=parent if target=='@region' else nearby_dungeon if target=='@dungeon' else target
            ident=f'{city_id}_contract_{i+1:02d}'
            add(data,ident,name+' — '+city_name,city_id+'_'+role,story+' This contract serves '+city_name+'.',[objective(action,target,count)],reward=reward,gold=gold+city_index*5,faction=faction)
    # Regional field contracts tie repeatable play to local ecology.
    for i,(region_id,region_name,biome,level,lore) in enumerate(REGIONS):
        giver=CITIES[i%len(CITIES)][0]+'_traveler'
        species=next(x for x in data['mobs'] if x['biome']==biome and not x['elite'] and not x['boss'])
        add(data,'field_'+region_id,'Field Report: '+region_name,giver,'Visit '+region_name+' and document its current threats. '+lore,[objective('explore',region_id),objective('kill',species['id'],3)],'repeatable',gold=50+level*3,repeatable=True)
    for i,(dungeon_id,name,parent,layer,biome,boss_id) in enumerate(DUNGEONS[:10]):
        giver=CITIES[i%5][0]+'_guild_registrar'
        add(data,'delve_'+dungeon_id,'Guild Delve: '+name,giver,'The guild will reward a verified return from '+name+'. Defeat its guardian after accepting this contract.',[objective('boss',boss_id)],'repeatable',gold=100+i*35,repeatable=True)
    for cls in data['classes']:
        skill=cls['affinity'][0]; ability=cls['abilities'][0]
        add(data,'class_'+cls['id'],cls['name']+' Initiation','dawnreach_trainer','Demonstrate the first technique of the '+cls['name']+'. Other classes may undertake this discipline after training the required skill.',[objective('cast',ability,3)],'class',reward='rune_precision_1',gold=60)
    # A short starter chain teaches gathering and recovery without text-only tutorials.
    add(data,'starter_fields','The Village Garden','wayfarers_rest_provisioner','Plant wheat on clear soil. Harvest it when the stalks mature.',[objective('plant','wheat'),objective('gather','wheat')],reward='wheat_seed',gold=25)
    add(data,'starter_rune','A Spark in the Stone','wayfarers_rest_trainer','Your starting weapon has one empty socket. Insert the rune supplied with your travel kit.',[objective('socket','*')],reward='healing_potion',gold=20)
    add(data,'starter_ore','Copper by the Road','wayfarers_rest_blacksmith','Use the pickaxe in your inventory to work a copper vein. Bring three pieces of ore back.',[objective('gather','copper_ore',3)],reward='copper_bar',gold=25)
