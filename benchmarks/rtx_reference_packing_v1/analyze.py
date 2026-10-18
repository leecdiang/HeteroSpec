"""Exhaustive deterministic panel aggregation; no candidate or input selection."""
import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from prepare import ROOT,sha,save

def main():
    plan=json.loads((ROOT/'PLAN.json').read_bytes());records=[];groups={};wait_names=set();trace_hashes={}
    complete=json.loads((ROOT/'formal/COMPLETE.json').read_bytes());assert complete['attempts']==len(plan['cells'])==390
    for i,cell in enumerate(plan['cells']):
        d=ROOT/f'formal/{i:04d}';receipt=json.loads((d/'CELL_RESULT.json').read_bytes())
        row=dict(index=i,**cell,status=receipt['status'])
        if receipt['status']=='PASS':
            result=json.loads((d/'OUTPUT.json').read_bytes());assert sha(d/'OUTPUT.json')==receipt['output_sha256']
            assert sha(d/'trace.jsonl.gz')==receipt['trace_sha256']
            row.update({k:v for k,v in result.items() if k not in ('output','waits','model_level')})
            for key,value in result['waits'].items():row['wait_'+key]=value;wait_names.add('wait_'+key)
            row.update(queue_peak=receipt['checker']['queue_peak'],micro_operations=receipt['checker']['micro_operations'])
            key=(cell['workload'],cell['resource']);groups.setdefault(key,{})[cell['mapping']]=result
            trace_hashes.setdefault(key,{})[cell['mapping']]=hashlib.sha256(gzip.decompress((d/'trace.jsonl.gz').read_bytes())).hexdigest()
        else:row['error']=receipt.get('error')
        records.append(row)
    comparisons=[]
    for (w,r),maps in groups.items():
        base=maps['B1_PACKED_MULTICAST'];assert len(maps)==5
        parity=all(x==base for x in maps.values());trace_equal=len(set(trace_hashes[(w,r)].values()))==1
        for name,result in maps.items():comparisons.append(dict(workload=w,resource=r,mapping=name,cycles=result['cycles'],B1_over_mapping=base['cycles']/result['cycles'],all_metrics_parity=parity,full_trace_parity=trace_equal))
    columns=sorted(set().union(*(r.keys() for r in records)))
    with (ROOT/'CELLS.csv').open('x',encoding='utf-8',newline='') as f:
        out=csv.DictWriter(f,fieldnames=columns);out.writeheader();out.writerows(records)
    with (ROOT/'COMPARISONS.csv').open('x',encoding='utf-8',newline='') as f:
        out=csv.DictWriter(f,fieldnames=list(comparisons[0]));out.writeheader();out.writerows(comparisons)
    per_resource={}
    for resource in plan['resources']:
        rs=[r for r in records if r['resource']==resource['id'] and r['status']=='PASS' and r['mapping']=='B1_PACKED_MULTICAST']
        per_resource[resource['id']]=dict(points=len(rs),cycles_range=[min(r['cycles'] for r in rs),max(r['cycles'] for r in rs)],peak_buffer_range=[min(r['peak_buffer_bytes'] for r in rs),max(r['peak_buffer_bytes'] for r in rs)],waits_total={k:sum(r.get(k,0) for r in rs) for k in sorted(wait_names)},queue_peak=max(r['queue_peak'] for r in rs))
    ledger=[json.loads(p.read_bytes()) for p in sorted((ROOT/'child_ledger').glob('*-EXIT.json'))]
    decision='SOFTWARE_FIRST' if complete['passed']==390 and all(r['all_metrics_parity'] and r['full_trace_parity'] for r in comparisons) else 'HOLD_MISSING_EVIDENCE'
    summary=dict(decision=decision,attempts=390,passed=complete['passed'],failed=complete['failures'],missing_cells=[],workloads=26,native_subviews=24,synthetic=2,
        resource_points=len(groups),mappings=5,comparisons=len(comparisons),all_metrics_and_full_trace_parity=all(r['all_metrics_parity'] and r['full_trace_parity'] for r in comparisons),
        cycle_ratio_range=[min(r['B1_over_mapping'] for r in comparisons),max(r['B1_over_mapping'] for r in comparisons)],per_resource=per_resource,
        counterexample_tests=23,formal_scientific_retries=0,new_GPU_model_operator_starts=0,prior_completed_research_child_jobs=len(ledger),
        prior_completed_child_seconds=sum(x['seconds'] for x in ledger),prior_peak_RSS_bytes=max(x['peak_rss_bytes'] or 0 for x in ledger),
        native_input_note='24 first-qualified layer0 MQ softmax/F16-V subviews; K64,head0,KVhead0,C2; P is not renormalized; not full native AV replay',
        reference='DECLARED_ARCHITECTURE_REFERENCE',no_hardware_speed_claim=True,no_RTX_calibration=True,
        alias_interpretation='Same implementation and capabilities by H0 design; parity is deliberate consistency/control evidence, not independent proof of different hardware equivalence',
        sensitivity='Three predeclared resource regimes and finite engineering overhead/write-port tests; no posthoc grid expansion')
    save(ROOT/'SUMMARY.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='per_resource'}))
if __name__=='__main__':main()
