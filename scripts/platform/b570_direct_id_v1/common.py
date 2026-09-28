"""Common execution utilities for the separately frozen direct-ID study."""
import gzip
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

START = '483c4cbd6cd72ae1cdcdbba4534a62fc1786f885'
UPSTREAM = '0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
TARGET_HASH = '408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6'
DRAFT_HASH = '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031'
DATA_HASH = 'b796127e635a67f93fb35c04f4cb03cf06f38c8072ee7cee8833d7bee06979ef'
TASKS = [f'HumanEval/{n}' for n in [3,10,19,20,28,32,44,47,48,50,54,57,62,64,68,70,89,90,101,104,105,106,107,111,119,123,126,128,129,162]]
SANITY = [f'HumanEval/{n}' for n in [3,10,19,20,106,129]]
CONDITIONS = ['TARGET_REFERENCE','B570_FAST_K2','B570_SERIALIZED_K2']
SEED = 20260928
PREFIX = 'Complete the following Python function. Return only the completed Python code, without Markdown fences.\n\n'
ORIGINAL = Path('C:/hs/b/bin/Release')
INSTRUMENTED = Path('C:/hs/b570-direct-id-v1-build/bin/Release')

def utc(): return datetime.now(timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
    return h.hexdigest()
def save(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    temp.replace(path)
def arraysha(ids): return hashlib.sha256(json.dumps(ids,separators=(',',':')).encode('ascii')).hexdigest()
def dataset(repo):
    path=repo/'datasets/humaneval/HumanEval.jsonl.gz'
    if sha(path)!=DATA_HASH: raise RuntimeError('Dataset hash mismatch')
    with gzip.open(path,'rt',encoding='utf-8') as f:return {x['task_id']:x for x in map(json.loads,f)}
def assets(repo):
    target=repo/'models/gguf/Qwen3-8B-Q8_0.gguf';draft=repo/'models/gguf/Qwen3-0.6B-Q8_0.gguf'
    if sha(target)!=TARGET_HASH or sha(draft)!=DRAFT_HASH:raise RuntimeError('Model hash mismatch')
    return target,draft
def command(binroot,target,draft,prompt,condition):
    reference=condition=='TARGET_REFERENCE'
    ubatch=1 if condition=='B570_SERIALIZED_K2' else 128
    exe='llama-completion.exe' if reference else 'llama-speculative.exe'
    cmd=[str(binroot/exe),'--model',str(target),'--device','Vulkan0','--n-gpu-layers','all',
         '--fit','off','--ctx-size','1024','--batch-size','512','--ubatch-size',str(ubatch),
         '--flash-attn','off','--file',str(prompt),'--n-predict','128' if reference else '127',
         '--temp','0','--top-k','0','--top-p','1','--min-p','0','--seed','123']
    if reference:cmd+=['--reasoning','off','--simple-io','--display-prompt','--no-warmup','--log-verbosity','4','--perf','--no-conversation']
    else:cmd+=['--verbose','--spec-type','draft-simple','--spec-draft-model',str(draft),
               '--spec-draft-device','Vulkan0','--spec-draft-ngl','all','--spec-draft-n-max','2','--spec-draft-n-min','0']
    return cmd
def semantic(sidecar):
    ids=sidecar['ids']; eog=sidecar['eog']
    if len(ids)!=len(eog) or not ids or any(type(x)!=int or x<0 for x in ids) or any(type(x)!=bool for x in eog):
        raise RuntimeError('Invalid direct-ID sidecar')
    stop=next((i+1 for i,x in enumerate(eog) if x),len(ids))
    end=min(stop,128)
    return ids[:end],bool(any(eog[:end])),len(ids)-end
def execute(root,stem,cmd,instrumented=True):
    root=Path(root)
    for d in ('stdout','stderr','ids'): (root/d).mkdir(parents=True,exist_ok=True)
    side=root/'ids'/f'{stem}.json'
    if side.exists(): raise RuntimeError(f'Existing sidecar: {side}')
    env=os.environ.copy(); env.pop('HETEROSPEC_DIRECT_ID_PATH',None)
    if instrumented:env['HETEROSPEC_DIRECT_ID_PATH']=str(side.resolve())
    start=utc(); t=time.perf_counter_ns()
    outpath=root/'stdout'/f'{stem}.txt';errpath=root/'stderr'/f'{stem}.txt'
    with outpath.open('wb') as out,errpath.open('wb') as err:
        p=subprocess.run(cmd,stdout=out,stderr=err,env=env,timeout=900)
    elapsed=(time.perf_counter_ns()-t)/1e9;end=utc()
    text=errpath.read_text(encoding='utf-8',errors='replace')
    off=re.findall(r'offloaded\s+(\d+)/(\d+) layers to GPU',text)
    required=[('37','37')] if Path(cmd[0]).name=='llama-completion.exe' else [('37','37'),('29','29')]
    valid=p.returncode==0 and off==required and 'using device Vulkan0 (Intel(R) Arc(TM) B570 Graphics)' in text
    result={'command':cmd,'exit_code':p.returncode,'offloads':off,'placement_pass':valid,
            'placement_evidence':[line for line in text.splitlines() if 'using device Vulkan0' in line or 'offloaded ' in line],
            'start_utc':start,'end_utc':end,'elapsed_operational_seconds':elapsed,
            'stdout':str(outpath.relative_to(root)).replace('\\','/'),'stderr':str(errpath.relative_to(root)).replace('\\','/'),
            'stdout_sha256':sha(outpath),'stderr_sha256':sha(errpath)}
    if instrumented and side.exists():
        raw=json.loads(side.read_text(encoding='utf-8'));ids,eos,overshoot=semantic(raw)
        result.update(raw_committed_ids=raw['ids'],raw_eog_flags=raw['eog'],generated_ids=ids,
                      generated_ids_sha256=arraysha(ids),raw_ids_sha256=arraysha(raw['ids']),semantic_output_length=len(ids),
                      eos=eos,cap_reached=len(ids)==128,raw_cli_overshoot_ids=overshoot,sidecar=str(side.relative_to(root)).replace('\\','/'),
                      sidecar_sha256=sha(side))
    elif instrumented:valid=False;result['sidecar_missing']=True
    result['execution_valid']=valid
    return result
