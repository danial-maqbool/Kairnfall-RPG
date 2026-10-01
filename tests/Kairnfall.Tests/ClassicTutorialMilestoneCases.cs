using System.Text.Json;
using Kairnfall.Core;

public static class ClassicTutorialMilestoneCases
{
    public static void Run(Action<string, Action> test, Catalog normal)
    {
        void Check(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
        string Bytes<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        (RealmEngine Realm, Character Player) Fixture()
        {
            var data = Wire.Copy(normal); ClassicTutorialContent.Enable(data);
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter(Guid.NewGuid().ToString("N"), "Food Lesson", "vanguard", new());
            realm.Active.Add(player.Id); return (realm, player);
        }
        GameCommand Consume(Character player, Item item) => new()
            { Kind = "consume", Item = item.Id, Sequence = player.LastAction + 1 };

        test("Successful potions keep their effects without completing the optional food lesson", () =>
        {
            foreach (string effect in new[] { "heal", "mana", "purge" })
            {
                var (realm, player) = Fixture(); var stats = CombatMath.Stats(player, realm.Data);
                var definition = realm.Data.Items.First(item => item.Type == "potion" && item.Effect == effect);
                var item = Items.Create(realm.Data, definition.Id, 2); player.Inventory.Add(item);
                player.Health = stats.Health - 5; player.Mana = stats.Mana - 5;
                player.Statuses.Add(new() { Kind = "poison", Until = 30, Power = 1 });
                double food = player.ClassicTutorial!.Food; long xp = player.SkillXp.GetValueOrDefault(ClassicTutorialContent.Questing);
                long notice = player.ClassicTutorial.NoticeId;
                var result = realm.Execute(player.Id, Consume(player, item));
                player = realm.Player(player.Id);
                Check(result.Ok && player.Inventory.First(x => x.Id == item.Id).Quantity == 1, "The ordinary potion action changed.");
                Check(effect switch { "heal" => player.Health == stats.Health, "mana" => player.Mana == stats.Mana,
                    _ => player.Statuses.All(status => status.Kind != "poison") }, "The potion lost its real effect.");
                Check(player.ClassicTutorial!.Food == food && !player.ClassicTutorial.Completed.Contains("food")
                    && player.SkillXp.GetValueOrDefault(ClassicTutorialContent.Questing) == xp && player.ClassicTutorial.NoticeId == notice,
                    "A potion fabricated the food milestone, Food restoration, notice or Questing reward.");
            }
        });

        test("Real tutorial and ordinary foods credit exactly once through consume replay and save reload", () =>
        {
            foreach (string template in new[] { "classic_berries", "bread" })
            {
                var (realm, player) = Fixture(); var item = Items.Create(realm.Data, template, 2); player.Inventory.Add(item);
                player.ClassicTutorial!.Food = 45;
                long before = player.SkillXp.GetValueOrDefault(ClassicTutorialContent.Questing);
                var command = Consume(player, item); var result = realm.Execute(player.Id, command);
                player = realm.Player(player.Id);
                Check(result.Ok && player.ClassicTutorial!.Completed.Contains("food")
                    && player.ClassicTutorial.Food == 45 + realm.Data.ClassicTutorial!.FoodRestore,
                    "A successful real food action did not teach the food lesson.");
                Check(player.SkillXp.GetValueOrDefault(ClassicTutorialContent.Questing) == before + realm.Data.ClassicTutorial!.MilestoneXp
                    && player.ClassicTutorial!.NoticeId == 1, "Food milestone reward or notice was not credited once.");
                string accepted = Bytes(player);
                Check(realm.Execute(player.Id, command).Ok && Bytes(realm.Player(player.Id)) == accepted,
                    "Replay consumed or rewarded the real food action twice.");
                var loaded = new RealmEngine(realm.Data, Wire.Copy(realm.State));
                Check(Bytes(loaded.Player(player.Id)) == accepted, "Reload altered earned food progress or possessions.");
                loaded.State.Time = 9; player = loaded.Player(player.Id); player.ClassicTutorial!.Food = 45;
                long earned = player.SkillXp.GetValueOrDefault(ClassicTutorialContent.Questing); long notice = player.ClassicTutorial.NoticeId;
                Check(loaded.Execute(player.Id, Consume(player, item)).Ok
                    && loaded.Player(player.Id).SkillXp.GetValueOrDefault(ClassicTutorialContent.Questing) == earned
                    && loaded.Player(player.Id).ClassicTutorial!.NoticeId == notice,
                    "Subsequent food consumption reset or duplicated the earned milestone.");
            }
        });

        test("Rejected food intentions cannot record tutorial progress or consume inventory", () =>
        {
            var (realm, player) = Fixture(); var item = player.Inventory.First(x => x.Template == "classic_berries");
            player.ClassicTutorial!.Food = 100; var stats = CombatMath.Stats(player, realm.Data);
            player.Health = stats.Health; player.Stamina = stats.Stamina;
            string before = Bytes(player);
            Check(!realm.Execute(player.Id, Consume(player, item)).Ok && Bytes(realm.Player(player.Id)) == before,
                "A rejected full-Food intention changed inventory or tutorial progress.");
        });
    }
}
