"""Content addressed closure and actual fresh restoration; no generation launch."""
import json,hashlib,zipfile,shutil,subprocess,sys,time
from pathlib import Path
R=Path('C:/hs/jsa-b570-run-v1');REPO=Path('C:/hs/jsa-b570-v1');PUBLIC=REPO/'benchmarks/jsa_b570_validation_v1';ART=REPO/'artifacts/jsa_b570_validation_v1'
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def prepare_sources():
 shutil.copytree(Path('C:/hs/b570-closeout-v1/src'),R/'source/pr63-original-front',dirs_exist_ok=True)
 shutil.copyfile(PUBLIC/'code/closeout.py',R/'cpu-closeout.py')
 shutil.copyfile(PUBLIC/'code/verify_states.py',R/'cpu-states.py')
 sources={p.relative_to(R).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in (R/'source/pr63-original-front').rglob('*') if p.is_file()}
 sources['cpu-closeout.py']=dict(sha256=sha(R/'cpu-closeout.py'),bytes=(R/'cpu-closeout.py').stat().st_size)
 sources['cpu-states.py']=dict(sha256=sha(R/'cpu-states.py'),bytes=(R/'cpu-states.py').stat().st_size)
 save(R/'CPU_CLOSEOUT_SOURCE_BINDINGS.json',dict(scope='CPU closeout/provenance only, frozen generation binaries and F0 unchanged',sources=sources))
def seal():
 assert not (R/'LOCK.json').exists();assert all((p.parent/'SESSION_CLOSE.json').exists() for p in (R/'sessions').glob('*/SESSION.json'))
 prepare_sources();files={};objects={};exclude={'dependencies','models','archive','restores','python-deps','__pycache__','transport'}
 for p in sorted(R.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(R)
  if rel.parts[0] in exclude or '__pycache__' in rel.parts or p.name in ['STOP','LOCK.json','CAS_INDEX.json','LOCAL_CAS_RESTORE.json','REMOTE_READBACK.json','FINAL_DELIVERY.json']:continue
  if p.name.endswith('.tmp') or p.suffix=='.download':continue
  if rel.parts[0]=='tokenizer-build' and not(p.suffix in ['.exe','.dll'] and p.parent.name=='Release'):continue
  h=sha(p);files[rel.as_posix()]=dict(sha256=h,bytes=p.stat().st_size);objects.setdefault(h,p)
 index=dict(schema='heterospec.jsa.b570.cas.v1',files=files,objects={h:dict(bytes=p.stat().st_size) for h,p in objects.items()},external_models=load(R/'MODEL_CHOICE.json')['models'],external_original_models=load(R/'QWEN_MODELS.json')['models'],legacy_cas_dependency=load(R/'LEGACY_RESTORE.json')['archive'],forward_calls_during_seal=0)
 archive=R/'archive';archive.mkdir(exist_ok=True);tmp=archive/('temp-'+str(time.time_ns())+'.zip')
 with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
  for i,(h,p) in enumerate(objects.items()):
   z.write(p,'objects/'+h)
   if i%300==0:print('CAS',i,'/',len(objects),flush=True)
  z.writestr('INDEX.json',json.dumps(index,sort_keys=True).encode())
 digest=sha(tmp);a=tmp.with_name(digest+'.zip');tmp.rename(a);parts=[];(ART/'parts').mkdir(parents=True,exist_ok=True)
 with a.open('rb') as f:
  for n in range(1000):
   b=f.read(48*1024*1024)
   if not b:break
   h=hashlib.sha256(b).hexdigest();p=ART/'parts'/(h+'.part');p.write_bytes(b);parts.append(dict(index=n,sha256=h,bytes=len(b),repo_path=p.relative_to(REPO).as_posix()))
 receipt=dict(schema=index['schema'],archive_sha256=digest,archive_bytes=a.stat().st_size,local_archive=str(a),files=len(files),objects=len(objects),parts=parts,external_assets='Exact installed original Qwen/Smol model files remain external hash-bound dependencies; numerical runtime and executable/DLL bytes included in CAS.',legacy_dependency=load(R/'LEGACY_RESTORE.json')['archive'],restore_command='python code/cas.py restore <fresh_checkout> <fresh_restore_root>',new_forwards=0)
 save(R/'CAS_INDEX.json',receipt);save(PUBLIC/'CAS_INDEX.json',receipt);print('SEALED',a.stat().st_size,len(files),len(parts),flush=True)
def restore(checkout,dest,receiptfile=None):
 checkout=Path(checkout);dest=Path(dest);dest.mkdir(parents=True,exist_ok=False);meta=load(checkout/'benchmarks/jsa_b570_validation_v1/CAS_INDEX.json');archive=dest/'transport.zip'
 with archive.open('wb') as out:
  for part in meta['parts']:
   p=checkout/part['repo_path'];assert p.stat().st_size==part['bytes'] and sha(p)==part['sha256'];shutil.copyfileobj(p.open('rb'),out,8*1024*1024)
 assert archive.stat().st_size==meta['archive_bytes'] and sha(archive)==meta['archive_sha256']
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None;index=json.loads(z.read('INDEX.json'))
  for i,(h,m) in enumerate(index['objects'].items()):
   b=z.read('objects/'+h);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==h
   if i%600==0:print('RESTORE objects',i,flush=True)
  for name,m in index['files'].items():
   p=dest/name;assert p.resolve().is_relative_to(dest.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read('objects/'+m['sha256']));assert sha(p)==m['sha256']
 expected={n:load(dest/n) for n in ['A_VERIFICATION.json','B_VERIFICATION.json','D_VERIFICATION.json','INDEPENDENT_VERIFICATION.json','DECISION.json','COUNTS.json','NATURAL_DIAGNOSTIC.json','STATE_FLOAT_VERIFICATION.json']};logs=[]
 for stage in ['A','B','D']:
  result=subprocess.run([sys.executable,str(dest/'code/verify.py'),stage,str(dest)],capture_output=True,text=True,encoding='utf8');logs.append(dict(stage=stage,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0
 result=subprocess.run([sys.executable,str(dest/'cpu-states.py'),str(dest)],capture_output=True,text=True,encoding='utf8');logs.append(dict(stage='states',returncode=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0
 result=subprocess.run([sys.executable,str(dest/'cpu-closeout.py'),'final',str(dest)],capture_output=True,text=True,encoding='utf8');logs.append(dict(stage='closeout',returncode=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0
 for name,x in expected.items():assert load(dest/name)==x,'fresh CPU rederivation changed '+name
 receipt=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_checkout=str(checkout),fresh_restore=str(dest),archive_sha256=meta['archive_sha256'],files=len(index['files']),objects=len(index['objects']),parts=len(meta['parts']),all_crc_sha_logical_files_verified=True,complete_CPU_rederivation_identical=True,logs=logs,new_forwards=0)
 if receiptfile:save(receiptfile,receipt)
 print('RESTORATION PASS',len(index['files']),flush=True);return receipt
if __name__=='__main__':
 if sys.argv[1]=='seal':seal()
 else:restore(sys.argv[2],sys.argv[3],sys.argv[4] if len(sys.argv)>4 else None)
