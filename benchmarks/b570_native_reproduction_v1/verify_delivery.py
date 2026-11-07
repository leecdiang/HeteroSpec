"""Verify every archived selected byte against the embedded manifest; no native execution."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,zipfile
def check(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    check(not a.out.exists(),'Existing verification receipt')
    with zipfile.ZipFile(a.archive) as z:
        names=z.namelist();check(len(names)==len(set(names)),'Duplicate archive member')
        check(all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and ':' not in n for n in names),'Unsafe archive member')
        manifest=json.loads(z.read('manifest.json'));rows=manifest['files']
        check(set(names)=={x['path']for x in rows}|{'manifest.json'},'Archive inventory mismatch')
        check(not any(n.lower().endswith('.gguf')for n in names),'Model bytes excluded')
        total=0
        for row in rows:
            digest=hashlib.sha256();count=0
            with z.open(row['path']) as f:
                while block:=f.read(1024*1024):count+=len(block);digest.update(block)
            check(count==row['bytes'] and digest.hexdigest()==row['sha256'],'Archive bytes changed '+row['path']);total+=count
    with a.archive.open('rb') as f:archive_hash=hashlib.file_digest(f,'sha256').hexdigest()
    out={'status':'ARCHIVE_FULL_BYTE_VERIFICATION_PASS','archive':str(a.archive.resolve()),'archive_bytes':a.archive.stat().st_size,'archive_sha256':archive_hash,'verified_files':len(rows),'uncompressed_bytes':total,'scope':'Lossless recovery and file integrity; native qualification has separate receipts'}
    a.out.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
if __name__=='__main__':main()
