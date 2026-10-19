"""CPU8 audit: original-root checks are mandatory; reconstruction never grants PASS."""
import sys,json,hashlib,datetime,math
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    b=Path(p).read_bytes();need(not b or b.endswith(b'\n'),'partial journal');return [json.loads(x) for x in b.splitlines()]
def load(p):return json.loads(Path(p).read_bytes())
def role_checks(root,relocated,mode):
    need(mode in ('live','reconstruct'),'verifier role')
    supplied=Path(root).absolute()
    root=supplied.resolve()
    campaign=load(root/'CAMPAIGN.json')
    original=Path(campaign['original_root']).absolute()
    is_original=root==original.resolve()
    need(not (relocated and is_original),'original root cannot claim relocation')
    need(mode!='live' or (is_original and not relocated),'live original root required')
    if not is_original:
        need(relocated and mode=='reconstruct','relocated reconstruction required')
        from campaign_budget import config
        config(root,read_only=True)
        return None
    # Inspect the supplied path before resolution, including junction ancestors.
    # A stable reconstruction requested on the original root still runs fresh gates.
    from identity_v6 import check as identity_check
    from campaign_budget import process_check,storage_check
    from budget_v6 import snapshot
    return dict(identity=identity_check(supplied),process=process_check(root),
                storage=storage_check(root),protected=snapshot(root,'delivery'))

def campaign_snapshot(root,relocated=False,mode="reconstruct"):
    current=role_checks(root,relocated,mode)
    from campaign_budget import process_check
    root=Path(root).resolve()
    seal=load(root/'CAMPAIGN_SEAL_CONTEXT.json')
    return dict(current=current if mode=='live' else None,role='RECONSTRUCTION_ONLY' if mode=='reconstruct' else 'LIVE_CHECKS_PERFORMED',process=process_check(root,now=datetime.datetime.fromisoformat(seal['observed_utc'].replace('Z','+00:00')),read_only=True),storage_at_seal=seal['storage'],scope='Stable raw reconstruction at recorded seal time; original root always checks current native identity and limits')

def audit(root,run,manifest=None,tool_binding=None,completion=None,completion_sha256=None,relocated=False,mode="reconstruct"):
    role_checks(root,relocated,mode)
    root=Path(root).resolve();sys.path.insert(0,str(root/'src/rev2'))
    from guards import FrozenBaseline,wall_budget,revision_budget,ProgressGuard
    from source_guard import check_sources,actual_d0
    import native_gate_audit,cpu8_audit,integration_gates
    integration=integration_gates.check(root)
    f=load(root/'CAPABILITY_FREEZE.json');freeze_sha=h(root/'CAPABILITY_FREEZE.json');FrozenBaseline(root,freeze_sha).check();check_sources(root,f)
    from evidence_contract import manifest_check,watchdog_check,member
    if manifest:manifest_check(root,manifest)
    index=load(root/'D0_GATE_INDEX.json');need(index['all_required_passed'] is True,'native gates');native_gate_audit.check(root)
    review=integration['source_review']
    need(review['status']=='SOURCE_REVIEW_EVIDENCE_CONSISTENT' and
         f.get('a_review_report_sha256')==review['report_sha256'] and
         f.get('a_external_approval_sha256')==h(root/'review/A_EXTERNAL_APPROVAL.json'),
         'A source review or external approval binding drift')
    legacy=root/'legacy';design=legacy/'repo/benchmarks/b570_supervision_fix_v2'
    sys.path.insert(0,str(design/'host'));import raw_audit
    final_manifest=load(root/'FINAL_RAW_AUDIT_BINDING.json');member(legacy,final_manifest['manifest_relative']);raw=raw_audit.audit(legacy,final_manifest['manifest_relative'])
    original=load(member(root,final_manifest['report_relative']));need(raw==original,'unchanged raw reconstruction mismatch')
    plan=load(root/'CPU8_PLAN.json');expected=[x['id'] for x in plan['cases']]
    actual=[]
    for s in plan['cases']:
        found=[r for r in raw['cases'] if r.get('run')==s['run_id'] and r.get('case_id')==s['id']]
        need(len(found)==1,'unique CPU8 raw case '+s['id']);cpu8_audit.qualify(root,raw,s['run_id'],s['id'],'FORMAL');actual.append(s['id'])
    need(actual==expected and len(actual)==8,'eight cases/order')
    folder=member(root,run,directory=True);wr=rows(folder/'WATCHDOG.jsonl');sr=rows(folder/'SUPERVISOR.jsonl')
    def one(rs,event):
        found=[r for r in rs if r['event']==event];need(len(found)==1,'unique '+event);return found[0]
    start=one(wr,'WATCHDOG_START');sup=one(sr,'SUPERVISOR_START');receipt=load(folder/'WATCHDOG_RECEIPT.json')
    watchdog_check(wr,receipt,sr)
    need(start['freeze_sha256']==sup['freeze_sha256']==freeze_sha,'initial pinned digest')
    need(receipt['outer_job_empty'] and receipt['owned_handles_closed'] and receipt['supervisor_exit_code']==0 and receipt['error'] is None,'outer closure')
    exits=one(wr,'SUPERVISOR_OS_EXIT');created=one(wr,'SUPERVISOR_CREATED_SUSPENDED');need(exits['created_filetime']==created['created_filetime'] and exits['exit_code']==0 and int(exits['exit_filetime'])>0,'actual supervisor OS exit')
    admissions=[r for r in sr if r['event']=='CPU8_CASE_ADMISSION'];need([r['case_id'] for r in admissions]==expected,'formal actual admission order')
    need(not any(r['event'] in ['CPU8_STOP','WATCHDOG_FAILURE','WATCHDOG_EXCEPTION','CLEANUP_ERROR'] for r in sr+wr),'actual outer failure')
    import cpu8_monitor
    outer_monitor=cpu8_monitor.check(folder)
    regs=load(root/'D0_RESERVATIONS.json');need(regs,'D0 reservation inventory');revision_budget(regs,__import__('continuation_policy').load(root));d0_actual=actual_d0(root,regs)
    budget=wall_budget(load(root/'ACQUISITION.json'),f,regs,start,receipt)
    tool_ok=False;tool_result=None
    if tool_binding:
        import tool_binding as terminal_binding
        tool_result=terminal_binding.check(root,run,freeze_sha,f,start,receipt,tool_binding);tool_ok=True
    campaign=campaign_snapshot(root,relocated,mode)
    delivered=False;delivery_proof=None
    if completion and mode=='live':
        from delivery_audit import external
        p=external(root,completion);need(completion_sha256 and h(p)==completion_sha256,'external completion hash');c=load(p);need(c['formal_run']==run,'completion run');need(c['freeze_sha256']==freeze_sha and c['manifest_sha256']==h(root/manifest) and c['tool_binding_sha256']==h(root/tool_binding),'tail byte binding');need(tool_ok,'tool binding required')
        from delivery_audit import check as delivery_check
        delivery_proof=delivery_check(root,c,manifest,tool_binding,lambda restored:audit(restored,run,manifest,tool_binding,relocated=True,mode="reconstruct"))
        budget=wall_budget(load(root/'ACQUISITION.json'),f,regs,start,receipt,c);delivered=True
    return dict(campaign_budget=campaign,delivery_proof=delivery_proof,outer_monitor=outer_monitor,tool_watchdog_binding=tool_result,integration_prerequisites=integration,status='RECONSTRUCTION_ONLY' if mode=='reconstruct' else 'CPU8_INTEGRATION_PASS' if delivered and tool_ok and manifest else 'CPU8_CASES_PASS_DELIVERY_PENDING',cases=[dict(case_id=x,status='PASS') for x in actual],budget=budget,d0_actual=d0_actual,tool_exit_verified=tool_ok,restoration_verified=delivered,task_total_ledger='UNKNOWN',outer_os_lifetime_gaps=['watchdog own exit','observer own exit','shell and tool host','early preflight/portable roots'],scope='Eight CPU cases and their inner one-second supervision only; not old full confirmation, ENGINEERING_READY or paper evidence')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);p.add_argument('--manifest');p.add_argument('--tool-binding');p.add_argument('--completion-receipt');p.add_argument('--completion-sha256');p.add_argument('--relocated',action='store_true');p.add_argument('--mode',choices=['live','reconstruct'],required=True);a=p.parse_args()
    print(json.dumps(audit(a.root,a.run,a.manifest,a.tool_binding,a.completion_receipt,a.completion_sha256,a.relocated,a.mode),sort_keys=True))
