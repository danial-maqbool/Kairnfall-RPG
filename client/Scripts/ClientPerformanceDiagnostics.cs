using System.Diagnostics;
using System.Text.Json;

namespace Kairnfall.Client;

public enum ClientPerfPhase
{
    SnapshotAccept,
    MotionAdvance,
    WorldDraw,
    HudUpdate,
    PanelStamp,
    PanelRefresh,
    ResourceLoad
}

public sealed record PerfMetric(
    int Count,
    double P50,
    double P95,
    double P99,
    double Max);

public sealed record ClientPerformanceReport(
    string Scenario,
    string Renderer,
    int Width,
    int Height,
    bool DiagnosticsEnabled,
    PerfMetric FrameIntervalMs,
    long FramesOver33_3Ms,
    long FramesOver50Ms,
    IReadOnlyDictionary<string, PerfMetric> PhaseMs,
    PerfMetric SnapshotArrivalMs,
    PerfMetric AuthoritativeSampleSpacingMs,
    PerfMetric SnapshotAgeMs,
    long DuplicateAuthoritativeSamples,
    long ReversedAuthoritativeSamples,
    PerfMetric PositionErrorTiles,
    PerfMetric MaxPositionErrorTiles,
    long UnexpectedRenderedReversals,
    PerfMetric VisibleActors,
    PerfMetric VisualRecords,
    PerfMetric DrawCalls,
    PerfMetric ManagedAllocatedBytesPerFrame,
    PerfMetric ManagedHeapBytes,
    int Gen0Collections,
    int Gen1Collections,
    int Gen2Collections,
    long TextureCacheHits,
    long TextureCacheMisses,
    long NegativeTextureCacheHits,
    long SynchronousResourceLoads,
    long MissingResources,
    PerfMetric SynchronousResourceLoadMs,
    long AtlasCacheHits,
    long AtlasCacheMisses,
    string AllocationScope,
    string DrawCountScope);

/// <summary>
/// Opt-in bounded client diagnostics. Recording is in memory only; reports are
/// materialized only when explicitly requested by diagnostics/tests.
/// </summary>
public sealed class ClientPerformanceDiagnostics
{
    private const int Capacity = 4096;

    private sealed class Series
    {
        private readonly double[] values = new double[Capacity];
        private int count;
        private int next;

        public void Add(double value)
        {
            if (!double.IsFinite(value)) return;
            values[next] = value;
            next = (next + 1) % values.Length;
            if (count < values.Length) count++;
        }

        public void Clear()
        {
            count = 0;
            next = 0;
            Array.Clear(values);
        }

        public PerfMetric Summary()
        {
            if (count == 0) return new PerfMetric(0, 0, 0, 0, 0);
            var copy = new double[count];
            int start = count == values.Length ? next : 0;
            for (int i = 0; i < count; i++) copy[i] = values[(start + i) % values.Length];
            Array.Sort(copy);
            double Pick(double q) => copy[Math.Clamp((int)Math.Ceiling(copy.Length * q) - 1, 0, copy.Length - 1)];
            return new PerfMetric(copy.Length, Pick(.50), Pick(.95), Pick(.99), copy[^1]);
        }
    }

    public static ClientPerformanceDiagnostics Disabled { get; } = new(false);

    public bool Enabled { get; }
    public string Scenario { get; private set; } = "";

    private readonly Series frameIntervals = new();
    private readonly Series snapshotArrival = new();
    private readonly Series authoritativeSpacing = new();
    private readonly Series snapshotAge = new();
    private readonly Series positionError = new();
    private readonly Series maxPositionError = new();
    private readonly Series visibleActors = new();
    private readonly Series visualRecords = new();
    private readonly Series drawCalls = new();
    private readonly Series allocatedBytesPerFrame = new();
    private readonly Series managedHeapBytes = new();
    private readonly Series resourceLoadMs = new();
    private readonly Dictionary<ClientPerfPhase, Series> phases = Enum.GetValues<ClientPerfPhase>()
        .ToDictionary(x => x, _ => new Series());

    private long lastSnapshotTicks;
    private double? lastAuthoritativeTime;
    private long lastAllocatedBytes = -1;
    private int frames;
    private long over33;
    private long over50;
    private long duplicateAuthoritative;
    private long reversedAuthoritative;
    private long unexpectedRenderedReversals;
    private long textureHits;
    private long textureMisses;
    private long negativeTextureHits;
    private long resourceLoads;
    private long missingResources;
    private long atlasHits;
    private long atlasMisses;
    private int drawCallsThisFrame;
    private int gen0Start;
    private int gen1Start;
    private int gen2Start;

    public ClientPerformanceDiagnostics(bool enabled)
    {
        Enabled = enabled;
        Reset();
    }

    public static ClientPerformanceDiagnostics FromEnvironment()
        => new(string.Equals(
            Environment.GetEnvironmentVariable("KAIRNFALL_PERF_DIAGNOSTICS"),
            "1",
            StringComparison.Ordinal));

    public long StartTimer() => Enabled ? Stopwatch.GetTimestamp() : 0;

    private static double ElapsedMilliseconds(long started)
        => started == 0 ? 0 : Stopwatch.GetElapsedTime(started).TotalMilliseconds;

    public void Reset(string scenario = "")
    {
        Scenario = scenario;
        frameIntervals.Clear();
        snapshotArrival.Clear();
        authoritativeSpacing.Clear();
        snapshotAge.Clear();
        positionError.Clear();
        maxPositionError.Clear();
        visibleActors.Clear();
        visualRecords.Clear();
        drawCalls.Clear();
        allocatedBytesPerFrame.Clear();
        managedHeapBytes.Clear();
        resourceLoadMs.Clear();
        foreach (var series in phases.Values) series.Clear();
        lastSnapshotTicks = 0;
        lastAuthoritativeTime = null;
        lastAllocatedBytes = Enabled ? GC.GetTotalAllocatedBytes(false) : -1;
        frames = 0;
        over33 = 0;
        over50 = 0;
        duplicateAuthoritative = 0;
        reversedAuthoritative = 0;
        unexpectedRenderedReversals = 0;
        textureHits = textureMisses = negativeTextureHits = 0;
        resourceLoads = missingResources = 0;
        atlasHits = atlasMisses = 0;
        drawCallsThisFrame = 0;
        gen0Start = GC.CollectionCount(0);
        gen1Start = GC.CollectionCount(1);
        gen2Start = GC.CollectionCount(2);
    }

    public void RecordDuration(ClientPerfPhase phase, long started)
    {
        if (!Enabled || started == 0) return;
        phases[phase].Add(ElapsedMilliseconds(started));
    }

    public void RecordFrame(double deltaSeconds, double? snapshotAgeSeconds)
    {
        if (!Enabled || !double.IsFinite(deltaSeconds) || deltaSeconds <= 0) return;
        double ms = deltaSeconds * 1000;
        frameIntervals.Add(ms);
        if (ms > 33.3) over33++;
        if (ms > 50) over50++;
        if (snapshotAgeSeconds is { } age && double.IsFinite(age) && age >= 0)
            snapshotAge.Add(age * 1000);

        long allocated = GC.GetTotalAllocatedBytes(false);
        if (lastAllocatedBytes >= 0 && allocated >= lastAllocatedBytes)
            allocatedBytesPerFrame.Add(allocated - lastAllocatedBytes);
        lastAllocatedBytes = allocated;

        frames++;
        if (frames % 30 == 0) managedHeapBytes.Add(GC.GetTotalMemory(false));
    }

    public void RecordSnapshot(double authoritativeTime)
    {
        if (!Enabled || !double.IsFinite(authoritativeTime)) return;
        long now = Stopwatch.GetTimestamp();
        if (lastSnapshotTicks != 0)
            snapshotArrival.Add(Stopwatch.GetElapsedTime(lastSnapshotTicks, now).TotalMilliseconds);
        lastSnapshotTicks = now;

        if (lastAuthoritativeTime is { } previous)
        {
            double spacing = authoritativeTime - previous;
            authoritativeSpacing.Add(spacing * 1000);
            if (Math.Abs(spacing) < 1e-9) duplicateAuthoritative++;
            else if (spacing < 0) reversedAuthoritative++;
        }
        lastAuthoritativeTime = authoritativeTime;
    }

    public void RecordMotion(double meanErrorTiles, double maxErrorTiles, int reversals, int actorCount)
    {
        if (!Enabled) return;
        if (actorCount > 0)
        {
            positionError.Add(meanErrorTiles);
            maxPositionError.Add(maxErrorTiles);
        }
        if (reversals > 0) unexpectedRenderedReversals += reversals;
    }

    public void BeginDrawFrame()
    {
        if (Enabled) drawCallsThisFrame = 0;
    }

    public void RecordDrawCall(int count = 1)
    {
        if (Enabled && count > 0) drawCallsThisFrame += count;
    }

    public void RecordScene(int actors, int records)
    {
        if (!Enabled) return;
        visibleActors.Add(Math.Max(0, actors));
        visualRecords.Add(Math.Max(0, records));
        drawCalls.Add(Math.Max(0, drawCallsThisFrame));
    }

    public void RecordTextureLookup(bool cacheHit, bool negativeCacheHit, bool loaded, bool missing, long started)
    {
        if (!Enabled) return;
        if (cacheHit) textureHits++;
        else textureMisses++;
        if (negativeCacheHit) negativeTextureHits++;
        if (loaded)
        {
            resourceLoads++;
            resourceLoadMs.Add(ElapsedMilliseconds(started));
            phases[ClientPerfPhase.ResourceLoad].Add(ElapsedMilliseconds(started));
        }
        if (missing) missingResources++;
    }

    public void RecordAtlasLookup(bool cacheHit)
    {
        if (!Enabled) return;
        if (cacheHit) atlasHits++;
        else atlasMisses++;
    }

    public ClientPerformanceReport Report(string renderer, int width, int height)
    {
        var phaseReport = phases.ToDictionary(
            pair => pair.Key.ToString(),
            pair => pair.Value.Summary(),
            StringComparer.Ordinal);
        return new ClientPerformanceReport(
            Scenario,
            renderer,
            width,
            height,
            Enabled,
            frameIntervals.Summary(),
            over33,
            over50,
            phaseReport,
            snapshotArrival.Summary(),
            authoritativeSpacing.Summary(),
            snapshotAge.Summary(),
            duplicateAuthoritative,
            reversedAuthoritative,
            positionError.Summary(),
            maxPositionError.Summary(),
            unexpectedRenderedReversals,
            visibleActors.Summary(),
            visualRecords.Summary(),
            drawCalls.Summary(),
            allocatedBytesPerFrame.Summary(),
            managedHeapBytes.Summary(),
            Math.Max(0, GC.CollectionCount(0) - gen0Start),
            Math.Max(0, GC.CollectionCount(1) - gen1Start),
            Math.Max(0, GC.CollectionCount(2) - gen2Start),
            textureHits,
            textureMisses,
            negativeTextureHits,
            resourceLoads,
            missingResources,
            resourceLoadMs.Summary(),
            atlasHits,
            atlasMisses,
            "GC.GetTotalAllocatedBytes(false) delta between WorldView process frames; process-wide managed allocation, not renderer/GPU allocation.",
            "Instrumented WorldView/PixelAssets texture and sprite submissions only; excludes Godot internal/UI primitive draw calls.");
    }

    public void WriteReport(string path, string renderer, int width, int height)
    {
        var report = Report(renderer, width, height);
        Directory.CreateDirectory(Path.GetDirectoryName(path) ?? ".");
        File.WriteAllText(path, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
    }
}
