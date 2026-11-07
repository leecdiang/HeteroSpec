"""Pinned public corpus, native full-string tokenization, output-blind roots."""
from host import *
import collections,gzip
sys.path.insert(0,str(HERE.parent/'tpds_prefix_reuse_v1'))
import study
CORPUS=ROOT/'corpus'
def digest_text(s):return hashlib.sha256(s.strip().encode()).hexdigest()
def exposure():
 base=Path('I:/HeteroSpec/b570-llama-20261102')
 paths=[base/'EXPOSURE_AUDIT-00.json',base/'research/EXPOSURE.jsonl',base/'UNSEEN_PANEL-00.json',
        Path('I:/HeteroSpec/b570-qwen-transfer-20261103/historical/NATIVE_PANEL.json'),Path('I:/HeteroSpec/b570-qwen-transfer-20261103/UNSEEN.json'),OLD/'NATURAL_PANEL.json',OLD/'NATURAL_QUAL.json',OLD/'pool/rtx-parallel-panel.json',*sorted((OLD/'pool').glob('*_PANEL.json'))]
 remote=CORPUS/'PR171-natural-inputs.json'
 if not remote.exists():remote.write_bytes(subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','show','371223b696bb805030c29f04e39eb17b57fb2ebb:benchmarks/rtx_operator_frontier_v1/execution/evidence/natural-inputs.json'],cwd=HERE))
 paths.append(remote);seen=set();pins=[];placeholders=[]
 def absorb(v):
  if isinstance(v,list):
   for z in v:absorb(z)
  elif isinstance(v,dict):
   for k,z in v.items():
    if isinstance(z,str):
     if k in ('id','input_id','root_id','message_id','text_sha256','prompt_ids_sha256','prompt_hash','request_token_sha256'):seen.add(z)
     if k in ('text','description','formatted_prompt','raw_prompt','prompt','content'):seen.add(digest_text(z))
    elif k in ('prompt_ids','request_ids','cached_ids','ids') and isinstance(z,list) and z and all(type(t)is int for t in z):seen.add(study.digest(z))
    else:absorb(z)
 for p in paths:
  pins.append(dict(path=str(p),sha256=sha(p)))
  if p.suffix=='.jsonl':
   for line in p.read_text(encoding='utf-8').splitlines():absorb(json.loads(line))
  else:
   v=read(p);absorb(v)
   if isinstance(v,dict) and 'keys' in v:seen.update(v['keys'])
 # Include locally delivered additional panels/history (never outputs for new corpus).
 candidates=subprocess.check_output(['rg','--files',str(HERE.parents[1]/'benchmarks'),'-g','*PANEL*.json','-g','*EXPOSURE*.json','-g','*panel*.json'],text=True).splitlines()
 for name in candidates:
  p=Path(name)
  if 'b570_prefix_reuse_v1' in p.parts or p in paths:continue
  if not p.read_text(encoding='utf-8-sig').strip():
   placeholders.append(dict(path=str(p),sha256=sha(p),reason='empty historical placeholder; complete inherited audit above remains authoritative'));continue
  v=read(p);absorb(v);pins.append(dict(path=str(p),sha256=sha(p)))
 write(CORPUS/'EXPOSURE_AUDIT.json',dict(utc=utc(),keys=sorted(seen),files=pins,empty_placeholders=placeholders,scope='Inherited complete both-platform audit plus subsequent delivered native panels through PR171; no new corpus outputs'))
 return seen
def prepare():
 assert sha(CORPUS/'messages.jsonl.gz')=='2ff4aa8999c911ffec7972ddf70359f220b3da184b731f3649f68b1391e19341'
 seen=exposure()
 with gzip.open(CORPUS/'messages.jsonl.gz','rt',encoding='utf-8') as f:all_rows=[json.loads(l) for l in f]
 by={r['message_id']:r for r in all_rows};parents={r.get('parent_id') for r in all_rows};excluded=[];kept=[]
 # Terminal means an actual leaf of the pinned message tree, not a truncated path.
 for r in all_rows:
  reason=None
  if r['message_id'] in parents:reason='not a terminal leaf'
  elif r['role']!='prompter':reason='terminal role not user'
  path=[];x=r;visited=set()
  if reason is None:
   while x is not None:
    if x['message_id'] in visited:reason='cycle';break
    path.append(x);visited.add(x['message_id']);parent=x.get('parent_id')
    if parent and parent not in by:reason='missing ancestor';break
    x=by.get(parent)
   path.reverse()
   if not reason:
    if len(path)<3:reason='no prior assistant'
    elif any(x['role']!=('prompter' if i%2==0 else 'assistant') for i,x in enumerate(path)):reason='not alternating from user root'
    elif any(x['lang']!='en' for x in path):reason='non-English path'
    elif any(x['deleted'] for x in path):reason='deleted path'
    elif any(x['synthetic'] for x in path):reason='synthetic path'
    elif any(not x.get('text') for x in path):reason='missing text'
  if reason:excluded.append(dict(id=r['message_id'],reason=reason));continue
  messages=[dict(role='user' if x['role']=='prompter' else 'assistant',content=x['text']) for x in path]
  keys={r['message_id'],path[0]['message_id'],*(digest_text(x['text']) for x in path)}
  kept.append(dict(id=r['message_id'],root_id=path[0]['message_id'],message_ids=[x['message_id'] for x in path],messages=messages,source_sha256=study.digest(path),history_exposed=bool(keys&seen)))
 with (CORPUS/'paths.jsonl').open('x',encoding='utf-8') as f:
  for r in kept:f.write(json.dumps(r,ensure_ascii=False)+'\n')
 write(CORPUS/'PATH_SELECTION.json',dict(utc=utc(),corpus_revision=study.CFG['corpus_revision'],source_sha256=sha(CORPUS/'messages.jsonl.gz'),messages=len(all_rows),candidate_paths=len(kept),terminal_definition='full root-to-leaf; no child beyond terminal user',exclusions=excluded,counts=dict(collections.Counter(x['reason'] for x in excluded))))
 print('candidate_paths',len(kept),flush=True)
def tokens():
 return run('native-tokenizer-00','reference-00',[],'zero-forward-tokenizer',tokenize_only=True,input_jsonl=str(CORPUS/'paths.jsonl'))
def select():
 admission=read(ROOT/'units/admit-candidate-00/native/result.json');assert admission['status']=='COMPLETE'
 native=admission['records'][0]['allocator_heads'];heads={x['logical']:x['physical'] for x in native};C=len(native);P=native[0]['padding']
 tokroot=ROOT/'units/native-tokenizer-00/native';meta=read(tokroot/'result.json')['tokenization'];seen=set(read(CORPUS/'EXPOSURE_AUDIT.json')['keys'])
 rows=[];oversized=[]
 for line in (tokroot/'tokens.jsonl').read_text(encoding='utf-8').splitlines():
  r=json.loads(line);H=study.lcp(r['cached_ids'],r['request_ids']);L=len(r['request_ids'])
  if any(v in seen for v in (study.digest(r['request_ids']),study.digest(r['cached_ids']),r['request_render_sha256'],r['cached_render_sha256'])):r['history_exposed']=True
  if H>=C or L+128>C:
   oversized.append(dict(id=r['id'],root_id=r['root_id'],prompt_tokens=L,logical_lcp=H,reason='prompt plus cap exceeds capacity'));continue
  r.update(effective_head=H,physical_head=heads[H],native_dense_verified=True);rows.append(r)
 model=read(ROOT/'INHERITED_AUTHENTICATION.json')['model']
 manifest=dict(schema_version=1,native_tokenization=True,corpus_revision=study.CFG['corpus_revision'],tokenizer_sha256=study.digest(dict(model_sha256=model['sha256'],reference_dlls=read(ROOT/'reference-00/FILES.json'),tokenization=meta)),template_sha256=meta['template_sha256'],deployment_id='b570-qwen3-8b-q8-f16-C4096-exact-token-host-snapshot-v1',capacity=C,padding=P,qmax=32,output_cap=128,cache_granule=1,reuse_policy='exact_lcp',exposure_audit_sha256=sha(CORPUS/'EXPOSURE_AUDIT.json'),rows=rows)
 # Native tokenizer identity independent of host paths, worker flags and backend DLLs.
 manifest['tokenizer_sha256']=study.digest(dict(model_sha256=model['sha256'],native_source_commit='0cae43063cf15170e91a2ff4d034da0ecef4a1b2',add_special=True,parse_special=True,renderer=meta['renderer']))
 write(ROOT/'manifest.json',manifest);census=study.inspect_manifest(manifest);panel=study.select(manifest)
 write(ROOT/'census.json',census);write(ROOT/'panel.json',panel);write(ROOT/'schedule.json',study.schedule(panel));write(ROOT/'OVERSIZED_PATHS.json',oversized)
 sensitivity=[]
 for granule in (1,16,32,64):
  m=json.loads(json.dumps(manifest));m.update(cache_granule=granule,reuse_policy='exact_lcp' if granule==1 else 'floor_lcp')
  for r in m['rows']:r['physical_head']=r['effective_head']=study.lcp(r['cached_ids'],r['request_ids'])//granule*granule
  cc=study.inspect_manifest(m);ids={r['id'] for r in panel['calibration']+panel['test']};eligible=cc.pop('eligible');cc.pop('rejected');cc.update(scenario_only=granule!=1,panel_crossed=sum(r['crossed_qb_calls']>0 for r in eligible if r['id'] in ids));sensitivity.append(cc)
 write(ROOT/'TOKENIZER_AND_CENSUS.json',dict(utc=utc(),source=sha(CORPUS/'messages.jsonl.gz'),tokenizer=meta,tokenizer_sha256=manifest['tokenizer_sha256'],renderer_source=sha(ROOT/'source-00/src/llama-chat.cpp'),tokenizer_source=sha(ROOT/'source-00/src/llama-vocab.cpp'),allocator_source=sha(HERE/'allocator_probe.cpp'),allocator_evidence=sha(ROOT/'units/admit-candidate-00/native/result.json'),allocator_mode='Zero-forward real find_slot/apply_ubatch metadata; no KV bytes computed. Actual service restore heads are rechecked during qualification.',cache_mode='exact-token immutable host sequence snapshot; no zero-copy resident-cache claim',manifest_sha256=study.digest(manifest),oversized=len(oversized),sensitivity=sensitivity))
 write(ROOT/'COHORT_RECEIPT.json',dict(utc=utc(),panel_sha256=study.digest(panel),manifest_sha256=study.digest(manifest),calibration_roots=[r['root_id'] for r in panel['calibration']],test_roots=[r['root_id'] for r in panel['test']],calibration=panel['calibration'],test=panel['test'],selection='unchanged study.select hash ranking; root and path selection blind to geometry and outputs',new_model_forwards=0))
 print('census',census['eligible_roots'],census['crossed_requests'],'panel',len(panel['calibration']),len(panel['test']))
if __name__=='__main__':{'prepare':prepare,'tokens':tokens,'select':select}[sys.argv[1]]()
