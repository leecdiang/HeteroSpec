"""Read-only identity reconciliation and full-source recovery; never initialize CUDA."""
import hashlib,json,shutil,sys
from pathlib import Path
from s0_budget import ROOT,save
OLD=Path('D:/hs104-e1-v1');RESTORED=Path('D:/hs104-authenticated-final-restore/E1/data')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        while b:=f.read(1048576):h.update(b)
    return h.hexdigest()
def main():
    assert json.loads((OLD/'RUN_COMPLETE.json').read_bytes())['contexts']==72
    inventory=json.loads((OLD/'SOURCE_HASHES.json').read_bytes());source=RESTORED/'native/source'
    for rel,h in inventory.items():assert sha(source/rel)==h,rel
    target=ROOT/'native/source';target.parent.mkdir(exist_ok=True);shutil.copytree(source,target)
    for rel,h in inventory.items():assert sha(target/rel)==h
    save(ROOT/'PARENT_SOURCE_HASHES.json',inventory)
    contexts=[]
    for index in range(72):
        r=json.loads((OLD/f'snapshot_registry/{index:03d}.json').read_bytes());original=Path(r['root']);snap=RESTORED/original.relative_to(OLD)
        for name,h in r['registry'].items():assert sha(snap/name)==h
        meta=json.loads((snap/'snapshot.json').read_bytes());contexts.append(dict(index=index,context=r['context'],root=str(snap),registry=r['registry'],metadata=meta))
    save(ROOT/'FULL_SNAPSHOTS.json',dict(contexts=contexts,count=72,cropped=False,source='authenticated PR104 complete fresh-restored bytes'))
    f0=json.loads(Path('D:/hs-qb-confirmation-v02/FREEZE.json').read_bytes());pins=[]
    for item in f0['files']:
        p=Path(item['path']);assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],str(p);pins.append(item)
    build=json.loads((OLD/'NATIVE_BUILD.json').read_bytes())
    for name,h in build['numerical_DLL_sha256'].items():assert sha(OLD/'native/build/bin'/name)==h
    save(ROOT/'IDENTITY_RECONCILIATION.json',dict(status='PASS',original_files=pins,PR104='f997262d6b0accb126a1217c9356745cc8bbf708',PR110='dae5aea9f9009a686196dd89981c0ae9699ae612',
        design='0fba42fe8732527ca99ceb9c9ee67e93b18e9d80',source_files=len(inventory),snapshots=72,numerical_DLLs=build['numerical_DLL_sha256'],
        numerical_runtime_directory=str(OLD/'native/build/bin'),GPU_initializations=0,device_queries=0,source_copied_bytes=sum((target/n).stat().st_size for n in inventory),
        immutable_large_payload='Full tensor files and numerical DLLs referenced read-only by exact hashes; not copied or cropped into PR110 inputs'))
    print(json.dumps(dict(source_files=len(inventory),snapshots=len(contexts),freeze_files_verified=len(pins),status='PASS')))
if __name__=='__main__':main()
