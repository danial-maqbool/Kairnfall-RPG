#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def replace_once(path,old,new):
    target=ROOT/path
    text=target.read_text(encoding='utf-8')
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f'{path}: expected one match, found {count}')
    target.write_text(text.replace(old,new,1),encoding='utf-8')

replace_once('src/Kairnfall.Core/ClassCombatRules.cs',
'''    private static bool Defensive(AbilityDef ability) => ability.Kind is "shield" or "taunt" or "buff";
    private static bool Support(AbilityDef ability) => ability.Kind is "heal" or "shield" or "summon" or "purge" or "buff";
''',
'''    private static bool Defensive(AbilityDef ability) => ability.Kind is "shield" or "taunt" or "buff";
    private static bool Support(AbilityDef ability) => ability.Kind is "heal" or "shield" or "summon" or "purge" or "buff";
    private static string SpellbladeFamily(string skill,Element element)
        => skill is "swordsmanship" or "axe_mastery" or "mace_mastery" or "spear_mastery" or "dagger_mastery" or "unarmed_combat"
            ? "martial" : element==Element.Physical ? "martial" : "magic";
''')
replace_once('src/Kairnfall.Core/ClassCombatRules.cs',
'''                string family = ability.Element == Element.Physical ? "martial" : "magic";
''',
'''                string family = SpellbladeFamily(ability.Skill,ability.Element);
''')
replace_once('src/Kairnfall.Core/ClassCombatRules.cs',
'''                string family = element == Element.Physical ? "martial" : "magic";
''',
'''                string family = SpellbladeFamily(skill,element);
''')
print('Spellblade weave classification refined.')
