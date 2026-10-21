"""Read-only stopped-run reconstruction; never grants CPU8 admission or PASS."""
import sys,json,hashlib,importlib.util
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p):
    raw=Path(p).read_bytes();need(not raw or raw.endswith(b'\n'),'partial journal');return [json.loads(s) for s in raw.splitlines()]
def one(rs,e):
    found=[r for r in rs if r['event']==e];need(len(found)==1,'unique '+e);return found[0]
def reconstruct(root,manifest=None):
    root=Path(root).resolve()
    if manifest:
        m=json.loads((root/manifest).read_bytes());need(m['files'],'empty manifest')
        for r in m['files']:
            p=Path(r['path']);need(not p.is_absolute() and '..' not in p.parts and ':' not in str(p),'manifest path');f=root/p
            need(root in f.resolve().parents and not f.is_symlink() and not f.is_junction() and f.is_file(),'manifest member path')
            need(f.stat().st_size==r['bytes'] and h(f)==r['sha256'],'member bytes '+str(p))
    stop=json.loads((root/'STOP.json').read_bytes());need(stop['status']=='ENGINEERING_BLOCKED' and not (root/'CAPABILITY_FREEZE.json').exists(),'stopped/not frozen')
    last=json.loads((root/'development/REVISION_2_SOURCE.json').read_bytes())
    for r in last['files']:need(h(root/r['path'])==r['sha256'],'last source drift')
    sys.path.insert(0,str(root/'src/rev2'));import verify
    native=root/'development/healthy-r0-a1';cases=[verify.verify_case(native/('D0_'+c)) for c in ['C1','C2','C3']]
    sw=verify.rows(native/'WATCHDOG.jsonl');ss=verify.rows(native/'SUPERVISOR.jsonl');sup=verify.one(sw,'SUPERVISOR_CREATED_SUSPENDED')
    sampling=verify.sample_check(native,ss,sw,sup['pid']);need(verify.one(sw,'SUPERVISOR_OS_EXIT')['exit_code']==0 and verify.one(sw,'OUTER_JOB_EMPTY')['active_pids']==[],'healthy supervisor closure')
    freezes=[]
    for mode,reason in [('source_and_manifest','FREEZE_REPLACED'),('before_child_manifest','initial freeze digest mismatch'),('source_only','SOURCE_DRIFT'),('missing_pin','initial freeze digest required')]:
        rs=rows(root/'development/freeze-r1'/mode/'EVENTS.jsonl');op=one(rs,'ACTUAL_MUTATION');det=one(rs,'EXPECTED_DETECTOR');need(reason in det['reason'] and one(rs,'CASE_CLOSED')['status']=='PASS','freeze rejection')
        f=root/'development/freeze-r1'/mode/'sacrifice/CAPABILITY_FREEZE.json';need(h(f)==op['current_sha256'],'freeze actual bytes');freezes.append(dict(case=mode,status='PASS',reason=det['reason']))
    stderr=(root/'development/stall-r2-a1/SUPERVISOR.stderr.log').read_text()
    need("ModuleNotFoundError: No module named 'win'" in stderr,'stale setup actual error')
    hr=rows(root/'development/stall_harness_r2/EVENTS.jsonl');need(not any(r['event']=='WATCHDOG_ACTUALLY_SUSPENDED' for r in hr),'stale control unexpectedly reached')
    need(one(hr,'HARNESS_CLOSED')['rescue_fired'] is False and one(hr,'HARNESS_JOB_EMPTY')['active_pids']==[],'harness actual cleanup')
    osr=rows(root/'processes/native-stale-r2/OS_EVENTS.jsonl');c=[r for r in osr if r['event']=='PROCESS_CREATE'];e=[r for r in osr if r['event']=='PROCESS_CLOSED']
    need(len(c)==len(e)==3 and {(x['pid'],x['created_filetime']) for x in c}=={(x['pid'],x['created_filetime']) for x in e},'stale actual identity closure');need(one(osr,'JOB_EMPTY')['active_pids']==[],'stale observer Job')
    created={};closed={}
    for p in sorted((root/'processes').glob('*/OS_EVENTS.jsonl')):
        for r in rows(p):
            if r['event']=='PROCESS_CREATE':created[(r['pid'],r['created_filetime'])]=r
            if r['event']=='PROCESS_CLOSED':closed[(r['pid'],r['created_filetime'])]=r
    for r in sw:
        if r['event']=='SUPERVISOR_CREATED_SUSPENDED':created[(r['pid'],r['created_filetime'])]=r
        if r['event']=='SUPERVISOR_OS_EXIT':closed[(r['pid'],r['created_filetime'])]=dict(r,lifetime_seconds=(int(r['exit_filetime'])-int(r['created_filetime']))/1e7)
    for cid in ['C1','C2','C3']:
        for r in rows(native/('D0_'+cid)/'EVENTS.jsonl'):
            if r['event']=='PROCESS_CREATE':created[(r['pid'],r['created_filetime'])]=r
            if r['event']=='PROCESS_EXIT':closed[(r['pid'],r['created_filetime'])]=r
    missing=sorted(set(created)-set(closed));need(len(created)==31 and len(closed)==21 and len(missing)==10,'observed process reconstruction')
    cleanup=json.loads((root/'development/REVIEW1_CLEANUP_QUERY.json').read_bytes());need(cleanup['all_known_gone'] and all(r['state']=='NO_SUCH_PID' for r in cleanup['identities']),'later known-identity cleanup query')
    need(not (root/'delivery/REVIEW1_FINAL.json').exists(),'unexpected independent review report')
    plan=json.loads((root/'CPU8_PLAN.json').read_bytes());matrix=[]
    for r in plan['cases']:
        need(not (root/'legacy/runs'/r['run_id']).exists(),'formal case root unexpectedly exists')
        matrix.append(dict(case_id=r['id'],status='UNSTARTED'))
    need(len(matrix)==8,'eight cases')
    old=json.loads((root/'delivery/LEGACY_RAW_AUDIT.json').read_bytes());need(old['process_ledger_valid'] is False and 'unclosed processes in published prefix' in old['process_ledger_errors'],'old ledger failure retained')
    # Pure import tree only. The C# binary is evidence under compiled/, never imported.
    design=root/'legacy/repo/benchmarks/b570_supervision_fix_v2';need(not list((design/'host').glob('*.dll')) and not list((root/'src/rev2').glob('*.pyc')),'source-only tree')
    sys.path.insert(0,str(design/'host'));import raw_audit
    raw=raw_audit.audit(root/'legacy','AUDIT_INPUT_MANIFEST-stopped-final.json');need(raw==old,'unmodified old raw audit recomputation differs')
    return dict(status='ENGINEERING_BLOCKED',reasons=stop['reasons'],execution_freeze_sha256=None,formal_cases=matrix,formal_started=0,formal_unstarted=8,source_revisions_used=3,d0_native_raw_CASE_BEGIN=7,d0_failed_stale_harness_before_CASE_BEGIN=1,d0_attempt_charge=8,d0_reserved=15,native_healthy_cases=cases,native_healthy_sampling=sampling,native_freeze_cases=freezes,native_stale_gate='NOT_REACHED',stale_processes_actually_closed=3,watchdog_pause_observed=False,independent_review_attempts=1,independent_final_clean=False,observed_identities=31,actual_os_closures=21,missing_actual_os_exits=[dict(pid=p,created_filetime=t,exit_filetime=None,lifetime_seconds=None) for p,t in missing],covered_lifetime_seconds=sum(x['lifetime_seconds'] for x in closed.values()),whole_task_lifetime_seconds=None,old_raw_audit_process_ledger_valid=False,old_raw_audit_recomputed_exact=True,forbidden_counts=stop['forbidden'],scope='Stopped CPU engineering evidence reconstruction only; not CPU8_PASS, full ledger, ENGINEERING_READY or paper evidence')
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--manifest');p.add_argument('--output',required=True);a=p.parse_args()
    r=reconstruct(a.root,a.manifest);b=(json.dumps(r,sort_keys=True,indent=2)+'\n').encode()
    with Path(a.output).open('xb') as f:f.write(b)
    print(json.dumps(dict(status=r['status'],formal_started=r['formal_started'],formal_unstarted=r['formal_unstarted'],identities=r['observed_identities'],os_closures=r['actual_os_closures'],old_raw_audit_recomputed_exact=r['old_raw_audit_recomputed_exact']),sort_keys=True))
