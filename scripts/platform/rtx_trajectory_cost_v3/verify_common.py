"""Independent raw verifier: imports only replay verifier, never execution/comparison code."""
import hashlib,json,re
from pathlib import Path
from itertools import zip_longest
import verify_replay as replay
def require(ok,msg):
    if not ok:raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arr(v):return hashlib.sha256(json.dumps(v,separators=(',',':')).encode('utf-8')).hexdigest()
def difference(a,b):
    for i,(x,y) in enumerate(zip_longest(a,b)):
        if x!=y:return {'index':i,'left_id':x,'right_id':y}
    return None
def timer(path,ids):
    b=Path(path).read_bytes();m=re.findall(rb'HS_TIMER start_qpc=(\d+) end_qpc=(\d+) frequency=(\d+) start_steady_ns=(\d+) end_steady_ns=(\d+) count=(\d+) terminal_id=(\d+)',b)
    require(len(m)==1,'missing/duplicate native timer')
    st,en,f,sn,ens,n,t=map(int,m[0]);require(en>st and ens>sn and f>0,'reverse/nonpositive interval')
    ms=1000*(en-st)/f;cross=(ens-sn)/1e6
    require(abs(ms-cross)<=max(.020,.001*ms),'clock disagreement');require(n==len(ids) and t==ids[-1],'timer endpoint ID/count')
    return {'milliseconds':ms,'count':n,'terminal_id':t,'start_qpc':st,'end_qpc':en,'frequency':f,'start_steady_ns':sn,'end_steady_ns':ens,'secondary_milliseconds':cross}
def check_run(path,tape=None,metadata=None,observer_off=False):
    path=Path(path);r=read(path/'record.json')
    if not r.get('implementation'):
        v=replay.check_run(path,tape,observed=not observer_off)
        if metadata and r['task_id'] in read(Path(metadata)/'INPUT_CONTRACT.json')['reserved_tokens']:
            require(v['prompt_ids']==read(Path(metadata)/'INPUT_CONTRACT.json')['reserved_tokens'][r['task_id']]['prompt_ids'],'replay token contract')
        return {**v,'record':r}
    require(r['status']=='VALID','incomplete native execution')
    for name,v in r['files'].items():
        q=path/name;require(q.is_file() and q.stat().st_size==v['bytes'] and sha(q)==v['sha256'],'native transport hash '+name)
    require(sha(path/'prompt.txt')==r['input_sha256'],'input bytes')
    require(r['run_id']==r['task_id'].replace('/','-')+'-r'+str(r['repetition'])+'-'+r['condition'],'native run association')
    text=(path/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1');ids,stop=replay.native_commits(text)
    require(ids==r['generated_ids']==read(path/'generated_ids.json') and arr(ids)==r['array_sha256'],'native complete IDs')
    require(stop==r['termination'],'termination reason')
    if metadata:
        templates=read(Path(metadata)/'COMMAND_TEMPLATES.json')
        expected=templates['timer' if r['implementation']=='TIMER' else 'original'][r['wire_condition']]
        values={'{prompt}':r['command'][r['command'].index('--file')+1],'{native_log}':r['command'][r['command'].index('--log-file')+1],'{transcript}':r['command'][r['command'].index('--output-file')+1]}
        require(r['command']==[values.get(x,x) for x in expected],'exact frozen native command differs')
        if r.get('phase') in ['A_PRE_LIVE','A_LIVE','B_FORMAL'] and (Path(metadata)/'F0_MANIFEST.json').exists():
            frozen=read(Path(metadata)/'F0_MANIFEST.json')['files'];prefix='benchmarks/rtx_trajectory_cost_v3/'
            require(r['protocol_sha256']==frozen[prefix+'JOINT_PROTOCOL.json']['sha256'] and r['asset_identity_sha256']==frozen[prefix+'ASSET_IDENTITY.json']['sha256'],'native reviewed source/asset identity')
    w=r['wire_condition'];spec=w in ['RTX_BATCHED_K2','RTX_SERIALIZED_K2'];ub=2 if w in ['TARGET_ONLY_UB2','RTX_BATCHED_K2'] else 1
    layers=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',text);require(layers==([('37','37'),('29','29')] if spec else [('37','37')]),'native actual model placement')
    devices=re.findall(r'llama_prepare_model_devices: using device ([^\n]+)',text);require(len(devices)==len(layers) and all(x.startswith('CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for x in devices),'actual CUDA0 device')
    u=list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',text)));require(u==[ub]*len(layers),'actual target/draft ubatch')
    require(re.findall(r'cached n_tokens = (\d+)',text)==['0'],'fresh KV context')
    prompt=None
    if r['process_environment_overrides']['LLAMA_BATCH_DEBUG']=='1':
        prompt=replay.native_prompt(text)
        import observations
        physical=observations.native(path/'native.log')['physical_group_sizes']
        require(physical and max(physical)==ub and min(physical)>=1,'actual physical splitting differs from requested UB')
        if metadata:
            inputs=read(Path(metadata)/'INPUT_CONTRACT.json');task=r['task_id']
            if task in inputs['reserved_tokens']:
                require(r['input_sha256']==inputs['input_hashes'][task] and prompt==inputs['reserved_tokens'][task]['prompt_ids'],'native input/task token contract')
    result={'run_id':r['run_id'],'ids':ids,'prompt_ids':prompt,'condition':r['condition'],'termination':stop,'record':r}
    if r['implementation']=='TIMER':
        t=timer(path/'stderr.log',ids);require(all(r['timer'][k]==v for k,v in t.items()),'declared timer vs raw');result['timer']=t
    else:require(b'HS_TIMER ' not in (path/'stderr.log').read_bytes(),'original executable unexpectedly instrumented')
    return result
def unique(runs):
    ids=[r['run_id'] for r in runs];require(len(ids)==len(set(ids)),'duplicate complete run')
