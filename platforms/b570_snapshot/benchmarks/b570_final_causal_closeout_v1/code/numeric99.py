"""Independent stdlib-only raw-evidence audit; never imports controller or executes a model."""
import argparse,json,hashlib,struct,math,collections,zipfile
from pathlib import Path
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def endpoint(x,ids,ub,pid):
 assert x['event']=='RESULT' and x['pid']==pid and x['prompt_ids']==ids and x['cap']==128
 o=x['ids'];f=x['eog'];assert 0<len(o)<=128 and len(o)==len(f)==x['length']
 assert all(type(i)is int and 0<=i<128256 for i in o)
 assert f==[i in {128001,128008,128009} for i in o] and not any(f[:-1])
 assert x['terminal_id']==o[-1] and x['stop_reason']==('EOG' if f[-1] else 'CAP') and (f[-1] or len(o)==128)
 assert not x['memory_violation'] and x['reset_target_min']==x['reset_target_max']==-1
 a=x['actual_condition']
 assert a==dict(prefill_ub=ub,continuation_ub=ub,output_capacity=1,maximum_k=0,logical_batch=512,n_ctx=1024,threads=10,kv='F16',flash_attention=False)
 assert x['mode']=='ordinary' and x['draft_decode_calls']==x['proposed']==x['accepted']==0
 assert x['component_completed_wall'] is None and x['GPU_completion_event_ms'] is None
 assert x['partition98']['context_ub_fixed']==ub and x['partition98']['prefill_logits_policy']=='ONLY_COMPLETE_PROMPT_FINAL_POSITION' and x['partition98']['cost_scope']=='DIAGNOSTIC_ONLY'
 w=x['workload'];assert w['prompt_ids_count']==len(ids) and w['output_ids_count']==len(o)
 assert w['initial_target_committed']==1 and w['fallback_committed']==len(o)-1 and w['sampling_calls']==len(o)
 assert w['phase_binding_calls']==w['kv_trim_calls']==w['verify_cycles']==w['draft_micrographs']==0
 assert w['inherited_explicit_sync_calls']==2
 for role in ['target','draft']:
  h=w[role+'_physical_width_hist'];assert sum(h.values())==w[role+'_micrographs'] and sum(int(k)*v for k,v in h.items())==w[role+'_micrograph_rows']
 assert w['target_micrograph_rows']==len(ids)+len(o)-1 and w['target_ordinary_rows']==len(o)-1
 assert w['target_continuation_physical_width_hist']==({'1':len(o)-1} if len(o)>1 else {})
def memory(m,pid):
 assert m['pid']==pid and m['vendor_id']==0x8086 and m['device_id']==0xE20C and m['adapter_luid_valid']
 h=[x for x in m['heaps'] if x['device_local']]
 assert len(h)==1 and h[0]['index']==0 and h[0]['physical_size_bytes']==10563354624
 assert m['device_local_headroom_bytes']==int(h[0]['budget_bytes'])-int(h[0]['usage_bytes'])>=536870912
def geometry(trace,x,ids,ub,part):
 rows=trace['target'];pre=[d for d in rows if d['phase']=='PREFILL'];cont=[d for d in rows if d['phase']=='ORDINARY']
 assert not trace['draft'] and not trace['verify'] and len(pre)==math.ceil(len(ids)/part)
 assert len(rows)==len(pre)+len(cont) and len(cont)==len(x['ids'])-1 and len(rows)==x['target_decode_calls']
 assert [i for d in pre for i in d['input_ids']]==ids
 assert [i for d in pre for i in d['logits_requested_positions']]==[len(ids)-1]
 for n,d in enumerate(pre):
  pos=n*part;seg=ids[pos:pos+part];assert d['pos']==pos and d['input_ids']==seg
  widths=collections.Counter(str(min(ub,len(seg)-i)) for i in range(0,len(seg),ub))
  assert d['physical_width_hist']==dict(widths) and d['successful_micrographs']==sum(widths.values()) and d['occupied_rows']==len(seg)
  assert d['last_output_requested']==(n==len(pre)-1) and not d['all_outputs']
 for n,d in enumerate(cont):
  assert d['pos']==len(ids)+n and d['input_ids']==[x['ids'][n]] and d['logits_requested_positions']==[len(ids)+n]
  assert d['physical_width_hist']=={'1':1} and d['successful_micrographs']==d['occupied_rows']==1 and d['last_output_requested'] and not d['all_outputs']
 hist=collections.Counter()
 for d in rows:
  assert d['role']=='TARGET' and d['ub']==ub and d['kv_min']==0 and d['kv_max']==d['pos']+len(d['input_ids'])-1
  assert d['GPU_completed_stage_wall'] is None
  hist.update(d['physical_width_hist'])
 assert dict(hist)==x['workload']['target_physical_width_hist']
 return pre
def payload(root,p):
 q=root/p['path'];assert q.resolve().is_relative_to(root.resolve())
 b=q.read_bytes();assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']
 return b
def top2(b):
 assert len(b)==128256*4
 f=struct.unpack('<128256f',b);assert all(math.isfinite(v) for v in f)
 a=max(range(len(f)),key=f.__getitem__);c=max((i for i in range(len(f)) if i!=a),key=f.__getitem__)
 return f,a,c
def parse_kv(b,n):
 # Source-pinned llama_kv_cache::state_write + meta/data; Llama3.1 F16 non-MRoPE.
 pos=0
 def take(fmt):
  nonlocal pos
  v=struct.unpack_from('<'+fmt,b,pos);pos+=struct.calcsize('<'+fmt)
  return v[0] if len(v)==1 else v
 assert take('I')==0xaf143cd8 and take('i')==0
 assert take('I')==1 and take('I')==n
 for i in range(n):assert take('i')==i and take('I')==1 and take('i')==0
 trans=take('I');assert trans in [0,1] and take('I')==32
 tensors=[]
 for layer in range(32):
  assert take('i')==1
  row=take('Q');assert row==2048
  size=n*row;d=b[pos:pos+size];assert len(d)==size;pos+=size
  tensors.append(dict(role='K',layer=layer,bytes=size,sha256=hashlib.sha256(d).hexdigest()))
 for layer in range(32):
  assert take('i')==1
  if trans:assert take('I')==2 and take('I')==1024;size=n*2048
  else:assert take('Q')==2048;size=n*2048
  d=b[pos:pos+size];assert len(d)==size;pos+=size
  tensors.append(dict(role='V',layer=layer,bytes=size,sha256=hashlib.sha256(d).hexdigest()))
 assert pos==len(b),'extra/cropped serialized KV bytes'
 return dict(streams=1,cells=n,positions='0..'+str(n-1),sequences=[0],layers=32,key_type='F16',value_type='F16',v_transposed=bool(trans),tensors=tensors)
def out(x):return {k:x[k] for k in ['ids','eog','length','terminal_id','stop_reason','cap']}
def first(a,b):
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:return i
 return min(len(a),len(b)) if len(a)!=len(b) else None
def distance(a,b):
 fa=struct.unpack('<128256f',a);fb=struct.unpack('<128256f',b);d=[abs(x-y) for x,y in zip(fa,fb)]
 return dict(bitwise_equal=a==b,differing_fp32_values=sum(x!=y for x,y in zip(fa,fb)),max_abs=max(d),rms=math.sqrt(math.fsum(t*t for t in d)/len(d)))
def compare_slots(actual,expected):
 assert len(actual)==len(set(actual))==len(expected)==len(set(expected)) and set(actual)==set(expected),'Missing/duplicate/extra request coordinate'
def audit(root,output,models=True):
 plan=load(root/'PLAN.json');f0a=load(root/'F0A.json');auth=load(root/'F0A_AUTHENTICATED.json')
 assert auth['status']=='PASS_ACTUAL_AUTHENTICATED_GITHUB_BYTES' and auth['before_new_forward']
 assert f0a['forward_calls_before_seal']==0 and f0a['plan_sha256']==digest(plan) and f0a['inputs_file_sha256']==sha(root/'INPUTS.json')
 for p in f0a['runtime_files']:assert (root/p['path']).stat().st_size==p['bytes'] and sha(root/p['path'])==p['sha256'],p['path']
 cap=load(root/'F0A_CAPSULE.json')
 assert (root/'F0A_SOURCE.zip').stat().st_size==cap['bytes'] and sha(root/'F0A_SOURCE.zip')==cap['sha256']
 with zipfile.ZipFile(root/'F0A_SOURCE.zip') as z:
  assert z.testzip() is None and len(z.namelist())==cap['files']
  for p in f0a['runtime_files']:assert z.read(p['path'])==(root/p['path']).read_bytes()
 cases=load(root/'INPUTS.json')['cases'];case={c['id']:c for c in cases}
 assert len(cases)==7 and [c['id'] for c in cases if c['role']=='stable_gt128']==['GSM8K/test/1011','GSM8K/test/1249']
 affected=case['GSM8K/test/1248']['prompt_ids'];assert len(affected)==161
 for n in [127,128,129]:assert case['FIXED_PREFIX_1248/'+str(n)]['prompt_ids']==affected[:n]
 records=load(root/'STUDY_RECORDS.json')
 expected=[s['slot'] for b in plan['blocks'] for s in b['slots']]
 compare_slots([r['slot'] for r in records],expected);assert len(records)==63
 ledger=[json.loads(t) for t in (root/'LEDGER.jsonl').read_text().splitlines()]
 compare_slots([r['slot'] for r in ledger if r['event']=='REQUEST_STARTED'],expected)
 compare_slots([r['slot'] for r in ledger if r['event']=='REQUEST_COMPLETED'],expected)
 assert not any(r['event']=='REQUEST_FAILED' for r in ledger)
 assert [r['slot'] for r in ledger if r['event']=='PROBE_STARTED']==['p0_probe_A']
 assert [r['slot'] for r in ledger if r['event']=='PROBE_COMPLETED']==['p0_probe_A']
 frozen_time=__import__('datetime').datetime.fromisoformat(f0a['utc'])
 assert all(__import__('datetime').datetime.fromisoformat(r['started_utc'])>frozen_time for r in records)
 life=[load(p) for p in sorted((root/'raw').glob('*/LIFECYCLE.json'))]
 assert len(life)==10 and all(p['returncode']==0 and not p['failed'] for p in life)
 seconds=sum(p['owned_seconds'] for p in life);assert seconds<=3600
 comp=load(root/'STUDY_COMPLETION.json');assert comp['requests_started']==comp['requests_completed']==63 and comp['retries']==comp['warmups']==comp['forks']==0 and comp['zero_forward_load_probes']==1 and math.isclose(seconds,comp['owned_gpu_seconds'])
 probe=load(root/'raw/p0_probe_A/PROBE_COMPLETE.json');assert probe['forward_calls']==probe['target_graphs']==probe['draft_graphs']==0
 preflight=load(root/'ASSET_PREFLIGHT.json');assert preflight['status']=='PASS' and preflight['numeric_DLLs_unchanged']
 for m in preflight['models']:
  if models:assert Path(m['path']).stat().st_size==m['bytes'] and sha(m['path'])==m['sha256']
 # Independent module/B570/GPU-buffer/KV admission + raw FIFO identity.
 minhead=10**30
 for p in sorted((root/'raw').glob('*/IDENTITY.json')):
  ident=load(p);pid=ident['owned_pid'];d=p.parent
  for m in ident['modules']:assert sha(root/'build/Release'/Path(m['path'].replace(chr(92),'/')).name)==m['sha256']
  assert len(ident['contexts'])==len(ident['weight_maps'])==1 and ident['contexts'][0]['outputs_max']==1
  for w in ident['weight_maps']:assert w['pid']==pid and w['all_weights_Vulkan0'] and all(t['backend_device']=='Vulkan0' and t['gpu_backend_buffer'] for t in w['tensors'])
  assert len(ident['kv_lines'])==1 and 'Vulkan0' in ident['kv_lines'][0]
  for m in ident['memory']:memory(m,pid);minhead=min(minhead,m['device_local_headroom_bytes'])
  events=[json.loads(t) for t in (d/'stdout.jsonl').read_text().splitlines()]
  ready=[t for t in events if t['event']=='READY'];assert len(ready)==1 and ready[0]['pid']==pid and ready[0]['forward_calls']==0
  actual=[t for t in events if t['event']=='RESULT'];stored=[load(root/r['raw_path']) for r in records if r['owned_pid']==pid and root/r['identity_path']==p]
  assert actual==stored,'hidden/cropped/FIFO-different native RESULT'
 data={};state={};geometry_rows=[];kv_layouts={}
 for r in records:
  assert r['status']=='COMPLETED' and not r['paid_formal_latency'] and r['source_commit']==auth['commit'] and r['identity_sha256']==sha(root/r['identity_path'])
  x=load(root/r['raw_path']);assert sha(root/r['raw_path'])==r['raw_sha256'] and sha(root/r['evidence_path'])==r['evidence_sha256']
  c=case[r['task']];a=plan['arms'][r['arm']];req=load((root/r['raw_path']).with_name(x['request_id']+'.REQUEST.json'))
  assert req['request_id']==x['request_id'] and req['prompt_ids']==c['prompt_ids'] and req['prefill_partition']==a['partition'] and not req['own_bind_sham']
  endpoint(x,c['prompt_ids'],a['ub'],r['owned_pid'])
  assert x['workload']['counter_semantics_sha256']==sha(root/'COUNTER_SEMANTICS.json')
  assert x['partition98']['external_submission_limit']==a['partition']
  n=c['prompt_length'];assert n==len(c['prompt_ids']) and x['workload']['target_prefill_calls']==math.ceil(n/a['partition'])
  want=collections.Counter(str(min(a['ub'],len(c['prompt_ids'][pos:pos+a['partition']])-i)) for pos in range(0,n,a['partition']) for i in range(0,len(c['prompt_ids'][pos:pos+a['partition']]),a['ub']))
  assert x['workload']['target_prefill_physical_width_hist']==dict(want)
  ev=load(root/r['evidence_path']);mem=ev['memory'] if r['observation_mode']=='heavy' else ev
  assert not mem['violation']
  for m in mem['samples']:memory(m,r['owned_pid']);minhead=min(minhead,m['device_local_headroom_bytes'])
  k=(r['task'],r['arm'],r['repeat']);data[k]=x
  geometry_rows.append(dict(slot=r['slot'],prefill_calls=x['workload']['target_prefill_calls'],prefill_physical_width_hist=dict(want),prefill_graphs=sum(want.values()),continuation_graphs=len(x['ids'])-1))
  if r['repeat']==0:assert not x['phase96']['diagnostic_capture'] and not x['phase96']['boundaries'] and not x['partition98']['full_payloads'];continue
  assert r['observation_mode']=='heavy' and req['capture'] and x['phase96']['diagnostic_capture'] and not x['phase96']['own_bind_sham']
  pre=geometry(ev,x,c['prompt_ids'],a['ub'],a['partition'])
  bs=x['phase96']['boundaries'];assert [b['output_index_zero_based'] for b in bs]==[i for i in c['boundary_cuts'] if i<len(x['ids'])]
  assert list(x['partition98']['full_payloads'])==[str(b['output_index_zero_based']) for b in bs]
  for b in bs:
   cut=b['output_index_zero_based'];assert b['naturally_committed_prefix_ids']==x['ids'][:cut] and b['sampled_top1_id']==x['ids'][cut]
   assert b['kv_min']==0 and b['kv_max']==n+cut-1 and b['actual_current_ub']==a['ub'] and b['output_capacity']==1 and b['own_path_binding_sham'] is None
   assert b['last_phase']==('PREFILL' if cut==0 else 'ORDINARY') and b['native_sample_output_row']==-1
   if cut:assert b['last_consumed_position']==n+cut-1 and b['last_consumed_input_ids']==[x['ids'][cut-1]]
   else:assert b['last_consumed_position']==pre[-1]['pos'] and b['last_consumed_input_ids']==pre[-1]['input_ids']
   p=x['partition98']['full_payloads'][str(cut)];lb=payload(root,p['logits']);assert p['logits']['sha256']==b['full_logits_sha256']
   vals,t1,t2=top2(lb);assert t1==b['sampled_top1_id'] and t2==b['top2_id']
   assert math.isclose(vals[t1],b['top1_logit'],abs_tol=1e-8) and math.isclose(vals[t2],b['top2_logit'],abs_tol=1e-8) and math.isclose(vals[t1]-vals[t2],b['top2_margin'],abs_tol=1e-8)
   if cut==0:
    kb=payload(root,p['sequence_KV']);assert p['sequence_KV']['sha256']==b['sequence_KV_sha256'] and len(kb)==b['sequence_KV_serialized_bytes']
    if p['sequence_KV']['sha256'] not in kv_layouts:kv_layouts[p['sequence_KV']['sha256']]=parse_kv(kb,n)
   else:assert p['sequence_KV'] is None
   state[(r['task'],r['arm'],r['repeat'],cut)]=(lb,b)
 # Historical proof is complete old native outputs, all10 repeats per path, never promoted to qualified stock.
 historical=load(root/'baseline/HISTORICAL_SELECTED.json')
 for pin in load(root/'baseline/HISTORICAL_NATIVE_PINS.json'):assert sha(root/pin['path'])==pin['sha256']
 for h in historical:
  native=load(root/'baseline'/h['raw_path'].replace('\\','/'))
  assert {k:native[k] for k in ['ids','length','terminal_id','stop_reason']}=={k:h['output'][k] for k in ['ids','length','terminal_id','stop_reason']}
  assert native['eog']==h['output']['eog_flags']
 result=[]
 for c in cases:
  tid=c['id'];xs={a:data[(tid,a,0)] for a in ['A','B','C']}
  for a in xs:assert all(out(data[(tid,a,r)])==out(xs[a]) for r in [1,2]),'observer/repeat full-output drift'
  refs={}
  for arm,cond in [('A','R_prod'),('C','R_stock')]:
   hh=[h for h in historical if h['task']==tid and h['condition']==cond]
   if c['role']!='threshold_fixed_prefix':
    assert len(hh)==10 and all(xs[arm]['ids']==h['output']['ids'] and xs[arm]['eog']==h['output']['eog_flags'] and xs[arm]['stop_reason']==h['output']['stop_reason'] and xs[arm]['length']==h['output']['length'] for h in hh),'historical reference changed'
    refs[arm]=dict(condition=cond,complete_old_native_requests=10,all_full_endpoints_equal=True)
   else:refs[arm]=None
  pairs=[]
  for a,b in [('A','B'),('B','C'),('A','C')]:
   cuts=[]
   for cut in c['boundary_cuts']:
    if (tid,a,1,cut) not in state or (tid,b,1,cut) not in state:
     cuts.append(dict(index=cut,status='NOT_REACHED_NATURAL_STOP'));continue
    la,ba=state[(tid,a,1,cut)];lb,bb=state[(tid,b,1,cut)]
    stable=all(state[(tid,a,2,cut)][1][h]==ba[h] and state[(tid,b,2,cut)][1][h]==bb[h] for h in ['full_logits_sha256','sequence_KV_sha256'])
    assert stable,'repeat numerical-state drift'
    kv_stats=None
    if cut==0:
     ta=kv_layouts[ba['sequence_KV_sha256']]['tensors'];tb=kv_layouts[bb['sequence_KV_sha256']]['tensors']
     diff=[dict(role=u['role'],layer=u['layer']) for u,w in zip(ta,tb,strict=True) if u['sha256']!=w['sha256']]
     kv_stats=dict(tensors_compared=64,tensors_with_different_bytes=len(diff),different_tensor_layers=diff)
    cuts.append(dict(prefill_KV_tensor_comparison=kv_stats,index=cut,natural_prefix_equal=ba['naturally_committed_prefix_ids']==bb['naturally_committed_prefix_ids'],logits=distance(la,lb),sequence_KV_bytes_equal=ba['sequence_KV_sha256']==bb['sequence_KV_sha256'],top1=[ba['sampled_top1_id'],bb['sampled_top1_id']],top2_margin=[ba['top2_margin'],bb['top2_margin']],full_logits_raw_rehashed=True,sequence_KV_raw_rehashed=cut==0,numeric_repeat_stable=stable))
   pairs.append(dict(pair=a+'/'+b,full_output_equal=out(xs[a])==out(xs[b]),first_differing_output_index=first(xs[a]['ids'],xs[b]['ids']),boundary_comparisons=cuts))
  ab,bc,ac=pairs
  state_equal=bc['boundary_comparisons'][0]['logits']['bitwise_equal'] and bc['boundary_comparisons'][0]['sequence_KV_bytes_equal']
  status='SUPPORTED_EXTERNAL_PREFILL_PARTITION_SUFFICIENT_ON_THIS_EXPOSED_INPUT' if not ab['full_output_equal'] and bc['full_output_equal'] and state_equal else 'REFUTED_EXTERNAL_PARTITION_SUFFICIENCY_ON_THIS_INPUT' if ab['full_output_equal'] and not ac['full_output_equal'] else 'NO_OUTPUT_TRIGGER_NUMERICAL_STATE_REPORTED' if all(p['full_output_equal'] for p in pairs) else 'PARTIAL_UNRESOLVED'
  result.append(dict(task=tid,role=c['role'],prompt_length=c['prompt_length'],status=status,pairs=pairs,historical_reference_guards=refs,all3_full_endpoint_repeats_equal=True,capture_off_on_guard=True,prefill_geometry=[dict(arm=a,external_calls=xs[a]['workload']['target_prefill_calls'],width_hist=xs[a]['workload']['target_prefill_physical_width_hist']) for a in ['A','B','C']]))
 # Preserve exact original qualification file and ancestry; no new cost ratio or deployed stock gate.
 baseline=load(root/'baseline/PR92_QUALIFICATION.json')
 qualification=dict(original_results_file_sha256=sha(root/'baseline/PR92_QUALIFICATION.json'),original_results=baseline,scope='Original PR92 stock qualification failures and null ratios preserved; new A/B/C exposed causality only',new_request_cost_qualified=False,physical_residency='UNKNOWN',model_timing='MODEL_TIMING_UNAVAILABLE',new_paid_requests=0)
 summary=dict(status='COMPLETED_INDEPENDENT_RAW_AUDIT',parent_head=plan['parent_head'],freeze_commit=auth['commit'],requests_started=63,requests_completed=63,zero_forward_load_probes=1,warmups=0,retries=0,forks=0,owned_native_lifetimes=10,owned_gpu_seconds=seconds,minimum_sampled_headroom_bytes=minhead,cases=result,causal_scope='A/B external prefill caller partition at fixed UB512; includes inherent invocation/scheduling effects; no kernel-only or state-to-output mediation/necessity claim',cost_scope='diagnostic elapsed only; original formal cost evidence unchanged')
 verification=dict(status='PASS',native_requests=63,independent_fresh_workers=9,raw_FIFO_results_exact=True,all_coordinate_coverage=True,full_EOG_CAP_endpoints=True,actual_B570_PID_placement_and_sampled_headroom=True,full_raw_FP32_and_prefill_sequence_KV_rehashed=True,kv_serialization_parsed=True,kv_unique_payloads=len(kv_layouts),models_full_rehashed=models,executor_imported=False,new_model_forwards=0)
 for name,x in [('RESULTS.json',summary),('QUALIFICATION.json',qualification),('WORK_WITNESSES.json',geometry_rows),('NUMERICAL_STATE_LAYOUTS.json',kv_layouts),('INDEPENDENT_VERIFICATION.json',verification)]:save(output/name,x)
 print(json.dumps(dict(status='PASS',requests=63,cases=[dict(task=c['task'],status=c['status'],AB=c['pairs'][0]['first_differing_output_index'],BC=c['pairs'][1]['full_output_equal'],BC_prefill_state_equal=c['pairs'][1]['boundary_comparisons'][0]['logits']['bitwise_equal'] and c['pairs'][1]['boundary_comparisons'][0]['sequence_KV_bytes_equal']) for c in result],owned_seconds=seconds,KV_unique_payloads=len(kv_layouts))))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True);p.add_argument('--skip-external-model-rehash',action='store_true');a=p.parse_args();audit(Path(a.root),Path(a.output),not a.skip_external_model_rehash)
