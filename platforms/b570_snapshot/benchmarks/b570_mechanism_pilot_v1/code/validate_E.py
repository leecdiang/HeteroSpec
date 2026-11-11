"""Independent native paid-reference qualification and cost derivation, CPU only."""
from pathlib import Path
import json,hashlib,csv,statistics,math,sys
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def gm(v):return math.exp(sum(math.log(x) for x in v)/len(v))
def difference(a,b):
 for i,(x,y) in enumerate(zip(a,b)):
  if x!=y:return i
 return None if len(a)==len(b) else min(len(a),len(b))
def main():
 manifest=load(R/'E_MANIFEST.json');inputs=load(R/'E_INPUTS.json');eog=set(load(R/'dependencies/TOKENIZATION_PROOF.json')['runtime_eog_ids']);data={};errors=[];checks=0;rows=[];costs=[];qualification_errors=[];diagnostic_variations=[]
 def ck(v,t):
  nonlocal checks;checks+=1
  if not v:errors.append(t)
 for group in manifest['formal_sessions']:
  for u in group['units']:
   p=R/'raw'/hashlib.sha256(u['unit_id'].encode()).hexdigest()[:20]/'RESULT.json';ck(p.exists(),'missing formal denominator '+u['unit_id'])
   if not p.exists():continue
   r=load(p);ck(r['config']==group['config'],'frozen session and request config '+u['unit_id'])
   for f,h in r['files'].items():ck(sha(R/f)==h,'full raw hash '+f)
   raw=load(R/next(f for f in r['files'] if f.endswith('/capture.json')));ids=raw['ids'];flags=raw['eog'];ck(flags==[t in eog for t in ids],'all runtime EOG '+u['unit_id']);n=min(128,next((i+1 for i,t in enumerate(ids) if t in eog),len(ids)));ep=dict(ids=ids[:n],eog=flags[:n],reason='EOG' if ids[n-1] in eog else 'CAP',raw_suffix=len(ids)-n);ck(ep==r['endpoint'],'full endpoint and charged suffix '+u['unit_id']);ck(raw['prompt_ids']==next(i['prompt_ids'] for i in inputs if i['id']==u['task']),'fixed eligible prompt identity '+u['unit_id'])
   key=(u['task'],group['config']['label'],group['config']['round']);ck(key not in data,'unique task/mode/round');data[key]=(r,raw,ep)
 for inp in inputs:
  task=inp['id']
  if not all((task,'ordinary_R',round) in data for round in [1,2]):continue
  refs=[data[task,'ordinary_R',round] for round in [1,2]]
  if refs[0][1]['ids']!=refs[1][1]['ids'] or refs[0][1]['eog']!=refs[1][1]['eog']:qualification_errors.append('paid R full raw unstable '+task)
  for label in ['ordinary_R','matched_target','candidate','old_N1']:
   mode=[]
   for round in [1,2]:
    if (task,label,round) not in data:continue
    r,raw,ep=data[task,label,round];ref=data[task,'ordinary_R',round][2];passed=all(ep[k]==ref[k] for k in ['ids','eog','reason']);rows.append(dict(task=task,label=label,round=round,qualified=passed,first_difference=difference(ep['ids'],ref['ids']),complete_endpoint_length=len(ep['ids']),raw_length=len(raw['ids']),raw_suffix=ep['raw_suffix'],reason=ep['reason']));mode.append(raw)
   if len(mode)==2 and (mode[0]['ids']!=mode[1]['ids'] or mode[0]['eog']!=mode[1]['eog']):
    (diagnostic_variations if label=='old_N1' else qualification_errors).append('full raw repeat unstable '+task+'/'+label)
 summaries=[]
 timers=['generation_ms','whole_request_ms','host_end_to_end_ms']
 for baseline in ['ordinary_R','matched_target','old_N1']:
  for timer in timers:
   ratios=[];by_round=[[],[]]
   for inp in inputs:
    task=inp['id']
    if not all((task,label,round) in data for label in [baseline,'candidate'] for round in [1,2]):continue
    def value(label,round):
     r=data[task,label,round][0];return r['host_seconds']*1000 if timer=='host_end_to_end_ms' else r['metrics'][timer]
    b=[value(baseline,round) for round in [1,2]];c=[value('candidate',round) for round in [1,2]];ratio=statistics.median(b)/statistics.median(c);ratios.append(ratio)
    for round in [1,2]:by_round[round-1].append(b[round-1]/c[round-1])
    bqualified=all(next(v['qualified'] for v in rows if v['task']==task and v['label']==baseline and v['round']==round) for round in [1,2]);cqualified=all(next(v['qualified'] for v in rows if v['task']==task and v['label']=='candidate' and v['round']==round) for round in [1,2])
    costs.append(dict(task=task,baseline=baseline,candidate='candidate',timer=timer,baseline_round1_ms=b[0],baseline_round2_ms=b[1],candidate_round1_ms=c[0],candidate_round2_ms=c[1],baseline_median_ms=statistics.median(b),candidate_median_ms=statistics.median(c),speed_ratio=ratio,round1_ratio=b[0]/c[0],round2_ratio=b[1]/c[1],baseline_qualified=bqualified,candidate_qualified=cqualified,cost_scope='qualified_formal' if bqualified and cqualified else 'diagnostic_failed_output'))
   if ratios:summaries.append(dict(baseline=baseline,candidate='candidate',timer=timer,tasks=len(ratios),GM=gm(ratios),round1_GM=gm(by_round[0]),round2_GM=gm(by_round[1]),all_qualified=all(v['baseline_qualified'] and v['candidate_qualified'] for v in costs if v['baseline']==baseline and v['timer']==timer)))
 complete=len(data);qualified=complete==len(inputs)*8 and all(v['qualified'] for v in rows if v['label'] in ['candidate','matched_target']) and not errors and not qualification_errors
 def summary(base,timer):return next((v for v in summaries if v['baseline']==base and v['timer']==timer),None)
 gen=summary('ordinary_R','generation_ms');whole=summary('ordinary_R','whole_request_ms')
 efficiency=qualified and gen and whole and gen['GM']>=1.05 and whole['GM']>=1.03 and all(x['round1_GM']>1 and x['round2_GM']>1 for x in [gen,whole])
 if not qualified:decision='NO_GO_TRANSFER'
 elif efficiency:decision='GO_LARGER_VALIDATION'
 elif gen['GM']<1 and whole['GM']<1 and summary('old_N1','whole_request_ms')['GM']>1:decision='SCOPED_REPAIR_WITHOUT_DEPLOYMENT_GAIN'
 else:decision='NO_GO_EFFICIENCY'
 result=dict(status='PASS' if not errors else 'FAIL',checks=checks,errors=errors,qualification_errors=qualification_errors,diagnostic_variations=diagnostic_variations,decision=decision,planned=len(inputs)*8,complete=complete,tasks=len(inputs),qualification_gate=bool(qualified),efficiency_gate=bool(efficiency),rows=rows,cost_summaries=summaries,no_significance_or_production_claim=True,baseline_candidate_ratio_definition='Per-task median of two absolute baseline costs divided by median candidate costs, then geometric mean across tasks; >1 candidate faster',old_N1_failed_outputs_diagnostic_only=True)
 (R/'E_VERIFICATION.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
 if costs:
  with (R/'E_COSTS.csv').open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=list(costs[0]));w.writeheader();w.writerows(costs)
 print(result['status'],decision,complete,checks,errors[:8],[(v['baseline'],v['timer'],v['GM']) for v in summaries],flush=True);return result
if __name__=='__main__':main()
