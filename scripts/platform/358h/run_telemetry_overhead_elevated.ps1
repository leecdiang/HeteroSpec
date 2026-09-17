$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$base = Join-Path $root 'runs\358h\qualification_ac_20260918\telemetry_overhead_v3_100ms_noitt'
$log = Join-Path (Split-Path -Parent $base) 'telemetry_overhead_elevated.log'
New-Item -ItemType Directory -Force -Path $base | Out-Null
Start-Transcript -Path $log -Force
try {
    & (Join-Path $PSScriptRoot 'qualify_telemetry_overhead.ps1') -Device CPU -OutputDirectory (Join-Path $base 'cpu')
    & (Join-Path $PSScriptRoot 'qualify_telemetry_overhead.ps1') -Device NPU -OutputDirectory (Join-Path $base 'npu')
    Stop-Transcript
    exit 0
} catch {
    Write-Error ($_ | Out-String)
    Stop-Transcript
    exit 1
}

