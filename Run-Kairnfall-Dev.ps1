[CmdletBinding()]
param([switch]$InstallDotNet)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    & ./bootstrap.ps1 -InstallDotNet:$InstallDotNet
    $tool=Get-Content -Raw .tools/godot.json | ConvertFrom-Json
    New-Item -ItemType Directory -Force build/client, build/server | Out-Null
    & $tool.binary --headless --editor --path client --import
    if ($LASTEXITCODE -ne 0) { throw 'Godot resource import failed.' }
    & $tool.binary --headless --path client --export-release 'Windows Desktop' '../build/client/Kairnfall.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Godot Windows export failed.' }
    dotnet publish src/Kairnfall.Server/Kairnfall.Server.csproj -c Release -r win-x64 --self-contained true -o build/server
    if ($LASTEXITCODE -ne 0) { throw 'Windows server publish failed.' }
    New-Item -ItemType Directory -Force build/server/content | Out-Null
    Copy-Item content/catalog.json build/server/content/catalog.json
    Copy-Item Play-Kairnfall.cmd, Start-Kairnfall.ps1, Stop-Kairnfall.ps1, compose.yml, LICENSE, README.md build/
    & ./build/Start-Kairnfall.ps1
} finally { Pop-Location }
