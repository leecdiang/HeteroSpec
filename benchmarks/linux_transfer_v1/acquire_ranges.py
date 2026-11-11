"""Bounded HTTP range fallback for stalled exact-object model downloads.

Retain each unsuccessful attempt. Validate every Content-Range and the final
protocol SHA256. Network retries do not execute a model or consume GPU requests.
"""
import argparse, concurrent.futures, functools, hashlib, json, os, shutil, socket, time, urllib.request
from pathlib import Path
from acquire_models import MODELS
MIRROR_REVISIONS={'Qwen-target':'c38f9307f3d23c914614557de83d66c0104f942c','Qwen-draft':'6abe20cd0aed577f4d0b267935868ecae190aee9',
                  'Smol-target':'310ce99801489d3f0e2b2769c7f7357b1139cbfe','Smol-draft':'12fadd80a04effd20c63ec19ae5fec3ce4f9a08a'}

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def main():
 # Process-local caching of the real resolver's answers avoids a DNS lookup for
 # every range. TLS still verifies the original hostname; system DNS is unchanged.
 original_lookup=socket.getaddrinfo
 socket.getaddrinfo=functools.lru_cache(maxsize=128)(original_lookup)
 p=argparse.ArgumentParser();p.add_argument('key',choices=MODELS);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=8)
 p.add_argument('--distribution',choices=('huggingface','modelscope'),default='huggingface');a=p.parse_args()
 if not 1<=a.workers<=32:raise ValueError('range concurrency limit')
 repo,rev,name,total,expected=MODELS[a.key];a.out.mkdir(parents=True,exist_ok=True)
 endpoint='https://huggingface.co';download_revision=rev
 if a.distribution=='modelscope':endpoint='https://modelscope.cn/models';download_revision=MIRROR_REVISIONS[a.key]
 parts=a.out/(a.key+'-parts');parts.mkdir(exist_ok=True);chunk=16*1024*1024
 def fetch(i):
  start=i*chunk;end=min(total,(i+1)*chunk)-1;size=end-start+1;final=parts/f'{i:04d}.part'
  if final.exists():
   if final.stat().st_size!=size:raise RuntimeError('saved part size')
   return i
  for attempt in range(8):
   tmp=parts/f'{i:04d}-attempt{attempt}.partial';log=parts/f'{i:04d}-attempt{attempt}.json'
   if tmp.exists() or log.exists():continue
   began=time.monotonic();record={'part':i,'attempt':attempt,'start':start,'end':end,'status':'FAILED'}
   seeds=[]
   for prior in parts.glob(f'{i:04d}-attempt*.json'):
    previous=json.loads(prior.read_text());data=prior.with_suffix('.partial')
    if data.exists() and (previous.get('prefix_validated_by_range') or (previous.get('http_status')==206 and previous.get('content_range')==f'bytes {start}-{end}/{total}')):
     if 0<data.stat().st_size<=size:seeds.append(data)
   seed=max(seeds,key=lambda x:x.stat().st_size) if seeds else None
   offset=seed.stat().st_size if seed else 0
   try:
    with tmp.open('xb') as f:
     if seed:
      with seed.open('rb') as saved:shutil.copyfileobj(saved,f)
    record.update(resume_bytes=offset,prefix_validated_by_range=bool(offset))
    if offset==size:
     record.update(status='COMPLETE',bytes=size,sha256=digest(tmp));os.rename(tmp,final)
    else:
     req=urllib.request.Request(f'{endpoint}/{repo}/resolve/{download_revision}/{name}?download=true&part={i}&attempt={attempt}',headers={'Range':f'bytes={start+offset}-{end}','Accept-Encoding':'identity'})
     with urllib.request.urlopen(req,timeout=45) as response, tmp.open('ab') as f:
      observed=response.headers.get('Content-Range');record.update(http_status=response.status,content_range=observed)
      if response.status!=206 or observed!=f'bytes {start+offset}-{end}/{total}':raise RuntimeError('server did not honor exact range')
      record['prefix_validated_by_range']=True
      copied=offset
      while True:
       if time.monotonic()-began>600:raise TimeoutError('absolute per-part deadline')
       b=response.read(min(1024*1024,size-copied+1))
       if not b:break
       copied+=len(b)
       if copied>size:raise RuntimeError('oversized range')
       f.write(b)
      if copied!=size:raise RuntimeError('truncated range')
      f.flush();os.fsync(f.fileno())
     record.update(status='COMPLETE',bytes=copied,sha256=digest(tmp));os.rename(tmp,final)
   except Exception as e:
    # Redirect URLs can contain temporary credentials: retain the exception class
    # and a bounded generic reason, never the signed URL in a publishable record.
    record.update(error_type=type(e).__name__,http_error_code=getattr(e,'code',None),bytes=tmp.stat().st_size if tmp.exists() else 0)
   finally:
    record['wall_s']=time.monotonic()-began
    with log.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
   if record['status']=='COMPLETE':print(json.dumps({'key':a.key,'part':i,'bytes':size,'status':'COMPLETE'}),flush=True);return i
  raise RuntimeError('range attempts exhausted: '+str(i))
 count=(total+chunk-1)//chunk
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(fetch,range(count)))
 path=a.out/name;partial=a.out/(name+'.assembled-partial')
 if not path.exists():
  with partial.open('xb') as f:
   for i in range(count):
    with (parts/f'{i:04d}.part').open('rb') as g:shutil.copyfileobj(g,f,8*1024*1024)
   f.flush();os.fsync(f.fileno())
  if partial.stat().st_size!=total or digest(partial)!=expected:raise RuntimeError('final pinned model identity mismatch')
  os.rename(partial,path)
 if path.stat().st_size!=total or digest(path)!=expected:raise RuntimeError('model changed')
 receipt=a.out/(a.key+'-VERIFIED.json')
 record={'repo':repo,'revision':rev,'distribution':a.distribution,'distribution_revision':download_revision,'file':name,'bytes':total,'sha256':expected,'verified':True,'acquisition':'exact HTTP ranges; final full-file SHA256','parts':count}
 if not receipt.exists():
  with receipt.open('x') as f:json.dump(record,f,indent=2);f.write('\n')
 print(json.dumps(record),flush=True)

if __name__=='__main__':main()
