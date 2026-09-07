[CmdletBinding()]
param(
    [string]$Version = '4.7.2',
    [string]$Channel = 'stable',
    [string]$ToolchainRoot = '.tools/godot',
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-RepoRoot
$toolchainPath = Join-Path $root $ToolchainRoot
New-Item -ItemType Directory -Force -Path $toolchainPath | Out-Null
$downloadPath = Join-Path $toolchainPath 'downloads'
$extractPath = Join-Path $toolchainPath 'extracted'
New-Item -ItemType Directory -Force -Path $downloadPath | Out-Null
New-Item -ItemType Directory -Force -Path $extractPath | Out-Null

$tag = "$Version-$Channel"
$editorName = "Godot_v${Version}-${Channel}_mono_win64.zip"
$templateName = "Godot_v${Version}-${Channel}_mono_export_templates.tpz"
$releaseUri = "https://api.github.com/repos/godotengine/godot-builds/releases/tags/$tag"

Write-Host "Fetching release metadata: $releaseUri"
$release = Invoke-RestMethod -Uri $releaseUri -Headers @{ 'Accept' = 'application/vnd.github+json' }
$assets = @{}
foreach ($asset in $release.assets) { $assets[$asset.name] = $asset.browser_download_url }

if (-not $assets.ContainsKey($editorName)) {
    throw "Release $tag does not include expected editor asset: $editorName"
}
if (-not $assets.ContainsKey($templateName)) {
    throw "Release $tag does not include expected template asset: $templateName"
}

$checksumAsset = $assets.GetEnumerator() | Where-Object { $_.Key -match 'SHA(256|512)-SUMS' } | Select-Object -First 1
$checksums = @{}
if ($null -ne $checksumAsset) {
    Write-Host "Downloading checksum file: $($checksumAsset.Key)"
    $checksumText = (Invoke-WebRequest -Uri $checksumAsset.Value -UseBasicParsing).Content
    foreach ($line in ($checksumText -split "`n")) {
        if ($line -match '^([a-fA-F0-9]{64,128})\s+\*?(.+)$') {
            $checksums[$matches[2].Trim()] = $matches[1].ToLowerInvariant()
        }
    }
}

function Save-VerifiedAsset {
    param([string]$Name)

    $url = $assets[$Name]
    $target = Join-Path $downloadPath $Name
    if ($Force -or -not (Test-Path -LiteralPath $target)) {
        Write-Host "Downloading $Name"
        Invoke-WebRequest -Uri $url -OutFile $target -UseBasicParsing
    }

    if ($checksums.ContainsKey($Name)) {
        $expected = $checksums[$Name]
        if ($expected.Length -eq 64) {
            $actual = (Get-FileHash -Path $target -Algorithm SHA256).Hash.ToLowerInvariant()
        }
        else {
            $actual = (Get-FileHash -Path $target -Algorithm SHA512).Hash.ToLowerInvariant()
        }
        if ($actual -ne $expected) {
            throw "Digest mismatch for $Name"
        }
    }
    else {
        Write-Warning "No published digest entry was found for $Name; validate manually before release."
    }

    return $target
}

$editorZip = Save-VerifiedAsset -Name $editorName
$templateArchive = Save-VerifiedAsset -Name $templateName

$editorExtract = Join-Path $extractPath 'editor'
if ($Force -and (Test-Path -LiteralPath $editorExtract)) { Remove-Item -Recurse -Force -LiteralPath $editorExtract }
if (-not (Test-Path -LiteralPath $editorExtract)) {
    Expand-Archive -LiteralPath $editorZip -DestinationPath $editorExtract -Force
}
$editorExe = Get-ChildItem -Path $editorExtract -Filter 'Godot*_mono.exe' -Recurse | Select-Object -First 1
if ($null -eq $editorExe) {
    throw "Unable to locate the Godot Mono editor executable in $editorExtract"
}

$templateExtract = Join-Path $extractPath 'templates'
if ($Force -and (Test-Path -LiteralPath $templateExtract)) { Remove-Item -Recurse -Force -LiteralPath $templateExtract }
if (-not (Test-Path -LiteralPath $templateExtract)) {
    Expand-Archive -LiteralPath $templateArchive -DestinationPath $templateExtract -Force
}

$versionFile = Get-ChildItem -Path $templateExtract -Filter 'version.txt' -Recurse | Select-Object -First 1
if ($null -eq $versionFile) {
    throw "The templates archive did not include version.txt"
}
$templateVersion = (Get-Content -LiteralPath $versionFile.FullName -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($templateVersion)) {
    throw 'Templates version.txt was empty.'
}

$templatesSource = $versionFile.Directory.FullName
$templatesTargetRoot = Join-Path $env:APPDATA 'Godot/export_templates'
$templatesTarget = Join-Path $templatesTargetRoot $templateVersion
New-Item -ItemType Directory -Force -Path $templatesTargetRoot | Out-Null
if (Test-Path -LiteralPath $templatesTarget) {
    Remove-Item -Recurse -Force -LiteralPath $templatesTarget
}
Copy-Item -Path (Join-Path $templatesSource '*') -Destination $templatesTarget -Recurse -Force

$result = [pscustomobject]@{
    Version = $Version
    Channel = $Channel
    Tag = $tag
    EditorPath = $editorExe.FullName
    TemplatesVersion = $templateVersion
    TemplatesDirectory = $templatesTarget
}
$result | ConvertTo-Json -Depth 4
