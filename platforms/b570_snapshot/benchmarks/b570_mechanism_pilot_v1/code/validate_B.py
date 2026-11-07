"""Independent binary state/logit and full raw continuation validator; no executor imports."""
from pathlib import Path
import sys,json,hashlib,struct,math,collections
import numpy as np
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
checks=0;errors=[]
def ck(x,m):
 global checks;checks+=1
 if not x:errors.append(m)
def kv(p):
 b=Path(p).read_bytes();off=0
 def read(fmt):
  nonlocal off
  s=struct.Struct('<'+fmt);v=s.unpack_from(b,off);off+=s.size;return v
 length,=read('I');arch=b[off:off+length];off+=length;streams,=read('I');ck(arch==b'qwen3' and streams==1,'KV arch/stream '+str(p));nc,=read('I');positions=[]
 for _ in range(nc):
  pos,ns=read('iI');seqs=read('i'*ns);ck(seqs==(0,),'KV ownership '+str(p));positions.append(pos)
 vt,nl=read('II');ck(vt==1 and nl in [28,36],'KV layout '+str(p));tensors=[]
 for i in range(nl):
  dtype,rowbytes=read('iQ');n=rowbytes*nc;chunk=b[off:off+n];off+=n;ck(dtype==1 and len(chunk)==n,'KV key dtype/bytes '+str(p));tensors.append(chunk)
 for i in range(nl):
  dtype,el,embd=read('iII');n=el*embd*nc;chunk=b[off:off+n];off+=n;ck(dtype==1 and el==2 and len(chunk)==n,'KV value dtype/bytes '+str(p));tensors.append(chunk)
 ck(off==len(b),'KV consumed every byte '+str(p));ck(len(positions)==len(set(positions)),'KV unique positions '+str(p))
 return dict(positions=positions,layers=nl,tensors=tensors,sha256=hashlib.sha256(b).hexdigest())
def raw(r):return load(R/next(f for f in r['files'] if f.endswith('/capture.json')))
def factor(table):
 state=[table[0][c]!=table[1][c] for c in [0,1]];path=[table[d][0]!=table[d][1] for d in [0,1]]
 if any(state) and any(path):kind='INTERACTION'
 elif any(state):kind='STATE_EFFECT' if all(state) else 'INTERACTION'
 elif any(path):kind='CURRENT_PATH_EFFECT' if all(path) else 'INTERACTION'
 else:kind='NO_DETECTED_EFFECT'
 return dict(classification=kind,state_effect=state,current_path_effect=path)
def main():
 manifest=load(R/'B_MANIFEST.json');hist=load(R/'HISTORICAL_PARENTS.json');eog=set(load(R/'dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids']);cases=[];valid_tasks=set();checkpoint_count=0
 # Every natural checkpoint, not only selected ones; authoritative binary sequence ownership.
 for result in (R/'raw').glob('*/RESULT.json'):
  r=load(result)
  for f in r['files']:
   if not (f.endswith('.json') and '.cp-' in f):continue
   j=load(R/f);base=str(R/f)[:-5];checkpoint_count+=1
   ck(j['n_predict']==len(j['ids'])==len(j['eog']) and j['pending']==-1 and not j['has_eos'],'natural committed boundary '+f)
   ck(j['ids']==raw(r)['ids'][:len(j['ids'])],'authentic natural prefix '+f)
   ck(j['target_sampler']['accepted_history']==[[i,True] for i in j['ids']],'actual target accepted history '+f)
   ck(j['draft_sampler']['accepted_history']==[[i,True] for i in j['ids']+j['draft_tokens'][1:]],'actual current draft accepted history '+f)
   for label in ['target_sampler','draft_sampler']:
    s=j[label];ck(s['chain']==s['clone_chain'] and s['history_string']==s['clone_history'] and s['seed']==s['clone_seed'],'real clone metadata '+f)
   effective=j['effective_sampling'];ck(effective['temp']==0 and effective['penalty_repeat']==1 and effective['penalty_freq']==effective['penalty_present']==effective['dry_multiplier']==0 and effective['grammar_empty'] and not effective['grammar_lazy'] and not effective['reasoning_control'] and effective['reasoning_budget_tokens']==-1 and not effective['backend_sampling'] and effective['mirostat']==0,'effective greedy restore scope '+f)
   for role in ['target','draft']:
    p=base+'.'+role+'.kv';parsed=kv(p);after=base+'.'+role+'.source_after.kv';ck(sha(p)==sha(after),'source byte unchanged '+f+role)
    pos=j[role+'_position'];ck(min(parsed['positions'])==pos['min'] and max(parsed['positions'])==pos['max'] and sorted(parsed['positions'])==list(range(pos['max']+1)),'real KV positions '+f+role)
   batch=j['batch_target'];ck(len(batch)==j['k']+1 and [x['id'] for x in batch]==j['draft_tokens'] and batch[0]['id']==j['ids'][-1],'already-generated actual caller '+f)
   ck(all(x['pos']==j['n_past_tgt']+i and x['seq']==[0] and x['logits'] for i,x in enumerate(batch)),'logical caller '+f)
   ck(Path(base+'.natural.f32').stat().st_size==len(batch)*151936*4,'full natural score rows '+f)
   dist=np.fromfile(base+'.dists',dtype=np.dtype([('id','<i4'),('logit','<f4'),('p','<f4')]))
   ck(len(dist)==sum(j['dist_sizes']),'all actual proposal distributions '+f);cursor=0
   for i,n in enumerate(j['dist_sizes']):
    if n:ck(int(dist[cursor]['id'])==j['draft_tokens'][i],'actual sampled proposal '+f)
    cursor+=n
 for ci,c in enumerate(manifest['cases']):
  if c['status']!='ALIGNED':cases.append(dict(task=c['task'],round=c['round'],status=c['status']));continue
  sham=[]
  for di,d in enumerate(c['donors']):
   u=f'B_SHAM/{ci}/{di}/{c["task"]}';p=R/'raw'/hashlib.sha256(u.encode()).hexdigest()[:20]/'RESULT.json';ck(p.exists(),'sham missing '+u)
   if not p.exists():sham.append(False);continue
   r=load(p);a=raw(r);parent=load(R/d['parent_raw']);same=a['ids']==parent['ids'] and a['eog']==parent['eog'];sham.append(same);ck(same,'own-path full raw continuation '+u)
   resume=load(R/next(f for f in r['files'] if f.endswith('.resume.json')));ck(resume['target_roundtrip'] and resume['draft_roundtrip'] and resume['no_prefill_recompute'],'real API resume '+u)
   source=load(R/'derived'/f'SHAM_SOURCE-{ci}-{di}.json');ck(source['before']==source['after'] and all(sha(R/f)==h for f,h in source['before'].items()),'sham frozen source unchanged '+u)
  cells=[];arrays={};decisions=[[None,None],[None,None]];table_by_row=[]
  for di,d in enumerate(c['donors']):
   for ri,recipe in enumerate(c['recipes']):
    u=f'B_CROSS/{ci}/{di}/{ri}';p=R/'aux'/u.replace('/','_')/'RESULT.json';ck(p.exists(),'cross missing '+u)
    if not p.exists():continue
    r=load(p)
    for f,h in r['files'].items():ck(sha(R/f)==h,'cross SHA '+f)
    f=next(f for f in r['files'] if f.endswith('/cross.json'));j=load(R/f);arr=np.fromfile(str(R/f)+'.logits.f32',dtype='<f4').reshape((-1,151936));arrays[di,ri]=arr
    ck(j['batch']==c['batch'] and j['recipe']==recipe and j['n_vocab']==151936,'fixed common logical batch '+u)
    ck(arr.shape==(len(c['batch']),151936) and np.isfinite(arr).all(),'full float32 vocabulary '+u)
    donor=kv(str(R/d['checkpoint'])[:-5]+'.target.kv');before=kv(str(R/f)+'.before.kv');after=kv(str(R/f)+'.after.kv');ck(before['sha256']==donor['sha256'],'byte-identical crossed donor '+u)
    ck(before['positions']==donor['positions'] and set(after['positions'])==set(range(c['batch'][-1]['pos']+1)),'cross logical positions '+u)
    source=load(R/next(x for x in r['files'] if x.endswith('/SOURCE_UNCHANGED.json')));ck(source['before']==source['after'] and all(sha(R/x)==h for x,h in source['before'].items()),'cross source preservation '+u)
    rows=[];ref=hist[c['task']+'/R_reference']['endpoint']['ids'];parentbad=load(R/c['donors'][0 if c['task']=='MBPP/72' else 1]['parent_raw'])['ids']
    for i,a in enumerate(arr):
     order=np.argsort(-a,kind='stable')[:2];one,two=map(int,order);ck(one==j['rows'][i]['top1'] and two==j['rows'][i]['top2'],'authentic full-vocab top two '+u)
     ck(float(a[one])==j['rows'][i]['top1_score'] and float(a[two])==j['rows'][i]['top2_score'],'scores '+u)
     ck(j['row_decision_ids'][i]==one,'actual effective greedy row decision '+u)
     idx=c['committed_length']+i;reference=ref[idx] if idx<len(ref) else None;alternative=parentbad[idx] if idx<len(parentbad) else None
     rows.append(dict(row=i,logical_output_index=idx,top1=one,top2=two,margin=float(a[one]-a[two]),reference_id=reference,reference_score=float(a[reference]) if reference is not None else None,alternative_id=alternative,alternative_score=float(a[alternative]) if alternative is not None else None,eog_scores={str(t):float(a[t]) for t in sorted(eog)}))
    ck(j['decision_id']==rows[0]['top1'] and j['decision_eog']==(j['decision_id'] in eog),'effective greedy row0 decision '+u);decisions[di][ri]=j['decision_id']
    cells.append(dict(unit=u,donor=d['label'],current_recipe=recipe['label'],rows=rows,forward_ms=j['forward_ms'],host_seconds=r['host_seconds']))
  if len(arrays)==4:
   for i in range(len(c['batch'])):
    table=[[int(np.argmax(arrays[d,p][i])) for p in [0,1]] for d in [0,1]];table_by_row.append(dict(row=i,logical_output_index=c['committed_length']+i,decisions=table,**factor(table)))
   path_deltas=[float(np.max(np.abs(arrays[d,0].astype('float64')-arrays[d,1]))) for d in [0,1]]
   state_deltas=[float(np.max(np.abs(arrays[0,p].astype('float64')-arrays[1,p]))) for p in [0,1]]
   nonadditive=float(np.max(np.abs((arrays[1,1].astype('float64')-arrays[1,0])-(arrays[0,1].astype('float64')-arrays[0,0]))))
   target_row=c['primary_row'];ck(target_row==min(c['retained_divergence']-c['committed_length'],len(c['batch'])-1),'predeclared row selection '+str(ci));focus=table_by_row[target_row]
   status='VALID' if all(sham) else 'UNSUPPORTED_SHAM';
   if status=='VALID':valid_tasks.add(c['task'])
   # Same-path cross donor0 may use donor1's different proposal: do not require equality to parent's decision.
   cases.append(dict(task=c['task'],round=c['round'],status=status,committed_length=c['committed_length'],retained_divergence=c['retained_divergence'],shams=sham,common_batch_source=c['batch_source'],classification_endpoint='closest retained-divergence row present in this actual common batch; all rows separately reported',classification=focus['classification'],focus_row=target_row,focus_output_index=focus['logical_output_index'],decisions=focus['decisions'],all_rows=table_by_row,max_abs_state_delta_by_path=state_deltas,max_abs_path_delta_by_donor=path_deltas,max_abs_nonadditive_score_delta=nonadditive,score_change_detected=any(x>0 for x in path_deltas+state_deltas),cells=cells,scope='real inherited target-state/current whole-recipe intervention; full shams validate restoration, not repaired counterfactual continuation'))
 result=dict(status='PASS' if not errors else 'FAIL',checks=checks,errors=errors,natural_checkpoints=checkpoint_count,valid_independent_tasks=sorted(valid_tasks),cross_case_support=len(valid_tasks)>=2,cases=cases,opaque_sampler_bytes='UNAVAILABLE',causal_scope='local genuine target numeric state x current complete recipe; no unique kernel cause; no counterfactual full trajectory repair')
 (R/'CAUSAL_RESULTS.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print(result['status'],checks,errors[:15],[(c['task'],c['round'],c['status'],c.get('classification'),c.get('decisions')) for c in cases],flush=True)
 return result
if __name__=='__main__':main()
