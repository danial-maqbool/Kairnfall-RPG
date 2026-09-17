using System.Text.Json;
using Kairnfall.Core;

int checks = 0;
void Need(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
    checks++; Console.WriteLine("PASS CHARACTER: " + message);
}
try
{
    var data = JsonSerializer.Deserialize<Catalog>(File.ReadAllText(args.FirstOrDefault() ?? "content/catalog.json"), Wire.Json)
        ?? throw new InvalidDataException("Missing catalogue.");
    for (int state = 2; state <= 10; state++)
    {
        if (!ActorMotion.IsAction(state)) continue;
        int previous = 0;
        for (int tick = 0; tick <= 120; tick++)
        {
            int frame = ActorMotion.ActionFrame(state, tick / 100.0, .8);
            Need(frame is >= 0 and < 8 && frame >= previous, $"State {state}, tick {tick}: monotonic bounded frame");
            previous = frame;
        }
        Need(previous == 7, "One-shot pose reaches its final frame: " + state);
    }
    Need(ActorMotion.ActionFrame(2, double.NaN, .6) == 0, "Non-finite time cannot index an atlas");
    Need(ActorMotion.ActionFrame(2, -.2, .6) == 0, "A future cue cannot skip anticipation");
    Need(ActorMotion.ActionFrame(5, .7, 6) == 7, "Corpse retention does not stretch the collapse");
    double whole = ActorMotion.AdvanceWalk(0, 1.2), split = 0;
    for (int i = 0; i < 120; i++) split = ActorMotion.AdvanceWalk(split, .01);
    Need(Math.Abs(whole - split) < 1e-8, "Gait phase depends on distance, not packet subdivision");
    Need(ActorMotion.AdvanceWalk(3, 7) == 0, "A teleport resets the stride");
    Need(ActorMotion.AdvanceWalk(3, 0) == 3, "Stationary actors do not march in place");
    Need(!ActorMotion.MayInterrupt(5, 6, false), "An interaction never interrupts a corpse");
    Need(!ActorMotion.MayInterrupt(4, 2, true), "Hit reaction is not erased by the same packet's attack cue");
    Need(ActorMotion.MayInterrupt(2, 4, true), "Confirmed damage can interrupt an attack");
    Need(ActorMotion.MayInterrupt(4, 5, false), "Confirmed death has highest priority");
    var oldSnapshot = JsonSerializer.Deserialize<Snapshot>("{\"time\":1,\"self\":{}}", Wire.Json)!;
    Need(oldSnapshot.ActorCues.Count == 0, "Historical snapshots without presentation data remain valid");

    var realm = new RealmEngine(data);
    var actor = realm.CreateCharacter("character-probe-a", "Motion Actor", "vanguard", new());
    var observer = realm.CreateCharacter("character-probe-b", "Motion Observer", "vanguard", new());
    string actorId = actor.Id, observerId = observer.Id;
    realm.Active.Add(actorId); realm.Active.Add(observerId);
    var npc = data.Npcs.First(n => n.Zone == "wayfarers_rest" && n.Role == "innkeeper");
    var zone = data.Zone(npc.Zone);
    actor.Position = WorldMap.FindFree(zone, npc.Position);
    observer.Position = actor.Position;
    Need(realm.Snapshot(actorId).ActorCues.Count == 0, "Spawn creates no phantom attack");
    var command = new GameCommand { Kind = "talk", Target = npc.Id, Sequence = actor.LastAction + 1 };
    var accepted = realm.Execute(actorId, command);
    Need(accepted.Ok, "An ordinary authoritative talk command succeeds: " + accepted.Message);
    var local = realm.Snapshot(actorId).ActorCues.Single(c => c.Actor == actorId);
    var remote = realm.Snapshot(observerId).ActorCues.Single(c => c.Actor == actorId);
    Need(local.State == 6 && remote.State == 6 && local.Sequence == command.Sequence,
        "The same accepted interaction is visible to self and a nearby player");
    Need(remote.Npc == npc.Id && remote.Facing.Finite, "NPC acknowledgement uses a validated public target");
    double started = remote.Started;
    remote.Actor = "modified-copy";
    Need(realm.Snapshot(observerId).ActorCues.Any(c => c.Actor == actorId), "Snapshot cues are detached copies");
    realm.State.Time += .1;
    var replay = realm.Execute(actorId, command);
    Need(replay.Ok && realm.Snapshot(observerId).ActorCues.Single(c => c.Actor == actorId).Started == started,
        "Receipt replay does not restart the animation");
    var rejected = realm.Execute(actorId, new GameCommand { Kind = "attack", Target = "missing", Sequence = command.Sequence + 1 });
    Need(!rejected.Ok, "Invalid combat intent is rejected");
    Need(realm.Snapshot(observerId).ActorCues.Single(c => c.Actor == actorId).Sequence == command.Sequence,
        "Rejected intent cannot create an action cue");
    actor = realm.Player(actorId); observer = realm.Player(observerId);
    observer.Position = actor.Position.Add(new Point(5, 0));
    actor.Statuses.Add(new StatusEffect { Kind = "stealth", Until = realm.State.Time + 10, Power = 1, Source = actorId });
    var hidden = realm.Snapshot(observerId);
    Need(hidden.Players.All(p => p.Id != actorId) && hidden.ActorCues.All(c => c.Actor != actorId),
        "Animation cues do not reveal a stealthed actor");
    actor.Statuses.Clear(); observer.Position = actor.Position.Add(new Point(80, 0));
    Need(realm.Snapshot(observerId).ActorCues.All(c => c.Actor != actorId), "Out-of-range actors have no cue side channel");
    observer.Position = actor.Position;
    actor.Zone = data.Zones.First(z => z.Id != observer.Zone).Id;
    actor.Position = data.Zone(actor.Zone).Spawn;
    Need(realm.Snapshot(actorId).ActorCues.Count == 0, "Zone travel does not replay an old-region action");
    string saved = JsonSerializer.Serialize(realm.State, Wire.Json);
    Need(!saved.Contains("actorCues", StringComparison.OrdinalIgnoreCase), "Ephemeral cues do not change the save schema");
    var restored = new RealmEngine(data, Wire.Copy(realm.State));
    restored.Active.Add(observerId);
    Need(restored.Snapshot(observerId).ActorCues.Count == 0, "Restart cannot replay a persisted animation");
    realm.State.Time += 3;
    Need(realm.Snapshot(observerId).ActorCues.Count == 0, "Expired cues are evicted");
    var invalid = new ActorPresentationCue { Actor = actorId, Sequence = 1, State = 6, Started = 0, Duration = double.NaN, Facing = new(1, 0) };
    Need(!ActorMotion.CueIsCurrent(invalid, .1), "Malformed durations cannot poison a presentation clock");
    invalid.Duration = .8; invalid.Facing = new(double.PositiveInfinity, 0);
    Need(!ActorMotion.CueIsCurrent(invalid, .1), "Non-finite presentation vectors are ignored");
    Console.WriteLine($"CHARACTER_PRESENTATION_PROBE: {checks} checks passed; accepted-action authority, replay, privacy, save compatibility, clocks and priority.");
    return 0;
}
catch (Exception error)
{
    Console.Error.WriteLine("CHARACTER_PRESENTATION_FAILED: " + error);
    return 1;
}
