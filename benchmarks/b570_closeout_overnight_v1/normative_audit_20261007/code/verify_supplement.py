"""CPU-only independent natural-parent and full-logit audit; no executor imports."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,math,collections,sys
import numpy as np
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).parent)
BASE=Path('C:/hs/b570-closeout-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
checks=0;errors=[]
def check(x,msg):
 global checks;checks+=1
 if not x:errors.append(msg)
def same(a,b):return all(a[k]==b[k] for k in ['ids','eog','reason'])
am=load(ROOT/'AMENDMENT.json');build=load(ROOT/'BUILD_FREEZE.json');eogs=load(ROOT/'TOKENIZATION_PROOF.json')['runtime_eog_ids'];historical=load(ROOT/'HISTORICAL_EXPECTED.json');raw_by_unit={};logits_by_unit={};records=[];logit_rows=0
for p in sorted((ROOT/'raw').glob('*/RESULT.json')):
 r=load(p);records.append(r);u=r['unit_id'];check(r['source_commit']==build['source_commit'],'frozen observer epoch '+u)
 capture=next(ROOT/n for n in r['files'] if n.endswith('/capture.json'));raw=load(capture);raw_by_unit[u]=raw
 for name,h in r['files'].items():check(sha(ROOT/name)==h,'raw file '+name)
 check(raw['eog']==[t in eogs for t in raw['ids']],'runtime eog '+u)
 check(raw['ids'] and len(raw['commits'])==len(raw['ids']),'all natural commits '+u)
 n=min(r['config']['cap'],next((i+1 for i,t in enumerate(raw['ids']) if t in eogs),len(raw['ids'])))
 check(dict(ids=raw['ids'][:n],eog=raw['eog'][:n],reason='EOG' if raw['ids'][n-1] in eogs else 'CAP',raw_suffix=len(raw['ids'])-n)==r['endpoint'],'full endpoint '+u)
 check(load(str(capture)+'.metrics.json')==r['metrics'],'authentic metrics '+u)
 start=load(capture.parent/'START.json');check(start['utc']>build['utc'] and start['utc']<am['new_experiment_stop_utc'],'frozen new deadline '+u)
 check(r['metrics']['reset_target']['min']==r['metrics']['reset_target']['max']==-1,'target reset '+u)
 if r['config']['native']:check(r['metrics']['reset_draft']['min']==r['metrics']['reset_draft']['max']==-1,'draft reset '+u)
 session=load(ROOT/'sessions'/r['session']/'SESSION.json');check(session['environment']['HS_AUDIT_FULL_LOGITS']=='1' and 'HS_TRACE_OFF' not in session['environment'],'capture-only instrumentation '+u)
 log=(ROOT/'sessions'/r['session']/'stderr.log').read_text(encoding='utf-8',errors='replace');check('using device Vulkan' in log and '(Intel(R) Arc(TM) B570 Graphics)' in log and 'offloaded 37/37 layers to GPU' in log,'actual B570 full offload '+u)
 check(start['request']['prompt_ids']==raw['prompt_ids'],'no changed prompt '+u)
 if raw['transfer']:
  t=raw['transfer'];check(t['source_unchanged'] and t['kv_equal'] and t['before']==t['after']==t['source_after'] and t['consumed_bytes']==t['state_bytes'],'state roundtrip '+u)
  check(t['pending_id']==raw['ids'][0] and t['sampler_chain']==t['clone_chain'] and t['sampler_history']==t['clone_history'] and t['seed']==t['clone_seed']==123,'pending/post-sample sampler '+u)
  kv=[capture.parent/(capture.name+s) for s in ['.before.kv','.restored.kv','.source_after.kv']];check(len({sha(f) for f in kv})==1,'actual KV bytes '+u)
 # All logits were captured from actual decisions, with no reference inputs.
 logit_paths=[]
 for i,c in enumerate(raw['commits']):
  f=Path(str(capture)+f'.decision-{i}.f32');check(f.exists(),'full current logits '+u+str(i));v=np.fromfile(f,dtype='<f4');check(len(v)==151936 and bool(np.isfinite(v).all()),'full vocabulary finite logits '+u+str(i))
  a=int(np.argmax(v));w=v.copy();w[a]=-np.inf;b=int(np.argmax(w));s=c['scores']
  check(a==s['top1'] and b==s['top2'] and math.isclose(float(v[a]),s['top1_score'],abs_tol=1e-6) and math.isclose(float(v[b]),s['top2_score'],abs_tol=1e-6),'independent top1/top2 '+u+str(i))
  check(c['id']==raw['ids'][i] and c['id']==a,'natural greedy output '+u+str(i));logit_paths.append(f);logit_rows+=1
 logits_by_unit[u]=logit_paths
check(len(records)==32 and sum(r['warm'] for r in records)==14,'18 parent/14 warm denominator')
nonwarm=[r for r in records if not r['warm']]
for stage,count in [('BRIDGE',8),('MECHANISM_SUPPLEMENT',10)]:
 rr=[r for r in nonwarm if r['unit_id'].startswith(stage+'/')];check(len(rr)==count,'stage count '+stage)
 for si,s in enumerate(load(ROOT/(stage+'_SCHEDULE.json'))):
  for ri,t in enumerate(s['inputs']):
   r=next((r for r in rr if r['unit_id']==f'{stage}/{si}/{ri}/{t["id"]}'),None);check(r is not None and r['config']==s['config'] and raw_by_unit[r['unit_id']]['prompt_ids']==t['prompt_ids'],'fixed diagnostic unit '+stage+str(si))
for r in [r for r in nonwarm if r['unit_id'].startswith('BRIDGE/')]:
 tag='N0' if r['config']['label']=='N0_ordinary' else 'R';ref=historical[r['task']+'/'+tag+'/1'];ref=dict(ref,reason='EOG' if ref['endpoint']=='EOG' else 'CAP');check(same(r['endpoint'],ref),'old contract bridge '+r['unit_id'])
observations=[]
for pi,pair in enumerate(am['selection']):
 rr=[r for r in nonwarm if r['unit_id'].startswith('MECHANISM_SUPPLEMENT/') and r['config']['pair']==pi];reference=next(r for r in rr if r['config']['label']=='R_reference');refs=reference['endpoint']['ids'];prior=historical[pair['task']+'/R/1'];check(reference['endpoint']['ids']==prior['ids'] and reference['endpoint']['eog']==prior['eog'],'new paid R identical old R '+pair['task'])
 native=next(r for r in rr if r['config']['label']=='M_failed');nid=native['endpoint']['ids'];boundary=next((i for i,(a,b) in enumerate(zip(nid,refs)) if a!=b),None);check(boundary is not None,'original failure persists '+pair['task'])
 for r in rr:
  u=r['unit_id'];raw=raw_by_unit[u];ids=r['endpoint']['ids'];diff=next((i for i,(a,b) in enumerate(zip(ids,refs)) if a!=b),min(len(ids),len(refs)) if ids!=refs else None);i=boundary
  if i>=len(raw['commits']):
   observations.append(dict(task=pair['task'],label=r['config']['label'],unit_id=u,boundary=i,qualified=same(r['endpoint'],reference['endpoint']),first_difference=diff,comparison='ENDED_BEFORE_SELECTED_BOUNDARY'));continue
  v=np.fromfile(logits_by_unit[u][i],dtype='<f4');c=raw['commits'][i];ref_token=refs[i];alternative=nid[i];top1=int(np.argmax(v));w=v.copy();w[top1]=-np.inf;top2=int(np.argmax(w));eog_best=max(eogs,key=lambda t:float(v[t]));common=ids[:i]==refs[:i]
  # Locate candidate decode events compatible with the actual sampled position.
  position=len(raw['prompt_ids'])+i-1
  events=[dict(event_index=j,**e) for j,e in enumerate(raw['trace']) if e['event']=='decode' and e['role']=='target' and position in e['positions'] and e['after']['max']==c['kv']['max']]
  query=events[-1] if events else None
  query_info={k:query[k] for k in ['event_index','input_ids','positions','sequence_ids','logits_requested','caller_batch_length','ub_capacity','graphs']} if query else None
  obs=dict(task=pair['task'],pair=pi,k=pair['k'],ub=pair['ub'],cap=pair['cap'],label=r['config']['label'],unit_id=u,qualified=same(r['endpoint'],reference['endpoint']),raw_length=len(raw['ids']),endpoint_length=len(ids),first_difference=diff,selected_natural_boundary=i,natural_common_prefix=common,common_prefix_sha256=hashlib.sha256(json.dumps(ids[:i],separators=(',',':')).encode()).hexdigest(),committed_id=ids[i],top1=top1,top2=top2,top1_logit=float(v[top1]),top2_logit=float(v[top2]),top1_top2_margin=float(v[top1])-float(v[top2]),reference_id=ref_token,reference_is_eog=ref_token in eogs,reference_logit=float(v[ref_token]),natural_native_alternative_id=alternative,alternative_is_eog=alternative in eogs,alternative_logit=float(v[alternative]),reference_minus_alternative=float(v[ref_token])-float(v[alternative]),best_runtime_eog_id=eog_best,best_eog_logit=float(v[eog_best]),reference_minus_best_eog=float(v[ref_token])-float(v[eog_best]),decision_logit_sha256=sha(logits_by_unit[u][i]),state_position=c['kv'],logits_index=c['logits_index'],compatible_target_decode=query_info,query_association='Last retained compatible target decode by natural position and KV maximum; no mid-state donor reconstruction or claimed crossed equivalence',transfer=raw['transfer'],work=raw['work'],metrics=r['metrics'],timing_scope='CAPTURE_DIAGNOSTIC_ONLY_NOT_PERFORMANCE')
  observations.append(obs)
 # These native outputs must reproduce both prior pilot repetitions.
 pilot=[r for r in load(ROOT/'PILOT_DEPENDENCY.json')['records'] if r['task']==pair['task'] and r['config']['k']==pair['k'] and r['config']['ub']==pair['ub']]
 check(len(pilot)==2 and all(same(native['endpoint'],r['endpoint']) for r in pilot),'observational change preserves prior failure '+pair['task'])
 anchor=next(r for r in rr if r['config']['label']=='N1_repaired');check(same(anchor['endpoint'],reference['endpoint']),'original anchor preserved '+pair['task'])
result=dict(status='PASS' if not errors else 'FAIL',utc=datetime.now(timezone.utc).isoformat(),checks=checks,errors=errors,raw_records=len(records),planned_nonwarm=18,completed_nonwarm=len(nonwarm),warm=14,full_logit_rows=logit_rows,selected_pairs=am['selection'],observations=observations,causal_status='NOT_CAUSALLY_IDENTIFIED',state_cross='NOT_IMPLEMENTED',auxiliary_model_forwards=0,performance_samples_added=0,original_failures_preserved=True,claim='Authentic natural trajectories and raw full decision scores show local margin and caller boundaries. Parent comparisons with different callers or past states are not crossed causal interventions. No unique kernel, universal bound, online guard or opaque sampler-byte claim.')
save(ROOT/'SUPPLEMENT_VERIFICATION.json',result);print({k:result[k] for k in ['status','checks','errors','raw_records','full_logit_rows']},flush=True);assert not errors,errors[:20]
