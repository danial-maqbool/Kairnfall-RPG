"""Apply one reviewed source patch when the local execution environment is unavailable.

Run only on the isolated repair branch. Verify every source blob before any write.
This script does not use network access, Git credentials, or production game data.
The verification workflow tests the resulting source before committing the patch.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'src/Kairnfall.Core/Models.cs': '4b8c6792b44ebd38382a51c60a0e497a6ef4138c',
    'src/Kairnfall.Core/Mechanics.cs': 'f0e651766b8810c7276f4d74373821723fe92061',
    'src/Kairnfall.Core/RealmCombat.cs': '997ec7dc57b30a4aa3a3d0ceabb91121740d1a33',
    'src/Kairnfall.Core/RealmEngine.cs': 'ada64928b080314bb2537e942d1a457d873d3eec',
    'src/Kairnfall.Server/RealmStore.cs': '69643d7a0dc1ba22a08f41d726aea0691ef5d571',
}

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError('Expected exactly one match for reviewed edit: ' + old[:100])
    return text.replace(old, new, 1)


def main() -> None:
    marker = ROOT / 'docs/reviews/repair-source-manifest.json'
    if marker.exists():
        manifest = json.loads(marker.read_text(encoding='utf-8'))
        for path, expected in manifest['result_blobs'].items():
            if git_blob((ROOT/path).read_bytes()) != expected:
                raise RuntimeError('The applied source changed: ' + path)
        print('The exact reviewed patch is already applied.')
        return
    texts = {}
    for path, expected in EXPECTED.items():
        raw = (ROOT/path).read_bytes()
        if git_blob(raw) != expected:
            raise RuntimeError('Source changed before patch application: ' + path)
        texts[path] = raw.decode('utf-8')

    path = 'src/Kairnfall.Core/Models.cs'
    texts[path] = replace_once(texts[path], 'public sealed class Telegraph\n{\n',
        'public sealed class Telegraph\n{\n    public string Skill { get; set; } = "";\n')

    path = 'src/Kairnfall.Core/Mechanics.cs'
    text = replace_once(texts[path], 'Block=p.Equipment.ContainsKey("offhand")?',
        'Block=HandEquipment.HasUsableShield(p,data)?')
    text = replace_once(text,
        '        if(def.Tags.Contains("two_handed")) p.Equipment.Remove("offhand");\n'
        '        if(def.Slot=="offhand"&&p.Equipment.TryGetValue("weapon",out var wid)&&catalog.Item(Owned(p,wid).Template).Tags.Contains("two_handed")) throw new RuleException("Your weapon requires both hands.");\n'
        '        p.Equipment[def.Slot]=id;',
        '        if(def.Slot=="weapon"&&!HandEquipment.Compatible(def,HandEquipment.Definition(p,"offhand",catalog)))\n'
        '            p.Equipment.Remove("offhand");\n'
        '        if(def.Slot=="offhand"&&!HandEquipment.Compatible(HandEquipment.Definition(p,"weapon",catalog),def))\n'
        '            throw new RuleException("This offhand item is incompatible with your weapon.");\n'
        '        p.Equipment[def.Slot]=id;')
    text = replace_once(text, '    public static void Socket(Character p,string equipmentId,string runeId,Catalog catalog)',
        '    public static void Unequip(Character p,string slot,Catalog catalog)\n'
        '    {\n'
        '        if(!p.Equipment.Remove(slot)) throw new RuleException("That equipment slot is empty.");\n'
        '        if(slot=="weapon"&&!HandEquipment.Compatible(null,HandEquipment.Definition(p,"offhand",catalog)))\n'
        '            p.Equipment.Remove("offhand");\n'
        '    }\n'
        '    public static void Socket(Character p,string equipmentId,string runeId,Catalog catalog)')
    text = replace_once(text,
        '            if(p.SkillXp.Any(x=>!data.Skills.Any(s=>s.Id==x.Key)||x.Value<0||x.Value>Progression.Threshold(100))) errors.Add("Invalid skill XP: "+p.Id);',
        '            if(!HandEquipment.Compatible(HandEquipment.Definition(p,"weapon",data),HandEquipment.Definition(p,"offhand",data))) errors.Add("Incompatible hand equipment: "+p.Id);\n'
        '            if(p.SkillXp.Any(x=>!data.Skills.Any(s=>s.Id==x.Key)||x.Value<0||x.Value>Progression.Threshold(100))) errors.Add("Invalid skill XP: "+p.Id);')
    texts[path] = text

    path = 'src/Kairnfall.Core/RealmCombat.cs'
    text = replace_once(texts[path], 'if((weapon?.Range??1.6)>2.2)', 'if(HandEquipment.IsProjectileWeapon(weapon))')
    for old, new in [
        ('Shape="projectile",Element=weapon?.Element', 'Shape="projectile",Skill=skill,Element=weapon?.Element'),
        ('Shape="projectile",Element=ability.Element', 'Shape="projectile",Skill=ability.Skill,Element=ability.Element'),
        ('Shape=shape,Element=ability.Element', 'Shape=shape,Skill=ability.Skill,Element=ability.Element'),
        ('Shape="circle",Element=ability.Element', 'Shape="circle",Skill=ability.Skill,Element=ability.Element'),
        ('        if(!selfKind)\n        {\n', '        if(!selfKind)\n        {\n            Need(selected is null||selected.Zone==p.Zone,"The ability target is in another region.");\n'),
        ('                if(player.Health<=0||player.Zone!=t.Zone) continue;', '                if(player.Health<=0||player.Zone!=t.Zone||!Data.Skills.Any(skill=>skill.Id==t.Skill)) continue;'),
        ('HitCreature(player,mob,t.Power,t.Element,ElementSkill(t.Element))', 'HitCreature(player,mob,t.Power,t.Element,t.Skill)'),
        ('        foreach(var e in State.Events.Where(x=>x.Ends<=State.Time).ToList()) State.Events.Remove(e);', '        if(WorldEventLifecycle.Expire(State,State.Time)>0) EconomicDirty=true;'),
        ('        State.Events.Add(eNew);', '        if(State.Events.Any(value=>value.Id==eNew.Id)) return;\n        State.Events.Add(eNew);'),
        ('Data.Mobs.FirstOrDefault(x=>x.Family==(kind=="undead"?"skeleton":"elemental")&&!x.Boss)', 'Data.Mobs.Where(x=>x.Family==(kind=="undead"?"skeleton":"elemental")&&!x.Boss&&!x.Elite&&x.Level<=zone.Level+5).OrderByDescending(x=>x.Level).FirstOrDefault()'),
    ]:
        text = replace_once(text, old, new)
    old = '''    private string ElementSkill(Element element)=>element switch
    {
        Element.Fire=>"pyromancy",Element.Frost=>"cryomancy",Element.Lightning=>"stormcalling",Element.Nature=>"nature_magic",Element.Poison=>"shadow_magic",Element.Arcane=>"arcane_magic",Element.Radiant=>"radiance",Element.Shadow=>"shadow_magic",_=>"swordsmanship"
    };
'''
    text = replace_once(text, old, '')
    texts[path] = text

    path = 'src/Kairnfall.Core/RealmEngine.cs'
    text = replace_once(texts[path], '        SeedWorld();',
        '        SeedWorld();\n        if(state is not null) lastEventCycle=(long)(State.Time/300);')
    text = replace_once(text, 'Regex.IsMatch(name??"",', 'Regex.IsMatch((name??"").Trim(),')
    text = replace_once(text,
        '        if(command.Target.Length>128||command.Item.Length>128||command.Arg.Length>512||command.Kind.Length>40)',
        '        if(command.Kind is null||command.Target is null||command.Item is null||command.Arg is null) return Result(false,"Command fields cannot be null.");\n'
        '        if(command.Target.Length>128||command.Item.Length>128||command.Arg.Length>512||command.Kind.Length>40)')
    text = replace_once(text,
        'case "unequip": Need(p.Equipment.Remove(c.Arg),"That equipment slot is empty."); return "Item unequipped.";',
        'case "unequip": Items.Unequip(p,c.Arg,Data); return "Item unequipped.";')
    texts[path] = text

    path = 'src/Kairnfall.Server/RealmStore.cs'
    text = texts[path]
    old = '''        const string sql="""
            INSERT INTO realm_snapshots(id,revision,format_version,payload)
            VALUES(1,$1,1,$2)
            ON CONFLICT(id) DO UPDATE SET revision=EXCLUDED.revision,
              format_version=EXCLUDED.format_version,payload=EXCLUDED.payload,updated_at=now()
            WHERE realm_snapshots.revision=$3
            RETURNING revision;
            """;'''
    new = '''        string sql=previous==0 ? """
            INSERT INTO realm_snapshots(id,revision,format_version,payload)
            VALUES(1,$1,1,$2)
            ON CONFLICT(id) DO NOTHING
            RETURNING revision;
            """ : """
            UPDATE realm_snapshots SET revision=$1,format_version=1,payload=$2,updated_at=now()
            WHERE id=1 AND revision=$3
            RETURNING revision;
            """;'''
    text = replace_once(text, old, new)
    text = replace_once(text, '        command.Parameters.AddWithValue(previous);',
        '        if(previous>0) command.Parameters.AddWithValue(previous);')
    texts[path] = text

    # Prepare the complete change set before replacing any source file.
    output = {path: text.encode('utf-8') for path, text in texts.items()}
    for path, raw in output.items():
        (ROOT/path).write_bytes(raw)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({
        'base_commit': '5ea0ff9753e3aeabfad4610b25c839d38d49c0df',
        'original_blobs': EXPECTED,
        'result_blobs': {path: git_blob(raw) for path, raw in output.items()},
        'note': 'This records source provenance. Test outcomes are in workflow artifacts, not inferred from this file.'
    }, indent=2)+'\n', encoding='utf-8')
    for path in output:
        print('PATCHED '+path)

if __name__ == '__main__':
    main()
