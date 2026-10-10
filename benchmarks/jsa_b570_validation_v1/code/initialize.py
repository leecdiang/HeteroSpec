from pathlib import Path
import json,hashlib,shutil,sys
from prepare import R,REPO,PLAN,load,save,sha
def make_spec(stage,arm,round,capture,family,input_file,indices,warm=False):
 name=f'{stage}-{round}-{arm}-'+('on' if capture else 'off');req=[]
 if warm:req.append(dict(unit=name+'/WARM',warm=True,input_file='SMOL_DISCOVERY_INPUTS.json',input_index=0))
 for i in indices:req.append(dict(unit=name+'/'+str(i),warm=False,input_file=input_file,input_index=i))
 return dict(stage=stage,arm=arm,round=round,capture=capture,family=family,session=name,requests=req)
def original():
 q=load(R/'dependencies/pr64/dependencies/TOKENIZATION_PROOF.json');q['offload_layers']=dict(target=37,draft=29);save('QWEN_RUNTIME.json',q)
 project=Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec');models={}
 source=load(R/'dependencies/pr64/ASSET_MANIFEST.json')['checked']
 for role,name in [('target','Qwen3-8B-Q8_0.gguf'),('draft','Qwen3-0.6B-Q8_0.gguf')]:
  p=project/'models/gguf'/name;d=source[str(p)];assert sha(p)==d['sha256'];models[role]=dict(d,path=str(p))
 save('QWEN_MODELS.json',dict(models=models))
 schedule=dict(A=[make_spec('A',a,c, bool(c), 'Qwen','QWEN_INPUTS.json',range(4)) for c in [0,1] for a in ['R','N','M','C']]);save('REQUEST_SCHEDULE.json',schedule)
 bindings={}
 for p in (R/'source').rglob('*'):
  if p.is_file():bindings[p.relative_to(R).as_posix()]=dict(sha256=sha(p),bytes=p.stat().st_size)
 save('SOURCE_BINDINGS.json',bindings)
 save('A_FREEZE.json',dict(plan_head='0a95a64805536323b0e8ae11784eaab150f91dcf',requests=32,sessions=8,warmup_requests=0,owned_gpu_limits=load(PLAN/'DESIGN.json')['limits'],files={n:sha(R/n) for n in ['QWEN_MODELS.json','QWEN_RUNTIME.json','QWEN_INPUTS.json','REQUEST_SCHEDULE.json','BINARY_BINDINGS.json','HISTORICAL_OWN_PATH.json','SOURCE_BINDINGS.json']},generation_binary_changes=0))
 save('TIMER_BINDINGS.json',dict(primary='Python perf_counter_ns before stdin write through HS_RESULT request identity, complete capture/metrics JSON readback, prompt/raw IDs/EOG/endpoint/reset validation. File hashing and receipt persist follow timer.',native_whole='Before reset to before observer.finish and required files, excludes observer/readback. Secondary only.',native_generation='Target: after prefill synchronization through final sync; speculative: original t_dec_start to t_dec_end, not interchangeable with host.',implicit_warmup='Original/candidate native source explicitly params.warmup=false; target --no-warmup. No common_init compatibility trial model forward.',sampler_defaults_source='hash-bound common.h and sampling.cpp: repeat1,freq0,presence0,dry0,grammar empty,mirostat0,reasoning budget-1/controlfalse,backend_samplingfalse; CLI temp0/seed123/top-k0/top-p1/min-p0; native greedy branch preserves original semantics.'))
 print('A frozen 32, no warm, original Qwen assets verified')
if __name__=='__main__':original()
