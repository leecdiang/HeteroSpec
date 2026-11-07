"""Metadata-only sealing after research jobs ended; no simulator invocation."""
import json
from pathlib import Path
import time
import zipfile
from prepare import ROOT,sha,save

def size(root):return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())
def main():
    assert not (ROOT/'CPU_JOB.lock').exists()
    f0=json.loads((ROOT/'CPU_F0.json').read_bytes())
    for name,h in f0['files'].items():assert sha(ROOT/name)==h
    for name,h in f0['runtime'].items():assert sha(name)==h
    check=json.loads((ROOT/'RESTORED_CPU_RECHECK.json').read_bytes());assert check['cells']==390 and check['independent_saved_trace_checks']=='PASS' and check['new_schedules']==0
    intermediate=json.loads((ROOT/'AUTHENTICATED_ARCHIVE_BYTES_RESTORE.json').read_bytes())
    readback=json.loads((ROOT/'AUTHENTICATED_ARCHIVE_READBACK.json').read_bytes())
    assert intermediate['members_verified']==1638 and readback['authenticated_remote_bytes']
    save(ROOT/'AUTHENTICATED_ARCHIVE_RESTORE.json',dict(**(intermediate|dict(status='PASS',remote_commit='901661bf02c2d07c79430f6817c1a9500a81b128',
        CPU_saved_trace_checks=390,separate_interpreter=True,restored_code_executed=True,CPU_result_sha256=sha(ROOT/'RESTORED_CPU_RECHECK.json'),
        note='Actual authenticated archive restoration and new-interpreter independent numerical/trace recheck; no new schedules or GPU runs'))))
    ledger=list((ROOT/'child_ledger').glob('*-EXIT.json'));data=[json.loads(p.read_bytes()) for p in ledger]
    assert len(ledger)==9 and len(list((ROOT/'child_ledger').glob('*-START.json')))==9
    assert all(d['exit_code']==0 and d['stop_reason'] is None for d in data)
    total=sum(d['seconds'] for d in data);peak=max(d['peak_rss_bytes'] for d in data)
    nested=json.loads((ROOT/'child_ledger/006-H3_readback_identity-EXIT.json').read_bytes())['seconds']
    assert total+nested<14400 and peak<=8589934592
    sizes={str(p):size(p) for p in (ROOT,Path('D:/hs110-authenticated-download-v1'),Path('D:/hs110-authenticated-download-v2'),Path('D:/hs110-fresh-restore-v1'))}
    # Conservative reserve: another entire research directory for closure ZIP,
    # two entire research-directory copies for delivery, plus16MiB metadata.
    bound=sum(sizes.values())+3*size(ROOT)+16777216;assert bound<2147483648
    save(ROOT/'BUDGET_ACCOUNTING.json',dict(research_children=9,watchdog_wrappers=9,recorded_child_seconds=total,
        nested_control_children=2,nested_additional_seconds_upper_bound=nested,conservative_research_plus_nested_seconds=total+nested,
        peak_observed_RSS_bytes=peak,child_exits_all_success=True,one_heavy_child=True,formal_attempts=390,formal_limit=1024,
        scientific_retry=0,new_GPU_model_operator_starts=0,derived_directory_bytes=sizes,
        conservative_derived_delivery_closure_bound_bytes=bound,derived_limit_bytes=2147483648,
        accounting_scope='Measured research/test/analysis/archive/restore driver lifetimes; nested gh lifetime conservatively bounded; ordinary Git, metadata-sealing and OS control starts not globally captured',
        monitor_limit='Watchdog scanned the study directory; external download/restore/delivery sizes additionally bounded here',
        control_transport_failures=1,engineering_test_failures=0,engineering_revisions=1))
    main_manifest=json.loads((ROOT/'RAW_ARCHIVE_MANIFEST.json').read_bytes());initial={x['path'] for x in main_manifest['members']}
    files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and 'raw_archive' not in p.parts and p.relative_to(ROOT).as_posix() not in initial]
    control=ROOT/'raw_archive/RAW_CLOSURE_CONTROL.zip'
    with zipfile.ZipFile(control,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    control_members=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    save(ROOT/'FINAL_ARCHIVE_MANIFEST.json',dict(schema=1,scientific_archive=dict(path='raw_archive/RAW_CPU.zip',bytes=main_manifest['bytes'],sha256=main_manifest['sha256'],members=len(main_manifest['members'])),
        closure_archive=dict(path=control.relative_to(ROOT).as_posix(),bytes=control.stat().st_size,sha256=sha(control),members=control_members),
        acceptance='AUTHENTICATED_ARCHIVE_RESTORE.json',all_390_coordinates_complete=True,terminal='SOFTWARE_FIRST',new_GPU_model_operator_starts=0,
        metadata_scope='Seal manifest itself and later Git/closure-transport/local-delivery receipts supplement these immutable archives; no scientific record is omitted'))
    print(json.dumps(dict(status='SEALED',research_seconds=total,peak_RSS=peak,closure_members=len(files),derived_bound=bound)))
if __name__=='__main__':main()
