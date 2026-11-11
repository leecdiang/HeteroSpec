"""Frozen paired-root families; qualification and profiling never enter estimands."""
from pathlib import Path
import collections,json,sys
import numpy as np
from admission import ROOT,put

def diagnostic():
    rows=json.loads((ROOT/'SAME_WORK_CLEAN_RECORDS.json').read_bytes())['records'];rows=[x for x in rows if x['probe']['kind']=='measurement']
    assert len(rows)==128
    groups=collections.defaultdict(dict)
    for r in rows:
        p=r['probe'];key=(p['origin'],r['projection'],p['geometry'],p['repeat']);groups[key][p['execution']]=r['receipt']['operation_seconds']
    assert len(groups)==64 and all(set(x)=={'q4pair','q8'} for x in groups.values())
    tables=[]
    for projection in ('loop4','packed'):
        for geometry in ('within','cross'):
            selected=[(key,v) for key,v in groups.items() if key[1:3]==(projection,geometry)]
            a=sum(v['q4pair'] for _,v in selected);b=sum(v['q8'] for _,v in selected)
            tables.append(dict(projection=projection,geometry=geometry,paired_observations=len(selected),q4pair_total_s=a,q8_total_s=b,q8_over_q4pair=b/a,change_pct=(b/a-1)*100,
                per_origin=[dict(origin=origin,q4pair_total_s=sum(v['q4pair'] for k,v in selected if k[0]==origin),q8_total_s=sum(v['q8'] for k,v in selected if k[0]==origin)) for origin in sorted({k[0] for k,_ in selected})]))
    result=dict(scope='Four fixed origins; paired AB,BA,BA,AB target-only equal work; no draft calls, live speedup or population inference',measured_requests=128,primers=32,tables=tables)
    put(ROOT/'SAME_WORK_RESULTS.json',result);return result

def live():
    bundle=json.loads((ROOT/'LIVE_RECORDS.json').read_bytes());assert bundle['passed'] and bundle['complete_workers']==64
    rows=[r for r in bundle['records'] if r['kind']=='measurement'];assert len(rows)==1024
    roots=[r['id'] for r in json.loads((ROOT/'cohort/COHORT_FREEZE.json').read_bytes())['inputs']];assert len(roots)==16
    root_index={r:i for i,r in enumerate(roots)};matrix=np.zeros((8,16));counts=np.zeros((8,16),dtype=int)
    for r in rows:matrix[r['arm'],root_index[r['root']]]+=r['receipt']['service_seconds'];counts[r['arm'],root_index[r['root']]]+=1
    assert np.all(counts==8) and np.all(matrix>0)
    rng=np.random.Generator(np.random.PCG64(20261109));draws=rng.integers(0,16,size=(10000,16));boot=matrix[:,draws].sum(axis=2)
    def contrast(name,numerator,denominator):
        ratio=float(matrix[numerator].sum()/matrix[denominator].sum());distribution=boot[numerator]/boot[denominator]
        interval=np.quantile(distribution,[.00625,.99375],method='linear')
        return dict(name=name,numerator_arm=numerator,denominator_arm=denominator,ratio=ratio,change_pct=(ratio-1)*100,
            adjusted_interval_ratio=interval.tolist(),adjusted_interval_change_pct=((interval-1)*100).tolist(),adverse_roots=int(np.sum(matrix[numerator]>matrix[denominator])),
            per_root=[dict(root=root,ratio=float(matrix[numerator,i]/matrix[denominator,i])) for i,root in enumerate(roots)])
    primary=[contrast(name,n,d) for name,n,d in [('W-loop4 k7/k3',1,0),('W-packed k7/k3',3,2),('LOCAL-loop4 k7/k3',5,4),('LOCAL-packed k7/k3',7,6)]]
    secondary=[contrast(name,n,d) for name,n,d in [('W k7 packed/loop4',3,1),('LOCAL k7 packed/loop4',7,5),('loop4 k7 LOCAL/W',5,1),('packed k7 LOCAL/W',7,3)]]
    arms=[]
    for arm in range(8):
        selected=[r for r in rows if r['arm']==arm];receipts=[x['receipt'] for x in selected]
        proposed=sum(len(c['proposals']) for r in receipts for c in r['cycles']);accepted=sum(c['accepted'] for r in receipts for c in r['cycles'])
        rejected=sum(bool(c['rejected']) for r in receipts for c in r['cycles']);tail=sum(len(c['proposals'])-c['accepted']-int(c['rejected']) for r in receipts for c in r['cycles'])
        assert proposed==accepted+rejected+tail
        phase=lambda role,name:sum(r[role+'_phases'].get(name,0) for r in receipts)
        service=sum(r['service_seconds'] for r in receipts);planning=sum(r['planning_s'] for r in receipts);output_copy=sum(r['output_copy_s'] for r in receipts)
        setup=sum(r['setup_seconds'] for r in receipts);teardown=sum(r['teardown_seconds'] for r in receipts)
        target=sum(sum(r['target_phases'].values()) for r in receipts);draft=sum(sum(r['draft_phases'].values()) for r in receipts)
        residual=service-target-draft-planning-output_copy-setup-teardown
        target_rows=sum(sum(int(k)*v for k,v in r['target_physical_width_hist'].items()) for r in receipts)
        draft_rows=sum(sum(int(k)*v for k,v in r['draft_physical_width_hist'].items()) for r in receipts)
        arms.append(dict(arm=arm,label=selected[0]['arm_label'],measurements=len(selected),service_total_s=service,mean_service_s=service/len(selected),
            emitted_tokens=sum(r['length'] for r in receipts),cap_hits=sum(r['stop_reason']=='CAP' for r in receipts),eog_stops=sum(r['stop_reason']=='EOG' for r in receipts),
            cycles=sum(len(r['cycles']) for r in receipts),proposed=proposed,accepted=accepted,rejected_incorrect_proposals=rejected,tail_unconsumed=tail,
            accepted_over_all_proposed=accepted/proposed if proposed else None,accepted_over_inspected=accepted/(accepted+rejected) if accepted+rejected else None,
            target_physical_rows=target_rows,draft_physical_rows=draft_rows,verify_physical_rows=sum(e['width'] for r in receipts for e in r['executions'] if e['phase']=='VERIFY'),
            target_prefill_s=phase('target','PREFILL'),draft_prefill_s=phase('draft','PREFILL'),target_verify_s=phase('target','VERIFY'),draft_sync_s=phase('draft','DRAFT_SYNC'),draft_propose_s=phase('draft','PROPOSE'),
            setup_s=setup,teardown_s=teardown,planning_s=planning,owned_output_copy_s=output_copy,unassigned_residual_s=residual,
            session_service_s={str(s):sum(r['receipt']['service_seconds'] for r in selected if r['session']==s) for s in range(8)},
            domain_service_s={d:sum(r['receipt']['service_seconds'] for r in selected if r['domain']==d) for d in ('code','math')}))
    result=dict(complete=True,measured_requests=1024,primers=128,root_clusters=16,paired_order_blocks=8,
        bootstrap=dict(draws=10000,seed=20261109,rng='numpy.PCG64',numpy_version=np.__version__,interval=98.75,percentile_method='linear',families='Four primary and four separately labelled secondary; Bonferroni within each family'),
        primary=primary,secondary=secondary,all_eight_arms=arms,service_by_arm_root=matrix.tolist(),roots=roots,
        limitations=['Finite16 project-outcome-unexposed roots at cap96/prompt<=192, one native Windows GPU/configuration.',
        'No contemporaneous timed target-only M control; no old M timing pooling or speculation/M superiority claim.',
        'Cross-platform GPU/OS/CPU/cohort/horizon/build differences prevent architecture-causal attribution.',
        'Host phase/residual clocks are not GPU kernel times; CUDA kernel/CUDA graph profiling absent.'])
    put(ROOT/'LIVE_RESULTS.json',result);return result

if __name__=='__main__':
    result={'diagnostic':diagnostic,'live':live}[sys.argv[1]]();print(json.dumps({k:v for k,v in result.items() if k in ('complete','primary','tables')},ensure_ascii=False),flush=True)
