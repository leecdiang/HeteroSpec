"""Record user display-routing change before any new forward."""
from preflight import *
samples=[]
for i in range(3):
    samples.append(host())
    if i<2:time.sleep(10)
file_bytes=sum(m['bytes'] for m in models()['Llama'].values())
background=max(512*1024**2,max(s['used_MiB'] for s in samples)*1024**2)
required=file_bytes+134217728+33554432+background+512*1024**2+512*1024**2
total=min(s['total_MiB'] for s in samples)*1024**2
assert all(s['AC']==1 for s in samples)
receipt={'status':'PASS' if required<=total else 'MEMORY_OR_ASSET_BLOCKED','utc':now(),'user_report':'Discrete display direct connection disabled; laptop panel now routed to integrated graphics. Model inference remains on RTX CUDA.','samples':samples,'formula':'fixed PR83 file bytes + F16 KV ctx1024 + max(512MiB,3 idle used samples) + 512MiB workspace + 512MiB safety','required_bytes':required,'available_total_bytes':total,'margin_bytes':total-required,'forwards':0,'initial_failed_admission_sha256':sha(LOCAL/'LLAMA_MEMORY_ADMISSION_01.json'),'initial_failed_admission_retained':True,'actual_full_offload_load_gate':'pending full pinned files'}
save(LOCAL/'LLAMA_MEMORY_ADMISSION_02.json',receipt)
save(PUB/'DISPLAY_CHANGE_ADMISSION.json',receipt)
print(json.dumps(receipt,ensure_ascii=False),flush=True)
