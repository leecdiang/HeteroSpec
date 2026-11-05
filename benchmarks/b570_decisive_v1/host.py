"""Original B570 host execution, additive to PR185 and historical evidence."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
TOOLKIT=HERE.parent/'tpds_decisive_v1'
if not TOOLKIT.exists():TOOLKIT=HERE.parent/'toolkit'
sys.path.insert(0,str(TOOLKIT))
from runner import Ledger
from stage_sources import b570_draft,observe_b570
ROOT=Path(os.environ.get('HS_DECISIVE_ROOT','I:/HeteroSpec/b570-decisive-20261105'))
OLD=Path('I:/HeteroSpec/b570-qwen-transfer-20261103')
ORACLE=Path('C:/hs/b570-native-reproduction-20261026')
HISTORY=Path('C:/hs/b570-producer-consumer-20261028')
LOCK=Path('C:/hs/b570-llama-exclusive.lock')
LIMITS=dict(requests=6144,token_rows=12000000,operators=2048)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def command(argv,log):
 started=utc();t0=time.monotonic();ok=False
 try:
  with Path(log).open('x',encoding='utf-8') as f:subprocess.run(list(map(str,argv)),stdout=f,stderr=subprocess.STDOUT,check=True)
  ok=True
 finally:write(str(log)+'.cost.json',dict(started_utc=started,finished_utc=utc(),wall_seconds=time.monotonic()-t0,success=ok,model_requests=0))
def setup():
 members=read(Path('I:/HeteroSpec/b570-qwen-transfer-delivery-20261103/MEMBERS.json'))['files']
 pins={x['path']:x for x in members}
 source=OLD/'shared-01/kit/b570_producer_consumer_boundary_v1/native/boundary.cpp'
 key=source.relative_to(OLD).as_posix();assert sha(source)==pins[key]['sha256']
 freeze=read(OLD/'FREEZE.json')
 for p in freeze['proofs']:assert sha(p['path'])==p['sha256'],p['path']
 for role in ('original-final','shared-01'):
  for f in read(OLD/role/'FILES.json')['files']:assert Path(f['path']).stat().st_size==f['bytes'] and sha(f['path'])==f['sha256']
 models=read(OLD/'MODEL_PINS.json')['files']
 for f in models:assert sha(f['path'])==f['sha256'] and Path(f['path']).stat().st_size==f['bytes']
 write(ROOT/'AUTHENTICATION.json',dict(utc=utc(),design_head='8befecc2484d749085ed95fca064b6acc42e7b1d',inherited_freeze_sha256=sha(OLD/'FREEZE.json'),worker_source=key,worker_sha256=sha(source),models=models,source_manifest_sha256=sha(Path('I:/HeteroSpec/b570-qwen-transfer-delivery-20261103/MEMBERS.json')),old_reference_unchanged=True))
 write(ROOT/'RESOURCE_LIMITS.json',dict(limits=LIMITS,per_worker_wall_seconds=900,per_request_wall_seconds=180,disk_reserve_bytes=20*1024**3,ram_reserve_bytes=2*1024**3,device_reserve_bytes=128*1024**2,job_memory_bytes=16*1024**3,zero_forward_max=10,planned_main_requests=600,development_roots=4,test_roots=12,source='PR185 C1024 dual-weight-resident fresh-context lifecycle'))
 for role in ('R','C1U1','C4U1','C4U2','C4U4'):
  dest=ROOT/role;dest.mkdir();shutil.copytree(OLD/('original-final' if role=='R' else 'shared-01')/'kit',dest/'kit')
  p=dest/'kit/b570_producer_consumer_boundary_v1/native/boundary.cpp'
  if role!='R':p.write_bytes(b570_draft(source.read_bytes(),int(role[1]),int(role[3])))
  shutil.copyfile(TOOLKIT/'native/draft_prefill.hpp',p.parent/'draft_prefill.hpp')
  header=p.parent/'transfer_scope.hpp';s=header.read_text();anchor='    min_device_free = std::min(min_device_free,available);'
  assert s.count(anchor)==1
  s=s.replace(anchor,'    need(available <= total, "device free exceeds total");\n'+anchor);header.write_text(s,encoding='utf-8')
  write(dest/'SOURCE.json',dict(worker_sha256=sha(p),resource_header_sha256=sha(header),historical_worker_sha256=sha(OLD/('original-final' if role=='R' else 'shared-01')/'kit/b570_producer_consumer_boundary_v1/native/boundary.cpp'),numeric_libraries='original' if role=='R' else 'PR165 shared-01'))
 assert (HERE/'supervisor.py').exists(),'Reviewed process supervisor missing'
def build(role):
 dest=ROOT/role;unit=dest/'kit/b570_producer_consumer_boundary_v1'
 command(['cmake','-S',unit,'-B',dest/'build','-G','Visual Studio 17 2022','-A','x64','-DLLAMA_SOURCE='+str(ORACLE/'clean-source2/llama.cpp-0cae43063cf15170e91a2ff4d034da0ecef4a1b2' if role=='R' else OLD/'source-01'),'-DQUALIFIED_BUILD='+str(ORACLE/'build' if role=='R' else OLD/'build-01')],dest/'configure.log')
 command(['cmake','--build',dest/'build','--config','Release','--parallel','4'],dest/'compile.log')
 bins=dest/'build/bin/Release';historical=OLD/('original-final' if role=='R' else 'shared-01')/'build/bin/Release'
 for p in historical.glob('*.dll'):shutil.copyfile(p,bins/p.name)
 write(dest/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.dll','.exe')]))
def run(name,role,slots,*,admit=False,panel=None,extra=None,token_rows=None):
 assert not LOCK.exists(),'Another owned GPU worker is active'
 assert shutil.disk_usage(ROOT).free>20*1024**3
 auth=read(ROOT/'AUTHENTICATION.json')
 for f in auth['models']:
  st=Path(f['path']).stat();assert st.st_size==f['bytes'] and st.st_mtime_ns==f['mtime_ns']
 unit=ROOT/'units'/name;unit.mkdir(parents=True)
 panel=Path(panel or HISTORY/'freeze/NATIVE_PANEL.json')
 template=read(HISTORY/'run-primary/B1-2.job.json');job={k:v for k,v in template.items() if k not in ('slots','payload_root','runtime_sha256')}
 manifest=ROOT/role/'FILES.json';job.update(slots=slots,payload_root=str(ROOT/'payload'),runtime_sha256=sha(manifest),admit=admit,**(extra or {}))
 requests=0 if admit else len(slots);rows=0 if admit else token_rows if token_rows is not None else sum(2*(s['prompt_tokens']+2*s['cap']) for s in slots)
 ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.reserve(name,dict(requests=requests,token_rows=rows,operators=0));ledger.close()
 write(unit/'JOB.json',job);write(unit/'RESERVATION.json',dict(requests=requests,token_rows=rows,operators=0,utc=utc()))
 exe=ROOT/role/'build/bin/Release/boundary.exe'
 argv=[sys.executable,'-B',str(HERE/'supervisor.py'),'--manifest',str(manifest),'--receipt',str(unit/'SUPERVISOR.json'),'--limit','900','--minimum-free-bytes',str(20*1024**3),str(exe),str(unit/'native'),*[f['path'] for f in auth['models']],str(panel),str(unit/'JOB.json')]
 write(unit/'COMMAND.json',argv);write(LOCK,dict(unit=str(unit),pid=os.getpid(),utc=utc()));start=time.monotonic();status='FAILED';code=None
 try:
  with (unit/'host.log').open('x') as log:code=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=950).returncode
  sup=read(unit/'SUPERVISOR.json');native=read(unit/'native/result.json')
  clean=sup['job_accounting']['active_processes']==0
  expected='ZERO_FORWARD_ADMITTED' if admit else 'WORKER_COMPLETE'
  ok=code==0 and native['status']==expected and clean
  loaded={Path(x['path']).name.lower():x['sha256'] for x in sup['loaded_module_hashes']}
  assert all(loaded.get(Path(x['path']).name.lower())==x['sha256'] for x in read(manifest)['files'] if x['path'].lower().endswith('.dll'))
  status='COMPLETE' if ok else 'FAILED'
  write(unit/'RECEIPT.json',dict(success=ok,status=native['status'],owned_seconds=time.monotonic()-start,cleanup_verified=clean,completed_requests=len(native['requests']),error=native.get('error')))
  return native
 finally:
  ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.finish(name,status,code);ledger.close()
  if (unit/'SUPERVISOR.json').exists() and read(unit/'SUPERVISOR.json').get('job_accounting',{}).get('active_processes')==0:LOCK.unlink(missing_ok=True)
def admission(role):
 assert len(list((ROOT/'units').glob('admit-*')))<10
 s=read(HISTORY/'run-primary/B1-2.job.json')['slots'][2]
 s.update(study_id='tpds_decisive_b570_draft_v1',draft_caller=1 if role=='R' else int(role[1]),draft_ubatch=1 if role=='R' else int(role[3]),target_ub=1 if role=='R' else 4)
 n=run('admit-'+role,role,[s],admit=True);print(role,n['status'],n.get('error'),flush=True)
if __name__=='__main__':
 cmd=sys.argv[1]
 if cmd=='setup':setup()
 elif cmd=='build':build(sys.argv[2])
 elif cmd=='admit':admission(sys.argv[2])
