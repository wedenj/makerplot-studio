# Install dependencies and launch MakerPlot Studio
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $Root
pip install -e . -q
python -m makerplot_studio
