"""Read-only end-state audit; never starts model inference."""
from pathlib import Path
import datetime,json,sqlite3,subprocess
from admission import ROOT,REPO,put,sha
from execute import WORK,BASE,LOCK,sample,resources

def main():
    assert not LOCK.exists(),'Another experiment still holds mutex'
    live=json.loads((ROOT/'LIVE_RECORDS.json').read_bytes())
    assert live['passed'] and live['complete_workers']==64 and len(live['records'])==1152
    db=sqlite3.connect((WORK/'ledger.sqlite').as_uri()+'?mode=ro',uri=True)
    groups=db.execute('SELECT stage,SUM(requests),SUM(rows),COUNT(*) FROM attempts GROUP BY stage').fetchall()
    statuses=db.execute('SELECT status,COUNT(*) FROM attempts GROUP BY status').fetchall();db.close()
    assert sum(x[1] for x in groups)==1775 and sum(x[2] for x in groups)==2296770
    assert dict(statuses).get('EXPECTED_REJECT')==8 and set(dict(statuses))=={'COMPLETE','EXPECTED_REJECT'}
    original=json.loads((ROOT/'CUMULATIVE_LEDGER_INITIAL.json').read_bytes());assert sha(BASE/'ledger.sqlite')==original['sha256']
    closure=json.loads((ROOT/'SOURCE_BINDINGS.json').read_bytes())
    for path,item in closure['files'].items():assert sha(Path(path))==item['sha256']
    manifest=json.loads((ROOT/'JOB_MANIFEST_LIVE.json').read_bytes());job=manifest['jobs'][0]['job']
    models={}
    for role in ('target','draft'):
        p=Path(job[role+'_model']);digest=sha(p);assert digest==job[role+'_sha256'];models[role]=dict(path=str(p),sha256=digest)
    reference=BASE/'R-Qwen/bin/worker.exe';assert sha(reference)=='73113940c38b24093a73d5bfefb46852af66b703c4923379fdd972cba603e249'
    competing=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip();assert not competing
    power_bytes=subprocess.check_output(['powercfg','/getactivescheme']);assert b'381b4222-f694-41f0-9685-ff5bb260df2e' in power_bytes
    power=power_bytes.decode('utf8',errors='replace').strip()
    resource=sample();resources(resource)
    unrelated=subprocess.check_output(['git','-C',str(REPO),'diff','ad9fb6846dd979c3a76d3c415c74fa9f86565f7d','--name-only','--','.',':(exclude)benchmarks/rtx_q8_transfer_20261109'],text=True).strip();assert not unrelated
    put(ROOT/'END_STATE.json',dict(passed=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),resource=resource,
        power_scheme=power,cooperative_mutex_released=True,competing_compute_apps=competing,groups=groups,statuses=statuses,
        original_ledger_unchanged=True,reference_sha256=sha(reference),models=models,source_closure_files_rehashed=len(closure['files']),
        changes_outside_new_task_directory=unrelated,new_model_requests=0,scope='Read-only end audit; hash checks are integrity evidence, not new numerical trials.'))
    print('End audit passed; original R/models/source bindings unchanged; no outstanding GPU worker',flush=True)

if __name__=='__main__':main()
