"""Distinct creature identities, anatomy references, behavior, and encounter roles."""
from copy import deepcopy
from .items import MATERIALS

# id, name, family, level, AI, anatomical construction
ROSTER = {
'plains': [
 ('field_rat','Field Rat','rat',1,'passive','animal:rat; pointed muzzle, rounded ears, low body, hairless curved tail'),
 ('wild_hare','Wild Hare','hare',1,'fleeing','animal:hare; long ears, large folded hind legs, short tail'),
 ('brush_fox','Brush Fox','fox',3,'territorial','animal:fox; narrow muzzle, upright ears, white chest, long brush tail'),
 ('goblin_forager','Goblin Forager','goblin',4,'ranged_kiter','humanoid:goblin; pointed ears, scavenged leather, woven basket, sling'),
 ('hay_golem','Hay Golem','construct',5,'guard','construct:hay; tied straw bundles, branch arms, sackcloth head, rope joints')],
'farmland': [
 ('granary_mouse','Granary Mouse','mouse',1,'fleeing','animal:mouse; round ears, compact body, thin curling tail'),
 ('walking_scarecrow','Walking Scarecrow','scarecrow',3,'ambusher','construct:scarecrow; crossbar shoulders, patched coat, straw-filled cuffs, sack face'),
 ('feral_boar','Feral Boar','boar',4,'territorial','animal:boar; barrel body, bristled ridge, tusks, short thick legs'),
 ('bandit_poacher','Bandit Poacher','bandit',6,'ranged_kiter','humanoid:human; hood, leather jerkin, hunting bow, quiver'),
 ('burrowing_weasel','Burrowing Weasel','weasel',2,'passive','animal:weasel; elongated spine, short legs, small ears, tapered tail')],
'forest': [
 ('red_deer','Red Deer','deer',6,'fleeing','animal:deer; long legs, branching antlers, pale rump, narrow hooves'),
 ('wood_spider','Wood Spider','spider',5,'ambusher','animal:spider; eight jointed legs, divided body, visible fangs'),
 ('pine_wolf','Pine Wolf','wolf',8,'pack_hunter','animal:wolf; deep chest, long muzzle, pointed ears, bushy lowered tail'),
 ('thorn_sprite','Thorn Sprite','sprite',9,'caster','spirit:plant; thorn limbs, leaf mantle, glowing seed head'),
 ('bark_beetle','Bark Beetle','beetle',7,'territorial','animal:beetle; paired wing cases, six legs, segmented antennae')],
'ancient_forest': [
 ('elder_stag','Elder Stag','stag',20,'territorial','animal:stag; massive branching antlers, heavy neck, hanging moss'),
 ('briar_wisp','Briar Wisp','wisp',22,'caster','spirit:thorn; suspended thorn cage surrounding a bright seed core'),
 ('root_walker','Root Walker','tree',24,'guard','construct:tree; split trunk, root feet, branch fingers, exposed growth rings'),
 ('moss_mantis','Moss Mantis','mantis',21,'ambusher','animal:mantis; folded raptorial forelegs, triangular head, leaf-shaped wing covers'),
 ('owlbear','Owlbear','owlbear',26,'berserker','animal:owlbear; ursine body, hooked beak, feathered face disc, heavy talons')],
'pine_forest': [
 ('horned_owl','Horned Owl','owl',25,'ambusher','animal:owl; broad wings, facial discs, ear tufts, hooked beak'),
 ('wolverine','Wolverine','wolverine',28,'berserker','animal:wolverine; stocky shoulders, broad paws, short ears, flank stripes'),
 ('black_bear','Black Bear','bear',30,'territorial','animal:bear; heavy torso, round ears, long claws, short muzzle'),
 ('resin_wasp','Resin Wasp','wasp',27,'pack_hunter','animal:wasp; narrow waist, two wing pairs, segmented abdomen, hooked legs'),
 ('stone_badger','Stone Badger','badger',29,'territorial','animal:badger; low broad body, striped face, digging foreclaws')],
'highlands': [
 ('mountain_goat','Mountain Goat','goat',16,'territorial','animal:goat; cloven hooves, upright horns, beard, heavy shoulder coat'),
 ('cliff_harpy','Cliff Harpy','harpy',18,'ranged_kiter','humanoid:avian; human torso, feathered forelimbs, taloned feet, tail fan'),
 ('rock_lizard','Rock Lizard','lizard',17,'ambusher','animal:lizard; flattened body, scaled back, five-toed feet, long tail'),
 ('kobold_slinger','Kobold Slinger','kobold',19,'ranged_kiter','humanoid:reptile; snout, scale plates, sling, small shield'),
 ('ogre_cook','Ogre Cook','ogre',23,'berserker','humanoid:ogre; broad shoulders, hanging apron, heavy cleaver, hooked cooking pot')],
'mountains': [
 ('ibex','Ibex','ibex',45,'territorial','animal:ibex; long ridged backward horns, cloven hooves, compact torso'),
 ('snow_leopard','Snow Leopard','leopard',48,'ambusher','animal:leopard; broad paws, low feline shoulders, very long spotted tail'),
 ('griffon','Griffon','griffon',52,'pack_hunter','animal:griffon; eagle head and wings, lion hindquarters, talons and tufted tail'),
 ('stone_gargoyle','Stone Gargoyle','gargoyle',50,'guard','construct:gargoyle; carved stone wings, crouched limbs, chipped face, masonry base'),
 ('ironback_tortoise','Ironback Tortoise','tortoise',46,'territorial','animal:tortoise; domed plated shell, stout scaled legs, blunt beak')],
'volcanic': [
 ('ash_moth','Ash Moth','moth',35,'fleeing','animal:moth; broad dusty wings, feathered antennae, curled proboscis'),
 ('fire_beetle','Fire Beetle','fire_beetle',38,'territorial','animal:beetle; glowing abdominal seams, hard wing cases, hooked antennae'),
 ('lava_salamander','Lava Salamander','salamander',42,'caster','animal:salamander; low amphibian body, broad head, tapering tail, fire-scarred skin'),
 ('obsidian_golem','Obsidian Golem','golem',55,'guard','construct:golem; angular glassy blocks, articulated stone joints, molten cracks'),
 ('ember_drake','Ember Drake','drake',60,'caster','animal:drake; reptile body, small wings, horned head, scaled tail')],
'tundra': [
 ('arctic_fox','Arctic Fox','arctic_fox',35,'ambusher','animal:fox; compact ears, thick rounded winter coat, short muzzle, heavy tail'),
 ('musk_ox','Musk Ox','ox',40,'territorial','animal:ox; sloping horns, shaggy curtain coat, broad head, stout hooves'),
 ('ice_worm','Ice Worm','worm',42,'ambusher','animal:worm; thick segmented tube, circular mouth, paired ice ridges'),
 ('snow_hound','Snow Hound','hound',38,'pack_hunter','animal:hound; long limbs, deep rib cage, drooping ears, curled fur ridge'),
 ('frost_revenant','Frost Revenant','revenant',45,'guard','undead:human; frozen armor, cracked helm, exposed skeletal hands, tattered cloak')],
'glacier': [
 ('polar_bear','Polar Bear','polar_bear',55,'berserker','animal:bear; long neck, small round ears, thick fur, wide paws'),
 ('glacier_crab','Glacier Crab','crab',58,'territorial','animal:crab; broad icy carapace, side-walking legs, unequal crushing claws'),
 ('white_wyrm','White Wyrm','wyrm',65,'caster','animal:wyrm; long sinuous reptile body, swept horns, paired forelimbs, icy fins'),
 ('ice_elemental','Ice Elemental','elemental',60,'caster','elemental:ice; interlocking translucent crystals, suspended core, splintered limbs'),
 ('rime_wraith','Rime Wraith','wraith',62,'ambusher','undead:spirit; hooded upper body, ragged floating shroud, frozen finger bones')],
'wetlands': [
 ('reed_heron','Reed Heron','heron',22,'fleeing','animal:heron; very long legs, folded neck, straight bill, compact folded wings'),
 ('mudskipper','Mudskipper','mudskipper',23,'territorial','animal:mudskipper; raised eyes, broad pectoral fins, wet tapered body'),
 ('marsh_leech','Marsh Leech','leech',25,'ambusher','animal:leech; flattened annulated body, broad suckers, moist highlights'),
 ('reed_serpent','Reed Serpent','serpent',27,'ambusher','animal:snake; coiled body, narrow head, ventral scales, flicking tongue'),
 ('fungal_hermit','Fungal Hermit','hermit',29,'healer','humanoid:fungal; shell-like mushroom cap, bent legs, spore staff, hanging roots')],
'swamp': [
 ('swamp_crocodile','Swamp Crocodile','crocodile',18,'ambusher','animal:crocodile; long toothed jaw, armored back ridges, heavy tail, splayed feet'),
 ('giant_toad','Giant Toad','toad',20,'territorial','animal:toad; squat warty body, broad mouth, powerful folded hind legs'),
 ('poison_frog','Poison Frog','frog',21,'ranged_kiter','animal:frog; smooth patterned skin, adhesive toe discs, large eyes'),
 ('bog_ghoul','Bog Ghoul','ghoul',24,'aggressive','undead:human; exposed ribs, elongated hands, broken jaw, hanging marsh cloth'),
 ('bloated_tick','Bloated Tick','tick',22,'ambusher','animal:tick; swollen oval abdomen, eight short legs clustered near the head')],
'coast': [
 ('sand_crab','Sand Crab','sand_crab',12,'territorial','animal:crab; compact shell, two visible claws, four pairs of walking legs'),
 ('sea_turtle','Sea Turtle','turtle',15,'passive','animal:turtle; flattened shell, broad front flippers, smaller rear flippers'),
 ('reef_skimmer','Reef Skimmer','skimmer',16,'ranged_kiter','animal:bird; narrow wings, forked tail, long contrasting bill'),
 ('pirate_cutthroat','Pirate Cutthroat','pirate',19,'aggressive','humanoid:human; salt-stained coat, wrapped head, curved saber, belt pouches'),
 ('brine_horror','Brine Horror','horror',25,'caster','monster:marine; barnacled torso, hooked tentacles, crusted shell plates')],
'archipelago': [
 ('hermit_crab','Hermit Crab','hermit_crab',32,'territorial','animal:crab; spiral borrowed shell, protruding claw, eyestalks, exposed jointed legs'),
 ('storm_gull','Storm Gull','gull',34,'pack_hunter','animal:gull; long pointed wings, hooked bill, webbed feet'),
 ('island_macaque','Island Macaque','monkey',36,'ranged_kiter','animal:primate; grasping hands, visible muzzle, curved tail, upright shoulders'),
 ('coral_construct','Coral Construct','coral',40,'guard','construct:coral; branching coral crown, porous body, crab-like stone feet'),
 ('shore_wyvern','Shore Wyvern','wyvern',45,'caster','animal:wyvern; two hind legs, wing forelimbs, long rudder tail, horned jaw')],
'badlands': [
 ('dune_scorpion','Dune Scorpion','scorpion',32,'ambusher','animal:scorpion; pincers, eight legs, segmented raised tail, sting'),
 ('horned_viper','Horned Viper','viper',34,'ambusher','animal:snake; broad triangular head, small brow horns, thick coiled body'),
 ('sand_vulture','Sand Vulture','vulture',36,'pack_hunter','animal:vulture; bare head, hooked beak, broad primary feathers, ruff'),
 ('dust_armadillo','Dust Armadillo','armadillo',35,'territorial','animal:armadillo; banded shell, elongated snout, short digging claws'),
 ('dust_djinn','Dust Djinn','djinn',42,'caster','spirit:air; articulated upper body, wrapped head, tapering dust vortex')],
'wasteland': [
 ('bone_jackal','Bone Jackal','jackal',40,'pack_hunter','undead:canine; rib cage, long muzzle, pointed ears, exposed leg bones'),
 ('plague_crow','Plague Crow','crow',42,'ranged_kiter','animal:crow; heavy black beak, ragged feathers, narrow tail fan'),
 ('headless_knight','Headless Knight','knight',48,'guard','undead:armored; empty neck ring, plate armor, long sword, shield'),
 ('skeletal_horse','Skeletal Horse','horse',46,'berserker','undead:horse; long skull, arched spine, exposed ribs, articulated hooves'),
 ('grave_worm','Grave Worm','grave_worm',44,'ambusher','animal:worm; segmented armored body, shovel-like mouth plates, side bristles')],
'crystal': [
 ('crystal_beetle','Crystal Beetle','crystal_beetle',55,'territorial','animal:beetle; faceted wing cases, long antennae, six clearly jointed legs'),
 ('quartz_spider','Quartz Spider','quartz_spider',58,'ambusher','animal:spider; translucent abdomen, eight angular legs, clustered eyes'),
 ('prism_golem','Prism Golem','prism',62,'guard','construct:crystal; geometric torso, separate prism arms, visible internal refraction'),
 ('geode_sprite','Geode Sprite','geode',60,'healer','spirit:stone; open geode shell around a luminous inner figure'),
 ('shard_bat','Shard Bat','bat',57,'pack_hunter','animal:bat; membrane wings with finger supports, large ears, small clawed feet')],
'fungal': [
 ('spore_moth','Spore Moth','spore_moth',45,'caster','animal:moth; rounded patterned wings, fungal nodules, feathery antennae'),
 ('myconid_stalker','Myconid Stalker','myconid',48,'ambusher','humanoid:fungus; tall gilled cap, stalk torso, fibrous limbs, hanging veil'),
 ('cavern_snail','Cavern Snail','snail',46,'passive','animal:snail; spiral shell, broad muscular foot, two pairs of tentacles'),
 ('lantern_fungus','Lantern Fungus','fungus',50,'healer','plant:fungus; glowing gills, layered caps, root-like support feet'),
 ('hollow_centipede','Hollow Centipede','centipede',52,'pack_hunter','animal:centipede; flattened segmented body, paired legs on each segment, venom claws')],
'ruins': [
 ('stone_guardian','Stone Guardian','guardian',65,'guard','construct:statue; carved armor plates, block joints, square plinth feet, worn inscriptions'),
 ('rune_arachnid','Rune Arachnid','automaton',68,'caster','construct:spider; brass body, eight hinged legs, rune plate, glass eye'),
 ('gilded_scarab','Gilded Scarab','scarab',66,'territorial','animal:scarab; rounded wing covers, shovel head, plated antennae, six legs'),
 ('armored_skeleton','Armored Skeleton','skeleton',70,'guard','undead:human; visible skull and bones, rusted breastplate, broken spear'),
 ('coffer_mimic','Coffer Mimic','mimic',72,'ambusher','monster:chest; wooden boards, iron bands, hinged tooth-lined lid, tongue and rooted legs')],
'arcane_anomaly': [
 ('rift_manta','Rift Manta','manta',75,'ranged_kiter','monster:floating ray; broad triangular fins, open gill vents, long whip tail'),
 ('arcane_sentinel','Arcane Sentinel','sentinel',78,'caster','construct:armor; hollow helm, floating articulated armor plates, rotating rune rings'),
 ('mirror_phantom','Mirror Phantom','phantom',80,'ambusher','spirit:humanoid; fractured reflective body, separate floating shards, defined face and hands'),
 ('void_cuttle','Void Cuttle','cuttle',82,'summoner','monster:cephalopod; mantle, lateral fins, eight short arms and two long tentacles'),
 ('spell_wisp','Spell Wisp','spell_wisp',85,'caster','spirit:rune; nested articulated rings surrounding a suspended bright core')]
}

BOSSES = [
 ('millbreaker','Millbreaker, the Red Tusk','boar',6,'farmland',['charge','cone','stomp'],'A scarred boar has driven the mill workers from the western road.'),
 ('bell_warden','The Bell Warden','knight',10,'ruins',['line','ring','interruptible'],'An empty suit of armor still answers the ruined chapel bell.'),
 ('mother_of_silk','Mother of Silk','spider',15,'forest',['poison_field','summon','root'],'Her web supports the ceiling of a buried toll house.'),
 ('bracken_king','The Bracken King','tree',22,'ancient_forest',['cone','root','summon'],'A walking tree carries the iron crown of a forgotten forester.'),
 ('kilnheart','Kilnheart','golem',28,'volcanic',['circle','ring','interruptible'],'The foundry core has fused itself into a moving stone shell.'),
 ('sable_matron','Sable Matron','owlbear',32,'pine_forest',['charge','cone','summon'],'A feathered beast nests above the old northern watch road.'),
 ('saltjaw','Saltjaw','crocodile',35,'swamp',['charge','poison_field','ring'],'Broken harbor chains hang from this ancient crocodile\'s jaw.'),
 ('captain_neris','Captain Neris, the Unmoored','pirate',38,'coast',['line','summon','interruptible'],'Her crew never left the wreck whose bell still rings below the cliffs.'),
 ('ivory_librarian','The Ivory Librarian','skeleton',42,'ruins',['line','summon','ring'],'A skeletal scholar guards records that name the builders of the Deepways.'),
 ('glasswing','Glasswing','moth',46,'crystal',['cone','field','interruptible'],'A great moth has grown translucent wings among the crystal furnaces.'),
 ('dune_regent','The Dune Regent','scorpion',50,'badlands',['charge','poison_field','summon'],'Its armored tail rises above the buried caravan road.'),
 ('chorus_below','The Chorus Below','fungus',54,'fungal',['summon','field','interruptible'],'Several enormous fruiting bodies speak with the voices of lost miners.'),
 ('winterhorn','Winterhorn','ox',58,'tundra',['charge','ring','cone'],'A horned guardian has blocked the last northern supply path.'),
 ('rime_abbess','The Rime Abbess','wraith',62,'glacier',['line','ring','summon'],'A frozen spirit keeps vigil in the submerged glacier shrine.'),
 ('cinder_marshal','The Cinder Marshal','revenant',66,'volcanic',['cone','field','interruptible'],'The marshal\'s armor carries fire from the war that sealed Emberhold\'s lower gates.'),
 ('reef_colossus','The Reef Colossus','coral',70,'archipelago',['ring','summon','line'],'A coral-covered sentinel rises where the lost harbor once stood.'),
 ('hollow_crown','The Hollow Crown','phantom',75,'wasteland',['summon','cone','interruptible'],'A crown and a cloak hold together the memory of a vanished ruler.'),
 ('prism_archon','The Prism Archon','prism',80,'crystal',['line','ring','field'],'Light bends around its articulated crystal body and leaves false paths behind.'),
 ('the_unwritten','The Unwritten','cuttle',88,'arcane_anomaly',['summon','field','interruptible'],'An entity that erases inscriptions now hunts the people who can read them.'),
 ('aether_heart','The Aether Heart','sentinel',98,'arcane_anomaly',['ring','line','summon'],'The broken engine below Kairnfall has assembled a body from its own guardians.')
]

ELEMENTS={'volcanic':'Fire','glacier':'Frost','tundra':'Frost','swamp':'Poison','wetlands':'Poison','ancient_forest':'Nature','fungal':'Nature','crystal':'Arcane','ruins':'Physical','arcane_anomaly':'Arcane','wasteland':'Shadow'}


def make_creature(ident,name,family,level,ai,anatomy,biome,boss=False,elite=False,lore='',attacks=None):
    element=ELEMENTS.get(biome,'Physical')
    armor=round(level*0.65 + (8 if family in {'golem','guardian','sentinel','tortoise','knight','prism','coral'} else 0),1)
    health=round((24+level*11+level*level*0.08)*(6 if boss else 2.0 if elite else 1),1)
    damage=round((4+level*1.8)*(1.5 if boss else 1.2 if elite else 1),1)
    speed=2.7 if ai in {'pack_hunter','ambusher'} else 1.8 if family in {'golem','tree','snail','tortoise','guardian'} else 2.2
    reach=6 if ai in {'caster','ranged_kiter','healer','summoner'} else 1.6
    material=next((row for row in reversed(MATERIALS) if row[2]<=level),MATERIALS[0])
    weapon=material[0]+'_'+('staff' if ai in {'caster','healer','summoner'} else 'dagger' if ai=='ambusher' else 'sword')
    drops=['raw_meat','raw_hide'] if anatomy.startswith('animal:') else ['bone','rune_dust'] if anatomy.startswith('undead:') else [material[0]+'_ore','ancient_fragment'] if anatomy.startswith('construct:') else ['rune_dust','ectoplasm'] if anatomy.startswith('spirit:') else ['cured_leather','thread']
    if family in {'spider','scorpion','viper','tick','centipede','frog'}: drops.append('venom_gland')
    if family in {'drake','wyvern','wyrm'}: drops.append('drake_scale')
    if biome in {'tundra','glacier'}: drops.append('frost_pelt')
    if level>=20: drops.append('rough_gem')
    drops.append(weapon)
    if boss or elite: drops.append('rune_'+('embers' if element=='Fire' else 'winter' if element=='Frost' else 'bulwark')+'_'+str(min(5,1+level//25)))
    resist={element:0.3} if element!='Physical' else {}
    opposite={'Fire':'Frost','Frost':'Fire','Nature':'Fire','Poison':'Radiant','Shadow':'Radiant','Arcane':'Physical'}.get(element)
    if opposite: resist[opposite]=-0.2
    return dict(id=ident,name=name,family=family,level=level,ai='boss' if boss else ai,anatomy=anatomy,biome=biome,sprite='mobs/'+ident+'.png',boss=boss,elite=elite,health=health,power=damage,armor=armor,speed=speed,range=reach,aggro=7 if boss else 5,element=element,resistances=resist,gold=(8+level*5) if boss else 2+level*2,xp=30+level*8,attacks=attacks or [ai],drops=list(dict.fromkeys(drops)),lore=lore or name+' inhabits the '+biome.replace('_',' ')+'. Its body structure and behavior determine how it fights.')


def build(data):
    for biome,rows in ROSTER.items():
        for ident,name,family,level,ai,anatomy in rows:
            data['mobs'].append(make_creature(ident,name,family,level,ai,anatomy,biome))
    originals=list(data['mobs'])
    for i,mob in enumerate(originals[::4][:25]):
        elite=deepcopy(mob); elite['id']='rare_'+mob['id']; elite['name']=['Scarred','Ancient','Crested','Battle-worn','Runemarked'][i%5]+' '+mob['name']; elite['elite']=True; elite['health']*=2; elite['power']*=1.25; elite['gold']*=2; elite['xp']*=2; elite['sprite']='mobs/'+elite['id']+'.png'; elite['anatomy']+='; additional scars, trophies, or structural markings identify a rare variant'; elite['drops'].append('rune_precision_'+str(min(5,1+mob['level']//25))); data['mobs'].append(elite)
    for ident,name,family,level,biome,attacks,lore in BOSSES:
        base=next((x for x in originals if x['family']==family),originals[0])
        anatomy=base['anatomy']+'; enlarged articulated form with unique battle damage, armor, and landmark-scale silhouette'
        data['mobs'].append(make_creature(ident,name,family,level,'boss',anatomy,biome,True,False,lore,attacks))
