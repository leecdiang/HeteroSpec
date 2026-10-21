"""CPU-only integrity of inherited complete PR97/PR92 capsule, no model runs."""
import json,hashlib,zipfile,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'baseline/HISTORICAL_PR97_COMPLETE_CAS.zip'
with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
assert h=='816b802f915373c861e754bba448048705ce790ee8a230e114fef8197079a530'
assert p.stat().st_size==84848226
with zipfile.ZipFile(p) as z:
 b=z.read('MANIFEST.json');assert hashlib.sha256(b).hexdigest()=='55b5c3094017cc0d5689ed55f4270b209465d1337337f6128c2b32fd7be6b6c6'
 m=json.loads(b)
 for r in m['files']:
  x=z.read('objects/'+r['sha256']);assert len(x)==r['bytes'] and hashlib.sha256(x).hexdigest()==r['sha256']
receipt=dict(status='PASS_FULL_HISTORICAL_CAPSULE_CRC_AND_EVERY_LOGICAL_OBJECT',bytes=p.stat().st_size,sha256=h,logical_files=len(m['files']),unique_objects=len({r['sha256'] for r in m['files']}),scope='Complete inherited PR97 and embedded PR92/93 audits and all original paid raw evidence retained byte-for-byte. Integrity verification; historical conclusions remain inherited audited conclusions, not new performance experiments.',new_model_forwards=0)
(R/'HISTORICAL_CAPSULE.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt))
