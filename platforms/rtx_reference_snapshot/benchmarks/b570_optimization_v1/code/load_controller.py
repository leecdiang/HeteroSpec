"""Serial, bounded, zero-forward platform-gate controller. No inference requests.

Earlier direct zero-forward preparations are retained as actual native logs, not
backdated ledger START entries. This controller records every subsequent launch
before loading; no failure is retried and no budget is reset.
"""
import argparse,json,hashlib,os,subprocess,time,datetime
from pathlib import Path
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def append(root,row):
 with (root/'LOAD_LEDGER.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
def run(root,name,family,q,ub,outputs):
 study_start=datetime.datetime.fromisoformat('2026-10-11T06:30:49+00:00').timestamp()
 config=root/'AVAILABLE_ASSET_CHECKS.json';assets=json.loads(config.read_text(encoding='utf8'))['models'];target=assets[family+'_target_Q8_0'];draft=assets[family+'_draft_'+q]
 existing=list(root.glob(family.upper()+'*_LOAD.stdout.jsonl'));assert len(existing)<8,'Per-family load-combination cap'
 out=root/(name+'_LOAD.stdout.jsonl');err=root/(name+'_LOAD.stderr.log');assert not out.exists(),'Never repeat/overwrite a completed or failed launch'
 binary=root/'build/Release/b570-opt-memory-load.exe';paths=[Path(target['path']),Path(draft['path'])]
 for p,a in zip(paths,[target,draft]):assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
 modules={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in binary.parent.glob('*.dll')}
 args=[str(binary),str(paths[0]),str(paths[1]),str(ub),str(outputs)];start=time.time()
 assert start-study_start<8*3600,'Conservative study-wall GPU-lifetime upper bound exhausted'
 append(root,dict(event='ZERO_FORWARD_LOAD_START',name=name,family=family,draft_quantization=q,ub=ub,n_outputs_max=outputs,utc=start,argv=args,binary_sha256=sha(binary),numeric_modules=modules,inference_requests_started=0))
 with out.open('wb') as f,err.open('wb') as e:
  p=subprocess.Popen(args,stdout=f,stderr=e,cwd=binary.parent)
  append(root,dict(event='OWNED_PID',name=name,pid=p.pid,utc=time.time()))
  rc=p.wait(timeout=8*3600-(time.time()-study_start))
 elapsed=time.time()-start;append(root,dict(event='ZERO_FORWARD_LOAD_END',name=name,pid=p.pid,returncode=rc,elapsed_seconds=elapsed,stdout_sha256=sha(out),stderr_sha256=sha(err),utc=time.time(),model_forwards=0))
 rows=[json.loads(x) for x in out.read_text(encoding='utf-8-sig').splitlines() if x];print(name,rows[-1].get('status',rows[-1].get('reason')),flush=True)
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('family',choices=['Qwen','Llama']);p.add_argument('quantization',choices=['Q8_0','Q4_K_M']);p.add_argument('ub',type=int,choices=[32,128,512]);p.add_argument('outputs',type=int,choices=[1,4]);p.add_argument('--root',type=Path,default=Path('C:/hs/b570-opt-run-v1'));a=p.parse_args();run(a.root,a.name,a.family,a.quantization,a.ub,a.outputs)
