param([Parameter(Mandatory=$true)][ValidateRange(0,7)][int]$Step)
$ErrorActionPreference='Stop'
$root='C:/hs/b570-draft-cpu-20261020'
$lp=Join-Path $root 'BUDGET_LEDGER.json'
$mode=if($Step -lt 4){'qual'}else{'time'}
$index=$Step%4
$limit=if($mode -eq 'qual'){180}else{600}
if($Step -eq 0){
 if(Test-Path $lp){throw 'No restart of existing study'}
 $old=Get-Content C:/hs/b570-formal-request-20261020/BUDGET_LEDGER.json -Raw|ConvertFrom-Json
 if([math]::Abs($old.all_history_cumulative_seconds-1817.8040152) -gt 1e-8){throw 'Historical charge changed'}
 $ledger=[ordered]@{study='B570_DRAFT_CPU_POLICY_V1';old_cumulative_seconds=1817.8040152;new_cap_seconds=3600;new_charged_seconds=0.0;sessions=@();status='STARTED'}
}else{
 $ledger=Get-Content $lp -Raw|ConvertFrom-Json -AsHashtable
 if($ledger.sessions.Count -ne $Step -or $ledger.status -ne 'PROCESS_COMPLETED'){throw 'Previous step failed/incomplete'}
}
if(3600-$ledger.new_charged_seconds -lt $limit+10){throw 'Need new prospective envelope; do not reset'}
if($mode -eq 'time'){
 foreach($i in 0..3){
  $n=Get-Content "$root/qual-$i/result.json" -Raw|ConvertFrom-Json
  if($n.status -ne 'QUALIFICATION_PASS'){throw 'Panel not qualified'}
 }
 if(-not(Test-Path "$root/QUALIFICATION_RECHECK.json")){throw 'CPU full panel recheck required'}
}
$m=Get-Content "$root/BUILD_MANIFEST.json" -Raw|ConvertFrom-Json
foreach($f in $m.files){if((Get-FileHash -LiteralPath $f.path).Hash.ToLowerInvariant() -ne $f.sha256){throw ('Frozen input changed '+$f.path)}}
$dest="$root/$mode-$index"
if(Test-Path $dest){throw 'Existing output'}
function Save-Ledger{[IO.File]::WriteAllText($lp,($ledger|ConvertTo-Json -Depth 12))}
Save-Ledger
$info=[Diagnostics.ProcessStartInfo]::new()
$info.FileName="$root/build/Release/draft_cpu.exe"
$argv=@($dest,'C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf/Qwen3-8B-Q8_0.gguf','C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/models/gguf/Qwen3-0.6B-Q8_0.gguf',"$root/INPUT_PANEL.json",$mode,"$index",$root)
foreach($a in $argv){$info.ArgumentList.Add($a)}
$info.WorkingDirectory="$root/build/Release";$info.UseShellExecute=$false;$info.CreateNoWindow=$true
$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
foreach($k in @('GGML_VK_PERF_LOGGER','GGML_VK_PERF_LOGGER_CONCURRENT','GGML_VK_PERF_LOGGER_FREQUENCY')){[void]$info.Environment.Remove($k)}
$p=[Diagnostics.Process]::new();$p.StartInfo=$info
$r=[ordered]@{step=$Step;mode=$mode;index=$index;argv=@($info.FileName)+$argv;started_utc=[DateTime]::UtcNow.ToString('o');deadline_seconds=$limit;status='STARTING'}
$watch=[Diagnostics.Stopwatch]::StartNew()
try{
 if(-not $p.Start()){throw 'start failed'}
 $r.pid=$p.Id;$r.os_start_utc=$p.StartTime.ToUniversalTime().ToString('o')
 $out=$p.StandardOutput.ReadToEndAsync();$err=$p.StandardError.ReadToEndAsync()
 $exited=$p.WaitForExit($limit*1000);$r.deadline_kill_requested=-not $exited
 if(-not $exited){$p.Kill($true);$exited=$p.WaitForExit(5000)}
 $r.exit_observed=$exited
 if($exited){$r.exit_code=$p.ExitCode;$r.os_exit_utc=$p.ExitTime.ToUniversalTime().ToString('o')}
 $r.capture_complete=[Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($out,$err),5000)
 if($out.IsCompletedSuccessfully){[IO.File]::WriteAllText("$root/$mode-$index.stdout.log",$out.Result)}
 if($err.IsCompletedSuccessfully){[IO.File]::WriteAllText("$root/$mode-$index.stderr.log",$err.Result)}
 $r.status=if($exited -and $r.exit_code -eq 0 -and $r.capture_complete -and -not $r.deadline_kill_requested){'PROCESS_COMPLETED'}else{'STOPPED_FIRST_FAILURE'}
 if($r.status -eq 'PROCESS_COMPLETED'){
  $n=Get-Content "$dest/result.json" -Raw|ConvertFrom-Json
  $expected=if($mode -eq 'qual'){'QUALIFICATION_PASS'}else{'TIMING_PASS'}
  if($n.status -ne $expected -or -not $n.normal_cleanup_returned){$r.status='STOPPED_NATIVE_CONTRACT'}
 }
}catch{
 $r.status='WRAPPER_FAILED';$r.error=$_.Exception.Message
 try{if(-not $p.HasExited){$p.Kill($true);$r.exit_observed=$p.WaitForExit(5000)}}catch{$r.cleanup_error=$_.Exception.Message}
}finally{
 $watch.Stop();$r.charged_seconds=$watch.Elapsed.TotalSeconds;$r.finished_utc=[DateTime]::UtcNow.ToString('o')
 $ledger.new_charged_seconds+=$r.charged_seconds;$ledger.all_history_cumulative_seconds=$ledger.old_cumulative_seconds+$ledger.new_charged_seconds
 $ledger.sessions+=@($r);$ledger.status=$r.status
 [IO.File]::WriteAllText("$root/$mode-$index.PROCESS_RECEIPT.json",($r|ConvertTo-Json -Depth 12))
 Save-Ledger;$p.Dispose()
}
$r|ConvertTo-Json -Depth 12
if($r.status -ne 'PROCESS_COMPLETED'){exit 1}
