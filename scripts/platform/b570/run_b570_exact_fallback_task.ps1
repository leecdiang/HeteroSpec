[CmdletBinding()]
param([Parameter(Mandatory)][string]$RunRoot,[int]$GraceSeconds=120)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
. (Join-Path $PSScriptRoot 'task_status_helpers.ps1')
$status=Join-Path $RunRoot 'status.json'; $statusText=Join-Path $RunRoot 'status.txt'
function Status([string]$state,[string]$stage,[string]$detail){$v=[ordered]@{schema='heterospec.b570.exact-fallback-task.v1';run_id=(Split-Path $RunRoot -Leaf);state=$state;stage=$stage;detail=$detail;task_name='HeteroSpec_B570_ExactFallback';main_pid=$PID;heartbeat_at=(Get-Date).ToString('o')};Write-TaskStatus $status $statusText $v}
function Wait-Heartbeat([int]$seconds,[string]$stage,[string]$detail){while($seconds -gt 0){Status 'WAITING' $stage "$detail ($seconds seconds remaining)";$n=[Math]::Min(20,$seconds);Start-Sleep $n;$seconds-=$n}}
$python='C:\Users\DIANG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe';$bin='C:\hs\b\bin\Release';$collector='C:\hs\pm\Release\b570_presentmon_telemetry.exe'
$target=Join-Path $repo 'models\gguf\Qwen3-8B-Q8_0.gguf';$draft=Join-Path $repo 'models\gguf\Qwen3-0.6B-Q8_0.gguf';$dataset=Join-Path $repo 'datasets\humaneval\HumanEval.jsonl.gz'
try{
  Wait-Heartbeat $GraceSeconds 'disconnect-grace' 'Waiting for ToDesk disconnect'
  $adapter=(Get-Counter '\GPU Adapter Memory(*)\Dedicated Usage' -ErrorAction SilentlyContinue).CounterSamples|Sort-Object CookedValue -Descending|Select-Object -First 1
  $pids=@(Get-Process ToDesk -ErrorAction SilentlyContinue|Select-Object -ExpandProperty Id)
  $samples=@(Get-Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval 1 -MaxSamples 5 -ErrorAction SilentlyContinue).CounterSamples
  $hits=@($samples|Where-Object{$path=$_.Path;$path -like "*$($adapter.InstanceName)*" -and @($pids|Where-Object{$path -match "pid_$($_)_"}).Count})
  $max=if($hits.Count){($hits.CookedValue|Measure-Object -Maximum).Maximum}else{0}
  [ordered]@{checked_at=(Get-Date).ToString('o');adapter=$adapter.InstanceName;todesk_b570_gpu_max_pct=$max;samples=$hits}|ConvertTo-Json -Depth 6|Set-Content (Join-Path $RunRoot 'todesk-disconnect-check.json') -Encoding utf8
  if($max -gt 0.1){throw "PRECONDITION_FAILURE: ToDesk B570 activity $max%"}
  Wait-Heartbeat 60 'idle-settling' 'Disconnected idle settling'
  Status 'RUNNING' 'exact-fallback-validation' 'V2_exact then frozen HumanEval30 serialized fallback'
  $saved=$ErrorActionPreference;$ErrorActionPreference='Continue'
  & $python (Join-Path $PSScriptRoot 'b570_exact_fallback_validation.py') --config (Join-Path $repo 'benchmarks\b570_backend_control\exact_fallback_validation_v1.json') --base-config (Join-Path $repo 'benchmarks\b570_backend_control\preregistration_v2.json') --run-root $RunRoot --status $status --llama-completion (Join-Path $bin 'llama-completion.exe') --llama-speculative (Join-Path $bin 'llama-speculative.exe') --tokenize (Join-Path $bin 'llama-tokenize.exe') --bench (Join-Path $bin 'llama-bench.exe') --target $target --draft $draft --dataset $dataset --collector $collector 1> (Join-Path $RunRoot 'stdout\controller.log') 2> (Join-Path $RunRoot 'stderr\controller.log')
  $code=$LASTEXITCODE;$ErrorActionPreference=$saved;if($code -ne 0){throw "EXACT_FALLBACK_CONTROLLER_FAILURE exit=$code"}
  Status 'FINALIZING' 'reports-archive-publish' 'Generating reports, archive, commits, push, and final status'
  $ErrorActionPreference='Continue'; & $python (Join-Path $PSScriptRoot 'finalize_b570_exact_fallback.py') --repo $repo --run-root $RunRoot 1> (Join-Path $RunRoot 'stdout\finalizer.log') 2> (Join-Path $RunRoot 'stderr\finalizer.log')
  $code=$LASTEXITCODE;$ErrorActionPreference=$saved;if($code -ne 0){throw "EXACT_FALLBACK_FINALIZER_FAILURE exit=$code"}
  $fp=Join-Path $repo 'work\b570\EXACT_FALLBACK_FINAL_STATUS.json';$final=Get-Content $fp -Raw|ConvertFrom-Json;$final.shutdown_status='SCHEDULED_60_SECONDS';$final|ConvertTo-Json -Depth 8|Set-Content $fp -Encoding utf8
  $final|ConvertTo-Json -Depth 8|Set-Content (Join-Path $repo 'work\b570\EXACT_FALLBACK_FINAL_STATUS.txt') -Encoding utf8
  Status 'COMPLETE' 'done' 'Exact fallback validation complete; automatic shutdown scheduled in 60 seconds'
  Stop-ScheduledTask -TaskName 'HeteroSpec_B570_ExactFallback_Watchdog' -ErrorAction SilentlyContinue
  shutdown.exe /s /t 60 /c "HeteroSpec B570 exact fallback validation completed; results preserved."
  exit 0
}catch{
  $message=$_|Out-String;$message|Set-Content (Join-Path $RunRoot 'stderr\task-failure.log') -Encoding utf8
  Status 'FAILED_INFRASTRUCTURE_OR_CONFIGURATION' 'failed' $message
  exit 1
}
