"""Read-only blocked-task evidence reconstruction. Never grants CPU8 or full-task acceptance."""
import sys,json,hashlib,datetime
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(ROOT/'source'),str(ROOT/'src/rev2'),str(ROOT/'legacy/repo/benchmarks/b570_supervision_fix_v2/host')]
import raw_audit,cpu8_audit,source_guard,native_gate_audit,integration_gates,startup_preflight,audit_identity_stream,check_observer_smoke
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
closing=load(ROOT/'CLOSING_STATE.json');need(closing['status']=='ENGINEERING_BLOCKED' and closing['formal_case_attempts']==0 and closing['execution_freeze'] is None,'true stop')
need(not (ROOT/'CAPABILITY_FREEZE.json').exists(),'unexpected execution freeze')
matrix=load(ROOT/'CPU8_MATRIX.json');need(len(matrix['cases'])==8 and all(x['status']=='UNSTARTED' for x in matrix['cases']),'eight unstarted')
need(not any((ROOT/'legacy/runs'/x['run_id']).exists() for x in matrix['cases']),'formal run exists')
m=ROOT/'ENTRY_SOURCE_MANIFEST.review2-final.json';startup_preflight.authenticate(ROOT,m,sha(m))
regs=load(ROOT/'D0_RESERVATIONS.json');d0=source_guard.actual_d0(ROOT,regs);need(d0['actual']==18,'D0 mismatch')
b=load(ROOT/'CLOSING_RAW_BINDING.json');raw=raw_audit.audit(ROOT/'legacy',b['manifest_relative'])
need(raw==load(ROOT/b['raw_report_relative']),'old raw output mismatch')
snap=ROOT/'D0_EVIDENCE_SNAPSHOT';sm= snap/'legacy/AUDIT_INPUT_MANIFEST-normal-readonly-final.json'
db=dict(d0_snapshot='D0_EVIDENCE_SNAPSHOT',d0_manifest=sm.name,d0_manifest_sha256=sha(sm),d0_expected_sha256=sha(snap/'EXPECTED.json'))
smokes=integration_gates.d0_reconstruct(ROOT,db)
native=native_gate_audit.check(ROOT)
identity={};observed={};closed={};rejections={}
for folder in sorted((ROOT/'processes').iterdir()):
    f=folder/'OS_EVENTS.jsonl'
    if not f.is_file():continue
    blob=f.read_bytes();need(blob.endswith(b'\n'),'partial command OS stream')
    rs=[json.loads(s) for s in blob.splitlines()]
    need(all(x['seq']==i+1 for i,x in enumerate(rs)),'OS sequence')
    cr={(x['pid'],x['created_filetime']):x for x in rs if x['event']=='PROCESS_CREATE'}
    cl={(x['pid'],x['created_filetime']):x for x in rs if x['event']=='PROCESS_CLOSED'}
    need(cr and set(cr)==set(cl),'recorded command identities not closed')
    for k,x in cl.items():
        need(int(x['exit_filetime'])>int(k[1]),'actual OS exit absent')
        need(abs((int(x['exit_filetime'])-int(k[1]))/1e7-x['lifetime_seconds'])<1e-6,'OS lifetime')
        need(k not in closed or closed[k]==x['exit_filetime'],'conflicting identity')
        observed[k]=cr[k];closed[k]=x['exit_filetime']
    try:identity[folder.name]=audit_identity_stream.check(folder,churn=folder.name=='review-churn-r1',breakpoint=folder.name=='review-breakpoint')
    except (ValueError,OSError,KeyError) as e:identity[folder.name]=dict(status='REJECTED_RETAINED',reason=str(e),closed_recorded_identities=len(cl))
reviews=[];review_seconds=0
for name,report in [('full-review','FINAL_REVIEW.json'),('full-review-2','FINAL_REVIEW_2.json')]:
    audit_identity_stream.check(ROOT/'processes'/name)
    r=load(ROOT/'review'/report);receipt=load(ROOT/'processes'/name/'RECEIPT.json')
    elapsed=(receipt['end_ns']-receipt['begin_ns'])/1e9;need(0<elapsed<=900,'review deadline')
    reviews.append(dict(report=report,status=r['status'],findings=r['findings'],candidate_manifest_sha256=r['candidate_manifest_sha256'],wall_seconds=elapsed,closed_identities=receipt['closed']))
    review_seconds+=elapsed
need(review_seconds<=1800 and len(reviews)==2 and reviews[-1]['status']=='findings','review ceiling/outcome')
three=[check_observer_smoke.check(ROOT/'processes'/n,k,neg) for n,k,neg in [('review-smoke-ok','review',False),('case-smoke-limit','case',True),('review-smoke-limit','review',True)]]
origin=datetime.datetime.fromisoformat(load(ROOT/'ACQUISITION.json')['first_preparation_utc'].replace('Z','+00:00'))
stop=datetime.datetime.fromisoformat(closing['stopped_utc'].replace('Z','+00:00'))
elapsed=(stop-origin).total_seconds();need(0<=elapsed<=5400,'D0 wall limit')
lifetime=sum(int(v)-int(k[1]) for k,v in closed.items())/1e7
need(len(observed)<=3000 and lifetime<=21600,'covered process budget')
result=dict(status='ENGINEERING_BLOCKED',reason='ADAPTER_REVIEW_BLOCKED',formal_freeze=None,formal_matrix=matrix['cases'],formal_started=0,
 source_manifest_sha256=sha(m),d0=d0,d0_raw_qualifications=smokes,native_gates=native,observer_smokes=three,command_identity_checks=identity,
 reviews=reviews,review_wall_seconds=review_seconds,engineering_wall_at_stop_seconds=elapsed,
 observed_command_tree_identities=len(observed),observed_closed_identities=len(closed),observed_lifetime_seconds=lifetime,
 task_total_processes='UNKNOWN',task_total_lifetime_seconds='UNKNOWN',outer_gaps=['observer own exit','watchdog own exit','shell/tool host','preflight/portable and delivery roots'],
 legacy_raw_sha256=sha(ROOT/b['raw_report_relative']),legacy_raw_process_ledger_valid=raw['process_ledger_valid'],
 legacy_raw_case_statuses=[dict(run=x.get('run'),case_id=x.get('case_id'),status=x['status']) for x in raw['cases']],
 forbidden=closing['forbidden'],scope='Authenticated retained CPU engineering evidence and bounded D0 gates; no final clean review, execution freeze, formal CPU8, full task accounting, ENGINEERING_READY or paper result')
text=json.dumps(result,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n'
if len(sys.argv)>2:
    with Path(sys.argv[2]).open('x',encoding='utf8',newline='\n') as out:out.write(text)
else:print(text,end='')
