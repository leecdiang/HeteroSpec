"""CPU/filesystem-only delivery and conservative new-artifact accounting."""
import hashlib,json,shutil,subprocess
from pathlib import Path
E=Path(__file__).resolve().parent
OUT=Path('C:/Users/ASUS/Documents/Codex/2026-10-14/heterospec-pr-104-rtx-implementation-pq/outputs/PR113_GPU14')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2);f.write('\n')
def size(p):return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
def main():
    assert json.loads((E/'FRESH_RESTORE.json').read_bytes())['status']=='PASS'
    OUT.mkdir(exist_ok=False);copies=[]
    for p in sorted(E.iterdir()):
        if p.is_file():
            dst=OUT/p.name;shutil.copyfile(p,dst);assert sha(p)==sha(dst)
            copies.append(dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)))
    save(E/'DELIVERY.json',dict(destination=str(OUT),files=copies,all_copies_byte_equal=True))
    roots=[Path('D:/hs113-timer-gpu14-v1'),E,Path('D:/hs113-gpu14-authenticated-v1'),Path('D:/hs113-gpu14-fresh-restore-v1'),OUT]
    measured=[dict(path=str(p),bytes=size(p)) for p in roots]
    objects=subprocess.check_output(['git','-C','D:/hs113','rev-list','--objects','9aefd4c722ac78421994052e41412c2c0417d73b..HEAD'])
    ids=b'\n'.join(line.split(b' ',1)[0] for line in objects.splitlines())+b'\n'
    stats=subprocess.check_output(['git','-C','D:/hs113','cat-file','--batch-check=%(objectsize)'],input=ids)
    object_bytes=sum(int(x) for x in stats.splitlines())
    # Includes a second entire uncompressed copy of new Git objects plus metadata
    # headroom; no pre-existing repair/S0/old scientific budget is borrowed.
    bound=sum(p['bytes'] for p in measured)+2*object_bytes+3*1024*1024
    assert bound<1073741824
    save(E/'ARTIFACT_ACCOUNTING.json',dict(status='PASS',directories=measured,directory_sum_bytes=sum(p['bytes'] for p in measured),
        new_Git_objects_uncompressed_bytes=object_bytes,Git_storage_conservative_allowance=2*object_bytes,
        final_metadata_and_small_tool_receipt_reserve=3*1024*1024,all_new_derived_conservative_bound_bytes=bound,ceiling_bytes=1073741824,
        no_old_budget_reuse=True,scope='All new raw/repo/authenticated-download/fresh-restore/user-delivery roots plus conservative Git and closure metadata allowance. CPU/Git packaging is not additional experimental GPU work.'))
    for name in ('DELIVERY.json','ARTIFACT_ACCOUNTING.json'):shutil.copyfile(E/name,OUT/name)
    print('PASS user delivery and all new artifacts:',bound,'<',1073741824)
if __name__=='__main__':main()
