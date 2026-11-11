[CmdletBinding()]
param([Parameter(Mandatory = $true)][string] $OutputDirectory)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$python = Get-ChildItem -LiteralPath "$env:LOCALAPPDATA\Programs\Python" -Filter python.exe -Recurse | Select-Object -First 1 -ExpandProperty FullName
if (-not $python) { throw "Python runtime not found" }
$bin = "C:\hs\b\bin\Release"
$target = Join-Path $repo "models\gguf\Qwen3-8B-Q8_0.gguf"
$draft = Join-Path $repo "models\gguf\Qwen3-0.6B-Q8_0.gguf"
$config = Join-Path $repo "benchmarks\b570_backend_control\preregistration_v2.json"
$dataset = Join-Path $repo "datasets\humaneval\HumanEval.jsonl.gz"
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$adapterSamples = Get-Counter '\GPU Adapter Memory(*)\Dedicated Usage' -ErrorAction SilentlyContinue
$adapterRows = @($adapterSamples.CounterSamples | ForEach-Object {
    [ordered]@{ instance = $_.InstanceName; dedicated_mib = [Math]::Round($_.CookedValue / 1MB, 1) }
})
$b570Baseline = $adapterRows | Sort-Object dedicated_mib -Descending | Select-Object -First 1
$b570Instance = $b570Baseline.instance
$preflight = [ordered]@{
    captured_at = (Get-Date).ToString("o")
    adapter_memory = $adapterRows
    inferred_b570_dedicated_mib = $b570Baseline.dedicated_mib
    b570_total_mib = 10074
    inferred_b570_headroom_mib = [Math]::Round(10074 - $b570Baseline.dedicated_mib, 1)
    todest_processes = @(Get-Process -Name ToDesk -ErrorAction SilentlyContinue | Select-Object Id, ProcessName)
    remote_requirement = "ToDesk connection must be disconnected; any measured ToDesk GPU activity above 0.1% aborts the run."
}
$toDeskIds = @(Get-Process -Name ToDesk -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$engineSamples = @(Get-Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval 1 -MaxSamples 5 -ErrorAction SilentlyContinue).CounterSamples
$toDeskGpuAllAdapters = @($engineSamples | Where-Object {
    $path = $_.Path
    $toDeskIds | Where-Object { $path -match "pid_$($_)_" }
} | ForEach-Object { [ordered]@{ path = $_.Path; utilization_pct = $_.CookedValue } })
$toDeskGpu = @($toDeskGpuAllAdapters | Where-Object { $_.path -like "*$b570Instance*" })
$preflight["todesk_gpu_samples_all_adapters"] = $toDeskGpuAllAdapters
$preflight["todesk_gpu_samples"] = $toDeskGpu
$toDeskValues = @($toDeskGpu | ForEach-Object { [double]$_.utilization_pct })
$preflight["todesk_gpu_max_pct"] = if ($toDeskValues.Count) { ($toDeskValues | Measure-Object -Maximum).Maximum } else { 0 }
$preflight | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory "preflight.json") -Encoding utf8
if ($preflight.todesk_gpu_max_pct -gt 0.1) { throw "ToDesk GPU activity detected during formal preflight: $($preflight.todesk_gpu_max_pct)%" }

& $python (Join-Path $PSScriptRoot "b570_correctness_gate.py") --config $config --output (Join-Path $OutputDirectory "correctness.json") --llama-completion (Join-Path $bin "llama-completion.exe") --llama-speculative (Join-Path $bin "llama-speculative.exe") --tokenize (Join-Path $bin "llama-tokenize.exe") --target $target --draft $draft --dataset $dataset
$correctnessExit = $LASTEXITCODE
if ($correctnessExit -notin @(0, 3)) { throw "Correctness runner failed with exit $correctnessExit" }

& $python (Join-Path $PSScriptRoot "b570_verification_microbench.py") --config $config --exe (Join-Path $bin "llama-bench.exe") --model $target --output (Join-Path $OutputDirectory "verification.json")
$verificationExit = $LASTEXITCODE
if ($verificationExit -ne 0) { throw "Verification runner failed with exit $verificationExit" }

$summary = [ordered]@{ correctness_exit = $correctnessExit; verification_exit = $verificationExit; finished_at = (Get-Date).ToString("o") }
$summary | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory "stage-summary.json") -Encoding utf8
exit $correctnessExit
