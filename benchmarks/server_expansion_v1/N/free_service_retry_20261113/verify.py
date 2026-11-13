"""Independent original-byte episode contract checker, no model/CUDA imports."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
def load(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def equal(a,b):
 offset=0
 with Path(a).open('rb') as x,Path(b).open('rb') as y:
  while True:
   l=x.read(65536);r=y.read(65536)
   if l!=r:
    i=next((i for i,(u,v) in enumerate(zip(l,r)) if u!=v),min(len(l),len(r)))
    raise RuntimeError('STRICT_RAW_FIRST_DIFFERENCE '+Path(a).name+' byte='+str(offset+i))
   if not l:return offset
   offset+=len(l)
def semantic_wire(c,cold):
 j=json.loads(c['wire_response_json'])
 for n in ['created','id','system_fingerprint']:j.pop(n,None)
 if cold:j['usage']['prompt_tokens_details'].pop('cached_tokens',None)
 return j
def verify(root,relative,nonce,jobsha,checker,out):
 root=Path(root);p=root/relative;out=Path(out);e=load(p/'EPISODE.json');m=load(root/'MANIFEST.json');state=load(root/'STATE.json');stage=e['stage'];case=next(c for c in m['cases'] if c['id']==e['case']);cold=stage=='COLD';timed=stage=='MEASURE';reference=None;ref=None
 if out.exists():raise RuntimeError('fresh independent certificate')
 if not (p/'RESET.json').exists() or load(p/'RESET.json')!={'frontier_valid':False,'head':0,'native_reset_s':load(p/'RESET.json')['native_reset_s'],'pending':None}:raise RuntimeError('native reset contract')
 if not e['free_generation'] or e['n_ctx']!=4096 or e['threads']!=2 or e['graphs'] or e['FA'] or e['actual_KV']!='F16':raise RuntimeError('actual service config')
 if stage!='R':reference=root/load(root/'REFERENCES.json')[e['case']];ref=load(reference/'EPISODE.json')
 jobs=[];pairs=[];vector_count=0;request_receipts=[]
 for r in e['requests']:
  turn=r['turn'];q=r['prompt']['canonical_ids'];c=r['consumer'];y=c['sampled_ids'];stop=c['stop'];k=r['retained'];expected_head=len(q)+len(y)-1
  if not q or len(q)>873 or c['cap']!=128 or len(y)<1 or len(y)>128 or r['native_head_after']!=expected_head or r['logical_ids']!=q+y or r['pending']!=y[-1] or c['pending']!=y[-1] or r['retained_frontier_valid'] or not r['frontier_valid'] or r['sampling_vectors']!=len(y):raise RuntimeError('pending/head/ownership contract')
  if any(t<0 or t>=151936 for t in q+y) or any(t in m['EOG_ids'] for t in y[:-1]):raise RuntimeError('token/EOG bounds')
  if stop not in ['EOG','CAP'] or (stop=='EOG')!=(y[-1] in m['EOG_ids']) or stop=='CAP' and len(y)!=128:raise RuntimeError('actual stopping/cap')
  if [x['id'] for x in c['pieces']]!=y or ''.join(x['piece_hex'] for x in c['pieces'])!=c['parser_input_hex'] or any(x['piece_hex'] for x in c['pieces'] if x['id'] in m['EOG_ids']):raise RuntimeError('sampled tokens → actual piece/parser byte chain')
  wire=json.loads(c['wire_response_json']);choice=wire['choices'][0]
  if choice['finish_reason']!=('stop' if stop=='EOG' else 'length') or choice['message']!=c['client_message'] or wire['usage']['prompt_tokens']!=len(q) or wire['usage']['completion_tokens']!=len(y):raise RuntimeError('actual wire consumer metadata')
  assistant={'role':'assistant','content':c['client_message'].get('content','')}
  if c['client_message'].get('reasoning_content'):assistant['reasoning_content']=c['client_message']['reasoning_content']
  if c['history_after']!=r['prompt']['history']+[assistant]:raise RuntimeError('wire → client history chain')
  if turn==0:
   if q!=case['initial_ids'] or r['prompt']['history']!=[case['users'][0]] or k!=0:raise RuntimeError('exact initial saved canonical input')
  elif not cold:
   old=e['requests'][0];logical=old['logical_ids'];lcp=next((i for i,(a,b) in enumerate(zip(logical,q)) if a!=b),min(len(logical),len(q)));keep=min(lcp,old['native_head_after']);keep-=keep==len(q)
   if k!=keep or r['prompt']['history']!=old['consumer']['history_after']+[case['users'][1]]:raise RuntimeError('actual generated-history LCP/next canonical chain')
  calls=[x for x in e['calls'] if x['request']==r['id']];ids=sum((x['input_ids'] for x in calls),[]);expected=(q if cold else q[k:])+y[:-1];rows=len(expected)
  if ids!=expected or sum(x['rows'] for x in calls)!=rows or r['rows']!=rows or state['requests'][r['id']]['rows']!=rows or state['requests'][r['id']]['status']!='COMPLETED':raise RuntimeError('native ordered physical input/durable row charge')
  pos=0 if cold else k
  for call in calls:
   if call['position']!=pos or call['head_after']!=pos+call['rows'] or call['requested_output_mask']!='last_only':raise RuntimeError('actual native append positions/output mask')
   pos+=call['rows']
  request_receipts.append(dict(id=r['id'],turn=turn,rows=rows,outputs=len(y),stop=stop,retained=k))
  for i,t in enumerate(y):
   name='T%d-V%03d.f32'%(turn,i);f=p/name;jobs.append(dict(path=str(f),name=name,type='F32',bytes=151936*4,expected_greedy=t));vector_count+=1
   if reference:pairs.append(dict(kind='full vocabulary raw bits',file=name,bytes=equal(reference/name,f)))
  if ref:
   rr=ref['requests'][turn]
   if r['prompt']!=rr['prompt'] or c['sampled_ids']!=rr['consumer']['sampled_ids'] or c['parser_input_hex']!=rr['consumer']['parser_input_hex'] or c['pieces']!=rr['consumer']['pieces'] or c['client_message']!=rr['consumer']['client_message'] or c['history_after']!=rr['consumer']['history_after'] or semantic_wire(c,cold)!=semantic_wire(rr['consumer'],cold):raise RuntimeError('producer/sampling strict semantic difference (declared envelope exceptions only)')
 kvs=sorted(p.glob('*.kv'))
 for f in kvs:
  meta=load(f.with_suffix('.json'));h=meta['head'];n=h*147456
  if f.stat().st_size!=n or meta['active_bytes']!=n or meta['capacity']!=4096 or len(meta['tensors'])!=(72 if h else 0) or sorted(c[1] for c in meta['cells'])!=list(range(h)) or any(c[2]!=0 for c in meta['cells']) or len(set(meta['physical_by_position']))!=h:raise RuntimeError('complete active KV shape/map')
  if h and [(t['kind'],t['layer']) for t in meta['tensors']]!=[(kind,i) for kind in ['K','V'] for i in range(36)]:raise RuntimeError('all layer tensor order')
  jobs.append(dict(path=str(f),name=f.name,type='F16',bytes=n))
  if reference:pairs.append(dict(kind='all active KV raw bits',file=f.name,bytes=equal(reference/f.name,f)))
 expected_names={'reset.kv','T1-terminal.kv'} if timed else {'reset.kv'}
 for r in ([] if timed else e['requests']):
  t=r['turn'];expected_names|={f'T{t}-terminal.kv'}
  if not timed:expected_names|={f'T{t}-prompt.kv'}
  if t==1 and not timed:expected_names.add('T1-retained.kv')
 if {f.name for f in kvs}!=expected_names:raise RuntimeError('missing native checkpoint denominator')
 if not timed and not cold:
  old=e['requests'][0]['native_head_after'];keep=e['requests'][1]['retained']
  with (p/'T0-terminal.kv').open('rb') as x,(p/'T1-retained.kv').open('rb') as z:
   for i in range(72*8):
    x.seek(i*old*256)
    if x.read(keep*256)!=z.read(keep*256):raise RuntimeError('actual retained-prefix bytes changed')
 # A std-only independent C++ process scans every F32/F16 scalar and recomputes
 # first-index greedy from the complete original vectors. No GPU library links.
 rawjob=p/'INDEPENDENT_RAW_INPUT.json';rawjob.open('x').write(json.dumps(jobs));process=subprocess.run([checker,str(rawjob)],capture_output=True,text=True,timeout=180)
 (p/'INDEPENDENT_RAW.stdout.log').open('x').write(process.stdout);(p/'INDEPENDENT_RAW.stderr.log').open('x').write(process.stderr)
 if process.returncode:raise RuntimeError('independent full finite/greedy CPU scan failed '+process.stderr)
 scanned=json.loads(process.stdout)['files'];values={x['file']:x for x in scanned}
 for j in jobs:
  if j['type']=='F32' and values[j['name']]['greedy']!=j['expected_greedy']:raise RuntimeError('full-vector greedy/tie rule differs')
 if e['dispatch'] is not None:
  d=e['dispatch'];physical=d['physical']
  if d['physical_rows']!=sum(r['rows'] for r in e['requests']) or d['physical_calls']!=len(physical) or any(x['API_width']!=x['physical_rows'] or x['physical_calls']!=1 or x['returncode'] for x in physical) or d['bad']:raise RuntimeError('real backend physical work')
  if stage=='HEAVY' and (d['loop4_marked_nodes']<=0 or d['GPU_nodes']<=0):raise RuntimeError('actual heavy graph/placement observations missing')
 index=[]
 for f in sorted(p.iterdir()):
  if f.is_file():index.append(dict(file=f.name,bytes=f.stat().st_size,sha256=sha(f)))
 result=dict(status='PASS',episode=e['episode'],stage=stage,case=e['case'],arm=e['arm'],nonce=nonce,job_sha256=jobsha,requests=request_receipts,full_vectors=vector_count,active_KV_snapshots=len(kvs),raw_pairs=pairs,all_scalar_finite_checked=True,greedy_recomputed_from_full_vectors=True,new_model_calls_for_validation=0,files=index,depth=e['capture_depth'],wire_exceptions=['created','id','system_fingerprint']+(['cached_token_usage'] if cold else []))
 out.open('x').write(json.dumps(result,sort_keys=True,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--relative',required=True);p.add_argument('--nonce',required=True);p.add_argument('--jobsha',required=True);p.add_argument('--checker',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 try:r=verify(a.root,a.relative,a.nonce,a.jobsha,a.checker,a.out);print(json.dumps({k:r[k] for k in ['status','episode','full_vectors','active_KV_snapshots']}))
 except Exception as e:
  f=Path(a.out+'.FAILED.json')
  if not f.exists():f.open('x').write(json.dumps(dict(status='FAIL',reason=str(e)))+'\n')
  raise
