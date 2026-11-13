"""Seal only new audit records; never modify original experimental evidence."""
import datetime,json,platform,zipfile
from core import HERE,OUT,REPO,RECORDS,WORK,read,put,digest
import numpy as np

def main():
    ledger=read(RECORDS/'CUMULATIVE_LEDGER.json');assert digest((WORK/'ledger.sqlite').read_bytes())==ledger['source_new_ledger_sha256']
    put('AUDIT_SCOPE_CLOSED.json',dict(closed_bjt=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        new_GPU_requests=0,new_native_processes=0,original_new_ledger_sha256=ledger['source_new_ledger_sha256'],original_ledger_bytes_unchanged=True,
        cumulative_requests=2679,cumulative_reserved_rows=2854298,python=platform.python_version(),numpy=np.__version__,
        actual_recompute='Raw numerical/state audit, raw panel/bootstrap and source-pool/fixture reconstruction',
        original_validators_imported=False,optional_supplement_executed=False,engineering_wall_total=None,
        scope='New audit directory only; existing data, failures, original Windows baseline and paper unchanged. No merge/Release/submission.'))
    files=[]
    for p in sorted(HERE.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            raw=p.read_bytes();files.append(dict(path=p.relative_to(HERE).as_posix(),bytes=len(raw),sha256=digest(raw)))
    index=HERE/'AUDIT_ARTIFACTS.json'
    with index.open('x',encoding='utf8') as f:json.dump(dict(files=files,hash_scope='Full local bytes; Git may normalize text EOL. Index excludes itself and subsequent delivery receipt.'),f,indent=2)
    target=REPO.parent/'q8rtx213-freeze-audit-evidence-20261109.zip'
    with zipfile.ZipFile(target,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for item in files:z.write(HERE/item['path'],item['path'])
        z.write(index,'AUDIT_ARTIFACTS.json')
    checked=0
    with zipfile.ZipFile(target) as z:
        for item in files:
            raw=z.read(item['path']);assert len(raw)==item['bytes'] and digest(raw)==item['sha256'];checked+=1
        assert z.read('AUDIT_ARTIFACTS.json')==index.read_bytes()
    put('AUDIT_PACKET_READBACK.json',dict(passed=True,archive=str(target),archive_bytes=target.stat().st_size,archive_sha256=digest(target.read_bytes()),
        audit_members_rehashed=checked+1,original_capture_bytes_included=False,raw_capture_dependency='Existing immutable PR213 complete archive/runtime, bound by RAW_FILES_READ hashes; model weights excluded',new_GPU_requests=0))
    print(json.dumps(dict(archive=str(target),members=checked+1,bytes=target.stat().st_size,all_audit_bytes_reread=True)),flush=True)

if __name__=='__main__':main()
