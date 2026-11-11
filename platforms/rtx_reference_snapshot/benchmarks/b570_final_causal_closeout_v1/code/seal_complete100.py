"""CPU-only full CAS seal, no executor import."""
import json,hashlib,zipfile,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def main():
 assert json.loads((R/'STUDY_COMPLETION.json').read_bytes())['status']=='COMPLETED'
 assert json.loads((R/'analysis/INDEPENDENT_VERIFICATION.json').read_bytes())['status']=='PASS'
 fs=[]
 for folder in ['code','native','dependencies','build/Release','baseline','raw','records','payloads','operator_payloads','versions','analysis','design']:
  fs.extend(p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 fs.extend(p for p in R.iterdir() if p.is_file() and p.name not in ['COMPLETE_CAS.zip','COMPLETE_CAS.json','ARCHIVE_MANIFEST.json','LOCAL_RESTORE.json','REMOTE_RESTORE.json','SCOPE_CHECK.json','RECEIPT_PUBLICATION.json'] and (p.suffix in ['.json','.jsonl','.md','.log'] or p.name=='F0_SOURCE.zip'))
 fs.extend(p for p in (R/'receipts').iterdir() if p.is_file() and p.suffix in ['.log'])
 logical=[];objects={}
 for p in sorted(set(fs)):
  h=sha(p);logical.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=h));objects.setdefault(h,p)
 m=dict(format='SHA256-CAS-ZIP-v1',logical_files=len(logical),unique_objects=len(objects),files=logical,external_weights='Actual inherited Meta-Llama-3.1-8B Q6_K GGUF full SHA verified at admission and every independent restore, external absolute path +publisherrevision preserved, not embedded; historical complete PR99 evidence fully embedded',parent_head='a1925c4a3b040f9ad3db7ec4301042791a82fe75')
 save(R/'ARCHIVE_MANIFEST.json',m)
 with zipfile.ZipFile(R/'COMPLETE_CAS.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  z.writestr('MANIFEST.json',(R/'ARCHIVE_MANIFEST.json').read_bytes())
  for h,p in sorted(objects.items()):z.write(p,'objects/'+h)
 p=R/'COMPLETE_CAS.zip';save(R/'COMPLETE_CAS.json',dict(bytes=p.stat().st_size,sha256=sha(p),logical_files=len(logical),unique_objects=len(objects),manifest_sha256=sha(R/'ARCHIVE_MANIFEST.json')))
 print((R/'COMPLETE_CAS.json').read_text(),flush=True)
if __name__=='__main__':main()
