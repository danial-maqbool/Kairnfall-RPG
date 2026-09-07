using System.Data;
using System.Text.Json;
using Kairnfall.Core;
using Npgsql;
using NpgsqlTypes;

namespace Kairnfall.Server;

public sealed class RealmStore(NpgsqlDataSource source) : IAsyncDisposable
{
    private NpgsqlConnection? lease;
    private const long RealmLock=0x4B4149524E46414C;
    public async Task InitializeAsync(CancellationToken cancel)
    {
        await using var connection=await source.OpenConnectionAsync(cancel);
        await using var transaction=await connection.BeginTransactionAsync(cancel);
        const string schema="""
            CREATE TABLE IF NOT EXISTS schema_versions (
              version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
            CREATE TABLE IF NOT EXISTS accounts (
              id uuid PRIMARY KEY, username varchar(24) NOT NULL UNIQUE,
              password_hash bytea NOT NULL, password_salt bytea NOT NULL,
              password_iterations integer NOT NULL CHECK(password_iterations >= 600000),
              created_at timestamptz NOT NULL DEFAULT now());
            CREATE TABLE IF NOT EXISTS sessions (
              token_hash bytea PRIMARY KEY, account_id uuid NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
              expires_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
            CREATE INDEX IF NOT EXISTS sessions_account_idx ON sessions(account_id);
            CREATE INDEX IF NOT EXISTS sessions_expiry_idx ON sessions(expires_at);
            CREATE TABLE IF NOT EXISTS realm_snapshots (
              id integer PRIMARY KEY CHECK(id=1), revision bigint NOT NULL CHECK(revision>=0),
              format_version integer NOT NULL, payload jsonb NOT NULL,
              updated_at timestamptz NOT NULL DEFAULT now());
            INSERT INTO schema_versions(version) VALUES(1) ON CONFLICT DO NOTHING;
            """;
        await using(var cmd=new NpgsqlCommand(schema,connection,transaction)) await cmd.ExecuteNonQueryAsync(cancel);
        await transaction.CommitAsync(cancel);
        lease=await source.OpenConnectionAsync(cancel);
        await using var acquire=new NpgsqlCommand("SELECT pg_try_advisory_lock($1)",lease);
        acquire.Parameters.AddWithValue(RealmLock);
        if(await acquire.ExecuteScalarAsync(cancel) is not true)
            throw new InvalidOperationException("Another server already owns this realm database. Run one authoritative process per realm.");
    }
    public async Task<RealmSave?> LoadAsync(CancellationToken cancel)
    {
        await using var cmd=source.CreateCommand("SELECT revision, format_version, payload::text FROM realm_snapshots WHERE id=1");
        await using var reader=await cmd.ExecuteReaderAsync(cancel);
        if(!await reader.ReadAsync(cancel)) return null;
        if(reader.GetInt32(1)!=1) throw new InvalidDataException("The realm database uses an unsupported save format.");
        var save=JsonSerializer.Deserialize<RealmSave>(reader.GetString(2),Wire.Json)??throw new InvalidDataException("The saved realm is empty.");
        if(save.FormatVersion!=1||save.State.Revision!=reader.GetInt64(0)) throw new InvalidDataException("The realm revision does not match its stored payload.");
        return save;
    }
    public async Task SaveAsync(RealmEngine engine,CancellationToken cancel)
    {
        if(lease is null||lease.State!=ConnectionState.Open) throw new InvalidOperationException("The realm writer lease was lost.");
        await using(var heartbeat=new NpgsqlCommand("SELECT 1",lease)) await heartbeat.ExecuteScalarAsync(cancel);
        long previous=engine.State.Revision;
        long next=checked(previous+1);
        engine.State.Revision=next;
        string payload;
        try { payload=JsonSerializer.Serialize(new RealmSave{State=engine.State,Loot=engine.Loot},Wire.Json); }
        finally { engine.State.Revision=previous; }
        await using var connection=await source.OpenConnectionAsync(cancel);
        await using var transaction=await connection.BeginTransactionAsync(IsolationLevel.Serializable,cancel);
        const string sql="""
            INSERT INTO realm_snapshots(id,revision,format_version,payload)
            VALUES(1,$1,1,$2)
            ON CONFLICT(id) DO UPDATE SET revision=EXCLUDED.revision,
              format_version=EXCLUDED.format_version,payload=EXCLUDED.payload,updated_at=now()
            WHERE realm_snapshots.revision=$3
            RETURNING revision;
            """;
        await using var command=new NpgsqlCommand(sql,connection,transaction);
        command.Parameters.AddWithValue(next);
        command.Parameters.AddWithValue(NpgsqlDbType.Jsonb,payload);
        command.Parameters.AddWithValue(previous);
        var updated=await command.ExecuteScalarAsync(cancel);
        if(updated is not long revision||revision!=next) throw new DBConcurrencyException("The realm revision changed outside the authoritative writer.");
        await transaction.CommitAsync(cancel);
        engine.State.Revision=next;
        engine.MarkSaved();
    }
    public async ValueTask DisposeAsync()
    {
        if(lease is not null) { await lease.DisposeAsync(); lease=null; }
    }
}
