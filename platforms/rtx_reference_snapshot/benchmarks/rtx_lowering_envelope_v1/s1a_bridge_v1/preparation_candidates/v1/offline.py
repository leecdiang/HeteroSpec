"""Bounded CPU delivery entry. No native/GPU/query action is available."""
import argparse,sys,time
from pathlib import Path
from common import V,load,save,sha,env
from lifecycle import Child,process_commit
from bounded import State,Deadline,durable

def main():
    begin=time.perf_counter()
    p=argparse.ArgumentParser();p.add_argument('--action',choices=('seal-census','census-readback','analyze','package','readback','restore','analyze-fresh'),required=True);p.add_argument('--commit');a=p.parse_args()
    f0=load(V/'F0.json');b=f0['budget']['offline_CPU_delivery'];root=Path(f0['execution_root']);out=V/'closure';out.mkdir(exist_ok=True)
    attempts=out/'ledger';attempts.mkdir(exist_ok=True)
    for d in attempts.iterdir():assert (d/'CPU_ENDED.json').exists(),'unresolved CPU delivery attempt: retain and review; no reset'
    spent=sum(load(d/'CPU_ENDED.json')['conservative_owned_seconds'] for d in attempts.iterdir())
    remaining=(b['conservative_owned_seconds']-spent)/3;assert remaining>15
    d=attempts/('%02d-%s'%(len(list(attempts.iterdir())),a.action));d.mkdir();s=State(d,'CPU');s.start=begin
    def monitor():
        commit=process_commit();s.peak_commit=max(s.peak_commit,commit)
        assert commit<=512*1024**2,'CPU delivery controller commit ceiling'
    worker=Child(f0['console_helper']);deadline=Deadline(s,remaining,worker.terminate,grace=5,monitor=monitor).start();error=None
    fresh=Path(f0['fresh_restore_root']);py=f0['python']['path'];archive=out/'RAW_BRIDGE.zip';readback=out/'readback.stdout'
    commands=dict(**{'seal-census':[py,'-B',str(V/'seal_census.py')]},analyze=[py,'-B',str(V/'analyzer.py'),'--root',str(root),'--output',str(out/'ANALYSIS.json')],
        package=[py,'-B',str(V/'evidence.py'),'--action','package','--root',str(root),'--output',str(archive)],
        restore=[py,'-B',str(V/'evidence.py'),'--action','restore','--archive',str(readback),'--output',str(fresh)],
        **{'analyze-fresh':[py,'-B',str(fresh/'frozen/analyzer.py'),'--root',str(fresh/'raw'),'--output',str(out/'FRESH_ANALYSIS.json')]})
    try:
        if a.action=='census-readback':
            assert a.commit and len(a.commit)==40 and all(x in '0123456789abcdef' for x in a.commit)
            for name in ('CENSUS.json','DECISION.json'):
                endpoint='repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v1/census_delivery/'+name+'?ref='+a.commit
                prefix=d/name
                worker.run([f0['gh']['path'],'api',endpoint,'--header','Accept: application/vnd.github.raw+json'],prefix,min(60,deadline.remaining()-5),env(''),b['process_commit_bytes'],deadline.guard,log_cap=16*1024**2)
                assert sha(prefix.with_suffix('.stdout'))==sha(V/'census_delivery'/name)
            durable(root/'CENSUS_AUTHENTICATED.json',dict(commit=a.commit,authenticated_remote_bytes=True,F0_sha256=sha(V/'F0.json'),census_sha256=sha(V/'census_delivery/CENSUS.json'),decision_sha256=sha(V/'census_delivery/DECISION.json')))
            return
        if a.action=='readback':
            assert a.commit and len(a.commit)==40 and all(x in '0123456789abcdef' for x in a.commit)
            assert not readback.exists() and archive.exists()
            endpoint='repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v1/closure/RAW_BRIDGE.zip?ref='+a.commit
            command=[f0['gh']['path'],'api',endpoint,'--header','Accept: application/vnd.github.raw+json'];prefix=out/'readback';cap=f0['budget']['storage']['archive_upper_bound_bytes']
        else:command=commands[a.action];prefix=d/'worker';cap=32768
        assert (root/'NUMERICAL_ENDED.json').exists() or (root/'CENSUS_ENDED.json').exists(),'sealed stage required'
        durable(d/'COMMAND.json',dict(command=command,prior_conservative_owned_seconds=spent,CPU_only=True))
        worker.run(command,prefix,min(300,remaining-5),env(''),b['process_commit_bytes'],deadline.guard,log_cap=cap)
        if a.action=='readback':assert sha(readback)==sha(archive);durable(out/'RAW_REMOTE_AUTHENTICATED.json',dict(commit=a.commit,sha256=sha(archive),authenticated_remote_bytes=True))
        if a.action=='analyze-fresh':assert (out/'ANALYSIS.json').read_bytes()==(out/'FRESH_ANALYSIS.json').read_bytes()
    except BaseException as exc:error=repr(exc);s.minimum_stop(error);worker.terminate()
    finally:worker.terminate();s.reason=error;s.finish('COMPLETE' if error is None else 'CPU_DELIVERY_FAILED');deadline.close()
    if error:raise RuntimeError(error)
if __name__=='__main__':main()
