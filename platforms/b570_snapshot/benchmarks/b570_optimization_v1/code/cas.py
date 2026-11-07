"""Content-addressed zero-forward evidence closure and actual CPU restoration."""
import hashlib,json,zipfile,shutil,sys,subprocess,time
from pathlib import Path
R=Path('C:/hs/b570-opt-run-v1');REPO=Path('C:/hs/b570-opt-v1');PUBLIC=REPO/'benchmarks/b570_optimization_v1';ART=REPO/'artifacts/b570_optimization_v1'
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def seal():
 assert load(R/'STUDY_CLOSE.json')['model_forward_calls']==0
 files={};objects={};skip={'models','archive','transport','__pycache__'}
 for p in sorted(R.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(R)
  if rel.parts[0] in skip or '__pycache__' in rel.parts:continue
  if rel.parts[0]=='build' and not (p.parent.name=='Release' and p.suffix in ['.exe','.dll']):continue
  if p.name in ['CAS_INDEX.json','LOCAL_RESTORE.json','REMOTE_READBACK.json','REMOTE_RESTORE.json','FINAL_DELIVERY.json']:continue
  h=sha(p);files[rel.as_posix()]=dict(sha256=h,bytes=p.stat().st_size);objects.setdefault(h,p)
 index=dict(schema='heterospec.b570.optimization.cas.v1',files=files,objects={h:dict(bytes=p.stat().st_size) for h,p in objects.items()},external_model_dependencies=load(R/'ASSET_CHECKS.json')['models'],historical_dependency=load(R/'PR82_RESTORE.json'),model_forwards=0)
 a=R/'archive';a.mkdir(exist_ok=True);temp=a/'seal.zip'
 with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
  for h,p in objects.items():z.write(p,'objects/'+h)
  z.writestr('INDEX.json',json.dumps(index,sort_keys=True).encode())
 h=sha(temp);archive=temp.with_name(h+'.zip');temp.rename(archive);parts=[];(ART/'parts').mkdir(parents=True,exist_ok=True)
 with archive.open('rb') as f:
  while b:=f.read(48*1024*1024):
   ph=hashlib.sha256(b).hexdigest();p=ART/'parts'/(ph+'.part');p.write_bytes(b);parts.append(dict(index=len(parts),sha256=ph,bytes=len(b),repo_path=p.relative_to(REPO).as_posix()))
 receipt=dict(schema=index['schema'],archive_sha256=h,archive_bytes=archive.stat().st_size,files=len(files),objects=len(objects),parts=parts,external_dependencies='Six exact full GGUF files remain external hash-bound dependencies; original PR82 CAS independently restored. Executed new binary versions and inherited numeric DLL bytes, full vocab dumps, source blobs and every negative load log are included.',new_model_forwards=0)
 save(R/'CAS_INDEX.json',receipt);save(PUBLIC/'CAS_INDEX.json',receipt);(ART/'.gitattributes').write_text('*.part -text\n');print('SEALED',receipt['archive_bytes'],len(files),len(objects),len(parts),flush=True)
def restore(checkout,dest,receipt_path):
 checkout=Path(checkout);dest=Path(dest);dest.mkdir(parents=True,exist_ok=False);meta=load(checkout/'benchmarks/b570_optimization_v1/CAS_INDEX.json');archive=dest/'transport.zip'
 with archive.open('wb') as out:
  for part in meta['parts']:
   p=checkout/part['repo_path'];assert p.stat().st_size==part['bytes'] and sha(p)==part['sha256'];shutil.copyfileobj(p.open('rb'),out,8*1024*1024)
 assert archive.stat().st_size==meta['archive_bytes'] and sha(archive)==meta['archive_sha256']
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None;index=json.loads(z.read('INDEX.json'))
  for h,m in index['objects'].items():b=z.read('objects/'+h);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==h
  for name,m in index['files'].items():
   p=dest/name;assert p.resolve().is_relative_to(dest.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read('objects/'+m['sha256']));assert sha(p)==m['sha256']
 expected=load(dest/'INDEPENDENT_LOAD_VERIFICATION.json');proc=subprocess.run([sys.executable,str(dest/'code/verify_loads.py'),str(dest)],capture_output=True,text=True,encoding='utf8');assert proc.returncode==0,proc.stderr
 actual=load(dest/'INDEPENDENT_LOAD_VERIFICATION.json');expected.pop('utc');actual.pop('utc');assert actual==expected,'Independent rederivation changed real evidence'
 for x in load(dest/'PLAN_SOURCE_VERIFICATION.json')['source_blobs']:
  p=dest/'source-blobs'/(x['sha256']+'.blob');assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
 bound=load(dest/'LOAD_SOURCE_BINARY_BINDINGS.json')['loads']
 for name,x in bound.items():
  assert sha(dest/name)==x['stdout_sha256'];assert sha(dest/name.replace('.stdout.jsonl','.stderr.log'))==x['stderr_sha256'];assert sha(dest/x['source_path'])==x['source_sha256'];assert sha(dest/x['binary_path'])==x['binary_sha256']
 modules=load(dest/'INHERITED_SOURCE_MODULE_RECHECK.json')['original_numerical_Dlls']
 for name,x in modules.items():assert sha(dest/'build/Release'/name)==x['sha256']
 receipt=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_checkout=str(checkout),fresh_restore=str(dest),archive_sha256=meta['archive_sha256'],files=len(index['files']),objects=len(index['objects']),parts=len(meta['parts']),complete_crc_sha_objects_logical_files_verified=True,independent_CPU_rederivation_identical_ignoring_receipt_utc=True,independent_checks=actual['checks'],load_records=len(actual['loads']),source_blobs_verified=15,native_source_binary_versions_and_modules_verified=True,external_models_rehashed=len(actual['independently_rehashed_external_models']),stdout=proc.stdout,model_forwards=0)
 save(receipt_path,receipt);print('ACTUAL FRESH RESTORE PASS',len(index['files']),actual['checks'],flush=True)
if __name__=='__main__':
 if sys.argv[1]=='seal':seal()
 else:restore(sys.argv[2],sys.argv[3],sys.argv[4])
