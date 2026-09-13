using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;
using Kairnfall.Server;
using Npgsql;

const string Usage="Usage: Kairnfall.Operations <backup|verify|restore> <dump-path>. Set KAIRNFALL_DB in the environment; never pass credentials on the command line.";
var json=new JsonSerializerOptions(JsonSerializerDefaults.Web){WriteIndented=true};
using var timeout=new CancellationTokenSource(TimeSpan.FromMinutes(15));
Console.CancelKeyPress+=(_,eventArgs)=>{ eventArgs.Cancel=true; timeout.Cancel(); };
try
{
    if(args.Length!=2) throw new ArgumentException(Usage);
    string command=args[0].ToLowerInvariant();
    string dumpPath=Path.GetFullPath(args[1]);
    if(command=="verify")
    {
        var metadata=await VerifyBackupAsync(dumpPath,timeout.Token);
        Console.WriteLine($"BACKUP_VERIFY_OK: schema={metadata.DatabaseSchemaVersion}; revision={metadata.RealmRevision?.ToString()??"none"}; accounts={metadata.Accounts}; bytes={metadata.Bytes}; sha256={metadata.Sha256}");
        return 0;
    }
    string connectionString=Environment.GetEnvironmentVariable("KAIRNFALL_DB")??throw new InvalidOperationException("Set KAIRNFALL_DB in the process environment. Credentials are intentionally not accepted as command arguments.");
    var settings=new NpgsqlConnectionStringBuilder(connectionString);
    if(string.IsNullOrWhiteSpace(settings.Host)||string.IsNullOrWhiteSpace(settings.Database)) throw new InvalidOperationException("KAIRNFALL_DB must identify a PostgreSQL host and database.");
    if(command=="backup") await BackupAsync(settings,dumpPath,timeout.Token);
    else if(command=="restore") await RestoreAsync(settings,dumpPath,timeout.Token);
    else throw new ArgumentException(Usage);
    return 0;
}
catch(OperationCanceledException)
{
    Console.Error.WriteLine("OPERATIONS_FAIL: operation cancelled or timed out.");
    return 2;
}
catch(Exception error)
{
    Console.Error.WriteLine("OPERATIONS_FAIL: "+error.Message);
    return 1;
}

async Task BackupAsync(NpgsqlConnectionStringBuilder settings,string dumpPath,CancellationToken cancel)
{
    string metadataPath=MetadataPath(dumpPath),checksumPath=ChecksumPath(dumpPath);
    if(File.Exists(dumpPath)||File.Exists(metadataPath)||File.Exists(checksumPath))
        throw new IOException("Backup output already exists. Choose a new path; existing backups are never overwritten implicitly.");
    Directory.CreateDirectory(Path.GetDirectoryName(dumpPath)!);
    await using var source=NpgsqlDataSource.Create(settings.ConnectionString);
    var state=await ReadStateAsync(source,cancel);
    await RunDumpAsync(settings,dumpPath,cancel);
    string hash=HashFile(dumpPath); long bytes=new FileInfo(dumpPath).Length;
    var metadata=new BackupMetadata(1,RealmStore.CurrentSchemaVersion,state.RealmRevision,state.Accounts,state.Sessions,bytes,hash);
    await File.WriteAllTextAsync(metadataPath,JsonSerializer.Serialize(metadata,json)+Environment.NewLine,cancel);
    await File.WriteAllTextAsync(checksumPath,$"{hash}  {Path.GetFileName(dumpPath)}{Environment.NewLine}",cancel);
    Console.WriteLine($"BACKUP_OK: schema={metadata.DatabaseSchemaVersion}; revision={metadata.RealmRevision?.ToString()??"none"}; accounts={metadata.Accounts}; sessions={metadata.Sessions}; bytes={bytes}; sha256={hash}");
}

async Task RestoreAsync(NpgsqlConnectionStringBuilder settings,string dumpPath,CancellationToken cancel)
{
    var metadata=await VerifyBackupAsync(dumpPath,cancel);
    await using var target=NpgsqlDataSource.Create(settings.ConnectionString);
    await EnsureEmptyRestoreTargetAsync(target,cancel);
    await RunRestoreAsync(settings,dumpPath,cancel);
    var restored=await ReadStateAsync(target,cancel);
    if(restored.RealmRevision!=metadata.RealmRevision||restored.Accounts!=metadata.Accounts||restored.Sessions!=metadata.Sessions)
        throw new InvalidDataException($"Restored database does not match backup metadata. revision={restored.RealmRevision?.ToString()??"none"}/{metadata.RealmRevision?.ToString()??"none"}; accounts={restored.Accounts}/{metadata.Accounts}; sessions={restored.Sessions}/{metadata.Sessions}.");
    Console.WriteLine($"RESTORE_OK: schema={metadata.DatabaseSchemaVersion}; revision={restored.RealmRevision?.ToString()??"none"}; accounts={restored.Accounts}; sessions={restored.Sessions}; sha256={metadata.Sha256}");
}

async Task<BackupMetadata> VerifyBackupAsync(string dumpPath,CancellationToken cancel)
{
    if(!File.Exists(dumpPath)) throw new FileNotFoundException("Backup dump is missing.",dumpPath);
    string metadataPath=MetadataPath(dumpPath),checksumPath=ChecksumPath(dumpPath);
    if(!File.Exists(metadataPath)||!File.Exists(checksumPath)) throw new FileNotFoundException("Backup metadata or SHA-256 sidecar is missing.");
    var metadata=JsonSerializer.Deserialize<BackupMetadata>(await File.ReadAllTextAsync(metadataPath,cancel),json)??throw new InvalidDataException("Backup metadata is empty.");
    if(metadata.Schema!=1||metadata.DatabaseSchemaVersion!=RealmStore.CurrentSchemaVersion) throw new InvalidDataException("Backup metadata uses an unsupported schema version.");
    string actual=HashFile(dumpPath); long bytes=new FileInfo(dumpPath).Length;
    if(!string.Equals(actual,metadata.Sha256,StringComparison.OrdinalIgnoreCase)||bytes!=metadata.Bytes) throw new InvalidDataException("Backup bytes do not match recorded SHA-256 metadata.");
    string sidecar=(await File.ReadAllTextAsync(checksumPath,cancel)).Trim();
    string expected=$"{metadata.Sha256}  {Path.GetFileName(dumpPath)}";
    if(!string.Equals(sidecar,expected,StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Backup SHA-256 sidecar does not match metadata and filename.");
    return metadata;
}

async Task<DatabaseState> ReadStateAsync(NpgsqlDataSource source,CancellationToken cancel)
{
    await using var connection=await source.OpenConnectionAsync(cancel);
    await using(var exists=new NpgsqlCommand("SELECT to_regclass('public.schema_versions') IS NOT NULL",connection))
        if(await exists.ExecuteScalarAsync(cancel) is not true) throw new InvalidDataException("Database has no Kairnfall schema_versions table.");
    var versions=new List<int>();
    await using(var versionsCommand=new NpgsqlCommand("SELECT version FROM schema_versions ORDER BY version",connection))
    await using(var reader=await versionsCommand.ExecuteReaderAsync(cancel))
        while(await reader.ReadAsync(cancel)) versions.Add(reader.GetInt32(0));
    if(!RealmStore.IsSupportedSchemaHistory(versions)) throw new InvalidDataException($"Database schema history [{string.Join(',',versions)}] is not supported by this server.");
    long? revision=null;
    await using(var revisionCommand=new NpgsqlCommand("SELECT revision FROM realm_snapshots WHERE id=1",connection))
    {
        var value=await revisionCommand.ExecuteScalarAsync(cancel);
        if(value is long number) revision=number;
    }
    long accounts;
    await using(var command=new NpgsqlCommand("SELECT count(*) FROM accounts",connection)) accounts=Convert.ToInt64(await command.ExecuteScalarAsync(cancel),CultureInfo.InvariantCulture);
    long sessions;
    await using(var command=new NpgsqlCommand("SELECT count(*) FROM sessions",connection)) sessions=Convert.ToInt64(await command.ExecuteScalarAsync(cancel),CultureInfo.InvariantCulture);
    return new(revision,accounts,sessions);
}

async Task EnsureEmptyRestoreTargetAsync(NpgsqlDataSource target,CancellationToken cancel)
{
    await using var connection=await target.OpenConnectionAsync(cancel);
    await using var command=new NpgsqlCommand("SELECT count(*) FROM pg_tables WHERE schemaname='public'",connection);
    long tables=Convert.ToInt64(await command.ExecuteScalarAsync(cancel),CultureInfo.InvariantCulture);
    if(tables!=0) throw new InvalidOperationException("Restore target is not empty. Restore into a fresh database and cut over explicitly; this tool will not overwrite a live realm.");
}

async Task RunDumpAsync(NpgsqlConnectionStringBuilder settings,string path,CancellationToken cancel)
{
    string executable=Environment.GetEnvironmentVariable("KAIRNFALL_PG_DUMP")??"pg_dump";
    var start=PgStart(executable,settings);
    start.RedirectStandardOutput=true; start.RedirectStandardError=true;
    start.ArgumentList.Add("--format=custom"); start.ArgumentList.Add("--no-owner"); start.ArgumentList.Add("--no-privileges");
    using var process=Process.Start(start)??throw new InvalidOperationException("Could not start pg_dump. Install a PostgreSQL client matching the server major version or set KAIRNFALL_PG_DUMP.");
    var stderrTask=process.StandardError.ReadToEndAsync();
    try
    {
        await using(var output=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None,81920,true))
            await process.StandardOutput.BaseStream.CopyToAsync(output,cancel);
        await process.WaitForExitAsync(cancel); string stderr=await stderrTask;
        if(process.ExitCode!=0) throw new InvalidOperationException($"pg_dump failed with exit code {process.ExitCode}: {stderr.Trim()}");
    }
    catch
    {
        try { if(File.Exists(path)) File.Delete(path); } catch(IOException) { }
        throw;
    }
}

async Task RunRestoreAsync(NpgsqlConnectionStringBuilder settings,string path,CancellationToken cancel)
{
    string executable=Environment.GetEnvironmentVariable("KAIRNFALL_PG_RESTORE")??"pg_restore";
    var start=PgStart(executable,settings);
    start.RedirectStandardInput=true; start.RedirectStandardOutput=true; start.RedirectStandardError=true;
    start.ArgumentList.Add("--format=custom"); start.ArgumentList.Add("--exit-on-error"); start.ArgumentList.Add("--no-owner"); start.ArgumentList.Add("--no-privileges"); start.ArgumentList.Add("--dbname"); start.ArgumentList.Add(settings.Database!);
    using var process=Process.Start(start)??throw new InvalidOperationException("Could not start pg_restore. Install a PostgreSQL client matching the server major version or set KAIRNFALL_PG_RESTORE.");
    var stdoutTask=process.StandardOutput.ReadToEndAsync(); var stderrTask=process.StandardError.ReadToEndAsync();
    await using(var input=File.OpenRead(path)) await input.CopyToAsync(process.StandardInput.BaseStream,cancel);
    process.StandardInput.Close();
    await process.WaitForExitAsync(cancel); string stdout=await stdoutTask,stderr=await stderrTask;
    if(process.ExitCode!=0) throw new InvalidOperationException($"pg_restore failed with exit code {process.ExitCode}: {(stderr+Environment.NewLine+stdout).Trim()}");
}

ProcessStartInfo PgStart(string executable,NpgsqlConnectionStringBuilder settings)
{
    var start=new ProcessStartInfo(executable){UseShellExecute=false};
    start.Environment["PGHOST"]=settings.Host;
    start.Environment["PGPORT"]=settings.Port.ToString(CultureInfo.InvariantCulture);
    start.Environment["PGDATABASE"]=settings.Database;
    if(!string.IsNullOrWhiteSpace(settings.Username)) start.Environment["PGUSER"]=settings.Username;
    if(!string.IsNullOrEmpty(settings.Password)) start.Environment["PGPASSWORD"]=settings.Password;
    start.Environment["PGCONNECT_TIMEOUT"]=Math.Max(1,settings.Timeout).ToString(CultureInfo.InvariantCulture);
    string ssl=settings.SslMode.ToString().ToLowerInvariant() switch {"verifyca"=>"verify-ca","verifyfull"=>"verify-full",var value=>value};
    start.Environment["PGSSLMODE"]=ssl;
    return start;
}

string HashFile(string path)
{
    using var stream=File.OpenRead(path);
    return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
}
string MetadataPath(string path)=>path+".json";
string ChecksumPath(string path)=>path+".sha256";

internal sealed record BackupMetadata(int Schema,int DatabaseSchemaVersion,long? RealmRevision,long Accounts,long Sessions,long Bytes,string Sha256);
internal sealed record DatabaseState(long? RealmRevision,long Accounts,long Sessions);
