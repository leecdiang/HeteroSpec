"""Batched actual Git transport; never starts a native worker or token forward."""
from common import *
import zipfile,shutil
head=git('rev-parse','HEAD').decode().strip();branch=git('branch','--show-current').decode().strip();dest=Path('C:/hs/b570-mem-f0a-readback-v2');assert dest.exists()
assert load(R/'F0A_BATCH_CLONE.json')['returncode']==0
assert git('rev-parse','HEAD',cwd=dest).decode().strip()==head
trees=git('ls-tree','-r',head,'benchmarks/b570_memory_followup_v1','artifacts/b570_memory_followup_v1').decode().splitlines();oids=sorted({line.split()[2] for line in trees});logs=[]
for attempt in range(3):
 p=subprocess.run(['git','-c','fetch.negotiationAlgorithm=noop','fetch','origin','--no-tags','--no-write-fetch-head','--recurse-submodules=no','--filter=blob:none','--stdin'],input=('\n'.join(oids)+'\n').encode(),capture_output=True,cwd=dest)
 logs.append(dict(attempt=attempt,returncode=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace')));save(R/'F0A_BATCH_FETCH.json',logs)
 if p.returncode==0:break
assert p.returncode==0,'Remote transport incomplete; no forward admission'
paths=[line.split('\t')[1] for line in trees];rows=[]
for rel in paths:
 b=git('show',head+':'+rel,cwd=dest);assert b==(REPO/rel).read_bytes()==git('show',head+':'+rel);rows.append(dict(path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
meta=load(PUBLIC/'F0A_TRANSPORT.json');archive=dest/'ACTUAL_REMOTE_F0A.zip'
with archive.open('wb') as out:
 for part in meta['parts']:
  b=git('show',head+':'+part['path'],cwd=dest);assert len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256'];out.write(b)
assert archive.stat().st_size==meta['archive_bytes'] and sha(archive)==meta['archive_sha256']
restore=dest/'ACTUAL_F0A_RESTORED';restore.mkdir()
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None and set(z.namelist())==set(meta['files'])
 for rel,m in meta['files'].items():
  b=z.read(rel);assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'] and b==(R/rel).read_bytes();p=restore/rel;assert p.resolve().is_relative_to(restore.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
save(R/'F0A_REMOTE_READBACK.json',dict(status='PASS',utc=now(),head=head,files=rows,frozen_logical_files_restored=len(meta['files']),all_frozen_bytes_restored_from_actual_remote_Git=True,fresh_remote_repository=str(dest),model_forwards=0,transport_repair='Initial per-blob fetch failed connecting to GitHub. This fresh checkout batches100 blob requests; no scientific rerun.',verifier_sha256=sha(__file__)))
shutil.copyfile(R/'F0A_REMOTE_READBACK.json',PUBLIC/'F0A_REMOTE_READBACK.json');print('ACTUAL F0A remote readback PASS',head,len(rows),len(meta['files']),flush=True)
