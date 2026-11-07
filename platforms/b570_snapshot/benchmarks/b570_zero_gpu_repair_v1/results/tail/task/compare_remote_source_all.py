"""Offline comparison of already downloaded bytes; no retry/qualification."""
import base64,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'repo/benchmarks/b570_zero_gpu_repair_v1';obj=json.loads((B/'task/REMOTE_SOURCE_PAYLOAD.json').read_text(encoding='utf-8'));root=B/'remote_source_comparison';root.mkdir()
members=[]
for r in obj['files']:
    data=base64.b64decode(''.join(r['content'].split()),validate=True);local=(D/r['path']).read_bytes();actual=hashlib.sha256(data).hexdigest()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert blob==r['git_blob']
    exact=actual==r['expected_sha256'];line_only=False;json_equal=None
    if not exact:
        try:line_only=data.decode('utf-8').replace('\r\n','\n')==local.decode('utf-8').replace('\r\n','\n')
        except UnicodeDecodeError:pass
        if r['path'].endswith('.json'):
            try:json_equal=json.loads(data)==json.loads(local)
            except ValueError:json_equal=False
    p=root/r['path'];p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data)
    members.append(dict(path=r['path'],git_blob=blob,local_sha256=r['expected_sha256'],remote_sha256=actual,exact_bytes_match=exact,line_endings_only=line_only,json_values_equal=json_equal))
different=[r for r in members if not r['exact_bytes_match']]
report=dict(status='EXACT_REMOTE_BINDING_FAILED' if different else 'EXACT_REMOTE_BYTES_MATCH',commit=obj['commit'],files=len(members),exact_matches=len(members)-len(different),mismatches=different,members=members,scope='Offline classification of actual initial readback; prior failed verifier retained. Line-ending equivalence is not exact source binding or freeze admission. No file/rule was repaired or rewritten.')
with (D/'results/SOURCE_BINDING_FAILURE.json').open('x',encoding='utf-8') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:report[k] for k in ('status','files','exact_matches','mismatches')}))
