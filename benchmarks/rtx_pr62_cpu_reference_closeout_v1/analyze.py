"""Independent CPU parser/cost analysis. Reads old records; no runner imports or model calls."""
import argparse, csv, hashlib, json, math, platform, random, statistics, sys
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

CONDITIONS=['scalar_reference','matched_target','target_scopes','all_scopes']
PAIRS=[('scalar_reference','target_scopes'),('matched_target','target_scopes'),('scalar_reference','matched_target'),('scalar_reference','all_scopes'),('matched_target','all_scopes'),('all_scopes','target_scopes')]
EOG={128247,151643,151645,151662,151663,151664}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    p=Path(p);q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n');q.replace(p)
def csvwrite(p,rows):
    with Path(p).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def gm(xs):return math.exp(math.fsum(math.log(x) for x in xs)/len(xs))
def sig(r):return r['response']['tokens'],r['endpoint']
def cost(r,timer):return r['response']['timings']['predicted_ms'] if timer=='generation' else r['wall_ms']
def validate(records,plan,inputs):
    expected={(t,c,k) for t in plan['tasks'] for c in CONDITIONS for k in range(1,5)}
    keyed={};qual=[]
    for r in records:
        key=(r['task'],r['condition'],r['repetition']);assert key not in keyed,'duplicate key';assert key in expected,'unexpected key';keyed[key]=r
        z=r['response'];ids=z['tokens'];assert ids and all(type(i)==int for i in ids);assert len(ids)==z['tokens_predicted'] and len(ids)<=128
        assert r['requested_cap']==128 and r['endpoint']==('EOS' if z['stop_type']=='eos' else 'limit') and z['stop_type'] in ['eos','limit']
        assert (ids[-1] in EOG)==(r['endpoint']=='EOS') and not any(i in EOG for i in ids[:-1]);assert len(ids)==128 or r['endpoint']=='EOS'
        # tokens_cached is final slot.prompt.n_tokens(), not reused-prompt cache hits.
        assert not z['truncated'] and z['timings']['cache_n']==0
        assert type(z['tokens_cached'])==int and z['tokens_cached']>=0
        inp=inputs[r['task']];assert z['prompt']==inp['formatted_prompt'];assert r['formatted_prompt_sha256']==inp['formatted_prompt_sha256']==hashlib.sha256(z['prompt'].encode()).hexdigest()
        assert z['timings']['prompt_n']==inp['prompt_token_count']==len(inp['prompt_ids'])
        settings=z['generation_settings'];assert settings['seed']==123 and settings['temperature']==0 and settings['top_k']==0 and settings['top_p']==1 and settings['min_p']==0 and settings['n_predict']==128 and not settings['stream'] and not settings['ignore_eos']
        condition=next(c for c in plan['conditions'] if c['name']==r['condition']);assert all(r[p]==condition[p] for p in ['mask','spec','ub','k'])
        assert r['source_commit']=='7b8c6fbecde9d173fb9f9e1cac390f58fd4fca24';assert r['server_sha256']=='f340f3be88fa7e99ccd8f34a92e9237e27c6009a1cb88a646e1a29efcb652416'
        for timer in ['generation','whole']:
            x=cost(r,timer);assert type(x) in [int,float] and math.isfinite(x) and x>0,'invalid cost/unit'
    assert set(keyed)==expected,'missing denominator'
    for task in plan['tasks']:
        ref=keyed[task,'scalar_reference',1];stable=all(sig(keyed[task,'scalar_reference',k])==sig(ref) for k in range(1,5));assert stable,'unstable reference'
        for c in CONDITIONS:
            for k in range(1,5):
                r=keyed[task,c,k];equal=sig(r)==sig(ref)
                qual.append({'task':task,'condition':c,'repetition':k,'reference_stable':stable,'full_array_equal':r['response']['tokens']==ref['response']['tokens'],'endpoint_equal':r['endpoint']==ref['endpoint'],'qualified':equal,'tokens':len(r['response']['tokens']),'endpoint':r['endpoint'],'last_id':r['response']['tokens'][-1],'tokens_sha256':hashlib.sha256(json.dumps(r['response']['tokens'],separators=(',',':')).encode()).hexdigest()})
    return keyed,qual
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--experiment',required=True);ap.add_argument('--output',default=str(Path(__file__).parent));a=ap.parse_args();root=Path(a.experiment);out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    plan=load(root/'B_MANIFEST.json');rows=load(root/'runs/b/RECORDS.json');inputs={r['id']:r for r in load(root/'B_INPUTS.json')}
    assert sha(root/'runs/b/RECORDS.json')=='a6e562625f229fd38eed31a9492bb04db269f78355391ab41cf31c6d2dce6bd4'
    keyed,qual=validate(rows,plan,inputs);csvwrite(out/'QUALIFICATION_RECOMPUTED.csv',qual)
    expected_order=[];sessions=[]
    for rep in range(1,5):
        order=CONDITIONS[rep-1:]+CONDITIONS[:rep-1];tasks=plan['tasks'][rep-1:]+plan['tasks'][:rep-1]
        for c in order:
            d=root/'runs/b'/f'r{rep}-{c}';cmd=load(d/'COMMAND.json');warm=load(d/'WARMUP.json');proc=load(d/'PROCESS.json');cond=next(v for v in plan['conditions'] if v['name']==c)
            assert cmd['mask']==cond['mask'] and cmd['spec']==cond['spec'] and not cmd['capture'];assert cmd['server_sha256']==keyed[tasks[0],c,rep]['server_sha256']
            opts=cmd['command'];assert opts[opts.index('--ubatch-size')+1]==str(cond['ub']);assert opts[opts.index('--ctx-size')+1]=='4096' and opts[opts.index('--threads')+1]=='24' and opts[opts.index('--flash-attn')+1]=='off';assert '--no-cache-prompt' in opts and '--no-warmup' in opts
            assert ('--model-draft' in opts)==cond['spec'];assert warm['prompt'] not in {x['formatted_prompt'] for x in inputs.values()} and warm['generation_settings']['n_predict']==32
            sessions.append({'session':d.name,'condition':c,'repetition':rep,'warmup_excluded':True,'warmup_sha256':sha(d/'WARMUP.json'),'command_sha256':sha(d/'COMMAND.json'),'process_sha256':sha(d/'PROCESS.json'),'server_sha256':cmd['server_sha256'],'utc':proc['utc']})
            for t in tasks:expected_order.append((t,c,rep))
    assert [(r['task'],r['condition'],r['repetition']) for r in rows]==expected_order
    raw=[]
    for r in rows:
        p=root/r['record_relative_path'];assert load(p)==r,'record aggregate/file mismatch';z=r['response'];q=next(x for x in qual if (x['task'],x['condition'],x['repetition'])==(r['task'],r['condition'],r['repetition']))
        raw.append({'task':r['task'],'condition':r['condition'],'repetition':r['repetition'],'session':f"r{r['repetition']}-{r['condition']}",'generation_ms':cost(r,'generation'),'whole_ms':cost(r,'whole'),'timer_unit':'ms','qualified':q['qualified'],'tokens':len(z['tokens']),'endpoint':r['endpoint'],'raw_record_sha256':sha(p),'prompt_sha256':r['formatted_prompt_sha256'],'source_commit':r['source_commit'],'server_sha256':r['server_sha256']})
    csvwrite(out/'RAW_COSTS.csv',raw);save(out/'SESSION_BINDINGS.json',sessions)
    taskpairs=[];roundpairs=[];summary=[];medians=[]
    rng=np.random.Generator(np.random.PCG64(20261008));draws=rng.integers(0,24,size=(10000,24))
    for timer in ['generation','whole']:
        ms={(t,c):statistics.median(cost(keyed[t,c,k],timer) for k in range(1,5)) for t in plan['tasks'] for c in CONDITIONS}
        for (t,c),v in ms.items():medians.append({'task':t,'condition':c,'timer':timer,'median_ms':v,'repeats':4})
        for idx,(base,cand) in enumerate(PAIRS):
            pairqual=all(q['qualified'] for q in qual if q['condition'] in [base,cand]);ratios=[ms[t,base]/ms[t,cand] for t in plan['tasks']]
            for t,v in zip(plan['tasks'],ratios):taskpairs.append({'task':t,'baseline':base,'candidate':cand,'primary':idx<3,'timer':timer,'baseline_median_ms':ms[t,base],'candidate_median_ms':ms[t,cand],'speedup_baseline_over_candidate':v,'qualified':pairqual})
            rounds=[]
            for k in range(1,5):
                vals=[]
                for t in plan['tasks']:
                    b=cost(keyed[t,base,k],timer);c=cost(keyed[t,cand,k],timer);vals.append(b/c)
                    roundpairs.append({'task':t,'baseline':base,'candidate':cand,'timer':timer,'repetition':k,'baseline_ms':b,'candidate_ms':c,'speedup_baseline_over_candidate':b/c,'qualified':pairqual})
                rounds.append({'repetition':k,'gm':gm(vals),'faster_tasks':sum(v>1 for v in vals),'slower_tasks':sum(v<1 for v in vals),'direction':'faster' if gm(vals)>1 else 'slower' if gm(vals)<1 else 'tie'})
            samples=np.exp(np.mean(np.log(np.asarray(ratios))[draws],axis=1));ci=np.quantile(samples,[.025,.975],method='linear').tolist()
            oldrng=random.Random(20261005);oldboot=sorted(gm(oldrng.choices(ratios,k=24)) for _ in range(4000))
            summary.append({'baseline':base,'candidate':cand,'primary':idx<3,'timer':timer,'task_count':24,'repeats_per_condition':4,'qualified':pairqual,'task_median_gm':gm(ratios) if pairqual else None,'descriptive_task_bootstrap_95_linear':ci if pairqual else None,'historical_interval_replication':[oldboot[99],oldboot[3899]] if pairqual else None,'faster_tasks':sum(v>1 for v in ratios),'slower_tasks':sum(v<1 for v in ratios),'tied_tasks':sum(v==1 for v in ratios),'rounds':rounds,'absolute_task_medians_median_baseline_ms':statistics.median(ms[t,base] for t in plan['tasks']),'absolute_task_medians_median_candidate_ms':statistics.median(ms[t,cand] for t in plan['tasks'])})
        for t in plan['tasks']:
            x=ms[t,'scalar_reference']/ms[t,'matched_target'];y=ms[t,'matched_target']/ms[t,'target_scopes'];z=ms[t,'scalar_reference']/ms[t,'target_scopes'];assert math.isclose(x*y,z,rel_tol=1e-12)
        ss=[x for x in summary if x['timer']==timer];get=lambda b,c:next(x for x in ss if x['baseline']==b and x['candidate']==c)['task_median_gm'];assert math.isclose(get('scalar_reference','matched_target')*get('matched_target','target_scopes'),get('scalar_reference','target_scopes'),rel_tol=1e-12)
    csvwrite(out/'TASK_COST_PAIRS.csv',taskpairs);csvwrite(out/'ROUND_COST_PAIRS.csv',roundpairs);csvwrite(out/'CONDITION_TASK_MEDIANS.csv',medians)
    old=load(root/'generated/B_RESULTS.json');anchor=[]
    for oldc in old['costs']:
        for timer,key in [('generation','generation'),('whole','wall')]:
            new=next(x for x in summary if x['timer']==timer and x['baseline']==oldc['denominator'] and x['candidate']==oldc['numerator']);v=oldc[key]
            assert math.isclose(new['task_median_gm'],v['task_median_geomean_speedup'],rel_tol=1e-12)
            assert all(math.isclose(x['gm'],y,rel_tol=1e-12) for x,y in zip(new['rounds'],v['repeat_geomeans']))
            assert all(math.isclose(x,y,rel_tol=1e-12) for x,y in zip(new['historical_interval_replication'],v['task_bootstrap_descriptive_95']))
            anchor.append({'baseline':new['baseline'],'candidate':new['candidate'],'timer':timer,'point_rounds_old_interval_match':True})
    save(out/'COST_SUMMARY.json',{'ratio_direction':'baseline_ms/candidate_ms; >1 candidate faster','aggregation':'median absolute costs within task/condition then ratio then unweighted task GM','comparisons':summary,'identity_checks':'all 48 per-task identities and two GM identities PASS','old_results_replication':anchor,'bootstrap':{'seed':20261008,'resamples':10000,'algorithm':'numpy Generator PCG64, integers(0,24,size=(10000,24)), common indices','quantile':'Hyndman-Fan type7 / numpy method=linear','unit':'24 tasks; repeats collapsed first; descriptive exposed-panel interval'},'historical_bootstrap':{'seed':20261005,'resamples':4000,'algorithm':'random.Random.choices, same frozen task order; sorted indices99/3899'},'software':{'python':platform.python_version(),'numpy':np.__version__},'new_model_requests':0})
    endpoints=[q for q in qual if q['condition']=='scalar_reference' and q['repetition']==1]
    save(out/'COUNTS.json',{'formal_expected':384,'formal_found':len(rows),'unique_formal_keys':len(keyed),'warmups_found_and_excluded':len(sessions),'sessions':16,'tasks':24,'conditions':4,'repetitions':4,'reference_stable_tasks':24,'qualified_by_condition':{c:sum(q['qualified'] for q in qual if q['condition']==c) for c in CONDITIONS},'reference_lengths_min_max':[min(q['tokens'] for q in endpoints),max(q['tokens'] for q in endpoints)],'reference_eos_tasks':sum(q['endpoint']=='EOS' for q in endpoints),'reference_limit_tasks':sum(q['endpoint']=='limit' for q in endpoints),'bridge_b_included':False,'new_model_requests':0,'new_target_draft_forwards':0,'new_warmups':0,'additional_full_stream_or_suffix_in_selected_B_records':False,'raw_array_contract':'response.tokens inclusive runtime EOG/cap, no recropping; no proof of any unrecorded internal sample stream'})
    with (out/'LEDGER.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'stage':'data_qualification_and_cost','status':'PASS','utc':datetime.now(timezone.utc).isoformat(),'model_work':0})+'\n')
    save(out/'STATUS.json',{'stage':'cost','status':'PASS','new_model_requests':0,'new_target_draft_forwards':0,'new_warmups':0})
    print(json.dumps([{'baseline':x['baseline'],'candidate':x['candidate'],'timer':x['timer'],'gm':x['task_median_gm'],'ci':x['descriptive_task_bootstrap_95_linear'],'rounds':[r['gm'] for r in x['rounds']],'faster_tasks':x['faster_tasks']} for x in summary if x['primary']],indent=2))
if __name__=='__main__':main()
