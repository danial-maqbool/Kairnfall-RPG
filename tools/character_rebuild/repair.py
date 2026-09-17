#!/usr/bin/env python3
"""Temporary guarded repairs for the tested character candidate; removed on integration."""
from runtime_upgrade import ROOT,replace


def repair_running():
    path=ROOT/'tools/art/character_motion.py'
    text=path.read_text()
    start=text.index("    elif state == 'run':")
    stop=text.index("    elif state == 'interact':",start)
    block=text[start:stop]
    if block.count("for side, sign in (('l',1),('r',-1)):")!=1:
        raise RuntimeError('Running-rig repair no longer matches the inspected source.')
    repaired=block.replace("for side, sign in (('l',1),('r',-1)):","for limb, limb_sign in (('l',1),('r',-1)):")
    for name in ('foot','elbow','hand'):
        repaired=repaired.replace("'"+name+"_'+side","'"+name+"_'+limb")
    repaired=repaired.replace('sign*stride','limb_sign*stride')
    path.write_text(text[:start]+repaired+text[stop:])


def repair_creatures():
    path='tools/art/wildlife.py'
    replace(path,"    dead=m['collapse']; z=s.height*(1-dead*.8); x=m['drive']; phase=m['phase']",
        "    dead=m['collapse']; z=s.height*(1-dead*.8)+m['charge']*3; x=m['drive']+m['charge']*2; phase=m['phase']")
    replace(path,"b.ellipsoid((x,0,z+1),9,8,4,s.accent or 'ab655b')",
        "b.ellipsoid((x,0,z+1),9+m['charge']*2,8+m['charge']*2,4+m['charge'],s.accent or 'ab655b')")
    replace(path,"angle=k*math.tau/7; yy=math.sin(angle)*7;xx=x+math.cos(angle)*7",
        "angle=k*math.tau/7; reach=7+m['charge']*3; yy=math.sin(angle)*reach;xx=x+math.cos(angle)*reach")
    # Root branches open in a visible foreground gesture rather than disappearing behind the stem.
    replace(path,"    for side in (-1,1):b.dot((x+3,side*2,z*.7),s.eye)","""    if m['charge']:
        for side in (-1,1):
            shoulder=(x,side*2,z*.68)
            elbow=(x+3,side*(5+m['charge']*3),z*.65+m['charge']*4)
            hand=(x+6,side*(7+m['charge']*3),z*.62+m['charge']*7)
            b.limb(shoulder,elbow,2.7,s.coat);b.limb(elbow,hand,1.8,s.coat)
            b.poly([hand,(hand[0]+2,hand[1]+side*2,hand[2]+3),(hand[0]-1,hand[1]+side*3,hand[2]+1)],s.accent or '628348')
    for side in (-1,1):b.dot((x+3,side*2,z*.7),s.eye)""")
    replace(path,"    shift=m['drive']","    shift=m['drive']\n    lift=abs(math.sin(phase))*2.5 if m['state']=='walk' else 0")
    replace(path,"angle=k*math.tau/5; height=(8+(k%3)*4)*(1-dead*.8)+charge*3",
        "angle=k*math.tau/5; height=(8+(k%3)*4)*(1-dead*.8)+charge*3+lift*(.65 if k%2 else 1)")
    replace(path,"x=shift+math.cos(angle)*(5+math.sin(phase+k)*m['stride']); y=math.sin(angle)*5",
        "x=shift+math.cos(angle)*(5+math.sin(phase+k)*m['stride']*2); y=math.sin(angle)*5+math.cos(phase+k)*m['stride']*2")
    replace(path,"(0,0,18*(1-dead*.7)+charge*3)","(shift*.45,0,18*(1-dead*.7)+charge*3+lift)")
    replace(path,"(0,0,17*(1-dead*.7)+charge*3)","(shift*.45,0,17*(1-dead*.7)+charge*3+lift)")
    snail='''

def _snail(b,s,m):
    """A muscular foot, retractile eyestalks and a carried shell, not a static shell icon."""
    dead=m['collapse'];charge=m['charge'];phase=m['phase']
    glide=math.sin(phase) if m['state']=='walk' else 0
    drive=m['drive'];body=s.coat;shell=s.accent or 'a78d6a'
    # The front of the foot rolls into contact as the rear releases it.
    foot=[(-10,-3,0),(-8,-4,1),(2,-4,1),(8+drive,-2,1),(10+drive,0,1),
          (8+drive,2,1),(2,4,1),(-8,4,1)]
    b.poly([(x,y+(glide*.7 if x<0 else -glide*.7),z) for x,y,z in foot],body)
    b.line([(-8,-3,1),(0,-3,1),(8+drive,-1,1)],shade(body,1.3),1.5)
    shell_z=8+abs(glide)*1.1-dead*1.7
    shell_y=glide*.9
    b.ellipsoid((-2+drive*.18,shell_y,shell_z),7,6,7*(1-dead*.1),shell)
    # A spiral on each visible shell side follows the shell, preserving material identity.
    for side in (-1,1):
        points=[]
        for k in range(13):
            a=k*math.pi/3;radius=max(.5,4.8-k*.32)
            points.append((-2+drive*.18+math.cos(a)*radius,shell_y+side*5.6,shell_z+math.sin(a)*radius))
        b.line(points,shade(shell,.62),1.1)
    rise=(1-dead)*(2+charge*3+max(0,-drive)*.4)
    neck=(7+drive,0,4+rise+glide*.8)
    b.limb((3+drive*.3,0,2),neck,4.4,body)
    b.ellipsoid(neck,3.2,3.0,2.6,body)
    for side in (-1,1):
        root=(neck[0]+1,side*1.3,neck[2]+1)
        tip=(neck[0]+2-charge*2+glide,side*(3.5+charge*2),neck[2]+5*(1-dead)+charge*2)
        b.limb(root,tip,1.5,body)
        b.ellipsoid(tip,1.2,1.1,1.1,shade(body,1.3))
        b.dot((tip[0]+.5,tip[1],tip[2]+.4),s.eye if dead<.8 else '51473b')
        b.line([(neck[0]+1,side,neck[2]-1),(neck[0]+3,side*3,neck[2]-2)],shade(body,.8))
    if m['state']=='attack' and m['frame'] in (3,4):
        b.line([(neck[0]+2,-1,neck[2]-1),(neck[0]+4,0,neck[2]-2),(neck[0]+2,1,neck[2]-1)],'b88d82',2)
'''
    replace(path,'\ndef frame(definition,state,number,direction):',snail+'\n\ndef frame(definition,state,number,direction):')
    replace(path,"elif s.archetype in ('serpent','worm'):_serpent(b,s,m)",
        "elif s.archetype in ('serpent','worm'):\n        if s.shell:_snail(b,s,m)\n        else:_serpent(b,s,m)")


def main():
    repair_running()
    repair_creatures()
    replace('tools/run_character_native.py','    try:\n        run(\'import\'',"    succeeded=False\n    try:\n        run('import'")
    replace('tools/run_character_native.py','    finally:\n        images=', '        succeeded=True\n    finally:\n        images=')
    replace('tools/run_character_native.py',"'passed':len(results)==3 and all(r['passed'] for r in results)","'passed':succeeded and len(results)==3 and all(r['passed'] for r in results)")
    replace('.github/workflows/grounded-actor-acceptance.yml',"      - 'tools/run_character_native.py'","      - 'tools/run_character_native.py'\n      - 'tools/check_character_source.py'")
    replace('.github/workflows/grounded-actor-acceptance.yml','          dotnet build client/Kairnfall.Client.csproj', '          python tools/check_character_source.py 2>&1 | tee artifacts/character-acceptance/logs/source-preflight.log\n          dotnet build client/Kairnfall.Client.csproj')
    print('Fixed direction shadowing; articulated plant, mineral and snail action poses; preserved strict native success accounting.',flush=True)

if __name__=='__main__':main()
