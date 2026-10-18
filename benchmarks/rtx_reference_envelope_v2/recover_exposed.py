"""Read-only recovery of remaining exposed inputs;no GPU qualification or pooling."""
import hashlib,json,subprocess
from pathlib import Path
from common import V,load,save,sha
from run import root
commit='2b5ed1552263907df3adfdff9b0121d115734a6c';path='benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/PLAN.json'
data=subprocess.check_output(['git','-C',str(V.parents[1]),'show',commit+':'+path]);p=json.loads(data);selected={c['id'] for c in load(root()/'RUN_SPEC.json')['contexts']};rows=[]
for d in p['descriptors']:
    if d['id'] in selected:continue
    files=[]
    for f in d['input_files']:
        source=Path(f['path']);ok=source.exists() and sha(source)==f['sha256'];files.append(dict(path=str(source),sha256=f['sha256'],available_exact=ok,bytes=f['bytes']))
    rows.append(dict(id=d['id'],family=d['family'],layer=d['layer'],phase=d['phase'],q=d['q'],input_status='RECOVERED_EXACT' if all(f['available_exact'] for f in files) else 'MISSING_OR_CHANGED',files=files,new_GPU_status='UNSTARTED'))
assert len(rows)==48
save(V/'RECOVERED_EXPOSED48.json',dict(source_commit=commit,source_path=path,source_Git_bytes_sha256=hashlib.sha256(data).hexdigest(),count=len(rows),recovered_exact=sum(r['input_status']=='RECOVERED_EXACT' for r in rows),new_GPU_calls=0,qualification='UNSTARTED;not merged withcore oroldPR113partial',order_note='read-only recovery audit completed duringCPUdelivery;controlledR1prefix was prioritized earlier;no additionalGPU collection',records=rows))
print('48inputs recovered:',sum(r['input_status']=='RECOVERED_EXACT' for r in rows))
