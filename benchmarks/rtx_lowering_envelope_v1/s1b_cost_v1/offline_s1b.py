"""Bounded CPU audit/transport only. No native host or device command exists."""
import argparse,re,sys,time,shutil,os
from pathlib import Path
from common import V,load,save,sha,env
from bounded import State,Deadline,durable
from lifecycle import Child,process_commit
from transport_lifecycle import TransportChild
def main():
    p=argparse.ArgumentParser();p.add_argument('--action',required=True,choices=['seal-census','census-readback','analyze','package','readback','restore','recompute','git-push']);p.add_argument('--commit');a=p.parse_args()
    begin=time.perf_counter();f=load(V/'F0.json');b=f['budget']['offline_CPU_delivery'];root=Path(f['execution_root']);out=V/'delivery';out.mkdir(exist_ok=True);ledger=out/'cpu_ledger';ledger.mkdir(exist_ok=True)
    old=list(ledger.iterdir());assert all((d/'CPU_ENDED.json').exists() for d in old),'unresolved CPU action;no retry'
    spent=sum(load(d/'CPU_ENDED.json')['conservative_owned_seconds'] for d in old);wall=sum(load(d/'CPU_ENDED.json')['seconds'] for d in old)
    factor=17 if a.action=='git-push' else 3;remaining=min(b['wall_seconds']-wall,(b['conservative_owned_seconds']-spent)/factor);assert remaining>15
    d=ledger/f'{len(old):02d}-{a.action}';d.mkdir()
    class CPUState(State):
        def snapshot(self,status):
            r=super().snapshot(status);r['conservative_owned_seconds']=factor*r['seconds'];r['process_bound_multiplier']=factor;return r
    s=CPUState(d,'CPU');s.start=begin;w=TransportChild(f['console_helper'],f['CPU_transport_executables']) if factor==17 else Child(f['console_helper']);error=None
    def monitor():s.peak_commit=max(s.peak_commit,process_commit());assert s.peak_commit<=b['controller_commit']
    deadline=Deadline(s,remaining,w.terminate,grace=5,monitor=monitor).start()
    py=f['python']['path'];fresh=Path(f['fresh_restore_root']);payload=V/'evidence_s1b.py'
    def run(command,prefix,cap=32768):
        durable(prefix.with_suffix('.COMMAND.json'),dict(command=command,CPU_only=True,owned_multiplier=factor))
        w.run(command,prefix,min(300,deadline.remaining()-5),env(''),b['job_commit'],deadline.guard,log_cap=cap)
    def fetch(name,prefix,cap=16*1024**2):
        assert a.commit and re.fullmatch('[0-9a-f]{40}',a.commit)
        endpoint='repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/s1b_cost_v1/'+name+'?ref='+a.commit
        run([f['gh']['path'],'api',endpoint,'--header','Accept: application/vnd.github.raw'],prefix,cap)
        assert sha(prefix.with_suffix('.stdout'))==sha(V/name),'actual remote bytes differ'
    try:
        assert any(root.glob('*_ENDED.json')),'ended GPU stage required'
        if a.action=='census-readback':
            for name in ['CENSUS.json','DECISION.json','RECEIPTS.zip','MANIFEST.json']:fetch('delivery/census/'+name,d/name)
            durable(root/'CENSUS_AUTHENTICATED.json',dict(commit=a.commit,authenticated_remote_bytes=True,F0_sha256=sha(V/'F0.json'),census_sha256=sha(out/'census/CENSUS.json'),decision_sha256=sha(out/'census/DECISION.json')))
        elif a.action=='readback':
            download=out/'download';download.mkdir(exist_ok=False);fetch('delivery/raw/ARCHIVE.json',d/'descriptor');desc=load(out/'raw/ARCHIVE.json');save(download/'ARCHIVE.json',desc);moves=[]
            for part in desc['parts']:
                assert re.fullmatch(r'raw-\d{3}\.zip\.part',part['name']);prefix=d/part['name'];fetch('delivery/raw/'+part['name'],prefix,40*1024**2)
                source=prefix.with_suffix('.stdout');target=download/part['name'];assert not target.exists();source.rename(target);assert sha(target)==part['sha256'];moves.append(dict(old=str(source),new=str(target),sha256=sha(target)))
            durable(out/'RAW_REMOTE_AUTHENTICATED.json',dict(commit=a.commit,authenticated_remote_bytes=True,archive=desc,moved_download_streams_preserved=moves))
        elif a.action=='git-push':
            branch=f['branch'];assert branch.startswith('research/');os.chdir(f['repository'])
            run([f['git']['path'],'branch','--show-current'],d/'branch');assert (d/'branch.stdout').read_text().strip()==branch
            rel='benchmarks/rtx_lowering_envelope_v1/s1b_cost_v1';run([f['git']['path'],'add','--sparse',rel],d/'add')
            run([f['git']['path'],'diff','--cached','--name-only'],d/'scope');names=(d/'scope.stdout').read_text().splitlines();assert names and all(n.startswith(rel+'/') for n in names)
            run([f['git']['path'],'commit','-m','Seal registered S1B execution evidence'],d/'commit');run([f['git']['path'],'push','origin',branch],d/'push')
        else:
            action={'seal-census':'seal-census','analyze':'analyze','package':'package','restore':'restore','recompute':'analyze'}[a.action]
            target=out/'census' if a.action=='seal-census' else out/'ANALYSIS.json' if a.action=='analyze' else out/'raw' if a.action=='package' else fresh if a.action=='restore' else out/'FRESH_ANALYSIS.json'
            code=fresh/'frozen/evidence_s1b.py' if a.action=='recompute' else payload
            command=[py,'-B',str(code),'--action',action,'--out',str(target),'--root',str(fresh/'raw' if a.action=='recompute' else root)]
            if a.action=='restore':command+=['--archive',str(out/'download')]
            run(command,d/'worker')
            if a.action=='recompute':assert (out/'ANALYSIS.json').read_bytes()==(out/'FRESH_ANALYSIS.json').read_bytes()
    except BaseException as exc:error=repr(exc);s.minimum_stop(error);w.terminate()
    finally:w.terminate();s.reason=error;s.finish('COMPLETE' if error is None else 'CPU_DELIVERY_FAILED');deadline.close()
    if error:raise RuntimeError(error)
if __name__=='__main__':main()
