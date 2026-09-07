"""Connected geography, distinct city plans, services, and dungeon entrances."""
from .items import MATERIALS
from .mobs import BOSSES

REGIONS = [
 ('pinewatch_reach','Pinewatch Reach','pine_forest',26,'Resin-scarred pines surround the abandoned charcoal road.'),
 ('northern_moor','Northern Moor','tundra',36,'Low stone windbreaks mark the winter route to Frostgate.'),
 ('glassmere','Glassmere','glacier',56,'Blue crevasses divide the frozen lake around a drowned shrine.'),
 ('basalt_spine','Basalt Spine','mountains',46,'Old rope bridges cross the ridges above the eastern mines.'),
 ('ash_crown','Ash Crown','volcanic',66,'Broken military roads disappear beneath cooling ash.'),
 ('old_boughs','The Old Boughs','ancient_forest',21,'Living roots hold together bridges older than the surrounding forest.'),
 ('thistle_woods','Thistle Woods','forest',6,'Small logging camps share the woods with old boundary shrines.'),
 ('kingsmeadow','Kingsmeadow','plains',1,'Five stone milestones mark the roads that converge on Dawnreach.'),
 ('ember_marches','Ember Marches','highlands',17,'Ore carts and broken watch posts line the forge road.'),
 ('cinder_fields','Cinder Fields','volcanic',36,'New growth appears between cold lava flows and abandoned kilns.'),
 ('westfarms','Westfarms','farmland',2,'Irrigation ditches, windmills, and terraced fields feed the capital.'),
 ('silver_run','Silver Run','forest',9,'A bright river passes through old hunting grounds and a ruined toll house.'),
 ('blackfen','Blackfen','swamp',19,'Raised causeways connect islands of firm ground above the marsh.'),
 ('saltwind','Saltwind Shore','coast',13,'Fishing sheds and stranded boats stand above the tidal flats.'),
 ('dry_reach','The Dry Reach','badlands',33,'Buried caravan markers point toward a city erased from recent maps.'),
 ('mosswater','Mosswater Basin','wetlands',24,'Reed villages trade herbs gathered beside the slow western channels.'),
 ('mournground','Mournground','wasteland',41,'Grass no longer grows between the old battlefield shrines.'),
 ('stonefall','Stonefall Ruins','ruins',66,'A fallen aqueduct links fragments of an older capital.'),
 ('gull_isles','The Gull Isles','archipelago',33,'Low causeways connect inhabited islands at the edge of the harbor charts.'),
 ('starfall_scar','Starfall Scar','arcane_anomaly',76,'A pale fracture crosses the land where an ancient engine touched the surface.')
]

CITIES = [
 ('dawnreach','Dawnreach','kingsmeadow','plains',1,'crown','limestone','A walled market capital built around the Five Roads compact.'),
 ('emberhold','Emberhold','ember_marches','highlands',18,'forge_clans','forge','A stepped forge city whose workshops surround the old lift shafts.'),
 ('thornhollow','Thornhollow','old_boughs','ancient_forest',22,'circle','timber','A forest city of timber halls and root bridges around a living council tree.'),
 ('frostgate','Frostgate','northern_moor','tundra',38,'wardens','northern','A northern fortress organized around sheltered courtyards and signal towers.'),
 ('gloamport','Gloamport','saltwind','coast',15,'league','harbor','A fog-bound harbor city whose market follows the old sea wall.')
]
SETTLEMENTS = [
 ('reedhaven','Reedhaven','mosswater'),('millcross','Millcross','westfarms'),('pinewatch','Pinewatch','pinewatch_reach'),('brambleford','Brambleford','thistle_woods'),('stonebridge','Stonebridge','silver_run'),('copperstead','Copperstead','ember_marches'),('whitepost','Whitepost','northern_moor'),('saltmere','Saltmere','saltwind'),('gullhaven','Gullhaven','gull_isles'),('dustwell','Dustwell','dry_reach')
]
DUNGEONS = [
 ('broken_mill','The Broken Mill','westfarms','Deepways','ruins','millbreaker'),
 ('bell_crypt','Bell Crypt','kingsmeadow','Deepways','ruins','bell_warden'),
 ('silken_tollhouse','Silken Tollhouse','silver_run','Deepways','forest','mother_of_silk'),
 ('root_court','The Root Court','old_boughs','Deepways','ancient_forest','bracken_king'),
 ('sunken_foundry','Sunken Foundry','ember_marches','Deepways','volcanic','kilnheart'),
 ('watchers_nest',"Watcher's Nest",'pinewatch_reach','Deepways','pine_forest','sable_matron'),
 ('drowned_cistern','Drowned Cistern','blackfen','Deepways','swamp','saltjaw'),
 ('unmoored_vault','The Unmoored Vault','saltwind','Deepways','coast','captain_neris'),
 ('ivory_archive','Ivory Archive','stonefall','Deepways','ruins','ivory_librarian'),
 ('glasswing_grotto','Glasswing Grotto','basalt_spine','Deepways','crystal','glasswing'),
 ('regents_tomb',"Regent's Tomb",'dry_reach','Umbral Depths','badlands','dune_regent'),
 ('chorus_caverns','Chorus Caverns','mosswater','Umbral Depths','fungal','chorus_below'),
 ('winterhorn_pass','Winterhorn Pass','northern_moor','Umbral Depths','tundra','winterhorn'),
 ('rime_abbey','Rime Abbey','glassmere','Umbral Depths','glacier','rime_abbess'),
 ('cinder_barracks','Cinder Barracks','ash_crown','Umbral Depths','volcanic','cinder_marshal'),
 ('reef_sanctum','Reef Sanctum','gull_isles','Umbral Depths','archipelago','reef_colossus'),
 ('hollow_throne','The Hollow Throne','mournground','Umbral Depths','wasteland','hollow_crown'),
 ('prism_observatory','Prism Observatory','basalt_spine','Aether Rift','crystal','prism_archon'),
 ('unwritten_library','The Unwritten Library','starfall_scar','Aether Rift','arcane_anomaly','the_unwritten'),
 ('engine_of_dawn','Engine of Dawn','starfall_scar','Aether Rift','arcane_anomaly','aether_heart')
]

ROLES = [
 ('blacksmith','Forge','forge','Hot metal tells me more than a polished blade. Bring ore to the forge, then come back when your equipment needs repair.'),
 ('armorer','Armory','','Plate needs joints as much as it needs metal. Read the armor skill requirement before you buy.'),
 ('weaponsmith','Weapon Shop','','Reach and recovery matter. A spear controls a lane; a dagger rewards close movement.'),
 ('fletcher','Fletcher','fletching_table','A straight shaft and matched feathers matter more than a bright arrowhead.'),
 ('provisioner','Provisions','','Food restores stamina and health over time. Carry supplies before leaving the road.'),
 ('alchemist','Apothecary','alchemy_table','Plants and clean glass make reliable medicine. Stronger herbs need stronger Herbalism training.'),
 ('rune_merchant','Runes','rune_table','A rune is an item, not a promise. Check the socket count before spending your gold.'),
 ('enchanter','Enchantments','enchanter','Rune extraction has a cost, but it need not destroy the equipment.'),
 ('jeweler','Jeweler','lapidary','A setting protects the stone. Cut rough gems here before you make a ring.'),
 ('banker','Bank','','I record every deposit. Unequip an item before moving it into storage.'),
 ('auctioneer','Auction Hall','','A listing moves the item into escrow. The price covers the complete listed stack.'),
 ('innkeeper','Inn','kitchen','A warm hearth restores a traveler. We do not offer rest while enemies are still following you.'),
 ('guild_registrar','Guild Registry','','A guild needs a name and a founder. The leader controls invitations and the public message.'),
 ('tailor','Tailor','loom','Turn gathered fiber into thread, then weave cloth. Higher cloth tiers need additional materials.'),
 ('tanner','Tannery','tannery','A raw hide is not yet leather. Salt and careful preparation keep it useful.'),
 ('carpenter','Joinery','workbench','A joint should carry its load without splitting. Workbenches and field stations need more than loose branches.'),
 ('woodworker','Sawmill','sawbench','Each timber has its own grain. Prepare boards before shaping a staff or shield.'),
 ('scribe','Scriptorium','scriptorium','Ink fixes a memory to paper. Read the old records before copying them.'),
 ('guard','Watch Post','','The road is patrolled, not harmless. Watch the ground when a creature prepares a heavy attack.'),
 ('scholar','Archive','','The five cities were not the first settlements here. Their roads follow older tunnels.'),
 ('ferryman','Travel Office','','Discover a destination before using its waystone. Unmarked journeys still require your own feet.'),
 ('herbalist','Herb Stall','','The leaves tell you which plant you found. Do not trust color alone.'),
 ('miner','Assay Office','','Prospecting can reveal a gem before you extract the ore. A used seam needs time to recover.'),
 ('fisher','Fish Market','','Different waters hold different catches. Weather can change the work even when the water looks calm.'),
 ('trainer','Training Yard','','Every skill contributes to your overall level. Class affinity helps, but it does not forbid another trade.'),
 ('traveler','Wayfarer Lodge','','I leave a small mark on every route I chart. A hidden cache rarely stands in the middle of the road.')
]
FIRST_NAMES=['Mara','Orin','Elira','Bren','Sera','Tavin','Iona','Kellan','Nessa','Doran','Vela','Harlan','Miren','Rusk','Alda','Fen','Liora','Corin','Tessa','Wren','Osric','Mina','Ronan','Edda','Silas','Anwen']
SURNAMES=['Alder','Stonehand','Reed','Northwind','Saltmere','Ashcroft','Vale','Briar','Wick','Brass','Rowan','Grey','Hearth','Thorn','Moss','Gale','Drift','Flint','Willow','Brook','Cairn','Tide','Frost','Ember','Hollow','Sable']


def point(x,y): return {'x':float(x),'y':float(y)}

def zone(ident,name,biome,level,kind='wilderness',layer='Surface',size=320,seed=1,world_x=0,world_y=0,lore=''):
    return dict(id=ident,name=name,biome=biome,level=level,kind=kind,layer=layer,width=size,height=size,seed=seed,spawn=point(size/2+0.5,size/2+0.5),worldX=world_x,worldY=world_y,lore=lore,exits=[],buildings=[],species=[],boss='',resources=[])

def connect(a,b,at_a,at_b,kind='road',requirement=1):
    a['exits'].append(dict(id=a['id']+'_to_'+b['id'],target=b['id'],position=point(*at_a),arrival=point(*at_b),kind=kind,requirement=requirement))
    b['exits'].append(dict(id=b['id']+'_to_'+a['id'],target=a['id'],position=point(*at_b),arrival=point(*at_a),kind=kind,requirement=1))

def stock_for(role,level,data):
    cap=min(100,max(10,level+15))
    categories={
      'blacksmith':{'tool','ore','material'},'armorer':{'armor'},'weaponsmith':{'weapon'},'fletcher':{'ammo'},'provisioner':{'food','potion','seed','material'},'alchemist':{'potion','herb'},'rune_merchant':{'rune'},'enchanter':{'rune','material'},'jeweler':{'gem','accessory'},'tailor':{'material'},'tanner':{'animal_material','material'},'carpenter':{'wood','structure'},'woodworker':{'wood'},'scribe':{'book','material','treasure_map'},'herbalist':{'herb'},'miner':{'ore'},'fisher':{'material','food'}
    }
    if role not in categories: return []
    candidates=[x for x in data['items'] if x['type'] in categories[role] and x['requirement']<=cap]
    if role=='blacksmith': candidates=[x for x in candidates if x['type']=='tool' or x['id'] in {'coal','copper_ore','iron_ore','copper_bar','iron_bar'}]
    elif role=='provisioner': candidates=[x for x in candidates if x['id'] in {'healing_potion','mana_potion','bread','salt','wheat_seed','animal_bait','empty_vial','glass','lockpick'}]
    elif role=='tailor': candidates=[x for x in candidates if 'cloth' in x['id'] or x['id'] in {'fiber','thread'}]
    elif role=='tanner': candidates=[x for x in candidates if x['id'] in {'raw_hide','cured_leather','salt','sinew'}]
    elif role=='enchanter': candidates=[x for x in candidates if x['type']=='rune' or x['id'] in {'rune_dust','rune_stone','enchanted_thread'}]
    elif role=='scribe': candidates=[x for x in candidates if x['type'] in {'book','treasure_map'} or x['id'] in {'ink','parchment'}]
    elif role=='fisher': candidates=[x for x in candidates if any(s in x['id'] for s in ['trout','carp','eel','pike','snapper','cod','ray','starfin','bait'])]
    return [x['id'] for x in candidates[:80]]


def add_npc(data,z,role_index,index,faction,location=None):
    role,service,station,dialogue=ROLES[role_index]
    x,y=location or (z['spawn']['x']+(index%2)*2,z['spawn']['y']-14+index*2)
    npc_id=z['id']+'_'+role
    if any(n['id']==npc_id for n in data['npcs']): npc_id+='_'+str(index)
    name=FIRST_NAMES[(index+z['seed'])%len(FIRST_NAMES)]+' '+SURNAMES[(index*3+z['seed']//7)%len(SURNAMES)]
    data['npcs'].append(dict(id=npc_id,name=name,role=role,zone=z['id'],faction=faction,position=point(x,y),dialogue=dialogue+' '+z['lore'],stock=stock_for(role,z['level'],data),station=station,sprite='npcs/'+role+'.png'))
    return npc_id


def build(data):
    zones=data['zones']; by_id={}
    for i,(ident,name,biome,level,lore) in enumerate(REGIONS):
        z=zone(ident,name,biome,level,seed=911+i*37,world_x=i%5,world_y=i//5,lore=lore)
        z['species']=[x['id'] for x in data['mobs'] if x['biome']==biome and not x['boss'] and not x['elite']]
        rare=[x['id'] for x in data['mobs'] if x['biome']==biome and x['elite']]
        if rare: z['species'].append(rare[i%len(rare)])
        tier=max(0,min(7,next((n for n,row in enumerate(MATERIALS) if row[2]>level),8)-1))
        material=MATERIALS[tier]; z['resources']=[material[0]+'_vein',material[4]+'_tree','buried_pottery']
        if biome in {'forest','ancient_forest','pine_forest','plains','farmland','wetlands'}: z['resources']+=['berry_bush','flax_patch','meadow_leaf_patch']
        if biome in {'coast','archipelago','wetlands','swamp','plains'}: z['resources']+=['river_trout_pool']
        if level>=40: z['resources']+=['relic_deposit']
        # Named landmarks carry world history and provide navigation anchors.
        for j,(suffix,label,style,dx,dy) in enumerate([
          ('watch','Old Watch Post','ruin',-26,-18),('shrine','Roadside Shrine','shrine',20,-24),('camp','Abandoned Camp','camp',-22,20),('mill','Broken Storehouse','ruin',26,22)]):
            z['buildings'].append(dict(id=ident+'_'+suffix,name=label,x=160+dx,y=160+dy,width=5+j%2,height=4+j%2,style=style,station=''))
        zones.append(z); by_id[ident]=z
    for i,(ident,*_) in enumerate(REGIONS):
        a=by_id[ident]
        if i%5<4: connect(a,by_id[REGIONS[i+1][0]],(317.5,160.5),(2.5,160.5))
        if i//5<3: connect(a,by_id[REGIONS[i+5][0]],(160.5,317.5),(160.5,2.5))
    # Each capital uses its own city layout instead of a duplicated block plan.
    plans={
      'dawnreach':[(48,49),(72,49),(48,73),(72,73),(40,60),(82,60),(59,40),(59,83)],
      'emberhold':[(42,45),(53,45),(74,45),(85,45),(42,76),(53,76),(74,76),(85,76)],
      'thornhollow':[(47,44),(73,44),(39,57),(82,57),(45,75),(75,75),(59,34),(59,87)],
      'frostgate':[(39,45),(49,45),(72,45),(82,45),(39,77),(49,77),(72,77),(82,77)],
      'gloamport':[(43,48),(56,43),(74,48),(44,73),(59,79),(77,71),(33,61),(85,58)]
    }
    for city_index,(ident,name,parent,biome,level,faction,style,lore) in enumerate(CITIES):
        z=zone(ident,name,biome,level,'city',size=128,seed=1400+city_index*71,world_x=by_id[parent]['worldX'],world_y=by_id[parent]['worldY'],lore=lore)
        zones.append(z); by_id[ident]=z
        connect(by_id[parent],z,(160.5,148.5),(64.5,119.5),'gate')
        for i,(x,y) in enumerate(plans[ident]):
            role,service,station,_=ROLES[i]
            building=dict(id=ident+'_building_'+str(i),name=service,x=x,y=y,width=7,height=5,style=style,station=station)
            z['buildings'].append(building)
            # Building interiors have a physical door and a reciprocal return exit.
            interior=zone(building['id']+'_inside',name+' '+service,biome,level,'interior','Surface',32,seed=z['seed']+i,lore='A working '+service.lower()+' in '+name+'.')
            zones.append(interior); by_id[interior['id']]=interior
            connect(z,interior,(x+3.5,y+4.5),(16.5,27.5),'door')
        for i in range(len(ROLES)):
            # Services line the central streets. No NPC is placed inside solid masonry.
            if i<13: location=(64.5,37.5+i*2)
            else: location=(37.5+(i-13)*2,64.5)
            # These authored halls overlap the nominal service cross. Place staff
            # beside the walls rather than relying on roads to erase masonry.
            service_positions={
                'dawnreach':{2:(67.5,41.5),3:(67.5,43.5),15:(41.5,66.5),17:(45.5,66.5)},
                'thornhollow':{0:(67.5,37.5)},
                'gloamport':{13:(37.5,67.5),14:(39.5,67.5)}
            }
            location=service_positions.get(ident,{}).get(i,location)
            add_npc(data,z,i,i,faction,location)
    starter=zone('wayfarers_rest',"Wayfarer's Rest",'plains',1,'settlement',size=80,seed=107,lore='A fortified roadside village where displaced travelers rebuild their lives.')
    starter['species']=['field_rat','wild_hare']; starter['resources']=['copper_vein','oak_tree','meadow_leaf_patch','berry_bush','flax_patch','river_trout_pool','buried_pottery']
    for i,(name,x,y) in enumerate([('The Lantern Hearth',25,28),('Wayfarer Forge',46,28),('Travelers\' Store',25,48),('Mara\'s Workshop',46,48)]):
        starter['buildings'].append(dict(id='starter_building_'+str(i),name=name,x=x,y=y,width=7,height=5,style='cottage',station=''))
    zones.insert(0,starter); by_id[starter['id']]=starter
    connect(starter,by_id['kingsmeadow'],(76.5,40.5),(130.5,160.5),'road')
    for i,role_index in enumerate([11,0,4,15,16,14,13,17,5,24]): add_npc(data,starter,role_index,i,'wayfarers',(40.5,26.5+i*2))
    for i,(ident,name,parent) in enumerate(SETTLEMENTS):
        root=by_id[parent]; z=zone(ident,name,root['biome'],root['level'],'settlement',size=80,seed=1900+i*31,world_x=root['worldX'],world_y=root['worldY'],lore=name+' maintains a sheltered stop along the regional supply road.')
        for j in range(4): z['buildings'].append(dict(id=ident+'_house_'+str(j),name=['Inn','Market','Workshop','Watch House'][j],x=25 if j%2==0 else 48,y=26 if j<2 else 49,width=6,height=5,style='cottage',station=''))
        zones.append(z); by_id[ident]=z; connect(root,z,(142.5,160.5),(40.5,75.5),'road')
        for j,role_index in enumerate([11,4,25]): add_npc(data,z,role_index,j,'wayfarers',(40.5,34.5+j*3))
    for i,(ident,name,parent,layer,biome,boss_id) in enumerate(DUNGEONS):
        boss=next(x for x in data['mobs'] if x['id']==boss_id)
        z=zone(ident,name,biome,boss['level'],'dungeon',layer,96,seed=2300+i*53,world_x=by_id[parent]['worldX'],world_y=by_id[parent]['worldY'],lore=boss['lore'])
        z['boss']=boss_id
        z['species']=[x['id'] for x in data['mobs'] if x['biome']==biome and not x['boss'] and not x['elite']][:4]
        material=max((row for row in MATERIALS if row[2]<=boss['level']),key=lambda row:row[2])
        z['resources']=[material[0]+'_vein','buried_pottery']+(['relic_deposit'] if boss['level']>=40 else [])
        zones.append(z); by_id[ident]=z
        connect(by_id[parent],z,(160.5,174.5+(i%3)*4),(48.5,88.5),'stairs',max(1,boss['level']//3))
    # The Deepways are a connected underground route, not isolated menus.
    for i,(city_id,city_name,*_) in enumerate(CITIES):
        z=zone(city_id+'_deepway',city_name+' Deepway','crystal' if i==1 else 'fungal' if i==2 else 'ruins',12+i*8,'tunnel','Deepways',128,seed=4100+i*37,lore='An old service tunnel links the city to the roads below Kairnfall.')
        z['resources']=['iron_vein','buried_pottery']; z['species']=['armored_skeleton'] if i>2 else ['field_rat','wood_spider']
        # Thornhollow's southern hall occupies the central column at y=88.
        city_stairs=(67.5,88.5) if city_id=='thornhollow' else (64.5,88.5)
        zones.append(z); by_id[z['id']]=z; connect(by_id[city_id],z,city_stairs,(64.5,118.5),'stairs')
        if i>0: connect(by_id[CITIES[i-1][0]+'_deepway'],z,(118.5,64.5),(8.5,64.5),'tunnel')
    umbral=zone('umbral_crossroads','Umbral Crossroads','fungal',60,'tunnel','Umbral Depths',128,seed=5501,lore='Mushroom light illuminates roads cut through the remains of buried workshops.')
    umbral['resources']=['cobalt_vein','relic_deposit']; umbral['species']=['myconid_stalker','lantern_fungus','hollow_centipede']
    zones.append(umbral); by_id[umbral['id']]=umbral; connect(by_id['emberhold_deepway'],umbral,(64.5,20.5),(64.5,118.5),'lift',20)
    for dungeon_id in ['regents_tomb','chorus_caverns','winterhorn_pass','rime_abbey','cinder_barracks','reef_sanctum','hollow_throne']:
        target=by_id[dungeon_id]; offset=len(umbral['exits'])*5
        connect(umbral,target,(20.5+offset,64.5),(48.5,8.5),'tunnel',20)
    aether=zone('aether_crossing','Aether Crossing','arcane_anomaly',85,'tunnel','Aether Rift',128,seed=7703,lore='A fractured transit hall reveals the true purpose of the old world engine.')
    aether['resources']=['obsidian_vein','relic_deposit']; aether['species']=['arcane_sentinel','rift_manta','spell_wisp']
    zones.append(aether); by_id[aether['id']]=aether; connect(umbral,aether,(64.5,12.5),(64.5,118.5),'portal',35)
    for i,dungeon_id in enumerate(['prism_observatory','unwritten_library','engine_of_dawn']): connect(aether,by_id[dungeon_id],(40.5+i*12,64.5),(48.5,8.5),'portal',35)
    # Ensure every gathered resource has at least one real node in the connected world.
    assigned={r for z in zones for r in z['resources']}
    for resource in data['resources']:
        if resource['id'] in assigned or resource['id'] in {'animal_carcass','wheat_crop','meteor_ore'}: continue
        candidates=[z for z in zones if z['kind'] in {'wilderness','dungeon'} and z['level']>=max(1,resource['requirement']-10)]
        if not candidates: candidates=[by_id['engine_of_dawn']]
        target=min(candidates,key=lambda z:abs(z['level']-resource['requirement']))
        target['resources'].append(resource['id'])
