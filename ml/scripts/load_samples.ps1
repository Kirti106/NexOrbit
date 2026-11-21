$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..\..")
$repoRoot = Get-Location
$python = Join-Path $repoRoot "datasets\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
$mlRoot = Join-Path (Get-Location) "ml"
$env:PYTHONPATH = $mlRoot
Set-Location $mlRoot

& $python -m src.pipeline --source satcat --from-file data/samples/celestrak_satcat_active.json
& $python -m src.pipeline --source gp --from-file data/samples/celestrak_gp_active.json
& $python -m src.pipeline --source gp --from-file data/samples/celestrak_gp_fengyun-1c-debris.json
& $python -m src.pipeline --source gp --from-file data/samples/celestrak_gp_cosmos-2251-debris.json
& $python -m src.pipeline --source gp --from-file data/samples/celestrak_gp_iridium-33-debris.json
& $python -m src.pipeline --source socrates --from-file data/samples/socrates_sample.csv
