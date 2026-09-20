"""Task 17: denser settlement stories and reasons to revisit existing geography."""
from .world import REGIONS, SETTLEMENTS, DUNGEONS, ROLES, add_npc

ROLE_INDEX = {row[0]: i for i, row in enumerate(ROLES)}
REGION_NAME = {row[0]: row[1] for row in REGIONS}
REGION_LEVEL = {row[0]: row[3] for row in REGIONS}
SETTLEMENT_NAME = {row[0]: row[1] for row in SETTLEMENTS}
PARENT = {row[0]: row[2] for row in SETTLEMENTS}
DUNGEON_FOR = {row[2]: row for row in DUNGEONS}

CONTENT = {
    'reedhaven': dict(
        specialist='alchemist', landmarks=('camp', 'shrine'),
        first='The Reed Ledger',
        first_story='Reedhaven keeps two route books because floodwater can erase a path overnight. Check the abandoned camp and roadside shrine in Mosswater Basin, then compare what you saw with the settlement alchemist. Anything the waymarks reveal beyond that route is an optional lead, not a requirement.',
        second='Bitters for the Ferries',
        second_story='The ferry shelters are short on medicine and preserved food after a wet week. Gather ingredients from the same basin, prepare a small medicine batch, and have the watch confirm the road is usable before the next crossing.',
        third='Voices Below the Basin',
        third_story='The field notes point below Mosswater rather than farther west. Enter Chorus Caverns, silence the thing carrying miners voices through the fungus, then give Reedhaven scribe a route that future crews can actually follow.',
        mode='reed_medicine', stage2_reward='healing_potion'),
    'millcross': dict(
        specialist='carpenter', landmarks=('mill', 'watch'),
        first='Channels Without Water',
        first_story='Millcross has grain in storage but its irrigation marks no longer match the road ledger. Recheck the broken storehouse and old watch post in Westfarms, then take the discrepancies to the settlement carpenter. Hidden finds are useful context, never required for the repair contract.',
        second='The Millwrights Measure',
        second_story='Repairs will fail if the work crews arrive hungry and empty-handed. Gather a local herb sample, bake travel bread at the inn kitchen, and let the watch decide which service lane can carry the timber carts.',
        third='What Turned the Mill',
        third_story='The damaged channels all lead back toward the Broken Mill. Enter the mill, defeat Millbreaker, and report the cleared machinery route to Millcross scribe instead of treating the ruin as a one-time boss room.',
        mode='mill_supply', stage2_reward='bread'),
    'pinewatch': dict(
        specialist='woodworker', landmarks=('camp', 'watch'),
        first='Charcoal Marks',
        first_story='Pinewatch charcoal burners left coded marks beside the camp and watch post before they vanished. Read both sites in Pinewatch Reach and ask the woodworker which marks belong to working crews. Any cache clue uncovered on the walk remains optional.',
        second='A Beam for the Lost Post',
        second_story='The watch platform needs material cut from the same forest, not imported lumber with the wrong grain. Gather local timber, shape replacement handles, thin the nearby predators, and have the guard inspect the supply.',
        third='The Nest Above the Pines',
        third_story='Fresh cuts on the replacement beams match the route toward Watchers Nest. Clear the Sable Matron from the old post and put the approach into Pinewatch scribe ledger so the settlement has a reason to keep using the road.',
        mode='pine_repair', stage2_reward='wooden_handle'),
    'brambleford': dict(
        specialist='tailor', landmarks=('shrine', 'camp'),
        first='Boundary Knots',
        first_story='Brambleford marks its forest boundary with cloth knots rather than stone. Survey the shrine and abandoned camp in Thistle Woods, then ask the tailor which faded patterns still identify safe paths. Optional discoveries along the way stay optional.',
        second='Thread for the Boundary Flags',
        second_story='New boundary flags need local fiber and visible patrols or they are only decoration. Gather fiber, spin thread at the settlement loom, drive back common woodland threats, and have the guard approve the next set of markers.',
        third='The Road Between the Knots',
        third_story='There is no grand ruin to blame in Thistle Woods. The final job is to make the existing road itself useful: clear the creatures around two neglected waymarks, recheck those landmarks, and give the scribe a route ordinary travelers can repeat.',
        mode='bramble_flags', stage2_reward='linen_cloth'),
    'stonebridge': dict(
        specialist='fletcher', landmarks=('watch', 'shrine'),
        first='Toll Marks in Silk',
        first_story='Stonebridge traders are finding silk tied around old toll marks in Silver Run. Inspect the watch post and roadside shrine, then show the pattern to the fletcher who supplies road escorts. A discovered cache is a bonus, not a gate.',
        second='Arrows for the Toll Road',
        second_story='Escorts need replacements that can be made locally instead of waiting for a capital shipment. Gather wood, prepare an arrow bundle, reduce the creatures crowding the crossing, and let the guard check the road before the next caravan.',
        third='The Web at the Crossing',
        third_story='The silk marks lead to the Silken Tollhouse that already shadows this road. Enter it, defeat the Mother of Silk, and give Stonebridge scribe a practical return route so the crossing remains useful after the first clear.',
        mode='stone_escort', stage2_reward='arrow_bundle'),
    'copperstead': dict(
        specialist='blacksmith', landmarks=('mill', 'watch'),
        first='Assay Marks on the Verge',
        first_story='Copperstead ore carts carry stamps that no longer match the roadside records. Survey the broken storehouse and watch post in Ember Marches, then ask the local blacksmith which marks still belong to active shafts. Any cache clue is extra exploration, not mandatory work.',
        second='Ore With a Witness',
        second_story='The settlement will not certify ore that appeared from an auction crate. Mine local metal, smelt a witnessed batch, and have the guard compare it with the carts moving through Copperstead.',
        third='Heat Under the Lift',
        third_story='The mismatched assay marks trace back to Sunken Foundry. Enter the foundry, stop Kilnheart, and give Copperstead scribe the surviving route so the old lift becomes a recurring expedition instead of forgotten scenery.',
        mode='copper_assay', stage2_reward='iron_bar'),
    'whitepost': dict(
        specialist='tanner', landmarks=('watch', 'camp'),
        first='Windbreak Names',
        first_story='Whitepost changes patrol routes whenever a winter windbreak collapses. Recheck the old watch post and abandoned camp on Northern Moor, then ask the tanner who outfits patrols which names still match real shelters. Secret finds remain optional.',
        second='Hides for the Signal Crew',
        second_story='Signal crews need durable gear and a safer approach before the next storm. Gather ore for fast repairs, prepare preserved leather, reduce the local threats, and have the guard confirm the supply route.',
        third='The Winter Road Below',
        third_story='The lost patrol route descends toward Winterhorn Pass. Defeat Winterhorn, then place the return path in Whitepost scribe ledger so the settlement can keep using the under-road rather than waiting for a new map.',
        mode='whitepost_supply', stage2_reward='cured_leather'),
    'saltmere': dict(
        specialist='fisher', landmarks=('camp', 'mill'),
        first='Boats Above the Tide',
        first_story='Saltmere has boats stranded above a tide line that moved years ago. Survey the abandoned camp and broken storehouse on Saltwind Shore, then ask the fisher which marks still match working water. Cache clues discovered during the walk are optional.',
        second='A Catch for the Empty Rack',
        second_story='The smoke racks are empty because crews no longer trust the shore road. Catch local fish, clear common coastal threats, recheck the old watch line, and let the guard reopen the short hauling route.',
        third='The Bell Under the Harbor',
        third_story='Old mooring notes point toward the Unmoored Vault beneath the same coast. Defeat Captain Neris and bring Saltmere scribe a reliable approach so the vault becomes part of the harbor story rather than an isolated delve.',
        mode='salt_catch', stage2_reward='salt'),
    'gullhaven': dict(
        specialist='woodworker', landmarks=('shrine', 'watch'),
        first='Causeway Tide Marks',
        first_story='Gullhaven causeways disappear under spring tides, but old shrine and watch marks record the safe crossings. Survey both in the Gull Isles, then compare them with the woodworker who repairs the low boats. Optional cache clues do not block the job.',
        second='Timber for the Low Boats',
        second_story='The repair crews need island timber and food from the same waters they travel. Gather both, reduce the creatures crowding the causeway, and have the guard certify the route before another boat is dragged inland.',
        third='Stone Beneath the Shoals',
        third_story='The causeway records mention Reef Sanctum as a hazard below the inhabited islands. Defeat the Reef Colossus and give Gullhaven scribe a safe approach so future crews can revisit the site without expanding the chart.',
        mode='gull_repairs', stage2_reward='wooden_handle'),
    'dustwell': dict(
        specialist='scholar', landmarks=('shrine', 'camp'),
        first='Markers Under Sand',
        first_story='Dustwell remembers caravan markers the recent maps omit. Survey the roadside shrine and abandoned camp in the Dry Reach, then ask the settlement scholar why the symbols were erased. Anything hidden that the waymarks expose is optional.',
        second='Samples From the Vanished Road',
        second_story='A theory is not enough for the ledger. Gather a local mineral sample, clear creatures using the old marker line as cover, prepare durable parchment with the scribe, and let the guard seal the field record.',
        third='The Regents Missing Seal',
        third_story='The copied symbols match Regents Tomb beneath the same badlands. Defeat the Dune Regent and return the approach to Dustwell scribe so the vanished road gains a present-day purpose.',
        mode='dust_records', stage2_reward='parchment'),
}

def _objective(action, target, count=1, description=''):
    return dict(action=action, target=target, count=count,
                description=description or f'{action.title()} {target.replace("_", " ")} ({count}).')

def _zone(data, ident):
    return next((z for z in data['zones'] if z['id'] == ident), None)

def _npc(data, ident):
    return next((n for n in data['npcs'] if n['id'] == ident), None)

def _mob(data, ident):
    return next((m for m in data['mobs'] if m['id'] == ident), None)

def _resource_item(data, zone_id, skill):
    zone = _zone(data, zone_id)
    for resource_id in zone['resources']:
        resource = next((r for r in data['resources'] if r['id'] == resource_id), None)
        if resource and resource['skill'] == skill:
            return resource['item']
    raise ValueError(f'Task 17: {zone_id} has no {skill} resource.')

def _kill_target(data, zone_id):
    zone = _zone(data, zone_id)
    for ident in zone['species']:
        mob = _mob(data, ident)
        if mob and not mob['boss'] and not mob['elite']:
            return mob['id']
    raise ValueError(f'Task 17: {zone_id} has no ordinary creature target.')

def _resolution_reward(level):
    if level < 15:
        return 'rune_precision_1'
    if level < 30:
        return 'rune_embers_2'
    if level < 50:
        return 'rune_wanderer_3'
    return 'rune_warding_4'

def _validate_quest(data, quest):
    items = {x['id'] for x in data['items']}
    zones = {x['id'] for x in data['zones']}
    npcs = {x['id'] for x in data['npcs']}
    mobs = {x['id'] for x in data['mobs']}
    buildings = {b['id'] for z in data['zones'] for b in z['buildings']}
    resource_items = {x['item'] for x in data['resources']}
    craft_outputs = {x['output'] for x in data['recipes']}
    quests = {x['id'] for x in data['quests']}
    if quest['giver'] not in npcs:
        raise ValueError(f"Task 17: missing giver for {quest['id']}.")
    if quest['reward'] and quest['reward'] not in items:
        raise ValueError(f"Task 17: missing reward for {quest['id']}.")
    if quest['prerequisite'] and quest['prerequisite'] not in quests:
        raise ValueError(f"Task 17: missing prerequisite for {quest['id']}.")
    for one in quest['objectives']:
        action, target = one['action'], one['target']
        valid = (
            action in {'explore', 'chart'} and target in zones or
            action == 'survey' and target in buildings or
            action == 'talk' and target in npcs or
            action in {'kill', 'boss'} and target in mobs or
            action == 'gather' and target in resource_items or
            action == 'craft' and target in craft_outputs
        )
        if not valid:
            raise ValueError(f"Task 17: invalid {action}:{target} in {quest['id']}.")

def _add_quest(data, ident, name, giver, story, objectives, prerequisite, reward, gold, minimum):
    quest = dict(
        id=ident, name=name, giver=giver, story=story, objectives=objectives,
        category='regional', prerequisite=prerequisite, reward=reward, gold=gold,
        faction='wayfarers', repeatable=False, minimumLevel=minimum)
    _validate_quest(data, quest)
    data['quests'].append(quest)

def _stage_two(data, settlement, parent, mode, guard_id):
    region_name = REGION_NAME[parent]
    mob = _kill_target(data, parent)
    if mode == 'reed_medicine':
        return [
            _objective('gather', _resource_item(data, parent, 'herbalism'), 4, f'Gather 4 medicinal plants in {region_name}.'),
            _objective('gather', _resource_item(data, parent, 'fishing'), 2, f'Catch 2 local fish in {region_name}.'),
            _objective('craft', 'healing_potion', 2, 'Brew 2 healing potions for the ferry shelters.'),
            _objective('talk', guard_id, 1, f'Ask the {SETTLEMENT_NAME[settlement]} guard to reopen the ferry road.')]
    if mode == 'mill_supply':
        return [
            _objective('gather', _resource_item(data, parent, 'herbalism'), 3, f'Gather 3 useful herbs from {region_name}.'),
            _objective('craft', 'bread', 3, 'Bake 3 loaves for the repair crew.'),
            _objective('kill', mob, 2, f'Drive 2 common threats away from the {region_name} service lanes.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard approve the cart lane.')]
    if mode == 'pine_repair':
        return [
            _objective('gather', _resource_item(data, parent, 'woodcutting'), 4, f'Cut 4 pieces of local timber in {region_name}.'),
            _objective('craft', 'wooden_handle', 2, 'Shape 2 replacement handles.'),
            _objective('kill', mob, 3, f'Clear 3 common creatures from the work route in {region_name}.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard inspect the repair stock.')]
    if mode == 'bramble_flags':
        return [
            _objective('gather', 'fiber', 4, f'Gather 4 fiber in {region_name}.'),
            _objective('craft', 'thread', 3, 'Spin 3 lengths of thread for boundary flags.'),
            _objective('kill', mob, 3, f'Clear 3 common creatures from the boundary line in {region_name}.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard approve the marker route.')]
    if mode == 'stone_escort':
        return [
            _objective('gather', _resource_item(data, parent, 'woodcutting'), 3, f'Gather 3 pieces of local wood in {region_name}.'),
            _objective('craft', 'arrow_bundle', 10, 'Prepare one matched bundle of 10 arrows for the escort.'),
            _objective('kill', mob, 3, f'Clear 3 common creatures near the {region_name} crossing.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard check the toll road.')]
    if mode == 'copper_assay':
        return [
            _objective('gather', _resource_item(data, parent, 'mining'), 5, f'Mine 5 pieces of local ore in {region_name}.'),
            _objective('craft', 'iron_bar', 2, 'Smelt 2 iron bars from traceable ore.'),
            _objective('kill', mob, 2, f'Clear 2 common creatures from the ore-cart road in {region_name}.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard witness the shipment.')]
    if mode == 'whitepost_supply':
        return [
            _objective('gather', _resource_item(data, parent, 'mining'), 4, f'Mine 4 pieces of local ore for quick repairs in {region_name}.'),
            _objective('craft', 'cured_leather', 2, 'Prepare 2 cured leather for signal-crew gear.'),
            _objective('kill', mob, 3, f'Clear 3 common creatures from the winter approach in {region_name}.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard confirm the signal route.')]
    if mode == 'salt_catch':
        return [
            _objective('gather', _resource_item(data, parent, 'fishing'), 4, f'Catch 4 local fish along {region_name}.'),
            _objective('kill', mob, 3, f'Clear 3 common coastal threats from {region_name}.'),
            _objective('survey', parent + '_watch', 1, f'Recheck the Old Watch Post on {region_name}.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard reopen the hauling lane.')]
    if mode == 'gull_repairs':
        return [
            _objective('gather', _resource_item(data, parent, 'fishing'), 4, f'Catch 4 local fish around {region_name}.'),
            _objective('gather', _resource_item(data, parent, 'woodcutting'), 3, f'Cut 3 pieces of island timber in {region_name}.'),
            _objective('kill', mob, 2, f'Clear 2 common creatures from the causeway in {region_name}.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard certify the crossing.')]
    if mode == 'dust_records':
        return [
            _objective('gather', _resource_item(data, parent, 'mining'), 4, f'Mine 4 local mineral samples in {region_name}.'),
            _objective('kill', mob, 3, f'Clear 3 common creatures from the old marker line in {region_name}.'),
            _objective('craft', 'parchment', 2, 'Prepare 2 durable parchment sheets for the field record.'),
            _objective('talk', guard_id, 1, f'Have the {SETTLEMENT_NAME[settlement]} guard seal the field record.')]
    raise ValueError(f'Task 17: unknown activity mode {mode}.')

def build(data):
    # Minor settlements previously carried only an innkeeper, provisioner, and traveler.
    # Add compact local purpose without adding zones or changing the overworld footprint.
    for index, (settlement, _, parent) in enumerate(SETTLEMENTS):
        spec = CONTENT[settlement]
        specialist = spec['specialist']
        for offset, (role, position) in enumerate([
            ('guard', (34.5, 43.5)),
            (specialist, (46.5, 43.5)),
            ('scribe', (40.5, 46.5)),
        ]):
            add_npc(data, _zone(data, settlement), ROLE_INDEX[role], 100 + index * 3 + offset,
                    'wayfarers', position)

        guard_id = settlement + '_guard'
        specialist_id = settlement + '_' + specialist
        scribe_id = settlement + '_scribe'
        level = REGION_LEVEL[parent]
        minimum = max(1, level - 5)
        landmarks = spec['landmarks']

        first_id = f'local_{settlement}_01'
        first_objectives = [
            _objective('explore', parent, 1, f'Reach {REGION_NAME[parent]} from {SETTLEMENT_NAME[settlement]}.'),
            _objective('survey', parent + '_' + landmarks[0], 1, f'Survey {landmarks[0].replace("_", " ")} in {REGION_NAME[parent]}.'),
            _objective('survey', parent + '_' + landmarks[1], 1, f'Survey {landmarks[1].replace("_", " ")} in {REGION_NAME[parent]}.'),
            _objective('talk', specialist_id, 1, f'Compare the route with the {specialist.replace("_", " ")} in {SETTLEMENT_NAME[settlement]}.'),
        ]
        _add_quest(data, first_id, spec['first'], settlement + '_traveler',
                   spec['first_story'], first_objectives, '', 'parchment',
                   30 + level * 2, minimum)

        second_id = f'local_{settlement}_02'
        _add_quest(data, second_id, spec['second'], specialist_id,
                   spec['second_story'], _stage_two(data, settlement, parent, spec['mode'], guard_id),
                   first_id, spec['stage2_reward'], 45 + level * 3, minimum)

        third_id = f'local_{settlement}_03'
        dungeon_row = DUNGEON_FOR.get(parent)
        if dungeon_row is not None:
            dungeon_id, dungeon_name, _, _, _, boss_id = dungeon_row
            boss = _mob(data, boss_id)
            challenge_level = boss['level']
            third_objectives = [
                _objective('explore', dungeon_id, 1, f'Enter {dungeon_name} from the existing {REGION_NAME[parent]} route.'),
                _objective('boss', boss_id, 1, f'Defeat {boss["name"]} in {dungeon_name}.'),
                _objective('talk', scribe_id, 1, f'Record the return route with the {SETTLEMENT_NAME[settlement]} scribe.'),
            ]
        else:
            challenge_level = level
            mob = _kill_target(data, parent)
            third_objectives = [
                _objective('kill', mob, 5, f'Clear 5 common threats from the working roads of {REGION_NAME[parent]}.'),
                _objective('survey', parent + '_watch', 1, f'Recheck the Old Watch Post in {REGION_NAME[parent]}.'),
                _objective('survey', parent + '_mill', 1, f'Recheck the Broken Storehouse in {REGION_NAME[parent]}.'),
                _objective('talk', scribe_id, 1, f'Record the maintained road with the {SETTLEMENT_NAME[settlement]} scribe.'),
            ]
        _add_quest(data, third_id, spec['third'], guard_id,
                   spec['third_story'], third_objectives, second_id,
                   _resolution_reward(challenge_level), 80 + challenge_level * 4,
                   max(minimum, challenge_level - 5))
