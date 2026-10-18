"""CPU-only positive/negative controller, evidence, admission and transport tests."""
import copy,hashlib,os,shutil,subprocess,sys,time,zipfile,json
from pathlib import Path
from common import V,load,save,pin,sha,env
from lifecycle import Child
from transport_lifecycle import TransportChild
from archive import package,restore,PartsReader,ESSENTIAL
import run_s1b as R
from bounded import State as RealState

def main():
    out=V/'cpu_tests/engineering_final';out.mkdir(exist_ok=False);results=[]
    def rejects(label,fn):
        try:fn()
        except Exception as exc:results.append(dict(case=label,status='EXPECTED_REJECTION',error=repr(exc)));return
        raise AssertionError('negative accepted '+label)
    # Real archive partitioning/fresh reconstruction. Source markers explicitly CPU.
    source=out/'raw';source.mkdir();(source/'bytes').write_bytes(os.urandom(70000));frozen=out/'fake_frozen';frozen.mkdir()
    for n in ESSENTIAL:(frozen/n).write_bytes(b'CPU_FIXTURE_NO_GPU_AUTHORITY')
    desc=package(source,out/'parts',frozen,cap=4096);restored=restore(out/'parts',desc,out/'fresh',2*1024**2);assert (out/'fresh/raw/bytes').read_bytes()==(source/'bytes').read_bytes();assert len(desc['parts'])>1
    rejects('negative_virtual_seek',lambda:PartsReader(out/'parts',desc['parts']).seek(-1))
    damaged=out/'damaged';shutil.copytree(out/'parts',damaged);p=damaged/desc['parts'][0]['name'];b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b);rejects('archive_part_corruption',lambda:restore(damaged,desc,out/'bad_fresh',2*1024**2))
    # Exact production authority gate, with synthetic standalone files only.
    case=out/'approval';case.mkdir();save(case/'F0.json',dict(CPU_fixture_only=True));(case/'REMOTE_F0_BYTES.json').write_bytes((case/'F0.json').read_bytes());save(case/'AUTHENTICATED_F0.json',dict(authenticated_remote_bytes=True,sha256=sha(case/'F0.json')))
    good=dict(stage='S1B_CENSUS_ONLY',run_id='pr116-s1b-cost-v1',F0_sha256=sha(case/'F0.json'),author_message='CPU_FIXTURE_ONLY',author_message_sha256=hashlib.sha256(b'CPU_FIXTURE_ONLY').hexdigest(),clean_first_trace_deferred_amendment_accepted=True)
    originalV=R.V;R.V=case;R.authority('census',{},good)
    for label,key,value in [('wrong_stage','stage','BRIDGE_V2_CENSUS_ONLY'),('wrong_run','run_id','old'),('wrong_hash','F0_sha256','0'*64),('unaccepted_amendment','clean_first_trace_deferred_amendment_accepted',False),('author_changed','author_message','changed')]:rejects(label,lambda key=key,value=value:R.authority('census',{},good|{key:value}))
    R.V=originalV
    # Production controller failure boundaries using explicit CPU transport stubs.
    real=time.perf_counter
    for label in ['readiness_failure','next_budget','started_failure']:
        wdir=out/label;wdir.mkdir();root=wdir/'run';root.mkdir();(root/'cas').mkdir();offset=[0.]
        slots=[dict(id='CPU_SLOT_'+str(i),index=i,kind='clean',block=0,descriptor='fixture',q=1,layout='PQ',warmups=1,graph_computes=9,native_output=str(root/'clean'/f'{i:03d}'/'native')) for i in range(2)]
        b=dict(stages=dict(clean0=dict(wall_seconds=150)),limits=dict(disk_free_before=0,disk_free_during=0,controller_commit=512*1024**2,raw_bytes=32*1024**2,per_host_reserve=1024**2,per_host_nonCAS=1024**2,native_commit=256*1024**2))
        f=dict(execution_root=str(root),budget=b,runtime_directory='',hosts=dict(clean=dict(path='CPU_NOT_A_GPU_EXECUTABLE')),console_helper={})
        save(wdir/'F0.json',f);save(wdir/'PLAN.json',dict(clean_slots=slots));save(wdir/'CPU_EXPECTED.json',[dict(descriptor_id='fixture',layout='PQ')]);save(wdir/'approval.json',dict(census_sha256='fixture',decision_sha256='fixture'));save(root/'CENSUS_AUTHENTICATED.json',dict(authenticated_remote_bytes=True,F0_sha256=sha(wdir/'F0.json'),census_sha256='fixture',decision_sha256='fixture'));save(root/'CENSUS_DECISION.json',dict(clean_admitted=True));save(root/'CENSUS_ENDED.json',dict(status='COMPLETE'))
        class S(RealState):
            def __init__(self,*a):super().__init__(*a,clock=lambda:real()+offset[0])
        class W:
            def __init__(self,*a):pass
            def terminate(self):pass
            def run(self,command,prefix,*a,on_start,**kw):
                on_start(42);p=Path(prefix);p.mkdir();save(p/'RECORD.json',dict(modules=[]))
                if label=='started_failure':raise RuntimeError('CPU_SYNTHETIC_NATIVE_FAILURE')
                offset[0]=90
        previous={name:getattr(R,name) for name in ['V','State','Child','authority','check','owned_conflicts','readiness','module_inventory','sha']};oldinspect=R.audit.inspect
        R.V=wdir;R.State=S;R.Child=W;R.authority=lambda *a:None;R.check=lambda *a:None;R.owned_conflicts=lambda *a:None;R.module_inventory=lambda *a:[]
        def ready(*a,**kw):
            if label=='readiness_failure':raise RuntimeError('CPU_FAKE_READINESS_FAILURE')
        R.readiness=ready;R.sha=lambda p:'fixture' if Path(p).name in ['CENSUS.json','CENSUS_DECISION.json'] else sha(p);R.audit.inspect=lambda *a:dict(process_identity=[42,1],q=1)
        argv=sys.argv;sys.argv=['run_s1b.py','--stage','clean0','--approval',str(wdir/'approval.json')]
        try:rejects(label,R.main)
        finally:
            sys.argv=argv
            for n,value in previous.items():setattr(R,n,value)
            R.audit.inspect=oldinspect
        ended=load(root/'CLEAN0_ENDED.json');assert (root/'CLEAN0_MINIMUM_STOP.json').exists()
        if label=='next_budget':assert ended['completed']==1 and ended['current'] is None and not (root/'clean/000/FAILED.json').exists() and not (root/'clean/001').exists()
        else:assert ended['completed']==0 and ended['native_started']==int(label=='started_failure')
    # Real OS job and parser paths. No CUDA plugin is loaded by these commands.
    old=load('D:/hs114-bridge-v2/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v2/F0.json');helper=old['console_helper']
    cmd='C:/Windows/System32/cmd.exe'
    for label,args,timeout,cap in [('pipe_overflow',[cmd,'/d','/c','for /L %i in (1,1,100000) do @echo CPU_TEST'],5,2048),('child_deadline',[sys.executable,'-B','-c','import time;time.sleep(5)'],.2,32768),('memory_commit',[sys.executable,'-B','-c','x=bytearray(256*1024*1024)'],5,32768)]:
        w=Child(helper);rejects(label,lambda args=args,label=label,timeout=timeout,cap=cap:w.run(args,out/label,timeout,env(''),64*1024**2,log_cap=cap))
    git=Path(shutil.which('git'));allowed=[pin(p) for p in [git,git.parent.parent/'mingw64/bin/git.exe',git.parent.parent/'mingw64/libexec/git-core/git-remote-https.exe'] if p.exists()]
    save(V/'CPU_TRANSPORT_PINS_FINAL.json',allowed);t=TransportChild(helper,allowed);t.run([str(git),'log','-1','--format=%H'],out/'real_git',10,env(''),512*1024**2);assert (out/'real_git.stdout').read_text().strip()=='2b5ed1552263907df3adfdff9b0121d115734a6c'
    save(V/'CPU_ENGINEERING_TESTS.json',dict(status='PASS',cases=results,real_split_archive=desc,real_fresh_restore=restored,real_Git_job=load(out/'real_git.LIFETIME.json'),new_GPU_queries=0,CUDA_loads=0,graph_computes=0))
    print('PASS split/fresh/authority,3controller stop flows,real job limits and pinned Git transport;GPU0')
if __name__=='__main__':main()
