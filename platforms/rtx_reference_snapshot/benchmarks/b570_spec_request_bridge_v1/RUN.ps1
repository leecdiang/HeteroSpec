$ErrorActionPreference='Stop'
$studyRoot='C:/hs/b570-spec-bridge-20261020200000'
$ledgerPath=Join-Path $studyRoot 'BUDGET_LEDGER.json'
if(Test-Path -LiteralPath $ledgerPath){throw 'Existing ledger: historical run cannot be restarted'}
$prior=Get-Content C:/hs/b570-gqa-av-preserve-20261020190000/BUDGET_LEDGER.json -Raw|ConvertFrom-Json
if([math]::Abs($prior.cumulative_charged_seconds-249.2473593) -gt 0.00000001){throw 'Prior ledger mismatch'}
$manifest=Get-Content (Join-Path $studyRoot 'BUILD_MANIFEST.json') -Raw|ConvertFrom-Json
foreach($f in $manifest.files){if((Get-FileHash -LiteralPath $f.path).Hash.ToLowerInvariant() -ne $f.sha256){throw ('Changed input '+$f.path)}}
if(300-$prior.cumulative_charged_seconds -lt 50){throw 'Insufficient 38s execution + cleanup/capture margin'}
$dest=Join-Path $studyRoot 'results'
if(Test-Path -LiteralPath $dest){throw 'Existing raw output'}
$ledger=[ordered]@{prior_cumulative_seconds=$prior.cumulative_charged_seconds;cap_seconds=300;status='STARTING';sessions=@()}
function Save-Ledger{[IO.File]::WriteAllText($ledgerPath,($ledger|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))}
Save-Ledger
$info=[Diagnostics.ProcessStartInfo]::new()
$info.FileName=Join-Path $studyRoot 'build/Release/spec_bridge.exe'
$info.ArgumentList.Add($dest)
$info.ArgumentList.Add('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf/Qwen3-8B-Q8_0.gguf')
$info.ArgumentList.Add('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf/Qwen3-0.6B-Q8_0.gguf')
$info.ArgumentList.Add((Join-Path $studyRoot 'INPUT.json'))
$info.WorkingDirectory=Join-Path $studyRoot 'build/Release'
$info.UseShellExecute=$false;$info.CreateNoWindow=$true
$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
foreach($k in @('GGML_VK_PERF_LOGGER','GGML_VK_PERF_LOGGER_CONCURRENT','GGML_VK_PERF_LOGGER_FREQUENCY')){[void]$info.Environment.Remove($k)}
$process=[Diagnostics.Process]::new();$process.StartInfo=$info
$r=[ordered]@{argv=@($info.FileName)+@($info.ArgumentList);prior_cumulative_seconds=$prior.cumulative_charged_seconds;started_utc=[DateTime]::UtcNow.ToString('o');deadline_seconds=38;status='STARTING'}
$watch=[Diagnostics.Stopwatch]::StartNew()
try{
 if(-not $process.Start()){throw 'start failed'}
 $r.pid=$process.Id;$r.os_start_utc=$process.StartTime.ToUniversalTime().ToString('o')
 $out=$process.StandardOutput.ReadToEndAsync();$err=$process.StandardError.ReadToEndAsync()
 $exited=$process.WaitForExit(38000);$r.deadline_kill_requested=-not $exited
 if(-not $exited){$process.Kill($true);$exited=$process.WaitForExit(5000)}
 $r.exit_observed=$exited
 if($exited){$r.exit_code=$process.ExitCode;$r.os_exit_utc=$process.ExitTime.ToUniversalTime().ToString('o')}
 $r.capture_complete=[Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($out,$err),5000)
 if($out.IsCompletedSuccessfully){[IO.File]::WriteAllText((Join-Path $studyRoot 'stdout.log'),$out.Result)}
 if($err.IsCompletedSuccessfully){[IO.File]::WriteAllText((Join-Path $studyRoot 'stderr.log'),$err.Result)}
 $r.status=if($exited -and $r.exit_code -eq 0 -and $r.capture_complete -and -not $r.deadline_kill_requested){'PROCESS_COMPLETED'}else{'STOPPED_FIRST_FAILURE'}
}catch{
 $r.status='WRAPPER_FAILED';$r.error=$_.Exception.Message
 try{if(-not $process.HasExited){$process.Kill($true);$r.exit_observed=$process.WaitForExit(5000)}}catch{$r.cleanup_error=$_.Exception.Message}
}finally{
 $watch.Stop();$r.charged_seconds=$watch.Elapsed.TotalSeconds
 $r.finished_utc=[DateTime]::UtcNow.ToString('o')
 $r.cumulative_charged_seconds=$prior.cumulative_charged_seconds+$r.charged_seconds
 $r.remaining_seconds=300-$r.cumulative_charged_seconds
 [IO.File]::WriteAllText((Join-Path $studyRoot 'PROCESS_RECEIPT.json'),($r|ConvertTo-Json -Depth 10))
 $ledger.sessions=@($r);$ledger.cumulative_charged_seconds=$r.cumulative_charged_seconds;$ledger.remaining_seconds=$r.remaining_seconds;$ledger.status=$r.status
 Save-Ledger;$process.Dispose()
}
$r|ConvertTo-Json -Depth 10
if($r.status -ne 'PROCESS_COMPLETED'){exit 1}
