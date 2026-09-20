#requires -Version 7.4
[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Run bootstrap.ps1 first.' }
& $python (Join-Path $PSScriptRoot 'tools/local_dev.py') stop-db
if ($LASTEXITCODE -ne 0) { throw 'The local database stop command failed. No volumes were deleted.' }
