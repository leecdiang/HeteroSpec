"""Pure-file, staged replay of the frozen N1a raw-byte contract.

No subprocess/native imports. A PASS is PROVISIONAL_PROVIDED_BYTES_ONLY, never
native qualification or GPU admission. Worker source truth remains external.
"""
import copy,hashlib,json,math,os,pathlib,re,stat,struct

ROLES=('RESIDENT_R','REPEAT_RESIDENT_R','COLD_CANONICAL_ORACLE','STRONG_WHOLE_RECHUNK_LOOP4')
ALIASES={'R':ROLES[0],'REPEAT':ROLES[1],'COLD':ROLES[2],'STRONG':ROLES[3]}
COUNTS=(27,81,72,81)
EOG=(128247,151643,151645,151662,151663,151664)
PINS={'N1A_PROPOSAL_NOT_ADMITTED.json':'bf00a976a5f5385bd818bd58bdfcaa575e49f9548fee615320ed9b1d86194892','REQUIRED_COVERAGE.json':'b28a8ba5337707a4e11f7a920ea665e6f4030a4028395158b9857101e201f8b2'}
CONTROL_TEMPLATE_PIN='4287bde0bfb1b34b35fbd2a4b0d9ef39106e1fefa864eea760196ecbc3c063ac'
CHUNK=1024*1024
class Invalid(ValueError):pass
def need(ok,message):
 if not ok:raise Invalid(message)
def integer(x,low=0):
 need(type(x) is int and low<=x<=9007199254740991,'invalid bounded integer');return x
def ids(x):
 need(type(x) is list,'dense token array required')
 for t in x:need(type(t) is int and 0<=t<151936,'invalid bound token ID')
 return x
def digest(b):return hashlib.sha256(b).hexdigest()
def normalized(x):return digest((json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n').encode())
def sha(x):need(type(x) is str and re.fullmatch('[0-9a-f]{64}',x),'invalid SHA256');return x
def parse_json(b):
 def pairs(ps):
  out={}
  for k,v in ps:need(k not in out,'duplicate JSON member');out[k]=v
  return out
 def bad(x):raise Invalid('non-JSON constant '+x)
 return json.loads(b.decode('utf8',errors='strict') if isinstance(b,bytes) else b,object_pairs_hook=pairs,parse_constant=bad)
def shape(t):
 need(type(t) is dict and t.get('dtype') in ('F16LE','F32LE'),'unsupported exact dtype')
 s,a=t.get('shape'),t.get('axes');need(type(s) is list and type(a) is list and len(s)==len(a)>0,'tensor dimensions/axes')
 need(all(type(x) is str and x for x in a) and len(set(a))==len(a),'invalid/duplicate axes')
 n=1
 for d in s:n*=integer(d);integer(n)
 scalar=2 if t['dtype']=='F16LE' else 4;need(type(t.get('bytes')) is int and t['bytes']==n*scalar,'tensor byte count differs');sha(t.get('sha256'));return n,scalar,n*scalar
def validate_snapshot(s):
 need(s.get('schema')=='hs.N1a.raw-state.v1','unknown snapshot schema');p=s.get('phase');need(p in ('POST_RECONCILE','POST_APPEND','TERMINAL','RESET'),'unknown phase')
 need(s.get('path_kind') in ('RESIDENT','COLD_ORACLE'),'path kind');cohort=s.get('cohort');need(cohort in ('NATURAL','SCRIPTED_CONTROL'),'cohort')
 modes=('FREE_SEQUENTIAL','CANONICAL_INPUT_ORACLE_REPLAY') if cohort=='NATURAL' else ('SCRIPTED_STATE_CONTROL','SCRIPTED_CONTROL_ORACLE')
 need(s.get('execution_mode')==modes[s['path_kind']=='COLD_ORACLE'],'execution mode');need(type(s.get('generation_cap')) is int and s['generation_cap']==(128 if cohort=='NATURAL' else 1),'generation cap')
 for k in ('run_id','operation_id','context_id'):need(type(s.get(k)) is str and s[k],'capture identity')
 for k in ('contract_sha256','model_sha256','tokenizer_sha256','template_sha256','producer_sha256'):sha(s['identity'][k])
 for k in ('executable_sha256','capture_writer_sha256'):sha(s['provenance'][k])
 for k in ('canonical_ids','materialized_ids','logical_ids','generated_ids'):ids(s[k])
 q,m,l,g=s['canonical_ids'],s['materialized_ids'],s['logical_ids'],s['generated_ids'];h=integer(s['head']);need(h<=4096 and h==len(m),'actual materialized head')
 if p!='RESET':need(q and len(q)+s['generation_cap']-1<=4096,'canonical capacity')
 need(len(l)-h in (0,1) and l[:h]==m,'logical/materialized prefix')
 pending=s['pending'];need(pending is None if len(l)==h else type(pending) is dict and type(pending.get('id')) is int and type(pending.get('position')) is int and pending=={'id':l[-1],'position':h},'pending identity/position')
 f=s['frontier'];need(type(f.get('valid')) is bool and type(f.get('owned')) is bool,'frontier flags')
 v=s['requested_vector_positions'];o=s['owned_vector_ids'];need(type(v) is list and all(type(x) is int and 0<=x<h for x in v),'requested row coordinate')
 need(type(o) is list and len(o)==len(v) and all(type(x) is str and x for x in o) and len(set(o))==len(o),'owned row IDs')
 need((h>0 and type(f.get('position')) is int and f['position']==h-1 and f['owned']) if f['valid'] else f.get('position') is None,'frontier coordinate/ownership')
 if p=='POST_RECONCILE':
  need(m==q[:h] and not g and pending is None,'reconciled prefix')
  need((not f['valid'] and not v) if s['path_kind']=='RESIDENT' else v==([h-1] if f['valid'] else []),'reconciled output mask')
 elif p=='POST_APPEND':need(q==m==l and not g and f['valid'] and v==[h-1],'postappend state/output mask')
 elif p=='TERMINAL':
  need(0<len(g)<=s['generation_cap'] and l==q+g and pending is not None,'terminal logical/pending')
  need(v==list(range(len(q)-1,len(q)-1+len(g))) and f['valid'],'complete sampling rows/frontier')
  need(not any(t in EOG for t in g[:-1]),'continued after EOG')
  need((g[-1] in EOG) if s.get('stop_reason')=='EOG' else s.get('stop_reason')=='CAP' and len(g)==s['generation_cap'] and not any(t in EOG for t in g),'stop/EOG/cap')
 else:need(h==0 and not l and not q and not g and pending is None and not f['valid'] and not v,'reset not empty')
 for k in ('active_k','active_v'):
  t=s['tensors'][k];shape(t);need(t['dtype']=='F16LE' and t['shape']==[36,8,h,128] and t['axes']==['layer','kv_head','position','dimension'],'full active KV layout')
 t=s['tensors']['vectors'];shape(t);need(t['dtype']=='F32LE' and t['shape']==[len(v),151936] and t['axes']==['requested_row','vocabulary'],'complete output vectors')
 return s

class RawChecker:
 """Strict bytes+finiteness, including signed-zero differences; no hash-only pass."""
 def __init__(self,root):self.root=pathlib.Path(root).absolute()
 @staticmethod
 def identity(s):return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns
 def stable_end(self,f,name,before):need(self.identity(before)==self.identity(os.fstat(f.fileno()))==self.identity(self.path(name).stat()),'evidence changed during raw comparison')
 def path(self,name):
  need(type(name) is str and name and '\\' not in name and not name.startswith('/'),'unsafe capture path');parts=name.split('/')
  need(all(x not in ('','.','..') and re.fullmatch('[A-Za-z0-9_.-]+',x) for x in parts),'unsafe path component')
  need(self.root.is_dir() and not self.root.is_symlink(),'capture root invalid');p=self.root
  for x in parts:p=p/x;need(not p.is_symlink(),'symlink evidence path')
  need(p.is_file() and self.root.resolve() in p.resolve().parents,'outside/nonfile evidence');return p
 def open(self,name):
  self.path(name);parts=name.split('/');flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0);directory=os.open(self.root,flags|os.O_DIRECTORY)
  try:
   for part in parts[:-1]:
    nextfd=os.open(part,flags|os.O_DIRECTORY,dir_fd=directory);os.close(directory);directory=nextfd
   fd=os.open(parts[-1],flags,dir_fd=directory)
  finally:os.close(directory)
  if not stat.S_ISREG(os.fstat(fd).st_mode):os.close(fd);raise Invalid('nonregular opened evidence')
  return os.fdopen(fd,'rb')
 def read(self,name,maximum=1024*1024):
  with self.open(name) as f:
   a=os.fstat(f.fileno());need(a.st_size<=maximum,'bounded file exceeded');b=f.read(maximum+1);z=os.fstat(f.fileno());linked=self.path(name).stat()
  identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns)
  need(identity(a)==identity(z)==identity(linked) and len(b)==a.st_size,'file changed/short read');return b
 def json(self,name,maximum=1024*1024):
  b=self.read(name,maximum);return parse_json(b),digest(b)
 def hash_file(self,name,expected_bytes=None,finite_dtype=None,maximum=700000000):
  h=hashlib.sha256();count=0
  scalar=2 if finite_dtype=='F16LE' else 4
  with self.open(name) as f:
   a=os.fstat(f.fileno());need(a.st_size<=maximum,'raw file exceeds bounded envelope');need(expected_bytes is None or a.st_size==expected_bytes,'raw file size differs')
   for b in iter(lambda:f.read(CHUNK),b''):
    h.update(b);count+=len(b);need(count<=maximum,'raw file grew beyond envelope')
    if finite_dtype:
     need(len(b)%scalar==0,'partial scalar')
     for (bits,) in struct.iter_unpack('<H' if scalar==2 else '<I',b):need((bits&(0x7c00 if scalar==2 else 0x7f800000))!=(0x7c00 if scalar==2 else 0x7f800000),'nonfinite raw scalar')
   z=os.fstat(f.fileno())
  linked=self.path(name).stat();identity=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns)
  need(identity(a)==identity(z)==identity(linked) and count==a.st_size,'raw file changed/short read');return h.hexdigest()
 def snapshot(self,d):
  s,h=self.json(d['file']);need(h==sha(d['sha256']),'snapshot transport digest');validate_snapshot(s)
  need((s['run_id'],s['operation_id'],s['phase'],s['provenance']['executable_sha256'])==(d['run_id'],d['operation_id'],d['phase'],sha(d['executable_sha256'])),'snapshot descriptor binding');return s
 def tensor(self,a,b):
  na,scalar,n=shape(a);shape(b)
  if [a[k] for k in ('dtype','shape','axes')]!=[b[k] for k in ('dtype','shape','axes')]:return {'status':'CONTRACT_CONFLICT','reason':'tensor coordinates/dtype/shape differ'}
  ap,bp=self.path(a['file']),self.path(b['file']);need(ap.stat().st_size==bp.stat().st_size==n,'raw length mismatch');ha,hb=hashlib.sha256(),hashlib.sha256();first=None;bad=None;differences=0;compared=0
  with self.open(a['file']) as af,self.open(b['file']) as bf:
   astat,bstat=os.fstat(af.fileno()),os.fstat(bf.fileno());need(astat.st_size==bstat.st_size==n,'opened raw size differs')
   for off in range(0,n,CHUNK):
    wanted=min(CHUNK,n-off);ab,bb=af.read(wanted),bf.read(wanted);need(len(ab)==len(bb)==wanted,'short raw read');ha.update(ab);hb.update(bb)
    for j in range(0,wanted,scalar):
     av=int.from_bytes(ab[j:j+scalar],'little');bv=int.from_bytes(bb[j:j+scalar],'little');mask=0x7c00 if scalar==2 else 0x7f800000
     ix=(off+j)//scalar
     if (av&mask)==mask or (bv&mask)==mask:
      if bad is None:bad={'scalar_index':ix,'coordinate':self.coordinate(ix,a)}
     if av!=bv:
      differences+=1
      if first is None:first={'scalar_index':ix,'byte_offset':off+j,'coordinate':self.coordinate(ix,a),'left_hex':ab[j:j+scalar].hex(),'right_hex':bb[j:j+scalar].hex()}
    compared+=wanted
   self.stable_end(af,a['file'],astat);self.stable_end(bf,b['file'],bstat)
  need(ha.hexdigest()==a['sha256'] and hb.hexdigest()==b['sha256'],'raw transport SHA mismatch')
  return {'status':'NUMERIC_FAIL' if first is not None or bad is not None else 'PASS','comparison':'STRICT_FULL_RAW_BYTES_AND_FINITE_VALUES_NO_TOLERANCE','bytes_compared':compared,'scalars_compared':na,'bit_different_scalars':differences,'first_difference':first,'first_nonfinite':bad,'hash_only_numerical_pass':False}
 @staticmethod
 def coordinate(index,t):
  out={}
  for axis,size in reversed(list(zip(t['axes'],t['shape']))):out[axis]=index%size;index//=size
  return out
 def aligned(self,c):
  a,b=self.snapshot(c['left']),self.snapshot(c['right'])
  if any(a.get(k)!=b.get(k) for k in ('identity','phase','cohort','canonical_ids')):return {'status':'CONTRACT_CONFLICT','reason':'input/producer/phase identity differs'}
  if any(a.get(k)!=b.get(k) for k in ('materialized_ids','logical_ids','generated_ids','head','pending','stop_reason','generation_cap')):return {'status':'STATE_FAIL','reason':'tokens/materialized/pending/stop differ'}
  if a['phase']!='POST_RECONCILE' and any(a.get(k)!=b.get(k) for k in ('requested_vector_positions','frontier')):return {'status':'STATE_FAIL','reason':'complete output mask/frontier differs'}
  keys=('active_k','active_v') if a['phase']=='POST_RECONCILE' else ('active_k','active_v','vectors');t={k:self.tensor(a['tensors'][k],b['tensors'][k]) for k in keys}
  return {'status':'PASS' if all(v['status']=='PASS' for v in t.values()) else 'NUMERIC_FAIL','tensors':t,'scope':'ALIGNED_ACTIVE_KV_ONLY_INVALID_RESIDENT_FRONTIER_NOT_COMPARED' if a['phase']=='POST_RECONCILE' else 'ALL_ACTIVE_KV_AND_COMPLETE_REQUESTED_VOCABULARY_ROWS'}
 def retained_tensor(self,a,b,oldhead,keep):
  shape(a);shape(b);astat,bstat=self.path(a['file']).stat(),self.path(b['file']).stat();need(self.hash_file(a['file'],a['bytes'])==a['sha256'] and self.hash_file(b['file'],b['bytes'])==b['sha256'],'retained transport SHA')
  need(self.identity(astat)==self.identity(self.path(a['file']).stat()) and self.identity(bstat)==self.identity(self.path(b['file']).stat()),'retained file changed during transport read')
  first=None;bad=None;different=0;compared=0
  with self.open(a['file']) as af,self.open(b['file']) as bf:
   need(self.identity(astat)==self.identity(os.fstat(af.fileno())) and self.identity(bstat)==self.identity(os.fstat(bf.fileno())),'retained file replaced after transport read')
   for layer in range(36):
    for head in range(8):
     af.seek((layer*8+head)*oldhead*256);bf.seek((layer*8+head)*keep*256)
     for off in range(0,keep*256,CHUNK):
      n=min(CHUNK,keep*256-off);ab,bb=af.read(n),bf.read(n);need(len(ab)==len(bb)==n,'short retained raw read')
      for j in range(0,n,2):
       av,bv=int.from_bytes(ab[j:j+2],'little'),int.from_bytes(bb[j:j+2],'little');coordinate={'layer':layer,'kv_head':head,'position':(off+j)//256,'dimension':((off+j)//2)%128}
       if (av&0x7c00)==0x7c00 or (bv&0x7c00)==0x7c00:
        if bad is None:bad={'coordinate':coordinate}
       if av!=bv:
        different+=1
        if first is None:first={'coordinate':coordinate,'left_hex':ab[j:j+2].hex(),'right_hex':bb[j:j+2].hex()}
      compared+=n
   self.stable_end(af,a['file'],astat);self.stable_end(bf,b['file'],bstat)
  return {'status':'NUMERIC_FAIL' if first is not None or bad is not None else 'PASS','bytes_compared':compared,'retained_positions':keep,'first_difference':first,'first_nonfinite':bad,'bit_different_scalars':different,'hash_only_numerical_pass':False}
 def prefix(self,c):
  a,b=self.snapshot(c['previous']),self.snapshot(c['current']);need((a['phase'],b['phase'],a['path_kind'],b['path_kind'])==('TERMINAL','POST_RECONCILE','RESIDENT','RESIDENT'),'retention lifecycle')
  if any(a[k]!=b[k] for k in ('identity','run_id','context_id','cohort')):return {'status':'CONTRACT_CONFLICT','reason':'not same live context/producer/cohort'}
  r,h=self.json(c['transition_receipt']['file']);need(h==sha(c['transition_receipt']['sha256']),'reconcile transport SHA')
  need(r['schema']=='hs.N1a.reconcile-receipt.v1' and (r['run_id'],r['context_id'],r['source_operation_id'],r['operation_id'])==(a['run_id'],a['context_id'],a['operation_id'],b['operation_id']),'reconcile identity')
  need((r['previous_snapshot_sha256'],r['current_snapshot_sha256'])==(c['previous']['sha256'],c['current']['sha256']),'reconcile snapshot binding');need(integer(a['event_ordinal'])<integer(b['event_ordinal']),'reconcile order')
  for field in ('actual_head_before','actual_keep','actual_model_rows_before_append'):integer(r[field])
  need(r['old_frontier_invalidated'] is True,'frontier invalidation flag')
  if r['old_pending_id'] is not None:need(type(r['old_pending_id']) is int and 0<=r['old_pending_id']<151936,'pending receipt token ID')
  lcp=0
  while lcp<min(len(a['logical_ids']),len(b['canonical_ids'])) and a['logical_ids'][lcp]==b['canonical_ids'][lcp]:lcp+=1
  keep=min(lcp,a['head']);replay=keep==len(b['canonical_ids']);keep-=int(replay);mode='LAST_TOKEN_REPLAY' if replay else 'DIRECT_APPEND' if lcp==len(a['logical_ids']) and keep==a['head'] else 'LCP_TRIM_REPLAY'
  if r['fallback_reason'] is not None:need(a['head']>keep and r['fallback_reason'] in ('TRIM_CAPABILITY_UNSUPPORTED','CALLER_INJECTED_TRIM_FAILURE_BEFORE_NATIVE_MUTATION'),'unapproved native-failure retry');keep=0;mode='COMMON_FULL_REBUILD'
  need((r['mode'],r['actual_head_before'],r['actual_keep'],b['head'],r['actual_model_rows_before_append'],r['old_frontier_invalidated'])==(mode,a['head'],keep,keep,0,True),'reconcile policy/head/frontier')
  need(b['materialized_ids']==a['materialized_ids'][:keep],'retained tokens changed')
  pending='NONE' if a['pending'] is None else 'DISCARD_OLD_PENDING_WITH_RESET' if mode=='COMMON_FULL_REBUILD' else 'REPLAY_OLD_PENDING_ONCE_AT_CANONICAL_POSITION' if lcp>a['head'] else 'DISCARD_OLD_PENDING_NOT_IN_REUSED_PREFIX'
  need(r['old_pending_id']==(a['pending']['id'] if a['pending'] else None) and r['pending_disposition']==pending,'pending disposition')
  t={k:self.retained_tensor(a['tensors'][k],b['tensors'][k],a['head'],keep) for k in ('active_k','active_v')};return {'status':'PASS' if all(x['status']=='PASS' for x in t.values()) else 'NUMERIC_FAIL','tensors':t,'keep':keep,'token_lcp':lcp,'mode':mode,'frontier_equivalence':'NOT_CLAIMED_OLD_FRONTIER_INVALIDATED'}
 def ownership(self,c):
  o=c['origin'];s=self.snapshot(o['snapshot']);row=integer(o['requested_row_index']);need(row<len(s['requested_vector_positions']) and s['frontier']['valid'] and s['frontier']['owned'],'ownership source row')
  integer(o['vector_position'])
  need(s['owned_vector_ids'][row]==o['ownership_id'] and s['requested_vector_positions'][row]==o['vector_position'] and o['next_operation_id']!=s['operation_id'],'owned origin binding')
  events=[]
  for key,phase in [('before_event','BEFORE_NEXT_MUTATION'),('after_event','AFTER_NEXT_MUTATION')]:
   e,h=self.json(c[key]['file']);need(h==sha(c[key]['sha256']),'owned event SHA')
   need(e['schema']=='hs.N1a.owned-vector-event.v1' and e['phase']==phase,'owned event lifecycle')
   need((e['run_id'],e['context_id'],e['source_operation_id'],e['next_operation_id'])==(s['run_id'],s['context_id'],s['operation_id'],o['next_operation_id']),'owned event identity')
   integer(e['source_requested_row_index']);integer(e['source_vector_position'])
   need((e['source_snapshot_sha256'],e['source_requested_row_index'],e['source_vector_position'],e['ownership_id'])==(o['snapshot']['sha256'],row,o['vector_position'],o['ownership_id']),'owned source row binding')
   need(e['caller_owned'] is True and e['capture_writer_sha256']==s['provenance']['capture_writer_sha256'],'owned writer/copy identity');integer(e['event_ordinal']);shape(e['tensor']);need(e['tensor']['dtype']=='F32LE' and e['tensor']['shape']==[1,151936] and e['tensor']['axes']==['requested_row','vocabulary'],'complete owned row');events.append(e)
  m,h=self.json(c['mutation_receipt']['file']);need(h==sha(c['mutation_receipt']['sha256']),'mutation SHA');need(m['schema']=='hs.N1a.mutation-receipt.v1' and (m['run_id'],m['context_id'],m['operation_id'],m['source_operation_id'])==(s['run_id'],s['context_id'],o['next_operation_id'],s['operation_id']),'mutation identity')
  integer(m['actual_decode_calls'],1);need(integer(m['actual_model_rows'],1)<=4096 and m['status']=='COMPLETE','bounded completed mutation')
  need(integer(s['event_ordinal'])<events[0]['event_ordinal']<integer(m['begin_event_ordinal'])<=integer(m['end_event_ordinal'])<events[1]['event_ordinal'],'ownership before/decode/after order')
  t=s['tensors']['vectors'];shape(t);source_stat=self.path(t['file']).stat();need(self.hash_file(t['file'],t['bytes'])==t['sha256'],'owned source raw SHA')
  with self.open(t['file']) as f:
   need(self.identity(source_stat)==self.identity(os.fstat(f.fileno())),'owned source changed after transport read');f.seek(row*151936*4);source=f.read(151936*4);self.stable_end(f,t['file'],source_stat)
  result=self.tensor(events[0]['tensor'],events[1]['tensor']);before=self.read(events[0]['tensor']['file'],151936*4)
  if source!=before:return {'status':'NUMERIC_FAIL','reason':'before ownership copy differs from actual full source row','source_row_bytes_compared':len(source),'before_after':result}
  return dict(result,source_row_bytes_compared=len(source),scope='COMPLETE_SOURCE_ROW_AND_SAME_OWNERSHIP_BEFORE_AFTER_PROVIDED_DECODE_RECEIPTS')
 def reset(self,c):
  s=self.snapshot(c['capture']);need(s['phase']=='RESET','reset phase')
  for t in s['tensors'].values():need(shape(t)[2]==0 and self.hash_file(t['file'],0)==t['sha256'],'reset nonempty raw file')
  return {'status':'PASS','scope':'EMPTY_RESET_METADATA_AND_ZERO_LENGTH_RAW_FILES_NO_FORWARD','head':0,'tensors':{k:{'status':'EMPTY_FILE_VERIFIED','bytes_compared':0,'comparison':'ACTUAL_ZERO_LENGTH_FILE_AND_EMPTY_STATE_METADATA_NOT_A_SELF_PAIR_NUMERICAL_PROOF'} for k in ('active_k','active_v','vectors')}}
 def compare(self,c):
  try:return dict({'ALIGNED_STATE':self.aligned,'PREFIX_RETENTION':self.prefix,'OWNED_VECTOR_STABILITY':self.ownership,'RESET_EMPTY_CHECK':self.reset}[c['scope']](c),id=c['id'],input_scope=c['scope'],bindings=c['bindings'])
  except (Invalid,KeyError,OSError,ValueError,TypeError,struct.error) as e:return {'id':c.get('id'),'status':'INVALID_CAPTURE','reason':str(e),'input_scope':c.get('scope'),'bindings':c.get('bindings')}

class StageVerifier:
 """Actual WorkerCapture inventory implementation follows below; no GPU authority."""
 def __init__(self,repo_root,capture_root,manifest):
  need(type(manifest) is dict,'explicit JSON admission manifest object required')
  self.repo=pathlib.Path(repo_root).absolute();self.root=pathlib.Path(capture_root).absolute();self.manifest=copy.deepcopy(manifest);self._manifest_fingerprint=normalized(self.manifest)
  self.frozen=self.repo/'benchmarks/server_expansion_v1/N/n1a_lifecycle_20261112';self.proposal=None;self.graph=None
  for file,want in PINS.items():
   b=(self.frozen/file).read_bytes();need(digest(b)==want,'frozen proposal/graph changed')
   if file.startswith('N1A_'):self.proposal=parse_json(b)
   else:self.graph=parse_json(b)
  need(len(self.graph['checks'])==261,'required graph count');self.operations={o['id']:o for o in self.proposal['operations']}
  b=(self.repo/'benchmarks/server_expansion_v1/N/native_chain_successor_20261112/NATIVE_JOB_TEMPLATE.json').read_bytes();need(digest(b)==CONTROL_TEMPLATE_PIN,'frozen exact control token template changed');template=parse_json(b)
  self.control_operations={o['id']:o for j in template['jobs'] for e in j['episodes'] if e['kind']=='SCRIPTED_RAW_TOKEN_CONTROL' for o in e['operations']}
  need(len(self.control_operations)==40,'exact control fixture count')
 def stage_checks(self,stage):
  role=ALIASES.get(stage,stage);need(role in ROLES,'unknown stage');out=[]
  for c in self.graph['checks']:
   b=c['bindings'];op=b['right']['operation_id'] if c['scope']=='ALIGNED_STATE' else b['previous']['operation_id'] if c['scope']=='PREFIX_RETENTION' else b['source']['operation_id'] if c['scope']=='OWNED_VECTOR_STABILITY' else b['capture']['operation_id']
   if self.operations[op]['path']==role:out.append(c)
  need(len(out)==COUNTS[ROLES.index(role)],'stage graph derivation');return role,out
 def verify_sealed(self,files):
  base={'schema':'hs.N1controller.prior-file-seal-replay.v1','scope':'PROVIDED_FILE_HASH_IDENTITY_ONLY_NO_NUMERICAL_QUALIFICATION','native_qualified':False,'admission_authorized':False,'files_checked':0,'first_difference':None}
  try:
   need(normalized(self.manifest)==self._manifest_fingerprint,'constructor manifest mutated');need(type(files) is dict and 0<len(files)<=8192,'nonempty bounded prior file seal required');files=copy.deepcopy(files);rc=RawChecker(self.root)
   for name,want in files.items():
    sha(want);actual=rc.hash_file(name)
    if actual!=want:return dict(base,status='FAIL',first_difference={'file':name,'expected_sha256':want,'actual_sha256':actual},files_checked=base['files_checked']+1)
    base['files_checked']+=1
   return dict(base,status='PASS')
  except (Invalid,OSError,ValueError,TypeError) as e:return dict(base,status='BLOCKED',first_difference={'kind':'INVALID_OR_MISSING_PRIOR_FILE_SEAL','reason':str(e)})
 def inventory(self,role):
  allowed=set(ROLES[:ROLES.index(role)+1]);ops={k:v for k,v in self.operations.items() if v['path'] in allowed};states_expected=set();owned_expected={};retained_expected={};events_expected=set();producers_expected={k:v for k,v in ops.items() if not v['control'] and v['path']!=ROLES[2]}
  def add(b):
   if b['operation_id'] in ops:states_expected.add((b['operation_id'],b['phase']))
  for c in self.graph['checks']:
   b=c['bindings'];scope=c['scope']
   if scope=='ALIGNED_STATE':add(b['left']);add(b['right'])
   elif scope=='PREFIX_RETENTION':
    add(b['previous']);add(b['current'])
    if b['previous']['operation_id'] in ops:retained_expected[(b['previous']['operation_id'],b['current']['operation_id'])]=c
   elif scope=='OWNED_VECTOR_STABILITY':
    add(b['source'])
    if b['source']['operation_id'] in ops:
     edge=(b['source']['operation_id'],b['mutation_operation_id']);owned_expected[edge]=c
     for p in ('BEFORE_NEXT_MUTATION','AFTER_NEXT_MUTATION'):events_expected.add((*edge,p))
   else:add(b['capture'])
  need(len(states_expected)==63*len(allowed) and len(events_expected)==18*len(allowed),'stage inventory derivation')
  run=self.manifest.get('run_id');need(type(run) is str and run,'independently bound run ID absent')
  bindings=self.manifest.get('worker_bindings');need(type(bindings) is dict,'independently bound worker identities absent')
  worker_keys={p+'/'+cohort for p in allowed for cohort in ('NATURAL','CONTROL')}
  for k in worker_keys:
   bind=bindings.get(k);need(type(bind) is dict,'worker binding absent: '+k)
   for field in ('source_sha256','executable_sha256','writer_sha256'):sha(bind.get(field))
   for field in ('contract_sha256','model_sha256','tokenizer_sha256','template_sha256','producer_sha256'):sha(bind['identity'].get(field))
   need(bind['identity']['model_sha256']==self.proposal['freezes']['model_sha256'] and bind['identity']['template_sha256']==self.proposal['freezes']['template_sha256'],'bound model/template changed')
  rc=RawChecker(self.root);need(self.root.is_dir() and not self.root.is_symlink(),'capture root invalid')
  rootstat=self.root.stat();states={};events={};retained={};mutations={};owned={};producers={};contexts={};context_worker={};hashes={};raw_files=set();rawbytes=0
  def key_for(op):return ops[op]['path']+('/CONTROL' if ops[op]['control'] else '/NATURAL')
  def bound(v,op):
   need(op in ops,'unplanned/future operation');worker=key_for(op);bind=bindings[worker]
   need(v.get('run_id')==run and type(v.get('context_id')) is str and v['context_id'],'run/context binding')
   if worker in contexts:need(contexts[worker]==v['context_id'],'context recreated inside worker')
   else:contexts[worker]=v['context_id']
   if v['context_id'] in context_worker:need(context_worker[v['context_id']]==worker,'context shared by workers')
   else:context_worker[v['context_id']]=worker
   return bind
  def read_json(name,maxbytes=1024*1024):
   self._inventory_current_file=name;raw=rc.read(name,maxbytes);hashes[name]=digest(raw);return parse_json(raw),hashes[name],raw
  def raw_tensor(t,folder):
   nonlocal rawbytes
   self._inventory_current_file=t.get('file',folder)
   need(t.get('canonical_numeric') is True,'opaque/noncanonical tensor');shape(t)
   need(pathlib.PurePosixPath(t['file']).parent.as_posix()==folder and re.fullmatch('[A-Za-z0-9_-]+\\.bin',pathlib.PurePosixPath(t['file']).name),'tensor not owned by capture directory')
   need(t['file'] not in raw_files,'tensor file reused across captures');raw_files.add(t['file'])
   h=rc.hash_file(t['file'],t['bytes'],t['dtype']);need(h==t['sha256'],'raw transport SHA');hashes[t['file']]=h;rawbytes+=t['bytes']
  for p in sorted(self.root.iterdir(),key=lambda x:x.name):
   self._inventory_current_file=p.name
   need(not p.is_symlink(),'symlink root entry');name=p.name;need(re.fullmatch('[A-Za-z0-9_.-]+',name),'unsafe root name')
   if p.is_dir():
    before=p.stat();files=list(p.iterdir());names={x.name for x in files};need(all(x.is_file() and not x.is_symlink() for x in files),'nested/nonfile/symlink capture')
    need(not names.intersection({'CAPTURE_OPEN','UNCERTAIN','POISON','POISONED'}),'uncommitted/uncertain/poisoned capture')
    need({'SNAPSHOT.json','COMPLETE.json','TRANSPORT.pending'}<=names,'partial capture commit')
    s,sh,_=read_json(name+'/SNAPSHOT.json');c,ch,cb=read_json(name+'/COMPLETE.json');t,th,tb=read_json(name+'/TRANSPORT.pending')
    need(cb==tb and c==t,'COMPLETE/pending bytes differ');need(c.get('schema')=='hs.N1chain.raw-transport.v1' and c.get('native_qualified') is False and c.get('snapshot_sha256')==sh,'transport commit/schema')
    isstate=s.get('schema')=='hs.N1a.raw-state.v1'
    if isstate:
     validate_snapshot(s);integer(s['event_ordinal'],1);op=s['operation_id'];semantic=(op,s['phase']);need(semantic in states_expected and semantic not in states,'duplicate/unplanned state')
     expected_dir=digest((op+'/'+s['phase']).encode())[:24]+'-'+s['phase'];tensors=list(s['tensors'].values());need(set(s['tensors'])=={'active_k','active_v','vectors'},'state tensor names')
    else:
     need(s.get('schema')=='hs.N1a.owned-vector-event.v1','unknown capture schema');op=s['source_operation_id'];semantic=(op,s['next_operation_id'],s['phase']);need(semantic in events_expected and semantic not in events,'duplicate/unplanned ownership event')
     expected_dir=digest((op+'/'+s['next_operation_id']+'/'+s['phase']).encode())[:24]+'-'+s['phase'];tensors=[s['tensor']]
    need(name==expected_dir,'noncanonical writer capture ID');bind=bound(c,op)
    need(c['source_sha256']==bind['source_sha256'] and c['executable_sha256']==bind['executable_sha256'] and c['capture_writer_sha256']==bind['writer_sha256'],'independently frozen transport source/ELF/writer differs')
    need(c['run_id']==s['run_id'] and c['context_id']==s['context_id'],'transport/snapshot run/context')
    if isstate:
     o=ops[op];need(s['identity']==bind['identity'] and s['provenance']=={'executable_sha256':bind['executable_sha256'],'capture_writer_sha256':bind['writer_sha256']},'state identity/provenance')
     need(s['path_kind']==('COLD_ORACLE' if o['path']==ROLES[2] else 'RESIDENT') and s['cohort']==('SCRIPTED_CONTROL' if o['control'] else 'NATURAL') and s['generation_cap']==o['response_cap'],'planned path/cohort/cap')
     if o['control']:
      fixed=self.control_operations[op]
      if s['phase']!='RESET':need(s['canonical_ids']==fixed['canonical_ids'],'frozen exact raw-token control changed')
      if s['phase']=='TERMINAL':need(s['generated_ids']==fixed['forced_terminal_ids'],'frozen scripted terminal tape changed')
     need(c['operation_id']==op,'state charged operation')
    else:
     need(c['operation_id']==(op if s['phase']=='BEFORE_NEXT_MUTATION' else s['next_operation_id']),'event charged operation');need(s['capture_writer_sha256']==bind['writer_sha256'] and s['caller_owned'] is True,'event writer/copy');integer(s['event_ordinal'],1)
    need(type(c.get('tensors')) is list and len(c['tensors'])==len(tensors),'transport tensor count');byfile={x['file']:x for x in c['tensors']};need(len(byfile)==len(tensors),'duplicate transport tensor')
    for tensor in tensors:need(byfile.get(tensor['file'])==tensor,'transport tensor descriptor differs');raw_tensor(tensor,name)
    need(names=={'SNAPSHOT.json','COMPLETE.json','TRANSPORT.pending'}|{pathlib.PurePosixPath(x['file']).name for x in tensors},'extra committed capture file')
    after=p.stat();need((before.st_dev,before.st_ino,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_mtime_ns),'capture directory changed')
    descriptor={'operation_id':s.get('operation_id'),'phase':s['phase'],'run_id':run,'file':name+'/SNAPSHOT.json','sha256':sh,'executable_sha256':bind['executable_sha256']} if isstate else {'file':name+'/SNAPSHOT.json','sha256':sh}
    (states if isstate else events)[semantic]={'value':s,'descriptor':descriptor,'transport':c}
   else:
    need(p.is_file() and re.fullmatch('[0-9a-f]{32}\\.json',name),'unexpected root marker/file');v,h,raw=read_json(name);schema=v.get('schema');producer=schema=='hs.N1chain.actual-producer.v1';need(producer or len(raw)<=65536,'nonproducer receipt exceeds64KiB')
    if producer:
     op=v['operation_id'];need(op in producers_expected and op not in producers,'duplicate/unplanned/cold producer');tag='PRODUCER';table=producers;k=op;bind=bound(v,op)
     need(v['source_sha256']==bind['source_sha256'] and v['identity']==bind['identity'] and v['role']==ops[op]['path'] and v['mode']=='ACTUAL_FREE_SEQUENTIAL_PRODUCER' and v['native_qualified'] is False,'producer source/identity/mode')
    elif schema=='hs.N1a.reconcile-receipt.v1':
     op=v['operation_id'];k=(v['source_operation_id'],op);need(k in retained_expected and k not in retained,'duplicate/unplanned reconcile');tag='RECONCILE';table=retained;bound(v,op)
    elif schema=='hs.N1a.mutation-receipt.v1':
     op=v['operation_id'];k=op;need((v['source_operation_id'],op) in owned_expected and op not in mutations,'duplicate/unplanned mutation');tag='MUTATION';table=mutations;bound(v,op)
    else:
     need(schema=='hs.N1chain.owned-required-binding.v1' and v['scope']=='OWNED_VECTOR_STABILITY','unknown root receipt');k=(v['origin']['snapshot']['operation_id'],v['origin']['next_operation_id']);need(k in owned_expected and k not in owned,'duplicate/unplanned ownership binding');op=k[1];tag='OWNERSHIP_CHECK';table=owned
    need(name==digest((op+'/'+tag).encode())[:32]+'.json','noncanonical root receipt ID');table[k]={'value':v,'descriptor':{'file':name,'sha256':h}}
  need(set(states)==states_expected,'missing stage state checkpoints');need(set(events)==events_expected,'missing stage ownership events');need(set(retained)==set(retained_expected),'missing reconcile receipts');need(set(owned)==set(owned_expected),'missing ownership bindings');need(set(mutations)=={e[1] for e in owned_expected},'missing mutation receipts');need(set(producers)==set(producers_expected),'missing producer receipts');need(set(contexts)==worker_keys and len(set(contexts.values()))==len(worker_keys),'registered worker context set incomplete/shared')
  def state(b):return states[(b['operation_id'],b['phase'])]
  for edge,entry in owned.items():
   self._inventory_current_file=entry['descriptor']['file']
   v=entry['value'];s=states[(edge[0],'TERMINAL')];need(v['origin']['snapshot']==s['descriptor'],'owned origin discovered descriptor differs');last=len(s['value']['requested_vector_positions'])-1
   need(v['origin']['requested_row_index']==last and v['origin']['vector_position']==s['value']['requested_vector_positions'][last] and v['origin']['ownership_id']==s['value']['owned_vector_ids'][last],'ownership must use last requested actual row')
   need(v['before_event']==events[(*edge,'BEFORE_NEXT_MUTATION')]['descriptor'] and v['after_event']==events[(*edge,'AFTER_NEXT_MUTATION')]['descriptor'] and v['mutation_receipt']==mutations[edge[1]]['descriptor'],'ownership receipt cross-binding differs')
  for edge,entry in retained.items():
   self._inventory_current_file=entry['descriptor']['file']
   r=entry['value'];need((r['previous_snapshot_sha256'],r['current_snapshot_sha256'])==(states[(edge[0],'TERMINAL')]['descriptor']['sha256'],states[(edge[1],'POST_RECONCILE')]['descriptor']['sha256']),'reconcile discovered binding')
  self._producers(producers,states,ops)
  after=self.root.stat();need((rootstat.st_dev,rootstat.st_ino,rootstat.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_mtime_ns),'capture root changed during inventory')
  return {'states':states,'owned':owned,'retained':retained,'hashes':hashes,'summary':{'states':len(states),'events':len(events),'reconcile_receipts':len(retained),'mutation_receipts':len(mutations),'ownership_bindings':len(owned),'producer_receipts':len(producers),'worker_contexts':len(contexts),'raw_files':len(raw_files),'raw_bytes_hashed_and_finite_checked':rawbytes,'inventory_sha256':normalized(hashes)}}
 def _producers(self,producers,states,ops):
  for op,entry in producers.items():
   self._inventory_current_file=entry['descriptor']['file']
   v=entry['value'];o=ops[op];ids(v['canonical_ids']);ids(v['previous_actual_generated_ids']);need(v['canonical_ids'] and len(v['canonical_ids'])+127<=4096,'producer capacity')
   for f in ('prompt_utf8','history_json','runtime_parser_state_json','wire_response_json','parser_input_hex','previous_stop_reason'):need(type(v.get(f)) is str,'producer complete string absent')
   need(re.fullmatch('(?:[0-9a-f]{2})*',v['parser_input_hex']) is not None,'producer parser hex');rt=parse_json(v['runtime_parser_state_json'])
   prompt='<|im_start|>assistant\n<think>\n\n</think>\n\n';need(rt['format_name']=='peg-native' and rt['generation_prompt']==prompt and rt['generation_prompt_hex']==prompt.encode().hex(),'actual parser/prefill binding')
   need(rt['additional_stops']==[] and rt['preserved_tokens']==['<think>','</think>','<tool_call>','</tool_call>'],'effective stop/preserved tokens')
   need(rt['profile']=={'use_jinja':True,'enable_thinking':False,'reasoning_format':'deepseek','stream':False,'explicit_stop_strings':[],'tools':[],'add_generation_prompt':True,'parse_special':True,'add_special':False},'producer fixed profile');need(type(rt['parser_serialized']) is str and rt['parser_serialized'],'actual parser absent');parse_json(rt['parser_serialized'])
   need(all(type(rt['profile'][k]) is bool for k in ('use_jinja','enable_thinking','stream','add_generation_prompt','parse_special','add_special')),'producer profile boolean types')
   user={'role':'user','content':self.proposal['source_episodes'][o['episode']]['users'][o['turn']]['content']};need(v['next_user']==user,'frozen natural user changed');history=parse_json(v['history_json']);need(type(history) is list,'history array')
   for phase in ('POST_RECONCILE','POST_APPEND','TERMINAL'):
    s=states[(op,phase)]['value'];need((v['identity'],v['canonical_ids'],v['run_id'],v['context_id'])==(s['identity'],s['canonical_ids'],s['run_id'],s['context_id']),'producer/state binding')
   if o['turn']==0:
    need(history==[user] and not v['previous_actual_generated_ids'] and v['previous_stop_reason']=='' and v['previous_cap'] is None and v['wire_response_json']=='' and v['parser_input_hex']=='','initial producer spurious history')
    need(normalized(v['canonical_ids'])==self.proposal['first_prompt_bindings'][o['source_root']]['ids_sha256'],'initial canonical IDs differ')
   else:
    oldid=op[:-1]+'0';s=states[(oldid,'TERMINAL')]['value'];need((v['previous_actual_generated_ids'],v['previous_stop_reason'],v['previous_cap'])==(s['generated_ids'],s['stop_reason'],s['generation_cap']),'producer did not consume actual previous terminal')
    wire=parse_json(v['wire_response_json']);message=wire['choices'][0]['message'];need(type(message['content']) is str,'wire assistant content');assistant={'role':'assistant','content':message['content']}
    if message.get('reasoning_content'):need(type(message['reasoning_content']) is str,'reasoning content');assistant['reasoning_content']=message['reasoning_content']
    need(history==parse_json(producers[oldid]['value']['history_json'])+[assistant,user],'stored history not actual wire history')
   if o['path']!=ROLES[0]:
    peer=op.replace('/'+o['path']+'/','/'+ROLES[0]+'/');r=producers[peer]['value']
    for f in ('canonical_ids','prompt_utf8','history_json','runtime_parser_state_json','parser_input_hex','previous_actual_generated_ids','previous_stop_reason','previous_cap','next_user'):need(v[f]==r[f],'producer contract conflict: '+f)
    if o['turn']==1:
     a,b=parse_json(v['wire_response_json'])['choices'][0],parse_json(r['wire_response_json'])['choices'][0];need((a['message'],a['finish_reason'])==(b['message'],b['finish_reason']),'wire message/finish reason differs')
 def verify(self,stage):
  self._inventory_current_file=None;role,checks=self.stage_checks(stage);base={'schema':'hs.N1controller.stage-provided-raw.v1','stage':role,'scope':'PROVISIONAL_PROVIDED_BYTES_ONLY','native_qualified':False,'admission_authorized':False,'exact_check_ids':[x['id'] for x in checks],'checks':[{'id':x['id'],'status':'NOT_RUN'} for x in checks],'first_difference':None}
  try:
   need(normalized(self.manifest)==self._manifest_fingerprint,'constructor manifest mutated')
   if not self.root.exists():return dict(base,status='NOT_RUN',reason='No native capture root; no model execution is inferred')
   admitted_ids=self.manifest.get('stage_check_ids',{}).get(role)
   need(admitted_ids==base['exact_check_ids'],'independent admission stage ID binding absent/different')
   x=self.inventory(role);rc=RawChecker(self.root);results=[]
   def state(b):return x['states'][(b['operation_id'],b['phase'])]['descriptor']
   for e in checks:
    b=e['bindings'];c=dict(e)
    if e['scope']=='ALIGNED_STATE':c.update(left=state(b['left']),right=state(b['right']))
    elif e['scope']=='PREFIX_RETENTION':c.update(previous=state(b['previous']),current=state(b['current']),transition_receipt=x['retained'][(b['previous']['operation_id'],b['current']['operation_id'])]['descriptor'])
    elif e['scope']=='OWNED_VECTOR_STABILITY':c.update(x['owned'][(b['source']['operation_id'],b['mutation_operation_id'])]['value'])
    else:c['capture']=state(b['capture'])
    result=rc.compare(c);results.append(result)
    if result['status']!='PASS':return dict(base,status='FAIL',checks=results+[{'id':v['id'],'status':'NOT_RUN'} for v in checks[len(results):]],first_difference=result,inventory=x['summary'])
   report=dict(base,status='PASS',checks=results,inventory=x['summary'],capture_file_sha256=x['hashes'],limitation='PROVIDED FILES AND BOUND RECEIPTS ONLY; NOT NATIVE SOURCE-TRUTH, LOADED IDENTITY, NUMERICAL EXECUTION OR ADMISSION CERTIFICATE')
   if role==ROLES[0]:
    inputs={}
    for op in self.proposal['operations']:
     if op['path']!=ROLES[0]:continue
     before=x['states'][(op['id'],'POST_RECONCILE')];terminal=x['states'][(op['id'],'TERMINAL')];s=terminal['value']
     inputs[op['id']]={'canonical_ids':copy.deepcopy(s['canonical_ids']),'retained_head':before['value']['head'],'generated_ids':copy.deepcopy(s['generated_ids']),'stop_reason':s['stop_reason'],'generation_cap':s['generation_cap'],'post_reconcile_snapshot':copy.deepcopy(before['descriptor']),'terminal_snapshot':copy.deepcopy(terminal['descriptor'])}
    need(len(inputs)==18,'reference input certificate missing requests')
    report.update(reference_inputs=inputs,reference_inputs_scope='PROVIDED_R_SELF_NOT_COLD_EQUIVALENCE',reference_inputs_sha256=normalized(inputs))
   return report
  except (Invalid,KeyError,OSError,ValueError,TypeError,struct.error) as e:return dict(base,status='BLOCKED',reason=str(e),first_difference={'kind':'INVALID_OR_INCOMPLETE_STAGE_EVIDENCE','file':getattr(self,'_inventory_current_file',None),'reason':str(e)})
