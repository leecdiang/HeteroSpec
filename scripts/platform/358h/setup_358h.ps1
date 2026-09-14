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

$qualificationDir = Join-Path $repo "runs\358h\qualification"
New-Item -ItemType Directory -Force -Path $qualificationDir | Out-Null
& $pythonExe -m pip freeze | Set-Content -Encoding UTF8 (Join-Path $qualificationDir "pip-freeze.txt")

$windowsInventory = [ordered]@{
    captured_at_utc = [DateTime]::UtcNow.ToString("o")
    computer = Get-ComputerInfo
    bios = Get-CimInstance Win32_BIOS
    processor = Get-CimInstance Win32_Processor
    graphics = Get-CimInstance Win32_VideoController
    system = Get-CimInstance Win32_ComputerSystem
    battery = Get-CimInstance Win32_Battery
    active_power_scheme = (& powercfg /getactivescheme | Out-String).Trim()
    git_commit = (& git rev-parse HEAD | Out-String).Trim()
    git_status = (& git status --porcelain=v1 | Out-String).Trim()
}
$windowsInventory | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $qualificationDir "windows-inventory.json")

& $pythonExe "scripts\platform\358h\qualify_environment.py" --output (Join-Path $qualificationDir "environment.json")
$inventoryExit = $LASTEXITCODE
Write-Host "Preflight complete. Review runs\358h\qualification\environment.json before installing/exporting models."
Write-Host "Inventory exit code: $inventoryExit (2 is expected before --model-xml qualification)."
Write-Host "Formal measurements remain blocked until preregistration_v1.json has no FILL_* values and is committed."
