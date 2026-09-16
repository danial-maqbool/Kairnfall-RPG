using System.Runtime.CompilerServices;
using System.Text.Json;
using Kairnfall.Core;

/// <summary>
/// Isolated integrated realm regressions. Fixture placement/clock advancement are
/// explicit; combat, rewards, equipment, crafting, shops and receipt replay use the
/// production command path. These are not native UI input or human pacing results.
/// </summary>
internal static class OpeningJourneyChecks
{
    [ModuleInitializer]
    internal static void Run()
    {
        var arguments = Environment.GetCommandLineArgs();
        var data = Catalog.Load(arguments.Length > 1 ? arguments[1] : "content/catalog.json");
        var failures = new List<string>(); int passed = 0, completedClasses = 0;
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        void Need(bool condition, string message)
        {
            if (!condition) throw new InvalidOperationException(message);
        }
        void Test(string title, Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS OPENING: " + title); }
            catch (Exception error) { failures.Add(title + ": " + error.Message); Console.WriteLine("FAIL OPENING: " + title + ": " + error); }
        }
        GameCommand Cmd(RealmEngine realm, string id, string kind, string target = "", string item = "", int quantity = 1, string arg = "")
            => new() { Kind = kind, Target = target, Item = item, Amount = quantity, Arg = arg,
                Sequence = realm.Player(id).LastAction + 1, RequestId = Guid.NewGuid().ToString("N") };
        void Act(RealmEngine realm, string id, GameCommand cmd)
        {
            var result = realm.Execute(id, cmd);
            Need(result.Ok, realm.Player(id).Class + " · " + cmd.Kind + " · " + cmd.Item + " · health=" + realm.Player(id).Health + ": " + result.Message);
        }
        void Advance(RealmEngine realm, double seconds)
        {
            double end = realm.State.Time + seconds;
            while (realm.State.Time + .0001 < end) realm.Tick(.1);
        }
        void Place(RealmEngine realm, string id, string zone, Point destination)
        {
            Need(WorldMap.Fits(data.Zone(zone), destination), "Fixture destination is not actor-fit: " + zone + " " + destination);
            var p = realm.Player(id);
            if (p.Zone == zone) Need(p.Position.Distance(destination) < 1
                || WorldMap.FindPath(data.Zone(zone), p.Position, destination, data.Zone(zone).Width * data.Zone(zone).Height * 2).Count > 0,
                "Fixture destination is not reachable: " + destination);
            p.Zone = zone; p.Position = destination;
        }
        void AtGiver(RealmEngine realm, string id)
        {
            var npc = OpeningJourney.Giver(data); Place(realm, id, npc.Zone, npc.Position);
        }
        RealmEngine Restart(RealmEngine realm, string id)
        {
            string before = Json(realm.Player(id));
            realm.Disconnect(id);
            var restored = new RealmEngine(data, Wire.Copy(realm.State)) { Loot = Wire.Copy(realm.Loot) };
            restored.Active.Add(id);
            Need(Json(restored.Player(id)) == before, "Restart/reconnect changed the character's persisted state.");
            return restored;
        }
        (RealmEngine Realm, string Id) Fresh(string cls = "vanguard")
        {
            var realm = new RealmEngine(data);
            var p = realm.CreateCharacter("opening-isolated", "Opening Hero", cls, new());
            realm.Active.Add(p.Id);
            Need(OpeningJourney.Eligible(p), "A fresh character did not opt into the new opening.");
            Need(NewPlayerJourney.Recommend(data, realm.Snapshot(p.Id)).TargetId == OpeningJourney.Giver(data).Id,
                "Initial guidance does not lead to the intended nearby NPC.");
            return (realm, p.Id);
        }
        void Accept(RealmEngine realm, string id)
        {
            AtGiver(realm, id);
            Act(realm, id, Cmd(realm, id, "talk", OpeningJourney.Giver(data).Id));
            Act(realm, id, Cmd(realm, id, "accept_quest", item: OpeningJourney.FightQuest));
        }
        void Fight(RealmEngine realm, string id)
        {
            int start = OpeningJourney.Kills(realm.Player(id));
            for (int kill = start; kill < OpeningJourney.KillGoal; kill++)
            {
                var target = realm.State.Creatures.Values.Where(x => x.Zone == OpeningJourney.Home && x.Template == OpeningJourney.Foe && x.Owner == "" && x.Health > 0)
                    .OrderBy(x => x.Position.Distance(realm.Player(id).Position)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
                Need(target is not null, "The opening needs two living, reachable starter rats without waiting on a respawn.");
                for (int strike = 0; target!.Health > 0 && strike < 80; strike++)
                {
                    var p = realm.Player(id);
                    Need(p.Health > 0, "A supported starting class died during the isolated two-rat fixture.");
                    Place(realm, id, target.Zone, target.Position);
                    // Use the same class technique named by the contextual opening
                    // guidance. The former fixture kept Arcanists in melee using only
                    // weak staff basics for two fights, contrary to their authored kit.
                    var potion = p.Inventory.FirstOrDefault(x => x.Template == "healing_potion");
                    if (p.Health < CombatMath.Stats(p,data).Health * .6 && potion is not null
                        && p.Cooldowns.GetValueOrDefault("potion") <= realm.State.Time)
                        Act(realm,id,Cmd(realm,id,"consume",item:potion.Id));
                    var technique = OpeningJourney.StarterTechnique(data,p)
                        ?? throw new InvalidOperationException("No contextual starting technique for " + p.Class);
                    if (p.Cooldowns.GetValueOrDefault("ability:"+technique.Id) <= realm.State.Time
                        && p.Cooldowns.GetValueOrDefault("global_ability") <= realm.State.Time
                        && p.Mana >= technique.Mana && p.Stamina >= technique.Stamina)
                        Act(realm,id,Cmd(realm,id,"cast",target.Id,technique.Id));
                    else Act(realm, id, Cmd(realm, id, "attack", target.Id));
                    Advance(realm, 2);
                }
                Need(target.Health <= 0, "Real attacks did not defeat the starter rat.");
                Need(OpeningJourney.Kills(realm.Player(id)) == kill + 1, "Real kill credit did not advance exactly one opening count.");
            }
        }
        GameCommand Claim(RealmEngine realm, string id)
        {
            AtGiver(realm, id);
            var command = Cmd(realm, id, "claim_quest", item: OpeningJourney.FightQuest);
            Act(realm, id, command); return command;
        }
        void Brew(RealmEngine realm, string id)
        {
            var station = data.Npcs.Where(x => x.Zone == OpeningJourney.Home && x.Station == data.Recipe(OpeningJourney.Recipe).Station)
                .OrderBy(x => x.Id, StringComparer.Ordinal).First();
            Place(realm, id, station.Zone, station.Position);
            Act(realm, id, Cmd(realm, id, "craft", item: OpeningJourney.Recipe));
        }
        void Invariants(RealmEngine realm) => Need(Items.Validate(realm.State, data).Count == 0, "Opening violated persistent inventory identities or equipment invariants.");

        Test("all starting classes complete fight, guaranteed upgrade, equip, useful craft and return", () =>
        {
            foreach (var cls in data.Classes)
            {
                Console.WriteLine("OPENING CLASS: " + cls.Id);
                var (realm, id) = Fresh(cls.Id); Accept(realm, id); realm = Restart(realm, id);
                Fight(realm, id); realm = Restart(realm, id);
                Need(realm.Player(id).Quests[OpeningJourney.FightQuest].Complete, "Fight quest is not authoritatively ready.");
                var claim = Claim(realm, id); var p = realm.Player(id); string rewardId = OpeningJourney.RewardId(p);
                var reward = Items.Owned(p, rewardId);
                Need(reward.Template == OpeningJourney.RewardTemplate(cls.Id) && data.Item(reward.Template).Skill == data.Item(cls.Weapon).Skill && data.Item(reward.Template).Tags.Contains("opening_reward") && reward.Rarity == Rarity.Rare && reward.Sockets == 1,
                    cls.Id + ": mandatory reward changed class type, quality or rune socket.");
                Need(p.Quests.ContainsKey(OpeningJourney.CraftQuest), "The next step was not accepted as part of the atomic reward transaction.");
                foreach (var ingredient in data.Recipe(OpeningJourney.Recipe).Ingredients)
                    Need(Items.Count(p, ingredient.Key) >= ingredient.Value, "Mandatory crafting ingredients were not supplied.");
                string beforeReplay = Json(p); string lootBefore = Json(realm.Loot);
                Act(realm, id, claim);
                Need(Json(realm.Player(id)) == beforeReplay && Json(realm.Loot) == lootBefore, "Replaying Claim duplicated rewards or changed state.");
                realm = Restart(realm, id); Act(realm, id, claim);
                Need(Json(realm.Player(id)) == beforeReplay, "Persisted Claim receipt replay changed the reward.");
                var unchangedStarter = realm.Player(id).Equipment["weapon"];
                Act(realm, id, Cmd(realm, id, "equip", item: unchangedStarter));
                Need(!OpeningJourney.Equipped(realm.Player(id)), "Re-equipping the unchanged starter counted as a meaningful upgrade.");
                var beforePower = CombatMath.Stats(realm.Player(id), data);
                Act(realm, id, Cmd(realm, id, "equip", item: rewardId));
                var afterPower = CombatMath.Stats(realm.Player(id), data);
                Need(afterPower.Physical > beforePower.Physical && afterPower.Spell > beforePower.Spell,
                    cls.Id + ": guaranteed reward did not improve physical and class spell power.");
                Need(OpeningJourney.Equipped(realm.Player(id)), "Authoritative Equip did not complete the objective.");
                realm = Restart(realm, id);
                int potions = Items.Count(realm.Player(id), "healing_potion"); Brew(realm, id);
                Need(Items.Count(realm.Player(id), "healing_potion") == potions + 2, "Crafted medicine was not delivered or was consumed as a quest hand-in.");
                Need(realm.Player(id).Quests[OpeningJourney.CraftQuest].Complete, "Equip plus real crafting did not complete the continuation.");
                realm = Restart(realm, id); AtGiver(realm, id);
                var finish = Cmd(realm, id, "claim_quest", item: OpeningJourney.CraftQuest); Act(realm, id, finish);
                Need(OpeningJourney.Finished(realm.Player(id)), "Returning to the NPC did not finish the opening.");
                Need(OpeningJourney.Recommend(data, realm.Snapshot(id)) is null, "Completed opening traps the player in guided mode.");
                string final = Json(realm.Player(id)); realm = Restart(realm, id); Act(realm, id, finish);
                Need(final == Json(realm.Player(id)), "Final acknowledgement replay changed rewards or progression.");
                Invariants(realm); completedClasses++;
            }
            Need(completedClasses == data.Classes.Count && completedClasses > 0, "Not all supported starting classes were exercised.");
        });

        Test("full inventory rolls back the complete claim and remains recoverable through a real merchant", () =>
        {
            var (realm, id) = Fresh(); Accept(realm, id); Fight(realm, id); AtGiver(realm, id);
            // Storage-capacity setup only; no kills, quest completion or reward is injected.
            var fillers = new List<string>();
            while (realm.Player(id).Inventory.Count < Items.InventoryCapacity)
            {
                var item = Items.Create(data, "copper_pickaxe"); fillers.Add(item.Id); Items.Add(realm.Player(id).Inventory, item, data);
            }
            string before = Json(realm.State);
            var failure = realm.Execute(id, Cmd(realm, id, "claim_quest", item: OpeningJourney.FightQuest));
            Need(!failure.Ok && failure.Message.Contains("backpack", StringComparison.OrdinalIgnoreCase), "Full inventory did not explain how to recover the claim.");
            Need(before == Json(realm.State) && OpeningJourney.RewardId(realm.Player(id)) == "", "Failed claim consumed gold, materials, identity or progression.");
            var merchant = data.Npcs.First(x => x.Zone == OpeningJourney.Home && x.Role == "provisioner");
            Place(realm, id, merchant.Zone, merchant.Position);
            foreach (var item in fillers.Take(3)) Act(realm, id, Cmd(realm, id, "sell", merchant.Id, item));
            realm = Restart(realm, id); Claim(realm, id);
            string claimed = Json(realm.Player(id));
            var repeated = realm.Execute(id, Cmd(realm, id, "claim_quest", item: OpeningJourney.FightQuest));
            Need(!repeated.Ok && claimed == Json(realm.Player(id)), "A new request id claimed a second reward.");
            Invariants(realm);
        });

        Test("pending reward cannot be sold; sale resumes after real equipment completion", () =>
        {
            var (realm, id) = Fresh(); Accept(realm, id); Fight(realm, id); Claim(realm, id);
            string reward = OpeningJourney.RewardId(realm.Player(id));
            var merchant = data.Npcs.First(x => x.Zone == OpeningJourney.Home && x.Role == "provisioner");
            Place(realm, id, merchant.Zone, merchant.Position);
            string before = Json(realm.State);
            Need(!realm.Execute(id, Cmd(realm, id, "sell", merchant.Id, reward)).Ok, "Pending guaranteed reward could be sold before the equip lesson.");
            Need(before == Json(realm.State), "Rejected pending-reward sale changed gold, item ownership or progress.");
            Act(realm, id, Cmd(realm, id, "equip", item: reward));
            Act(realm, id, Cmd(realm, id, "unequip", arg: "weapon"));
            Act(realm, id, Cmd(realm, id, "sell", merchant.Id, reward));
            Need(OpeningJourney.Equipped(realm.Player(id)) && !realm.Player(id).Inventory.Any(x => x.Id == reward),
                "Completed equip lesson was reset by a normal later sale.");
            Advance(realm,3); // Respect the prior class technique cooldown before the recovery fixture.
            var hostile = realm.State.Creatures.Values.Where(x => x.Owner == "" && x.Health > 0
                && data.Mob(x.Template).Level >= 10 && !data.Mob(x.Template).Boss)
                .OrderBy(x => data.Mob(x.Template).Level).ThenBy(x => x.Id,StringComparer.Ordinal).First();
            Place(realm,id,hostile.Zone,hostile.Position);
            Act(realm,id,Cmd(realm,id,"cast",hostile.Id,OpeningJourney.StarterTechnique(data,realm.Player(id))!.Id));
            for (int second=0; realm.Player(id).Health>0 && second<180; second++)
            {
                Place(realm,id,hostile.Zone,hostile.Position); Advance(realm,1);
            }
            Need(realm.Player(id).Health<=0,"Real incoming damage did not exercise the death recovery path.");
            Need(NewPlayerJourney.Recommend(data,realm.Snapshot(id)).Stage=="recovery","Death did not take priority over opening guidance.");
            realm=Restart(realm,id);
            Advance(realm,Math.Max(0,realm.Player(id).DeadUntil-realm.State.Time)+.2);
            Act(realm,id,Cmd(realm,id,"respawn"));
            Need(realm.Player(id).Health>0 && realm.Player(id).Zone==OpeningJourney.Home
                && OpeningJourney.Equipped(realm.Player(id)) && realm.Player(id).CompletedQuests.Contains(OpeningJourney.FightQuest),
                "Real respawn lost opening progress or failed to return the character safely.");
            Brew(realm, id); Invariants(realm);
        });

        Test("genuine actions out of order are retained without granting early or duplicate rewards", () =>
        {
            var (realm, id) = Fresh();
            // Supply setup for an intentionally early craft; output still comes from the real recipe transaction.
            foreach (var ingredient in data.Recipe(OpeningJourney.Recipe).Ingredients)
                Items.Add(realm.Player(id).Inventory, Items.Create(data, ingredient.Key, ingredient.Value), data);
            Brew(realm, id); Fight(realm, id);
            Need(OpeningJourney.Crafted(realm.Player(id)) && OpeningJourney.RewardId(realm.Player(id)) == "", "Out-of-order actions granted a reward early or lost actual crafting.");
            Accept(realm, id); Need(realm.Player(id).Quests[OpeningJourney.FightQuest].Complete, "Pre-acceptance real starter kills were discarded.");
            Claim(realm, id); realm = Restart(realm, id);
            Act(realm, id, Cmd(realm, id, "equip", item: OpeningJourney.RewardId(realm.Player(id))));
            Need(realm.Player(id).Quests[OpeningJourney.CraftQuest].Complete, "Crafting had to be repeated despite a real earlier success.");
            Invariants(realm);
        });

        Test("historical characters are not enrolled and cannot request opening rewards", () =>
        {
            var (realm, id) = Fresh();
            // A copied legacy-save shape, not an in-game opt-out command.
            realm.Player(id).Discoveries.Remove(OpeningJourney.EligibleKey);
            realm.Player(id).Discoveries.Add(FirstHourExperience.Key("combat"));
            realm = Restart(realm, id); AtGiver(realm, id);
            string before = Json(realm.State);
            Need(OpeningJourney.Recommend(data, realm.Snapshot(id)) is null, "Historical save was forced into the replacement opening.");
            Need(!NewPlayerJourney.Available(realm.Player(id), data.Quest(OpeningJourney.FightQuest), realm.State.Time), "New opening quest is offered to a historical character.");
            Need(!realm.Execute(id, Cmd(realm, id, "accept_quest", item: OpeningJourney.FightQuest)).Ok, "Historical character can request the fresh-character reward path.");
            Need(before == Json(realm.State), "Rejecting a historical character changed their save.");
        });

        Console.WriteLine($"OPENING_JOURNEY_CHECKS: {passed}/{passed + failures.Count} groups; classes={completedClasses}/{data.Classes.Count}. Isolated real-command fixtures; no human pacing or native-input approval.");
        if (failures.Count > 0) throw new InvalidOperationException("Opening regression failures: " + string.Join(" | ", failures));
    }
}
