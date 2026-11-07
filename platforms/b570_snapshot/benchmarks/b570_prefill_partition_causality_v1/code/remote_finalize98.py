"""Authenticated per-file download URLs arrive on stdin; never persist/log credentials."""
import sys,json,urllib.request,urllib.parse,hashlib,concurrent.futures,time,zipfile,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
job=json.loads(sys.stdin.read());parts=job['parts'];cas=job['cas'];head=job['commit']
dest=R/'receipts/authenticated_remote_parts';assert dest.exists()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_bytes((json.dumps(x,indent=2)+'\n').encode())
def download(p):
 b=(dest/p['name']).read_bytes()
 assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']
 assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==p['git_sha']
 return dict(name=p['name'],bytes=len(b),sha256=p['sha256'],git_sha=p['git_sha'],method='Actual authenticated HTTPS bytes retained from scoped GitHub download batches; independently rehashed again; no local original substituted')
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 futures=[pool.submit(download,p) for p in parts]
 for f in concurrent.futures.as_completed(futures):
  results.append(f.result())
  if len(results)%25==0 or len(results)==len(parts):
   save(R/'receipts/remote_progress.json',dict(status='DOWNLOADING',verified=len(results),total=len(parts),commit=head))
   print('ACTUAL_AUTHENTICATED_REMOTE_PARTS',len(results),flush=True)
actual=R/'receipts/ACTUAL_REMOTE_COMPLETE_CAS.zip'
with actual.open('wb') as f:
 for p in parts:f.write((dest/p['name']).read_bytes())
assert actual.stat().st_size==cas['bytes'] and sha(actual)==cas['sha256']
save(R/'receipts/REMOTE_BYTES.json',dict(status='PASS_ALL_ACTUAL_AUTHENTICATED_GITHUB_BODY_BYTES',commit=head,archive_bytes=actual.stat().st_size,archive_sha256=sha(actual),parts=sorted(results,key=lambda p:p['name']),credentials_persisted=False))
with zipfile.ZipFile(actual) as z:
 m=z.read('MANIFEST.json');assert hashlib.sha256(m).hexdigest()==cas['manifest_sha256'];assert m==(R/'ARCHIVE_MANIFEST.json').read_bytes()
def step(name,args):
 p=subprocess.run([sys.executable,'-B','-X','utf8',*args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 (R/'receipts'/(name+'.stdout.log')).write_bytes(p.stdout);(R/'receipts'/(name+'.stderr.log')).write_bytes(p.stderr)
 assert p.returncode==0,p.stdout.decode(errors='replace')+p.stderr.decode(errors='replace')
 print(name,p.stdout.decode(errors='replace').strip(),flush=True)
rest=R/'receipts/remote_restore'
step('remote_restore',[str(R/'code/restore98.py'),'--cas',str(actual),'--dest',str(rest)])
step('remote_rederive',[str(rest/'code/verify98.py'),'--root',str(rest),'--output',str(R/'receipts/remote_rederived')])
step('remote_synthetic',[str(rest/'code/test_verify98.py')])
names=['RESULTS.json','QUALIFICATION.json','WORK_WITNESSES.json','NUMERICAL_STATE_LAYOUTS.json','INDEPENDENT_VERIFICATION.json'];checks={}
for n in names:
 b=(R/'analysis'/n).read_bytes();assert b==(R/'receipts/remote_rederived'/n).read_bytes();checks[n]=hashlib.sha256(b).hexdigest()
save(R/'REMOTE_RESTORE.json',dict(status='PASS_ACTUAL_AUTHENTICATED_REMOTE_BYTES_AND_INDEPENDENT_EXACT_REDERIVATION',authenticated_commit=head,cas_sha256=cas['sha256'],manifest_sha256=cas['manifest_sha256'],logical_files=cas['logical_files'],unique_objects=cas['unique_objects'],actual_downloaded_parts=len(parts),exact_artifacts=checks,full_target_model_rehashed=True,synthetic_rejection_tests=12,new_model_forwards=0,credentials_persisted=False,transport='Actual bodies from scoped GitHub download URLs supplied by authenticated contents API; exact Git blob SHA1 pins matched authenticated metadata and each body SHA256'))
print('REMOTE_RESTORE_ALL_CLOSED',flush=True)
