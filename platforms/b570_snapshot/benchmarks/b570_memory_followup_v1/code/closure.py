"""Full content-addressed evidence closure and actual fresh CPU restoration."""
import hashlib,json,zipfile,shutil,sys,subprocess,time
from pathlib import Path
R=Path('C:/hs/b570-mem-run-v1');REPO=Path('C:/hs/b570-mem-v1');PUBLIC=REPO/'benchmarks/b570_memory_followup_v1';ART=REPO/'artifacts/b570_memory_followup_v1'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def seal():
 report=load(R/'INDEPENDENT_VERIFICATION.json');assert report['status'].startswith('PASS_') and report['raw_completed']==550
 files={};objects={};omit={'CAS_INDEX.json','LOCAL_RESTORE.json','REMOTE_READBACK.json','REMOTE_RESTORE.json','FINAL_DELIVERY.json','f0a-transport.zip'}
 for p in sorted(R.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(R)
  if rel.parts[0] in {'models','archive'} or '__pycache__' in rel.parts or p.name in omit:continue
  if rel.parts[0]=='build' and not (p.parent.name=='Release' and p.suffix in {'.exe','.dll','.lib'}):continue
  if p.suffix in {'.pdb','.obj','.ilk','.exp'}:continue
  h=sha(p);files[rel.as_posix()]=dict(sha256=h,bytes=p.stat().st_size);objects.setdefault(h,p)
 assert set(load(R/'F0A.json')['files']).issubset(files),'All frozen source, binary, vocabulary and dependency files recoverable'
 index=dict(schema='heterospec.b570.memory.followup.cas.v1',files=files,objects={h:dict(bytes=p.stat().st_size) for h,p in objects.items()},external_models=load(R/'ASSET_CHECKS.json')['models'],F0A_actual_remote_head=report['F0A_actual_remote_head'],formal_requests=0)
 a=R/'archive';a.mkdir(exist_ok=True);temp=a/'seal.zip'
 with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
  for h,p in objects.items():z.write(p,'objects/'+h)
  z.writestr('INDEX.json',json.dumps(index,sort_keys=True).encode())
 h=sha(temp);archive=temp.with_name(h+'.zip');temp.rename(archive);parts=[];(ART/'parts').mkdir(parents=True,exist_ok=True)
 with archive.open('rb') as f:
  while b:=f.read(48*1024*1024):
   ph=hashlib.sha256(b).hexdigest();p=ART/'parts'/(ph+'.part');p.write_bytes(b);parts.append(dict(index=len(parts),sha256=ph,bytes=len(b),repo_path=p.relative_to(REPO).as_posix()))
 receipt=dict(schema=index['schema'],archive_sha256=h,archive_bytes=archive.stat().st_size,files=len(files),objects=len(objects),parts=parts,external_dependencies='Four full GGUF files remain hash-bound external dependencies; each independently rehashed in every fresh CPU restoration. Full private core, tokenizer, native actor versions, source blobs, DLLs, vocabulary, paid raw requests/probes and negative evidence included.',formal_requests=0)
 save(R/'CAS_INDEX.json',receipt);save(PUBLIC/'CAS_INDEX.json',receipt);(ART/'parts/.gitattributes').write_text('*.part -text\n',encoding='utf8');print('SEALED',receipt['archive_bytes'],len(files),len(objects),len(parts),flush=True)
def restore(checkout,dest,receipt_path):
 checkout=Path(checkout);dest=Path(dest);dest.mkdir(parents=True,exist_ok=False);meta=load(checkout/'benchmarks/b570_memory_followup_v1/CAS_INDEX.json');archive=dest/'transport.zip'
 with archive.open('wb') as out:
  for part in meta['parts']:
   p=checkout/part['repo_path'];assert p.stat().st_size==part['bytes'] and sha(p)==part['sha256'];shutil.copyfileobj(p.open('rb'),out,8*1024*1024)
 assert archive.stat().st_size==meta['archive_bytes'] and sha(archive)==meta['archive_sha256']
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None;index=json.loads(z.read('INDEX.json'))
  for h,m in index['objects'].items():b=z.read('objects/'+h);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==h
  for name,m in index['files'].items():
   p=dest/name;assert p.resolve().is_relative_to(dest.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read('objects/'+m['sha256']));assert sha(p)==m['sha256']
 expected=load(dest/'INDEPENDENT_VERIFICATION.json');proc=subprocess.run([sys.executable,str(dest/'code/independent_verify.py'),str(dest)],capture_output=True,text=True,encoding='utf8');assert proc.returncode==0,proc.stderr
 assert load(dest/'INDEPENDENT_VERIFICATION.json')==expected,'Independent semantic rederivation changed evidence'
 save(receipt_path,dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),source_checkout=str(checkout),fresh_restore=str(dest),archive_sha256=meta['archive_sha256'],files=len(index['files']),objects=len(index['objects']),parts=len(meta['parts']),complete_crc_sha_objects_logical_files_verified=True,independent_CPU_rederivation_identical=True,independent_checks=expected['checks'],raw_completed=expected['raw_completed'],external_models_rehashed=len(expected['independently_rehashed_assets']),frozen_source_binary_dependency_files_verified=expected['F0A_native_source_binary_bytes'],stdout=proc.stdout,formal_requests=0));print('ACTUAL FRESH RESTORE PASS',len(index['files']),expected['checks'],flush=True)
if __name__=='__main__':
 if sys.argv[1]=='seal':seal()
 else:restore(sys.argv[2],sys.argv[3],sys.argv[4])
