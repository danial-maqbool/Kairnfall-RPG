"""Ability and skill icons using readable weapons, tools, and elemental forms."""
from __future__ import annotations
from .common import Pixel, canvas, palette, shade, ELEMENT_COLORS, INK
from .items import icon, weapon_icon


def ability_icon(ability):
    image=canvas((32,32));p=Pixel(image);element=ability.get('element','Physical');base=ELEMENT_COLORS.get(element,'c7b79b');c=palette(base);kind=ability.get('kind','strike')
    if kind in {'strike','cleave','interrupt','execute','bleed','backstab'}:
        weapon=weapon_icon(dict(id='steel_sword',type='weapon',tags=['dagger' if kind=='backstab' else 'sword'],material='steel'))
        image.alpha_composite(weapon)
        p.line([(3,18),(8,8),(19,4),(28,8)],c[3],2);p.line([(4,19),(9,10),(18,6)],c[5])
    elif kind in {'shield','block','guard','barrier','reflect'}:
        p.poly([(5,5),(16,2),(27,5),(26,21),(16,30),(6,21)],c[1]);p.poly([(8,7),(16,5),(24,7),(23,19),(16,26),(9,19)],c[3]);p.line([(9,8),(16,6),(21,8)],c[5]);p.line([(16,7),(16,23)],c[1]);p.sphere((12,11,20,19),base)
    elif kind in {'heal','regenerate','purge','cleanse','revive','restoration'}:
        p.poly([(5,22),(7,13),(11,13),(12,18),(15,15),(17,15),(17,23),(23,21),(27,22),(24,27),(12,29)],'c6ad88');p.rect((13,3,18,14),c[3],INK);p.rect((9,7,23,11),c[3],INK);p.line([(14,4),(16,4)],c[5]);p.dot(24,4,c[5])
    elif kind in {'dash','blink','teleport','charge','evade','step'}:
        p.poly([(14,7),(20,7),(19,17),(26,23),(24,27),(11,26),(9,22),(13,17)],c[2]);p.line([(15,9),(14,18),(20,22)],c[5]);
        for y in (10,16,22):p.line([(2,y),(8,y)],c[3],2)
    elif kind in {'summon','pet','companion'}:
        p.poly([(8,25),(8,17),(11,13),(10,5),(16,10),(22,5),(23,14),(27,19),(24,27),(14,29)],c[2]);p.poly([(11,17),(16,13),(22,16),(23,23),(17,25)],c[4],None);p.dot(13,18,INK);p.dot(21,18,INK);p.poly([(15,22),(19,22),(17,25)],c[0])
    elif kind in {'trap','root','snare','entangle'}:
        p.ellipse((4,16,28,29),c[1],INK);p.ellipse((8,19,24,26),'494d3e');
        for x in (7,13,19,25):p.poly([(x-2,18),(x,10),(x+2,18)],c[3]);p.poly([(x-2,27),(x,20),(x+2,27)],c[4])
        p.line([(16,20),(16,11),(22,6)],'91ab70',2)
    elif element=='Fire':
        p.poly([(4,23),(7,13),(12,18),(17,2),(21,13),(25,9),(29,23),(22,30),(11,30)],c[1]);p.poly([(8,24),(12,17),(15,21),(19,9),(24,24),(18,28)],c[3],None);p.poly([(13,25),(17,17),(21,25),(17,29)],'efd798',None)
    elif element=='Frost':
        for dx,dy in [(0,12),(11,6),(11,-6),(0,-12),(-11,-6),(-11,6)]:
            p.line([(16,16),(16+dx,16+dy)],c[3],2);p.dot(16+dx,16+dy,c[5])
        p.poly([(16,9),(22,16),(16,23),(10,16)],c[2]);p.line([(16,11),(12,16),(16,19)],c[5])
    elif element=='Lightning':
        p.poly([(18,1),(7,18),(15,17),(11,31),(28,12),(19,14),(25,2)],c[1]);p.poly([(19,4),(11,16),(18,15),(14,26),(24,15),(17,17)],c[4],None);p.line([(18,5),(13,13)],c[5])
    elif element in {'Nature','Poison'}:
        p.line([(14,30),(17,8)],c[1],3)
        for x,y,side in [(15,24,-1),(16,17,1),(17,10,-1)]:p.poly([(x,y),(x+side*11,y-4),(x+side*8,y-12),(x,y-5)],c[2]);p.line([(x,y-2),(x+side*7,y-8)],c[4])
        if element=='Poison':p.sphere((21,21,28,29),'a8b969')
    elif kind in {'cone','line','projectile','chain','meteor','nova','blast'}:
        p.poly([(3,28),(9,14),(17,7),(26,3),(28,13),(21,23)],c[1]);p.poly([(7,24),(14,13),(23,7),(21,16),(13,24)],c[3],None);p.line([(12,20),(22,9)],c[5],2)
    else:
        # A carved runestone is the shared icon for utility magic, not a letter tile.
        p.poly([(8,3),(24,3),(28,11),(25,28),(7,29),(4,14)],'6c797c');p.poly([(9,5),(21,5),(23,10),(20,25),(8,26)],'9aa39a',None);p.line([(16,7),(22,15),(16,25),(10,15),(16,7)],c[3],2);p.line([(16,11),(16,21)],c[5])
    return image


def skill_icon(skill,items):
    ident=skill['id'];by_id={item['id']:item for item in items}
    direct={'mining':'copper_pickaxe','woodcutting':'woodcutters_axe','fishing':'field_rod','farming':'wheat_seed','herbalism':'sickle','skinning':'skinning_knife','excavation':'shovel','construction':'crafting_hammer','lockpicking':'lockpick','cartography':'parchment','scribing':'ink'}
    if direct.get(ident) in by_id:return icon(by_id[direct[ident]])
    match=next((item for item in items if item.get('skill')==ident and item.get('slot')),None)
    if match:return icon(match)
    element={'pyromancy':'Fire','cryomancy':'Frost','stormcalling':'Lightning','nature_magic':'Nature','shadow_magic':'Shadow','radiance':'Radiant','restoration':'Radiant','arcane_magic':'Arcane','geomancy':'Physical'}.get(ident,'Arcane')
    kind='summon' if ident in {'summoning','animal_handling','hunting'} else 'heal' if ident in {'restoration','survival'} else 'shield' if ident in {'endurance','shield_mastery'} else 'dash' if ident in {'evasion','exploration'} else 'utility'
    return ability_icon(dict(id=ident,kind=kind,element=element))
