"""Authored progression and combat content. No runtime rewards originate here."""
from __future__ import annotations


def slug(name: str) -> str:
    return name.lower().replace("'", "").replace("-", "_").replace(" ", "_")


SKILL_GROUPS = {
    "Weapons": "Swordsmanship|Axe Mastery|Mace Mastery|Spear Mastery|Dagger Mastery|Archery|Crossbow Mastery|Staff Mastery|Wand Mastery|Shield Mastery|Unarmed Combat",
    "Magic": "Pyromancy|Cryomancy|Stormcalling|Geomancy|Nature Magic|Shadow Magic|Radiance|Arcane Magic|Restoration|Summoning|Runecasting",
    "Survival": "Light Armor|Medium Armor|Heavy Armor|Evasion|Endurance|Meditation|Hunting|Slayer|Survival|Exploration",
    "Gathering": "Mining|Woodcutting|Fishing|Farming|Foraging|Herbalism|Skinning|Excavation|Prospecting|Treasure Hunting",
    "Crafting": "Smithing|Woodworking|Fletching|Tailoring|Leatherworking|Cooking|Alchemy|Enchanting|Runecrafting|Jewelcrafting|Carpentry|Scribing|Tinkering",
    "Utility": "Lockpicking|Bartering|Cartography|Animal Handling|Construction",
}

SKILL_PURPOSES = {
    "swordsmanship": ("Hit a hostile creature with a sword.", "Improve sword damage and unlock sword techniques."),
    "axe_mastery": ("Hit a hostile creature with an axe.", "Improve axe damage and unlock cleaving techniques."),
    "mace_mastery": ("Hit a hostile creature with a mace.", "Improve crushing damage and unlock interruptions."),
    "spear_mastery": ("Hit a hostile creature with a spear or halberd.", "Improve reach-weapon damage and line attacks."),
    "dagger_mastery": ("Hit a hostile creature with a dagger.", "Improve dagger damage and poison techniques."),
    "archery": ("Hit a hostile creature with a bow.", "Improve bow damage and unlock precise shots."),
    "crossbow_mastery": ("Hit a hostile creature with a crossbow.", "Improve crossbow damage and piercing shots."),
    "staff_mastery": ("Attack with a staff.", "Improve staff damage and qualify for stronger staves."),
    "wand_mastery": ("Attack with a wand.", "Improve wand damage and qualify for stronger wands."),
    "shield_mastery": ("Block a hostile attack with a shield.", "Improve block chance and unlock shield guards."),
    "unarmed_combat": ("Fight without a weapon or use fist weapons.", "Improve unarmed damage and unlock physical techniques."),
    "pyromancy": ("Damage enemies with fire magic.", "Unlock fire projectiles, burning ground, and fire bursts."),
    "cryomancy": ("Damage enemies with frost magic.", "Unlock chill, freezing fields, and frost defenses."),
    "stormcalling": ("Damage enemies with lightning magic.", "Unlock lightning lines, cones, and storm fields."),
    "geomancy": ("Use earth attacks and protection spells.", "Unlock stone protection and ground disruption."),
    "nature_magic": ("Use nature magic against enemies.", "Unlock roots, thorns, and nature fields."),
    "shadow_magic": ("Use shadow spells against enemies.", "Unlock curses, life drain, and concealment."),
    "radiance": ("Use radiant attacks or protection.", "Unlock radiant attacks, cleansing, and protection."),
    "arcane_magic": ("Use arcane spells.", "Unlock arcane projectiles, fields, and displacement."),
    "restoration": ("Restore missing health with healing spells.", "Increase healing options and unlock stronger recovery spells."),
    "summoning": ("Summon a companion and fight alongside it.", "Unlock stronger companions and summon abilities."),
    "runecasting": ("Cast a rune-based ability.", "Unlock rune barriers, pulses, and triggered spells."),
    "light_armor": ("Survive hostile hits while wearing light armor.", "Qualify for higher-level light armor."),
    "medium_armor": ("Survive hostile hits while wearing medium armor.", "Qualify for higher-level medium armor."),
    "heavy_armor": ("Survive hostile hits while wearing heavy armor.", "Qualify for higher-level heavy armor."),
    "evasion": ("Evade hostile attacks.", "Increase the chance to avoid a hostile hit."),
    "endurance": ("Fight and gather while using stamina.", "Increase stamina recovery."),
    "meditation": ("Recover spent mana through meditation.", "Increase mana recovery."),
    "hunting": ("Defeat wild animals.", "Unlock advanced hunting equipment and hunting contracts."),
    "slayer": ("Defeat hostile creatures.", "Unlock slayer techniques and difficult creature contracts."),
    "survival": ("Rest outside cities and prepare supplies.", "Unlock survival food and equipment."),
    "exploration": ("Discover new areas of the world.", "Earn experience once per newly discovered map sector."),
    "mining": ("Extract ore from a mineral node.", "Unlock richer mineral deposits and improve gathering yield."),
    "woodcutting": ("Cut a mature tree with an axe.", "Unlock harder woods and improve gathering yield."),
    "fishing": ("Fish at a marked fishing shoal.", "Unlock new fish and improve gathering yield."),
    "farming": ("Plant seeds and harvest mature crops.", "Reduce crop growth time and unlock farming recipes."),
    "foraging": ("Collect wild food and natural materials.", "Unlock wild food sources and improve gathering yield."),
    "herbalism": ("Collect medicinal and magical herbs.", "Unlock rare herbs and improve gathering yield."),
    "skinning": ("Skin the carcass of an animal.", "Unlock stronger hides and improve gathering yield."),
    "excavation": ("Excavate an archaeological deposit.", "Recover artifacts and unlock deeper dig sites."),
    "prospecting": ("Inspect a mineral deposit before extraction.", "Discover gems and earn mineral knowledge."),
    "treasure_hunting": ("Discover concealed caches and open treasure.", "Unlock difficult caches and treasure clues."),
    "smithing": ("Smelt metal and forge equipment at an anvil.", "Unlock metal components, weapons, and heavy armor."),
    "woodworking": ("Cut timber and make weapon components.", "Unlock handles, staves, and wooden components."),
    "fletching": ("Make bows, crossbows, and ammunition components.", "Unlock advanced ranged weapons."),
    "tailoring": ("Weave cloth and sew clothing.", "Unlock light armor, cloaks, and woven components."),
    "leatherworking": ("Tan hides and stitch leather equipment.", "Unlock medium armor and weapon grips."),
    "cooking": ("Cook gathered ingredients at a cooking station.", "Unlock food with stronger recovery effects."),
    "alchemy": ("Brew potions from gathered herbs.", "Unlock healing, mana, and combat consumables."),
    "enchanting": ("Craft enchanted equipment at an enchanting station.", "Unlock magical equipment recipes."),
    "runecrafting": ("Carve runes or insert runes into sockets.", "Unlock higher-tier rune recipes."),
    "jewelcrafting": ("Cut gems and make jewelry.", "Unlock jewelry and precision-cut rune ingredients."),
    "carpentry": ("Build furniture and station components.", "Unlock furniture and camp-station recipes."),
    "scribing": ("Make paper, scrolls, and books.", "Unlock written knowledge and spell consumables."),
    "tinkering": ("Assemble locks and mechanical components.", "Unlock mechanisms, tools, and crossbow components."),
    "lockpicking": ("Open locked chests with lockpicks.", "Unlock more difficult locked containers."),
    "bartering": ("Complete legitimate merchant transactions.", "Reduce buying prices within a bounded discount."),
    "cartography": ("Record a newly discovered region on paper.", "Earn map knowledge once per charted region."),
    "animal_handling": ("Tame weakened animals and feed companions.", "Unlock stronger tameable animals."),
    "construction": ("Build a camp station in an approved wilderness location.", "Unlock more advanced outdoor stations."),
}

# Base attributes use the same keys as the authoritative stat calculator.
CLASS_ROWS = [
    ("Vanguard", "Defensive melee", "Shield discipline", "sword", "heavy", (16,9,6,16,7,16,10), "swordsmanship,shield_mastery,heavy_armor"),
    ("Berserker", "Aggressive melee", "Relentless pressure", "great_axe", "medium", (20,11,5,15,5,10,10), "axe_mastery,mace_mastery,endurance"),
    ("Ranger", "Ranged physical", "Patient hunter", "bow", "medium", (10,20,8,10,8,10,12), "archery,hunting,animal_handling"),
    ("Rogue", "Mobile melee", "Concealed approach", "dagger", "light", (10,22,8,9,8,10,14), "dagger_mastery,evasion,lockpicking"),
    ("Arcanist", "Elemental caster", "Elemental study", "staff", "light", (5,9,22,9,17,8,10), "pyromancy,cryomancy,stormcalling,arcane_magic"),
    ("Warden", "Nature support", "Living bond", "staff", "light", (8,10,16,12,18,12,10), "nature_magic,summoning,herbalism"),
    ("Templar", "Armored support", "Oath of restoration", "mace", "heavy", (14,7,12,14,18,15,8), "radiance,restoration,shield_mastery"),
    ("Spellblade", "Magic melee", "Tempered magic", "sword", "medium", (13,14,16,11,10,10,10), "swordsmanship,arcane_magic,runecasting"),
]

# Fifteen named abilities per class. Each row defines a real server-supported
# mechanic, not a separate entry created only by changing a damage percentage.
# name | skill | kind | element | power | range | radius | cost | cooldown | duration | status
KITS = {
    "vanguard": [
        "Measured Cut|swordsmanship|strike|Physical|1.25|2|0|7|2|0|",
        "Shield Wall|shield_mastery|shield|Physical|0.35|0|0|10|12|6|guard",
        "Challenge|shield_mastery|taunt|Physical|1|6|0|8|8|4|",
        "Shield Rush|shield_mastery|dash|Physical|1|5|0|12|10|0|",
        "Pommel Check|mace_mastery|interrupt|Physical|0.7|2|0|8|9|2|stun",
        "Sweeping Guard|swordsmanship|cone|Physical|1.1|3|3|12|6|0|",
        "Hold the Line|heavy_armor|buff|Physical|0.3|0|0|14|18|8|guard",
        "Sundering Thrust|spear_mastery|line|Physical|1.3|5|1|14|7|5|vulnerable",
        "Rally|restoration|heal|Radiant|1.3|6|0|15|10|0|",
        "Iron Circle|shield_mastery|area|Physical|1.1|0|3|18|14|2|stun",
        "Oath Brand|radiance|dot|Radiant|0.3|5|0|14|10|6|burn",
        "Stone Resolve|geomancy|shield|Physical|0.5|0|0|22|24|10|guard",
        "Banner Strike|swordsmanship|strike|Physical|2|2|0|20|15|0|",
        "Gatekeeper|shield_mastery|field|Physical|0.65|5|3|25|24|6|root",
        "Last Bastion|heavy_armor|shield|Radiant|0.65|0|0|35|60|10|guard",
    ],
    "berserker": [
        "Rending Blow|axe_mastery|strike|Physical|1.4|2|0|8|2|4|bleed",
        "War Cry|endurance|buff|Physical|0.22|0|0|10|15|8|empower",
        "Reckless Leap|axe_mastery|dash|Physical|1|5|0|12|10|0|",
        "Bone Breaker|mace_mastery|interrupt|Physical|1|2|0|10|9|2|stun",
        "Reaping Arc|axe_mastery|cone|Physical|1.2|3|3|12|6|4|bleed",
        "Blood Oath|shadow_magic|drain|Shadow|1.2|2|0|12|8|0|",
        "Savage Roar|slayer|taunt|Physical|1|6|0|8|10|4|",
        "Earth Splitter|mace_mastery|line|Physical|1.5|6|1|18|10|2|stun",
        "Whirlwind|axe_mastery|area|Physical|1.5|0|3|20|12|0|",
        "Defiant Hide|medium_armor|shield|Physical|0.3|0|0|15|20|6|guard",
        "Hurling Axe|axe_mastery|projectile|Physical|1.7|8|0|18|8|0|",
        "Battle Recovery|restoration|heal|Physical|1.4|0|0|20|18|0|",
        "Ashen Frenzy|pyromancy|field|Fire|0.55|5|3|22|18|5|burn",
        "Execution|axe_mastery|strike|Physical|2.7|2|0|30|20|0|",
        "Mountain Breaker|mace_mastery|area|Physical|3|0|5|40|60|3|stun",
    ],
    "ranger": [
        "Steady Shot|archery|projectile|Physical|1.2|10|0|6|2|0|",
        "Briar Snare|nature_magic|field|Nature|0.25|7|2|10|10|7|root",
        "Trail Step|evasion|dash|Physical|1|5|0|10|9|0|",
        "Fan of Arrows|archery|cone|Physical|1.1|7|4|14|7|0|",
        "Poisoned Tip|archery|dot|Poison|0.3|9|0|12|7|7|poison",
        "Hawk Call|summoning|summon|Nature|1|0|0|20|30|35|",
        "Piercing Bolt|crossbow_mastery|line|Physical|1.6|10|1|16|8|0|",
        "Camouflage|hunting|stealth|Nature|1|0|0|10|20|8|stealth",
        "Binding Arrow|archery|projectile|Nature|0.9|9|0|14|10|3|root",
        "Field Dressing|restoration|heal|Nature|1.3|5|0|16|12|0|",
        "Disrupting Shot|crossbow_mastery|interrupt|Physical|1.1|9|0|16|12|2|stun",
        "Frost Trap|cryomancy|field|Frost|0.45|7|3|20|18|7|chill",
        "Hunter's Focus|hunting|buff|Physical|0.3|0|0|18|24|10|empower",
        "Arrow Rain|archery|area|Physical|2.1|9|4|28|20|0|",
        "Wild Hunt|summoning|summon|Nature|2|0|0|40|60|60|",
    ],
    "rogue": [
        "Quick Cut|dagger_mastery|strike|Physical|1.1|1.8|0|5|1.5|0|",
        "Venom Blade|dagger_mastery|dot|Poison|0.35|2|0|8|6|6|poison",
        "Vanish|shadow_magic|stealth|Shadow|1|0|0|12|18|8|stealth",
        "Side Step|evasion|dash|Physical|1|4|0|8|7|0|",
        "Nerve Strike|dagger_mastery|interrupt|Physical|0.8|2|0|10|9|2|stun",
        "Knife Fan|dagger_mastery|cone|Physical|1.1|5|3|12|7|0|",
        "Shadow Dart|shadow_magic|projectile|Shadow|1.3|8|0|14|6|4|curse",
        "Smoke Guard|evasion|shield|Shadow|0.3|0|0|12|16|5|guard",
        "Life Theft|shadow_magic|drain|Shadow|1.5|3|0|18|10|0|",
        "Hamstring|dagger_mastery|strike|Physical|1|2|0|12|10|3|root",
        "Deadly Intent|dagger_mastery|buff|Physical|0.3|0|0|14|20|8|empower",
        "Venom Cloud|alchemy|field|Poison|0.5|6|3|22|18|7|poison",
        "Crossing Blades|dagger_mastery|line|Physical|1.8|6|1|20|14|0|",
        "Nightfall|shadow_magic|area|Shadow|1.8|6|4|28|22|5|curse",
        "Assassin's Mark|dagger_mastery|strike|Physical|3.2|2|0|35|50|5|vulnerable",
    ],
    "arcanist": [
        "Ember Bolt|pyromancy|projectile|Fire|1.05|9|0|6|2|3|burn",
        "Frost Lance|cryomancy|line|Frost|1.2|9|1|10|5|4|chill",
        "Spark Fan|stormcalling|cone|Lightning|1.1|6|4|12|6|0|",
        "Arcane Ward|arcane_magic|shield|Arcane|0.3|0|0|14|15|6|guard",
        "Blink|arcane_magic|dash|Arcane|1|5|0|12|10|0|",
        "Flame Ring|pyromancy|area|Fire|1.3|0|3|16|8|5|burn",
        "Counterspell|arcane_magic|interrupt|Arcane|0.6|8|0|12|10|2|stun",
        "Winter Ground|cryomancy|field|Frost|0.4|8|3|22|14|7|chill",
        "Thunder Line|stormcalling|line|Lightning|1.7|11|1|20|9|0|",
        "Arcane Exposure|arcane_magic|dot|Arcane|0.35|9|0|18|12|7|vulnerable",
        "Stone Mantle|geomancy|shield|Physical|0.5|0|0|25|24|8|guard",
        "Cleanse Magic|radiance|purge|Radiant|1|6|0|18|12|0|",
        "Astral Ally|summoning|summon|Arcane|1|0|0|30|35|40|",
        "Firestorm|pyromancy|field|Fire|0.8|9|4|35|25|8|burn",
        "Convergence|arcane_magic|area|Arcane|3|9|5|50|60|5|vulnerable",
    ],
    "warden": [
        "Thorn Dart|nature_magic|projectile|Nature|1.05|8|0|6|2|0|",
        "Renewal|restoration|heal|Nature|1.2|7|0|10|5|0|",
        "Root Grasp|nature_magic|dot|Nature|0.25|7|0|10|8|5|root",
        "Call Companion|summoning|summon|Nature|1|0|0|18|25|35|",
        "Barkskin|nature_magic|shield|Nature|0.35|0|0|12|16|7|guard",
        "Vine Sweep|nature_magic|cone|Nature|1.1|5|3|14|7|3|root",
        "Wisp Step|arcane_magic|dash|Nature|1|4|0|12|10|0|",
        "Spore Ground|nature_magic|field|Poison|0.45|7|3|18|12|7|poison",
        "Purifying Sap|restoration|purge|Nature|1|7|0|16|10|0|",
        "Stone Root|geomancy|line|Physical|1.4|7|1|18|10|3|root",
        "Forest Rebuke|nature_magic|interrupt|Nature|0.8|7|0|14|10|2|stun",
        "Lifebloom|restoration|heal|Nature|2.2|7|0|28|12|0|",
        "Wild Strength|animal_handling|buff|Nature|0.3|0|0|18|24|10|empower",
        "Ancient Grove|nature_magic|field|Nature|0.65|8|4|30|25|10|root",
        "Heart of the Forest|summoning|summon|Nature|2.5|0|0|45|60|70|",
    ],
    "templar": [
        "Oath Strike|mace_mastery|strike|Radiant|1.15|2|0|6|2|0|",
        "Mending Light|restoration|heal|Radiant|1.3|7|0|10|5|0|",
        "Consecrated Shield|shield_mastery|shield|Radiant|0.35|0|0|12|14|7|guard",
        "Judgment|radiance|projectile|Radiant|1.3|8|0|12|6|0|",
        "Cleanse|restoration|purge|Radiant|1|7|0|12|8|0|",
        "Pilgrim's Step|radiance|dash|Radiant|1|4|0|12|11|0|",
        "Rebuke|mace_mastery|interrupt|Radiant|0.8|3|0|12|9|2|stun",
        "Sanctuary|radiance|field|Radiant|0.4|6|3|20|16|8|burn",
        "Vow of Courage|resolve|buff|Radiant|0.25|0|0|14|20|9|empower",
        "Beacon|radiance|taunt|Radiant|1|7|0|14|12|5|",
        "Dawn Sweep|mace_mastery|cone|Radiant|1.4|4|3|18|10|0|",
        "Mercy|restoration|heal|Radiant|2.5|8|0|30|14|0|",
        "Hallowed Line|radiance|line|Radiant|1.9|9|1|24|12|0|",
        "Martyr's Guard|heavy_armor|shield|Radiant|0.55|0|0|28|30|10|guard",
        "Dawnfall|radiance|area|Radiant|2.8|8|5|45|60|5|burn",
    ],
    "spellblade": [
        "Runic Cut|swordsmanship|strike|Arcane|1.2|2|0|6|2|0|",
        "Blink Strike|arcane_magic|dash|Arcane|1|5|0|10|8|0|",
        "Flame Edge|pyromancy|cone|Fire|1.1|3|3|12|6|4|burn",
        "Rune Guard|runecasting|shield|Arcane|0.3|0|0|12|14|6|guard",
        "Frost Draw|cryomancy|line|Frost|1.25|6|1|14|7|4|chill",
        "Spell Sever|swordsmanship|interrupt|Arcane|0.9|3|0|12|9|2|stun",
        "Arcane Blade|arcane_magic|projectile|Arcane|1.4|8|0|14|7|0|",
        "Thunder Step|stormcalling|area|Lightning|1.3|0|3|18|10|0|",
        "Siphon|shadow_magic|drain|Shadow|1.4|4|0|18|10|0|",
        "Inscribed Ground|runecasting|field|Arcane|0.45|6|3|22|16|7|vulnerable",
        "Tempered Will|swordsmanship|buff|Arcane|0.28|0|0|18|22|9|empower",
        "Mending Rune|restoration|heal|Arcane|1.8|6|0|24|12|0|",
        "Spell Purge|radiance|purge|Radiant|1|6|0|18|12|0|",
        "Rift Cleave|swordsmanship|cone|Arcane|2|5|4|28|18|4|vulnerable",
        "Aether Rupture|runecasting|area|Arcane|3|8|5|45|60|5|vulnerable",
    ],
}


def build_rules() -> tuple[list[dict], list[dict], list[dict]]:
    skills = []
    for category, names in SKILL_GROUPS.items():
        for name in names.split("|"):
            ident = slug(name)
            action, benefit = SKILL_PURPOSES[ident]
            skills.append(dict(id=ident, name=name, category=category, action=action,
                               benefit=benefit, unlocks=[1, 10, 25, 50, 75, 100]))
    assert len(skills) == 60 and len({s["id"] for s in skills}) == 60
    classes, abilities = [], []
    attribute_keys = "strength dexterity intellect vitality spirit resolve luck".split()
    thresholds = [1, 1, 3, 5, 8, 10, 15, 20, 25, 30, 40, 50, 60, 75, 90]
    for name, role, passive, weapon, armor, stats, affinity in CLASS_ROWS:
        ident = slug(name)
        class_abilities = []
        for index, row in enumerate(KITS[ident]):
            n, skill, kind, element, power, reach, radius, cost, cooldown, duration, status = row.split("|")
            if skill == "resolve":
                skill = "radiance"
            aid = ident + "_" + slug(n)
            class_abilities.append(aid)
            physical = element == "Physical" and skill not in ("restoration", "geomancy")
            abilities.append(dict(id=aid, name=n, **{"class": ident}, skill=skill,
                requirement=thresholds[index], kind=kind, element=element, power=float(power),
                range=float(reach), radius=float(radius), mana=0 if physical else float(cost),
                stamina=float(cost) if physical else 0, cooldown=float(cooldown),
                duration=float(duration), status=status,
                description=f"{n}: {kind.replace('_', ' ')}; {element.lower()} effect. "
                            f"Range {reach} tiles. Cooldown {cooldown} seconds."
                            + (f" Applies {status} for {duration} seconds." if status else "")))
        classes.append(dict(id=ident, name=name, role=role, passive=passive,
            weapon="copper_" + weapon, armor="linen_chest" if armor == "light" else
            ("hide_chest" if armor == "medium" else "copper_chest"),
            affinity=affinity.split(","), stats=dict(zip(attribute_keys, stats)), abilities=class_abilities))
    assert len(abilities) == 120
    known = {s["id"] for s in skills}
    assert all(a["skill"] in known for a in abilities)
    return skills, classes, abilities
