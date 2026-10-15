"""Compact CPU coverage and error distributions without tolerance selection."""
import collections, json
from common import ROOT, load, save, sha, modules

def main():
    before=modules();rows=[];receipts=[]
    for group in ('DEV','HOLDOUT'):
        receipt=load(ROOT/(group+'_RECEIPT.json'));receipts.append(receipt)
        assert receipt['returncode']==0 and receipt['planned']==receipt['completed']
        assert sha(ROOT/(group+'_RAW.jsonl'))==receipt['raw_sha256']
        for x in map(json.loads,(ROOT/(group+'_RAW.jsonl')).read_text().splitlines()):
            if x['event']=='FIXTURE':x['group']=group;rows.append(x)
    assert len(rows)==432 and len({x['id'] for x in rows})==432
    assert receipts[0]['executable_sha256']==receipts[1]['executable_sha256']==load(ROOT/'RULE_LOCK.json')['executable_sha256']
    assert receipts[0]['sources']==receipts[1]['sources']
    geometries=collections.defaultdict(list);metrics=collections.defaultdict(list)
    for x in rows:
        f=x['geometry'];key=tuple(f[n] for n in ('q','k','h','hk','storage'));geometries[key].append(x)
        for y in x['layouts']:
            for stage in ('QK','softmax','AV','permute','final'):metrics[(y['layout'],stage)].append(y[stage])
    assert len(geometries)==72 and all(len(x)==6 for x in geometries.values())
    summary=[]
    for (layout,stage),ms in metrics.items():
        total=sum(x['elements'] for x in ms)
        summary.append(dict(layout=['MQ','PQ','QB'][layout],stage=stage,elements=total,
         exact_fp64=sum(x['exact_fp64'] for x in ms),nonfinite=sum(x['nonfinite'] for x in ms),
         max_abs=max(x['max_abs'] for x in ms),max_relative=max(x['max_relative_floor_1e_300'] for x in ms),
         max_f32_ulp=max(x['max_f32_ulp'] for x in ms),
         ulp_bins_0_1_2to4_5to16_gt16=[sum(x['ulp_bins_0_1_2to4_5to16_gt16'][i] for x in ms) for i in range(5)],
         rms=(sum(x['rms']**2*x['elements'] for x in ms)/total)**.5,
         max_abs_witness=max(ms,key=lambda x:x['max_abs'])['max_abs_witness']))
    assert sum(x['nonfinite'] for x in summary)==0
    coverage=[dict(zip(('q','k','h','hk','storage'),key),fixtures=6,
                   group=xs[0]['group'],address_checks=sum(x['address_checks'] for x in xs)) for key,xs in geometries.items()]
    save(ROOT/'CPU_RESULT.json',dict(geometries=72,fixtures=432,development=144,holdout=288,
         graph_computes=1296,CPU_model_processes=0,CPU_harness_processes=2,
         q1_common_original_graph_computes=648,q2_distinct_graph_computes=648,
         exact_structured_fixtures=216,single_valid_key_structured_fixtures=72,
         address_checks=sum(x['address_checks'] for x in rows),coverage=coverage,metrics=summary,
         CPU_harness_wall_s=sum(x['elapsed_s'] for x in receipts),
         failures=dict(address_or_strict=0,crash=0,nonfinite=0),
         interpretation='QK exact for these dyadic inputs; general softmax/AV errors are distributions, not semantic/GPU PASS thresholds. ULP sign crossings near zero can be very large. No posthoc tolerance.',
         first_holdout_retained=True,fixture_oracle_implementation_revisions=0,
         numerical_executable_sha256=receipts[0]['executable_sha256'],
         new_model_requests=0,new_GPU_forwards=0,new_GPU_operators=0,probes=0,warmups=0,retries=0,
         modules_before=before,modules_after=modules()))
    text=['q,k,h,hk,storage,group,fixtures,address_checks']
    text += [','.join(str(x[n]) for n in ('q','k','h','hk','storage','group','fixtures','address_checks')) for x in coverage]
    (ROOT/'COVERAGE.csv').write_text('\n'.join(text)+'\n')
    print(dict(fixtures=432,geometries=72,address_checks=sum(x['address_checks'] for x in rows),max_av_abs=max(x['max_abs'] for x in summary if x['stage']=='AV')))

if __name__=='__main__':main()
