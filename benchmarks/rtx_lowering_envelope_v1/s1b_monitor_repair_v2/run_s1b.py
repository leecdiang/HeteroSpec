"""Sole future GPU entry. Separate exact author approval for census/each block.
Trace cannot launch while collector is unavailable. No retry or auto-next-stage.
"""
import argparse,hashlib,os,shutil,time,json
import exact_binding
from pathlib import Path
from common import V,RUN,load,save,sha,wire,env
from bounded import Deadline,ByteLedger,durable
from identified_state import IdentifiedState
from strict_lifecycle import StrictChild
from resource_guard import ResourceGuard
from monitor_contract import identities,MAX_MONITOR_INTERVAL_NS
from lifecycle import Child,process_commit
from admission import owned_conflicts,module_inventory,readiness
import identity as I
import audit

def check(f,p):
    assert f['run_id']==p['run_id']==RUN and f['stage']=='S1B_COST_V1' and not f.get('CPU_fixture_only')
    identities(f,p)
    identities(f,f['monitor_contract'])
    for s in p['clean_slots']+p['trace_slots']:identities(f,s)
    assert f['monitor_contract']['max_monitor_interval_ns']==MAX_MONITOR_INTERVAL_NS and f['monitor_contract']['CPU_fixture_only'] is False
    assert f['plan_sha256']==sha(V/'PLAN.json') and len(p['clean_slots'])==216 and len(p['trace_slots'])==72
    assert sum(s['graph_computes'] for s in p['clean_slots']+p['trace_slots'])==2088
    assert f['budget']==load(V/'BUDGET.json')
    for x in f['files']:assert sha(x['path'])==x['sha256'],x['path']

def authority(stage,f,approval):
    expected='S1B_CENSUS_ONLY' if stage=='census' else 'S1B_CLEAN_BLOCK_'+stage[-1]+'_EXACT'
    assert approval['stage']==expected and approval['run_id']==RUN and approval['F0_sha256']==sha(V/'F0.json')
    identities(f,approval)
    assert stage=='clean0','repair registration admits only Block0 review'
    assert approval['author_message'] and hashlib.sha256(approval['author_message'].encode()).hexdigest()==approval['author_message_sha256']
    assert approval['clean_first_trace_deferred_amendment_accepted'] is True
    auth=load(V/'AUTHENTICATED_F0.json');assert auth['authenticated_remote_bytes'] and auth['sha256']==sha(V/'F0.json')
    assert (V/'REMOTE_F0_BYTES.json').read_bytes()==(V/'F0.json').read_bytes()
    exact_binding.admit(f,approval,V/'F0.json')

def main():
    begin=time.perf_counter();p=argparse.ArgumentParser();p.add_argument('--stage',choices=['clean0']);p.add_argument('--approval',type=Path);p.add_argument('--dry-check',action='store_true');a=p.parse_args()
    f=load(V/'F0.json');plan=load(V/'PLAN.json')
    if a.dry_check:check(f,plan);print('CPU identity only; no stage/device action');return
    assert a.stage and a.approval,'separate human approval required'
    assert a.stage!='trace','PROFILE_UNAVAILABLE: all72 trace coordinates retained, none admitted'
    approval=load(a.approval);authority(a.stage,f,approval);root=Path(f['execution_root']);stage=a.stage.upper();budget=f['budget']['stages'][a.stage];limits=f['budget']['limits']
    ledger=V/'execution_ledger';ledger.mkdir(exist_ok=True);assert not (ledger/(stage+'_CONTROLLER_STARTED.json')).exists()
    # The exact raw artifact below is the SAME artifact pinned by F0/approval.
    # No JSON parse/normalization participates in the byte admission decision.
    census_bytes,decision_bytes=exact_binding.admit(f,approval,V/'F0.json')
    proof=load(V/'CENSUS_EXACT_AUTHENTICATED.json')
    assert proof['authenticated_remote_bytes'] and proof['execution_bound_sha256']==f['execution_bound_census']['sha256']
    expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_EXPECTED.json')}
    assert audit.census(json.loads(census_bytes),plan,expected)==json.loads(decision_bytes)
    assert not root.exists(),'independent execution root must be absent;no resume'
    assert shutil.disk_usage(root.anchor).free>=limits['disk_free_before'];root.mkdir(exist_ok=False)
    state=IdentifiedState(root,stage,f['run_id'],f['execution_id']);state.start=begin;receipt=dict(pid=os.getpid(),epoch=time.time(),approval=approval,run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'))
    durable(ledger/(stage+'_CONTROLLER_STARTED.json'),receipt);durable(root/(stage+'_CONTROLLER_STARTED.json'),receipt);durable(root/(stage+'_ACTIVE.lock'),dict(pid=os.getpid(),never_restart=True))
    worker=StrictChild(f['console_helper'],f['monitor_contract']);error=None;current=None;qualified=[]
    def monitor():
        state.peak_commit=max(state.peak_commit,process_commit());assert state.peak_commit<=limits['controller_commit']
        assert shutil.disk_usage(root.anchor).free>=limits['disk_free_during']
    deadline=Deadline(state,min(budget['wall_seconds'],budget['owned_seconds']/5),worker.terminate,grace=5,monitor=monitor).start();account=ByteLedger(root,limits['raw_bytes'],root/(stage+'_BYTES.jsonl'))
    runtime_guard=ResourceGuard(monitor,deadline.guard)
    def settle(producer=None,initial=False):
        fresh=[p for p in (root/'cas').glob('*.bin') if p.relative_to(root).as_posix() not in account.files]
        for p in fresh:assert p.stem==sha(p)
        paths=([p for p in producer.rglob('*') if p.is_file()] if producer else [])+fresh+[p for p in root.iterdir() if p.is_file()]
        if initial:paths=[p for p in root.rglob('*') if p.is_file()]
        account.adopt(paths);state.accounting=dict(known_files=len(account.files),reconciliation_seconds=account.scan_seconds)
    try:
        check(f,plan);owned_conflicts(f);deadline.guard()
        account.reserve(limits['raw_bytes']-8*1024**2)
        if a.stage=='clean0':
            (root/'cas').mkdir()
            for row in load(V/'CAS_INDEX.json'):
                deadline.guard();assert sha(row['path'])==row['sha256'];shutil.copyfile(row['path'],root/'cas'/(row['sha256']+'.bin'))
        settle(initial=True);account.reconcile()
        expected={(r['descriptor_id'],r['layout']):r for r in load(V/'CPU_EXPECTED.json')}
        slots=[plan['census_job']] if a.stage=='census' else [s for s in plan['clean_slots'] if s['block']==int(a.stage[-1])]
        for s in slots:
            deadline.guard();state.reserve_start(s,deadline.remaining(),260 if a.stage=='census' else 80)
            current=root/'census' if a.stage=='census' else root/'clean'/f'{s["index"]:03d}';current.mkdir(parents=True,exist_ok=False);account.reserve(limits['per_host_reserve'])
            owned_conflicts(f);save(current/'SLOT.json',s);readiness(worker,current,f,runtime_guard,on_start=lambda pid:setattr(state,'active_pid',pid))
            job=wire(s,V/'F0.json');save(current/'JOB.json',job);host=f['hosts']['clean']['path'];mode='--gpu-census' if a.stage=='census' else '--gpu-clean'
            save(current/'BEFORE_START.json',dict(slot=s['id'],graph_cap=s['graph_computes'],warmups=s['warmups']))
            worker.run([host,mode,str(current/'JOB.json'),s['native_output']],current/'native',240 if a.stage=='census' else 60,env(f['runtime_directory']),limits['native_commit'],runtime_guard,on_start=state.native_start)
            n=current/'native';r=load(n/('CENSUS.json' if a.stage=='census' else 'RECORD.json'));inventory=module_inventory(r['modules'],f);save(current/'MODULE_FILES.json',inventory)
            if a.stage=='census':
                I.process_identity(current,'native',dict(f,executable=host),240);I.process_identity(current,'readiness',f);I.verify_modules(n,r,dict(f,executable=host,executable_sha256=f['hosts']['clean']['sha256']),inventory);decision=audit.census(r,plan,expected);save(root/'CENSUS_DECISION.json',decision)
            else:
                q=audit.inspect(s,current,f,plan,expected[s['descriptor'],s['layout']],root)
                q.update(run_id=f['run_id'],execution_id=f['execution_id'])
                assert q['process_identity'] not in [r['process_identity'] for r in qualified];qualified.append(q);save(current/'AUDIT.json',q)
            assert sum(p.stat().st_size for p in current.rglob('*') if p.is_file())<=(limits['census_nonCAS'] if a.stage=='census' else limits['per_host_nonCAS']);save(current/'COMPLETED.json',dict(run_id=f['run_id'],execution_id=f['execution_id'],slot=s['id'],qualified=True));finished=current;state.complete();current=None;settle(finished)
            if state.completed%18==0:account.reconcile()
        if a.stage!='census':
            assert len(qualified)==72 and sum(r['q']==1 for r in qualified)==18
            save(root/(stage+'_QUALIFIED.json'),dict(run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'),qualified=72,all_clean_graph_warmups_and_outputs_match_PR116=True,all_q1_controls=True))
        account.reserve(1024**2);settle();account.reconcile();deadline.guard()
    except BaseException as exc:
        error=repr(exc);state.minimum_stop(error);worker.terminate()
        if current is not None and not (current/'COMPLETED.json').exists():durable(current/'FAILED.json',dict(run_id=f['run_id'],execution_id=f['execution_id'],reason=error,state=state.current,no_retry=True))
    finally:worker.terminate();state.finish('COMPLETE' if error is None else 'INCOMPLETE_STOPPED');deadline.close()
    if error:raise RuntimeError(error)
    print('Stage ended;separate CPU seal/remote authentication and next human approval required.')
if __name__=='__main__':main()
