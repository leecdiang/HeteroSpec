"""Adversarial CPU-only review; creates only temporary local ledgers."""
from pathlib import Path
import hashlib,json,sys,tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'src'))
from windows_epoch import Ledger,ResourceRefusal,admit_live,KEYS

def main():
    plan=json.loads((ROOT/'RESOURCE_PLAN.json').read_bytes())
    results=[]
    receipt=dict(original_thread_status='VERIFIED_IDLE_OR_COMPLETED',original_thread_id='FIXTURE',
        thread_evidence='FIXTURE_ONLY_NOT_REAL',fresh=True,device_uuid=plan['device']['uuid'],
        visible_device_uuids=[plan['device']['uuid']],physical_index=plan['device']['physical_index'],
        foreign_compute_pids=[],legacy_lock_present=False,source_build_model_modules_verified=True,
        purpose='qualification',qualification_plan_frozen=True,independent_reference_available=True)
    try: results.append(dict(case='blocked_plan_with_self_reported_fresh_receipt',result=admit_live(plan,receipt,[])))
    except Exception as exc:results.append(dict(case='blocked_plan_with_self_reported_fresh_receipt',error=repr(exc)))
    with tempfile.TemporaryDirectory(dir=HERE) as folder:
        db=Ledger(Path(folder)/'ledger.sqlite',plan)
        admitted=dict(status='ADMITTED',device_uuid=plan['device']['uuid'])
        zero={k:0 for k in KEYS};one=dict(zero,model_requests=1)
        try:
            db.reserve('fractional-actual','failure_margin',one,admitted)
            db.finish('fractional-actual',dict(zero,model_requests=0.5),'FAILED')
            results.append(dict(case='fractional_actual_counter',result=db.snapshot()['attempts'][-1]))
        except Exception as exc:results.append(dict(case='fractional_actual_counter',error=repr(exc)))
        try:
            db.reserve('overrun','failure_margin',one,admitted)
            db.finish('overrun',dict(zero,model_requests=2),'FAILED')
            results.append(dict(case='overrun_actual_retention',result=db.snapshot()['attempts']))
        except Exception as exc:results.append(dict(case='overrun_actual_retention',error=repr(exc),ledger=db.snapshot()['attempts']))
        db.close()
    output=dict(scope='CPU_FIXTURE_ONLY_ZERO_GPU',source_sha256=hashlib.sha256((ROOT/'src/windows_epoch.py').read_bytes()).hexdigest(),
                resource_plan_sha256=hashlib.sha256((ROOT/'RESOURCE_PLAN.json').read_bytes()).hexdigest(),cases=results)
    dest=HERE/'RESOURCE_GAPS_INITIAL.json'
    with dest.open('x',encoding='utf8') as f:json.dump(output,f,indent=2)
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
