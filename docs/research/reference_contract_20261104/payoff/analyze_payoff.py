#!/usr/bin/env python3
"""CPU-only saved-data sensitivity analysis. No native/model/GPU requests.
Run: python analyze_payoff.py --out analysis.json
These are conditional opportunity bounds, not predictions of unmeasured loop4.
"""
import argparse, collections, gzip, hashlib, json, math, statistics
from pathlib import Path
P=Path(__file__).resolve().parent
D=P
BUNDLE=json.loads((D/'data.json').read_text())
def load(n):
    return BUNDLE[n]
def mean(xs): return statistics.mean(xs)
def gm(xs): return statistics.geometric_mean(xs)
def scenario(total,phase):
    f=phase/total
    return {'total_mean_s':total,'phase_mean_s':phase,'phase_fraction_ratio_of_sums':f,
      'phase_zero_cost_speedup_ceiling':1/(1-f),
      'hypothetical_all_phase_reduction_grid':[
         {'phase_time_reduction':r,'service_time_reduction_no_overhead':f*r,
          'service_time_reduction_with_1pct_overhead':f*r-.01}
         for r in (.05,.1,.2,.5,1)],
      'phase_reduction_required_for_5pct_service_no_overhead':.05/f,
      'phase_reduction_required_for_5pct_service_with_1pct_overhead':.06/f}
def matched(rows,arm): return [r for r in rows if r['arm']==arm]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(P/'analysis.json'));args=ap.parse_args()
    manifest=json.loads((D/'sources.json').read_text())
    assert hashlib.sha256((D/'data.json').read_bytes()).hexdigest()==manifest['bundle_sha256'],'data.json'
    out={'scope':'Saved data only. Phase savings are hypothetical whole-phase ceilings; loop4 and new safety performance remain NOT_RUN.',
      'aggregation':'Ratios of arithmetic sums for mean-latency budget. Per-root/session transformations also report geometric latency ratio. Never subtract geometric means or add overlapping timers.'}
    rows=load('171_service-cost.json.gz');assert len(rows)==36
    out['171']={}
    for arm in ('oldQB','newQB','newWB'):
        a=[r['measured'] for r in matched(rows,arm)]
        assert len(a)==12
        assert all(r['prefill_wall_seconds']+r['continuation_wall_seconds']<=r['service_seconds']+1e-6 for r in a)
        x=scenario(mean(r['service_seconds'] for r in a),mean(r['prefill_wall_seconds'] for r in a))
        x.update(service_geomean_s=gm(r['service_seconds'] for r in a),
          phase_label='Entire target+draft prefill, loose superset of packing-addressable work',
          prompt_lengths=sorted({r['prompt_tokens'] for r in a}),
          actual_verify_widths=sorted({c['caller_rows'] for r in a for c in r['cycles']}),
          rows=[{'index':i,'prompt_tokens':next(r['measured']['prompt_tokens'] for r in rows if r['arm']==arm and r['index']==i),
                 **scenario(mean(r['measured']['service_seconds'] for r in rows if r['arm']==arm and r['index']==i),
                            mean(r['measured']['prefill_wall_seconds'] for r in rows if r['arm']==arm and r['index']==i))} for i in range(4)])
        x['counterfactual_geometric_service_ratio']={str(s):gm((r['service_seconds']-s*r['prefill_wall_seconds'])/r['service_seconds'] for r in a) for s in (.1,.2,.5,1)}
        out['171'][arm]=x
    lookup={(r['session'],r['index'],r['arm']):r['measured'] for r in rows}
    old=[lookup[s,i,'oldQB'] for s in range(3) for i in range(4)]
    new=[lookup[s,i,'newQB'] for s in range(3) for i in range(4)]
    out['171_old_to_new']={'mean_service_saved_s':mean(a['service_seconds']-b['service_seconds'] for a,b in zip(old,new)),
       'mean_prefill_saved_s':mean(a['prefill_wall_seconds']-b['prefill_wall_seconds'] for a,b in zip(old,new)),
       'geometric_latency_ratio':gm(b['service_seconds']/a['service_seconds'] for a,b in zip(old,new))}
    details=load('174_DETAILS.json');out['174']={}
    for arm,x in details['phase_summaries'].items():
        out['174'][arm]=scenario(x['seconds']['mean'],x['append_from_receipt_s']['mean'])
        out['174'][arm].update(phase_label='Receipt-to-append, includes file/index/reset/lookup/import and all append; loose ceiling ONLY',
            import_cumulative_unsynchronized_mean_s=x['import_s']['mean'],
            prohibited_inference='Do not subtract import from append and call it isolated GPU append.')
    out['174']['auto_calibration']=details['break_even']
    panel=load('174_common-panel.json')['test']
    out['174']['panel_geometry']={'roots':len(panel),'head_min_max':[min(r['effective_head'] for r in panel),max(r['effective_head'] for r in panel)],
        'append_min_max':[min(r['append_tokens'] for r in panel),max(r['append_tokens'] for r in panel)],
        'crossed_roots':sum(r['crossed_qb_calls']>0 for r in panel)}
    rows=load('177_ANALYSIS.json')['records'];out['177']={};assert len(rows)==48
    for arm in ('QB','WB-cut','WB-rechunk'):
        a=matched(rows,arm);assert len(a)==16
        assert all(abs(r['service_s']-sum(r[k] for k in ('lookup_import_ready_s','append_execution_s','continuation_s')))<1e-6 for r in a)
        x=scenario(mean(r['service_s'] for r in a),mean(r['append_execution_s'] for r in a))
        x.update(phase_label='Synchronized disjoint append; includes planning, graph, all kernels, synchronization',
             lookup_import_mean_s=mean(r['lookup_import_ready_s'] for r in a),continuation_mean_s=mean(r['continuation_s'] for r in a),
             service_geomean_s=gm(r['service_s'] for r in a),
             rows=[{'index':i,**scenario(mean(r['service_s'] for r in a if r['index']==i),mean(r['append_execution_s'] for r in a if r['index']==i))} for i in range(8)])
        x['counterfactual_geometric_service_ratio']={str(s):gm((r['service_s']-s*r['append_execution_s'])/r['service_s'] for r in a) for s in (.1,.2,.5,1)}
        out['177'][arm]=x
    cov=load('177_coverage.json')
    out['177']['coverage']={k:cov[k] for k in ('paths_seen','roots_seen','paths_with_distinct_rechunk_schedule','unexposed_root_representatives','unexposed_representatives_with_distinct_schedule')}
    out['177']['coverage']['selection_fraction']=cov['unexposed_representatives_with_distinct_schedule']/cov['unexposed_root_representatives']
    ops=load('171_operands.json.gz');trace=load('171_operator-activities.json.gz');out['171_operators']=[]
    for op in ops:
        if op['model']!='8B':continue
        name=op['descriptor']['weight']['name']
        for q in (8,16,32):
            z={r['route']:r for r in op['routes'] if r['q']==q}
            item={'name':name,'q':q,'source_scope':'Three post-initial synchronized unprofiled replay samples; separate single trace; captured operands only'}
            for arm in ('tile','packed'):
                r=z[arm];assert r['scalar_equal']
                item[arm]={'median_wall_us':statistics.median(a+b for a,b in zip(r['submit_s'][1:],r['sync_s'][1:]))*1e6,'plan_us':r['plan_s']*1e6}
                categories=collections.defaultdict(lambda:{'count':0,'kernel_sum_us':0})
                for e in trace[f'{name}/{q}-{arm}']:
                    if e['kind']!='kernel':continue
                    typ='quantizer' if 'quantize' in e['name'] else 'concat' if 'concat' in e['name'] else 'mmvq' if 'mul_mat_vec' in e['name'] else 'other'
                    categories[typ]['count']+=1;categories[typ]['kernel_sum_us']+=(e['end']-e['start'])/1000
                item[arm]['profiled_categories']=dict(categories)
            item['wall_time_reduction']=1-item['packed']['median_wall_us']/item['tile']['median_wall_us']
            item['mechanistic_loop4_launch_count_not_measured']=1+math.ceil(q/4)
            out['171_operators'].append(item)
    checkpoint=BUNDLE['179_latest_native_checkpoint.hpp']
    assert checkpoint==BUNDLE['179_native_checkpoint.hpp']
    vocab=next(o['descriptor']['weight']['ne'][1] for o in ops if o['model']=='8B' and o['descriptor']['weight']['name']=='output.weight')
    out['179']={'latest_checked_ref':'8005cf01b9b7736d77e4e0c5dc3ecb2da2c29603',
       'checkpoint_header_unchanged_from_d694011':True,'vocab_from_saved_operator':vocab,
       'q32_all_logit_payload_bytes':32*vocab*4,'q32_all_logit_payload_MiB':32*vocab*4/2**20,
       'scope':'Payload arithmetic only, not transfer duration or measured peak memory. Every-logit contract cannot be weakened to last-row after the fact.',
       'performance':'NOT_RUN'}
    Path(args.out).write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: source hashes, 36 PR171 rows, 48 PR177 rows, all disjoint phase sums, checkpoint identity.')
    print('Output:',args.out)
    for label,x in [('171 newWB prefill',out['171']['newWB']),('174 WB-cut receipt→append',out['174']['WB-cut']),('177 WB-rechunk append',out['177']['WB-rechunk'])]:
        print(label,'fraction',round(x['phase_fraction_ratio_of_sums'],6),'required phase reduction for 5% net + 1% overhead',round(x['phase_reduction_required_for_5pct_service_with_1pct_overhead'],6))
if __name__=='__main__':main()
