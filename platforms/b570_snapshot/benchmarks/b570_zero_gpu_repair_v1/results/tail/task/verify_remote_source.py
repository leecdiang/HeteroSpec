import base64,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parents[1];D=B/'repo/benchmarks/b570_zero_gpu_repair_v1';obj=json.loads((B/'task/REMOTE_SOURCE_PAYLOAD.json').read_text(encoding='utf-8'));root=B/'remote_source_bytes';root.mkdir()
members=[]
for row in obj['files']:
    assert row['encoding']=='base64'
    data=base64.b64decode(''.join(row['content'].split()),validate=True)
    actual=hashlib.sha256(data).hexdigest();assert actual==row['expected_sha256'],row['path']
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert blob==row['git_blob'],row['path']
    p=root/row['path'];p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data)
    members.append(dict(path=row['path'],bytes=len(data),sha256=actual,git_blob=blob))
out=dict(status='REJECTED_CANDIDATE_SOURCE_BYTES_MATCH',commit=obj['commit'],members=members,scope='Actual remote source/artifact readback, not a clean review, freeze or execution admission')
with (D/'results/REMOTE_SOURCE_AUTH.json').open('x',encoding='utf-8') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print('remote byte authentication',len(members),'files; implementation remains blocked')
