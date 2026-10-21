"""Prespecified same-prefix frontiers and the complete bounded new matrix."""
from __future__ import annotations
import argparse,collections,itertools,random
from pathlib import Path
from contracts import *

def frontier(endpoints,arms):
 seq=[endpoints[s]['ids'] for s in arms];length=min(map(len,seq));t=next((i for i in range(length) if len({v[i] for v in seq})!=1),None)
 if t is not None:
  require(t!=0,'RESTORE_T0_ANOMALY: same recipient first token differs')
  require(all(s[:t]==seq[0][:t] for s in seq),'different token prefixes');r=seq[0][t];u=next(endpoints[s]['ids'][t] for s in arms[1:] if endpoints[s]['ids'][t]!=r)
  requested=sorted(set((1,t-1,t)));valid=[q for q in requested if 1<=q<=127 and q<length]
  return {'status':'ALIGNED_FIRST_DIFFERENT_DECISION','t_star':t,'common_prefix_ids':seq[0][:t],'common_effective_length':length,'positions':valid,'not_reached':[q for q in requested if q not in valid],'token_pair_rule':'FRONTIER_EMPTY_R_FIRST_NONEMPTY_DIFFERENT_U_IN_FIXED_ARM_ORDER_SHARED_AT_ALL_SELECTED_POSITIONS','r':r,'u':u,'priority':list(arms[1:])}
 stop={e['stop_reason'] for e in endpoints.values()};same_lengths=len({len(v) for v in seq})==1
 if not same_lengths or len(stop)>1:return {'status':'ENDPOINT_ONLY','t_star':None,'common_prefix_ids':seq[0][:length],'common_effective_length':length,'positions':[],'not_reached':[],'token_pair_rule':None,'r':None,'u':None,'priority':list(arms[1:])}
 status='EOG_FINISHED' if stop=={'EOG'} else 'RIGHT_CENSORED_AT_128';requested=[1,31,63,95,127]
 return {'status':status,'t_star':None,'common_prefix_ids':seq[0][:length],'common_effective_length':length,'positions':[q for q in requested if q<length],'not_reached':[q for q in requested if q>=length],'token_pair_rule':'EMPTY_HEAVY_REPEAT0_TOP1_TOP2_STABLE_TOKEN_ID_TIE_SHARED_BOTH_REPEATS','r':None,'u':None,'priority':list(arms[1:])}
def old_index(audit):
 idx=collections.defaultdict(list)
 for r in audit['rows']:idx[(r['task'],r['recipient'],r['selector'])].append(r)
 for key,rs in idx.items():require(len(rs)==2 and rs[0]['endpoint']==rs[1]['endpoint'],'old repeat mismatch/missing: '+str(key))
 return idx
def ordered_stage(cells,mode,repeats,seed):
 # Balanced groups: task order rotates, recipient and state order alternate; no outcome-based ordering.
 rng=random.Random(seed);states=sorted({c['state'] for c in cells});rng.shuffle(states);tasks=list(CASES);rng.shuffle(tasks);lookup={(c['task'],c['recipient'],c['state']):c for c in cells};rows=[]
 for repeat in range(repeats):
  for j,state in enumerate(states):
   for k,task in enumerate(tasks[j%len(tasks):]+tasks[:j%len(tasks)]):
    for recipient in (('A','B') if (j+k+repeat)%2==0 else ('B','A')):
     c=lookup.get((task,recipient,state))
     if c:rows.append(dict(c,mode=mode,repeat=repeat))
 return rows
def build(audit,fresh):
 idx=old_index(audit);res=Resolver(fresh,audit['resolver_original_prefix']);panels=[];gaps=[];cells=[]
 for task in CASES:
  for recipient in ('A','B'):
   cuts={s:set() for s in STATES}
   for panel,arms in PANELS.items():
    endpoints={s:idx[(task,recipient,s)][0]['endpoint'] for s in arms};p=dict(task=task,recipient=recipient,donor='B' if recipient=='A' else 'A',panel=panel,arms=list(arms),**frontier(endpoints,arms));available=[]
    for state in arms:
     cuts[state].update(p['positions'])
     for old in sorted(idx[(task,recipient,state)],key=lambda r:r['repeat']):
      x=res.record_file(old['raw_path'],old['raw_sha256'])
      for t in p['positions']:
       z,proof=logits_at(x,t,res,old['initial_logits_spec']);row={'task':task,'recipient':recipient,'panel':panel,'state':state,'repeat':old['repeat'],'t':t,'available':z is not None,'proof':proof};available.append(row)
       if z is None:gaps.append(row)
    p['old_availability']=available;panels.append(p)
   for state in STATES:
    old=idx[(task,recipient,state)][0];cells.append({'task':task,'recipient':recipient,'donor':old['donor'],'direction':old['direction'],'state':state,'cuts':sorted(cuts[state]),'prompt_ids':read(fresh/'PLAN.json')['cases'][task]['prompt_ids'],'mixture_spec':dict(old['mixture_spec'],path=str(res.resolve(old['mixture_spec']['path']))),'initial_logits_spec':dict(old['initial_logits_spec'],path=str(res.resolve(old['initial_logits_spec']['path']))),'reference_endpoint':old['endpoint'],'reference_old_slots':[r['slot'] for r in idx[(task,recipient,state)]]})
 require(len(cells)==len(CASES)*2*len(STATES),'cell inventory')
 stages=[('anchor_counts','counts',1,[c for c in cells if c['state'] in ('EMPTY','ALL')]),('anchor_heavy','heavy',2,[c for c in cells if c['state'] in ('EMPTY','ALL')]),('subset_counts','counts',1,[c for c in cells if c['state'] not in ('EMPTY','ALL')]),('subset_heavy','heavy',2,[c for c in cells if c['state'] not in ('EMPTY','ALL')])];requests=[]
 for i,(stage,mode,repeats,cs) in enumerate(stages):
  rr=ordered_stage(cs,mode,repeats,20261014+i)
  for order,r in enumerate(rr):
   r.update(stage=stage,order=order);r['slot']=digest(encoded({k:r[k] for k in ('task','recipient','state','stage','mode','repeat')}))[:24];requests.append(r)
 require(len(requests)==len(cells)*3==168 and len({r['slot'] for r in requests})==len(requests),'new budget/slot duplication')
 require(dict(collections.Counter(r['stage'] for r in requests))=={'anchor_counts':16,'anchor_heavy':32,'subset_counts':40,'subset_heavy':80},'stage budget')
 return {'schema':1,'study':'b570-decision-frontier-v1','input_commit':RESULT103,'registration103':REG103,'baseline_commit':BASE101,'historical_results_exposed':True,'positions_selected_from_exposed_endpoints_not_blind_validation':True,'panels':panels,'cells':cells,'requests':requests,'old_full_logits_gap_count':len(gaps),'old_full_logits_gaps':gaps,'need_new_native':bool(gaps),'budgets':{'request_start_attempts_including_failed_loads':168,'owned_native_process_seconds':21600,'new_run_bytes':4*1024**3,'external_readonly_sources_excluded':True,'warmups':0,'smoke_requests':0,'scientific_retries':0},'rules':{'arithmetic':'FP32 source vectors promoted to FP64; FP64 differences and sums; preserve both repeats; no epsilon zero declarations','L0':'d=z[u]-z[r]; delta_K=d_K-d_EMPTY; delta_V=d_V-d_EMPTY; I=d_KV-d_K-d_V+d_EMPTY','POSITION':'I=d_ALL-d_prefix-d_tail+d_EMPTY','vector_residual':'full vocabulary FP64 vector follows same four-cell contrast','margin_certificate':'observed EMPTY top1 margin m > 2*||z_S-z_EMPTY||_infinity is sufficient at that observed same-prefix position only; converse false','third_candidates':'report true argmax and r/u ranks over complete vocabulary','no_drift_hiding':'preserve unequal repeated FP32 logits even when endpoint equal'},'geometry':{'UB':512,'ordinary':True,'greedy':'native stateless','KV':'F16','FA':False,'ctx':1024,'cap':128,'threads':10,'operator_capture':False,'restore_prefill_schedule':[],'heavy':{'capture':True,'phase96_diagnostic':True,'evidence':'trace.json'},'counts':{'capture':False,'phase96_diagnostic':False,'boundary_cuts':[],'evidence':'memory.json_no_full_geometry'}},'upstream_injection_authorized':False}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--fresh',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();p=build(read(a.audit),a.fresh);write(a.output,p);print(json.dumps({'panels':[{k:r[k] for k in ('task','recipient','panel','status','t_star','positions','r','u')} for r in p['panels']],'old_full_logits_gap_count':p['old_full_logits_gap_count'],'need_new_native':p['need_new_native'],'request_budget':len(p['requests'])},indent=2))
