using System.Diagnostics;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Sockets;
using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Kairnfall.Core;
using Npgsql;

namespace Kairnfall.Probes;

/// <summary>Explicit loopback/PostgreSQL probe. It creates only fresh owned schemas and never converts a retained realm.</summary>
public static class ClassicTutorialLiveProbe
{
    private static readonly string[] Cases = ["startup opt-in gates", "normal saved-mode refusal", "downloaded tutorial catalog",
        "authoritative tutorial actions", "receipt replay", "disconnect and reconnect", "receipt replay after authenticated reconnect",
        "process restart", "durable receipt replay after process restart", "tutorial saved-mode refusal"];
    private static string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
    private static string Hash(string value) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(value))).ToLowerInvariant();
    private static void Require([System.Diagnostics.CodeAnalysis.DoesNotReturnIf(false)] bool value, string message) { if (!value) throw new InvalidOperationException(message); }
    public static NpgsqlConnectionStringBuilder RequireDatabase(string connection, bool permitted)
    {
        NpgsqlConnectionStringBuilder options;
        try { options = new NpgsqlConnectionStringBuilder(connection); }
        catch (ArgumentException) { throw new InvalidOperationException("Disposable database connection settings are malformed."); }
        Require(permitted && options.Database is { } name && name.EndsWith("_test", StringComparison.Ordinal)
            && (options.Host == "localhost" || IPAddress.TryParse(options.Host, out var ip) && IPAddress.IsLoopback(ip)),
            "Optional live probe requires explicit disposable loopback *_test database permission.");
        Require(string.IsNullOrEmpty(options.SearchPath), "Supply the disposable database without a pre-existing Search Path.");
        return options;
    }
    private static string OwnedSchema(string kind, string suffix)
    {
        Require((kind is "normal" or "optional") && suffix.Length == 32 && suffix.All(x => x is >= '0' and <= '9' or >= 'a' and <= 'f'),
            "Only generated optional-probe schema names are permitted.");
        return "classic_probe_" + kind + "_" + suffix;
    }
    private static void SanitizeServerEnvironment(ProcessStartInfo start)
    {
        foreach (string key in start.Environment.Keys.Where(x => x.StartsWith("KAIRNFALL_", StringComparison.OrdinalIgnoreCase)
            || x.StartsWith("ASPNETCORE_", StringComparison.OrdinalIgnoreCase)
            || x.StartsWith("DOTNET_", StringComparison.OrdinalIgnoreCase) && !x.Equals("DOTNET_ROOT", StringComparison.OrdinalIgnoreCase)
                && !x.StartsWith("DOTNET_ROOT_", StringComparison.OrdinalIgnoreCase)
            || x.Equals("Kestrel", StringComparison.OrdinalIgnoreCase) || x.StartsWith("Kestrel__", StringComparison.OrdinalIgnoreCase)
            || x.StartsWith("Kestrel:", StringComparison.OrdinalIgnoreCase)
            || x.StartsWith("Logging__", StringComparison.OrdinalIgnoreCase) || x.StartsWith("Logging:", StringComparison.OrdinalIgnoreCase)
            || new[] { "urls", "HTTP_PORTS", "HTTPS_PORTS", "contentRoot", "applicationName", "environment", "webRoot" }
                .Contains(x, StringComparer.OrdinalIgnoreCase)).ToArray()) start.Environment.Remove(key);
    }
    private static string? AnnouncedBinding(string line)
    {
        const string marker = "Now listening on:";
        int at = line.IndexOf(marker, StringComparison.Ordinal);
        return at < 0 ? null : line[(at + marker.Length)..].Trim();
    }
    private static bool OwnsBinding(IEnumerable<string> bindings, string address)
    {
        var actual = bindings.Distinct(StringComparer.Ordinal).ToArray();
        Require(actual.All(x => x == address), "The owned fixture announced an unexpected listener; no HTTP requests are permitted.");
        return actual.Length == 1;
    }
    private static string Within(string root, string path)
    {
        string full = Path.GetFullPath(path), prefix = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        Require(full.StartsWith(prefix, OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal),
            "Probe files must stay inside the calling workspace.");
        for (string? current = full; current is not null && current.Length >= prefix.Length - 1; current = Path.GetDirectoryName(current))
        {
            try { Require((File.GetAttributes(current) & FileAttributes.ReparsePoint) == 0, "Linked probe paths are refused."); }
            catch (FileNotFoundException) { } catch (DirectoryNotFoundException) { }
        }
        return full;
    }
    private sealed record ObservedFile(string Path, long Bytes, DateTime ModifiedUtc, string Sha256);
    private static ObservedFile ObserveFile(string root, string path)
    {
        path = Within(root, path); var before = new FileInfo(path);
        Require(before.Exists, "A required Release build input or assembly is missing: " + Path.GetRelativePath(root, path));
        long length = before.Length; DateTime modified = before.LastWriteTimeUtc;
        byte[] bytes = File.ReadAllBytes(path); var after = new FileInfo(path);
        Require(after.Exists && length == after.Length && modified == after.LastWriteTimeUtc && bytes.LongLength == length,
            "A build input or assembly changed while it was fingerprinted: " + Path.GetRelativePath(root, path));
        return new(Path.GetRelativePath(root, path).Replace('\\', '/'), length, modified,
            Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant());
    }
    private static string[] SourceInputs(string root, string relative)
    {
        var result = new List<string>(); var directories = new Stack<string>();
        directories.Push(Within(root, Path.Combine(root, relative)));
        while (directories.Count > 0)
        {
            string directory = directories.Pop();
            foreach (string child in Directory.EnumerateDirectories(directory))
                if (Path.GetFileName(child) is not ("bin" or "obj")) directories.Push(Within(root, child));
            foreach (string file in Directory.EnumerateFiles(directory))
                if (Path.GetExtension(file) is ".cs" or ".csproj" or ".props" or ".targets"
                    || Path.GetFileName(file) is "NuGet.Config" or "nuget.config" or "packages.lock.json")
                    result.Add(Within(root, file));
        }
        return result.Order(StringComparer.Ordinal).ToArray();
    }
    private static string[] NewerInputs(ObservedFile assembly, IEnumerable<ObservedFile> inputs)
        => inputs.Where(x => x.ModifiedUtc > assembly.ModifiedUtc).Select(x => x.Path).Order(StringComparer.Ordinal).ToArray();
    private static ObservedFile[] ObserveReleaseBuild(string root, string serverDll, Dictionary<string, object?> evidence)
    {
        evidence["status"] = "checking";
        evidence["method"] = "Current source/build inputs and Release DLL hashes plus modification-time stale-build rejection. This is a conservative guard, not compilation correspondence.";
        evidence["sourceToAssemblyCorrespondenceProved"] = false;
        evidence["localDeliveryAccepted"] = false;
        evidence["externalCiProofRequired"] = "Exact checkout GITHUB_SHA and the retained Release build invocation must establish CI provenance separately.";
        evidence["limitations"] = "No trusted compiler input manifest is available here. Modification times cannot establish correspondence or detect backdated/deleted inputs; current byte fingerprints only guard against changes during this invocation.";
        string probeDll = Within(root, typeof(ClassicTutorialLiveProbe).Assembly.Location);
        string expectedProbe = Within(root, Path.Combine(root, "tools", "new_player_probe", "bin", "Release", "net10.0", "new_player_probe.dll"));
        var comparison = OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;
        Require(probeDll.Equals(expectedProbe, comparison), "Run the optional live probe from the current Release build; a Debug or unrelated assembly is refused.");
        string probeCore = Within(root, typeof(Character).Assembly.Location);
        Require(probeCore.Equals(Path.Combine(Path.GetDirectoryName(expectedProbe)!, "Kairnfall.Core.dll"), comparison),
            "The executing probe must use its workspace Release Core assembly.");
        var core = SourceInputs(root, "src/Kairnfall.Core"); var server = SourceInputs(root, "src/Kairnfall.Server");
        var probe = SourceInputs(root, "tools/new_player_probe");
        foreach (string project in new[] { "src/Kairnfall.Core/Kairnfall.Core.csproj", "src/Kairnfall.Server/Kairnfall.Server.csproj", "tools/new_player_probe/new_player_probe.csproj" })
            Require(File.Exists(Within(root, Path.Combine(root, project))), "Current workspace project inputs are required: " + project);
        var shared = new List<string>();
        foreach (string directory in new[] { "", "src", "tools" })
            foreach (string name in new[] { "Directory.Build.props", "Directory.Build.targets", "Directory.Packages.props", "NuGet.Config", "nuget.config", "global.json" })
            {
                string path = Within(root, Path.Combine(root, directory, name));
                if (File.Exists(path)) shared.Add(path);
            }
        shared.Add(Within(root, Path.Combine(root, "Kairnfall.slnx")));
        var inputs = core.Concat(server).Concat(probe).Concat(shared).Distinct(StringComparer.Ordinal)
            .Order(StringComparer.Ordinal).Select(path => ObserveFile(root, path)).ToArray();
        ObservedFile[] For(IEnumerable<string> paths) => paths.Concat(shared).Distinct(StringComparer.Ordinal)
            .Select(path => inputs.Single(x => x.Path == Path.GetRelativePath(root, path).Replace('\\', '/'))).ToArray();
        var coreInputs = For(core); var serverInputs = For(core.Concat(server)); var probeInputs = For(core.Concat(server).Concat(probe));
        var assemblies = new[]
        {
            (File: ObserveFile(root, serverDll), Inputs: serverInputs),
            (File: ObserveFile(root, Path.Combine(Path.GetDirectoryName(serverDll)!, "Kairnfall.Core.dll")), Inputs: coreInputs),
            (File: ObserveFile(root, probeDll), Inputs: probeInputs),
            (File: ObserveFile(root, probeCore), Inputs: coreInputs)
        };
        var newer = assemblies.Select(x => new { assembly = x.File, newerInputs = NewerInputs(x.File, x.Inputs) }).ToArray();
        evidence["sourceInputs"] = inputs; evidence["assemblies"] = newer;
        evidence["status"] = newer.Any(x => x.newerInputs.Length > 0) ? "stale" : "no-newer-inputs-detected";
        Require((string)evidence["status"]! != "stale", "Release DLLs predate source/build inputs. Rebuild Release before live execution; see retained buildFreshness evidence.");
        return inputs.Concat(assemblies.Select(x => x.File)).DistinctBy(x => x.Path).ToArray();
    }
    private static void RequireUnchangedBuild(string root, IEnumerable<ObservedFile> baseline)
    {
        foreach (var expected in baseline)
            Require(ObserveFile(root, Path.Combine(root, expected.Path)) == expected,
                "Source/build inputs or Release assemblies changed during the live probe: " + expected.Path);
    }
    private static void RequireOriginalReplay(GameCommand command, string signature, CommandResult original, CommandResult replay)
    {
        Require(Json(command) == signature && command.Kind == "classic_interact" && command.Target == "classic_first_sign"
            && Guid.TryParseExact(command.RequestId, "N", out _) && command.RequestId == original.RequestId
            && command.Sequence == original.Sequence && original.Ok && original.Sequence > 0,
            "Replay must preserve the successful sign's exact original GUID, sequence and command signature.");
        Require(replay.Ok && Json(replay) == Json(original), "A retained replay did not return the exact original successful receipt.");
    }
    private static void RequirePersistedReceipt(Character player, GameCommand command, CommandResult original)
    {
        var receipts = player.Receipts.Where(x => x.RequestId == command.RequestId).ToArray();
        Require(receipts.Length == 1 && Json(receipts[0].Result) == Json(original),
            "The persisted replay ledger lost, changed or duplicated the real sign receipt.");
    }
    private static string Progress(Character player) => Json(new { player.Id, player.Name, player.Class, player.Appearance, player.Zone, player.Position, player.Facing,
        player.Gold, Inventory = player.Inventory.OrderBy(x => x.Id), Bank = player.Bank.OrderBy(x => x.Id),
        Equipment = player.Equipment.OrderBy(x => x.Key), SkillXp = player.SkillXp.OrderBy(x => x.Key),
        player.PracticeOnlyXp, player.OverallCreditRemainder,
        CombatPracticeRemainders = player.CombatPracticeRemainders.OrderBy(x => x.Key),
        GeneralPracticeRemainders = player.GeneralPracticeRemainders.OrderBy(x => x.Key),
        Quests = player.Quests.OrderBy(x => x.Key), CompletedQuests = player.CompletedQuests.Order(),
        Reputation = player.Reputation.OrderBy(x => x.Key), Discoveries = player.Discoveries.Order(),
        Waypoints = player.Waypoints.Order(), Achievements = player.Achievements.Order(), Bestiary = player.Bestiary.OrderBy(x => x.Key),
        player.Deaths, player.PublicEventsCompleted,
        Cooldowns = player.Cooldowns.OrderBy(x => x.Key), player.DeadUntil, player.LastAction,
        Milestones = player.ClassicTutorial?.Completed.Order(), NoticeId = player.ClassicTutorial?.NoticeId, Notice = player.ClassicTutorial?.Notice });

    public static void CheckScopeBoundaries(Catalog normal)
    {
        void Reject(Action action)
        {
            try { action(); } catch (InvalidOperationException) { return; }
            throw new InvalidOperationException("A malformed scope was accepted.");
        }
        const string test = "Host=127.0.0.1;Database=optional_test;Username=fixture";
        RequireDatabase(test, true); Reject(() => RequireDatabase(test, false));
        foreach (string bad in new[] { "Host=127.0.0.1;Database=retained", "Host=example.com;Database=optional_test",
            "Host=127.0.0.1;Database=optional_test;Search Path=public", "Host=127.0.0.1,example.com;Database=optional_test", "malformed-connection" })
            Reject(() => RequireDatabase(bad, true));
        string suffix = new string('a', 32); Require(OwnedSchema("optional", suffix).StartsWith("classic_probe_optional_"), "Owned schema prefix changed.");
        Reject(() => OwnedSchema("public", suffix)); Reject(() => OwnedSchema("normal", suffix + "\";"));
        string root = Path.GetFullPath(Directory.GetCurrentDirectory()); Within(root, Path.Combine(root, "artifacts", "fixture.json"));
        Reject(() => Within(root, Path.Combine(root, "..", "outside.json")));
        var start = new ProcessStartInfo("dotnet"); start.Environment.Clear();
        foreach (string key in new[] { "DOTNET_URLS", "dotnet_http_ports", "DOTNET_Kestrel__Endpoints__Public__Url", "Kestrel:Endpoints:Public:Url", "ASPNETCORE_URLS", "urls", "HTTP_PORTS", "Logging__LogLevel__Default" })
            start.Environment[key] = "untrusted-fixture-setting";
        start.Environment["DOTNET_ROOT"] = "fixture-runtime"; start.Environment["PATH"] = "fixture-path";
        SanitizeServerEnvironment(start);
        Require(start.Environment.Count == 2 && start.Environment["DOTNET_ROOT"] == "fixture-runtime" && start.Environment["PATH"] == "fixture-path",
            "Binding configuration must be removed without losing the runtime executable search paths.");
        const string address = "http://127.0.0.1:5089";
        Require(!OwnsBinding([], address) && OwnsBinding([AnnouncedBinding("      Now listening on: " + address)!], address), "Readiness requires the owned child's exact listening announcement.");
        Reject(() => OwnsBinding(["http://127.0.0.1:50890"], address));
        Reject(() => OwnsBinding([address, "http://0.0.0.0:5090"], address));
        var fixture = new Character { PracticeOnlyXp = 7, OverallCreditRemainder = .25, CombatPracticeRemainders = new() { ["blade"] = .5 }, GeneralPracticeRemainders = new() { ["mining"] = .5 } };
        string progress = Progress(fixture);
        foreach (Action<Character> mutate in new Action<Character>[] { x => x.PracticeOnlyXp++, x => x.OverallCreditRemainder += .1,
            x => x.CombatPracticeRemainders["blade"] += .1, x => x.GeneralPracticeRemainders["mining"] += .1 })
        {
            var changed = Wire.Copy(fixture); mutate(changed);
            Require(Progress(changed) != progress, "A persisted XP accounting loss must not pass the restart comparison.");
        }
        var command = new GameCommand { Kind = "classic_interact", Target = "classic_first_sign", Sequence = 3 };
        var receipt = new CommandResult { Ok = true, RequestId = command.RequestId, Sequence = command.Sequence, Message = "Original sign receipt" };
        string signature = Json(command);
        RequireOriginalReplay(Wire.Copy(command), signature, receipt, Wire.Copy(receipt));
        foreach (Action<GameCommand> mutate in new Action<GameCommand>[] { x => x.RequestId = Guid.NewGuid().ToString("N"),
            x => x.Sequence++, x => x.Target = "classic_fountain", x => x.Arg = "changed-signature" })
        {
            var changed = Wire.Copy(command); mutate(changed);
            Reject(() => RequireOriginalReplay(changed, signature, receipt, receipt));
        }
        fixture.LastAction = 7;
        fixture.Receipts.Add(new() { RequestId = command.RequestId, Result = Wire.Copy(receipt) });
        RequirePersistedReceipt(fixture, command, receipt); progress = Progress(fixture);
        foreach (Action<Character> mutate in new Action<Character>[] { x => x.Receipts.Clear(), x => x.Receipts[0].Result.Sequence++,
            x => x.Receipts.Add(Wire.Copy(x.Receipts[0])) })
        {
            var changed = Wire.Copy(fixture); mutate(changed);
            Require(Progress(changed) == progress, "The private replay ledger is deliberately absent from projected progress.");
            Reject(() => RequirePersistedReceipt(changed, command, receipt));
        }
        var observed = ObserveFile(root, Path.Combine(root, "tools", "new_player_probe", "ClassicTutorialLiveProbe.cs"));
        RequireUnchangedBuild(root, [observed]);
        Reject(() => RequireUnchangedBuild(root, [observed with { Sha256 = new string('0', 64) }]));
        var assembly = new ObservedFile("fixture.dll", 1, new DateTime(2026, 1, 1, 0, 0, 0, DateTimeKind.Utc), "fixture");
        Require(NewerInputs(assembly, [assembly with { Path = "same.cs" }, assembly with { Path = "older.cs", ModifiedUtc = assembly.ModifiedUtc.AddTicks(-1) }]).Length == 0,
            "A conservative timestamp guard must not claim that equal or older inputs prove compilation correspondence.");
        Require(NewerInputs(assembly, [assembly with { Path = "changed.cs", ModifiedUtc = assembly.ModifiedUtc.AddTicks(1) }]).SequenceEqual(["changed.cs"]),
            "A newer build input must reject a potentially stale Release assembly.");
        string before = Json(normal); var optional = Wire.Copy(normal); ClassicTutorialContent.Enable(optional);
        Require(Json(normal) == before && optional.Validate().Count == 0, "Disposable overlay changed the source catalog.");
        Reject(() => ClassicTutorialContent.RequireLocalStartup(false, true, true, true, ["http://127.0.0.1:5089"]));
        Reject(() => ClassicTutorialContent.RequireLocalStartup(true, true, false, true, ["http://127.0.0.1:5089"]));
        Reject(() => ClassicTutorialContent.RequireLocalStartup(true, true, true, false, ["http://127.0.0.1:5089"]));
        ClassicTutorialContent.RequireLocalStartup(true, true, true, true, ["http://127.0.0.1:5089"]);
        Console.WriteLine("CLASSIC_TUTORIAL_SCOPE_CHECKS: database, schema, workspace, child binding configuration, persistence accounting, original replay signatures/ledger, conservative build guards and detached catalog boundaries passed; no services started or compilation correspondence proved.");
    }

    public static async Task<int> RunAsync(Catalog normal, string catalogPath)
    {
        string root = Path.GetFullPath(Directory.GetCurrentDirectory());
        Require(File.Exists(Path.Combine(root, "Kairnfall.slnx")), "Run from the Kairnfall workspace root.");
        catalogPath = Within(root, catalogPath);
        Require(normal.ClassicTutorial is null && normal.Validate().Count == 0, "This probe starts from a validated ordinary catalog.");
        string suffix = Guid.NewGuid().ToString("N"), normalSchema = OwnedSchema("normal", suffix), optionalSchema = OwnedSchema("optional", suffix);
        string evidence = Within(root, Path.Combine(root, "artifacts", "journey", "optional-live", suffix)); Directory.CreateDirectory(evidence);
        string serverDll = Within(root, Path.Combine(root, "src", "Kairnfall.Server", "bin", "Release", "net10.0", "Kairnfall.Server.dll"));
        string overlaid = Within(root, Path.Combine(evidence, "validated-optional-catalog.json"));
        string contentRoot = Within(root, Path.Combine(evidence, "server-content"));
        var results = Cases.ToDictionary(x => x, _ => new Dictionary<string, object?> { ["status"] = "not-run" });
        var setup = new Dictionary<string, object?> { ["status"] = "not-run" };
        var cleanup = new Dictionary<string, object?> { ["status"] = "not-run", ["server"] = "not-run" };
        var attemptedSchemas = new List<string>(); var createdSchemas = new HashSet<string>(); var removedSchemas = new HashSet<string>();
        var cleanupErrors = new List<string>(); var launchesEvidence = new List<Dictionary<string, object?>>();
        var buildFreshness = new Dictionary<string, object?> { ["status"] = "not-run", ["sourceToAssemblyCorrespondenceProved"] = false,
            ["localDeliveryAccepted"] = false };
        ObservedFile[] observedBuild = [];
        string ownership = "kairnfall-classic-probe:" + suffix;
        NpgsqlConnectionStringBuilder? database = null; NpgsqlDataSource? admin = null; Catalog optional = null!;
        string? failure = null; bool publicEndpointOpened = false;
        using var deadline = new CancellationTokenSource(TimeSpan.FromMinutes(7)); var cancel = deadline.Token;
        string Scrub(string message)
        {
            string? password = database?.Password;
            return string.IsNullOrEmpty(password) ? message : message.Replace(password, "[REDACTED]", StringComparison.Ordinal);
        }
        string Error(Exception error) => Scrub(error.GetType().Name + ": " + error.Message);
        string address = ""; Process? server = null; int launches = 0;
        async Task Stop(CancellationToken cleanupToken = default)
        {
            if (server is null) return;
            if (!server.HasExited) { server.Kill(entireProcessTree: true); await server.WaitForExitAsync(cleanupToken).WaitAsync(TimeSpan.FromSeconds(20), cleanupToken); }
            server.Dispose(); server = null;
        }
        async Task Start(string schema, bool tutorial, string path, bool ready = true, string environment = "Testing", bool allowHttp = true, string? expected = null)
        {
            RequireUnchangedBuild(root, observedBuild);
            await Stop(); var scoped = new NpgsqlConnectionStringBuilder(database!.ConnectionString) { SearchPath = schema };
            Require(createdSchemas.Contains(schema), "A fixture server may use only a schema created by this invocation.");
            var start = new ProcessStartInfo("dotnet") { WorkingDirectory = contentRoot, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
            start.ArgumentList.Add(serverDll);
            start.ArgumentList.Add("--urls"); start.ArgumentList.Add(address);
            start.ArgumentList.Add("--contentRoot"); start.ArgumentList.Add(contentRoot);
            SanitizeServerEnvironment(start);
            start.Environment["KAIRNFALL_DB"] = scoped.ConnectionString; start.Environment["KAIRNFALL_CATALOG"] = path;
            start.Environment["KAIRNFALL_CLASSIC_TUTORIAL"] = tutorial ? "1" : "0";
            start.Environment["KAIRNFALL_ALLOW_LOCAL_HTTP"] = allowHttp ? "1" : "0";
            start.Environment["ASPNETCORE_ENVIRONMENT"] = environment; start.Environment["DOTNET_ENVIRONMENT"] = environment;
            start.Environment["ASPNETCORE_URLS"] = address;
            start.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
            start.Environment["DOTNET_GENERATE_ASPNET_CERTIFICATE"] = "false";
            start.Environment["DOTNET_ADD_GLOBAL_TOOLS_TO_PATH"] = "false";
            start.Environment["Logging__LogLevel__Default"] = "Warning";
            start.Environment["Logging__LogLevel__Microsoft.Hosting.Lifetime"] = "Information";
            start.Environment["Logging__Console__FormatterName"] = "simple";
            start.Environment["Logging__Console__FormatterOptions__ColorBehavior"] = "Disabled";
            string log = Within(root, Path.Combine(evidence, "server-" + (++launches) + ".log")); var lines = new StringBuilder(); var bindings = new List<string>(); object logLock = new();
            string? logError = null;
            server = Process.Start(start) ?? throw new InvalidOperationException("Fixture server did not start.");
            var launch = new Dictionary<string, object?> { ["pid"] = server.Id, ["schema"] = schema, ["address"] = address, ["log"] = Path.GetFileName(log), ["status"] = "starting" };
            launchesEvidence.Add(launch);
            void Record(string? text)
            {
                if (text is null) return;
                lock (logLock)
                {
                    text = Scrub(text); lines.AppendLine(text);
                    if (AnnouncedBinding(text) is { } binding) bindings.Add(binding);
                    try { File.AppendAllText(log, text + Environment.NewLine); }
                    catch (Exception error) { logError ??= Error(error); }
                }
            }
            server.OutputDataReceived += (_, item) => Record(item.Data); server.ErrorDataReceived += (_, item) => Record(item.Data);
            server.BeginOutputReadLine(); server.BeginErrorReadLine();
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(2) }; var clock = Stopwatch.StartNew();
            while (clock.Elapsed < TimeSpan.FromSeconds(35))
            {
                string[] actualBindings;
                lock (logLock) { actualBindings = bindings.ToArray(); Require(logError is null, "Fixture log could not be retained: " + logError); }
                launch["announcedBindings"] = actualBindings;
                publicEndpointOpened |= actualBindings.Any(x => !Uri.TryCreate(x, UriKind.Absolute, out var bound) || !bound.IsLoopback);
                bool ownsBinding = OwnsBinding(actualBindings, address);
                if (server.HasExited)
                {
                    server.WaitForExit(); string output;
                    lock (logLock) { output = lines.ToString(); actualBindings = bindings.ToArray(); Require(logError is null, "Fixture log could not be retained: " + logError); }
                    launch["announcedBindings"] = actualBindings;
                    publicEndpointOpened |= actualBindings.Any(x => !Uri.TryCreate(x, UriKind.Absolute, out var bound) || !bound.IsLoopback);
                    ownsBinding = OwnsBinding(actualBindings, address);
                    Require(!ready && server.ExitCode != 0 && expected is not null && output.Contains(expected, StringComparison.Ordinal), "Server failed for an unexpected startup reason; inspect its retained log.");
                    Require(!ownsBinding, "A forbidden fixture bound its listener before refusing startup.");
                    launch["status"] = "expected-refusal";
                    await Stop(); return;
                }
                if (ownsBinding)
                {
                    try
                    {
                        using var response = await http.GetAsync(address + "/health", cancel);
                        Require(!server.HasExited, "The owned server exited while readiness was being checked.");
                        if (response.IsSuccessStatusCode)
                        {
                            Require(ready, "A forbidden fixture server became ready.");
                            using var health = JsonDocument.Parse(await response.Content.ReadAsStringAsync(cancel));
                            Require(health.RootElement.GetProperty("ready").GetBoolean() && health.RootElement.GetProperty("protocol").GetInt32() == Wire.Version,
                                "The owned listener did not return the expected ready realm protocol.");
                            launch["status"] = "ready"; return;
                        }
                    }
                    catch (HttpRequestException) { } catch (TaskCanceledException) when (!cancel.IsCancellationRequested) { }
                }
                await Task.Delay(100, cancel);
            }
            throw new TimeoutException("Expected bounded fixture readiness/startup refusal was not observed.");
        }
        async Task<(string Hash, RealmSave Save)> Saved(string schema)
        {
            Require(createdSchemas.Contains(schema), "Only this invocation's owned saved realms may be inspected.");
            await using var source = NpgsqlDataSource.Create(new NpgsqlConnectionStringBuilder(database!.ConnectionString) { SearchPath = schema }.ConnectionString);
            await using var query = source.CreateCommand("SELECT payload::text FROM realm_snapshots WHERE id=1");
            string payload = (string?)await query.ExecuteScalarAsync(cancel) ?? throw new InvalidOperationException("No durable fixture realm was produced.");
            return (Hash(payload), JsonSerializer.Deserialize<RealmSave>(payload, Wire.Json)!);
        }
        async Task Case(string name, Func<Task> body)
        {
            var clock = Stopwatch.StartNew(); results[name]["status"] = "running";
            try { await body(); results[name]["status"] = "passed"; Console.WriteLine("PASS CLASSIC LIVE: " + name); }
            catch (Exception error) { results[name]["status"] = "failed"; results[name]["error"] = Error(error); throw; }
            finally { results[name]["milliseconds"] = clock.Elapsed.TotalMilliseconds; }
        }
        int code = 1;
        try
        {
            setup["status"] = "running";
            observedBuild = ObserveReleaseBuild(root, serverDll, buildFreshness);
            RequireUnchangedBuild(root, observedBuild);
            database = RequireDatabase(Environment.GetEnvironmentVariable("KAIRNFALL_TEST_DB") ?? "",
                Environment.GetEnvironmentVariable("KAIRNFALL_ALLOW_DB_TESTS") == "1");
            Require(File.Exists(serverDll), "Build the Release server before explicitly running the live probe.");
            Directory.CreateDirectory(contentRoot);
            Require(!Directory.EnumerateFileSystemEntries(contentRoot).Any(), "The owned server content root must contain no inherited configuration.");
            optional = Wire.Copy(normal); ClassicTutorialContent.Enable(optional);
            await File.WriteAllTextAsync(overlaid, Json(optional), cancel);
            admin = NpgsqlDataSource.Create(database.ConnectionString);
            foreach (string schema in new[] { normalSchema, optionalSchema })
            {
                attemptedSchemas.Add(schema);
                await using var connection = await admin.OpenConnectionAsync(cancel);
                await using var transaction = await connection.BeginTransactionAsync(cancel);
                await using (var command = new NpgsqlCommand("CREATE SCHEMA \"" + schema + "\"; COMMENT ON SCHEMA \"" + schema + "\" IS '" + ownership + "'", connection, transaction))
                    await command.ExecuteNonQueryAsync(cancel);
                await transaction.CommitAsync(cancel); createdSchemas.Add(schema);
            }
            var listener = new TcpListener(IPAddress.Loopback, 0);
            try { listener.Start(); address = "http://127.0.0.1:" + ((IPEndPoint)listener.LocalEndpoint).Port; }
            finally { listener.Stop(); }
            setup["status"] = "passed";
            await Case("startup opt-in gates", async () =>
            {
                const string refusal = "Classic tutorial startup requires";
                await Start(normalSchema, false, overlaid, false, expected: refusal);
                await Start(normalSchema, true, catalogPath, false, environment: "Production", expected: refusal);
                await Start(normalSchema, true, catalogPath, false, allowHttp: false, expected: refusal);
                await using var query = admin.CreateCommand("SELECT count(*) FROM information_schema.tables WHERE table_schema=$1");
                query.Parameters.AddWithValue(normalSchema);
                Require((long)(await query.ExecuteScalarAsync(cancel))! == 0, "Startup opt-in refusals reached database initialization.");
            });
            await Case("normal saved-mode refusal", async () =>
            {
                await Start(normalSchema, false, catalogPath);
                await using (var client = new GameConnection(address))
                {
                    await client.SignInAsync("cn_" + suffix[..12], "QA_" + Guid.NewGuid().ToString("N"), true, cancel);
                    var downloaded = await client.CatalogAsync(cancel); Require(downloaded.ClassicTutorial is null && downloaded.Validate().Count == 0, "Normal startup changed catalog mode.");
                    var created = await client.CreateCharacterAsync(new CharacterRequest { Name = "Normal Boundary", Class = "vanguard" }, cancel);
                    await client.ConnectAsync(created.Id, cancel); await client.DisconnectAsync();
                }
                await Stop(); var before = await Saved(normalSchema);
                await Start(normalSchema, true, catalogPath, false, expected: "World mode mismatch");
                var after = await Saved(normalSchema); Require(before.Hash == after.Hash && !after.Save.State.ClassicTutorialEnabled, "Normal retained save was converted or rewritten.");
                results["normal saved-mode refusal"]["savedPayloadSha256"] = before.Hash;
            });
            await Start(optionalSchema, true, catalogPath);
            await using var account = new GameConnection(address);
            string username = "ct_" + suffix[..12], password = "QA_" + Guid.NewGuid().ToString("N");
            await account.SignInAsync(username, password, true, cancel);
            Catalog downloadedOptional = null!;
            await Case("downloaded tutorial catalog", async () =>
            {
                downloadedOptional = await account.CatalogAsync(cancel);
                Require(downloadedOptional.ClassicTutorial is not null && downloadedOptional.Validate().Count == 0, "Downloaded tutorial catalog is incomplete or invalid.");
                Require(Json(downloadedOptional.ClassicTutorial) == Json(optional.ClassicTutorial), "Server changed authoritative tutorial tuning.");
                Require(downloadedOptional.Zone(ClassicTutorialContent.ZoneId).Furnishings.Count == ClassicTutorialContent.Sites.Length, "Downloaded site context is incomplete.");
                results["downloaded tutorial catalog"]["catalogSha256"] = Hash(Json(downloadedOptional));
            });
            var character = await account.CreateCharacterAsync(new CharacterRequest { Name = "Optional Boundary", Class = "vanguard" }, cancel);
            WireClient? wire = null; GameCommand signReceipt = null!; CommandResult originalReceipt = null!;
            string signSignature = "", expectedProgress = "";
            async Task VerifyRetainedReplay(string name)
            {
                var active = wire ?? throw new InvalidOperationException("Replay requires the authenticated owned character connection.");
                string before = Progress(active.Self); long lastAction = active.Self.LastAction;
                Require(before == expectedProgress && lastAction > signReceipt.Sequence,
                    "Retained replay must start from independently observed later actions, without resetting accepted sequencing.");
                var command = Wire.Copy(signReceipt);
                RequireOriginalReplay(command, signSignature, originalReceipt, originalReceipt);
                var replay = await active.Replay(command, cancel);
                RequireOriginalReplay(command, signSignature, originalReceipt, replay);
                // A queued pre-replay snapshot has unchanged LastAction too. A
                // completed authenticated detach checkpoints the actual state;
                // inspect that private ledger and then establish a fresh read.
                await active.Disconnect(cancel); wire = null;
                var saved = await Saved(optionalSchema); var retained = saved.Save.State.Characters[character.Id];
                Require(retained.Account == account.Session!.AccountId && retained.LastAction == lastAction && Progress(retained) == before,
                    "Retained replay changed durable ownership, possessions, progress, XP or accepted sequencing.");
                RequirePersistedReceipt(retained, command, originalReceipt);
                wire = await WireClient.Connect(address, account.Session.Token, character.Id, cancel);
                Require(wire.Self.LastAction == lastAction && Progress(wire.Self) == before && Progress(wire.Self) == expectedProgress,
                    "A fresh authenticated snapshot observed duplicated replay rewards, milestones, XP or sequencing.");
                results[name]["requestId"] = command.RequestId;
                results[name]["commandSignatureSha256"] = Hash(signSignature);
                results[name]["originalReceiptSha256"] = Hash(Json(originalReceipt));
                results[name]["replayedReceiptSha256"] = Hash(Json(replay));
                results[name]["acceptedLastActionBefore"] = lastAction;
                results[name]["acceptedLastActionAfter"] = wire.Self.LastAction;
                results[name]["savedProgressSha256"] = Hash(Progress(retained));
                results[name]["freshProgressSha256"] = Hash(Progress(wire.Self));
                results[name]["persistedOriginalReceiptVerified"] = true;
                results[name]["conservationObservation"] = "Completed authenticated detach, actual saved receipt ledger, then a fresh authenticated reconnect; projected snapshot receipt fields alone are not evidence.";
            }
            try
            {
                wire = await WireClient.Connect(address, account.Session!.Token, character.Id, cancel);
                await Case("authoritative tutorial actions", async () =>
                {
                    Require(wire.Self.Zone == ClassicTutorialContent.ZoneId && wire.Self.ClassicTutorial is not null, "New tutorial character did not start in First Glade.");
                    var initial = wire.Self; Require(Items.Count(initial, "classic_berries") == 4, "Server starter possessions changed.");
                    var refused = await wire.Act(new GameCommand { Kind = "classic_interact", Target = "classic_first_sign" }, cancel);
                    Require(!refused.Ok && !wire.Self.ClassicTutorial!.Completed.Contains("read_sign"), "Distant site interaction fabricated a milestone.");
                    await wire.Step(new Point(1, 0), cancel);
                    Require(ClassicTutorialContent.FacingAdjacent(wire.Self, ClassicTutorialContent.Sites[0].Position), "Accepted grid movement did not establish site adjacency/facing.");
                    signReceipt = new GameCommand { Kind = "classic_interact", Target = "classic_first_sign" };
                    originalReceipt = await wire.Act(signReceipt, cancel); Require(originalReceipt.Ok, "The reachable sign action was refused.");
                    signSignature = Json(signReceipt);
                    RequireOriginalReplay(signReceipt, signSignature, originalReceipt, originalReceipt);
                    await wire.State(x => x.Self.ClassicTutorial!.Completed.Contains("read_sign"), cancel);
                    int berries = Items.Count(wire.Self, "classic_berries"); double food = wire.Self.ClassicTutorial!.Food;
                    var consume = await wire.Act(new GameCommand { Kind = "consume", Item = wire.Self.Inventory.First(x => x.Template == "classic_berries").Id }, cancel);
                    Require(consume.Ok, "Server refused tutorial food.");
                    await wire.State(x => Items.Count(x.Self, "classic_berries") == berries - 1 && x.Self.ClassicTutorial!.Completed.Contains("food"), cancel);
                    Require(wire.Self.ClassicTutorial!.Food > food && wire.Self.ClassicTutorial.Food <= 100, "Food restoration did not come from the authoritative action.");
                    await Gather(wire, downloadedOptional, "classic_tree", "classic_wood", 5, cancel);
                    await Gather(wire, downloadedOptional, "classic_stone_node", "classic_stone", 10, cancel);
                    var craft = await wire.Act(new GameCommand { Kind = "craft", Item = "classic_make_pickaxe" }, cancel); Require(craft.Ok, "Real gathered ingredients did not craft a pickaxe.");
                    await wire.State(x => x.Self.Inventory.Any(item => item.Template == "classic_stone_pickaxe"), cancel);
                    string pickaxe = wire.Self.Inventory.First(x => x.Template == "classic_stone_pickaxe").Id;
                    var equip = await wire.Act(new GameCommand { Kind = "equip", Item = pickaxe }, cancel); Require(equip.Ok, "Crafted pickaxe could not be equipped.");
                    await wire.State(x => x.Self.Equipment.GetValueOrDefault("weapon") == pickaxe, cancel);
                    Require(wire.Self.ClassicTutorial!.Completed.IsSupersetOf(["read_sign", "food", "wood", "stone", "pickaxe"]), "Real actions did not record their authoritative milestones.");
                    expectedProgress = Progress(wire.Self);
                    results["authoritative tutorial actions"]["expectedProgressSha256"] = Hash(expectedProgress);
                });
                await Case("receipt replay", () => VerifyRetainedReplay("receipt replay"));
                await Case("disconnect and reconnect", async () =>
                {
                    string before = Progress(wire.Self); await wire.Disconnect(cancel); wire = null;
                    wire = await WireClient.Connect(address, account.Session!.Token, character.Id, cancel);
                    Require(Progress(wire.Self) == before && Progress(wire.Self) == expectedProgress, "Same-server reconnect changed exact progress, XP accounting or possessions.");
                });
                await Case("receipt replay after authenticated reconnect", () => VerifyRetainedReplay("receipt replay after authenticated reconnect"));
                Require(Progress(wire.Self) == expectedProgress, "The independently observed post-equip progress changed before restart.");
                await wire.Disconnect(cancel); wire = null; await Stop();
                await Case("process restart", async () =>
                {
                    var saved = await Saved(optionalSchema);
                    var retained = saved.Save.State.Characters[character.Id]; Require(retained.ClassicTutorial is not null, "Durable tutorial progress is missing.");
                    Require(Progress(retained) == expectedProgress && retained.Account == account.Session!.AccountId,
                        "The durable realm lost independently observed post-equip progress, XP accounting, possessions or account ownership.");
                    RequirePersistedReceipt(retained, signReceipt, originalReceipt);
                    results["process restart"]["persistedOriginalReceiptVerifiedBeforeRestart"] = true;
                    results["process restart"]["expectedProgressSha256"] = Hash(expectedProgress);
                    results["process restart"]["savedProgressSha256"] = Hash(Progress(retained));
                    await Start(optionalSchema, true, overlaid);
                    await account.SignInAsync(username, password, false, cancel);
                    var restartedCatalog = await account.CatalogAsync(cancel);
                    Require(restartedCatalog.Validate().Count == 0 && Json(restartedCatalog) == Json(downloadedOptional),
                        "Pre-overlaid restart changed the downloaded catalog.");
                    wire = await WireClient.Connect(address, account.Session!.Token, character.Id, cancel);
                    Require(Progress(wire.Self) == expectedProgress, "Process restart changed independently observed identity, possessions, facing, XP accounting or milestone progress.");
                    Require(wire.Latest.Time >= saved.Save.State.Time && wire.Self.ClassicTutorial!.Food <= retained.ClassicTutorial.Food
                        && retained.ClassicTutorial.Food - wire.Self.ClassicTutorial.Food < 1, "Restart Food does not follow the retained server clock.");
                });
                await Case("durable receipt replay after process restart", () => VerifyRetainedReplay("durable receipt replay after process restart"));
                var completedReplayWire = wire ?? throw new InvalidOperationException("The durable replay did not restore its authenticated connection.");
                await completedReplayWire.Disconnect(cancel); wire = null;
                await Stop(); var beforeRefusal = await Saved(optionalSchema);
                await Case("tutorial saved-mode refusal", async () =>
                {
                    await Start(optionalSchema, false, catalogPath, false, expected: "World mode mismatch");
                    var after = await Saved(optionalSchema); Require(after.Hash == beforeRefusal.Hash && after.Save.State.ClassicTutorialEnabled, "Tutorial retained save was converted or rewritten.");
                    results["tutorial saved-mode refusal"]["savedPayloadSha256"] = beforeRefusal.Hash;
                });
            }
            finally { if (wire is not null) await wire.DisposeAsync(); }
            RequireUnchangedBuild(root, observedBuild); buildFreshness["stabilityAfterRuntime"] = "unchanged";
            code = 0;
        }
        catch (Exception error)
        {
            failure = Error(error);
            if ((string)buildFreshness["status"]! == "checking") { buildFreshness["status"] = "failed"; buildFreshness["error"] = failure; }
            if ((string)setup["status"]! != "passed") { setup["status"] = "failed"; setup["error"] = failure; }
            Console.Error.WriteLine("CLASSIC_TUTORIAL_LIVE_FAILED: " + failure);
        }
        finally
        {
            // Cleanup has a fresh bounded budget even when gameplay/setup was
            // cancelled. Every cleanup error is retained instead of hiding the
            // original case failure or preventing the final report.
            cleanup["status"] = "running";
            using var cleanupDeadline = new CancellationTokenSource(TimeSpan.FromSeconds(25));
            bool stopped = false;
            try { await Stop(cleanupDeadline.Token); stopped = true; cleanup["server"] = "stopped"; }
            catch (Exception error) { cleanup["server"] = "failed"; cleanupErrors.Add(Error(error)); }
            var schemaCleanup = new List<Dictionary<string, object?>>();
            foreach (string schema in attemptedSchemas)
            {
                var outcome = new Dictionary<string, object?> { ["schema"] = schema, ["status"] = "not-run" }; schemaCleanup.Add(outcome);
                try
                {
                    Require(schema == OwnedSchema("normal", suffix) || schema == OwnedSchema("optional", suffix), "Cleanup received an unowned schema name.");
                    Require(stopped, "Schema cleanup requires the owned server to have stopped.");
                    await using var check = admin!.CreateCommand("SELECT pg_catalog.obj_description(oid, 'pg_namespace') FROM pg_catalog.pg_namespace WHERE nspname=$1");
                    check.CommandTimeout = 5; check.Parameters.AddWithValue(schema);
                    object? marker = await check.ExecuteScalarAsync(cleanupDeadline.Token);
                    if (marker is null) { outcome["status"] = "not-created-or-already-absent"; continue; }
                    // The transactional marker resolves an uncertain CREATE/COMMIT
                    // acknowledgement. A pre-existing colliding schema is never
                    // adopted or deleted, even though its name matches this run.
                    Require(marker is string tag && tag == ownership, "An unmarked/colliding schema was preserved; ownership could not be proved.");
                    createdSchemas.Add(schema);
                    await using var drop = admin.CreateCommand("DROP SCHEMA \"" + schema + "\" CASCADE"); drop.CommandTimeout = 5;
                    await drop.ExecuteNonQueryAsync(cleanupDeadline.Token); removedSchemas.Add(schema); outcome["status"] = "removed-owned-schema";
                }
                catch (Exception error) { outcome["status"] = "failed"; outcome["error"] = Error(error); cleanupErrors.Add(Error(error)); }
            }
            if (admin is not null)
            {
                try { await admin.DisposeAsync().AsTask().WaitAsync(TimeSpan.FromSeconds(3)); }
                catch (Exception error) { cleanupErrors.Add(Error(error)); }
            }
            cleanup["schemas"] = schemaCleanup; cleanup["errors"] = cleanupErrors;
            cleanup["status"] = cleanupErrors.Count == 0 ? "passed" : "failed";
            if (cleanupErrors.Count > 0) code = 1;
            try
            {
                await File.WriteAllTextAsync(Within(root, Path.Combine(evidence, "results.json")), Json(new { schema = 1, sourceSha = Environment.GetEnvironmentVariable("GITHUB_SHA") ?? "local-unverified",
                    status = code == 0 ? "passed" : "failed", failure, setup, results, cleanup, buildFreshness, launches = launchesEvidence,
                    sourceToAssemblyCorrespondenceProved = false, localDeliveryAccepted = false,
                    provenance = Environment.GetEnvironmentVariable("GITHUB_SHA") is null ? "local-unverified" : "external-exact-CI-checkout-and-build-proof-required",
                    schemas = new[] { normalSchema, optionalSchema }, createdSchemas = createdSchemas.Order().ToArray(), removedSchemas = removedSchemas.Order().ToArray(),
                    credentialsRetained = cleanupErrors.Count == 0 ? (bool?)false : null, publicEndpointOpened, nativeExecuted = false, humanPlayApproved = false, wholeGameComplete = false,
                    unrun = new[] { "native optional live UI", "tutorial fountain action", "tutorial rat/loot", "campfire construction", "art/audio/GPU acceptance" } }));
            }
            catch (Exception error) { code = 1; Console.Error.WriteLine("CLASSIC_TUTORIAL_LIVE_REPORT_FAILED: " + Error(error)); }
            Console.WriteLine("CLASSIC_TUTORIAL_LIVE_PROBE: " + (code == 0 ? "passed" : "failed") + "; evidence directory=" + evidence
                + "; modification-time/hash guards do not prove compilation correspondence; exact CI checkout/build proof is separate.");
        }
        return code;
    }

    private static async Task Gather(WireClient wire, Catalog data, string template, string item, int count, CancellationToken cancel)
    {
        var node = wire.Latest.Nodes.First(x => x.Template == template); var zone = data.Zone(wire.Self.Zone);
        var approach = new Point[] { new(1, 0), new(-1, 0), new(0, 1), new(0, -1) }
            .Select(direction => new { Facing = direction, Adjacent = node.Position.Add(direction.Scale(-1)), Entry = node.Position.Add(direction.Scale(-2)) })
            .Where(option => WorldMap.Fits(zone, option.Adjacent) && WorldMap.Fits(zone, option.Entry))
            .Select(option => new { option.Facing, option.Adjacent, option.Entry, Path = WorldMap.FindPath(zone, wire.Self.Position, option.Entry, 4096) })
            .Where(option => option.Path.Count > 0 || wire.Self.Position.Distance(option.Entry) <= .000001)
            .OrderBy(option => option.Path.Count).First();
        foreach (var at in approach.Path)
            await wire.Step(GridMovementRules.Cardinal(wire.Self.Position.Direction(at)), cancel);
        // Finish an accepted grid step on the adjacent tile, facing the resource.
        // Never step onto the resource or patch authoritative position/facing.
        await wire.Step(approach.Facing, cancel);
        Require(ClassicTutorialContent.FacingAdjacent(wire.Self, node.Position), "Resource approach did not establish accepted adjacency/facing.");
        while (Items.Count(wire.Self, item) < count)
        {
            await wire.State(x => x.Nodes.First(n => n.Id == node.Id).ReadyAt <= x.Time && x.Self.Cooldowns.GetValueOrDefault("gather") <= x.Time, cancel);
            int before = Items.Count(wire.Self, item);
            var result = await wire.Act(new GameCommand { Kind = "gather", Target = node.Id }, cancel); Require(result.Ok, "Authoritative tutorial gathering was refused.");
            await wire.State(x => Items.Count(x.Self, item) > before, cancel);
        }
    }

    private sealed class WireClient(ClientWebSocket socket, string address, string sessionToken, string characterId) : IAsyncDisposable
    {
        public Snapshot Latest { get; private set; } = null!;
        public Character Self => Latest.Self;
        public static async Task<WireClient> Connect(string address, string token, string character, CancellationToken cancel)
        {
            var uri = new UriBuilder(address + "/play") { Scheme = "ws" };
            Require(uri.Uri.IsLoopback && Guid.TryParseExact(character, "N", out _), "Fixture connection requires a loopback endpoint and valid character identifier.");
            var socket = new ClientWebSocket();
            var client = new WireClient(socket, address, token, character);
            try
            {
                await socket.ConnectAsync(uri.Uri, cancel);
                await client.Send(new ConnectionHello { Token = token, CharacterId = character }, cancel); await client.State(_ => true, cancel); return client;
            }
            catch { await client.DisposeAsync(); throw; }
        }
        public async Task Disconnect(CancellationToken cancel)
        {
            using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(15) };
            http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", sessionToken);
            using var response = await http.PostAsync(address + "/api/disconnect/" + Uri.EscapeDataString(characterId), null, cancel);
            Require(response.StatusCode == HttpStatusCode.NoContent, "Authenticated fixture disconnect did not confirm completed detach/persistence: HTTP " + (int)response.StatusCode + ".");
            await DisposeAsync();
        }
        public async Task Send<T>(T value, CancellationToken token)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(Json(value)); Require(bytes.Length <= Wire.MaximumMessageBytes, "Probe command exceeds the protocol limit.");
            await socket.SendAsync(bytes.AsMemory(), WebSocketMessageType.Text, true, token);
        }
        private async Task<TransportPacket> Read(CancellationToken token)
        {
            using var bounded = CancellationTokenSource.CreateLinkedTokenSource(token); bounded.CancelAfter(TimeSpan.FromSeconds(20));
            byte[] buffer = new byte[16384]; using var stream = new MemoryStream();
            WebSocketReceiveResult result;
            do
            {
                result = await socket.ReceiveAsync(new ArraySegment<byte>(buffer), bounded.Token);
                Require(result.MessageType == WebSocketMessageType.Text, "Fixture transport closed or sent a non-text packet.");
                stream.Write(buffer, 0, result.Count); Require(stream.Length <= 1024 * 1024, "Fixture snapshot exceeds the bounded receive limit.");
            } while (!result.EndOfMessage);
            var packet = JsonSerializer.Deserialize<TransportPacket>(stream.ToArray(), Wire.Json) ?? throw new InvalidOperationException("Empty fixture packet.");
            if (packet.Snapshot is { } snapshot) Latest = snapshot;
            Require(packet.Kind != "error", "Fixture server rejected its session."); return packet;
        }
        public async Task State(Func<Snapshot, bool> condition, CancellationToken token)
        {
            var clock = Stopwatch.StartNew();
            while (clock.Elapsed < TimeSpan.FromSeconds(20))
            {
                await Read(token); if (Latest is not null && condition(Latest)) return;
            }
            throw new TimeoutException("Authoritative fixture state did not arrive.");
        }
        public async Task<CommandResult> Act(GameCommand command, CancellationToken token)
        {
            command.Sequence = Self.LastAction + 1; return await Replay(command, token);
        }
        public async Task<CommandResult> Replay(GameCommand command, CancellationToken token)
        {
            await Send(command, token);
            var clock = Stopwatch.StartNew();
            while (clock.Elapsed < TimeSpan.FromSeconds(20)) { var packet = await Read(token); if (packet.Result?.RequestId == command.RequestId) return packet.Result; }
            throw new TimeoutException("The fixture command receipt did not arrive.");
        }
        public async Task Step(Point direction, CancellationToken token)
        {
            var next = GridMovementRules.Next(Self.Position, direction);
            await Send(new GameCommand { Kind = "move", Arg = GridMovementRules.Step, X = direction.X, Y = direction.Y }, token);
            await State(x => x.Self.Position.Distance(next) <= .000001, token);
        }
        public ValueTask DisposeAsync() { socket.Abort(); socket.Dispose(); return ValueTask.CompletedTask; }
    }
}
