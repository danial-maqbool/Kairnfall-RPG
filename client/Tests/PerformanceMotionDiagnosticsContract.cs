using Godot;
using Kairnfall.Core;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

public sealed record DiagnosticsOverheadResult(
    int Iterations,
    double DisabledNanosecondsPerIteration,
    double EnabledNanosecondsPerIteration,
    double AddedNanosecondsPerIteration);

public sealed record MotionScheduleResult(
    string Scenario,
    int RenderFps,
    int Frames,
    int DeliveredSamples,
    double P95ErrorTiles,
    double MaxErrorTiles,
    double MaxForwardLeadTiles,
    int UnexpectedReversals,
    double FinalErrorTiles);

/// <summary>
/// Native bounded diagnostics plus deterministic motion schedules. Timing results
/// are evidence for this environment only; CI timing is never treated as Windows GPU performance.
/// </summary>
public partial class PerformanceMotionDiagnosticsContract : Node
{
    private int checks;

    private void Require([DoesNotReturnIf(false)] bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++;
        GD.Print("PASS PERFORMANCE: " + message);
    }

    private async Task Frame()
        => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);

    private async Task RunForSeconds(double seconds, Action<double>? tick = null)
    {
        double started = Time.GetTicksMsec() / 1000.0;
        double now;
        do
        {
            await Frame();
            now = Time.GetTicksMsec() / 1000.0;
            tick?.Invoke(now - started);
        }
        while (now - started < seconds);
    }

    private static object? Call(GameRoot game, string method, params object?[] args)
        => typeof(GameRoot).GetMethod(method, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);

    private static string RendererLabel()
        => ProjectSettings.GetSetting("rendering/renderer/rendering_method", "unknown").AsString()
           + " / " + OS.GetName();

    private static Snapshot BaseSnapshot(Character self, double time = 100)
        => new()
        {
            Time = time,
            Revision = 1,
            Self = Wire.Copy(self)
        };

    private static List<Point> NearbyFit(ZoneDef zone, Point origin, int required)
    {
        var result = new List<Point>();
        for (int radius = 1; radius <= 12 && result.Count < required; radius++)
        {
            for (int y = -radius; y <= radius && result.Count < required; y++)
            for (int x = -radius; x <= radius && result.Count < required; x++)
            {
                if (Math.Abs(x) != radius && Math.Abs(y) != radius) continue;
                var point = origin.Add(new Point(x * .55, y * .55));
                if (point.Distance(origin) < .4 || !WorldMap.Fits(zone, point)) continue;
                result.Add(point);
            }
        }
        return result;
    }

    private static Snapshot DenseSnapshot(Catalog data, Character self)
    {
        var snapshot = BaseSnapshot(self, 120);
        var zone = data.Zone(self.Zone);
        var positions = NearbyFit(zone, self.Position, 56);
        string mobTemplate = data.Mobs.First(x => !x.Boss).Id;
        var equipment = PixelAssets.VisibleEquipment(self);

        for (int i = 0; i < Math.Min(30, positions.Count); i++)
        {
            var at = positions[i];
            snapshot.Creatures.Add(new Creature
            {
                Id = "perf-mob-" + i,
                Template = mobTemplate,
                Zone = self.Zone,
                Position = at,
                Home = at,
                Facing = at.Direction(self.Position),
                Health = 50
            });
        }

        for (int i = 30; i < Math.Min(48, positions.Count); i++)
        {
            var at = positions[i];
            snapshot.Players.Add(new PublicPlayer
            {
                Id = "perf-player-" + i,
                Name = "Traveler " + i,
                Class = self.Class,
                Appearance = self.Appearance,
                Position = at,
                Facing = at.Direction(self.Position),
                Health = 100,
                MaxHealth = 100,
                Level = 10,
                Equipment = equipment.ToDictionary(x => x.Key, x => x.Value)
            });
        }
        return snapshot;
    }

    private static Snapshot CombatSnapshot(Catalog data, Character self)
    {
        var snapshot = DenseSnapshot(data, self);
        snapshot.Time = 140;
        int count = Math.Min(10, snapshot.Creatures.Count);
        for (int i = 0; i < count; i++)
        {
            var mob = snapshot.Creatures[i];
            snapshot.Telegraphs.Add(new Telegraph
            {
                Id = "perf-telegraph-" + i,
                Skill = "diagnostic",
                Zone = self.Zone,
                Source = mob.Id,
                Position = mob.Position,
                Direction = mob.Position.Direction(self.Position),
                Shape = i % 2 == 0 ? "circle" : "cone",
                Radius = 2.5,
                Resolves = snapshot.Time + .8 + i * .03
            });
        }
        return snapshot;
    }

    private static ClientPerformanceReport Capture(GameRoot game, string scenario)
    {
        var size = game.GetWindow().Size;
        var report = game.Diagnostics.Report(RendererLabel(), size.X, size.Y);
        return report with { Scenario = scenario };
    }

    private async Task<ClientPerformanceReport> RunStationaryCreatureMotionNative(GameRoot game, Snapshot snapshot)
    {
        game.Diagnostics.Reset("stationary-player-moving-creatures");
        double nextPacket = 0;
        int packets = 0;
        await RunForSeconds(1.35, elapsed =>
        {
            if (elapsed + 1e-6 < nextPacket) return;
            snapshot.Time += .1;
            snapshot.Revision++;
            int index = 0;
            foreach (var creature in snapshot.Creatures.Take(12))
            {
                double phase = snapshot.Time * 2.2 + index++ * .31;
                creature.Position = creature.Home.Add(new Point(Math.Sin(phase) * .42, Math.Cos(phase) * .18));
            }
            game.World.Accept(new TransportPacket { Snapshot = Wire.Copy(snapshot) });
            nextPacket += .1;
            packets++;
        });
        Require(packets >= 10, "Stationary-player fixture delivered moving-creature snapshots while self remained fixed");
        return Capture(game, "stationary-player-moving-creatures");
    }

    private async Task<ClientPerformanceReport> RunMotionNative(GameRoot game, Snapshot snapshot)
    {
        game.Diagnostics.Reset("motion-start-stop-reversal");
        var zone = game.Data.Zone(snapshot.Self.Zone);
        Point origin = snapshot.Self.Position;
        double nextPacket = 0;
        int packet = 0;

        await RunForSeconds(2.8, elapsed =>
        {
            if (elapsed + 1e-6 < nextPacket) return;
            double phase = elapsed < .7 ? elapsed / .7
                : elapsed < 1.15 ? 1
                : elapsed < 1.85 ? 1 - (elapsed - 1.15) / .7
                : elapsed < 2.25 ? 0
                : -(elapsed - 2.25) / .55;
            var desired = origin.Add(new Point(phase * 1.8, phase * .7));
            var moved = WorldMap.Move(zone, origin, new Point(desired.X - origin.X, desired.Y - origin.Y));
            snapshot.Time += .1;
            snapshot.Revision++;
            snapshot.Self.Position = moved;
            snapshot.Self.Facing = origin.Direction(moved);
            foreach (var creature in snapshot.Creatures.Take(8))
            {
                double wobble = Math.Sin(snapshot.Time * 2 + creature.Id.GetHashCode() * .01) * .3;
                creature.Position = creature.Home.Add(new Point(wobble, 0));
            }
            game.World.Accept(new TransportPacket { Snapshot = Wire.Copy(snapshot) });
            nextPacket += .1;
            packet++;
        });
        Require(packet >= 20, "Native motion fixture delivered at least twenty 10 Hz-style snapshots");
        return Capture(game, "motion-start-stop-reversal");
    }

    private async Task<ClientPerformanceReport> RunPanelNative(GameRoot game, Snapshot snapshot, string page)
    {
        game.Diagnostics.Reset("panel-" + page.ToLowerInvariant());
        Call(game, "OpenPage", page);
        int updates = 0;
        double next = 0;
        await RunForSeconds(1.25, elapsed =>
        {
            if (elapsed + 1e-6 < next) return;
            snapshot.Time += .1;
            snapshot.Revision++;
            snapshot.Self.Gold += 1;
            game.World.Accept(new TransportPacket { Snapshot = Wire.Copy(snapshot) });
            next += .1;
            updates++;
        });
        Call(game, "ClosePage");
        Require(updates >= 10, page + " panel fixture received continuing snapshots");
        var report = Capture(game, "panel-" + page.ToLowerInvariant());
        Require(report.PhaseMs["PanelStamp"].Count > 0, page + " recorded panel stamp cost");
        Require(report.PhaseMs["PanelRefresh"].Count > 0, page + " recorded panel refresh cost");
        return report;
    }

    private sealed record Delivered(double Delivery, double Authoritative, Point Position);

    private sealed class MotionState
    {
        public Point Position;
        public Point Target;
        public Point Velocity;
        public double LastSnapshotAt;
        public double LastTargetAt;
        public double RenderSpeed;
        public bool Moving;
        public Point PreviousRendered;
        public bool PreviousReady;
    }

    private static MotionScheduleResult Simulate(string scenario, int fps, IReadOnlyList<Delivered> samples)
    {
        double dt = 1.0 / fps;
        var state = new MotionState
        {
            Position = samples[0].Position,
            Target = samples[0].Position,
            LastSnapshotAt = samples[0].Delivery,
            LastTargetAt = samples[0].Delivery
        };
        var errors = new List<double>();
        int index = 1, delivered = 1, reversals = 0, frames = 0;
        double maxLead = 0;
        double end = Math.Max(3.2, samples[^1].Delivery + .8);

        for (double now = 0; now <= end + 1e-9; now += dt)
        {
            Delivered? latest = null;
            while (index < samples.Count && samples[index].Delivery <= now + 1e-9)
            {
                latest = samples[index++];
                delivered++;
            }
            if (latest is { } sample)
            {
                double shift = state.Target.Distance(sample.Position);
                if (shift > MotionPresentationRules.TeleportDistance)
                {
                    state.Velocity = new Point(0, 0);
                    state.LastTargetAt = now;
                }
                else if (shift >= .01)
                {
                    double seconds = now - state.LastTargetAt;
                    state.Velocity = MotionPresentationRules.EstimateVelocity(
                        state.Target, sample.Position, seconds, state.Velocity);
                    state.LastTargetAt = now;
                }
                else
                {
                    double seconds = now - state.LastSnapshotAt;
                    if (seconds > .16)
                        state.Velocity = MotionPresentationRules.EstimateVelocity(
                            state.Target, sample.Position, seconds, state.Velocity);
                }
                state.Target = sample.Position;
                state.LastSnapshotAt = now;
            }

            var previous = state.Position;
            double remaining = previous.Distance(state.Target);
            if (remaining > MotionPresentationRules.TeleportDistance)
            {
                state.Position = state.Target;
                state.Velocity = new Point(0, 0);
                state.RenderSpeed = 0;
                state.Moving = false;
            }
            else
            {
                double age = Math.Max(0, now - state.LastSnapshotAt);
                double sourceSpeed = state.Velocity.Distance(new Point(0, 0))
                    * MotionPresentationRules.SnapshotFreshness(age);
                var visualTarget = MotionPresentationRules.VisualTarget(state.Target, state.Velocity, age);
                double visualRemaining = previous.Distance(visualTarget);
                if (remaining < .006 && sourceSpeed < .06)
                {
                    state.Position = state.Target;
                    state.RenderSpeed = 0;
                    state.Moving = false;
                }
                else
                {
                    double weight = MotionPresentationRules.SmoothingWeight(dt);
                    state.Position = visualRemaining < .003 ? visualTarget : new Point(
                        previous.X + (visualTarget.X - previous.X) * weight,
                        previous.Y + (visualTarget.Y - previous.Y) * weight);
                    double travelled = previous.Distance(state.Position);
                    double instantSpeed = travelled / dt;
                    double speedWeight = 1 - Math.Exp(-12 * Math.Min(dt, .1));
                    state.RenderSpeed += (instantSpeed - state.RenderSpeed) * speedWeight;
                    bool keep = state.RenderSpeed > .055 || visualRemaining > .012 || sourceSpeed > .08;
                    bool start = state.RenderSpeed > .12 && (visualRemaining > .012 || sourceSpeed > .12);
                    state.Moving = state.Moving ? keep : start;
                }
            }

            double error = state.Position.Distance(state.Target);
            errors.Add(error);
            double speed = state.Velocity.Distance(new Point(0, 0));
            if (speed > .05)
            {
                double leadX = state.Position.X - state.Target.X;
                double leadY = state.Position.Y - state.Target.Y;
                double projected = (leadX * state.Velocity.X + leadY * state.Velocity.Y) / speed;
                maxLead = Math.Max(maxLead, projected);
            }
            if (state.PreviousReady)
            {
                double dx = state.Position.X - state.PreviousRendered.X;
                double dy = state.Position.Y - state.PreviousRendered.Y;
                double distance = Math.Sqrt(dx * dx + dy * dy);
                if (distance > .0005 && speed > .05)
                {
                    double cosine = (dx * state.Velocity.X + dy * state.Velocity.Y) / (distance * speed);
                    if (cosine < -.25) reversals++;
                }
            }
            state.PreviousRendered = state.Position;
            state.PreviousReady = true;
            frames++;
        }

        var sorted = errors.Order().ToArray();
        double p95 = sorted[Math.Clamp((int)Math.Ceiling(sorted.Length * .95) - 1, 0, sorted.Length - 1)];
        return new MotionScheduleResult(
            scenario,
            fps,
            frames,
            delivered,
            p95,
            errors.Max(),
            maxLead,
            reversals,
            errors[^1]);
    }

    private static IReadOnlyList<Delivered> Schedule(string kind)
    {
        var list = new List<Delivered> { new(0, 0, new Point(10, 10)) };
        double delivery = 0;
        for (int i = 1; i <= 28; i++)
        {
            double authoritative = i * .1;
            delivery += kind switch
            {
                "irregular" => i % 5 switch { 0 => .18, 1 => .04, 2 => .12, 3 => .07, _ => .09 },
                "stall" when i is >= 9 and <= 12 => i == 9 ? .42 : .001,
                "delayed-coalesced" when i % 6 is 0 or 1 => i % 6 == 0 ? .19 : .001,
                _ => .1
            };
            double motionTime = kind == "long-idle-start" ? Math.Max(0, authoritative - 1.2) : authoritative;
            double x;
            if (kind is "continuous-straight" or "continuous-diagonal")
                x = 10 + authoritative * 1.25;
            else
                x = motionTime < .8 ? 10 + motionTime * 2
                    : motionTime < 1.2 ? 11.6
                    : motionTime < 1.8 ? 11.6 - (motionTime - 1.2) * 2
                    : motionTime < 2.2 ? 10.4
                    : 10.4 + (motionTime - 2.2) * 1.5;
            double y = kind == "continuous-diagonal" ? 10 + (x - 10) * .55 : 10;
            if (kind == "interstitial" && i % 2 == 1 && list.Count > 0)
                (x, y) = (list[^1].Position.X, list[^1].Position.Y);
            list.Add(new Delivered(delivery, authoritative, new Point(x, y)));
            if (kind == "duplicates" && i is 6 or 15)
                list.Add(new Delivered(delivery + .002, authoritative, new Point(x, y)));
        }
        return list;
    }

    private static DiagnosticsOverheadResult DiagnosticsOverhead()
    {
        const int iterations = 200_000;
        static void Exercise(ClientPerformanceDiagnostics diagnostics)
        {
            long started = diagnostics.StartTimer();
            diagnostics.RecordFrame(1.0 / 60, .05);
            diagnostics.RecordDuration(ClientPerfPhase.MotionAdvance, started);
            diagnostics.RecordMotion(.01, .03, 0, 12);
            diagnostics.BeginDrawFrame();
            diagnostics.RecordDrawCall(24);
            diagnostics.RecordScene(12, 30);
        }

        var disabled = new ClientPerformanceDiagnostics(false);
        var enabled = new ClientPerformanceDiagnostics(true);
        for (int i = 0; i < 5000; i++) { Exercise(disabled); Exercise(enabled); }

        var watch = Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++) Exercise(disabled);
        watch.Stop();
        double disabledNs = watch.Elapsed.TotalNanoseconds / iterations;

        watch.Restart();
        for (int i = 0; i < iterations; i++) Exercise(enabled);
        watch.Stop();
        double enabledNs = watch.Elapsed.TotalNanoseconds / iterations;

        return new DiagnosticsOverheadResult(iterations, disabledNs, enabledNs, Math.Max(0, enabledNs - disabledNs));
    }

    private static List<MotionScheduleResult> SyntheticMatrix()
    {
        string[] scenarios =
        [
            "regular", "continuous-straight", "continuous-diagonal", "long-idle-start",
            "interstitial", "irregular", "duplicates", "delayed-coalesced", "stall"
        ];
        int[] rates = [30, 60, 120, 144];
        return scenarios.SelectMany(s => rates.Select(fps => Simulate(s, fps, Schedule(s)))).ToList();
    }

    public override async void _Ready()
    {
        GameRoot? game = null;
        try
        {
            System.Environment.SetEnvironmentVariable("KAIRNFALL_PERF_DIAGNOSTICS", "1");
            GetWindow().Size = new Vector2I(1280, 720);
            await Frame(); await Frame();

            var data = PixelAssets.LoadCatalog();
            var realm = new RealmEngine(data);
            var self = realm.CreateCharacter("performance-fixture", "Performance Tester", "vanguard", new());
            var snapshot = BaseSnapshot(self);
            var scene = GD.Load<PackedScene>("res://Main.tscn");
            game = scene.Instantiate<GameRoot>();
            AddChild(game);
            await Frame(); await Frame();
            Require(game.Diagnostics.Enabled, "Performance diagnostics are explicitly enabled for the fixture");
            var frontendControl = typeof(GameRoot).GetField("frontend", BindingFlags.Instance | BindingFlags.NonPublic)!
                .GetValue(game) as Control ?? throw new InvalidOperationException("Frontend control unavailable.");
            frontendControl.Hide();

            var reports = new List<ClientPerformanceReport>();

            game.Diagnostics.Reset("cold-first-use");
            game.World.Accept(new TransportPacket { Snapshot = Wire.Copy(snapshot) });
            await RunForSeconds(1.0);
            reports.Add(Capture(game, "cold-first-use"));

            game.Diagnostics.Reset("warm-cache");
            await RunForSeconds(1.0);
            reports.Add(Capture(game, "warm-cache"));

            snapshot = DenseSnapshot(data, self);
            game.Diagnostics.Reset("dense-layered-actors");
            game.World.Accept(new TransportPacket { Snapshot = Wire.Copy(snapshot) });
            await RunForSeconds(1.1);
            reports.Add(Capture(game, "dense-layered-actors"));

            reports.Add(await RunStationaryCreatureMotionNative(game, snapshot));
            reports.Add(await RunMotionNative(game, snapshot));

            snapshot = CombatSnapshot(data, self);
            game.Diagnostics.Reset("combat-telegraphs-labels");
            game.World.Accept(new TransportPacket { Snapshot = Wire.Copy(snapshot) });
            foreach (var mob in snapshot.Creatures.Take(8))
            {
                game.World.CombatNote(mob.Position, "24", Ui.Danger);
                game.World.CombatImpact(mob.Position, 2.4f);
            }
            await RunForSeconds(1.1);
            reports.Add(Capture(game, "combat-telegraphs-labels"));

            reports.Add(await RunPanelNative(game, snapshot, "Inventory"));
            reports.Add(await RunPanelNative(game, snapshot, "Crafting"));
            reports.Add(await RunPanelNative(game, snapshot, "Skills"));

            var outside = Wire.Copy(snapshot);
            var interior = data.Zones.First(z => z.Kind == "interior");
            var inside = Wire.Copy(snapshot);
            inside.Self.Zone = interior.Id;
            inside.Self.Position = interior.Spawn;
            inside.Time += .1;
            game.Diagnostics.Reset("interior-roundtrip");
            game.World.Accept(new TransportPacket { Snapshot = inside });
            await RunForSeconds(.7);
            outside.Time = inside.Time + .1;
            game.World.Accept(new TransportPacket { Snapshot = outside });
            await RunForSeconds(.7);
            reports.Add(Capture(game, "interior-roundtrip"));

            foreach (var report in reports)
            {
                Require(report.FrameIntervalMs.Count > 10, report.Scenario + " collected bounded frame samples");
                Require(report.PhaseMs["WorldDraw"].Count > 0, report.Scenario + " measured world drawing");
                Require(report.PhaseMs["MotionAdvance"].Count > 0, report.Scenario + " measured motion advancement");
            }

            var matrix = SyntheticMatrix();
            var diagnosticsOverhead = DiagnosticsOverhead();
            Require(diagnosticsOverhead.Iterations == 200_000 && double.IsFinite(diagnosticsOverhead.AddedNanosecondsPerIteration),
                "Diagnostics overhead probe completed with bounded in-process sampling");
            Require(matrix.Count == 36, "Synthetic matrix covers nine timing patterns at 30/60/120/144 FPS");
            Require(matrix.All(x => double.IsFinite(x.MaxErrorTiles) && double.IsFinite(x.FinalErrorTiles)),
                "Synthetic matrix remains finite across continuous, long-idle, irregular, duplicate, coalesced and stalled delivery");
            Require(matrix.All(x => x.MaxForwardLeadTiles <= MotionPresentationRules.MaxLeadTiles + .02),
                "Synthetic schedules keep forward visual lead within the configured cap");
            Require(matrix.Where(x => x.Scenario == "stall").All(x => x.FinalErrorTiles < .03),
                "Short stalls decay stale lead and reconverge without persistent error");

            string output = System.Environment.GetEnvironmentVariable("KAIRNFALL_PERF_OUTPUT")
                ?? Path.Combine(Directory.GetCurrentDirectory(), "artifacts", "performance-diagnostics", "report.json");
            Directory.CreateDirectory(Path.GetDirectoryName(output)!);
            var payload = new
            {
                schema = 1,
                revision = System.Environment.GetEnvironmentVariable("GITHUB_SHA") ?? "local",
                platform = OS.GetName(),
                renderer = RendererLabel(),
                window = new { width = GetWindow().Size.X, height = GetWindow().Size.Y },
                warmup = "Two native frames before scene setup; each named scenario resets diagnostics. Cold-first-use intentionally includes first texture loads.",
                profilingOverhead = "Opt-in in-memory Stopwatch/GC sampling; no per-frame console or file writes. This fixture writes one JSON report at completion.",
                diagnosticsOverhead,
                reports,
                syntheticMotion = matrix,
                checks,
                windowsGpuPerformanceApproved = false,
                sixtyFpsApproved = false
            };
            File.WriteAllText(output, JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }) + System.Environment.NewLine);
            GD.Print($"PERFORMANCE_MOTION_DIAGNOSTICS: {checks} checks passed; scenarios={reports.Count}; schedules={matrix.Count}; output={output}");
            await NativeTestLifetime.ReleaseSceneAsync(this, game);
            game = null;
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("PERFORMANCE_MOTION_DIAGNOSTICS: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game))
                await NativeTestLifetime.ReleaseSceneAsync(this, game);
            GetTree().Quit(1);
        }
        finally
        {
            System.Environment.SetEnvironmentVariable("KAIRNFALL_PERF_DIAGNOSTICS", null);
        }
    }
}
