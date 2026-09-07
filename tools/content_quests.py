"""Quest records with executable objective types and explicit prerequisite chains."""
from __future__ import annotations
from content_rules import slug
from content_world import CITY_ROWS, DUNGEONS, SETTLEMENTS


def build_quests(zones: list[dict], npcs: list[dict], classes: list[dict]) -> list[dict]:
    quests=[]
    def objective(action,target,count=1,text=""):
        return dict(action=action,target=target,count=count,description=text or f"{action.replace('_',' ').title()}: {target.replace('_',' ')} ({count}).")
    def add(ident,name,giver,story,objectives,category="side",prerequisite="",gold=25,reward="",repeat=False):
        npc=next(n for n in npcs if n["id"]==giver)
        quests.append(dict(id=ident,name=name,giver=giver,story=story,category=category,
            prerequisite=prerequisite,faction=npc["faction"],objectives=objectives,gold=gold,reward=reward,repeatable=repeat))
    main_rows=[
        ("A Name on the Register","wayfarers_rest_trainer","The Wayfarers Guild records every traveler before the western gate opens. Meet the village smith and learn who keeps the roads supplied.",[objective("talk","wayfarers_rest_blacksmith")],"bread"),
        ("Ore for the Road","wayfarers_rest_blacksmith","The watchtower's spare fittings are gone. Extract three pieces of copper ore from the village deposit.",[objective("gather","copper_ore",3)],"healing_potion"),
        ("The First Ingot","wayfarers_rest_blacksmith","Raw stone cannot hold a gate hinge. Refine your copper at the smith's anvil.",[objective("craft","copper_ingot")],"ash_log"),
        ("Sound Timber","wayfarers_rest_carpenter","The guild needs wood that will not split at the grip. Cut ash and prepare a pair of planks at the workbench.",[objective("gather","ash_log",2),objective("craft","ash_plank",2)],"hide_leather"),
        ("An Edge of Your Own","wayfarers_rest_blacksmith","A road weapon needs metal, timber, and a bound grip. Forge a copper sword. You may keep your class weapon equipped.",[objective("craft","copper_sword")],"rune_warding_1"),
        ("Carved Power","wayfarers_rest_trainer","The mark on your starter weapon is an empty rune socket. Insert a rune and inspect the resulting statistics.",[objective("socket","*")],"healing_potion"),
        ("Below the Grain Bins","wayfarers_rest_provisioner","Rats have entered the grain store from the western ditch. Clear three without attacking the village's harmless wildlife.",[objective("kill","granary_rat",3)],"bread"),
        ("Provisions Before Pride","wayfarers_rest_innkeeper","The road has no dining hall. Collect wild berries and buy a loaf for the journey.",[objective("gather","berry",2),objective("buy","bread")],"blank_paper"),
        ("The Silent Milestone","wayfarers_rest_scholar","The Goldenfields watch bell has not rung for two nights. Find the road beyond the village and return with your observations.",[objective("explore","goldenfields")],"field_journal"),
        ("The Bell Beneath the Hill","wayfarers_rest_trainer","The tower itself is empty. Its keeper may have followed the mechanism into the cellar.",[objective("explore","old_watchtower_cellar"),objective("kill","the_bellkeeper")],"watchtower_key"),
        ("A Road to Dawnreach","wayfarers_rest_scholar","The bell's markings match an old royal survey. Follow the King's Road to Dawnreach.",[objective("explore","dawnreach")],"sealed_dispatch"),
        ("The Sixth Road","dawnreach_scholar","The dispatch refers to a road beneath the capital. Speak with the registrar and inspect the sewer entrance.",[objective("talk","dawnreach_guild_registrar"),objective("explore","dawnreach_sewers")],"mana_potion"),
        ("Water Under Stone","dawnreach_guard","A creature has blocked the lower sluice. Clear the obstruction so workers can reach the old paving.",[objective("kill","grate_maw")],"rune_precision_1"),
        ("A Living Boundary","dawnreach_scholar","The lower road points toward a forest shrine. The circle at Thornhollow may know why the crown sealed it.",[objective("explore","thornhollow"),objective("talk","thornhollow_scholar")],"cut_emerald"),
        ("Roots Remember","thornhollow_scholar","The sanctuary roots have grown through a waystone conduit. Enter the sanctuary and confront its guardian.",[objective("explore","rootbound_sanctuary"),objective("kill","elder_bramble")],"rune_thorns_2"),
        ("Marks of the Forge Clans","thornhollow_scholar","The conduit carries forge-clan stamps. Take the old trade route to Emberhold and consult its smith.",[objective("explore","emberhold"),objective("talk","emberhold_blacksmith")],"steel_ingot"),
        ("The Unclosed Shift","emberhold_blacksmith","A foreman refused to abandon the lower mine. His last shift has continued for a century.",[objective("explore","emberhold_lower_mine"),objective("kill","foreman_irongrief")],"rune_bulwark_2"),
        ("Debts of the Harbor","emberhold_scholar","Shipping ledgers sent the missing waystone cores to Gloamport. Ask the harbor guild where the cargo went.",[objective("explore","gloamport"),objective("talk","gloamport_guild_registrar")],"treasure_map"),
        ("The Drowned Record","gloamport_scholar","A bailiff sealed the cargo records below the tide stairs. Recover the route by reaching the catacombs and ending his watch.",[objective("explore","gloamport_catacombs"),objective("kill","the_drowned_bailiff")],"rune_dusk_2"),
        ("North of the Last Cairn","gloamport_scholar","The final shipment crossed the frozen road. Frostgate keeps the names of every convoy that reached its gates.",[objective("explore","frostgate"),objective("talk","frostgate_scholar")],"frostpetal"),
        ("A Jarl Without Dawn","frostgate_guard","The old jarl ordered the shipment buried beneath his keep. Enter the halls and break the oath that binds him.",[objective("explore","frostgate_burial_halls"),objective("kill","jarl_without_dawn")],"rune_winter_3"),
        ("An Archive Without Names","frostgate_scholar","Five fragments describe the same fracture. The missing account lies under the Moonlit Ruins.",[objective("explore","the_unwritten_archive"),objective("kill","the_unnamed_scribe")],"rune_focus_4"),
        ("The Broken Meridian","dawnreach_scholar","The archive describes a machine built to join distant waystones. Its failed alignment still distorts the western heath.",[objective("explore","meridian_rift"),objective("kill","the_meridian_engine")],"rune_aether_4"),
        ("Before the First Light","dawnreach_scholar","The original vault lies below the oldest cairn. Record its location before confronting what the machine released.",[objective("explore","cairn_of_first_light"),objective("explore","first_light_vault")],"royal_healing_potion"),
        ("Aster Unbound","dawnreach_guild_registrar","Aster holds the fracture open. Close the account that joined the five cities in silence.",[objective("kill","aster_the_unbound")],"rune_warding_5"),
    ]
    previous=""
    for index,(name,giver,story,objectives,reward) in enumerate(main_rows):
        ident=f"main_{index+1:02d}"
        add(ident,name,giver,story,objectives,"main",previous,30+index*25,reward)
        previous=ident

    # Each city has ten local stories. The objectives mix professions, travel,
    # dialogue, supplies, and combat. These are not escort or puzzle claims.
    city_stories={
      "dawnreach":[
        ("A Mill Without Bread","provisioner","Floodwater stopped the mill. Bring wheat and bread while the wheel is repaired.",[("deliver","wheat",5),("craft","bread",2)]),
        ("The Bent Gate Pin","blacksmith","The north gate drags against its lower pin. Forge replacement copper and inspect the guard's fitting list.",[("craft","copper_ingot",2),("talk","dawnreach_guard",1)]),
        ("Surveyor's Missing Page","scribe","The royal survey skips Miller's Reach. Visit the mill road and bring blank paper for a corrected copy.",[("explore","millers_reach",1),("deliver","blank_paper",3)]),
        ("A Stitch for the Watch","tailor","Watch cloaks tear at the shoulder seam. Sew a linen cloak before the next patrol leaves.",[("craft","linen_cloak",1)]),
        ("The Copper Measure","jeweler","Counterfeit weights entered the market. Refine two ingots so the jeweler can cast a verified measure.",[("craft","copper_ingot",2)]),
        ("Tracks at the Tollhouse","guard","Travelers report a cutpurse who waits near the old milestones. End the ambushes on the road.",[("kill","road_cutpurse",4)]),
        ("A Book That Survives Rain","scribe","Loose notes rot in saddle bags. Bind a field journal with leather and prepared paper.",[("craft","field_journal",1)]),
        ("Below the Market","scholar","The market drains follow masonry older than the city. Explore the sewers and report to the smith.",[("explore","dawnreach_sewers",1),("talk","dawnreach_blacksmith",1)]),
        ("Medicine for the East Road","alchemist","The east-road patrol has exhausted its field medicine. Brew healing draughts rather than buying old stock.",[("craft","healing_potion",3)]),
        ("The Traveler's Account","banker","A sound journey needs supplies and a return route. Visit Wayfarer's Rest and bring a loaf for the bank's courier.",[("explore","wayfarers_rest",1),("deliver","bread",1)]),
      ],
      "emberhold":[
        ("Cooling Channel","blacksmith","A blocked cooling channel damaged the forge tools. Mine iron for new heads.",[("gather","iron_ore",6)]),
        ("No Timber in a Furnace","carpenter","The furnace crews keep burning handle stock. Prepare oak planks and deliver them separately.",[("craft","oak_plank",4),("deliver","oak_plank",4)]),
        ("A Surveyor Gone Still","scholar","A brass surveyor patrols a route that no longer exists. Record the Brass Vault and stop its sentries.",[("explore","the_brass_vault",1),("kill","brass_surveyor",3)]),
        ("The Redstone Crossing","guard","The ridge route is unsafe after a bridge troll claimed the toll span. Clear the pass approach.",[("explore","redstone_pass",1),("kill","bridge_troll",2)]),
        ("Gem Dust in the Water","jeweler","The new ore loads contain gem-bearing stone. Recover rough gems for inspection.",[("gather","rough_gem",3)]),
        ("The Clerk's Spring Lock","carpenter","The wage chest needs a new spring lock. Assemble a clockwork mechanism from iron and copper.",[("craft","mechanism",1)]),
        ("A Furnace Meal","innkeeper","The night shift needs food that can stand beside a hot forge. Prepare honey roast.",[("craft","honey_roast",2)]),
        ("Cobalt Under Glass","blacksmith","Blue seams under the northern rock resist ordinary tools. Extract cobalt without mixing it with surface iron.",[("gather","cobalt_ore",4)]),
        ("Ash in the Ledger","scribe","Workers left a ledger in the Cinder Valley shelters. Visit the valley and prepare a new journal for their testimony.",[("explore","cinder_valley",1),("craft","field_journal",1)]),
        ("The Observatory Stair","scholar","The Rookspine instrument was built by forge-clan workers. Reach the observatory and return with an account.",[("explore","rookspine_observatory",1)]),
      ],
      "thornhollow":[
        ("What the Soil Keeps","alchemist","The western soil grows unfamiliar mushrooms. Gather a controlled sample before the circle clears it.",[("gather","mushroom",5)]),
        ("A Bridge That Bends","carpenter","A living bridge still needs replaceable deck boards. Prepare oak without cutting its supporting roots.",[("craft","oak_plank",4)]),
        ("The Empty Bait Bowl","trainer","The refuge's animal bait has gone stale. Make fresh bait and consult the local scholar.",[("craft","animal_bait",3),("talk","thornhollow_scholar",1)]),
        ("Silk Without Spiders","tailor","A webbed hollow contains strong loose silk. Explore it before the weavers send a collecting party.",[("explore","widows_hollow",1),("deliver","silk_fiber",4)]),
        ("Thorns Across the Survey","scholar","The old survey cut has disappeared beneath living thorns. Find the Thorn Basin boundary.",[("explore","thorn_basin",1)]),
        ("Medicine at Root Level","alchemist","The sanctuary attendants need clean herbs. Collect sage and mint from living plants.",[("gather","sage",4),("gather","mint",4)]),
        ("The Watchful Oak","guard","A sentinel no longer recognizes the circle's markers. Remove the hostile guardian in the outer forest.",[("kill","oak_sentinel",2)]),
        ("The Fungal Crossing","scholar","The underground stream may join two old roots. Enter Fungal Hollow and chart its entrance in a field journal.",[("explore","fungal_hollow",1),("deliver","field_journal",1)]),
        ("A Cloak for Rain","tailor","The canopy drips long after rain stops. Stitch a wool cloak for a new trail keeper.",[("craft","wool_cloak",1)]),
        ("The Hartwood Meal","innkeeper","The refuge needs provisions for travelers without hunting rights. Prepare mushroom stew.",[("craft","mushroom_stew",3)]),
      ],
      "frostgate":[
        ("Before the Whiteout","innkeeper","The cairn patrol leaves before dawn. Prepare salmon pies for the long route.",[("craft","salmon_pie",3)]),
        ("Bent Signal Wire","carpenter","Ice has pulled the signal line from its anchors. Prepare pine planks for replacement supports.",[("craft","pine_plank",4)]),
        ("A Name in the Ice","scholar","The glacier preserves a settlement omitted from the clan histories. Reach its blue roofs and return.",[("explore","mirror_glacier",1)]),
        ("Frostpetal Remedy","alchemist","Northern healers use a flower that opens in freezing air. Collect frostpetals from their plants.",[("gather","frostpetal",4)]),
        ("The Cairn Keeper","guard","The Northwind route needs an inspection before the convoy. Visit the steppe and consult the city's trainer.",[("explore","northwind_steppe",1),("talk","frostgate_trainer",1)]),
        ("Cloth Against the Wind","tailor","Ordinary wool tears against ice crust. Sew a frostweave chest piece for the gate watch.",[("craft","frostweave_chest",1)]),
        ("The Empty Burial Boat","scholar","An open burial boat lies beneath the keep. Enter the halls and record the route for the wardens.",[("explore","frostgate_burial_halls",1),("deliver","blank_paper",4)]),
        ("Claws at Whitebark","guard","A lynx has begun hunting near the trail shelters. Clear hostile lynxes from the pine route.",[("kill","pine_lynx",3)]),
        ("A Blue Edge","blacksmith","The northern smiths temper cobalt for the cold. Forge a cobalt sword with sound wood and leather.",[("craft","cobalt_sword",1)]),
        ("The Last Bell","scholar","A bell rings above the Frozen Crown without wind. Reach the summit road and return alive.",[("explore","frozen_crown",1)]),
      ],
      "gloamport":[
        ("Salt in the Stores","provisioner","Saltwater spoiled the dry stores. Bring grain before the next ship takes the remaining bread.",[("deliver","wheat",8)]),
        ("The Pilot's Supper","innkeeper","The night pilots need meals that can be carried aboard. Grill trout for the next tide.",[("craft","grilled_trout",3)]),
        ("Lamps in the Wrong Channel","scholar","A second line of lamps has appeared in Lantern Marsh. Reach the marsh and consult the guard.",[("explore","lantern_marsh",1),("talk","gloamport_guard",1)]),
        ("Tarred Rope and Iron","blacksmith","The quay needs new metal fittings. Refine iron before seawater reaches the next warehouse.",[("craft","iron_ingot",4)]),
        ("A Smuggler's Quiet Route","guard","Smoke smugglers use the island ferry landings. Stop their hostile lookouts.",[("kill","smoke_smuggler",3)]),
        ("The Willow Passage","scholar","The ferrymen follow an older channel. Visit Willowwater and bring paper for a corrected harbor map.",[("explore","willowwater",1),("deliver","blank_paper",3)]),
        ("Shells in the Foundation","jeweler","Workers found intact spiral shells below the oldest quay. Recover shells from the shore creatures.",[("deliver","shell",5)]),
        ("The Mourning Star","scribe","A wreck forms a bridge beyond Stormhook. Reach the ship and return with a written record.",[("explore","wreck_of_the_mourning_star",1),("craft","field_journal",1)]),
        ("A Bottle Without Fever","alchemist","Swamp fever follows a poison that remains in drinking vessels. Brew antidotes for the harbor workers.",[("craft","antidote",3)]),
        ("Debt Below the Waterline","banker","The old debt archive lies beneath the tide stairs. Find the catacomb entrance without opening an account with its keeper.",[("explore","gloamport_catacombs",1)]),
      ],
    }
    for city,rows in city_stories.items():
        for index,(name,role,story,steps) in enumerate(rows):
            add(city+"_story_"+str(index+1),name,city+"_"+role,story,
                [objective(*s) for s in steps],gold=35+index*12,reward="healing_potion" if index%3==0 else "")
    for name,_,level,parent,_,_ in SETTLEMENTS:
        ident="wayfarers_rest" if name=="Wayfarer's Rest" else slug(name)
        add(ident+"_supply_path",name+": The Supply Path",ident+"_provisioner",
            "The refuge cannot supply travelers when its approach is unknown. Inspect the nearby road and bring fresh food.",
            [objective("explore",parent),objective("deliver","bread",2)],gold=30+level*2)
        add(ident+"_repair_bench",name+": The Repair Bench",ident+"_carpenter",
            "The shelter's workbench has worn through its front boards. Prepare replacements and deliver them to the carpenter.",
            [objective("craft","ash_plank",4),objective("deliver","ash_plank",4)],gold=35+level*2)
    for index,(name,parent,_,_,level,boss,lore) in enumerate(DUNGEONS):
        # Boss contracts use the nearest relevant major-city guild service.
        city=["dawnreach","thornhollow","emberhold","frostgate","gloamport"][min(4,index//4)]
        add("contract_"+slug(boss),"Contract: "+boss,city+"_guild_registrar",lore,
            [objective("explore",slug(name)),objective("kill",slug(boss))],gold=100+level*12,reward="rough_gem")
    for cls in classes:
        aid=cls["abilities"][0]
        add("trial_"+cls["id"],cls["name"]+": First Discipline","dawnreach_trainer",
            "Practice a signature discipline against a hostile target. Training other skills does not remove your original class identity.",
            [objective("cast",aid,3)],gold=60,reward="rune_precision_1")
    for index in range(30):
        city=["dawnreach","emberhold","thornhollow","frostgate","gloamport"][index//6]
        options=[("grain","wheat",6),("timber","ash_log",5),("metal","copper_ore",6),
                 ("medicine","sage",4),("paper","blank_paper",3),("food","bread",2)]
        label,material,count=options[index%6]
        add("daily_"+city+"_"+label,"Supply Commission: "+label.title(),city+"_provisioner",
            "The city posts a new supply order each realm day. Turn in actual goods to receive payment.",
            [objective("deliver",material,count)],"repeatable",gold=20+count*3,repeat=True)
    assert len([q for q in quests if q["category"]=="main"])==25
    assert len([q for q in quests if q["category"]=="side"])==100
    assert len([q for q in quests if q["category"]=="repeatable"])==30
    return quests
