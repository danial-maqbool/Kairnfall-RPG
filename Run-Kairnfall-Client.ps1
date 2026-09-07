#requires -Version 7.4
[CmdletBinding()]
param([switch]$Smoke)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Run bootstrap.ps1 first.' }
$arguments = @((Join-Path $PSScriptRoot 'tools/local_dev.py'), 'client')
if ($Smoke) { $arguments += '--smoke' }
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw 'The client run failed. Review artifacts/local.' }
