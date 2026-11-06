"""Original-host adapter; reuse PR187's supervisor and durable ledger unchanged."""
from pathlib import Path,PureWindowsPath
import datetime,hashlib,json,os,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'b570_decisive_v1'
TOOLKIT=HERE.parent/'tpds_decisive_v1'
ROOT=Path(os.environ.get('HS_ECON_ROOT','I:/HeteroSpec/b570-economics-20261106'))
OLD=Path(os.environ.get('HS_ECON_PR187','E:/HeteroSpec/b570-decisive-recovery-restored-20261105'))
OSMOL=OLD/'secondary-smol'
OLD_CAMPAIGN=OSMOL/'campaign02'
LOCK=Path('C:/hs/b570-llama-exclusive.lock')
LIMITS={'requests':3072,'token_rows':4000000,'operators':2048}
sys.path.insert(0,str(TOOLKIT))
from runner import Ledger
sys.path.insert(0,str(HERE))
from stage_costs import stage
if sys.flags.optimize:raise RuntimeError('Native execution requires assertions enabled')

def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
def command(argv,log):
 started=utc();t=time.monotonic();ok=False
 try:
  with Path(log).open('x',encoding='utf-8') as f:subprocess.run(list(map(str,argv)),stdout=f,stderr=subprocess.STDOUT,check=True)
  ok=True
 finally:write(str(log)+'.cost.json',dict(started_utc=started,finished_utc=utc(),wall_seconds=time.monotonic()-t,success=ok,model_requests=0))
def old_path(value):
 parts=PureWindowsPath(str(value)).parts
 assert 'secondary-smol' in parts
 p=OSMOL.joinpath(*parts[parts.index('secondary-smol')+1:]);assert OSMOL.resolve() in p.resolve().parents
 return p

def bind():
 if (ROOT/'HOST_BINDINGS.json').exists():return read(ROOT/'HOST_BINDINGS.json')
 freeze=read(OLD_CAMPAIGN/'FREEZE.json');published=read(PREVIOUS/'evidence/recovery/SMOL_PUBLISHED_FREEZE.json')
 assert sha(OLD_CAMPAIGN/'FREEZE.json')==published['freeze_sha256']
 auth=read(OSMOL/'AUTHENTICATION.json')
 for m in auth['models']:
  p=Path(m['path']);assert p.stat().st_size==m['bytes'] and p.stat().st_mtime_ns==m['mtime_ns'] and sha(p)==m['sha256']
 original=read(OSMOL/'original-FILES.json');assert sha(OSMOL/'original-FILES.json')==freeze['reference_manifest_sha256']
 actual=[]
 for x in original['files']:
  p=old_path(x['path']);assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'];actual.append(dict(x,path=str(p)))
 write(ROOT/'bindings/original-FILES.json',dict(files=actual,source_manifest_sha256=sha(OSMOL/'original-FILES.json')))
 Ledger(ROOT/'ledger.sqlite',LIMITS).close()
 fixed=[]
 for group,index in [('development',0),('development',2),('test',1),('test',8)]:
  row=read(OSMOL/'cohort/PANEL.json')[group][index];r=read(OSMOL/'cohort/INPUTS.json')[row['id']]
  fixed.append(dict(group=group,index=index,**r))
 write(ROOT/'EXPOSED_INPUTS.json',dict(structural_rule='PR189 fixed dev0/dev2/test1/test8; no outcome selection',inputs=fixed))
 record=dict(base_design_commit='03bc44b6f382919e08a8c1aaa198c2dd723b5c8f',pr187_freeze_sha256=sha(OLD_CAMPAIGN/'FREEZE.json'),pr187_records_sha256=sha(OLD_CAMPAIGN/'RECORDS.json'),models=auth['models'],original_files=actual,supervisor_sha256=sha(PREVIOUS/'supervisor.py'),new_study_limits=LIMITS,old_ledger_not_modified=True,reference_producer_ub=128,reference_outer_batch=512,reference_changed=False)
 write(ROOT/'HOST_BINDINGS.json',record);return record

def build_a1(arm,mode):
 bind();active='target' if arm=='M' else 'native';d=ROOT/'a1-build'/f'{arm}-mode{mode}'
 if (d/'FILES.json').exists():
  for x in read(d/'FILES.json')['files']:assert sha(x['path'])==x['sha256']
  return d
 stage(OLD_CAMPAIGN/arm,ROOT/'bindings'/(arm+'.json'),d,mode,active)
 command(['cmake','-S',d,'-B',d/'build','-G','Visual Studio 17 2022','-A','x64'],d/'configure.log')
 command(['cmake','--build',d/'build','--config','Release','--target','b570-closeout-'+active,'--parallel','4'],d/'compile.log')
 bins=d/'build/Release'
 for x in read(ROOT/'bindings/original-FILES.json')['files']:
  p=Path(x['path'])
  if p.suffix.lower()=='.dll':shutil.copyfile(p,bins/p.name)
 write(d/'FILES.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(bins.iterdir()) if p.suffix.lower() in ('.exe','.dll')]))
 return d

def bind_arm(arm):
 out=ROOT/'bindings'/(arm+'.json')
 if out.exists():return out
 freeze=read(OLD_CAMPAIGN/'FREEZE.json');files={}
 for p in (OLD_CAMPAIGN/arm).iterdir():
  if p.is_file() and p.suffix in ('.cpp','.h','.hpp','.txt'):
   h=freeze['native_source_proofs']['secondary-smol/campaign02/'+arm+'/'+p.name];assert sha(p)==h;files[p.name]=h
 assert {'observer.h','native.cpp','target.cpp','CMakeLists.txt'}<=files.keys()
 write(out,dict(arm=arm,files=files,receipt=dict(path=str(OLD_CAMPAIGN/'FREEZE.json'),sha256=sha(OLD_CAMPAIGN/'FREEZE.json'))));return out

def supervised(name,manifest,argv,cost,stdin_file,environment_file,stream=None):
 bind();assert not LOCK.exists();unit=ROOT/'units'/name;unit.mkdir(parents=True)
 for m in read(ROOT/'HOST_BINDINGS.json')['models']:
  s=Path(m['path']).stat();assert s.st_size==m['bytes'] and s.st_mtime_ns==m['mtime_ns']
 ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.reserve(name,cost);ledger.close()
 write(unit/'RESERVATION.json',dict(**cost,utc=utc()));write(LOCK,dict(pid=os.getpid(),unit=str(unit)))
 sup=PREVIOUS/'supervisor.py'
 if (ROOT/'supervisor02.py').exists():
  sup=ROOT/'supervisor02.py';binding=read(ROOT/'SUPERVISOR_ADAPTER.json');proof=read(ROOT/'SUPERVISOR02_VALIDATION.json')
  assert sha(sup)==binding['adapted_sha256']==proof['adapted_sha256'] and sha(PREVIOUS/'supervisor.py')==binding['base_sha256']
 args=[sys.executable,'-B',str(sup),'--manifest',str(manifest),'--receipt',str(unit/'SUPERVISOR.json'),'--limit','900','--minimum-free-bytes',str(20*1024**3),'--stdin-file',str(stdin_file),'--environment-file',str(environment_file),'--progress-limit','180',*map(str,argv)]
 write(unit/'COMMAND.json',args);started=time.monotonic();status='FAILED';code=None
 try:
  with (unit/'host.log').open('x') as f:code=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=950).returncode
  s=read(unit/'SUPERVISOR.json');assert s['cleanup_verified'] and s['job_accounting']['active_processes']==0 and s['assigned_before_resume']
  status='COMPLETE' if code==0 else 'FAILED';write(unit/'RECEIPT.json',dict(success=code==0,owned_seconds=time.monotonic()-started,cleanup=True))
  return unit,code
 finally:
  ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.finish(name,status,code);ledger.close()
  if (unit/'SUPERVISOR.json').exists() and read(unit/'SUPERVISOR.json').get('cleanup_verified'):LOCK.unlink(missing_ok=True)
  if stream is not None:stream.finish()

if __name__=='__main__':
 if sys.argv[1]=='bind':print(json.dumps(bind(),indent=2))
 elif sys.argv[1]=='build':build_a1(sys.argv[2],int(sys.argv[3]))
 else:
  for arm in ('M','H1','C4U4'):
   for mode in (0,1,2):build_a1(arm,mode);print('NATIVE_FRONTEND_BUILD_PASS',arm,mode,flush=True)
