"""Read-only integration prerequisite reconstruction from authenticated raw evidence."""
import json,hashlib,sys
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def confined(root,rel):
    p=Path(rel);need(not p.is_absolute() and '..' not in p.parts and ':' not in str(p),'gate path')
    q=root/p;need(not any(x.is_symlink() or x.is_junction() for x in [q,*q.parents] if x!=root.parent),'gate alias');return q
def d0_reconstruct(root,bind):
    root=Path(root);snapshot=confined(root,bind['d0_snapshot'])
    manifest=confined(snapshot/'legacy',bind['d0_manifest'])
    expected_path=confined(snapshot,'EXPECTED.json')
    need(sha(manifest)==bind['d0_manifest_sha256'] and sha(expected_path)==bind['d0_expected_sha256'],'D0 snapshot binding')
    m=load(manifest)
    for row in m['members']:
        p=confined(snapshot/'legacy',row['path'])
        need(p.is_file() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'D0 raw member drift')
    sys.path[:0]=[str(root/'source'),str(root/'src/rev2'),str(root/'legacy/repo/benchmarks/b570_supervision_fix_v2/host')]
    import raw_audit,cpu8_audit
    raw=raw_audit.audit(snapshot/'legacy',bind['d0_manifest'])
    expected=load(expected_path)
    raw_bytes=(json.dumps(raw,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
    need(hashlib.sha256(raw_bytes).hexdigest()==expected['raw_sha256'],'D0 original raw recomputation')
    plan=load(root/'D0_BRIDGE_PLAN.json')
    need(set(plan)=={'normal','journal'} and plan['normal']['case_id']=='normal_single' and plan['journal']['case_id']=='journal_write_failure','two D0 bridge cases')
    outcomes={}
    for key,item in plan.items():
        result=cpu8_audit.qualify(snapshot,raw,item['run_id'],item['case_id'],'D0')
        need(result==expected['results'][key] and result['status']=='D0_BRIDGE_SMOKE_PASS','D0 native raw qualification')
        saved=load(root/item['report_dir']/(item['run_id']+'.qualification.json'))
        need(all(saved.get(k)==v for k,v in result.items()),'D0 summary differs from actual raw')
        outcomes[key]=result
    return outcomes
def check(root):
    root=Path(root).resolve();sys.path[:0]=[str(root/'source'),str(root/'src/rev2')]
    import startup_preflight,check_observer_smoke,audit_identity_stream,native_gate_audit,entry_bootstrap
    bind=load(root/'INTEGRATION_GATE_BINDING.json')
    campaign=load(root/'CAMPAIGN.json')
    need(bind.get('schema')=='B570_C_NATIVE_BINDING_V2' and bind.get('task_uuid')==campaign.get('task_uuid') and campaign.get('task_uuid'),'current C task binding')
    for name in ['startup_manifest','startup_receipt','startup_intent','source_review_report']:
        confined(root,bind[name])
    receipt=load(root/bind['startup_receipt']);manifest=root/bind['startup_manifest']
    need(receipt['status']=='STARTUP_PREFLIGHT_PASS' and receipt['manifest_sha256']==sha(manifest),'real startup receipt')
    startup_preflight.authenticate(root,manifest,receipt['manifest_sha256'])
    intent=load(root/bind['startup_intent']);operation=load(root/bind['startup_operation']);need(intent['operation_sha256']==sha(root/bind['startup_operation']),'prospective startup operation pin');need('--manifest-sha256' in operation['argv'] and operation['argv'][operation['argv'].index('--manifest-sha256')+1]==receipt['manifest_sha256'],'prospective startup pin')
    original=Path(load(root/'legacy/ROOT_BINDING.json')['task_root'])
    records=receipt['records'];need([r['entry'] for r in records]==list(startup_preflight.ENTRIES),'four native entries')
    for r in records:
        d=json.loads(r['stdout']);entry=original/'source'/r['entry']
        need(r['exit_code']==0 and d['status']=='ENTRY_IMPORT_READY' and Path(d['entry'])==entry,'actual entry outcome')
        need(d['modules']=={n:str(p) for n,p in entry_bootstrap.expected_modules(original,entry).items()},'entry module origins')
    # Native observer/churn/interrupt requirements remain mandatory, but names are
    # explicitly frozen by C rather than inherited from a source-review task.
    smoke_rows=bind['observer_smokes']
    need(type(smoke_rows) is list and len(smoke_rows)==3,'exact observer smoke roles')
    smokes=[check_observer_smoke.check(confined(root,item['path']),item['kind'],item['negative']) for item in smoke_rows]
    churn_result=audit_identity_stream.check(confined(root,bind['churn']),churn=True)
    breakpoint_result=audit_identity_stream.check(confined(root,bind['breakpoint']),breakpoint=True)
    # A's reviewer process is NOT part of the Windows native integration tree.
    from finalize_review_v6 import verify as verify_source_review
    review_result=verify_source_review(root)
    need(sha(root/bind['source_review_report'])==review_result['report_sha256'], 'exact A review report')
    need(review_result['candidate_manifest_sha256']==bind['candidate_manifest_sha256'], 'A candidate pin')
    approval=load(confined(root,bind['a_external_approval_record']))
    need(approval.get('status')=='SOURCE_REVIEW_PASS' and approval.get('review_report_sha256')==review_result['report_sha256']
         and approval.get('candidate_manifest_sha256')==review_result['candidate_manifest_sha256'], 'separate A source approval required')
    # Approval origin is checked externally before C admission; these fields only bind its bytes.
    need(approval.get('external_provider_reference') and approval.get('independent_reviewer_identity'), 'independent A provenance required')
    from source_review_origin_v7 import check as review_origin_check
    review_origin=review_origin_check(root,approval,review_result)
    native=native_gate_audit.check(root)
    from engineering_gates_v6 import check as engineering_check
    engineering=engineering_check(root)
    d0=d0_reconstruct(root,bind)
    return dict(status='ALL_INTEGRATION_GATES_RECONSTRUCTED',smokes=smokes,churn=churn_result,breakpoint=breakpoint_result,source_review=review_result,source_review_origin=review_origin,source_review_provider_authentication='REQUIRES_INDEPENDENT_PLATFORM_AUTHENTICATION',native=native,engineering=engineering,d0_reconstructed=d0)
