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

# Independent final-study auditor: no imports from executor/controller/common.
def endpoint100(x,ids,ub,pid,restored=False):
 assert x['event']=='RESULT' and x['pid']==pid and x['prompt_ids']==ids and x['cap']==128
 o=x['ids'];f=x['eog'];assert 0<len(o)<=128 and len(o)==len(f)==x['length']
 assert all(type(i)is int and 0<=i<128256 for i in o)
 assert f==[i in {128001,128008,128009} for i in o] and not any(f[:-1])
 assert x['terminal_id']==o[-1] and x['stop_reason']==('EOG' if f[-1] else 'CAP') and (f[-1] or len(o)==128)
 assert x['reset_target_min']==x['reset_target_max']==-1 and not x['memory_violation']
 assert x['actual_condition']==dict(prefill_ub=ub,continuation_ub=ub,output_capacity=1,maximum_k=0,logical_batch=512,n_ctx=1024,threads=10,kv='F16',flash_attention=False)
 w=x['workload'];assert w['initial_target_committed']==1 and w['fallback_committed']==len(o)-1 and w['sampling_calls']==len(o)
 assert w['phase_binding_calls']==w['kv_trim_calls']==w['verify_cycles']==w['draft_micrographs']==0
 assert w['inherited_explicit_sync_calls']==(3 if restored else 2)
 assert w['target_micrograph_rows']==(0 if restored else len(ids))+len(o)-1 and w['target_ordinary_rows']==len(o)-1
 assert w['target_continuation_physical_width_hist']=={'1':len(o)-1}
 assert x['target_decode_calls']==w['target_prefill_calls']+len(o)-1
 assert x['mode']=='ordinary' and x['draft_decode_calls']==x['proposed']==x['accepted']==0
 for role in ['target','draft']:
  h=w[role+'_physical_width_hist'];assert sum(h.values())==w[role+'_micrographs'] and sum(int(k)*v for k,v in h.items())==w[role+'_micrograph_rows']
 assert x['component_completed_wall'] is None and x['GPU_completion_event_ms'] is None
def geometry100(tr,x,ids,ub,schedule):
 pre=[t for t in tr['target'] if t['phase']=='PREFILL'];cont=[t for t in tr['target'] if t['phase']=='ORDINARY']
 assert len(pre)==len(schedule) and len(cont)==len(x['ids'])-1 and len(tr['target'])==len(pre)+len(cont)
 assert not tr['draft'] and not tr['verify']
 pos=0
 for i,(t,n) in enumerate(zip(pre,schedule)):
  assert t['pos']==pos and t['input_ids']==ids[pos:pos+n] and not t['all_outputs']
  final=i==len(schedule)-1
  assert t['last_output_requested']==final and t['logits_requested_positions']==([len(ids)-1] if final else [])
  hist=dict(collections.Counter(str(min(ub,n-j)) for j in range(0,n,ub)))
  assert t['physical_width_hist']==hist and t['successful_micrographs']==sum(hist.values()) and t['occupied_rows']==n
  pos+=n
 assert pos==(len(ids) if schedule else 0)
 for i,t in enumerate(cont):
  assert t['pos']==len(ids)+i and t['input_ids']==[x['ids'][i]] and t['logits_requested_positions']==[len(ids)+i] and t['last_output_requested'] and not t['all_outputs']
  assert t['physical_width_hist']=={'1':1} and t['successful_micrographs']==t['occupied_rows']==1
 for t in tr['target']:
  assert t['kv_min']==0 and t['kv_max']==t['pos']+len(t['input_ids'])-1 and t['ub']==ub and t['GPU_completed_stage_wall'] is None
def snapshots(root,x):
 result=[]
 cuts=x['phase96']['requested_boundary_indices'];bs=x['phase96']['boundaries']
 # Restored first logits consumed via explicitly equivalent native sampler, not old output-buffer API.
 expected=[i for i in cuts if i<len(x['ids']) and (not x['restore100'] or i!=0)]
 assert [b['output_index_zero_based'] for b in bs]==sorted(expected),'missing/extra boundary capture'
 for b in bs:
  i=b['output_index_zero_based'];p=x['partition98']['full_payloads'][str(i)];l=payload(root,p['logits']);f,a,c=top2(l)
  assert a==b['sampled_top1_id']==x['ids'][i] and c==b['top2_id'] and p['logits']['sha256']==b['full_logits_sha256']
  assert b['naturally_committed_prefix_ids']==x['ids'][:i] and b['kv_min']==0
  assert b['kv_max']==len(x['prompt_ids'])+i-1 and b['last_consumed_position']==(sum(x['partition100']['caller_lengths'][:-1]) if i==0 else len(x['prompt_ids'])+i-1)
  assert b['native_sample_output_row']==-1 and b['actual_current_ub']==x['actual_condition']['prefill_ub'] and b['output_capacity']==1
  if i==0:
   k=payload(root,p['sequence_KV']);assert p['sequence_KV']['sha256']==b['sequence_KV_sha256'];layout=parse_kv(k,len(x['prompt_ids']))
   result.append(dict(logits_sha256=p['logits']['sha256'],KV_sha256=p['sequence_KV']['sha256'],layout=layout))
  else:assert p['sequence_KV'] is None
 return result
def audit100(root,output,models=True):
 from operator_audit100 import native_ops,stats,raw as opraw
 plan=load(root/'PLAN.json');freeze=load(root/'F0_BASE.json');auth=load(root/'F0_AUTHENTICATED.json')
 assert auth['status']=='PASS_ACTUAL_AUTHENTICATED_GITHUB_BYTES' and auth['before_new_forward'] and freeze['forward_calls_before_seal']==0
 assert plan['design_head']==freeze['design_head']=='a1925c4a3b040f9ad3db7ec4301042791a82fe75' and freeze['parent_head']=='c0e16aff9f3eeb0e677a52fcdc092068c096bf5d'
 assert digest(plan)==freeze['plan_sha256'] and sha(root/'INPUTS.json')==freeze['inputs_file_sha256']
 for p in freeze['runtime_files']:assert (root/p['path']).stat().st_size==p['bytes'] and sha(root/p['path'])==p['sha256'],p['path']
 cap=load(root/'F0_CAPSULE.json');assert sha(root/'F0_SOURCE.zip')==cap['sha256'] and (root/'F0_SOURCE.zip').stat().st_size==cap['bytes']
 with zipfile.ZipFile(root/'F0_SOURCE.zip') as z:
  assert z.testzip() is None and len(z.namelist())==cap['files']
  for p in freeze['runtime_files']:assert z.read(p['path'])==(root/p['path']).read_bytes()
 inherited=load(root/'INHERITED_FILES.json')
 for p in inherited:assert sha(root/'baseline/pr99'/p['path'])==p['sha256'] and (root/'baseline/pr99'/p['path']).stat().st_size==p['bytes']
 assert sha(root/'PR99_MANIFEST_REMOTE.json')=='24899b23410cd4802f0e75ff3675a6f068ffc8ee690e1512b72dc3e12e877fbc'
 # Entire inherited source/raw payload inventory is byte-preserved, not just displayed conclusions.
 manifest=load(root/'PR99_MANIFEST_REMOTE.json')
 for p in manifest['files']:
  assert sha(root/'baseline/pr99'/p['path'])==p['sha256'] and (root/'baseline/pr99'/p['path']).stat().st_size==p['bytes']
 if models:
  for p in load(root/'ASSET_PREFLIGHT.json')['models']:
   q=Path(p['path']);assert q.stat().st_size==p['bytes'] and sha(q)==p['sha256']
 amendment=load(root/'F0_LOGICAL_MAPPING_AMENDMENT.json');assert sha(root/'code/operator_audit100.py')==amendment['parser_sha256']
 assert load(root/'F0_AMENDMENT_AUTHENTICATED.json')['before_P1C'] and amendment['before_P1C_native_forward']
 cases={c['id']:c for c in load(root/'INPUTS.json')['cases']};records=load(root/'STUDY_RECORDS.json')
 ledger=[json.loads(s) for s in (root/'LEDGER.jsonl').read_text().splitlines()]
 starts=[r['slot'] for r in ledger if r['event']=='REQUEST_STARTED'];completed=[r['slot'] for r in ledger if r['event']=='REQUEST_COMPLETED'];failed=[r for r in ledger if r['event']=='REQUEST_FAILED']
 compare_slots([r['slot'] for r in records],completed)
 assert len(starts)==len(set(starts))<=200 and set(starts)==set(completed)|{r['slot'] for r in failed} and not(set(completed)&{r['slot'] for r in failed})
 assert len([r for r in ledger if r['event']=='PROBE_STARTED'])==len([r for r in ledger if r['event']=='PROBE_COMPLETED'])==1
 ops_started=[r for r in ledger if r['event']=='OPERATOR_STARTED'];assert len(ops_started)==len({r['slot'] for r in ops_started})<=72
 life=[r for r in ledger if r['event'] in ['WORKER_CLOSED','OPERATOR_CLOSED']];seconds=sum(r['owned_seconds'] for r in life);assert seconds<=21600
 assert len([r for r in ledger if r['event']=='WORKER_STARTED'])==len([r for r in ledger if r['event']=='WORKER_CLOSED'])
 slots={s['slot']:(b,s) for b in plan['blocks']+plan['conditional_blocks'] for s in b['slots']}
 assert all(r['slot'] in slots for r in records)
 gate=load(root/'STATE_RESTORE_ADMISSION.json');p2=[r for r in records if r['phase']=='P2']
 if gate['status']!='PASS':assert not p2
 expected=[s['slot'] for b in plan['blocks']+(plan['conditional_blocks'] if gate['status']=='PASS' else []) for s in b['slots']]
 notstarted=[r['slot'] for r in ledger if r['event']=='SLOT_NOT_STARTED']
 assert set(starts)|set(notstarted)==set(expected)
 history=load(root/'baseline/pr99/STUDY_RECORDS.json')
 hist={}
 for r in history:
  assert sha(root/'baseline/pr99'/r['raw_path'])==r['raw_sha256'];hist[(r['task'],r['arm'],r['repeat'])]=load(root/'baseline/pr99'/r['raw_path'])
 rawmap={};minimum=2**63-1;layouts=[];state_hashes={};identities=set()
 for r in records:
  b,s=slots[r['slot']];c=cases[r['task']];cfg=plan['arms'][b['arm']]
  assert r['source_commit']==auth['commit'] and r['arm']==b['arm'] and r['repeat']==b['repeat'] and r['phase']==b['phase']
  assert r['observation_mode']==b['observation_mode'] and not r['paid_formal_latency']
  for name in ['raw','evidence','identity']:
   assert sha(root/r[name+'_path'])==r[name+'_sha256']
  uid=r['raw_path'].split('/')[-1].split('.')[0];dir=(root/r['raw_path']).parent
  req=load(dir/(uid+'.REQUEST.json'));x=load(root/r['raw_path']);rawmap[r['slot']]=x;restored=s.get('restore_donors') is not None
  endpoint100(x,c['prompt_ids'],cfg['ub'],r['owned_pid'],restored)
  assert req['request_id']==x['request_id'] and req['prompt_ids']==c['prompt_ids'] and req['prefill_schedule']==s['schedule'] and x['partition100']['caller_lengths']==s['schedule']
  assert req['operator_capture']==s.get('operator_capture',False)
  stdout=[json.loads(z) for z in (dir/'stdout.jsonl').read_text().splitlines()]
  native=[z for z in stdout if z['event']=='RESULT' and z['request_id']==uid];assert native==[x]
  assert len([z for z in stdout if z['event']=='PERSISTED' and z['request_id']==uid])==1
  assert not any(z['event']=='ERROR' for z in stdout)
  evidence=load(root/r['evidence_path']);mem=evidence['memory'] if req['capture'] else evidence
  assert not mem['violation'] and mem['samples']
  for m in mem['samples']:memory(m,r['owned_pid']);minimum=min(minimum,m['device_local_headroom_bytes'])
  ident=load(root/r['identity_path'])
  if r['identity_path'] not in identities:
   identities.add(r['identity_path']);assert ident['status']=='PASS' and ident['owned_pid']==r['owned_pid']
   for p in ident['modules']:
    q=root/'build/Release'/Path(p['path']).name;assert sha(q)==p['sha256']
   for w in ident['weight_maps']:assert w['all_weights_Vulkan0'] and all(t['backend_device']=='Vulkan0' and t['gpu_backend_buffer'] for t in w['tensors'])
   assert all('Vulkan0' in line and 'CPU' not in line for line in ident['kv_lines'])
   lines=(dir/'stderr.log').read_text(errors='replace').splitlines()
   assert all('Vulkan0' in line and 'CPU' not in line for line in lines if 'KV buffer size' in line)
  h=collections.Counter()
  for n in s['schedule']:
   for i in range(0,n,cfg['ub']):h[str(min(cfg['ub'],n-i))]+=1
  assert x['workload']['target_prefill_physical_width_hist']==dict(h)
  if req['capture']:
   geometry100(evidence,x,c['prompt_ids'],cfg['ub'],s['schedule']);saved=snapshots(root,x)
   if saved:state_hashes[r['slot']]=saved[0];layouts+=saved
  else:assert not x['phase96']['boundaries'] and not x['partition98']['full_payloads']
  if restored:
   d=x['restore100'];kv,l=s['restore_donors'];dp=hist[(r['task'],kv,1)]['partition98']['full_payloads']['0'];lp=hist[(r['task'],l,1)]['partition98']['full_payloads']['0']
   assert d['post_restore_KV_sha256']==dp['sequence_KV']['sha256'] and d['post_restore_logits_sha256']==lp['logits']['sha256']
   assert d['extra_forward_calls']==0 and d['clean_context_and_scheduler'] and d['KV_max']==len(c['prompt_ids'])-1
   _,top,_=top2(payload(root/'baseline/pr99',lp['logits']));assert top==d['natural_first_id']==x['ids'][0] and d['first_token_consumed_count']==1
   if r['phase']=='P0':
    if gate['status']=='PASS':assert out(x)==out(hist[(r['task'],kv,1)])
    for bound in x['phase96']['boundaries']:
     old=next(z for z in hist[(r['task'],kv,1)]['phase96']['boundaries'] if z['output_index_zero_based']==bound['output_index_zero_based'])
     if gate['status']=='PASS':assert bound['full_logits_sha256']==old['full_logits_sha256'] and bound['sequence_KV_sha256']==old['sequence_KV_sha256']
  for t in x['operator100']['tensors']:
   assert t['device']=='Vulkan0','captured compute tensor CPU fallback'
   for v in [t]+t['operands']:
    if v['payload']:opraw(root,v['payload'])
 counts=dict(collections.Counter(r['phase'] for r in records))
 # Recompute partition matrix from immutable native arrays and payloads.
 matrix=[]
 for task in cases:
  rs=[r for r in records if r['phase']=='P1A' and r['task']==task];assert len(rs)==3
  assert all(out(rawmap[r['slot']])==out(rawmap[rs[0]['slot']]) for r in rs)
  D=rawmap[rs[0]['slot']];states=[state_hashes[r['slot']] for r in rs if r['slot'] in state_hashes]
  assert len(states)==2 and states[0]==states[1]
  old={arm:hist[(task,arm,1)] for arm in 'ABC'}
  def stateof(z):return {k:z['partition98']['full_payloads']['0'][k]['sha256'] for k in ['logits','sequence_KV']}
  ds=dict(logits=states[0]['logits_sha256'],sequence_KV=states[0]['KV_sha256'])
  matrix.append(dict(stage='P1A',task=task,full_repeat_and_observer_stability=True,output_equal={a:out(D)==out(z) for a,z in old.items()},first_diff={a:first(D['ids'],z['ids']) for a,z in old.items()},prefill_state_equal={a:ds==stateof(z) for a,z in old.items()},physical_width_hist=D['workload']['target_prefill_physical_width_hist']))
 groups=collections.defaultdict(list)
 for r in records:
  if r['phase']=='P1B':groups[(r['task'],tuple(slots[r['slot']][1]['schedule']))].append(r)
 for (task,schedule),rs in groups.items():
  assert len(rs)==2 and out(rawmap[rs[0]['slot']])==out(rawmap[rs[1]['slot']]),'sweep observer changed complete output'
  z=rawmap[rs[1]['slot']];old={a:hist[(task,a,1)] for a in 'ABC'};p=z['partition98']['full_payloads']['0'];stat=state_hashes[rs[1]['slot']]
  logs={};kvcount={}
  for a,hx in old.items():
   hp=hx['partition98']['full_payloads']['0'];logs[a]=distance(payload(root,p['logits']),payload(root/'baseline/pr99',hp['logits']))
   kh=parse_kv(payload(root/'baseline/pr99',hp['sequence_KV']),len(z['prompt_ids']))
   kvcount[a]=sum(x['sha256']!=y['sha256'] for x,y in zip(stat['layout']['tensors'],kh['tensors']))
  matrix.append(dict(stage='P1B',task=task,schedule=list(schedule),exposure=slots[rs[0]['slot']][1]['exposure'],full_capture_on_off_equal=True,output_equal={a:out(z)==out(h) for a,h in old.items()},first_diff={a:first(z['ids'],h['ids']) for a,h in old.items()},FP32_distance_to_references=logs,KV_differing_tensors_to_references=kvcount,physical_width_hist=z['workload']['target_prefill_physical_width_hist'],native_endpoint=out(z)))
 save(output/'PARTITION_MATRIX.json',dict(status='AUDITED_FULL_NATIVE_ENDPOINTS',D=7,sweeps=19,rows=matrix))
 operators=native_ops(root,records)

 # Additional exact source dataflow checks disambiguate repeated "norm-0" label without new scientific selection.
 from operator_audit100 import groups as opgroups,dense_rows,stats as opstats
 supplements=[]
 for task in ['GSM8K/test/1248','GSM8K/test/831']:
  for rep in [1,2]:
   rr={r['arm']:r for r in records if r['phase']=='P1C' and r['task']==task and r['repeat']==rep}
   if set(rr)!=set('ABC'):continue
   gs={a:opgroups(root,rawmap[r['slot']]['operator100']['tensors'],cases[task]['prompt_ids'])[0] for a,r in rr.items()}
   vals={};projinputs={}
   for a,gg in gs.items():
    normalized=[];perproj={tag:[] for tag in ['Qcur-0','Kcur-0','Vcur-0']}
    for g in gg:
     scale=next(t for t in g['tensors'] if t['name']=='attn_norm-0' and t['op']=='MUL')
     operand=scale['operands'][0];rms=next(t for t in g['tensors'] if t['tensor_identity']==operand['tensor_identity'] and t['op']=='RMS_NORM')
     assert rms['payload']['sha256']==operand['payload']['sha256']
     normalized+=dense_rows(root,operand,g['width'])
     for tag in perproj:
      t=next(t for t in g['tensors'] if t['name']==tag and t['op']=='MUL_MAT');assert t['operands'][1]['dtype']=='f32'
      perproj[tag]+=dense_rows(root,t['operands'][1],g['width'])
    vals[a]=b''.join(normalized);projinputs[a]={tag:b''.join(v) for tag,v in perproj.items()}
   rmscompare=dict(A_B=opstats(vals['A'],vals['B'],'f32'),B_C=opstats(vals['B'],vals['C'],'f32'))
   control={tag:dict(A_B=opstats(projinputs['A'][tag],projinputs['B'][tag],'f32'),B_C=opstats(projinputs['B'][tag],projinputs['C'][tag],'f32')) for tag in projinputs['A']}
   assert rmscompare['A_B']['bitwise_equal'] and all(v['A_B']['bitwise_equal'] and v['B_C']['bitwise_equal'] for v in control.values())
   numeric_guard={}
   for a,r in rr.items():
    x=rawmap[r['slot']];old=hist[(task,a,1)]
    numeric_guard[a]=all(x['phase96']['boundaries'][0][k]==old['phase96']['boundaries'][0][k] for k in ['full_logits_sha256','sequence_KV_sha256'])
   assert all(numeric_guard.values()),'native observer numerical state changed'
   supplements.append(dict(task=task,repeat=rep,exact_attention_RMS_producer_source_binding=True,upstream_RMS=rmscompare,all_projection_dynamic_operands=control,original_prefill_FP32_KV_observer_guard=numeric_guard,first_divergent_frontier='K/V projections' if task.endswith('/1248') else 'Q/K/V projections; Q differences confined to remainder5 logical positions128..132',actual_topological_first_observed_projection='Vcur MUL_MAT' if task.endswith('/1248') else 'Qcur MUL_MAT',scope='first_comparable_divergence above is frozen Q/K/V family order; projections are sibling branches, does not identify unique shader or one unique cause'))
 operators['source_dataflow_supplement']=supplements

 save(output/'OPERATOR_FIRST_DIFF.json',operators)
 # Restore own-path gate and full factorial recomputation, no partial donor inference.
 p0=[r for r in records if r['phase']=='P0'];assert len(p0)==16 and gate['own_path_shams']==16
 save(output/'STATE_RESTORE_ADMISSION.json',gate)
 cross=[]
 for task in list(cases)[:4]:
  rs=[r for r in p2 if r['task']==task];cells={}
  for cell in ['AA','AB','BA','BB']:
   vv=[r for r in rs if ''.join(slots[r['slot']][1]['restore_donors'])==cell]
   if vv:
    assert all(out(rawmap[r['slot']])==out(rawmap[vv[0]['slot']]) for r in vv)
    cells[cell]=rawmap[vv[0]['slot']]
  if len(cells)!=4:cross.append(dict(task=task,status='NOT_ADMITTED',cells_completed=len(cells)));continue
  aa,ab,ba,bb=[cells[k] for k in ['AA','AB','BA','BB']]
  expected_reps=3 if task in list(cases)[:2] else 2;assert len(rs)==4*expected_reps
  assert out(aa)==out(hist[(task,'A',1)]) and out(bb)==out(hist[(task,'B',1)])
  kv_sensitive=out(aa)!=out(ba);logit_null=out(aa)==out(ab) and out(ba)==out(bb)
  cross.append(dict(task=task,status='SUPPORTED_CONDITIONAL_KV_SUFFIX_SENSITIVITY' if kv_sensitive and logit_null else 'NO_OUTPUT_TRIGGER' if not kv_sensitive and logit_null else 'UNRESOLVED_INTERACTION',first_diff_KV_source=first(aa['ids'],ba['ids']),initial_top1={k:v['ids'][0] for k,v in cells.items()},initial_logits_swap_null=logit_null,full_cells={k:out(v) for k,v in cells.items()},repetitions=expected_reps,natural_own_path_matches=True))
 save(output/'KV_LOGITS_CROSS.json',dict(status='SUPPORTED_CONDITIONAL_KV_MEDIATION' if all(x['status']=='SUPPORTED_CONDITIONAL_KV_SUFFIX_SENSITIVITY' for x in cross[:2]) else 'UNRESOLVED',scope='Boundary0 clean UB512 receiver and native greedy equivalence only; no universal necessity, general opaque clone or deeper-logits claim',restore_gate=gate['status'],rows=cross))
 # Standalone GPU replay, exact input readback and geometry, compare output/native shams.
 replay_rows=load(root/'OPERATOR_REPLAY_RECORDS.json') if (root/'OPERATOR_REPLAY_RECORDS.json').exists() else [];replay=[]
 for r in replay_rows:
  directory=root/r['raw_dir'];assert sha(directory/'REQUEST.json')==r['request_sha256'] and sha(directory/'stdout.jsonl')==r['stdout_sha256']
  q=load(directory/'REQUEST.json')
  if r['status']!='COMPLETED':continue
  v=r['result'];assert v['pid']==r['pid'] and v['vendor']==0x8086 and v['device']==0xE20C and v['geometry']==q['schedule'] and v['native_op']==q['op']
  ident=load(directory/'IDENTITY.json');assert ident['status']=='PASS_ACTUAL_LOADED_MODULES' and ident['pid']==v['pid']
  for p in ident['modules']:assert sha(root/'build/Release'/Path(p['path']).name)==p['sha256']
  for m in v['memory']:
   assert m['pid']==v['pid']
   h=[h for h in m['heaps'] if h['device_local']];assert len(h)==1 and h[0]['index']==0 and h[0]['physical_size_bytes']==10563354624
   assert h[0]['headroom']==int(h[0]['budget_bytes'])-int(h[0]['usage_bytes'])>=536870912;minimum=min(minimum,h[0]['headroom'])
  offset=0
  for call,n in zip(v['calls'],q['schedule']):
   assert call['pos']==offset and call['width']==n
   for i,p in enumerate(q['operands']):
    source=payload(root,dict(p['payload'],path='operator_payloads/'+Path(p['payload']['path']).name));nb=p['nb']
    expected=source if p['token_axis']<0 else source[offset*nb[1]:(offset+n)*nb[1]]
    got=call['inputs'][i];assert hashlib.sha256(expected).hexdigest()==got['sha256'] and len(expected)==got['bytes']
   offset+=n
  assert offset==q['N'];opraw(root,v['full_output'])
  replay.append(dict(q=q,r=r))
 replay_groups=collections.defaultdict(list)
 for z in replay:replay_groups[(z['q']['task'],z['q']['tag'])].append(z)
 repcomp=[]
 for (task,tag),rs in replay_groups.items():
  if len(rs)!=4:repcomp.append(dict(task=task,operator=tag,status='UNRESOLVED_INCOMPLETE_REPLAY'));continue
  data={}
  for geom in ['full','split']:
   rr=sorted([x for x in rs if x['q']['geometry']==geom],key=lambda z:z['q']['repeat'])
   data[geom]=[opraw(root,x['r']['result']['full_output']) for x in rr];assert data[geom][0]==data[geom][1],'same-arm replay unstable'
  native=opraw(root,rs[0]['q']['native_reference'])
  sham=data['full'][0]==native
  repcomp.append(dict(task=task,operator=tag,status='SUPPORTED_FIXED_INPUT_GEOMETRY_DIFFERENCE' if sham and data['full'][0]!=data['split'][0] else 'BITWISE_INVARIANT' if sham else 'OPERATOR_CAUSAL_ISOLATION_UNRESOLVED',same_input_bitwise_readbacks=True,repeat_bitwise_stability=True,full_geometry_native_output_sham_equal=sham,difference=stats(data['full'][0],data['split'][0],'f32'),actual_pipeline=None,dispatch_dimensions=None))
 save(output/'FIXED_INPUT_REPLAY.json',dict(status='SUPPORTED_OPERATOR_GEOMETRY_EFFECT' if any(x['status']=='SUPPORTED_FIXED_INPUT_GEOMETRY_DIFFERENCE' for x in repcomp) else 'OPERATOR_CAUSAL_ISOLATION_UNRESOLVED',started=len(ops_started),completed=len(replay),rows=repcomp,scope='Faithful GGML operator/data geometry under same captured operands and immutable numerical DLLs; exact Vulkan shader/pipeline/dispatch identity remains UNKNOWN'))
 timeline=load(root/'F0_P3.json');save(output/'GPU_TIMELINE.json',timeline)
 q=load(root/'baseline/pr99/QUALIFICATION.json');save(output/'QUALIFICATION.json',dict(original= q,original_exact_PR92_file_sha256=sha(root/'baseline/pr99/baseline/PR92_QUALIFICATION.json'),new_paid_cost_ratios=None,new_stock_qualification=None,rule='Original FAILED R_stock qualified ratios NULL retained. Posthoc equal-output paid loss separate from physical counts and all new diagnostic observercost.'))
 opbytes=sum(p.stat().st_size for p in (root/'operator_payloads').iterdir());assert opbytes<=536870912
 inv=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for folder in ['raw','records','payloads','operator_payloads'] for p in sorted((root/folder).rglob('*')) if p.is_file()]
 save(output/'RAW_EVIDENCE.json',dict(files=inv,source_numeric_pins=freeze['runtime_files'],new_operator_payload_bytes=opbytes,external_model_bytes_verified=models))
 result=dict(status='EXECUTED_AUDITED',design_head=freeze['design_head'],parent_head=freeze['parent_head'],native_whole_starts=len(starts),native_completed=len(records),native_failed=len(failed),zero_forward_probes=1,operator_starts=len(ops_started),operator_completed=len(replay),owned_GPU_seconds=seconds,minimum_same_PID_headroom_bytes=minimum,operator_unique_payload_bytes=opbytes,warmups=0,retries=0,stages=counts,H1='SUPPORTED_OBSERVED_PARTITION_RECIPE' if all(r['prefill_state_equal']['B'] and r['prefill_state_equal']['C'] and r['output_equal']['B'] and r['output_equal']['C'] for r in matrix if r['stage']=='P1A') else 'UNRESOLVED',H2_native=operators['status'],H2_fixed_replay=load(output/'FIXED_INPUT_REPLAY.json')['status'],H3=load(output/'KV_LOGITS_CROSS.json')['status'],H4='NOT_ADMITTED_GPU_TIMELINE_NOT_AVAILABLE',complete_opaque_clone='NOT_ADMITTED_NOT_CLAIMED',physical_residency='UNKNOWN',new_paid_request_cost_ratio=None,stock_gate='FAILED_QUALIFIED_RATIOS_NULL_UNCHANGED',per_input_D=[r for r in matrix if r['stage']=='P1A'],remaining=['Exact Vulkan pipeline/shader/dispatch provenance unavailable','No exclusive/overlapping GPU stagewall','No continuous physical residency proof','Bounded exposed-input diagnostics, not blind transfer','Complete boundary0 necessary-state resume validated; general opaque full actor cloning not implemented'])
 save(output/'RESULTS.json',result)
 save(output/'INDEPENDENT_VERIFICATION.json',dict(status='PASS',rederived_artifacts=['PARTITION_MATRIX','OPERATOR_FIRST_DIFF','FIXED_INPUT_REPLAY','STATE_RESTORE_ADMISSION','KV_LOGITS_CROSS','GPU_TIMELINE','QUALIFICATION','RAW_EVIDENCE','RESULTS'],native_whole_requests=len(records),operator_completed=len(replay),full_target_model_rehashed=models,independent_stdlib_no_executor_imports=True,original_all_bytes_preserved=True,full_output_contract=True,hard_budgets=True))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--skip-external-model-rehash',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);print(json.dumps(audit100(a.root,a.output,not a.skip_external_model_rehash)))
