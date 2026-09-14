param(
    [string]$Python = "py -3.11",
    [string]$Venv = ".venv-358h"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
Set-Location $repo

if ($Python -eq "py -3.11") {
    & py -3.11 -m venv $Venv
} else {
    & $Python -m venv $Venv
}

$pythonExe = Join-Path $repo "$Venv\Scripts\python.exe"
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r "requirements\358h.txt"

$env:HETEROSPEC_ROOT = $repo
if (-not $env:HETEROSPEC_MODEL_ROOT) { $env:HETEROSPEC_MODEL_ROOT = Join-Path $repo "models" }
if (-not $env:HETEROSPEC_DATA_ROOT) { $env:HETEROSPEC_DATA_ROOT = Join-Path $repo "datasets" }
if (-not $env:HETEROSPEC_CACHE_ROOT) { $env:HETEROSPEC_CACHE_ROOT = Join-Path $repo ".cache\358h" }
New-Item -ItemType Directory -Force -Path $env:HETEROSPEC_CACHE_ROOT | Out-Null

& $pythonExe "scripts\platform\358h\qualify_environment.py" --output "runs\358h\qualification\environment.json"
$inventoryExit = $LASTEXITCODE
Write-Host "Preflight complete. Review runs\358h\qualification\environment.json before installing/exporting models."
Write-Host "Inventory exit code: $inventoryExit (2 is expected before --model-xml qualification)."
Write-Host "Formal measurements remain blocked until preregistration_v1.json has no FILL_* values and is committed."
