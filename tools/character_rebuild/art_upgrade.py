"""Temporary, guarded actor-generation migration. Removed after candidate publication."""
from pathlib import Path
import ast, json, shutil
from runtime_upgrade import ROOT,HERE,replace,install


def apply():
    motion='tools/art/character_motion.py';people='tools/art/characters.py';wild='tools/art/wildlife.py'
    replace(motion,"STATES = ('idle', 'walk', 'attack', 'cast', 'hit', 'death')","STATES = ('idle', 'walk', 'attack', 'cast', 'hit', 'death')\nEXTRA_STATES = ('interact', 'craft', 'run', 'bow_attack', 'crossbow_attack')")
    replace(motion,"if state not in STATES or not isinstance(frame, int)","if state not in STATES + EXTRA_STATES or not isinstance(frame, int)")
    replace(motion,"    stride = math.sin(cycle) if state == 'walk' else 0.0","    moving = state in ('walk', 'run')\n    stride = math.sin(cycle) if moving else 0.0")
    replace(motion,"if state == 'walk' else 0\n    breath", "if moving else 0\n    breath")
    replace(motion,"    if state == 'walk':","    if moving:")
    replace(motion,"    elif state == 'hit':",'''    elif state == 'run':
        # A longer stride, forward torso and bent elbows distinguish running from fast walking.
        for name in ('head', 'neck', 'shoulder_l', 'shoulder_r'):
            x,y=j[name]; j[name]=(x+2,y-1)
        for side, sign in (('l',1),('r',-1)):
            x,y=j['foot_'+side];j['foot_'+side]=(x+round(sign*stride*2),y-max(0,round(sign*stride*2)))
            x,y=j['elbow_'+side];j['elbow_'+side]=(x+round(sign*stride*2),y-1)
            x,y=j['hand_'+side];j['hand_'+side]=(x+round(sign*stride*2),y-3)
    elif state == 'interact':
        reach=(0,1,3,5,5,3,1,0)[frame]
        j['hand_l']=(j['hand_l'][0]-round(reach*.25),j['hand_l'][1]-reach)
        j['hand_r']=(j['hand_r'][0]+round(reach*.5),j['hand_r'][1]-round(reach*.6))
        j['elbow_l']=(j['elbow_l'][0],j['elbow_l'][1]-round(reach*.5))
        j['elbow_r']=(j['elbow_r'][0]+round(reach*.2),j['elbow_r'][1]-round(reach*.3))
        j['head']=(32,17+(1 if frame in (3,4) else 0))
    elif state == 'craft':
        lift=(0,3,7,9,2,0,3,0)[frame]
        j['hand_r']=(40,38-lift)
        j['elbow_r']=(38,33-round(lift*.6))
        j['hand_l']=(29,39+(1 if frame==4 else 0))
        j['elbow_l']=(24,35)
        j['head']=(33,18+(1 if frame==4 else 0))
    elif state in ('bow_attack','crossbow_attack'):
        if state=='bow_attack':
            draw=(1,3,7,12,5,2,1,0)[frame]
            j['hand_r']=(43,34)
            j['hand_l']=(40-draw,34)
            j['elbow_r']=(39,31)
            j['elbow_l']=(31-round(draw*.35),31)
        else:
            recoil=(0,0,0,0,-2,-1,0,0)[frame]
            j['hand_r']=(35+recoil,36)
            j['hand_l']=(43+recoil,34)
            j['elbow_r']=(39,32)
            j['elbow_l']=(29,35)
        j['head']=(33,17-(1 if frame in (2,3) else 0))
        angle=24
    elif state == 'hit':''')
    replace(motion,"cloth=round(math.sin(cycle-.65)*2) if state=='walk' else round(lean*.6),","cloth=round(math.sin(cycle-.65)*(3 if state=='run' else 2)) if moving else round((0,1,2,3,3,2,1,0)[frame]*.65) if state=='cast' else round(lean*.6),")
    replace(people,"    kind=_weapon_kind(item); material=item.get('material','iron'); c=palette(METALS.get(material,'a5b9c7'))",'''    j=dict(j)
    if j['state'] in ('interact','craft'):
        j['hand_r']=(j['hip'][0]-7*j['sign'],j['hip'][1]-5)
        j['angle']=155*j['sign'] if _weapon_kind(item) not in ('staff','spear','bow','crossbow') else -15*j['sign']
    kind=_weapon_kind(item); material=item.get('material','iron'); c=palette(METALS.get(material,'a5b9c7'))''')
    replace(people,"if j['state']=='attack' else 0","if j['state'] in ('attack','bow_attack','crossbow_attack') else 0")
    replace(people,"tips=[(x-2*s,y-14),(x+4*s,y-9),(x+6*s,y-2),(x+4*s,y+6),(x-2*s,y+11)]","tips=[(x-4*s,y-14),(x+2*s,y-9),(x+3*s,y-3),(x,y),(x+3*s,y+4),(x+s,y+9),(x-4*s,y+12)]")
    replace(people,"pull=(x-(3+draw)*s,y-1)","pull=j['hand_l'] if j['state']=='bow_attack' else (x-(3+draw)*s,y-1)")
    replace(people,"if j['state']=='attack' and j['frame'] in (1,2,3):","if j['state'] in ('attack','bow_attack') and j['frame'] in (1,2,3):")
    replace(people,"p.line([(x+5*s,y-3),(x+5*s,y+1)],'6d4632',3)","p.line([(x,y-2),(x,y+2)],'6d4632',3)")
    replace(people,"    x,y=j['hand_l']; base=clothing_base(item); c=palette(base); s=j['sign']","    j=dict(j)\n    if j['state'] in ('interact','craft'): j['hand_l']=(j['hip'][0]+3*j['sign'],j['hip'][1]-4)\n    x,y=j['hand_l']; base=clothing_base(item); c=palette(base); s=j['sign']")
    replace(people,"    identity=seed('wayfarer:'+role); body=identity%2; skin=(identity//3)%6","    if role=='fletcher' and state=='attack': state='bow_attack'\n    identity=seed('wayfarer:'+role); body=identity%2; skin=(identity//3)%6")
    replace(people,"    for layer in layer_order(direction):\n        if layer in layers: result.alpha_composite(layers[layer])","    order=layer_order(direction)\n    if state in ('interact','craft'): order=['weapon','offhand']+[k for k in order if k not in ('weapon','offhand')]\n    for layer in order:\n        if layer in layers: result.alpha_composite(layers[layer])")
    # Copy species catalogue data and colour rules, not the old creature rendering functions.
    source=(ROOT/'atelier/forge/beasts.py').read_text(encoding='utf-8');parsed=ast.parse(source)
    names={'Beast','Q','FAMILIES','BIOME_TINT','PATTERNS','EYE_COLOURS','_vary','describe'}
    segments=[]
    for node in parsed.body:
        name=node.name if isinstance(node,(ast.ClassDef,ast.FunctionDef)) else next((t.id for t in node.targets if isinstance(t,ast.Name)),None) if isinstance(node,ast.Assign) else None
        if name in names:
            text=ast.get_source_segment(source,node)
            if name=='Beast':text='@dataclass\n'+text
            segments.append(text)
    if len(segments)!=len(names):raise RuntimeError('Creature anatomy source changed; required data nodes not found.')
    anatomy='"""Retained catalogue species proportions and coloration; contains no image renderer."""\nimport math, random\nfrom dataclasses import dataclass, replace\nfrom atelier.forge import pigment\nfrom atelier.forge.pigment import blend\n\n'+'\n\n'.join(segments)+'\n'
    (ROOT/'tools/art/creature_anatomy.py').write_text(anatomy,encoding='utf-8')
    replace('tools/art/creature_anatomy.py','    if spec is None:\n        spec = Beast()','    if spec is None:\n        raise ValueError("Unmapped creature family: " + str(mob.get("family", "")))')
    replace('tools/art/creature_anatomy.py','    spec = _vary(spec, mob)\n    if mob.get(\'boss\'):','    spec = _vary(spec, mob)\n    if not mob.get(\'boss\'):\n        spec.horn = FAMILIES[mob[\'family\']].horn\n    if mob.get(\'boss\'):')
    replace(wild,'from atelier.forge.beasts import describe, FAMILIES','from .creature_anatomy import describe, FAMILIES')
    replace(wild,"    span*=1-m['collapse']*.7","    span*=1-m['collapse']*.7\n    if m['state'] in ('idle','hit','death'): span*=.42; beat=-3")
    replace(wild,"    dead=m['collapse']; charge=m['charge']; phase=m['phase'];tone=s.accent or s.coat","    dead=m['collapse']; charge=m['charge']; phase=m['phase'];tone=s.accent or s.coat\n    shift=m['drive']")
    replace(wild,"x=math.cos(angle)*(5+math.sin(phase+k)*m['stride']); y=math.sin(angle)*5","x=shift+math.cos(angle)*(5+math.sin(phase+k)*m['stride']); y=math.sin(angle)*5")
    replace(wild,"    gape=max(0,m['drive']*.9)+m['charge']*3;dead=m['collapse']","    gape=abs(m['drive']*.9)+m['charge']*3;dead=m['collapse']")
    replace(wild,"    elif family=='pirate':\n        p.line([(x-5,y-2),(x+5,y-2)],'883e42',2);p.rect((x+1,y-1,x+3,y+1),'252632')",'''    elif family=='pirate':
        # Tricorn, bandanna and eyepatch; not a colour-only human silhouette.
        if j['collapse']>.6:
            p.poly([(x-8,y-1),(x-5,y-4),(x+4,y-3),(x+8,y),(x+6,y+1),(x-7,y+1)],'393c48')
        else:
            p.poly([(x-8,y-3),(x-6,y-8),(x,y-7),(x+6,y-8),(x+8,y-3),(x+3,y-4),(x,y-2),(x-3,y-4)],'393c48')
            p.line([(x-6,y-6),(x-2,y-5),(x+2,y-5),(x+6,y-6)],'b79c68')
        if not j['back']:
            p.line([(x-5,y-2),(x+5,y-2)],'883e42',2);p.rect((x+1,y-1,x+3,y+1),'252632')
    elif family=='ghoul':
        for hand in ('hand_l','hand_r'):
            hx,hy=j[hand]
            for claw in (-1,1):p.line([(hx+claw,hy+1),(hx+claw*2,hy+4)],'c9cfb0')''')
    # Dedicated amphibian and fish construction: neither inherits mammal ears or paws.
    extra='''

def _amphibian(b,s,m):
    dead=m['collapse'];x=m['drive'];z=4+s.girth*.45*(1-dead)+m['charge']*2
    for side in (-1,1):
        kick=math.sin(m['phase']+(0 if side<0 else math.pi))*3 if m['state']=='walk' else 0
        b.limb((x-3,side*3,z),(x-7+kick,side*6,3),4,s.coat)
        b.limb((x-7+kick,side*6,3),(x-2,side*8,0),2.3,s.coat)
        b.limb((x+3,side*3,z),(x+6+kick*.4,side*5,0),2,s.coat)
        for toe in (-1,0,1):b.line([(x+6,side*5,0),(x+8,side*(5+toe),0)],shade(s.coat,1.2))
    b.ellipsoid((x-1,0,z),s.length*.43,s.girth*.95,s.girth*.62,s.coat)
    b.ellipsoid((x+4,0,z+1),s.head+2,s.head+1,s.head*.7,s.coat)
    for side in (-1,1):
        b.ellipsoid((x+4,side*3,z+4),1.6,1.5,1.5,shade(s.coat,1.25))
        b.dot((x+5,side*3,z+4),s.eye if dead<.8 else '464138')
    b.line([(x+6,-3,z),(x+8,0,z-1),(x+6,3,z)],shade(s.coat,.6))
    if m['state']=='attack' and m['frame'] in (3,4):b.line([(x+8,0,z),(x+13,0,z-1)],'c48283',1.4)


def _aquatic(b,s,m):
    dead=m['collapse'];x=m['drive'];wave=math.sin(m['phase'])*(3 if m['state']=='walk' else .5)
    z=5+s.girth*(1-dead)*.55+m['charge']*2
    b.ellipsoid((x,0,z),s.length*.45,s.girth*.58,s.girth*.8,s.coat)
    rear=x-s.length*.4
    b.poly([(rear,0,z),(rear-7,wave,z+6*(1-dead)),(rear-5,wave,z),(rear-7,wave,z-5*(1-dead))],s.accent or shade(s.coat,.8))
    b.poly([(x-3,0,z+s.girth*.6),(x,0,z+s.girth+5),(x+4,0,z+s.girth*.6)],s.accent or shade(s.coat,1.2))
    for side in (-1,1):
        b.poly([(x+2,side*2,z),(x-2,side*(7+m['charge']),z-3),(x+4,side*3,z-1)],s.accent or shade(s.coat,.8))
        b.dot((x+s.length*.30,side*s.girth*.5,z+1),s.eye if dead<.8 else '35353a')
    b.line([(x+s.length*.22,-s.girth*.45,z+2),(x+s.length*.22,-s.girth*.5,z-2)],shade(s.coat,.6))
'''
    replace(wild,'\ndef frame(definition,state,number,direction):',extra+'\n\ndef frame(definition,state,number,direction):')
    replace(wild,"if s.archetype in ('quadruped','primate','amphibian','drake'):_quadruped(b,s,m)","if s.archetype in ('quadruped','primate','drake'):_quadruped(b,s,m)\n    elif s.archetype=='amphibian':_amphibian(b,s,m)")
    replace(wild,"elif s.archetype in ('serpent','worm','aquatic'):_serpent(b,s,m)","elif s.archetype in ('serpent','worm'):_serpent(b,s,m)\n    elif s.archetype=='aquatic':_aquatic(b,s,m)")
    (ROOT/'tools/art/people.py').write_text('"""Sole active humanoid entry point. Legacy raster fallback is prohibited."""\nfrom .characters import SKINS, HAIRS, ROLE_COLORS, body_frame, hair_frame, armour_frame, equipment_frame, npc_frame, clothing_base, layer_order\nfrom .character_motion import rig\n')
    (ROOT/'tools/art/humanoid.py').write_text('"""Compatibility imports for the Wayfarer renderer; no previous drawing implementation remains."""\nfrom .characters import SKINS, HAIRS, ROLE_COLORS, body_frame, hair_frame, armour_frame, equipment_frame, npc_frame, clothing_base, layer_order\nfrom .character_motion import rig\n')
    (ROOT/'tools/art/fauna.py').write_text('"""Sole active creature entry point. Unknown anatomy fails rather than falling back."""\nfrom .wildlife import SUPPORTED, frame\n')
    # Build small one-action atlases so a gesture does not load every other action into VRAM.
    builder='tools/build_game_assets.py'
    replace(builder,'from art.people import body_frame,hair_frame,equipment_frame,npc_frame','from art.people import body_frame,hair_frame,equipment_frame,npc_frame\nfrom art.character_motion import EXTRA_STATES')
    replace(builder,'    preflight(data)\n    def emit(image,key,animated=False):','    preflight(data)\n    for group in ("people","equipment","npcs","mobs","motions"):\n        path=root/group\n        if path.is_symlink(): raise ValueError("Actor output must not be a symlink: "+str(path))\n        if path.exists(): shutil.rmtree(path)\n    state_counts={}\n    def emit(image,key,animated=False,state_count=6):')
    replace(builder,'        if animated: sheets.append(key)','        if animated: sheets.append(key); state_counts[key]=state_count')
    replace(builder,"    print('ASSETS: creature anatomy',flush=True)",'''    print('ASSETS: separate interaction, work, running and ranged-pose atlases',flush=True)
    def motion_sheet(draw,state):
        image=canvas((512,256))
        for direction in range(4):
            for frame in range(8): image.alpha_composite(draw(state,frame,direction),(frame*64,direction*64))
        return image
    for state in EXTRA_STATES:
        for body in range(2):
            for skin in range(6): emit(motion_sheet(lambda st,n,d:body_frame(body,skin,st,n,d),state),f'motions/{state}/people/body_{body}_{skin}',True,1)
        for style in range(6):
            for colour in range(8): emit(motion_sheet(lambda st,n,d:hair_frame(style,colour,st,n,d),state),f'motions/{state}/people/hair_{style}_{colour}',True,1)
        for item in equipment: emit(motion_sheet(lambda st,n,d:equipment_frame(item,st,n,d),state),f'motions/{state}/equipment/'+item['id'],True,1)
        for role in sorted({n['role'] for n in data['npcs']}): emit(motion_sheet(lambda st,n,d:npc_frame(role,st,n,d),state),f'motions/{state}/npcs/'+role,True,1)
        print('ASSETS: extra pose',state,'complete',flush=True)
    print('ASSETS: creature anatomy',flush=True)''')
    replace(builder,'im.height!=im.width//8*24','im.height!=im.width//8*4*state_counts[key]')
    replace(builder,"'animated':key in animated_keys}","'animated':key in animated_keys,**({'state_count':state_counts[key]} if key in animated_keys else {})}")
    replace(builder,"'frame_order':list(STATES),'directions':list(DIRECTIONS)","'frame_order':list(STATES),'motion_order':list(EXTRA_STATES),'directions':list(DIRECTIONS)")
    replace(builder,'Original project and checksum-verified Atelier catalog artwork; source scripts are included.','Wayfarer actor construction and checksum-verified non-actor Atelier artwork; source scripts are included.')
    replace(builder,'Matching Atelier assets from atelier/Assets replace compatible catalog artwork as a complete humanoid rig cohort.','Only compatible non-actor Atelier artwork is integrated. Wayfarer is the sole character and creature source; no actor raster fallback is permitted.')
    replace('tools/integrate_atelier.py','Grounded-2026 runtime actor source owns','Wayfarer runtime actor source owns')
    replace('tools/integrate_atelier.py','Grounded-2026 procedural construction','Wayfarer original joint construction')
    # Existing whole-game checks retain six base states and additionally inspect explicit one-action grids.
    validator='tools/validate_game_assets.py'
    replace(validator,'image.height==24*size','image.height==4*e.get("state_count",6)*size')
    install('build_wayfarer_pack.py','tools/build_wayfarer_pack.py')
    install('validate_character_assets.py','tools/validate_character_assets.py')
    replace('tools/validate_character_assets.py',"('walk','attack','hit','death') if group=='mobs'","('walk','attack','cast','hit','death') if group=='mobs'")
    replace('tools/validate_character_assets.py',"'native_rendering':'verified_by_separate_native_contract'","'native_rendering':'not_asserted_by_this_validator'")
    (ROOT/'tools/validate_grounded_actor_assets.py').write_text('#!/usr/bin/env python3\n"""Compatibility command: actor acceptance is now the Wayfarer contract."""\nfrom validate_character_assets import main\nif __name__=="__main__": main()\n')
    print('Guarded Wayfarer source, additional poses and generator ownership applied.')
