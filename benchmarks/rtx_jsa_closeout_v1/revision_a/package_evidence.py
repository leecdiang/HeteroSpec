"""Lossless finite evidence archives with independent fresh extraction checks."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

work=Path(__file__).parent;repo=work/'HeteroSpec';here=repo/'benchmarks/rtx_jsa_closeout_v1/revision_a'
def read(p):return json.loads(p.read_bytes())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())

def main(config_path,verification,out):
    config=read(config_path);root=Path(config['run_root']);out.mkdir(exist_ok=False)
    extract=out/'fresh-extraction';extract.mkdir()
    files=[];names=set()
    def add(p,name):
        assert p.is_file() and name not in names and '..' not in Path(name).parts
        names.add(name);files.append({'source':str(p),'path':name,'bytes':p.stat().st_size,'sha256':sha(p)})
    for p in sorted(root.rglob('*')):
        if p.is_file():add(p,'raw/'+p.relative_to(root).as_posix())
    for p in sorted(verification.rglob('*')):
        if p.is_file():add(p,'verification/'+p.relative_to(verification).as_posix())
    audit=read(here/'FINAL_EXPOSURE_AUDIT.json')
    for i,r in enumerate(audit['receipts']):add(Path(r['path']),f'exposure/{i:02d}_{Path(r["path"]).name}')
    for p in sorted(here.rglob('*')):
        if p.is_file() and p.suffix in ['.py','.h','.md','.json','.jsonl','.csv']:add(p,'registration/'+p.relative_to(here).as_posix())
    for version in ['amended-native','amended-native-v2']:
        for variant in ['original','metadata4']:
            base=work/version/variant
            for p in sorted((base/'source').rglob('*')):
                if p.is_file():add(p,f'native/{version}/{variant}/source/'+p.relative_to(base/'source').as_posix())
            for p in sorted(base.glob('*.json')):add(p,f'native/{version}/{variant}/'+p.name)
            p=base/'build/bin/llama-server.exe';add(p,f'native/{version}/{variant}/llama-server.exe')
    save(out/'FILES.json',files)
    # Each archive has at most 1 GiB original bytes, below the GitHub per-asset ceiling.
    groups=[];current=[];size=0
    for r in files:
        if current and size+r['bytes']>1024**3:groups.append(current);current=[];size=0
        assert r['bytes']<1024**3,'single source file requires prospective transport splitting'
        current.append(r);size+=r['bytes']
    if current:groups.append(current)
    archives=[]
    for i,group in enumerate(groups):
        path=out/f'RTX_CLOSEOUT_{i:03d}.zip'
        with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
            for r in group:archive.write(r['source'],r['path'])
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            for r in group:
                target=extract/r['path'];target.parent.mkdir(parents=True,exist_ok=True)
                assert not target.exists()
                with archive.open(r['path']) as source,target.open('xb') as dest:
                    while True:
                        block=source.read(1024*1024)
                        if not block:break
                        dest.write(block)
                assert target.stat().st_size==r['bytes'] and sha(target)==r['sha256']
        archives.append({'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path),'files':len(group),'uncompressed_bytes':sum(r['bytes'] for r in group),'fresh_extraction':'PASS'})
        save(out/'ARCHIVE_PROGRESS.json',archives)
        print('ARCHIVE',i,len(group),path.stat().st_size,'fresh extraction PASS',flush=True)
    save(out/'ARCHIVES.json',{'status':'PASS_LOSSLESS_FRESH_EXTRACTION','files':len(files),'original_bytes':sum(r['bytes'] for r in files),'file_manifest_sha256':sha(out/'FILES.json'),'archives':archives,'excluded':'Model weights and third-party numerical DLL bytes; their frozen identity manifests are included'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--verification',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=repo);a=p.parse_args();repo=a.repo.resolve();work=repo.parent;here=repo/'benchmarks/rtx_jsa_closeout_v1/revision_a';main(a.config,a.verification,a.out)
