"""Independent byte/identity/native-event checks. No runner/comparator imports."""
import hashlib, json, re
from pathlib import Path

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for x in iter(lambda:f.read(8*1024*1024),b''):h.update(x)
    return h.hexdigest()
def require(x,message):
    if not x:raise ValueError(message)
def meta(root):
    return root/'metadata' if (root/'metadata').exists() else Path(__file__).resolve().parents[3]/'benchmarks/rtx_transfer_latency_v1'
def validate_run(r,phase,arm,metadata):
    d=phase/'runs'/r['run_id'];require(read(d/'record.json')==r,'record differs')
    for name,h in r['files_sha256'].items():require(sha(d/name)==h,'run byte hash differs: '+name)
    require(r['status']=='VALID' and r['process_returncode']==0,'failed run')
    p=read(metadata/'protocol.json');identity=read(metadata/'asset_identity.json')[arm]
    require(r['identity']==identity and r['protocol_sha256']==sha(metadata/'protocol.json'),'identity/protocol differs')
    template=p[arm]['commands'][r['condition']]
    vals={'{prompt}':r['command'][r['command'].index('--file')+1],'{native_log}':r['command'][r['command'].index('--log-file')+1],'{transcript}':r['command'][r['command'].index('--output-file')+1]}
    require(r['command']==[vals.get(x,x) for x in template],'command template differs')
    require(sha(d/'prompt.txt')==r['prompt_sha256'],'prompt bytes differ')
    require(r['prompt_sha256']==p[arm]['prompt_hashes'][r['task_id']],'frozen full template/input hash differs')
    raw=(d/'native.log').read_bytes().replace(b'\r\n',b'\n');ids=[];tasks=set()
    for m in re.finditer(rb'^\d+\.\d{2}\.\d{3}\.\d{3} D slot process_toke: id\s+(\d+) \| task (\d+) \| n_gen = (\d+), n_remaining = (-?\d+), next token:\s+(-?\d+) ',raw,re.M):
        slot,task,index,budget,tok=map(int,m.groups())
        require(slot==0 and index==len(ids)+1 and budget==128-index and tok>=0,'native index/budget/ID invalid')
        tasks.add(task);ids.append(tok)
    require(len(tasks)==1 and 0<len(ids)<=128,'native task/output cap differs')
    require(ids==read(d/'generated_ids.json')==r['generated_ids'],'native complete array differs')
    require(hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()==r['token_array_sha256'],'array digest differs')
    stop=re.findall(rb'\| stopped by (EOS|limit)',raw);require(len(stop)==1,'termination event differs')
    require(stop[0].decode()==r['termination'] and (stop[0]==b'EOS' or len(ids)==128),'inclusive EOG/cap differs')
    count=re.findall(rb'slot print_timing:.*?\|\s+eval time\s*=\s*[\d.]+ ms /\s*(\d+) tokens',raw)
    require(count==[str(len(ids)).encode()],'runtime count differs')
    draft=r['condition'] in ('RTX_BATCHED_K2','RTX_SERIALIZED_K2')
    layers=re.findall(rb'load_tensors: offloaded (\d+)/(\d+) layers to GPU',raw)
    require(layers==([(b'37',b'37'),(b'29',b'29')] if draft else [(b'37',b'37')]),'full offload differs')
    devices=re.findall(rb'llama_prepare_model_devices: using device ([^\n]+)',raw)
    require(len(devices)==len(layers) and all(x.startswith(b'CUDA0 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)') for x in devices),'actual device differs')
    ub=re.findall(rb'llama_context: n_ubatch\s*=\s*(\d+)',raw)
    require(int(ub[0])==(2 if r['condition'] in ('RTX_BATCHED_K2','H1_TARGET_UB2') else 1),'actual target ubatch differs')
    require(re.findall(rb'cached n_tokens = (\d+), memory_seq_rm',raw)==[b'0'],'fresh context differs')
    require('616.92' in r['device_before']['gpu'] and '616.92' in r['device_after']['gpu'],'driver evidence missing')
    return ids
def validate_phase(root,name,arm,metadata):
    d=root/name;data=read(d/'records.json');require(data['status']=='COMPLETE','incomplete phase: '+name)
    require(data['freeze_sha256']==sha(metadata/'runtime_freeze.json'),'freeze differs')
    order=[(r['task_id'],r['repetition'],r['condition']) for r in data['runs']]
    require(order==[tuple(x) for x in data['schedule']] and len(set(order))==len(order),'schedule/membership differs')
    require(data['post_execution_rehash']['status']=='PASS','post hash check missing')
    for r in data['runs']:validate_run(r,d,arm,metadata)
    return data
def package_checks(root,metadata,arm,asset_root=None):
    manifest=root/'SHA256_MANIFEST.json'
    if manifest.exists():
        files=read(manifest)['files']
        actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=manifest}
        require(actual==set(files),'archive inventory differs')
        for f,h in files.items():require(sha(root/f)==h,'archive hash differs: '+f)
    if (root/'frozen_source').exists():
        for rel,h in read(metadata/'runtime_freeze.json')['files'].items():require(sha(root/'frozen_source'/rel)==h,'frozen source differs')
    if asset_root:
        identity=read(metadata/'asset_identity.json')[arm]
        for k in ('target','draft','dataset'):require(sha(identity[k]['path'])==identity[k]['sha256'],'external model/data differs')
        for f,h in identity['binaries'].items():require(sha(Path(identity['binary_dir'])/f)==h,'external binary differs')
    return {'archive_file_bytes_checked':manifest.exists(),'frozen_source_bytes_checked':(root/'frozen_source').exists(),'external_asset_bytes_checked':bool(asset_root)}
