"""Archive immutable stopped-delivery snapshot, standard library only, no subprocess."""
import sys,json,hashlib,tarfile,lzma
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
SNAP=BASE/'export_snapshot'
M=SNAP/'TAIL_MANIFEST.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads(M.read_bytes())
for row in m['files']:
 p=SNAP/row['path']
 if p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:raise ValueError('tail snapshot drift')
out=BASE/'TAIL_EVIDENCE.tar.xz'
with out.open('xb') as raw:
 with lzma.LZMAFile(raw,'w',preset=6) as compressed:
  with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for row in m['files']:tar.add(SNAP/row['path'],arcname=row['path'],recursive=False)
   tar.add(M,arcname='TAIL_MANIFEST.json',recursive=False)
for row in m['files']:
 if sha(SNAP/row['path'])!=row['sha256']:raise ValueError('tail snapshot changed during compression')
print(json.dumps(dict(status='STOPPED_DELIVERY_SNAPSHOT_ARCHIVED',bytes=out.stat().st_size,sha256=sha(out),members=len(m['files'])+1,manifest_sha256=sha(M)),sort_keys=True))
