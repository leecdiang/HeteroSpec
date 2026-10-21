"""Read-only final integrity audit against frozen and native evidence."""
from pathlib import Path
import datetime, hashlib, json, time, zipfile
from prepare import ROOT, read, write, sha

def main():
    started=time.monotonic();reg=read(ROOT/'REGISTRATION.json');close=read(ROOT/'CLOSEOUT.json')
    frozen=read(ROOT/'FROZEN_FILES.json')
    assert sha(ROOT/'FROZEN_FILES.json')==reg['frozen_files_sha256']
    for row in frozen:
        p=Path(row['path']);assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],p
    ledger=read(ROOT/'BUDGET_LEDGER.json');receipts=ledger['sessions'];previous=None
    for r in receipts:
        if previous:assert r['started_utc']>previous
        assert r['exit_observed'] and r['job_kill_on_close']
        previous=r.get('exit_observed_utc',r['finished_utc'])
        native=read(ROOT/f"{r['mode']}-{r['index']}/result.json")
        service_sum=sum(x['service_seconds'] for x in native['requests'])
        assert service_sum+native['model_load_seconds']<=r['charged_seconds']+.1,(r['step'],service_sum,r['charged_seconds'])
    assert abs(sum(x['charged_seconds'] for x in receipts)-ledger['charged_worker_seconds'])<1e-8
    assert abs(close['worker_wall_seconds']-ledger['charged_worker_seconds'])<1e-8
    assert len(receipts)<=9 and len(read(ROOT/'SLOT_DISPOSITION.json'))==156
    if close['complete_matrix']:
        assert len(receipts)==9 and close['completed_native_request_records']==156
        assert read(ROOT/'E0_AUDIT.json')['status']=='E0_FULL_PASS'
        assert read(ROOT/'QUALIFICATION_AUDIT.json')['status']=='E1_FULL_PASS'
        assert read(ROOT/'QUALIFICATION_AUDIT.json')['raw_vectors_rechecked']==914
        analysis=read(ROOT/'INDEPENDENT_ANALYSIS.json')
        assert analysis['toolkit_agreement'] and analysis['warmups']==64 and analysis['measured']==64
    vectors=[]
    for name in ['E0_RAW_MANIFEST.json','E1_RAW_MANIFEST.json']:
        if (ROOT/name).exists():vectors+=read(ROOT/name)
    archive=read(ROOT/'LOCAL_RAW_ARCHIVE.json');assert sha(Path(archive['path']))==archive['sha256']
    with zipfile.ZipFile(archive['path']) as z:
        assert len(z.namelist())==archive['vectors']
        for row in vectors:
            p=Path(row['path']);member=str(p.relative_to(ROOT)).replace('\\','/')
            assert hashlib.sha256(z.read(member)).hexdigest()==row['sha256'],member
    compact=read(ROOT/'COMPACT_MANIFEST.json');assert sha(Path(compact['path']))==compact['sha256']
    with zipfile.ZipFile(compact['path']) as z:assert z.testzip() is None
    history=read(ROOT/'HISTORY.json')
    assert history['uncommitted_attempt2_timing'][1]['requests']==5
    assert history['historical_total_exactly_known'] is False
    # Snapshot the actual compiler products and logs after their immutability checks.
    result={'status':'PASS','frozen_file_hashes_rechecked':len(frozen),
            'independent_native_vector_archive_checks':len(vectors),'worker_receipts':len(receipts),
            'nonoverlap_and_ledger_verified':True,'complete_new_matrix':close['complete_matrix'],
            'historical_incomplete_timing_preserved':True,'external_raw_certification':False,
            'audit_cpu_parent_wall_seconds':time.monotonic()-started,
            'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    write('DELIVERY_CHECK.json',result)
    destination=Path(reg['worktree'])/reg['result_path']
    import shutil
    for name in ['DELIVERY_CHECK.json','verify_delivery.py']:shutil.copy2(ROOT/name,destination/name)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
