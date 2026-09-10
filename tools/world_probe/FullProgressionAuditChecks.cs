using Kairnfall.Core;
using System.Runtime.CompilerServices;
using System.Text.Json;

/// <summary>Exhaustive catalog and progression mechanics audit. This is automated coverage, not a human 60-skill playthrough.</summary>
internal static class FullProgressionAuditChecks
{
    [ModuleInitializer]
    internal static void RunOnWorldProbeStart()
    {
        var args=Environment.GetCommandLineArgs();
        string path=args.Length>1?args[1]:"content/catalog.json";
        var data=JsonSerializer.Deserialize<Catalog>(File.ReadAllText(path),Wire.Json)??throw new InvalidDataException("Empty progression catalog.");
        var failures=new List<string>();
        Run(data,failures);
        if(failures.Count>0) throw new InvalidDataException("Full progression audit failed: "+string.Join(", ",failures));
    }

    private static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message) { if(!value) throw new InvalidOperationException(message); }
        void Test(string name,Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS FULL PROGRESSION: "+name); }
            catch(Exception error) { failures.Add(name); Console.WriteLine("FAIL FULL PROGRESSION: "+name+": "+error.Message); }
        }

        var expectedCategories=new Dictionary<string,int>(StringComparer.Ordinal)
        {
            ["Combat"]=11,["Magic"]=11,["Defense"]=10,["Gathering"]=10,["Crafting"]=13,["Utility"]=5
        };
        var expectedClasses=new HashSet<string>(["vanguard","berserker","ranger","rogue","arcanist","warden","templar","spellblade"],StringComparer.Ordinal);
        var specialRuntimeSkills=new HashSet<string>([
            "unarmed_combat","shield_mastery","light_armor","medium_armor","heavy_armor","evasion","endurance","meditation",
            "hunting","slayer","survival","exploration","skinning","prospecting","treasure_hunting","lockpicking","bartering",
            "cartography","animal_handling","construction"
        ],StringComparer.Ordinal);

        Test("exact 60-skill taxonomy and authored training records",()=>
        {
            Need(data.Skills.Count==60,"Expected exactly 60 skills.");
            Need(data.Skills.Select(x=>x.Id).Distinct(StringComparer.Ordinal).Count()==60,"Skill IDs are not unique.");
            Need(data.Skills.Select(x=>x.Name).Distinct(StringComparer.Ordinal).Count()==60,"Skill names are not unique.");
            foreach(var pair in expectedCategories)
                Need(data.Skills.Count(x=>x.Category==pair.Key)==pair.Value,$"{pair.Key} count changed.");
            foreach(var skill in data.Skills)
            {
                Need(!string.IsNullOrWhiteSpace(skill.Action),skill.Id+" has no real training action description.");
                Need(!string.IsNullOrWhiteSpace(skill.Benefit),skill.Id+" has no benefit description.");
                Need(skill.Unlocks.SequenceEqual(new[]{1,10,25,50,75,100}),skill.Id+" unlock milestones changed or are incomplete.");
            }
        });

        Test("every skill has a concrete runtime training source",()=>
        {
            var runtime=new HashSet<string>(StringComparer.Ordinal);
            runtime.UnionWith(data.Items.Where(x=>x.Skill!="").Select(x=>x.Skill));
            runtime.UnionWith(data.Abilities.Select(x=>x.Skill));
            runtime.UnionWith(data.Resources.Select(x=>x.Skill));
            runtime.UnionWith(data.Recipes.Select(x=>x.Skill));
            runtime.UnionWith(specialRuntimeSkills);
            var missing=data.Skills.Where(x=>!runtime.Contains(x.Id)).Select(x=>x.Id).OrderBy(x=>x).ToArray();
            Need(missing.Length==0,"Skills without an item/ability/resource/recipe or explicit world/combat handler: "+string.Join(", ",missing));
        });

        foreach(var skill in data.Skills)
        {
            Test(skill.Name+" awards XP, levels and character progression with persistence",()=>
            {
                var p=new Character{Id="audit-"+skill.Id,Name="Audit "+skill.Name,Class="vanguard",Zone="wayfarers_rest"};
                long beforeXp=p.SkillXp.GetValueOrDefault(skill.Id),beforeTotal=Progression.Total(p);
                double beforeLevel=Progression.PlayerLevelValue(p);
                long award=Progression.Train(p,skill.Id,1000,1,data);
                Need(award>0,skill.Id+" produced no XP from a successful bounded award.");
                Need(p.SkillXp[skill.Id]>beforeXp,skill.Id+" XP did not increase.");
                Need(Progression.SkillLevel(p.SkillXp[skill.Id])>1,skill.Id+" did not reach a visible skill level-up.");
                Need(Progression.Total(p)>beforeTotal,skill.Id+" did not contribute to accumulated character XP.");
                Need(Progression.PlayerLevelValue(p)>beforeLevel,skill.Id+" did not advance character-level value.");
                var copy=Wire.Copy(p);
                Need(copy.SkillXp.GetValueOrDefault(skill.Id)==p.SkillXp[skill.Id],skill.Id+" XP did not survive serialization.");
                Need(Math.Abs(copy.GeneralPracticeRemainders.GetValueOrDefault(skill.Id)-p.GeneralPracticeRemainders.GetValueOrDefault(skill.Id))<1e-9,
                    skill.Id+" fractional practice did not survive serialization.");
            });
        }

        Test("exact eight-class identity set",()=>
        {
            Need(data.Classes.Count==8,"Expected exactly eight classes.");
            Need(data.Classes.Select(x=>x.Id).ToHashSet(StringComparer.Ordinal).SetEquals(expectedClasses),"Class identity set changed.");
        });

        foreach(var cls in data.Classes)
        {
            Test(cls.Name+" starter equipment, affinities, stats and ability identity",()=>
            {
                Need(!string.IsNullOrWhiteSpace(cls.Role)&&!string.IsNullOrWhiteSpace(cls.Passive),cls.Id+" lacks role/passive identity.");
                Need(cls.Affinity.Length==3&&cls.Affinity.Distinct(StringComparer.Ordinal).Count()==3,cls.Id+" must have three unique affinities.");
                Need(cls.Affinity.All(x=>data.Skills.Any(s=>s.Id==x)),cls.Id+" references an unknown affinity skill.");
                Need(cls.Stats.Count>=6&&cls.Stats.Values.All(x=>double.IsFinite(x)&&x>0),cls.Id+" has an incomplete or invalid base stat profile.");
                var weapon=data.Item(cls.Weapon); var armor=data.Item(cls.Armor);
                Need(weapon.Slot=="weapon",cls.Id+" starter weapon is not a weapon.");
                Need(armor.Slot=="chest",cls.Id+" starter armor is not chest armor.");
                Need(weapon.Skill==""||cls.Affinity.Contains(weapon.Skill),cls.Id+" starter weapon does not match class affinity.");
                var abilities=cls.Abilities.Select(data.Ability).ToArray();
                Need(abilities.Length==15,cls.Id+" must have 15 authored class abilities.");
                Need(abilities.All(x=>x.Class==cls.Id&&data.Skills.Any(s=>s.Id==x.Skill)),cls.Id+" ability ownership/skill references are invalid.");
                Need(abilities.Count(x=>x.Requirement==1)>=3,cls.Id+" lacks its three level-1 identity abilities.");
                Need(abilities.Any(x=>x.Requirement==90),cls.Id+" lacks its level-90 capstone ability.");
                Need(abilities.Any(x=>cls.Affinity.Contains(x.Skill)),cls.Id+" ability kit does not use class affinities.");

                var realm=new RealmEngine(data);
                var p=realm.CreateCharacter("audit-account-"+cls.Id,"Audit "+cls.Name,cls.Id,new());
                Need(p.Equipment.TryGetValue("weapon",out var weaponId),cls.Id+" starts without an equipped weapon.");
                Need(p.Inventory.First(x=>x.Id==weaponId).Template==cls.Weapon,cls.Id+" equips the wrong starter weapon.");
                Need(p.Equipment.TryGetValue("chest",out var chestId),cls.Id+" starts without equipped chest armor.");
                Need(p.Inventory.First(x=>x.Id==chestId).Template==cls.Armor,cls.Id+" equips the wrong starter armor.");
                var roundtrip=Wire.Copy(p);
                Need(roundtrip.Class==cls.Id&&roundtrip.Equipment.Count==p.Equipment.Count&&roundtrip.Equipment.All(x=>p.Equipment.GetValueOrDefault(x.Key)==x.Value),
                    cls.Id+" identity/equipment changed after serialization.");
            });
        }
        Console.WriteLine($"FULL_PROGRESSION_AUDIT: 60 skills and 8 classes checked; {passed} groups passed; total failures {failures.Count}. Automated mechanics/catalog audit; human normal-play acceptance remains separate.");
    }
}
