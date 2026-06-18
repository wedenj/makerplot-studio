# One-time setup: install package and download UGS Classic
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Project = Split-Path -Parent $Root

Set-Location $Project
pip install -e .

python -c "
from makerplot_studio.paths import ensure_ugs_jar
print(ensure_ugs_jar(on_progress=print))
"

Write-Host "Setup complete. Run: .\run.ps1"
