"""Authenticated CPU-only closure readback and PR113 metadata synchronization."""
import datetime, hashlib, json, subprocess, urllib.request
from pathlib import Path

D=Path(__file__).resolve().parent
V=D.parent
token=subprocess.check_output(['gh','auth','token']).decode().strip()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=V).decode().strip()
assert head=='1a4686752af100439f7babfff5fc9fb4c43fb435'
headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-census-closure'}
rows=[]
for name in ('AUTHENTICATED_CENSUS.json','CLOSURE.json','RESULT.md','SUMMARY.json','CENSUS_CONTROLLER_STARTED.json'):
    url='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/census_execution/'+name+'?ref='+head
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45) as r:
        assert r.status==200;b=r.read()
    assert b==(D/name).read_bytes()
    rows.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))

# The first gh pr edit GraphQL attempt failed before updating metadata; retain it.
failure=dict(kind='CPU_PR_METADATA_TRANSPORT_FAILURE',reported_server_UTC='2026-10-15T15:43:57Z',error='GraphQL: Something went wrong while executing your query',request_id='28B1:1AD451:107317:118C00:6AD0F4BC',subsequent_read_confirmed_title_unchanged=True,new_GPU_starts=0)
body=dict(title='RTX lowering: formal v2 census passed; numerical authorization pending',body=(D/'PR_BODY.md').read_text(encoding='utf-8'))
rest_headers={**headers,'Accept':'application/vnd.github+json','Content-Type':'application/json'}
url='https://api.github.com/repos/leecdiang/HeteroSpec/pulls/113'
req=urllib.request.Request(url,data=json.dumps(body).encode(),headers=rest_headers,method='PATCH')
with urllib.request.urlopen(req,timeout=45) as r:
    assert r.status==200;pr=json.load(r)
assert pr['draft'] and pr['state']=='open' and pr['head']['sha']==head
assert pr['title']==body['title'] and pr['body']==body['body']
receipt=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),closure_commit=head,authenticated_remote_bytes=True,files=rows,PR_metadata_transport_failure=failure,PR_metadata_synchronized=True,isDraft=pr['draft'],state=pr['state'],PR_head=pr['head']['sha'],numerical_authorization='NOT_GRANTED',new_GPU_starts=0)
with (D/'DELIVERY_VERIFIED.json').open('x',encoding='utf-8',newline='\n') as out:
    json.dump(receipt,out,ensure_ascii=False,indent=2);out.write('\n')
print('Authenticated closure bytes and synchronized PR113 Draft metadata; no new GPU activity.')
