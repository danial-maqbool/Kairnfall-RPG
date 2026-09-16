"""Versioned first-session quest content. Existing story IDs and rewards are unchanged.

The realm opts newly created characters into these quests; historical saves are not
silently enrolled. Class-specific reward construction remains on the server.
"""
from __future__ import annotations
from copy import deepcopy

FIGHT_QUEST = 'opening_road_medicine'
CRAFT_QUEST = 'opening_ready_for_the_road'


def build(data: dict) -> None:
    quests = {quest['id']: quest for quest in data['quests']}
    if FIGHT_QUEST in quests or CRAFT_QUEST in quests:
        raise ValueError('Opening quest identifiers already exist')
    giver = quests['main_01']['giver']
    if next(npc for npc in data['npcs'] if npc['id'] == giver)['zone'] != 'wayfarers_rest':
        raise ValueError('The opening giver must be in the safe starter village')
    recipe = next(recipe for recipe in data['recipes'] if recipe['id'] == 'brew_healing')
    if (recipe['requirement'] != 1 or recipe['output'] != 'healing_potion'
            or recipe['quantity'] != 2 or recipe['station'] != 'alchemy_table'
            or recipe['ingredients'] != {'meadow_leaf': 2, 'empty_vial': 1}):
        raise ValueError('Review the opening explanation and supply bundle after changing the starter medicine recipe')
    names = {
        'vanguard': "Roadwarden's Longsword", 'berserker': "Roadwarden's Greataxe",
        'ranger': "Roadwarden's Recurve", 'rogue': "Roadwarden's Dirk",
        'arcanist': "Roadwarden's Focus Staff", 'warden': "Roadwarden's Thornstaff",
        'templar': "Roadwarden's Flanged Mace", 'spellblade': "Roadwarden's Arming Sword",
    }
    items = {item['id']: item for item in data['items']}
    for cls in data['classes']:
        identity = 'opening_' + cls['id'] + '_weapon'
        if identity in items or cls['id'] not in names:
            raise ValueError('Review the opening reward mapping for ' + cls['id'])
        reward = deepcopy(items[cls['weapon']])
        reward.update(id=identity, name=names[cls['id']], icon=identity,
                      description="Bren's earned roadwarden weapon. Its blue grip and brass maker's mark identify the village reward while preserving your starting weapon training.")
        reward['tags'] = list(dict.fromkeys(reward.get('tags', []) + ['opening_reward', 'class:' + cls['id']]))
        data['items'].append(reward)
    data['quests'].extend([
        dict(id=FIGHT_QUEST, name='Medicine for the Road', giver=giver,
             story="Welcome to Wayfarer's Rest. Field rats have spoiled our medicine stores. Clear two from the nearby path, then return. I will give you a better weapon for your training and everything needed to brew fresh medicine.",
             category='side', prerequisite='', faction='wayfarers', minimumLevel=1,
             objectives=[dict(action='opening_kill', target='field_rat', count=2,
                              description='Defeat two Field Rats near Wayfarer\'s Rest')],
             gold=20, reward='', repeatable=False),
        dict(id=CRAFT_QUEST, name='Ready for the Road', giver=giver,
             story='Your earned weapon and medicine ingredients are already in your backpack. Equip the upgrade, then brew one batch of Healing Potions at the village alchemy table. Keep the medicine and tell me when you are ready to travel.',
             category='side', prerequisite=FIGHT_QUEST, faction='wayfarers', minimumLevel=1,
             objectives=[dict(action='opening_equip', target='weapon', count=1,
                              description='Equip the rewarded weapon or an already-owned stronger weapon'),
                         dict(action='opening_craft', target='healing_potion', count=1,
                              description='Brew Healing Potions at the village alchemy table')],
             gold=0, reward='', repeatable=False),
    ])
