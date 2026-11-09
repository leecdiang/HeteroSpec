"""Detached remaining eligibility gates and conditional whole descriptive panel.

No automatic retry or confirmation expansion. Source/destination epochs remain
distinct, including the offline observer and actual operand-recipe verifier.
"""
from pathlib import Path
from collections import Counter
import argparse,copy,datetime,fcntl,hashlib,json,os,subprocess,sys,time,traceback,types
from build import read,sha,save
def now():return datetime.datetime.now(datetime.timezone.utc)
STOP=datetime.datetime(2026,11,9,21,tzinfo=datetime.timezone.utc)
ADMIT=datetime.datetime(2026,11,9,19,tzinfo=datetime.timezone.utc)
def extra(s,label,job,build,negative=None):
 s.admission(job);p=s.out/'jobs'/(label+'.json');save(p,job);dest=s.out/'runs'/label
 save(s.out/'admissions'/(label+'.json'),dict(job_sha256=sha(p),build_sha256=sha(build),requests=s.host.reservation(job)[0],rows=s.host.reservation(job)[1],expected_native_failure=negative))
 error=None
 try:s.host.run(s.cfg,build,p,dest,'development')
 except RuntimeError as e:error=str(e)
 if negative:
  assert error and read(dest/'HOST.json')['status']=='FAILED';fail=read(dest/'native/failure.json');assert negative in fail['error'],fail
  save(s.out/'negative-checks'/(label+'.json'),dict(passed=True,expected_native_failure=negative,actual_failure=fail,host_sha256=sha(dest/'HOST.json'),failure_charged=True));return dest
 assert error is None,error;return dest
def negatives(s,q):
 models=copy.deepcopy(s.models);base={**models,'draft':True,'draft_width':4,'lowering':'LOCAL','residency':'matched','profile':False,'k':3,'target_output_reserve':8,'proposal_mode':'live','inputs':[],'capability_request':q.capability(models,s.structures['target'],s.structures['draft'],'packed','LOCAL',True,'live')}
 inp={**s.roots[0],'prompt_ids':(s.roots[0]['prompt_ids']*20)[:893],'cap':128}
 cases=[('unsupported-k',dict(k=7),'Q32 explicit k3 reserve32 M/D4 contract'),('insufficient-reserve',dict(target_output_reserve=4),'Q32 explicit k3 reserve32 M/D4 contract'),('unknown-field',dict(unregistered_q32_option=True),'Unknown M1 native job field'),('ignored-context',dict(n_ctx=2048),'Ignored context request'),('transient-capacity',dict(inputs=[dict(name='bad',input=inp,capture=False)]),'transient position capacity')]
 for name,patch,error in cases:extra(s,'negative-'+name,{**base,**patch},s.builds/'packed/BUILD.json',error)
 save(s.out/'NATIVE_NEGATIVES_COMPLETE.json',dict(passed=True,cases=[x[0]for x in cases],all_native_expected_failures=True,charged_without_refund=True))
def operands(s,q,a):
 original=read(a.work/'qualification-02/GEOMETRY_REGISTERED.json')['cases'][0];case=copy.deepcopy(original);job={**s.models,'draft':False,'draft_width':1,'lowering':'LOCAL','residency':'target_only','profile':False,'k':3,'target_output_reserve':8,'proposal_mode':'live','cases':[case],'capture_real_operands':True,'capability_request':q.capability(s.models,s.structures['target'],s.structures['draft'],'packed','LOCAL',False,'live')};job.pop('draft_model');job.pop('draft_sha256')
 out=extra(s,'real-operand-observer',job,a.operand_builds/'observer/BUILD.json');meta=read(out/'native/result.json');reuse=a.work/'qualification-02/reuse/geometry-R-0.json';reference_run=Path(read(reuse)['prior'])if reuse.exists()else a.work/'qualification-02/runs/geometry-R-0';r=reference_run/'native'/case['name'];proof=[]
 for n in case['observe_positions']:
  aa=out/'native'/case['name']/'captures'/str(n);bb=r/'captures'/str(n);pair=dict(position=n,vector=s.checks.vector_pair(aa/'frontier.f32',bb/'frontier.f32',meta['vocab']))
  if n in case['state_positions']:pair['state']=s.checks.state_pair(aa/'sequence.bin',bb/'sequence.bin',n,s.parse,s.profiles['Qwen32B'])
  proof.append(pair)
 save(s.out/'OPERAND_OBSERVER_BRIDGE.json',dict(passed=all(x['vector']['equal']and x.get('state',{'equal':True})['equal']for x in proof),rows=proof,scope='Offline after-op capture changes graph synchronization/fusion; independent full-vector and active64-layer state bridge required',clean_timing_ELF_unchanged=True))
 assert read(s.out/'OPERAND_OBSERVER_BRIDGE.json')['passed']
 directory=out/'native/operands';metas=sorted(directory.glob('*.json'));assert len(metas)==2;types={read(p)['weight_type']for p in metas};assert types=={'q4_K','q6_K'},types
 probes=[]
 for p in metas:
  x=read(p);n=x['activation_tensor']['ne'][2];assert n==4;probes.append(dict(operand_dir=str(directory),weight=x['weight'],prefix=[],ids=[0]*(2*n),work_unit='Actual typed projection rows; groupN and scalarN, not full-model token rows'))
 job={k:s.models[k]for k in('family','target_model','target_sha256','n_ctx','threads')};job['append_probes']=probes
 tested=extra(s,'original-real-operand-recipes',job,a.operand_builds/'verifier/BUILD.json');result=read(tested/'native/result.json');assert len(result['operands'])==2 and all(x['passed']for x in result['operands'])
 save(s.out/'REAL_OPERAND_RECIPES_COMPLETE.json',dict(passed=True,actual_Q4_K_and_Q6_K=True,original_scalar_vs_group_and_actual_full_model_operation='Exact bytes of each entire output, same real GGUF weights and captured F32 inputs',physical_projection_rows=result['token_rows'],not_full_model_rows=True,observer_bridge_sha256=sha(s.out/'OPERAND_OBSERVER_BRIDGE.json'),native_result_sha256=sha(tested/'native/result.json'),operand_commitments=[read(p)for p in metas],private_raw_weight_payloads_not_published=True))
def primers(s):
 xs=copy.deepcopy(read(s.root/'run-01/inputs-01/Qwen-DEVELOPMENT.json')['inputs'][:2]);entries=[]
 for i,x in enumerate(xs):x.update(family='Qwen32B',cap=128);entries.append(dict(name='primer-'+str(i),input=x,capture=False))
 save(s.out/'PRIMERS_REGISTERED.json',dict(inputs=entries,selection='Original distinct GSM8K806/70; exposed deployment primers; own32B R endpoints, no selection on timing'))
 out=s.execute('primer-independent-R','Qwen32B',dict(inputs=entries));return entries,{x['name']:s.native.endpoint(read(out/'native'/x['name']/'receipt.json'))for x in entries}
def metadata(s):
 import struct
 def gguf(path):
  with Path(path).open('rb')as f:
   def rd(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))[0]
   def string():return f.read(rd('Q')).decode('utf8')
   def value(t):
    formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
    if t in formats:return rd(formats[t])
    if t==8:return string()
    assert t==9;et,n=rd('I'),rd('Q');return[value(et)for _ in range(n)]
   assert f.read(4)==b'GGUF'and rd('I')in(2,3);nt,nm=rd('Q'),rd('Q');out={}
   for _ in range(nm):key=string();out[key]=value(rd('I'))
   return{k:v for k,v in out.items()if k.startswith('tokenizer.')or 'license'in k}
 target=gguf(s.models['target_model']);draft=gguf(s.models['draft_model']);checks={}
 for key in('tokenizer.ggml.model','tokenizer.ggml.tokens','tokenizer.ggml.merges','tokenizer.ggml.token_type','tokenizer.ggml.bos_token_id','tokenizer.ggml.eos_token_id','tokenizer.chat_template'):
  assert key in target and key in draft,key;equal=target[key]==draft[key];checks[key]=dict(equal=equal,target_sha256=hashlib.sha256(json.dumps(target[key],ensure_ascii=True,separators=(',',':')).encode()).hexdigest(),draft_sha256=hashlib.sha256(json.dumps(draft[key],ensure_ascii=True,separators=(',',':')).encode()).hexdigest());assert equal,'Target/draft tokenizer/template differs: '+key
 licenses=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))for p in sorted((s.root/'q32-models-01/licenses').rglob('*'))if p.is_file()];assert licenses,'Acquisition license evidence missing'
 save(s.out/'TOKENIZER_TEMPLATE_LICENSE_CHECKED.json',dict(passed=True,checks=checks,license_files=licenses,model_license_metadata={k:v for k,v in target.items()if'license'in k},native_EOG_basis='Full151936 native token strings and EOG flags also compared on every live D4 native load',model_files_fixed=True))
def final_boundaries(s,q):
 # A registered synthetic capacity stress input is deliberately separate from
 # all natural roots and timing. It repeats real prompt tokens, not oracle KV.
 prompt=s.roots[0]['prompt_ids'];owned=(prompt*40)[:1024];c=dict(name='capacity1024-q32',forced=[dict(ids=owned[:992],phase='PREFILL',all=False),dict(ids=owned[992:],phase='VERIFY',all=True)],observe_positions=list(range(992,1025)),state_positions=[992,1024]);save(s.out/'CAPACITY_FIXTURES_REGISTERED.json',dict(forced=c,pending_cap1_prompt=owned[:1019],scope='Synthetic repeated real-token capacity stress only; no natural-input or performance claim; own32B R newly executed'))
 ref=s.execute('capacity1024-R','Qwen32B',dict(cases=[c]));reports=[]
 for arm,(core,cut,draft)in q.ARMS.items():
  if draft:continue
  out=s.execute('capacity1024-'+arm,'Qwen32B',dict(cases=[c],lowering=cut),core);meta=read(out/'native/result.json');pairs=[]
  for n in c['observe_positions']:
   aa=out/'native'/c['name']/'captures'/str(n);bb=ref/'native'/c['name']/'captures'/str(n);pair=dict(position=n,vector=s.checks.vector_pair(aa/'frontier.f32',bb/'frontier.f32',meta['vocab']))
   if n in c['state_positions']:pair['active_KV']=s.checks.state_pair(aa/'sequence.bin',bb/'sequence.bin',n,s.parse,s.profiles['Qwen32B'])
   pairs.append(pair)
  proof=dict(passed=all(p['vector']['equal']and p.get('active_KV',{'equal':True})['equal']for p in pairs),arm=arm,rows=pairs,executions=meta['cases'][0]['executions']);save(s.out/'capacity-checks'/(arm+'.json'),proof);assert proof['passed'];reports.append(proof)
 x={**s.roots[0],'id':'Q32/synthetic-capacity-pending-v1','prompt_ids':owned[:1019],'prompt_tokens':1019,'cap':1};x.pop('prompt_ids_sha256',None)
 ref=s.execute('capacity-pending-R','Qwen32B',dict(inputs=[dict(name='pending',input=x,capture=True,state_positions=[1019])]))
 index=len(s.roots);s.roots.append(x);s.free.append(ref/'native/pending')
 for arm,(core,cut,draft)in q.ARMS.items():
  if not draft:continue
  out=s.execute('capacity-pending-'+arm,'Qwen32B',dict(inputs=[dict(name='heavy',input=x,capture=True),dict(name='clean',input=x,capture=False)],lowering=cut),core,True);proof=s.pair(index,x,out,'heavy','clean',True);save(s.out/'capacity-checks'/(arm+'-pending.json'),dict(passed=True,proof=proof))
 s.roots.pop();s.free.pop();s.banks={k:b for k,b in s.banks.items()if k[0]!=index}
 # Actual termination fixture was independently produced and qualified above.
 eog=read(a.work/'qualification-02/EOG-INPUT_REGISTERED.json')['input'];free=a.work/'qualification-02/runs/extra-free-R-EOG/native/EOG';endpoint=read(free/'receipt.json');assert endpoint['terminal_kind']=='EOG';index=len(s.roots);s.roots.append(eog);s.free.append(free);length=len(endpoint['ids']);assert length>1
 for arm,(core,cut,draft)in q.ARMS.items():
  inputs=[]
  for cap in(length-1,length):inputs +=[dict(name=f'cap{cap}-'+kind,input={**eog,'cap':cap},capture=kind=='heavy')for kind in('heavy','clean')]
  out=s.execute('EOG-cap-'+arm,'Qwen32B',dict(inputs=inputs,lowering=cut),core,draft)
  # Reuse only complete hash-bound prior scalar branch operands, with every
  # actual vector/state byte committed here before the comparison.
  for cap in(length-1,length):
   x={**eog,'cap':cap};bank=s.bank(index,x);bindings=[]
   for job in sorted((a.work/'qualification-02/jobs').glob('Qwen32B-root5-R-branches-*.json')):
    prior=a.work/'qualification-02/runs'/job.stem;launch=read(prior/'launch.json');assert read(prior/'HOST.json')['status']=='COMPLETE'and launch['job_sha256']==sha(job)and launch['build_sha256']==sha(s.ref_build)
    cases=read(job)['cases']
    for case in cases:
     for n in case['observe_positions']:
      directory=prior/'native'/case['name']/'captures'/str(n)
      for file in([directory/'frontier.f32']+([directory/'sequence.bin']if n in case['state_positions']else[])):bindings.append(dict(path=str(file),bytes=file.stat().st_size,sha256=sha(file)))
    bank.add(prior,cases)
   save(s.out/'reused-EOG-R'/(arm+'-cap'+str(cap)+'.json'),dict(complete_actual_operands=bindings,no_native_replay=True));proof=s.pair(index,x,out,f'cap{cap}-heavy',f'cap{cap}-clean',draft);save(s.out/'EOG-cap-checks'/(arm+'-'+str(cap)+'.json'),dict(passed=True,proof=proof,expected_stop='CAP'if cap<length else'EOG'))
 s.roots.pop();s.free.pop();save(s.out/'CAPACITY_EOG_BOUNDARIES_COMPLETE.json',dict(passed=True,exact_C1024_active_forward=True,transient_equal_capacity_pending_cap1=True,EOG_at_length_cap_and_one_before=True,scope='Finite synthetic capacity and actual autonomous EOG boundaries; all exact vector/KV gates retained'))
def panel(s,q,entries,primer_endpoints):
 assert now()<ADMIT,'Whole-panel admission after03:00 denied'
 # Overestimate based on the worst complete qualification worker plus its full
 # request count, then include complete six-request worker startup for every slot.
 costs=[]
 for p in(a.work/'qualification-02/runs').glob('natural-*/HOST.json'):
  j=read(a.work/'qualification-02/jobs'/(p.parent.name+'.json'));h=read(p);costs.append((h,len(j['inputs'])))
 def wall(h):
  for key in('caller_inclusive_wall_s','caller_wall_s','wrapper_wall_s','wall_s'):
   if key in h:return float(h[key])
  raise RuntimeError('Unknown HOST cost schema; refuse guessed whole-panel budget')
 estimate=max(wall(h)/n for h,n in costs)*6*24*1.5+24*60
 assert (STOP-now()).total_seconds()>estimate+900,'Insufficient whole-panel conservative runtime'
 out=a.work/'panel-01';out.mkdir();names=list(q.ARMS);base=[0,1,5,2,4,3];other=[(x+2)%6 for x in base];orders=[base,base[::-1],other,other[::-1]];workers=[];expected={}
 for i,root in enumerate(s.roots):expected[root['id']]=s.native.endpoint(read(s.free[i]/'receipt.json'))
 for rnd,order in enumerate(orders):
  for position,idx in enumerate(order):
   arm=names[idx];core,cut,draft=q.ARMS[arm];tests=[dict(name='root-'+str(i),input=x,capture=False)for i,x in enumerate(s.roots)];tests=tests if rnd%2==0 else tests[::-1]
   job={**s.models,'draft':draft,'draft_width':4 if draft else 1,'lowering':cut,'residency':'matched'if draft else'target_only','profile':False,'k':3,'target_output_reserve':8,'proposal_mode':'live','inputs':copy.deepcopy(entries)+tests,'capability_request':q.capability(s.models,s.structures['target'],s.structures['draft'],core,cut,draft,'live')}
   if not draft:job.pop('draft_model');job.pop('draft_sha256')
   wid=f'r{rnd}-p{position}-{arm}';path=out/'jobs'/(wid+'.json');save(path,job);workers.append(dict(id=wid,round=rnd,position=position,arm=arm,core=core,job='jobs/'+path.name,job_sha256=sha(path)))
 plan=out/'PLAN.json';save(plan,dict(schema='heterospec.q32.descriptive-six-arm.v1',workers=workers,orders=[[names[i]for i in z]for z in orders],roots=[x['id']for x in s.roots],measured=96,primers=48,balance='Four complementary rows; partial six-arm position/precedence balance, no full Williams claim',admitted_utc=now().isoformat(),conservative_whole_panel_seconds=estimate,analysis='Descriptive paired roots/rounds only; original exposed roots; size and precision/recipe changed together',expected_endpoints=expected,primer_endpoints=primer_endpoints))
 executables={}
 for core in('loop4','packed'):
  path=s.builds/core/'BUILD.json';b=read(path);module=next((a.work/'qualification-02/runs').glob('natural-'+('W_REF1L_M'if core=='loop4'else'W_REF1G_M')+'-0/LOADED_MODULES.json'));executables[b['executable_sha256']]=dict(build=dict(path=str(path),sha256=sha(path)),loaded_modules=read(module))
 gates=[a.work/'qualification-02/CORE_GATES_COMPLETE.json',s.out/'NATIVE_NEGATIVES_COMPLETE.json',s.out/'REAL_OPERAND_RECIPES_COMPLETE.json',s.out/'CAPACITY_EOG_BOUNDARIES_COMPLETE.json',s.out/'TOKENIZER_TEMPLATE_LICENSE_CHECKED.json',s.out/'QUALIFICATION_COMPLETE.json']
 freeze=out/'FROZEN.json';save(freeze,dict(status='QUALIFIED_AND_FROZEN',plan=dict(path=str(plan),sha256=sha(plan)),executables=executables,job_sha256=[w['job_sha256']for w in workers],proofs=[dict(path=str(p),sha256=sha(p))for p in gates],descriptive_only=True))
 cfg=read(s.cfg);cfg.update(freeze=str(freeze),freeze_sha256=sha(freeze));config=out/'config.private.json';save(config,cfg);records=[]
 for w in workers:
  assert (STOP-now()).total_seconds()>=960 and not(s.guard/'PAUSE.json').exists();assert sha(plan)==read(freeze)['plan']['sha256']
  for p in gates:assert sha(p)==next(z['sha256']for z in read(freeze)['proofs']if z['path']==str(p))
  assert time.time()-read(s.guard/'RESOURCE_GUARD_LATEST.private.json')['epoch']<20
  job=read(out/w['job']);dest=out/'runs'/w['id'];began=time.monotonic();s.host.run(config,s.builds/w['core']/'BUILD.json',out/w['job'],dest,'confirmation');save(dest/'CALLER_COST.json',dict(caller_inclusive_wall_s=time.monotonic()-began,boundary='Before host dependency/model SHA admission through native exit and module hashing; distinct from clean service and marker burst'));meta=read(dest/'native/result.json');assert meta['total_observed_API_calls']['context_creates']==(2 if q.ARMS[w['arm']][2]else 1)
  for entry in job['inputs']:
   r=read(dest/'native'/entry['name']/'receipt.json');want=primer_endpoints[entry['name']]if entry['name'].startswith('primer-')else expected[entry['input']['id']];assert s.native.endpoint(r)==want
   assert all(v==0 for v in r['observed_API_calls_within_service'].values());r['study_cap']=128;s.trace(r,entry['input']['prompt_ids'],meta['vocab'],meta['eog_ids'],'rtx');s.physical(r,entry['input'],q.ARMS[w['arm']][2])
  row=dict(worker=w,HOST=read(dest/'HOST.json'),CLOCKS=read(dest/'CLOCKS.json'),receipt_sha256={e['name']:sha(dest/'native'/e['name']/'receipt.json')for e in job['inputs']});save(out/'checked'/(w['id']+'.json'),dict(passed=True,**row));records.append(row);print('Q32_PANEL_WORKER_PASS',w['id'],flush=True)
 save(out/'COMPLETE.json',dict(passed=True,workers=24,measurements=96,primers=48,descriptive=True,records=[dict(path=str(p),sha256=sha(p))for p in sorted((out/'checked').glob('*.json'))],utc=now().isoformat()))
def main():
 global a
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--builds',type=Path,required=True);p.add_argument('--operand-builds',type=Path,required=True);a=p.parse_args();w=a.work
 while not(w/'qualification-02/CORE_GATES_COMPLETE.json').exists():
  for failure in(w/'reference/FAILURE.json',w/'qualification-02/FAILURE.json'):
   if failure.exists():save(w/'FINISH_NOT_ADMITTED-02.json',dict(reason='Prior required gate failed',failure=str(failure),sha256=sha(failure),timing_admitted=False));return
  assert (STOP-now()).total_seconds()>=960;time.sleep(10)
 while not(w/'qualification-02/control/GUARD_STOPPED.private.json').exists():time.sleep(1)
 src=Path(__file__).parent/'qualification.py';original=src.read_text();assert original.count("self.w/'qualification-02'")==1;adapted=original.replace("self.w/'qualification-02'","self.w/'closure-02'",1)
 q=types.ModuleType('_q32_closure_adapter');q.__file__=str(src);exec(compile(adapted,str(src), 'exec'),q.__dict__);s=q.Study(a);save(s.out/'CONTROLLER_ADAPTER.json',dict(original_source_sha256=sha(src),adapted_source_sha256=hashlib.sha256(adapted.encode()).hexdigest(),only_change='New output closure-02; reuse exact request/native capability/admission/comparison functions',native_results_replayed=False));s.guard.mkdir();save(s.guard/'config.private.json',read(w/'config.private.json'))
 with(s.guard/'stdout.log').open('xb')as so,(s.guard/'stderr.log').open('xb')as se:guard=subprocess.Popen(['taskset','-c','36',sys.executable,'-B',str(Path(__file__).parent/'resource_guard.py'),'--work',str(s.guard)],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
 try:
  for _ in range(30):
   if(s.guard/'RESOURCE_GUARD_LATEST.private.json').exists():break
   assert guard.poll()is None;time.sleep(.5)
  with(a.root/'STUDY_SCHEDULING.lock').open('a+')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);metadata(s);negatives(s,q);operands(s,q,a);final_boundaries(s,q);entries,eps=primers(s);save(s.out/'QUALIFICATION_COMPLETE.json',dict(passed=True,core_gates_sha256=sha(w/'qualification-02/CORE_GATES_COMPLETE.json'),native_negatives=True,real_operand_recipe_and_observer_bridge=True,capacity_EOG_sha256=sha(s.out/'CAPACITY_EOG_BOUNDARIES_COMPLETE.json'),primer_own_R_endpoints=True,tokenizer_template_license_sha256=sha(s.out/'TOKENIZER_TEMPLATE_LICENSE_CHECKED.json'),finite_only=True));panel(s,q,entries,eps)
 except BaseException as e:save(s.out/'FAILURE.json',dict(error=str(e),traceback=traceback.format_exc(),utc=now().isoformat(),automatic_native_retry=False));raise
 finally:
  (s.guard/'GUARD_DONE').touch(exist_ok=False)
  try:guard.wait(timeout=20)
  except subprocess.TimeoutExpired:pass
if __name__=='__main__':main()
