$ErrorActionPreference='Stop'
$pilotRoot='C:/hs/b570-qb-broadcast-20261020061400'
$release=Join-Path $pilotRoot 'build/Release'
$startInfo=[Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName=Join-Path $release 'cross.exe'
$startInfo.ArgumentList.Add((Join-Path $pilotRoot 'results'))
$startInfo.WorkingDirectory=$release
$startInfo.UseShellExecute=$false
$startInfo.CreateNoWindow=$true
$startInfo.RedirectStandardOutput=$true
$startInfo.RedirectStandardError=$true
$process=[Diagnostics.Process]::new()
$process.StartInfo=$startInfo
$receipt=[ordered]@{experiment='B570_QB_BATCH_BROADCAST_FIX_CROSS';argv=@($startInfo.FileName,(Join-Path $pilotRoot 'results'));started_utc=[DateTime]::UtcNow.ToString('o');gpu_process_wall_budget_seconds=298.2525353;prior_charged_seconds=1.7474647;cumulative_budget_seconds=300;kill_wait_seconds=270;model_actor_rtl='NONE';cpu8='UNSTARTED_UNQUALIFIED';status='STARTING'}
$watch=[Diagnostics.Stopwatch]::StartNew()
try {
 if(-not $process.Start()){throw 'Process start returned false'}
 $receipt.pid=$process.Id
 try {$receipt.os_start_utc=$process.StartTime.ToUniversalTime().ToString('o')}catch{$receipt.os_start_utc='UNKNOWN'}
 $stdoutTask=$process.StandardOutput.ReadToEndAsync()
 $stderrTask=$process.StandardError.ReadToEndAsync()
 $exited=$process.WaitForExit(270000)
 $receipt.deadline_kill_requested=-not $exited
 if(-not $exited){$process.Kill($true);$exited=$process.WaitForExit(5000)}
 $receipt.exit_observed=$exited
 if($exited){$receipt.exit_code=$process.ExitCode;try{$receipt.os_exit_utc=$process.ExitTime.ToUniversalTime().ToString('o')}catch{$receipt.os_exit_utc='UNKNOWN'}}
 $captureDone=[Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($stdoutTask,$stderrTask),5000)
 $receipt.capture_complete=$captureDone
 if($stdoutTask.IsCompletedSuccessfully){[IO.File]::WriteAllText((Join-Path $pilotRoot 'stdout.log'),$stdoutTask.Result,[Text.UTF8Encoding]::new($false))}
 if($stderrTask.IsCompletedSuccessfully){[IO.File]::WriteAllText((Join-Path $pilotRoot 'stderr.log'),$stderrTask.Result,[Text.UTF8Encoding]::new($false))}
 $receipt.status=if($exited -and $receipt.exit_code -eq 0 -and $captureDone -and -not $receipt.deadline_kill_requested){'PROCESS_COMPLETED'}else{'FAILED_OR_TIMEOUT'}
}catch{
 $receipt.status='WRAPPER_FAILED'
 $receipt.error=$_.Exception.Message
 try{if(-not $process.HasExited){$process.Kill($true);$receipt.exit_observed=$process.WaitForExit(5000)}}catch{$receipt.cleanup_error=$_.Exception.Message}
}finally{
 $watch.Stop()
 $receipt.elapsed_wall_seconds=$watch.Elapsed.TotalSeconds
 $receipt.finished_utc=[DateTime]::UtcNow.ToString('o')
 $receipt.cumulative_charged_seconds=1.7474647+$watch.Elapsed.TotalSeconds
 $receipt.within_300_second_budget=$receipt.cumulative_charged_seconds -le 300
 [IO.File]::WriteAllText((Join-Path $pilotRoot 'PROCESS_RECEIPT.json'),($receipt|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
 $process.Dispose()
 $receipt|ConvertTo-Json -Depth 6
}
if($receipt.status -ne 'PROCESS_COMPLETED' -or -not $receipt.within_300_second_budget){exit 1}
