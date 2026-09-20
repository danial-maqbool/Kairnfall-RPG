#requires -Version 7.4
[CmdletBinding()]
param([switch]$SkipGodot)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$arguments = @((Join-Path $PSScriptRoot 'tools/local_dev.py'), 'prepare')
if ($SkipGodot) { $arguments += '--skip-godot' }
$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($null -ne $launcher) {
    & $launcher.Source -3.12 @arguments
} else {
    $python = Get-Command python -ErrorAction Stop
    & $python.Source @arguments
}
if ($LASTEXITCODE -ne 0) { throw 'Source preparation failed. Read the error and docs/LOCAL_REQUIREMENTS.md.' }
