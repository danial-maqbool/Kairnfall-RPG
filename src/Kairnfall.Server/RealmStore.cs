using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Kairnfall.Core;
using Npgsql;
using NpgsqlTypes;

namespace Kairnfall.Server;

public sealed class RealmDocument
{
    public int Format { get; set; } = 1;
    public RealmState State { get; set; } = new();
    public Dictionary<string,LootPile> Loot { get; set; } = [];
}

public sealed record AccountRecord(string Id,string Login,byte[] Salt,byte[] PasswordHash,int Iterations);

/// <summary>
/// PostgreSQL owns the durable revision. Only one live process may own a realm.
/// A successful action response must follow a successful SaveAsync call.
/// </summary>
public sealed class RealmStore : IAsyncDisposable
{
    private readonly NpgsqlDataSource source;
    private NpgsqlConnection? lease;
    private long revision;
    public long Revision => revision;

    public RealmStore(string connectionString)
    {
        if(string.IsNullOrWhiteSpace(connectionString))
            throw new InvalidOperationException("Set KAIRNFALL_DB to a PostgreSQL connection string. Do not commit credentials.");
        var settings=new NpgsqlConnectionStringBuilder(connectionString)
        {
            ApplicationName="Kairnfall Realm",
            Timeout=10,
            CommandTimeout=15,
            IncludeErrorDetail=false
        };
        source=NpgsqlDataSource.Create(settings.ConnectionString);
    }

    public async Task InitializeAsync(CancellationToken cancellationToken)
    {
        lease=await source.OpenConnectionAsync(cancellationToken);
        await using(var claim=new NpgsqlCommand("SELECT pg_try_advisory_lock(721983001)",lease))
        {
            if(await claim.ExecuteScalarAsync(cancellationToken) is not true)
                throw new InvalidOperationException("Another server already owns this realm database.");
        }
        const string migration="""
            CREATE TABLE IF NOT EXISTS kairnfall_migrations (
                version integer PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS kairnfall_accounts (
                id text PRIMARY KEY,
                login text NOT NULL UNIQUE,
                salt bytea NOT NULL,
                password_hash bytea NOT NULL,
                iterations integer NOT NULL CHECK (iterations >= 600000),
                created_at timestamptz NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS kairnfall_realms (
                id integer PRIMARY KEY CHECK (id = 1),
                revision bigint NOT NULL CHECK (revision >= 0),
                payload jsonb NOT NULL,
                updated_at timestamptz NOT NULL DEFAULT now()
            );
            INSERT INTO kairnfall_migrations(version) VALUES (1) ON CONFLICT DO NOTHING;
            """;
        await using var connection=await source.OpenConnectionAsync(cancellationToken);
        await using var transaction=await connection.BeginTransactionAsync(cancellationToken);
        await using var command=new NpgsqlCommand(migration,connection,transaction);
        await command.ExecuteNonQueryAsync(cancellationToken);
        await transaction.CommitAsync(cancellationToken);
    }

    public async Task<RealmDocument?> LoadAsync(CancellationToken cancellationToken)
    {
        await using var command=source.CreateCommand("SELECT revision, payload::text FROM kairnfall_realms WHERE id=1");
        await using var reader=await command.ExecuteReaderAsync(cancellationToken);
        if(!await reader.ReadAsync(cancellationToken)) { revision=0; return null; }
        revision=reader.GetInt64(0);
        var document=JsonSerializer.Deserialize<RealmDocument>(reader.GetString(1),Wire.Json)
            ??throw new InvalidDataException("The saved realm is empty.");
        if(document.Format!=1||document.State.Schema!=1)
            throw new InvalidDataException("Unsupported realm save format. Do not overwrite this database.");
        document.State.Revision=revision;
        return document;
    }

    public async Task SaveAsync(RealmEngine engine,CancellationToken cancellationToken)
    {
        if(lease is null||lease.State!=System.Data.ConnectionState.Open)
            throw new InvalidOperationException("The realm writer lease is not available.");
        long next=checked(revision+1);
        var document=new RealmDocument { State=engine.State,Loot=engine.Loot };
        long previousStateRevision=engine.State.Revision;
        engine.State.Revision=next;
        string payload;
        try { payload=JsonSerializer.Serialize(document,Wire.Json); }
        catch { engine.State.Revision=previousStateRevision; throw; }
        await using var connection=await source.OpenConnectionAsync(cancellationToken);
        await using var transaction=await connection.BeginTransactionAsync(System.Data.IsolationLevel.Serializable,cancellationToken);
        try
        {
            const string sql="""
                INSERT INTO kairnfall_realms(id,revision,payload) VALUES (1,@next,@payload)
                ON CONFLICT (id) DO UPDATE
                SET revision=@next, payload=@payload, updated_at=now()
                WHERE kairnfall_realms.revision=@previous;
                """;
            await using var command=new NpgsqlCommand(sql,connection,transaction);
            command.Parameters.AddWithValue("next",next);
            command.Parameters.AddWithValue("previous",revision);
            command.Parameters.AddWithValue("payload",NpgsqlDbType.Jsonb,payload);
            if(await command.ExecuteNonQueryAsync(cancellationToken)!=1)
                throw new InvalidOperationException("The durable realm revision changed. Refusing to overwrite another writer.");
            await transaction.CommitAsync(cancellationToken);
            revision=next;
            engine.MarkSaved();
        }
        catch
        {
            engine.State.Revision=previousStateRevision;
            throw;
        }
    }

    public async Task<AccountRecord?> FindAccountAsync(string login,CancellationToken cancellationToken)
    {
        await using var command=source.CreateCommand("SELECT id,login,salt,password_hash,iterations FROM kairnfall_accounts WHERE login=@login");
        command.Parameters.AddWithValue("login",login);
        await using var reader=await command.ExecuteReaderAsync(cancellationToken);
        return await reader.ReadAsync(cancellationToken)
            ?new AccountRecord(reader.GetString(0),reader.GetString(1),reader.GetFieldValue<byte[]>(2),reader.GetFieldValue<byte[]>(3),reader.GetInt32(4))
            :null;
    }

    public async Task CreateAccountAsync(AccountRecord account,CancellationToken cancellationToken)
    {
        await using var command=source.CreateCommand("INSERT INTO kairnfall_accounts(id,login,salt,password_hash,iterations) VALUES (@id,@login,@salt,@hash,@iterations)");
        command.Parameters.AddWithValue("id",account.Id);
        command.Parameters.AddWithValue("login",account.Login);
        command.Parameters.AddWithValue("salt",account.Salt);
        command.Parameters.AddWithValue("hash",account.PasswordHash);
        command.Parameters.AddWithValue("iterations",account.Iterations);
        try { await command.ExecuteNonQueryAsync(cancellationToken); }
        catch(PostgresException error) when(error.SqlState==PostgresErrorCodes.UniqueViolation)
        { throw new RuleException("That account name is unavailable."); }
    }

    public async ValueTask DisposeAsync()
    {
        if(lease is not null) await lease.DisposeAsync();
        await source.DisposeAsync();
    }
}
