"""Independent CPU parser for real native zero-forward load evidence.

No executor/prepare imports, no model calls, no memory-gate truth from input flags.
"""
import hashlib,json,re,sys,copy,time,datetime
from pathlib import Path
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path('C:/hs/b570-opt-run-v1')
checks=0
def check(b,msg):
 global checks
 checks+=1
 if not b:raise ValueError(msg)
def parse(rows,stderr):
 check(rows[0]['event']=='MEMORY' and rows[0]['point']=='BEFORE_LOAD','No pre-load identity')
 pid=rows[0]['pid'];check(type(pid) is int and pid>0,'Worker PID')
 samples=[x for x in rows if x['event']=='MEMORY'];full=[x for x in samples if x['point']=='LOADED']
 for s in samples:
  check(s['pid']==pid and s['scope']=='OWNED_MODEL_PROCESS','External memory PID')
  check(s['vendor_id']==0x8086 and s['device_id']==0xE20C and 'B570' in s['device_name'] and s['device_type']==2,'Wrong/non-discrete physical GPU')
  check(s['decode_calls']==s['model_forward_calls']==0 and s['timestamp_utc'].endswith('Z'),'Non-zero or unknown forward')
  local=[h for h in s['heaps'] if h['device_local'] is True];nonlocal_=[h for h in s['heaps'] if h['device_local'] is False]
  check(len(local)==1 and len(nonlocal_)>=1,'Dedicated heap mapping unavailable')
  check(local[0]['physical_size_bytes']==10563354624,'Actual B570 heap size changed')
  check(all(type(h[k]) is int and h[k]>=0 for h in s['heaps'] for k in ['physical_size_bytes','budget_bytes','usage_bytes']),'Invalid byte evidence')
  free=sum(h['budget_bytes']-h['usage_bytes'] for h in local)
  check(s['device_local_headroom_bytes']==free,'Shared heap was added to headroom or invalid budget')
  check(s['headroom_gate']==(free>=536870912),'Wrong512MiB predicate')
 errors=[x for x in rows if x['event']=='ERROR']
 if errors:
  check(not full,'Error after a completed loaded sample')
  return dict(pid=pid,status='BLOCKED_LOAD_ERROR',error=errors[-1]['reason'],last_memory_point=samples[-1]['point'],last_observed_headroom_bytes=samples[-1]['device_local_headroom_bytes'],overrun_numeric_sample_retained=samples[-1]['device_local_headroom_bytes']<0,qualified_speedup=None)
 check(len(full)==1 and rows[-1]['event']=='FINAL','Incomplete zero-forward load')
 check(samples[-1]['point']=='UNLOADED','Missing unload record')
 contexts=[x for x in rows if x['event']=='CONTEXT'];check(len(contexts)==2,'Target/draft contexts missing')
 actual_offload=re.findall(r'offloaded (\d+)/(\d+) layers to GPU',stderr)
 check(len(actual_offload)==2,'Actual layer offload logs missing')
 kv_layers=re.findall(r'llama_kv_cache: layer\s+(\d+): dev = (\S+)',stderr)
 check(len(kv_layers)==sum(x['layers']-1 for x in contexts) and all(dev=='Vulkan0' for _,dev in kv_layers),'KV placement not fully Vulkan')
 for c,pair in zip(contexts,actual_offload):
  check(c['layers']==int(pair[0])==int(pair[1]),'Requested full offload differs from actual layers')
  check(c['n_ctx']==1024 and c['decode_calls']==0 and c['hidden_warmup_disabled_by_direct_API'],'Changed context or hidden warmup')
 check('type_k = \'f16\'' in stderr or 'K (f16)' in stderr,'F16 K evidence missing')
 check('Vulkan0 KV buffer' in stderr and 'warmup' not in stderr.lower(),'Warmup or missing resident KV log')
 free=full[0]['device_local_headroom_bytes'];passed=free>=536870912
 check(rows[-1]['status']==('LOADED_HEADROOM_PASS_ZERO_FORWARD' if passed else 'BLOCKED_INSUFFICIENT_LOADED_HEADROOM'),'Final status disagrees with actual bytes')
 return dict(pid=pid,status=rows[-1]['status'],loaded_headroom_bytes=free,loaded_headroom_MiB=free/1048576,required_headroom_bytes=536870912,margin_bytes=free-536870912,contexts=contexts,actual_gpu_layers=actual_offload,actual_KV_layer_records=len(kv_layers),all_layers_and_KV_actual_Vulkan=True,model_forwards=0,qualified_speedup=None,limits=['Zero-forward loaded memory only; engineering peak, no-spill, native mode, raw boundary and performance gates remain untested.'])
results={};raw={}
for p in sorted(R.glob('*_LOAD.stdout.jsonl')):
 rows=[json.loads(x) for x in p.read_text(encoding='utf-8-sig').splitlines() if x];err=p.with_name(p.name.replace('.stdout.jsonl','.stderr.log'));stderr=err.read_text(encoding='utf-8-sig',errors='replace');raw[p.name]=(rows,stderr);results[p.name]=parse(rows,stderr)
check(bool(results),'No actual loads')
imports=(R/'BINARY_IMPORTS.txt').read_text(encoding='utf-8-sig');check('llama_model_load_from_file' in imports and 'llama_init_from_model' in imports,'Missing actual API imports');check('llama_decode' not in imports and 'llama_encode' not in imports and 'common_init_from_params' not in imports,'Inference/warmup entry point imported')
family_counts={f:sum(k.startswith(f.upper()) for k in results) for f in ['Qwen','Llama']};check(all(v<=8 for v in family_counts.values()),'Zero-forward load-combination cap exceeded')
if (R/'BUDGET_ACCOUNTING.json').exists():
 budget=json.loads((R/'BUDGET_ACCOUNTING.json').read_text());bindings=json.loads((R/'LOAD_SOURCE_BINARY_BINDINGS.json').read_text())['loads'];total=0
 for name,(rows,_) in raw.items():
  start=rows[0]['timestamp_utc'];last=next(x for x in reversed(rows) if 'timestamp_utc' in x or 'utc' in x);end=last.get('timestamp_utc',last.get('utc'));duration=(datetime.datetime.fromisoformat(end.replace('Z','+00:00'))-datetime.datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds();total+=duration
  check(bindings[name]['native_last_timestamp_utc']==end,'Last actual native timestamp not retained')
  check(abs(bindings[name]['native_recorded_interval_seconds']-duration)<1e-9 and duration>=0,'Native interval miscount')
 check(abs(budget['native_recorded_intervals_seconds']-total)<1e-9,'Native total interval omitted or invented')
 check(budget['load_combinations_per_family']==family_counts and budget['conservative_engineering_budget_charges_per_family']==family_counts,'Loads omitted from conservative budget charge')
vocab_pairs=[]
for family in ['Qwen','Llama']:
 p=R/'vocab'/(family+'_target_Q8_0.jsonl')
 if not p.exists():continue
 target=json.loads(p.read_text(encoding='utf8').splitlines()[0])
 check(target['vocab_only'] is True and target['forward_calls']==0,'Target vocab-only proof')
 for quant in ['Q8_0','Q4_K_M']:
  p=R/'vocab'/(family+'_draft_'+quant+'.jsonl');draft=json.loads(p.read_text(encoding='utf8').splitlines()[0])
  check(draft['vocab_only'] is True and draft['forward_calls']==0,'Draft vocab-only proof')
  for key in ['vocab_tokens','vocab_type','bos','eos','add_bos','add_eos','runtime_eog_ids']:check(target[key]==draft[key],'Actual native special-token mismatch')
  check(len(target['table'])==len(draft['table'])==target['vocab_tokens'],'Truncated native vocabulary')
  for i,(a,b) in enumerate(zip(target['table'],draft['table'])):check(a==b and a['id']==i,'Full actual vocab bytes/type/score/EOG mismatch')
  check([x['id'] for x in target['table'] if x['eog']]==target['runtime_eog_ids'],'Native EOG list differs from actual full table')
  vocab_pairs.append(dict(family=family,draft=quant,tokens=target['vocab_tokens'],status='PASS'))
asset_checks=[]
assetfile=R/'ASSET_CHECKS.json'
if assetfile.exists():
 for key,x in json.loads(assetfile.read_text(encoding='utf8'))['models'].items():
  p=Path(x['path']);check(p.stat().st_size==x['bytes'],'Full installed model size differs from fixed pin')
  with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
  check(actual==x['sha256'],'Full installed model SHA differs from fixed pin')
  asset_checks.append(dict(asset=key,bytes=p.stat().st_size,sha256=actual,status='PASS'))
first=next((x for x in raw.values() if not any(r['event']=='ERROR' for r in x[0])),None);negative=[]
if first:
 rows,stderr=first
 for case in ['external_pid','shared_headroom','threshold_false','wrong_device','hidden_forward','partial_gpu','unknown_kv']:
  b=copy.deepcopy(rows);e=stderr
  if case=='external_pid':b[1]['pid']+=1
  elif case=='shared_headroom':b[0]['device_local_headroom_bytes']+=1
  elif case=='threshold_false':b[0]['headroom_gate']=False
  elif case=='wrong_device':b[0]['device_id']=0
  elif case=='hidden_forward':b[0]['model_forward_calls']=1
  elif case=='partial_gpu':e=e.replace('offloaded 37/37','offloaded 36/37').replace('offloaded 33/33','offloaded 32/33')
  else:e=e.replace('dev = Vulkan0','dev = CPU',1)
  try:parse(b,e)
  except ValueError as ex:negative.append(dict(case=case,status='REJECTED_AS_REQUIRED',reason=str(ex)))
  else:raise ValueError('Negative failed to reject '+case)
out=dict(status='PASS_ZERO_FORWARD_EVIDENCE_PARSER',checks=checks,loads=results,load_combinations_by_family=family_counts,independently_compared_full_native_vocab_pairs=vocab_pairs,independently_rehashed_external_models=asset_checks,negative_tests=negative,forward_requests_started=0,formal_requests_started=0,performance_qualified_ratios=None,model_forwards=0,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
(R/'INDEPENDENT_LOAD_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print('INDEPENDENT LOAD VERIFICATION PASS',checks,'checks',len(results),'actual load records',flush=True)
