$ErrorActionPreference='Stop'
$studyRoot='C:/hs/b570-qb-aa-balanced-20261020065000'
$release=Join-Path $studyRoot 'build/Release'
$ledgerPath=Join-Path $studyRoot 'BUDGET_LEDGER.json'
if(Test-Path -LiteralPath $ledgerPath){throw 'Existing budget ledger; refusing to restart'}
$ledger=[ordered]@{study='PR128_BALANCED_AA';prior_cumulative_seconds=4.7601167;total_budget_seconds=300;cumulative_charged_seconds=4.7601167;remaining_seconds=295.2398833;sessions=@();status='STARTED'}
function Save-Ledger{[IO.File]::WriteAllText($ledgerPath,($ledger|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))}
Save-Ledger
$allPassed=$true
for($session=0;$session -lt 3;$session++){
 if($ledger.remaining_seconds -lt 70){$ledger.status='STOPPED_BUDGET_ADMISSION';Save-Ledger;$allPassed=$false;break}
 $manifest=Get-Content -LiteralPath (Join-Path $studyRoot 'BUILD_MANIFEST.json') -Raw|ConvertFrom-Json
 foreach($file in $manifest.files){if((Get-FileHash -LiteralPath $file.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $file.sha256){throw ('Frozen input changed: '+$file.path)}}
 $dest=Join-Path $studyRoot "session-$session"
 if(Test-Path -LiteralPath $dest){throw 'Existing session directory; refusing to overwrite'}
 $info=[Diagnostics.ProcessStartInfo]::new()
 $info.FileName=Join-Path $release 'balanced.exe'
 $info.ArgumentList.Add($dest)
 $info.ArgumentList.Add([string]$session)
 $info.WorkingDirectory=$release
 $info.UseShellExecute=$false
 $info.CreateNoWindow=$true
 $info.RedirectStandardOutput=$true
 $info.RedirectStandardError=$true
 $process=[Diagnostics.Process]::new()
 $process.StartInfo=$info
 $receipt=[ordered]@{session=$session;argv=@($info.FileName,$dest,[string]$session);prior_cumulative_seconds=$ledger.cumulative_charged_seconds;started_utc=[DateTime]::UtcNow.ToString('o');deadline_seconds=60;status='STARTING'}
 $watch=[Diagnostics.Stopwatch]::StartNew()
 try{
  if(-not $process.Start()){throw 'Process start false'}
  $receipt.pid=$process.Id
  $receipt.os_start_utc=$process.StartTime.ToUniversalTime().ToString('o')
  $stdoutTask=$process.StandardOutput.ReadToEndAsync()
  $stderrTask=$process.StandardError.ReadToEndAsync()
  $exited=$process.WaitForExit(60000)
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
 if($native.status -ne 'EXPLORATORY_ALL_PASS' -or -not $native.normal_cleanup_returned){$ledger.status='STOPPED_FIRST_NATIVE_FAILURE';Save-Ledger;$allPassed=$false;break}
}
if($allPassed){$ledger.status='THREE_SESSIONS_COMPLETED';Save-Ledger}else{exit 1}
