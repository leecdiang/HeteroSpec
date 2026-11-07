"""New-run CPU build and native graph/address checks. No GPU work."""
import argparse,os,subprocess,time
from pathlib import Path
from common import V,load,save,sha
ROLES=['Q','K','V','mask'];LAYOUTS=['PQ','QB','QH_C']
def root():return Path(os.environ.get('HETEROSPEC_RUN_ROOT') or load(V/'LOCAL_RUN.json')['root'])
def build():
    r=root();s=load(r/'RUN_SPEC.json')
    for name,source in [('collector','collector.cpp'),('address_cpu','boundary_cpu.cpp')]:
        cmd=[s['compiler']['path'],'c++','-O3','-DNDEBUG','-D_CRT_SECURE_NO_WARNINGS','-std=c++17','-DGGML_BACKEND_DL','-DGGML_SHARED','-I'+s['ggml_include'],'-I'+s['vendor_include'],'-I'+str(Path(s['tool_root'])/'nvidia-cuda-cupti-cu12/nvidia/cuda_cupti/include'),'-I'+str(Path(s['tool_root'])/'nvidia-cuda-runtime-cu12/nvidia/cuda_runtime/include'),str(V/source),str(V/'build/libggml.dll.a'),str(V/'build/libggml-base.dll.a'),'-lpsapi','-lbcrypt','-o',str(V/f'build/{name}.exe')]
        cmd.insert(2,'-I'+str(Path(s['tool_root'])/'nvcc-headers-only/nvidia/cuda_nvcc/include'))
        start=time.monotonic();p=subprocess.run(cmd,capture_output=True,timeout=600);receipt=dict(command=cmd,exit=p.returncode,seconds=time.monotonic()-start,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'),GPU_calls=0,native_sha256=sha(V/f'build/{name}.exe') if p.returncode==0 else None);save(r/f'BUILD_{name}_{len(list(r.glob("BUILD_"+name+"*.json")))}.json',receipt);assert p.returncode==0,('build failure retained',name)
def graphs():
    from runner import Child,helper,env
    r=root();s=load(r/'RUN_SPEC.json');count=words=0
    for cid,c in load(r/'INPUTS.json').items():
        folder=r/'CPU'/cid;folder.mkdir(parents=True,exist_ok=True)
        for layout in c['layouts']:
            job=folder/(layout+'_JOB.json')
            if not (folder/(layout+'.json')).exists():
                save(job,dict(spec=str(r/'RUN_SPEC.json'),context=c,layout=layout));w=Child(helper());w.run([str(V/'build/address_cpu.exe'),str(job),str(folder/(layout+'.json'))],folder/(layout+'_host'),120,env(s),s['host_RAM_bytes'])
            result=load(folder/(layout+'.json'));assert result['status']=='PASS' and result['CUDA_loads']==0;count+=1;words+=result['whole_Q_mask_output_words']
    save(V/'CPU_GRAPHS_ALL.json',dict(status='PASS',graphs=count,complete_Q_mask_output_words=words,GPU_calls=0,CUDA_loads=0))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','graphs']);a=ap.parse_args();globals()[a.action]()

