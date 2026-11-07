"""Frozen core B/C/anchor/D campaign; gates use complete observed outputs only."""
from pathlib import Path
import json,subprocess,sys,hashlib,statistics,math,time,os
from datetime import datetime,timezone
ROOT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
 p=Path(p);tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n');os.replace(tmp,p)
def eq(a,b):return all(a[k]==b[k] for k in ['ids','eog','reason'])
def stage(name,sessions):
 begin=time.monotonic()
 path=ROOT/(name+'_SCHEDULE.json')
 if path.exists():assert read(path)==sessions
 else:save(path,sessions)
 subprocess.run([sys.executable,str(ROOT/'runner.py'),'schedule',name,str(path)],check=True)
 allrows=read(ROOT/(name+'_RESULTS.json'));rows=[r for r in allrows if not r['warm']]
 window=read(ROOT/('CONTINUATION_AMENDMENT.json' if (ROOT/'CONTINUATION_AMENDMENT.json').exists() else 'RECOVERY_AMENDMENT.json'))
 progress={'utc':datetime.now(timezone.utc).isoformat(),'stage':name,'completed_nonwarm':len(rows),'excluded_warm_in_result_list':sum(r['warm'] for r in allrows),'stage_elapsed_seconds':time.monotonic()-begin,'observed_mean_host_request_seconds':statistics.mean(r['host_seconds'] for r in rows),'seconds_to_experiment_cutoff':(datetime.fromisoformat(window['new_experiment_stop_utc'])-datetime.now(timezone.utc)).total_seconds(),'profile_frozen':read(ROOT/'PROTOCOL.json')['budget_profile'] if (ROOT/'PROTOCOL.json').exists() else None,'new_source_or_task_selection':False}
 with (ROOT/'PROGRESS_ESTIMATES.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(progress)+'\n')
 return rows
def cfg(label,native=False,k=2,ub=1,prefill=128,**extra):return dict(label=label,native=native,k=k,ub=ub,prefill=prefill,**extra)
R=cfg('R_reference',ub=128,plain=True)
T=cfg('T_matched',matched=True)
N0=cfg('N0_ordinary',True,prefill=1)
N1=cfg('N1_repaired',True)
def panel(rows):
 tasks=sorted({r['task'] for r in rows});labels=sorted({r['config']['label'] for r in rows});details=[];passed={m:True for m in labels}
 for task in tasks:
  rr=[r for r in rows if r['task']==task and r['config']['label']=='R_reference'];assert rr
  stable=all(eq(r['endpoint'],rr[0]['endpoint']) for r in rr)
  for label in labels:
   obs=[r for r in rows if r['task']==task and r['config']['label']==label];assert obs
   good=stable and all(eq(r['endpoint'],rr[0]['endpoint']) for r in obs);passed[label]&=good
   differences=[]
   for r in obs:
    a=r['endpoint']['ids'];b=rr[0]['endpoint']['ids'];d=next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)) if a!=b else None);differences.append(d)
   details.append({'task':task,'label':label,'qualified':good,'reference_stable':stable,'reference_length':len(rr[0]['endpoint']['ids']),'reference_reason':rr[0]['endpoint']['reason'],'observed_lengths':[len(r['endpoint']['ids']) for r in obs],'first_differences':differences,'raw_suffix_counts':[r['endpoint']['raw_suffix'] for r in obs]})
 return {'qualification':passed,'details':details,'requests':len(rows),'tasks':len(tasks)}
def freeze():
 if (ROOT/'EXECUTION_FREEZE.json').exists():
  frozen=read(ROOT/'EXECUTION_FREEZE.json')
  assert hashlib.sha256((ROOT/'INPUTS.json').read_bytes()).hexdigest()==frozen['inputs_sha256']
  assert hashlib.sha256((ROOT/'PROTOCOL.json').read_bytes()).hexdigest()==frozen['protocol_sha256']
  for name,digest in read(ROOT/'PROTOCOL.json')['sources'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
  return read(ROOT/'INPUTS.json')
 assert not (ROOT/'INPUTS.json').exists() and not (ROOT/'PROTOCOL.json').exists(),'Incomplete freeze must be independently recovered; never overwrite or reselect inputs'
 assert read(ROOT/'G0.json')['status']=='PASS'
 assert read(ROOT/'G0_SHAM.json')['status']=='PASS'
 assert read(ROOT/'G0_TARGET_FINAL.json')['status']=='PASS'
 assert (ROOT/'G0_WIDTH.json').exists() and (ROOT/'G0_ETA.json').exists()
 if not (ROOT/'G0_ETA_N0.json').exists():
  subprocess.run(['git','add','campaign.py','runner.py','independent_verify.py','generate_report.py','publish_evidence.py'],cwd=ROOT,check=True)
  if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:
   subprocess.run(['git','commit','-m','Bind current-reference ETA and CPU-only resume guards before old-input N0 cost controls'],cwd=ROOT,check=True)
  old=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
  exposed=[dict(id=t,prompt_ids=read(old[t]['ids'])) for t in ['HumanEval/58','HumanEval/42']]
  n0rows=stage('G0_ETA_N0',[dict(config=dict(N0,cap=128,capture=False),inputs=exposed)])
  historical=read(ROOT/'dependencies/B570/HISTORICAL_EXPECTED.json');failed=[]
  for r in n0rows:
   ref=historical[r['task']+'/N0/1'];ref=dict(ref,reason='EOG' if ref['endpoint']=='EOG' else 'CAP')
   if not eq(r['endpoint'],ref):failed.append(r['unit_id'])
  save(ROOT/'G0_ETA_N0.json',dict(status='PASS' if not failed else 'BLOCKED_REFERENCE',requests=len(n0rows),warmups=1,failed=failed,reason='Current ordinary native engineering cost, old inputs only; valid prior measurements retained.'))
 assert read(ROOT/'G0_ETA_N0.json')['status']=='PASS'
 candidates=read(ROOT/'INPUT_CANDIDATES.json')
 # Freeze scope using exclusively old-input measurements. Never inspect new outputs.
 oldrows=[r for r in read(ROOT/'G0_RESULTS.json') if not r['warm']]
 probes=[r for r in read(ROOT/'G0_ETA_RESULTS.json') if not r['warm']]
 shortrows=[r for r in oldrows if r['config']['native']]+[r for name in ['G0_WIDTH','G0_TARGET_FINAL'] for r in read(ROOT/(name+'_RESULTS.json')) if not r['warm'] and (name=='G0_TARGET_FINAL' or r['config']['native'])]
 def cost(native,ub,cap,k=2,matched=False,ordinary=False):
  if ordinary and native:
   a=[r for r in read(ROOT/'G0_ETA_N0_RESULTS.json') if not r['warm']]
   longest_new=max(len(i['prompt_ids']) for i in candidates['shared']+candidates['eligible_unused'][:12])
   rates=[]
   for r in a:
    raw=read(next(ROOT/f for f in r['files'] if f.endswith('/capture.json')))
    rates.append(r['metrics']['prefill_ms']/1000/len(raw['prompt_ids']))
   # N0 serial prefill is predicted from current old-input costs and known input lengths.
   return max(r['metrics']['generation_ms'] for r in a)/1000*cap/128+max(rates)*longest_new+1.0
  a=[r for r in probes if r['config']['native']==native and r['config']['ub']==ub and r['config']['k']==k and (native or r['config'].get('matched',False)==matched)]
  assert a,(native,ub,k,matched)
  estimates=[]
  for r in a:
   n=len(r['endpoint']['ids']);overhead=max(0,r['metrics']['whole_request_ms']-r['metrics']['generation_ms'])/1000
   short=[q for q in shortrows if q['task']==r['task'] and q['config']['native']==native and q['config']['prefill']==128 and q['config']['ub']==ub and q['config'].get('k',2)==k and (native or q['config'].get('matched',False)==matched)]
   if short and n>max(len(q['endpoint']['ids']) for q in short):
    # Same exposed task at two actual output lengths: keep state transfer as a fixed cost.
    q=max(short,key=lambda q:q['metrics']['generation_ms']);n0=len(q['endpoint']['ids']);g0=q['metrics']['generation_ms']/1000;g1=r['metrics']['generation_ms']/1000
    slope=max(0,(g1-g0)/(n-n0));intercept=max(0,g0-slope*n0)
    estimates.append(overhead+intercept+slope*cap)
   else:estimates.append(overhead+r['metrics']['generation_ms']/1000*cap/max(n,1))
  return max(estimates)
 anchor=cost(True,1,128);tm=cost(False,1,128,matched=True);ordinary=cost(True,1,128,ordinary=True);ref=cost(False,128,128,ordinary=True)
 def estimate(nunused,nc):
  b=4*(24+nunused)*(anchor+tm+ordinary+ref)
  c=nc*2*sum(cost(False,128,cap,ordinary=True)+cost(False,ub,cap,k,matched=True)+cost(True,ub,cap,k) for k,ub in [(1,2),(3,4),(5,6),(7,8)] for cap in [128,256,512])
  al=nc*2*sum(cost(False,128,cap,ordinary=True)+cost(False,1,cap,matched=True)+cost(True,1,cap) for cap in [256,512])
  d=96*(anchor+tm)
  warm_b=4*(anchor+tm+ordinary+ref)
  warm_c=2*sum(cost(False,128,cap,ordinary=True)+cost(False,ub,cap,k,matched=True)+cost(True,ub,cap,k) for k,ub in [(1,2),(3,4),(5,6),(7,8)] for cap in [128,256,512])
  warm_anchor=2*sum(cost(False,128,cap,ordinary=True)+cost(False,1,cap,matched=True)+cost(True,1,cap) for cap in [256,512])
  warm_d=4*(anchor+tm)
  # Conservatism for observed capture-on D qualification and service reloads.
  return {'B_seconds':b,'C_seconds':c,'anchor_seconds':al,'D_seconds':d,'warm_seconds':warm_b+warm_c+warm_anchor+warm_d,'service_load_seconds':108*15,'safety_multiplier':1.15,'total_seconds':1.15*(b+c+al+d+warm_b+warm_c+warm_anchor+warm_d+108*15)}
 estimates={'FULL':estimate(12,11),'NIGHT':estimate(8,7)}
 window=read(ROOT/('CONTINUATION_AMENDMENT.json' if (ROOT/'CONTINUATION_AMENDMENT.json').exists() else 'RECOVERY_AMENDMENT.json'));remaining=(datetime.fromisoformat(window['new_experiment_stop_utc'])-datetime.now(timezone.utc)).total_seconds()
 profile='FULL' if estimates['FULL']['total_seconds']<=remaining else 'NIGHT'
 unused=candidates['eligible_unused'][:12 if profile=='FULL' else 8]
 if estimates[profile]['total_seconds']>remaining:
  save(ROOT/'BUDGET_DEGRADATION.json',{'utc':datetime.now(timezone.utc).isoformat(),'status':'PARTIAL_BUDGET_RISK_FROZEN_BEFORE_NEW_INPUT','remaining_seconds':remaining,'estimates':estimates,'priority':'G0, B, original anchor, D; C remains fully frozen, no failure-driven trimming'})
 old=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
 pilot_old=[{'id':task,'prompt_ids':read(old[task]['ids']),'cohort':'exposed_old_diagnostics'} for task in ['HumanEval/134','HumanEval/42','HumanEval/145','HumanEval/138']]
 inputs={'shared':candidates['shared'],'unused':unused,'long':candidates['long'],'pilot_old':pilot_old};save(ROOT/'INPUTS.json',inputs)
 g0=[r for r in read(ROOT/'G0_RESULTS.json') if not r['warm']]
 means={}
 for name,c in [('R',False),('native',True)]:means[name]=statistics.mean(r['host_seconds'] for r in g0 if r['config']['native']==c)
 protocol={'study':'B570_CLOSEOUT_OVERNIGHT_V1','budget_profile':profile,'planned_core_requests':1856 if profile=='FULL' else 1456,'G0':164,'B':576 if profile=='FULL' else 512,'C':792 if profile=='FULL' else 504,'C_ANCHOR_LONG':132 if profile=='FULL' else 84,'D_RESET':96,'D_TIMING':96,'conditions_B':[R,T,N0,N1],'C_widths':[[1,2],[3,4],[5,6],[7,8]],'C_shared_count':8 if profile=='FULL' else 4,'C_warmups':72,'C_anchor_warmups':12,'caps':[128,256,512],'context':1024,'threads':10,'batch_threads':10,'FA':'off','seed':123,'greedy':True,'target_prefill':128,'draft_prefill':1,'draft_continuation':1,'endpoint':'inclusive first runtime EOG or cap, native n_predict=cap-1; unmodified native loop overshoot fully retained','reference':'B570 original ordinary target harness UB128, common chunk grouping and serial query; independently paid each repetition','matched':'native target caller prompt[:-1],prompt[-1], pending sampled in source, sampler clone and real state into specified continuation context; no draft','generation_timer':'C++ before first target sample/state transfer through all draft/verification/rollback plus final device synchronization','whole_timer':'before parsing JSON request and resets through context transfer, generation, actual synchronization and cleanup; evidence-file disk writes excluded; host end-to-end artifact latency separately retained','resident':'models/source contexts loaded once per service; no KV/prompt cache; independently clear both memories, reset samplers and pending on each request','retries':{'valid_scientific_output':0,'infrastructure_maximum':2,'deterministic_crash_oom':0},'startup':read(ROOT/'STARTUP.json'),'recovery_amendment':window,'observed_old_request_mean_seconds':means,'ETA_by_profile':estimates,'freeze_remaining_seconds':remaining,'mechanism_pair_selection':'width ascending, cap ascending, frozen task order; at most two pairs','E_selection':'smallest qualified continuation UB>1, else1; fixed k1/2/3/5/7 plus k2UB1 anchor; <=6 configs; cost-selected pilot requires generation>=1.03, wall>=1, both repeat directions faster; independent confirmation separately required','prototype':'optional at most one family, not necessary for core; never shader/precision changes','scientific_failure':'retain complete valid outputs and continue independent stages','exposure_limit':'accessible history plus fixed RTX exposure receipt; inaccessible RTX bulk histories explicitly not independently rescanned','sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in list((ROOT/'src').glob('*'))+[ROOT/'runner.py',ROOT/'derive_frontends.py',ROOT/'campaign.py']},'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'models':{'target':'408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6','draft':'9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'}}
 save(ROOT/'PROTOCOL.json',protocol)
 protocol['matched_output_reservation_amendment']=read(ROOT/'MATCHED_RESERVATION_AMENDMENT.json')
 protocol['final_target_control']=read(ROOT/'G0_TARGET_FINAL.json')
 save(ROOT/'PROTOCOL.json',protocol)
 subprocess.run(['git','add','INPUTS.json','PROTOCOL.json','G0.json','G0_SHAM.json','G0_WIDTH.json','G0_TARGET_FINAL.json','MATCHED_RESERVATION_AMENDMENT.json','G0_ETA.json','G0_ETA_N0.json'],cwd=ROOT,check=True)
 subprocess.run(['git','commit','-m','Freeze old-input ETA-selected scope and complete input contract before new inference'],cwd=ROOT,check=True)
 assets={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in window['unchanged_numerical_assets']}
 save(ROOT/'EXECUTION_FREEZE.json',{'utc':datetime.now(timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.json').read_bytes()).hexdigest(),'inputs_sha256':hashlib.sha256((ROOT/'INPUTS.json').read_bytes()).hexdigest(),'numerical_assets':assets,'new_input_forwards_before_freeze':0})
 return inputs
def core(inputs):
 shared=inputs['shared'];unused=inputs['unused'];long=inputs['long'];allB=shared+unused;ctasks=shared[:read(ROOT/'PROTOCOL.json')['C_shared_count']]+long
 bs=[]
 conditions=[R,T,N0,N1]
 for rep in range(4):
  tasks=allB[rep:]+allB[:rep]
  for c in conditions[rep:]+conditions[:rep]:bs.append({'config':dict(c,cap=128,repetition=rep+1),'inputs':tasks})
 b=stage('B',bs)
 bsummary={cohort:panel([r for r in b if r['task'] in {i['id'] for i in tasks}]) for cohort,tasks in [('shared',shared),('unused',unused)]};save(ROOT/'B_SUMMARY.json',bsummary)
 cs=[]
 widths=[(1,2),(3,4),(5,6),(7,8)]
 for rep in range(2):
  for wi,(k,ub) in enumerate(widths if rep==0 else widths[::-1]):
   modes=[R,dict(T,ub=ub),cfg('N_candidate',True,k,ub)]
   for cap in [128,256,512]:
    for c in modes[wi%3:]+modes[:wi%3]:cs.append({'config':dict(c,cap=cap,repetition=rep+1,width_k=k,width_ub=ub),'inputs':ctasks[rep:]+ctasks[:rep]})
 def perform_c():
  c=stage('C',cs);csummary=[]
  for k,ub in widths:
   for cap in [128,256,512]:
    rows=[r for r in c if r['config']['width_k']==k and r['config']['cap']==cap]
    csummary.append({'k':k,'ub':ub,'cap':cap,'shared':panel([r for r in rows if r['task'].startswith('MBPP/')]),'long':panel([r for r in rows if r['task'].startswith('HumanEval/')])})
  save(ROOT/'C_SUMMARY.json',csummary)
 # Frozen budget risk prioritizes the original anchor/D, never removes failed C tasks.
 defer_c=(ROOT/'BUDGET_DEGRADATION.json').exists()
 if not defer_c:perform_c()
 als=[{'config':dict(c,cap=cap,repetition=rep+1),'inputs':ctasks} for rep in range(2) for cap in [256,512] for c in [R,T,N1]]
 al=stage('C_ANCHOR_LONG',als);alsummary={str(cap):panel([r for r in al if r['config']['cap']==cap]) for cap in [256,512]};save(ROOT/'C_ANCHOR_SUMMARY.json',alsummary)
 sharedpass=bsummary['shared']['qualification'].get('N1_repaired',False) and bsummary['shared']['qualification'].get('T_matched',False)
 anchorpass=all(v['qualification'].get('N1_repaired',False) and v['qualification'].get('T_matched',False) for v in alsummary.values())
 if sharedpass and anchorpass:
  for stage_name,capture in [('D_RESET',True),('D_TIMING',False)]:
   ds=[]
   for cycle in [1,2]:
    order=sorted(shared,key=lambda i:(hashlib.sha256((i['id']+'HeteroSpec-B570-Closeout-D-v1-cycle'+str(cycle)).encode()).hexdigest(),i['id']))
    for mode in [T,N1]:ds.append({'config':dict(mode,cap=128,capture=capture,cycle=cycle),'inputs':order})
   rows=stage(stage_name,ds)
   failures=[r['unit_id'] for r in rows if not eq(r['endpoint'],next(q for q in b if q['task']==r['task'] and q['config']['label']=='R_reference')['endpoint'])]
   save(ROOT/(stage_name+'_SUMMARY.json'),{'status':'COMPLETED_PASS' if not failures else 'COMPLETED_SCIENTIFIC_FAIL','requests':len(rows),'failures':failures})
 else:save(ROOT/'D_GATE.json',{'status':'GATED_BY_QUALIFICATION','reason':'Original k2/UB1 shared or long-anchor qualification failed','B_shared_pass':sharedpass,'long_anchor_pass':anchorpass})
 if defer_c:perform_c()
 save(ROOT/'CORE_DONE.json',{'utc':datetime.now(timezone.utc).isoformat(),'status':'CORE_MEASURED_PENDING_INDEPENDENT_AUDIT','B':bsummary,'D_gated':not(sharedpass and anchorpass)})
if __name__=='__main__':
 if sys.argv[1]=='freeze':freeze()
 elif sys.argv[1]=='core':core(read(ROOT/'INPUTS.json'))
