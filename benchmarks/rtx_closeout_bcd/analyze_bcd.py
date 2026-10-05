"""Frozen full-array gates and descriptive paired costs, with no outcome tuning."""
import math,random,statistics
from close_base import HERE,read,save,sha

def signature(r):return (tuple(r['response']['tokens']),r['endpoint'])
def gm(values):return math.exp(statistics.mean(math.log(v) for v in values))
def cost(r,key):return r['wall_ms'] if key=='wall' else r['response']['timings']['predicted_ms']
def summarize(rows,tasks,numerator,denominator,qualified):
    result={'numerator':numerator,'denominator':denominator,'qualified':qualified}
    for key in ['generation','wall']:
        ratios=[statistics.median(cost(r,key) for r in rows if r['task']==t and r['condition']==denominator)/statistics.median(cost(r,key) for r in rows if r['task']==t and r['condition']==numerator) for t in tasks]
        rng=random.Random(20261005);samples=sorted(gm(rng.choices(ratios,k=len(ratios))) for _ in range(4000))
        reps=sorted({r['repetition'] for r in rows})
        rr=[gm([next(cost(r,key) for r in rows if r['task']==t and r['condition']==denominator and r['repetition']==rep)/next(cost(r,key) for r in rows if r['task']==t and r['condition']==numerator and r['repetition']==rep) for t in tasks]) for rep in reps]
        result[key]={'task_median_geomean_speedup':gm(ratios),'task_ratios':dict(zip(tasks,ratios)),
                     'task_bootstrap_descriptive_95':[samples[99],samples[3899]],'repeat_geomeans':rr,'faster_tasks':sum(x>1 for x in ratios)}
    # Same practical threshold as A; secondary gates never replace full correctness.
    result['practical_decode_gain']=qualified and result['generation']['task_median_geomean_speedup']>=1.03 and result['wall']['task_median_geomean_speedup']>=1 and sum(x>1 for x in result['generation']['repeat_geomeans'])>=math.ceil(len(reps)*2/3)
    return result

def correctness(rows,tasks,conditions,repetitions,anchors=None):
    assert len(rows)==len(tasks)*len(conditions)*repetitions
    refs={};stable=True;details=[];qualified={c:True for c in conditions}
    for t in tasks:
        refrows=[r for r in rows if r['task']==t and r['condition']=='scalar_reference']
        assert len(refrows)==repetitions and len({r['repetition'] for r in refrows})==repetitions
        ref=signature(refrows[0]);s=all(signature(r)==ref for r in refrows)
        if anchors is not None:s=s and ref==anchors[t]
        stable=stable and s;refs[t]=ref
        for c in conditions:
            rs=[r for r in rows if r['task']==t and r['condition']==c]
            assert len(rs)==repetitions and len({r['repetition'] for r in rs})==repetitions
            equal=s and all(signature(r)==ref for r in rs);qualified[c]=qualified[c] and equal
            details.append({'task':t,'condition':c,'reference_stable':s,'full_equal':equal,'reference_tokens':len(ref[0]),'reference_endpoint':ref[1],
                            'observed_token_counts':[len(r['response']['tokens']) for r in rs], 'endpoints':[r['endpoint'] for r in rs],
                            'first_differences':[next((i for i,(a,b) in enumerate(zip(r['response']['tokens'],ref[0])) if a!=b),min(len(r['response']['tokens']),len(ref[0]))) if signature(r)!=ref else None for r in rs]})
    return stable,qualified,details,refs

def b():
    plan=read(HERE/'B_MANIFEST.json');rows=read(HERE/'runs/b/RECORDS.json');tasks=plan['tasks'];names=[c['name'] for c in plan['conditions']]
    stable,q,details,refs=correctness(rows,tasks,names,plan['repetitions'])
    costs=[summarize(rows,tasks,a,z,q[a] and q[z]) for a,z in [('target_scopes','matched_target'),('all_scopes','matched_target'),('target_scopes','all_scopes')]]
    selected='target_scopes' if q['matched_target'] and q['target_scopes'] else ('all_scopes' if q['matched_target'] and q['all_scopes'] else None)
    out={'stage':'B','records_sha256':sha(HERE/'runs/b/RECORDS.json'),'reference_stable':stable,'qualification':q,'details':details,'costs':costs,'selected_condition':selected,
         'requests':len(rows),'warmups':16,'scope':'Previously unused MBPP in audited available project history; no functional accuracy or population confidence claim.'}
    save(HERE/'generated/B_RESULTS.json',out)
    save(HERE/'generated/C_SELECTION.json',{'status':'QUALIFIED' if selected else 'BLOCKED','condition':next((c for c in plan['conditions'] if c['name']==selected),None),
         'B_results_sha256':sha(HERE/'generated/B_RESULTS.json'),'B_records_sha256':sha(HERE/'runs/b/RECORDS.json'),'tasks':tasks[:8],
         'legacy_long_tasks':[t['id'] for t in read(HERE/'C_LEGACY_INPUTS.json')],'caps':[128,256,512],'widths':[[1,2],[3,4],[5,6],[7,8]]})
    print({'qualification':q,'selected':selected,'costs':[(x['numerator'],x['denominator'],x['generation']['task_median_geomean_speedup'],x['wall']['task_median_geomean_speedup']) for x in costs]},flush=True)

def c():
    rows=read(HERE/'runs/c/RECORDS.json');inputs=read(HERE/'C_INPUTS.json');tasks=[t['id'] for t in inputs];assert len(rows)==792
    modes=['scalar_reference','matched_target','selected_speculation'];bycap={};configs=[];failures=[]
    anchors128={r['task']:signature(r) for r in read(HERE/'runs/b/RECORDS.json') if r['condition']=='scalar_reference' and r['repetition']==1}
    anchors128.update({t['id']:(tuple(t['original_reference_ids']),t['original_endpoint']) for t in inputs if t['cohort']=='exposed_long_supplement'})
    anchors128={t:anchors128[t] for t in tasks}
    for cap in [128,256,512]:
        bycap[cap]={t:signature(next(r for r in rows if r['task']==t and r['condition']=='scalar_reference' and r['width_k']==1 and r['requested_cap']==cap)) for t in tasks}
        if cap==128:assert bycap[cap]==anchors128
    for k,ub in [[1,2],[3,4],[5,6],[7,8]]:
        for cap in [128,256,512]:
            rs=[r for r in rows if r['width_k']==k and r['requested_cap']==cap]
            stable,q,details,refs=correctness(rs,tasks,modes,2,bycap[cap]);cohorts={};costs=[]
            for cohort in ['primary_unused_MBPP','exposed_long_supplement']:
                tt=[t['id'] for t in inputs if t['cohort']==cohort];cq={mode:all(d['full_equal'] for d in details if d['task'] in tt and d['condition']==mode) for mode in modes}
                cohorts[cohort]={'tasks':tt,'qualification':cq,'actual_reference_lengths':{t:len(refs[t][0]) for t in tt},'reference_endpoints':{t:refs[t][1] for t in tt}}
                costs.append({'cohort':cohort,**summarize(rs,tt,'selected_speculation','matched_target',cq['matched_target'] and cq['selected_speculation'])})
            config={'k':k,'ub':ub,'cap':cap,'reference_stable':stable,'qualification':q,'cohorts':cohorts,'details':details,'costs':costs}
            configs.append(config)
            for t in tasks:
                failing=[d for d in details if d['task']==t and d['condition']!='scalar_reference' and not d['full_equal']]
                if failing:failures.append({'task':t,'k':k,'ub':ub,'cap':cap,'failures':failing})
    anchor=next(x for x in configs if x['k']==3 and x['cap']==128)
    out={'stage':'C','requests':len(rows),'warmups':24,'records_sha256':sha(HERE/'runs/c/RECORDS.json'),'configurations':configs,'all_reference_cross_width_stable':all(x['reference_stable'] for x in configs),
         'D_anchor_qualified':anchor['qualification']['matched_target'] and anchor['qualification']['selected_speculation'],'diagnostic_pairs':failures[:2]}
    save(HERE/'generated/C_RESULTS.json',out)
    print({'qualified_configs':[(x['k'],x['cap']) for x in configs if x['qualification']['matched_target'] and x['qualification']['selected_speculation']],'D_anchor_qualified':out['D_anchor_qualified'],'diagnostic_pairs':[(x['task'],x['k'],x['cap']) for x in failures[:2]]},flush=True)

def d():
    plan=read(HERE/'D_MANIFEST.json');inputs=read(HERE/'B_INPUTS.json');tasks=[t['id'] for t in inputs]
    refs={r['task']:signature(r) for r in read(HERE/'runs/b/RECORDS.json') if r['condition']=='scalar_reference' and r['repetition']==1}
    out={'stage':'D','requests':192,'warmups':8,'panels':{}}
    for stage in ['d_reset','d']:
        rows=read(HERE/f'runs/{stage}/RECORDS.json');assert len(rows)==96
        q={mode:all(signature(r)==refs[r['task']] for r in rows if r['condition']==mode) for mode in ['matched_target','selected_speculation']}
        details=[{'task':r['task'],'condition':r['condition'],'cycle':r['repetition'],'full_equal':signature(r)==refs[r['task']],'tokens':len(r['response']['tokens']),'endpoint':r['endpoint'],'drafted':r['response']['timings'].get('draft_n'),'accepted_drafts':r['response']['timings'].get('draft_n_accepted'),'timings':r['response']['timings']} for r in rows]
        panel={'records_sha256':sha(HERE/f'runs/{stage}/RECORDS.json'),'qualification':q,'details':details,'measured':stage=='d'}
        if stage=='d':
            panel['costs']=summarize(rows,tasks,'selected_speculation','matched_target',all(q.values()))
            panel['order_half_trends']=[{'session':s['name'],'first_half_wall_median_ms':statistics.median(r['wall_ms'] for r in rows if r['session']==s['name'] and r['order_index']<12),'last_half_wall_median_ms':statistics.median(r['wall_ms'] for r in rows if r['session']==s['name'] and r['order_index']>=12)} for s in plan['schedule']]
        out['panels'][stage]=panel
    out['reset_proof']=read(HERE/'generated/D_RESET_QUALIFICATION.json');out['qualified']=all(all(p['qualification'].values()) for p in out['panels'].values())
    save(HERE/'generated/D_RESULTS.json',out);print({'qualified':out['qualified'],'costs':out['panels']['d']['costs']['generation']['task_median_geomean_speedup'],'wall':out['panels']['d']['costs']['wall']['task_median_geomean_speedup']},flush=True)

if __name__=='__main__':
    import sys
    globals()[sys.argv[1]]()
