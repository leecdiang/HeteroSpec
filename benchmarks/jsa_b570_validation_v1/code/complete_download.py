"""Resume interrupted static asset transport, retain partial receipt, verify exact bytes."""
import urllib.request,shutil,time
from pathlib import Path
from prepare import R,PLAN,load,save,sha
x=load(PLAN/'COORDINATION_SNAPSHOT.json')['model_pair']['draft'];p=R/'models'/Path(x['url'].split('?')[0]).name;tmp=p.with_suffix('.download');start=tmp.stat().st_size if tmp.exists() else 0
save('MODEL_DOWNLOAD_INTERRUPTION.json',dict(role='draft',partial_bytes=start,expected_bytes=x['bytes'],reason='HTTP response ended before fixed expected size; rejected, no model was loaded.',scientific_request_starts=0,partial_sha256=sha(tmp)))
req=urllib.request.Request(x['url']+'&transport_resume='+str(time.time_ns()),headers={'Range':f'bytes={start}-'})
with urllib.request.urlopen(req,timeout=120) as response:
 headers=dict(response.headers);append=response.status==206 and headers.get('Content-Range',headers.get('content-range','')).startswith(f'bytes {start}-')
 save('MODEL_DOWNLOAD_RESUME_HEADERS.json',dict(status=response.status,headers=headers,resume_offset=start,append=append))
 with tmp.open('ab' if append else 'wb') as f:shutil.copyfileobj(response,f,1024*1024)
assert tmp.stat().st_size==x['bytes'] and sha(tmp)==x['sha256'];tmp.rename(p)
models={}
for role,y in load(PLAN/'COORDINATION_SNAPSHOT.json')['model_pair'].items():
 q=R/'models'/Path(y['url'].split('?')[0]).name;assert q.stat().st_size==y['bytes'] and sha(q)==y['sha256'];models[role]=dict(y,path=str(q))
save('MODEL_CHOICE.json',dict(status='EXACT_BYTES_VERIFIED_NO_FORWARD',models=models,selection='PR81 fixed publisher pair, no scientific-output selection',official_conversion_lineage='NOT_CERTIFIED_BY_PUBLISHER',new_forwards=0));print('Both fixed model assets verified',flush=True)
