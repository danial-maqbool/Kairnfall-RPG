using System.Security.Cryptography;
using System.Text.RegularExpressions;
using Kairnfall.Core;
using Npgsql;

namespace Kairnfall.Server;

public sealed record AccountSession(string AccountId,string TokenFingerprint,DateTimeOffset Expires);

public sealed class AccountStore(NpgsqlDataSource source)
{
    public const int PasswordIterations=600000;
    private static readonly byte[] DummySalt=RandomNumberGenerator.GetBytes(16);
    private static readonly byte[] DummyHash=RandomNumberGenerator.GetBytes(32);
    private static byte[] HashPassword(string password,byte[] salt,int iterations)=>Rfc2898DeriveBytes.Pbkdf2(password,salt,iterations,HashAlgorithmName.SHA256,32);
    private static string Normalize(string? username)
    {
        if(username is null||!Regex.IsMatch(username,@"\A[A-Za-z][A-Za-z0-9_]{2,23}\z")) throw new RuleException("Use an account name with 3–24 letters, digits, or underscores.");
        return username.ToLowerInvariant();
    }
    private static void CheckPassword(string? password)
    {
        if(password is null||password.Length is <12 or >128||password.Any(char.IsControl)) throw new RuleException("Use a password with 12–128 printable characters.");
    }
    public async Task<LoginResponse> RegisterAsync(LoginRequest request,CancellationToken cancel)
    {
        string username=Normalize(request.Username); CheckPassword(request.Password);
        var salt=RandomNumberGenerator.GetBytes(16); var hash=HashPassword(request.Password,salt,PasswordIterations); var id=Guid.NewGuid();
        await using var connection=await source.OpenConnectionAsync(cancel);
        await using var transaction=await connection.BeginTransactionAsync(cancel);
        try
        {
            await using(var command=new NpgsqlCommand("INSERT INTO accounts(id,username,password_hash,password_salt,password_iterations) VALUES($1,$2,$3,$4,$5)",connection,transaction))
            {
                command.Parameters.AddWithValue(id); command.Parameters.AddWithValue(username); command.Parameters.AddWithValue(hash); command.Parameters.AddWithValue(salt); command.Parameters.AddWithValue(PasswordIterations);
                await command.ExecuteNonQueryAsync(cancel);
            }
            var result=await NewSessionAsync(id,connection,transaction,cancel);
            await transaction.CommitAsync(cancel); return result;
        }
        catch(PostgresException e) when(e.SqlState==PostgresErrorCodes.UniqueViolation)
        { throw new RuleException("That account name is not available."); }
        finally { CryptographicOperations.ZeroMemory(hash); }
    }
    public async Task<LoginResponse> LoginAsync(LoginRequest request,CancellationToken cancel)
    {
        string username=Normalize(request.Username); CheckPassword(request.Password);
        Guid account=Guid.Empty; byte[] hash=DummyHash,salt=DummySalt; int iterations=PasswordIterations;
        await using(var command=source.CreateCommand("SELECT id,password_hash,password_salt,password_iterations FROM accounts WHERE username=$1"))
        {
            command.Parameters.AddWithValue(username);
            await using var reader=await command.ExecuteReaderAsync(cancel);
            if(await reader.ReadAsync(cancel)) { account=reader.GetGuid(0); hash=reader.GetFieldValue<byte[]>(1); salt=reader.GetFieldValue<byte[]>(2); iterations=reader.GetInt32(3); }
        }
        var supplied=HashPassword(request.Password,salt,iterations);
        bool valid=CryptographicOperations.FixedTimeEquals(hash,supplied)&&account!=Guid.Empty;
        CryptographicOperations.ZeroMemory(supplied);
        if(!valid) throw new RuleException("The account name or password is incorrect.");
        await using var connection=await source.OpenConnectionAsync(cancel);
        await using var transaction=await connection.BeginTransactionAsync(cancel);
        await using(var cleanup=new NpgsqlCommand("DELETE FROM sessions WHERE account_id=$1 OR expires_at<now()",connection,transaction))
        { cleanup.Parameters.AddWithValue(account); await cleanup.ExecuteNonQueryAsync(cancel); }
        var result=await NewSessionAsync(account,connection,transaction,cancel);
        await transaction.CommitAsync(cancel); return result;
    }
    private static async Task<LoginResponse> NewSessionAsync(Guid account,NpgsqlConnection connection,NpgsqlTransaction transaction,CancellationToken cancel)
    {
        var bytes=RandomNumberGenerator.GetBytes(32);
        string token=Convert.ToBase64String(bytes).TrimEnd('=').Replace('+','-').Replace('/','_');
        var fingerprint=SHA256.HashData(bytes); CryptographicOperations.ZeroMemory(bytes);
        var expiry=DateTimeOffset.UtcNow.AddHours(12);
        await using var command=new NpgsqlCommand("INSERT INTO sessions(token_hash,account_id,expires_at) VALUES($1,$2,$3)",connection,transaction);
        command.Parameters.AddWithValue(fingerprint); command.Parameters.AddWithValue(account); command.Parameters.AddWithValue(expiry);
        await command.ExecuteNonQueryAsync(cancel);
        return new(){Token=token,AccountId=account.ToString("N"),Expires=expiry};
    }
    public static byte[]? Fingerprint(string? token)
    {
        if(token is null||token.Length!=43||!Regex.IsMatch(token,@"\A[A-Za-z0-9_-]{43}\z")) return null;
        try { return SHA256.HashData(Convert.FromBase64String(token.Replace('-','+').Replace('_','/')+"=")); }
        catch(FormatException) { return null; }
    }
    public async Task<AccountSession?> AuthenticateAsync(string? token,CancellationToken cancel)
    {
        var fingerprint=Fingerprint(token); if(fingerprint is null) return null;
        await using var command=source.CreateCommand("SELECT account_id,expires_at FROM sessions WHERE token_hash=$1 AND expires_at>now()");
        command.Parameters.AddWithValue(fingerprint);
        await using var reader=await command.ExecuteReaderAsync(cancel);
        if(!await reader.ReadAsync(cancel)) return null;
        return new(reader.GetGuid(0).ToString("N"),Convert.ToHexString(fingerprint),reader.GetFieldValue<DateTimeOffset>(1));
    }
    public async Task<bool> IsSessionValidAsync(AccountSession session,CancellationToken cancel)
    {
        if(session.Expires<=DateTimeOffset.UtcNow) return false;
        await using var command=source.CreateCommand("SELECT EXISTS(SELECT 1 FROM sessions WHERE token_hash=$1 AND expires_at>now())");
        command.Parameters.AddWithValue(Convert.FromHexString(session.TokenFingerprint));
        return await command.ExecuteScalarAsync(cancel) is true;
    }
    public async Task RevokeAsync(string token,CancellationToken cancel)
    {
        var fingerprint=Fingerprint(token); if(fingerprint is null) return;
        await using var command=source.CreateCommand("DELETE FROM sessions WHERE token_hash=$1"); command.Parameters.AddWithValue(fingerprint); await command.ExecuteNonQueryAsync(cancel);
    }
}
