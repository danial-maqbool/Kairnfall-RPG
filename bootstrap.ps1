# Prepare source tools and content in this repository. No global execution-policy change.
[CmdletBinding()]
param([switch]$InstallDotNet, [switch]$SkipAssets)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
    $tools=Join-Path $PSScriptRoot '.tools'
    New-Item -ItemType Directory -Force $tools | Out-Null
    if ($InstallDotNet) {
        $installer=Join-Path $tools 'dotnet-install.ps1'
        Invoke-WebRequest -UseBasicParsing -Uri 'https://dot.net/v1/dotnet-install.ps1' -OutFile $installer
        & $installer -Channel '10.0' -InstallDir (Join-Path $tools 'dotnet') -NoPath
        $env:DOTNET_ROOT=Join-Path $tools 'dotnet'
        $env:PATH="$env:DOTNET_ROOT;$env:PATH"
    } elseif (Test-Path (Join-Path $tools 'dotnet/dotnet.exe')) {
        $env:DOTNET_ROOT=Join-Path $tools 'dotnet'; $env:PATH="$env:DOTNET_ROOT;$env:PATH"
    }
    $dotnet=Get-Command dotnet -ErrorAction Stop
    & $dotnet.Source --version
    if ($LASTEXITCODE -ne 0) { throw 'Install the .NET 10 SDK or run bootstrap.ps1 -InstallDotNet.' }
    $python=Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) { throw 'Install Python 3.12 from python.org with its PATH option. The source asset tools need Python 3.11 or later.' }
    & $python.Source -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11 or later is required"'
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.11 or later is required.' }
    $venv=Join-Path $tools 'venv/Scripts/python.exe'
    if (!(Test-Path $venv)) { & $python.Source -m venv (Join-Path $tools 'venv'); if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment.' } }
    & $venv -m pip install Pillow==11.3.0
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the asset dependency.' }
    & $venv tools/build_content.py
    if ($LASTEXITCODE -ne 0) { throw 'Content validation failed.' }
    if (!$SkipAssets) {
        & $venv tools/build_assets.py --workers 2
        if ($LASTEXITCODE -ne 0) { throw 'Asset generation or structural validation failed.' }
    }
    & $venv tools/get_godot.py --os windows --with-templates
    if ($LASTEXITCODE -ne 0) { throw 'The pinned official Godot toolchain could not be verified.' }
    dotnet build Kairnfall.slnx -c Debug
    if ($LASTEXITCODE -ne 0) { throw 'Solution build failed.' }
    Write-Host 'Source tools and assets are prepared. No public server was deployed.'
} finally { Pop-Location }
