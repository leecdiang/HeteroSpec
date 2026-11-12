"""Independent CPU recheck of review fixes. Synthetic READY plan is local only."""
from pathlib import Path
import copy,datetime,hashlib,json,sys,tempfile

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from windows_epoch import Ledger,ResourceRefusal,admit_live,KEYS
from admission import AdmissionError,NativeStateSpec,admit_descriptor,validate_bundle
from test_admission import identity,descriptor

def main():
    plan=json.loads((ROOT/'RESOURCE_PLAN.json').read_bytes()); results=[]
    def deny(name,kind,fn,expected):
        try:fn();results.append(dict(case=name,pass_check=False,unexpected='ACCEPTED'))
        except kind as exc:results.append(dict(case=name,pass_check=expected in str(exc),error=str(exc)))
    deny('blocked_plan_cannot_admit',ResourceRefusal,lambda:admit_live(plan,{},[]),'Frozen plan')
    synthetic=copy.deepcopy(plan);synthetic['gpu_admission']='READY'
    admit=dict(status='ADMITTED',device_uuid=plan['device']['uuid']);zero={k:0 for k in KEYS}
    with tempfile.TemporaryDirectory(dir=HERE) as folder:
        blocked=Ledger(Path(folder)/'blocked.sqlite',plan)
        deny('blocked_plan_cannot_reserve',ResourceRefusal,lambda:blocked.reserve('x','failure_margin',zero,admit),'Frozen plan')
        blocked.close()
        db=Ledger(Path(folder)/'synthetic.sqlite',synthetic)
        db.reserve('fraction','failure_margin',dict(zero,model_requests=1),admit)
        deny('fractional_actual_rejected',ResourceRefusal,lambda:db.finish('fraction',dict(zero,model_requests=0.5),'FAILED'),'Noninteger actual')
        deny('overrun_retained_before_refusal',ResourceRefusal,lambda:db.finish('fraction',dict(zero,model_requests=2),'FAILED'),'overrun persisted')
        snap=db.snapshot(); row=snap['attempts'][0]
        results.append(dict(case='overrun_actual_persisted_and_charged',pass_check=row['status']=='OVERRUN' and json.loads(row['actual'])['model_requests']==2 and snap['reserved']['model_requests']==2))
        deny('reservation_after_overrun_refused',ResourceRefusal,lambda:db.reserve('next','failure_margin',dict(zero,model_requests=1),admit),'overrun')
        db.close()
        receipt=dict(schema='heterospec.rtx-round1.evidence.v1',identity=identity(),vocab_size=151936,
            requested_rows=[0],vectors=[],states={},geometries={})
        deny('producer_cannot_hide_requested_rows',AdmissionError,
            lambda:validate_bundle(Path(folder),receipt,identity(),NativeStateSpec(1,2,2,256),{},list(range(8)),151936),'FULL_VECTOR')
        receipt['requested_rows']=list(range(8));receipt['vocab_size']=1
        deny('producer_cannot_shrink_vocabulary',AdmissionError,
            lambda:validate_bundle(Path(folder),receipt,identity(),NativeStateSpec(1,2,2,256),{},list(range(8)),151936),'FULL_VECTOR')
    deny('metadata_cannot_change_authorized_uuid',AdmissionError,lambda:admit_descriptor('B',descriptor('B'),'GPU-OTHER'),'PLACEMENT')
    output=dict(schema='heterospec.round1.cross-review-recheck.v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('src/windows_epoch.py','src/admission.py','RESOURCE_PLAN.json')},
        scope='CPU_FIXTURE_ONLY_ZERO_MODEL_ZERO_KERNEL',
        all_cases_pass=all(r['pass_check'] for r in results),cases=results,
        native_live_readiness='BLOCKED; no exclusive lock/worker monitor/window deadline adapter is claimed',
        synthetic_READY_plan_published_or_used_for_GPU=False)
    destination=HERE/('CROSS_REVIEW_RECHECK_O.json' if sys.flags.optimize else 'CROSS_REVIEW_RECHECK.json')
    with destination.open('x',encoding='utf8') as f:json.dump(output,f,indent=2)
    print(json.dumps(output,indent=2))
    if not output['all_cases_pass']:return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
