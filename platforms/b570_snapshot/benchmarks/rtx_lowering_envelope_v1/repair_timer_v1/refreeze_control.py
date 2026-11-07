"""Pre-GPU control-only correction. Preserve initial dry failure and all slots."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;B=R.parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    f0=json.loads((R/'failed_dry_F0/GPU14_F0.json').read_bytes());old=json.loads((B/'registration/S1_F0.json').read_bytes())
    assert not Path(f0['execution_root']).exists()
    before=f0['slots'];files={p['path']:p for p in old['files']}
    for p in sorted(R.rglob('*')):
        if p.is_file() and p.name not in ('GPU14_F0.json','RAW_REPAIR.zip','RAW_REPAIR_MANIFEST.json'):
            files[str(p)]=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
    # The preserved initial F0 is evidence, not a recursive active freeze.
    p=R/'failed_dry_F0/GPU14_F0.json';files[str(p)]=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
    f0.update(schema=2,registration_revision=2,files=list(files.values()),pre_GPU_control_amendment=dict(initial_unexecuted_F0_sha256=sha(p),reason='Dry hash used whole-file reads and hit bounded memory. Replace with streaming SHA256; preserve failure. Add complete prespecified pairwise q2 raw analysis. Same14 fixed slots/native binary/input/limits and zero GPU starts.',old_F0_and_old_720_execution_unchanged=True))
    assert before==f0['slots'];save(R/'GPU14_F0.json',f0)
    save(R/'GPU14_SELECTION.json',dict(registered_before_new_GPU_outputs=True,slots=[dict(id=s['id'],descriptor=s['descriptor'],layout=s['layout'],repeat=s['repeat'],group=s['group'],support_API_queries=s['registered_support_queries']) for s in before],support_API_queries=166,author_GPU_permission='NOT_GRANTED'))
    print('New CPU-only corrected F0',sha(R/'GPU14_F0.json'))
if __name__=='__main__':main()
