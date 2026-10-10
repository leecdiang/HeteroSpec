"""CPU preparation and asset restoration. Never launches generation programs."""
from pathlib import Path
import json,hashlib,zipfile,shutil,subprocess,sys,time,urllib.request,struct
REPO=Path('C:/hs/jsa-b570-v1'); R=Path('C:/hs/jsa-b570-run-v1')
PLAN=REPO/'docs/experiments/jsa_b570_validation_20261010'
OLD=Path('C:/hs/b570-mechanism-pilot-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(n,x):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def restore():
 ix=load(OLD/'ARCHIVE_INDEX.json');a=Path(ix['archive']);assert sha(a)==ix['sha256']
 dest=R/'dependencies/pr64';dest.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(a) as z:
  index=json.loads(z.read('INDEX.json'));assert z.testzip() is None
  for i,(h,d) in enumerate(index['objects'].items()):
   b=z.read('objects/'+h);assert hashlib.sha256(b).hexdigest()==h and len(b)==d['bytes']
   if i%400==0:print('Verified legacy objects',i,flush=True)
  for name,d in index['files'].items():
   p=dest/name;assert p.resolve().is_relative_to(dest.resolve());p.parent.mkdir(parents=True,exist_ok=True)
   if not p.exists():p.write_bytes(z.read('objects/'+d['sha256']))
   assert sha(p)==d['sha256']
 for rel,h in {**load(dest/'B_FREEZE.json')['binaries'],**load(dest/'C_FREEZE.json')['binaries']}.items():
  if rel.endswith('.dll') and not (dest/rel).exists():
   assert sha(OLD/rel)==h;shutil.copyfile(OLD/rel,dest/rel)
 # Direct CPU verifier from the sealed dependency, no import of the new runner.
 p=subprocess.run([sys.executable,str(dest/'independent_verify.py'),str(dest)],cwd=dest,capture_output=True,text=True,encoding='utf8')
 save('LEGACY_CPU_VERIFY_PROCESS.json',dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0
 assert load(dest/'INDEPENDENT_VERIFICATION.json')['status']=='PASS'
 save('LEGACY_RESTORE.json',dict(status='PASS',archive=ix,destination=str(dest),files=len(index['files']),objects=len(index['objects']),full_crc_object_and_logical_sha=True,independent_cpu_verifier='PASS',new_forwards=0))
 bindings={}
 for label,src in [('original',Path('C:/hs/b570-closeout-v1/build/Release')),('candidate',dest/'candidate-build/Release')]:
  dst=R/'bin'/label;dst.mkdir(parents=True,exist_ok=True)
  for p in src.iterdir():
   if p.suffix not in ['.exe','.dll']:continue
   shutil.copyfile(p,dst/p.name);bindings[str((dst/p.name).relative_to(R)).replace('\\','/')]=dict(sha256=sha(p),bytes=p.stat().st_size,source=str(p))
 save('BINARY_BINDINGS.json',bindings)
 for name in ['src','candidate-src','candidate-common','candidate-front']:
  shutil.copytree(dest/name,R/'source'/name,dirs_exist_ok=True)
 # Histories include exact raw arrays, selected mechanically from retained own-path records.
 history={};mapping={'R_reference':'R','ordinary_R':'R','N1_repaired':'N','old_N1':'N','matched_target':'M','matched_bridge':'M','candidate':'C'}
 for p in sorted((dest/'raw').glob('*/RESULT.json')):
  x=load(p);arm=mapping.get(x['config'].get('label'))
  if x['warm'] or not arm or x['config'].get('cap',128)!=128:continue
  task=x['task'];caps=[dest/f for f in x['files'] if f.endswith('/capture.json')]
  if len(caps)!=1:continue
  raw=load(caps[0]);key=task+'/'+arm
  row=dict(ids=raw['ids'],eog=raw['eog'],endpoint=x['endpoint'],source_unit=x['unit_id'],capture_sha256=sha(caps[0]))
  if key in history:assert history[key]['ids']==row['ids'] and history[key]['eog']==row['eog'],key
  else:history[key]=row
 save('HISTORICAL_OWN_PATH.json',history)
 inputs=load(dest/'DEV_INPUTS.json')+load(dest/'E_INPUTS.json');ids=load(PLAN/'DESIGN.json')['stages']['B_second_family_discovery']['tasks']
 pool={x['id']:x for x in inputs};assert all(i in pool for i in ids)
 save('QWEN_INPUTS.json',[pool[i] for i in ids]);print('Restored legacy and bound original/candidate',flush=True)
def download():
 m=load(PLAN/'COORDINATION_SNAPSHOT.json')['model_pair'];out={}
 for role,x in m.items():
  p=R/'models'/Path(x['url'].split('?')[0]).name;p.parent.mkdir(exist_ok=True)
  if not p.exists():
   tmp=p.with_suffix('.download');print('Downloading',role,x['bytes'],flush=True)
   with urllib.request.urlopen(x['url'],timeout=90) as response,tmp.open('wb') as f:
    shutil.copyfileobj(response,f,4*1024*1024)
   assert tmp.stat().st_size==x['bytes'] and sha(tmp)==x['sha256'];tmp.rename(p)
  assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'];out[role]=dict(x,path=str(p))
  print('Model bytes verified',role,flush=True)
 save('MODEL_CHOICE.json',dict(status='EXACT_BYTES_VERIFIED_NO_FORWARD',models=out,selection='PR81 fixed publisher pair, no scientific-output selection',official_conversion_lineage='NOT_CERTIFIED_BY_PUBLISHER',new_forwards=0))
if __name__=='__main__':
 {'restore':restore,'download':download}[sys.argv[1]]()
