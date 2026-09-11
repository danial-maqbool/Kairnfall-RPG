using Kairnfall.Core;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json;

/// <summary>
/// Task 2 authoritative activity audit. Fixtures place a character immediately at a valid activity and
/// immediately below a skill-level boundary; the XP itself must come from the real RealmEngine handler.
/// This is deterministic server-side acceptance evidence, not a human normal-play session.
/// </summary>
internal static class RealActivityProgressionChecks
{
    private sealed record SkillRecord(
        string Id, string Category, string Activity, long XpBefore, long XpAfter,
        int LevelBefore, int LevelAfter, double CharacterLevelBefore, double CharacterLevelAfter,
        string[] ConcreteUnlocks, bool RestartPersistence);
    private sealed record ClassRecord(
        string Id, string Role, string Passive, string[] Affinities, int AbilitiesExecuted,
        string[] AbilityKinds, bool StarterEquipmentPersisted, bool AffinityMultiplierVerified);
    private sealed record AuditRecord(string Scope, SkillRecord[] Skills, ClassRecord[] Classes, string HumanAcceptance);

    private static readonly MethodInfo HitPlayerMethod = typeof(RealmEngine).GetMethod(
        "HitPlayer", BindingFlags.Instance | BindingFlags.NonPublic)
        ?? throw new InvalidOperationException("RealmEngine.HitPlayer is unavailable to the authoritative audit.");

    [ModuleInitializer]
    internal static void RunOnWorldProbeStart()
    {
        var args = Environment.GetCommandLineArgs();
        string path = args.Length > 1 ? args[1] : "content/catalog.json";
        var data = JsonSerializer.Deserialize<Catalog>(File.ReadAllText(path), Wire.Json)
            ?? throw new InvalidDataException("Empty progression catalog.");
        var failures = new List<string>();
        var skillRecords = new List<SkillRecord>();
        var classRecords = new List<ClassRecord>();
        Run(data, failures, skillRecords, classRecords);
        Directory.CreateDirectory("artifacts/logs");
        File.WriteAllText("artifacts/logs/task2-progression-audit.json", JsonSerializer.Serialize(
            new AuditRecord(
                "All 60 skills use real RealmEngine activities; all 120 class abilities execute through their real handlers.",
                skillRecords.ToArray(), classRecords.ToArray(),
                "Human normal-play class identity, feel, pacing and physical-input acceptance remain separate."),
            new JsonSerializerOptions { WriteIndented = true }));
        if (failures.Count > 0)
            throw new InvalidDataException("Real-activity progression audit failed: " + string.Join(", ", failures));
    }

    private static void Run(Catalog data, List<string> failures, List<SkillRecord> skillRecords, List<ClassRecord> classRecords)
    {
        int passed = 0;
        void Test(string name, Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS REAL PROGRESSION: " + name); }
            catch (Exception error)
            {
                failures.Add(name);
                Console.WriteLine("FAIL REAL PROGRESSION: " + name + ": " + error);
            }
        }

        foreach (var skill in data.Skills)
        {
            Test(skill.Name + " trains through its authoritative activity", () =>
            {
                var result = TrainSkill(data, skill);
                Need(result.Character.SkillXp.GetValueOrDefault(skill.Id) > result.XpBefore,
                    skill.Id + " real activity did not award skill XP.");
                Need(Progression.BaseLevel(result.Character, skill.Id) > result.LevelBefore,
                    skill.Id + " real activity did not cross the prepared visible skill-level boundary.");
                Need(Progression.Total(result.Character) > result.TotalBefore,
                    skill.Id + " real activity did not increase accumulated character XP.");
                Need(Progression.PlayerLevelValue(result.Character) > result.CharacterLevelBefore,
                    skill.Id + " real activity did not advance character-level value.");

                var restoredRealm = new RealmEngine(data, Wire.Copy(result.Realm.State));
                var restored = restoredRealm.Player(result.Character.Id);
                Need(restored.SkillXp.GetValueOrDefault(skill.Id) == result.Character.SkillXp.GetValueOrDefault(skill.Id),
                    skill.Id + " XP did not survive a full realm-state restart roundtrip.");
                Need(Progression.BaseLevel(restored, skill.Id) == Progression.BaseLevel(result.Character, skill.Id),
                    skill.Id + " level did not survive a full realm-state restart roundtrip.");

                foreach (int milestone in skill.Unlocks)
                {
                    Need(Progression.SkillLevel(Progression.Threshold(milestone)) == milestone,
                        skill.Id + " milestone " + milestone + " is not reachable at its declared threshold.");
                    if (milestone > 1)
                        Need(Progression.SkillLevel(Progression.Threshold(milestone) - 1) == milestone - 1,
                            skill.Id + " milestone " + milestone + " opens before its threshold.");
                }

                string[] unlocks = ConcreteUnlocks(data, skill.Id);
                skillRecords.Add(new SkillRecord(
                    skill.Id, skill.Category, result.Activity, result.XpBefore,
                    result.Character.SkillXp.GetValueOrDefault(skill.Id), result.LevelBefore,
                    Progression.BaseLevel(result.Character, skill.Id), result.CharacterLevelBefore,
                    Progression.PlayerLevelValue(result.Character), unlocks, true));
            });
        }

        foreach (var cls in data.Classes)
        {
            Test(cls.Name + " executes its complete authored class kit", () =>
            {
                var abilities = cls.Abilities.Select(data.Ability).ToArray();
                Need(abilities.Length == 15, cls.Id + " no longer has 15 class abilities.");
                int executed = 0;
                foreach (var ability in abilities)
                {
                    ExecuteAbilityFixture(data, cls.Id, ability, "class-" + cls.Id + "-" + executed);
                    executed++;
                }
                Need(executed == abilities.Length, cls.Id + " did not execute its complete ability kit.");

                var realm = new RealmEngine(data);
                var player = realm.CreateCharacter("class-persist-" + cls.Id, SafeName("Class " + cls.Id), cls.Id, new());
                string weapon = player.Equipment.GetValueOrDefault("weapon")!;
                string chest = player.Equipment.GetValueOrDefault("chest")!;
                Need(weapon != "" && player.Inventory.Any(x => x.Id == weapon && x.Template == cls.Weapon),
                    cls.Id + " starter weapon identity failed.");
                Need(chest != "" && player.Inventory.Any(x => x.Id == chest && x.Template == cls.Armor),
                    cls.Id + " starter armor identity failed.");
                var persisted = new RealmEngine(data, Wire.Copy(realm.State)).Player(player.Id);
                Need(persisted.Class == cls.Id && persisted.Equipment.GetValueOrDefault("weapon") == weapon
                    && persisted.Equipment.GetValueOrDefault("chest") == chest,
                    cls.Id + " starter identity/equipment did not survive restart.");

                Need(cls.Affinity.Length == 3 && cls.Affinity.All(x => data.Skills.Any(s => s.Id == x)),
                    cls.Id + " has invalid affinity data.");
                var affinityCharacter = new Character { Class = cls.Id };
                foreach (var skill in data.Skills) affinityCharacter.SkillXp[skill.Id] = 0;
                string affinity = cls.Affinity[0];
                string neutral = data.Skills.Select(x => x.Id).First(x => !cls.Affinity.Contains(x, StringComparer.Ordinal));
                var affiliated = Wire.Copy(affinityCharacter);
                var unaffiliated = Wire.Copy(affinityCharacter);
                long affinityAward = Progression.Train(affiliated, affinity, 1000, 1, data);
                long neutralAward = Progression.Train(unaffiliated, neutral, 1000, 1, data);
                Need(affinityAward > neutralAward,
                    cls.Id + " affinity does not provide its authored training advantage.");

                classRecords.Add(new ClassRecord(
                    cls.Id, cls.Role, cls.Passive, cls.Affinity, executed,
                    abilities.Select(x => x.Kind).Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToArray(),
                    true, true));
            });
        }

        Need(skillRecords.Count == 60, "The real-activity report did not record all 60 skills.");
        Need(classRecords.Count == 8, "The class report did not record all eight classes.");
        Console.WriteLine($"REAL_ACTIVITY_PROGRESSION_AUDIT: {skillRecords.Count} skills and {classRecords.Count} classes recorded; {passed} groups passed; {failures.Count} failures. Boundary setup is fixture-seeded; XP/effects use authoritative gameplay handlers. Human normal-play acceptance remains separate.");
    }

    private sealed record ActivityResult(
        RealmEngine Realm, Character Character, string Activity, long XpBefore,
        long TotalBefore, int LevelBefore, double CharacterLevelBefore);

    private static ActivityResult TrainSkill(Catalog data, SkillDef skill)
    {
        if (skill.Category == "Weapons" && skill.Id is not "shield_mastery")
            return WeaponActivity(data, skill);
        if (skill.Category == "Magic")
            return MagicActivity(data, skill);
        if (skill.Category == "Gathering" && skill.Id is not "prospecting" and not "treasure_hunting")
            return GatherActivity(data, skill);
        if (skill.Category == "Crafting")
            return CraftActivity(data, skill);

        return skill.Id switch
        {
            "shield_mastery" => DefensiveActivity(data, skill, "shield"),
            "light_armor" or "medium_armor" or "heavy_armor" => DefensiveActivity(data, skill, "armor"),
            "evasion" => DefensiveActivity(data, skill, "evasion"),
            "endurance" => EnduranceActivity(data, skill),
            "meditation" => MeditationActivity(data, skill),
            "hunting" => KillActivity(data, skill, animal: true),
            "slayer" => KillActivity(data, skill, animal: false),
            "survival" => SurvivalActivity(data, skill),
            "exploration" => ExplorationActivity(data, skill),
            "prospecting" => ProspectingActivity(data, skill),
            "treasure_hunting" => ChestActivity(data, skill, "weathered"),
            "lockpicking" => ChestActivity(data, skill, "locked"),
            "bartering" => BarteringActivity(data, skill),
            "cartography" => CartographyActivity(data, skill),
            "animal_handling" => AnimalHandlingActivity(data, skill),
            "construction" => ConstructionActivity(data, skill),
            _ => throw new InvalidOperationException("No authoritative activity route for skill " + skill.Id)
        };
    }

    private static ActivityResult WeaponActivity(Catalog data, SkillDef skill)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-weapon-" + skill.Id, SafeName("W " + skill.Id), "vanguard", new());
        int requirement = 1;
        if (skill.Id == "unarmed_combat") p.Equipment.Remove("weapon");
        else
        {
            var def = data.Items.Where(x => x.Slot == "weapon" && x.Skill == skill.Id)
                .OrderBy(BeginnerProgression.EquipmentRequirement).FirstOrDefault()
                ?? throw new InvalidOperationException(skill.Id + " has no usable weapon training source.");
            requirement = BeginnerProgression.EquipmentRequirement(def);
            PrepareBoundary(p, skill.Id, requirement, combat: true);
            p.Equipment.Remove("weapon");
            var item = Items.Create(data, def.Id); Items.Add(p.Inventory, item, data); Items.Equip(p, item.Id, data);
        }
        if (skill.Id == "unarmed_combat") PrepareBoundary(p, skill.Id, requirement, combat: true);
        RefreshResources(p, data);
        var target = AddHostile(realm, p, TargetDefinition(data, Progression.BaseLevel(p, skill.Id)));
        double health = target.Health;
        var before = Before(realm, p, skill, skill.Id == "unarmed_combat" ? "unarmed basic attack" : "equipped-weapon basic attack");
        RequireOk(Act(realm, p, "attack", target: target.Id), skill.Id + " attack");
        Tick(realm, 10);
        Need(target.Health < health, skill.Id + " attack produced no hostile-health effect.");
        return before;
    }

    private static ActivityResult MagicActivity(Catalog data, SkillDef skill)
    {
        var preferred = data.Abilities.Where(x => x.Skill == skill.Id)
            .OrderBy(x => x.Kind is "heal" or "summon" or "shield" or "buff" or "stealth" or "purge" ? 1 : 0)
            .ThenBy(x => x.Requirement).FirstOrDefault()
            ?? throw new InvalidOperationException(skill.Id + " has no castable ability training source.");
        var fixture = ExecuteAbilityFixture(data, preferred.Class == "" ? "vanguard" : preferred.Class, preferred, "skill-" + skill.Id, prepareBoundary: true);
        return fixture;
    }

    private static ActivityResult GatherActivity(Catalog data, SkillDef skill)
    {
        var resource = data.Resources.Where(x => x.Skill == skill.Id).OrderBy(x => x.Requirement).FirstOrDefault()
            ?? throw new InvalidOperationException(skill.Id + " has no gatherable resource.");
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-gather-" + skill.Id, SafeName("G " + skill.Id), "vanguard", new());
        PrepareBoundary(p, skill.Id, resource.Requirement, combat: false);
        RefreshResources(p, data);
        string nodeId = "audit-node-" + skill.Id;
        string template = skill.Id == "farming" ? "crop_wheat" : resource.Id;
        realm.State.Nodes[nodeId] = new()
        {
            Id = nodeId, Template = template, Zone = p.Zone, Position = p.Position,
            Owner = skill.Id == "farming" ? p.Id : "", ReadyAt = realm.State.Time
        };
        int items = Items.Count(p, resource.Item);
        var before = Before(realm, p, skill, "gather " + resource.Id);
        RequireOk(Act(realm, p, "gather", target: nodeId), skill.Id + " gather");
        Need(Items.Count(p, resource.Item) > items, skill.Id + " gather produced no resource output.");
        return before;
    }

    private static ActivityResult CraftActivity(Catalog data, SkillDef skill)
    {
        var recipe = data.Recipes.Where(x => x.Skill == skill.Id).OrderBy(x => x.Requirement).FirstOrDefault()
            ?? throw new InvalidOperationException(skill.Id + " has no recipe training source.");
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-craft-" + skill.Id, SafeName("C " + skill.Id), "vanguard", new());
        PrepareBoundary(p, skill.Id, recipe.Requirement, combat: false);
        RefreshResources(p, data);
        AddIngredients(p, data, recipe.Ingredients);
        if (recipe.Station != "hand")
        {
            string station = "audit-station-" + skill.Id;
            realm.State.Nodes[station] = new() { Id = station, Template = "structure_" + recipe.Station, Zone = p.Zone, Position = p.Position, Owner = p.Id };
        }
        int output = Items.Count(p, recipe.Output);
        var before = Before(realm, p, skill, "craft " + recipe.Id);
        RequireOk(Act(realm, p, "craft", item: recipe.Id), skill.Id + " craft");
        Need(Items.Count(p, recipe.Output) > output, skill.Id + " craft produced no output.");
        return before;
    }

    private static ActivityResult DefensiveActivity(Catalog data, SkillDef skill, string kind)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-defense-" + skill.Id, SafeName("D " + skill.Id), "vanguard", new());
        PrepareBoundary(p, skill.Id, 1, combat: true);
        p.Equipment.Remove("chest");
        p.Equipment.Remove("offhand");

        if (kind == "armor")
        {
            var def = data.Items.Where(x => x.Slot == "chest" && x.Skill == skill.Id)
                .OrderBy(BeginnerProgression.EquipmentRequirement).FirstOrDefault()
                ?? throw new InvalidOperationException(skill.Id + " has no chest-armor training source.");
            int requirement = BeginnerProgression.EquipmentRequirement(def);
            PrepareBoundary(p, skill.Id, requirement, combat: true);
            var item = Items.Create(data, def.Id); Items.Add(p.Inventory, item, data); Items.Equip(p, item.Id, data);
        }
        else if (kind == "shield")
        {
            var def = data.Items.Where(x => x.Slot == "offhand" && x.Skill == "shield_mastery").OrderBy(x => x.Requirement).FirstOrDefault()
                ?? throw new InvalidOperationException("Shield Mastery has no shield equipment source.");
            var item = Items.Create(data, def.Id); item.Affixes.Add(new() { Name = "audit block", Stat = "block", Value = 45 });
            Items.Add(p.Inventory, item, data); Items.Equip(p, item.Id, data);
        }
        else if (kind == "evasion")
        {
            string equipped = p.Equipment.GetValueOrDefault("weapon")!;
            var item = p.Inventory.First(x => x.Id == equipped);
            item.Affixes.Add(new() { Name = "audit evasion", Stat = "evasion", Value = 45 });
        }

        RefreshResources(p, data);
        var mobDef = TargetDefinition(data, Progression.BaseLevel(p, skill.Id));
        var mob = AddHostile(realm, p, mobDef);
        var before = Before(realm, p, skill, kind == "armor" ? "take damage in matching armor" : kind == "shield" ? "block a hostile hit" : "evade a hostile hit");
        long xp = before.XpBefore;
        bool healthChanged = false;
        for (int attempt = 0; attempt < 160 && p.SkillXp.GetValueOrDefault(skill.Id) == xp; attempt++)
        {
            var stats = CombatMath.Stats(p, data); p.Health = stats.Health;
            double health = p.Health;
            HitPlayerMethod.Invoke(realm, [p, mob, 8.0, Element.Physical]);
            healthChanged |= p.Health < health;
        }
        Need(p.SkillXp.GetValueOrDefault(skill.Id) > xp, skill.Id + " did not train from hostile defense resolution.");
        if (kind == "armor") Need(healthChanged, skill.Id + " armor fixture never received damage.");
        return before;
    }

    private static ActivityResult EnduranceActivity(Catalog data, SkillDef skill)
    {
        var resource = data.Resources.Where(x => x.Skill == "foraging").OrderBy(x => x.Requirement).First();
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-endurance", "Endurance Audit", "vanguard", new());
        PrepareBoundary(p, skill.Id, 1, combat: false);
        SetAtLeastLevel(p, resource.Skill, resource.Requirement);
        RefreshResources(p, data);
        string id = "audit-endurance-node";
        realm.State.Nodes[id] = new() { Id = id, Template = resource.Id, Zone = p.Zone, Position = p.Position, ReadyAt = realm.State.Time };
        double stamina = p.Stamina;
        var before = Before(realm, p, skill, "gather while spending stamina");
        RequireOk(Act(realm, p, "gather", target: id), "endurance gather");
        Need(p.Stamina < stamina, "Endurance activity did not spend stamina.");
        return before;
    }

    private static ActivityResult MeditationActivity(Catalog data, SkillDef skill)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-meditation", "Meditation Audit", "arcanist", new());
        PrepareBoundary(p, skill.Id, 1, combat: false);
        RefreshResources(p, data); p.Mana = 0; realm.Active.Add(p.Id);
        var before = Before(realm, p, skill, "meditation channel while mana is missing");
        RequireOk(Act(realm, p, "meditate"), "meditation channel");
        Tick(realm, 12);
        Need(p.Mana > 0 && p.Statuses.Any(x => x.Kind == "meditate" && x.Until > realm.State.Time),
            "Meditation channel produced no mana/status effect.");
        return before;
    }

    private static ActivityResult KillActivity(Catalog data, SkillDef skill, bool animal)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-kill-" + skill.Id, SafeName("K " + skill.Id), "vanguard", new());
        PrepareBoundary(p, skill.Id, 1, combat: true);
        RefreshResources(p, data); realm.Active.Add(p.Id);
        var def = data.Mobs.Where(x => !x.Boss && !x.Elite && (!animal || x.Anatomy.StartsWith("animal:", StringComparison.Ordinal)))
            .OrderBy(x => x.Level).FirstOrDefault()
            ?? throw new InvalidOperationException("No compatible kill target for " + skill.Id);
        var mob = AddHostile(realm, p, def); mob.Health = .25;
        var before = Before(realm, p, skill, animal ? "defeat a wild animal" : "defeat a hostile creature");
        RequireOk(Act(realm, p, "attack", target: mob.Id), skill.Id + " kill attack");
        Tick(realm, 10);
        Need(mob.Health <= 0, skill.Id + " target survived the prepared kill activity.");
        return before;
    }

    private static ActivityResult SurvivalActivity(Catalog data, SkillDef skill)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-survival", "Survival Audit", "vanguard", new());
        PrepareBoundary(p, skill.Id, 1, combat: false);
        RefreshResources(p, data); p.Health = Math.Max(1, p.Health - 25); p.LastCombat = -100;
        realm.State.Nodes["audit-campfire"] = new() { Id = "audit-campfire", Template = "structure_campfire", Zone = p.Zone, Position = p.Position, Owner = p.Id };
        double health = p.Health;
        var before = Before(realm, p, skill, "rest at an owned campfire");
        RequireOk(Act(realm, p, "rest"), "survival rest");
        Need(p.Health > health, "Survival rest did not restore health.");
        return before;
    }

    private static ActivityResult ExplorationActivity(Catalog data, SkillDef skill)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-exploration", "Explore Audit", "vanguard", new());
        PrepareBoundary(p, skill.Id, 1, combat: false);
        RefreshResources(p, data); realm.Active.Add(p.Id);
        string chunk = $"{p.Zone}:{(int)p.Position.X / 16}:{(int)p.Position.Y / 16}";
        p.Discoveries.Remove(chunk);
        var before = Before(realm, p, skill, "enter an undiscovered map sector");
        Tick(realm, 1);
        Need(p.Discoveries.Contains(chunk), "Exploration activity did not record the newly visited sector.");
        return before;
    }

    private static ActivityResult ProspectingActivity(Catalog data, SkillDef skill)
    {
        var resource = data.Resources.Where(x => x.Skill == "mining").OrderBy(x => x.Requirement).First();
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-prospecting", "Prospect Audit", "vanguard", new());
        PrepareBoundary(p, skill.Id, resource.Requirement, combat: false);
        RefreshResources(p, data);
        string id = "audit-prospect-node";
        realm.State.Nodes[id] = new() { Id = id, Template = resource.Id, Zone = p.Zone, Position = p.Position, ReadyAt = realm.State.Time };
        double stamina = p.Stamina;
        var before = Before(realm, p, skill, "prospect an available ore seam");
        RequireOk(Act(realm, p, "prospect", target: id), "prospecting");
        Need(p.Stamina < stamina && p.Cooldowns.ContainsKey("prospect:" + id), "Prospecting produced no stamina/cooldown effect.");
        return before;
    }

    private static ActivityResult ChestActivity(Catalog data, SkillDef skill, string kind)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-chest-" + skill.Id, SafeName("T " + skill.Id), "vanguard", new());
        PrepareBoundary(p, skill.Id, 1, combat: false);
        RefreshResources(p, data);
        string id = "audit-chest-" + skill.Id;
        realm.State.Chests[id] = new() { Id = id, Zone = p.Zone, Position = p.Position, Kind = kind, Requirement = 1, ReadyAt = realm.State.Time };
        long gold = p.Gold;
        int lockpicks = Items.Count(p, "lockpick");
        var before = Before(realm, p, skill, kind == "locked" ? "open a locked chest" : "open a treasure chest");
        RequireOk(Act(realm, p, "chest", target: id), skill.Id + " chest");
        Need(realm.State.Chests[id].ReadyAt > realm.State.Time && p.Gold > gold, skill.Id + " chest produced no reward/cooldown effect.");
        if (kind == "locked") Need(Items.Count(p, "lockpick") < lockpicks, "Lockpicking did not consume a lockpick.");
        return before;
    }

    private static ActivityResult BarteringActivity(Catalog data, SkillDef skill)
    {
        var merchant = data.Npcs.Where(x => x.Stock.Length > 0).FirstOrDefault()
            ?? throw new InvalidOperationException("No merchant exists for Bartering.");
        string template = merchant.Stock.First(); var item = data.Item(template);
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-bartering", "Barter Audit", "vanguard", new());
        PrepareBoundary(p, skill.Id, 1, combat: false);
        p.Zone = merchant.Zone; p.Position = merchant.Position; p.Gold = 1_000_000;
        realm.State.ShopStock[merchant.Id + "/" + template] = 10;
        int count = Items.Count(p, template); long gold = p.Gold;
        var before = Before(realm, p, skill, "buy from a stocked merchant");
        RequireOk(Act(realm, p, "buy", target: merchant.Id, item: template), "bartering buy");
        Need(Items.Count(p, template) > count && p.Gold < gold, "Bartering purchase did not exchange gold for goods.");
        Need(realm.BuyPrice(p, merchant, item) <= (long)Math.Ceiling(item.Value * 1.2), "Bartering price benefit is invalid.");
        return before;
    }

    private static ActivityResult CartographyActivity(Catalog data, SkillDef skill)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-cartography", "Map Audit", "vanguard", new());
        PrepareBoundary(p, skill.Id, 1, combat: false);
        for (int i = 0; i < 4; i++) p.Discoveries.Add($"{p.Zone}:{i}:0");
        AddTemplate(p, data, "parchment", 1); AddTemplate(p, data, "ink", 1);
        var before = Before(realm, p, skill, "record a region after exploring four sectors");
        RequireOk(Act(realm, p, "chart"), "cartography chart");
        Need(p.Discoveries.Contains("charted:" + p.Zone), "Cartography did not record the completed regional chart.");
        return before;
    }

    private static ActivityResult AnimalHandlingActivity(Catalog data, SkillDef skill)
    {
        var def = data.Mobs.Where(x => !x.Boss && !x.Elite && x.Anatomy.StartsWith("animal:", StringComparison.Ordinal))
            .OrderBy(x => x.Level).FirstOrDefault()
            ?? throw new InvalidOperationException("No tameable animal exists.");
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-animal-handling", "Tame Audit", "warden", new());
        PrepareBoundary(p, skill.Id, Math.Min(99, def.Level), combat: false);
        RefreshResources(p, data); AddTemplate(p, data, "animal_bait", 1);
        var mob = AddHostile(realm, p, def); mob.Health = Math.Max(.1, def.Health * .4);
        var before = Before(realm, p, skill, "weaken and tame a wild animal");
        RequireOk(Act(realm, p, "tame", target: mob.Id), "animal handling tame");
        Need(p.Pet == mob.Id && mob.Owner == p.Id, "Animal Handling did not establish companion ownership.");
        return before;
    }

    private static ActivityResult ConstructionActivity(Catalog data, SkillDef skill)
    {
        var recipe = data.Recipes.Where(x => data.Item(x.Output).Type == "structure").OrderBy(x => x.Requirement).FirstOrDefault()
            ?? throw new InvalidOperationException("No structure recipe exists for Construction.");
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("real-construction", "Build Audit", "vanguard", new());
        PrepareBoundary(p, skill.Id, recipe.Requirement, combat: false);
        AddIngredients(p, data, recipe.Ingredients);
        var zone = data.Zones.First(x => x.Kind == "wilderness");
        Point at = BuildPoint(zone); p.Zone = zone.Id; p.Position = at; RefreshResources(p, data);
        var before = Before(realm, p, skill, "build an owned wilderness structure");
        RequireOk(Act(realm, p, "build", item: recipe.Id, x: at.X, y: at.Y), "construction build");
        Need(realm.State.Nodes.Values.Any(x => x.Owner == p.Id && x.Template == recipe.Output), "Construction produced no owned structure.");
        return before;
    }

    private static ActivityResult ExecuteAbilityFixture(Catalog data, string classId, AbilityDef ability, string suffix, bool prepareBoundary = false)
    {
        var realm = new RealmEngine(data);
        var p = realm.CreateCharacter("ability-" + suffix, SafeName("A " + suffix), classId, new());
        if (prepareBoundary) PrepareBoundary(p, ability.Skill, Math.Clamp(ability.Requirement, 1, 99), combat: true);
        else SetAtLeastLevel(p, ability.Skill, ability.Requirement);
        RefreshResources(p, data);
        SupportTraining.Record(p, Math.Clamp(Math.Max(1, ability.Requirement), 1, 100), realm.State.Time);

        bool offensive = ability.Kind is "strike" or "drain" or "dot" or "projectile" or "interrupt" or "area" or "cone" or "line" or "field";
        Creature? target = null; double targetHealth = 0;
        if (offensive || ability.Kind == "taunt")
        {
            target = AddHostile(realm, p, TargetDefinition(data, Math.Max(1, ability.Requirement)));
            targetHealth = target.Health;
        }

        var stats = CombatMath.Stats(p, data); p.Health = stats.Health; p.Mana = stats.Mana; p.Stamina = stats.Stamina;
        if (ability.Kind == "heal") p.Health = Math.Max(1, stats.Health - Math.Max(20, ability.Power * stats.Healing));
        if (ability.Kind == "purge") p.Statuses.Add(new() { Kind = "poison", Element = Element.Poison, Until = realm.State.Time + 10, Power = 1, Source = "audit" });

        Point aim = p.Position;
        if (ability.Kind == "dash")
        {
            aim = DashPoint(data.Zone(p.Zone), p.Position);
            target = AddHostile(realm, p, TargetDefinition(data, Math.Max(1, ability.Requirement)), aim);
            targetHealth = target.Health;
        }
        else if (ability.Kind != "taunt" && target is not null) aim = target.Position;

        long xpBefore = p.SkillXp.GetValueOrDefault(ability.Skill);
        long totalBefore = Progression.Total(p);
        int levelBefore = Progression.BaseLevel(p, ability.Skill);
        double characterBefore = Progression.PlayerLevelValue(p);
        double healthBefore = p.Health; Point positionBefore = p.Position;
        int statusesBefore = p.Statuses.Count; string petBefore = p.Pet;
        var result = Act(realm, p, "cast", target: ability.Kind is "dash" or "taunt" ? "" : target?.Id ?? "", item: ability.Id, x: aim.X, y: aim.Y);
        RequireOk(result, classId + "/" + ability.Id);
        Tick(realm, 12);

        bool effect = ability.Kind switch
        {
            "heal" => p.Health > healthBefore,
            "shield" => p.Statuses.Any(x => x.Kind == "shield"),
            "buff" => p.Statuses.Count > statusesBefore,
            "stealth" => p.Statuses.Any(x => x.Kind == "stealth"),
            "purge" => !p.Statuses.Any(x => x.Kind is "poison" or "burn" or "curse" or "root"),
            "summon" => p.Pet != petBefore && p.Pet != "" && realm.State.Creatures.ContainsKey(p.Pet),
            "taunt" => p.Statuses.Any(x => x.Kind == "guard") && target is not null && target.Target == p.Id,
            "dash" => p.Position != positionBefore && (target is null || target.Health < targetHealth),
            _ => target is not null && target.Health < targetHealth
        };
        Need(effect, classId + "/" + ability.Id + " produced no observable " + ability.Kind + " effect.");

        if (prepareBoundary)
        {
            var activity = new ActivityResult(realm, p, "cast " + ability.Id + " (" + ability.Kind + ")", xpBefore, totalBefore, levelBefore, characterBefore);
            return activity;
        }
        return new ActivityResult(realm, p, "class ability " + ability.Id, xpBefore, totalBefore, levelBefore, characterBefore);
    }

    private static ActivityResult Before(RealmEngine realm, Character p, SkillDef skill, string activity)
        => new(realm, p, activity, p.SkillXp.GetValueOrDefault(skill.Id), Progression.Total(p),
            Progression.BaseLevel(p, skill.Id), Progression.PlayerLevelValue(p));

    private static void PrepareBoundary(Character p, string skill, int minimumLevel, bool combat)
    {
        int level = Math.Clamp(minimumLevel, 1, 99);
        p.SkillXp[skill] = Progression.Threshold(level + 1) - 1;
        if (combat) p.CombatPracticeRemainders[skill] = .999999;
        else p.GeneralPracticeRemainders[skill] = .999999;
    }

    private static void SetAtLeastLevel(Character p, string skill, int level)
    {
        level = Math.Clamp(level, 1, Progression.SkillCap);
        p.SkillXp[skill] = Math.Max(p.SkillXp.GetValueOrDefault(skill), Progression.Threshold(level));
    }

    private static void RefreshResources(Character p, Catalog data)
    {
        var stats = CombatMath.Stats(p, data);
        p.Health = stats.Health; p.Mana = stats.Mana; p.Stamina = stats.Stamina;
        p.Cooldowns.Clear();
    }

    private static CommandResult Act(RealmEngine realm, Character p, string kind, string target = "", string item = "", string arg = "", int amount = 1, double x = 0, double y = 0)
        => realm.Execute(p.Id, new GameCommand
        {
            Kind = kind, Target = target, Item = item, Arg = arg, Amount = amount, X = x, Y = y,
            Sequence = p.LastAction + 1
        });

    private static void RequireOk(CommandResult result, string activity)
        => Need(result.Ok, activity + " rejected by the authoritative handler: " + result.Message);

    private static void Tick(RealmEngine realm, int count)
    {
        for (int i = 0; i < count; i++) realm.Tick(.1);
    }

    private static Creature AddHostile(RealmEngine realm, Character p, MobDef def, Point? position = null)
    {
        Point at = position ?? WorldMap.FindFree(realm.Data.Zone(p.Zone), new Point(p.Position.X + 1, p.Position.Y));
        if (p.Position.Distance(at) > 2) at = p.Position;
        string id = "audit-mob-" + Guid.NewGuid().ToString("N");
        var mob = new Creature { Id = id, Template = def.Id, Zone = p.Zone, Position = at, Home = at, Health = def.Health };
        realm.State.Creatures[id] = mob; return mob;
    }

    private static MobDef TargetDefinition(Catalog data, int targetLevel)
        => data.Mobs.Where(x => !x.Boss && !x.Elite)
            .OrderBy(x => Math.Abs(x.Level - Math.Clamp(targetLevel, 1, 100))).ThenBy(x => x.Level).First();

    private static Point DashPoint(ZoneDef zone, Point start)
    {
        Point[] attempts =
        [
            new(start.X + 1, start.Y), new(start.X - 1, start.Y), new(start.X, start.Y + 1), new(start.X, start.Y - 1),
            new(start.X + 1, start.Y + 1), new(start.X - 1, start.Y - 1)
        ];
        foreach (var candidate in attempts)
        {
            if (!WorldMap.Fits(zone, candidate)) continue;
            var end = WorldMap.Move(zone, start, new Point(candidate.X - start.X, candidate.Y - start.Y));
            if (start.Distance(end) > .5 && end.Distance(candidate) < .5) return candidate;
        }
        throw new InvalidOperationException("No clear one-tile dash route exists from the fixture spawn.");
    }

    private static Point BuildPoint(ZoneDef zone)
    {
        for (int radius = 7; radius < 24; radius++)
            for (int dy = -radius; dy <= radius; dy++)
                for (int dx = -radius; dx <= radius; dx++)
                {
                    if (Math.Abs(dx) != radius && Math.Abs(dy) != radius) continue;
                    var at = new Point(Math.Floor(zone.Spawn.X) + dx + .5, Math.Floor(zone.Spawn.Y) + dy + .5);
                    if (zone.Spawn.Distance(at) <= 5 || zone.Exits.Any(x => x.Position.Distance(at) <= 5)) continue;
                    if (WorldMap.Fits(zone, at)) return at;
                }
        throw new InvalidOperationException("No clear wilderness structure fixture point exists.");
    }

    private static void AddIngredients(Character p, Catalog data, IReadOnlyDictionary<string, int> ingredients)
    {
        foreach (var ingredient in ingredients) AddTemplate(p, data, ingredient.Key, ingredient.Value);
    }

    private static void AddTemplate(Character p, Catalog data, string template, int quantity)
    {
        int remaining = quantity;
        var def = data.Item(template);
        while (remaining > 0)
        {
            int part = Math.Min(remaining, Math.Max(1, def.StackMax));
            Items.Add(p.Inventory, Items.Create(data, template, part), data);
            remaining -= part;
        }
    }

    private static string[] ConcreteUnlocks(Catalog data, string skill)
        => data.Items.Where(x => x.Skill == skill && x.Slot != "").Select(x => "equipment:" + x.Id + "@" + BeginnerProgression.EquipmentRequirement(x))
            .Concat(data.Recipes.Where(x => x.Skill == skill).Select(x => "recipe:" + x.Id + "@" + x.Requirement))
            .Concat(data.Abilities.Where(x => x.Skill == skill).Select(x => "ability:" + x.Id + "@" + x.Requirement))
            .Concat(data.Resources.Where(x => x.Skill == skill).Select(x => "resource:" + x.Id + "@" + x.Requirement))
            .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToArray();

    private static string SafeName(string source)
    {
        string text = new(source.Where(char.IsLetterOrDigit).Take(18).ToArray());
        if (text.Length < 3) text = "Audit" + text;
        return text;
    }

    private static void Need(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
