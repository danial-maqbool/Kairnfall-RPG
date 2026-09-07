#requires -Version 7.4
[CmdletBinding()]
param([switch]$WithDatabase)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Run bootstrap.ps1 first.' }
$arguments = @((Join-Path $PSScriptRoot 'tools/local_dev.py'), 'test')
$previous = $env:KAIRNFALL_ALLOW_DB_TESTS
try {
    if ($WithDatabase) {
        $arguments += '--with-database'
        $env:KAIRNFALL_ALLOW_DB_TESTS = '1'
    }
    & $python @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Local tests failed. Review artifacts/local-tests and artifacts/test-results.' }
} finally { $env:KAIRNFALL_ALLOW_DB_TESTS = $previous }
