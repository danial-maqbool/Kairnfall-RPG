[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'Start-Kairnfall.ps1') -ServerOnly
