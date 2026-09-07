"""Skill emblems built from recognizable equipment and profession objects."""
from __future__ import annotations
from .common import Pixel, canvas, palette, INK
from .items import icon as item_icon

REFERENCES = {
 'swordsmanship':'copper_sword','axe_mastery':'copper_axe','mace_mastery':'copper_mace',
 'spear_mastery':'copper_spear','dagger_mastery':'copper_dagger','archery':'copper_bow',
 'crossbow_mastery':'copper_crossbow','staff_mastery':'copper_staff','wand_mastery':'copper_wand',
 'shield_mastery':'copper_shield','unarmed_combat':'copper_knuckles',
 'light_armor':'linen_light_chest','medium_armor':'linen_medium_chest','heavy_armor':'linen_heavy_chest',
 'mining':'copper_pickaxe','woodcutting':'woodcutters_axe','fishing':'field_rod',
 'farming':'wheat_seed','foraging':'fiber','herbalism':'sickle','skinning':'skinning_knife',
 'excavation':'shovel','prospecting':'rough_gem','smithing':'crafting_hammer',
 'woodworking':'oak_plank','fletching':'feather','tailoring':'thread',
 'leatherworking':'cured_leather','alchemy':'empty_vial','jewelcrafting':'polished_gem',
 'carpentry':'oak_log','scribing':'parchment','tinkering':'copper_crossbow',
 'lockpicking':'lockpick','enchanting':'rune_embers_1','runecrafting':'rune_stone',
}
MAGIC = {'pyromancy':'fire','cryomancy':'frost','stormcalling':'lightning','geomancy':'earth',
 'nature_magic':'leaf','shadow_magic':'moon','radiance':'sun','arcane_magic':'star',
 'restoration':'hand','summoning':'paw','runecasting':'rune'}
OTHER = {'evasion','endurance','meditation','hunting','slayer','survival','exploration',
 'treasure_hunting','cooking','bartering','cartography','animal_handling','construction'}
COLORS = {'fire':'d38958','frost':'9dc3c7','lightning':'d5c086','earth':'a49474',
 'leaf':'97b07b','moon':'ac97ba','sun':'dec995','star':'aaaed0','hand':'c6b799',
 'paw':'b99e78','rune':'a8bebb'}

def icon(payload):
    skill=payload['skill']; reference=payload.get('reference')
    if reference is not None:
        image=item_icon(reference)
        if skill=='prospecting':
            p=Pixel(image); p.ellipse((3,17,14,28),(0,0,0,0),'c6ad73',2); p.line([(12,27),(17,31)],'a78c63',3)
        return image
    image=canvas((32,32)); p=Pixel(image)
    if skill in MAGIC:
        shape=MAGIC[skill]; c=palette(COLORS[shape])
        if shape=='fire':
            p.poly([(16,2),(18,10),(24,7),(23,15),(28,19),(26,27),(20,30),(11,29),(5,24),(7,16),(11,11),(11,19),(15,13)],c[2])
            p.poly([(17,13),(18,21),(22,19),(23,26),(17,29),(11,26),(12,20)],c[4]); p.poly([(17,22),(19,28),(15,28)],c[5])
        elif shape=='frost':
            for a,b in [((16,3),(16,29)),((5,9),(27,23)),((5,23),(27,9))]: p.line([a,b],c[3],3); p.line([a,b],c[5])
            for y in (7,25):
                sign=1 if y<16 else -1; p.line([(11,y),(16,y+sign*4),(21,y)],c[4],2)
        elif shape=='lightning':
            p.poly([(18,2),(8,17),(15,17),(11,30),(26,12),(19,13),(24,2)],c[3]); p.line([(18,5),(12,14),(18,14),(15,24)],c[5],2)
        elif shape=='earth':
            p.poly([(4,26),(9,14),(17,7),(26,11),(29,24),(22,29),(11,29)],c[2]); p.poly([(10,15),(17,9),(23,12),(17,22),(7,24)],c[4]); p.line([(18,22),(26,24)],c[0]); p.line([(16,23),(13,28)],c[0])
        elif shape=='leaf':
            p.poly([(7,26),(5,18),(10,8),(25,3),(27,12),(22,22),(13,27)],c[3]); p.line([(5,29),(23,7)],c[5],2)
            for x,y in [(11,22),(16,16),(20,11)]: p.line([(x,y),(x-4,y-7)],c[1]); p.line([(x,y),(x+7,y-1)],c[4])
        elif shape=='moon':
            p.poly([(21,3),(12,6),(7,14),(8,23),(15,29),(24,27),(28,21),(22,24),(16,21),(13,14),(15,8)],c[3]); p.line([(19,5),(12,11),(11,19),(16,25)],c[5])
        elif shape in {'sun','star'}:
            points=[(16,2),(19,11),(29,7),(23,16),(30,23),(20,22),(16,30),(12,22),(3,25),(9,16),(3,8),(12,10)]
            p.poly(points,c[3]); p.sphere((10,10,22,23),c[4]); p.line([(12,13),(15,11),(19,12)],c[5])
            if shape=='star': p.poly([(16,7),(20,16),(16,25),(12,16)],c[1]); p.line([(16,9),(16,23)],c[5])
        elif shape in {'hand','paw'}:
            p.sphere((10,15,23,28),c[3])
            for x,y in [(8,12),(13,7),(19,7),(25,12)]:
                p.sphere((x-3,y-3,x+3,y+4),c[3]); p.line([(x-1,y-2),(x,y-2)],c[5])
            if shape=='hand': p.line([(12,20),(17,22),(20,18)],c[1]); p.line([(13,25),(19,25)],c[4])
        else:
            p.poly([(10,4),(22,4),(27,10),(26,25),(21,29),(8,27),(5,12)],c[2]); p.line([(10,8),(15,6),(22,9)],c[4]); p.line([(15,10),(15,23),(21,19),(10,15),(20,11)],c[5],2)
        return image
    if skill not in OTHER: raise ValueError('No authored icon mapping for skill: '+skill)
    if skill in {'exploration','cartography','treasure_hunting'}:
        p.poly([(4,7),(11,4),(22,8),(28,5),(28,25),(21,28),(11,24),(4,27)],'c1ad82')
        p.line([(11,6),(11,23)],'8d795b'); p.line([(22,9),(22,26)],'8d795b')
        p.line([(7,21),(9,17),(16,19),(18,13),(24,12)],'708675',2)
        p.poly([(6,14),(10,8),(14,14)],'927957'); p.poly([(17,23),(21,17),(26,23)],'a58c65')
        if skill=='treasure_hunting': p.line([(18,10),(23,15)],'a46752',2); p.line([(18,15),(23,10)],'a46752',2)
        elif skill=='cartography': p.line([(7,28),(24,6)],'4b6372',2); p.poly([(24,6),(27,4),(26,11)],'d1d6c1')
    elif skill=='bartering':
        for x,y in [(9,23),(15,20),(23,24),(13,13),(22,12)]:
            p.ellipse((x-5,y-3,x+5,y+4),'967344',INK); p.ellipse((x-5,y-4,x+5,y+2),'cfb473','7b623e'); p.line([(x-2,y-2),(x+2,y-2)],'eee0a7'); p.line([(x,y-2),(x,y)],'9a7a42')
    elif skill=='cooking':
        p.rect((7,23,25,27),'655647',INK); p.line([(8,29),(25,25)],'a1845d',3); p.line([(8,26),(25,29)],'977551',3)
        p.poly([(6,12),(27,12),(25,23),(21,26),(12,25),(8,22)],'697b85'); p.ellipse((6,8,27,15),'9faba9',INK); p.ellipse((9,10,24,13),'bf985f','4a5557'); p.line([(5,13),(2,14),(3,19),(7,18)],'a5aaa1',2); p.line([(23,6),(26,2)],'b19a75',3)
    elif skill=='construction':
        p.poly([(6,14),(25,14),(25,28),(6,28)],'b4a58a'); p.poly([(3,15),(16,3),(29,15)],'947765'); p.line([(5,14),(16,5),(27,14)],'d0b493',2); p.rect((14,19,20,28),'755c49',INK); p.rect((8,18,11,23),'8ea3a0',INK)
    elif skill in {'evasion','endurance'}:
        p.poly([(12,3),(21,3),(20,21),(28,24),(28,29),(9,29),(7,26),(10,19)],'987750'); p.line([(13,6),(13,20),(10,24),(24,26)],'c4a271',2); p.line([(8,28),(27,28)],'544638',2)
        if skill=='evasion':
            for y in (9,14,19): p.line([(2,y),(7,y)],'aaa992')
    elif skill in {'hunting','animal_handling'}:
        p.sphere((10,15,23,28),'b59a76')
        for x,y in [(7,14),(13,8),(20,8),(26,15)]: p.sphere((x-3,y-3,x+3,y+3),'b59a76')
        if skill=='animal_handling': p.line([(4,26),(9,30),(24,30),(29,26)],'829e87',2)
        else: p.line([(3,28),(27,4)],'aaa993',2); p.poly([(27,3),(23,6),(28,9)],'d1cbc0')
    elif skill=='slayer':
        p.sphere((7,4,25,23),'c5b99b'); p.rect((10,12,14,16),'41443d'); p.rect((19,12,22,16),'41443d'); p.poly([(16,17),(14,20),(18,20)],'655d50')
        for x in range(11,23,3): p.line([(x,22),(x,27)],'b7a985',2)
    elif skill=='meditation':
        p.sphere((12,3,21,13),'beac8b'); p.poly([(12,15),(22,15),(24,22),(30,27),(24,30),(16,27),(8,30),(2,26),(10,22)],'879a9a'); p.line([(13,16),(14,23),(9,26)],'bbbfaa',2); p.line([(20,17),(19,23),(24,26)],'5a7478',2)
    elif skill=='survival':
        p.line([(4,28),(27,23)],'87694e',4); p.line([(4,24),(27,29)],'a98a5b',4); p.poly([(9,23),(7,16),(12,11),(16,3),(18,12),(24,14),(25,21),(20,27),(13,26)],'c08554'); p.poly([(14,23),(13,17),(17,12),(18,20),(21,22),(17,26)],'dfc184')
    return image
