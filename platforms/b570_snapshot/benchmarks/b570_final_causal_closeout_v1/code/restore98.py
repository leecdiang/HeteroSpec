"""CPU-only strict fresh CAS restoration. No native model execution."""
import argparse,json,zipfile,hashlib
from pathlib import Path
def restore(cas,dest):
 assert not dest.exists(),'fresh destination required'
 dest.mkdir(parents=True)
 with zipfile.ZipFile(cas) as z:
  assert z.testzip() is None
  m=json.loads(z.read('MANIFEST.json'));assert len(m['files'])==m['logical_files'] and len({r['path'] for r in m['files']})==m['logical_files']
  assert len({r['sha256'] for r in m['files']})==m['unique_objects']
  assert set(z.namelist())=={'MANIFEST.json'}|{'objects/'+r['sha256'] for r in m['files']}
  for r in m['files']:
   data=z.read('objects/'+r['sha256']);assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
   p=dest/r['path'];assert p.resolve().is_relative_to(dest.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  (dest/'RESTORE_MANIFEST.json').write_bytes(z.read('MANIFEST.json'))
 print(json.dumps(dict(status='PASS_FRESH_FULL_BYTE_RESTORE',files=m['logical_files'],objects=m['unique_objects'])))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cas',required=True);p.add_argument('--dest',required=True);a=p.parse_args();restore(Path(a.cas),Path(a.dest))
