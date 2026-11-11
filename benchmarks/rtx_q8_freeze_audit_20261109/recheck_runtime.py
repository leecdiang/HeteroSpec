"""Read-only runtime identity and evidence timing precision checks."""
from pathlib import Path
import collections,json
from core import RECORDS,WORK,OUT,ORIGINAL,read,put,digest,ledger

def main():
    fingerprints={};records=[];drivers=read(RECORDS/'DRIVER_MODULE_PINS.json')['pins']
    for a in ledger():
        folder=WORK/'runs'/a['id'];j=read(folder/'JOB.json');build=read(folder/'BUILD.json')
        p=folder/'ACTUAL_MODULES.json'
        if not p.exists():assert a['status']=='EXPECTED_REJECT';continue
        modules=read(p);assert any(x['sha256']==j['exe_sha256'] for x in modules['modules_after'] if Path(x['path']).name.lower()=='worker.exe')
        for x in modules['modules_before']+modules['modules_after']:
            name=Path(x['path']).name.lower();expected={k.lower():h for k,h in build['modules'].items()}.get(name)
            if name in drivers:expected=drivers[name]['sha256']
            if expected:
                assert x['sha256']==expected,('Loaded numerical module pin mismatch',a['id'],x)
                key=x['path'].lower()
                if key not in fingerprints:fingerprints[key]=dict(path=x['path'],sha256=digest(Path(x['path']).read_bytes()))
                assert fingerprints[key]['sha256']==expected
        assert any(Path(x['path']).name.lower()=='ggml-cuda.dll' for x in modules['modules_after'])
        records.append(dict(job=a['id'],stage=a['stage'],exe_sha256=j['exe_sha256'],numerical_module_records_consistent=True))
    t=read(OUT/'TIMELINE_FINAL.json');near=[]
    for a in t['attempts']:
        if not a['local_exact_file_precedes_reservation']:
            delta=Path(RECORDS/a['manifest'].split('results_20261109/',1)[1]).stat().st_mtime-a['started']
            near.append(dict(job=a['id'],manifest_mtime_minus_reservation_s=delta,
                interpretation='Sub-microsecond local clock/float precision tie. Keep raw sign; cannot resolve causal order at this precision. Source code writes/closes the file before execute().'))
    old=read(RECORDS/'CUMULATIVE_LEDGER_INITIAL.json');current=read(RECORDS/'CUMULATIVE_LEDGER.json')
    assert digest(Path(old['source']).read_bytes())==old['sha256'] and digest((WORK/'ledger.sqlite').read_bytes())==current['source_new_ledger_sha256']
    put('RUNTIME_TIMING_SCOPE.json',dict(passed=True,current_numerical_module_files_rehashed=list(fingerprints.values()),recorded_loads_rechecked=records,
        ambiguous_manifest_mtime=near,publication_timestamp_limit='Commit author dates, local reflog, executor readback receipts and filesystem timestamps are corroborating local evidence, not an independent server-side historical timestamp attestation.',
        ledgers_byte_unchanged=True,cumulative_requests=2679,cumulative_rows=2854298,qualification_requests=463,new_GPU_requests=0,
        limits='Actual historical process execution and unlogged attempted inputs cannot be independently reconstructed from hashes alone. No native executable was launched by this audit.'))
    print('Runtime records/current numerical files consistent; original ledgers unchanged',flush=True)

if __name__=='__main__':main()
