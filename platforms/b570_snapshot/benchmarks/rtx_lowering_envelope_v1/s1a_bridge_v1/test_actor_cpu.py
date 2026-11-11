"""Compile a CPU contract probe, never the actor's model/request main."""
import subprocess,sys,time
from pathlib import Path
from common import V,load,save,sha,env,pin
from pe_review import PE
from lifecycle import Child

def main():
    old=Path('D:/hs113/benchmarks/rtx_lowering_envelope_v1');source=old/'native/source'
    zig=load(V/'LINK_IDENTITY.json')['link_command'][0]
    cmd=[zig,'c++','-O3','-DNDEBUG','-std=c++17',*[f'-I{source/p}' for p in ('','src','include','ggml/include')],str(V/'actor_contract_cpu.cpp'),'-o',str(V/'actor_contract_cpu.exe')]
    r=subprocess.run([sys.executable,'-B',str(V/'cpu_job.py'),'--label','compile_actor_contract_v2','--parallel-bound','8',*cmd],capture_output=True)
    save(V/'ACTOR_CPU_COMPILE_v2.json',dict(command=cmd,exit_code=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')));assert r.returncode==0
    imports=PE(V/'actor_contract_cpu.exe').imports();assert not any('ggml' in n.lower() or 'cuda' in n.lower() for n in imports)
    helper=load(old/'formal_numerical_v2/F0.json')['console_helper'];rows=[]
    for i,mask in enumerate(('3','0','15','-1','garbage','16')):
        worker=Child(helper);error=None
        try:worker.run([str(V/'actor_contract_cpu.exe'),mask],V/'cpu_tests'/('actor_v2_'+str(i)),10,env(''),256*1024**2)
        except Exception as exc:error=repr(exc)
        assert (error is None)==(mask=='3');rows.append(dict(mask=mask,error=error,expected='PASS' if mask=='3' else 'REJECT'))
    exe=old/'native/build/bin/llama-server.exe';actorimports=PE(exe).imports()
    assert not any(n.lower() in ('ggml-base.dll','ggml.dll') for n in actorimports)
    save(V/'ACTOR_CPU_AUDIT.json',dict(status='PASS_CPU_CONTRACT_ONLY',CPU_probe=pin(V/'actor_contract_cpu.exe'),CPU_PE_imports=imports,actual_mask_processes=rows,
        actor=pin(exe),actor_PE_imports=actorimports,actor_shared_core='NO_GO_STATIC_CORE: no ggml.dll/ggml-base.dll import; build.ninja static archives agree',
        actor_initialization_IAT='No shared-core ggml_init IAT to certify. Static initialization cannot qualify CUDA plugin DLL state.',
        natural_requests=0,CUDA_loads=0,GPU_queries=0,full_actor_qualification=False))
    print('PASS actual actor headers:mask3/cache guards;5 fresh invalid-mask processes rejected;actor static core remains NO_GO')
if __name__=='__main__':main()
