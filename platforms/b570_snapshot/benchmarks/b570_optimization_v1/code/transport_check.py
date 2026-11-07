import json,urllib.request,time
from pathlib import Path
R=Path('C:/hs/b570-opt-run-v1');pin=json.loads(Path('C:/hs/b570-opt-v1/docs/experiments/b570_optimization_20261011/ASSETS.json').read_text())['models']['Llama_target_Q8_0']
t=time.time()
try:
 req=urllib.request.Request(pin['url']+'?download=true',headers={'Range':'bytes=0-1023','User-Agent':'HeteroSpec-transport-only'})
 with urllib.request.urlopen(req,timeout=25) as r:
  b=r.read(1024);x=dict(status=r.status,content_range=r.headers.get('Content-Range'),content_length=r.headers.get('Content-Length'),received_bytes=len(b),elapsed=time.time()-t,model_forwards=0)
except Exception as e:x=dict(error=str(e),elapsed=time.time()-t,model_forwards=0)
(R/'TARGET_RANGE_PROBE.json').write_text(json.dumps(x,indent=2)+'\n');print(x,flush=True)
