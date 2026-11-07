"""Independent CPU-only derivation from immutable bytes/raw records; no executor imports."""
import json,hashlib,sys,re,math,statistics,copy
from pathlib import Path
from datetime import datetime
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path('C:/hs/b570-mem-run-v1');checks=0
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def digest(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ck(x,msg):
 global checks
 checks+=1
 if not x:raise AssertionError(msg)
policy=read(R/'PIN_POLICY.json');assets=read(R/'ASSET_CHECKS.json')['models'];rehashed={}
for key,a in assets.items():
 path=Path(a['path']);h=digest(path);ck(path.stat().st_size==a['bytes'] and h==a['sha256']==a['actual_sha256'],key);rehashed[key]=dict(bytes=path.stat().st_size,sha256=h)
vocabs={}
for p in (R/'vocab').glob('*.jsonl'):
 v=json.loads(p.read_text(encoding='utf8').splitlines()[0]);ck(v['vocab_only'] and v['forward_calls']==0,p.name);vocabs[p.stem]=v
reference=vocabs['Llama_target_Q6_K'];eog=set(reference['runtime_eog_ids']);table=reference['table']
for name,v in vocabs.items():
 for key in ['vocab_tokens','vocab_type','bos','eos','add_bos','add_eos','runtime_eog_ids']:ck(v[key]==reference[key],name+' '+key)
 ck(len(v['table'])==128256,name+' full table')
 for i,(a,b) in enumerate(zip(table,v['table'])):ck(a==b,name+' row'+str(i))
def memory(row,profile,pid):
 ck(row['event']=='MEMORY' and row['profile']==profile and row['pid']==pid and row['scope']=='OWNED_MODEL_PROCESS','native memory process/profile')
 ck((row['vendor_id'],row['device_id'],row['device_type'])==(0x8086,0xE20C,2),'PCI/discrete map')
 ck('B570' in row['device_name'] and row['timestamp_utc'],'device timestamp')
 hs=row['heaps'];ck(len({h['index'] for h in hs})==len(hs),'unique heaps');local=[]
 for h in hs:
  ck(all(type(h[k])==int for k in ['index','physical_size_bytes','budget_bytes','usage_bytes']) and type(h['device_local'])==bool,'heap types')
  ck(0<=h['budget_bytes']<=h['physical_size_bytes'] and h['usage_bytes']>=0,'raw budgets')
  if h['device_local']:
   ck(h['index']==0 and h['physical_size_bytes']==10563354624,'dedicated heap mapping');local.append(h['budget_bytes']-h['usage_bytes'])
 ck(len(local)==1,'one mapped dedicated heap');value=min(local);threshold=policy['profiles'][profile]['dedicated_headroom_min_bytes']
 ck(type(row['device_local_headroom_bytes'])==int and row['device_local_headroom_bytes']==value,'signed min, never add system heap')
 ck(row['threshold_bytes']==threshold and row['headroom_gate']==(value>=threshold),'profile native threshold')
 return value,max(h['usage_bytes'] for h in hs if h['device_local'])
def endpoint(x):
 ids=x['ids'];flags=x['eog'];cap=x['cap'];ck(type(cap)==int and 1<=cap<=128,'cap bound')
 ck(0<len(ids)<=cap and len(flags)==len(ids)==x['length'],'raw complete size')
 ck(all(type(i)==int and 0<=i<128256 for i in ids),'native IDs')
 ck(all(type(f)==bool for f in flags) and flags==[i in eog for i in ids],'actual EOG flags')
 ck(not any(flags[:-1]) and x['terminal_id']==ids[-1],'no native suffix after EOG')
 ck(x['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==cap),'native terminal stop')
 ck(x['reset_target_min']==x['reset_target_max']==-1,'actual target reset positions')
 if x['draft_decode_calls']:ck(x['reset_draft_min']==x['reset_draft_max']==-1,'actual draft reset positions')
 ck(not x['memory_violation'] and x['residency_status']=='RESIDENCY_UNKNOWN','no unsupported qualified residency')
 return (tuple(ids),tuple(flags),x['length'],x['terminal_id'],x['stop_reason'])
ledger=[json.loads(s) for s in (R/'LEDGER.jsonl').read_text(encoding='utf8').splitlines()];starts={x['unit']:x for x in ledger if x['event']=='REQUEST_START'};ck(len(starts)==sum(x['event']=='REQUEST_START' for x in ledger),'unique paid actual request starts')
f0=read(R/'F0A.json');remote=read(R/'F0A_REMOTE_READBACK.json');ck(remote['status']=='PASS' and remote['all_frozen_bytes_restored_from_actual_remote_Git'] and remote['frozen_logical_files_restored']==len(f0['files']),'actual complete F0A')
if starts:ck(datetime.fromisoformat(remote['utc'])<min(datetime.fromisoformat(x['utc']) for x in starts.values()),'F0A remote verification precedes every forward')
for rel,m in f0['files'].items():ck((R/rel).stat().st_size==m['bytes'] and digest(R/rel)==m['sha256'],'F0A frozen byte '+rel)
probes=[]
for folder in sorted((R/'probes').iterdir()):
 receipt=read(folder/'RECEIPT.json');rows=[json.loads(s) for s in (folder/'stdout.jsonl').read_text(encoding='utf8').splitlines()];profile=receipt['profile'];mem=[x for x in rows if x['event']=='MEMORY'];ck(mem,'probe samples');pid=mem[0]['pid'];values=[memory(x,profile,pid)[0] for x in mem]
 ck(receipt['model_forward_calls']==0 and not any(x['event']=='RESULT' for x in rows),'probe no native result/forward')
 final=rows[-1];ck(final['event'] in ['PROBE_COMPLETE','ERROR'],'native zero-forward terminal')
 loaded=next((x for x in mem if x['point']=='LOADED'),None);weights=[x for x in rows if x['event']=='WEIGHT_MAP'];new=folder.name.startswith('ALLGPU_');cpu=bool(re.search(r'CPU_Mapped model buffer size\s*=\s*[1-9]',(folder/'stderr.log').read_text(encoding='utf8',errors='replace')))
 if new:
  ck(weights,'new actual tensor mappings')
  for w in weights:
   ck(w['pid']==pid and w['all_weights_Vulkan0'] and w['tensors'],'actual same-PID weight map')
   for t in w['tensors']:ck(t['gpu_backend_buffer'] and t['backend_device']=='Vulkan0' and t['tensor_bytes']>0,'actual GPU weight '+t['name'])
  ck(not cpu,'new placement excludes CPU model buffer')
  if final['event']=='PROBE_COMPLETE':ck(loaded and min(values)>=policy['profiles'][profile]['dedicated_headroom_min_bytes'],'all observed loaded samples satisfy threshold')
 status='LOADED_ONLY_GPU_BUFFER_MAP_PHYSICAL_UNKNOWN' if new and loaded else 'MEMORY_BLOCKED_BEFORE_DUAL_CONTEXT' if new else 'NONQUALIFYING_CPU_INPUT_WEIGHT_PLACEMENT'
 probes.append(dict(name=folder.name,profile=profile,pid=pid,status=status,loaded_headroom_bytes=loaded['device_local_headroom_bytes'] if loaded else None,min_observed_headroom_bytes=min(values),actual_cpu_weight_buffer_observed=cpu,new_all_gpu_weight_buffers=new,raw_final=final,zero_forward=True))
results=[];failures=[];coverage={};streams={}
for folder in sorted((R/'workers').glob('*')):
 spec=read(folder/'SPEC.json');rows=[json.loads(s) for s in (folder/'stdout.jsonl').read_text(encoding='utf8').splitlines()];profile=spec['profile'];pids={r['pid'] for r in rows if 'pid' in r};ck(len(pids)==1,'owned worker PID identity');pid=next(iter(pids));streams[folder.name]={r['request_id']:r for r in rows if r['event']=='RESULT'}
 modules=read(folder/'MODULES.json');ck(modules['pid']==pid and len(modules['actual'])==6,'actual process module identity/count')
 for m in modules['actual']:ck(digest(R/'build/Release'/m['ModuleName'])==m['sha256'],'actual process loaded module matches frozen recoverable bytes')
 for w in (r for r in rows if r['event']=='WEIGHT_MAP'):
  ck(w['all_weights_Vulkan0'] and w['pid']==pid,'actual resident model map')
  for t in w['tensors']:ck(t['backend_device']=='Vulkan0' and t['gpu_backend_buffer'],'resident tensor map '+t['name'])
 for w in (r for r in rows if r['event']=='COMPUTE_BUFFER_OBSERVATION'):
  ck(w['GPU_buffer'] and w['backend_device']=='Vulkan0','sampled compute buffer');coverage.setdefault(profile,set()).add((w['role'],w['op']))
for unit,start in starts.items():
 folder=R/'raw'/unit
 if not (folder/'RESULT.json').exists():
  ck((folder/'FAILURE.json').exists(),'paid failure retained');failures.append(dict(unit=unit,profile=start['profile'],failure=read(folder/'FAILURE.json')));continue
 r=read(folder/'RESULT.json');x=r['native'];sig=endpoint(x);ck(r['unit']==unit and r['profile']==start['profile'] and r['task']==start['task'],'slot provenance');ck(r['qualified_ratio'] is None,'qualified ratios remain null')
 ck(type(r['whole_request_seconds']) in [int,float] and math.isfinite(r['whole_request_seconds']) and r['whole_request_seconds']>0,'whole timer finite')
 wf=next(folder for folder in (R/'workers').iterdir() if unit in streams.get(folder.name,{}));ck(streams[wf.name][unit]==x,'response is actual native stdout')
 path=wf/(unit+('.trace.json' if r['capture'] else '.memory.json'));raw=read(path);raw=raw['memory'] if r['capture'] else raw;ck(not raw['violation'],'no native peak violation');values=[memory(s,r['profile'],x['pid']) for s in raw['samples']];ck(values,'actual engineering samples')
 minimum=min(t[0] for t in values);maximum=max(t[1] for t in values);ck(minimum==r['observed_minimum_headroom_bytes'] and maximum==r['observed_maximum_heap_usage_bytes'],'actual sampled extrema');ck(minimum>=policy['profiles'][r['profile']]['dedicated_headroom_min_bytes'],'every observed engineering sample above fixed threshold')
 if r['capture']:
  trace=read(path)
  for phase in (y for y in trace['target'] if y['phase']=='BINDING'):ck(phase['actual_full_state_bytes_equal'] and phase['before_bytes']==phase['after_bytes']>0,'actual full KV/state byte equality at binding')
  for v in trace['verify']:ck(len(v['batch_ids'])<=4 and len(v['batch_ids'])>=2 and 0<=v['accepted']<=len(v['batch_ids'])-1,'logical verify and rollback trace')
 ck(x['target_decode_calls']>0,'explicit target decode')
 results.append(r)
binary_versions={digest(p) for p in R.rglob('b570-memory-worker.exe')}
for x in ledger:
 if x['event']=='PROBE_START':ck(x['binary_sha256'] in binary_versions,'every paid zero-forward actor version recoverable')
for name in ['ggml.dll','ggml-base.dll','ggml-cpu.dll','ggml-vulkan.dll']:
 h=digest(R/'build/Release'/name);ck(all(digest(p)==h for p in (R/'versions').rglob(name)),'inherited numeric module bytes unchanged across versions')
profiles={}
for profile,cfg in policy['profiles'].items():
 es=[x for x in ledger if x.get('profile')==profile];charged=sum(x['event'] in ['PROBE_START','LOAD_WARMUP_RESERVATION'] or x['event']=='REQUEST_START' and not x.get('warm',False) for x in es);probe_count=sum(x['event']=='PROBE_START' for x in es);gpu=sum(x.get('seconds',0) for x in es if x['event'] in ['PROBE_END','WORKER_END']);ck(charged<=640 and probe_count<=12 and gpu<=28800,'profile hard units/lifetime')
 rr=[x for x in results if x['profile']==profile];ordinary={};stability={};candidate_rows=[]
 for ub in [32,128,512]:
  rs=[x for x in rr if x['arm']=='R_UB'+str(ub) and not x['warm']];ordinary[ub]=rs
  if len(rs)==24:
   by={(x['repeat'],x['task']):endpoint(x['native']) for x in rs};stability[ub]=all(by[1,t]==by[2,t] for _,t in by)
 ref={(x['repeat'],x['task']):x for x in ordinary[128]}
 for draft_asset in cfg['draft_assets']:
  q=draft_asset[len('Llama_draft_'):]
  for mode in ['native_greedy','vulkan_batched_repair']:
   for k in [1,2,3]:
    cid=f'{q}_{mode}_k{k}';rs=[x for x in rr if x['arm']=='C_'+cid and not x['warm']];match=[x for x in rr if x['arm']=='M_'+mode and not x['warm']]
    equal=len(rs)==24 and len(ref)==24 and all(endpoint(x['native'])==endpoint(ref[x['repeat'],x['task']]['native']) for x in rs);mequal=len(match)==24 and len(ref)==24 and all(endpoint(x['native'])==endpoint(ref[x['repeat'],x['task']]['native']) for x in match)
    candidate_rows.append(dict(candidate_id=cid,paid_completed=len(rs),whole_native_reference_equal=equal,matched_reference_equal=mequal,status='RAW_EQUIVALENT_PHYSICAL_RESIDENCY_UNKNOWN' if equal and mequal else 'INCOMPLETE_OR_DIVERGENT',qualified_ratio=None))
 profiles[profile]=dict(engineering_units=charged,dedicated_zero_forward_probes=probe_count,actual_request_starts=sum(x['event']=='REQUEST_START' for x in es),complete=len(rr),paid_failures=sum(x['profile']==profile for x in failures),formal_requests=0,owned_gpu_lifetime_seconds_upper_bound=gpu,ordinary_two_repeat_stability=stability,candidate_matrix=candidate_rows,compute_buffer_sample_ops=sorted([list(x) for x in coverage.get(profile,set())]),residency='UNKNOWN',all_qualified_ratios=None)
main=read(R/'STANDARD_Q6_ENGINEERING.json');rr=[x for x in results if x['profile']=='STANDARD_Q6' and not x['warm']]
gm=lambda xs:math.exp(statistics.mean(math.log(x) for x in xs))
by=lambda arm:{(x['repeat'],x['task']):x for x in rr if x['arm']==arm}
stock=by('R_UB128');good=[]
for row in main['ordinary_grid']:
 rows=by('R_UB'+str(row['ub']));equal=len(rows)==24 and all(endpoint(x['native'])==endpoint(stock[key]['native']) for key,x in rows.items())
 seconds=gm([x['whole_request_seconds'] for x in rows.values()]);ck(equal==row['whole_output_equal'] and math.isclose(seconds,row['gm_seconds'],rel_tol=1e-12),'ordinary eligibility/timer independently derived')
 if equal:good.append((seconds,row['ub']))
ck(min(good)[1]==main['R_prod_ub'],'fastest whole-equivalent ordinary selected');prod=by('R_UB'+str(main['R_prod_ub']));rank=[]
for row in main['candidates']:
 rows=by('C_'+row['candidate_id']);ratios=[gm([prod[key]['whole_request_seconds']/x['whole_request_seconds'] for key,x in rows.items() if key[0]==r]) for r in [1,2]]
 ck(all(math.isclose(a,b,rel_tol=1e-12) for a,b in zip(ratios,row['diagnostic_repeat_R_prod_C'])),'unqualified diagnostic ratios independently derived')
 equal=all(endpoint(x['native'])==endpoint(stock[key]['native']) for key,x in rows.items());ck(equal==row['complete_raw_equal'],'complete candidate raw equivalence')
 if equal:rank.append((-min(ratios),row['k_max'],max(x['observed_maximum_heap_usage_bytes'] for x in rows.values()),row['candidate_id']))
ck(min(rank)[3]==main['diagnostic_ranked_first'],'one diagnostic selection, negative scores retained')
boundary=[x for x in rr if '_BOUNDARY_R_stock_' in x['unit'] or '_BOUNDARY_C_selected_' in x['unit']];groups={}
for x in boundary:groups.setdefault((x['task'],x['native']['cap']),[]).append(x)
ck(len(groups)==15 and all(len(xs)==4 and len({endpoint(x['native']) for x in xs})==1 for xs in groups.values()),'complete 56 boundary plus four longest outputs/capture modes equal')
ck(any(x['native']['stop_reason']=='EOG' for x in boundary),'natural native EOG exercised')
ck(all(len(x['native']['prompt_ids'])==768 for x in boundary if 'LONGEST' in x['unit']),'longest native prompt exactly 768')
tiny=read(R/'TINY_MODE_VERIFICATION.json');ck(tiny['status']=='COMPLETE' and len(tiny['cases'])==4 and tiny['candidate_selection_unchanged'],'four declared tiny modes complete without reselection')
for case in tiny['cases']:
 ck(len(case['requests'])==8 and case['status']=='COMPLETE_RAW_EQUIVALENT','tiny cap/rollback native outputs')
 for row in case['requests']:
  x=next(x for x in rr if x['unit']==row['unit']);ref=next(x for x in groups[row['task'],row['cap']] if x['arm']=='R_stock' and not x['capture']);ck(endpoint(x['native'])==endpoint(ref['native']),'tiny raw reference equal')
ck(main['F0B']=='NOT_CREATED' and main['confirmation']=='NOT_ADMITTED_RESIDENCY_UNKNOWN','no physical residency qualification inferred')
sample=next(json.loads(s) for s in (R/'probes/ALLGPU_STANDARD_Q6_NONE_128_ordinary_k1/stdout.jsonl').read_text(encoding='utf8').splitlines() if json.loads(s)['event']=='MEMORY');rejections=[]
for name,mutate in [('foreign_PID',lambda y:y.update(pid=y['pid']+1)),('foreign_PCI',lambda y:y.update(device_id=0)),('threshold_drift',lambda y:y.update(threshold_bytes=134217728)),('unsigned_or_scalar_headroom',lambda y:y.update(device_local_headroom_bytes=2**64-1)),('system_heap_substitution',lambda y:y['heaps'][0].update(device_local=False)),('duplicate_heap',lambda y:y['heaps'].append(copy.deepcopy(y['heaps'][0]))),('false_logged_gate',lambda y:y.update(headroom_gate=not y['headroom_gate']))]:
 y=copy.deepcopy(sample);mutate(y)
 try:memory(y,sample['profile'],sample['pid'])
 except AssertionError:rejections.append(name)
 else:raise AssertionError('Bad memory evidence accepted:'+name)
report=dict(status='PASS_INDEPENDENT_RAW_EVIDENCE_NO_SPEEDUP_QUALIFICATION',checks=checks,profiles=profiles,probes=probes,raw_completed=len(results),raw_failures=failures,independently_rehashed_assets=rehashed,F0A_native_source_binary_bytes= len(f0['files']),F0A_actual_remote_head=remote['head'],historical_PR86_unchanged_loads=11,historical_PR86_generation_forwards=0,negative_evidence_rejections=rejections,nonretry_scope='All attempted slots/probes retained; no formal requests or scientific retries.',physical_residency='UNKNOWN_NOT_INFERRED_FROM_GPU_BUFFERS_OR_BUDGETS')
(R/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Independent verification PASS',checks,len(results),len(failures),flush=True)
