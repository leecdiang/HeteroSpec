"""Transport/full hashing only. Immutable model pins; zero model forwards."""
import concurrent.futures,hashlib,json,urllib.request,time
from pathlib import Path
R=Path('C:/hs/b570-mem-run-v1');P=Path('C:/hs/b570-mem-v1/docs/experiments/b570_memory_followup_20261011')
R.joinpath('models').mkdir(parents=True,exist_ok=True)
pins=json.loads((P/'ASSETS.json').read_text())['models']
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(key,pin):
 if key != 'Llama_target_Q6_K':
  path=Path('C:/hs/b570-opt-run-v1/models')/pin['filename']
 else:
  path=R/'models'/pin['filename'];partial=path.with_suffix('.download')
  for attempt in range(5):
   if path.exists():break
   offset=partial.stat().st_size if partial.exists() else 0
   if offset==pin['bytes']:partial.rename(path);break
   req=urllib.request.Request(pin['url'],headers={'Range':f'bytes={offset}-','User-Agent':'HeteroSpec-frozen-asset-transfer'})
   try:
    with urllib.request.urlopen(req,timeout=120) as response:
     if offset and response.status!=206:raise RuntimeError('Refusing non-range overwrite')
     with partial.open('ab' if offset else 'wb') as out:
      while block:=response.read(8*1024*1024):out.write(block)
    if partial.stat().st_size==pin['bytes']:partial.rename(path)
   except Exception as e:
    with (R/'ASSET_TRANSPORT.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(dict(key=key,attempt=attempt,offset=offset,error=str(e),utc=time.time()))+'\n')
   print(key,'transport bytes',partial.stat().st_size if partial.exists() else path.stat().st_size,flush=True)
  if not path.exists():raise RuntimeError(key+' incomplete asset transfer')
 size=path.stat().st_size;h=sha(path);assert size==pin['bytes'] and h==pin['sha256'],key
 print('FULL ASSET PASS',key,size,flush=True)
 return key,dict(**pin,path=str(path),actual_bytes=size,actual_sha256=h,full_file_verified=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 result=dict(pool.map(lambda item:one(*item),pins.items()))
(R/'ASSET_CHECKS.json').write_text(json.dumps(dict(status='ASSET_BYTES_PASS',models=result,model_forwards=0),indent=2)+'\n')
print('ALL FOUR MODEL ASSETS PASS',flush=True)
