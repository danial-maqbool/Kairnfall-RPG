"""Connected beginner hunting dungeons using existing creatures and boss mechanics."""
from .world import zone,connect


def build(data):
    zones={z['id']:z for z in data['zones']};mobs={m['id']:m for m in data['mobs']}
    resources={r['id'] for r in data['resources']}
    if 'wayfarer_burrows' in zones or 'silkroot_den' in zones:raise ValueError('Hunting routes must be installed once')
    burrows=zone('wayfarer_burrows',"Wayfarer's Burrows",'farmland',5,kind='dungeon',layer='Deepways',size=96,seed=81731,world_x=0,world_y=1)
    burrows['lore']='Old storage passages below the village lead to rat colonies and a scarred boar nesting chamber. Follow the exit markers back to daylight.'
    burrows['boss']='millbreaker'
    burrows['species']=[m for m in ('field_rat','wild_hare','wild_boar') if m in mobs]
    burrows['resources']=[r for r in ('copper_vein','oak_tree','meadow_herbs') if r in resources]
    den=zone('silkroot_den','Silkroot Den','forest',15,kind='dungeon',layer='Umbral Depths',size=96,seed=81773,world_x=1,world_y=1)
    den['lore']='Webbed root chambers join the lower road. Small ambush packs guard the path to Mother of Silk. Search side chambers rather than the entrance for hidden supplies.'
    den['boss']='mother_of_silk'
    den['species']=[m for m in ('wood_spider','field_rat','grey_wolf','wild_boar') if m in mobs]
    den['resources']=[r for r in ('iron_vein','oak_tree','meadow_herbs') if r in resources]
    data['zones'].extend([burrows,den]);zones.update({burrows['id']:burrows,den['id']:den})
    connect(zones['wayfarers_rest'],burrows,(18.5,60.5),(48.5,88.5),'stairs',1)
    connect(zones['thistle_woods'],den,(130.5,174.5),(48.5,88.5),'stairs',5)
    connect(den,zones['dawnreach_deepway'],(64.5,24.5),(48.5,8.5),'stairs',5)
    # Earlier biome lists put level-65 guardians into level-6 cellars.
    # Curate ordinary dungeon populations without replacing the boss or reward rules.
    for region in data['zones']:
        if region['kind']!='dungeon':continue
        cap=region['level']+8
        chosen=[m for m in region['species'] if mobs[m]['level']<=cap and not mobs[m]['boss']]
        desired=max(2,min(4,len(region['species'])))
        candidates=[m for m in data['mobs'] if not m['boss'] and not m['elite'] and m['level']<=cap]
        candidates.sort(key=lambda m:(m['biome']!=region['biome'],m['family'] not in ('rat','spider','bat','goblin','skeleton','boar'),abs(m['level']-region['level']),m['id']))
        for mob in candidates:
            if len(chosen)>=desired:break
            if mob['id'] not in chosen:chosen.append(mob['id'])
        region['species']=chosen
