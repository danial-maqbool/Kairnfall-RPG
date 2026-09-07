# Stop only the local realm recorded by the launcher. Preserve the database volume.
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$state=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Kairnfall/local-realm'
$pidFile=Join-Path $state 'server-process.json'
if (Test-Path $pidFile) {
    $saved=Get-Content -Raw $pidFile | ConvertFrom-Json
    $process=Get-Process -Id $saved.pid -ErrorAction SilentlyContinue
    if ($null -ne $process) {
        if ($process.Path -ne $saved.path -or $process.StartTime.ToUniversalTime().Ticks -ne [long]$saved.startTicks) {
            throw 'The recorded PID belongs to a different process. Nothing was stopped.'
        }
        Stop-Process -Id $process.Id
        $process.WaitForExit(10000) | Out-Null
    }
    Remove-Item $pidFile
}
$compose=Join-Path $PSScriptRoot 'compose.yml'
$passwordFile=Join-Path $state 'postgres-password.dpapi'
if ((Test-Path $compose) -and (Test-Path $passwordFile)) {
    $old=$env:KAIRNFALL_DB_PASSWORD
    try {
        $secure=Get-Content -Raw $passwordFile | ConvertTo-SecureString
        $env:KAIRNFALL_DB_PASSWORD=(New-Object Net.NetworkCredential('', $secure)).Password
        docker compose --project-name kairnfall-local --file $compose stop postgres
        if ($LASTEXITCODE -ne 0) { throw 'Docker could not stop PostgreSQL. Open Docker Desktop to inspect the local container.' }
    } finally { $env:KAIRNFALL_DB_PASSWORD=$old }
}
Write-Host 'Local realm stopped. The PostgreSQL volume and password file remain unchanged.'
