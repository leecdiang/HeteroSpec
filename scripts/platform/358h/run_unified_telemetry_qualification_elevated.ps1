$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$base = Join-Path $root 'runs\358h\qualification_ac_20260918'
$log = Join-Path $base 'unified_telemetry_elevated.log'
New-Item -ItemType Directory -Force -Path $base | Out-Null
Start-Transcript -Path $log -Force
try {
    & (Join-Path $PSScriptRoot 'qualify_unified_telemetry_smoke.ps1') -OutputDirectory (Join-Path $base 'unified_telemetry_smoke_100ms')
    Stop-Transcript
    exit 0
} catch {
    Write-Error ($_ | Out-String)
    Stop-Transcript
    exit 1
}

