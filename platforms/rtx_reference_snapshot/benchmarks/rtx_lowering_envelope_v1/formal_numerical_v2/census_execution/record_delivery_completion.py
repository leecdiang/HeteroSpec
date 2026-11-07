"""Persist the completed readback/metadata delivery, without a native/GPU launch."""
import datetime, hashlib, json
from pathlib import Path
D=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
pr=load(D/'PR_METADATA_VERIFIED.json')
assert pr['draft'] and pr['state']=='open'
assert pr['head']=='1a4686752af100439f7babfff5fc9fb4c43fb435'
assert pr['body']==(D/'PR_BODY.md').read_text(encoding='utf-8')
assert pr['title']=='RTX lowering: formal v2 census passed; numerical authorization pending'
rows=[]
for name in ('AUTHENTICATED_CENSUS.json','CLOSURE.json','RESULT.md','SUMMARY.json','CENSUS_CONTROLLER_STARTED.json'):
    b=(D/name).read_bytes();rows.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
receipt=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),closure_commit=pr['head'],authenticated_remote_bytes=True,files=rows,readback_semantics='All five files were authenticated and byte-compared by finalize_delivery.py before its subsequent PR PATCH request returned502; script and failure retained. Raw archive and exact decision authenticated separately by frozen seal_census.py.',PR_metadata_attempts=[dict(method='gh pr edit GraphQL',error='Something went wrong while executing your query',server_UTC='2026-10-15T15:43:57Z',request_id='28B1:1AD451:107317:118C00:6AD0F4BC'),dict(method='urllib REST PATCH in finalize_delivery.py',error='HTTPError502 Bad Gateway',stage='after five successful closure byte readbacks; no successful metadata receipt'),dict(method='gh api REST PATCH',exit_code=0,followup_actual_title_body_Draft_verified=True)],PR_metadata_synchronized=True,isDraft=True,state=pr['state'],data_commit=load(D/'AUTHENTICATED_CENSUS.json')['data_commit'],numerical_authorization='NOT_GRANTED',new_GPU_starts_during_delivery=0,scientific_retries=0)
with (D/'DELIVERY_VERIFIED.json').open('x',encoding='utf-8',newline='\n') as out:json.dump(receipt,out,ensure_ascii=False,indent=2);out.write('\n')
print('Actual PR113 metadata and authenticated census closure retained; census-only work complete.')
