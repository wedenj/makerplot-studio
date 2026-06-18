# Copy required third-party apps from the MakerPlot kit into vendor/
param(
    [string]$MakerPlotDir = "d:\Bambu\MakerPlot\GoogleDrive"
)

$ErrorActionPreference = "Stop"
$Project = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Vendor = Join-Path $Project "vendor"
$MakerPlot = (Resolve-Path $MakerPlotDir).Path

Write-Host "MakerPlot Studio - bundle applications"
Write-Host "Source: $MakerPlot"
Write-Host "Target: $Vendor"
Write-Host ""

function Copy-Tree {
    param(
        [string]$Source,
        [string]$Dest,
        [string]$Label
    )
    if (-not (Test-Path $Source)) {
        Write-Warning "Skip $Label - not found: $Source"
        return $false
    }
    Write-Host "Copying $Label..."
    if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force }
    New-Item -ItemType Directory -Path (Split-Path $Dest) -Force | Out-Null
    Copy-Item -Path $Source -Destination $Dest -Recurse -Force
    $mb = [math]::Round(((Get-ChildItem $Dest -Recurse -File | Measure-Object Length -Sum).Sum / 1MB), 1)
    Write-Host "  -> $Dest ($mb MB)"
    return $true
}

# F-Engrave runtime (exclude source tree to save space)
$feSrc = Join-Path $MakerPlot "F-Engrave-1.78_win"
$feDest = Join-Path $Vendor "f-engrave"
if (Test-Path $feSrc) {
    Write-Host "Copying F-Engrave..."
    if (Test-Path $feDest) { Remove-Item $feDest -Recurse -Force }
    New-Item -ItemType Directory -Path $feDest -Force | Out-Null
    Get-ChildItem $feSrc -Exclude "F-Engrave-1.78_src" | Copy-Item -Destination $feDest -Recurse -Force
    $mb = [math]::Round(((Get-ChildItem $feDest -Recurse -File | Measure-Object Length -Sum).Sum / 1MB), 1)
    Write-Host "  -> $feDest ($mb MB)"
} else {
    Write-Warning "F-Engrave not found at $feSrc"
}

# Bundled JRE from MakerPlot UGS Platform package
$jreCandidates = @(
    Join-Path $MakerPlot "win64-ugs-platform-app-2.1.18\ugsplatform-win\jdk\jdk-17.0.8.1+1-jre"
)
$jreCandidates += Get-ChildItem $MakerPlot -Directory -Filter "win64-ugs-platform-app-*" -ErrorAction SilentlyContinue |
    ForEach-Object { Join-Path $_.FullName "ugsplatform-win\jdk\jdk-17.0.8.1+1-jre" }

$jreCopied = $false
foreach ($jre in $jreCandidates) {
    if (Test-Path $jre) {
        Copy-Tree -Source $jre -Dest (Join-Path $Vendor "jre") -Label "Java JRE" | Out-Null
        $jreCopied = $true
        break
    }
}
if (-not $jreCopied) { Write-Warning "JRE not found in MakerPlot folder." }

# UGS Classic JAR (from local zip or existing extract)
$ugsJarDest = Join-Path $Vendor "ugs-classic\UniversalGcodeSender\UniversalGcodeSender.jar"
$ugsZip = Join-Path $Vendor "UniversalGcodeSender.zip"
if (-not (Test-Path $ugsJarDest)) {
    if (Test-Path $ugsZip) {
        Write-Host "Extracting UGS Classic JAR from zip..."
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($ugsZip)
        foreach ($entry in $zip.Entries) {
            if ($entry.FullName -like "*UniversalGcodeSender.jar") {
                New-Item -ItemType Directory -Path (Split-Path $ugsJarDest) -Force | Out-Null
                [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $ugsJarDest, $true)
                Write-Host "  -> $ugsJarDest"
                break
            }
        }
        $zip.Dispose()
    } else {
        Write-Host "Downloading UGS Classic..."
        $url = "https://github.com/winder/Universal-G-Code-Sender/releases/download/v2.1.23/UniversalGcodeSender.zip"
        Invoke-WebRequest -Uri $url -OutFile $ugsZip
        & $MyInvocation.MyCommand.Path -MakerPlotDir $MakerPlot
        return
    }
} else {
    Write-Host "UGS Classic JAR already present."
}

# F-Engrave settings templates
$Settings = Join-Path $Project "settings"
New-Item -ItemType Directory -Path $Settings -Force | Out-Null

$textSrc = Join-Path $MakerPlot "f-engrave settings.txt"
$textDest = Join-Path $Settings "text_settings.txt"
if (Test-Path $textSrc) {
    Copy-Item $textSrc $textDest -Force
    Write-Host "Copied text settings -> settings\text_settings.txt"
}

# Sample image
$Samples = Join-Path $Project "samples"
New-Item -ItemType Directory -Path $Samples -Force | Out-Null
$monkeySrc = Join-Path $MakerPlot "monkey.png"
if (Test-Path $monkeySrc) {
    Copy-Item $monkeySrc (Join-Path $Samples "monkey.png") -Force
    Write-Host "Copied sample image -> samples\monkey.png"
}

Write-Host ""
Write-Host "Bundle complete."
