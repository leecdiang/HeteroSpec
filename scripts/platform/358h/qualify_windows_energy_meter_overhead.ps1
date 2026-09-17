[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [int]$RepetitionsPerCondition = 10,
    [int]$Seed = 570,
    [int]$ContextTokens = 0,
    [int]$OutputTokens = 4,
    [int]$Iterations = 20,
    [int]$Warmups = 3,
    [int]$LeadTailSeconds = 5,
    [int]$CollectorDurationSeconds = 15,
    [string]$WorkloadAffinityCpus = '',
    [string]$CollectorAffinityCpus = ''
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python = Join-Path $root '.venv-358h\Scripts\python.exe'
$probe = Join-Path $PSScriptRoot 'telemetry_overhead_probe.py'
$sampler = Join-Path $PSScriptRoot 'sample_windows_energy_meter.py'
$model = Join-Path $root 'models\openvino\qwen3-0.6b-6130ef-int4-sym-g128'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$random = [Random]::new($Seed)
$schedule = @()
1..$RepetitionsPerCondition | ForEach-Object { $schedule += 'OFF'; $schedule += 'ON' }
$schedule = $schedule | Sort-Object { $random.Next() }
$records = @()

for ($index = 0; $index -lt $schedule.Count; $index++) {
    $condition = $schedule[$index]
    $slug = ('{0:D2}-{1}' -f ($index + 1), $condition.ToLowerInvariant())
    $probeOut = Join-Path $OutputDirectory ($slug + '-probe.json')
    if ($condition -eq 'ON') {
        $csv = Join-Path $OutputDirectory ($slug + '-rapl.csv')
        $meta = Join-Path $OutputDirectory ($slug + '-rapl.json')
        $collectorArgs = @($sampler, '--output-csv', $csv, '--metadata-json', $meta, '--duration-seconds', "$CollectorDurationSeconds", '--period-ms', '1000')
        if ($CollectorAffinityCpus) { $collectorArgs += @('--affinity-cpus', $CollectorAffinityCpus) }
        $collector = Start-Process -FilePath $python -ArgumentList $collectorArgs -PassThru -WindowStyle Hidden
        Start-Sleep -Milliseconds 1500
        $probeArgs = @($probe, '--device', 'CPU', '--model-dir', $model, '--output', $probeOut, '--iterations', "$Iterations", '--lead-tail-seconds', "$LeadTailSeconds", '--output-tokens', "$OutputTokens", '--warmups', "$Warmups")
        if ($ContextTokens -gt 0) { $probeArgs += @('--context-tokens', "$ContextTokens") }
        if ($WorkloadAffinityCpus) { $probeArgs += @('--affinity-cpus', $WorkloadAffinityCpus) }
        & $python @probeArgs
        if ($LASTEXITCODE -ne 0) { throw "ON workload failed: $slug" }
        $collector.WaitForExit()
        if ($collector.ExitCode -ne 0) { throw "Energy Meter collector failed: $slug" }
    } else {
        $probeArgs = @($probe, '--device', 'CPU', '--model-dir', $model, '--output', $probeOut, '--iterations', "$Iterations", '--lead-tail-seconds', "$LeadTailSeconds", '--output-tokens', "$OutputTokens", '--warmups', "$Warmups")
        if ($ContextTokens -gt 0) { $probeArgs += @('--context-tokens', "$ContextTokens") }
        if ($WorkloadAffinityCpus) { $probeArgs += @('--affinity-cpus', $WorkloadAffinityCpus) }
        & $python @probeArgs
        if ($LASTEXITCODE -ne 0) { throw "OFF workload failed: $slug" }
    }
    $probeRecord = Get-Content -Raw -LiteralPath $probeOut | ConvertFrom-Json
    $records += [pscustomobject]@{index=$index+1; condition=$condition; inner_duration_ms=[double]$probeRecord.inner_duration_ms; probe=$probeOut}
}

function Median($values) {
    $ordered = @($values | Sort-Object)
    $count = $ordered.Count
    if ($count % 2) { return [double]$ordered[[int]($count/2)] }
    return ([double]$ordered[$count/2-1] + [double]$ordered[$count/2]) / 2.0
}
$offMedian = Median @($records | Where-Object condition -eq 'OFF' | ForEach-Object inner_duration_ms)
$onMedian = Median @($records | Where-Object condition -eq 'ON' | ForEach-Object inner_duration_ms)
$overheadPct = (($onMedian / $offMedian) - 1.0) * 100.0
$result = [ordered]@{
    schema = 'heterospec.358h.windows_energy_meter_overhead.v1'
    formal_measurement = $false
    invalid_for_claims = $true
    device = 'CPU'
    sensor = 'Windows Energy Meter RAPL_Package0_PKG via direct PDH API'
    seed = $Seed
    workload = [ordered]@{context_tokens=$ContextTokens; output_tokens=$OutputTokens; iterations=$Iterations; warmups=$Warmups; lead_tail_seconds=$LeadTailSeconds}
    affinity = [ordered]@{workload_cpus=$WorkloadAffinityCpus; collector_cpus=$CollectorAffinityCpus}
    schedule = $schedule
    repetitions_per_condition = $RepetitionsPerCondition
    statistic_frozen_before_result = 'absolute percent change between ON and OFF medians'
    median_off_ms = $offMedian
    median_on_ms = $onMedian
    absolute_overhead_percent = [Math]::Abs($overheadPct)
    threshold_percent = 1.0
    qualification_pass = ([Math]::Abs($overheadPct) -le 1.0)
    records = $records
}
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $OutputDirectory 'overhead_qualification.json')
$result | ConvertTo-Json -Depth 4
if (-not $result.qualification_pass) { exit 2 }

