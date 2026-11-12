from pathlib import Path
import hashlib,json,re

HERE=Path(__file__).resolve().parent
log=HERE/'build-v3/logs/mmvq.cu.log'
s=log.read_text(encoding='utf8',errors='replace')
entries=list(re.finditer(r"Compiling entry function '([^']+)' for '([^']+)'",s))
rows=[]
for index,entry in enumerate(entries):
    name,arch=entry.groups()
    if not(name.startswith('_Z15hs_two_group_q8') or 'L9ggml_type8ELi4ELb0ELb0ELb0E' in name):continue
    end=entries[index+1].start() if index+1<len(entries) else len(s)
    body=s[entry.end():end]
    regs=re.search(r'Used (\d+) registers',body)
    shared=re.search(r'(\d+) bytes smem',body)
    spills=re.search(r'(\d+) bytes stack frame, (\d+) bytes spill stores, (\d+) bytes spill loads',body)
    rows.append({'kernel':name,'arch':arch,'registers_per_thread':int(regs.group(1)) if regs else None,
        'static_shared_bytes':int(shared.group(1)) if shared else None,'stack_spill_bytes':list(map(int,spills.groups())) if spills else None})
receipt={'kind':'COMPILER_RESOURCE_METADATA_ONLY_NOT_GPU_OBSERVATION','log':str(log),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
    'kernels':rows,'occupancy':'unknown','DRAM':'unknown','L2':'unknown','latency':'unknown','model_requests':0,'kernel_launches':0}
(HERE/'COMPILER_RESOURCES.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');print(json.dumps(receipt))
