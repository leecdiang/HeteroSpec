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
    for name in ['startup_manifest','startup_receipt','startup_intent','full_review_report']:
        confined(root,bind[name])
    receipt=load(root/bind['startup_receipt']);manifest=root/bind['startup_manifest']
    need(receipt['status']=='STARTUP_PREFLIGHT_PASS' and receipt['manifest_sha256']==sha(manifest),'real startup receipt')
    startup_preflight.authenticate(root,manifest,receipt['manifest_sha256'])
    intent=load(root/bind['startup_intent']);need(receipt['manifest_sha256'] in intent['request']['cmd'],'prospective startup pin')
    original=Path(load(root/'legacy/ROOT_BINDING.json')['task_root'])
    records=receipt['records'];need([r['entry'] for r in records]==list(startup_preflight.ENTRIES),'four native entries')
    for r in records:
        d=json.loads(r['stdout']);entry=original/'source'/r['entry']
        need(r['exit_code']==0 and d['status']=='ENTRY_IMPORT_READY' and Path(d['entry'])==entry,'actual entry outcome')
        need(d['modules']=={n:str(p) for n,p in entry_bootstrap.expected_modules(original,entry).items()},'entry module origins')
    smokes=[check_observer_smoke.check(root/'processes'/n,k,negative) for n,k,negative in [('review-smoke-ok','review',False),('case-smoke-limit','case',True),('review-smoke-limit','review',True)]]
    churn=bind['churn'];need(churn in ('review-churn','review-churn-r1'),'registered churn selection')
    churn_result=audit_identity_stream.check(root/'processes'/churn,churn=True)
    breakpoint_result=audit_identity_stream.check(root/'processes/review-breakpoint',breakpoint=True)
    review_process=bind['full_review_process'];need(__import__('continuation_policy').review_id(review_process,__import__('continuation_policy').load(root)),'registered review')
    review_result=audit_identity_stream.check(root/'processes'/review_process)
    review=load(root/bind['full_review_report']);need(review['status']=='scoped-clean' and review['findings']==[],'completed full review')
    need(review['candidate_manifest_sha256']==bind['candidate_manifest_sha256'],'review candidate pin')
    final=load(root/'source/FINAL_REVIEW_BINDING.json')
    need(final['report_sha256']==sha(root/bind['full_review_report']),'review report bytes')
    for row in final['files']:need(sha(confined(root,row['path']))==row['sha256'],'reviewed input drift')
    native=native_gate_audit.check(root)
    d0=d0_reconstruct(root,bind)
    return dict(status='ALL_INTEGRATION_GATES_RECONSTRUCTED',smokes=smokes,churn=churn_result,breakpoint=breakpoint_result,full_review_identity=review_result,native=native,d0_reconstructed=d0)
