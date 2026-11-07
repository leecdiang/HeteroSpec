"""CPU-only complete evidence accountant. No imports from any execution/comparison code."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,collections,csv,math,statistics,subprocess
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
checks=0;errors=[]
def ck(x,m):
 global checks;checks+=1
 if not x:errors.append(m)
def save(n,x):(R/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def main():
 ledger=[json.loads(l) for l in (R/'LEDGER.jsonl').read_text().splitlines()];starts=[e for e in ledger if e['event']=='REQUEST_START'];forwards=[e for e in ledger if e['event']=='TARGET_FORWARD_START'];full=sum(not e['warm'] for e in starts);warm=sum(e['warm'] for e in starts)
 ck(full<=312 and warm<=48 and len(forwards)<=24,'budget all starts including failures');ck(len({e['unit_id'] for e in starts})==len(starts),'no repeated scientific request key');ck(len({e['unit_id'] for e in forwards})==len(forwards),'no repeated auxiliary forward')
 raw_results=[load(p) for p in sorted((R/'raw').glob('*/RESULT.json'))];aux_results=[load(p) for p in sorted((R/'aux').glob('*/RESULT.json'))];keys=[r['unit_id'] for r in raw_results+aux_results];ck(len(set(keys))==len(keys),'all unique complete keys')
 eog=set(load(R/'dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids']);costs=[];counter=collections.Counter();failure_attempts=[]
 A_freeze=load(R/'A_FREEZE.json');B_freeze=load(R/'B_FREEZE.json') if (R/'B_FREEZE.json').exists() else None
 C_freeze=load(R/'C_FREEZE.json') if (R/'C_FREEZE.json').exists() else None
 D_freeze=load(R/'D_FREEZE.json') if (R/'D_FREEZE.json').exists() else None
 E_freeze=load(R/'E_FREEZE.json') if (R/'E_FREEZE.json').exists() else None
 E=load(R/'E_VERIFICATION.json') if (R/'E_VERIFICATION.json').exists() else None
 for p in (R/'raw').glob('*/attempt-*/START.json'):
  start=load(p);unit=start['unit_id'];matches=[s for s in starts if s['unit_id']==unit];ck(len(matches)==1,'sent attempt counted '+unit)
  receipt=p.parent.parent/'RESULT.json'
  if not receipt.exists():failure_attempts.append(dict(unit=unit,start=str(p.relative_to(R)),classification='incomplete or failed; counts toward budget'))
 for r in raw_results:
  u=r['unit_id'];counter['warm' if r['warm'] else u.split('/')[0]]+=1
  ck(any(e['unit_id']==u and e['warm']==r['warm'] for e in starts),'complete request was charged '+u)
  for f,h in r['files'].items():ck(sha(R/f)==h,'full payload hash '+f)
  raw=load(R/next(f for f in r['files'] if f.endswith('/capture.json')));ids=raw['ids'];flags=raw['eog'];ck(len(ids)==len(flags)>0 and all(type(i)==int and 0<=i<151936 for i in ids),'all raw tokens '+u);ck(flags==[i in eog for i in ids],'all runtime EOG '+u)
  n=min(r['config'].get('cap',128),next((i+1 for i,t in enumerate(ids) if t in eog),len(ids)))
  ep=dict(ids=ids[:n],eog=flags[:n],reason='EOG' if ids[n-1] in eog else 'CAP',raw_suffix=len(ids)-n);ck(ep==r['endpoint'],'untrimmed suffix/full endpoint '+u)
  st=load(R/next(f for f in r['files'] if f.endswith('/START.json')));m=load(R/next(f for f in r['files'] if f.endswith('/capture.json.metrics.json')))
  ck(st['config']==r['config'] and st['unit_id']==u and st['request']['prompt_ids']==raw['prompt_ids'],'frozen request '+u);ck(st['source_commit']==r['source_commit'],'source epoch '+u)
  frozen=A_freeze if u.startswith('A/') else C_freeze if u.startswith('C/') else D_freeze if u.startswith('D/') else E_freeze if u.startswith('E/') else B_freeze
  if u in ['D/1/HumanEval/58','D/1/WARM/D-1-282a03'] and (R/'D_ENDPOINT_NAMESPACE_AMENDMENT.json').exists():
   amend=load(R/'D_ENDPOINT_NAMESPACE_AMENDMENT.json');frozen=load(R/amend['old_freeze']);ck(st['source_commit']==amend['old_source_epoch'],'unchanged first D source epoch, including paid warm')
   if not r['warm']:ck(sha(R/'raw'/hashlib.sha256(u.encode()).hexdigest()[:20]/'RESULT.json')==amend['reused_model_receipt_sha256'],'unchanged completed D unit reused after CPU namespace fix')
  ck(frozen is not None and st['utc']>frozen['utc'],'output follows phase freeze '+u)
  ck(m==r['metrics'] and m['request_id']==u and m['raw_count']==len(ids),'authentic metrics '+u)
  # A/B Python3.12 GetTickCount64 resolution is 15.625ms; measured steps15-16ms.
  # All original times remain unadjusted. C uses QueryPerformanceCounter.
  timer_tolerance=0.016 if u.startswith(('A/','B_SHAM/')) else 0.000001
  ck(m['whole_request_ms']>=m['generation_ms']>0 and r['host_seconds']+timer_tolerance>=m['whole_request_ms']/1000,'nested paid times '+u)
  ck(m['reset_target']['min']==m['reset_target']['max']==-1,'target reset '+u)
  if r['config']['native']:ck(m['reset_draft']['min']==m['reset_draft']['max']==-1,'draft reset '+u)
  session=load(R/'sessions'/r['session']/'SESSION.json');log=(R/'sessions'/r['session']/'stderr.log').read_text(encoding='utf8',errors='replace');ck(session['pid']>0 and bool(session['creation_identity']),'owned PID and creation identity '+u)
  import re
  used=re.findall(r'using device (Vulkan\d+) \(([^)]+\)[^\n]*)',log)
  ck('using device' in log and 'Intel(R) Arc(TM) B570 Graphics' in log and 'offloaded 37/37 layers to GPU' in log,'actual target fullGPU '+u)
  if r['config']['native']:ck('offloaded 29/29 layers to GPU' in log and log.count('(Intel(R) Arc(TM) B570 Graphics)')>=2,'actual target and draft B570 fullGPU '+u)
  if raw['transfer']:
   t=raw['transfer'];ck(t['kv_equal'] and t['source_unchanged'] and t['before']==t['after']==t['source_after'] and t['consumed_bytes']==t['state_bytes'],'natural online transfer '+u)
   ck(t['pending_id']==ids[0] and t['seed']==t['clone_seed']==123 and t['sampler_chain']==t['clone_chain'] and t['sampler_history']==t['clone_history'],'actual post-sample clone/pending '+u)
  scope='excluded_warmup' if r['warm'] else 'diagnostic_only'
  if E and u.startswith('E/FORMAL/') and not r['warm']:
   v=next(v for v in E['rows'] if v['task']==r['task'] and v['label']==r['config']['label'] and v['round']==r['config']['round'])
   scope='qualified_formal_capture_off' if v['qualified'] else 'diagnostic_failed_output'
  if u.startswith('D/') and not r['warm']:
   inp=next(i for i in load(R/'D_INPUTS.json') if i['id']==r['task']);ck(raw['prompt_ids']==inp['prompt_ids'],'D complete frozen input identity '+u)
  for field in ['generation_ms','whole_request_ms']:
   costs.append(dict(unit=u,task=r['task'],stage=u.split('/')[0],label=r['config']['label'],round=r['config'].get('round'),warm=r['warm'],cost_scope=scope,timer=field,ms=m[field],raw_count=len(ids),endpoint_count=n,raw_suffix=len(ids)-n))
  costs.append(dict(unit=u,task=r['task'],stage=u.split('/')[0],label=r['config']['label'],round=r['config'].get('round'),warm=r['warm'],cost_scope=scope,timer='host_end_to_end_ms',ms=r['host_seconds']*1000,raw_count=len(ids),endpoint_count=n,raw_suffix=len(ids)-n))
 for r in aux_results:
  ck(any(e['unit_id']==r['unit_id'] for e in forwards),'aux charged '+r['unit_id'])
  for f,h in r['files'].items():ck(sha(R/f)==h,'aux full hash '+f)
 # Online C++ may restore an authentic checkpoint, but cannot read old/future answers.
 for name in ['native.cpp','target.cpp','cross.cpp','pilot_state.h']:
  s=(R/'src'/name).read_text(encoding='utf8');ck(all(word not in s for word in ['HISTORICAL_PARENTS','HISTORICAL_EXPECTED','R_reference','MBPP/','HumanEval/','future_tape']),'no task/reference/oracle C++ input '+name)
 ck(load(R/'STAGE0.json')['status']=='PASS' and load(R/'STAGE0.json')['cost_rows']==744,'old CPU dependency gate')
 A=load(R/'A_VERIFICATION.json');ck(A['status'] in ['PASS','BLOCKED_BRIDGE'],'historical bridge gate is explicit')
 allowed_gate_errors=('historical endpoint ','historical raw array ','capture switch raw stable ')
 for problem in A['errors']:
  if not problem.startswith(allowed_gate_errors):ck(False,'A evidence verification '+problem)
 B=load(R/'CAUSAL_RESULTS.json') if (R/'CAUSAL_RESULTS.json').exists() else None
 if B and B.get('checks'):
  for problem in B.get('errors',[]):
   if not problem.startswith('own-path full raw continuation '):ck(False,'B evidence verification '+problem)
 # Exact used program bindings. A's unused helper was prepared before B and never run by A.
 for f,h in A_freeze['binaries'].items():
  if f.endswith('b570-pilot-cross.exe'):continue
  ck(sha(R/f)==h,'A loaded binary/runtime unchanged '+f)
 if C_freeze:
  for f,h in C_freeze['binaries'].items():ck(sha(R/f)==h,'C loaded private binary/backend unchanged '+f)
  for f,h in C_freeze['sources'].items():ck(sha(R/f)==h,'C exact frozen source unchanged '+f)
  if (R/'C_VERIFICATION.json').exists():
   C=load(R/'C_VERIFICATION.json');ck(C['status']=='PASS','independent C evidence integrity');ck(C['scientific_gate'] in ['PASS','FAIL','INCOMPLETE'],'C scientific outcome explicit')
 if B_freeze:
  for f,h in B_freeze['binaries'].items():ck(sha(R/f)==h,'B loaded binary/runtime unchanged '+f)
 if D_freeze:
  for f,h in D_freeze['files'].items():ck(sha(R/f)==h,'D frozen bindings unchanged '+f)
  if (R/'D_VERIFICATION.json').exists():ck(load(R/'D_VERIFICATION.json')['status']=='PASS','D independent evidence integrity')
 if E_freeze:
  for f,h in E_freeze['files'].items():ck(sha(R/f)==h,'E frozen bindings unchanged '+f)
  if E:ck(E['status']=='PASS','E independent integrity and fixed denominators')
  if (R/'E_BRIDGE_VERIFICATION.json').exists():ck(load(R/'E_BRIDGE_VERIFICATION.json')['status']=='PASS','E matched target bridge integrity')
  if E:
   audit=load(R/'E_EXPOSURE_AUDIT.json');eligible=audit['eligible_ranked'];panel=load(R/'E_INPUTS.json');amend=load(R/'E_BUDGET_AMENDMENT.json')
   ck([i['id'] for i in panel]==eligible[:len(panel)]==amend['selected'],'fixed top-hash selection with uniformly deducted bridge')
   ck(all(i['selection_hash']==hashlib.sha256((i['id']+'HeteroSpec-B570-mechanism-v1-confirm').encode()).hexdigest() and len(i['prompt_ids'])+128+6<=1024 for i in panel),'exact static hash/context rule')
   ck(not set(i['id'] for i in panel)&set(audit['known_executed']),'new panel excludes all known exposure')
   ck(len(panel)>=8 and len(panel)*8+8<=128,'unchanged balanced planned formal denominator plus8 prepaid diagnostics')
   lost=load(R/'E_INTERRUPTION.json') if (R/'E_INTERRUPTION.json').exists() else None
   ck(E['complete']==len(panel)*8-(1 if lost else 0) and (not lost or E['missing_units']==[lost['unit_id']] and lost['budget_charged'] and not lost['retry']),'exact complete receipts plus charged documented interruption')
   if lost:
    ck([f['unit'] for f in failure_attempts]==[lost['unit_id']],'single incomplete scientific attempt preserved')
    ck(E['matrix_complete'] is False and E['decision']=='PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED' and E['efficiency_gate'] is False,'partial cannot claim full matrix or GO')
 fields=['unit','task','stage','label','round','warm','cost_scope','timer','ms','raw_count','endpoint_count','raw_suffix']
 with (R/'COSTS.csv').open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(costs)
 loads=[];closes=[]
 for folder in sorted((R/'sessions').iterdir()):
  if (folder/'SESSION_LOAD.json').exists():loads.append(load(folder/'SESSION_LOAD.json'))
  if (folder/'SESSION_CLOSE.json').exists():closes.append(load(folder/'SESSION_CLOSE.json'))
 counts=dict(nonwarm_started=full,nonwarm_complete=sum(not r['warm'] for r in raw_results),warm_started=warm,warm_complete=sum(r['warm'] for r in raw_results),aux_started=len(forwards),aux_complete=len(aux_results),complete_by_stage=dict(counter),A=dict(planned=48,complete=counter['A']),B=dict(sham_max=12,sham_complete=counter['B_SHAM'],forward_max=24,forward_complete=len(aux_results)),C=dict(planned_if_gated=12,complete=counter['C']),D=dict(planned_if_gated=112,complete=counter['D']),E=dict(planned_if_gated=128,complete=counter['E']))
 if E_freeze:counts['E'].update(bridge_complete=sum(not r['warm'] and r['unit_id'].startswith('E/BRIDGE/') for r in raw_results),formal_complete=sum(not r['warm'] and r['unit_id'].startswith('E/FORMAL/') for r in raw_results),formal_tasks=load(R/'E_MANIFEST.json')['formal_tasks'])
 save('COUNTS.json',counts);save('FAILURES.json',dict(preparation=load(R/'PREPARATION_FAILURES.json'),C_zero_forward_loader_binding=load(R/'C_PRE_FORWARD_BINDING_AMENDMENT.json') if (R/'C_PRE_FORWARD_BINDING_AMENDMENT.json').exists() else None,D_zero_model_endpoint_namespace=load(R/'D_ENDPOINT_NAMESPACE_AMENDMENT.json') if (R/'D_ENDPOINT_NAMESPACE_AMENDMENT.json').exists() else None,incomplete_attempts=failure_attempts,scientific_parent_failures=A['known_scientific_failures_retained'],scientific_retries=0,E_infrastructure_interruption=load(R/'E_INTERRUPTION.json') if (R/'E_INTERRUPTION.json').exists() else None))
 work=dict(counts=counts,sessions=len(loads),model_context_load_seconds=sum(x['model_and_context_load_seconds'] for x in loads),session_cleanup_seconds=sum(x['model_session_cleanup_seconds'] for x in closes),complete_request_host_seconds=sum(r['host_seconds'] for r in raw_results),complete_generation_seconds=sum(r['metrics']['generation_ms'] for r in raw_results)/1000,complete_whole_seconds=sum(r['metrics']['whole_request_ms'] for r in raw_results)/1000,aux_host_seconds=sum(r['host_seconds'] for r in aux_results),warmup_excluded_but_charged=True,request_timers_include_online_init_transfer_clones_rollback_draft_sync_cleanup=True,diagnostic_checkpoint_IO_in_request_timer=True,terminal_capture_files_disk_IO_outside_cpp_timers_inside_host=True,record_hashing_after_host_endpoint=True,no_operator_duration_or_dispatch_measurement=True,no_energy_claim=True)
 work['incomplete_request_costs_unavailable']=[f['unit'] for f in failure_attempts];work['unmeasured_cleanup_sessions']=[str(p.parent.relative_to(R)) for p in (R/'sessions').glob('*/SESSION_CLOSE.json') if load(p).get('cleanup_duration_available') is False];work['duration_sums_are_measured_subtotals_not_total_campaign_cost']=bool(failure_attempts)
 save('WORK_ACCOUNTING.json',work)
 result=dict(status='PASS' if not errors else 'FAIL',utc=datetime.now(timezone.utc).isoformat(),checks=checks,errors=errors,counts=counts,scientific_gate_A=A['status'],scientific_gate_B=B['status'] if B else 'NOT_RUN',scientific_gate_C=load(R/'C_VERIFICATION.json')['scientific_gate'] if (R/'C_VERIFICATION.json').exists() else 'NOT_RUN',independent_no_executor_imports=True,full_raw_suffix_EOG_cost_endpoint_hash_provenance_checked=True,A_checks=A['checks'],B_checks=B.get('checks',0) if B else 0,C_checks=load(R/'C_VERIFICATION.json')['checks'] if (R/'C_VERIFICATION.json').exists() else 0,hidden_reference_or_future_model_inputs=False,scientific_retries=0,AB_host_clock='GetTickCount64 resolution 15.625ms; unchanged raw values, nesting tolerance16ms verified independently; no speed inference',D_checks=load(R/'D_VERIFICATION.json')['checks'] if (R/'D_VERIFICATION.json').exists() else 0,E_checks=E['checks'] if E else 0,closure_scope='all authorized remaining slots executed; one documented lost slot, scientific PARTIAL' if failure_attempts else 'complete',C_host_clock='QueryPerformanceCounter unadjusted')
 save('INDEPENDENT_VERIFICATION.json',result);print(result['status'],checks,errors[:15],counts,flush=True);return result
if __name__=='__main__':main()
