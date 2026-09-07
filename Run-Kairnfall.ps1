# Start only this package's local server. Never remove the realm database volume.
[CmdletBinding()]
param([switch]$ServerOnly, [switch]$Stop)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$local = Join-Path $root '.local'
$pidFile = Join-Path $local 'server-process.json'
$serverExe = Join-Path $root 'server/Kairnfall.Server.exe'
$clientExe = Join-Path $root 'client/Kairnfall.exe'

function Invoke-Docker([string[]]$Arguments) {
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker failed with exit code $LASTEXITCODE." }
}
function Get-OwnedServer {
    if (-not (Test-Path -LiteralPath $pidFile)) { return $null }
    $record = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
    $process = Get-Process -Id $record.id -ErrorAction SilentlyContinue
    if ($null -eq $process) { return $null }
    if ($process.Path -ne $serverExe -or $process.StartTime.ToUniversalTime().ToString('o') -ne $record.started) {
        throw 'The recorded process no longer belongs to this game. It will not be stopped or reused.'
    }
    return $process
}

try {
    if ($Stop) {
        $owned = Get-OwnedServer
        if ($null -ne $owned) {
            # The server persists acknowledged actions before answering. Terminate only our recorded process.
            Stop-Process -Id $owned.Id -ErrorAction Stop
            Write-Host 'The local game server stopped. The persistent database was retained.'
        }
        if (Test-Path -LiteralPath $pidFile) { Remove-Item -LiteralPath $pidFile }
        return
    }
    if (-not (Test-Path -LiteralPath $serverExe)) { throw 'The Windows server package is missing. Extract the complete Windows test package, not the source archive.' }
    if (-not $ServerOnly -and -not (Test-Path -LiteralPath $clientExe)) { throw 'The Windows client package is missing. Extract the complete archive first.' }
    $null = Get-Command docker -ErrorAction Stop
    Invoke-Docker @('info', '--format', '{{.OSType}}')
    New-Item -ItemType Directory -Force -Path $local | Out-Null
    $envFile = Join-Path $local 'realm.env'
    if (-not (Test-Path -LiteralPath $envFile)) {
        $bytes = New-Object byte[] 32
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
        $password = [BitConverter]::ToString($bytes).Replace('-', '')
        [IO.File]::WriteAllText($envFile, "POSTGRES_PASSWORD=$password`n", [Text.UTF8Encoding]::new($false))
        # Keep the generated database password readable only by the Windows account that created it.
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
        $acl = Get-Acl -LiteralPath $envFile
        $acl.SetAccessRuleProtection($true, $false)
        $rule = [Security.AccessControl.FileSystemAccessRule]::new($identity, 'FullControl', 'Allow')
        $acl.SetAccessRule($rule)
        Set-Acl -LiteralPath $envFile -AclObject $acl
    }
    $line = Get-Content -LiteralPath $envFile | Where-Object { $_ -match '^POSTGRES_PASSWORD=[A-Fa-f0-9]{64}$' } | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($line)) { throw 'The private realm configuration is invalid. Do not delete it or reset a database without a backup.' }
    $password = $line.Substring('POSTGRES_PASSWORD='.Length)
    Invoke-Docker @('compose', '--project-name', 'kairnfall-local', '--env-file', $envFile, '-f', (Join-Path $root 'docker-compose.yml'), 'up', '-d', '--wait', '--wait-timeout', '90')
    $owned = Get-OwnedServer
    if ($null -eq $owned) {
        $listener = Get-NetTCPConnection -LocalPort 5077 -State Listen -ErrorAction SilentlyContinue
        if ($null -ne $listener) { throw 'Port 5077 is in use by another process. This launcher will not stop it.' }
        $values = @{
            KAIRNFALL_DB = "Host=127.0.0.1;Port=55432;Database=kairnfall;Username=kairnfall;Password=$password"
            KAIRNFALL_CATALOG = (Join-Path $root 'server/content/catalog.json')
            KAIRNFALL_ALLOW_LOCAL_HTTP = '1'
            ASPNETCORE_ENVIRONMENT = 'Development'
            ASPNETCORE_URLS = 'http://127.0.0.1:5077'
        }
        $before = @{}
        try {
            foreach ($key in $values.Keys) { $before[$key] = [Environment]::GetEnvironmentVariable($key, 'Process'); [Environment]::SetEnvironmentVariable($key, $values[$key], 'Process') }
            $owned = Start-Process -FilePath $serverExe -WorkingDirectory (Join-Path $root 'server') -PassThru -RedirectStandardOutput (Join-Path $local 'server.log') -RedirectStandardError (Join-Path $local 'server-errors.log')
        } finally {
            foreach ($key in $before.Keys) { [Environment]::SetEnvironmentVariable($key, $before[$key], 'Process') }
        }
        @{id=$owned.Id; started=$owned.StartTime.ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $pidFile -Encoding UTF8
    }
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $owned.Refresh()
        if ($owned.HasExited) { throw 'The game server exited. Read .local/server-errors.log. The database was not removed.' }
        try { $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5077/health' -TimeoutSec 2; if ($response.StatusCode -eq 200) { $ready = $true; break } } catch { }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw 'The local server did not become ready. Read the local server logs before retrying.' }
    Write-Host 'Local realm: http://127.0.0.1:5077'
    Write-Host 'Create a game account in the client. Do not use your GitHub password.'
    if (-not $ServerOnly) { Start-Process -FilePath $clientExe -WorkingDirectory (Join-Path $root 'client') | Out-Null }
} catch {
    Write-Error $_
    exit 1
}
