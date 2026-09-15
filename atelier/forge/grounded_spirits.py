"""Grounded-2026 spirit and elemental renderer.

Spirits float rather than step, so locomotion is expressed through core drift,
mantle sway and independently moving tendrils. Action states still alter the
whole silhouette instead of translating an idle frame.
"""
from __future__ import annotations

import math
from PIL import Image
from . import pigment
from .grounded_beasts import Stage, _motion, _ramps


def render_spirit(definition,state,number,direction,spec):
    size=128 if definition.get('boss') else 64
    stage=Stage(size); m=_motion(state,number); coat,dark,pale=_ramps(spec)
    c=m['collapse']; charge=m['charge']; side=direction in (1,2)
    facing=1 if direction==2 else -1 if direction==1 else 0

    # A floating gait must visibly articulate at native pixels. The core drifts
    # while opposite mantle/tendril phases keep this from being a translated idle.
    gait=math.sin(m['phase'])*2.4*m['stride']
    gait_lift=abs(math.cos(m['phase']))*.8*m['stride']
    mantle_sway=math.sin(m['phase'])*1.6*m['stride']
    drive=m['lunge']*(facing if side else .28)
    x=drive + gait*(facing if side else .55)
    y=max(3,spec.height*(1-c*.75)*.55+m['bob']+gait_lift+2+charge*1.7-m['crouch']*.25)
    squash=1.0+min(.18,abs(m['lunge'])*.025)-c*.28
    stage.ellipse((x,y),spec.girth*(1+charge*.16)*squash,spec.girth*(1.25-charge*.08)*(1-c*.18),coat[3])

    reach=spec.girth+2+abs(m['lunge'])*.55+charge*2.2
    lift=5+charge*4+m['crouch']*.45
    for s in (-1,1):
        forward=(facing if side else s)
        local_reach=reach+s*mantle_sway*.45
        local_lift=lift-s*mantle_sway*.35
        stage.poly([(x+s*1.4,y+1),(x+s*local_reach+forward*m['lunge']*.16,y+local_lift),(x+s*(spec.girth+1),y-1)],dark[3])

    trail=-m['lunge']*(facing if side else .18)
    for i in range(3):
        left=-spec.girth+i*spec.girth
        tendril=math.sin(m['phase']+i*2.05)*1.45*m['stride']
        tip_x=x+left+spec.girth*.5+trail+tendril
        tip_y=y-spec.girth-5-c*4-charge*1.3-abs(tendril)*.35
        stage.poly([(x+left,y-spec.girth*.5),(tip_x,tip_y),(x+left+spec.girth,y-spec.girth*.5)],coat[2])

    if spec.glow:
        g=pigment.ramp(spec.glow)
        radius=max(1.2,spec.girth*.28)*(1+charge*.38+min(.24,abs(m['lunge'])*.035))
        stage.disc((x+(facing if side else 0)*m['lunge']*.12,y+.8+charge*.8),radius,g[5],None)
        if charge>.25:
            stage.line([(x-2-charge*2,y+spec.girth+2),(x,y+spec.girth+4+charge*2),(x+2+charge*2,y+spec.girth+2)],g[4],1.2)

    if definition.get('elite') or definition.get('boss'):
        tone=pigment.ramp(spec.glow or '#d4aa5a')
        stage.line([(-5,spec.height+5),(0,spec.height+8),(5,spec.height+5)],tone[4],1.4)
    if m['flash']:
        overlay=Image.new('RGBA',stage.image.size,(255,234,210,0))
        overlay.putalpha(stage.image.getchannel('A').point(lambda a:round(a*m['flash']*.45)))
        stage.image=Image.alpha_composite(stage.image,overlay)
    if m['fade']<1:
        stage.image.putalpha(stage.image.getchannel('A').point(lambda a:round(a*m['fade'])))
    return stage.image
