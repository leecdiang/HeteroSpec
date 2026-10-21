"""Independent read-only evidence contracts. No model execution."""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path,PureWindowsPath
import numpy as np
V=128256
CASES=('GSM8K/test/1248','GSM8K/test/831','GSM8K/test/1011','GSM8K/test/1249')
STATES=('EMPTY','K_layer0','V_layer0','KV_layer0','KV_prefix128','KV_tail128','ALL')
PANELS={'L0':('EMPTY','K_layer0','V_layer0','KV_layer0'),'POSITION':('EMPTY','KV_prefix128','KV_tail128','ALL')}
BASE101='26706c9fb4818ec3465e45acea029c4ab88a390f'
RESULT103='b46415f2725d7c06e093a6cd2b2d261b61925dc6'
REG103='dd33b24abebc335d39f3b63b4e7beff86bdcf934'
def require(ok,msg):
 if not ok:raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def encoded(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encoded(v))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def gitblob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def endpoint(x):return {k:x[k] for k in ('ids','eog','length','terminal_id','stop_reason','cap')}
def top2(z):
 require(z.shape==(V,) and np.isfinite(z).all(),'full finite FP32 vocabulary required')
 # stable sorting preserves ascending token ID on exact score ties.
 ids=np.argsort(-z.astype(np.float64),kind='stable')[:2];return tuple(map(int,ids))
class Resolver:
 def __init__(self,fresh,original):self.fresh=Path(fresh).resolve();self.original=str(original).replace('\\','/').rstrip('/');self.mapping={}
 def resolve(self,logical):
  s=str(logical).replace('\\','/');low=s.lower();prefix=self.original.lower()+'/'
  if PureWindowsPath(s).is_absolute() or Path(s).is_absolute():
   require(low.startswith(prefix),'absolute evidence path is not the pinned PR103 run: '+s);rel=s[len(prefix):]
  else:rel=s
  p=(self.fresh/rel).resolve();require(p.is_relative_to(self.fresh),'evidence path escape: '+s)
  self.mapping[s]=str(p);return p
 def payload(self,spec):
  p=self.resolve(spec['path']);b=p.read_bytes();require(len(b)==spec['bytes'] and digest(b)==spec['sha256'],'payload pin mismatch: '+str(p));return b
 def record_file(self,path,expected):
  p=self.resolve(path);require(sha(p)==expected,'raw/trace/identity hash mismatch: '+str(p));return read(p)
def validate_endpoint(x,prompt,pid,observation):
 require(x['event']=='RESULT' and x['pid']==pid and x['prompt_ids']==prompt,'native result coordinate/PID mismatch')
 e=endpoint(x);ids=e['ids'];flags=e['eog'];require(e['cap']==128 and 0<len(ids)<=128 and len(ids)==len(flags)==e['length'],'invalid endpoint length')
 require(all(type(i)is int and 0<=i<V for i in ids),'invalid token ID')
 require(flags==[i in (128001,128008,128009) for i in ids] and not any(flags[:-1]),'EOG mismatch')
 require(e['terminal_id']==ids[-1] and e['stop_reason']==('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids)==128),'stop mismatch')
 require(x['observation_mode']==observation and x['mode']=='ordinary','observer/mode mismatch')
 require(x['actual_condition']==dict(prefill_ub=512,continuation_ub=512,output_capacity=1,maximum_k=0,logical_batch=512,n_ctx=1024,threads=10,kv='F16',flash_attention=False),'wrong runtime recipe')
 require(not x['memory_violation'] and x['reset_target_min']==x['reset_target_max']==-1,'reset/memory violation')
 w=x['workload'];require(w['initial_target_committed']==1 and w['fallback_committed']==len(ids)-1 and w['sampling_calls']==len(ids),'committed/sampling accounting')
 require(w['target_prefill_calls']==0 and w['target_micrograph_rows']==len(ids)-1 and x['target_decode_calls']==len(ids)-1,'unexpected restored forward geometry')
 require(w['inherited_explicit_sync_calls']==3 and x['draft_decode_calls']==x['proposed']==x['accepted']==0,'extra forwards/draft')
 require(w['phase_binding_calls']==w['kv_trim_calls']==w['verify_cycles']==0,'unexpected intervention')
 p=x['restore100'];require(p and p['extra_forward_calls']==0 and p['clean_context_and_scheduler'],'restore guard')
 require(p['receiver_ub']==512 and p['capacity']==1 and p['KV_min']==0 and p['KV_max']==len(prompt)-1,'restore positions')
 require(p['committed_prefix']==[] and p['natural_first_id']==ids[0] and p['first_token_consumed_count']==1,'token zero restore anomaly')
 require(not x['operator100']['enabled'],'restore plus operator capture prohibited')
 return e
def validate_memory(m,pid):
 require(not m['violation'] and bool(m['samples']),'missing/failed memory proof')
 for s in m['samples']:
  require(s['pid']==pid and s['vendor_id']==0x8086 and s['device_id']==0xE20C and s['adapter_luid_valid'],'wrong process/device')
  h=[v for v in s['heaps'] if v['device_local']];require(len(h)==1 and h[0]['index']==0 and h[0]['physical_size_bytes']==10563354624,'wrong heap')
  require(s['device_local_headroom_bytes']==h[0]['budget_bytes']-h[0]['usage_bytes']>=536870912,'memory headroom')
def validate_channel(evidence,x,prompt,pid,mode):
 if mode=='counts':
  require('samples' in evidence and 'target' not in evidence,'counts must be memory.json, not heavy geometry');validate_memory(evidence,pid);return {'geometry_scope':'RESULT_AGGREGATE_ONLY_NO_FULL_TRACE'}
 require(mode=='heavy' and all(k in evidence for k in ('target','draft','verify','memory')),'heavy trace required')
 require(not evidence['draft'] and not evidence['verify'],'unexpected draft trace')
 ts=evidence['target'];require(len(ts)==len(x['ids'])-1 and all(t['phase']=='ORDINARY' for t in ts),'restored trace has prefill/extra calls')
 for i,t in enumerate(ts):
  require(t['pos']==len(prompt)+i and t['input_ids']==[x['ids'][i]],'different continuation prefix/position')
  require(t['logits_requested_positions']==[len(prompt)+i] and t['last_output_requested'] and not t['all_outputs'],'output geometry')
  require(t['physical_width_hist']=={'1':1} and t['successful_micrographs']==t['occupied_rows']==1 and t['ub']==512,'micrograph geometry')
  require(t['kv_min']==0 and t['kv_max']==t['pos'],'KV extent')
 validate_memory(evidence['memory'],pid);return {'geometry_scope':'FULL_HEAVY_TRACE'}
def validate_restore(x,resolver,kv_spec,logits_spec):
 p=x['restore100'];kb=resolver.payload(kv_spec);lb=resolver.payload(logits_spec)
 require(p['post_restore_KV_sha256']==digest(kb) and p['post_restore_logits_sha256']==digest(lb),'native state/logits import differs')
 require(digest(resolver.payload(p['KV_source']))==digest(kb) and digest(resolver.payload(p['logits_source']))==digest(lb),'source pin mismatch')
 z=np.frombuffer(lb,dtype='<f4');a,b=top2(z);require(a==x['ids'][0]==p['natural_first_id'],'token zero differs from fixed recipient initial logits')
 return {'t0_argmax':a,'t0_top2':b,'t0_source_sha256':digest(lb),'extra_forward_for_t0':0}
def logits_at(x,t,resolver,initial_spec):
 require(type(t)is int and 0<=t<len(x['ids']),'NOT_REACHED')
 if t==0:
  data=resolver.payload(initial_spec);z=np.frombuffer(data,dtype='<f4');a,b=top2(z);require(a==x['ids'][0],'RESTORE_T0_ANOMALY');return z,{'source':'PINNED_INITIAL_LOGITS','prefix':[],'sha256':digest(data),'position':None,'native_argmax':a,'top2':b}
 full=x['partition98']['full_payloads'];spec=full.get(str(t),{}).get('logits')
 if not spec:return None,{'status':'MISSING_FULL_LOGITS','t':t}
 require(spec['bytes']==V*4,'wrong full-logit size');data=resolver.payload(spec);z=np.frombuffer(data,dtype='<f4');a,b=top2(z)
 bs=[q for q in x['phase96']['boundaries'] if q['output_index_zero_based']==t];require(len(bs)==1,'missing/duplicate native snapshot')
 s=bs[0];require(s['naturally_committed_prefix_ids']==x['ids'][:t],'different naturally committed prefix')
 require(s['sampled_top1_id']==x['ids'][t]==a and s['top2_id']==b,'native sample/top2 mismatch')
 require(s['full_logits_sha256']==digest(data),'snapshot full-vector hash mismatch')
 require(s['last_consumed_input_ids']==[x['ids'][t-1]] and s['last_consumed_position']==len(x['prompt_ids'])+t-1,'snapshot position mismatch')
 require(float(z[a])==s['top1_logit'] and float(z[b])==s['top2_logit'],'snapshot FP32 values mismatch')
 return z,{'source':'RESULT.partition98.full_payloads','prefix':s['naturally_committed_prefix_ids'],'sha256':digest(data),'position':s['last_consumed_position'],'native_argmax':a,'top2':b}

def validate_new_receipt(r,s,run,f0,commit):
 require(r['status']=='COMPLETED' and r['slot']==s,'receipt does not match frozen plan slot')
 rec=r['record'];require(rec['slot']==s['slot'] and rec['task']==s['task'] and rec['repeat']==s['repeat'] and rec['source_commit']==commit,'new record coordinate/registration')
 res=Resolver(run,run);x=res.record_file(rec['raw_path'],rec['raw_sha256']);e=validate_endpoint(x,s['prompt_ids'],rec['owned_pid'],s['mode']);require(e==r['endpoint']==s['reference_endpoint'],'native endpoint/reference mismatch')
 req=read(res.resolve(rec['raw_path'].replace('.RESULT.json','.REQUEST.json')))
 require(req['request_id']==x['request_id'] and req['prompt_ids']==s['prompt_ids'] and req['cap']==128,'REQUEST/RESULT linkage')
 require(req['observation_mode']==s['mode'] and req['capture']==(s['mode']=='heavy') and req['phase96_diagnostic']==(s['mode']=='heavy') and req['boundary_cuts']==(s['cuts'] if s['mode']=='heavy' else []) and req['prefill_schedule']==[] and not req['operator_capture'] and not req['own_bind_sham'],'observation recipe')
 require(req['restore100']['KV']==s['mixture_spec'] and req['restore100']['logits']==s['initial_logits_spec'] and req['restore100']['donor_labels']==[s['state'],'recipient_'+s['recipient']],'restore direction/input specs')
 ev=res.record_file(rec['evidence_path'],rec['evidence_sha256']);require(rec['evidence_path'].endswith('.trace.json' if s['mode']=='heavy' else '.memory.json'),'wrong counts/heavy channel');validate_channel(ev,x,s['prompt_ids'],rec['owned_pid'],s['mode'])
 identity=res.record_file(rec['identity_path'],rec['identity_sha256']);require(identity['status']=='PASS' and identity['owned_pid']==rec['owned_pid'] and not identity['api_layer_loaded'],'native process identity')
 for m in identity['modules']:
  require(any(str(Path(p['path']).resolve()).lower()==str(Path(m['path']).resolve()).lower() and p['sha256']==m['sha256'] for p in f0['bindings']),'loaded runtime differs from F0')
 loaded=json.loads(res.resolve(str(Path(rec['identity_path']).parent/'MODULES.stdout')).read_text(encoding='utf-8-sig'));loaded=loaded if isinstance(loaded,list) else [loaded];loaded_paths={str(Path(p).resolve()).lower() for p in loaded}
 for p in f0['driver_module_pins']:require(str(Path(p['path']).resolve()).lower() in loaded_paths and sha(Path(p['path']))==p['sha256'],'wrong loaded Vulkan/driver module')
 life=read(res.resolve(str(Path(rec['identity_path']).parent/'LIFECYCLE.json')));require(life['pid']==rec['owned_pid'] and life['returncode']==0 and not life['failed'],'native lifecycle failed')
 led=[json.loads(v) for v in (Path(run)/'LEDGER.jsonl').read_text().splitlines()]
 for event,key in [('ATTEMPT_STARTED','slot'),('WORKER_STARTED','block'),('NATIVE_PROCESS_START_ATTEMPT','slot'),('OWNED_PID','block'),('REQUEST_STARTED','slot'),('REQUEST_COMPLETED','slot'),('WORKER_CLOSED','block'),('ATTEMPT_COMPLETED','slot')]:
  matches=[v for v in led if v['event']==event and v.get(key)==s['slot']];require(len(matches)==1,'missing/duplicate ledger linkage: '+event)
  if 'pid' in matches[0]:require(matches[0]['pid']==rec['owned_pid'],'ledger PID differs')
 for spec in (s['mixture_spec'],s['initial_logits_spec']):require(Path(spec['path']).stat().st_size==spec['bytes'] and sha(Path(spec['path']))==spec['sha256'],'frozen external mixture changed')
 p=x['restore100'];require(p['KV_source']==s['mixture_spec'] and p['logits_source']==s['initial_logits_spec'] and p['post_restore_KV_sha256']==s['mixture_spec']['sha256'] and p['post_restore_logits_sha256']==s['initial_logits_spec']['sha256'],'native restored input differs')
 z0=np.fromfile(s['initial_logits_spec']['path'],dtype='<f4');require(top2(z0)[0]==x['ids'][0],'RESTORE_T0_ANOMALY')
 if s['mode']=='heavy':
  for t in s['cuts']:z,proof=logits_at(x,t,res,s['initial_logits_spec']);require(z is not None,'missing planned native full logits')
 return x,rec,s

def validate_new_plan(plan):
 requests=plan['requests'];require(len(requests)==168 and len({s['slot'] for s in requests})==168,'duplicate/missing new slot')
 coords={(s['task'],s['recipient'],s['state'],s['mode'],s['repeat']) for s in requests}
 expected={(t,r,k,m,i) for t in CASES for r in ('A','B') for k in STATES for m,i in [('counts',0),('heavy',0),('heavy',1)]}
 require(coords==expected and len(coords)==168,'missing new matrix coordinate')
 for s in requests:
  require(s['donor']==('B' if s['recipient']=='A' else 'A') and s['direction']==s['donor']+'->'+s['recipient'],'direction reversed')
  require(s['slot']==digest(encoded({k:s[k] for k in ('task','recipient','state','stage','mode','repeat')}))[:24],'new slot hash changed')
 return requests
