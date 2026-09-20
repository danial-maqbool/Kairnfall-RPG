namespace Kairnfall.Core;

/// <summary>
/// A versioned opening built on ordinary quests, server kill credit, inventory and
/// crafting transactions. No client command sets these milestones or reward values.
/// Historical characters without EligibleKey retain their previous journey unchanged.
/// </summary>
public static class OpeningJourney
{
    public const string Prefix = "opening:v2:";
    public const string EligibleKey = Prefix + "eligible";
    public const string FightQuest = "opening_road_medicine";
    public const string CraftQuest = "opening_ready_for_the_road";
    public const string Home = "wayfarers_rest";
    public const string Foe = "field_rat";
    public const string Recipe = "brew_healing";
    public const int KillGoal = 2;
    private const string RewardPrefix = Prefix + "reward_item:";

    public static string RewardTemplate(string classId) => "opening_" + classId + "_weapon";
    public static bool Eligible(Character p) => p.Discoveries.Contains(EligibleKey);
    public static bool IsOpeningQuest(string id) => id is FightQuest or CraftQuest;
    public static bool QuestVisible(Character p, string id) => !IsOpeningQuest(id) || Eligible(p);
    public static bool Finished(Character p) => p.CompletedQuests.Contains(CraftQuest);
    public static bool Marked(Character p, string id) => p.Discoveries.Contains(Prefix + id);
    public static string RewardId(Character p) => p.Discoveries.Where(x => x.StartsWith(RewardPrefix, StringComparison.Ordinal))
        .OrderBy(x => x, StringComparer.Ordinal).Select(x => x[RewardPrefix.Length..]).FirstOrDefault() ?? "";
    public static int Kills(Character p) => Enumerable.Range(1, KillGoal).Count(n => Marked(p, "kill:" + n));
    public static bool Equipped(Character p) => Marked(p, "equipped");
    public static bool Crafted(Character p) => Marked(p, "crafted");
    public static NpcDef Giver(Catalog data) => data.Npc(data.Quest(FightQuest).Giver);
    public static AbilityDef? StarterTechnique(Catalog data, Character p) => data.Abilities.FirstOrDefault(x =>
        x.Class == p.Class && x.Requirement == 1 && x.Kind is "strike" or "projectile" or "dot");
    public static string CombatGuidance(Catalog data, Character p)
    {
        var technique = StarterTechnique(data,p);
        string art = technique is null ? "Try a starting class art from your hotbar." : "Try " + technique.Name + " from your hotbar.";
        return "Fight one Field Rat at a time. " + art + " Follow with basic attacks within your weapon's range; casters should not rely only on close staff swings. Move or dash out of attack warnings. A Healing Potion from your backpack restores 60 health; you already carry a small supply.";
    }

    private static void Mark(Character p, string id) => p.Discoveries.Add(Prefix + id);

    /// <summary>Called exclusively from the realm's successful activity/kill-credit path.</summary>
    public static void ObserveActivity(Character p, string action, string target, int amount)
    {
        if (!Eligible(p) || Finished(p) || amount < 1) return;
        if (action == "kill" && target == Foe && p.Zone == Home)
        {
            int count = Math.Min(KillGoal, Kills(p) + Math.Min(amount, KillGoal));
            for (int n = 1; n <= count; n++) Mark(p, "kill:" + n);
        }
        if (action == "craft" && target == "healing_potion") Mark(p, "crafted");
        Refresh(p);
    }

    /// <summary>Read-only comparison. Re-equipping an unchanged starter is not an upgrade.</summary>
    public static bool CurrentWeaponIsUpgrade(Catalog data, Character p)
    {
        if (!p.Equipment.TryGetValue("weapon", out var id)) return false;
        var current = p.Inventory.FirstOrDefault(x => x.Id == id);
        if (current is null || current.Durability <= 0) return false;
        if (id == RewardId(p)) return true;
        var baseline = Wire.Copy(p);
        var starter = new Item { Template = data.Class(p.Class).Weapon };
        baseline.Inventory.Add(starter); baseline.Equipment["weapon"] = starter.Id;
        var before = CombatMath.Stats(baseline, data); var after = CombatMath.Stats(p, data);
        return after.Physical >= before.Physical + 1 || after.Spell >= before.Spell + 1;
    }

    /// <summary>Called after a validated real command; never from a snapshot or UI read.</summary>
    public static void ObserveCommand(Catalog data, Character p, GameCommand command)
    {
        if (!Eligible(p) || Finished(p)) return;
        if (command.Kind == "equip" && p.CompletedQuests.Contains(FightQuest)
            && CurrentWeaponIsUpgrade(data, p)) Mark(p, "equipped");
        Refresh(p);
    }

    public static void Refresh(Character p)
    {
        if (!Eligible(p)) return;
        if (p.Quests.TryGetValue(FightQuest, out var fight))
        {
            fight.Counts = [Kills(p)];
            fight.Complete = fight.Counts[0] >= KillGoal;
        }
        if (p.Quests.TryGetValue(CraftQuest, out var craft))
        {
            craft.Counts = [Equipped(p) ? 1 : 0, Crafted(p) ? 1 : 0];
            craft.Complete = craft.Counts.All(x => x >= 1);
        }
    }

    /// <summary>
    /// A deterministic, class-compatible upgrade. No rarity, affix, socket or material
    /// roll determines this mandatory milestone. The ordinary item identity is retained.
    /// </summary>
    public static Item CreateReward(Catalog data, Character p)
    {
        var def = data.Item(RewardTemplate(p.Class));
        var reward = new Item
        {
            Template = def.Id, Rarity = Rarity.Rare, Sockets = 1,
            Affixes = [new() { Name = "Roadwarden's strength", Stat = "physical", Value = 3 },
                       new() { Name = "Roadwarden's focus", Stat = "spell", Value = 3 }]
        };
        if (def.Skill != "") reward.SkillBonuses[def.Skill] = 2;
        return reward;
    }

    /// <summary>
    /// Invoked inside ClaimQuest's existing rollback/receipt transaction. Failure to fit
    /// the complete reward bundle leaves both quests and every item/currency unchanged.
    /// </summary>
    public static void GrantFightReward(Catalog data, Character p)
    {
        if (!Eligible(p) || RewardId(p) != "" || Kills(p) < KillGoal
            || p.CompletedQuests.Contains(FightQuest) || p.Quests.ContainsKey(CraftQuest)
            || p.CompletedQuests.Contains(CraftQuest)) throw new RuleException("This opening reward is not available.");
        var reward = CreateReward(data, p);
        try
        {
            Items.Add(p.Inventory, reward, data);
            foreach (var ingredient in data.Recipe(Recipe).Ingredients)
                Items.Add(p.Inventory, Items.Create(data, ingredient.Key, ingredient.Value), data);
        }
        catch (RuleException error) when (error.Message == "Not enough storage space.")
        {
            throw new RuleException("Your reward is still with " + Giver(data).Name
                + ". Free up to three backpack slots, then choose Claim reward again. Nothing has been spent or claimed.");
        }
        p.Discoveries.Add(RewardPrefix + reward.Id);
        p.Quests[CraftQuest] = new() { Counts = [0, 0] };
        Refresh(p);
    }

    /// <summary>
    /// Protect the one-time upgrade from being lost before the equip lesson. This checks
    /// both sides of trades and all transactional transfer paths, not just the sender.
    /// Banking is allowed; no replacement copies or free resupply exploit are introduced.
    /// Once a meaningful weapon is equipped, normal ownership/market rules resume.
    /// </summary>
    public static void ValidatePendingRewardTransfers(RealmState before, RealmState after)
    {
        foreach (var old in before.Characters.Values)
        {
            if (!Eligible(old) || Equipped(old)) continue;
            string id = RewardId(old);
            if (id == "" || !old.Inventory.Concat(old.Bank).Any(x => x.Id == id)) continue;
            if (!after.Characters.TryGetValue(old.Id, out var current)
                || !Equipped(current) && !current.Inventory.Concat(current.Bank).Any(x => x.Id == id))
                throw new RuleException("Equip your opening reward once before selling, dropping or trading it. A stronger weapon also fulfils this step. Banking the reward remains available.");
        }
    }

    public static string RewardDescription(Catalog data, Character p) => "Guaranteed Rare "
        + data.Item(RewardTemplate(p.Class)).Name
        + ": 20% more base weapon power, +3 physical power and +3 spell power; an empty rune socket."
        + " Includes every ingredient for two Healing Potions. Claim transfers the bundle to your backpack; it is not a random drop.";

    public static JourneyObjective? Recommend(Catalog data, Snapshot snapshot)
    {
        var p = snapshot.Self;
        if (!Eligible(p) || Finished(p)) return null;
        var giver = Giver(data);
        JourneyObjective AtGiver(string stage, string objective, string why, string reward)
            => new(stage, "Medicine for the Road", objective, why, reward, giver.Zone, giver.Position, "npc", giver.Id, "Dialogue");
        if (!p.CompletedQuests.Contains(FightQuest))
        {
            if (!p.Quests.ContainsKey(FightQuest))
                return AtGiver("quest_offer", "Meet " + giver.Name,
                    "You are safe inside Wayfarer's Rest. Field rats have spoiled the village's medicine stores. Offer to clear the nearby path.",
                    RewardDescription(data, p) + " +" + data.Quest(FightQuest).Gold + " gold");
            if (Kills(p) >= KillGoal)
                return AtGiver("claim", "Claim your weapon and medicine supplies",
                    "The nearby path is safer. Your guaranteed reward is waiting with " + giver.Name + ", not in a loot pile.",
                    RewardDescription(data, p) + " +" + data.Quest(FightQuest).Gold + " gold");
            var foe = snapshot.Creatures.Where(x => x.Zone == Home && x.Template == Foe && x.Health > 0 && x.Owner == "")
                .OrderBy(x => x.Position.Distance(p.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
            return new("combat", "Clear the medicine path", $"Defeat Field Rats · {Kills(p)}/{KillGoal}",
                foe is null ? "No living Field Rat is in view. Return to the village path and move closer to the nearby hunting ground. Defeated normal creatures recover; do not fight stronger species to fill this objective." : CombatGuidance(data,p),
                "Return to " + giver.Name + " for your guaranteed upgrade", Home, foe?.Position ?? data.Zone(Home).Spawn,
                foe is null ? "" : "creature", foe?.Id ?? "", "Hunting");
        }
        if (!Equipped(p))
        {
            string id = RewardId(p);
            var item = p.Inventory.FirstOrDefault(x => x.Id == id);
            if (item is not null)
                return new("equipment", "Your earned upgrade", "Equip the rewarded " + data.Item(item.Template).Name,
                    "The Rare reward is already in your backpack. Review its comparison, then choose Equip. It keeps your class weapon type and an empty rune socket.",
                    "+20% base weapon power · +3 physical and spell power", p.Zone, TargetKind: "equipment", TargetId: id, Panel: "Inventory");
            if (p.Bank.Any(x => x.Id == id))
            {
                var banker = data.Npcs.Where(x => x.Role == "banker" && (x.Zone == p.Zone || NewPlayerJourney.FirstExit(data, p, x.Zone) is not null))
                    .OrderBy(x => x.Zone == p.Zone ? 0 : 1).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
                if (banker is not null)
                    return new("equipment_recovery", "Your upgrade is safe in the bank", "Withdraw your opening reward",
                        "Your item keeps the same identity. Withdraw it and equip it; no duplicate reward is needed.",
                        "Or equip an already-owned stronger weapon", banker.Zone, banker.Position, "npc", banker.Id, "Dialogue");
            }
            return new("equipment_recovery", "Finish your loadout", "Equip a stronger weapon from your backpack",
                "A meaningful weapon upgrade completes this step. Your completed fight and crafting progress are retained.",
                "Review the comparison before equipping", p.Zone, Panel: "Inventory");
        }
        if (!Crafted(p))
        {
            var recipe = data.Recipe(Recipe);
            foreach (var missing in recipe.Ingredients.Where(x => Items.Count(p, x.Key) < x.Value))
            {
                var resourceIds = data.Resources.Where(x => x.Item == missing.Key).Select(x => x.Id).ToHashSet();
                var node = snapshot.Nodes.Where(x => x.Zone == Home && resourceIds.Contains(x.Template) && x.ReadyAt <= snapshot.Time)
                    .OrderBy(x => x.Position.Distance(p.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
                if (node is not null)
                    return new("gather", "Replace the missing medicine supplies", "Gather " + data.Item(missing.Key).Name,
                        "The original supplies were moved or used. Gather only what is missing; your completed fight and upgrade stay complete.",
                        $"Need {missing.Value - Items.Count(p, missing.Key)} more", Home, node.Position, "node", node.Id, "Crafting");
                var merchant = data.Npcs.Where(x => x.Zone == Home && x.Stock.Contains(missing.Key))
                    .OrderBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
                if (merchant is not null)
                {
                    long cost = MerchantSales.BuyUnitPrice(p, merchant, data.Item(missing.Key))
                        * (missing.Value - Items.Count(p, missing.Key));
                    return new("supplies", "Replace only the missing supplies", "Buy " + data.Item(missing.Key).Name + " from " + merchant.Name,
                        "Your original reward included these ingredients. A normal merchant purchase replaces sold or used supplies; no reward is claimed twice. Gather and sell a local resource if you need gold.",
                        $"Need {missing.Value - Items.Count(p, missing.Key)} · {cost} gold at the current quote", merchant.Zone, merchant.Position, "npc", merchant.Id, "Dialogue");
                }
                if (resourceIds.Count > 0)
                    return new("gather", "Find a fresh medicine plant", "Gather " + data.Item(missing.Key).Name,
                        "Return to Wayfarer's Rest and use a fresh resource patch. Used patches recover; other players share these resources.",
                        $"Need {missing.Value - Items.Count(p, missing.Key)} more", Home, data.Zone(Home).Spawn, Panel: "Map");
            }
            var station = data.Npcs.Where(x => x.Zone == Home && x.Station == recipe.Station)
                .OrderBy(x => x.Id, StringComparer.Ordinal).First();
            return new("craft", "Restock the medicine pouch", "Brew two Healing Potions",
                "Use the village alchemy table. One batch costs 2 Meadow Leaves and 1 Empty Vial. Keep the potions: each restores 60 health when you need it.",
                "Two useful potions · all starting classes", station.Zone, station.Position, "recipe", Recipe, "Crafting");
        }
        return AtGiver("claim", "Tell " + giver.Name + " you are ready for the road",
            "You cleared the path, equipped a stronger weapon and brewed your own medicine. Your potions remain in your backpack; use them during your next fight.",
            "Next: the workshop story, or nearby travelers in Social");
    }
}
