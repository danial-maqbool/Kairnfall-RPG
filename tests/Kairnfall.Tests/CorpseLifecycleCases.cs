using System.Text.Json;
using Kairnfall.Core;

public static class CorpseLifecycleCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        CommandResult Send(RealmEngine realm, Character player, string kind, string target, string item = "")
            => realm.Execute(player.Id, new() { Kind = kind, Target = target, Item = item, Sequence = realm.Player(player.Id).LastAction + 1 });
        (RealmEngine Realm, Character Player, Creature Mob, WorldNode Remains) Fixture()
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("corpse-account", "Corpse Fixture", "vanguard", new());
            realm.State.Creatures.Clear();
            var mob = new Creature
            {
                Id = "corpse/field_rat", Template = "field_rat", Zone = player.Zone,
                Home = player.Position, Position = player.Position, Health = 1
            };
            realm.State.Creatures.Add(mob.Id, mob);
            var killed = Send(realm, player, "attack", mob.Id);
            Check(killed.Ok && mob.Health == 0, "The authoritative animal kill fixture failed: " + killed.Message);
            var remains = realm.State.Nodes.Values.Single(x => x.Id == "carcass/" + mob.Id + "/" + mob.Generation);
            Check(remains.ReadyAt == realm.State.Time && remains.Position == mob.Position, "Kill did not retain the remains creation time and position.");
            return (realm, player, mob, remains);
        }
        void Sweep(RealmEngine realm) { for (int i = 0; i < 20; i++) realm.Tick(.1); }
        (RealmEngine Realm, Character Player, string Summon) CompanionFixture()
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("companion-account", "Companion Fixture", "warden", new());
            realm.State.Creatures.Clear();
            return (realm, player, data.Abilities.First(x => x.Class == "warden" && x.Kind == "summon" && x.Requirement == 1).Id);
        }
        string Summon(RealmEngine realm, Character player, string ability)
        {
            realm.State.Time = Math.Max(realm.State.Time, player.Cooldowns.GetValueOrDefault("ability:" + ability)) + 1;
            var result = Send(realm, player, "cast", "", ability);
            Check(result.Ok && player.Pet != "" && realm.State.Creatures[player.Pet].Owner == player.Id,
                "Authoritative companion summon failed: " + result.Message);
            return player.Pet;
        }
        void Die(RealmEngine realm, Character player, string companionId)
        {
            player.Health = 1;
            player.Statuses.Add(new() { Kind = "poison", Element = Element.Poison, Power = 1_000_000, Until = realm.State.Time + 10 });
            Sweep(realm);
            Check(player.Health == 0 && player.Pet == "" && player.DeadUntil > realm.State.Time,
                "Normal damage did not complete the owner's death and return countdown.");
            Check(realm.State.Creatures.TryGetValue(companionId, out var pet) && pet.Owner == player.Id
                && pet.Health == 0 && pet.RespawnAt == double.MaxValue,
                "Companion terminal state was missing or removed before the owner's return countdown.");
        }

        test("Animal remains can still be skinned once before decay without changing combat rewards", () =>
        {
            var (realm, player, mob, remains) = Fixture();
            var resource = data.Resource(remains.Template);
            string lootBefore = Json(realm.Loot), mobBefore = Json(mob);
            int materialsBefore = Items.Count(player, resource.Item);
            long skinningBefore = player.SkillXp[resource.Skill];
            double staminaBefore = player.Stamina;
            realm.State.Time = remains.ReadyAt + LootPile.LifetimeSeconds - 1;
            var harvested = Send(realm, player, "gather", remains.Id);
            Check(harvested.Ok, "Fresh animal remains could not be skinned: " + harvested.Message);
            Check(Items.Count(player, resource.Item) > materialsBefore && player.SkillXp[resource.Skill] > skinningBefore
                && player.Stamina < staminaBefore, "Skinning lost its normal materials, training or stamina cost.");
            Check(!Send(realm, player, "gather", remains.Id).Ok, "The same remains yielded a second harvest.");
            Sweep(realm);
            Check(!realm.State.Nodes.ContainsKey(remains.Id), "Spent remains survived their cleanup sweep.");
            Check(Json(realm.State.Creatures[mob.Id]) == mobBefore, "Remains cleanup changed the retained creature or respawn timer.");
            // Ground loot expires on its existing independent timer after this point.
            Check(lootBefore != "{}" && realm.Loot.Count == 0, "Combat loot did not retain its ordinary independent expiry.");
        });

        test("Untouched animal remains decay globally while ordinary nodes and fresh loot survive", () =>
        {
            var (realm, player, mob, remains) = Fixture();
            string mobBefore = Json(mob), possessionsBefore = Json(player.Inventory), skillsBefore = Json(player.SkillXp);
            var ordinary = realm.State.Nodes.Values.First(x => !x.Id.StartsWith("carcass/", StringComparison.Ordinal));
            string ordinaryBefore = Json(ordinary);
            var freshLoot = new LootPile { Zone = player.Zone, Position = player.Position, Owner = player.Id,
                Items = [Items.Create(data, "river_trout", 2)], Expires = LootPile.LifetimeSeconds + 100 };
            realm.Loot.Add(freshLoot.Id, freshLoot); string freshBefore = Json(freshLoot);
            realm.State.Time = remains.ReadyAt + LootPile.LifetimeSeconds - 5;
            Sweep(realm);
            Check(realm.State.Nodes.ContainsKey(remains.Id), "Untouched remains vanished before their three-minute opportunity ended.");
            realm.MarkSaved(); realm.State.Time = remains.ReadyAt + LootPile.LifetimeSeconds;
            Sweep(realm);
            Check(!realm.State.Nodes.ContainsKey(remains.Id) && realm.EconomicDirty, "Expired remains were retained or their removal was not saved.");
            Check(Json(realm.State.Nodes[ordinary.Id]) == ordinaryBefore && Json(realm.Loot[freshLoot.Id]) == freshBefore,
                "Decay removed or changed an unrelated resource or unexpired ground item.");
            Check(Json(realm.State.Creatures[mob.Id]) == mobBefore && Json(player.Inventory) == possessionsBefore
                && Json(player.SkillXp) == skillsBefore, "Decay changed creature identity, possessions or earned training.");
        });

        test("Saved remains keep their age and expired skinning requests are atomic before cleanup", () =>
        {
            var (realm, player, mob, remains) = Fixture();
            realm.State.Time = remains.ReadyAt + LootPile.LifetimeSeconds - 5;
            var loaded = new RealmEngine(data, Wire.Copy(realm.State)) { Loot = Wire.Copy(realm.Loot) };
            Check(loaded.State.Nodes[remains.Id].ReadyAt == remains.ReadyAt, "Reload reset the age of historical remains.");
            Sweep(loaded); Check(loaded.State.Nodes.ContainsKey(remains.Id), "Reload prematurely removed fresh remains.");
            loaded.State.Time = remains.ReadyAt + LootPile.LifetimeSeconds;
            var savedPlayer = loaded.Player(player.Id);
            string inventoryBefore = Json(savedPlayer.Inventory), skillsBefore = Json(savedPlayer.SkillXp);
            double staminaBefore = savedPlayer.Stamina; long sequenceBefore = savedPlayer.LastAction;
            Check(!Send(loaded, savedPlayer, "gather", remains.Id).Ok, "Expired remains could be harvested before the environment sweep.");
            savedPlayer = loaded.Player(player.Id);
            Check(Json(savedPlayer.Inventory) == inventoryBefore && Json(savedPlayer.SkillXp) == skillsBefore
                && savedPlayer.Stamina == staminaBefore && savedPlayer.LastAction == sequenceBefore,
                "Rejected expired skinning spent possessions, stamina, training or an action sequence.");
            Sweep(loaded); Check(!loaded.State.Nodes.ContainsKey(remains.Id), "Reloaded expired remains survived cleanup.");
            Check(loaded.State.Creatures[mob.Id].Generation == mob.Generation, "Reloaded cleanup changed the creature generation.");
        });

        test("Successive animal generations decay independently without renewing older remains", () =>
        {
            var (realm, player, mob, first) = Fixture();
            realm.State.Time = 30; mob.Health = 1;
            var killed = Send(realm, player, "attack", mob.Id);
            Check(killed.Ok && mob.Generation == 2, "The second authoritative kill fixture failed: " + killed.Message);
            var second = realm.State.Nodes.Values.Single(x => x.Id == "carcass/" + mob.Id + "/2");
            string secondBefore = Json(second), mobBefore = Json(mob);
            int killsBefore = player.Bestiary["field_rat"]; long slayerBefore = player.SkillXp["slayer"];
            realm.State.Time = first.ReadyAt + LootPile.LifetimeSeconds; Sweep(realm);
            Check(!realm.State.Nodes.ContainsKey(first.Id) && Json(realm.State.Nodes[second.Id]) == secondBefore,
                "A later kill renewed old remains or prematurely removed the new generation.");
            realm.State.Time = second.ReadyAt + LootPile.LifetimeSeconds; Sweep(realm);
            Check(!realm.State.Nodes.ContainsKey(second.Id) && Json(realm.State.Creatures[mob.Id]) == mobBefore,
                "Second-generation decay altered the retained mob or left stale remains.");
            Check(player.Bestiary["field_rat"] == killsBefore && player.SkillXp["slayer"] == slayerBefore,
                "Decay changed already-earned kill credit or combat training.");
        });

        test("Repeated owner death and resummoning do not accumulate dead companions or alter possessions", () =>
        {
            var (realm, player, ability) = CompanionFixture();
            var carried = player.Inventory.First(x => x.Template == "healing_potion");
            // Seed an ordinary owned pile through the existing item transfer API.
            // Companion cleanup coverage does not depend on optional drop controls.
            var grounded = Items.Take(player.Inventory, carried.Id, 1, player);
            var pile = new LootPile { Zone = player.Zone, Position = player.Position, Owner = player.Id,
                Items = [grounded], PublicAt = realm.State.Time + 60, Expires = realm.State.Time + LootPile.LifetimeSeconds };
            realm.Loot.Add(pile.Id, pile);
            string groundLootBefore = Json(realm.Loot);
            var retired = new HashSet<string>();
            for (int cycle = 0; cycle < 3; cycle++)
            {
                string companion = Summon(realm, player, ability);
                Check(!retired.Contains(companion) && realm.State.Creatures.Values.Count(x => x.Owner == player.Id) == 1,
                    "Resummoning reused a retired identity or retained a previous dead companion.");
                int deathsBefore = player.Deaths;
                Die(realm, player, companion);
                Check(player.Deaths == deathsBefore + 1, "A single damage death changed the death count more than once.");
                string inventoryBefore = Json(player.Inventory), skillsBefore = Json(player.SkillXp), lootBefore = Json(realm.Loot);
                realm.State.Time = player.DeadUntil; realm.MarkSaved(); Sweep(realm);
                Check(!realm.State.Creatures.ContainsKey(companion) && realm.EconomicDirty,
                    "Finished dead companion remained in the realm or its cleanup was not saved.");
                Check(Json(player.Inventory) == inventoryBefore && Json(player.SkillXp) == skillsBefore && Json(realm.Loot) == lootBefore,
                    "Companion cleanup changed possessions, earned training or ground rewards.");
                retired.Add(companion);
                var returned = Send(realm, player, "respawn", "");
                Check(returned.Ok && player.Health > 0 && player.Pet == "", "Normal authoritative respawn failed: " + returned.Message);
            }
            Check(retired.All(id => !realm.State.Creatures.ContainsKey(id)), "An older dead companion returned after another death cycle.");
            string living = Summon(realm, player, ability); string livingBefore = Json(realm.State.Creatures[living]);
            var loaded = new RealmEngine(data, Wire.Copy(realm.State)) { Loot = Wire.Copy(realm.Loot) };
            Sweep(loaded);
            Check(loaded.Player(player.Id).Pet == living && Json(loaded.State.Creatures[living]) == livingBefore,
                "Reload or cleanup changed the current living companion.");
            Check(retired.All(id => !loaded.State.Creatures.ContainsKey(id)), "Reload recreated a retired summoned companion.");
            Check(Json(loaded.Loot) == groundLootBefore, "Repeated companion death or reload changed the reserved ground item.");
            Check(PersistenceIntegrity.Validate(loaded).Count == 0, "Companion lifecycle produced an invalid persisted realm.");
        });

        test("Reload removes only finished orphan companions while retaining tamed and pending death states", () =>
        {
            var (realm, player, ability) = CompanionFixture();
            string dead = Summon(realm, player, ability); Die(realm, player, dead);
            var tamer = realm.CreateCharacter("companion-tamer", "Tame Holder", "warden", new());
            var animal = data.Mob("field_rat");
            var tamed = new Creature { Id = "companion/tamed_rat", Template = animal.Id, Zone = tamer.Zone,
                Position = tamer.Position, Home = tamer.Position, Health = animal.Health * .4 };
            realm.State.Creatures.Add(tamed.Id, tamed); Items.Add(tamer.Inventory, Items.Create(data, "animal_bait"), data);
            var taming = Send(realm, tamer, "tame", tamed.Id);
            Check(taming.Ok && tamer.Pet == tamed.Id && tamed.Owner == tamer.Id, "Authoritative taming fixture failed: " + taming.Message);
            var pending = new Creature { Id = "companion/pending_death", Template = animal.Id, Zone = player.Zone,
                Position = player.Position, Home = player.Position, Owner = player.Id, Health = 0, RespawnAt = realm.State.Time + 60 };
            realm.State.Creatures.Add(pending.Id, pending);
            var keeper = realm.CreateCharacter("companion-keeper", "Death State Keeper", "warden", new());
            var referenced = new Creature { Id = "companion/referenced_death", Template = animal.Id, Zone = keeper.Zone,
                Position = keeper.Position, Home = keeper.Position, Owner = keeper.Id, Health = 0, RespawnAt = double.MaxValue };
            realm.State.Creatures.Add(referenced.Id, referenced); keeper.Pet = referenced.Id;
            string tamedBefore = Json(tamed), pendingBefore = Json(pending), referencedBefore = Json(referenced);
            string tamerInventory = Json(tamer.Inventory), ownerInventory = Json(player.Inventory), ownerSkills = Json(player.SkillXp);
            var loaded = new RealmEngine(data, Wire.Copy(realm.State)) { Loot = Wire.Copy(realm.Loot) };
            Check(loaded.State.Creatures.ContainsKey(dead), "Reload removed a companion during its owner's unfinished return countdown.");
            loaded.State.Time = loaded.Player(player.Id).DeadUntil; Sweep(loaded);
            Check(!loaded.State.Creatures.ContainsKey(dead), "Reloaded terminal orphan remained after its owner's return countdown.");
            Check(Json(loaded.State.Creatures[tamed.Id]) == tamedBefore && loaded.Player(tamer.Id).Pet == tamed.Id,
                "Cleanup altered a living tamed companion or its saved ownership.");
            Check(Json(loaded.State.Creatures[pending.Id]) == pendingBefore && Json(loaded.State.Creatures[referenced.Id]) == referencedBefore
                && loaded.Player(keeper.Id).Pet == referenced.Id, "Cleanup removed a finite pending death or a still-referenced companion.");
            Check(Json(loaded.Player(tamer.Id).Inventory) == tamerInventory && Json(loaded.Player(player.Id).Inventory) == ownerInventory
                && Json(loaded.Player(player.Id).SkillXp) == ownerSkills, "Reloaded companion cleanup changed materials, equipment or earned training.");
            Check(PersistenceIntegrity.Validate(loaded).Count == 0, "Reloaded companion cleanup broke saved ownership integrity.");
        });
    }
}
