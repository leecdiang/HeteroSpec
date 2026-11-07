[CmdletBinding()]
param(
    [string] $RepoRoot = '',
    [string] $LlamaBench = 'C:\hs\b\bin\Release\llama-bench.exe',
    [string] $Collector = 'C:\hs\pm\Release\b570_presentmon_telemetry.exe',
    [string] $SysmanProbe = 'C:\hs\pm\Release\b570_sysman_probe.exe',
    [string] $Python = 'C:\Users\DIANG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe',
    [int] $DisconnectDelaySeconds = 90
)

$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path }
$stamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
$root = Join-Path $RepoRoot "work\b570\telemetry-qualification-$stamp"
New-Item -ItemType Directory -Path $root | Out-Null
$status = Join-Path $RepoRoot 'work\b570\telemetry_qualification_status.txt'
$target = Join-Path $RepoRoot 'models\gguf\Qwen3-8B-Q8_0.gguf'
$draft = Join-Path $RepoRoot 'models\gguf\Qwen3-0.6B-Q8_0.gguf'
$runner = Join-Path $RepoRoot 'scripts\platform\b570\run_unattended.ps1'
$analysis = Join-Path $RepoRoot 'scripts\platform\b570\analyze_telemetry.py'
$integrator = Join-Path $RepoRoot 'scripts\platform\b570\integrate_energy.py'
$overheadAnalysis = Join-Path $RepoRoot 'scripts\platform\b570\analyze_telemetry_overhead.py'

foreach ($path in @($LlamaBench, $Collector, $SysmanProbe, $Python, $target, $draft, $runner, $analysis, $integrator, $overheadAnalysis)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required file missing: $path" }
}

"READY_TO_DISCONNECT_TODESK_FOR_TELEMETRY_QUALIFICATION`noutput=$root" | Set-Content -LiteralPath $status -Encoding utf8
Write-Output 'READY_TO_DISCONNECT_TODESK_FOR_TELEMETRY_QUALIFICATION'
Start-Sleep -Seconds $DisconnectDelaySeconds

# Sanity profile: 20 s idle, about 30-60 s of repeated B570 Vulkan PP512, 20 s idle.
$sanityRoot = Join-Path $root 'sanity'
$sanityParams = @{
    Command = $LlamaBench
    CommandArgs = @('-m',$target,'-dev','Vulkan0','-ngl','99','-p','512','-n','0','-r','100','-o','json','-fa','off')
    OutputRoot = $sanityRoot
    RunName = 'idle20-load-pp512x100-idle20'
    DelaySeconds = 0
    PreIdleSeconds = 20
    PostIdleSeconds = 20
    TelemetryCommand = $Collector
    TelemetryPeriodMs = 100
    TelemetryMaxDurationSeconds = 300
}
& $runner @sanityParams
if ($LASTEXITCODE -ne 0) { throw "Sanity workload failed: $LASTEXITCODE" }
$sanity = Get-ChildItem -LiteralPath $sanityRoot -Directory | Sort-Object LastWriteTime | Select-Object -Last 1
& $Python $analysis --telemetry (Join-Path $sanity.FullName 'telemetry.csv') --metadata (Join-Path $sanity.FullName 'telemetry.metadata.json') --window (Join-Path $sanity.FullName 'workload-window.json') --output (Join-Path $sanity.FullName 'analysis.json') | Out-Null
& $Python $integrator --telemetry (Join-Path $sanity.FullName 'telemetry.csv') --window (Join-Path $sanity.FullName 'workload-window.json') --output (Join-Path $sanity.FullName 'energy.json') | Out-Null

# Official Sysman is a bounded secondary probe, not the primary boundary.
& $SysmanProbe 1000 | Set-Content -LiteralPath (Join-Path $root 'sysman.json') -Encoding utf8

# Freeze a deterministic randomized/interleaved 10 OFF + 10 ON schedule before observing outcomes.
$conditions = @('OFF') * 10 + @('ON') * 10
$random = [Random]::new(570)
$conditions = $conditions | Sort-Object { $random.Next() }
$schedule = for ($i = 0; $i -lt $conditions.Count; $i++) { [ordered]@{ order = $i + 1; condition = $conditions[$i] } }
$schedule | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $root 'overhead_schedule.json') -Encoding utf8

$overheadDir = Join-Path $root 'overhead'
New-Item -ItemType Directory -Path $overheadDir | Out-Null
$results = @()
for ($i = 0; $i -lt $conditions.Count; $i++) {
    $condition = $conditions[$i]
    $prefix = '{0:D2}-{1}' -f ($i + 1), $condition.ToLowerInvariant()
    $stop = Join-Path $overheadDir "$prefix.telemetry.stop"
    $telemetryProcess = $null
    if ($condition -eq 'ON') {
        $telemetryProcess = Start-Process -FilePath $Collector -ArgumentList @(
            (Join-Path $overheadDir "$prefix.telemetry.csv"),
            (Join-Path $overheadDir "$prefix.telemetry.metadata.json"),
            '120', '100', $stop
        ) -RedirectStandardOutput (Join-Path $overheadDir "$prefix.telemetry.stdout.log") -RedirectStandardError (Join-Path $overheadDir "$prefix.telemetry.stderr.log") -WindowStyle Hidden -PassThru
        Start-Sleep -Milliseconds 1000
    }
    $stdout = Join-Path $overheadDir "$prefix.stdout.json"
    $stderr = Join-Path $overheadDir "$prefix.stderr.log"
    $qpcStart = [Diagnostics.Stopwatch]::GetTimestamp()
    $process = Start-Process -FilePath $LlamaBench -ArgumentList @(
        '-m',$draft,'-dev','Vulkan0','-ngl','99','-p','1024','-n','0','-r','20','-o','json','-fa','off'
    ) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -Wait -PassThru
    $qpcEnd = [Diagnostics.Stopwatch]::GetTimestamp()
    if ($telemetryProcess) {
        Start-Sleep -Milliseconds 500
        New-Item -ItemType File -Path $stop | Out-Null
        if (-not $telemetryProcess.WaitForExit(15000)) { $telemetryProcess.Kill($true) }
        if ($telemetryProcess.ExitCode -ne 0) { throw "Telemetry overhead collector failed at $prefix" }
        $telemetryProcess.Dispose()
    }
    if ($process.ExitCode -ne 0) { throw "Overhead workload failed at $prefix" }
    $bench = (Get-Content -LiteralPath $stdout -Raw | ConvertFrom-Json)[0]
    $results += [ordered]@{
        order = $i + 1
        condition = $condition
        process_elapsed_ns = [int64](($qpcEnd - $qpcStart) * 1000000000 / [Diagnostics.Stopwatch]::Frequency)
        llama_bench_avg_ns = [int64]$bench.avg_ns
        llama_bench_cv = if ($bench.avg_ns) { [double]$bench.stddev_ns / [double]$bench.avg_ns } else { $null }
        workload_exit_code = $process.ExitCode
    }
    $process.Dispose()
}
$results | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root 'overhead_results.json') -Encoding utf8
& $Python $overheadAnalysis --input (Join-Path $root 'overhead_results.json') --output (Join-Path $root 'overhead_analysis.json') | Out-Null

[ordered]@{
    schema = 'heterospec.b570.telemetry_qualification.v1'
    completed_at = (Get-Date).ToString('o')
    output_directory = $root
    sanity_directory = $sanity.FullName
    sampling_period_ms = 100
    overhead_schedule_seed = 570
    overhead_metric = 'llama-bench avg_ns for non-formal Qwen3-0.6B PP1024, 20 internal repetitions per process'
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root 'qualification_manifest.json') -Encoding utf8

"TELEMETRY_QUALIFICATION_COMPLETE`noutput=$root" | Set-Content -LiteralPath $status -Encoding utf8
Write-Output 'TELEMETRY_QUALIFICATION_COMPLETE'
