Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..' '..')).Path
}

function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [Parameter(Mandatory = $false)][string[]]$Arguments = @(),
        [Parameter(Mandatory = $false)][hashtable]$Environment = @{},
        [Parameter(Mandatory = $false)][string]$WorkingDirectory = (Get-Location).Path
    )

    $start = [System.Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $File
    foreach ($argument in $Arguments) {
        [void]$start.ArgumentList.Add($argument)
    }
    $start.WorkingDirectory = $WorkingDirectory
    $start.UseShellExecute = $false
    foreach ($key in $Environment.Keys) {
        $start.Environment[$key] = [string]$Environment[$key]
    }

    $process = [System.Diagnostics.Process]::Start($start)
    if ($null -eq $process) {
        throw "Failed to start native process: $File"
    }
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {
        throw "$File failed with exit code $($process.ExitCode)."
    }
}

function New-RandomSecret {
    param([int]$Bytes = 24)
    return [Convert]::ToHexString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes($Bytes)).ToLowerInvariant()
}

function Resolve-DevEnvironment {
    param(
        [string]$PostgresUser = 'kairnfall_dev',
        [string]$PostgresDatabase = 'kairnfall_dev',
        [int]$PostgresPort = 5433,
        [switch]$ForceRotatePassword
    )

    $root = Get-RepoRoot
    $directory = Join-Path $root '.tools/windows/dev'
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    $environmentFile = Join-Path $directory '.env'

    $password = $env:KAIRNFALL_PG_PASSWORD
    if ([string]::IsNullOrWhiteSpace($password) -or $ForceRotatePassword) {
        if ((-not [string]::IsNullOrWhiteSpace($password)) -and $ForceRotatePassword) {
            Write-Warning 'Ignoring KAIRNFALL_PG_PASSWORD because -ForceRotatePassword was requested.'
        }
        $password = New-RandomSecret -Bytes 24
    }

    $lines = @(
        "POSTGRES_USER=$PostgresUser"
        "POSTGRES_DB=$PostgresDatabase"
        "POSTGRES_PASSWORD=$password"
        "POSTGRES_PORT=$PostgresPort"
    )
    Set-Content -Path $environmentFile -Value ($lines -join [Environment]::NewLine) -Encoding utf8NoBOM

    return [pscustomobject]@{
        RootDirectory = $root
        EnvironmentFile = $environmentFile
        PostgresUser = $PostgresUser
        PostgresDatabase = $PostgresDatabase
        PostgresPassword = $password
        PostgresPort = $PostgresPort
        ConnectionString = "Host=127.0.0.1;Port=$PostgresPort;Database=$PostgresDatabase;Username=$PostgresUser;******;SSL Mode=Disable;Pooling=true;Maximum Pool Size=20"
    }
}

function Wait-HttpHealth {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    }

    throw "Timed out waiting for health endpoint: $Url"
}

function Ensure-FilePresent {
    param([Parameter(Mandatory = $true)][string]$Path, [string]$Message = 'Required file is missing.')
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Message Path: $Path"
    }
}
