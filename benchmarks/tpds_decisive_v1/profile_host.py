"""Profile actual Qwen writer and validate through native GPU sequence I/O."""
from build_host import *
from build_v2 import compile_one,HERE
from native_adapter import execute
import struct,numpy as np,importlib.util
from active_kv import parse
def main():
    dest=ROOT/'forced-v2';dest.mkdir()
    for name in ['worker.cpp','target_capture.hpp','replay_path.hpp']:shutil.copy2(ROOT/'forced-v1'/name,dest/name)
    shutil.copy2(HERE/'forced_host.cpp',dest/'forced_host.cpp');compile_one(dest,'forced_host.cpp')
    writer=OLD/'source/src/llama-kv-cache.cpp'
    p=dict(format='dense_seq_f16_v1',writer_sha256=sha(writer),layer_map_source_sha256=sha(writer),target_model_sha256='408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6',host_writer_reviewed=True,capacity=1024,layers=[dict(id=i,k_elements=1024,v_elements=1024) for i in range(36)])
    # Independently construct token/layer/K,V sentinels; all half bit patterns finite.
    n=3;values=(np.arange(n*36*2*1024,dtype=np.uint32)%15360).astype('<u2').reshape(n,36,2,1024);expected=values.tobytes()
    raw=bytearray(struct.pack('<IiII',0xaf143cd8,0,1,n))
    for i in range(n):raw+=struct.pack('<iIi',i,1,0)
    raw+=struct.pack('<II',1,36)
    for i in range(36):raw+=struct.pack('<iQ',1,2048)+values[:,i,0,:].copy().tobytes()
    for i in range(36):raw+=struct.pack('<iII',1,2,1024)+values[:,i,1,:].T.copy().tobytes()
    (dest/'sentinel-input.bin').write_bytes(raw);assert parse(bytes(raw),list(range(n)),p)[0]==expected
    binding=json.loads((ROOT/'bridge-old-r-01/BINDING.json').read_bytes());binding['families']['Qwen']['executable_sha256']=sha(dest/'bin/worker.exe')
    job=dict(attempt_id='profile-sentinel-v2',exe=str(dest/'bin/worker.exe'),binding=binding,forced=dict(no_candidate_payload=True,sentinel_state=str(dest/'sentinel-input.bin'),prompt_ids=[1],paths=[]),reservation=dict(requests=1,token_rows=0,operators=0))
    out=execute(job);export=(out/'native/sentinel-export.bin').read_bytes();assert parse(export,list(range(n)),p)[0]==expected
    actual=(ROOT/'bridge-observer-r-01/native/r0/target/state/initial/sequence.bin').read_bytes()
    original=subprocess.check_output(['git','show','db3793e2ca44514eaf155f2ecb671bf38c7bc17e:benchmarks/tpds_decisive_v1/active_kv.py']);(dest/'original_active_kv.py').write_bytes(original)
    spec=importlib.util.spec_from_file_location('original_active',dest/'original_active_kv.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    assert parse(actual,list(range(99)),p)==mod.parse(actual,list(range(99)),p)
    put(ROOT/'QWEN_PROFILE.json',p);put(ROOT/'PROFILE_VALIDATION.json',dict(status='ACTUAL_GPU_WRITER_SENTINEL_AND_PARSER_MATCH',sentinel_sha256=sha(dest/'sentinel-input.bin'),export_sha256=sha(out/'native/sentinel-export.bin'),actual_initial_sha256=__import__('hashlib').sha256(actual).hexdigest(),actual_layers=36,k_elements=1024,v_elements=1024,optimized_parser_matches_pinned_parser=True,sequence_io_only=True,charged_requests=1,decoded_rows=0,independent_model_reference_still_required=True))
    print('GPU writer sentinel and actual trained-model profile validated')
if __name__=='__main__':main()
