[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$OutputDirectory)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $root '.venv-358h\Scripts\python.exe'
$probe = Join-Path $PSScriptRoot 'telemetry_overhead_probe.py'
$runner = Join-Path $PSScriptRoot 'run_unified_telemetry.ps1'
$analyzer = Join-Path $PSScriptRoot 'analyze_ut_trace.py'
$model = Join-Path $root 'models\openvino\qwen3-0.6b-6130ef-int4-sym-g128'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

foreach ($device in @('CPU','NPU')) {
    $slug = $device.ToLowerInvariant()
    $probeOut = Join-Path $OutputDirectory ($slug + '-probe.json')
    $prefix = Join-Path $OutputDirectory ($slug + '-ut')
    $app = '"{0}" "{1}" --device {2} --model-dir "{3}" --output "{4}" --iterations 20 --lead-tail-seconds 5 --emit-itt' -f $python,$probe,$device,$model,$probeOut
    if ($device -eq 'CPU') {
        & $runner -ApplicationCommand $app -OutputPrefix $prefix -Collectors 'socwatch,itt'
        & $python $analyzer --trace ($prefix + '.json') --output (Join-Path $OutputDirectory 'cpu-sensor-inventory.json')
    } else {
        & $runner -ApplicationCommand $app -OutputPrefix $prefix -Collectors 'socwatch,level-zero,xpu-os,itt'
        & $python $analyzer --trace ($prefix + '.json') --output (Join-Path $OutputDirectory 'npu-sensor-inventory.json') --require-npu
    }
    if ($LASTEXITCODE -ne 0) { throw "Unified Telemetry sensor qualification failed for $device" }
}

