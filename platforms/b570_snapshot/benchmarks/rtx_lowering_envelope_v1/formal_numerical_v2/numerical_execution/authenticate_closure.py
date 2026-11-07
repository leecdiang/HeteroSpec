"""Authenticated small closure bytes; no scientific execution or qualification change."""
import datetime,hashlib,json,subprocess,sys,urllib.request
from pathlib import Path
D=Path(__file__).resolve().parent;V=D.parent
sys.path.insert(0,str(V))
from common import load,save,sha
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=V).decode().strip()
pr=load(D/'PR_METADATA_VERIFIED.json')
assert pr['head']==commit and pr['draft'] and pr['state']=='open'
assert pr['body']==(D/'PR_BODY.md').read_text(encoding='utf-8')
token=subprocess.check_output(['gh','auth','token']).decode().strip();rows=[]
headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-formal-closure-auth'}
for name in ('RESULT.md','AUTHENTICATED_FORMAL.json','FRESH_AUDIT.json','DELIVERY_CLOSURE.json','NEXT_CPU_PREPARATION.json','CLAIM_EVIDENCE.csv'):
    req=urllib.request.Request('https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/numerical_execution/'+name+'?ref='+commit,headers=headers)
    with urllib.request.urlopen(req,timeout=45) as response:
        assert response.status==200;b=response.read()
    assert b==(D/name).read_bytes();rows.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
assert sha(V/'F0.json')=='73ef7106240be73ab914e4c6a36064a0d1fd6d41ce5d9c38bf65f38e8331f080'
for p in subprocess.check_output(['git','diff','ba5719149c2ae5e8f0ac6d1f68a4bd5b248b5e4f','--name-only'],cwd=V).decode().splitlines():
    assert p.startswith('benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/')
save(D/'CLOSURE_REMOTE_VERIFIED.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),closure_commit=commit,data_commit=load(D/'AUTHENTICATED_FORMAL.json')['data_commit'],authenticated_remote_bytes=True,files=rows,Draft=True,state='open',PR_body_verified=True,full_raw_remote_fresh_audit_completed=True,additional_GPU_starts=0,current_run_permanently_stopped=True,next_GPU_authorization='NOT_GRANTED'))
print('Actual raw/CPU/next-step closure bytes authenticated at current Draft head. No additional GPU admission.')
