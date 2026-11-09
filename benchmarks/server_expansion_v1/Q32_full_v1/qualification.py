"""Real32B qualification, strict inherited byte readers and native transactions.

Every independently executed branch is enumerated, admitted and charged before
execution. A failed gate never admits a timing panel. No tolerance adaptation.
"""
from pathlib import Path
from collections import Counter
import argparse,copy,datetime,fcntl,hashlib,inspect,json,os,subprocess,sys,time,traceback,textwrap
from build import read,sha,save
ARMS={'W_REF1L_M':('loop4','SIMPLE',False),'W_REF1G_M':('packed','SIMPLE',False),'L_REF1L_M':('loop4','LOCAL',False),'L_REF1G_M':('packed','LOCAL',False),'W_REF1L_D4':('loop4','SIMPLE',True),'L_REF1G_D4':('packed','LOCAL',True)}
def canonical(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def capability(m,ts,ds,core,cut,draft,mode):
 topology=lambda s:{k:s[k]for k in('layers','query_heads','kv_heads','head_k','head_v','K_elements','V_elements')}
 ctx=lambda ub,n:dict(n_ctx=1024,n_batch=1024,n_ubatch=ub,outputs_max=n,outputs_per_seq=n,flash_attention=False,type_k='f16',type_v='f16')
 place=lambda s:dict(layers=['NVIDIA RTX A5000']*s['layers'],output='NVIDIA RTX A5000')
 return dict(schema='heterospec.q32.ref1.native-capability.v1',target_sha256=m['target_sha256'],draft_sha256=m['draft_sha256']if draft else None,target_structure=topology(ts),draft_structure=topology(ds)if draft else None,target_context=ctx(32,8),draft_context=ctx(4,1)if draft else None,target_placement=place(ts),draft_placement=place(ds)if draft else None,k=3,draft_width=4 if draft else 1,cut=cut,projection='REF1-group'if core=='packed'else'REF1-loop',typed_recipes={'Q4_K':'original scalar vec_dot_q4_K_q8_1','Q6_K':'original scalar vec_dot_q6_K_q8_1'},atomic_columns=1,residency='matched'if draft else'target_only',proposal_mode=mode,target_output_reserve=8,threads=2,greedy=True,target_output_policy='PREFILL:last;VERIFY:all_original_rows',draft_output_policy='last',physical_rows_evidence='per-request executions and native physical width histograms')
class Study:
 def __init__(self,a):
  self.root,self.w,self.builds=a.root,a.work,a.builds;self.out=self.w/'qualification-01';self.out.mkdir();self.cfg=self.w/'config-reference-frozen.private.json';self.ref_build=self.root/'run-01/build-R-01/BUILD.json';self.guard=self.out/'control'
  sys.path.insert(0,str(self.w/'runtime'));import host,native_checks,qualify_native
  self.host,self.checks,self.native=host,native_checks,qualify_native;self.trace,self.parse=native_checks.legacy_readers(self.root/'repository-01');self.physical=qualify_native.Study.physical
  job=read(self.w/'REFERENCE_PLAN.private.json')['jobs'][0]['job'];base=read(job);self.models={k:base[k]for k in('family','target_model','target_sha256','n_ctx','threads')};self.models.update(draft_model=str(self.root/'models-final/Qwen3-0.6B-Q8_0.gguf'),draft_sha256='9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031')
  self.structures={k:native_checks.gguf_structure(self.models[k+'_model'])for k in('target','draft')};self.profiles={'Qwen32B':read(self.w/'STATE_PROFILE.json')};self.roots=[x['input']for x in base['inputs']];self.free=[self.w/'reference/runs/R-repeat-0/native'/x['name']for x in base['inputs']];self.modules={};self.banks={};self.counter=0
  src=inspect.getsource(qualify_native.Bank.check);anchor="cycle['draft_after']==cycle['target_after']";assert src.count(anchor)==1
  src=src.replace(anchor,"cycle['draft_after']==({'min':-1,'max':-1} if r.get('proposal_mode')=='replay' else cycle['target_after'])")
  ns=dict(qualify_native.__dict__);exec(compile(textwrap.dedent(src),'<Q32 replay empty-draft adapter>','exec'),ns);self.bank_check=ns['check']
  fill=inspect.getsource(qualify_native.Bank.fill);assert fill.count('range(0,len(cases),12)')==1;fill=fill.replace('range(0,len(cases),12)','range(0,len(cases),2)').replace('cases[start:start+12]','cases[start:start+2]');ns=dict(qualify_native.__dict__);exec(compile(textwrap.dedent(fill),'<Q32 scalar R bounded grouping>','exec'),ns);qualify_native.Bank.fill=ns['fill']
  save(self.out/'READER_BINDING.json',dict(original_reader_sha256=sha(self.w/'runtime/native_checks.py'),original_Bank_sha256=sha(self.w/'runtime/qualify_native.py'),adapted_check_sha256=hashlib.sha256(src.encode()).hexdigest(),adapted_fill_sha256=hashlib.sha256(fill.encode()).hexdigest(),changes=['Replay requires actually empty draft KV, unchanged live equality','Group at most2 complete scalar R branches/job, all branches remain charged'],full_vector_comparison='Exact all151936 F32 elements; no tolerance',active_KV='Independently parsed all64 dense F16 layers and frontier',own_R_freeze_sha256=sha(self.w/'reference/REFERENCE_FREEZE.json')))
  bindings={}
  for core in('loop4','packed'):
   b=read(self.builds/core/'BUILD.json');d=read(self.builds/core/'DEPENDENCIES.json');assert b['cuda']and b['dependency_closure_complete']and d['cuda_translation_units']>0
   for p,h in d['files'].items():assert sha(p)==h,p
   assert sha(b['executable'])==b['executable_sha256'];bindings[core]=dict(build_sha256=sha(self.builds/core/'BUILD.json'),executable_sha256=b['executable_sha256'],core_binding_sha256=sha(self.builds/core/'CORE_BINDING.json'))
  save(self.out/'SOURCE_BINDING.json',dict(builds=bindings,drivers={p.name:sha(p)for p in Path(__file__).parent.glob('*.py')},reference_freeze_sha256=sha(self.w/'reference/REFERENCE_FREEZE.json'),original_CUDA_arithmetic_unchanged=True,modified_numerical_TU='llama-graph.cpp',candidate_status='NOT_YET_QUALIFIED'))
 def admission(self,job):
  assert not(self.guard/'PAUSE.json').exists();g=read(self.guard/'RESOURCE_GUARD_LATEST.private.json');assert not g['events']and time.time()-g['epoch']<20
  assert (datetime.datetime(2026,11,9,21,tzinfo=datetime.timezone.utc)-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>=960,'New worker cutoff'
  inherited=read(self.w/'INHERITED_ACCOUNTING.json');xs=[json.loads(x)for x in(self.w/'ledger.jsonl').read_text().splitlines()if json.loads(x)['event']=='RESERVE'];n,rows=self.host.reservation(job)
  assert inherited['requests']+sum(x['requests']for x in xs)+n<=352,'Preserve144 panel slots and16 failure/closure slots; stop qualification without omission'
  assert inherited['rows']+sum(x['rows']for x in xs)+rows<=2000000,'Q32 conservative row ceiling'
 def execute(self,label,family,job,core='reference',draft=False,mode='live'):
  self.counter+=1;m=copy.deepcopy(self.models);m.update(job)
  if core=='reference':
   m.pop('draft_model',None);m.pop('draft_sha256',None);m.update(draft=False,residency='target_only');b=self.ref_build
  else:
   m.update(draft=draft,draft_width=4 if draft else 1,residency='matched'if draft else'target_only',profile=False,k=3,target_output_reserve=8,proposal_mode=mode)
   if not draft:m.pop('draft_model',None);m.pop('draft_sha256',None)
   m['capability_request']=capability(self.models,self.structures['target'],self.structures['draft'],core,m['lowering'],draft,mode);b=self.builds/core/'BUILD.json'
  self.admission(m);path=self.out/'jobs'/(label+'.json');save(path,m);dest=self.out/'runs'/label
  save(self.out/'admissions'/(label+'.json'),dict(job_sha256=sha(path),build_sha256=sha(b),requests=self.host.reservation(m)[0],conservative_rows=self.host.reservation(m)[1],enumerated_before_execution=True))
  self.host.run(self.cfg,b,path,dest,'reference'if core=='reference'else'development')
  modules=read(dest/'LOADED_MODULES.json');prior=self.modules.setdefault(core,modules);assert modules==prior
  if core!='reference':assert read(dest/'native/CAPABILITY.json')==m['capability_request']
  print('Q32_NATIVE_COMPLETE',label,flush=True);return dest
 def bank(self,index,x):
  key=(index,x['cap']);old=read(self.free[index]/'receipt.json');ids=old['ids'][:x['cap']];assert len(ids)==x['cap']or old['eog'][len(ids)-1]
  if key in self.banks:return self.banks[key]
  b=self.native.Bank.__new__(self.native.Bank);b.s=self;b.family='Qwen32B';b.index=index;b.input=x;b.free=self.free[index];b.teacher_count=10000+1000*len(self.banks);b.entries={};b.ep={**old,'ids':ids,'eog':old['eog'][:len(ids)],'terminal_kind':'EOG'if old['eog'][len(ids)-1]else'CAP'}
  prompt=x['prompt_ids']
  for n in range(len(old['ids'])):
   d=b.free/'captures'/str(len(prompt)+n);assert(d/'sequence.bin').exists();b.entries[tuple(prompt+old['ids'][:n])]=dict(vector=str(d/'frontier.f32'),state=str(d/'sequence.bin'))
  for (i,c),other in self.banks.items():
   if i==index:b.entries.update(other.entries)
  self.banks[key]=b;return b
 def pair(self,index,x,actual,heavy,clean,draft,mode='live'):
  meta=read(actual/'native/result.json');assert meta['total_observed_API_calls']['context_creates']==(2 if draft else 1)
  b=self.bank(index,x)
  if mode=='replay':
   def replay_physical(r,inp,d):
    rr=copy.deepcopy(r);rr['draft_physical_width_hist']={};p=self.native.Study.physical(rr,inp,False)if not d else None
    es=r['executions'];assert sum(z['width']for z in es)==len(inp['prompt_ids'])+4*len(r['cycles']);assert dict(Counter(str(z['width'])for z in es))==r['target_physical_width_hist'];assert not r['draft_physical_width_hist']and r['draft_calls']==0 and r['draft_final_kv']=={'min':-1,'max':-1}
    assert all(0<z['width']<=32 and z['active_cells']==z['position']+z['width']<=1024 for z in es);return dict(target_histogram=r['target_physical_width_hist'],draft_histogram={},target_rows=sum(z['width']for z in es),replay_zero_draft=True)
   self.physical=replay_physical
  try:proof=self.bank_check(b,actual/'native'/heavy,actual/'native'/clean,meta,draft)
  finally:self.physical=self.native.Study.physical
  save(self.out/'comparisons'/(actual.name+'--'+heavy+'.json'),proof);assert proof['passed'],'Full numerical/state mismatch: '+actual.name
  r=read(actual/'native'/heavy/'receipt.json');dispatch=self.dispatch(r)
  for (i,c),other in self.banks.items():
   if i==index:other.entries.update(b.entries)
  return dict(numerical=proof,dispatch=dispatch)
 def dispatch(self,r):
  graph=[z for z in r['geometry']if z['op']=='MUL_MAT'];assert graph
  mixed=[z for z in graph if z['sources']and z['sources'][0]['type']in('q4_K','q6_K')];assert mixed
  named=[z for z in mixed if z['name'].startswith(('hs_ref1_loop_','hs_ref1_group_'))]
  for z in named:
   assert z['ne'][1]==1 and z['sources'][1]['ne'][1]==1
   assert all(s['device']=='NVIDIA RTX A5000'for s in z['sources'][:2])and z['device']=='NVIDIA RTX A5000'
  if any(z['caller_rows']>1 for z in mixed):assert named,'No actual typed scalar projection dispatch'
  return dict(mixed_nodes=len(mixed),typed_REF1_nodes=len(named),types=sorted(set(z['sources'][0]['type']for z in named)),samples=named[:4],actual_widths=r['target_physical_width_hist'],basis='Actual real32B weight/activation descriptor, stride and GPU buffer observed for original typed scalar dot recipe; full model result independently checked',kernel_symbol_timing=False)
 def geometry(self):
  # The old geometry file supplies exposed INPUT tokens only. Every oracle
  # below is newly computed by the pristine32B reference, never an8B output.
  original=self.root/'run-01/inputs-01/Qwen-GEOMETRY.json';cases=read(original)['cases'];cases=copy.deepcopy(cases)
  for c in cases:
   n=sum(len(z['ids'])for z in c['forced']);p=len(c['forced'][0]['ids']);c['observe_positions']=list(range(p,n+1));c['state_positions']=[p,n]
  # Begin with actual owned short operands before paying long geometry cost.
  owned=self.roots[0]['prompt_ids']+read(self.free[0]/'receipt.json')['ids'];small=dict(name='own-short-q4',forced=[dict(ids=owned[:31],phase='PREFILL',all=False),dict(ids=owned[31:35],phase='VERIFY',all=True)],observe_positions=list(range(31,36)),state_positions=[31,35]);cases=[small]+cases
  save(self.out/'GEOMETRY_REGISTERED.json',dict(cases=cases,original_input_source_sha256=sha(original),outputs='New32B scalar R only',all_requested_rows=True))
  reports=[]
  for start in range(0,len(cases),2):
   group=cases[start:start+2];ref=self.execute('geometry-R-'+str(start),'Qwen32B',dict(cases=group))
   for arm,(core,cut,draft)in ARMS.items():
    if draft:continue
    actual=self.execute('geometry-'+arm+'-'+str(start),'Qwen32B',dict(cases=group,lowering=cut),core);meta=read(actual/'native/result.json');rows=[]
    for i,c in enumerate(group):
     record=meta['cases'][i];es=record['executions'];assert sum(z['width']for z in es)==sum(len(z['ids'])for z in c['forced']);assert all(z['active_cells']==z['position']+z['width']<=1024 for z in es)
     width=len(c['forced'][1]['ids']);vs=[z for z in es if z['phase']=='VERIFY'];assert sum(z['width']for z in vs)==width and sorted(j for z in vs for j in z['requested_rows'])==list(range(width))
     if cut=='LOCAL':assert len(vs)==1 and vs[0]['width']==width
     vectors=[];states=[]
     for n in c['observe_positions']:
      aa=actual/'native'/c['name']/'captures'/str(n);bb=ref/'native'/c['name']/'captures'/str(n);vectors.append(self.checks.vector_pair(aa/'frontier.f32',bb/'frontier.f32',meta['vocab']))
      if n in c['state_positions']:states.append(self.checks.state_pair(aa/'sequence.bin',bb/'sequence.bin',n,self.parse,self.profiles['Qwen32B']))
     dispatch=self.dispatch(dict(geometry=record['geometry'],target_physical_width_hist=dict(Counter(str(z['width'])for z in es))))
     rows.append(dict(case=c['name'],vectors=vectors,states=states,dispatch=dispatch,executions=vs));passed=all(z['equal']for z in vectors+states)
     save(self.out/'geometry-checks'/(arm+'-'+c['name']+'.json'),dict(passed=passed,**rows[-1]));assert passed,'32B geometry exact byte gate failed: '+arm+'/'+c['name']
    reports.append(dict(arm=arm,start=start,rows=rows));print('Q32_GEOMETRY_PASS',arm,start,flush=True)
  save(self.out/'GEOMETRY_COMPLETE.json',dict(passed=True,reports=reports,scope='Finite widths1,3,4,7,8,19,32; within/cross256/tail; every requested vector; all64-layer initial/final active states'))
 def additional_references(self):
  long=copy.deepcopy(read(self.root/'run-01/inputs-01/Qwen-DEVELOPMENT.json')['inputs'][3]);eog=copy.deepcopy(read(self.root/'d14-source-07/D14/EOG_FIXTURE_V1.json')['inputs'][0]);long.update(family='Qwen32B',cap=32);eog.update(family='Qwen32B',id='Q32/native-termination-fixture-v1')
  for name,x in [('long',long),('EOG',eog)]:
   save(self.out/(name+'-INPUT_REGISTERED.json'),dict(input=x,oracle='Own32B autonomous pristine R',benchmark=False))
   p=len(x['prompt_ids']);entry=dict(name=name,input=x,capture=True,state_positions=list(range(p,p+x['cap'])))
   out=self.execute('extra-free-R-'+name,'Qwen32B',dict(inputs=[entry]));ep=read(out/'native'/name/'receipt.json')
   if name=='EOG':assert ep['terminal_kind']=='EOG'and len(ep['ids'])>1,'No genuine32B EOG observed within fixed cap'
   self.roots.append(x);self.free.append(out/'native'/name)
 def natural(self):
  self.additional_references();reports=[]
  for arm,(core,cut,draft)in ARMS.items():
   arm_reports=[]
   for i,original in enumerate(self.roots):
    x={**original,'cap':32}if i in(1,2,3)else copy.deepcopy(original);inputs=[dict(name='heavy',input=x,capture=True),dict(name='clean',input=x,capture=False)]
    if i==0:inputs += [dict(name='cap1-'+kind,input={**x,'cap':1},capture=kind=='heavy')for kind in('heavy','clean')]
    actual=self.execute('natural-'+arm+'-'+str(i),'Qwen32B',dict(inputs=inputs,lowering=cut),core,draft);proof=self.pair(i,x,actual,'heavy','clean',draft)
    if i==0:proof['cap1']=self.pair(i,{**x,'cap':1},actual,'cap1-heavy','cap1-clean',draft)
    save(self.out/'natural-checks'/(arm+'-'+str(i)+'.json'),dict(passed=True,proof=proof));arm_reports.append(proof);print('Q32_NATURAL_PASS',arm,i,flush=True)
   reports.append(dict(arm=arm,roots=arm_reports))
  save(self.out/'NATURAL_COMPLETE.json',dict(passed=True,arms=reports,native_EOG=True,real_target_only_M=True,heavy_clean_bridge=True))
 def boundaries(self):
  for arm,(core,cut,draft)in ARMS.items():
   if not draft:continue
   oracle=read(self.free[0]/'receipt.json');requests=[];lookup={};vocab=self.structures['target']['vocab']
   specs=[('reject-'+str(j),j+2,j)for j in range(3)]+[('cap-'+str(cap),cap,None)for cap in(2,3,4)]+[('bonus',5,None),('cap1',1,None)]
   for name,cap,reject in specs:
    x={**self.roots[0],'cap':cap};proposals=oracle['ids'][1:8].copy()
    if reject is not None:proposals[reject]=(proposals[reject]+1)%vocab
    tape=dict(schema='heterospec.q32.R-derived-boundary-fixture.v1',root=x['id'],prompt_ids=x['prompt_ids'],max_k=7,target_sha256=self.models['target_sha256'],draft_sha256=self.models['draft_sha256'],autonomous_R_receipt_sha256=sha(self.free[0]/'receipt.json'),rows=[dict(base=len(x['prompt_ids']),seed=oracle['ids'][0],proposals=proposals)])
    x.update(proposal_tape=tape,proposal_tape_sha256=canonical(tape));lookup[name]=x
    requests += [dict(name=name+'-'+kind,input=x,capture=kind=='heavy')for kind in('heavy','clean')]
   actual=self.execute('boundaries-'+arm,'Qwen32B',dict(inputs=requests,lowering=cut),core,True,'replay');rows=[]
   for name,cap,reject in specs:
    proof=self.pair(0,lookup[name],actual,name+'-heavy',name+'-clean',True,'replay');r=read(actual/'native'/(name+'-heavy')/'receipt.json')
    if reject is not None:assert len(r['cycles'])==1 and r['cycles'][0]['rejected']and r['cycles'][0]['accepted']==reject
    if name=='bonus':assert len(r['cycles'])==1 and r['cycles'][0]['commit_kind']=='bonus'and r['cycles'][0]['accepted']==3
    if name.startswith('cap-'):assert r['cycles'][0]['commit_kind']=='accepted'and r['length']==cap
    if name=='cap1':assert not r['cycles']
    rows.append(dict(name=name,proof=proof))
   save(self.out/(arm+'-BOUNDARIES_COMPLETE.json'),dict(passed=True,rows=rows,scope='Controlled target-replay; actual zero draft work; distinct from live service'))
 def run(self):
  self.geometry();self.natural();self.boundaries()
  # These remaining contracts require explicit evidence before any timing.
  save(self.out/'CORE_GATES_COMPLETE.json',dict(passed=True,geometry=True,natural=True,controlled_transactions=True,remaining=['Native invalid-contract/capacity rejection gates','Real operand capture/recipe bridge','Freeze panel and independent primer endpoints'],timing_admitted=False))
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--builds',type=Path,required=True);a=p.parse_args()
 cutoff=datetime.datetime(2026,11,9,21,tzinfo=datetime.timezone.utc)
 while not(a.work/'reference/COMPLETE.json').exists():
  if(a.work/'reference/FAILURE.json').exists():raise RuntimeError('Independent reference failed; no candidate admitted')
  assert (cutoff-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>=960;time.sleep(10)
 while not(a.work/'GUARD_STOPPED.private.json').exists():time.sleep(1)
 s=Study(a);s.guard.mkdir();save(s.guard/'config.private.json',read(a.work/'config.private.json'))
 with(s.guard/'stdout.log').open('xb')as so,(s.guard/'stderr.log').open('xb')as se:guard=subprocess.Popen(['taskset','-c','36',sys.executable,'-B',str(Path(__file__).parent/'resource_guard.py'),'--work',str(s.guard)],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
 try:
  for _ in range(30):
   if(s.guard/'RESOURCE_GUARD_LATEST.private.json').exists():break
   assert guard.poll()is None;time.sleep(.5)
  with(a.root/'STUDY_SCHEDULING.lock').open('a+')as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);s.run()
 except BaseException as e:
  save(s.out/'FAILURE.json',dict(error=str(e),traceback=traceback.format_exc(),epoch=time.time(),automatic_native_retry=False,timing_admitted=False));raise
 finally:
  (s.guard/'GUARD_DONE').touch(exist_ok=False)
  try:guard.wait(timeout=20)
  except subprocess.TimeoutExpired:pass
if __name__=='__main__':main()
