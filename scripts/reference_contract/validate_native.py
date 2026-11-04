"""Build/test an authorized source kit on Linux CPU; no network/model downloads.
The frozen source is copied, then patched in a fresh work directory.
"""
from pathlib import Path
import argparse,hashlib,json,os,platform,subprocess
from stage import stage
from port_observer import port
from harden_native import harden
from stage_cuda_audit import stage as stage_cuda
ROOT=Path(__file__).resolve().parents[2]
def main(source,work,output):
    work.mkdir(parents=True,exist_ok=False);records=[]
    def run(cmd):
        r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True)
        records.append({'command':list(map(str,cmd)),'returncode':r.returncode,'stdout_tail':r.stdout[-12000:],'stderr_tail':r.stderr[-12000:],
                        'stdout_sha256':hashlib.sha256(r.stdout.encode()).hexdigest(),
                        'stderr_sha256':hashlib.sha256(r.stderr.encode()).hexdigest()})
        if r.returncode:
            output.write_text(json.dumps({'status':'FAILED','records':records},indent=2)+'\n')
            raise RuntimeError('command failed: '+str(cmd))
        return r.stdout
    tree=work/'source';receipt=stage(source,tree);cuda_receipt=stage_cuda(tree)
    observer=tree/'common/hs_observer.h';observer.write_text(port(observer.read_text()))
    graph=tree/'src/llama-graph.cpp';graph.write_text(harden(graph.read_text()))
    build=work/'build';bin=build/'bin'
    run(['cmake','-S',tree,'-B',build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release','-DGGML_CUDA=OFF','-DGGML_VULKAN=OFF','-DGGML_NATIVE=OFF','-DLLAMA_BUILD_TESTS=ON','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_TOOLS=OFF','-DLLAMA_BUILD_SERVER=OFF','-DLLAMA_CURL=OFF','-DGGML_CCACHE=OFF'])
    run(['cmake','--build',build,'--target','llama','test-llama-archs','test-save-load-state','test-backend-ops','-j','6'])
    models=work/'models';models.mkdir()
    run([bin/'test-llama-archs','-a','llama','-s','178','-o',models])
    flags=['g++','-std=c++17','-O2','-pthread','-I'+str(ROOT/'src/reference_batching'),'-I'+str(tree/'include'),'-I'+str(tree/'ggml/include')]
    links=['-L'+str(bin),'-Wl,-rpath,'+str(bin),'-lllama','-lggml','-lggml-base']
    quant=work/'quantize';test=work/'native-checkpoint'
    run(flags+[ROOT/'tests/reference_contract/make_q8_fixture.cpp']+links+['-o',quant])
    run([quant,models/'llama-dense.gguf',models/'llama-q8.gguf'])
    run(flags+[ROOT/'tests/reference_contract/test_native_checkpoint.cpp']+links+['-o',test])
    run([test,models/'llama-q8.gguf'])
    observation=work/'tensor-observation'
    run(flags+[ROOT/'tests/reference_contract/test_tensor_observation.cpp']+links+['-lggml-cpu','-o',observation])
    run([observation])
    abi=work/'cuda-audit-abi'
    run(flags+['-I'+str(tree/'ggml/src'),'-I'+str(tree/'ggml/src/ggml-cuda'),ROOT/'tests/reference_contract/test_cuda_audit_abi.cpp']+links+['-lggml-cpu','-o',abi])
    run([abi])
    run([bin/'test-save-load-state','-m',models/'llama-q8.gguf','-n','2','-c','128','-ngl','0'])
    hashes={str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [tree/'src/llama-graph.cpp',tree/'src/llama-graph.h',tree/'src/llama-kv-cache.cpp',tree/'src/hs_reference_batching.hpp',tree/'src/hs_native_preflight.inc',tree/'src/execution_contract.hpp',tree/'src/hs_packing_gate.hpp',tree/'src/hs_packing_gate.cpp',observer,bin/'libllama.so.0.4.0',models/'llama-q8.gguf',test]}
    result={'status':'NATIVE_CPU_SOURCE_BUILD_AND_CHECKPOINT_TESTS_PASS','platform':platform.platform(),
      'stage':receipt,'cuda_source_stage':cuda_receipt,'sha256':hashes,'expected_source_kit_sha256':'b1926827029e0bb8e219861901f2ca3538b330a44f9c6093b5267157dbfcd1ac','zip_verification':'external acquisition step, not performed by this directory-based runner','gpu_executions':0,'windows_dll':'NOT_RUN',
      'native_dispatch_qualification':'NOT_IMPLEMENTED','full_reference_equivalence':'NOT_ESTABLISHED',
      'model':'synthetic dense Llama, seed178, Q8_0; not research Qwen workload',
      'records':records}
    output.write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.source.resolve(),a.work.resolve(),a.output.resolve())
