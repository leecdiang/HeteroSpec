from pathlib import Path
import json,hashlib,subprocess,sys
from datetime import datetime,timezone
ROOT=Path(__file__).parent;BASE=Path('C:/hs/b570-closeout-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def same(a,b):return all(a.get(k)==b.get(k) for k in ['ids','eog','reason'])
am=load(ROOT/'AMENDMENT.json')
for n,h in am['before_sources'].items():assert sha(BASE/n)==h,n
for n,h in am['after_sources'].items():assert sha(ROOT/n)==h,n
for n,h in am['original_numerical_assets'].items():assert sha(BASE/n)==h,n
assert (BASE/'STOP').exists() and not (BASE/'LOCK.json').exists()
save(ROOT/'BUILD_FREEZE.json',dict(utc=datetime.now(timezone.utc).isoformat(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),executables={p.name:sha(p) for p in (ROOT/'build/Release').glob('*.exe')},libraries={p.name:sha(p) for p in (ROOT/'build/Release').glob('*.dll')},compiler='MSVC 19.44.35228; VS17 x64 Release; pinned library ABI',numeric_cpp_unchanged=all(sha(ROOT/'src'/n)==sha(BASE/'src'/n) for n in ['native.cpp','target.cpp','CMakeLists.txt']),observer_only=True))
for stage in ['BRIDGE','MECHANISM_SUPPLEMENT']:
 subprocess.run([sys.executable,str(ROOT/'runner.py'),'schedule',stage,str(ROOT/(stage+'_SCHEDULE.json'))],cwd=ROOT,check=True)
 rows=[r for r in load(ROOT/(stage+'_RESULTS.json')) if not r['warm']]
 if stage=='BRIDGE':
  historical=load(ROOT/'HISTORICAL_EXPECTED.json');bad=[]
  for r in rows:
   tag='N0' if r['config']['label']=='N0_ordinary' else 'R'
   ref=historical[r['task']+'/'+tag+'/1'];ref=dict(ref,reason='EOG' if ref['endpoint']=='EOG' else 'CAP')
   if not same(r['endpoint'],ref):bad.append(r['unit_id'])
  save(ROOT/'BRIDGE_QUALIFICATION.json',dict(status='PASS' if not bad else 'BLOCKED_REFERENCE',requests=len(rows),failed=bad))
  assert not bad,bad
save(ROOT/'DONE.json',dict(utc=datetime.now(timezone.utc).isoformat(),nonwarm=18,warm=14,model_auxiliary_decodes=0,original_science_replayed=False,new_performance_samples=0))
(ROOT/'STOP').write_text('Bounded audit supplement finished. CPU review only.\n',encoding='utf-8')
print('AUDIT SUPPLEMENT MODEL REQUESTS COMPLETE',flush=True)
