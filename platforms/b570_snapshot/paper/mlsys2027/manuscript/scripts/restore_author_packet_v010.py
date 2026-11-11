#!/usr/bin/env python3
"""Reassemble the byte-identical author evidence ZIP from Git-backed parts."""
import hashlib,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];PARTS=HERE/'output/author-evidence-packet-v0.10.0.zip.parts';OUT=HERE/'output/author-evidence-packet-v0.10.0.zip'
def main():
 m=json.loads((PARTS/'MANIFEST.json').read_text());size=0;whole=hashlib.sha256();tmp=OUT.with_suffix('.zip.reassembling')
 with tmp.open('wb') as f:
  for row in m['parts']:
   p=PARTS/row['name'];b=p.read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],p
   f.write(b);whole.update(b);size+=len(b)
 assert size==m['bytes'] and whole.hexdigest()==m['sha256']
 with zipfile.ZipFile(tmp) as z:
  assert z.testzip() is None
  manifest=json.loads(z.read('SHA256SUMS.json'))
  for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 tmp.replace(OUT);print(json.dumps({'status':'PASS','bytes':size,'sha256':whole.hexdigest(),'output':str(OUT)}))
if __name__=='__main__':main()
