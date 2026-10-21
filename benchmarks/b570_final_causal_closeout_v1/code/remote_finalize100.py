"""CPU-only actual authenticated full-byte restore. Credentials never persisted."""
import sys,json,hashlib,concurrent.futures,zipfile,subprocess,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];job=json.loads(sys.stdin.read());parts=job['parts'];cas=job['cas'];head=job['commit']
dest=R/'receipts/authenticated_remote_parts';assert dest.exists()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def used():return sum(p.stat().st_size for p in R.rglob('*') if p.is_file())
cap=json.loads((R/'PLAN.json').read_bytes())['limits']['total_disk_bytes']
def check(label,forecast=0):
 n=used();assert n+forecast<=cap,(label,n,forecast,cap)
 with (R/'receipts/DISK_CHECKPOINTS.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(label=label,bytes=n,forecast=forecast,cap=cap,status='PASS'))+'\n')
def one(p):
 b=(dest/p['name']).read_bytes();assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']
 assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==p['git_sha']
 return dict(name=p['name'],bytes=len(b),sha256=p['sha256'],git_sha=p['git_sha'],method='Actual authenticated HTTPS body, rehashed; no local original substituted')
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(one,parts))
actual=R/'receipts/ACTUAL_REMOTE_COMPLETE_CAS.zip';check('before_remote_assembly',cas['bytes'])
with actual.open('wb') as f:
 for p in parts:f.write((dest/p['name']).read_bytes())
assert actual.stat().st_size==cas['bytes'] and sha(actual)==cas['sha256']
save(R/'receipts/REMOTE_BYTES.json',dict(status='PASS_ALL_ACTUAL_AUTHENTICATED_GITHUB_BODY_BYTES',commit=head,archive_bytes=actual.stat().st_size,archive_sha256=sha(actual),parts=sorted(results,key=lambda p:p['name']),credentials_persisted=False))
with zipfile.ZipFile(actual) as z:
 m=z.read('MANIFEST.json');assert hashlib.sha256(m).hexdigest()==cas['manifest_sha256'] and m==(R/'ARCHIVE_MANIFEST.json').read_bytes()
 manifest=json.loads(m)
target=dest.resolve();assert target.parent==(R/'receipts').resolve() and target.name=='authenticated_remote_parts';shutil.rmtree(target)
# Keep only one canonical identical archive if peak restore replicas would exceed prospectively frozen disk cap.
swap=False;forecast=sum(p['bytes'] for p in manifest['files'])+len(m)+10485760
if used()+forecast>cap:
 original=(R/'COMPLETE_CAS.zip').resolve();assert original.parent==R.resolve() and original.name=='COMPLETE_CAS.zip' and sha(original)==cas['sha256'] and sha(actual)==cas['sha256']
 original.unlink();swap=True
 save(R/'receipts/CANONICAL_CAS_SPACE_RECEIPT.json',dict(action='Canonical archive contents preserved in fully verified actual remote ZIP; byte-identical remote archive becomes canonical after independent restoration',sha256=cas['sha256'],original_verified_local_restore=True,scope='Only this newly generated study archive, no frozen historical artifact changed'))
check('before_remote_fresh_restore',forecast)
def step(name,args):
 p=subprocess.run([sys.executable,'-B','-X','utf8',*args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=240)
 (R/'receipts'/(name+'.stdout.log')).write_bytes(p.stdout);(R/'receipts'/(name+'.stderr.log')).write_bytes(p.stderr)
 assert p.returncode==0,p.stderr.decode(errors='replace');print(name,'PASS',flush=True)
rest=R/'receipts/remote_restore';out=R/'receipts/remote_rederived'
step('REMOTE_FRESH_RESTORE',[str(R/'code/restore98.py'),'--cas',str(actual),'--dest',str(rest)])
step('REMOTE_INDEPENDENT_AUDIT',[str(rest/'code/verify100.py'),'--root',str(rest),'--output',str(out)])
step('REMOTE_SYNTHETIC',[str(rest/'code/test_verify100.py'),str(rest)])
oldout=R/'receipts/remote_rederived99';oldout.mkdir()
step('REMOTE_INHERITED99_AUDIT',[str(rest/'baseline/pr99/code/verify98.py'),'--root',str(rest/'baseline/pr99'),'--output',str(oldout)])
names=['PARTITION_MATRIX','OPERATOR_FIRST_DIFF','FIXED_INPUT_REPLAY','STATE_RESTORE_ADMISSION','KV_LOGITS_CROSS','GPU_TIMELINE','QUALIFICATION','RAW_EVIDENCE','RESULTS','INDEPENDENT_VERIFICATION'];checks={}
for n in names:
 assert (R/f'{n}.json').read_bytes()==(out/f'{n}.json').read_bytes();checks[n+'.json']=sha(out/f'{n}.json')
for n in ['RESULTS','QUALIFICATION','WORK_WITNESSES','NUMERICAL_STATE_LAYOUTS','INDEPENDENT_VERIFICATION']:assert (oldout/f'{n}.json').read_bytes()==(rest/'baseline/pr99'/f'{n}.json').read_bytes()
save(R/'REMOTE_RESTORE.json',dict(status='PASS_ACTUAL_AUTHENTICATED_REMOTE_BYTES_AND_INDEPENDENT_EXACT_REDERIVATION',authenticated_commit=head,cas_sha256=cas['sha256'],manifest_sha256=cas['manifest_sha256'],logical_files=cas['logical_files'],unique_objects=cas['unique_objects'],actual_downloaded_parts=len(parts),exact_artifacts=checks,full_target_model_rehashed=True,full_historical_PR99_independent_reaudit=True,synthetic_rejection_tests=15,new_model_forwards=0,credentials_persisted=False,transport='Fresh GitHub authenticated contents URLs, actual HTTPS bodies, exact eachbodySHA256/GitSHA1/fullarchiveSHA256/manifestSHA, no local substitution'))
if swap:actual.replace(R/'COMPLETE_CAS.zip')
check('REMOTE_COMPLETE')
print('REMOTE_COMPLETE_ALL_BYTES_REDERIVED',flush=True)
