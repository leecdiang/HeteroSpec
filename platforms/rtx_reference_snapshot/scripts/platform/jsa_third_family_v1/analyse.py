"""Independent CPU reanalysis: native full arrays; two-session descriptive effects."""
from common import *
import math,statistics,collections
from datetime import timedelta

def signature(r):return (r.get('tokens'),r.get('stop_type'),r.get('stopping_word'),r.get('truncated'))
def contract(a,t,eog):
    r=a['response'];ids=r.get('tokens');timing=r.get('timings',{})
    return isinstance(ids,list) and 0<len(ids)<=t['cap'] and all(type(i) is int for i in ids) and len(ids)==r.get('tokens_predicted') and not any(i in eog for i in ids[:-1]) and ((ids[-1] in eog)==(r.get('stop_type')=='eos')) and (len(ids)==t['cap'] or r.get('stop_type')=='eos') and not r.get('truncated',True) and timing.get('cache_n')==0 and timing.get('prompt_n')==t['prompt_token_count'] and math.isfinite(a['wall_ms']) and a['wall_ms']>0

def analyse(local=LOCAL,pub=PUB):
    plan=read(pub/'FORMAL_PLAN.json');inputs=read(pub/'CONFIRMATION_INPUTS.json');models=read(pub/'MODEL_CONTRACT.json')['families'];freeze=read(local/'F0B_REMOTE_RECEIPT.json')
    expected={slot:b for b in plan['blocks'] for slot in b['slots']};assert len(expected)==3456
    records={};ledger={s:{'status':'PLANNED_OR_UNEXECUTED'} for s in expected};contracts={};cases=[]
    root=local/'runs/formal'
    for p in sorted(root.rglob('REQUEST_STARTED.json')):
        started=read(p)
        if started['warmup']:continue
        slot=started['slot'];assert slot in expected and ledger[slot]['status']=='PLANNED_OR_UNEXECUTED','duplicate paid slot'
        ledger[slot]={'status':'STARTED_NO_COMPLETE_RECORD','started':str(p.relative_to(local)),'started_sha256':sha(p)}
        done=p.parent/'COMPLETED.json';record=p.parent/'RECORD.json'
        if done.exists():
            assert sha(record)==read(done)['record_sha256'];a=read(record);b=expected[slot]
            assert a['slot']==slot and a['family']==b['family'] and a['condition']==b['condition'] and a['freeze_commit']==freeze['frozen_sha']
            assert a['tokens_digest']==digest(a['response'].get('tokens'))
            task=next(t for t in inputs['families'][b['family']] if t['id']==a['task']);assert a['input_sha256']==digest(task)
            records[slot]=a;contracts[slot]=bool(contract(a,task,set(models[b['family']]['eog'])))
            ledger[slot].update(status='COMPLETED',record=str(record.relative_to(local)),record_sha256=sha(record),contract_valid=contracts[slot])
            ids=a['response'].get('tokens',[]);eog=set(models[b['family']]['eog']);first_eog=next((i for i,x in enumerate(ids) if x in eog),None)
            endpoint=min(task['cap'],first_eog+1 if first_eog is not None else len(ids))
            cases.append({'slot':slot,'family':b['family'],'condition':b['condition']['name'],'task':a['task'],'session':b['session'],'round':b['round'],'wall_ms':a['wall_ms'],'length':len(ids),'stop_type':a['response'].get('stop_type'),'terminal_id':ids[-1] if ids else None,'suffix_ids':ids[endpoint:],'contract_valid':contracts[slot],'utc':a['utc'],'native_counts':{'tokens_predicted':a['response'].get('tokens_predicted'),**{k:a['response'].get('timings',{})[k] for k in ['draft_n','draft_n_accepted'] if k in a['response'].get('timings',{})}}})
        elif (p.parent/'FAILED.json').exists():ledger[slot]['status']='FAILED_OPERATION'
    for p in sorted((root/'missing').glob('*.json')):
        a=read(p);slot=a['slot'];assert slot in expected and ledger[slot]['status']=='PLANNED_OR_UNEXECUTED';ledger[slot]={'status':a['status'],'evidence':str(p.relative_to(local)),'sha256':sha(p)}
    result={};taskcosts=[]
    for family in models:
        tids=[t['id'] for t in inputs['tasks']];by_key={(expected[s]['session'],expected[s]['round'],records[s]['task'],expected[s]['condition']['name']):a for s,a in records.items() if expected[s]['family']==family}
        refs={tid:[by_key.get((session,rnd,tid,'R')) for session in range(2) for rnd in range(4)] for tid in tids}
        stable_R=all(all(a is not None for a in rows) and all(signature(a['response'])==signature(rows[0]['response']) for a in rows if a is not None) for rows in refs.values())
        qual={};costs={}
        for c in plan['conditions']:
            name=c['name'];mismatches=[];invalid=[];completed=0;stable=True
            for tid in tids:
                allrows=[by_key.get((session,rnd,tid,name)) for session in range(2) for rnd in range(4)];existing=[a for a in allrows if a is not None]
                stable &= len(existing)==8 and all(signature(a['response'])==signature(existing[0]['response']) for a in existing)
                for a in existing:
                    completed+=1
                    if not contracts[a['slot']]:invalid.append(a['slot'])
                    different=[r for r in refs[tid] if r is not None and signature(a['response'])!=signature(r['response'])]
                    if different:
                        ref=different[0]['response'];r=a['response'];left=ref.get('tokens',[]);right=r.get('tokens',[])
                        first=next((i for i in range(max(len(left),len(right))) if (left[i] if i<len(left) else None)!=(right[i] if i<len(right) else None)),None)
                        mismatches.append({'slot':a['slot'],'reference_slot':different[0]['slot'],'first_divergence':first,'reference_id':left[first] if first is not None and first<len(left) else None,'candidate_id':right[first] if first is not None and first<len(right) else None,'reference_length':len(left),'candidate_length':len(right),'reference_stop':ref.get('stop_type'),'candidate_stop':r.get('stop_type')})
                for session in range(2):
                    rows=[by_key.get((session,rnd,tid,name)) for rnd in range(4)];times=[a['wall_ms'] for a in rows if a is not None];value=statistics.median(times) if len(times)==4 else None;costs[(session,tid,name)]=value
                    taskcosts.append({'family':family,'session':session,'task':tid,'condition':name,'completed':len(times),'planned':4,'resident_median_ms':value,'diagnostic_available_median_ms':statistics.median(times) if times else None,'min_ms':min(times) if times else None,'max_ms':max(times) if times else None})
            valid=stable_R and completed==192 and stable and not invalid and not mismatches
            qual[name]={'status':'COMPLETE_QUALIFIED' if valid else ('INCOMPLETE' if completed<192 else 'COMPLETE_CONTRACT_MISMATCH'),'qualified':bool(valid),'planned':192,'completed':completed,'repeat_stable':bool(stable),'invalid_contract_slots':invalid,'mismatch_count':len(mismatches),'mismatches':mismatches}
        comparisons=[]
        pairs=[('M3','C3_K3'),('R','C3_K3'),('R','M3'),('R','N'),('M3','N')]+[(base,cand) for cand in ['C3_K1','C3_K2'] for base in ['R','M3']]
        for base,cand in pairs:
            effects=[];domains={d:[] for d in ['MBPP','GSM8K']};task_effects=collections.defaultdict(list)
            for session in range(2):
                logs=[];ds={d:[] for d in domains}
                for task in inputs['tasks']:
                    tid=task['id'];l=costs[(session,tid,base)];r=costs[(session,tid,cand)]
                    if l is None or r is None:continue
                    v=math.log(l/r);logs.append(v);ds[task['domain']].append(v);task_effects[tid].append(v)
                effects.append(statistics.mean(logs) if len(logs)==24 else None)
                for d in domains:domains[d].append(statistics.mean(ds[d]) if len(ds[d])==12 else None)
            gm=math.exp(statistics.mean(effects)) if all(z is not None for z in effects) else None
            allowed=stable_R and qual['R']['qualified'] and qual[base]['qualified'] and qual[cand]['qualified']
            comparisons.append({'comparison':base+'/'+cand,'qualified_ratio':gm if allowed else None,'diagnostic_complete_cost_ratio':gm,'session_effect_log':effects,'session_ratios':[math.exp(z) if z is not None else None for z in effects],'domain_qualified_ratios':{d:math.exp(statistics.mean(z)) if allowed and all(v is not None for v in z) else None for d,z in domains.items()},'domain_diagnostic_ratios':{d:math.exp(statistics.mean(z)) if all(v is not None for v in z) else None for d,z in domains.items()},'task_ratios':{t:math.exp(statistics.mean(v)) if len(v)==2 else None for t,v in task_effects.items()},'regressions':[t for t,v in task_effects.items() if len(v)==2 and statistics.mean(v)<0],'six_date_95pct_CI':None,'Bonferroni_date_CI':None,'cross_date_positive_decision':'UNTESTED','primary':family=='Llama' and base=='M3' and cand=='C3_K3'})
        distributions={}
        for c in plan['conditions']:
            name=c['name'];rows=[r for r in cases if r['family']==family and r['condition']==name];lengths=[r['length'] for r in rows]
            proposed=sum(r['native_counts'].get('draft_n',0) for r in rows);accepted=sum(r['native_counts'].get('draft_n_accepted',0) for r in rows)
            distributions[name]={'stop_types':dict(collections.Counter(r['stop_type'] for r in rows)),'length_min':min(lengths) if lengths else None,'length_median':statistics.median(lengths) if lengths else None,'length_max':max(lengths) if lengths else None,'suffix_cases':sum(bool(r['suffix_ids']) for r in rows),'total_suffix_IDs':sum(len(r['suffix_ids']) for r in rows),'native_proposed_draft_IDs':proposed,'native_accepted_draft_IDs':accepted,'native_acceptance_fraction':accepted/proposed if proposed else None}
        result[family]={'stable_complete_R':bool(stable_R),'qualification':qual,'comparisons':comparisons,'native_distributions':distributions}
    return {'study_id':'JSA_THIRD_FAMILY_V1','planned':3456,'completed':len(records),'slot_statuses':dict(collections.Counter(r['status'] for r in ledger.values())),'families':result,'ledger':ledger,'task_costs':taskcosts,'native_case_diagnostics':cases,'timer':'resident client HTTP submit through JSON parse perf_counter','aggregation':'median 4 absolute request costs per task/condition/session; mean24 task log ratios per session; average2session effects','dates_in_records':sorted({a['utc'][:10] for a in records.values()}),'dates_in_Asia_Shanghai':sorted({datetime.fromisoformat(a['utc']).astimezone(timezone(timedelta(hours=8))).date().isoformat() for a in records.values()}),'generation_cost_ratios':None,'intervals':'all date intervals and cross-date positive decisions untested under pre-forward fast amendment','freeze_commit':freeze['frozen_sha']}
if __name__=='__main__':
    import sys
    result=analyse();out=Path(sys.argv[1]) if len(sys.argv)>1 else PUB/'RESULTS.json';save(out,result)
    print(json.dumps({'planned':result['planned'],'completed':result['completed'],'statuses':result['slot_statuses']}),flush=True)
