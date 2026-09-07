"""Skill identities and class starting profiles."""

SKILL_GROUPS = {
    'Weapons': [('Swordsmanship','swordsmanship'),('Axe Mastery','axe_mastery'),('Mace Mastery','mace_mastery'),('Spear Mastery','spear_mastery'),('Dagger Mastery','dagger_mastery'),('Archery','archery'),('Crossbow Mastery','crossbow_mastery'),('Staff Mastery','staff_mastery'),('Wand Mastery','wand_mastery'),('Shield Mastery','shield_mastery'),('Unarmed Combat','unarmed_combat')],
    'Magic': [('Pyromancy','pyromancy'),('Cryomancy','cryomancy'),('Stormcalling','stormcalling'),('Geomancy','geomancy'),('Nature Magic','nature_magic'),('Shadow Magic','shadow_magic'),('Radiance','radiance'),('Arcane Magic','arcane_magic'),('Restoration','restoration'),('Summoning','summoning'),('Runecasting','runecasting')],
    'Survival': [('Light Armor','light_armor'),('Medium Armor','medium_armor'),('Heavy Armor','heavy_armor'),('Evasion','evasion'),('Endurance','endurance'),('Meditation','meditation'),('Hunting','hunting'),('Slayer','slayer'),('Survival','survival'),('Exploration','exploration')],
    'Gathering': [('Mining','mining'),('Woodcutting','woodcutting'),('Fishing','fishing'),('Farming','farming'),('Foraging','foraging'),('Herbalism','herbalism'),('Skinning','skinning'),('Excavation','excavation'),('Prospecting','prospecting'),('Treasure Hunting','treasure_hunting')],
    'Crafting': [('Smithing','smithing'),('Woodworking','woodworking'),('Fletching','fletching'),('Tailoring','tailoring'),('Leatherworking','leatherworking'),('Cooking','cooking'),('Alchemy','alchemy'),('Enchanting','enchanting'),('Runecrafting','runecrafting'),('Jewelcrafting','jewelcrafting'),('Carpentry','carpentry'),('Scribing','scribing'),('Tinkering','tinkering')],
    'Utility': [('Lockpicking','lockpicking'),('Bartering','bartering'),('Cartography','cartography'),('Animal Handling','animal_handling'),('Construction','construction')]
}

DETAILS = {
 'shield_mastery': ('Block hostile attacks with a shield.','Raises block chance and unlocks shield techniques.'),
 'light_armor': ('Take hostile damage while wearing light armor.','Unlocks cloth and light equipment and improves its protection.'),
 'medium_armor': ('Take hostile damage while wearing medium armor.','Unlocks leather and mail equipment and improves its protection.'),
 'heavy_armor': ('Take hostile damage while wearing heavy armor.','Unlocks plate equipment and improves its protection.'),
 'evasion': ('Evade a hostile attack.','Raises the chance to avoid attacks.'),
 'endurance': ('Fight, gather, and survive hostile attacks.','Improves stamina recovery.'),
 'meditation': ('Recover missing mana through meditation.','Improves passive and channeled mana recovery.'),
 'hunting': ('Defeat wild animals.','Unlocks hunting techniques and improves damage against animals.'),
 'slayer': ('Defeat creatures that still pose a challenge.','Unlocks dangerous contracts and improves damage against elite foes.'),
 'survival': ('Rest at a camp or gather during severe weather.','Improves recovery and reduces the cost of wilderness travel.'),
 'exploration': ('Enter an undiscovered region or map sector.','Unlocks travel routes and reduces waystone travel costs.'),
 'mining': ('Extract ore with a suitable pickaxe.','Unlocks harder ores and raises gathering yield.'),
 'woodcutting': ('Cut marked timber trees with an axe.','Unlocks stronger timber and raises gathering yield.'),
 'fishing': ('Fish from marked fishing waters with a rod.','Unlocks rare catches and raises gathering yield.'),
 'farming': ('Plant seeds and harvest mature crops.','Shortens crop growth and raises harvest yield.'),
 'foraging': ('Gather wild mushrooms, fruit, and fibers.','Unlocks scarce wild materials and raises gathering yield.'),
 'herbalism': ('Gather medicinal plants with a sickle.','Unlocks potent herbs and raises gathering yield.'),
 'skinning': ('Harvest a defeated animal with a skinning knife.','Unlocks resilient hides and raises material yield.'),
 'excavation': ('Excavate marked buried remains with a shovel.','Unlocks deeper artifact deposits and raises yield.'),
 'prospecting': ('Inspect an available ore seam.','Raises the chance to discover a gemstone.'),
 'treasure_hunting': ('Discover hidden caches and open treasure chests.','Unlocks treasure clues and advanced caches.'),
 'lockpicking': ('Open a locked chest with a lockpick.','Unlocks more complex chest mechanisms.'),
 'bartering': ('Complete purchases with merchants.','Reduces merchant purchase prices, within a fixed cap.'),
 'cartography': ('Explore a region and draw a chart with ink and parchment.','Records regional roads and discovered exits.'),
 'animal_handling': ('Tame, feed, and fight with a companion.','Unlocks stronger animal companions.'),
 'construction': ('Build a wilderness structure from its recipe.','Unlocks useful camps and crafting stations.')
}

CLASSES = [
 ('vanguard','Vanguard','Defensive melee','Disciplined Guard','copper_sword','linen_heavy_chest',['swordsmanship','shield_mastery','heavy_armor'],{'strength':13,'dexterity':8,'intellect':7,'vitality':15,'spirit':8,'resolve':15,'luck':5}),
 ('berserker','Berserker','Risk-based melee','Blood Fury','copper_greataxe','linen_medium_chest',['axe_mastery','mace_mastery','endurance'],{'strength':17,'dexterity':10,'intellect':5,'vitality':14,'spirit':6,'resolve':10,'luck':5}),
 ('ranger','Ranger','Ranged physical','Keen Trail','copper_bow','linen_medium_chest',['archery','crossbow_mastery','hunting'],{'strength':10,'dexterity':17,'intellect':8,'vitality':10,'spirit':9,'resolve':8,'luck':7}),
 ('rogue','Rogue','Ambush and mobility','Patient Blade','copper_dagger','linen_light_chest',['dagger_mastery','evasion','lockpicking'],{'strength':10,'dexterity':18,'intellect':9,'vitality':9,'spirit':7,'resolve':8,'luck':8}),
 ('arcanist','Arcanist','Elemental caster','Arcane Discipline','copper_staff','linen_light_chest',['pyromancy','cryomancy','arcane_magic'],{'strength':5,'dexterity':9,'intellect':19,'vitality':9,'spirit':14,'resolve':8,'luck':5}),
 ('warden','Warden','Nature and companions','Living Bond','copper_staff','linen_medium_chest',['nature_magic','summoning','animal_handling'],{'strength':9,'dexterity':10,'intellect':14,'vitality':11,'spirit':16,'resolve':9,'luck':5}),
 ('templar','Templar','Healing and support','Oath of Mercy','copper_mace','linen_heavy_chest',['radiance','restoration','shield_mastery'],{'strength':12,'dexterity':7,'intellect':11,'vitality':13,'spirit':16,'resolve':13,'luck':5}),
 ('spellblade','Spellblade','Melee and magic','Runebound Edge','copper_sword','linen_medium_chest',['swordsmanship','arcane_magic','runecasting'],{'strength':13,'dexterity':12,'intellect':14,'vitality':10,'spirit':10,'resolve':9,'luck':5})
]

def build(data):
    for group, entries in SKILL_GROUPS.items():
        for name, ident in entries:
            if ident in DETAILS:
                action, benefit = DETAILS[ident]
            elif group == 'Weapons':
                action = 'Deal valid damage with a matching weapon.'
                benefit = 'Improves matching weapon damage and unlocks equipment and techniques.'
            elif group == 'Magic':
                action = 'Use matching spells against valid threats or heal injured allies in combat.'
                benefit = 'Improves matching spell power and unlocks advanced spells.'
            else:
                action = 'Complete recipes at the appropriate crafting station.'
                benefit = 'Unlocks recipes and improves equipment quality.'
            data['skills'].append(dict(id=ident,name=name,category=group,action=action,benefit=benefit,unlocks=[1,10,25,50,75,100]))
    for ident,name,role,passive,weapon,armor,affinity,stats in CLASSES:
        data['classes'].append(dict(id=ident,name=name,role=role,passive=passive,weapon=weapon,armor=armor,affinity=affinity,stats=stats,abilities=[]))
