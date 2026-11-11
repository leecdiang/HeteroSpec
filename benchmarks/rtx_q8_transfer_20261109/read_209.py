"""Verify the complete archived stream and retain the compiled M2 frontend."""
from pathlib import Path
import hashlib, importlib.util, json, shutil, subprocess, sys, time
from admission import HERE, ROOT, REPO, sha, put

def main():
    start=time.monotonic();base=HERE.parent/'server_expansion_v1/M2'
    archive=base/'results_pilot_20261108/archive'
    dest=ROOT/'reference_209';dest.mkdir(exist_ok=False)
    parts=json.loads((archive/'PARTS.json').read_bytes());joined=dest/'scientific-records.json.gz'
    with joined.open('xb') as out:
        for item in parts['parts']:
            p=archive/item['name'];assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256']
            with p.open('rb') as f:shutil.copyfileobj(f,out)
    assert joined.stat().st_size==parts['joined_bytes'] and sha(joined)==parts['joined_sha256']
    spec=importlib.util.spec_from_file_location('replay_209',base/'replay_public.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    index={r['path']:r for r in json.loads((archive/'TEXT_INDEX.json').read_bytes())['files']}
    seen=set();retained=[]
    for record in module.records(joined):
        key=record['path'];assert key not in seen and key in index;seen.add(key)
        raw=record['text'].encode();item=index[key]
        assert len(raw)==item['exported_bytes'] and hashlib.sha256(raw).hexdigest()==item['exported_sha256']
        if key.startswith('m2-build-01/frontend/') or key in ('m2-run-03/ROOT_SELECTION.json','m2-run-03/SOURCE_FREEZE.json'):
            p=dest/key;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);retained.append(dict(path=key,sha256=sha(p),raw_sha256=item['raw_sha256']))
    assert set(index)==seen
    p=dest/'adapt_host_203.py';p.write_bytes(subprocess.check_output(['git','-C',str(REPO),'show','592abdfe9267fd97ecbde18cd0ee9a1bfc319e20:benchmarks/linux_transfer_v1/adapt_host.py']))
    put(dest/'READBACK.json',dict(passed=True,records_checked=len(seen),joined_sha256=sha(joined),
        text_index_sha256=sha(archive/'TEXT_INDEX.json'),retained=retained,model_forwards=0,wall_seconds=time.monotonic()-start,
        scope='Full public text stream byte validation and exact generated frontend inspection; not Windows numerical qualification'))
    print(json.dumps(dict(records=len(seen),retained=len(retained),roots=json.loads((dest/'m2-run-03/ROOT_SELECTION.json').read_bytes())['roots'],model_forwards=0)))

if __name__=='__main__':main()
