"""Full remote text-packet byte readback, no numerical or model rerun claim."""
import base64,gzip,hashlib,json,time
from pathlib import Path
from common import HERE,read,put,sha
from close_results import DEST

def main():
    started=time.monotonic();folder=DEST/'github-readback';download=read(folder/'DOWNLOAD.json');manifest=read(HERE/'results/public_archive/PARTS.json');packet=folder/'scientific-records.json.gz'
    with packet.open('xb') as out:
        for p in manifest['parts']:
            b=base64.b64decode((folder/(p['name']+'.b64')).read_bytes());assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'];out.write(b)
    assert packet.stat().st_size==manifest['joined_bytes'] and sha(packet)==manifest['joined_sha256']
    with gzip.open(packet,'rt',encoding='utf8') as f:bundle=json.load(f)
    assert bundle['schema']=='heterospec.rtx213.supplement-text.v1';index={x['path']:x for x in read(HERE/'results/public_archive/TEXT_INDEX.json')['files']}
    assert len(bundle['records'])==len(index);restored=folder/'text-restored';restored.mkdir();data={}
    for r in bundle['records']:
        b=r['text'].encode();e=index[r['path']];assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256']
        p=restored/r['path'];assert p.resolve().is_relative_to(restored.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);data[r['path']]=r['text']
    ledger=json.loads(data['scripts/results/CUMULATIVE_LEDGER.json']);assert ledger['new_requests']==37 and ledger['cumulative_requests']==2716 and ledger['cumulative_reserved_rows']==2872841
    checks=[json.loads(v) for k,v in data.items() if k.startswith('runtime/checks/') and k.endswith('.json')];assert len(checks)==8 and all(x['passed'] for x in checks)
    assert sum(len(x['all_full_vectors']) for x in checks)==1936 and sum(len(x['all_committed_target_states']) for x in checks)==296
    put(HERE/'results/PUBLIC_READBACK.json',dict(passed=True,commit=download['commit'],parts_downloaded=len(manifest['parts']),joined_bytes=packet.stat().st_size,joined_sha256=sha(packet),
        text_records_verified=len(index),all_text_bytes_reread=True,all_published_qualification_and_ledger_summaries_consistent=True,
        binary_numerical_recheck='Separate local full CAS restoration and archived vector/KV recheck; remote text is not claimed to contain numerical binary operands.',
        new_GPU_requests=0,wall_seconds=time.monotonic()-started))
    print(json.dumps(dict(all_parts_verified=len(manifest['parts']),text_records=len(index),bytes=packet.stat().st_size,no_new_GPU=True)),flush=True)

if __name__=='__main__':main()
