from __future__ import annotations
import math
from PIL import Image
from .common import Pixel,canvas,palette,rgba,shade,seed,METALS,WOODS,ELEMENT_COLORS,INK


def metal_for(item):
    key=item['id'].split('_')[0]
    return METALS.get(key,METALS.get(item.get('material',''),'a5afb5'))


def weapon_icon(item):
    image=canvas((32,32)); p=Pixel(image)
    tags=item.get('tags',[]); family=tags[0] if tags else item['id'].split('_')[-1]
    colors=palette(metal_for(item)); wood=palette(WOODS.get(item.get('material',''),'8d6846'))
    leather=palette('80523c')
    if family in {'sword','greatsword','dagger'}:
        top=2 if family=='greatsword' else 4 if family=='sword' else 10
        width=3 if family=='greatsword' else 2
        p.poly([(16,top),(16-width,top+5),(16-width,21),(16+width,21),(16+width,top+5)],colors[2])
        p.line([(16,top+2),(16,20)],colors[5]); p.line([(17,top+6),(17,20)],colors[1]); p.line([(15,top+6),(15,19)],colors[4])
        p.poly([(10,20),(13,19),(19,19),(22,20),(22,22),(18,21),(14,21),(10,22)],colors[3])
        p.rect((14,22,17,28),leather[2],INK)
        for y in (23,25,27): p.line([(15,y),(17,y-1)],leather[4])
        p.sphere((13,27,18,31),metal_for(item))
    elif family in {'axe','greataxe','halberd','pickaxe'}:
        p.limb((13,29),(18,5),3,'94734f')
        if family=='pickaxe':
            p.poly([(5,8),(13,5),(21,5),(29,9),(24,8),(18,8),(10,9)],colors[3]); p.line([(8,7),(20,5),(26,8)],colors[5])
        else:
            p.poly([(17,5),(22,5),(25,3),(28,5),(27,12),(24,15),(20,12),(16,12)],colors[2])
            p.poly([(25,4),(27,5),(26,11),(24,14),(23,12)],colors[5],None)
            p.line([(18,7),(22,7),(24,9)],colors[4])
            p.rect((16,6,19,12),colors[3],INK)
            if family=='greataxe':
                p.poly([(17,5),(12,5),(9,3),(6,5),(7,12),(10,15),(14,12),(17,12)],colors[2]); p.line([(8,5),(8,10),(10,13)],colors[5])
            if family=='halberd': p.poly([(19,0),(16,5),(18,8),(21,5)],colors[4])
        for y in (20,23,26): p.line([(12+(29-y)*.2,y),(15+(29-y)*.2,y)],leather[4])
    elif family in {'mace','greatmace','hammer'}:
        p.limb((14,29),(17,9),3,'87664b')
        if family=='greatmace' or family=='hammer':
            p.poly([(7,5),(21,3),(25,7),(24,14),(10,16),(6,12)],colors[1]); p.poly([(7,5),(20,4),(21,10),(8,12)],colors[3]); p.line([(8,6),(19,5)],colors[5]); p.line([(10,13),(23,11)],colors[2])
        else:
            p.sphere((11,4,23,16),metal_for(item))
            for dx in (-5,0,5): p.poly([(17+dx,3),(19+dx,7),(18+dx,16),(15+dx,14),(15+dx,7)],colors[3],INK)
            p.line([(16,4),(17,14)],colors[5])
    elif family=='spear':
        p.limb((13,30),(18,8),2,'94734f'); p.poly([(19,1),(14,9),(17,13),(21,9)],colors[3]); p.line([(19,3),(18,10)],colors[5]); p.line([(15,11),(21,12)],colors[2])
    elif family in {'bow','crossbow'}:
        if family=='bow':
            p.line([(11,3),(18,6),(22,13),(22,18),(18,25),(11,29)],INK,4)
            p.line([(11,3),(18,6),(22,13),(22,18),(18,25),(11,29)],wood[3],2)
            p.line([(12,4),(18,8),(21,14)],wood[5])
            p.line([(11,4),(11,28)],'d8d0b8'); p.rect((19,13,23,18),leather[2],INK)
            p.line([(6,16),(27,16)],'c7bfa0'); p.poly([(29,16),(25,14),(25,18)],colors[4]); p.line([(6,14),(8,16),(6,18)],'8fbdad')
        else:
            p.poly([(13,6),(18,6),(19,24),(16,30),(12,28),(14,20)],wood[3]); p.line([(15,8),(16,23)],wood[5])
            p.line([(3,8),(8,12),(16,14),(24,12),(29,8)],INK,4); p.line([(3,8),(8,12),(16,14),(24,12),(29,8)],colors[3],2)
            p.line([(3,8),(16,21),(29,8)],'d8d0b8'); p.line([(16,3),(16,23)],'e0d6bb'); p.poly([(16,1),(13,5),(19,5)],colors[5])
    elif family=='wand':
        # A short tapered baton with a ferrule and small pointed focus, rather
        # than a shortened copy of the staff's large jewel cage.
        p.poly([(9,28),(12,30),(24,9),(23,5),(20,7)],wood[2])
        p.line([(11,27),(21,9)],wood[5])
        p.poly([(8,27),(11,30),(16,22),(13,20)],leather[2])
        for x,y in ((10,26),(12,23)):
            p.line([(x,y),(x+2,y+1)],leather[4])
        p.line([(14,19),(17,21)],colors[4],2)
        p.poly([(21,8),(24,3),(25,7),(23,11)],ELEMENT_COLORS.get(item.get('element','Arcane'),'b3a2d4'))
        p.dot(24,5,'fff0cf')
    elif family=='staff':
        top=5
        p.limb((12,29),(19,top+4),3,WOODS.get(item.get('material',''),'99734f'))
        p.line([(12,27),(15,20),(15,15)],wood[5]); p.line([(14,28),(16,21),(18,14)],wood[1])
        p.poly([(16,top+7),(14,top+2),(17,top-2),(23,top-1),(25,top+3),(22,top+7)],colors[2])
        gem=ELEMENT_COLORS.get(item.get('element','Arcane'),'b3a2d4')
        p.poly([(19,top-1),(23,top+2),(20,top+6),(16,top+3)],gem)
        p.line([(19,top),(17,top+3),(20,top+4)],shade(gem,1.3,15))
        p.dot(20,top+1,'fff0cf')
    elif family=='tome':
        p.poly([(5,6),(22,3),(27,7),(27,27),(10,30),(5,26)],leather[1]); p.poly([(9,7),(24,5),(25,25),(9,28)],'806c95')
        p.rect((6,8,9,26),leather[3],INK)
        for y in (10,13,16,19,22,25): p.line([(25,y),(27,y-1)],'e1d3aa')
        p.poly([(17,10),(22,15),(17,21),(12,16)],'cbb675'); p.line([(17,12),(17,19)],'eee0b1'); p.rect((22,15,29,18),colors[2],INK)
    elif family=='knuckles':
        p.poly([(6,10),(22,7),(28,12),(28,21),(10,27),(5,21)],leather[2]); p.poly([(8,11),(23,9),(25,13),(10,17)],colors[3]);
        for x,y in [(10,12),(15,11),(20,10),(24,12)]: p.sphere((x-2,y-2,x+2,y+3),metal_for(item))
        p.line([(8,19),(24,15)],leather[5],2); p.line([(10,23),(24,19)],leather[1],2)
    elif family=='knife':
        p.poly([(20,3),(20,17),(15,22),(12,20),(16,15)],colors[3]); p.line([(19,5),(18,15),(14,20)],colors[5]); p.limb((13,22),(7,29),4,'83543d')
    elif family=='sickle':
        p.limb((9,29),(14,18),4,'936b48'); p.poly([(13,19),(11,15),(12,8),(17,3),(24,3),(28,7),(25,6),(20,6),(16,10),(16,16)],colors[3]); p.line([(13,14),(14,8),(19,4),(24,4)],colors[5])
    elif family=='shovel':
        p.limb((16,8),(16,23),3,'94734f'); p.poly([(11,20),(21,20),(22,25),(17,31),(11,27)],colors[3]); p.line([(12,22),(17,28),(20,25)],colors[5]); p.rect((12,2,20,8),wood[3],INK); p.rect((14,3,18,6),(0,0,0,0))
    elif family=='rod':
        p.line([(8,29),(12,19),(17,8),(22,2)],INK,3); p.line([(8,28),(13,18),(18,7),(22,2)],'b2925e',2); p.line([(22,2),(27,12),(26,22)],'c0c6bb'); p.sphere((24,21,28,25),'d78461'); p.sphere((9,19,15,24),'8b9699')
    else:
        p.plank((11,6,20,27),'94734f'); p.rect((8,5,24,11),colors[3],INK)
    return image


def armor_icon(item):
    image=canvas((32,32)); p=Pixel(image); slot=item.get('slot','chest'); weight=next((x for x in item.get('tags',[]) if x in {'light','medium','heavy'}),'medium')
    base='647c8c' if weight=='light' else '98714b' if weight=='medium' else metal_for(item)
    tier=item['id'].split('_')[0]
    accents={'linen':'728a79','wool':'807286','silk':'8c5567','moonweave':'8896b0','frostweave':'8ab2b5','duskweave':'745d84','aetherweave':'b3a2c8'}
    if weight=='light': base=accents.get(tier,base)
    c=palette(base)
    if slot=='chest':
        p.poly([(8,5),(12,4),(13,8),(19,8),(20,4),(24,5),(29,12),(24,16),(22,13),(23,28),(9,28),(10,13),(8,16),(3,12)],c[2]);
        p.poly([(12,10),(19,10),(21,24),(11,24)],c[3],None); p.line([(12,10),(12,22)],c[4]); p.line([(20,11),(20,26)],c[1])
        if weight=='heavy':
            p.poly([(10,10),(15,9),(21,10),(20,19),(16,22),(11,19)],c[4]); p.line([(16,10),(16,21)],c[1]);
            for y in (22,25): p.line([(10,y),(22,y)],c[1]); p.line([(10,y+1),(21,y+1)],c[4])
            for x in (7,24): p.sphere((x-3,5,x+3,11),base)
        elif weight=='medium':
            for x in (13,18):
                for y in (12,16,20): p.dot(x,y,c[5])
            p.line([(16,10),(16,23)],c[0]); p.rect((10,23,22,25),'604839',INK); p.rect((15,22,18,26),'c8ad6b',INK)
        else:
            p.poly([(11,22),(21,22),(25,30),(7,30)],c[2]); p.line([(13,22),(12,29)],c[4]); p.line([(18,22),(20,29)],c[1]); p.line([(10,11),(16,17),(22,11)],'d0bf8d')
    elif slot=='helmet':
        p.sphere((5,4,26,26),base); p.poly([(5,14),(10,12),(22,12),(27,15),(26,25),(21,28),(20,21),(11,21),(10,28),(5,25)],c[2]);
        p.rect((10,14,21,18),'2a2c34'); p.line([(8,12),(24,12)],c[5]); p.rect((15,5,17,22),c[4]);
        if weight=='light': p.poly([(5,19),(7,5),(15,1),(24,5),(28,21),(23,15),(20,9),(12,9),(8,16)],c[3])
    elif slot=='gloves':
        for dx in (0,14):
            p.poly([(3+dx,8),(10+dx,7),(13+dx,17),(10+dx,26),(5+dx,27),(1+dx,20)],c[2]); p.rect((3+dx,7,10+dx,12),c[4],INK); p.line([(5+dx,14),(6+dx,24)],c[4]); p.line([(9+dx,15),(9+dx,24)],c[1])
    elif slot=='legs':
        p.poly([(7,3),(25,3),(24,27),(17,29),(16,14),(13,29),(5,27)],c[2]); p.line([(9,6),(9,25)],c[4],2); p.line([(20,6),(20,26)],c[4],2); p.rect((7,3,24,6),'644c3b',INK)
        if weight=='heavy':
            for x in (9,21): p.sphere((x-3,15,x+3,20),base)
    elif slot=='boots':
        for dx in (0,15):
            p.poly([(5+dx,4),(12+dx,4),(12+dx,21),(14+dx,25),(12+dx,28),(2+dx,28),(1+dx,24),(5+dx,21)],c[2]); p.line([(6+dx,6),(6+dx,20)],c[4]); p.line([(3+dx,25),(12+dx,25)],c[4]); p.line([(2+dx,28),(13+dx,28)],c[0],2)
            for y in (10,14,18): p.line([(8+dx,y),(11+dx,y-1)],c[1])
    elif slot=='cloak':
        p.poly([(11,3),(20,3),(23,8),(29,29),(19,27),(14,30),(3,28),(8,9)],c[2]); p.poly([(13,6),(18,6),(20,26),(14,28),(9,26)],c[3],None); p.line([(12,8),(8,25)],c[4]); p.line([(20,10),(25,27)],c[1]); p.sphere((13,5,18,9),'c8ad6b')
    else:
        p.poly([(2,12),(28,8),(30,16),(3,21)],'77523b'); p.line([(4,13),(27,10)],'b1895b'); p.rect((12,10,21,19),'c8ad6b',INK); p.rect((14,12,19,17),'624731',INK); p.line([(14,15),(22,15)],'e0ce91');
        for x in (5,8,25,28): p.dot(x,16-x//8,INK)
    return image


def icon(item):
    kind=item['type']; ident=item['id']; mat=item.get('material','');
    if kind in {'weapon','tool'}: return weapon_icon(item)
    if kind=='armor': return armor_icon(item)
    image=canvas((32,32)); p=Pixel(image); metal=palette(metal_for(item)); wood=palette('99734f')
    if kind=='offhand':
        family=item['tags'][0]
        if family=='shield':
            p.poly([(4,5),(16,2),(28,5),(26,19),(16,30),(6,19)],metal[2]); p.poly([(7,7),(16,5),(25,7),(23,18),(16,26),(9,18)],'526f80'); p.line([(16,5),(16,25)],metal[5],2); p.line([(8,11),(24,11)],metal[4]); p.sphere((12,9,20,17),metal_for(item));
            for x,y in [(6,6),(26,6),(16,27)]: p.dot(x,y,metal[5])
        elif family=='quiver':
            p.poly([(9,8),(23,5),(24,24),(16,30),(9,26)],'866449'); p.line([(10,10),(11,25)],'bd9565');
            for x in (12,16,20): p.line([(x,2),(x+2,17)],'bb9564'); p.poly([(x-2,2),(x,6),(x+2,2)],'b7c6bc')
        else:
            p.sphere((7,4,26,23),ELEMENT_COLORS.get(item.get('element','Arcane'),'b2a1c4')); p.poly([(7,23),(26,23),(24,27),(9,29)],metal[3]); p.line([(10,25),(23,24)],metal[5]); p.line([(11,9),(16,6),(20,8)],'e8e6cb',2)
    elif kind=='accessory':
        slot=item['slot']
        if slot=='ring':
            p.ellipse((7,9,25,28),metal[2],INK); p.ellipse((11,13,21,25),(0,0,0,0),metal[4]); p.poly([(12,4),(20,3),(25,10),(20,17),(12,16),(8,10)],metal[3]); p.poly([(15,5),(21,9),(18,14),(12,10)],'7096a7'); p.line([(15,6),(13,10),(18,12)],'cadfd9')
        else:
            p.line([(4,2),(5,11),(10,16),(22,16),(27,10),(28,2)],metal[4],2); p.line([(5,3),(7,11),(12,14),(21,14),(25,10)],metal[1]); p.poly([(16,14),(24,20),(20,28),(12,29),(8,21)],metal[3]); p.poly([(16,17),(21,21),(17,26),(12,23)],'907baf'); p.dot(15,19,'ede1b3')
    elif kind in {'potion','scroll'} or ident in {'empty_vial','ink'}:
        if kind=='scroll':
            p.plank((7,6,25,26),'c9b88e'); p.sphere((3,4,12,10),'d8c79a'); p.sphere((20,23,29,29),'d8c79a');
            for y in range(12,23,3): p.line([(11,y),(21,y)],'85735a')
        else:
            base='b95c54' if item.get('effect')=='heal' else '648ead' if item.get('effect')=='mana' else '729568'
            p.poly([(12,5),(20,5),(20,12),(26,18),(26,26),(22,29),(10,29),(6,25),(6,18),(12,12)],'a2bab7');
            p.poly([(9,18),(23,18),(24,25),(21,27),(11,27),(8,24)],base if ident!='empty_vial' else '76898d'); p.rect((11,3,21,7),'a38254',INK); p.line([(10,17),(9,23)],'dfede0',2); p.line([(14,9),(14,12)],'e0e9dd'); p.line([(11,19),(20,19)],shade(base,1.2,15)); p.rect((12,20,21,24),'d8c8a1',INK); p.line([(14,22),(19,22)],'886f57')
    elif kind=='rune':
        color=ELEMENT_COLORS.get(item.get('element','Physical'),'baac8b')
        p.poly([(8,3),(24,4),(29,13),(26,27),(14,30),(4,24),(3,11)],'59616a'); p.poly([(9,5),(22,6),(26,13),(23,24),(14,27),(7,22),(6,12)],'858c8e'); p.line([(8,8),(11,5),(21,6)],'bbc1b2')
        shape=seed(ident.rsplit('_',1)[0])%4
        strokes=[[(11,10),(21,10),(13,23),(21,23)],[(15,8),(10,16),(22,16),(16,24)],[(11,8),(21,13),(11,18),(21,24)],[(16,8),(9,19),(23,19),(16,8),(16,25)]][shape]
        p.line(strokes,shade(color,.45),3); p.line(strokes,color); p.dot(strokes[0][0],strokes[0][1],shade(color,1.2,20))
        for i in range(item.get('tier',1)): p.dot(10+i*3,27,'ddce9c')
    elif kind=='ore' or ident in {'ancient_fragment','relic_shard','coal','rune_stone'}:
        base='56525a' if ident=='coal' else '837d73'; p.poly([(3,23),(5,12),(12,5),(24,7),(29,18),(25,27),(12,29)],base); p.poly([(6,12),(12,7),(21,9),(15,18),(5,22)],shade(base,1.2)); p.poly([(15,18),(24,8),(27,18),(23,25)],shade(base,.75)); p.line([(12,7),(15,18),(12,27)],shade(base,.55))
        color=metal[4]
        for x,y in [(9,13),(19,12),(22,20),(11,23)]: p.poly([(x,y-2),(x+3,y),(x+1,y+3),(x-2,y+1)],color,shade(color,.6))
    elif ident.endswith('_bar'):
        p.poly([(4,12),(22,6),(29,11),(27,23),(10,29),(3,23)],metal[1]); p.poly([(5,12),(22,8),(27,12),(10,17)],metal[4]); p.poly([(10,17),(27,12),(25,21),(10,26)],metal[3]); p.line([(11,18),(25,14)],metal[5]); p.line([(15,20),(19,19),(19,22),(15,23),(15,20)],metal[1])
    elif kind=='wood' or ident=='wooden_handle':
        base=WOODS.get(ident.split('_')[0],'98734f')
        if ident.endswith('_log'):
            p.poly([(5,9),(20,4),(28,22),(13,29)],shade(base,.7)); p.line([(7,10),(23,22)],shade(base,1.1),3); p.line([(12,8),(25,21)],shade(base,.45),2); p.sphere((9,19,28,30),shade(base,1.15));
            for box in [(12,21,25,28),(15,23,22,27)]: p.ellipse(box,(0,0,0,0),shade(base,.6));
        else:
            p.plank((4,6,28,14),base); p.plank((3,17,27,25),base)
    elif kind=='herb' or ident in {'fiber','wheat','wheat_seed','wild_berry'}:
        p.line([(16,29),(15,17),(19,6)],'658054',2)
        for x,y,side in [(15,22,-1),(16,17,1),(17,12,-1)]:
            p.poly([(x,y),(x+side*8,y-5),(x+side*5,y-9),(x,y-3)],'6f9560'); p.line([(x,y-1),(x+side*5,y-6)],'b2c17c')
        flower='d1ae68' if 'wheat' in ident or ident=='fiber' else 'b9a4c2' if 'moon' in ident or 'ghost' in ident else 'a96562'
        for x,y in [(18,4),(22,7),(17,8),(21,3)]: p.sphere((x-2,y-2,x+2,y+2),flower)
    elif kind in {'book','treasure_map','quest'} or ident=='parchment':
        if kind=='book': return weapon_icon(dict(item,type='weapon',tags=['tome']))
        p.poly([(5,3),(24,4),(28,9),(26,28),(4,27),(6,20),(3,14)],'d4c49d'); p.poly([(24,4),(24,10),(28,9)],'f1e0b1');
        for y in (10,14,18,22): p.line([(9,y),(22-(y%3),y)],'927d5e')
        if kind=='treasure_map': p.line([(8,22),(12,16),(17,19),(24,11)],'9b654e'); p.line([(21,9),(26,14)],'974e48',2); p.line([(26,9),(21,14)],'974e48',2)
        if kind=='quest': p.sphere((17,17,24,24),'ad5c51')
    elif kind in {'gem'} or ident in {'aether_mote','storm_crystal','ember_core'}:
        color=ELEMENT_COLORS.get(item.get('element','Arcane'),'8ea7b9'); p.poly([(9,4),(23,4),(29,13),(17,29),(3,13)],shade(color,.7)); p.poly([(9,5),(22,5),(18,13),(4,13)],shade(color,1.2)); p.poly([(18,13),(27,13),(17,27)],color); p.poly([(5,14),(17,14),(16,26)],shade(color,.9)); p.line([(10,6),(7,11)],'e5ecdc',2)
    elif ident in {'raw_hide','cured_leather','frost_pelt','drake_scale'}:
        base='c1c5bc' if ident=='frost_pelt' else '8a7054' if ident=='drake_scale' else 'a0805d'
        p.poly([(7,3),(14,6),(23,3),(24,10),(29,14),(25,19),(27,28),(19,26),(14,30),(9,25),(3,26),(6,17),(3,10)],base)
        p.poly([(12,8),(20,7),(23,17),(20,23),(11,23),(8,15)],shade(base,1.2),None)
        for y in range(8,24,4): p.line([(11,y),(14,y+2),(18,y),(22,y+2)],shade(base,.65))
    elif kind=='animal_material' or ident=='bone':
        p.limb((7,26),(23,7),4,'c6b88f');
        for x,y in [(6,27),(9,28),(21,6),(25,8)]: p.sphere((x-3,y-3,x+3,y+3),'d1c39c')
        if ident=='feather':
            image=canvas((32,32)); p=Pixel(image); p.poly([(8,29),(9,14),(18,3),(24,2),(26,8),(18,23)],'abb9ad');
            for y in range(7,24,3): p.line([(10+(23-y)*.4,y+4),(22,y)],'d5d9bf'); p.line([(8,29),(23,3)],'6c796f')
    elif kind=='food' or ident in {'raw_meat','field_mushroom'} or any(x in ident for x in ('trout','carp','eel','pike','snapper','cod','starfin','storm_ray')):
        if 'bread' in ident:
            p.sphere((3,8,29,26),'be965f'); p.line([(7,15),(10,10)],'e5cb94',2); p.line([(14,17),(17,10)],'e5cb94',2); p.line([(21,18),(23,12)],'e5cb94',2); p.line([(7,23),(22,24)],'825735')
        elif 'mushroom' in ident:
            p.rect((13,13,20,28),'d0b78d',INK); p.line([(15,17),(15,25)],'ead4a7'); p.sphere((3,3,29,19),'b27b60'); p.line([(7,17),(25,17)],'d2b38c');
            for x,y in [(10,7),(20,6),(23,12),(8,12)]: p.rect((x,y,x+2,y+1),'e3c59b')
        elif any(x in ident for x in ('trout','carp','eel','pike','snapper','cod','starfin','ray')):
            p.poly([(5,14),(1,7),(2,24),(7,19)],'809c9b'); p.sphere((5,7,29,23),'a4ada0'); p.poly([(13,9),(19,3),(21,11)],'758c89'); p.poly([(12,21),(17,27),(22,22)],'71867e'); p.line([(9,17),(23,18)],'647f7e'); p.dot(25,12,INK); p.dot(24,11,'eef0d3');
            for x in (11,15,19): p.line([(x,11),(x+2,13),(x,15)],'d0d1af')
        else:
            p.sphere((3,9,27,27),'a66650' if ident=='raw_meat' else 'a17b51'); p.poly([(19,7),(26,3),(30,7),(23,15)],'d6c8a2'); p.line([(8,15),(13,12),(20,15),(16,22),(9,21)],'d9b294',2)
    elif kind=='structure':
        p.plank((3,9,29,15),'97734f'); p.plank((5,16,10,28),'816344'); p.plank((23,16,28,28),'816344'); p.limb((8,21),(25,21),2,'6d523d'); p.rect((9,5,14,8),metal[3],INK)
    else:
        # Supply objects retain distinct physical forms rather than letter tiles.
        category=ident
        if 'thread' in category or category=='sinew':
            p.rect((8,4,24,7),'b39563',INK); p.rect((8,25,24,28),'b39563',INK)
            for y in range(8,25,2): p.line([(10,y),(22,y)],'d3c6a0' if 'enchanted' not in category else 'a3b2cc',2)
            p.line([(11,7),(11,25)],'e4d8b1'); p.line([(23,18),(28,23),(27,29)],'b9aa83')
        elif 'cloth' in category:
            p.poly([(5,5),(26,6),(28,24),(23,29),(3,26)],'91a09b'); p.line([(7,8),(24,9)],'c0c9b1'); p.poly([(8,10),(13,26),(25,27),(22,10)],'738785',None); p.line([(8,11),(12,25)],'aebfb0'); p.line([(23,11),(26,23)],'56696b')
        elif category=='lockpick':
            p.line([(7,29),(16,10),(23,8),(26,10)],INK,4); p.line([(7,28),(17,11),(23,9),(25,10)],metal[4],2); p.line([(17,28),(24,17),(28,17)],metal[3],2)
        elif category=='arrow_bundle':
            for dx in (-4,0,4): p.line([(7+dx,28),(24+dx,6)],'ad8a55',2); p.poly([(24+dx,3),(27+dx,7),(22+dx,8)],metal[4]); p.line([(5+dx,23),(9+dx,26)],'9bab9b',2)
        else:
            p.poly([(9,4),(23,4),(24,8),(21,11),(28,21),(26,28),(6,29),(3,23),(10,11),(7,8)],'a88b5f'); p.line([(10,5),(21,5)],'d6bc86'); p.line([(11,10),(22,10)],'66513b',2); p.line([(9,17),(7,24),(11,26)],'d0b37c'); p.line([(21,15),(24,23)],'7d6345')
    return image
