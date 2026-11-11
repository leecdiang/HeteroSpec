"""Offline builds and native CPU tests; no GPU modes can be selected here."""
import subprocess,sys,copy,json
from pathlib import Path
from common import V,load,save,sha,env,wire
from lifecycle import Child
OLD=Path('D:/hs114-bridge-v2/benchmarks/rtx_lowering_envelope_v1/s1a_bridge_v2')
def main():
    command=load(OLD/'COMPILE.json')['command'];builds=[]
    for role in ('clean','trace'):
        args=[str(V/'native_cost.cpp') if x.endswith('native_formal.cpp') else str(V/f's1b_{role}.exe') if x.endswith('lowering113_formal.exe') else str(V/Path(x).name) if x.endswith('.dll.a') else x for x in command]
        if role=='trace':args.insert(2,'-DS1B_TRACE_BUILD')
        r=subprocess.run([sys.executable,'-B',str(V/'cpu_job.py'),'--label','build_'+role,'--parallel-bound','8',*args],capture_output=True)
        row=dict(role=role,command=args,exit_code=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace'),CUDA_loads=0);save(V/('BUILD_final2_'+role+'.json'),row);assert r.returncode==0,row;builds.append(row)
    plan=load(V/'PLAN.json');oldf=load(OLD/'F0.json');helper=oldf['console_helper'];test=V/'CPU_FIXTURE_FINAL2';test.mkdir(exist_ok=False)
    f=dict(CPU_fixture_only=True,run_id=plan['run_id'],stage='S1B_COST_V1',hosts={l:dict(sha256=sha(V/f's1b_{l}.exe')) for l in ('clean','trace')},plan_path=str(V/'PLAN.json'),plan_sha256=sha(V/'PLAN.json'),runtime_directory=oldf['runtime_directory'],numerical_DLLs=oldf['numerical_DLLs'])
    save(test/'F0.json',f);paths=[]
    for s in plan['clean_slots'][:72]:
        p=test/'wires'/f'{s["index"]:03d}.json';save(p,wire(s,test/'F0.json'));paths.append(str(p))
    save(test/'WIRES.json',dict(wires=paths));save(test/'LOOP.json',{})
    cases=[]
    def run(label,role,mode,job,out,good=True):
        w=Child(helper);error=None
        try:w.run([str(V/f's1b_{role}.exe'),mode,str(job),str(out)],V/'cpu_tests'/('final2_'+label),60,env(oldf['runtime_directory']),512*1024**2)
        except Exception as exc:error=repr(exc)
        save(V/'cpu_tests'/('final2_'+label+'.controller.json'),dict(expected_success=good,error=error));assert (error is None)==good,label;cases.append(dict(case=label,expected_success=good,error=error))
    run('actual72','clean','--cpu-graphs',test/'WIRES.json',V/'CPU_GRAPHS_FINAL2.json')
    run('loop_clean','clean','--cpu-loop',test/'LOOP.json',V/'CPU_LOOP_CLEAN_FINAL2.json')
    run('loop_trace','trace','--cpu-loop',test/'LOOP.json',V/'CPU_LOOP_TRACE_FINAL2.json')
    base=load(paths[0]);negative=[('old_run','run_id','pr114-s1a-bridge-v2'),('wrong_hash','approved_stage_F0','0'*64),('extra_warmup','warmups',2),('extra_compute','graph_computes',10),('wrong_layout','layout','MQ'),('wrong_reference','ordinary_reference',{}),('wrong_root','root',str(test)),('wrong_output','native_output',str(test)),('wrong_measurements','measured_evaluations',9)]
    for label,key,value in negative:
        j=copy.deepcopy(base);j[key]=value;p=test/(label+'.json');save(p,j);run('reject_'+label,'clean','--cpu-wire',p,V/'cpu_tests'/(label+'.json'),False)
    # Finite collector absence blocks trace before CUDA, even for a CPU fixture
    # parser request into the actual GPU entry. The fixture itself is rejected.
    trace=wire(plan['trace_slots'][0],test/'F0.json');save(test/'TRACE.json',trace)
    run('deny_GPU_fixture','trace','--gpu-trace',test/'TRACE.json',V/'cpu_tests/never_GPU',False)
    save(V/'CPU_NATIVE_TESTS_FINAL2.json',dict(status='PASS',cases=cases,CPU_graphs=72,CUDA_loads=0,GPU_queries=0,graph_computes=0,model_requests=0))
    print('PASS2offline shared-core builds;actual72CPUgraphs;realQPC/synthetic-loop/negativewire tests')
if __name__=='__main__':main()
