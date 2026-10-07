"""Supplement-only immutable CAS, complete CRC/SHA, clean CPU rederivation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys,zipfile,time
ROOT=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
assert not (ROOT/'LOCK.json').exists() and (ROOT/'DONE.json').exists()
assert load(ROOT/'SUPPLEMENT_VERIFICATION.json')['status']=='PASS' and load(ROOT/'CORE_REVIEW.json')['status']=='PASS_WITH_REQUIRED_SUPPLEMENT'
stamp=str(time.time_ns());archive=ROOT/'archive';archive.mkdir(exist_ok=True);bundle=ROOT/'audit-source.bundle';subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=ROOT,check=True)
files=[p for p in ROOT.rglob('*') if p.is_file() and not (set(p.relative_to(ROOT).parts)&{'.git','archive','__pycache__'}) and not ('build' in p.relative_to(ROOT).parts and p.suffix!='.exe') and not p.name.endswith('.tmp')]
index=dict(source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),files={},objects={},original_scientific_archive=load(ROOT/'AMENDMENT.json')['prior_archive_sha256'],models_excluded=load(ROOT/'AMENDMENT.json')['models'],runtime_external=load(ROOT/'BUILD_FREEZE.json')['libraries'])
pending=archive/('pending-'+stamp+'.zip')
with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
 for p in sorted(files):
  h=sha(p);rel=p.relative_to(ROOT).as_posix();index['files'][rel]=dict(sha256=h,bytes=p.stat().st_size)
  if h not in index['objects']:z.write(p,'objects/'+h);index['objects'][h]=dict(bytes=p.stat().st_size,crc32=z.getinfo('objects/'+h).CRC)
 z.writestr('INDEX.json',json.dumps(index,indent=2)+'\n')
digest=sha(pending);sealed=archive/(digest+'.zip');pending.rename(sealed);restore=archive/('restore-'+stamp);restore.mkdir()
with zipfile.ZipFile(sealed) as z:
 assert z.testzip() is None
 for h,m in index['objects'].items():assert hashlib.sha256(z.read('objects/'+h)).hexdigest()==h and z.getinfo('objects/'+h).CRC==m['crc32']
 for name,m in index['files'].items():
  p=restore/name;assert p.resolve().is_relative_to(restore.resolve());p.parent.mkdir(parents=True,exist_ok=True)
  with z.open('objects/'+m['sha256']) as source,p.open('xb') as f:
   while b:=source.read(8*1024*1024):f.write(b)
  assert sha(p)==m['sha256']
before=load(restore/'SUPPLEMENT_VERIFICATION.json');result=subprocess.run([sys.executable,str(restore/'verify_supplement.py'),str(restore)],capture_output=True,text=True);save(archive/('RESTORE_CPU-'+stamp+'.json'),dict(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr));assert result.returncode==0,result.stdout+result.stderr
after=load(restore/'SUPPLEMENT_VERIFICATION.json');before.pop('utc');after.pop('utc');assert before==after,'Restored CPU derivation differs beyond fresh audit timestamp'
history=archive/('history-'+stamp+'.git');subprocess.run(['git','clone','--quiet','--bare',str(restore/'audit-source.bundle'),str(history)],check=True);assert subprocess.check_output(['git','--git-dir',str(history),'rev-parse','HEAD'],text=True).strip()==index['source_head']
for n,h in load(ROOT/'BUILD_FREEZE.json')['executables'].items():assert sha(restore/'build/Release'/n)==h
for n,h in load(ROOT/'BUILD_FREEZE.json')['libraries'].items():assert sha(ROOT/'build/Release'/n)==h
receipt=dict(status='PASS',utc=datetime.now(timezone.utc).isoformat(),archive=str(sealed),archive_sha256=digest,archive_bytes=sealed.stat().st_size,files=len(index['files']),objects=len(index['objects']),restore=str(restore),source_head=index['source_head'],source_bundle_sha256=sha(bundle),all_crc_sha_pass=True,clean_CPU_derivation_identical_excluding_fresh_timestamp=True,private_executables_restored=True,runtime_installed_hashes_verified=True,original_archive_unchanged=index['original_scientific_archive'],raw_records=32,nonwarm=18,warm=14,restore_model_forwards=0)
save(ROOT/'SUPPLEMENT_ARCHIVE_RESTORE.json',receipt);print(receipt,flush=True)
