"""Archive all scientific cells, inputs, frozen source and completed child history."""
import json
import zipfile
from prepare import ROOT,sha,save

def main():
    target=ROOT/'raw_archive';target.mkdir(exist_ok=False)
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts or 'raw_archive' in p.parts or p.name=='CPU_JOB.lock':continue
        if p.parent.name=='child_ledger' and 'H3_archive' in p.name:continue # current job unfinished; supplemental final ledger retained in Git
        files.append(p)
    members=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    path=target/'RAW_CPU.zip'
    with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    save(ROOT/'RAW_ARCHIVE_MANIFEST.json',dict(schema=1,archive='raw_archive/RAW_CPU.zip',bytes=path.stat().st_size,sha256=sha(path),members=members,
        excludes='archive itself, current unfinished archiver watchdog receipts, bytecode/lock; final archiver/restore receipts supplement in Git',
        source_native_full_payload='already archived under PR104 c06e1991; exact selected input bytes and full provenance retained here'))
    print(json.dumps(dict(members=len(members),archive_bytes=path.stat().st_size,sha256=sha(path))))
if __name__=='__main__':main()
