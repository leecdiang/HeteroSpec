"""Independent CPU verification and paired descriptive bootstrap from paid rows."""
import json,hashlib,os,math,statistics,csv
from pathlib import Path
import numpy as np
REPO=Path(__file__).resolve().parents[3];PUB=REPO/'benchmarks/jsa_rtx_validation_v1';LOCAL=Path(os.environ.get('JSA_LOCAL_ROOT',str(REPO.parent/'jsa')))
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def csv_write(p,rows):
    with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def main(model):
    plan=read(PUB/(model+'_F0.json'));ledger=read(LOCAL/(model+'_SLOTS.json'));tasks={t['id']:t for t in read(PUB/plan['input_file'])};expected=[s for b in plan['blocks'] for s in b['slots']];assert len(expected)==len(set(expected))==plan['formal_requests'] and set(ledger)==set(expected)
    eog=set(read(PUB/'MODEL_CHOICE.json')['eog' if model=='SmolLM2' else 'Qwen_eog']);records={};contract={}
    for slot,l in ledger.items():
        if l['status']!='COMPLETED':continue
        p=LOCAL/l['record'];assert h(p)==l['record_sha256'];a=read(p);assert a['slot']==slot;t=tasks[a['task']];r=a['response'];ids=r['tokens']
        assert h(PUB/plan['input_file'])==plan['input_sha256'];assert hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()==a['tokens_digest']
        valid=0<len(ids)<=t['cap'] and all(type(x) is int for x in ids) and len(ids)==r['tokens_predicted'] and not any(x in eog for x in ids[:-1]) and ((ids[-1] in eog)==(r['stop_type']=='eos')) and (len(ids)==t['cap'] or r['stop_type']=='eos') and not r['truncated'] and r['timings']['cache_n']==0 and r['prompt']==t['formatted_prompt'] and r['timings']['prompt_n']==t['prompt_token_count'] and math.isfinite(a['wall_ms']) and a['wall_ms']>0
        if a['condition']['name']=='E32':valid &= r['request_reset'] and all(b['actual_queries']==32 and b['retained_kv_owner']=='verifier' for b in r['blocks']) and len(r['blocks'])==r['verify_decode_calls']
        key=(a['round'],a['task'],a['condition']['name']);assert key not in records;records[key]=a;contract[slot]=bool(valid)
    conditions=[c['name'] for c in plan['conditions']];n=plan['rounds'];complete=len(records)==plan['formal_requests'];stable_R=True;qual={};taskrows=[]
    for tid in tasks:
        refs=[records.get((rnd,tid,'R')) for rnd in range(1,n+1)];stable_R &= all(a is not None for a in refs) and all(a['response']['tokens']==refs[0]['response']['tokens'] and a['response']['stop_type']==refs[0]['response']['stop_type'] for a in refs if a is not None)
    for c in conditions:
        count=0;failed=[];stable=True;valid=True
        for tid,t in tasks.items():
            rows=[records.get((rnd,tid,c)) for rnd in range(1,n+1)];existing=[a for a in rows if a is not None];stable &= len(existing)==n and all(a['response']['tokens']==existing[0]['response']['tokens'] and a['response']['stop_type']==existing[0]['response']['stop_type'] for a in existing)
            for rnd,a in enumerate(rows,1):
                if a is None:continue
                count+=1;valid &= contract[a['slot']];ref=records.get((rnd,tid,'R'));left=ref['response']['tokens'] if ref else [];right=a['response']['tokens']
                if ref is None or left!=right or ref['response']['stop_type']!=a['response']['stop_type']:
                    i=next((i for i in range(max(len(left),len(right))) if (left[i] if i<len(left) else None)!=(right[i] if i<len(right) else None)),None)
                    failed.append({'round':rnd,'task':tid,'first_divergence_zero_based':i,'reference_id':left[i] if i is not None and i<len(left) else None,'candidate_id':right[i] if i is not None and i<len(right) else None,'reference_length':len(left),'candidate_length':len(right),'reference_stop':ref['response']['stop_type'] if ref else None,'candidate_stop':a['response']['stop_type']})
            times=[a['wall_ms'] for a in existing];gen=[a['response']['timings'].get('predicted_ms') for a in existing]
            taskrows.append({'task':tid,'condition':c,'completed':len(existing),'planned':n,'request_median_ms':statistics.median(times) if times else None,'predicted_median_ms':statistics.median(gen) if gen and all(x is not None for x in gen) else None,'request_min_ms':min(times) if times else None,'request_max_ms':max(times) if times else None})
        qualified=complete and stable_R and count==24*n and valid and not failed
        qual[c]={'qualified':qualified,'repeat_stable':bool(stable),'completed':count,'full_contract_valid':bool(valid),'mismatch_count':len(failed),'mismatches':failed,'status':'COMPLETE_QUALIFIED' if qualified else ('COMPLETE_CONTRACT_MISMATCH' if complete and stable and failed else ('COMPLETE_NEGATIVE' if complete else 'INCOMPLETE'))}
    comparisons=[('R','C3'),('M3','C3'),('R','M3')]
    if 'E32' in conditions:comparisons += [('R','E32'),('E32','C3')]
    if 'Csel' in conditions:comparisons += [('R','Csel'),('Msel','Csel'),('R','Msel')]
    costs={(a['task'],a['condition']):a['request_median_ms'] for a in taskrows};ratios=[];rng=np.random.Generator(np.random.PCG64(20261010));indices=rng.integers(0,24,size=(10000,24))
    for base,cand in comparisons:
        allowed=qual[base]['qualified'] and qual[cand]['qualified']
        if base=='E32' and cand=='C3':allowed &= qual['M3']['qualified']
        values=[math.log(costs[(t,base)]/costs[(t,cand)]) for t in tasks if costs[(t,base)] is not None and costs[(t,cand)] is not None];gm=math.exp(statistics.mean(values)) if len(values)==24 else None
        bounds=np.quantile(np.exp(np.array(values)[indices].mean(axis=1)),[.025,.975],method='linear').tolist() if len(values)==24 else None
        ratios.append({'comparison':base+'/'+cand,'qualified_ratio':gm if allowed else None,'qualified_descriptive_95pct_task_bootstrap':bounds if allowed else None,'diagnostic_ratio':gm,'task_regressions':sum(x<0 for x in values),'generation_comparison':None,'all_24_tasks_and_rounds_required':True})
    result={'model':model,'status':'COMPLETE' if complete else 'INCOMPLETE','planned':plan['formal_requests'],'completed':len(records),'warmups':len(list((LOCAL/'runs'/('confirmation_'+model)).glob('*/WARMUP.json'))),'stable_R':bool(stable_R),'qualification':qual,'comparisons':ratios,'contract_checks':contract,'slot_statuses':{s:sum(a['status']==s for a in ledger.values()) for s in sorted(set(a['status'] for a in ledger.values()))},'shared_F_E_exact_run_root':'runs/confirmation_'+model if model=='SmolLM2' else None,'bootstrap':'10000 task rows paired across conditions; PCG64 seed20261010;NumPy linear/type7;descriptive only','raw_ledger_sha256':h(LOCAL/(model+'_SLOTS.json')),'freeze_sha':read(LOCAL/(model+'_REMOTE_RECEIPT.json'))['frozen_sha']}
    write(PUB/(model+'_QUALIFICATION.json'),result);csv_write(PUB/(model+'_TASKS.csv'),taskrows);print(json.dumps({k:result[k] for k in ['model','status','completed','warmups','stable_R','comparisons']}),flush=True)
if __name__=='__main__':
    import sys
    main(sys.argv[1])
