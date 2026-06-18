# Install dependencies and launch MakerPlot Studio
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $Root
pip install -e . -q 2>$null
if ($LASTEXITCODE -ne 0) {
    $env:PYTHONPATH = Join-Path $Root "src"
}
python -m makerplot_studio
