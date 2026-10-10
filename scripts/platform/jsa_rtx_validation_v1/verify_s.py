"""Independent CPU reconstruction of every frozen S slot and estimator."""
import json,hashlib,statistics,math,csv,os
from pathlib import Path
REPO=Path(__file__).resolve().parents[3];PUB=REPO/'benchmarks/jsa_rtx_validation_v1';LOCAL=Path(os.environ.get('JSA_LOCAL_ROOT',str(REPO.parent/'jsa')))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csv_write(p,rows):
    with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def main():
    plan=read(PUB/'S_F0.json');slots=read(LOCAL/'S_SLOTS.json');tasks={t['id']:t for t in read(PUB/'S_INPUTS.json')};expected=[slot for b in plan['blocks'] for slot in b['slots']];assert len(set(expected))==len(expected)==768 and set(slots)==set(expected)
    eog=set(read(PUB/'S_TOKEN_CONTRACT.json')['eog']);records={};checks=[]
    for slot,a in slots.items():
        if a['status']!='COMPLETED':continue
        p=LOCAL/a['record'];assert h(p)==a['record_sha256'];r=read(p);assert r['slot']==slot;t=tasks[r['task']];resp=r['response'];ids=resp['tokens']
        valid=all(isinstance(x,int) for x in ids) and len(ids)==resp['tokens_predicted'] and 0<len(ids)<=128 and not any(x in eog for x in ids[:-1]) and ((ids[-1] in eog)==(resp['stop_type']=='eos')) and (len(ids)==128 or resp['stop_type']=='eos') and not resp['truncated'] and resp['timings']['cache_n']==0 and resp['prompt']==t['formatted_prompt'] and resp['timings']['prompt_n']==t['prompt_token_count'] and math.isfinite(r['wall_ms']) and r['wall_ms']>0
        assert hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()==r['tokens_digest'];records[(r['session'],r['round'],r['task'],r['condition']['name'])]=r;checks.append({'slot':slot,'valid_contract':valid})
    conditions=['scalar_reference','matched_target','target_scopes','all_scopes'];complete=len(records)==768 and all(r['valid_contract'] for r in checks);qualification={};stable=True
    for tid in tasks:
        refs=[r['response'] for (s,n,t,c),r in records.items() if t==tid and c=='scalar_reference']
        stable&=len(refs)==8 and all(r['tokens']==refs[0]['tokens'] and r['stop_type']==refs[0]['stop_type'] for r in refs)
    for c in conditions:
        equal=True;count=0;failures=[]
        for key,r in records.items():
            s,n,tid,name=key
            if name!=c:continue
            ref=records.get((s,n,tid,'scalar_reference'));count+=1
            ok=ref is not None and r['response']['tokens']==ref['response']['tokens'] and r['response']['stop_type']==ref['response']['stop_type']
            if not ok:
                left=ref['response']['tokens'] if ref else [];right=r['response']['tokens'];i=next((i for i in range(max(len(left),len(right))) if (left[i] if i<len(left) else None)!=(right[i] if i<len(right) else None)),None)
                failures.append({'session':s,'round':n,'task':tid,'first_divergence_zero_based':i,'reference_length':len(left),'candidate_length':len(right)})
            equal&=ok
        qualification[c]={'qualified':complete and stable and count==192 and equal,'completed':count,'mismatch_count':len(failures),'mismatches':failures}
    comparisons=[('matched_target','target_scopes','primary'),('scalar_reference','target_scopes','secondary'),('scalar_reference','matched_target','secondary'),('all_scopes','target_scopes','secondary')];task_rows=[];session_rows=[];round_rows=[]
    for baseline,candidate,kind in comparisons:
        allowed=qualification[baseline]['qualified'] and qualification[candidate]['qualified'];effects=[]
        for s in [1,2]:
            per_task=[]
            for tid in tasks:
                a=[records[(s,r,tid,baseline)]['wall_ms'] for r in range(1,5) if (s,r,tid,baseline) in records];b=[records[(s,r,tid,candidate)]['wall_ms'] for r in range(1,5) if (s,r,tid,candidate) in records]
                ratio=statistics.median(a)/statistics.median(b) if len(a)==len(b)==4 else None
                if ratio is not None:per_task.append(math.log(ratio))
                ga=[records[(s,r,tid,baseline)]['response']['timings']['predicted_ms'] for r in range(1,5) if (s,r,tid,baseline) in records];gb=[records[(s,r,tid,candidate)]['response']['timings']['predicted_ms'] for r in range(1,5) if (s,r,tid,candidate) in records];gr=statistics.median(ga)/statistics.median(gb) if len(ga)==len(gb)==4 and statistics.median(gb)>0 else None
                task_rows.append({'session':s,'task':tid,'baseline':baseline,'candidate':candidate,'baseline_median_ms':statistics.median(a) if a else None,'candidate_median_ms':statistics.median(b) if b else None,'diagnostic_ratio':ratio,'qualified_ratio':ratio if allowed else None,'generation_baseline_median_ms':statistics.median(ga) if ga else None,'generation_candidate_median_ms':statistics.median(gb) if gb else None,'generation_secondary_ratio':gr if allowed else None})
            effect=statistics.mean(per_task) if len(per_task)==24 else None
            if effect is not None:effects.append(effect)
            session_rows.append({'session':s,'comparison':baseline+'/'+candidate,'kind':kind,'diagnostic_ratio':math.exp(effect) if effect is not None else None,'qualified_ratio':math.exp(effect) if effect is not None and allowed else None,'task_regressions':sum(v<0 for v in per_task),'complete_tasks':len(per_task)})
            for n in range(1,5):
                rr=[math.log(records[(s,n,t,baseline)]['wall_ms']/records[(s,n,t,candidate)]['wall_ms']) for t in tasks if (s,n,t,baseline) in records and (s,n,t,candidate) in records]
                round_rows.append({'session':s,'round':n,'comparison':baseline+'/'+candidate,'diagnostic_ratio':math.exp(statistics.mean(rr)) if len(rr)==24 else None,'qualified_ratio':math.exp(statistics.mean(rr)) if len(rr)==24 and allowed else None})
        if kind=='primary':primary=math.exp(statistics.mean(effects)) if len(effects)==2 and allowed else None
    counts={name:sum(a['status']==name for a in slots.values()) for name in sorted({a['status'] for a in slots.values()})};warmups=len(list((LOCAL/'runs/S_formal').glob('*/WARMUP.json')))
    result={'status':'COMPLETE_QUALIFIED_SAME_DAY' if primary is not None else ('COMPLETE_NEGATIVE' if complete else 'INCOMPLETE'),'formal_planned':768,'formal_completed':len(records),'slot_statuses':counts,'warmups':warmups,'full_contract_valid':all(r['valid_contract'] for r in checks),'stable_reference':stable,'qualification':qualification,'primary_request_ratio':primary,'primary_session_ratios':[r['qualified_ratio'] for r in session_rows if r['kind']=='primary'],'cross_date_interval':None,'cross_date_benefit':'NOT_TESTED_AUTHOR_AMENDMENT','checks':checks,'freeze_sha':read(LOCAL/'S_REMOTE_RECEIPT.json')['frozen_sha'],'analysis':'within-session task/condition absolute medians across4 rounds; session mean log ratios; exponentiated mean of2 session effects; no day t interval','raw_slots_sha256':h(LOCAL/'S_SLOTS.json')}
    (PUB/'S_QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');csv_write(PUB/'S_TASKS.csv',task_rows);csv_write(PUB/'S_SESSIONS.csv',session_rows);csv_write(PUB/'S_ROUNDS.csv',round_rows)
    print(json.dumps({k:result[k] for k in ['status','formal_completed','warmups','stable_reference','primary_request_ratio','primary_session_ratios']}),flush=True)
if __name__=='__main__':main()
