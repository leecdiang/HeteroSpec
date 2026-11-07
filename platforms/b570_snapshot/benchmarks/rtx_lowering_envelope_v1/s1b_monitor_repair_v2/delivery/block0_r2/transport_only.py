"""One bounded CPU transport attempt,never repeats the stopped GPU experiment."""
import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from common import V,load,env
from bounded import State,Deadline,durable
from transport_lifecycle import TransportChild
from lifecycle import process_commit

def main():
    out=Path(__file__).resolve().parent;f=load(V/'F0.json');b=f['budget']['offline_CPU_delivery'];ledger=out/'cpu_ledger';prior=list(ledger.iterdir())+list((V/'delivery/cpu_ledger').iterdir());assert all((p/'CPU_ENDED.json').exists() for p in prior)
    wall=sum(load(p/'CPU_ENDED.json')['seconds'] for p in prior);spent=sum(load(p/'CPU_ENDED.json')['conservative_owned_seconds'] for p in prior);remaining=min(b['wall_seconds']-wall,(b['conservative_owned_seconds']-spent)/17);assert remaining>15
    d=ledger/f'{len(list(ledger.iterdir())):02d}-CPU-transport-only';d.mkdir();error=None
    class S(State):
        def snapshot(self,status):
            r=super().snapshot(status);r.update(run_id=f['run_id'],execution_id=f['execution_id'],conservative_owned_seconds=17*r['seconds'],process_bound_multiplier=17,experiment_retry=False);return r
    state=S(d,'CPU');w=TransportChild(f['console_helper'],f['CPU_transport_executables'])
    def monitor():state.peak_commit=max(state.peak_commit,process_commit());assert state.peak_commit<=b['controller_commit']
    deadline=Deadline(state,remaining,w.terminate,grace=5,monitor=monitor).start()
    cmd=[f['git']['path'],'-C',f['repository'],'-c','http.version=HTTP/1.1','push','origin',f['branch']]
    durable(d/'COMMAND.json',dict(command=cmd,CPU_only=True,only_existing_commit_transport=True,source_failure_preserved=True,no_GPU_reentry=True))
    try:w.run(cmd,d/'push',min(120,deadline.remaining()-5),env(''),b['job_commit'],deadline.guard)
    except BaseException as e:error=repr(e);state.minimum_stop(error);raise
    finally:w.terminate();state.reason=error;state.finish('COMPLETE' if error is None else 'CPU_DELIVERY_FAILED');deadline.close()
if __name__=='__main__':main()
