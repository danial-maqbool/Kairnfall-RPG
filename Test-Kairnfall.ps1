# Run the implemented server and gameplay tests. This does not launch a game client.
[CmdletBinding()]
param(
    [switch]$WithDatabase
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$File failed with exit code $LASTEXITCODE."
    }
}

Push-Location $PSScriptRoot
try {
    $dotnet = Get-Command dotnet -ErrorAction Stop
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        $python = Get-Command python3 -ErrorAction Stop
    }
    if ($WithDatabase) {
        if ([string]::IsNullOrWhiteSpace($env:KAIRNFALL_TEST_DB)) {
            throw 'Set KAIRNFALL_TEST_DB to a disposable PostgreSQL test database.'
        }
        if ($env:KAIRNFALL_ALLOW_DB_TESTS -ne '1') {
            throw 'Set KAIRNFALL_ALLOW_DB_TESTS=1 only for a disposable test database. Never use a production database.'
        }
    }
    Invoke-CheckedNative -File $python.Source -Arguments @('tools/build_content.py')
    Invoke-CheckedNative -File $dotnet.Source -Arguments @('build', 'Kairnfall.slnx', '-c', 'Release')
    Invoke-CheckedNative -File $dotnet.Source -Arguments @('run', '--no-build', '--project', 'tests/Kairnfall.Tests/Kairnfall.Tests.csproj', '-c', 'Release', '--', 'content/catalog.json')
    Invoke-CheckedNative -File $dotnet.Source -Arguments @('run', '--no-build', '--project', 'tests/Kairnfall.ReviewTests/Kairnfall.ReviewTests.csproj', '-c', 'Release')
    if ($WithDatabase) {
        Invoke-CheckedNative -File $dotnet.Source -Arguments @('run', '--no-build', '--project', 'tests/Kairnfall.Integration/Kairnfall.Integration.csproj', '-c', 'Release')
        Invoke-CheckedNative -File $dotnet.Source -Arguments @('run', '--no-build', '--project', 'tests/Kairnfall.ReviewTests/Kairnfall.ReviewTests.csproj', '-c', 'Release', '--', '--database')
    }
    Write-Host 'Requested test suites passed. JSON reports are in artifacts/test-results.'
}
finally {
    Pop-Location
}
