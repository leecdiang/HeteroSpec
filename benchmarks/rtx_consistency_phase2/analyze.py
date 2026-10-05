"""Full-output gates, deterministic selection and matched cost summaries."""
import csv,math,random,statistics,sys
from base import HERE,read,save,sha

def gm(x):return math.exp(statistics.mean(math.log(v) for v in x))
def main(stage):
    root=HERE/'runs'/stage;manifest=read(root/'MANIFEST.json');rr=read(root/'RECORDS.json');config=read(HERE/'CONFIG.json')
    assert len(rr)==manifest['request_cap'];tasks=manifest['tasks'];conditions=manifest['conditions'];reps=manifest['repetitions']
    assert len({(r['task'],r['condition'],r['repetition']) for r in rr})==len(rr)
    assert {(r['task'],r['condition'],r['repetition']) for r in rr}=={(t,c['name'],n) for t in tasks for c in conditions for n in range(1,reps+1)}
    for r in rr:
        assert r['source_commit']==manifest['source_commit'] and r['response']['timings']['cache_n']==0
        p=root/f'r{r["repetition"]}-{r["condition"]}'/(r['task'].replace('/','-')+'.json');assert read(p)==r
    summary=[]
    for c in conditions:
        cr=[r for r in rr if r['condition']==c['name']]
        stable=all(len({(tuple(r['response']['tokens']),r['endpoint']) for r in cr if r['task']==t})==1 for t in tasks)
        assert stable
        summary.append({**c,'reference_matches':sum(r['original_reference_equal'] for r in cr),'requests':len(cr),
            'qualifies':all(r['original_reference_equal'] for r in cr),'repeat_stable':stable,
            'task_matches':{t:all(r['original_reference_equal'] for r in cr if r['task']==t) for t in tasks}})
    result={'status':'COMPLETE','stage':stage,'requests':len(rr),'conditions':summary,'source_commit':manifest['source_commit'],
            'record_sha256':sha(root/'RECORDS.json'),'warmups':len(list(root.glob('*/WARMUP.json')))}
    out=HERE/'generated/analysis';out.mkdir(exist_ok=True)
    if stage=='a1':
        passing=[r['mask'] for r in summary if r['qualifies']];assert 15 in passing
        frontier=[m for m in passing if not any(p!=m and (p&m)==p for p in passing)]
        frontier.sort(key=lambda m:(m.bit_count(),m));selected=frontier[:config['max_a2_frontier_masks']]
        masks=sorted(set([15]+selected));controls=sorted({m&3 for m in masks})
        selection={'gate':'PASS','source_analysis_sha256':sha(root/'RECORDS.json'),'sentinel_passing_masks':passing,
            'sentinel_inclusion_minimal_frontier':frontier,'not_selected_frontier_masks':frontier[len(selected):],
            'selection_rule':config['selection_rule'],'repetitions':2,
            'conditions':[{'name':f'target{m}','mask':m,'spec':False} for m in controls]+[{'name':f'mask{m}','mask':m,'spec':True} for m in masks]}
        save(HERE/'A2_SELECTION.json',selection);result['passing_masks']=passing;result['finite_sentinel_frontier']=frontier
    elif stage=='a2':
        qualified={r['name'] for r in summary if r['qualifies']};assert 'mask15' in qualified and 'target3' in qualified
        eligible=[r['mask'] for r in summary if r['spec'] and r['mask']!=15 and r['qualifies'] and f'target{r["mask"]&3}' in qualified]
        eligible.sort(key=lambda m:(m.bit_count(),m))
        if eligible:
            winner=eligible[0];controls=sorted({3,winner&3})
            cs=[{'name':f'target{m}','mask':m,'spec':False} for m in controls]+[
                {'name':'mask15','mask':15,'spec':True},{'name':f'mask{winner}','mask':winner,'spec':True}]
            selection={'gate':'PASS','winner_mask':winner,'eligible_masks':eligible,'selection_rule':config['selection_rule'],
                       'conditions':cs,'repetitions':config['a3_repetitions_by_condition_count'][str(len(cs))],
                       'source_analysis_sha256':sha(root/'RECORDS.json')}
        else:selection={'gate':'NO_NEW_SCOPE','eligible_masks':[],'reason':'No reduced sentinel-frontier recipe and matched target qualified on all19 tasks.'}
        save(HERE/'A3_SELECTION.json',selection);result['cost_gate']=selection
    elif stage=='a3':
        assert all(r['qualifies'] for r in summary);winner=read(HERE/'A3_SELECTION.json')['winner_mask']
        comparisons=[(f'mask{winner}','mask15'),(f'mask{winner}',f'target{winner&3}'),('mask15','target3')]
        costs=[];rng=random.Random(config['bootstrap_seed'])
        for candidate,baseline in comparisons:
            per_task=[]
            for t in tasks:
                cr=[r for r in rr if r['condition']==candidate and r['task']==t];br=[r for r in rr if r['condition']==baseline and r['task']==t]
                w=statistics.median(r['wall_ms'] for r in br)/statistics.median(r['wall_ms'] for r in cr)
                g=statistics.median(r['response']['timings']['predicted_ms'] for r in br)/statistics.median(r['response']['timings']['predicted_ms'] for r in cr)
                per_task.append({'candidate':candidate,'baseline':baseline,'task':t,'request_speedup':w,'generation_speedup':g})
            repeat=[]
            for rep in range(1,reps+1):
                ratios=[]
                for t in tasks:
                    a=next(r for r in rr if r['condition']==candidate and r['task']==t and r['repetition']==rep)
                    b=next(r for r in rr if r['condition']==baseline and r['task']==t and r['repetition']==rep)
                    ratios.append(b['response']['timings']['predicted_ms']/a['response']['timings']['predicted_ms'])
                repeat.append(gm(ratios))
            draws=sorted(gm([rng.choice(per_task)['generation_speedup'] for _ in tasks]) for _ in range(config['bootstrap_samples']))
            costs.append({'candidate':candidate,'baseline':baseline,'request_speedup_gm':gm([r['request_speedup'] for r in per_task]),
                'generation_speedup_gm':gm([r['generation_speedup'] for r in per_task]),'repeat_generation_speedups':repeat,
                'faster_request_tasks':sum(r['request_speedup']>1 for r in per_task),'faster_generation_tasks':sum(r['generation_speedup']>1 for r in per_task),
                'descriptive_task_bootstrap_95pct':[draws[int(.025*len(draws))],draws[int(.975*len(draws))]],
                'interval_scope':'Descriptive resampling of this exposed19-task panel, not a population-transfer inference.',
                'per_task':per_task})
        primary=costs[0];needed=4 if reps==6 else 6
        result['costs']=costs;result['scope_efficiency_advance']=(primary['generation_speedup_gm']>=1.03 and primary['request_speedup_gm']>=1 and sum(x>1 for x in primary['repeat_generation_speedups'])>=needed)
        with (out/'a3_TASK_COSTS.csv').open('w',encoding='utf-8',newline='') as f:
            flat=[r for c in costs for r in c['per_task']];w=csv.DictWriter(f,fieldnames=flat[0]);w.writeheader();w.writerows(flat)
    save(out/(stage.upper()+'_RESULTS.json'),result)
    with (out/(stage.upper()+'_OUTPUT_GATE.csv')).open('w',encoding='utf-8',newline='') as f:
        rows=[{k:r[k] for k in ['name','mask','spec','reference_matches','requests','qualifies','repeat_stable']} for r in summary]
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print(__import__('json').dumps({k:v for k,v in result.items() if k not in ['conditions','costs']}),flush=True)

if __name__=='__main__':main(sys.argv[1])
