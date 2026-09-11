"""One-time regional exploration trophies generated from authored wilderness regions."""
from .items import Builder


def build(data):
    b=Builder(data)
    regions=sorted(
        (z for z in data['zones'] if z['kind']=='wilderness' and z['layer']=='Surface'),
        key=lambda z:(z['level'],z['id']))
    for zone in regions:
        ident='keepsake_'+zone['id']
        b.item(
            ident,
            zone['name']+' Keepsake',
            'treasure',
            material='relic',
            requirement=max(1,min(100,zone['level'])),
            value=80+max(1,zone['level'])*5,
            tags=['exploration_unique','zone:'+zone['id']],
            description=(
                'A one-of-a-kind regional trophy awarded for surveying every waymark, '
                'finding the hidden cache, and charting '+zone['name']+'. '+zone['lore']))
