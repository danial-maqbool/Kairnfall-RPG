# Start the local PostgreSQL realm and the Windows client. Do not expose these ports publicly.
[CmdletBinding()]
param([switch]$ServerOnly, [switch]$CheckOnly)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'This launcher supports Windows only.' }
$root = $PSScriptRoot
if (!(Test-Path (Join-Path $root 'server/Kairnfall.Server.exe'))) {
    if (Test-Path (Join-Path $root 'build/server/Kairnfall.Server.exe')) { $root = Join-Path $root 'build' }
    else { throw 'The Windows server package is missing. Use the complete development package or run Run-Kairnfall-Dev.ps1 from source.' }
}
$server = Join-Path $root 'server/Kairnfall.Server.exe'
$client = Join-Path $root 'client/Kairnfall.exe'
$compose = Join-Path $root 'compose.yml'
if (!(Test-Path $compose)) { throw 'compose.yml is missing from the package. Extract the complete ZIP.' }
if (!$ServerOnly -and !(Test-Path $client)) { throw 'The Windows client is missing. Extract the complete ZIP.' }
if ($CheckOnly) { Write-Host 'Package paths are valid. This check did not start Docker or the game.'; return }
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $docker) { throw 'Install Docker Desktop from docker.com, open it, and use Linux containers. Then run Play-Kairnfall.cmd again.' }
$dockerType = & $docker.Source info --format '{{.OSType}}' 2>$null
if ($LASTEXITCODE -ne 0 -or $dockerType -ne 'linux') { throw 'Open Docker Desktop and start its Linux container engine. Then run Play-Kairnfall.cmd again.' }
$state = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Kairnfall/local-realm'
$logs = Join-Path $state 'logs'
New-Item -ItemType Directory -Force $state, $logs | Out-Null
$passwordFile = Join-Path $state 'postgres-password.dpapi'
if (!(Test-Path $passwordFile)) {
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $plain = [Convert]::ToBase64String($bytes)
    $secure = ConvertTo-SecureString $plain -AsPlainText -Force
    $secure | ConvertFrom-SecureString | Set-Content -Path $passwordFile -Encoding ASCII
    $plain = $null
}
$secure = Get-Content -Raw $passwordFile | ConvertTo-SecureString
$password = (New-Object System.Net.NetworkCredential('', $secure)).Password
$oldPassword = $env:KAIRNFALL_DB_PASSWORD
$oldDb = $env:KAIRNFALL_DB
$oldAllow = $env:KAIRNFALL_ALLOW_LOCAL_HTTP
$oldEnvironment = $env:ASPNETCORE_ENVIRONMENT
$oldUrls = $env:ASPNETCORE_URLS
$pidFile = Join-Path $state 'server-process.json'
try {
    $env:KAIRNFALL_DB_PASSWORD = $password
    & $docker.Source compose --project-name kairnfall-local --file $compose up -d --wait postgres
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL did not start. Keep the existing volume and password file. Do not reset the database.' }
    $running = $null
    if (Test-Path $pidFile) {
        $saved = Get-Content -Raw $pidFile | ConvertFrom-Json
        $candidate = Get-Process -Id $saved.pid -ErrorAction SilentlyContinue
        if ($null -ne $candidate -and $candidate.Path -eq $saved.path -and $candidate.StartTime.ToUniversalTime().Ticks -eq [long]$saved.startTicks) { $running = $candidate }
    }
    if ($null -eq $running) {
        $socket = New-Object Net.Sockets.TcpClient
        try {
            $connect = $socket.BeginConnect('127.0.0.1',5077,$null,$null)
            if ($connect.AsyncWaitHandle.WaitOne(300) -and $socket.Connected) { throw 'Port 5077 is already in use by an unrecognized process. The launcher will not replace it.' }
        } finally { $socket.Dispose() }
        $env:KAIRNFALL_DB = "Host=127.0.0.1;Port=55432;Database=kairnfall;Username=kairnfall;Password=$password"
        $env:KAIRNFALL_ALLOW_LOCAL_HTTP = '1'
        $env:ASPNETCORE_ENVIRONMENT = 'Development'
        $env:ASPNETCORE_URLS = 'http://127.0.0.1:5077'
        $running = Start-Process -FilePath $server -WorkingDirectory (Split-Path $server) -PassThru -RedirectStandardOutput (Join-Path $logs 'server.log') -RedirectStandardError (Join-Path $logs 'server-errors.log')
        Start-Sleep -Milliseconds 300
        $running.Refresh()
        if ($running.HasExited) { throw "Server stopped during startup. Read $logs\server-errors.log." }
        @{pid=$running.Id; path=$running.Path; startTicks=$running.StartTime.ToUniversalTime().Ticks} | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8
    }
    $ready = $false
    for ($attempt=0; $attempt -lt 60; $attempt++) {
        try {
            $result = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5077/health' -TimeoutSec 2
            if ($result.StatusCode -eq 200) { $ready=$true; break }
        } catch { Start-Sleep -Seconds 1 }
        $running.Refresh()
        if ($running.HasExited) { break }
    }
    if (!$ready) { throw "The local server did not become ready. Read logs in $logs. Existing saves were not deleted." }
} finally {
    $env:KAIRNFALL_DB_PASSWORD=$oldPassword; $env:KAIRNFALL_DB=$oldDb
    $env:KAIRNFALL_ALLOW_LOCAL_HTTP=$oldAllow; $env:ASPNETCORE_ENVIRONMENT=$oldEnvironment; $env:ASPNETCORE_URLS=$oldUrls
    $password=$null
}
Write-Host 'Local realm ready: http://127.0.0.1:5077'
Write-Host "Logs: $logs"
Write-Host 'The server stays running after the client closes. Run Stop-Kairnfall.ps1 to stop it without deleting saves.'
if (!$ServerOnly) { Start-Process -FilePath $client -WorkingDirectory (Split-Path $client) }
