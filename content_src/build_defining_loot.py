"""Authored build-defining loot metadata layered after deterministic gear progression.

This pass never creates a second art tree and never changes an existing item icon path.
It gives boss signatures, offhands, runes, and three optional micro-sets deterministic
behavior identifiers consumed by the authoritative C# rules.
"""

CLASS_EFFECTS = {
    'vanguard': 'unique_vanguard_bastion',
    'berserker': 'unique_berserker_bloodprice',
    'ranger': 'unique_ranger_quarry',
    'rogue': 'unique_rogue_venomburst',
    'arcanist': 'unique_arcanist_resonance',
    'warden': 'unique_warden_bond',
    'templar': 'unique_templar_conviction',
    'spellblade': 'unique_spellblade_weave',
}
OFFHAND_EFFECTS = {
    'shield': 'offhand_bastion',
    'focus': 'offhand_resonant_focus',
    'quiver': 'offhand_quarry_quiver',
    'orb': 'offhand_flux_orb',
}
RUNE_EFFECTS = {
    'rune_embers_': 'rune_fire_conversion',
    'rune_storm_': 'rune_lightning_conversion',
    'rune_echoes_': 'rune_resonant_echo',
    'rune_bulwark_': 'rune_guard_store',
}
SETS = (
    ('roadwarden', 25, ('armor/heavy/chest', 'offhand/shield', 'accessory/charm')),
    ('stormrunner', 55, ('armor/medium/boots', 'offhand/quiver', 'accessory/ring')),
    ('starweaver', 70, ('armor/light/gloves', 'offhand/focus', 'accessory/necklace')),
)


def _append_description(item, sentence):
    text = item.get('description', '').rstrip()
    if sentence not in text:
        item['description'] = (text + (' ' if text else '') + sentence).strip()


def build(data):
    items = {item['id']: item for item in data['items']}
    icons_before = {ident: item.get('icon', '') for ident, item in items.items()}

    # Boss signatures keep their deterministic IDs, assigned boss drops and art paths.
    boss_unique_count = 0
    for item in data['items']:
        tags = item.get('tags', [])
        if 'boss_unique' not in tags:
            continue
        class_tags = [tag.split(':', 1)[1] for tag in tags if tag.startswith('class:')]
        if len(class_tags) != 1 or class_tags[0] not in CLASS_EFFECTS:
            raise ValueError('Boss unique must identify exactly one playable class: ' + item['id'])
        item['effect'] = CLASS_EFFECTS[class_tags[0]]
        _append_description(item, 'Its signature effect becomes build-defining when the matching class engine reaches READY, but the item remains legal for off-class builds that meet its skill requirement.')
        boss_unique_count += 1
    if boss_unique_count != 40:
        raise ValueError('Expected the existing 40 class milestone boss uniques, found ' + str(boss_unique_count))

    # Every progression offhand receives a family identity instead of being a stat-only choice.
    for item in data['items']:
        if item.get('type') != 'offhand':
            continue
        families = [family for family in OFFHAND_EFFECTS if family in item.get('tags', [])]
        if len(families) != 1:
            raise ValueError('Offhand needs exactly one authored family: ' + item['id'])
        family = families[0]
        item['effect'] = OFFHAND_EFFECTS[family]
        _append_description(item, 'This offhand family has a distinct combat identity; swapping it changes the build rather than only changing its item score.')

    # Existing rune templates become bounded transforms. No new rune/item art is introduced.
    for item in data['items']:
        if item.get('type') != 'rune':
            continue
        matches = [effect for prefix, effect in RUNE_EFFECTS.items() if item['id'].startswith(prefix)]
        if matches:
            item['effect'] = matches[0]
            _append_description(item, 'This rune also carries an authored build transformation. Multiple element conversions resolve by tier and stable rune ID, never by proc order.')

    # Optional 2/3-piece sets reuse authored progression pieces at three distinct mastery bands.
    tiers = {entry['level']: entry for entry in data.get('equipmentTiers', [])}
    for set_id, level, families in SETS:
        if level not in tiers:
            raise ValueError('Missing equipment tier for set ' + set_id)
        tier = tiers[level]
        for family in families:
            ident = tier['entries'].get(family)
            if not ident or ident not in items:
                raise ValueError(set_id + ': missing set family ' + family)
            item = items[ident]
            tags = list(item.get('tags', []))
            tag = 'set:' + set_id
            if tag not in tags:
                tags.append(tag)
            item['tags'] = tags
            _append_description(item, 'Part of the optional ' + set_id.replace('_', ' ').title() + ' three-piece micro-set.')

    # Asset contract: this programme changes item behavior and presentation metadata only.
    # Every pre-existing template retains exactly the same deterministic icon path.
    icons_after = {item['id']: item.get('icon', '') for item in data['items']}
    if icons_after != icons_before:
        raise ValueError('Build-defining loot changed deterministic item icon paths.')
