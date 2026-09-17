[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('CPU','NPU')][string]$Device,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $root '.venv-358h\Scripts\python.exe'
$probe = Join-Path $PSScriptRoot 'telemetry_overhead_probe.py'
$utWrapper = Join-Path $PSScriptRoot 'run_unified_telemetry.ps1'
$model = Join-Path $root 'models\openvino\qwen3-0.6b-6130ef-int4-sym-g128'

$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Telemetry overhead qualification requires an Administrator PowerShell.'
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$random = [Random]::new(570)
$schedule = @()
1..10 | ForEach-Object { $schedule += 'OFF'; $schedule += 'ON' }
$schedule = $schedule | Sort-Object { $random.Next() }

$records = @()
for ($index = 0; $index -lt $schedule.Count; $index++) {
    $condition = $schedule[$index]
    $slug = ('{0:D2}-{1}' -f ($index + 1), $condition.ToLowerInvariant())
    $probeOut = Join-Path $OutputDirectory ($slug + '-probe.json')
    $app = '"{0}" "{1}" --device {2} --model-dir "{3}" --output "{4}" --iterations 20 --lead-tail-seconds 5' -f $python,$probe,$Device,$model,$probeOut
    if ($condition -eq 'ON') {
        $collectors = if ($Device -eq 'CPU') { 'socwatch' } else { 'socwatch,level-zero,xpu-os' }
        & $utWrapper -ApplicationCommand $app -OutputPrefix (Join-Path $OutputDirectory ($slug + '-ut')) -Collectors $collectors -SkipConversion
    } else {
        & $python $probe --device $Device --model-dir $model --output $probeOut --iterations 20 --lead-tail-seconds 5
        if ($LASTEXITCODE -ne 0) { throw "OFF probe failed: $slug" }
    }
    $probeRecord = Get-Content -Raw -LiteralPath $probeOut | ConvertFrom-Json
    $records += [pscustomobject]@{ index=$index+1; condition=$condition; inner_duration_ms=[double]$probeRecord.inner_duration_ms; probe=$probeOut }
}

$off = @($records | Where-Object condition -eq 'OFF' | Sort-Object inner_duration_ms)
$on = @($records | Where-Object condition -eq 'ON' | Sort-Object inner_duration_ms)
function Median($values) {
    $count = $values.Count
    if ($count % 2) { return [double]$values[[int]($count/2)] }
    return ([double]$values[$count/2-1] + [double]$values[$count/2]) / 2.0
}
$offMedian = Median @($off.inner_duration_ms)
$onMedian = Median @($on.inner_duration_ms)
$overheadPct = (($onMedian / $offMedian) - 1.0) * 100.0
$result = [ordered]@{
    schema_version = 1
    formal_measurement = $false
    device = $Device
    seed = 570
    schedule = $schedule
    repetitions_per_condition = 10
    median_off_ms = $offMedian
    median_on_ms = $onMedian
    absolute_overhead_percent = [Math]::Abs($overheadPct)
    threshold_percent = 1.0
    qualification_pass = ([Math]::Abs($overheadPct) -le 1.0)
    records = $records
}
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'overhead_qualification.json')
if (-not $result.qualification_pass) { throw "Telemetry overhead gate failed: $overheadPct percent" }
