[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$client=Join-Path $PSScriptRoot 'build/client/Kairnfall.exe'
if (!(Test-Path $client)) { throw 'Build the source with Run-Kairnfall-Dev.ps1 first, or use Play-Kairnfall.cmd in the complete package.' }
Start-Process -FilePath $client -WorkingDirectory (Split-Path $client)
