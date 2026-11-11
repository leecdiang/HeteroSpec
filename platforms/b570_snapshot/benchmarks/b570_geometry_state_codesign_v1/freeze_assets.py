"""Fresh CPU byte hashing of model/driver/dependency assets. Never loads a model."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
HISTORY=Path(r'C:/Users/DIANG/Documents/ChatGPT/HeteroSpec/work/b570-final-causal-closeout-v1')
def pin(p):
 p=Path(p)
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),name=p.name,bytes=p.stat().st_size,sha256=h)
def main():
 original=json.loads((ROOT/'_host/pr97/baseline/SOURCE_IDENTITY.json').read_text())['identity']['models']['families']['Llama']['models'];models={}
 for role,x in original.items():
  p=Path('C:/hs/b570-mem-run-v1/models' if role=='target' else 'C:/hs/b570-opt-run-v1/models')/x['filename'];v=pin(p);assert v['sha256']==x['sha256'] and v['bytes']==x['bytes'];models[role]=v
 history=json.loads((HISTORY/'LOADED_DRIVER_RUNTIME_HASHES.json').read_text());drivers=[]
 for x in history['pins']:
  v=pin(x['path']);v['historical_sha256']=x['sha256'];v['unchanged_from_PR101']=v['sha256']==x['sha256'];drivers.append(v)
 assert all(x['unchanged_from_PR101'] for x in drivers),'Driver/system dependency changed: do not silently broaden reference'
 libs=[pin(ROOT/'_host/pr97/dependencies/pinned-build/ggml/src/Release'/n) for n in ('ggml-base.lib','ggml.lib')]
 (ROOT/'p0/ASSETS.json').write_text(json.dumps(dict(models=models,driver_files=drivers,driver_version=history['version'],import_libraries=libs,native_starts=0),indent=2)+'\n')
 print('PASS full model and driver byte hashing; native starts 0')
if __name__=='__main__':main()
