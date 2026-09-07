"""Compile equipment families and authored material/profession relationships."""
from __future__ import annotations
from content_rules import slug

METALS = [
    ("copper", "Copper", 1, "Physical", {"physical": 0}),
    ("bronze", "Bronze", 10, "Physical", {"resolve": 1}),
    ("iron", "Iron", 20, "Physical", {"physical": 2}),
    ("steel", "Steel", 30, "Physical", {"crit": 1}),
    ("silver", "Silver", 40, "Radiant", {"damage_radiant": 4}),
    ("cobalt", "Cobalt", 50, "Frost", {"resist_frost": 5}),
    ("mithril", "Mithril", 60, "Arcane", {"attack_speed": 4}),
    ("obsidian", "Obsidian", 70, "Fire", {"damage_fire": 6}),
    ("adamant", "Adamant", 80, "Physical", {"armor": 8}),
    ("aetherium", "Aetherium", 90, "Arcane", {"spell": 8}),
]
WOODS = [("ash",1), ("oak",15), ("pine",30), ("yew",45), ("ironwood",60), ("moonwood",80)]
HIDES = [("hide",1), ("boarhide",15), ("wolfhide",30), ("bearhide",45), ("drakehide",65), ("wyrmhide",85)]
CLOTHS = [("linen",1), ("wool",15), ("silk",30), ("duskweave",45), ("frostweave",65), ("aetherweave",85)]
# Family, skill, power factor, attack interval, reach, optional stat.
WEAPONS = [
    ("sword", "swordsmanship", 1.0, 1.0, 1.9, {"accuracy":2}),
    ("greatsword", "swordsmanship", 1.65, 1.6, 2.3, {"physical":2}),
    ("axe", "axe_mastery", 1.15, 1.15, 1.8, {"crit_damage":4}),
    ("great_axe", "axe_mastery", 1.85, 1.8, 2.1, {"crit_damage":6}),
    ("mace", "mace_mastery", 1.12, 1.2, 1.7, {"armor":2}),
    ("great_mace", "mace_mastery", 1.95, 2.0, 2.2, {"block":1}),
    ("spear", "spear_mastery", 0.95, 1.1, 3.2, {"accuracy":3}),
    ("halberd", "spear_mastery", 1.6, 1.7, 3.0, {"physical":1}),
    ("dagger", "dagger_mastery", 0.66, 0.65, 1.5, {"crit":2}),
    ("bow", "archery", 0.9, 1.3, 9.0, {"accuracy":2}),
    ("crossbow", "crossbow_mastery", 1.55, 1.9, 10.0, {"crit_damage":3}),
    ("staff", "staff_mastery", 0.7, 1.3, 6.5, {"spell":3}),
    ("wand", "wand_mastery", 0.55, 0.9, 7.5, {"mana":5}),
    ("war_tome", "arcane_magic", 0.5, 1.5, 7.0, {"intellect":2}),
    ("fist_weapon", "unarmed_combat", 0.7, 0.75, 1.4, {"evasion":1}),
]
ARMOR_SLOTS = [("helmet",0.6), ("chest",1.5), ("gloves",0.4), ("legs",1.0), ("boots",0.5), ("belt",0.25)]
RUNE_ROWS = [
    ("embers", "Embers", "Fire", "damage_fire", 3, "A copper-inlaid ember spiral adds fire damage."),
    ("winter", "Winter", "Frost", "damage_frost", 3, "A six-point crystal mark adds frost damage."),
    ("storm", "Storm", "Lightning", "damage_lightning", 3, "A forked silver stroke adds lightning damage."),
    ("thorns", "Thorns", "Nature", "damage_nature", 3, "A carved thorn ring adds nature damage."),
    ("venom", "Venom", "Poison", "damage_poison", 3, "A coiled serpent mark adds poison damage."),
    ("aether", "Aether", "Arcane", "damage_arcane", 3, "Concentric etched rings add arcane damage."),
    ("dawn", "Dawn", "Radiant", "damage_radiant", 3, "A gold sunburst adds radiant damage."),
    ("dusk", "Dusk", "Shadow", "damage_shadow", 3, "A dark crescent adds shadow damage."),
    ("bulwark", "Bulwark", "Physical", "block", 2, "An interlocked stone knot improves block chance."),
    ("precision", "Precision", "Physical", "crit", 1, "A narrow pointed glyph improves critical chance."),
    ("leeching", "Leeching", "Shadow", "leech", 1, "A hooked crimson mark grants bounded life recovery."),
    ("prospector", "Prospector", "Physical", "gather_yield", 2, "An ore-vein carving improves gathering yield."),
    ("wanderer", "Wanderer", "Nature", "movement", 1, "A crossing-path mark improves movement speed."),
    ("vitality", "Vitality", "Nature", "health", 10, "A branching tree mark increases maximum health."),
    ("warding", "Warding", "Arcane", "armor", 3, "A concentric shield mark adds armor."),
    ("focus", "Focus", "Arcane", "mana", 8, "A sapphire eye increases maximum mana."),
]


def build_items() -> tuple[list[dict], list[dict], list[dict]]:
    items: list[dict] = []
    recipes: list[dict] = []
    resources: list[dict] = []
    ids: set[str] = set()

    def item(ident: str, name: str, kind: str, **extra) -> dict:
        if ident in ids:
            raise ValueError(f"Duplicate item: {ident}")
        ids.add(ident)
        result = dict(id=ident, name=name, type=kind, slot="", skill="", requirement=1,
                      icon=f"res://Art/Icons/{ident}.png", material="", description=name,
                      stackMax=1, value=1, power=0, armor=0, speed=1, range=1.7,
                      element="Physical", stats={}, tags=[], tier=1, effect="")
        result.update(extra)
        items.append(result)
        return result

    def recipe(output: str, skill: str, station: str, ingredients: dict[str,int], level=1,
               quantity=1, name: str|None=None) -> None:
        recipes.append(dict(id="make_" + output, name=name or output.replace("_", " ").title(),
                            skill=skill, station=station, requirement=level, ingredients=ingredients,
                            output=output, quantity=quantity, xp=20+level*3))

    def node(ident: str, name: str, skill: str, tool: str, output: str, level=1, respawn=30) -> None:
        resources.append(dict(id=ident, name=name, skill=skill, tool=tool, item=output,
                              sprite=f"res://Art/Resources/{ident}.png", requirement=level,
                              xp=25+level*3, respawn=respawn))

    # Materials retain different crafting roles. Refined products require raw nodes.
    for ident, name, level, element, bonus in METALS:
        tier=METALS.index((ident,name,level,element,bonus))+1
        item(ident+"_ore", name+" Ore", "material", stackMax=99, value=2+tier*3,
             material=ident, tags=["ore"], description=f"Raw {name.lower()}-bearing stone. Refine it at a forge.")
        item(ident+"_ingot", name+" Ingot", "material", stackMax=99, value=10+tier*8,
             material=ident, tags=["metal"], description=f"A cast {name.lower()} bar with a flattened top and stamped end.")
        recipe(ident+"_ingot", "smithing", "anvil", {ident+"_ore":3}, level)
        node(ident+"_vein", name+" Deposit", "mining", "pickaxe", ident+"_ore", level, 25+tier*8)
    for name,level in WOODS:
        item(name+"_log", name.title()+" Log", "material", stackMax=99, value=3+level//5,
             material=name, tags=["wood"], description="A cut trunk section with bark, grain, and visible end rings.")
        item(name+"_plank", name.title()+" Plank", "material", stackMax=99, value=8+level//3, material=name, tags=["wood"])
        recipe(name+"_plank", "woodworking", "workbench", {name+"_log":2}, level, 2)
        node(name+"_tree", name.title()+" Tree", "woodcutting", "axe", name+"_log", level, 45+level)
    for name,level in HIDES:
        item(name+"_raw", "Untanned "+name.title(), "material", stackMax=99, value=4+level//4, material="leather", tags=["hide"])
        item(name+"_leather", "Tanned "+name.title(), "material", stackMax=99, value=10+level//3, material="leather", tags=["leather"])
        recipe(name+"_leather", "leatherworking", "tannery", {name+"_raw":2}, level)
        node(name+"_carcass", name.title()+" Carcass", "skinning", "knife", name+"_raw", level, 60)
    for name,level in CLOTHS:
        item(name+"_fiber", name.title()+" Fiber", "material", stackMax=99, value=4+level//5, material="cloth", tags=["fiber"])
        item(name+"_cloth", name.title()+" Cloth", "material", stackMax=99, value=12+level//3, material="cloth", tags=["cloth"])
        recipe(name+"_cloth", "tailoring", "loom", {name+"_fiber":3}, level)
        node(name+"_patch", name.title()+" Fiber Patch", "foraging", "sickle", name+"_fiber", level, 35+level)

    # Fifteen weapon families across ten material tiers. Shape and handling stay
    # tied to the family; a material tier is not counted as a new weapon family.
    for metal, metal_name, level, element, metal_bonus in METALS:
        wood=WOODS[min(len(WOODS)-1,level//18)][0]
        for family,skill,factor,interval,reach,family_bonus in WEAPONS:
            stats=dict(metal_bonus)
            for key,value in family_bonus.items():
                stats[key]=stats.get(key,0)+value
            ident=metal+"_"+family
            item(ident, metal_name+" "+family.replace("_"," ").title(), "weapon",
                 slot="weapon", skill=skill, requirement=level, material=metal,
                 value=25+level*9, power=round((8+level*0.85)*factor,2), speed=interval,
                 range=reach, element=element, stats=stats,
                 tags=[family,"two_handed"] if family in ("greatsword","great_axe","great_mace","halberd","bow","crossbow","staff") else [family],
                 description=f"A {family.replace('_',' ')} built from {metal_name.lower()}, {wood}, and leather. "
                             f"Attack interval {interval} seconds; reach {reach} tiles.")
            profession="fletching" if family in ("bow","crossbow") else ("enchanting" if family in ("staff","wand","war_tome") else "smithing")
            station={"fletching":"fletching_bench","enchanting":"enchanting_table","smithing":"anvil"}[profession]
            recipe(ident,profession,station,{metal+"_ingot":2,wood+"_plank":1,"hide_leather":1},level)
        for slot,factor in ARMOR_SLOTS:
            ident=metal+"_"+slot
            item(ident,metal_name+" "+slot.title(),"armor",slot=slot,skill="heavy_armor",requirement=level,
                 material=metal,value=20+level*6,armor=round((4+level*0.3)*factor,2),stats={"resolve":1+level//30},tags=["heavy"],
                 description="Articulated metal plates, leather fastening straps, and a cloth lining.")
            recipe(ident,"smithing","anvil",{metal+"_ingot":2,"hide_leather":1},level)
        item(metal+"_shield",metal_name+" Shield","offhand",slot="offhand",skill="shield_mastery",requirement=level,
             material=metal,armor=5+level*0.3,value=30+level*6,stats={"block":2+level//20},tags=["shield"],
             description="A curved shield with a central boss, rim binding, and rear hand straps.")
        recipe(metal+"_shield","smithing","anvil",{metal+"_ingot":2,wood+"_plank":2,"hide_leather":1},level)
    for material_rows,skill,profession,station,weight,tag,suffix in [
        (HIDES,"medium_armor","leatherworking","tannery",0.7,"medium","leather"),
        (CLOTHS,"light_armor","tailoring","loom",0.35,"light","cloth"),
    ]:
        for mat,level in material_rows:
            for slot,factor in ARMOR_SLOTS:
                ident=mat+"_"+slot
                stats={"dexterity":1+level//30} if tag=="medium" else {"intellect":1+level//25,"mana":2+level//5}
                item(ident,mat.title()+" "+slot.title(),"armor",slot=slot,skill=skill,requirement=level,material="leather" if tag=="medium" else "cloth",
                     value=15+level*5,armor=round((4+level*0.3)*factor*weight,2),stats=stats,tags=[tag],
                     description="Layered stitched leather with buckles." if tag=="medium" else "Woven fabric with stitched hems and visible folds.")
                recipe(ident,profession,station,{mat+"_"+suffix:3},level)
            item(mat+"_cloak",mat.title()+" Cloak","armor",slot="cloak",skill=skill,requirement=level,material="cloth",
                 value=20+level*5,armor=2+level*0.1,stats={"resist_frost":2+level//10},tags=[tag],description="A pinned shoulder cloak with a folded hood and weighted hem.")
            recipe(mat+"_cloak",profession,station,{mat+"_"+suffix:4},level)

    for gem,element,stat in [("ruby","Fire","physical"),("sapphire","Frost","mana"),("emerald","Nature","health"),
                             ("amethyst","Arcane","spell"),("topaz","Lightning","crit"),("onyx","Shadow","evasion")]:
        item("rough_"+gem,"Rough "+gem.title(),"material",stackMax=99,value=20,material="gem",tags=["gem"])
        item("cut_"+gem,"Cut "+gem.title(),"material",stackMax=99,value=70,material="gem",tags=["gem"])
        recipe("cut_"+gem,"jewelcrafting","jewelers_bench",{"rough_"+gem:2},15)
        for level,metal in [(1,"copper"),(25,"iron"),(50,"cobalt"),(75,"mithril")]:
            for slot in ("ring","necklace","charm"):
                ident=metal+"_"+gem+"_"+slot
                item(ident,metal.title()+" "+gem.title()+" "+slot.title(),"accessory",slot=slot,requirement=level,
                     material=metal,value=50+level*8,element=element,stats={stat:2+level//8},tags=[slot],
                     description="A faceted gemstone held by small metal prongs in a shaped setting.")
                recipe(ident,"jewelcrafting","jewelers_bench",{"cut_"+gem:1,metal+"_ingot":1},level)
    for rid,rname,element,stat,scale,description in RUNE_ROWS:
        for tier in range(1,6):
            level=1+(tier-1)*20
            ident=f"rune_{rid}_{tier}"
            item(ident,f"Rune of {rname} {['I','II','III','IV','V'][tier-1]}","rune",skill="runecrafting",requirement=level,
                 material="runestone",value=40*tier*tier,tier=tier,element=element,stats={stat:scale*tier},tags=["rune"],description=description)
            recipe(ident,"runecrafting","rune_table",{"runestone":tier,"arcane_dust":tier},level)

    for ident,name,tool in [("copper_pickaxe","Copper Pickaxe","pickaxe"),("woodcutters_axe","Woodcutter's Axe","axe"),
                           ("field_rod","Field Fishing Rod","rod"),("sickle","Harvest Sickle","sickle"),
                           ("shovel","Iron-bound Shovel","shovel"),("skinning_knife","Skinning Knife","knife"),
                           ("crafting_hammer","Crafting Hammer","hammer")]:
        item(ident,name,"tool",value=18,material="wood_iron",tags=[tool],description="A fitted metal working head, shaped wooden handle, and bound grip.")
        recipe(ident,"tinkering","workbench",{"copper_ingot":1,"ash_plank":1},1)
    item("lockpick","Lockpick","tool",stackMax=50,value=3,material="iron",tags=["lockpick"],description="A thin spring-steel pick with an offset hook and narrow handle.")
    recipe("lockpick","tinkering","workbench",{"copper_ingot":1},1,5)

    raw_rows = [
        ("wheat","Wheat","grain"),("wheat_seed","Wheat Seed","seed"),("raw_meat","Raw Meat","food_material"),
        ("trout","River Trout","fish"),("perch","Lake Perch","fish"),("salmon","Northern Salmon","fish"),
        ("tuna","Sea Tuna","fish"),("mushroom","Field Mushroom","food_material"),("berry","Wild Berries","food_material"),
        ("apple","Orchard Apple","food_material"),("honey","Wild Honey","food_material"),
        ("sage","Sage","herb"),("mint","Mint","herb"),("marigold","Marigold","herb"),
        ("nightshade","Nightshade","herb"),("frostpetal","Frostpetal","herb"),("sunroot","Sunroot","herb"),
        ("runestone","Blank Runestone","stone"),("arcane_dust","Arcane Dust","powder"),
        ("bone","Bone Fragment","bone"),("fang","Animal Fang","bone"),("feather","Flight Feather","feather"),
        ("shell","Spiral Shell","shell"),("ancient_shard","Ancient Pottery Shard","artifact"),
        ("rough_gem","Unsorted Rough Gem","gem"),("coal","Coal","stone"),
        ("blank_paper","Blank Paper","paper"),("ink","Ink Bottle","glass"),
        ("animal_bait","Animal Bait","food_material"),("mechanism","Clockwork Mechanism","metal"),
    ]
    for ident,name,material in raw_rows:
        item(ident,name,"material",stackMax=99,value=2 if ident in ("wheat_seed","wheat","berry") else 8,
             material=material,tags=[material])
    recipe("wheat_seed","farming","hand",{"wheat":1},1,2)
    recipe("animal_bait","cooking","cooking_fire",{"raw_meat":1,"berry":2},1,2)
    recipe("blank_paper","scribing","scribing_desk",{"ash_log":1,"linen_fiber":1},1,3)
    recipe("ink","scribing","scribing_desk",{"berry":3,"coal":1},5)
    recipe("mechanism","tinkering","workbench",{"iron_ingot":2,"copper_ingot":1},20)
    node("animal_carcass","Animal Carcass","skinning","knife","hide_raw",1,90)
    node("wheat_crop","Mature Wheat","farming","sickle","wheat",1,50)
    node("meteor_ore","Meteor Fragment","mining","pickaxe","aetherium_ore",60,180)
    node("river_shoal","River Shoal","fishing","rod","trout",1,30)
    node("lake_shoal","Lake Shoal","fishing","rod","perch",15,40)
    node("northern_shoal","Northern Shoal","fishing","rod","salmon",40,55)
    node("sea_shoal","Sea Shoal","fishing","rod","tuna",60,70)
    for index,(ident,name) in enumerate([("berry","Berry Bush"),("mushroom","Mushroom Patch"),("apple","Wild Apple Tree"),("honey","Wild Beehive")]):
        node(ident+"_patch",name,"foraging","sickle",ident,1+index*10,35+index*10)
    for index,herb in enumerate(["sage","mint","marigold","nightshade","frostpetal","sunroot"]):
        node(herb+"_plant",herb.title()+" Plant","herbalism","sickle",herb,1+index*15,35+index*10)
    node("buried_pottery","Buried Pottery","excavation","shovel","ancient_shard",1,70)
    node("buried_runestone","Buried Runestone","excavation","shovel","runestone",20,90)
    node("crystal_seam","Arcane Crystal Seam","mining","pickaxe","arcane_dust",25,60)
    node("gem_seam","Gem-bearing Rock","mining","pickaxe","rough_gem",15,50)
    node("coal_seam","Coal Seam","mining","pickaxe","coal",1,35)
    for gem in ("ruby","sapphire","emerald","amethyst","topaz","onyx"):
        node(gem+"_deposit",gem.title()+" Deposit","mining","pickaxe","rough_"+gem,20,80)

    potion_rows=[("healing_potion","Healing Draught","heal",60,1,{"sage":2,"marigold":1}),
                 ("mana_potion","Mana Draught","mana",55,1,{"mint":2,"arcane_dust":1}),
                 ("antidote","Antidote","purge",1,10,{"sage":2,"honey":1}),
                 ("greater_healing_potion","Restorative Elixir","heal",150,25,{"marigold":3,"honey":1}),
                 ("greater_mana_potion","Clear-Mind Elixir","mana",130,25,{"mint":3,"frostpetal":1}),
                 ("royal_healing_potion","Royal Restoration","heal",350,60,{"sunroot":3,"frostpetal":2}),
                 ("royal_mana_potion","Aether Elixir","mana",300,60,{"arcane_dust":4,"sunroot":2})]
    for ident,name,effect,power,level,ingredients in potion_rows:
        item(ident,name,"potion",stackMax=20,value=12+level*2,power=power,effect=effect,material="glass",tags=["potion"],
             description="A corked glass vial with a wrapped neck, clear rim, and visible liquid.")
        recipe(ident,"alchemy","alchemy_table",ingredients,level)
    food_rows=[("bread","Hearth Bread",36,1,{"wheat":3}),
               ("roast_meat","Roast Meat",50,1,{"raw_meat":2}),
               ("berry_tart","Berry Tart",65,10,{"wheat":2,"berry":3}),
               ("grilled_trout","Grilled Trout",80,15,{"trout":2,"sage":1}),
               ("mushroom_stew","Mushroom Stew",90,20,{"mushroom":3,"wheat":1}),
               ("honey_roast","Honey Roast",110,30,{"raw_meat":2,"honey":2}),
               ("salmon_pie","Salmon Pie",145,40,{"salmon":2,"wheat":2}),
               ("frostgate_feast","Frostgate Feast",200,60,{"salmon":3,"raw_meat":2,"frostpetal":1})]
    for ident,name,power,level,ingredients in food_rows:
        item(ident,name,"food",stackMax=20,value=8+level,power=power,effect="food",material="food",tags=["food"])
        recipe(ident,"cooking","cooking_fire",ingredients,level)
    for station,level in [("campfire",1),("workbench",10),("cooking_fire",15),("rune_table",35),("anvil",50)]:
        ident="structure_"+station
        item(ident,station.replace("_"," ").title()+" Kit","structure",value=35+level*4,material="wood_iron",tags=["structure"],
             description="A packed set of fitted components for an outdoor crafting station.")
        recipe(ident,"construction","hand",{"ash_plank":4,"copper_ingot":2},level)
    item("carved_stool","Carved Stool","material",value=15,material="wood",tags=["furniture"])
    recipe("carved_stool","carpentry","workbench",{"ash_plank":3},1)
    item("field_journal","Wayfarer's Field Journal","book",value=25,material="paper",tags=["book"],effect="lore",
         description="A stitched leather-bound book. Its pages describe lost roads beneath Dawnreach.")
    recipe("field_journal","scribing","scribing_desk",{"blank_paper":3,"ink":1,"hide_leather":1},1)
    item("treasure_map","Weathered Treasure Map","map",value=50,material="paper",tags=["map"],effect="map",
         description="A folded chart with a hand-drawn landmark and an incomplete route.")
    item("sealed_dispatch","Sealed Wayfarer Dispatch","quest",value=0,material="paper",tags=["quest"],
         description="A parchment dispatch sealed with the Wayfarers Guild mark.")
    item("watchtower_key","Old Watchtower Key","key",value=0,material="iron",tags=["key"],
         description="A rusted iron key with a square bit and an oval bow.")
    item("carved_idol","Carved River Idol","collectible",value=80,material="stone",tags=["collectible"],
         description="A small river-stone figure with worn carved eyes and a chipped base.")
    assert all(r["output"] in ids and all(i in ids for i in r["ingredients"]) for r in recipes)
    assert all(r["item"] in ids for r in resources)
    return items, recipes, resources
