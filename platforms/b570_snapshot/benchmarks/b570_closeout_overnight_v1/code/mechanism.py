"""Bounded natural parent traces; no forced prefixes and no invented cross-state result."""
from pathlib import Path
from datetime import datetime,timezone
import math
from campaign import read,save,stage,cfg,R,T,N1,eq
ROOT=Path(__file__).parent
def run():
 inputs=read(ROOT/'INPUTS.json');p=read(ROOT/'PROTOCOL.json');tasks=inputs['shared'][:p['C_shared_count']]+inputs['long'];byid={t['id']:t for t in tasks}
 rows=[r for r in read(ROOT/'C_RESULTS.json') if not r['warm']];selected=[];seen=set()
 for k,ub in [(1,2),(3,4),(5,6),(7,8)]:
  for cap in [128,256,512]:
   for task in tasks:
    rr=[r for r in rows if r['task']==task['id'] and r['config']['width_k']==k and r['config']['cap']==cap];ref=next(r for r in rr if r['config']['label']=='R_reference')
    native=next(r for r in rr if r['config']['label']=='N_candidate')
    identity=(task['id'],k,ub)
    if identity not in seen and not eq(native['endpoint'],ref['endpoint']):
     seen.add(identity);selected.append({'task':task['id'],'k':k,'ub':ub,'cap':cap})
     if len(selected)==2:break
   if len(selected)==2:break
  if len(selected)==2:break
 plan={'selection':selected,'ordering':'frozen width, cap, task order; repeated cap is not an independent case','state_cross':'NOT_IMPLEMENTED: final qualified frontends expose authentic prefill transfer but do not expose a mid-natural-trajectory target+draft+post-sample sampler checkpoint. Final trace positions or forced prefixes cannot reconstruct that donor. Published API supports state serialization in general; this is a frontend checkpoint limitation, not proof that Vulkan cannot support it.','forwards':'R/T/failed native/original anchor/ordinary same k and UB, all natural generation and separately charged','causal_status':'NOT_CAUSALLY_IDENTIFIED'}
 save(ROOT/'MECHANISM_PLAN.json',plan)
 if not selected:
  save(ROOT/'MECHANISM.json',{'status':'GATED_BY_QUALIFICATION','reason':'No naturally failing C native configuration in complete matrix','plan':plan});return
 remaining=(datetime.fromisoformat(read(ROOT/'RECOVERY_AMENDMENT.json')['new_experiment_stop_utc'])-datetime.now(timezone.utc)).total_seconds()
 if remaining<1200:
  save(ROOT/'MECHANISM.json',{'status':'NOT_RUN_TIME','plan':plan,'causal_status':'NOT_CAUSALLY_IDENTIFIED'});return
 sessions=[]
 for pi,pair in enumerate(selected):
  modes=[R,dict(T,ub=pair['ub']),cfg('M_failed',True,pair['k'],pair['ub']),N1,cfg('M_ordinary',True,pair['k'],pair['ub'],prefill=pair['ub'],plain=True)]
  for mode in modes:sessions.append({'config':dict(mode,cap=pair['cap'],capture=True,pair=pi),'inputs':[byid[pair['task']]]})
 observed=stage('MECHANISM',sessions);evidence=[]
 for pi,pair in enumerate(selected):
  rr=[r for r in observed if r['config']['pair']==pi];ref=next(r for r in rr if r['config']['label']=='R_reference');reference=ref['endpoint']['ids']
  for r in rr:
   raw=read(next(ROOT/f for f in r['files'] if f.endswith('/capture.json')));ids=r['endpoint']['ids'];first=next((i for i,(a,b) in enumerate(zip(ids,reference)) if a!=b),min(len(ids),len(reference)) if ids!=reference else None)
   commit=raw['commits'][first] if first is not None and first<len(raw['commits']) else None;scores=commit.get('scores',{}) if commit else {}
   if not scores and commit and 'top1' in commit:scores=commit
   expected=reference[first] if first is not None and first<len(reference) else None
   top1=scores.get('top1');top2=scores.get('top2');score1=scores.get('top1_score');score2=scores.get('top2_score')
   margin=score1-score2 if score1 is not None and score2 is not None else None
   expected_score=score1 if expected==top1 else score2 if expected==top2 else None
   evidence.append({'pair':pair,'label':r['config']['label'],'unit_id':r['unit_id'],'qualified':eq(r['endpoint'],ref['endpoint']),'first_difference':first,'common_natural_committed_prefix':first,'first_difference_commit':commit,'top1_top2_margin':margin,'reference_token':expected,'reference_token_logit':expected_score,'reference_margin':score1-expected_score if score1 is not None and expected_score is not None else None,'reference_margin_status':'OBSERVED_TOP2_MEMBER' if expected_score is not None else 'MISSING: reference token outside retained top two or endpoint-only difference; no full future logits invented','EOS_margin_status':'MISSING unless observed reference EOG is retained top-two token; top1/top2 margin is not automatically EOS margin','state_transfer':raw['transfer'],'actual_target_query_range':[min(g['ne1'] for c in raw['trace'] if c['event']=='decode' and c['role']=='target' and c['phase']=='continuation' for g in c['graphs'] if g['tensor']=='embd'),max(g['ne1'] for c in raw['trace'] if c['event']=='decode' and c['role']=='target' and c['phase']=='continuation' for g in c['graphs'] if g['tensor']=='embd')] if any(c.get('graphs') for c in raw['trace'] if c['event']=='decode' and c['role']=='target' and c['phase']=='continuation') else None})
 save(ROOT/'MECHANISM.json',{'status':'COMPLETED_TRACE_DIAGNOSTIC','causal_status':'NOT_CAUSALLY_IDENTIFIED','plan':plan,'natural_parent_requests':len(observed),'warmups':len(sessions),'observations':evidence,'claim':'Current graph shape and authentic prefill roundtrip can be observed. No mid-state crossed counterfactual, opaque sampler byte certification, unique kernel cause or causal EOS claim.'})
if __name__=='__main__':run()
