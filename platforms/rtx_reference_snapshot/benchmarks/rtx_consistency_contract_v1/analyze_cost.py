"""Complete output gates and matched task-median resident costs."""
import csv,hashlib,json,math,statistics
from pathlib import Path
from run import HERE,read,save,sha

def analyze(panel,expected_conditions,expected_count):
    root=HERE/'runs'/panel;manifest=read(root/'MANIFEST.json');records=read(root/'RECORDS.json')
    inputs=read(HERE/'COST_INPUTS.json');expected={x['id']:x for x in inputs};rows=[];seen=set()
    reps=manifest.get('repetitions',3)
    assert len(records)==expected_count
    for r in records:
        key=(r['task'],r['condition'],r['repetition']);assert key not in seen;seen.add(key)
        assert r['source_commit']==manifest['source_commit']
        t=expected[r['task']];response=r['response'];ids=response['tokens']
        assert ids and len(ids)==response['tokens_predicted'] and len(ids)<=128 and response['timings']['cache_n']==0
        assert r['formatted_prompt_sha256']==hashlib.sha256(t['formatted_prompt'].encode()).hexdigest()
        assert response['prompt']==t['formatted_prompt']
        end='EOS' if response['stop_type']=='eos' else 'limit';assert response['stop_type'] in ['eos','limit']
        assert len(ids)==128 or end=='EOS'
        eog={128247,151643,151645,151662,151663,151664};assert not any(x in eog for x in ids[:-1])
        assert (ids[-1] in eog)==(end=='EOS')
        equal=ids==t['original_reference_ids'] and end==t['original_endpoint'];assert equal==r['original_reference_equal']
        if r['condition']=='target':assert equal
        diff=next((i for i,(a,b) in enumerate(zip(ids,t['original_reference_ids'])) if a!=b),None)
        if diff is None and len(ids)!=len(t['original_reference_ids']):diff=min(len(ids),len(t['original_reference_ids']))
        rows.append({'task':r['task'],'condition':r['condition'],'repetition':r['repetition'],'reference_equal':equal,
                     'first_difference':diff,'length':len(ids),'endpoint':end,'wall_ms':r['wall_ms'],
                     'generation_ms':response['timings']['predicted_ms'],'prompt_ms':response['timings']['prompt_ms'],
                     'drafted':response['timings'].get('draft_n',0),'accepted':response['timings'].get('draft_n_accepted',0)})
    assert seen=={(t,c,r) for t in expected for c in expected_conditions for r in range(1,reps+1)}
    paired=[];summary=[]
    for condition in expected_conditions:
        cr=[x for x in rows if x['condition']==condition]
        stable=all(len({tuple(r['response']['tokens']) for r in records if r['task']==t and r['condition']==condition})==1 for t in expected)
        gm_wall=[];gm_gen=[];faster_wall=0;faster_gen=0
        for task in expected:
            rr=[x for x in cr if x['task']==task];tr=[x for x in rows if x['task']==task and x['condition']=='target']
            tw=statistics.median(x['wall_ms'] for x in tr);cw=statistics.median(x['wall_ms'] for x in rr)
            tg=statistics.median(x['generation_ms'] for x in tr);cg=statistics.median(x['generation_ms'] for x in rr)
            sw=tw/cw;sg=tg/cg;gm_wall.append(sw);gm_gen.append(sg);faster_wall+=sw>1;faster_gen+=sg>1
            paired.append({'panel':panel,'task':task,'condition':condition,'all_repetitions_reference_equal':all(x['reference_equal'] for x in rr),
                           'target_wall_median_ms':tw,'candidate_wall_median_ms':cw,'wall_speedup':sw,
                           'target_generation_median_ms':tg,'candidate_generation_median_ms':cg,'generation_speedup':sg})
        qualifies=all(x['reference_equal'] for x in cr)
        summary.append({'panel':panel,'condition':condition,'matches':sum(x['reference_equal'] for x in cr),'pairs':len(cr),
                        'repeat_stable':stable,'qualifies_whole_panel':qualifies,'wall_speedup_gm':math.exp(sum(map(math.log,gm_wall))/len(gm_wall)),
                        'generation_speedup_gm':math.exp(sum(map(math.log,gm_gen))/len(gm_gen)),
                        'faster_wall_tasks':faster_wall,'faster_generation_tasks':faster_gen,
                        'qualified_wall_speedup_gm':math.exp(sum(map(math.log,gm_wall))/len(gm_wall)) if qualifies else None,
                        'qualified_generation_speedup_gm':math.exp(sum(map(math.log,gm_gen))/len(gm_gen)) if qualifies else None})
    out=HERE/'generated/analysis'
    for name,data in [('REQUESTS',rows),('PAIRED',paired),('SUMMARY',summary)]:
        with (out/f'{panel}_{name}.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=data[0].keys());w.writeheader();w.writerows(data)
    save(out/(panel+'_VALIDATION.json'),{'status':'PASS','requests':len(records),'task_count':19,'conditions':expected_conditions,
        'warmups':len(list(root.glob('*_WARMUP.json'))),'repetitions':reps,'source_commit':manifest['source_commit'],
        'record_file_sha256':sha(root/'RECORDS.json'),'summary':summary})
    print(json.dumps(summary),flush=True)
    return summary

if __name__=='__main__':
    import sys
    if sys.argv[1]=='k2':analyze('cost-v2',['target','serialized','attention'],171)
    elif sys.argv[1]=='k3':
        conditions=read(HERE/'runs/cost-wide/MANIFEST.json')['conditions']
        manifest=read(HERE/'runs/cost-wide/MANIFEST.json')
        analyze('cost-wide',conditions,19*manifest['repetitions']*len(conditions))
    elif sys.argv[1]=='matched':analyze('cost-matched',['target','query_batch_k3'],152)
