"""New study ledger; each actual zero-forward native allocation launch costs one unit."""
from common import *
def budget(profile):
 es=[json.loads(s) for s in (R/'LEDGER.jsonl').read_text().splitlines()] if (R/'LEDGER.jsonl').exists() else []
 es=[x for x in es if x.get('profile')==profile]
 return dict(engineering_units=sum(x['event'] in ['PROBE_START','LOAD_WARMUP_RESERVATION'] or x['event']=='REQUEST_START' and not x.get('warm',False) for x in es),probe_units=sum(x['event']=='PROBE_START' for x in es),owned_gpu_seconds=sum(x.get('seconds',0) for x in es if x['event'] in ['PROBE_END','WORKER_END']))
def config(profile,q,ub,mode,k):
 policy=load(R/'PIN_POLICY.json')['profiles'];assert profile in policy
 cfg=policy[profile];assets=load(R/'ASSET_CHECKS.json')['models'];target=assets[cfg['target_asset']]
 draft='NONE' if q=='NONE' else assets['Llama_draft_'+q]['path']
 if q!='NONE':assert 'Llama_draft_'+q in cfg['draft_assets']
 assert ub in [32,128,512] and mode in ['ordinary','native_greedy','vulkan_batched_repair','N_unrepaired'] and k in [1,2,3]
 if profile=='TIGHT_Q8' and mode!='ordinary':assert ub==32
 assert (q=='NONE')==(mode=='ordinary' or mode in ['native_greedy','vulkan_batched_repair'] and q=='NONE')
 return target['path'],draft,cfg['dedicated_headroom_min_bytes']
def probe(profile,q,ub,mode,k):
 target,draft,threshold=config(profile,q,ub,mode,k);name=f'ALLGPU_{profile}_{q}_{ub}_{mode}_k{k}';folder=R/'probes'/name;folder.mkdir(parents=True,exist_ok=False)
 b=budget(profile);assert b['probe_units']<12 and b['engineering_units']<640 and b['owned_gpu_seconds']<28800
 assets=load(R/'ASSET_CHECKS.json')['models']
 for path in [target,draft]:
  if path=='NONE':continue
  a=next(x for x in assets.values() if x['path']==path);assert sha(path)==a['sha256'] and Path(path).stat().st_size==a['bytes']
 exe=R/'build/Release/b570-memory-worker.exe';cmd=[str(exe),profile,target,draft,str(ub),mode,str(k),str(folder),'probe'];event(event='PROBE_START',profile=profile,name=name,argv=cmd,threshold_bytes=threshold,binary_sha256=sha(exe))
 start=time.perf_counter()
 with (folder/'stdout.jsonl').open('wb') as out,(folder/'stderr.log').open('wb') as err:
  p=subprocess.Popen(cmd,stdout=out,stderr=err,cwd=exe.parent,creationflags=subprocess.CREATE_NO_WINDOW);event(event='PROBE_PID',profile=profile,name=name,pid=p.pid)
  try:rc=p.wait(timeout=min(300,28800-b['owned_gpu_seconds']))
  except subprocess.TimeoutExpired:p.kill();rc=p.wait();raise
  finally:event(event='PROBE_END',profile=profile,name=name,pid=p.pid,seconds=time.perf_counter()-start,exit_code=p.poll())
 rows=[json.loads(s) for s in (folder/'stdout.jsonl').read_text().splitlines()];loaded=next((x for x in rows if x.get('point')=='LOADED'),None)
 result=dict(profile=profile,name=name,draft=q,ub=ub,mode=mode,k=k,threshold_bytes=threshold,exit_code=rc,loaded=loaded,status='LOADED_ONLY_PASS' if rc==0 else 'MEMORY_OR_NATIVE_LOAD_BLOCKED',model_forward_calls=0,residency_status='UNKNOWN',engineering_peak='NOT_TESTED',raw_commit='NOT_TESTED')
 save(folder/'RECEIPT.json',result);print(name,result['status'],loaded['device_local_headroom_bytes'] if loaded else rows[-1],flush=True);return result
if __name__=='__main__':
 import sys
 profile=sys.argv[1]
 for ub in ([128] if profile=='STANDARD_Q6' else [32,128,512]):probe(profile,'NONE',ub,'ordinary',1)
 for q in (['Q8_0','Q4_K_M'] if profile=='STANDARD_Q6' else ['Q4_K_M']):
  for mode in ['native_greedy','vulkan_batched_repair']:probe(profile,q,32,mode,3)
