"""Read-only reconstruction of D0 native gates, not a Boolean receipt promotion."""
import json,sys,hashlib
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def rows(p):
    raw=Path(p).read_bytes();need(not raw or raw.endswith(b'\n'),'partial native gate journal');r=[json.loads(x) for x in raw.splitlines()];need(all(x['seq']==i+1 for i,x in enumerate(r)),'native gate sequence');return r
def one(rs,e):
    x=[r for r in rs if r['event']==e];need(len(x)==1,'unique '+e);return x[0]
def check(root):
    root=Path(root).resolve();sys.path.insert(0,str(root/'src/rev2'));import verify
    from operation_roles_v7 import native_gate_paths
    gates=native_gate_paths(root)
    healthy=gates['healthy'];sr=verify.rows(healthy/'SUPERVISOR.jsonl');wr=verify.rows(healthy/'WATCHDOG.jsonl')
    cases=[verify.verify_case(healthy/('D0_'+c)) for c in ['C1','C2','C3']]
    sup=verify.one(wr,'SUPERVISOR_CREATED_SUSPENDED');sample=verify.sample_check(healthy,sr,wr,sup['pid'])
    ended=verify.one(wr,'SUPERVISOR_OS_EXIT');need(ended['exit_code']==0 and int(ended['exit_filetime'])>0 and verify.one(wr,'OUTER_JOB_EMPTY')['active_pids']==[],'healthy actual closure')
    gate=gates['stall_harness'];g=rows(gate/'EVENTS.jsonl');susp=one(g,'WATCHDOG_ACTUALLY_SUSPENDED');readable=one(g,'WATCHDOG_STILL_IDENTITY_RSS_READABLE')
    need(susp['pid']==readable['pid'] and susp['created_filetime']==readable['created_filetime'] and susp['alive'] and readable['alive'] and susp['rss_bytes']>0 and readable['rss_bytes']>0,'real stalled identity/RSS')
    need(not any(x['event']=='INDEPENDENT_RESCUE_FIRED' for x in g) and one(g,'HARNESS_CLOSED')['rescue_fired'] is False,'rescue cannot qualify supervisor cleanup')
    folder=gates['stall'];rs=rows(folder/'SUPERVISOR.jsonl');bad=one(rs,'SUPERVISOR_FAILURE')
    need('WATCHDOG_PROGRESS_STALE' in bad['error'] and 5_000_000_000<bad['at_ns']-susp['progress']['progress_ns']<6_000_000_000,'stale actual detector age')
    need(not (folder/'MUST_NOT_START').exists(),'stale next case was admitted');verify.verify_case(folder/'D0_C1')
    se=one(g,'SUPERVISOR_OS_EXIT_WHILE_WATCHDOG_SUSPENDED');need(se['exit_code']==1 and int(se['exit_filetime'])>0,'stale actual supervisor exit')
    need(one(g,'HARNESS_JOB_EMPTY')['active_pids']==[] and one(g,'WATCHDOG_OS_EXIT')['exit_code']==1,'stale owned closure')
    group=gates['freeze'];results=[]
    for mode,reason in [('source_and_manifest','FREEZE_REPLACED'),('before_child_manifest','initial freeze digest mismatch'),('source_only','SOURCE_DRIFT'),('missing_pin','initial freeze digest required')]:
        rs=rows(group/mode/'EVENTS.jsonl');one(rs,'CASE_BEGIN');op=one(rs,'ACTUAL_MUTATION');d=one(rs,'EXPECTED_DETECTOR');need(reason in d['reason'] and one(rs,'CASE_CLOSED')['status']=='PASS','freeze detector evidence')
        f=group/mode/'sacrifice/CAPABILITY_FREEZE.json';raw=f.read_bytes();after=hashlib.sha256(raw).hexdigest()
        need(op['current_sha256']==after,'mutated bytes changed')
        if mode in ['source_and_manifest','before_child_manifest']:need(op['initial_sha256']!=after,'actual manifest replacement absent')
        if mode in ['source_and_manifest','source_only']:
            p=group/mode/'sacrifice/src/rev2/actor.py';need(p.read_bytes()==(root/'src/rev2/actor.py').read_bytes()+b'\n# sacrificial mutation\n','actual source mutation')
        results.append(dict(case=mode,reason=d['reason']))
    return dict(status='NATIVE_GATES_RECONSTRUCTED',healthy_cases=cases,healthy_sampling=sample,stale_detection_age_ns=bad['at_ns']-susp['progress']['progress_ns'],freeze_cases=results,gate_booleans_are_not_the_only_source=True)
