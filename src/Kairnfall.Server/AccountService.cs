using System.Collections.Concurrent;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Kairnfall.Core;

namespace Kairnfall.Server;

public sealed record Credentials(string Login,string Password);
public sealed record LoginResult(string Token,DateTimeOffset Expires,int Protocol,string Login);
public sealed record Session(string Account,string Login,DateTimeOffset Expires);

public sealed class AccountService(RealmStore store)
{
    public const int PasswordIterations=600_000;
    private readonly ConcurrentDictionary<string,Session> sessions=new(StringComparer.Ordinal);
    private static readonly byte[] DummySalt=RandomNumberGenerator.GetBytes(24);
    private static readonly byte[] DummyHash=RandomNumberGenerator.GetBytes(32);

    public static string NormalizeLogin(string? value)
    {
        if(value is null||!Regex.IsMatch(value,@"\A[A-Za-z][A-Za-z0-9_]{2,23}\z",RegexOptions.CultureInvariant))
            throw new RuleException("Use 3–24 letters, digits, or underscores. Start the account name with a letter.");
        return value.ToLowerInvariant();
    }
    private static byte[] HashPassword(string password,byte[] salt,int iterations)
        =>Rfc2898DeriveBytes.Pbkdf2(password,salt,iterations,HashAlgorithmName.SHA256,32);
    private static string TokenHash(string token)=>Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(token)));

    public async Task<LoginResult> RegisterAsync(Credentials input,CancellationToken cancellationToken)
    {
        var login=NormalizeLogin(input.Login);
        if(input.Password is null||input.Password.Length is <12 or >128)
            throw new RuleException("Use a password with 12–128 characters.");
        byte[] salt=RandomNumberGenerator.GetBytes(24);
        var hash=await Task.Run(()=>HashPassword(input.Password,salt,PasswordIterations),cancellationToken);
        var account=new AccountRecord(Guid.NewGuid().ToString("N"),login,salt,hash,PasswordIterations);
        await store.CreateAccountAsync(account,cancellationToken);
        return CreateSession(account);
    }

    public async Task<LoginResult> LoginAsync(Credentials input,CancellationToken cancellationToken)
    {
        string login=NormalizeLogin(input.Login);
        if(input.Password is null||input.Password.Length>128)
            throw new RuleException("The account name or password is incorrect.");
        var account=await store.FindAccountAsync(login,cancellationToken);
        byte[] calculated=await Task.Run(()=>HashPassword(input.Password,account?.Salt??DummySalt,account?.Iterations??PasswordIterations),cancellationToken);
        bool matches=CryptographicOperations.FixedTimeEquals(calculated,account?.PasswordHash??DummyHash);
        CryptographicOperations.ZeroMemory(calculated);
        if(!matches||account is null) throw new RuleException("The account name or password is incorrect.");
        return CreateSession(account);
    }

    private LoginResult CreateSession(AccountRecord account)
    {
        foreach(var entry in sessions)
            if(entry.Value.Expires<=DateTimeOffset.UtcNow||entry.Value.Account==account.Id)
                sessions.TryRemove(entry.Key,out _);
        string token=Convert.ToBase64String(RandomNumberGenerator.GetBytes(32)).TrimEnd('=').Replace('+','-').Replace('/','_');
        var expiry=DateTimeOffset.UtcNow.AddHours(8);
        sessions[TokenHash(token)]=new(account.Id,account.Login,expiry);
        return new(token,expiry,Wire.Version,account.Login);
    }

    public Session? Authenticate(string? token)
    {
        if(string.IsNullOrEmpty(token)||token.Length>128) return null;
        string key=TokenHash(token);
        if(!sessions.TryGetValue(key,out var session)) return null;
        if(session.Expires<=DateTimeOffset.UtcNow) { sessions.TryRemove(key,out _); return null; }
        return session;
    }

    public void Logout(string? token)
    {
        if(!string.IsNullOrEmpty(token)&&token.Length<=128) sessions.TryRemove(TokenHash(token),out _);
    }

    public static string? Bearer(HttpContext context)
    {
        string value=context.Request.Headers.Authorization.ToString();
        return value.StartsWith("Bearer ",StringComparison.Ordinal)?value[7..]:null;
    }
}
