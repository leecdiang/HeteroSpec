$ErrorActionPreference='Stop'
$studyRoot='C:/hs/b570-model-profile-final-20261020164000'
$release=Join-Path $studyRoot 'build/Release'
$ledgerPath=Join-Path $studyRoot 'BUDGET_LEDGER.json'
if(Test-Path -LiteralPath $ledgerPath){throw 'Existing budget ledger; refusing to restart'}
$ledger=[ordered]@{study='PR128_MODEL_PROFILE_CALIBRATION';prior_cumulative_seconds=195.7685326;total_budget_seconds=300;cumulative_charged_seconds=195.7685326;remaining_seconds=104.2314674;sessions=@();status='STARTED'}
function Save-Ledger{[IO.File]::WriteAllText($ledgerPath,($ledger|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))}
Save-Ledger
$allPassed=$true
for($session=0;$session -lt 3;$session++){
 if($ledger.remaining_seconds -lt 45){$ledger.status='STOPPED_BUDGET_ADMISSION';Save-Ledger;$allPassed=$false;break}
 $manifest=Get-Content -LiteralPath (Join-Path $studyRoot 'BUILD_MANIFEST.json') -Raw|ConvertFrom-Json
 foreach($file in $manifest.files){if((Get-FileHash -LiteralPath $file.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256){throw ('Frozen input changed: '+$file.path)}}
 $dest=Join-Path $studyRoot "session-$session"
 if(Test-Path -LiteralPath $dest){throw 'Existing session directory; refusing to overwrite'}
 $info=[Diagnostics.ProcessStartInfo]::new()
 $info.FileName=Join-Path $release 'model_bridge.exe'
 $info.ArgumentList.Add($dest)
 $modelPath='C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf/Qwen3-8B-Q8_0.gguf'
 $info.ArgumentList.Add($modelPath)
 $info.ArgumentList.Add((Join-Path $studyRoot 'INPUT.json'))
 $info.WorkingDirectory=$release
 foreach($key in @('GGML_VK_PERF_LOGGER','GGML_VK_PERF_LOGGER_CONCURRENT','GGML_VK_PERF_LOGGER_FREQUENCY')){[void]$info.Environment.Remove($key)}
 if($session -eq 1){$info.Environment['GGML_VK_PERF_LOGGER']='1';$info.Environment['GGML_VK_PERF_LOGGER_CONCURRENT']='1';$info.Environment['GGML_VK_PERF_LOGGER_FREQUENCY']='1000000'}
 $info.UseShellExecute=$false
 $info.CreateNoWindow=$true
 $info.RedirectStandardOutput=$true
 $info.RedirectStandardError=$true
 $process=[Diagnostics.Process]::new()
 $process.StartInfo=$info
 $receipt=[ordered]@{session=$session;argv=@($info.FileName,$dest,$modelPath,(Join-Path $studyRoot 'INPUT.json'));prior_cumulative_seconds=$ledger.cumulative_charged_seconds;started_utc=[DateTime]::UtcNow.ToString('o');deadline_seconds=30;status='STARTING'}
 $watch=[Diagnostics.Stopwatch]::StartNew()
 try{
  if(-not $process.Start()){throw 'Process start false'}
  $receipt.pid=$process.Id
  $receipt.os_start_utc=$process.StartTime.ToUniversalTime().ToString('o')
  $stdoutTask=$process.StandardOutput.ReadToEndAsync()
  $stderrTask=$process.StandardError.ReadToEndAsync()
  $exited=$process.WaitForExit(30000)
  $receipt.deadline_kill_requested=-not $exited
  if(-not $exited){$process.Kill($true);$exited=$process.WaitForExit(5000)}
  $receipt.exit_observed=$exited
  if($exited){$receipt.exit_code=$process.ExitCode;$receipt.os_exit_utc=$process.ExitTime.ToUniversalTime().ToString('o')}
  $captureDone=[Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($stdoutTask,$stderrTask),5000)
  $receipt.capture_complete=$captureDone
  if($stdoutTask.IsCompletedSuccessfully){[IO.File]::WriteAllText((Join-Path $studyRoot "session-$session.stdout.log"),$stdoutTask.Result,[Text.UTF8Encoding]::new($false))}
  if($stderrTask.IsCompletedSuccessfully){[IO.File]::WriteAllText((Join-Path $studyRoot "session-$session.stderr.log"),$stderrTask.Result,[Text.UTF8Encoding]::new($false))}
  $receipt.status=if($exited -and $receipt.exit_code -eq 0 -and $captureDone -and -not $receipt.deadline_kill_requested){'PROCESS_COMPLETED'}else{'FAILED_OR_TIMEOUT'}
 }catch{
  $receipt.status='WRAPPER_FAILED';$receipt.error=$_.Exception.Message
  try{if(-not $process.HasExited){$process.Kill($true);$receipt.exit_observed=$process.WaitForExit(5000)}}catch{$receipt.cleanup_error=$_.Exception.Message}
 }finally{
  $watch.Stop()
  $receipt.charged_seconds=$watch.Elapsed.TotalSeconds
  $receipt.finished_utc=[DateTime]::UtcNow.ToString('o')
  $ledger.cumulative_charged_seconds+=$receipt.charged_seconds
  $ledger.remaining_seconds=300-$ledger.cumulative_charged_seconds
  $receipt.cumulative_charged_seconds=$ledger.cumulative_charged_seconds
  $receipt.remaining_seconds=$ledger.remaining_seconds
  [IO.File]::WriteAllText((Join-Path $studyRoot "session-$session.PROCESS_RECEIPT.json"),($receipt|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
  $ledger.sessions+=@($receipt)
  Save-Ledger
  $process.Dispose()
 }
 $receipt|ConvertTo-Json -Depth 7
 if($receipt.status -ne 'PROCESS_COMPLETED' -or $ledger.remaining_seconds -lt 0){$ledger.status='STOPPED_FIRST_FAILURE';Save-Ledger;$allPassed=$false;break}
 $native=Get-Content -LiteralPath (Join-Path $dest 'result.json') -Raw|ConvertFrom-Json
 if($native.status -ne 'GEOMETRY_AND_OBSERVER_QUALIFIED' -or -not $native.normal_cleanup_returned){$ledger.status='STOPPED_FIRST_NATIVE_FAILURE';Save-Ledger;$allPassed=$false;break}
 $referenceRoot='C:/hs/b570-model-bridge-20261020162500/session-0'
 $matches=$true
 foreach($file in Get-ChildItem -LiteralPath $dest -Filter '*.f32'){
  if((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath (Join-Path $referenceRoot $file.Name)).Hash){$matches=$false;break}
 }
 if(-not $matches){$ledger.status='STOPPED_CROSS_PROCESS_LOGITS_MISMATCH';Save-Ledger;$allPassed=$false;break}

}
if($allPassed){$ledger.status='TAIL_FIXED_THREE_PROCESSES_COMPLETED';Save-Ledger}else{exit 1}
