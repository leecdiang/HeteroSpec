from pathlib import Path
import json,hashlib,shutil
r=Path(__file__).parent
pr={
"study":"B570_FORMAL_FINITE_PANEL_V1","uuid":"c4e01a7e-6450-48e1-b8b6-5b36c17d12bc",
"registered_before_gpu":True,"parent":"34787ab56f0ae8b533d18fe02db2d37e8ebb63a4",
"paper_plan":"PR130/7a209727f151f375c28653605f58252b6da77953: reference-preserving method, actual request migration, full costs, hardware only after strong software residual",
"authorization":"User requests formal experiment and conclusions; prior old balance explicitly removed as blocking limit. Preserve old historical charge401.2123575s.",
"scope":"Formal preregistered finite-panel study, four existing exposed HumanEval inputs; not new-input population confirmation; one machine/date; no E3 two-date claim.",
"input_selection":"Fixed IDs38,65,115,127 from existing PROMPT_TOKENS; lengths181,109,349,277. Chosen for short/long geometry before new outputs; not chosen by acceptance or new timing.",
"reference":"Prospective R_e: same frozen PR133 runtime, same models, explicit input IDs, greedy q1,64token CAP/EOG, serial prefill. New input/window reference never replaces prior R or extends old16token qualification.",
"qualification":{"processes":4,"order":"R then PQ then QB per input; no cost admission until all four pass","endpoint":"IDs,EOG,length,terminal,stop exact R/PQ/QB","full_logits":"All PQ/QB target and draft saved vectors byte exact including discarded verification rows","trace":"All PQ/QB proposal/accept/rollback/correction cycles exact","geometry":"actual q2,physical key256/512,GQA32/8,36 target layers on B570"},
"timing":{"processes":4,"warmup_per_process":4,"steady_requests_per_process":16,"total_steady_requests":64,"total_warmup_requests":16,
"arms":["R","PQ_A","PQ_B","QB"],"same_implementation":"PQ_A and PQ_B identical code","warmup":"Each arm executes old16token prompt once, in balanced order, all checked against PR133 reference; reported separately, never treated as free",
"orders":[["R","PQ_A","QB","PQ_B"],["PQ_A","PQ_B","R","QB"],["PQ_B","QB","PQ_A","R"],["QB","R","PQ_B","PQ_A"]],
"input_order":"cycle input index by process; arm order row=(process+input)%4. Each input/arm appears in each arm position once.",
"primary_window":"service_seconds: fresh context creation/graph reserve, both prefills when speculative, proposal/verify/host sample/state, final sync and context destruction. Excludes shared model loading, comparisons and disk writes.",
"secondary_window":"request_seconds: inside fresh contexts, includes prefills and generation. Both windows include full host logits copy/finite check and cycle-record work. R measured with draft model resident, no draft context.",
"cold":"First-use requests are explicit warmup records. Shared persistent driver caches not reset; no claim cold-boot measurement.",
"stages":"Existing per-decode synchronized wall durations, role/phase separated; no extra synchronization or node observer during timing. Residual host/other time remains unassigned; not GPU critical-path attribution."},
"analysis":{"primary":"Per-input geometric mean of QB/mean(PQ_A,PQ_B) service ratios over4 sessions; equal-input geometric mean. Request-only ratios reported separately.",
"secondary":"QB/R service ratio, draft economics; also per-input lengths/acceptances and actual geometry.",
"practical_screen":"All inputs qualified; primary reduction>2%, greater than largest per-input aggregate absolute A/A relative imbalance; QB faster than dualPQ in all4 process-level panel aggregates. Failure => no established practical panel benefit, not equivalence.",
"uncertainty":"Four fixed exposed inputs and4 sessions onone date; descriptive ranges and all paired blocks. No population CI/pvalue, no cross-date or held-out claim, no optional stopping for positive result.",
"failure":"First support/reference/capture failure stops entire panel before any further GPU execution; preserve failed input and unexecuted cells; no qualified speedup from partial pass subset."},
"execution":{"new_operational_envelope_seconds":3600,"qualification_deadline_seconds":240,"timing_deadline_seconds":600,"cleanup_margin_seconds":10,
"maximum_reserved_seconds":4*250+4*610,"old_cumulative_seconds":401.2123575,"no_actor_RTL_CPU8":True}
}
(r/"PREREGISTRATION.json").write_text(json.dumps(pr,indent=2))
run=r'''param([Parameter(Mandatory=$true)][ValidateRange(0,7)][int]$Step)
$ErrorActionPreference='Stop'
$root='C:/hs/b570-formal-request-20261020'
$lp=Join-Path $root 'BUDGET_LEDGER.json'
$mode=if($Step -lt 4){'qual'}else{'time'}
$index=$Step%4
$limit=if($mode -eq 'qual'){240}else{600}
if($Step -eq 0){
 if(Test-Path $lp){throw 'No restart of existing study'}
 $old=Get-Content C:/hs/b570-spec-cost-20261020203000/BUDGET_LEDGER.json -Raw|ConvertFrom-Json
 if([math]::Abs($old.all_history_cumulative_seconds-401.2123575) -gt 1e-8){throw 'Historical charge changed'}
 $ledger=[ordered]@{study='B570_FORMAL_FINITE_PANEL_V1';old_cumulative_seconds=401.2123575;new_cap_seconds=3600;new_charged_seconds=0.0;sessions=@();status='STARTED'}
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
$info.FileName="$root/build/Release/formal.exe"
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
'''
(r/"RUN.ps1").write_text(run)
print("Registered complete panel; GPU not started")
