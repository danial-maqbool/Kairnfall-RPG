"""World topology and creature ecology. Generated terrain is not an art approval."""
from __future__ import annotations
from content_rules import slug

# Name, biome, recommended skill level, world-grid X/Y, local history.
REGIONS = [
 ("Goldenfields","farmland",1,0,0,"Windmills and irrigation channels supply Dawnreach. The western watchtower has stopped answering its bell."),
 ("Old King's Road","plains",5,1,0,"Milestones from three dynasties stand beside a road that no king now maintains."),
 ("Miller's Reach","farmland",3,-1,1,"A flooded mill blocks the grain route. Tracks lead from its broken sluice into the reeds."),
 ("Middleshade","forest",8,0,-1,"Carved trail posts mark the boundary between royal logging rights and the forest circle."),
 ("Ashen Copse","forest",12,-1,-1,"One hillside burned without lightning. Young shoots grow around stones that remain warm at night."),
 ("Greenveil","ancient_forest",20,-2,-2,"Raised root bridges cross a forest floor that has not seen direct sunlight for generations."),
 ("Hartwood","ancient_forest",28,-3,-2,"The forest wardens leave empty bowls beneath an antlered shrine. Something empties them before dawn."),
 ("Thorn Basin","ancient_forest",38,-3,-3,"Living thorns seal old survey cuts. The water below carries traces of a forgotten alchemical spill."),
 ("Pinewatch Trail","pine_forest",25,-1,-3,"Northern trappers maintain wind shelters along a narrow pine ridge."),
 ("Whitebark Vale","pine_forest",35,0,-4,"Heavy snow has bent the whitebark trees into archways. An abandoned signal line climbs the eastern slope."),
 ("Northwind Steppe","tundra",45,1,-4,"Stone cairns guide travelers when blowing snow hides every distant landmark."),
 ("Mammoth March","tundra",55,2,-5,"Broad migration tracks cross a frozen river. Northern hunters refuse to camp inside the old bone circle."),
 ("Mirror Glacier","glacier",65,3,-5,"Blue ice preserves the roofs of a settlement lost before Frostgate was built."),
 ("Frozen Crown","glacier",80,4,-5,"Broken towers protrude from the summit ice. Their bells move when the air is still."),
 ("Ironroad","highlands",15,2,0,"Ore carts cut deep grooves in the paving. Forge-clan tollhouses guard each narrow bridge."),
 ("Redstone Pass","mountains",25,3,0,"Ochre cliffs conceal abandoned adits and a staircase cut for workers, not armies."),
 ("Rookspine","mountains",40,4,-1,"Ravens nest in a ruined observatory above a chain of suspension bridges."),
 ("Cinder Valley","volcanic",55,5,0,"Basalt terraces channel hot water into the forge city's cooling reservoirs."),
 ("Glass Wastes","volcanic",70,6,1,"A past eruption fused sand into dark sheets. Footsteps ring across the shallow glass basins."),
 ("Molten Stair","volcanic",85,6,-1,"Stone ramps follow a cooled lava fall toward a sealed forge beneath the caldera."),
 ("Copper Flats","badlands",25,3,2,"Green mineral seams cross dry washes. Survey stakes mark deposits whose owners never returned."),
 ("Saffron Ravine","badlands",45,4,3,"The ravine holds a ruined caravanserai and wells covered by heavy stone lids."),
 ("Reedfen","wetlands",10,1,2,"Raised causeways link fishing huts above the flooded fields."),
 ("Willowwater","wetlands",20,0,3,"Willow roots hold fragments of an older stone quay. Ferrymen follow a route the maps omit."),
 ("Blackroot Mire","swamp",35,-1,4,"Peat-cutting trenches surround a chapel whose floor lies below the water table."),
 ("Lantern Marsh","swamp",50,0,5,"Harbor pilots hang colored lamps over safe channels. Unlit boats drift between them."),
 ("Saltwind Strand","coast",20,2,3,"Salt, driftwood, and wrecked fishing gear gather beneath the harbor cliffs."),
 ("Tidebreak Cliffs","coast",35,3,4,"A lighthouse stands above caves accessible through the cliff road."),
 ("Gull Islands","archipelago",45,4,5,"Ferry landings connect low islands, shell beaches, and pirate lookouts."),
 ("Stormhook Isle","archipelago",65,5,5,"A wrecked warship forms a bridge between two rocky islands."),
 ("Hollow Battlefield","wasteland",40,2,-2,"Old trenches encircle a shattered banner pole. No faction claims the graves here."),
 ("Pilgrim's Desolation","wasteland",60,3,-3,"Empty shrines mark a pilgrimage that ended when the eastern sky changed color."),
 ("Moonlit Ruins","ruins",55,-2,1,"A roofless library surrounds a courtyard of weathered astronomical carvings."),
 ("The Broken Meridian","arcane",75,-3,2,"Survey instruments point toward a floating stone arch instead of north."),
 ("Starfall Heath","arcane",85,-4,2,"Fresh craters expose crystals among the heather after each arcane storm."),
 ("Cairn of First Light","ruins",95,-4,3,"The oldest waystone stands within a ring of collapsed arches. Its lower stairs lead into the earth."),
]
CITY_ROWS = [
 ("Dawnreach","plains",1,1,1,"stone","dawnreach_crown","The walled capital stands where the five old trade roads met. Its archives record a sixth road beneath the city."),
 ("Emberhold","mountains",25,4,0,"forge","forge_clans","Terraced foundries surround a basalt reservoir. Clan marks identify each furnace and ore lift."),
 ("Thornhollow","ancient_forest",20,-2,-3,"treehouse","thornhollow_circle","Living bridges connect workshops built around ancient trunks. No building cuts through a living root."),
 ("Frostgate","tundra",45,2,-4,"northern","frostgate_wardens","A sheltered stone keep protects a market of timber halls against the north wind."),
 ("Gloamport","coast",20,2,4,"harbor","gloamport_league","Warehouses, tide stairs, and old defensive walls crowd a harbor lit by blue pilot lamps."),
]
SETTLEMENTS = [
 ("Wayfarer's Rest","plains",1,"goldenfields",-1,0),
 ("Miller's Ford","farmland",3,"millers_reach",-2,1),
 ("Ashbridge","forest",12,"ashen_copse",-2,-1),
 ("Hart Refuge","ancient_forest",28,"hartwood",-4,-2),
 ("Pinewatch","pine_forest",25,"pinewatch_trail",-2,-4),
 ("Whitecairn","tundra",45,"northwind_steppe",0,-5),
 ("Redstone Camp","mountains",25,"redstone_pass",3,1),
 ("Cinderpost","volcanic",55,"cinder_valley",5,1),
 ("Reedmarket","wetlands",10,"reedfen",0,2),
 ("Willow Ferry","wetlands",20,"willowwater",-1,3),
 ("Saltwatch","coast",20,"saltwind_strand",2,2),
]
# Dungeon, entrance region, biome, layer, recommended level, boss, arena premise.
DUNGEONS = [
 ("Old Watchtower Cellar","goldenfields","ruins","Deepways",5,"The Bellkeeper","A brass alarm frame controls the cellar's sealed doors."),
 ("Dawnreach Sewers","dawnreach","swamp","Deepways",12,"Grate Maw","Collapsed sluices divide the underground waterworks."),
 ("Widow's Hollow","middleshade","forest","Deepways",18,"Silk Matriarch","Webbed galleries meet in a chamber beneath the root bridge."),
 ("Rootbound Sanctuary","thornhollow","ancient_forest","Deepways",25,"Elder Bramble","Stone channels feed an ancient root system."),
 ("The Sunken Chapel","blackroot_mire","swamp","Deepways",35,"Sister Mire","A flooded nave hides a dry crypt under its raised altar."),
 ("Emberhold Lower Mine","emberhold","mountains","Deepways",30,"Foreman Irongrief","Broken ore lifts surround a furnace that has remained lit."),
 ("The Brass Vault","redstone_pass","ruins","Deepways",40,"The Brass Auditor","Counterweighted gates divide an abandoned coin foundry."),
 ("Rookspine Observatory","rookspine","arcane","Deepways",45,"The Hollow Astronomer","A fallen telescope points through the floor into a crystal chamber."),
 ("Fungal Hollow","greenveil","fungal","Deepways",35,"Spore Regent","Giant fungal shelves bridge a deep underground stream."),
 ("Crystal Resonance","whitebark_vale","crystal","Deepways",50,"The Glass Choir","Tuned crystal pillars surround a buried circular hall."),
 ("Frostgate Burial Halls","frostgate","glacier","Umbral Depths",55,"Jarl Without Dawn","Stone burial boats rest below the fortress foundations."),
 ("The Blue Sepulcher","mirror_glacier","glacier","Umbral Depths",65,"Icebound Herald","Preserved streets descend into a frozen ceremonial hall."),
 ("Ashen Crucible","cinder_valley","volcanic","Umbral Depths",60,"Cinder Colossus","Casting channels converge around a failed guardian mold."),
 ("Caldera Heart","molten_stair","volcanic","Umbral Depths",85,"Veyr the Furnace Wyrm","Ancient cooling gates surround a deep magma vent."),
 ("Gloamport Catacombs","gloamport","ruins","Deepways",30,"The Drowned Bailiff","Tide tunnels intersect a sealed archive of harbor debts."),
 ("Wreck of the Mourning Star","stormhook_isle","coast","Umbral Depths",65,"Captain Saltwraith","The broken keel rests inside a sheltered sea cavern."),
 ("The Bannerless Keep","hollow_battlefield","wasteland","Umbral Depths",55,"Marshal of Ash","Ruined barracks lead to a hall filled with unclaimed standards."),
 ("The Unwritten Archive","moonlit_ruins","arcane","Umbral Depths",70,"The Unnamed Scribe","Movable shelves circle an empty lectern and a sealed stair."),
 ("Meridian Rift","the_broken_meridian","arcane","Aether Rift",85,"The Meridian Engine","Suspended stone walkways join four displaced observatory rooms."),
 ("First Light Vault","cairn_of_first_light","crystal","Aether Rift",95,"Aster the Unbound","A ring of waystone cores encloses the original fracture."),
]

# Family, species name, biome, anatomy, AI, level, element. Names are not palette
# variants. Their asset completion is tracked separately from catalog coverage.
CREATURE_ROWS = [
 ("rat","Granary Rat","farmland","animal:rat","aggressive",1,"Physical"),
 ("boar","Bristle Boar","forest","animal:boar","territorial",5,"Physical"),
 ("wolf","Timber Wolf","forest","animal:wolf","pack",8,"Physical"),
 ("bear","Brown Bear","forest","animal:bear","territorial",14,"Physical"),
 ("deer","Red Deer","plains","animal:deer","fleeing",3,"Physical"),
 ("hare","Field Hare","farmland","animal:hare","passive",1,"Physical"),
 ("fox","Red Fox","plains","animal:fox","fleeing",4,"Physical"),
 ("badger","Bank Badger","forest","animal:badger","territorial",6,"Physical"),
 ("beaver","River Beaver","wetlands","animal:beaver","passive",8,"Physical"),
 ("otter","Reed Otter","wetlands","animal:otter","fleeing",7,"Physical"),
 ("lynx","Pine Lynx","pine_forest","animal:lynx","ambusher",25,"Physical"),
 ("wolverine","Ridge Wolverine","highlands","animal:wolverine","berserker",22,"Physical"),
 ("elk","Northern Elk","pine_forest","animal:elk","territorial",28,"Physical"),
 ("bison","Steppe Bison","tundra","animal:bison","territorial",42,"Physical"),
 ("mammoth","Woolly Mammoth","tundra","animal:mammoth","territorial",55,"Physical"),
 ("goat","Mountain Ibex","mountains","animal:ibex","passive",20,"Physical"),
 ("ram","Ironhorn Ram","highlands","animal:ram","territorial",25,"Physical"),
 ("leopard","Snow Leopard","glacier","animal:leopard","ambusher",48,"Frost"),
 ("seal","Harbor Seal","coast","animal:seal","passive",18,"Physical"),
 ("walrus","Tusked Walrus","glacier","animal:walrus","territorial",50,"Frost"),
 ("crocodile","Marsh Crocodile","swamp","animal:crocodile","ambusher",30,"Physical"),
 ("tortoise","Stoneback Tortoise","badlands","animal:tortoise","territorial",24,"Physical"),
 ("snake","Reed Viper","wetlands","animal:snake","ambusher",12,"Poison"),
 ("lizard","Ravine Monitor","badlands","animal:monitor","aggressive",32,"Poison"),
 ("frog","Bullfrog","swamp","animal:frog","territorial",14,"Poison"),
 ("newt","Ember Newt","volcanic","animal:newt","passive",42,"Fire"),
 ("crab","Rock Crab","coast","animal:crab","territorial",16,"Physical"),
 ("lobster","Tide Lobster","archipelago","animal:lobster","aggressive",35,"Physical"),
 ("hermit","Shell Hermit","coast","animal:hermit","territorial",18,"Physical"),
 ("octopus","Reef Octopus","archipelago","animal:octopus","ambusher",40,"Physical"),
 ("spider","Cellar Spider","ruins","arthropod:spider","ambusher",4,"Poison"),
 ("scorpion","Copper Scorpion","badlands","arthropod:scorpion","aggressive",25,"Poison"),
 ("beetle","Stag Beetle","forest","arthropod:beetle","territorial",8,"Physical"),
 ("mantis","Thorn Mantis","ancient_forest","arthropod:mantis","ambusher",24,"Physical"),
 ("wasp","Paper Wasp","farmland","arthropod:wasp","pack",5,"Poison"),
 ("dragonfly","Fen Dragonfly","wetlands","arthropod:dragonfly","ranged",15,"Nature"),
 ("centipede","Cave Centipede","fungal","arthropod:centipede","aggressive",35,"Poison"),
 ("moth","Lantern Moth","ancient_forest","arthropod:moth","caster",23,"Arcane"),
 ("ant","Soldier Ant","highlands","arthropod:ant","pack",18,"Physical"),
 ("snail","Moss Snail","fungal","arthropod:snail","territorial",28,"Nature"),
 ("bat","Cave Bat","ruins","animal:bat","pack",6,"Physical"),
 ("owl","Tawny Owl","forest","animal:owl","ambusher",9,"Physical"),
 ("raven","Carrion Raven","wasteland","animal:raven","pack",28,"Shadow"),
 ("gull","Storm Gull","coast","animal:gull","ranged",17,"Physical"),
 ("eagle","Crested Eagle","mountains","animal:eagle","ranged",32,"Physical"),
 ("vulture","Ravine Vulture","badlands","animal:vulture","pack",35,"Physical"),
 ("crane","Marsh Crane","wetlands","animal:crane","territorial",18,"Physical"),
 ("pelican","Harbor Pelican","coast","animal:pelican","passive",15,"Physical"),
 ("cockatrice","Briar Cockatrice","ancient_forest","chimera:cockatrice","caster",40,"Nature"),
 ("harpy","Cliff Harpy","mountains","chimera:harpy","ranged",45,"Physical"),
 ("goblin","Goblin Scrapper","plains","humanoid:goblin","aggressive",7,"Physical"),
 ("kobold","Kobold Sapper","mountains","humanoid:kobold","ranged",20,"Fire"),
 ("bandit","Road Cutpurse","plains","humanoid:bandit","ambusher",8,"Physical"),
 ("outlaw","Outlaw Arbalist","highlands","humanoid:crossbowman","ranged",18,"Physical"),
 ("raider","Marsh Reaver","swamp","humanoid:raider","berserker",28,"Poison"),
 ("pirate","Harbor Corsair","coast","humanoid:pirate","aggressive",25,"Physical"),
 ("smuggler","Smoke Smuggler","archipelago","humanoid:smuggler","fleeing",32,"Shadow"),
 ("cultist","Candle Cultist","ruins","humanoid:cultist","caster",22,"Fire"),
 ("necromancer","Grave Binder","wasteland","humanoid:necromancer","summoner",45,"Shadow"),
 ("apostate","Fallen Mender","ruins","humanoid:healer","healer",35,"Radiant"),
 ("skeleton","Ossuary Spearman","ruins","undead:skeleton","guard",15,"Physical"),
 ("zombie","Mirewalker","swamp","undead:zombie","aggressive",18,"Poison"),
 ("ghoul","Crypt Ghoul","ruins","undead:ghoul","berserker",28,"Shadow"),
 ("wraith","Veiled Wraith","wasteland","undead:wraith","caster",45,"Shadow"),
 ("ghost","Bell Ghost","ruins","undead:ghost","ranged",25,"Arcane"),
 ("revenant","Banner Revenant","wasteland","undead:revenant","guard",50,"Shadow"),
 ("mummy","Saltbound Mummy","badlands","undead:mummy","aggressive",40,"Poison"),
 ("dullahan","Headless Rider","wasteland","undead:dullahan","patrol",65,"Shadow"),
 ("banshee","Reed Banshee","swamp","undead:banshee","caster",48,"Shadow"),
 ("bone_serpent","Bone Serpent","crystal","undead:bone_serpent","ambusher",58,"Physical"),
 ("sprout","Walking Mandrake","forest","plant:mandrake","fleeing",10,"Nature"),
 ("vine","Strangler Vine","ancient_forest","plant:vine","ambusher",25,"Nature"),
 ("treant","Oak Sentinel","ancient_forest","plant:treant","guard",42,"Nature"),
 ("fungus","Spore Walker","fungal","plant:fungus","caster",32,"Poison"),
 ("bloom","Glasspetal Bloom","crystal","plant:bloom","ranged",50,"Arcane"),
 ("cactus","Needle Cactus","badlands","plant:cactus","ranged",35,"Physical"),
 ("rootling","Burrow Rootling","forest","plant:rootling","ambusher",20,"Nature"),
 ("slime","Well Slime","wetlands","amorphous:slime","aggressive",7,"Nature"),
 ("ooze","Tar Ooze","volcanic","amorphous:ooze","territorial",48,"Fire"),
 ("mimic","Chest Mimic","ruins","construct:mimic","ambusher",30,"Physical"),
 ("golem","Quarry Golem","mountains","construct:stone_golem","guard",40,"Physical"),
 ("automaton","Brass Surveyor","ruins","construct:automaton","patrol",45,"Lightning"),
 ("armor","Hollow Armor","ruins","construct:armor","guard",38,"Physical"),
 ("gargoyle","Chapel Gargoyle","ruins","construct:gargoyle","ambusher",45,"Physical"),
 ("crystal_golem","Prism Guardian","crystal","construct:crystal_golem","caster",65,"Arcane"),
 ("elemental","Cinder Elemental","volcanic","elemental:fire","caster",55,"Fire"),
 ("water_spirit","Tide Spirit","coast","elemental:water","healer",45,"Frost"),
 ("storm_spirit","Storm Wisp","arcane","elemental:lightning","ranged",60,"Lightning"),
 ("earth_spirit","Silt Guardian","wetlands","elemental:earth","territorial",35,"Physical"),
 ("ice_spirit","Glacier Shardling","glacier","elemental:ice","ranged",58,"Frost"),
 ("troll","Bridge Troll","highlands","giant:troll","berserker",35,"Physical"),
 ("ogre","Ridge Ogre","mountains","giant:ogre","aggressive",45,"Physical"),
 ("ettin","Two-headed Ettin","mountains","giant:ettin","territorial",60,"Physical"),
 ("yeti","Rime Yeti","tundra","giant:yeti","ambusher",65,"Frost"),
 ("wyvern","Rook Wyvern","mountains","dragon:wyvern","ranged",65,"Poison"),
 ("drake","Basalt Drake","volcanic","dragon:drake","territorial",70,"Fire"),
 ("basilisk","Cavern Basilisk","crystal","dragon:basilisk","caster",65,"Nature"),
 ("imp","Furnace Imp","volcanic","fiend:imp","ranged",48,"Fire"),
 ("fiend","Chain Fiend","wasteland","fiend:chain","aggressive",75,"Shadow"),
 ("aether_ray","Aether Ray","arcane","aberration:ray","caster",85,"Arcane"),
]


def make_mobs(items: list[dict]) -> list[dict]:
    mobs=[]
    for index,(family,name,biome,anatomy,ai,level,element) in enumerate(CREATURE_ROWS):
        ident=slug(name)
        is_animal=anatomy.startswith("animal:")
        drops=["raw_meat","hide_raw","animal_bait"] if is_animal else ["bone","arcane_dust","runestone"]
        if family in ("owl","raven","gull","eagle","vulture","crane","pelican","harpy"):
            drops=["feather","raw_meat","fang"]
        if anatomy.startswith("humanoid:"):
            drops=["healing_potion","lockpick","blank_paper"]
        if anatomy.startswith("construct:"):
            drops=["iron_ore","rough_gem","mechanism"]
        if anatomy.startswith("plant:"):
            drops=["sage","mushroom","linen_fiber"]
        if anatomy.startswith("arthropod:"):
            drops=["shell","nightshade","silk_fiber"]
        if family in ("rat","hare"):
            drops=["raw_meat","hide_raw","berry"]
        resist={element:0.25} if element!="Physical" else {}
        if element=="Fire": resist["Frost"]=-0.2
        if element=="Frost": resist["Fire"]=-0.2
        if element=="Shadow": resist["Radiant"]=-0.25
        mobs.append(dict(id=ident,name=name,family=family,biome=biome,anatomy=anatomy,
            sprite=f"res://Art/Mobs/{ident}.png",ai=ai,level=level,health=22+level*10,
            power=2+level*1.2,armor=level*0.45,speed=1.6+(index%5)*0.25,
            range=6 if ai in ("ranged","caster","healer") else 1.6,
            aggro=5 if ai not in ("passive","fleeing") else 0,gold=2+level*2,xp=15+level*12,
            element=element,resistances=resist,attacks=["basic","special"],drops=drops,
            lore=f"Native to {biome.replace('_',' ')}. Its {ai} behavior determines how it engages travelers."))
    # Elite variants are explicitly marked and excluded from the species count.
    for base in mobs[:25]:
        elite=dict(base)
        elite.update(id=base["id"]+"_elite",name="Veteran "+base["name"],elite=True,
                     health=base["health"]*2.2,power=base["power"]*1.4,gold=base["gold"]*3,xp=base["xp"]*3)
        mobs.append(elite)
    for index,(_,_,biome,_,level,name,lore) in enumerate(DUNGEONS):
        element={"volcanic":"Fire","glacier":"Frost","swamp":"Poison","arcane":"Arcane","wasteland":"Shadow","ancient_forest":"Nature","fungal":"Poison","crystal":"Arcane"}.get(biome,"Physical")
        ident=slug(name)
        mobs.append(dict(id=ident,name=name,family="boss",biome=biome,anatomy="boss:"+ident,
            sprite=f"res://Art/Bosses/{ident}.png",ai="boss",boss=True,level=level,
            health=250+level*45,power=8+level*1.6,armor=5+level*0.7,speed=1.7,
            range=2.5,aggro=12,gold=50+level*12,xp=150+level*40,element=element,
            resistances={element:0.2} if element!="Physical" else {},
            attacks=["telegraph_circle","telegraph_cone","phase_reinforcements"],
            drops=["rune_embers_1","rune_warding_1","rough_gem","carved_idol"],lore=lore))
    assert len([m for m in mobs if not m.get("elite") and not m.get("boss")]) == 100
    return mobs


def build_world(mobs: list[dict], resources: list[dict], items: list[dict]) -> tuple[list[dict],list[dict]]:
    zones=[]
    by_id={}
    def zone(ident,name,biome,level,x,y,kind="wilderness",layer="Surface",lore="",size=224):
        z=dict(id=ident,name=name,biome=biome,level=level,worldX=x,worldY=y,kind=kind,layer=layer,lore=lore,
               width=size,height=size,seed=1009+len(zones)*7919,spawn={"x":size//2,"y":size//2},
               exits=[],buildings=[],species=[],resources=[],boss="")
        zones.append(z); by_id[ident]=z
        if kind=="wilderness":
            candidates=[m for m in mobs if not m.get("boss") and not m.get("elite") and m["biome"]==biome]
            z["species"]=[m["id"] for m in candidates]
            z["resources"]=[r["id"] for r in resources if r["requirement"]<=level+10 and r["requirement"]>=max(1,level-30) and r["skill"]!="skinning"][:10]
        return z
    for name,biome,level,x,y,lore in REGIONS:
        zone(slug(name),name,biome,level,x,y,lore=lore)
    for name,biome,level,x,y,style,faction,lore in CITY_ROWS:
        z=zone(slug(name),name,biome,level,x,y,"city",lore=lore,size=144)
        z["style"]=style; z["faction"]=faction
        # City layouts differ by district arrangement, block proportions, and
        # building styles. Main approach lanes stay clear for collision tests.
        for i in range(12):
            column=i%4; row=i//4
            bx=22+column*26; by=23+row*34
            if style=="harbor": bx+=row*3; by+=column%2*3
            elif style=="treehouse": bx+=(-1 if row%2 else 1)*5; by+=column%2*5
            elif style=="forge": bx+=column%2*3
            elif style=="northern": by+=row%2*5
            if abs(bx-72)<8: bx+=12
            if abs(by-72)<8: by+=12
            z["buildings"].append(dict(id=f"{z['id']}_building_{i}",name=["Market Hall","Forge","Lodge","Archive"][column],x=bx,y=by,width=9+(i%3)*2,height=7+(i%2)*2,style=style,station=""))
    for name,biome,level,parent,x,y in SETTLEMENTS:
        ident="wayfarers_rest" if name=="Wayfarer's Rest" else slug(name)
        z=zone(ident,name,biome,level,x,y,"settlement",lore="A staffed refuge on the road to "+by_id[parent]["name"]+".",size=96)
        for i,(bx,by) in enumerate([(27,30),(54,30),(27,58),(54,58)]):
            z["buildings"].append(dict(id=f"{ident}_building_{i}",name=["Inn","Workshop","Store","Guild Shelter"][i],x=bx,y=by,width=9,height=7,style="cottage",station=""))
        z["resources"]=["copper_vein","ash_tree","river_shoal","sage_plant","linen_patch","berry_patch","coal_seam","buried_pottery"]
        z["species"]=["granary_rat","field_hare"] if ident=="wayfarers_rest" else []

    def connect(a,b,kind="road",level=1):
        za,zb=by_id[a],by_id[b]
        # Place each entrance on a distinct spoke. Exit lanes are cleared by
        # WorldMap; use interior points, never an impassable boundary tile.
        def pos(z,index):
            c=z["width"]//2; d=min(22,c-8)
            offsets=[(-d,0),(d,0),(0,-d),(0,d),(-d,-d),(d,d),(-d,d),(d,-d)]
            dx,dy=offsets[index%len(offsets)]
            return {"x":c+dx,"y":c+dy}
        pa=pos(za,len(za["exits"])); pb=pos(zb,len(zb["exits"]))
        za["exits"].append(dict(id=a+"_to_"+b,target=b,position=pa,arrival=pb,kind=kind,requirement=level))
        zb["exits"].append(dict(id=b+"_to_"+a,target=a,position=pb,arrival=pa,kind=kind,requirement=level))

    for a,b in [
        ("goldenfields","old_kings_road"),("goldenfields","millers_reach"),("goldenfields","middleshade"),
        ("middleshade","ashen_copse"),("ashen_copse","greenveil"),("greenveil","hartwood"),("hartwood","thorn_basin"),
        ("greenveil","pinewatch_trail"),("pinewatch_trail","whitebark_vale"),("whitebark_vale","northwind_steppe"),
        ("northwind_steppe","mammoth_march"),("mammoth_march","mirror_glacier"),("mirror_glacier","frozen_crown"),
        ("old_kings_road","ironroad"),("ironroad","redstone_pass"),("redstone_pass","rookspine"),
        ("redstone_pass","cinder_valley"),("cinder_valley","glass_wastes"),("cinder_valley","molten_stair"),
        ("ironroad","copper_flats"),("copper_flats","saffron_ravine"),
        ("old_kings_road","reedfen"),("reedfen","willowwater"),("willowwater","blackroot_mire"),
        ("blackroot_mire","lantern_marsh"),("reedfen","saltwind_strand"),("saltwind_strand","tidebreak_cliffs"),
        ("tidebreak_cliffs","gull_islands"),("gull_islands","stormhook_isle"),("lantern_marsh","saltwind_strand"),
        ("ironroad","hollow_battlefield"),("hollow_battlefield","pilgrims_desolation"),("pilgrims_desolation","northwind_steppe"),
        ("ashen_copse","moonlit_ruins"),("moonlit_ruins","the_broken_meridian"),("the_broken_meridian","starfall_heath"),
        ("starfall_heath","cairn_of_first_light"),("moonlit_ruins","millers_reach"),("saffron_ravine","tidebreak_cliffs"),
        ("dawnreach","old_kings_road"),("emberhold","redstone_pass"),("thornhollow","greenveil"),
        ("frostgate","northwind_steppe"),("gloamport","saltwind_strand"),
    ]: connect(a,b,"ferry" if "island" in b or "isle" in b else "road")
    for name,_,_,parent,_,_ in SETTLEMENTS:
        connect("wayfarers_rest" if name=="Wayfarer's Rest" else slug(name),parent)
    for name,parent,biome,layer,level,boss,lore in DUNGEONS:
        ident=slug(name); p=by_id[parent]
        z=zone(ident,name,biome,level,p["worldX"],p["worldY"],"dungeon",layer,lore,size=128)
        z["boss"]=slug(boss)
        z["species"]=[m["id"] for m in mobs if not m.get("boss") and not m.get("elite") and m["biome"] in (biome,"ruins") and abs(m["level"]-level)<22][:10]
        z["resources"]=[r["id"] for r in resources if r["skill"] in ("mining","excavation") and level-25<=r["requirement"]<=level+5][:6]
        connect(parent,ident,"portal" if layer=="Aether Rift" else "stairs")
    # Underground links create routes, not just isolated menu dungeons.
    for a,b in [("dawnreach_sewers","old_watchtower_cellar"),("rootbound_sanctuary","fungal_hollow"),
                ("emberhold_lower_mine","the_brass_vault"),("frostgate_burial_halls","the_blue_sepulcher"),
                ("ashen_crucible","caldera_heart"),("gloamport_catacombs","the_sunken_chapel"),
                ("the_unwritten_archive","meridian_rift"),("meridian_rift","first_light_vault")]:
        connect(a,b,"passage")

    # Walk-in interiors. The doorway is represented by the normal transition
    # protocol; the client renders it as a door, never a disconnected map menu.
    for name,_,_,_,_,style,_,_ in CITY_ROWS:
        city=by_id[slug(name)]
        interior=zone(city["id"]+"_guildhall",name+" Guildhall",city["biome"],city["level"],city["worldX"],city["worldY"],"interior","Surface","The city guild keeps its records and public commissions here.",size=48)
        interior["style"]=style
        connect(city["id"],interior["id"],"door")

    roles=[("blacksmith","anvil"),("armorer","anvil"),("weapon_merchant",""),("fletcher","fletching_bench"),
           ("provisioner","cooking_fire"),("alchemist","alchemy_table"),("rune_merchant","rune_table"),
           ("enchanter","enchanting_table"),("jeweler","jewelers_bench"),("banker",""),("auctioneer",""),
           ("innkeeper","cooking_fire"),("guild_registrar",""),("tailor","loom"),("leatherworker","tannery"),
           ("carpenter","workbench"),("scribe","scribing_desk"),("trainer",""),("guard",""),("scholar","")]
    given="Mara|Osric|Elin|Bram|Sera|Tovin|Ilya|Garran|Nessa|Rowan|Ysra|Corin|Halla|Darin|Vera|Perrin|Maela|Oran|Lysa|Tarn|Asha|Rurik|Fenn|Isolde|Kellan|Mira|Tor|Anwen|Jory|Selene|Della|Borin|Neris|Calder|Edda|Faris|Greta|Hadrin|Ines|Jalen".split("|")
    surnames=["Vale","Emberwell","Thornward","Snowcrest","Tideford","Reed","Ashgrove","Stonehand"]
    npcs=[]
    item_ids={i["id"] for i in items}
    def stock(role,level):
        if role in ("banker","auctioneer","guild_registrar","guard","scholar","trainer"): return []
        if role=="provisioner": return ["healing_potion","mana_potion","bread","wheat_seed","animal_bait","lockpick","blank_paper"]
        allowed={"blacksmith":["weapon","tool"],"armorer":["armor","offhand"],"weapon_merchant":["weapon"],
                 "fletcher":["weapon"],"alchemist":["potion"],"rune_merchant":["rune"],"enchanter":["rune"],
                 "jeweler":["accessory"],"innkeeper":["food"],"tailor":["armor"],"leatherworker":["armor"],
                 "carpenter":["tool","structure"],"scribe":["book","map","material"]}.get(role,[])
        candidates=[i for i in items if i["type"] in allowed and i["requirement"]<=level+10]
        if role=="fletcher": candidates=[i for i in candidates if "bow" in i["tags"] or "crossbow" in i["tags"]]
        if role=="tailor": candidates=[i for i in candidates if "light" in i["tags"]]
        if role=="leatherworker": candidates=[i for i in candidates if "medium" in i["tags"]]
        return [i["id"] for i in candidates[:30]]
    settlements=[z for z in zones if z["kind"] in ("city","settlement")]
    for zi,z in enumerate(settlements):
        service_roles=roles if z["kind"]=="city" else (roles[:6]+[roles[9],roles[11],roles[15],roles[16],roles[17],roles[19]])
        for ri,(role,station) in enumerate(service_roles):
            n=len(npcs); c=z["width"]//2
            # Keep service positions on the clear central road and away from
            # buildings. Distributed along both axes within walking distance.
            side=-1 if ri%2==0 else 1
            offset=4+(ri//4)*3
            x=c+side*offset if ri%4<2 else c+side
            y=c+side if ri%4<2 else c+side*offset
            ident=z["id"]+"_"+role
            display=given[n%len(given)]+" "+surnames[zi%len(surnames)]
            dialogue={"banker":"Deposits stay in your bank after you leave the realm.",
                      "blacksmith":"Ore becomes ingots here. Weapons also need sound wood and leather grips.",
                      "trainer":"Your overall level follows the experience earned by individual skills. A different profession still advances your character.",
                      "rune_merchant":"A socket holds one rune. An enchanter can remove it without destroying your equipment.",
                      "auctioneer":"Listed items leave your inventory. A completed purchase transfers the item and gold together.",
                      "innkeeper":"Food helps on the road. Rest here when combat is behind you.",
                      "scribe":"Carry blank paper. Charting a place twice does not create new knowledge.",
                      "scholar":z["lore"]}.get(role,"My work supports the people of "+z["name"]+". Ask about local commissions before you leave.")
            npcs.append(dict(id=ident,name=display,role=role,zone=z["id"],faction=z.get("faction","wayfarers"),
                position={"x":x,"y":y},dialogue=dialogue,stock=stock(role,z["level"]),station=station,
                sprite=f"res://Art/Npcs/{role}.png"))
    assert all(s in item_ids for n in npcs for s in n["stock"])
    return zones,npcs
