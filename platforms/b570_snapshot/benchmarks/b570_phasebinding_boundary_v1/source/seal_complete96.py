"""Seal selected evidence into a de-duplicated CAS. Does not run native code."""
import pathlib,json,hashlib,zipfile
R=pathlib.Path(__file__).resolve().parent.parent
def h(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def j(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
files=[]
for folder in ['raw','records','native','dependencies','code','versions','baseline/pr92_restore','baseline/native','baseline/design96','baseline/audit93_rederived']:
 files += [p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
# Preserve original authenticated source ZIP, complete readback receipts, all actual
# SDK/raw records and failure logs. Repeated Git transport chunks/restores are not
# separately nested: their exact source archive is retained once.
files += [p for p in (R/'receipts').rglob('*') if p.is_file() and '__pycache__' not in p.parts and not any(x.startswith(('f0a_remote_blobs','f0a_source_restored','f0a_amend_remote','local_restore','remote_restore')) for x in p.relative_to(R/'receipts').parts)]
files += [p for p in (R/'baseline').iterdir() if p.is_file()]
files += [p for p in (R/'build/Release').iterdir() if p.suffix in ['.exe','.dll','.lib','.exp','.txt']]
files += [p for p in R.iterdir() if p.is_file() and p.suffix in ['.json','.jsonl','.md','.log'] and not p.name.startswith(('CAS_', 'cas-seal', 'LOCAL_RESTORE','REMOTE_RESTORE'))]
files += [p for p in (R/'analysis').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files=sorted(set(files));objects={};rows=[]
for p in files:
 q=p.relative_to(R).as_posix();check=pathlib.PurePosixPath(q);assert not check.is_absolute() and '..' not in check.parts and p.suffix.lower()!='.gguf'
 s=h(p);objects.setdefault(s,p);rows.append(dict(path=q,bytes=p.stat().st_size,sha256=s))
m=dict(schema='heterospec.b570.phasebinding.cas.v1',stage='FINAL',files=rows,logical_files=len(rows),unique_objects=len(objects),source_commit=j(R/'F0A_AUTHENTICATED.json')['commit'],design_head=j(R/'PLAN.json')['design_head'],external_models=j(R/'ASSET_PREFLIGHT.json')['models'],baseline_logical_files=7379,results_sha256=h(R/'analysis/RESULTS.json'),audit_script_sha256=h(R/'code/verify96.py'),scope='Full inherited PR92 evidence plus native new diagnostics/source/failures/ledger. No external model weights.')
write(R/'public/ARCHIVE_MANIFEST.json',m)
a=R/'COMPLETE_CAS.zip'
with zipfile.ZipFile(a,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for s,p in sorted(objects.items()):z.write(p,'objects/'+s)
 z.writestr('MANIFEST.json',json.dumps(m,ensure_ascii=False,indent=2)+'\n')
b=a.read_bytes();parts=[]
for i in range(0,len(b),524288):
 p=R/'public'/('COMPLETE_CAS.chunk'+str(len(parts)+1).zfill(3));p.write_bytes(b[i:i+524288]);bb=p.read_bytes()
 parts.append(dict(name=p.name,bytes=len(bb),sha256=h(p),git_blob_sha1=hashlib.sha1(b'blob '+str(len(bb)).encode()+b'\0'+bb).hexdigest()))
d=dict(schema='heterospec.b570.phasebinding.cas.transport.v1',archive_bytes=len(b),archive_sha256=h(a),manifest_sha256=h(R/'public/ARCHIVE_MANIFEST.json'),manifest_git_blob_sha1=hashlib.sha1(b'blob '+str((R/'public/ARCHIVE_MANIFEST.json').stat().st_size).encode()+b'\0'+(R/'public/ARCHIVE_MANIFEST.json').read_bytes()).hexdigest(),logical_files=len(rows),unique_objects=len(objects),parts=parts,format='ZIP CAS, 512KiB GitHub-readable raw chunks',source_commit=m['source_commit'])
write(R/'public/COMPLETE_CAS.json',d);print(json.dumps({k:v for k,v in d.items() if k!='parts'}|dict(parts=len(parts))))
