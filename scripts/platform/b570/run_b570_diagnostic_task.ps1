[CmdletBinding()]
param([Parameter(Mandatory)][string]$RunRoot,[int]$GraceSeconds=120)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
. (Join-Path $PSScriptRoot 'task_status_helpers.ps1')
$status=Join-Path $RunRoot 'status.json'; $statusText=Join-Path $RunRoot 'status.txt'
function Status([string]$state,[string]$stage,[string]$detail){$v=[ordered]@{schema='heterospec.b570.diagnostic-task.v1';run_id=(Split-Path $RunRoot -Leaf);state=$state;stage=$stage;detail=$detail;task_name='HeteroSpec_B570_Diagnostic';main_pid=$PID;heartbeat_at=(Get-Date).ToString('o')};Write-TaskStatus $status $statusText $v}
function Wait-Heartbeat([int]$seconds,[string]$stage,[string]$detail){while($seconds -gt 0){Status 'WAITING' $stage "$detail ($seconds seconds remaining)";$n=[Math]::Min(20,$seconds);Start-Sleep $n;$seconds-=$n}}
$python='C:\Users\DIANG\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'; $bin='C:\hs\b\bin\Release'; $collector='C:\hs\pm\Release\b570_presentmon_telemetry.exe'
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
  Status 'RUNNING' 'diagnostic-extension' 'V2_raw then frozen HumanEval30 then the single preregistered fallback'
  & $python (Join-Path $PSScriptRoot 'b570_diagnostic_extension.py') --diagnostic-config (Join-Path $repo 'benchmarks\b570_backend_control\diagnostic_extension_v1.json') --base-config (Join-Path $repo 'benchmarks\b570_backend_control\preregistration_v2.json') --run-root $RunRoot --status $status --llama-completion (Join-Path $bin 'llama-completion.exe') --llama-speculative (Join-Path $bin 'llama-speculative.exe') --tokenize (Join-Path $bin 'llama-tokenize.exe') --bench (Join-Path $bin 'llama-bench.exe') --target $target --draft $draft --dataset $dataset --collector $collector 1> (Join-Path $RunRoot 'stdout\diagnostic-controller.log') 2> (Join-Path $RunRoot 'stderr\diagnostic-controller.log')
  if($LASTEXITCODE -ne 0){throw "DIAGNOSTIC_CONTROLLER_FAILURE exit=$LASTEXITCODE"}
  Status 'FINALIZING' 'reports-archive-publish' 'Generating reports, archive, checksums, commits, push, and PR'
  & $python (Join-Path $PSScriptRoot 'finalize_b570_diagnostic.py') --repo $repo --run-root $RunRoot 1> (Join-Path $RunRoot 'stdout\diagnostic-finalizer.log') 2> (Join-Path $RunRoot 'stderr\diagnostic-finalizer.log')
  if($LASTEXITCODE -ne 0){throw "DIAGNOSTIC_FINALIZER_FAILURE exit=$LASTEXITCODE"}
  Status 'COMPLETE' 'done' 'Diagnostic extension complete; automatic shutdown disabled'
  exit 0
}catch{
  $message=$_|Out-String;$message|Set-Content (Join-Path $RunRoot 'stderr\task-failure.log') -Encoding utf8
  Status 'FAILED_INFRASTRUCTURE_OR_CONFIGURATION' 'failed' $message
  exit 1
}
