param([Parameter(Mandatory=$true)][ValidateRange(0,2)][int]$Session)
$ErrorActionPreference='Stop'
$root='C:/hs/b570-spec-cost-20261020203000'
$ledgerPath=Join-Path $root 'BUDGET_LEDGER.json'
if($Session -eq 0){
 if(Test-Path -LiteralPath $ledgerPath){throw 'Existing ledger; no restart'}
 $old=Get-Content C:/hs/b570-spec-bridge-20261020200000/BUDGET_LEDGER.json -Raw|ConvertFrom-Json
 if([math]::Abs($old.cumulative_charged_seconds-285.6803089) -gt 1e-8){throw 'Prior charge mismatch'}
 $ledger=[ordered]@{study='B570_SPECULATIVE_REQUEST_COST';old_cumulative_seconds=285.6803089;new_study_cap_seconds=180;new_study_charged_seconds=0.0;new_study_remaining_seconds=180.0;sessions=@();status='STARTED'}
}else{
 $ledger=Get-Content $ledgerPath -Raw|ConvertFrom-Json -AsHashtable
 if($ledger.sessions.Count -ne $Session -or $ledger.status -ne 'PROCESS_COMPLETED'){throw 'Prior session incomplete or failed'}
}
function Save-Ledger{[IO.File]::WriteAllText($ledgerPath,($ledger|ConvertTo-Json -Depth 12))}
if($ledger.new_study_remaining_seconds -lt 60){throw 'Insufficient process+cleanup margin'}
$m=Get-Content (Join-Path $root 'BUILD_MANIFEST.json') -Raw|ConvertFrom-Json
foreach($f in $m.files){if((Get-FileHash -LiteralPath $f.path).Hash.ToLowerInvariant() -ne $f.sha256){throw ('Frozen input changed '+$f.path)}}
$dest=Join-Path $root "session-$Session"
if(Test-Path -LiteralPath $dest){throw 'Existing session output'}
Save-Ledger
$info=[Diagnostics.ProcessStartInfo]::new()
$info.FileName=Join-Path $root 'build/Release/spec_cost.exe'
$argv=@($dest,'C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf/Qwen3-8B-Q8_0.gguf','C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf/Qwen3-0.6B-Q8_0.gguf',(Join-Path $root 'INPUT.json'),(Join-Path $root 'QUALIFIED_REFERENCE.json'),"$Session")
foreach($a in $argv){$info.ArgumentList.Add($a)}
$info.WorkingDirectory=Join-Path $root 'build/Release';$info.UseShellExecute=$false;$info.CreateNoWindow=$true
$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
foreach($k in @('GGML_VK_PERF_LOGGER','GGML_VK_PERF_LOGGER_CONCURRENT','GGML_VK_PERF_LOGGER_FREQUENCY')){[void]$info.Environment.Remove($k)}
$p=[Diagnostics.Process]::new();$p.StartInfo=$info
$r=[ordered]@{session=$Session;argv=@($info.FileName)+$argv;started_utc=[DateTime]::UtcNow.ToString('o');deadline_seconds=50;status='STARTING'}
$watch=[Diagnostics.Stopwatch]::StartNew()
try{
 if(-not $p.Start()){throw 'start failed'}
 $r.pid=$p.Id;$r.os_start_utc=$p.StartTime.ToUniversalTime().ToString('o')
 $out=$p.StandardOutput.ReadToEndAsync();$err=$p.StandardError.ReadToEndAsync()
 $exited=$p.WaitForExit(50000);$r.deadline_kill_requested=-not $exited
 if(-not $exited){$p.Kill($true);$exited=$p.WaitForExit(5000)}
 $r.exit_observed=$exited
 if($exited){$r.exit_code=$p.ExitCode;$r.os_exit_utc=$p.ExitTime.ToUniversalTime().ToString('o')}
 $r.capture_complete=[Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($out,$err),5000)
 if($out.IsCompletedSuccessfully){[IO.File]::WriteAllText((Join-Path $root "session-$Session.stdout.log"),$out.Result)}
 if($err.IsCompletedSuccessfully){[IO.File]::WriteAllText((Join-Path $root "session-$Session.stderr.log"),$err.Result)}
 $r.status=if($exited -and $r.exit_code -eq 0 -and $r.capture_complete -and -not $r.deadline_kill_requested){'PROCESS_COMPLETED'}else{'STOPPED_FIRST_FAILURE'}
}catch{
 $r.status='WRAPPER_FAILED';$r.error=$_.Exception.Message
 try{if(-not $p.HasExited){$p.Kill($true);$r.exit_observed=$p.WaitForExit(5000)}}catch{$r.cleanup_error=$_.Exception.Message}
}finally{
 $watch.Stop();$r.charged_seconds=$watch.Elapsed.TotalSeconds;$r.finished_utc=[DateTime]::UtcNow.ToString('o')
 $ledger.new_study_charged_seconds+=$r.charged_seconds
 $ledger.new_study_remaining_seconds=180-$ledger.new_study_charged_seconds
 $ledger.all_history_cumulative_seconds=$ledger.old_cumulative_seconds+$ledger.new_study_charged_seconds
 $ledger.sessions+=@($r);$ledger.status=$r.status
 [IO.File]::WriteAllText((Join-Path $root "session-$Session.PROCESS_RECEIPT.json"),($r|ConvertTo-Json -Depth 12))
 Save-Ledger;$p.Dispose()
}
$r|ConvertTo-Json -Depth 12
if($r.status -ne 'PROCESS_COMPLETED'){exit 1}
$n=Get-Content (Join-Path $dest 'result.json') -Raw|ConvertFrom-Json
if($n.status -ne 'COST_SESSION_PASS' -or -not $n.normal_cleanup_returned){$ledger.status='STOPPED_NATIVE_CONTRACT';Save-Ledger;exit 1}
