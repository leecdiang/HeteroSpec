"""Optional B timing repair, exact closed B ELF/checkpoints/complete outputs.

Preparing is CPU/file-only. Execution requires completed public32B delivery,
unchanged8B budget, source/job/qualification freezes and enough whole-panel time.
Never recompiles, starts D/E, or admits the576-request confirmation experiment.
"""
from pathlib import Path
from collections import defaultdict
import argparse,datetime,fcntl,hashlib,importlib.util,json,math,os,shutil,subprocess,sys,time,traceback
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p);p.write_text(json.dumps(x,indent=2)+'\n')
STOP=datetime.datetime(2026,11,9,21,tzinfo=datetime.timezone.utc)
def prepare(a):
 r,w=a.root,a.work;b=r/'pr210-stage-b-20261109-05';c=r/'pr210-stage-c-20261109-01';w.mkdir()
 qualified=b/'QUALIFIED.json';assert sha(qualified)=='4f851b57aa21879beb2e4b0a36bf8dd6f329895e4054efeb8a2d8efc5df94a37';q=read(qualified);assert q['passed']and len(q['cells'])==32 and all(x['passed']for x in q['cells'])
 # Verify the public archived commitments, including all actual retained heavy
 # numerical capture bytes. This does not execute or invent new qualification.
 archive=r/'pr210-stage-b-export-03';index=read(archive/'BINARY_CAPTURE_INDEX.json')['files'];captures=[]
 for x in index:
  if x['path'].startswith(b.name+'/runs/qualification-'):
   p=r/x['path'];assert p.stat().st_size==x['bytes']and sha(p)==x['sha256'];captures.append(x)
 frozen=read(b/'REFERENCE_DERIVED_FREEZE.json');assert frozen['status']=='DERIVED_ORACLES_FROZEN'and frozen['old_R_unchanged']
 for x in frozen['files']:assert Path(x['path']).stat().st_size==x['bytes']and sha(x['path'])==x['sha256']
 previous=read(c/'INHERITED_ACCOUNTING.json');ledger=c/'ledger.jsonl';entries=[json.loads(x)for x in ledger.read_text().splitlines()];reserved=[x for x in entries if x['event']=='RESERVE'];counts=dict(requests=previous['requests']+sum(x['requests']for x in reserved),rows=previous['rows']+sum(x['rows']for x in reserved));assert counts==dict(requests=1909,rows=3053954)
 inherited=dict(ledgers=previous['ledgers']+[dict(path=str(ledger),sha256=sha(ledger))],**counts)
 for x in inherited['ledgers']:assert sha(x['path'])==x['sha256']
 save(w/'INHERITED_ACCOUNTING.json',inherited)
 shutil.copytree(b/'runtime',w/'runtime',ignore=shutil.ignore_patterns('__pycache__'))
 p=w/'runtime/host.py';s=p.read_text();anchor="            if 'inputs' in job:\n                need([m['name']";assert s.count(anchor)==1
 s=s.replace(anchor,"            if 'diagnostics' in job:\n                need([m['name']for m in markers]==[x['name']for x in job['diagnostics']],'Complete ordered B2 external markers required')\n                save(out/'CLOCKS.json',dict(markers=markers,boundary='External launch-to-complete markers for all four warm then four measured operations; first warm includes process/model start; subsequent marker deltas include operand disk/SHA/restore, operation, output SHA and serialization; no legacy two-primer burst'))\n            elif 'inputs' in job:\n                need([m['name']",1);compile(s,str(p),'exec');p.write_text(s)
 cfg=read(b/'config.private.json');cfg['work_root']=str(w);cfg['disk_reserve_bytes']=max(cfg['disk_reserve_bytes'],100*1024**3);save(w/'config.private.json',cfg)
 base={k:read(next((b/'jobs').glob('qualification-loop4-0.json')))[k]for k in ('family','target_model','target_sha256','n_ctx','threads')};assert sha(base['target_model'])==base['target_sha256']
 oracle=b/'runs/R-trunk-0/native/trunk/captures';assert oracle.exists();stream=frozen['streams']['0'];assert len(stream)==260
 builds={};known=set()
 for core in ('loop4','packed'):
  folder=r/'pr210-stage-b-build-02'/core;build=read(folder/'BUILD.json');assert sha(build['executable'])==build['executable_sha256']
  for p,h in read(folder/'DEPENDENCIES.json')['files'].items():
   if p not in known:assert sha(p)==h;known.add(p)
  modules=read(b/f'runs/qualification-{core}-0/LOADED_MODULES.json')
  for p,v in modules.items():
   if v['kind']=='ELF_file':assert sha(p)==v['sha256']
  builds[core]=dict(path=str(folder/'BUILD.json'),sha256=sha(folder/'BUILD.json'),executable_sha256=build['executable_sha256'],loaded_modules=modules,context=read(b/f'runs/qualification-{core}-0/native/result.json')['context'])
 cells=[(core,pos)for core in ('loop4','packed')for pos in (248,252)];orders=[[0,1,3,2],[1,2,0,3],[2,3,1,0],[3,0,2,1]];workers=[]
 for rnd,order in enumerate(orders):
  for position,cell in enumerate(order):
   core,pos=cells[cell];warm=['q4pair','q8','q8','q4pair']if rnd%2==0 else['q8','q4pair','q4pair','q8'];measured=['q4pair','q8','q8','q4pair']if rnd<2 else['q8','q4pair','q4pair','q8'];items=[]
   for role,executions in [('warm',warm),('measured',measured)]:
    for i,path in enumerate(executions):
     initial=oracle/str(pos);items.append(dict(name=f'{role}-{i}-{path}',origin=0,position=pos,ids=stream[pos:pos+8],execution=path,capture=False,state_path=str(initial/'sequence.bin'),state_sha256=sha(initial/'sequence.bin'),frontier_path=str(initial/'frontier.f32'),frontier_sha256=sha(initial/'frontier.f32')))
   job={**base,'diagnostics':items,'pause_file':str(w/'PAUSE.json')};name=f'r{rnd}-p{position}-{core}-{pos}';path=w/'jobs'/(name+'.json');save(path,job);workers.append(dict(id=name,core=core,boundary=pos,round=rnd,cell_position=position,job=str(path.relative_to(w)),job_sha256=sha(path)))
 rows=sum(x['position']+len(x['ids'])for worker in workers for x in read(w/worker['job'])['diagnostics']);assert rows==33024 and inherited['requests']+128<=2048 and inherited['rows']+rows<=8000000
 old_cost=[read(p)['wall_s']for p in(b/'worker-records').glob('timing-*.json')];assert len(old_cost)==8;estimate=16*max(old_cost)*1.35+120
 save(w/'PLAN.json',dict(schema='heterospec.pr210.controlled-B2.v1',workers=workers,cells=cells,orders=orders,warmup_requests=64,measured_requests=64,total_requests=128,reserved_rows=rows,whole_panel_estimate_s=estimate,old_full_caller_max_s=max(old_cost),complete_all_eight_outputs=True,identical_state_restore_before_every_operation=True,qualifications_reused=32,independent_processes_per_cell=4,analysis='Descriptive process-blocked contrasts; only exposed root0; no general steady-state, live-service or population-confirmation claim',reuse=dict(qualified_sha256=sha(qualified),reference_derived_freeze_sha256=sha(b/'REFERENCE_DERIVED_FREEZE.json'),original_checker_source_sha256=sha(r/'pr210-stage-b-source-05/run.py'),heavy_capture_commitments=captures,builds=builds,oracle=str(oracle)),execution_requires='Full32B delivery public byte/statistical readback PASS and enough complete-panel time; no native auto-retry'))
 save(w/'PREPARED.json',dict(passed=True,zero_native_requests=True,zero_GPU_forwards=True,plan_sha256=sha(w/'PLAN.json'),source_sha256=sha(Path(__file__)),runtime={p.name:sha(p)for p in(w/'runtime').iterdir()if p.is_file()}))
 print('B2_CPU_ONLY_PREPARED',len(workers),128)
def execute(a):
 r,w=a.root,a.work;plan=read(w/'PLAN.json');prepared=read(w/'PREPARED.json');assert sha(Path(__file__))==prepared['source_sha256']and sha(w/'PLAN.json')==prepared['plan_sha256']
 activation=w/'ACTIVATION_PUBLIC_BINDING.json';activated=read(activation);assert activated['passed']and activated['plan_sha256']==prepared['plan_sha256']and activated['Q32_complete_public_readback']is True
 assert (STOP-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>plan['whole_panel_estimate_s']+900,'Whole B2 panel and closure margin cannot fit'
 for n,h in prepared['runtime'].items():assert sha(w/'runtime'/n)==h
 sys.path.insert(0,str(w/'runtime'));import host
 # Import the unchanged original checker, without executing its main/Runner.
 old=r/'pr210-stage-b-source-05/run.py';assert sha(old)==plan['reuse']['original_checker_source_sha256'];sys.path.insert(0,str(old.parent));spec=importlib.util.spec_from_file_location('_closed_B_check',old);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);checker=module.Runner.__new__(module.Runner);checker.oracles={0:Path(plan['reuse']['oracle'])}
 guard=None;records=[]
 with(w/'guard.stdout.log').open('xb')as so,(w/'guard.stderr.log').open('xb')as se:guard=subprocess.Popen(['taskset','-c','36',sys.executable,'-B',str(Path(__file__).parent/'b2_resource_guard.py'),'--work',str(w)],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
 try:
  for _ in range(30):
   if(w/'RESOURCE_GUARD_LATEST.private.json').exists():break
   assert guard.poll()is None;time.sleep(.5)
  with(r/'STUDY_SCHEDULING.lock').open('a+')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   for worker in plan['workers']:
    assert not(w/'PAUSE.json').exists()and (STOP-datetime.datetime.now(datetime.timezone.utc)).total_seconds()>=960
    latest=read(w/'RESOURCE_GUARD_LATEST.private.json');assert time.time()-latest['epoch']<20 and not latest['events'];assert sha(w/'PLAN.json')==prepared['plan_sha256']
    job_path=w/worker['job'];assert sha(job_path)==worker['job_sha256'];job=read(job_path);build=plan['reuse']['builds'][worker['core']];assert sha(build['path'])==build['sha256'];out=w/'runs'/worker['id'];began=time.monotonic();host.run(w/'config.private.json',Path(build['path']),job_path,out,'development');caller=time.monotonic()-began
    assert read(out/'LOADED_MODULES.json')==build['loaded_modules'];native=read(out/'native/result.json');assert native['context']==build['context']and native['draft_calls']==0
    items=[]
    for item in job['diagnostics']:
     proof=module.Runner.check(checker,out/'native',item,worker['core'],False);receipt=read(out/'native'/item['name']/'receipt.json');assert not receipt['capture'];items.append(dict(role='warm'if item['name'].startswith('warm-')else'measured',item=item,proof=proof,receipt=receipt,receipt_sha256=sha(out/'native'/item['name']/'receipt.json')))
    row=dict(worker=worker,caller_inclusive_wall_s=caller,host=read(out/'HOST.json'),external_clocks=read(out/'CLOCKS.json'),operations=items);save(w/'checked'/(worker['id']+'.json'),dict(passed=True,**row));records.append(row);print('B2_CHECKED_WORKER',worker['id'],flush=True)
  assert len(records)==16;contrasts=[]
  for core,pos in plan['cells']:
   ratios=[];full=[]
   for record in records:
    if(record['worker']['core'],record['worker']['boundary'])!=(core,pos):continue
    sums=defaultdict(float)
    for x in record['operations']:
     if x['role']=='measured':sums[x['item']['execution']]+=x['receipt']['operation_s']
    ratio=sums['q8']/sums['q4pair'];ratios.append(ratio);full.append(dict(worker=record['worker']['id'],q8_over_q4pair=ratio,operation_totals_s=dict(sums),complete_caller_s=record['caller_inclusive_wall_s']))
   assert len(ratios)==4;contrasts.append(dict(core=core,boundary=pos,process_ratios=ratios,paired_process_geomean_ratio=math.exp(sum(map(math.log,ratios))/4),process_range=[min(ratios),max(ratios)],processes=full))
  save(w/'RESULTS.json',dict(passed=True,descriptive_only=True,warmups=64,measurements=64,workers=16,contrasts=contrasts,limitations=['Only one exposed root at two boundaries and two projections','Four independent processes per cell; uniform two full warm operations per path, not proof that every possible history is steady','Exact unchanged B ELF/state/full-output qualification reused; new clean operations check all eight full vector hashes and actual physical width, not repeated internal KV exports','No live drafting or end-to-end speculative-service speedup claim; full process/operand/restore/output-SHA/serialization costs retained'],records=records));save(w/'COMPLETE.json',dict(passed=True,requests=128,reserved_rows=33024,no_automatic_D_E_or_confirmation=True))
 except BaseException as e:save(w/'FAILURE.json',dict(error=str(e),traceback=traceback.format_exc(),no_automatic_native_retry=True));raise
 finally:
  (w/'GUARD_DONE').touch(exist_ok=False)
  try:guard.wait(timeout=20)
  except subprocess.TimeoutExpired:pass
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--prepare',action='store_true');p.add_argument('--execute',action='store_true');a=p.parse_args();assert a.prepare!=a.execute;prepare(a)if a.prepare else execute(a)
