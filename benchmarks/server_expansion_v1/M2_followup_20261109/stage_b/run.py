"""Bounded Stage B. Every native call uses the retained strict host adapter.

Prepare emits exact jobs/counts before any GPU access. Run requires a public
admission commitment. Reference extensions are separately derived artifacts;
old R receipts, implementations, source freezes and ledgers are never written.
"""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,importlib.util,json,os,shutil,sys,time,traceback
sys.dont_write_bytecode=True
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def prepare(a):
 r,w=a.root,a.work;w.mkdir();runtime=w/'runtime';shutil.copytree(r/'m2-runtime-03',runtime)
 hp=runtime/'host.py';text=hp.read_text();anchor='def reservation(job):';assert text.count(anchor)==1
 text=text.replace(anchor,anchor+"\n    if 'diagnostics' in job:\n        xs=job['diagnostics'];return len(xs),sum(x['position']+len(x['ids']) for x in xs)",1)
 anchor="        inherited=read(work/'INHERITED_ACCOUNTING.json')";assert text.count(anchor)==1
 text=text.replace(anchor,"        need(sum(r['requests'] for r in reserved)+req<=80,'Stage B ceiling, no stage transfer')\n"+anchor,1);hp.write_text(text)
 ledgers=[];requests=rows=0
 for name in ('run-01','m1-run-01','m2-run-01','m2-run-02','m2-run-03'):
  p=r/name/'ledger.jsonl';xs=[json.loads(s)for s in p.read_text().splitlines()];res=[x for x in xs if x['event']=='RESERVE']
  requests+=sum(x['requests']for x in res);rows+=sum(x['rows']for x in res);ledgers.append(dict(path=str(p),sha256=sha(p)))
 assert (requests,rows)==(1826,3021131),'Cumulative snapshot changed; do not assume remaining budget'
 save(w/'INHERITED_ACCOUNTING.json',dict(ledgers=ledgers,requests=requests,rows=rows))
 cfg=read(r/'m2-run-03/config.json');cfg.update(work_root=str(w),allocation_id='explicit-user-resumption-20261109-stage-B',freeze=None,freeze_sha256=None)
 assert cfg['worker_timeout_s']==900 and cfg['protected_gpu_indices']==[0]
 assert sha(cfg['reference_freeze'])==cfg['reference_freeze_sha256']=='fa8ceec6d54f98730d63880436a6bf088c119232c0f091406725e724a4665731'
 save(w/'config.private.json',cfg)
 selection=read(r/'m2-run-03/ROOT_SELECTION.json');save(w/'ROOT_SELECTION.private.json',selection)
 models=read(r/'run-01/inputs-01/MODELS.json')['Qwen'];models={k:v for k,v in models.items()if k in ('target_model','target_sha256')}
 base=dict(models,family='Qwen',n_ctx=1024,threads=2)
 extensions=[];maxrows=0
 for i,key in enumerate(selection['roots']):
  x=selection['inputs'][key];old=selection['expected'][key];assert sha(old['path'])==old['sha256'];ep=old['receipt'];assert ep==read(old['path'])
  assert len(ep['ids'])==128 and not any(ep['eog'])
  prompt=x['prompt_ids']+ep['ids'][:-1]
  if len(x['prompt_ids'])+len(ep['ids'])<260:
   cap=261-len(prompt);assert 0<cap<=128
   item=dict(name='extension',input=dict(x,prompt_ids=prompt,cap=cap),capture=True,state_positions=list(range(248,261)))
   job=dict(base,inputs=[item]);p=w/'jobs'/f'R-extension-{i}.json';save(p,job)
   bound=2*len(prompt)+16*cap;maxrows+=bound
   extensions.append(dict(origin=i,root=key,job=str(p),job_sha256=sha(p),prompt_tokens=len(prompt),cap=cap,rows_bound=bound,
      bridge_position=len(prompt),old_receipt_sha256=old['sha256'],old_pending_id=ep['ids'][-1]))
 assert len(extensions)==3
 # Four forced scalar trunks (one per original root) cover both geometries.
 maxrows+=4*260+32*260+24*260
 manifest=dict(schema='heterospec.pr210.stage-B.admission.v1',prepared_utc=stamp(),protocol_head='3268a63dcbde99d5d9f8dd461f34d56e9840d3a0',
    Stage_A_head='398e79a177bc71d83db4d58cf78672554f552586',original_reference_unchanged=True,reference_freeze_sha256=cfg['reference_freeze_sha256'],
    amendment='Explicitly register three same-R continuation extensions; exact old pending/frontier/active-KV bridge required. Original 128-token records and root order remain fixed.',
    origins=selection['roots'],extension_jobs=extensions,job_counts=dict(extension=3,forced_scalar_oracle=4,candidate_qualification=32,primer=8,timed=16,total_planned=63,stage_B_ceiling=80,unspent_failure_oracle_reservation=17),
    inherited=dict(requests=requests,rows=rows,request_ceiling=2048,row_ceiling=8000000),planned_rows_conservative_bound=maxrows,
    accounting='Each extension input, forced oracle case, or eight-output diagnostic operation is one logical request. q4pair is one request/two calls/eight physical rows. Restored prefix length is conservatively reserved again although not forwarded.',
    geometry=dict(within=248,crossing=252,append_tokens=8,observed_extent=256),target=dict(C=1024,KV='F16',FA=False,UB=32,reserve=8,cut='LOCAL',threads=2),
    R=dict(UB=1,reserve=1,executable_sha256=read(r/'run-01/build-R-01/BUILD.json')['executable_sha256']),
    allocation=dict(approved=True,device='Previously explicitly assigned GPU1; full UUID private',protected_indices=[0],CPU_affinity=[32,33]),
    timing=dict(origin=selection['roots'][0],rounds=2,block_order_round0=['loop4-within','loop4-crossing','packed-within','packed-crossing'],round1='reverse block order',execution_order=['q4pair,q8','q8,q4pair'],primers_per_cell=1,outputs='all eight full owned vocabulary vectors; same ownership moves on both paths',restore='outside primary operation timer; separately reported',qualification='all four roots, all eight cells, exact full vectors and active KV/frontier; no tolerance change'),
    shutdown=dict(new_worker_cutoff_BJT=a.cutoff,hard_archive_boundary_BJT=a.closure,worker_timeout_s=900,start_margin_s=960),
    next_stages='No automatic C/D/E or 32B; no optimization without measured hotspot and further bounded registration',new_task_policy='User revised policy: pause on assigned-GPU conflict, reserve violation, reboot or observable interference. Other-device jobs alone do not pause. Never signal foreign tasks.')
 save(w/'ADMISSION.private.json',manifest)
 public=json.loads(json.dumps(manifest))
 for e in public['extension_jobs']:e['job']=Path(e['job']).name
 save(w/'ADMISSION_PUBLIC.json',public)
 save(w/'SOURCE_AT_PREPARE.json',{p.name:sha(p)for p in Path(__file__).parent.iterdir()if p.is_file()})
 print(json.dumps(dict(prepared=True,planned_requests=63,rows_bound=maxrows)),flush=True)

class Runner:
 def __init__(self,a):
  self.a=a;self.r=a.root;self.w=a.work;self.plan=read(self.w/'ADMISSION.private.json');self.selection=read(self.w/'ROOT_SELECTION.private.json');self.models=read(self.r/'run-01/inputs-01/MODELS.json')['Qwen']
  sys.path.insert(0,str(self.w/'runtime'));import host,native_checks
  self.host=host;self.checks=native_checks;_,self.parse=native_checks.legacy_readers(a.repo);self.profile=read(self.r/'run-01/qualification-02/STATE_PROFILES.json')['Qwen']
  self.base=dict(family='Qwen',target_model=self.models['target_model'],target_sha256=self.models['target_sha256'],n_ctx=1024,threads=2)
  self.cutoff=datetime.datetime.fromisoformat(self.plan['shutdown']['new_worker_cutoff_BJT']);self.proofs=[];self.workers=[]
 def gate(self):
  assert not (self.w/'PAUSE.json').exists(),'New foreign work/reboot: admission paused'
  guard=read(self.w/'RESOURCE_GUARD_LATEST.private.json')
  assert time.time()-guard['epoch']<20 and not guard['events'],'Resource observer unavailable or conflict detected'
  assert (self.cutoff-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>=960,'Insufficient worker/archive window'
  for p,h in read(self.w/'SOURCE_AT_PREPARE.json').items():assert sha(Path(__file__).parent/p)==h,'Source changed after preparation'
 def run(self,name,job,core='reference'):
  self.gate();p=self.w/'jobs'/(name+'.json')
  if p.exists():assert read(p)==job
  else:save(p,job)
  build=self.r/'run-01/build-R-01/BUILD.json' if core=='reference' else self.a.builds/core/'BUILD.json'
  out=self.w/'runs'/name;t=time.monotonic();self.host.run(self.w/'config.private.json',build,p,out,'reference' if core=='reference' else 'development')
  self.workers.append(dict(name=name,core=core,wall_s=time.monotonic()-t,host_sha256=sha(out/'HOST.json'),module_map_sha256=sha(out/'LOADED_MODULES.json')))
  save(self.w/'worker-records'/(name+'.json'),self.workers[-1]);return out/'native'
 def state(self,actual,expected,n):return self.checks.state_pair(actual,expected,n,self.parse,self.profile)
 def vector(self,actual,expected):return self.checks.vector_pair(actual,expected,151936)
 def references(self):
  self.streams={};self.free={}
  for i,key in enumerate(self.selection['roots']):
   x=self.selection['inputs'][key];old=self.selection['expected'][key];assert sha(old['path'])==old['sha256'];oldfree=Path(old['path']).parent;ep=old['receipt'];stream=x['prompt_ids']+ep['ids'];free=oldfree
   if len(stream)<260:
    e=next(e for e in self.plan['extension_jobs']if e['origin']==i);job=read(e['job']);free=self.run(f'R-extension-{i}',job)/'extension';new=read(free/'receipt.json');prefix=job['inputs'][0]['input']['prompt_ids'];n=len(prefix)
    bridge=dict(origin=i,first_pending_equal=new['ids'][0]==ep['ids'][-1],frontier=self.vector(free/'captures'/str(n)/'frontier.f32',oldfree/'captures'/str(n)/'frontier.f32'),active_KV=self.state(free/'captures'/str(n)/'sequence.bin',oldfree/'captures'/str(n)/'sequence.bin',n),new_terminal=new['terminal_kind'])
    save(self.w/'reference-bridges'/f'{i}.json',bridge);assert bridge['first_pending_equal']and bridge['frontier']['equal']and bridge['active_KV']['equal'],'R continuation bridge failed'
    stream=prefix+new['ids'];assert len(stream)>=261 and not any(new['eog']),'Extended stream ended before required fixture; preserve root and stop'
   self.streams[i]=stream;self.free[i]=free
  # Independent scalar forced trunks, unchanged pristine R and original prompt
  # boundary. Each captures both initial states, every output and final states.
  self.oracles={}
  for i,key in enumerate(self.selection['roots']):
   prompt=self.selection['inputs'][key]['prompt_ids'];stream=self.streams[i]
   bridge_position=len(prompt)+127 if len(prompt)+127<=260 else len(prompt)
   positions=sorted(set(range(248,261))|{bridge_position})
   case=dict(name='trunk',forced=[dict(ids=prompt,phase='PREFILL'),dict(ids=stream[len(prompt):260],phase='FORCED')],observe_positions=positions,state_positions=positions)
   out=self.run(f'R-trunk-{i}',dict(self.base,cases=[case]));oracle=out/'trunk/captures';checks=[]
   for n in range(248,261):
    p=self.free[i]/'captures'/str(n)/'frontier.f32';assert p.exists(),'Independent autonomous frontier missing'
    v=self.vector(oracle/str(n)/'frontier.f32',p);checks.append(dict(position=n,vector=v));assert v['equal'],'Free/forced scalar disagreement'
   oldfree=Path(self.selection['expected'][key]['path']).parent;n=bridge_position
   b=self.state(oracle/str(n)/'sequence.bin',oldfree/'captures'/str(n)/'sequence.bin',n);assert b['equal'],'Forced trunk changed original reference state'
   save(self.w/'reference-bridges'/f'trunk-{i}.json',dict(passed=True,free_forced=checks,old_terminal_state=b));self.oracles[i]=oracle
  save(self.w/'REFERENCE_DERIVED_FREEZE.json',dict(status='DERIVED_ORACLES_FROZEN',old_R_unchanged=True,streams={str(i):ids[:260]for i,ids in self.streams.items()},files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))for o in self.oracles.values()for p in o.rglob('*')if p.is_file()]))
 def item(self,i,pos,execution,name,capture):
  oracle=self.oracles[i];initial=oracle/str(pos)
  return dict(name=name,origin=i,position=pos,ids=self.streams[i][pos:pos+8],execution=execution,capture=capture,
       state_path=str(initial/'sequence.bin'),state_sha256=sha(initial/'sequence.bin'),frontier_path=str(initial/'frontier.f32'),frontier_sha256=sha(initial/'frontier.f32'))
 def job(self,items):return dict(self.base,diagnostics=items,pause_file=str(self.w/'PAUSE.json'))
 def check(self,out,item,core,heavy):
  d=out/item['name'];r=read(d/'receipt.json');pos=item['position'];oracle=self.oracles[item['origin']];width=8 if item['execution']=='q8' else 4;calls=8//width
  assert r['ids']==item['ids']and r['position']==pos and r['execution']==item['execution']
  assert r['online_state_imports']==r['online_state_exports']==r['online_heavy_captures']==0
  assert r['physical_width_histogram']=={str(width):calls} and len(r['executions'])==calls
  for j,e in enumerate(r['executions']):
   assert e['position']==pos+j*width and e['width']==width and e['active_cells']==e['position']+width
   assert e['requested_rows']==list(range(width))
   assert e['expected_extents']==[256 if p<256 else 512 for p in range(e['position'],e['position']+width)]
   assert e['actual_attention_extent']==max(e['expected_extents'])
  assert r['final_bounds']==dict(min=0,max=pos+7)and r['output_vectors']==8 and r['output_floats']==8*151936
  assert r['output_sha256']==[sha(oracle/str(pos+j+1)/'frontier.f32')for j in range(8)],'Requested full vectors differ'
  proof=dict(name=item['name'],origin=item['origin'],core=core,position=pos,execution=item['execution'],physical_histogram=r['physical_width_histogram'],operation_s=r['operation_s'],all_eight_output_hashes_match=True)
  if heavy:
   proof['vectors']=[self.vector(d/f'row-{j}.f32',oracle/str(pos+j+1)/'frontier.f32')for j in range(8)]
   proof['initial_frontier']=self.vector(d/'initial/frontier.f32',oracle/str(pos)/'frontier.f32')
   proof['initial_KV']=self.state(d/'initial/sequence.bin',oracle/str(pos)/'sequence.bin',pos)
   proof['final_KV']=self.state(d/'final-sequence.bin',oracle/str(pos+8)/'sequence.bin',pos+8)
   assert all(v['equal']for v in proof['vectors'])and proof['initial_frontier']['equal']and proof['initial_KV']['equal']and proof['final_KV']['equal']
   nodes=[n for n in r['geometry']if n['phase']=='VERIFY'];packed=[n for n in nodes if n['name'].startswith('frontier_packed_')];loops=[n for n in nodes if n['name'].startswith('hs_backend_loop4_')]
   assert nodes and all(n['device']=='NVIDIA RTX A5000'for n in nodes)
   if width==8 and core=='packed':assert packed and all(n['ne'][1]==4 and n['ne'][2]>=2 for n in packed),'Missing actual packed q8 geometry'
   if width==4:assert not packed,'q4 cannot claim wide packing'
   if width==8 and core=='loop4':assert loops,'Missing marked loop4 projection'
   proof['dispatch']=dict(packed_nodes=len(packed),loop4_nodes=len(loops),samples=packed[:2]+loops[:2],scope='Scheduled tensor descriptors and core counters, not measured CUDA kernel launches')
  proof['passed']=True;return proof
 def qualify(self):
  for core in ('loop4','packed'):
   for i in range(4):
    items=[self.item(i,pos,execution,f'q-{i}-{pos}-{execution}',True)for pos in (248,252)for execution in ('q4pair','q8')]
    out=self.run(f'qualification-{core}-{i}',self.job(items),core)
    for item in items:self.proofs.append(self.check(out,item,core,True))
  assert len(self.proofs)==32;save(self.w/'QUALIFIED.json',dict(passed=True,cells=self.proofs,exact_vectors=True,active_KV=True,physical_width=True))
 def timing(self):
  assert read(self.w/'QUALIFIED.json')['passed'];blocks=[(core,pos)for core in ('loop4','packed')for pos in (248,252)];frozen=[]
  for round in range(2):
   for core,pos in (blocks if round==0 else list(reversed(blocks))):
    items=[]
    if round==0:
     items.extend(self.item(0,pos,e,'primer-'+e,False)for e in ('q4pair','q8'))
    order=('q4pair','q8')if round==0 else ('q8','q4pair')
    items.extend(self.item(0,pos,e,'timed-'+e,False)for e in order)
    frozen.append(dict(name=f'timing-s{round}-{core}-{pos}',core=core,round=round,position=pos,job=self.job(items)))
  save(self.w/'TIMING_PLAN.json',dict(frozen_before_timing_utc=stamp(),workers=frozen,measurement_requests=16,primer_requests=8))
  rows=[]
  for worker in frozen:
   out=self.run(worker['name'],worker['job'],worker['core'])
   for item in worker['job']['diagnostics']:
    proof=self.check(out,item,worker['core'],False);r=read(out/item['name']/'receipt.json');rows.append(dict(worker=worker['name'],round=worker['round'],kind='primer'if item['name'].startswith('primer')else 'measurement',core=worker['core'],position=worker['position'],execution=item['execution'],**r,checked=proof))
  contrasts=[]
  for core,pos in blocks:
   cells=[r for r in rows if r['kind']=='measurement'and r['core']==core and r['position']==pos];tot={e:sum(r['operation_s']for r in cells if r['execution']==e)for e in ('q4pair','q8')}
   assert len(cells)==4;contrasts.append(dict(core=core,position=pos,total_s=tot,q8_over_q4pair=tot['q8']/tot['q4pair']))
  save(self.w/'RESULTS.json',dict(status='COMPLETE_EQUALWORK_DIAGNOSTIC',scope='Two descriptive paired rounds, first predeclared exposed root only. Not live speculative service, whole/local attribution or population inference.',rows=rows,contrasts=contrasts))
 def execute(self):
  public=read(self.w/'PUBLIC_ADMISSION_BINDING.json');assert public['passed']and public['admission_sha256']==sha(self.w/'ADMISSION_PUBLIC.json')
  for name,h in read(self.w/'SOURCE_AT_PREPARE.json').items():assert sha(Path(__file__).parent/name)==h
  lockpath=self.r/'STUDY_SCHEDULING.lock'
  with lockpath.open('a+')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   self.references();self.qualify();self.timing()
  ledger=[json.loads(x)for x in (self.w/'ledger.jsonl').read_text().splitlines()];reserved=[x for x in ledger if x['event']=='RESERVE']
  assert sum(x['requests']for x in reserved)==63
  save(self.w/'COMPLETE.json',dict(passed=True,utc=stamp(),stage='B_ONLY',new_requests=63,conservative_rows_reserved=sum(x['rows']for x in reserved),workers=self.workers,candidate_optimization=False,next='No automatic C/D/E or 32B'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--builds',type=Path);p.add_argument('--repo',type=Path);p.add_argument('--prepare',action='store_true');p.add_argument('--cutoff',default='2026-11-09T20:30:00+08:00');p.add_argument('--closure',default='2026-11-09T21:00:00+08:00');a=p.parse_args()
 if a.prepare:prepare(a)
 else:
  try:Runner(a).execute()
  except BaseException as e:
   save(a.work/('STOPPED-'+str(time.time_ns())+'.json'),dict(status='STOPPED',utc=stamp(),error=str(e),traceback=traceback.format_exc(),no_automatic_retry=True));raise
if __name__=='__main__':main()
