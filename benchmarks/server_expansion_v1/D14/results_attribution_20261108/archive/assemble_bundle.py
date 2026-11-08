"""Reconstruct the exact sanitized text gzip; never downloads weights/raw captures."""
from pathlib import Path
import argparse,hashlib,json

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--parts',type=Path,default=Path(__file__).parent/'PARTS.json');p.add_argument('--out',type=Path);a=p.parse_args();m=json.loads(a.parts.read_text());base=a.parts.resolve().parent;dest=a.out or base/m['joined_name']
 if dest.exists():
  if dest.stat().st_size==m['joined_bytes'] and sha(dest)==m['joined_sha256']:print('EXACT_EXISTING_BUNDLE_VERIFIED');return
  raise RuntimeError('Existing mismatching output retained; choose a fresh --out')
 with dest.open('xb') as out:
  for r in m['parts']:
   name=Path(r['name'])
   if name.is_absolute() or '..' in name.parts:raise RuntimeError('Unsafe part name')
   b=(base/name).read_bytes()
   if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise RuntimeError('Part changed; partial output retained')
   out.write(b)
 if dest.stat().st_size!=m['joined_bytes'] or sha(dest)!=m['joined_sha256']:raise RuntimeError('Joined mismatch; output retained')
 print('EXACT_SANITIZED_BUNDLE_RECONSTRUCTED',dest.stat().st_size)
if __name__=='__main__':main()
