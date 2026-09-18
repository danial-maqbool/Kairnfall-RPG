"""Wayfarer character joints, authored on a 64px canvas with a fixed foot anchor.

Only coordinates are interpolated. Raster frames are never rotated or warped.
The module has no image/runtime dependency so motion contracts can run alone.
"""
from __future__ import annotations
import math

STATES = ('idle', 'walk', 'attack', 'cast', 'hit', 'death')
EXTRA_STATES = ('interact', 'craft', 'run', 'bow_attack', 'crossbow_attack')
DIRECTIONS = ('south', 'west', 'east', 'north')
FRAMES = 8
SIZE = 64
FOOT_BASELINE = 55


def _lerp(a, b, amount):
    return tuple(round(x + (y - x) * amount) for x, y in zip(a, b))


def rig(state: str, frame: int, direction: int, body: int = 0) -> dict:
    """Return synchronized body, clothing and equipment attachment coordinates."""
    if state not in STATES + EXTRA_STATES or not isinstance(frame, int) or not 0 <= frame < FRAMES:
        raise ValueError('Invalid character animation state/frame')
    if not isinstance(direction, int) or not 0 <= direction < len(DIRECTIONS):
        raise ValueError('Invalid character direction')
    if body not in (0, 1):
        raise ValueError('Invalid character body')
    profile = direction in (1, 2)
    side = -1 if direction == 1 else 1
    back = direction == 3
    cycle = frame * math.tau / FRAMES
    moving = state in ('walk', 'run')
    stride = math.sin(cycle) if moving else 0.0
    bounce = (0, -1, -1, 0, 0, -1, -1, 0)[frame] if moving else 0
    breath = -1 if state == 'idle' and frame in (3, 4) else 0
    j = {
        'head': (32, 17 + bounce), 'neck': (32, 26 + bounce),
        'hip': (32, 40 + bounce),
        'shoulder_l': (25 if body == 0 else 26, 28 + bounce + breath),
        'shoulder_r': (39 if body == 0 else 38, 28 + bounce + breath),
        'elbow_l': (23, 34 + bounce + breath), 'elbow_r': (41, 34 + bounce + breath),
        'hand_l': (24, 40 + bounce + breath), 'hand_r': (42, 39 + bounce + breath),
        'knee_l': (29, 47), 'knee_r': (35, 47),
        'foot_l': (28, 55), 'foot_r': (36, 55),
    }
    if profile:
        j.update(shoulder_l=(30, 28+bounce+breath), shoulder_r=(34, 28+bounce+breath),
                 elbow_l=(29, 34+bounce+breath), elbow_r=(36, 34+bounce+breath),
                 hand_l=(30, 40+bounce+breath), hand_r=(39, 39+bounce+breath),
                 knee_l=(31, 47), knee_r=(34, 47), foot_l=(30, 55), foot_r=(35, 55))
    if moving:
        if profile:
            j['foot_l'] = (32 + round(6*stride), 55 - max(0, round(3*stride)))
            j['foot_r'] = (32 - round(6*stride), 55 - max(0, round(-3*stride)))
            j['knee_l'] = (31 + round(3*stride), 47 - max(0, round(2*stride)))
            j['knee_r'] = (34 - round(3*stride), 47 - max(0, round(-2*stride)))
            j['hand_l'] = (30 - round(4*stride), 39+bounce)
            j['hand_r'] = (38 + round(4*stride), 39+bounce)
            j['elbow_l'] = (29 - round(2*stride), 33+bounce)
            j['elbow_r'] = (36 + round(2*stride), 33+bounce)
        else:
            j['foot_l'] = (28-round(2*stride), 55-max(0, round(4*stride)))
            j['foot_r'] = (36+round(2*stride), 55-max(0, round(-4*stride)))
            j['knee_l'] = (29-round(stride), 47-max(0, round(2*stride)))
            j['knee_r'] = (35+round(stride), 47-max(0, round(-2*stride)))
            for name, sign in (('hand_l', 1), ('hand_r', -1), ('elbow_l', 1), ('elbow_r', -1)):
                x, y = j[name]
                j[name] = (x, y + round(sign*stride*(3 if 'hand' in name else 1)))
    angle = 24.0
    lean = 0
    if state == 'attack':
        # Two anticipation frames, one contact frame, then visible follow-through.
        lean = (0, -1, -2, 2, 3, 2, 1, 0)[frame]
        angle = (24, -12, -48, 74, 108, 72, 38, 24)[frame]
        hand = ((41,38),(37,33),(36,27),(47,32),(48,40),(44,41),(42,39),(41,38))[frame]
        elbow = ((40,33),(36,29),(35,25),(40,29),(42,34),(40,35),(40,34),(40,33))[frame]
        j['hand_r'], j['elbow_r'] = hand, elbow
        lx, ly = j['hand_l']; j['hand_l'] = (lx-round(lean*.5), ly-abs(lean))
        for name in ('head','neck','shoulder_l','shoulder_r'):
            x,y=j[name]; j[name]=(x+lean,y+(-1 if frame==2 else 0))
        x,y=j['hip']; j['hip']=(x+round(lean*.5),y)
        j['knee_r']=(36+max(0,lean),47)
        j['foot_r']=(36+max(0,lean),55)
    elif state == 'cast':
        lift = (0, 2, 5, 8, 8, 6, 3, 0)[frame]
        j['hand_l']=(j['hand_l'][0]-round(lift*.2),j['hand_l'][1]-lift)
        j['hand_r']=(j['hand_r'][0]+round(lift*.2),j['hand_r'][1]-lift)
        for name in ('elbow_l','elbow_r'):
            x,y=j[name]; j[name]=(x,y-round(lift*.5))
        j['head']=(32,17-(1 if lift>=5 else 0))
        angle=24-round(lift*1.6)
    elif state == 'run':
        # A longer stride, forward torso and bent elbows distinguish running from fast walking.
        for name in ('head', 'neck', 'shoulder_l', 'shoulder_r'):
            x,y=j[name]; j[name]=(x+2,y-1)
        for limb, limb_sign in (('l',1),('r',-1)):
            x,y=j['foot_'+limb];j['foot_'+limb]=(x+round(limb_sign*stride*2),y-max(0,round(limb_sign*stride*2)))
            x,y=j['elbow_'+limb];j['elbow_'+limb]=(x+round(limb_sign*stride*2),y-1)
            x,y=j['hand_'+limb];j['hand_'+limb]=(x+round(limb_sign*stride*2),y-3)
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
    elif state == 'hit':
        recoil=(0,-3,-4,-2,-1,0,0,0)[frame]
        for name in ('head','neck','shoulder_l','shoulder_r','elbow_l','elbow_r','hand_l','hand_r'):
            x,y=j[name]; j[name]=(x+recoil,y+abs(recoil)//2)
        x,y=j['hip']; j['hip']=(x+round(recoil*.5),y+abs(recoil)//3)
        angle=24+recoil*5
    elif state == 'death':
        collapse=(0,.12,.30,.52,.76,.92,1,1)[frame]
        end={'head':(44,47),'neck':(39,48),'hip':(30,51),
             'shoulder_l':(35,49),'shoulder_r':(40,49),
             'elbow_l':(33,53),'elbow_r':(46,52),'hand_l':(38,54),'hand_r':(50,54),
             'knee_l':(23,53),'knee_r':(29,53),'foot_l':(18,55),'foot_r':(25,55)}
        for name,target in end.items(): j[name]=_lerp(j[name],target,collapse)
        angle=24+(100-24)*collapse
    if side < 0:
        for name, value in tuple(j.items()):
            j[name]=(SIZE-value[0],value[1])
        angle=-angle
    # Metadata is added after mirroring to keep the joint transformation explicit.
    j.update(state=state,frame=frame,side=profile,back=back,sign=side,body=body,
             stride=stride,angle=angle,lean=lean*side,
             cloth=round(math.sin(cycle-.65)*(3 if state=='run' else 2)) if moving else round((0,1,2,3,3,2,1,0)[frame]*.65) if state=='cast' else round(lean*.6),
             collapse=(0,.12,.30,.52,.76,.92,1,1)[frame] if state=='death' else 0.0)
    return j
