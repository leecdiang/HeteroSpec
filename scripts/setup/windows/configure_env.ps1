$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
if (-not $env:HETEROSPEC_ROOT) { $env:HETEROSPEC_ROOT = $repoRoot }
if (-not $env:HETEROSPEC_MODEL_ROOT) { $env:HETEROSPEC_MODEL_ROOT = Join-Path $repoRoot "models" }
if (-not $env:HETEROSPEC_DATA_ROOT) { $env:HETEROSPEC_DATA_ROOT = Join-Path $repoRoot "datasets" }
if (-not $env:HETEROSPEC_CACHE_ROOT) { $env:HETEROSPEC_CACHE_ROOT = Join-Path $repoRoot "hf-cache" }
Write-Host "HeteroSpec-PC environment configured for this PowerShell session."
