"""Additive inventory-complete builder; frozen execution/restore code stays unchanged."""
import json, pathlib, tarfile
from common import ROOT,DOC,OUT,load,sha,save
def main():
    artifact=ROOT/'artifacts/rtx_target_only_bridge_v1';artifact.mkdir(parents=True,exist_ok=True);files={}
    for directory in [OUT,DOC/'historical_raw',pathlib.Path(__file__).parent]:
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.tmp') and 'packaging' not in p.parts:
                files[p.relative_to(ROOT).as_posix()]=p
    for p in DOC.iterdir():
        if p.is_file() and (p.suffix in ['.md','.json','.jsonl','.csv'] or p.name=='.gitignore'):files[p.relative_to(ROOT).as_posix()]=p
    for p in (DOC/'inputs').rglob('*'):
        if p.is_file():files[p.relative_to(ROOT).as_posix()]=p
    for name in set(load(DOC/'SOURCE_BINDINGS.json')['files'])|set(load(DOC/'FREEZE_RECEIPT.json')['files']):files[name]=ROOT/name
    manifest={'schema':'heterospec.cas.archive.v1','files':{name:{'sha256':sha(p),'bytes':p.stat().st_size} for name,p in sorted(files.items())},'omissions':['model weights','released/native runtime binaries'],'scope':'snapshot before packaging and final delivery receipts; later reports/receipts remain separate Git objects','builder':'additive delivery_package includes every freeze-bound file, including .gitignore; original frozen package.py unchanged'}
    work=OUT/'packaging';work.mkdir(exist_ok=True);save(work/'MANIFEST.json',manifest);archive=work/'raw-cas-v1.tar.gz';cas={}
    for name,p in files.items():cas.setdefault(manifest['files'][name]['sha256'],p)
    with tarfile.open(archive,'w:gz',compresslevel=6) as tf:
        tf.add(work/'MANIFEST.json',arcname='MANIFEST.json',recursive=False)
        for h,p in sorted(cas.items()):tf.add(p,arcname='cas/'+h,recursive=False)
    parts=[]
    with archive.open('rb') as f:
        i=0
        for data in iter(lambda:f.read(48*1024*1024),b''):
            i+=1;p=artifact/f'raw-cas-v1.part-{i:03d}';p.write_bytes(data);parts.append({'path':p.relative_to(ROOT).as_posix(),'bytes':len(data),'sha256':sha(p)})
    save(artifact/'MANIFEST.json',manifest);index={'schema':'heterospec.cas.parts.v1','bytes':archive.stat().st_size,'sha256':sha(archive),'parts':parts,'logical_files':len(files),'unique_blobs':len(cas)};save(artifact/'ARCHIVE.json',index)
    print(json.dumps(index),flush=True)
if __name__=='__main__':main()
