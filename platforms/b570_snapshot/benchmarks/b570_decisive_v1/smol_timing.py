"""Fixed all-arm pilot, immutable freeze and complete balanced confirmation."""
from smol_driver import *
from common import digest
from design import ARMS as DESIGN_ARMS,SESSIONS
from analyze import analyze

def register():
 DESIGN_ARMS['b570-smol-draft']=ARMS;SESSIONS['b570-smol-draft']=6

def endpoint(group,index):
 prefix='dev' if group=='development' else 'test'
 return read(SROOT/EPOCH/'runs'/f'{prefix}-{index}-oldR'/'0.json')

def pair(name,arm,r,reference):
 if not done(name):execute(name,arm,[r,r])
 folder=SROOT/EPOCH/'runs'/name
 for j in range(2):
  x=read(folder/(str(j)+'.json'))
  assert (x['ids'],x['eog'])==(reference['ids'],reference['eog']),('timing endpoint mismatch',name,j)
  assert 'committed_states' not in x and not x['trace'],'diagnostic capture in clean timing'
 return [read(folder/(str(j)+'.json.metrics.json')) for j in range(2)]

def pilot():
 records=[]
 for i in range(4):
  q=read(SROOT/EPOCH/f'dev-{i}-QUALIFICATION.json');assert q['status']=='FINITE_NATIVE_CAPTURE_MATCH'
  r=input_row('development',i);reference=endpoint('development',i)
  # Fixed rotation, one pair per arm/root; no pilot-driven selection.
  for a in range(6):
   arm=ARMS[(a+i)%6];name=f'pilot-{i}-{arm}'
   for j,m in enumerate(pair(name,arm,r,reference)):
    records.append(dict(root_id=r['root_id'],input_id=r['id'],arm=arm,kind='warmup' if j==0 else 'measure',service_s=m['service_ms']/1000,endpoint_equal=True,metrics_sha256=sha(SROOT/EPOCH/'runs'/name/(str(j)+'.json.metrics.json'))))
 report=dict(status='COMPLETE_FIXED_DEVELOPMENT_PILOT',measurements=24,warmups=24,all_six_arms_retained=True,confirmation_tuning=False,records=records,measured_total_seconds={a:sum(x['service_s'] for x in records if x['arm']==a and x['kind']=='measure') for a in ARMS})
 write(SROOT/EPOCH/'PILOT.json',report);print(report['status'],report['measured_total_seconds'],flush=True)

def freeze():
 assert not list((SROOT/EPOCH/'runs').glob('test-*')),'Test exposure before source freeze'
 assert read(SROOT/EPOCH/'PILOT.json')['status']=='COMPLETE_FIXED_DEVELOPMENT_PILOT'
 head=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','rev-parse','HEAD'],cwd=HERE,text=True).strip()
 dirty=subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','status','--porcelain'],cwd=HERE,text=True);assert not dirty,'Commit reviewable source before freezing'
 proofs=[]
 for base in (HERE,TOOLKIT):
  for p in sorted(base.rglob('*')):
   if p.is_file() and p.suffix in ('.py','.cpp','.hpp','.h','.md','.json') and '__pycache__' not in p.parts:
    snapshot=SROOT/EPOCH/'source-freeze'/('host' if base==HERE else 'toolkit')/p.relative_to(base);snapshot.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snapshot)
    proofs.append(dict(path=str(p),snapshot=snapshot.relative_to(ROOT).as_posix(),sha256=sha(p)))
 bindings={a:sha(SROOT/EPOCH/a/'FILES.json') for a in ARMS}
 for a in ARMS:
  for f in read(SROOT/EPOCH/a/'FILES.json')['files']:assert sha(f['path'])==f['sha256']
 native_sources={}
 for base in [SROOT/EPOCH/a for a in ARMS]+[SROOT/'forced-reference02']:
  for p in base.iterdir():
   if p.is_file() and p.suffix in ('.cpp','.h','.hpp','.txt','.json'):native_sources[p.relative_to(ROOT).as_posix()]=sha(p)
 data={n:sha(SROOT/'cohort'/n) for n in ('INPUTS.json','PANEL.json','SCHEDULE.json','SELECTION_AUDIT.json','EXPOSURE_SUPPLEMENT.json','POPULATION_RECOMPUTATION.json','rendered.jsonl','tokenized.jsonl')}
 write(SROOT/EPOCH/'PYTHON_BINDING.json',dict(version=sys.version,executable_sha256=sha(sys.executable),optimize=sys.flags.optimize,numpy=np.__version__,python_optimize_environment=os.environ.get('PYTHONOPTIMIZE'),template_dependency='jinja2 3.1.6 used only for pre-output rendering'))
 native_sources[(SROOT/EPOCH/'PYTHON_BINDING.json').relative_to(ROOT).as_posix()]=sha(SROOT/EPOCH/'PYTHON_BINDING.json')
 write(SROOT/EPOCH/'FREEZE.json',dict(utc=utc(),source_commit=head,source_proofs=proofs,native_source_proofs=native_sources,data_proofs=data,binary_manifest_sha256=bindings,reference_manifest_sha256=sha(SROOT/'original-FILES.json'),forced_reference_manifest_sha256=sha(SROOT/'forced-reference02/FILES.json'),panel_sha256=sha(SROOT/'cohort/PANEL.json'),schedule_sha256=sha(SROOT/'cohort/SCHEDULE.json'),exposure_supplement_sha256=sha(SROOT/'cohort/EXPOSURE_SUPPLEMENT.json'),state_profile_sha256=sha(SROOT/'STATE_PROFILE.json'),pilot_sha256=sha(SROOT/EPOCH/'PILOT.json'),arms=ARMS,all_controls_retained=True,source_frozen_before_test=True,main_slots=864,analysis='all15 fixed contrasts; primary total complete service; equal-root log sensitivity; root bootstrap10000; no extra sessions',lifecycle=read(SROOT/EPOCH/'PROSPECTIVE.json')['lifecycle']))

def assert_frozen():
 f=read(SROOT/EPOCH/'FREEZE.json');receipt=read(SROOT/EPOCH/'PUBLISHED_FREEZE.json')
 binding=read(SROOT/EPOCH/'PYTHON_BINDING.json');assert sha(sys.executable)==binding['executable_sha256'] and sys.flags.optimize==binding['optimize']==0 and np.__version__==binding['numpy']
 assert receipt['freeze_sha256']==sha(SROOT/EPOCH/'FREEZE.json') and receipt['remote_readback_equal']
 for a,h in f['binary_manifest_sha256'].items():
  assert h==sha(SROOT/EPOCH/a/'FILES.json')
  for x in read(SROOT/EPOCH/a/'FILES.json')['files']:assert sha(x['path'])==x['sha256']
 for x in f['source_proofs']:assert sha(x['path'])==x['sha256'],x['path']
 for path,h in f['native_source_proofs'].items():assert sha(ROOT/path)==h
 for name,h in f['data_proofs'].items():assert sha(SROOT/'cohort'/name)==h
 for manifest,h in ((SROOT/'original-FILES.json',f['reference_manifest_sha256']),(SROOT/'forced-reference02/FILES.json',f['forced_reference_manifest_sha256'])):
  assert sha(manifest)==h
  for x in read(manifest)['files']:assert sha(x['path'])==x['sha256']
 assert f['panel_sha256']==sha(SROOT/'cohort/PANEL.json') and f['schedule_sha256']==sha(SROOT/'cohort/SCHEDULE.json')
 return f

def test_qualification():
 assert_frozen()
 for i in range(12):qualify_root('test',i)

def main_panel():
 f=assert_frozen();register();panel=read(SROOT/'cohort/PANEL.json');plan=read(SROOT/'cohort/SCHEDULE.json');records=[]
 assert not list((SROOT/EPOCH/'runs').glob('main-*')),'Existing confirmation attempt requires explicit whole-session disposition; never silently resume or replace slots'
 for i in range(12):assert read(SROOT/EPOCH/f'test-{i}-QUALIFICATION.json')['status']=='FINITE_NATIVE_CAPTURE_MATCH'
 byid={r['id']:i for i,r in enumerate(panel['test'])};inputs=read(SROOT/'cohort/INPUTS.json')
 for k in range(0,len(plan['slots']),2):
  a,b=plan['slots'][k:k+2];assert a['kind']=='warmup' and b['kind']=='measure' and a['arm']==b['arm'] and a['root_id']==b['root_id']
  ix=byid[a['input_id']];r=inputs[a['input_id']];reference=endpoint('test',ix);name=f"main-s{a['session']}-r{ix}-{a['arm']}"
  metrics=pair(name,a['arm'],r,reference)
  for slot,m in zip((a,b),metrics):records.append(dict(slot,service_s=m['service_ms']/1000,status='COMPLETE',endpoint_equal=True,fallback_count=0,endpoint_sha256=digest([reference['ids'],reference['eog']]),source_freeze_sha256=sha(SROOT/EPOCH/'FREEZE.json'),numeric_profile_sha256=sha(SROOT/'STATE_PROFILE.json'),metrics_sha256=sha(SROOT/EPOCH/'runs'/name/('0.json.metrics.json' if slot['kind']=='warmup' else '1.json.metrics.json'))))
  write(SROOT/EPOCH/'main-progress'/(str(k//2)+'.json'),dict(completed_slots=len(records),total_slots=len(plan['slots']),last_slot=b,utc=utc()))
 report=dict(lane='b570-smol-draft',panel_sha256=digest(panel),frozen_before_test=True,qualification_status='FINITE_NATIVE_CAPTURE_MATCH',source_freeze_sha256=sha(SROOT/EPOCH/'FREEZE.json'),numeric_profile_sha256=sha(SROOT/'STATE_PROFILE.json'),records=records)
 write(SROOT/EPOCH/'RECORDS.json',report);write(SROOT/EPOCH/'ANALYSIS.json',analyze(panel,'b570-smol-draft',report))

if __name__=='__main__':
 action=sys.argv[1];started=utc();t0=time.monotonic();success=False
 try:
  {'pilot':pilot,'freeze':freeze,'qualify':test_qualification,'main':main_panel}[action]();success=True
 finally:write(SROOT/EPOCH/('PHASE-'+action+'-'+started.replace(':','').replace('.','')+'.json'),dict(action=action,started_utc=started,finished_utc=utc(),wall_seconds=time.monotonic()-t0,success=success,includes_child_native_and_storage=True,additive_to_native_cost=False))
