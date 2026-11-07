#!/usr/bin/env python3
"""Standard-library reviewer recomputation; no model, network or external assets."""
import collections,hashlib,json,math,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def check_rows(rows,n):
 pairs={(r['task_id'],r['repetition']) for r in rows};assert len(rows)==len(pairs)==3*n and len({t for t,r in pairs})==n
 assert all({r for a,r in pairs if a==t}=={1,2,3} for t,r in pairs)
def quantile(v,q):
 v=sorted(v);p=(len(v)-1)*q;i=int(p);j=math.ceil(p);return v[i]+(v[j]-v[i])*(p-i)
def validate(studies):
 results={};s=studies['B570_original_H1'];rows=s['rows'];check_rows(rows,24);counts={k:sum(x['arrays'][a]==x['arrays'][b] for x in rows) for k,a,b in [('prediction_live','prediction','live'),('reference_live','reference','live')]};assert counts=={'prediction_live':72,'reference_live':60};assert all(len(a)==128 for x in rows for a in x['arrays'].values());assert len({x['task_id'] for x in rows if x['arrays']['reference']!=x['arrays']['live']})==4;results['B570_original_H1']=counts
 s=studies['B570_live_intervention'];rows=s['rows'];check_rows(rows,24);score=sum(x['primary_scores']!=x['alternate_scores'] for x in rows);top=sum(any(a['raw_top1_id']!=b['raw_top1_id'] for a,b in zip(x['primary_scores'],x['alternate_scores'])) for x in rows);dec=sum(any(a['native']['committed_id']!=a['alternate']['committed_id'] or a['native']['accepted_proposal']!=a['alternate']['accepted_proposal'] for a in x['paired_decisions']) for x in rows);later=sum(x['primary_ids']!=x['alternate_ids'] for x in rows);events=sum(len(x['paired_decisions']) for x in rows);assert (score,top,dec,later,events)==(72,0,0,18,195);assert len({x['task_id'] for x in rows if x['primary_ids']!=x['alternate_ids']})==6
 for x in rows:
  assert x['checkpoint_output_index']>=64 and x['primary_ids'][:x['checkpoint_output_index']]==x['alternate_ids'][:x['checkpoint_output_index']]
  st=x['state'];assert st['serialized_kv_equal'] and st['source_unchanged'] and st['state_bytes']==st['consumed_bytes'] and st['sampler_chain']==st['clone_chain'] and st['sampler_history']==st['clone_history'] and st['sampler_seed']==st['clone_seed']
 results['B570_live_intervention']={'score':score,'raw_top1':top,'immediate':dec,'continuation':later,'correlated_events':events}
 s=studies['RTX_H1_discovery'];rows=s['rows'];check_rows(rows,12);c=s['conditions'];assert sum(x['arrays'][c[0]]==x['arrays'][c[1]] for x in rows)==24 and s['reserved_executions']==0 and s['selected_hypothesis'] is None;results['RTX_H1_discovery']={'matches':24,'total':36,'reserved':0}
 s=studies['RTX_H2'];rows=s['rows'];check_rows(rows,24);a='REFERENCE_UB1';b='RTX_BATCHED_K2';counts={k:sum(x['arrays'][l]==x['arrays'][r] for x in rows) for k,l,r in [('H2_live','H2_P_R',b),('R_ONLY_live','R_ONLY',b),('H2_R_ONLY','H2_P_R','R_ONLY'),('reference_live',a,b)]};assert counts=={'H2_live':72,'R_ONLY_live':72,'H2_R_ONLY':72,'reference_live':60}
 assert s.get('qualification_status','BLOCKED')=='BLOCKED' and s.get('prediction_status','MATCH')=='MATCH'
 assert {x['task_id'] for x in rows if x['arrays'][a]!=x['arrays'][b]}=={'HumanEval/17','HumanEval/33','HumanEval/14','HumanEval/22'}
 for x in rows:
  for c,arr in x['arrays'].items():
   assert 0<len(arr)<=128 and (x['termination'][c]=='EOS' and arr[-1] in (151643,151645) or x['termination'][c]=='limit' and len(arr)==128)
   assert hashlib.sha256(json.dumps(arr,separators=(',',':')).encode()).hexdigest()==x['array_sha256'][c]
 assert sum(x['termination'][b]=='EOS' for x in rows)==63 and sum(x['termination'][b]=='limit' for x in rows)==9;results['RTX_H2']=counts
 s=studies['RTX_matched_latency'];rows=s['run_rows'];by={(x['task_id'],x['repetition'],x['condition']):x for x in rows};assert len(rows)==len(by)==180;ratios=[]
 for p in s['prompt_rows']:
  t=p['task_id'];ref=statistics.median(by[t,r,'TARGET_REFERENCE']['milliseconds'] for r in (1,2,3));ser=statistics.median(by[t,r,'RTX_SERIALIZED_K2']['milliseconds'] for r in (1,2,3));assert ref==p['reference_median_ms'] and ser==p['serialized_median_ms'] and ref/ser==p['ratio'];ratios.append(ref/ser)
  for r in (1,2,3):assert by[t,r,'TARGET_REFERENCE']['generated_ids']==by[t,r,'RTX_SERIALIZED_K2']['generated_ids']
 assert len(ratios)==30 and sum(r>1 for r in ratios)==0
 logs=[math.log(x) for x in ratios];gm=math.exp(math.fsum(logs)/30);rng=random.Random(2026093002);samples=[math.exp(math.fsum(logs[rng.randrange(30)] for _ in range(30))/30) for _ in range(10000)];ci=[quantile(samples,q) for q in (.025,.975)];assert abs(gm-s['ratio'])<1e-14 and all(abs(a-b)<1e-14 for a,b in zip(ci,s['ci95']));results['RTX_matched_latency']={'ratio':gm,'ci95':ci,'pairs':90,'runs':180}
 return results
def main():
 m=read(ROOT/'SHA256SUMS.json');assert {p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()}==set(m)|{'SHA256SUMS.json'}
 for n,h in m.items():assert digest(ROOT/n)==h,n
 studies={p.stem:read(p) for p in (ROOT/'evidence').glob('*.json')};r=validate(studies);print(json.dumps({'status':'PASS','studies':r,'limits':'Derived retained arrays/paired records/times only. Original chronology and omitted external bytes not authenticated; no functional pass@k.'}))
if __name__=='__main__':main()
