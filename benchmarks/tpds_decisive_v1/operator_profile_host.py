"""Train-model writer layouts validated by real old-operator-runtime I/O."""
from native_adapter import *
from build_operator_driver import ORIG
from active_kv import parse
import numpy as np,struct,hashlib
def main():
    for model,layers in [('8B',36),('0.6B',28)]:
        out=ROOT/('O-profile-'+model);out.mkdir();modelpath=Path('D:/HeteroSpec-PC/models/gguf/Qwen3-'+model+'-Q8_0.gguf');writer=ORIG/'source/src/llama-kv-cache.cpp'
        p=dict(format='dense_seq_f16_v1',writer_sha256=sha(writer),layer_map_source_sha256=sha(writer),target_model_sha256=sha(modelpath),host_writer_reviewed=True,capacity=1536,layers=[dict(id=i,k_elements=1024,v_elements=1024) for i in range(layers)])
        n=3;v=(np.arange(n*layers*2*1024,dtype=np.uint32)%15360).astype('<u2').reshape(n,layers,2,1024);raw=bytearray(struct.pack('<IiII',0xaf143cd8,0,1,n))
        for i in range(n):raw+=struct.pack('<iIi',i,1,0)
        raw+=struct.pack('<II',1,layers)
        for i in range(layers):raw+=struct.pack('<iQ',1,2048)+v[:,i,0,:].copy().tobytes()
        for i in range(layers):raw+=struct.pack('<iII',1,2,1024)+v[:,i,1,:].T.copy().tobytes()
        (out/'sentinel.bin').write_bytes(raw);assert parse(bytes(raw),list(range(n)),p)[0]==v.tobytes()
        build=Path('D:/rtx184-operator/original-service-v3');manifest=dict(ctx=1536,layers=999,width=32,forced=dict(no_candidate_payload=True,prompt_ids=[1],paths=[],sentinel_state=str(out/'sentinel.bin')))
        run=execute(dict(attempt_id='O-sentinel-'+model,exe=str(build/'bin/service.exe'),operator_service=manifest,model_paths=[str(modelpath),'D:/HeteroSpec-PC/models/gguf/Qwen3-0.6B-Q8_0.gguf'],reservation=dict(requests=1,token_rows=0,operators=0)))
        exported=(run/'native/sentinel-export.bin').read_bytes();assert exported==raw;assert parse(exported,list(range(n)),p)[0]==v.tobytes()
        put(out/'PROFILE.json',p);put(out/'VALIDATION.json',dict(status='ACTUAL_GPU_WRITER_SENTINEL_MATCH',raw_sha256=hashlib.sha256(exported).hexdigest(),model=model,source=sha(writer),layers=layers,sequence_io_only=True,model_forward_rows=0));print('operator GPU writer qualified',model,flush=True)
if __name__=='__main__':main()
