using Kairnfall.Core;

public static class GridMovementCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        (RealmEngine Realm, Character Player) Fixture()
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("grid-account", "Grid Fixture", "vanguard", new());
            realm.Active.Add(player.Id); realm.State.Creatures.Clear();
            player.Position = WorldMap.FindFree(data.Zone(player.Zone), player.Position);
            return (realm, player);
        }
        void Move(RealmEngine realm, Character player, double x, double y, string arg = GridMovementRules.Intent)
            => Check(realm.Execute(player.Id, new() { Kind = "move", X = x, Y = y, Arg = arg }).Ok, "Movement rejected.");
        void Advance(RealmEngine realm, int count = 30) { for (int i = 0; i < count; i++) realm.Tick(.05); }
        test("Classic tap completes exactly one server-owned tile", () =>
        {
            var (realm, player) = Fixture(); var start = player.Position; long sequence = player.LastAction;
            Move(realm, player, 1, 0); realm.Tick(.05); Move(realm, player, 0, 0); Advance(realm);
            Check(player.Position == start.Add(new Point(1, 0)), "A released tap overshot or stopped between tiles.");
            Check(player.LastAction == sequence, "Movement consumed an action receipt.");
        });
        test("Classic route step stops at one tile without a release packet", () =>
        {
            var (realm, player) = Fixture(); var start = player.Position;
            Move(realm, player, 1, 0, GridMovementRules.Step); Advance(realm, 100);
            Check(player.Position == start.Add(new Point(1, 0)), "A delayed frame repeated a route step.");
            Move(realm, player, 0, 1, GridMovementRules.Step); Advance(realm, 100);
            Check(player.Position == start.Add(new Point(1, 1)), "A route corner overshot its authoritative tile.");
        });
        test("Classic holding turns only at tile boundaries and keeps ordinary speed", () =>
        {
            var (realm, player) = Fixture(); var start = player.Position; bool turned = false;
            for (int i = 0; i < 30; i++)
            {
                Move(realm, player, i < 2 ? 1 : 0, i < 2 ? 0 : 1);
                var before = player.Position; realm.Tick(.05);
                Check(player.Position.Distance(before) <= CombatMath.Stats(player, data).MoveSpeed * .05 + .000001, "Grid movement sped up the character.");
                if (player.Position.Y > start.Y + .000001)
                { turned = true; Check(Math.Abs(player.Position.X - start.X - 1) < .000001, "Turn cut across a tile."); }
                Check(WorldMap.Fits(data.Zone(player.Zone), player.Position), "Holding crossed a wall.");
            }
            Check(turned, "Holding did not continue onto the next tile.");
        });
        test("Classic diagonal input chooses one axis and cannot boost movement", () =>
        {
            var (realm, player) = Fixture(); var start = player.Position;
            Move(realm, player, 1, 1); Move(realm, player, 0, 0); Advance(realm);
            Check(player.Position == start.Add(new Point(1, 0)), "Diagonal input did not remain cardinal.");
        });
        test("Classic tile steps respect collision and do not creep into solid tiles", () =>
        {
            var (realm, player) = Fixture(); var zone = data.Zone(player.Zone);
            var start = Enumerable.Range(2, zone.Width - 4).SelectMany(x => Enumerable.Range(2, zone.Height - 4).Select(y => new Point(x + .5, y + .5)))
                .First(p => WorldMap.Fits(zone, p) && !WorldMap.Fits(zone, p.Add(new Point(1, 0))) && !zone.Exits.Any(e => p.Distance(e.Position) < 3));
            player.Position = start;
            for (int i = 0; i < 30; i++) { Move(realm, player, 1, 0); realm.Tick(.05); }
            Check(player.Position == start, "Blocked grid movement crept towards a wall.");
            Check(player.Facing == new Point(1, 0), "Blocked movement did not face the attempted direction.");
        });
        test("Classic cancellation and root prevent queued movement", () =>
        {
            var (realm, player) = Fixture();
            Move(realm, player, 1, 0); realm.Tick(.05); var cancelled = player.Position;
            Move(realm, player, 0, 0, GridMovementRules.Cancel); Advance(realm);
            Check(player.Position == cancelled, "Modal cancellation finished a hidden step.");
            player.Statuses.Add(new() { Kind = "root", Power = 1, Until = realm.State.Time + 4 });
            Move(realm, player, 1, 0); Advance(realm, 60);
            Check(player.Position == cancelled, "Root failed to stop grid movement.");
            Advance(realm, 40); Check(player.Position == cancelled, "Expired grid input moved after root ended.");
        });
        test("Classic legacy positions align through movement and survive save reload unchanged", () =>
        {
            var (realm, player) = Fixture(); player.Position = player.Position.Add(new Point(.15, .08));
            var saved = Wire.Copy(realm.State); var loaded = new RealmEngine(data, saved);
            Check(loaded.Player(player.Id).Position == player.Position, "Loading rounded a valid old saved position.");
            var ids = player.Inventory.Select(x => x.Id).ToArray(); var original = player.Position;
            Move(realm, player, 1, 0); realm.Tick(.05);
            Check(player.Position.Distance(original) <= CombatMath.Stats(player, data).MoveSpeed * .05 + .000001, "Legacy alignment teleported.");
            var halfway = player.Position; var recovered = new RealmEngine(data, Wire.Copy(realm.State));
            Check(recovered.Player(player.Id).Position == halfway, "Saving a partial step changed its valid position.");
            Check(recovered.Player(player.Id).Inventory.Select(x => x.Id).SequenceEqual(ids), "Grid save changed possessions.");
            Move(realm, player, 0, 0); Advance(realm);
            Check(player.Position == new Point(Math.Floor(original.X) + .5, Math.Floor(original.Y) + .5), "Legacy alignment did not stop at its own tile center.");
        });
        test("Classic disconnect and ordinary movement discard pending steps", () =>
        {
            var (realm, player) = Fixture(); var start = player.Position;
            Move(realm, player, 1, 0); realm.Tick(.05); Move(realm, player, 0, 1, ""); realm.Tick(.05);
            Check(player.Position.Y > start.Y, "Legacy continuous movement was changed.");
            Move(realm, player, 1, 0); realm.Disconnect(player.Id); realm.Active.Add(player.Id); var before = player.Position; Advance(realm);
            Check(player.Position == before, "Reconnect restored stale movement input.");
        });
    }
}
