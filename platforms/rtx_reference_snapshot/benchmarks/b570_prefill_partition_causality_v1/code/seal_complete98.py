"""CPU-only complete content-address archive; deterministic reconstruction manifest."""
import json,hashlib,zipfile,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def main():
 comp=json.loads((R/'STUDY_COMPLETION.json').read_bytes());assert comp['status']=='COMPLETED' and comp['requests_completed']==63
 assert json.loads((R/'analysis/INDEPENDENT_VERIFICATION.json').read_bytes())['status']=='PASS'
 fs=[]
 for folder in ['code','native','dependencies','build/Release','baseline','raw','records','payloads','versions','analysis']:
  fs.extend(p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 fs.extend(p for p in R.iterdir() if p.is_file() and p.name not in ['COMPLETE_CAS.zip','COMPLETE_CAS.json','ARCHIVE_MANIFEST.json'] and (p.suffix in ['.json','.jsonl','.md','.log'] or p.name=='F0A_SOURCE.zip'))
 fs.extend(p for p in (R/'receipts').iterdir() if p.is_file() and p.name in ['synthetic.stdout.log','synthetic.stderr.log','audit.stdout.log','audit.stderr.log'])
 logical=[]
 objects={}
 for p in sorted(set(fs)):
  h=sha(p);rel=p.relative_to(R).as_posix();logical.append(dict(path=rel,bytes=p.stat().st_size,sha256=h));objects.setdefault(h,p)
 m=dict(format='SHA256-CAS-ZIP-v1',logical_files=len(logical),unique_objects=len(objects),files=logical,external_weights='Q6 GGUF hash-bound; not embedded; full hash rechecked by independent audit',parent_head='5a66653bd0ce413d4eb9aef3a4501b93c138071b')
 save(R/'ARCHIVE_MANIFEST.json',m)
 with zipfile.ZipFile(R/'COMPLETE_CAS.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  z.writestr('MANIFEST.json',(R/'ARCHIVE_MANIFEST.json').read_bytes())
  for h,p in sorted(objects.items()):z.write(p,'objects/'+h)
 p=R/'COMPLETE_CAS.zip'
 d=dict(bytes=p.stat().st_size,sha256=sha(p),logical_files=len(logical),unique_objects=len(objects),manifest_sha256=sha(R/'ARCHIVE_MANIFEST.json'))
 save(R/'COMPLETE_CAS.json',d);print(json.dumps(d),flush=True)
if __name__=='__main__':main()
