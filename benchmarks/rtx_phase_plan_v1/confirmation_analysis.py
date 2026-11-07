"""Read-only frozen estimands; roots, not repeated slots, are resampled."""
from confirmation import *
import math

def analyze():
    assert (DEST/'COMPLETE.json').exists()
    data=inputs();schedule=json.loads((DEST/'SCHEDULE.json').read_bytes());families={}
    for family,rs in data.items():
        times=np.full((8,6,6),np.nan);arms={a:dict(rows=[],model_load_s=0.,pool_setup_s=0.,warmup_service_s=0.,initial_plan_compile_s=0.,host_attempt_wall_s=0.) for a in ARMS}
        for s in [x for x in schedule if x['family']==family]:
            out=ROOT/'runs'/s['label'];assert json.loads((out/'CHECKED.json').read_bytes())['original_R_endpoint_equal']
            r=json.loads((out/'native/measure/receipt.json').read_bytes());w=json.loads((out/'native/warmup/receipt.json').read_bytes());meta=native_fields(out/'native/result.json',['model_load_s','pool_setup_s','resident_initial_plan_compile_s'])
            assert all(v==0 for v in r['observed_API_calls_within_service'].values())
            native=sum(r['target_phases'].values())+sum(r['draft_phases'].values());other=r['service_seconds']-native-r['setup_seconds']-r['teardown_seconds']-r['planning_s']-r['output_copy_s'];assert other>=-1e-6
            a=arms[s['arm']];a['rows'].append(dict(root=s['root'],root_index=s['root_index'],session=s['session'],service_s=r['service_seconds'],target_phases=r['target_phases'],draft_phases=r['draft_phases'],planning_s=r['planning_s'],output_copy_s=r['output_copy_s'],reset_s=r['setup_seconds'],teardown_s=r['teardown_seconds'],other_service_s=other,tokens=len(r['ids']),stop=r['stop_reason'],warmup_service_s=w['service_seconds'],online_API_calls=r['observed_API_calls_within_service']))
            for key,source in [('model_load_s','model_load_s'),('pool_setup_s','pool_setup_s'),('initial_plan_compile_s','resident_initial_plan_compile_s')]:a[key]+=meta[source]
            a['warmup_service_s']+=w['service_seconds'];a['host_attempt_wall_s']+=json.loads((out/'exit.json').read_bytes())['seconds']
            times[s['root_index'],s['session'],ARMS.index(s['arm'])]=r['service_seconds']
        assert np.isfinite(times).all() and (times>0).all();totals=times.sum(axis=1)
        seed=int.from_bytes(hashlib.sha256((SEED+'|bootstrap|'+family).encode()).digest()[:8],'little')
        indices=np.random.Generator(np.random.PCG64(seed)).integers(0,8,size=(10000,8));boot=totals[indices].sum(axis=1)
        index_path=DEST/(family+'-bootstrap-indices.npy')
        if not index_path.exists():np.save(index_path,indices.astype(np.uint8))
        else:assert np.array_equal(np.load(index_path),indices)
        def contrast(num,den,alpha):
            i,j=ARMS.index(num),ARMS.index(den);ratios=totals[:,i]/totals[:,j];br=boot[:,i]/boot[:,j]
            return dict(numerator=num,denominator=den,total_complete_service_ratio=float(totals[:,i].sum()/totals[:,j].sum()),family_adjusted_percentile_interval=np.quantile(br,[alpha/2,1-alpha/2],method='linear').tolist(),equal_root_geometric_ratio=float(np.exp(np.log(ratios).mean())),absolute_total_difference_s=float(totals[:,i].sum()-totals[:,j].sum()),per_root_six_session_ratios=ratios.tolist(),adverse_roots=[rs[k]['id'] for k,v in enumerate(ratios) if v>1],root_cluster_n=8,repetitions_per_root=6)
        all_pairs=[contrast(a,b,.05/15) for a,b in combinations(ARMS,2)]
        primary=[contrast('LOCAL-D4',den,.05/3) for den in ('SIMPLE-D4','SIMPLE-M','LOCAL-M')]
        min_ratio=max(x['total_complete_service_ratio'] for x in primary[1:]);min_interval=[max(x['family_adjusted_percentile_interval'][k] for x in primary[1:]) for k in (0,1)]
        for arm,a in arms.items():
            j=ARMS.index(arm);a['measurement_service_s']=float(totals[:,j].sum());a['per_root_six_session_service_s']=totals[:,j].tolist();a['mean_measured_service_s']=a['measurement_service_s']/48
            setup=(a['model_load_s']+a['pool_setup_s'])/48
            a['calculated_setup_amortization_per_request_s']={str(n):a['mean_measured_service_s']+setup/n for n in (1,16,128)}
            a['amortization_is_calculated_not_an_additional_measurement']=True
        families[family]=dict(roots=[r['id'] for r in rs],arms=arms,primary_three_fixed_contrasts=primary,LOCAL_D4_over_observed_min_M=dict(ratio=min_ratio,simultaneous_fixed_M_interval_envelope=min_interval,both_fixed_M_contrasts_reported=True),all_fifteen_contrasts=all_pairs,bootstrap=dict(seed=seed,bit_generator='PCG64',draws=10000,indices_sha256=sha(index_path),units='Eight independent roots with all six sessions and all arms kept together',intervals='Approximate root-cluster percentile bootstrap; primary family3 and descriptive family15 have separate Bonferroni adjustments.'),fastest_observed_fixed_arm=min(arms,key=lambda a:arms[a]['measurement_service_s']))
    result=dict(families=families,measurements=576,warmups=576,all_six_controls_retained=True,primary_total_service_secondary_equal_root_log=True,families_analyzed_separately=True,no_historical_timing_pooling=True,no_extra_sessions=True,no_significance_target=True,complete_native_host_costs='host_evidence/UNIFIED_COSTS.json; setup/warmups/failed and original-R work retained, not added twice to service.',full_vector_and_committed_KV_scope='Finite development qualification only; clean confirmation checks endpoints/producer/frontier/pending/stop traces and actual zero online state API calls.')
    save(DEST/'RESULTS.json',result)
    for family,f in families.items():
        print(family,'total service',{a:round(r['measurement_service_s'],6) for a,r in f['arms'].items()},flush=True)
        print('primary',f['primary_three_fixed_contrasts'],flush=True)

if __name__=='__main__':analyze()
