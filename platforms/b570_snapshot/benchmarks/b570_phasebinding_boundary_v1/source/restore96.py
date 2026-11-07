"""Independent stdlib archive restoration; refuses existing targets and invalid objects."""
import argparse,hashlib,json,pathlib,zipfile
def h(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def restore(a,mfile,d,expected):
 assert not d.exists(),'restore destination must be fresh'
 assert h(a)==expected,'archive SHA256'
 mb=mfile.read_bytes();m=json.loads(mb);rows=m['files'];assert len(rows)==m['logical_files']
 paths=[x['path'] for x in rows];assert len(paths)==len(set(paths));assert len(set(paths))==len({p.casefold() for p in paths})
 hashes={x['sha256'] for x in rows};assert len(hashes)==m['unique_objects']
 with zipfile.ZipFile(a) as z:
  assert z.testzip() is None
  assert len(z.namelist())==len(set(z.namelist())) and set(z.namelist())=={'MANIFEST.json'}|{'objects/'+v for v in hashes}
  assert z.read('MANIFEST.json')==mb,'exact canonical manifest bytes'
  sizes={}
  for s in hashes:
   b=z.read('objects/'+s);assert hashlib.sha256(b).hexdigest()==s;sizes[s]=len(b)
  d.mkdir(parents=True)
  for r in rows:
   p=pathlib.PurePosixPath(r['path']);assert not p.is_absolute() and '..' not in p.parts and '\\' not in r['path'] and ':' not in r['path']
   assert sizes[r['sha256']]==r['bytes'];o=d/p;assert o.resolve().is_relative_to(d.resolve())
   o.parent.mkdir(parents=True,exist_ok=True);o.write_bytes(z.read('objects/'+r['sha256']))
  for r in rows:assert h(d/r['path'])==r['sha256'] and (d/r['path']).stat().st_size==r['bytes']
 return dict(status='PASS_FRESH_FULL_BYTE_RESTORE',archive_sha256=expected,manifest_sha256=hashlib.sha256(mb).hexdigest(),logical_files=len(rows),unique_objects=len(hashes),destination=str(d),new_model_forwards=0)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--manifest',required=True);p.add_argument('--destination',required=True);p.add_argument('--sha256',required=True);p.add_argument('--receipt',required=True);a=p.parse_args()
 r=restore(pathlib.Path(a.archive),pathlib.Path(a.manifest),pathlib.Path(a.destination),a.sha256);pathlib.Path(a.receipt).write_bytes((json.dumps(r,indent=2)+'\n').encode());print(json.dumps(r))
