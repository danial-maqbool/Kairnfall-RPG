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

# The class-identity candidate originally strengthened permanent CI by adding a
# second explicit client build. The normal repository CI already reaches the
# client through its retained Windows/client gates, and the dedicated publisher
# compiles it directly. Revert this workflow-only edit so the publication commit
# contains gameplay/client/test/docs source only and does not require workflow
# mutation permissions from the Actions token.
replace_once('.github/workflows/ci.yml',
'''      - name: Compile every implemented project and the Godot client
        run: |
          dotnet build Kairnfall.slnx -c Release | tee artifacts/logs/build.log
          dotnet build client/Kairnfall.Client.csproj -c Release | tee artifacts/logs/client-build.log
''',
'''      - name: Compile every implemented project
        run: dotnet build Kairnfall.slnx -c Release | tee artifacts/logs/build.log
''')
print('Spellblade weave classification refined; permanent CI workflow preserved.')
