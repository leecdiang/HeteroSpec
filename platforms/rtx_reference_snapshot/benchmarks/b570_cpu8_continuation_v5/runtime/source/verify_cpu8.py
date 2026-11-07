"""Read-only CPU8 reconstruction. No Win32 backend import or evidence mutation."""
import sys,json,hashlib,datetime,math
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    b=Path(p).read_bytes();need(not b or b.endswith(b'\n'),'partial journal');return [json.loads(x) for x in b.splitlines()]
def load(p):return json.loads(Path(p).read_bytes())
def audit(root,run,manifest=None,tool_binding=None,completion=None,completion_sha256=None,relocated=False):
    root=Path(root).resolve();sys.path.insert(0,str(root/'src/rev2'))
    from guards import FrozenBaseline,wall_budget,revision_budget,ProgressGuard
    from source_guard import check_sources,actual_d0
    import native_gate_audit,cpu8_audit,integration_gates
    integration=integration_gates.check(root)
    f=load(root/'CAPABILITY_FREEZE.json');freeze_sha=h(root/'CAPABILITY_FREEZE.json');FrozenBaseline(root,freeze_sha).check();check_sources(root,f)
    from evidence_contract import manifest_check,watchdog_check,member
    if manifest:manifest_check(root,manifest)
    index=load(root/'D0_GATE_INDEX.json');need(index['all_required_passed'] is True,'native gates');native_gate_audit.check(root)
    review=load(root/'source/FINAL_REVIEW_BINDING.json');need(review['status']=='scoped-clean','adapter review not clean')
    for r in review['files']:need(h(member(root,r['path']))==r['sha256'],'review drift')
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
    delivered=False
    if completion:
        p=Path(completion).resolve();need(root not in p.parents and p!=root,'completion must be outside sealed root');need(completion_sha256 and h(p)==completion_sha256,'external completion hash');c=load(p);need(c['freeze_sha256']==freeze_sha and c['manifest_sha256']==h(root/manifest) and c['tool_binding_sha256']==h(root/tool_binding),'tail byte binding');need(tool_ok,'tool binding required')
        budget=wall_budget(load(root/'ACQUISITION.json'),f,regs,start,receipt,c);delivered=True
    return dict(outer_monitor=outer_monitor,tool_watchdog_binding=tool_result,integration_prerequisites=integration,status='CPU8_INTEGRATION_PASS' if delivered and tool_ok and manifest else 'PENDING_DELIVERY',cases=[dict(case_id=x,status='PASS') for x in actual],budget=budget,d0_actual=d0_actual,tool_exit_verified=tool_ok,restoration_verified=delivered,task_total_ledger='UNKNOWN',outer_os_lifetime_gaps=['watchdog own exit','observer own exit','shell and tool host','early preflight/portable roots'],scope='Eight CPU cases and their inner one-second supervision only; not old full confirmation, ENGINEERING_READY or paper evidence')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);p.add_argument('--manifest');p.add_argument('--tool-binding');p.add_argument('--completion-receipt');p.add_argument('--completion-sha256');p.add_argument('--relocated',action='store_true');a=p.parse_args()
    print(json.dumps(audit(a.root,a.run,a.manifest,a.tool_binding,a.completion_receipt,a.completion_sha256,a.relocated),sort_keys=True))
