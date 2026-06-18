# One-time setup: install package and bundle required apps
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = Split-Path -Parent $Root

Set-Location $Project

pip install -e . -q 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Note: pip install -e failed; run.ps1 will use PYTHONPATH instead."
}

$Kit = "d:\Bambu\MakerPlot\GoogleDrive"
if (Test-Path $Kit) {
    & (Join-Path $Root "bundle-apps.ps1") -MakerPlotDir $Kit
} else {
    Write-Host "MakerPlot kit not found at $Kit"
    Write-Host "Run: .\scripts\bundle-apps.ps1 -MakerPlotDir <path-to-MakerPlot-GoogleDrive>"
    python -c "from makerplot_studio.paths import ensure_ugs_jar; print(ensure_ugs_jar(on_progress=print))"
}

Write-Host ""
Write-Host "Setup complete. Run: .\run.ps1"
