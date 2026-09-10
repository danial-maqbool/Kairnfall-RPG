"""Final creature action articulation over the authored fauna renderer.

The base renderer keeps all existing anatomy. This layer moves existing upper-body
pixels during attacks and adds locomotion phases only for previously static movers.
The lower ground anchor remains fixed.
"""
from __future__ import annotations
from PIL import Image
from .fauna_base import SUPPORTED, frame as base_frame

STATIC_WALK_FAMILIES=frozenset({'wisp','geode','snail','fungus','mimic','manta'})


def _articulate_frame(image,family,state,number,direction):
    scale=max(1,image.width//64); width,height=image.size
    if state=='attack':
        advance=(0,1,2,3,2,1,0,0)[number]*scale
        if advance:
            cut=min(height,52*scale)
            upper=image.crop((0,0,width,cut)); result=Image.new('RGBA',image.size,(0,0,0,0))
            dx=dy=0
            if direction==0: dy=advance
            elif direction==3: dy=-advance
            elif direction==2: dx=advance
            else: dx=-advance
            result.alpha_composite(upper,(dx,dy))
            result.alpha_composite(image.crop((0,cut,width,height)),(0,cut))
            image=result
    elif state=='walk' and family in STATIC_WALK_FAMILIES:
        phase=(0,1,1,0,-1,-1,0,1)[number]*scale
        if phase:
            cut=min(height,54*scale)
            upper=image.crop((0,0,width,cut)); result=Image.new('RGBA',image.size,(0,0,0,0))
            if family in {'wisp','geode','manta'}: result.alpha_composite(upper,(0,phase))
            else: result.alpha_composite(upper,(phase,0))
            result.alpha_composite(image.crop((0,cut,width,height)),(0,cut))
            image=result
    return image


def frame(definition,state,number,direction):
    return _articulate_frame(base_frame(definition,state,number,direction),definition['family'],state,number,direction)
