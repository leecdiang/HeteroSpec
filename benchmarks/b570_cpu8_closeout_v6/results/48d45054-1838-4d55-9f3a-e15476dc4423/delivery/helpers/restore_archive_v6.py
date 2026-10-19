"""Restore downloaded stopped-delivery archive, verify all members and original seal. No child/native loads."""
import sys,json,hashlib,tarfile,os
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
archive=BASE/'remote-tail-download-01/TAIL_EVIDENCE.tar.xz'
expected='0c8f6b888fb45d97441f05f5f1f11826996fc5c86db35331601e47b3511d3450'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
need(sha(archive)==expected,'downloaded tail identity')
dest=BASE/'remote-tail-restored-01';need(not dest.exists(),'new restore root')
with tarfile.open(archive,'r:xz') as t:
 members=t.getmembers();names=[m.name for m in members]
 need(len(names)==len(set(names)),'duplicate member')
 manifest=json.loads(t.extractfile('TAIL_MANIFEST.json').read());wanted={r['path']:r for r in manifest['files']}
 need(set(names)==set(wanted)|{'TAIL_MANIFEST.json'},'exact tail membership')
 dest.mkdir()
 for info in members:
  n=info.name;p=Path(n)
  need(info.isfile() and not p.is_absolute() and '..' not in p.parts and ':' not in n and '\\' not in n,'tail path/type')
  b=t.extractfile(info).read()
  if n in wanted:need(len(b)==wanted[n]['bytes'] and hashlib.sha256(b).hexdigest()==wanted[n]['sha256'],'tail member hash')
  out=dest/p;out.parent.mkdir(parents=True,exist_ok=True)
  with out.open('xb') as f:f.write(b)
original=Path('C:/hs/b570-capability-v1/48d45054-1838-4d55-9f3a-e15476dc4423')
name='delivery/EVIDENCE_MANIFEST.json';m=json.loads((original/name).read_bytes());actual=set()
for parent,dirs,files in os.walk(original,followlinks=False):
 for n in dirs+files:
  p=Path(parent,n);need(not p.is_symlink() and not p.is_junction(),'original alias')
 for n in files:actual.add((Path(parent,n)).relative_to(original).as_posix())
need(actual=={r['path'] for r in m['files']}|{name},'original member set changed')
for r in m['files']:need((original/r['path']).stat().st_size==r['bytes'] and sha(original/r['path'])==r['sha256'],'original seal drift')
report=dict(status='RECONSTRUCTION_ONLY_TAIL_BYTES_RESTORED',archive_sha256=expected,tail_members=len(names),manifest_sha256=sha(dest/'TAIL_MANIFEST.json'),original_seal_sha256=sha(original/name),original_members=len(actual),original_seal_unchanged=True,qualification='ENGINEERING_BLOCKED; no live admission')
with (BASE/'TAIL_RESTORE_RECEIPT.json').open('x',encoding='utf8',newline='\n') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(report,sort_keys=True))
