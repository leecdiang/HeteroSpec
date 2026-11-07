#!/usr/bin/env python3
"""Package offline raw-evidence audit instructions and preserved notices."""
from pathlib import Path
import json,shutil,zipfile,hashlib,tempfile
p=Path(__file__).resolve().parents[1];a=p/'review_access';out=p/'output/JSA_v0153_raw_archives'
f=out/'ARCHIVE_CHECKSUMS.json';m=json.loads(f.read_text());m['license']='CC-BY-4.0 for author-owned data; MIT for author-owned code; third-party terms preserved. See LICENSE_SCOPE.txt.';f.write_text(json.dumps(m,indent=2)+'\n')
with tempfile.TemporaryDirectory() as td:
 t=Path(td)
 shutil.copytree(a/'licenses',t/'licenses')
 for name in ['LICENSE_SCOPE.txt','THIRD_PARTY_NOTICES.txt','RAW_REPRODUCTION.txt']:
  shutil.copy2(a/name,t/name)
 for name in ['RAW_ARCHIVE_ACCESS.json','RAW_RESTORE_VERIFICATION.json','RAW_SCIENTIFIC_AUDIT.json','RAW_RESTORE_HELPER_QA.json','RAW_TEXT_SECRET_SCAN.json']:
  if (a/name).exists():
   (t/'review_access').mkdir(exist_ok=True);shutil.copy2(a/name,t/'review_access'/name)
 (t/'scripts').mkdir()
 for name in ['verify_restored_archives.py','audit_restored_raw.py']:shutil.copy2(p/'scripts'/name,t/'scripts'/name)
 shutil.copytree(p/'output/review_access_stage/evidence',t/'output/review_access_stage/evidence')
 shutil.copy2(f,t/f.name)
 (t/'README.txt').write_text('''Raw evidence review package, manuscript v0.15.3

Unpublished Zenodo draft. Start with the companion review-core package for the
article, supplement, figures and lightweight offline checks.

Download all six *-raw.zip files beside this support ZIP. Extract this support
ZIP into a new folder. Run:
    python3 stage_downloaded_archives.py /path/to/downloads
This verifies every complete archive against ARCHIVE_CHECKSUMS.json, then
copies it to output/raw_restore/<campaign>/archive.zip. It does not fetch GitHub
or execute native programs. Python 3.11+ and sufficient free disk are required.
    python3 scripts/verify_restored_archives.py
Then follow RAW_REPRODUCTION.txt step 3 for CPU audits. Skip its author-only
part-download step: the complete archives are already supplied here. The fixed
public manifests and original audit expectations are included offline under
output/review_access_stage/evidence; no GitHub account is required.

All six original archives are byte-identical to their authenticated sources.
The intentionally corrupted RTX CPU diagnostic is a negative fixture, not
scientific data loss. The 52,925 logical paths include inherited copies.
External model-weight checks and a GPU rerun remain separate and were not done.
See LICENSE_SCOPE.txt, licenses/ and THIRD_PARTY_NOTICES.txt for reuse terms.
''')
 (t/'stage_downloaded_archives.py').write_text('''from pathlib import Path
import hashlib,json,shutil,sys
root=Path(__file__).resolve().parent
source=Path(sys.argv[1]).resolve()
rows=json.loads((root/'ARCHIVE_CHECKSUMS.json').read_text())['archives']
for r in rows:
 p=source/r['file']
 with p.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
 assert p.stat().st_size==r['bytes'] and digest==r['sha256'],r['file']
 dest=root/'output/raw_restore'/r['file'].removesuffix('-raw.zip')/'archive.zip'
 dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():
  with dest.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==digest
 else: shutil.copyfile(p,dest)
 print('PASS',r['file'])
''')
 files=sorted(x for x in t.rglob('*') if x.is_file());manifest={str(x.relative_to(t)):{'bytes':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in files}
 (t/'PACKAGE_CHECKSUMS.json').write_text(json.dumps({'files':manifest},indent=2)+'\n')
 zpath=p/'output/JSA_v0153_raw_support.zip'
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
  for x in sorted(t.rglob('*')):
   if x.is_file():z.write(x,x.relative_to(t))
 with zipfile.ZipFile(zpath) as z:
  assert z.testzip() is None
  for name,v in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==v['sha256']
 print(zpath.name,zpath.stat().st_size,hashlib.sha256(zpath.read_bytes()).hexdigest(),len(manifest))
