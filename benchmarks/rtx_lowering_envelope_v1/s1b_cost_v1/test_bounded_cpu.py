"""Real CPU processes/files exercise stops; no CUDA, graph evaluation or query."""
import argparse,copy,json,os,sys,tempfile,time
from pathlib import Path
from common import V,load,save,env
from bounded import State,Deadline,ByteLedger,BudgetStop
from lifecycle import Child

def rejects(call):
    try:call()
    except (AssertionError,BudgetStop):return
    raise AssertionError('negative accepted')

def hanging_fixture(root,resource=False):
    root.mkdir();s=State(root,'NUMERICAL')
    def monitor():
        if resource:raise AssertionError('CPU fixture memory ceiling')
    Deadline(s,1.5,lambda:None,grace=.7,monitor=monitor).start()
    # Intentionally no finally: only the independent watcher can seal this run.
    time.sleep(20)

def main():
    p=argparse.ArgumentParser();p.add_argument('--hang',type=Path);p.add_argument('--resource',action='store_true');a=p.parse_args()
    if a.hang:return hanging_fixture(a.hang,a.resource)
    out=V/'cpu_tests/bounded';out.mkdir(parents=True,exist_ok=False);checks=[]
    s=State(out,'NORMAL');s.reserve_start(dict(id='slot0'),100,70);s.native_start(123);s.complete()
    rejects(lambda:s.reserve_start(dict(id='slot1'),69,70));s.minimum_stop(s.reason);s.finish('INCOMPLETE_STOPPED')
    r=load(out/'NORMAL_ENDED.json');assert r['completed']==1 and r['current'] is None and r['native_started']==1
    assert not list(out.glob('*FAILED*'));checks.append('completed slot survives next-start budget rejection')
    s=State(out,'FAIL');s.reserve_start(dict(id='slot0'),100,70);s.native_start(456);s.minimum_stop('CPU child failed');s.finish('INCOMPLETE_STOPPED')
    r=load(out/'FAIL_ENDED.json');assert r['completed']==0 and r['native_started']==1 and r['current']['state']=='NATIVE_STARTED';checks.append('started failure distinct from no-start')
    s=State(out,'READY');s.reserve_start(dict(id='slot0'),100,70);s.minimum_stop('readiness failed');s.finish('INCOMPLETE_STOPPED')
    assert load(out/'READY_ENDED.json')['native_started']==0;checks.append('readiness failure preserves zero native starts')
    rejects(lambda:s.reserve_start(dict(id='again'),100,70));checks.append('unsettled slot cannot be replaced')
    for label,mutation in [('changed',lambda f:f.write_bytes(b'xxxx')),('truncated',lambda f:f.write_bytes(b'x')),('deleted',lambda f:f.unlink()),('unregistered',lambda f:(f.parent/'intruder').write_bytes(b'x'))]:
        d=out/label;d.mkdir();b=ByteLedger(d,8*1024**2,d/'bytes.jsonl');b.reserve(4096);f=d/'evidence';f.write_bytes(b'abcd');b.adopt([f]);b.reconcile();mutation(f);rejects(b.reconcile);checks.append('real filesystem '+label+' rejected')
    d=out/'over';d.mkdir();b=ByteLedger(d,8*1024**2,d/'bytes.jsonl');rejects(lambda:b.reserve(8*1024**2));b.reserve(3);f=d/'too_big';f.write_bytes(b'abcd');rejects(lambda:b.adopt([f]));checks.extend(['capacity reservation rejection','producer overflow rejection'])
    # Real independently started CPU controllers reach hard deadline, preserve
    # fsynced stop/end receipts and exit nonzero without relying on finally.
    helper=load(Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/F0.json'))['console_helper']
    for label,resource in [('deadline',False),('monitor_failure',True)]:
        worker=Child(helper);root=out/label;error=None
        try:worker.run([sys.executable,'-B',__file__,'--hang',str(root),*(['--resource'] if resource else [])],out/(label+'_child'),8,env(''),256*1024**2)
        except Exception as exc:error=repr(exc)
        assert error and load(root/'NUMERICAL_MINIMUM_STOP.json')['reason'] and load(root/'NUMERICAL_ENDED.json')['status']=='HARD_TERMINATION_INCOMPLETE'
        assert load(out/(label+'_child.LIFETIME.json'))['exit_code']==70
        assert load(root/'NUMERICAL_ENDED.json')['seconds']<1.5;checks.append('actual fresh CPU '+label+' durable receipt before hard exit')
    save(V/'CPU_BOUNDED_TESTS.json',dict(status='PASS',checks=checks,real_CPU_deadline_processes=2,CUDA_loads=0,GPU_queries=0,graph_computes=0))
    print('PASS',len(checks),'bounded state/filesystem/real-process deadline controls')
if __name__=='__main__':main()
