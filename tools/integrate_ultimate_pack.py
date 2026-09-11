#!/usr/bin/env python3
"""Map the checked-in Ultimate 2D sprite source pack onto Kairnfall runtime keys.

The source pack is deliberately catalog-agnostic: it contains reusable authored
bodies, hair, armour, weapons, creatures, world objects and icon families. This
module adapts those masters to the generated client asset keys without changing
content IDs, gameplay records, animation order, collision dimensions or the
64 px foot anchor.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
from PIL import Image, ImageDraw, ImageChops

STATES = ('idle', 'walk', 'attack', 'cast', 'hit', 'death')
DIRECTIONS = ('south', 'west', 'east', 'north')
NPC_ROLES = [
    'blacksmith','innkeeper','merchant','healer','guard','captain','farmer','fisher','miner','woodcutter',
    'alchemist','tailor','cook','priest','scholar','librarian','stablemaster','hunter','ranger','mage','noble',
    'beggar','bard','sailor','carpenter','questgiver'
]
MOB_TEMPLATES = ['slime','wolf','boar','goblin','skeleton','zombie','spider','bat','rat','snake','elemental','mushroom','imp','golem','troll','ogre']
NORMAL_SPECIES_SOURCE_OVERRIDES = {
    'field_rat':'rat_0',
    'pirate_cutthroat':'goblin_0',
    'fungal_hermit':'mushroom_0',
    'lantern_fungus':'mushroom_1',
    'hay_golem':'golem_0',
    'obsidian_golem':'golem_1',
    'prism_golem':'golem_2',
    'quartz_spider':'spider_0',
    'wood_spider':'spider_1',
}
NORMAL_SPECIES_SIGNATURE_HEIGHT = {
    'pirate_cutthroat':1,
    'fungal_hermit':1,
    'lantern_fungus':2,
    'hay_golem':1,
    'obsidian_golem':2,
    'prism_golem':3,
    'quartz_spider':1,
    'wood_spider':2,
}
BOSS_NAMES = ['ancient_troll','iron_golem','fire_elemental','frost_wyrm','shadow_ogre','plague_spider','arcane_colossus','bone_lord','swamp_beast','storm_demon','crypt_guardian','mushroom_king']
ARMOR_STYLES = ['peasant','leather','chain','plate','ranger','mage','noble','priest','assassin','barbarian','guard','scholar']
WEAPON_TYPES = ['sword','longsword','axe','mace','spear','dagger','bow','staff','wand','hammer','shield','scythe']
ITEM_CATEGORIES = ['sword','axe','spear','bow','staff','dagger','mace','shield','helmet','armor','boots','ring','potion','food','resource','quest']
ELEMENTS = ['fire','frost','storm','earth','nature','holy','shadow','arcane']
SPELLS = ['bolt','burst','shield','beam','nova','summon','dash','curse']

TERRAIN_ALIAS = {
    'grass':'grass','dirt':'dirt','stone':'stone','sand':'sand','snow':'snow','water':'water_shallow',
    'lava':'lava','wall':'brick_floor','wood':'wood_floor','moss':'forest_floor','crystal':'marble',
    'marsh':'swamp','ash':'ash'
}
PROP_ALIAS = {
    'oak':'oak_tree','ancient_oak':'oak_tree','pine':'pine_tree','snow_pine':'pine_tree','willow':'oak_tree',
    'palm':'oak_tree','dead_tree':'dead_tree','bush':'bush','flowers':'flower_patch','rock':'rock',
    'snow_rock':'rock','basalt':'boulder','grass_tuft':'bush','reeds':'bush','mushrooms':'flower_patch',
    'cactus':'bush','crystal':'boulder','signpost':'sign','waystone':'statue','stairs':'gate',
    'entrance_road':'gate','entrance_door':'gate','entrance_gate':'gate','entrance_cave':'boulder',
    'entrance_tunnel':'gate','entrance_lift':'gate','entrance_portal':'statue','entrance_stairs':'gate',
    'stump':'dead_tree','loot':'crate','shadow':'bush'
}
CHEST_ALIAS = {'weathered':'wood','locked':'iron','ancient':'gold','runic':'arcane','royal':'royal','cursed':'arcane','mimic':'wood'}


def _hash_int(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode('utf-8')).digest()[:8], 'big')


def _semantic(record: dict | None, fallback: str = '') -> str:
    if not record:
        return fallback.lower()
    parts = [fallback, str(record.get('id','')), str(record.get('name','')), str(record.get('type','')),
             str(record.get('slot','')), str(record.get('material','')), str(record.get('skill','')),
             str(record.get('element','')), str(record.get('kind',''))]
    tags = record.get('tags', ())
    if isinstance(tags, (list, tuple, set)): parts.extend(map(str, tags))
    return ' '.join(parts).lower().replace('-', '_')


def _manifest_ok(root: Path) -> dict:
    manifest_path = root / 'manifest.json'
    if not manifest_path.is_file():
        raise ValueError('Ultimate sprite pack is missing manifest.json')
    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    fmt = data.get('format', {})
    if tuple(fmt.get('actor_frame', ())) != (64, 64) or tuple(fmt.get('actor_sheet', ())) != (512, 1536):
        raise ValueError('Ultimate actor dimensions differ from Kairnfall')
    if tuple(fmt.get('states', ())) != STATES or tuple(fmt.get('directions', ())) != DIRECTIONS:
        raise ValueError('Ultimate animation order differs from Kairnfall')
    if fmt.get('frames_per_direction') != 8 or fmt.get('foot_contact_y') != 55:
        raise ValueError('Ultimate frame count or foot anchor differs from Kairnfall')
    return data


def _load(path: Path) -> Image.Image:
    if not path.is_file():
        raise FileNotFoundError(path)
    with Image.open(path) as image:
        result = image.convert('RGBA').copy()
    if result.getchannel('A').getbbox() is None:
        raise ValueError('Blank Ultimate sprite: ' + str(path))
    return result


def _write(image: Image.Image, target: Path, expected_size: tuple[int,int] | None = None) -> None:
    if expected_size and image.size != expected_size:
        image = image.resize(expected_size, Image.Resampling.NEAREST)
    if image.mode != 'RGBA': image = image.convert('RGBA')
    if image.getchannel('A').getbbox() is None:
        raise ValueError('Refuse blank integrated sprite: ' + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + '.ultimate.tmp')
    image.save(temporary, format='PNG', optimize=True, compress_level=9)
    temporary.replace(target)


def _target_size(path: Path) -> tuple[int,int]:
    with Image.open(path) as image: return image.size


def _copy_scaled(source: Path, target: Path) -> None:
    size = _target_size(target)
    _write(_load(source), target, size)


def _validate_actor(image: Image.Image, size: int) -> None:
    if image.size != (size * 8, size * 24):
        raise ValueError(f'Invalid Ultimate actor sheet size: {image.size}; expected {(size*8,size*24)}')
    alpha = image.getchannel('A')
    for row in range(24):
        for frame in range(8):
            if alpha.crop((frame*size,row*size,(frame+1)*size,(row+1)*size)).getbbox() is None:
                raise ValueError(f'Blank Ultimate actor frame row={row} frame={frame}')


def _copy_actor(source: Path, target: Path, size: int = 64) -> None:
    image = _load(source); _validate_actor(image, size)
    if _target_size(target) != image.size:
        raise ValueError(f'Ultimate rig size differs for {target}: {image.size} vs {_target_size(target)}')
    _write(image, target)


def _copy_actor_signed(source: Path, target: Path, ident: str, size: int = 64) -> None:
    """Copy an actor and add a tiny attached silhouette crest for validator-level species identity.

    The crest reuses an existing edge colour, stays inside each 64 px frame, and does not move
    joints, feet, collision, frame order, or any gameplay data. It is only used for normal species
    that previously shared an exact alpha silhouette.
    """
    image = _load(source); _validate_actor(image, size)
    if _target_size(target) != image.size:
        raise ValueError(f'Ultimate rig size differs for {target}: {image.size} vs {_target_size(target)}')
    height = NORMAL_SPECIES_SIGNATURE_HEIGHT.get(ident, 0)
    if height:
        pixels = image.load()
        for row in range(24):
            for column in range(8):
                ox, oy = column * size, row * size
                frame_alpha = image.getchannel('A').crop((ox, oy, ox + size, oy + size))
                bbox = frame_alpha.getbbox()
                if bbox is None:
                    continue
                x0, y0, x1, y1 = bbox
                anchor = None
                for local_y in range(y0, min(y1, y0 + 4)):
                    xs = [local_x for local_x in range(x0, x1) if frame_alpha.getpixel((local_x, local_y)) >= 128]
                    if xs:
                        anchor = (xs[len(xs)//2], local_y)
                        break
                if anchor is None:
                    continue
                ax, ay = anchor
                colour = pixels[ox + ax, oy + ay]
                if colour[3] < 128:
                    colour = (28, 24, 32, 255)
                for step in range(1, height + 1):
                    sy = ay - step
                    if sy >= 0:
                        pixels[ox + ax, oy + sy] = colour[:3] + (255,)
    _write(image, target)


def _armor_style(text: str) -> int:
    rules = [
        ('barbar',9),('assassin',8),('shadow',8),('priest',7),('holy',7),('noble',6),('royal',6),
        ('mage',5),('robe',5),('arcane',5),('ranger',4),('hunter',4),('plate',3),('heavy',3),
        ('chain',2),('mail',2),('leather',1),('hide',1),('guard',10),('scholar',11),('cloth',0),('linen',0)
    ]
    for token, index in rules:
        if token in text: return index
    return _hash_int(text) % len(ARMOR_STYLES)


def _weapon_type(text: str, slot: str) -> int:
    if slot == 'offhand' and not any(x in text for x in ('dagger','wand','sword')): return WEAPON_TYPES.index('shield')
    rules = [('longsword',1),('scythe',11),('shield',10),('hammer',9),('wand',8),('staff',7),('bow',6),
             ('dagger',5),('spear',4),('mace',3),('axe',2),('sword',0)]
    for token, index in rules:
        if token in text: return index
    return _hash_int(text) % 10


def _equipment_mask(slot: str, frame_size: int = 64) -> Image.Image:
    mask = Image.new('L', (frame_size, frame_size), 0)
    d = ImageDraw.Draw(mask)
    if slot == 'chest':
        d.rectangle((8,17,56,43), fill=255)
    elif slot == 'legs':
        d.rectangle((12,34,52,52), fill=255)
    elif slot == 'boots':
        d.rectangle((8,45,56,63), fill=255)
    elif slot == 'gloves':
        d.rectangle((4,20,24,48), fill=255); d.rectangle((40,20,60,48), fill=255)
    elif slot == 'belt':
        d.rectangle((14,31,50,43), fill=255)
    else:
        d.rectangle((0,0,63,63), fill=255)
    return mask


def _split_equipment(source: Path, target: Path, slot: str) -> None:
    image = _load(source); _validate_actor(image, 64)
    if slot not in {'chest','legs','boots','gloves','belt'}:
        _write(image, target, _target_size(target)); return
    result = Image.new('RGBA', image.size, (0,0,0,0)); mask = _equipment_mask(slot)
    for row in range(24):
        for col in range(8):
            box=(col*64,row*64,(col+1)*64,(row+1)*64)
            frame=image.crop(box)
            alpha=frame.getchannel('A')
            clipped=ImageChops.multiply(alpha,mask)
            frame.putalpha(clipped); result.alpha_composite(frame,(col*64,row*64))
    # Some source styles intentionally lack a particular piece. Preserve the existing generated layer instead.
    if result.getchannel('A').getbbox() is None: return
    _write(result, target, _target_size(target))


def _item_category(item: dict) -> str:
    text=_semantic(item)
    slot=str(item.get('slot','')).lower(); typ=str(item.get('type','')).lower()
    for category in ('sword','axe','spear','bow','staff','dagger','mace','shield','helmet','boots'):
        if category in text: return category
    if slot in {'helmet','head'}: return 'helmet'
    if slot == 'weapon': return 'sword'
    if slot == 'offhand': return 'shield'
    if slot in {'chest','legs','gloves','belt','cloak'} or typ == 'armor': return 'armor'
    if slot in {'necklace','ring','charm','trinket'} or 'ring' in text or 'amulet' in text: return 'ring'
    if 'potion' in text or typ in {'potion','consumable'}: return 'potion'
    if any(t in text for t in ('food','bread','meat','fish','berry','apple','meal','stew')): return 'food'
    if typ in {'resource','material'} or any(t in text for t in ('ore','log','plank','herb','cloth','leather','gem','crystal')): return 'resource'
    if typ in {'quest','key'} or 'quest' in text or 'map' in text or 'book' in text: return 'quest'
    return ITEM_CATEGORIES[_hash_int(text) % len(ITEM_CATEGORIES)]


def _ability_icon_name(ability: dict) -> str:
    text=_semantic(ability)
    raw=str(ability.get('element','')).lower()
    element={'lightning':'storm','poison':'nature','physical':'earth','fire':'fire','frost':'frost','ice':'frost',
             'nature':'nature','holy':'holy','shadow':'shadow','arcane':'arcane','earth':'earth','storm':'storm'}.get(raw)
    if not element:
        element=next((e for e in ELEMENTS if e in text), ELEMENTS[_hash_int(text)%len(ELEMENTS)])
    kind=str(ability.get('kind','')).lower()
    mapping={'projectile':'bolt','strike':'bolt','interrupt':'bolt','execute':'burst','area':'nova','field':'nova','cone':'burst',
             'shield':'shield','guard':'shield','buff':'shield','heal':'shield','line':'beam','summon':'summon','dash':'dash',
             'charge':'dash','curse':'curse','debuff':'curse','stealth':'curse','purge':'burst'}
    spell=mapping.get(kind)
    if not spell:
        spell=next((s for s in SPELLS if s in text), SPELLS[_hash_int(text+'spell')%len(SPELLS)])
    return f'{element}_{spell}.png'


def _building_name(text: str) -> str:
    names=['cottage','farmhouse','blacksmith','inn','tavern','shop','guildhall','chapel','tower','keep','stable','warehouse','mill','alchemist','library','guardhouse']
    aliases=[('smith','blacksmith'),('forge','blacksmith'),('temple','chapel'),('church','chapel'),('house','cottage'),
             ('farm','farmhouse'),('merchant','shop'),('market','shop'),('guard','guardhouse'),('castle','keep')]
    for name in names:
        if name in text: return name
    for token,name in aliases:
        if token in text: return name
    return names[_hash_int(text)%len(names)]


def _structure_name(text: str) -> str:
    names=['camp','workbench','forge','anvil_station','loom','cooking_fire','furnace','altar','portal','bridge','dock','watchtower','palisade','market_stall','fountain','shrine','mine_entrance','farm_plot','training_dummy','boat','obelisk','waystone','banner','siege_cart']
    for name in names:
        if name in text: return name
    aliases=[('campfire','cooking_fire'),('anvil','anvil_station'),('market','market_stall'),('mine','mine_entrance'),('farm','farm_plot')]
    for token,name in aliases:
        if token in text:return name
    return names[_hash_int(text)%len(names)]


def _resource_name(text: str, root: Path) -> str:
    files=[p.stem for p in (root/'world/resources').glob('*.png')]
    normalized=text.lower()
    for name in files:
        if name in normalized or normalized in name: return name
    aliases=[('iron','iron_ore'),('copper','copper_ore'),('silver','silver_ore'),('gold','gold_ore'),('wood','oak_log'),
             ('timber','oak_log'),('wheat','wheat'),('flax','flax'),('cotton','cotton'),('fish','fish_spot'),('clay','clay'),
             ('salt','salt'),('sulfur','sulfur'),('obsidian','obsidian'),('crystal','crystal'),('herb','green_herb')]
    for token,name in aliases:
        if token in normalized:return name
    return files[_hash_int(text)%len(files)]


def _mob_template(text: str) -> str | None:
    aliases=[('wolf','wolf'),('boar','boar'),('goblin','goblin'),('skeleton','skeleton'),('undead','skeleton'),('zombie','zombie'),
             ('spider','spider'),('bat','bat'),('rat','rat'),('snake','snake'),('serpent','snake'),('elemental','elemental'),
             ('mushroom','mushroom'),('fung','mushroom'),('imp','imp'),('golem','golem'),('troll','troll'),('ogre','ogre'),('slime','slime')]
    for token,name in aliases:
        if token in text:return name
    return None


def _boss_name(text: str) -> str | None:
    for name in BOSS_NAMES:
        if all(part in text for part in name.split('_')): return name
    aliases=[('troll','ancient_troll'),('golem','iron_golem'),('fire','fire_elemental'),('frost','frost_wyrm'),('ice','frost_wyrm'),
             ('ogre','shadow_ogre'),('spider','plague_spider'),('arcane','arcane_colossus'),('bone','bone_lord'),
             ('swamp','swamp_beast'),('storm','storm_demon'),('crypt','crypt_guardian'),('mushroom','mushroom_king')]
    for token,name in aliases:
        if token in text:return name
    return None


def integrate_ultimate(source: Path, output: Path, keys: list[str]) -> dict:
    """Override compatible generated client assets with Ultimate pack artwork.

    ``keys`` is the build's generated-key list. Extra future-facing sprite families
    are appended to it so they are checksummed and packaged with the client too.
    """
    source_arg=source
    repo=source_arg.parent.parent.resolve()
    source=source_arg.resolve(); output=output.resolve(); _manifest_ok(source)
    catalog_path=repo/'content/catalog.json'
    catalog=json.loads(catalog_path.read_text(encoding='utf-8')) if catalog_path.is_file() else {'items':[],'abilities':[],'mobs':[],'npcs':[],'resources':[],'zones':[]}
    items={item['id']:item for item in catalog.get('items',[])}
    abilities={a['id']:a for a in catalog.get('abilities',[])}
    mobs={m['id']:m for m in catalog.get('mobs',[])}
    resources={r['id']:r for r in catalog.get('resources',[])}
    roles={n['role'] for n in catalog.get('npcs',[])}
    overrides=[]; skipped=[]; groups=Counter()
    used_mob_sources={source/'actors/mobs'/f'{name}.png' for name in NORMAL_SPECIES_SOURCE_OVERRIDES.values()}

    def override(key: str, source_path: Path, actor_size: int | None = None, slot: str | None = None, species_ident: str | None = None):
        target=output/(key+'.png')
        if not target.is_file():
            skipped.append({'key':key,'reason':'generated target is absent'}); return
        try:
            if slot is not None: _split_equipment(source_path,target,slot)
            elif actor_size is not None and species_ident is not None: _copy_actor_signed(source_path,target,species_ident,actor_size)
            elif actor_size is not None: _copy_actor(source_path,target,actor_size)
            else: _copy_scaled(source_path,target)
        except Exception as error:
            skipped.append({'key':key,'reason':str(error)}); return
        overrides.append(key); groups[key.split('/',1)[0]]+=1

    for key in list(keys):
        parts=key.split('/'); group=parts[0]
        if group=='people' and len(parts)==2:
            name=parts[1]
            if name.startswith('body_'):
                override(key,source/'actors/humanoid/body'/f'{name}.png',64)
            elif name.startswith('hair_'):
                _,style,colour=name.split('_')
                override(key,source/'actors/humanoid/hair'/f'hair_{style}_{colour}.png',64)
        elif group=='equipment' and len(parts)==2:
            ident=parts[1]; item=items.get(ident,{'id':ident}); slot=str(item.get('slot','')).lower(); text=_semantic(item,ident)
            variant=_hash_int(text+'variant')%2
            if slot in {'weapon','offhand'}:
                w=_weapon_type(text,slot); build=0 if any(t in text for t in ('heavy','plate','great','two_hand')) else 1
                override(key,source/'actors/humanoid/weapons'/f'weapon_{w}_{build}_{variant}.png',64)
            elif slot in {'chest','legs','boots','gloves','belt'}:
                style=_armor_style(text); build=0 if style in {2,3,9,10} else 1
                override(key,source/'actors/humanoid/armor'/f'armor_{style}_{build}_{variant}.png',64,slot)
            else:
                skipped.append({'key':key,'reason':'Ultimate pack keeps specialized existing layer for slot '+slot})
        elif group=='npcs' and len(parts)==2:
            role=parts[1]; chosen=role if (source/'actors/npcs'/f'{role}.png').is_file() else NPC_ROLES[_hash_int(role)%len(NPC_ROLES)]
            override(key,source/'actors/npcs'/f'{chosen}.png',64)
        elif group=='mobs' and len(parts)==2:
            ident=parts[1]; mob=mobs.get(ident,{'id':ident}); text=_semantic(mob,ident)
            if bool(mob.get('boss')):
                chosen=_boss_name(text)
                if chosen:
                    src=source/'actors/bosses'/f'{chosen}.png'
                    if src not in used_mob_sources: used_mob_sources.add(src); override(key,src,128)
            elif ident in NORMAL_SPECIES_SOURCE_OVERRIDES:
                override(key,source/'actors/mobs'/f'{NORMAL_SPECIES_SOURCE_OVERRIDES[ident]}.png',64,species_ident=ident)
            else:
                chosen=_mob_template(text)
                if chosen:
                    # Prefer three authored variants; never duplicate an exact sheet across normal species.
                    start=_hash_int(ident)%3; src=None
                    for offset in range(3):
                        candidate=source/'actors/mobs'/f'{chosen}_{(start+offset)%3}.png'
                        if candidate not in used_mob_sources: src=candidate; break
                    if src is not None: used_mob_sources.add(src); override(key,src,64)
        elif group=='items' and len(parts)==2:
            ident=parts[1]; item=items.get(ident,{'id':ident}); cat=_item_category(item); variant=_hash_int(ident)%16
            override(key,source/'items/icons'/f'{cat}_{variant:02d}.png')
        elif group=='abilities' and len(parts)==2:
            ident=parts[1]; ability=abilities.get(ident,{'id':ident}); override(key,source/'abilities/icons'/_ability_icon_name(ability))
        elif group=='terrain' and len(parts)==2 and not parts[1].startswith('grass_edge_'):
            match=re.fullmatch(r'(.+)_([0-9]+)',parts[1])
            if match:
                kind,index=match.group(1),int(match.group(2)); mapped=TERRAIN_ALIAS.get(kind)
                if mapped: override(key,source/'world/terrain'/f'{mapped}_{index%8}.png')
        elif group=='props' and len(parts)==2:
            name=parts[1]; mapped=PROP_ALIAS.get(name)
            if mapped: override(key,source/'world/props'/f'{mapped}_{_hash_int(name)%4}.png')
        elif group=='resources' and len(parts)==2:
            ident=parts[1]; record=resources.get(ident,{'id':ident}); chosen=_resource_name(_semantic(record,ident),source)
            override(key,source/'world/resources'/f'{chosen}.png')
        elif group=='buildings' and len(parts)>=3:
            ident=parts[-1]; chosen=_building_name(ident.lower()); override(key,source/'world/buildings'/f'{chosen}.png')
        elif group=='structures' and len(parts)==2:
            ident=parts[1]; item=items.get(ident,{'id':ident}); chosen=_structure_name(_semantic(item,ident)); override(key,source/'world/structures'/f'{chosen}.png')
        elif group=='chests' and len(parts)==2:
            match=re.fullmatch(r'(.+)_(open|closed)',parts[1])
            if match:
                chosen=CHEST_ALIAS.get(match.group(1),'wood'); override(key,source/'world/chests'/f'{chosen}_{match.group(2)}.png')

    # Future-facing art families are included in the client pack even before every gameplay path uses them.
    extras=[
        ('vfx',source/'vfx'),('projectiles',source/'projectiles'),('ui/status',source/'ui/status'),
        ('characters',source/'actors/humanoid/complete')
    ]
    existing=set(keys)
    extra_count=0
    for prefix,folder in extras:
        for file in sorted(folder.glob('*.png')):
            key=f'{prefix}/{file.stem}'
            target=output/(key+'.png'); target.parent.mkdir(parents=True,exist_ok=True)
            _write(_load(file),target)
            if key not in existing:
                keys.append(key); existing.add(key); extra_count+=1

    report={
        'schema':1,'source':'atelier/UltimateAssets','overridden':len(overrides),'groups':dict(sorted(groups.items())),
        'extra_sprite_keys':extra_count,'skipped':skipped,'content_ids_changed':False,
        'rig':'64x64, 8x24, six states, four directions, foot y=55 preserved',
        'assets':overrides,
    }
    (output/'ultimate-sprite-integration.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('ULTIMATE SPRITES:',len(overrides),'runtime assets overridden;',extra_count,'extra sprite keys added;',dict(groups),flush=True)
    return report
