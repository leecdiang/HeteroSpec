[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$RunRoot,[int]$GraceSeconds=120)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$python='C:\Users\DIANG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$bin='C:\hs\b\bin\Release'; $collector='C:\hs\pm\Release\b570_presentmon_telemetry.exe'
$config=Join-Path $repo 'benchmarks\b570_backend_control\preregistration_v2.json'; $target=Join-Path $repo 'models\gguf\Qwen3-8B-Q8_0.gguf'; $draft=Join-Path $repo 'models\gguf\Qwen3-0.6B-Q8_0.gguf'; $dataset=Join-Path $repo 'datasets\humaneval\HumanEval.jsonl.gz'
$status=Join-Path $repo 'work\b570\current_task_status.json'; $statusText=Join-Path $repo 'work\b570\current_task_status.txt'; $processed=Join-Path $RunRoot 'processed'; foreach($d in @($processed,(Join-Path $RunRoot 'stdout'),(Join-Path $RunRoot 'stderr'),(Join-Path $RunRoot 'telemetry'),(Join-Path $RunRoot 'raw'))){New-Item -ItemType Directory -Force -Path $d|Out-Null}
. (Join-Path $PSScriptRoot 'task_status_helpers.ps1')
function Status([string]$state,[string]$stage,[string]$detail){$value=[ordered]@{schema='heterospec.b570.formal-task.v1';run_id=(Split-Path $RunRoot -Leaf);state=$state;stage=$stage;detail=$detail;task_name='HeteroSpec_B570_Formal';main_pid=$PID;heartbeat_at=(Get-Date).ToString('o')}; Write-TaskStatus -JsonPath $status -TextPath $statusText -Status $value; Copy-Item -LiteralPath $status -Destination (Join-Path $RunRoot 'status.json') -Force}
function Wait-WithHeartbeat([int]$Seconds,[string]$state,[string]$stage,[string]$detail){$remaining=$Seconds; while($remaining -gt 0){Status $state $stage "$detail ($remaining seconds remaining)"; $slice=[Math]::Min(20,$remaining); Start-Sleep -Seconds $slice; $remaining-=$slice}}
$overall='RUNTIME_FAILURE'; $correctness='NOT_RUN'; $verification='NOT_RUN'; $failure=$null
try {
  Status 'GRACE_PERIOD' 'preflight' "Waiting $GraceSeconds seconds for ToDesk disconnect"
  Wait-WithHeartbeat $GraceSeconds 'GRACE_PERIOD' 'preflight' 'Waiting for ToDesk disconnect'
  $adapter=(Get-Counter '\GPU Adapter Memory(*)\Dedicated Usage' -ErrorAction SilentlyContinue).CounterSamples|Sort-Object CookedValue -Descending|Select-Object -First 1
  $pids=@(Get-Process ToDesk -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
  $samples=@(Get-Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval 1 -MaxSamples 5 -ErrorAction SilentlyContinue).CounterSamples
  $hits=@($samples|Where-Object{$path=$_.Path; $path -like "*$($adapter.InstanceName)*" -and @($pids|Where-Object{$path -match "pid_$($_)_"}).Count})
  $max=if($hits.Count){($hits.CookedValue|Measure-Object -Maximum).Maximum}else{0}
  [ordered]@{checked_at=(Get-Date).ToString('o');b570_instance=$adapter.InstanceName;todesk_gpu_max_pct=$max;samples=$hits}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $RunRoot 'todesk-disconnect-check.json') -Encoding utf8
  if($max -gt 0.1){throw "PRECONDITION_FAILURE: ToDesk B570 GPU activity $max%"}
  Status 'SETTLING' 'preflight' 'Disconnected check passed; 60 second preregistered settling interval'
  Wait-WithHeartbeat 60 'SETTLING' 'preflight' 'Disconnected idle settling interval'
  Status 'RUNNING' 'correctness' 'Six frozen prompts, baseline/speculative x3'
  & $python (Join-Path $PSScriptRoot 'b570_correctness_gate.py') --config $config --output (Join-Path $processed 'correctness.json') --run-root $RunRoot --status-file $status --collector $collector --llama-completion (Join-Path $bin 'llama-completion.exe') --llama-speculative (Join-Path $bin 'llama-speculative.exe') --tokenize (Join-Path $bin 'llama-tokenize.exe') --target $target --draft $draft --dataset $dataset 1> (Join-Path $RunRoot 'stdout\correctness-controller.log') 2> (Join-Path $RunRoot 'stderr\correctness-controller.log')
  $ce=$LASTEXITCODE
  if($ce -eq 0){
    $correctness='PASS'; Status 'RUNNING' 'verification' 'Correctness PASS; running preregistered V2 cells'
    & $python (Join-Path $PSScriptRoot 'b570_verification_microbench.py') --config $config --exe (Join-Path $bin 'llama-bench.exe') --model $target --output (Join-Path $processed 'verification.json') --collector $collector --run-root $RunRoot --status-file $status 1> (Join-Path $RunRoot 'stdout\verification-controller.log') 2> (Join-Path $RunRoot 'stderr\verification-controller.log')
    if($LASTEXITCODE -ne 0){throw "V2_RUNTIME_FAILURE exit=$LASTEXITCODE"}; $verification='PASS'; $overall='COMPLETE'
  } elseif($ce -eq 3){$correctness='FAIL';$verification='NOT_RUN_BY_PREREGISTERED_STOP_RULE';$overall='COMPLETE_STOP_RULE'}
  else {$correctness='CONFIGURATION_ERROR';throw "CORRECTNESS_CONFIGURATION_OR_RUNTIME_ERROR exit=$ce"}
} catch {$failure=$_|Out-String; if($failure -match 'PRECONDITION_FAILURE'){$overall='PRECONDITION_FAILURE'} elseif($correctness -eq 'CONFIGURATION_ERROR'){$overall='CONFIGURATION_ERROR'}; $failure|Set-Content (Join-Path $RunRoot 'stderr\controller-failure.log') -Encoding utf8}
finally {
  [ordered]@{overall_status=$overall;correctness=$correctness;verification=$verification;failure=$failure;finished_at=(Get-Date).ToString('o');humaneval30='NOT_RUN_BY_PREREGISTRATION_V2_SEPARATE_LATER_PHASE'}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $RunRoot 'stage-outcome.json') -Encoding utf8
  Status 'FINALIZING' 'archive' 'Generating reports, archive, commits, push, PR attempt, and shutdown'
  & $python (Join-Path $PSScriptRoot 'finalize_b570_formal.py') --repo $repo --run-root $RunRoot 1> (Join-Path $RunRoot 'stdout\finalizer.log') 2> (Join-Path $RunRoot 'stderr\finalizer.log')
  if($LASTEXITCODE -ne 0){
    [ordered]@{overall_status='FINALIZATION_FAILURE';formal_run_id=(Split-Path $RunRoot -Leaf);correctness=$correctness;V2_512=$null;V2_2048=$null;classification='UNCLASSIFIED';humaneval30_status='NOT_RUN_BY_PREREGISTRATION_V2_SEPARATE_LATER_PHASE';archive_status='FAILED_OR_PARTIAL';push_status='NOT_CONFIRMED';PR_url=$null;shutdown_scheduled=$true}|ConvertTo-Json|Set-Content (Join-Path $repo 'work\b570\FINAL_STATUS.json') -Encoding utf8
    "Finalization failure; evidence retained at $RunRoot; shutdown scheduled."|Set-Content (Join-Path $repo 'work\b570\FINAL_STATUS.txt') -Encoding utf8
    Start-Sleep -Seconds 60
    shutdown.exe /s /t 60 /c "HeteroSpec B570 formal experiment stopped; evidence preserved."
  }
}
