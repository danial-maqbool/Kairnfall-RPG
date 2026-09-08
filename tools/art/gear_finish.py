"""Material and construction details for the added equipment tracks.

Only the new grade metadata enables this pass. Old saved templates retain their
existing art. Pixel clusters describe stitching, inlay and alloy highlights.
"""
from .common import Pixel, canvas, palette, shade, INK


def material_icon(item):
    ident=item['id']; base=item.get('_color')
    if not base or not (ident.endswith('_treated_leather') or ident.endswith('_cloth')):
        return None
    image=canvas((32,32)); p=Pixel(image); c=palette(base)
    if ident.endswith('_treated_leather'):
        p.poly([(7,4),(13,6),(24,3),(24,10),(28,14),(25,21),(27,27),(19,26),
                (13,30),(9,25),(3,26),(6,17),(3,10)],c[2])
        p.poly([(12,9),(20,7),(23,17),(19,23),(11,23),(8,15)],c[3],None)
        p.line([(9,9),(7,14),(9,21)],c[4]); p.line([(21,10),(23,18),(20,23)],c[1])
        for x,y in ((8,7),(23,7),(25,15),(24,25),(12,27),(5,23)):
            p.line([(x,y),(x+1,y+1)],c[0])
        p.line([(11,16),(18,15)],shade(base,.72)); p.line([(12,17),(16,17)],c[4])
    else:
        p.poly([(5,5),(25,5),(28,23),(23,29),(3,26)],c[2])
        p.poly([(8,10),(13,25),(24,27),(21,10)],c[1],None)
        p.line([(7,8),(23,8)],c[4]); p.line([(8,11),(12,24)],c[3],2)
        p.line([(23,10),(26,22)],c[0]); p.line([(5,24),(13,27),(23,27)],c[4])
        for x in range(7,23,3): p.line([(x,6),(x+1,7)],c[1])
        for x in range(5,23,3): p.line([(x,26),(x+1,28)],c[2])
    return image


def finish_icon(image,item):
    if not (item.get('_metal_color') or item.get('_color')): return image
    p=Pixel(image); level=item.get('requirement',1); tags=item.get('tags',[])
    family=tags[0] if tags else ''; slot=item.get('slot','')
    metal=palette(item.get('_metal_color','b6afa0'))
    trim='cbb680' if level>=55 else 'ae9d76' if level>=27 else '796349'
    if item['type']=='weapon':
        if family in ('sword','greatsword','dagger') and level>=27:
            start=9 if family!='dagger' else 15
            p.line([(15,start),(15,18)],metal[1])
            p.line([(16,18),(17,16)],trim)
            if level>=55:
                p.line([(10,20),(12,21)],trim); p.line([(20,21),(22,20)],trim)
            if level>=85: p.poly([(16,27),(17,29),(16,30),(15,29)],'a7c4d2',metal[1])
        elif family=='bow':
            for x,y in ((18,7),(21,11),(21,21),(18,25)):
                p.line([(x-1,y),(x+1,y+1)],trim)
        elif family in ('axe','greataxe','halberd','mace','greatmace','spear') and level>=27:
            p.line([(17,8),(19,9),(17,11)],metal[1])
            if level>=55: p.line([(16,14),(18,14)],trim)
        elif family=='tome':
            p.line([(11,9),(13,8)],trim); p.line([(22,22),(22,24),(20,25)],trim)
        elif family in ('staff','wand'):
            p.line([(13,25),(15,26)],trim)
    elif item['type']=='armor':
        if slot=='chest':
            if 'light' in tags: p.line([(9,27),(15,28),(23,28)],trim)
            elif 'medium' in tags:
                for y in (13,17,21): p.line([(14,y),(16,y+1)],trim)
            elif level>=27: p.line([(12,15),(16,18),(20,15)],metal[1])
        elif slot=='cloak':
            p.line([(6,26),(13,28),(18,25),(25,27)],trim)
        elif slot=='helmet' and level>=27:
            p.line([(9,8),(12,6)],trim); p.line([(20,6),(23,8)],trim)
    return image


def equipment_details(p,j,item):
    if not item.get('_color') or not item.get('_metal_color'): return
    level=item.get('requirement',1); slot=item.get('slot'); tags=item.get('tags',[])
    x,y=j['hip']; nx,ny=j['neck']; c=palette(item['_color'])
    trim='cbb680' if level>=55 else 'a79370'
    if slot=='chest' and not j['back']:
        if 'light' in tags:
            p.line([(nx-2,ny+2),(nx,ny+5),(nx+2,ny+2)],trim)
        elif 'medium' in tags:
            for dy in (6,9): p.line([(nx-1,ny+dy),(nx+1,ny+dy)],c[4])
        elif level>=27:
            p.line([(nx-2,ny+6),(nx,ny+8),(nx+2,ny+6)],c[1])
            if level>=55: p.line([(nx-2,ny+5),(nx,ny+7),(nx+2,ny+5)],trim)
    elif slot=='cloak' and j['back']:
        end=min(54,y+9); p.line([(x-4,end-1),(x,end),(x+4,end-1)],trim)
